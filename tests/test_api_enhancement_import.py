"""Bloqueante 3.4.5: backend/routes/api_enhancement_routes.py no debe usar
Query(regex=...), que FastAPI marca como deprecado (y que falla con pydantic
antiguo). Debe usarse pattern=."""
import subprocess
import sys

CODIGO = (
    "import warnings\n"
    "from fastapi.exceptions import FastAPIDeprecationWarning as W\n"
    "warnings.simplefilter('error', W)\n"
    "import backend.routes.api_enhancement_routes\n"
)


def test_modulo_importa_sin_regex_deprecado():
    r = subprocess.run([sys.executable, "-c", CODIGO], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-800:]
