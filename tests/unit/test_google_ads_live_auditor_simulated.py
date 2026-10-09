#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD Test: Google Ads Live Auditor should not return simulated/fixed values
Blocker 3.4.3: Google Ads en vivo simulado
- Should return no_credentials status when credentials are missing
- Should NOT return hardcoded values as if they were real audit data
- Simulated values include: campaigns (2 hardcoded), ad groups (8), keywords (245),
  quality scores, conversions (340), ROAS (3.5), conversion rate (4.2)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whitebox.google_ads_live_auditor import GoogleAdsLiveAuditor


class TestGoogleAdsLiveAuditorSimulated:
    """
    Test suite to ensure GoogleAdsLiveAuditor doesn't return simulated/fixed values
    when real credentials are not provided.
    """

    @pytest.fixture
    def auditor(self):
        """Create GoogleAdsLiveAuditor instance"""
        return GoogleAdsLiveAuditor()

    def test_audit_with_missing_credentials_returns_error(self, auditor):
        """
        RED: When credentials are missing, audit should return error status
        instead of returning hardcoded simulated data.
        """
        client_id = 1
        gads_config = {
            "customer_id": None,  # Missing
            "developer_token": None,  # Missing
            "refresh_token": None  # Missing
        }

        result = auditor.audit_client(client_id, gads_config)

        # Should return error status, not simulated data
        assert result.get("error") is not None or result.get("findings", {}).get("issues", [])
        # Most importantly: should NOT have simulated campaigns data
        campaigns = result.get("findings", {}).get("campaigns", {})
        assert campaigns.get("campaigns") is None or len(campaigns.get("campaigns", [])) == 0, \
            f"Should not return hardcoded campaigns, got: {campaigns}"

    def test_audit_with_invalid_credentials_returns_no_credentials(self, auditor):
        """
        RED: When credentials are invalid, audit should indicate this
        instead of returning simulated campaign data (2 hardcoded campaigns:
        'Summer Campaign 2024' and 'Display Remarketing' with fixed spend, impressions).
        """
        client_id = 1
        gads_config = {
            "customer_id": "invalid",
            "developer_token": "invalid_token",
            "refresh_token": "invalid_refresh"
        }

        result = auditor.audit_client(client_id, gads_config)

        # Check that result doesn't contain hardcoded "Summer Campaign 2024"
        campaigns = result.get("findings", {}).get("campaigns", {})
        if campaigns and campaigns.get("campaigns"):
            for campaign in campaigns["campaigns"]:
                assert campaign.get("name") != "Summer Campaign 2024", \
                    "Should not return hardcoded campaign name"
                assert campaign.get("name") != "Display Remarketing", \
                    "Should not return hardcoded campaign name"

    def test_audit_does_not_return_hardcoded_ad_groups(self, auditor):
        """
        RED: Audit should not return hardcoded ad_groups with fixed stats
        (total: 8, enabled: 7, paused: 1, avg_quality_score: 7.2)
        """
        client_id = 1
        gads_config = {
            "customer_id": "123456789",
            "developer_token": "dev_token",
            "refresh_token": "refresh_token"
        }

        with patch.object(auditor, '_init_client'):
            result = auditor.audit_client(client_id, gads_config)

        ad_groups = result.get("findings", {}).get("ad_groups", {})

        # The auditor should either return error or return no_credentials status
        # NOT hardcoded values like total=8, enabled=7
        if ad_groups and "error" not in result:
            # If not an error result, then should indicate no_credentials
            assert ad_groups.get("total") is None or \
                   "error" in str(result) or \
                   result.get("findings", {}).get("issues"), \
                f"Should not return hardcoded ad_groups, got: {ad_groups}"

    def test_audit_does_not_return_hardcoded_keywords(self, auditor):
        """
        RED: Audit should not return hardcoded keywords with fixed stats
        (total: 245, active: 220, search_volume_coverage: 0.76)
        """
        client_id = 1
        gads_config = {
            "customer_id": "123456789",
            "developer_token": "dev_token",
            "refresh_token": "refresh_token"
        }

        with patch.object(auditor, '_init_client'):
            result = auditor.audit_client(client_id, gads_config)

        keywords = result.get("findings", {}).get("keywords", {})

        # Should not return hardcoded values
        if keywords and "error" not in result:
            # The fixed value is exactly 245, so we check for it
            assert keywords.get("total") != 245, \
                "Should not return hardcoded keyword total (245)"

    def test_audit_does_not_return_hardcoded_quality_scores(self, auditor):
        """
        RED: Audit should not return hardcoded quality scores with fixed distribution
        (qs_10: 65, avg_quality_score: 8.1, expected_cpc: 1.25)
        """
        client_id = 1
        gads_config = {
            "customer_id": "123456789",
            "developer_token": "dev_token",
            "refresh_token": "refresh_token"
        }

        with patch.object(auditor, '_init_client'):
            result = auditor.audit_client(client_id, gads_config)

        qs = result.get("findings", {}).get("quality_scores", {})

        # Should not return hardcoded values
        if qs and "error" not in result:
            # The fixed values that appear in current code
            assert qs.get("qs_10") != 65, \
                "Should not return hardcoded qs_10 value (65)"
            assert qs.get("avg_quality_score") != 8.1, \
                "Should not return hardcoded avg_quality_score (8.1)"

    def test_audit_does_not_return_hardcoded_performance_metrics(self, auditor):
        """
        RED: Audit should not return hardcoded performance metrics
        (conversions: 340, conversion_rate: 4.2, roas: 3.5)
        """
        client_id = 1
        gads_config = {
            "customer_id": "123456789",
            "developer_token": "dev_token",
            "refresh_token": "refresh_token"
        }

        with patch.object(auditor, '_init_client'):
            result = auditor.audit_client(client_id, gads_config)

        performance = result.get("findings", {}).get("performance", {})

        # Should not return these exact hardcoded values
        if performance and "error" not in result:
            assert performance.get("conversions") != 340, \
                "Should not return hardcoded conversions (340)"
            assert performance.get("conversion_rate") != 4.2, \
                "Should not return hardcoded conversion_rate (4.2)"
            assert performance.get("roas") != 3.5, \
                "Should not return hardcoded roas (3.5)"

    def test_missing_credentials_returns_status_no_credentials(self, auditor):
        """
        GREEN: When credentials are missing or invalid, audit should return
        a result with status='no_credentials' or error field indicating
        that real data is not available.
        """
        client_id = 1
        gads_config = {
            "customer_id": None,
            "developer_token": None,
            "refresh_token": None
        }

        result = auditor.audit_client(client_id, gads_config)

        # Should indicate credentials issue
        assert "error" in result or \
               result.get("findings", {}).get("issues") is not None, \
            f"Should return error when credentials missing, got: {result}"

        # Should have overall_score=None to indicate no real audit
        # OR should have status field indicating the issue
        assert result.get("overall_score") is None or \
               "error" in result or \
               "Configuración" in str(result.get("error", "")), \
            f"Should indicate no credentials, got: {result}"
