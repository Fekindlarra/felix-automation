"""Revisión GTM desde HTML: solo hechos medidos, sin puntajes inventados."""
from auditors.gtm_html_auditor import auditar_gtm_html

SNIPPET = """
<script>window.dataLayer = window.dataLayer || [];
gtag('consent', 'default', {'analytics_storage': 'denied'});</script>
<script>(function(w,d,s,l,i){})(window,document,'script','dataLayer','GTM-ABC123');</script>
<script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABC123"></script>
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-ABC123"></iframe></noscript>
"""


def test_html_vacio_sin_datos():
    r = auditar_gtm_html("")
    assert r["status"] == "sin_datos"
    assert r["metrics"] == {}


def test_sin_gtm_no_inventa_contenedor():
    r = auditar_gtm_html("<html><body>hola</body></html>")
    m = r["metrics"]
    assert m["contenedores"] == []
    assert m["cantidad_contenedores"] == 0
    assert m["duplicado"] is False
    assert m["consent_mode_default"] is False
    assert r["overall_score"] is None


def test_snippet_completo_con_consent_mode():
    m = auditar_gtm_html(SNIPPET)["metrics"]
    assert m["contenedores"] == ["GTM-ABC123"]
    assert m["snippet_noscript_presente"] is True
    assert m["datalayer_presente"] is True
    assert m["consent_mode_default"] is True
    assert m["duplicado"] is False


def test_snippet_repetido_se_marca_duplicado():
    m = auditar_gtm_html(SNIPPET + SNIPPET)["metrics"]
    assert m["snippet_script_repeticiones"] == 2
    assert m["duplicado"] is True


def test_dos_contenedores_distintos_se_marcan_duplicado():
    html = SNIPPET + '<script src="https://www.googletagmanager.com/gtm.js?id=GTM-ZZZ999"></script>'
    m = auditar_gtm_html(html)["metrics"]
    assert m["cantidad_contenedores"] == 2
    assert m["duplicado"] is True
