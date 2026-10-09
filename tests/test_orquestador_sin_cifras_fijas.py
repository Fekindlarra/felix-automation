"""Bloqueante 3.4.1 (ESTADO_VERIFICADO_Y_PLAN.md):
el orquestador no debe devolver puntajes fijos o de muestra como si fueran medidos.

Cuando no hay medición real, la auditoría debe reportarse como "sin_datos"
con overall_score None. Nunca un número inventado.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent


@pytest.fixture
def agent():
    return MultiPlatformAuditorAgent(orchestrator=MagicMock())


def _client(name, website=None):
    return SimpleNamespace(name=name, website=website)


def test_web_sin_medicion_no_devuelve_puntaje_fijo(agent):
    r1 = agent._compute_web_audit(_client("A"))
    r2 = agent._compute_web_audit(_client("B"))
    assert r1["overall_score"] is None
    assert r2["overall_score"] is None
    assert r1.get("status") == "sin_datos"


def test_facebook_sin_medicion_no_usa_muestra(agent):
    r = agent._compute_facebook_audit(_client("A"))
    assert r["overall_score"] is None
    assert r.get("status") == "sin_datos"


def test_google_sin_medicion_no_usa_muestra(agent):
    r = agent._compute_google_audit(_client("A"))
    assert r["overall_score"] is None
    assert r.get("status") == "sin_datos"


def test_seo_sin_url_no_usa_muestra(agent):
    r = agent._compute_seo_audit(_client("A", website=None))
    assert r["overall_score"] is None
    assert r.get("status") == "sin_datos"
