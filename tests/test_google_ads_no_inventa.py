"""Bloqueante 3.4.3 (Google Ads): el auditor en vivo no llama a la API real;
todas sus secciones son valores escritos a mano (ENABLED, USD, America/Los_Angeles...).
Debe reportar error explícito y no devolver una auditoría aparente."""
from whitebox.google_ads_live_auditor import GoogleAdsLiveAuditor

CONFIG = {
    "developer_token": "dev-token-simulado",
    "customer_id": "1234567890",
    "refresh_token": "refresh-simulado",
}


def test_sin_api_real_reporta_error_y_no_inventa_cuenta():
    r = GoogleAdsLiveAuditor().audit_client(1, CONFIG)
    assert "error" in r
    assert r["findings"].get("account", {}) == {}
    assert r["score"] == 0
