"""Auditor de Search Console: mide solo lo que devuelve la API, sin cifras inventadas.

Se usa una sesión falsa con respuestas simuladas (sin red ni credenciales).
"""
from whitebox.gsc_auditor import GSCAuditor, audit_gsc


class _Creds:
    valid = True
    token = "token-de-prueba"


class _Resp:
    def __init__(self, rows):
        self._rows = rows

    def raise_for_status(self):
        pass

    def json(self):
        return {"rows": self._rows}


class _Sesion:
    """Devuelve filas distintas según la dimensión pedida."""

    def __init__(self, consultas, paginas):
        self.consultas = consultas
        self.paginas = paginas

    def post(self, url, json, headers, timeout):
        if json["dimensions"] == ["query"]:
            return _Resp(self.consultas)
        return _Resp(self.paginas)


class _SesionCaida:
    def post(self, url, json, headers, timeout):
        raise ConnectionError("sin red")


CONSULTAS = [
    {"keys": ["taller mecanico buena mesa"], "clicks": 30, "impressions": 300, "ctr": 0.1, "position": 2.0},
    {"keys": ["talleres"], "clicks": 10, "impressions": 700, "ctr": 0.014, "position": 8.0},
]
PAGINAS = [
    {"keys": ["https://ejemplo.cl/"], "clicks": 35, "impressions": 900},
]


def test_sin_propiedad_no_mide_nada():
    r = GSCAuditor({}).audit()
    assert r["overall_score"] is None
    assert r["status"] == "sin_datos"
    assert r["metrics"] == {}


def test_mide_clics_impresiones_y_posicion_ponderada():
    r = GSCAuditor({"site_url": "https://ejemplo.cl/", "session": _Sesion(CONSULTAS, PAGINAS), "creds": _Creds()}).audit()
    m = r["metrics"]
    assert r["status"] == "medido"
    assert r["overall_score"] is None  # el puntaje no se inventa
    assert m["clics_top_consultas"] == 40
    assert m["impresiones_top_consultas"] == 1000
    assert m["ctr_top_consultas"] == 0.04
    # (2*300 + 8*700) / 1000 = 6.2
    assert m["posicion_media_ponderada"] == 6.2
    assert m["top_consultas"][0]["consulta"] == "taller mecanico buena mesa"
    assert m["top_paginas"][0]["url"] == "https://ejemplo.cl/"


def test_sin_filas_queda_sin_datos():
    r = GSCAuditor({"site_url": "https://ejemplo.cl/", "session": _Sesion([], []), "creds": _Creds()}).audit()
    assert r["status"] == "sin_datos"
    assert r["overall_score"] is None


def test_error_de_api_no_inventa_resultados():
    r = GSCAuditor({"site_url": "https://ejemplo.cl/", "session": _SesionCaida(), "creds": _Creds()}).audit()
    assert r["status"] == "sin_datos"
    assert "sin red" in r["motivo"]
    assert r["metrics"] == {}


def test_helper_audit_gsc_sin_credenciales():
    assert audit_gsc()["status"] == "sin_datos"
