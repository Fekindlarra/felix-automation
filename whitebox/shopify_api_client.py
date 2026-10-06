"""
Shopify API Client - FASE 14 Real Integration
Real-time data collection from Shopify stores
"""

import requests
import logging
import time
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac

logger = logging.getLogger(__name__)


class ShopifyAPIVersion:
    """Supported Shopify API versions"""
    LATEST = "2024-01"
    STABLE = "2023-10"


@dataclass
class ShopifyStore:
    """Shopify store credentials"""
    shop_domain: str
    access_token: str
    api_version: str = ShopifyAPIVersion.LATEST

    @property
    def base_url(self) -> str:
        """Get base URL for API calls"""
        return f"https://{self.shop_domain}/admin/api/{self.api_version}"

    @property
    def headers(self) -> Dict:
        """Get auth headers for requests"""
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }


class ShopifyRateLimiter:
    """Simple rate limiter for Shopify API (2 requests per second)"""

    def __init__(self, max_calls: int = 2, time_period: float = 1.0):
        """
        Initialize rate limiter

        Args:
            max_calls: Maximum calls allowed
            time_period: Time period in seconds
        """
        self.max_calls = max_calls
        self.time_period = time_period
        self.calls = []

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()

        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_period]

        # Check if we need to wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_period - (now - self.calls[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit hit, sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                now = time.time()
                self.calls = [call_time for call_time in self.calls if now - call_time < self.time_period]

        self.calls.append(now)


