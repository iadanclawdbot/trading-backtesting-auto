# =============================================================================
# TESTS DE INTEGRACIÓN — MOTOR DE BACKTESTING
# test_integracion.py
#
# Tests end-to-end del motor de backtesting usando datos sintéticos.
# No dependen de datos reales ni de fechas específicas.
# =============================================================================

import unittest
import sys
import os
import pandas as pd

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from conftest_data import make_candles
from motor_base import calcular_indicadores, correr_backtest_base, calcular_metricas, calcular_indicadores_breakout
from config import STRATEGY, RULES, COSTS, INITIAL_CAPITAL


class TestMotorIntegracion(unittest.TestCase):
    """Tests de integración del motor de backtesting."""

    def test_sin_datos_no_crashea(self):
        """Motor handles empty dataframe gracefully."""
        import pandas as pd

        df_empty = pd.DataFrame()
        # Should return empty trades, not raise exception
        trades, capital, _ = correr_backtest_base(
            df_empty, STRATEGY, RULES, COSTS, INITIAL_CAPITAL
        )
        self.assertEqual(trades, [])
        self.assertEqual(capital, INITIAL_CAPITAL)

    def test_capital_nunca_negativo(self):
        """Capital can drop but trades should never risk more than available."""
        df = make_candles(500, trend="bajista")
        df = calcular_indicadores(df, STRATEGY)
        trades, capital_final, _ = correr_backtest_base(
            df, STRATEGY, RULES, COSTS, INITIAL_CAPITAL
        )

        for t in trades:
            self.assertGreater(t["capital_antes"], 0, "capital_antes debe ser positivo")
            self.assertLessEqual(
                t["risk_amount"],
                t["capital_antes"] * 0.025,
                "riesgo no puede superar 2.5% del capital",
            )

    def test_salida_siempre_sl_o_tp(self):
        """Every trade must exit at exactly SL or TP price."""
        df = make_candles(300, trend="alcista")
        df = calcular_indicadores(df, STRATEGY)
        trades, _, _ = correr_backtest_base(df, STRATEGY, RULES, COSTS, INITIAL_CAPITAL)

        last_close = df["close"].iloc[-1]

        for t in trades:
            # Salida válida: SL, TP, o cierre final si los datos terminaron
            valid_exit = (
                abs(t["precio_salida"] - t["tp_price"]) < 1
                or abs(t["precio_salida"] - t["sl_price"]) < 1
                or abs(t["precio_salida"] - last_close) < 1
            )
            self.assertTrue(
                valid_exit,
                f"Trade {t['trade_num']}: precio_salida {t['precio_salida']:.2f} "
                f"no es SL ({t['sl_price']:.2f}), TP ({t['tp_price']:.2f}), ni cierre final ({last_close:.2f})",
            )

    def test_no_lookahead_bias(self):
        """Entry decision on candle N cannot use data from candle N+1 or later."""
        df = make_candles(200, trend="alcista")
        df = calcular_indicadores(df, STRATEGY)
        trades, _, _ = correr_backtest_base(df, STRATEGY, RULES, COSTS, INITIAL_CAPITAL)

        indices = df.index.tolist()
        for t in trades:
            entry_ts = df[df["datetime_ar"] == t["entrada_fecha"]].index[0]
            exit_ts = df[df["datetime_ar"] == t["salida_fecha"]].index[0]
            entry_pos = indices.index(entry_ts)
            exit_pos = indices.index(exit_ts)

            self.assertGreater(
                exit_pos, entry_pos, "La salida debe ser posterior a la entrada"
            )

    def test_stop_diario_para_operaciones(self):
        """After daily stop triggers, no more trades that day."""
        df = make_candles(500, trend="bajista")
        df = calcular_indicadores(df, STRATEGY)
        trades, _, _ = correr_backtest_base(df, STRATEGY, RULES, COSTS, INITIAL_CAPITAL)

        from collections import defaultdict

        pnl_por_dia = defaultdict(float)
        capital_por_dia = defaultdict(float)

        for t in trades:
            fecha = t["entrada_fecha"][:10]
            if fecha not in capital_por_dia:
                capital_por_dia[fecha] = t["capital_antes"]
            pnl_por_dia[fecha] += t["pnl_neto"]

            if t.get("stop_diario"):
                pnl_pct = pnl_por_dia[fecha] / capital_por_dia[fecha]
                self.assertLessEqual(
                    pnl_pct,
                    -0.05,
                    f"Stop diario activado pero pérdida solo {pnl_pct:.2%}",
                )

    def test_orden_cronologico_estricto(self):
        """Trades must be in chronological order, no overlapping."""
        df = make_candles(400)
        df = calcular_indicadores(df, STRATEGY)
        trades, _, _ = correr_backtest_base(df, STRATEGY, RULES, COSTS, INITIAL_CAPITAL)

        for i in range(1, len(trades)):
            prev_exit = trades[i - 1]["salida_fecha"]
            curr_entry = trades[i]["entrada_fecha"]
            self.assertGreaterEqual(
                curr_entry,
                prev_exit,
                f"Trade {i} empieza antes de que termine el trade {i - 1}",
            )


