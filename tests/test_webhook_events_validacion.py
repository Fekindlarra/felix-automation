"""Bloqueante 3.4.5 (ampliado): pydantic 2.5 no aplica pattern= sobre List[str].
La validación de 'events' debe hacerse en la función, no en Query()."""
import re

from backend.routes.api_enhancement_routes import validar_eventos_webhook


def test_eventos_validos_pasan():
    assert validar_eventos_webhook(["anomaly.critical", "prediction.high"]) == ["anomaly.critical", "prediction.high"]


def test_evento_invalido_se_rechaza():
    import pytest
    with pytest.raises(ValueError):
        validar_eventos_webhook(["evento.inventado"])