class ShopifyAPIClient:
    """Client for Shopify REST API with automatic retry and rate limiting"""

    def __init__(self, shop_domain: str, access_token: str, config: Dict = None):
        """
        Initialize Shopify API client

        Args:
            shop_domain: Shopify store domain (e.g., "mystore.myshopify.com")
            access_token: Shopify API access token (starts with "shpat_")
            config: Configuration dictionary
        """
        self.store = ShopifyStore(shop_domain, access_token)
        self.config = config or {}
        self.rate_limiter = ShopifyRateLimiter(max_calls=2, time_period=1.0)
        self.session = requests.Session()
        self.session.headers.update(self.store.headers)

        # Retry configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)

        # Webhook validation
        self.webhook_secret = self.config.get('webhook_secret', '')

        logger.info(f"Shopify API client initialized for {shop_domain}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Optional[Dict]:
        """
        Make API request with automatic retry and rate limiting

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., /orders.json)
            data: Request body data
            retry_count: Current retry attempt

        Returns:
            Response JSON or None on failure
        """
        self.rate_limiter.wait_if_needed()

        url = f"{self.store.base_url}{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(url, timeout=30)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=30)
            elif method == "PUT":
                response = self.session.put(url, json=data, timeout=30)
            elif method == "DELETE":
                response = self.session.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                logger.warning(f"Rate limited by Shopify, waiting {retry_after}s")

                if retry_count < self.max_retries:
                    time.sleep(retry_after)
                    return self._make_request(method, endpoint, data, retry_count + 1)
                else:
                    logger.error("Max retries exceeded for rate limit")
                    return None

            # Handle errors
            if response.status_code >= 400:
                logger.error(f"Shopify API error {response.status_code}: {response.text}")

                if response.status_code in [500, 502, 503] and retry_count < self.max_retries:
                    wait_time = self.retry_delay * (2 ** retry_count)  # Exponential backoff
                    logger.info(f"Server error, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    return self._make_request(method, endpoint, data, retry_count + 1)

                return None

            return response.json() if response.text else {}

        except requests.Timeout:
            logger.error("Shopify API request timeout")
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                time.sleep(wait_time)
                return self._make_request(method, endpoint, data, retry_count + 1)
            return None

        except Exception as e:
            logger.error(f"Shopify API request error: {e}")
            return None

    def get_orders(
        self,
        limit: int = 100,
        status: str = "any",
        fields: Optional[List[str]] = None,
        updated_after: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch orders from store

        Args:
            limit: Maximum orders to return (1-250)
            status: Order status filter (any, fulfilled, unfulfilled, etc.)
            fields: Specific fields to return
            updated_after: Only return orders updated after this date

        Returns:
            List of order dictionaries
        """
        try:
            limit = min(limit, 250)  # Shopify limit
            params = f"?limit={limit}&status={status}"

            if fields:
                fields_str = ",".join(fields)
                params += f"&fields={fields_str}"

            if updated_after:
                params += f"&updated_at_min={updated_after.isoformat()}"

            response = self._make_request("GET", f"/orders.json{params}")

            if response and "orders" in response:
                return response["orders"]

            logger.warning("No orders found in response")
            return []

        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []

    def get_orders_paginated(
        self,
        status: str = "any",
        updated_after: Optional[datetime] = None
    ):
        """
        Fetch orders with pagination support (generator)

        Args:
            status: Order status filter
            updated_after: Only return orders updated after this date

        Yields:
            Order dictionaries
        """
        try:
            url = f"/orders.json?limit=250&status={status}"

            if updated_after:
                url += f"&updated_at_min={updated_after.isoformat()}"

            while url:
                response = self._make_request("GET", url)

                if not response or "orders" not in response:
                    break

                for order in response["orders"]:
                    yield order

                # Check for next page
                link_header = response.get("Link", "")
                if "rel=\"next\"" in link_header:
                    # Extract next URL
                    url = None  # TODO: Parse Link header for next page
                else:
                    break

        except Exception as e:
            logger.error(f"Error paginating orders: {e}")

    def get_products(
        self,
        limit: int = 100,
        fields: Optional[List[str]] = None,
        updated_after: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch products from store

        Args:
            limit: Maximum products to return
            fields: Specific fields to return
            updated_after: Only return products updated after this date

        Returns:
            List of product dictionaries
        """
        try:
            limit = min(limit, 250)
            params = f"?limit={limit}"

            if fields:
                fields_str = ",".join(fields)
                params += f"&fields={fields_str}"

            if updated_after:
                params += f"&updated_at_min={updated_after.isoformat()}"

            response = self._make_request("GET", f"/products.json{params}")

            if response and "products" in response:
                return response["products"]

            return []

        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []

    def get_customers(self, limit: int = 100) -> List[Dict]:
        """Fetch customers from store"""
        try:
            limit = min(limit, 250)
            response = self._make_request("GET", f"/customers.json?limit={limit}")

            if response and "customers" in response:
                return response["customers"]

            return []

        except Exception as e:
            logger.error(f"Error fetching customers: {e}")
            return []

    def get_shop_info(self) -> Optional[Dict]:
        """Get shop information"""
        try:
            response = self._make_request("GET", "/shop.json")

            if response and "shop" in response:
                return response["shop"]

            return None

        except Exception as e:
            logger.error(f"Error fetching shop info: {e}")
            return None

    def calculate_analytics(self) -> Dict[str, Any]:
        """Calculate key analytics from store data"""
        try:
            orders = self.get_orders(limit=250, status="any")

            if not orders:
                return {
                    'total_orders': 0,
                    'total_revenue': 0,
                    'average_order_value': 0,
                    'conversion_rate': 0,
                    'repeat_customer_rate': 0
                }

            total_revenue = sum(float(o.get('total_price', 0)) for o in orders)
            customer_ids = [o.get('customer', {}).get('id') for o in orders if o.get('customer')]
            unique_customers = len(set(c for c in customer_ids if c))
            repeat_customers = len(customer_ids) - unique_customers

            return {
                'total_orders': len(orders),
                'total_revenue': round(total_revenue, 2),
                'average_order_value': round(total_revenue / len(orders), 2) if orders else 0,
                'conversion_rate': 0,  # Would need traffic data
                'repeat_customer_rate': round(repeat_customers / len(orders) * 100, 2) if orders else 0,
                'unique_customers': unique_customers,
                'most_recent_order': orders[0].get('created_at') if orders else None
            }

        except Exception as e:
            logger.error(f"Error calculating analytics: {e}")
            return {}

    def validate_webhook_signature(self, request_body: bytes, hmac_header: str) -> bool:
        """
        Validate Shopify webhook signature

        Args:
            request_body: Raw request body bytes
            hmac_header: HMAC from X-Shopify-Hmac-SHA256 header

        Returns:
            True if signature is valid
        """
        try:
            if not self.webhook_secret:
                logger.warning("Webhook secret not configured")
                return False

            computed_hmac = hmac.new(
                self.webhook_secret.encode(),
                request_body,
                hashlib.sha256
            ).digest()

            computed_b64 = __import__('base64').b64encode(computed_hmac).decode()

            return hmac.compare_digest(computed_b64, hmac_header)

        except Exception as e:
            logger.error(f"Error validating webhook: {e}")
            return False

    def register_webhook(
        self,
        topic: str,
        callback_url: str,
        description: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Register a webhook in Shopify

        Args:
            topic: Webhook topic (e.g., "orders/created")
            callback_url: URL to send webhook to
            description: Optional description

        Returns:
            Webhook data or None on failure
        """
        try:
            data = {
                "webhook": {
                    "topic": topic,
                    "address": callback_url,
                    "format": "json"
                }
            }

            if description:
                data["webhook"]["description"] = description

            response = self._make_request("POST", "/webhooks.json", data)

            if response and "webhook" in response:
                logger.info(f"Webhook registered: {topic}")
                return response["webhook"]

            return None

        except Exception as e:
            logger.error(f"Error registering webhook: {e}")
            return None

    def get_webhooks(self) -> List[Dict]:
        """Get all registered webhooks"""
        try:
            response = self._make_request("GET", "/webhooks.json")

            if response and "webhooks" in response:
                return response["webhooks"]

            return []

        except Exception as e:
            logger.error(f"Error fetching webhooks: {e}")
            return []

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        try:
            response = self._make_request("DELETE", f"/webhooks/{webhook_id}.json")
            if response:
                logger.info(f"Webhook deleted: {webhook_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False

    def health_check(self) -> bool:
        """Check if API connection is working"""
        try:
            shop_info = self.get_shop_info()
            if shop_info:
                logger.info(f"API health check passed for {shop_info.get('name')}")
                return True
            return False

        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    client = ShopifyAPIClient(
        shop_domain="example.myshopify.com",
        access_token="shpat_example_token"
    )

    # Health check
    if client.health_check():
        print("✓ Connected to Shopify")

        # Get shop info
        shop = client.get_shop_info()
        print(f"\nShop: {shop.get('name')}")
        print(f"URL: {shop.get('myshopify_domain')}")

        # Get analytics
        analytics = client.calculate_analytics()
        print(f"\nAnalytics:")
        print(f"  Total Orders: {analytics.get('total_orders')}")
        print(f"  Total Revenue: ${analytics.get('total_revenue')}")
        print(f"  Avg Order Value: ${analytics.get('average_order_value')}")
        print(f"  Repeat Customer Rate: {analytics.get('repeat_customer_rate')}%")
    else:
        print("✗ Failed to connect to Shopify")
