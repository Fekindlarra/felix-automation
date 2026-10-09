"""Auditoría de una URL: un solo flujo, sin red (HTML inyectado o descarga simulada)."""
from auditors.auditoria_url import auditar_url

HTML = """<html><head>
<title>Talleres en Buena Mesa</title>
<meta name="viewport" content="width=device-width">
<meta name="description" content="Taller mecánico en Buena Mesa">
<link rel="preconnect" href="https://images.jumpseller.com">
<script>window.dataLayer = window.dataLayer || [];</script>
<script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABC123"></script>
</head><body><h1>Taller</h1></body></html>"""


class _Resp:
    def __init__(self, text, fallar=False):
        self.text = text
        self._fallar = fallar

    def raise_for_status(self):
        if self._fallar:
            raise RuntimeError("HTTP 500")


def test_con_html_entrega_todas_las_secciones_sin_red():
    r = auditar_url("talleresenbuenamesa.cl", html=HTML)
    assert r["url"] == "https://talleresenbuenamesa.cl"
    assert r["origen_html"]["tipo"] == "archivo"
    s = r["secciones"]
    assert set(s) == {"seo", "tracking", "gtm", "plataforma"}
    assert s["gtm"]["metrics"]["contenedores"] == ["GTM-ABC123"]
    assert [d["platform"] for d in s["plataforma"]["detectadas"]] == ["jumpseller"]
    assert s["seo"]["status"] == "medido"
    assert s["tracking"]["status"] == "medido"


def test_descarga_fallida_deja_todo_sin_datos():
    def fetch_caido(url, timeout, headers):
        raise ConnectionError("sin red")
    r = auditar_url("https://ejemplo.cl", fetch=fetch_caido)
    assert r["origen_html"]["status"] == "error"
    for seccion in r["secciones"].values():
        assert seccion["status"] == "sin_datos"
        assert "sin red" in seccion["motivo"]


def test_descarga_ok_usa_el_html_descargado():
    llamadas = []
    def fetch(url, timeout, headers):
        llamadas.append(url)
        return _Resp(HTML)
    r = auditar_url("https://ejemplo.cl", fetch=fetch)
    assert llamadas == ["https://ejemplo.cl"]
    assert r["origen_html"]["status"] == "ok"
    assert r["secciones"]["gtm"]["metrics"]["cantidad_contenedores"] == 1


def test_http_500_se_trata_como_error():
    r = auditar_url("https://ejemplo.cl", fetch=lambda url, timeout, headers: _Resp("", fallar=True))
    assert r["origen_html"]["status"] == "error"
    assert r["secciones"]["seo"]["status"] == "sin_datos"
