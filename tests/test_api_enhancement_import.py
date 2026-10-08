"""Bloqueante 3.4.5: api_enhancement_routes no debe usar Query(regex=...):
está deprecado en FastAPI y falla con pydantic antiguo. Se usa pattern= o
validación en la función."""
import re
from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "backend" / "routes" / "api_enhancement_routes.py"


def test_no_queda_regex_en_query():
    codigo = RUTA.read_text(encoding="utf-8")
    assert not re.search(r"Query\([^)]*\bregex=", codigo, flags=re.S)


def test_modulo_importa():
    import backend.routes.api_enhancement_routes  # noqa: F401
