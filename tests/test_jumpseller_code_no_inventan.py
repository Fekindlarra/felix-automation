"""Bloqueante 3.4.3 (Jumpseller y código): los auditores devolvían secciones
con valores escritos a mano (p.ej. secrets_exposed 0, vulnerable_dependencies 3,
headers y MFA en True). Sin medición real deben reportar error explícito."""
from whitebox.code_auditor import CodeAuditor
from whitebox.jumpseller_auditor import JumpsellerAuditor


def test_jumpseller_sin_medicion_reporta_error():
    r = JumpsellerAuditor().audit_client(1, {"store_id": "demo", "api_key": "k-simulada"})
    assert "error" in r
    assert r.get("score", 0) == 0
    assert r["findings"].get("security", {}) == {}


def test_codigo_sin_medicion_reporta_error():
    r = CodeAuditor().audit_client(1, {"repo_url": "https://example.com/repo.git"})
    assert "error" in r
    assert r.get("score", 0) == 0
    assert r["findings"].get("security", {}) == {}
