"""
Pruebas de métricas de audiencia y contenido de Meta (Instagram y Facebook Ads).
No llaman a Meta: usan respuestas simuladas.
"""
from unittest import mock

import requests

from whitebox.instagram_auditor import InstagramAuditor
from whitebox.facebook_ads_live_auditor import FacebookAdsLiveAuditor


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class RouterSession:
    """Responde según la ruta pedida. Las rutas no definidas devuelven 400."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params or {}})
        # Rutas más específicas primero (p. ej. "p1/insights" antes que "/insights")
        for needle in sorted(self.routes, key=len, reverse=True):
            payload = self.routes[needle]
            if needle in url:
                if isinstance(payload, Exception):
                    raise payload
                return FakeResponse(payload)
        return FakeResponse({"error": "no route"}, status=400)


IG_CREDS = {"access_token": "tok", "instagram_business_account_id": "17841"}


def test_instagram_without_credentials_returns_waiting_status():
    report = InstagramAuditor().audit()
    assert report["status"] == "WAITING_FOR_CREDENTIALS"
    assert report["summary"]["can_audit"] is False


def test_instagram_demographics_one_call_per_breakdown():
    session = RouterSession({
        "/insights": {"data": [{"total_value": {"breakdowns": [
            {"results": [{"dimension_values": ["25-34"], "value": 120}]}
        ]}}]},
        "/media": {"data": []},
    })
    report = InstagramAuditor(IG_CREDS, session=session).audit()
    breakdowns_asked = [c["params"].get("breakdown") for c in session.calls if c["params"].get("metric") == "follower_demographics"]
    assert breakdowns_asked == ["age", "gender", "city", "country"]
    assert report["audience_data"]["age"] == {"25-34": 120}


def test_instagram_uses_graph_facebook_host_not_instagram_host():
    session = RouterSession({"/media": {"data": []}, "/insights": {"data": []}})
    InstagramAuditor(IG_CREDS, session=session).audit()
    assert all(c["url"].startswith("https://graph.facebook.com/") for c in session.calls)


def test_instagram_content_collects_post_metrics_and_groups_by_type():
    session = RouterSession({
        "/insights": {"data": []},
        "/media": {"data": [
            {"id": "p1", "media_type": "REELS", "like_count": 40, "comments_count": 3,
             "caption": "Frenos en 30 min", "timestamp": "2026-09-20T10:00:00+0000"},
        ]},
        "p1/insights": {"data": [
            {"name": "reach", "values": [{"value": 900}]},
            {"name": "saved", "values": [{"value": 25}]},
        ]},
    })
    report = InstagramAuditor(IG_CREDS, session=session).audit()
    post = report["content_data"]["posts"][0]
    assert post["reach"] == 900 and post["saved"] == 25 and post["likes"] == 40
    assert report["content_data"]["by_media_type"]["REELS"]["posts"] == 1


def test_instagram_failed_section_is_reported_and_others_continue():
    session = RouterSession({
        "/insights": requests.HTTPError("403"),
        "/media": {"data": []},
    })
    report = InstagramAuditor(IG_CREDS, session=session).audit()
    titles = [f["title"] for f in report["findings"]]
    assert any("No se pudo leer" in t for t in titles)
    assert "content_data" in report


def test_facebook_host_is_graph_facebook():
    assert FacebookAdsLiveAuditor.GRAPH_API_URL.startswith("https://graph.facebook.com/")


def test_facebook_demographics_requests_each_breakdown():
    auditor = FacebookAdsLiveAuditor()
    auditor.access_token = "tok"
    auditor.ad_account_id = "act_1"
    audit_result = {"findings": {"issues": []}}
    with mock.patch("whitebox.facebook_ads_live_auditor.requests.get") as get:
        get.return_value = mock.Mock(status_code=200, raise_for_status=lambda: None,
                                     json=lambda: {"data": [{"impressions": "10"}]})
        auditor._audit_demographics(audit_result)
    breakdowns = [c.kwargs["params"]["breakdowns"] for c in get.call_args_list]
    assert breakdowns == FacebookAdsLiveAuditor.DEMOGRAPHIC_BREAKDOWNS
    assert set(audit_result["findings"]["demographics"]) == set(FacebookAdsLiveAuditor.DEMOGRAPHIC_BREAKDOWNS)


def test_facebook_adset_interests_come_from_configured_targeting():
    auditor = FacebookAdsLiveAuditor()
    auditor.access_token = "tok"
    auditor.ad_account_id = "act_1"
    adsets = [
        {"id": "s1", "status": "ACTIVE", "targeting": {
            "genders": [2],
            "geo_locations": {"regions": [{"name": "Metropolitana"}], "countries": ["CL"]},
            "flexible_spec": [{"interests": [{"name": "Autos"}, {"name": "Mantención"}]}],
        }},
        {"id": "s2", "status": "PAUSED", "targeting": {
            "flexible_spec": [{"interests": [{"name": "Autos"}]}],
        }},
    ]
    audit_result = {"findings": {"issues": [], "recommendations": []}}
    with mock.patch("whitebox.facebook_ads_live_auditor.requests.get") as get:
        get.return_value = mock.Mock(status_code=200, raise_for_status=lambda: None,
                                     json=lambda: {"data": adsets})
        auditor._audit_adsets(audit_result)
    stats = audit_result["findings"]["adsets"]
    assert tuple(stats["configured_interests"][0]) == ("Autos", 2)
    assert stats["configured_genders"] == ["mujeres"]
    assert "Metropolitana" in stats["configured_geo"] and "CL" in stats["configured_geo"]
