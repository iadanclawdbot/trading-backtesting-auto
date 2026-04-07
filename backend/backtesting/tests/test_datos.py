# =============================================================================
# TESTS DE INTEGRIDAD DE DATOS
# test_datos.py
#
# Verifica que los datos en coco_lab.db cumplan con los requisitos
# mínimos para un backtest confiable.
#
# NOTA: Los datos empiezan en 2023-12-31 21:00, no en 2024-01-01.
# Los tests NO asumen un año específico.
# =============================================================================

import unittest
import pandas as pd
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import UNIFIED_DB
from fase1_motor import cargar_velas


class TestDatosCandles(unittest.TestCase):
    """Tests de integridad de datos históricos BTC/USDT 1H."""

    @classmethod
    def setUpClass(cls):
        """Load data once for all tests."""
        try:
            cls.df = cargar_velas(symbol="BTCUSDT", timeframe="1h", dataset="train").reset_index()
            cls.data_loaded = len(cls.df) > 0
        except Exception as e:
            cls.df = None
            cls.data_loaded = False
            cls.load_error = str(e)

    def test_base_de_datos_existe(self):
        """Database file must exist."""
        self.assertTrue(
            os.path.exists(UNIFIED_DB), f"Base de datos no encontrada: {UNIFIED_DB}"
        )

    def test_tabla_candles_train_existe(self):
        """BTCUSDT/1h/train must exist and have data."""
        self.assertTrue(
            self.data_loaded,
            f"Error cargando datos: {getattr(self, 'load_error', 'unknown')}",
        )
        self.assertIsNotNone(self.df)
        self.assertGreater(len(self.df), 0, "BTCUSDT/1h/train está vacía")

    def test_cantidad_velas_minima(self):
        """At least 6000 candles for a meaningful backtest."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        self.assertGreater(
            len(self.df),
            6000,
            f"Solo {len(self.df)} velas — insuficiente para backtest",
        )

    def test_columnas_requeridas(self):
        """All required columns must exist."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        required = [
            "timestamp",
            "datetime_ar",
            "open",
            "high",
            "low",
            "close",
            "volume_btc",
        ]
        for col in required:
            self.assertIn(
                col, self.df.columns, f"Columna requerida '{col}' no encontrada"
            )

    def test_sin_precios_nulos(self):
        """Price columns must not have null values."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        for col in ["open", "high", "low", "close"]:
            nulls = self.df[col].isnull().sum()
            self.assertEqual(nulls, 0, f"Columna {col} tiene {nulls} nulls")

    def test_sin_precios_cero(self):
        """Price columns must not have zero values."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        for col in ["open", "high", "low", "close"]:
            zeros = (self.df[col] == 0).sum()
            self.assertEqual(zeros, 0, f"Columna {col} tiene {zeros} ceros")

    def test_high_mayor_que_low(self):
        """high must always be >= low (impossible otherwise)."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        bad = self.df[self.df["high"] < self.df["low"]]
        self.assertEqual(len(bad), 0, f"{len(bad)} velas tienen high < low (imposible)")

    def test_open_close_dentro_rango(self):
        """open and close must be within [low, high] range."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        bad_open = self.df[
            (self.df["open"] > self.df["high"]) | (self.df["open"] < self.df["low"])
        ]
        bad_close = self.df[
            (self.df["close"] > self.df["high"]) | (self.df["close"] < self.df["low"])
        ]
        self.assertEqual(
            len(bad_open), 0, f"{len(bad_open)} velas con open fuera de [low, high]"
        )
        self.assertEqual(
            len(bad_close), 0, f"{len(bad_close)} velas con close fuera de [low, high]"
        )

    def test_orden_cronologico(self):
        """Timestamps must be in ascending order."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        ts = self.df["timestamp"].tolist()
        for i in range(1, len(ts)):
            self.assertLess(ts[i - 1], ts[i], f"Velas fuera de orden en posición {i}")

    def test_gaps_maximos(self):
        """No gap should be larger than 4 hours (2 missing candles max)."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        diffs = self.df["timestamp"].diff().dropna()
        max_gap_hours = diffs.max() / 3_600_000
        self.assertLess(
            max_gap_hours,
            4,
            f"Gap de {max_gap_hours:.1f}h detectado — posible corrupción de datos",
        )

    def test_sin_timestamps_duplicados(self):
        """No duplicate timestamps allowed."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        dups = self.df["timestamp"].duplicated().sum()
        self.assertEqual(dups, 0, f"{dups} timestamps duplicados")


class TestDatosValidacion(unittest.TestCase):
    """Tests para datos de validación BTCUSDT/1h/valid."""

    @classmethod
    def setUpClass(cls):
        """Load validation data."""
        try:
            cls.df = cargar_velas(symbol="BTCUSDT", timeframe="1h", dataset="valid").reset_index()
            cls.data_loaded = len(cls.df) > 0
        except Exception as e:
            cls.df = None
            cls.data_loaded = False
            cls.load_error = str(e)

    def test_candles_valid_existe(self):
        """BTCUSDT/1h/valid must exist."""
        self.assertTrue(
            self.data_loaded,
            f"Error cargando BTCUSDT/1h/valid: {getattr(self, 'load_error', 'unknown')}",
        )

    def test_candles_valid_cantidad_minima(self):
        """At least 1000 candles for meaningful validation."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        self.assertGreater(
            len(self.df),
            1000,
            f"Solo {len(self.df)} velas en validación — insuficiente",
        )


