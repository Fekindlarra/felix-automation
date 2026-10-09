"""Universal Analytics (UA-): obsoleto desde julio de 2023; se reporta aparte de GA4."""
from auditors.tracking_scripts_auditor import audit_tracking_scripts


def _titulos(html):
    r = audit_tracking_scripts("https://x.cl", html)
    return [f["title"] for f in r.get("findings", [])]


def test_ua_en_codigo_inline_se_detecta():
    html = "<script>ga('create', 'UA-52982126-1', 'auto');</script>"
    titulos = _titulos(html)
    assert any("Universal Analytics Detectado" in t for t in titulos)


def test_ua_en_analytics_js_se_detecta():
    html = '<script src="https://www.google-analytics.com/analytics.js"></script><script>ga("create","UA-123456-7")</script>'
    assert any("Universal Analytics Detectado" in t for t in _titulos(html))


def test_sin_ua_se_informa_no_detectado():
    html = "<html><body>sin nada</body></html>"
    assert any("Universal Analytics NO Detectado" in t for t in _titulos(html))