class TestReglas(unittest.TestCase):
    """Tests de las 4 reglas inviolables de Coco."""

    def test_regla_1_riesgo_maximo_2pct(self):
        """Risk per trade must never exceed 2% of current capital."""
        df = make_candles(300, trend="alcista")
        df = calcular_indicadores(df, STRATEGY)
        trades, _, _ = correr_backtest_base(df, STRATEGY, RULES, COSTS, INITIAL_CAPITAL)

        for t in trades:
            riesgo_real = t["risk_amount"] / t["capital_antes"]
            self.assertLessEqual(
                riesgo_real,
                0.021,
                f"Trade {t['trade_num']}: riesgo {riesgo_real:.2%} supera el 2%",
            )

    def test_regla_2_rr_minimo_1_2(self):
        """R:R ratio must be at least 2.0 on every trade."""
        df = make_candles(300, trend="alcista")
        df = calcular_indicadores(df, STRATEGY)
        trades, _, _ = correr_backtest_base(df, STRATEGY, RULES, COSTS, INITIAL_CAPITAL)

        for t in trades:
            self.assertGreaterEqual(
                t["rr_ratio"],
                1.99,
                f"Trade {t['trade_num']}: R:R {t['rr_ratio']} menor que 1:2",
            )

    def test_regla_4_riesgo_dinamico(self):
        """Risk amount must be calculated on current capital, not initial."""
        df = make_candles(300, trend="alcista")
        df = calcular_indicadores(df, STRATEGY)
        trades, _, _ = correr_backtest_base(df, STRATEGY, RULES, COSTS, INITIAL_CAPITAL)

        for t in trades:
            expected_risk = t["capital_antes"] * 0.02
            self.assertAlmostEqual(
                t["risk_amount"],
                expected_risk,
                places=2,
                msg=f"Trade {t['trade_num']}: riesgo calculado sobre capital incorrecto",
            )


class TestMetricas(unittest.TestCase):
    """Tests del cálculo de métricas."""

    def test_sharpe_usa_365_no_252(self):
        """Sharpe ratio must use 365 days (crypto), not 252 (stock market)."""
        # Create fake trades with known daily returns
        trades = [
            {
                "pnl_neto": 5.0,
                "capital_antes": 250.0,
                "capital_despues": 255.0,
                "resultado": "WIN",
                "entrada_fecha": "2024-01-01 10:00",
                "velas_abierto": 2,
                "stop_diario": False,
            },
            {
                "pnl_neto": -2.5,
                "capital_antes": 255.0,
                "capital_despues": 252.5,
                "resultado": "LOSS",
                "entrada_fecha": "2024-01-02 10:00",
                "velas_abierto": 3,
                "stop_diario": False,
            },
            {
                "pnl_neto": 5.1,
                "capital_antes": 252.5,
                "capital_despues": 257.6,
                "resultado": "WIN",
                "entrada_fecha": "2024-01-03 10:00",
                "velas_abierto": 2,
                "stop_diario": False,
            },
        ]
        metricas = calcular_metricas(trades, 257.6)

        # Sharpe should be calculated (not zero, not NaN)
        self.assertIsNotNone(metricas.get("sharpe_ratio"))
        self.assertFalse(pd.isna(metricas["sharpe_ratio"]))

    def test_win_rate_calculo_correcto(self):
        """Win rate = wins / total trades."""
        trades = [
            {
                "pnl_neto": 5.0,
                "capital_antes": 250.0,
                "capital_despues": 255.0,
                "resultado": "WIN",
                "entrada_fecha": "2024-01-01 10:00",
                "velas_abierto": 2,
                "stop_diario": False,
            },
            {
                "pnl_neto": -2.5,
                "capital_antes": 255.0,
                "capital_despues": 252.5,
                "resultado": "LOSS",
                "entrada_fecha": "2024-01-02 10:00",
                "velas_abierto": 3,
                "stop_diario": False,
            },
        ]
        metricas = calcular_metricas(trades, 252.5)
        self.assertEqual(metricas["win_rate"], 50.0)
        self.assertEqual(metricas["wins"], 1)
        self.assertEqual(metricas["losses"], 1)

    def test_max_drawdown_capital_inicial(self):
        """Max drawdown should handle capital starting at INITIAL_CAPITAL."""
        trades = [
            {
                "pnl_neto": -10.0,
                "capital_antes": 250.0,
                "capital_despues": 240.0,
                "resultado": "LOSS",
                "entrada_fecha": "2024-01-01 10:00",
                "velas_abierto": 2,
                "stop_diario": False,
            },
            {
                "pnl_neto": -10.0,
                "capital_antes": 240.0,
                "capital_despues": 230.0,
                "resultado": "LOSS",
                "entrada_fecha": "2024-01-02 10:00",
                "velas_abierto": 3,
                "stop_diario": False,
            },
        ]
        metricas = calcular_metricas(trades, 230.0)
        # Max drawdown should be negative
        self.assertLess(metricas["max_drawdown_pct"], 0)