class TestDatosCandles4H(unittest.TestCase):
    """Tests de integridad de datos históricos BTC/USDT 4H."""

    @classmethod
    def setUpClass(cls):
        """Load data once for all tests."""
        try:
            cls.df = cargar_velas(symbol="BTCUSDT", timeframe="4h", dataset="train").reset_index()
            cls.data_loaded = len(cls.df) > 0
        except Exception as e:
            cls.df = None
            cls.data_loaded = False
            cls.load_error = str(e)

    def test_tabla_candles_train_4h_existe(self):
        """BTCUSDT/4h/train must exist and have data."""
        self.assertTrue(
            self.data_loaded,
            f"Error cargando datos 4H: {getattr(self, 'load_error', 'unknown')}",
        )
        self.assertIsNotNone(self.df)
        self.assertGreater(len(self.df), 0, "BTCUSDT/4h/train está vacía")

    def test_cantidad_velas_minima_4h(self):
        """At least 1500 candles for a meaningful 4H backtest."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        self.assertGreater(
            len(self.df),
            1500,
            f"Solo {len(self.df)} velas 4H — insuficiente para backtest",
        )

    def test_sin_precios_nulos_4h(self):
        """Price columns must not have null values."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        for col in ["open", "high", "low", "close"]:
            nulls = self.df[col].isnull().sum()
            self.assertEqual(nulls, 0, f"Columna {col} tiene {nulls} nulls")

    def test_gaps_maximos_4h(self):
        """No gap should be larger than 12 hours (2 missing 4H candles max)."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        diffs = self.df["timestamp"].diff().dropna()
        max_gap_hours = diffs.max() / 3_600_000
        self.assertLess(
            max_gap_hours,
            12.5,
            f"Gap de {max_gap_hours:.1f}h detectado en 4H — posible corrupción de datos",
        )


class TestDatosValidacion4H(unittest.TestCase):
    """Tests para datos de validación BTCUSDT/4h/valid."""

    @classmethod
    def setUpClass(cls):
        """Load validation data 4H."""
        try:
            cls.df = cargar_velas(symbol="BTCUSDT", timeframe="4h", dataset="valid").reset_index()
            cls.data_loaded = len(cls.df) > 0
        except Exception as e:
            cls.df = None
            cls.data_loaded = False
            cls.load_error = str(e)

    def test_candles_valid_4h_existe(self):
        """BTCUSDT/4h/valid must exist."""
        self.assertTrue(
            self.data_loaded,
            f"Error cargando BTCUSDT/4h/valid: {getattr(self, 'load_error', 'unknown')}",
        )

    def test_candles_valid_cantidad_minima_4h(self):
        """At least 250 candles for meaningful validation in 4H."""
        self.assertTrue(self.data_loaded, "Datos no cargados")
        self.assertGreater(
            len(self.df),
            250,
            f"Solo {len(self.df)} velas en validación 4H — insuficiente",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
