#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shopify API Client - Real REST API Integration
FASE 14: Real-Time & ML Features
Manages connection pooling, rate limiting, error handling, webhooks
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for Shopify API (2 requests/second limit)"""

    def __init__(self, max_calls: int = 2, time_period: float = 1.0):
        self.max_calls = max_calls
        self.time_period = time_period
        self.calls = []

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = datetime.now()
        # Remove old calls outside the time window
        self.calls = [t for t in self.calls if (now - t).total_seconds() < self.time_period]

        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_period - (now - self.calls[0]).total_seconds()
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                import time
                time.sleep(sleep_time)

        self.calls.append(datetime.now())


class ShopifyAPIClient:
    """
    Shopify REST API Client with connection pooling, rate limiting, and error handling

    Supports:
    - Real REST API calls (OAuth token-based auth, "shpat_*" format)
    - Connection pooling for performance
    - Rate limiting (2 req/sec per Shopify API limits)
    - Retry logic with exponential backoff
    - Webhook validation and processing
    - Health checks and uptime monitoring
    """

    # Shopify API version
    API_VERSION = "2024-01"

    def __init__(self, shop_domain: str, access_token: str, timeout: int = 30):
        """
        Initialize Shopify API client

        Args:
            shop_domain: Shop domain (e.g., "myshop.myshopify.com")
            access_token: OAuth access token (format: "shpat_*")
            timeout: Request timeout in seconds
        """
        self.shop_domain = shop_domain.rstrip('/')
        self.access_token = access_token
        self.timeout = timeout
        self.base_url = f"https://{shop_domain}/admin/api/{self.API_VERSION}"

        # Setup session with connection pooling and retry logic
        self.session = self._create_session()
        self.rate_limiter = RateLimiter(max_calls=2, time_period=1.0)

        # Track health metrics
        self.last_successful_request = None
        self.error_count = 0
        self.success_count = 0

        logger.info(f"✅ Shopify API Client initialized for: {shop_domain}")

    def _create_session(self) -> requests.Session:
        """Create requests session with connection pooling and retry strategy"""
        session = requests.Session()

        # Setup retry strategy (exponential backoff)
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )

        # Mount adapters for HTTP and HTTPS with connection pooling
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set authorization header
        session.headers.update({
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        })

        return session

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Make API request with rate limiting and error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/orders.json")
            **kwargs: Additional arguments for requests

        Returns:
            Response JSON or None if error
        """
        self.rate_limiter.wait_if_needed()

        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )

            # Handle rate limit (429)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2))
                logger.warning(f"⚠️ Rate limited. Retrying after {retry_after}s")
                import time
                time.sleep(retry_after)
                return self._request(method, endpoint, **kwargs)

            response.raise_for_status()

            self.success_count += 1
            self.last_successful_request = datetime.now()

            if response.text:
                return response.json()
            return {"status": "success"}

        except requests.exceptions.Timeout:
            self.error_count += 1
            logger.error(f"❌ Timeout: {url}")
            return None
        except requests.exceptions.ConnectionError as e:
            self.error_count += 1
            logger.error(f"❌ Connection error: {str(e)}")
            return None
        except requests.exceptions.HTTPError as e:
            self.error_count += 1
            logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
            return None
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Unexpected error: {str(e)}")
            return None

    def validate_credentials(self) -> bool:
        """
        Validate that credentials work by calling a simple endpoint

        Returns:
            True if credentials are valid, False otherwise
        """
        logger.info("🧪 Validating Shopify credentials...")
        result = self._request("GET", "/shop.json")
        if result and "shop" in result:
            shop = result["shop"]
            logger.info(f"✅ Credentials valid. Shop: {shop.get('name')}")
            return True
        logger.error("❌ Invalid credentials")
        return False

    def get_orders(self, limit: int = 100, updated_after: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch orders from store

        Args:
            limit: Number of orders to fetch (max 250)
            updated_after: Only return orders updated after this datetime

        Returns:
            List of order dictionaries
        """
        logger.info(f"📦 Fetching orders (limit: {limit})...")

        params = {
            "limit": min(limit, 250),
            "status": "any"
        }

        if updated_after:
            params["updated_at_min"] = updated_after.isoformat()

        result = self._request("GET", "/orders.json", params=params)

        if result and "orders" in result:
            logger.info(f"✅ Fetched {len(result['orders'])} orders")
            return result["orders"]

        logger.warning("⚠️ No orders found or API error")
        return []

    def get_products(self, limit: int = 100, updated_after: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch products from store

        Args:
            limit: Number of products to fetch (max 250)
            updated_after: Only return products updated after this datetime

        Returns:
            List of product dictionaries
        """
        logger.info(f"📦 Fetching products (limit: {limit})...")

        params = {
            "limit": min(limit, 250),
            "status": "active"
        }

        if updated_after:
            params["updated_at_min"] = updated_after.isoformat()

        result = self._request("GET", "/products.json", params=params)

        if result and "products" in result:
            logger.info(f"✅ Fetched {len(result['products'])} products")
            return result["products"]

        logger.warning("⚠️ No products found or API error")
        return []

    def get_analytics(self) -> Dict[str, Any]:
        """
        Collect analytics data: revenue, conversion rate, top products

        Returns:
            Dictionary with analytics metrics
        """
        logger.info("📊 Collecting analytics...")

        analytics = {
            "total_revenue": 0,
            "total_orders": 0,
            "average_order_value": 0,
            "conversion_rate": 0,
            "top_products": [],
            "updated_at": datetime.now().isoformat()
        }

        try:
            # Get shop info
            shop_result = self._request("GET", "/shop.json")
            if shop_result and "shop" in shop_result:
                shop = shop_result["shop"]
                analytics["shop_name"] = shop.get("name")
                analytics["currency"] = shop.get("currency")

            # Get order data (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            orders = self.get_orders(limit=250, updated_after=thirty_days_ago)

            analytics["total_orders"] = len(orders)

            if orders:
                total_revenue = sum(float(o.get("total_price", 0)) for o in orders)
                analytics["total_revenue"] = total_revenue
                analytics["average_order_value"] = total_revenue / len(orders) if orders else 0

            # Get top products (by sales count)
            products_result = self._request("GET", "/products.json?limit=10")
            if products_result and "products" in products_result:
                products = sorted(
                    products_result["products"],
                    key=lambda p: sum(v.get("inventory_quantity", 0) for v in p.get("variants", [])),
                    reverse=True
                )[:5]
                analytics["top_products"] = [
                    {
                        "id": p.get("id"),
                        "title": p.get("title"),
                        "variants_count": len(p.get("variants", []))
                    }
                    for p in products
                ]

            logger.info(f"✅ Analytics collected: {analytics['total_orders']} orders, {analytics['total_revenue']} revenue")
            return analytics

        except Exception as e:
            logger.error(f"❌ Error collecting analytics: {str(e)}")
            return analytics

    def validate_webhook_signature(self, signature: str, body: bytes, secret: str) -> bool:
        """
        Validate webhook signature using HMAC-SHA256

        Args:
            signature: X-Shopify-Hmac-SHA256 header value
            body: Raw request body bytes
            secret: Webhook API secret

        Returns:
            True if signature is valid, False otherwise
        """
        import hmac
        import hashlib
        import base64

        try:
            computed_hmac = base64.b64encode(
                hmac.new(
                    secret.encode('utf-8'),
                    body,
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')

            return hmac.compare_digest(signature, computed_hmac)
        except Exception as e:
            logger.error(f"❌ Webhook signature validation error: {str(e)}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get client health metrics

        Returns:
            Dictionary with health information
        """
        uptime_percent = 0
        if self.success_count + self.error_count > 0:
            uptime_percent = (self.success_count / (self.success_count + self.error_count)) * 100

        return {
            "status": "healthy" if uptime_percent > 95 else "degraded" if uptime_percent > 80 else "unhealthy",
            "success_count": self.success_count,
            "error_count": self.error_count,
            "uptime_percent": round(uptime_percent, 2),
            "last_successful_request": self.last_successful_request.isoformat() if self.last_successful_request else None
        }

    def close(self):
        """Close the session and cleanup resources"""
        if self.session:
            self.session.close()
            logger.info("✅ Shopify API session closed")


def main():
    """Example usage"""
    # This would use real credentials in production
    shop_domain = "example.myshopify.com"
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN", "shpat_example")

    client = ShopifyAPIClient(shop_domain, access_token)

    # Validate credentials
    if client.validate_credentials():
        # Get data
        orders = client.get_orders(limit=10)
        print(f"Orders: {len(orders)}")

        analytics = client.get_analytics()
        print(f"Analytics: {json.dumps(analytics, indent=2)}")

        # Health check
        health = client.get_health_status()
        print(f"Health: {health}")

    client.close()


if __name__ == "__main__":
    main()
