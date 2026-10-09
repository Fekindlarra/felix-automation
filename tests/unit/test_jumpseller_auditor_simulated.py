#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD Test: Jumpseller Auditor should not return simulated/fixed values
Blocker 3.4.4: Jumpseller auditor roto (returns hardcoded metrics)
- Should return error status when credentials are missing
- Should NOT return hardcoded values as if they were real audit data
- Simulated values include: puntaje 86, total_products 342, total_orders 245,
  revenue 8532150, configured integrations (Transbank, PayPal, Correos Chile),
  security metrics (0 critical, 0 high vulnerabilities)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whitebox.jumpseller_auditor import JumpsellerAuditor


class TestJumpsellerAuditorSimulated:
    """
    Test suite to ensure JumpsellerAuditor doesn't return simulated/fixed values
    when real credentials are not provided.
    """

    @pytest.fixture
    def auditor(self):
        """Create JumpsellerAuditor instance"""
        return JumpsellerAuditor()

    def test_audit_with_missing_credentials_returns_error(self, auditor):
        """
        RED: When credentials are missing, audit should return error status
        instead of returning hardcoded simulated data.
        """
        client_id = 1
        jumpseller_config = {
            "store_id": None,  # Missing
            "api_key": None  # Missing
        }

        result = auditor.audit_client(client_id, jumpseller_config)

        # Should return error status, not simulated data
        assert result.get("error") is not None or result.get("status") == "failed", \
            f"Should return error status when credentials missing, got: {result}"

        # Most importantly: should NOT have simulated products/transactions
        findings = result.get("findings", {})
        products = findings.get("products", {})
        transactions = findings.get("transactions", {})

        # Should not have hardcoded total_products=342
        assert products.get("total_products") != 342, \
            "Should not return hardcoded total_products=342"
        # Should not have hardcoded total_orders=245
        assert transactions.get("total_orders") != 245, \
            "Should not return hardcoded total_orders=245"

    def test_audit_with_invalid_credentials_returns_no_credentials(self, auditor):
        """
        RED: When credentials are invalid, audit should indicate this
        instead of returning simulated data (puntaje 86, 342 products, 245 orders).
        """
        client_id = 1
        jumpseller_config = {
            "store_id": "invalid",
            "api_key": "invalid_api_key"
        }

        result = auditor.audit_client(client_id, jumpseller_config)

        # Check that result doesn't contain hardcoded metrics
        score = result.get("score")

        # The hardcoded weighted score is approximately 86
        if score and "error" not in result:
            assert score != 86, \
                "Should not return hardcoded score 86 when credentials invalid"

    def test_audit_does_not_return_hardcoded_products(self, auditor):
        """
        RED: Audit should not return hardcoded products with fixed stats
        (total_products: 342, categories: 12, pricing with avg: 35000)
        """
        client_id = 1
        jumpseller_config = {
            "store_id": "tienda123",
            "api_key": "api_key_123"
        }

        with patch.object(auditor, '_validate_credentials', return_value=False):
            result = auditor.audit_client(client_id, jumpseller_config)

        products = result.get("findings", {}).get("products", {})

        # Should not return hardcoded values
        if products and "error" not in result:
            assert products.get("total_products") != 342, \
                "Should not return hardcoded total_products=342"
            assert products.get("categories") != 12, \
                "Should not return hardcoded categories=12"
            assert products.get("pricing", {}).get("average_price") != 35000, \
                "Should not return hardcoded average_price=35000"

    def test_audit_does_not_return_hardcoded_transactions(self, auditor):
        """
        RED: Audit should not return hardcoded transactions with fixed stats
        (total_orders: 245, revenue.total: 8532150, new_customers: 158)
        """
        client_id = 1
        jumpseller_config = {
            "store_id": "tienda123",
            "api_key": "api_key_123"
        }

        with patch.object(auditor, '_validate_credentials', return_value=False):
            result = auditor.audit_client(client_id, jumpseller_config)

        transactions = result.get("findings", {}).get("transactions", {})

        # Should not return hardcoded values
        if transactions and "error" not in result:
            assert transactions.get("total_orders") != 245, \
                "Should not return hardcoded total_orders=245"
            assert transactions.get("revenue", {}).get("total") != 8532150, \
                "Should not return hardcoded revenue.total=8532150"
            assert transactions.get("customer_metrics", {}).get("new_customers") != 158, \
                "Should not return hardcoded new_customers=158"

    def test_audit_does_not_return_hardcoded_integrations(self, auditor):
        """
        RED: Audit should not return hardcoded integrations with fixed providers
        (Transbank, Flow, PayPal, Correos de Chile, BluExpress, Mailchimp, etc.)
        """
        client_id = 1
        jumpseller_config = {
            "store_id": "tienda123",
            "api_key": "api_key_123"
        }

        with patch.object(auditor, '_validate_credentials', return_value=False):
            result = auditor.audit_client(client_id, jumpseller_config)

        integrations = result.get("findings", {}).get("integrations", {})

        # Should not return hardcoded integration providers
        if integrations and "error" not in result:
            payment_gateways = integrations.get("payment_gateways", [])

            # Check that it doesn't have the hardcoded list
            gateway_names = [gw.get("name") for gw in payment_gateways]
            if gateway_names:  # Only check if there's data
                assert "Transbank" not in gateway_names, \
                    "Should not return hardcoded Transbank integration"
                assert "PayPal" not in gateway_names, \
                    "Should not return hardcoded PayPal integration"

    def test_audit_does_not_return_hardcoded_security(self, auditor):
        """
        RED: Audit should not return hardcoded security metrics
        (vulnerabilities critical=0, high=0, medium=1, low=2)
        """
        client_id = 1
        jumpseller_config = {
            "store_id": "tienda123",
            "api_key": "api_key_123"
        }

        with patch.object(auditor, '_validate_credentials', return_value=False):
            result = auditor.audit_client(client_id, jumpseller_config)

        security = result.get("findings", {}).get("security", {})

        # Should not return hardcoded security values
        if security and "error" not in result:
            vulns = security.get("vulnerabilities", {})

            assert vulns.get("critical") != 0, \
                "Should not return hardcoded critical=0 vulnerabilities"
            assert vulns.get("high") != 0, \
                "Should not return hardcoded high=0 vulnerabilities"
            assert vulns.get("medium") != 1, \
                "Should not return hardcoded medium=1 vulnerabilities"

    def test_missing_credentials_returns_error_status(self, auditor):
        """
        GREEN: When credentials are missing or invalid, audit should return
        error status instead of simulated data.
        """
        client_id = 1
        jumpseller_config = {
            "store_id": None,
            "api_key": None
        }

        result = auditor.audit_client(client_id, jumpseller_config)

        # Should indicate credentials issue
        assert result.get("error") is not None or \
               result.get("status") == "failed", \
            f"Should return error when credentials missing, got: {result}"

    def test_invalid_api_key_returns_error(self, auditor):
        """
        GREEN: When API key is invalid format, should return error status
        instead of proceeding with hardcoded data.
        """
        client_id = 1
        jumpseller_config = {
            "store_id": "tienda123",
            "api_key": ""  # Empty API key
        }

        result = auditor.audit_client(client_id, jumpseller_config)

        # Should return error status
        assert result.get("error") is not None or \
               result.get("status") == "failed", \
            f"Should return error for empty api_key, got: {result}"
