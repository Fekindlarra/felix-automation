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
        self.content = text.encode("utf-8")
        self.headers = {"Content-Type": "text/html; charset=utf-8", "X-Frame-Options": "DENY"}
        self._fallar = fallar

    def raise_for_status(self):
        if self._fallar:
            raise RuntimeError("HTTP 500")


def test_con_html_entrega_todas_las_secciones_sin_red():
    r = auditar_url("talleresenbuenamesa.cl", html=HTML)
    assert r["url"] == "https://talleresenbuenamesa.cl"
    assert r["origen_html"]["tipo"] == "archivo"
    s = r["secciones"]
    assert set(s) == {"seo", "tracking", "gtm", "quick", "plataforma"}
    assert s["quick"]["status"] == "medido"
    assert s["quick"]["website_url"] == "https://talleresenbuenamesa.cl"
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


def test_descarga_pasa_cabeceras_y_medidas_reales_a_seo():
    r = auditar_url("https://ejemplo.cl", fetch=lambda url, timeout, headers: _Resp(HTML))
    seo = r["secciones"]["seo"]["metrics"]
    assert seo["rendimiento"]["score"] is not None
    assert seo["seguridad"]["score"] is not None


def test_sin_descarga_seo_no_inventa_rendimiento_ni_seguridad():
    r = auditar_url("talleresenbuenamesa.cl", html=HTML)
    seo = r["secciones"]["seo"]["metrics"]
    assert seo["rendimiento"]["score"] is None
    assert seo["seguridad"]["score"] is None
    # El promedio sale solo de las secciones medidas (técnica y contenido).
    assert r["secciones"]["seo"]["overall_score"] is not None


def test_charset_meta_sin_name_no_se_marca_como_faltante():
    from auditors.seo_auditor import SEOAuditor
    html = '<html><head><meta charset="UTF-8"><title>Taller en Buena Mesa de Chile</title></head><body><h1>x</h1></body></html>'
    r = SEOAuditor().audit({"url": "https://ejemplo.cl", "html": html})
    issues = [f["issue"] for sec in r["metrics"].values() for f in sec.get("findings", [])]
    assert "Falta charset declaration" not in issues


def test_meta_description_corta_no_se_reporta_como_faltante():
    from auditors.quick_audit import QuickAuditor
    html = '<html><head><title>En buena mesa taller</title><meta name="viewport" content="x"><meta name="description" content="En buena mesa "></head><body><h1>x</h1></body></html>'
    r = QuickAuditor().analizar_html("https://ejemplo.cl", html, 1000)
    titulos = [f["title"] for f in r["findings"]]
    assert "⚠️ Meta Description Corta" in titulos
    assert "⚠️ Meta Description Faltante" not in titulos