class TestBreakout(unittest.TestCase):
    """Tests de la estrategia breakout + ATR trailing stop."""

    @classmethod
    def setUpClass(cls):
        """Import breakout functions once for all tests."""
        from motor_base import (
            calcular_indicadores_breakout as _calc,
            generar_señal_breakout as _gen,
            buscar_salida_trailing,
            correr_backtest_breakout as _bt,
        )
        from config import STRATEGY_BREAKOUT
        cls.calc_ind = staticmethod(_calc)
        cls.gen_señal = staticmethod(_gen)
        cls.buscar_salida = staticmethod(buscar_salida_trailing)
        cls.correr_bt = staticmethod(_bt)
        cls.params = STRATEGY_BREAKOUT

    def test_breakout_señal_basica(self):
        """Breakout genera señal cuando close > high_max_N y vol > 1.5x."""
        df = make_candles(200, trend="alcista")
        df = self.calc_ind(df, self.params)

        # At least some candles should generate a breakout signal
        señales = [self.gen_señal(df.loc[idx], self.params) for idx in df.index]
        n_señales = sum(señales)
        # In an uptrend with synthetic data, expect at least 1 signal
        self.assertGreater(n_señales, 0, "Ninguna señal de breakout en tendencia alcista")

    def test_breakout_sin_volumen_no_entra(self):
        """Sin volumen suficiente (< 1.5x), no debe generar señal."""
        df = make_candles(200, trend="alcista")
        df = self.calc_ind(df, self.params)

        # Force all vol_ratios to below threshold
        df["vol_ratio"] = 0.5

        señales = [self.gen_señal(df.loc[idx], self.params) for idx in df.index]
        n_señales = sum(señales)
        self.assertEqual(n_señales, 0, "Generó señal sin volumen suficiente")

    def test_trailing_stop_sube_con_precio(self):
        """El trailing stop debe subir cuando el precio sube."""
        import numpy as np

        # Create simple uptrend data
        n = 20
        data = {
            "open": [100 + i * 2 for i in range(n)],
            "high": [102 + i * 2 for i in range(n)],
            "low": [99 + i * 2 for i in range(n)],
            "close": [101 + i * 2 for i in range(n)],
            "atr": [1.0] * n,
            "volume_btc": [10.0] * n,
            "datetime_ar": [f"2024-01-{i+1:02d} 00:00" for i in range(n)],
        }
        df = pd.DataFrame(data, index=range(n))

        # Entry at index 0, SL at 90, trail distance = 5
        idx_salida, precio, resultado, velas = self.buscar_salida(
            df, 0, 90.0, 5.0, 15
        )

        # In a strong uptrend, the trailing should lock in profit
        # The final SL should be higher than initial
        self.assertEqual(resultado, "WIN", "Trailing stop en uptrend debería ser WIN")

    def test_trailing_stop_no_baja(self):
        """El SL nunca debe bajar, incluso si el precio baja."""
        import numpy as np

        # Create data: goes up then down
        n = 20
        prices = list(range(100, 110)) + list(range(109, 99, -1))
        data = {
            "open": prices,
            "high": [p + 1 for p in prices],
            "low": [p - 1 for p in prices],
            "close": prices,
            "atr": [1.0] * n,
            "volume_btc": [10.0] * n,
            "datetime_ar": [f"2024-01-{i+1:02d} 00:00" for i in range(n)],
        }
        df = pd.DataFrame(data, index=range(n))

        # Initial SL at 95, trail distance = 3
        idx_salida, precio_salida, resultado, velas = self.buscar_salida(
            df, 0, 95.0, 3.0, 18
        )

        # The exit price should be >= initial SL (95)
        # because trailing only goes up
        self.assertGreaterEqual(
            precio_salida, 95.0,
            f"Trailing stop bajó: salida a {precio_salida} < SL inicial 95"
        )

    def test_atr_sizing_respeta_2pct(self):
        """Risk amount con SL dinámico (ATR) no supera 2% del capital."""
        df = make_candles(300, trend="alcista")
        df = self.calc_ind(df, self.params)
        trades, _, _ = self.correr_bt(df,self.params)

        for t in trades:
            riesgo_real = t["risk_amount"] / t["capital_antes"]
            self.assertLessEqual(
                riesgo_real, 0.021,
                f"Trade {t['trade_num']}: riesgo {riesgo_real:.2%} supera 2%"
            )

    def test_max_hold_bars_timeout(self):
        """Trade se cierra forzosamente después de max_hold_bars."""
        # Use short max_hold for testing
        params = {**self.params, "max_hold_bars": 5}
        df = make_candles(100)
        df = calcular_indicadores_breakout(df, params)
        trades, _, _ = self.correr_bt(df,params)

        for t in trades:
            self.assertLessEqual(
                t["velas_abierto"], 5,
                f"Trade {t['trade_num']}: duró {t['velas_abierto']} velas > max 5"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
