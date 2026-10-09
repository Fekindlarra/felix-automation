"""Bloqueante 3.4.2 (ESTADO_VERIFICADO_Y_PLAN.md):
ShopifyAuditor debe usar la firma real de ShopifyAPIClient.

Se usa autospec para que el mock tenga exactamente la firma y los métodos
del cliente real. Si el auditor pasa un argumento o llama un método que no
existe, el test falla, como ocurría antes.
"""
from unittest.mock import patch

from whitebox.shopify_api_client import ShopifyAPIClient
from whitebox.shopify_auditor import ShopifyAuditor


def test_get_or_create_client_usa_firma_real():
    with patch("whitebox.shopify_auditor.ShopifyAPIClient", autospec=True) as cls:
        instancia = cls.return_value
        instancia.health_check.return_value = True

        auditor = ShopifyAuditor()
        client = auditor._get_or_create_client("demo.myshopify.com", "shpat_test")

        assert client is not None
        cls.assert_called_once()
        _, kwargs = cls.call_args
        assert "timeout" not in kwargs  # la firma real no tiene ese parámetro
        instancia.health_check.assert_called()


def test_auditor_no_llama_metodos_inexistentes():
    import inspect
    import whitebox.shopify_auditor as mod

    codigo = inspect.getsource(mod)
    for nombre in ["validate_credentials", "get_analytics", "is_healthy"]:
        assert f".{nombre}(" not in codigo, nombre
    for nombre in ["health_check", "calculate_analytics"]:
        assert hasattr(ShopifyAPIClient, nombre), nombre
