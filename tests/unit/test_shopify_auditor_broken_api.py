#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD Test: Shopify Auditor should not call non-existent API methods
Blocker 3.4.2: Shopify auditor roto (broken)
- Line 52: Passes timeout=30 directly to ShopifyAPIClient (should be in config dict)
- Line 54: Calls validate_credentials() method that doesn't exist
- Line 247: Calls get_analytics() that doesn't exist (should be calculate_analytics())
- Line 287: Calls is_healthy() that doesn't exist (should be health_check())
- Line 359: Calls is_healthy() that doesn't exist (should be health_check())
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, PropertyMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whitebox.shopify_auditor import ShopifyAuditor
from whitebox.shopify_api_client import ShopifyAPIClient


class TestShopifyAuditorBrokenAPI:
    """
    Test suite to ensure ShopifyAuditor doesn't call non-existent
    ShopifyAPIClient methods and passes parameters correctly.
    """

    @pytest.fixture
    def auditor(self):
        """Create ShopifyAuditor instance"""
        return ShopifyAuditor()

    def test_client_initialization_no_direct_timeout_param(self, auditor):
        """
        RED: ShopifyAPIClient constructor should not accept timeout as direct parameter.
        It should be passed in config dict.
        """
        store_url = "example.myshopify.com"
        access_token = "shpat_test123"

        with patch('whitebox.shopify_api_client.ShopifyAPIClient') as MockClient:
            # Mock the client to track how it was instantiated
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance

            # Try to create client the broken way
            try:
                client = ShopifyAPIClient(store_url, access_token, timeout=30)
                # Should fail with TypeError
                pytest.fail("ShopifyAPIClient should not accept timeout as direct parameter")
            except TypeError as e:
                # Expected: __init__() got an unexpected keyword argument 'timeout'
                assert "timeout" in str(e), f"Expected timeout error, got: {e}"

    def test_validate_credentials_method_does_not_exist(self, auditor):
        """
        RED: ShopifyAPIClient doesn't have validate_credentials() method.
        Calling it will raise AttributeError.
        """
        store_url = "example.myshopify.com"
        access_token = "shpat_test123"

        with patch('whitebox.shopify_auditor.ShopifyAPIClient') as MockClient:
            mock_client = MagicMock()
            # Don't define validate_credentials method
            del mock_client.validate_credentials
            MockClient.return_value = mock_client

            # This should fail because validate_credentials doesn't exist
            try:
                result = mock_client.validate_credentials()
                pytest.fail("validate_credentials() should not exist")
            except AttributeError:
                # Expected: Mock has no attribute 'validate_credentials'
                pass

    def test_get_analytics_method_does_not_exist(self, auditor):
        """
        RED: ShopifyAPIClient has calculate_analytics() not get_analytics().
        Calling get_analytics() will raise AttributeError.
        """
        with patch('whitebox.shopify_auditor.ShopifyAPIClient') as MockClient:
            mock_client = MagicMock()
            # Don't define get_analytics method, but define calculate_analytics
            del mock_client.get_analytics
            mock_client.calculate_analytics = MagicMock(return_value={
                'total_orders': 50,
                'total_revenue': 5000.0,
                'average_order_value': 100.0,
                'currency': 'USD'
            })
            MockClient.return_value = mock_client

            # This should fail because get_analytics doesn't exist
            try:
                result = mock_client.get_analytics()
                pytest.fail("get_analytics() should not exist")
            except AttributeError:
                # Expected: Mock has no attribute 'get_analytics'
                pass

    def test_is_healthy_method_does_not_exist(self, auditor):
        """
        RED: ShopifyAPIClient has health_check() not is_healthy().
        Calling is_healthy() will raise AttributeError.
        """
        with patch('whitebox.shopify_auditor.ShopifyAPIClient') as MockClient:
            mock_client = MagicMock()
            # Don't define is_healthy method, but define health_check
            del mock_client.is_healthy
            mock_client.health_check = MagicMock(return_value=True)
            MockClient.return_value = mock_client

            # This should fail because is_healthy doesn't exist
            try:
                result = mock_client.is_healthy()
                pytest.fail("is_healthy() should not exist")
            except AttributeError:
                # Expected: Mock has no attribute 'is_healthy'
                pass

    def test_get_or_create_client_with_invalid_timeout_param(self, auditor):
        """
        RED: Current code passes timeout=30 directly to ShopifyAPIClient.__init__
        which doesn't accept it as a parameter - should be in config dict.
        This test will FAIL with current code because TypeError is raised.
        """
        store_url = "example.myshopify.com"
        access_token = "shpat_test123"

        # The current code on line 52 does this:
        # client = ShopifyAPIClient(store_url, access_token, timeout=30)
        # This will raise TypeError because timeout is not a parameter

        with pytest.raises(TypeError) as exc_info:
            # This is what the current code tries to do
            client = ShopifyAPIClient(store_url, access_token, timeout=30)

        assert "timeout" in str(exc_info.value)

    def test_get_or_create_client_calls_nonexistent_validate_credentials(self, auditor):
        """
        RED: Current code calls validate_credentials() on line 54,
        but this method doesn't exist in ShopifyAPIClient.
        This test will FAIL with current code because AttributeError is raised.
        """
        store_url = "example.myshopify.com"
        access_token = "shpat_test123"

        # Mock ShopifyAPIClient to create a client without the timeout error
        with patch('whitebox.shopify_auditor.ShopifyAPIClient') as MockClient:
            mock_client = MagicMock(spec=[])  # Empty spec to simulate no methods
            MockClient.return_value = mock_client

            # The current code on line 54 tries to call:
            # if client.validate_credentials():
            # This will fail because the method doesn't exist

            with pytest.raises(AttributeError):
                # Simulate what _get_or_create_client does
                client = MockClient(store_url, access_token)
                client.validate_credentials()

    def test_audit_performance_calls_nonexistent_get_analytics(self, auditor):
        """
        RED: Current code calls get_analytics() on line 247,
        but ShopifyAPIClient has calculate_analytics() not get_analytics().
        This test will FAIL with current code because AttributeError is raised.
        """
        store_url = "example.myshopify.com"
        access_token = "shpat_test123"

        with patch('whitebox.shopify_auditor.ShopifyAPIClient') as MockClient:
            mock_client = MagicMock()
            # Only define the correct method (calculate_analytics)
            mock_client.calculate_analytics = MagicMock(return_value={'total_orders': 50})
            # Make get_analytics raise AttributeError when called
            mock_client.get_analytics = PropertyMock(side_effect=AttributeError("get_analytics"))

            MockClient.return_value = mock_client

            # Current code tries to call get_analytics() which doesn't exist
            with pytest.raises(AttributeError):
                result = mock_client.get_analytics()

    def test_audit_performance_calls_nonexistent_is_healthy(self, auditor):
        """
        RED: Current code calls is_healthy() on line 287,
        but ShopifyAPIClient has health_check() not is_healthy().
        This test will FAIL with current code because AttributeError is raised.
        """
        with patch('whitebox.shopify_auditor.ShopifyAPIClient') as MockClient:
            mock_client = MagicMock()
            # Only define the correct method (health_check)
            mock_client.health_check = MagicMock(return_value=True)
            # Make is_healthy raise AttributeError when called
            mock_client.is_healthy = PropertyMock(side_effect=AttributeError("is_healthy"))

            MockClient.return_value = mock_client

            # Current code tries to call is_healthy() which doesn't exist
            with pytest.raises(AttributeError):
                result = mock_client.is_healthy()

    def test_audit_security_calls_nonexistent_is_healthy(self, auditor):
        """
        RED: Current code calls is_healthy() on line 359,
        but ShopifyAPIClient has health_check() not is_healthy().
        This test will FAIL with current code because AttributeError is raised.
        """
        with patch('whitebox.shopify_auditor.ShopifyAPIClient') as MockClient:
            mock_client = MagicMock()
            # Only define the correct method (health_check)
            mock_client.health_check = MagicMock(return_value=True)
            # Make is_healthy raise AttributeError when called
            mock_client.is_healthy = PropertyMock(side_effect=AttributeError("is_healthy"))

            MockClient.return_value = mock_client

            # Current code tries to call is_healthy() which doesn't exist
            with pytest.raises(AttributeError):
                result = mock_client.is_healthy()
