"""
Pruebas del cliente de Search Console con cuenta de servicio.
No llaman a Google: usan credenciales y respuestas simuladas.
"""
import os
from datetime import date
from unittest import mock

import pytest

from whitebox import gsc_service_client as gsc


class FakeCreds:
    def __init__(self, valid=True, token="tok-123"):
        self.valid = valid
        self.token = token
        self.refreshed = False

    def refresh(self, _request):
        self.refreshed = True
        self.valid = True


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, payload=None, status=200):
        self.calls = []
        self._payload = payload if payload is not None else {"rows": []}
        self._status = status

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return FakeResponse(self._payload, self._status)


def test_date_window_ends_lag_days_before_today():
    start, end = gsc.date_window(days=28, lag_days=3, today=date(2026, 10, 8))
    assert end == "2026-10-05"
    assert start == "2026-09-07"


def test_query_uses_bearer_token_and_encoded_site_url():
    creds = FakeCreds(valid=True, token="abc")
    session = FakeSession({"rows": [{"keys": ["taller"], "clicks": 3}]})
    data = gsc.query_search_analytics(
        "https://www.talleresenbuenamesa.cl/", {"dimensions": ["query"]}, creds=creds, session=session
    )
    call = session.calls[0]
    assert call["headers"] == {"Authorization": "Bearer abc"}
    assert "https%3A%2F%2Fwww.talleresenbuenamesa.cl%2F" in call["url"]
    assert call["url"].endswith("/searchAnalytics/query")
    assert data["rows"][0]["clicks"] == 3


def test_expired_token_is_refreshed_before_request():
    creds = FakeCreds(valid=False, token="nuevo")
    session = FakeSession()
    gsc.query_search_analytics("sc-domain:ejemplo.cl", {}, creds=creds, session=session)
    assert creds.refreshed is True
    assert session.calls[0]["headers"]["Authorization"] == "Bearer nuevo"


def test_http_error_is_raised_not_swallowed():
    creds = FakeCreds()
    session = FakeSession(status=403)
    with pytest.raises(RuntimeError):
        gsc.query_search_analytics("https://ejemplo.cl/", {}, creds=creds, session=session)


def test_top_queries_builds_body_and_returns_rows():
    creds = FakeCreds()
    session = FakeSession({"rows": [{"keys": ["reparacion auto"], "clicks": 12}]})
    rows = gsc.top_queries(
        "https://www.talleresenbuenamesa.cl/", days=28, limit=5,
        creds=creds, session=session, today=date(2026, 10, 8),
    )
    body = session.calls[0]["json"]
    assert body["dimensions"] == ["query"]
    assert body["rowLimit"] == 5
    assert body["endDate"] == "2026-10-05"
    assert rows == [{"keys": ["reparacion auto"], "clicks": 12}]


def test_top_pages_uses_page_dimension():
    creds = FakeCreds()
    session = FakeSession()
    gsc.top_pages("https://ejemplo.cl/", creds=creds, session=session, today=date(2026, 10, 8))
    assert session.calls[0]["json"]["dimensions"] == ["page"]


def test_load_credentials_requires_path(monkeypatch):
    monkeypatch.delenv(gsc.ENV_KEY_FILE, raising=False)
    with pytest.raises(RuntimeError, match="GSC_SERVICE_ACCOUNT_FILE"):
        gsc.load_credentials()


def test_load_credentials_reads_env_path(monkeypatch):
    monkeypatch.setenv(gsc.ENV_KEY_FILE, "/ruta/falsa.json")
    with mock.patch.object(gsc.service_account.Credentials, "from_service_account_file") as loader:
        gsc.load_credentials()
    loader.assert_called_once_with("/ruta/falsa.json", scopes=[gsc.SCOPE])


def test_scope_is_read_only():
    assert gsc.SCOPE.endswith("webmasters.readonly")
