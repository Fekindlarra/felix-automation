"""Bloqueante 3.4.2 (resto): las secciones de ShopifyAuditor tenían valores
escritos a mano (desktop_score 75, bounce_rate 45.2, SSL valid, MFA...).
Sin medición real deben devolver status 'sin_datos'."""
from unittest.mock import MagicMock, patch

import pytest

from whitebox.shopify_auditor import ShopifyAuditor

SECCIONES = ["_audit_configuration", "_audit_performance", "_audit_security",
             "_audit_integrations", "_audit_seo"]


def _cliente_simulado():
    c = MagicMock()
    c.health_check.return_value = True
    c.calculate_analytics.return_value = {"total_orders": 5, "total_revenue": 100.0}
    c._make_request.return_value = {"shop": {"name": "Demo"}, "gateways": [], "installations": []}
    return c


@pytest.mark.parametrize("metodo", SECCIONES)
def test_seccion_sin_medicion_no_devuelve_valores_fijos(metodo):
    a = ShopifyAuditor()
    with patch.object(a, "_get_or_create_client", return_value=_cliente_simulado()):
        args = ("demo.myshopify.com",) if metodo == "_audit_seo" else ("demo.myshopify.com", "shpat_test")
        r = getattr(a, metodo)(*args)
    assert r.get("status") == "sin_datos", (metodo, r)
    for clave_fija in ["desktop_score", "bounce_rate", "uptime_percent", "meta_descriptions", "mobile_speed"]:
        assert clave_fija not in r, (metodo, clave_fija)
