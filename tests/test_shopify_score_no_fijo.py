"""Bloqueante 3.4.2 (resto): el puntaje de Shopify no puede ser una constante
(79 siempre). Sin medición real, no hay puntaje: score None y error explícito."""
from whitebox.shopify_auditor import ShopifyAuditor


def test_score_no_depende_de_constantes():
    a = ShopifyAuditor()
    assert a._calculate_score({"configuration": {"x": 1}}) is None
    assert a._calculate_score({"configuration": {"x": 2}, "security": {"y": 9}}) is None
