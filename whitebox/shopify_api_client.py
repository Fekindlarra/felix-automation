#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 14: Shopify API Client
Real Shopify REST API integration with rate limiting and error handling
"""

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, max_calls: int, time_period: float):
        self.max_calls = max_calls
        self.time_period = time_period
        self.calls = []

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        # Remove old calls outside time period
        self.calls = [call_time for call_time in self.calls
                     if now - call_time < self.time_period]

        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_period - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.calls = []

        self.calls.append(now)


class ShopifyAPIClient:
    """Shopify REST API client with connection pooling and rate limiting"""

    def __init__(self, shop_domain: str, access_token: str, timeout: int = 30):
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.timeout = timeout
        self.base_url = f"https://{shop_domain}/admin/api/2024-01"

        # Connection pooling
        self.session = requests.Session()

        # Rate limiting: 2 requests per second
        self.rate_limiter = RateLimiter(max_calls=2, time_period=1.0)

        # Headers for authentication
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }

        logger.info(f"✅ Shopify API client initialized for {shop_domain}")

    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to Shopify API with rate limiting"""
        self.rate_limiter.wait_if_needed()

        url = f"{self.base_url}/{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(url, headers=self.headers)
            elif method == "POST":
                response = self.session.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None

    def get_orders(self, limit: int = 100, 
                  updated_after: Optional[datetime] = None) -> List[Dict]:
        """Fetch orders from Shopify store"""
        params = f"orders.json?limit={limit}&status=any"

        if updated_after:
            iso_date = updated_after.isoformat()
            params += f"&updated_at_min={iso_date}"

        result = self._make_request("GET", params)

        if result and "orders" in result:
            return result["orders"]

        return []

    def get_products(self, limit: int = 100,
                    updated_after: Optional[datetime] = None) -> List[Dict]:
        """Fetch products from Shopify store"""
        params = f"products.json?limit={limit}"

        if updated_after:
            iso_date = updated_after.isoformat()
            params += f"&updated_at_min={iso_date}"

        result = self._make_request("GET", params)

        if result and "products" in result:
            return result["products"]

        return []

    def get_analytics(self) -> Dict:
        """Collect analytics: revenue, conversion rate, AOV"""
        orders = self.get_orders(limit=100)

        if not orders:
            return {
                "total_orders": 0,
                "total_revenue": 0,
                "average_order_value": 0,
                "currency": "USD"
            }

        total_revenue = sum(
            float(order.get("total_price", 0)) for order in orders
        )

        return {
            "total_orders": len(orders),
            "total_revenue": total_revenue,
            "average_order_value": total_revenue / len(orders) if orders else 0,
            "currency": orders[0].get("currency", "USD") if orders else "USD",
            "timestamp": datetime.utcnow().isoformat()
        }

    def validate_webhook_signature(self, signature: str, 
                                  body: bytes) -> bool:
        """Validate Shopify webhook signature (HMAC-SHA256)"""
        import hmac
        import hashlib
        import base64

        computed_sig = base64.b64encode(
            hmac.new(
                self.access_token.encode(),
                body,
                hashlib.sha256
            ).digest()
        ).decode()

        return hmac.compare_digest(signature, computed_sig)

    def is_healthy(self) -> bool:
        """Health check: verify API connection is working"""
        result = self._make_request("GET", "shop.json")
        return result is not None and "shop" in result

    def validate_credentials(self) -> bool:
        """Validate that the provided credentials work with Shopify API"""
        try:
            result = self._make_request("GET", "shop.json")
            is_valid = result is not None and "shop" in result

            if is_valid:
                shop_name = result.get("shop", {}).get("name", "Unknown")
                logger.info(f"✅ Shopify credentials validated for: {shop_name}")
            else:
                logger.warning(f"❌ Shopify credentials validation failed for {self.shop_domain}")

            return is_valid
        except Exception as e:
            logger.error(f"❌ Credential validation error: {e}")
            return False

    def close(self):
        """Close session and cleanup"""
        self.session.close()
        logger.info("Shopify API client closed")
