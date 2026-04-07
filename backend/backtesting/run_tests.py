#!/usr/bin/env python3
# =============================================================================
# RUN_TESTS.PY — Ejecutar todos los tests del proyecto
#
# Uso: python run_tests.py
#
# Sale con código 0 si todos los tests pasan, 1 si alguno falla.
# =============================================================================

import unittest
import sys
import os

# Asegurar que el directorio scripts esté en el path
sys.path.insert(0, os.path.dirname(__file__))


def main():
    """Descubre y corre todos los tests."""
    loader = unittest.TestLoader()

    # Descubrir tests en scripts/tests/
    suite = loader.discover(
        start_dir=os.path.join(os.path.dirname(__file__), "tests"),
        pattern="test_*.py",
    )

    # Correr tests con verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE TESTS")
    print("=" * 70)
    print(f"  Tests corridos: {result.testsRun}")
    print(
        f"  Exitosos:       {result.testsRun - len(result.failures) - len(result.errors)}"
    )
    print(f"  Fallidos:       {len(result.failures)}")
    print(f"  Errores:        {len(result.errors)}")
    print("=" * 70)

    # Salir con código apropiado
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
