#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shopify Webhook Handler - FASE 14: Real-Time & ML Features
Procesa eventos en tiempo real de Shopify (órdenes, productos, etc.)
Valida firmas y almacena en base de datos para análisis
"""

import json
import hmac
import hashlib
import logging
import base64
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Global database connection (will be injected by main app)
database = None


def init_webhooks(db):
    """Initialize webhook handler with database connection"""
    global database
    database = db
    logger.info("✅ Shopify webhook handler initialized")


def validate_webhook_signature(signature: str, body: bytes, secret: str) -> bool:
    """
    Validate Shopify webhook signature using HMAC-SHA256

    Args:
        signature: X-Shopify-Hmac-SHA256 header value (base64)
        body: Raw request body bytes
        secret: Webhook secret from Shopify Admin

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Compute expected HMAC
        computed_hmac = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

        # Compare signatures (use constant-time comparison)
        is_valid = hmac.compare_digest(signature, computed_hmac)

        if is_valid:
            logger.debug("✅ Webhook signature validated successfully")
        else:
            logger.warning("⚠️ Webhook signature validation failed")

        return is_valid

    except Exception as e:
        logger.error(f"❌ Error validating webhook signature: {str(e)}")
        return False


def store_webhook_event(store_id: int, topic: str, data: Dict[str, Any]) -> bool:
    """
    Store webhook event in database for audit trail

    Args:
        store_id: Shopify store ID
        topic: Webhook topic (e.g., "orders/created")
        data: Webhook payload data

    Returns:
        True if stored successfully
    """
    try:
        if not database:
            logger.warning("⚠️ Database not configured - event not stored")
            return False

        cursor = database.cursor()
        cursor.execute("""
        INSERT INTO shopify_webhooks
        (store_id, topic, payload_json, received_at, processed)
        VALUES (?, ?, ?, ?, 0)
        """, (
            store_id,
            topic,
            json.dumps(data),
            datetime.now().isoformat()
        ))

        database.commit()
        logger.debug(f"✅ Webhook event stored: {topic}")
        return True

    except Exception as e:
        logger.error(f"❌ Error storing webhook event: {str(e)}")
        return False


async def process_orders_created(store_id: int, order_data: Dict[str, Any]):
    """
    Process order/created webhook

    Args:
        store_id: Shopify store ID
        order_data: Order data from webhook
    """
    try:
        logger.info(f"📦 Processing new order: {order_data.get('id')}")

        if not database:
            logger.warning("⚠️ Database not configured")
            return

        order_id = order_data.get('id')
        order_number = order_data.get('order_number')
        customer_email = order_data.get('customer', {}).get('email')
        total_price = float(order_data.get('total_price', 0))

        # Store order in database
        cursor = database.cursor()
        cursor.execute("""
        INSERT INTO shopify_orders
        (store_id, shopify_order_id, order_number, customer_email, total_price,
         status, payment_status, fulfillment_status, created_at_shopify, synced_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            store_id,
            order_id,
            order_number,
            customer_email,
            total_price,
            order_data.get('financial_status'),
            order_data.get('financial_status'),
            order_data.get('fulfillment_status'),
            order_data.get('created_at')[:19],  # ISO datetime
            datetime.now().isoformat()
        ))

        database.commit()
        logger.info(f"✅ Order {order_number} stored in database")

    except Exception as e:
        logger.error(f"❌ Error processing order: {str(e)}")


async def process_orders_updated(store_id: int, order_data: Dict[str, Any]):
    """
    Process order/updated webhook

    Args:
        store_id: Shopify store ID
        order_data: Order data from webhook
    """
    try:
        logger.info(f"📦 Processing order update: {order_data.get('id')}")

        if not database:
            logger.warning("⚠️ Database not configured")
            return

        order_id = order_data.get('id')
        status = order_data.get('financial_status')
        fulfillment_status = order_data.get('fulfillment_status')

        # Update order in database
        cursor = database.cursor()
        cursor.execute("""
        UPDATE shopify_orders
        SET status = ?, payment_status = ?, fulfillment_status = ?, updated_at_shopify = ?
        WHERE store_id = ? AND shopify_order_id = ?
        """, (
            status,
            status,
            fulfillment_status,
            order_data.get('updated_at')[:19],
            store_id,
            order_id
        ))

        database.commit()
        logger.info(f"✅ Order {order_id} updated in database")

    except Exception as e:
        logger.error(f"❌ Error processing order update: {str(e)}")


async def process_products_updated(store_id: int, product_data: Dict[str, Any]):
    """
    Process product/updated webhook

    Args:
        store_id: Shopify store ID
        product_data: Product data from webhook
    """
    try:
        logger.info(f"📦 Processing product update: {product_data.get('id')}")

        if not database:
            logger.warning("⚠️ Database not configured")
            return

        # For now, just log the product update
        # Full product tracking could be added to schema
        logger.debug(f"Product {product_data.get('title')} updated")

    except Exception as e:
        logger.error(f"❌ Error processing product update: {str(e)}")


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@router.post("/webhooks/shopify/orders/created")
async def webhook_orders_created(request: Request):
    """
    Webhook for order/created events

    Expected headers:
    - X-Shopify-Hmac-SHA256: HMAC signature
    - X-Shopify-Shop-Id: Store ID
    - X-Shopify-Webhook-Id: Unique webhook ID
    - X-Shopify-Webhook-Topic: orders/created
    """
    try:
        # Get headers
        signature = request.headers.get('X-Shopify-Hmac-SHA256')
        shop_id = request.headers.get('X-Shopify-Shop-Id')
        topic = request.headers.get('X-Shopify-Webhook-Topic')

        if not signature or not shop_id:
            logger.warning("⚠️ Missing webhook headers")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing headers")

        # Get raw body for signature validation
        body = await request.body()

        # For now, skip signature validation if secret not configured
        # In production, validate against stored webhook secret
        webhook_secret = None  # TODO: Get from database or environment
        if webhook_secret:
            if not validate_webhook_signature(signature, body, webhook_secret):
                logger.warning("⚠️ Invalid webhook signature")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

        # Parse JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

        # Extract store ID from Shopify header (numeric)
        try:
            store_id = int(shop_id) if shop_id else 0
        except ValueError:
            store_id = 0

        # Store webhook event
        store_webhook_event(store_id, topic or "orders/created", data)

        # Process order
        await process_orders_created(store_id, data)

        logger.info(f"✅ Order created webhook processed for store {store_id}")
        return JSONResponse({"status": "ok", "message": "Webhook processed"}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing order created webhook: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Processing error")


@router.post("/webhooks/shopify/orders/updated")
async def webhook_orders_updated(request: Request):
    """
    Webhook for order/updated events

    Expected headers:
    - X-Shopify-Hmac-SHA256: HMAC signature
    - X-Shopify-Shop-Id: Store ID
    - X-Shopify-Webhook-Topic: orders/updated
    """
    try:
        # Get headers
        signature = request.headers.get('X-Shopify-Hmac-SHA256')
        shop_id = request.headers.get('X-Shopify-Shop-Id')
        topic = request.headers.get('X-Shopify-Webhook-Topic')

        if not signature or not shop_id:
            logger.warning("⚠️ Missing webhook headers")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing headers")

        # Get raw body
        body = await request.body()

        # Signature validation (optional for now)
        webhook_secret = None  # TODO: Get from database
        if webhook_secret:
            if not validate_webhook_signature(signature, body, webhook_secret):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

        # Parse JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

        # Extract store ID
        try:
            store_id = int(shop_id) if shop_id else 0
        except ValueError:
            store_id = 0

        # Store webhook event
        store_webhook_event(store_id, topic or "orders/updated", data)

        # Process order update
        await process_orders_updated(store_id, data)

        logger.info(f"✅ Order updated webhook processed for store {store_id}")
        return JSONResponse({"status": "ok", "message": "Webhook processed"}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing order updated webhook: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Processing error")


@router.post("/webhooks/shopify/products/updated")
async def webhook_products_updated(request: Request):
    """
    Webhook for product/updated events

    Expected headers:
    - X-Shopify-Hmac-SHA256: HMAC signature
    - X-Shopify-Shop-Id: Store ID
    - X-Shopify-Webhook-Topic: products/updated
    """
    try:
        # Get headers
        signature = request.headers.get('X-Shopify-Hmac-SHA256')
        shop_id = request.headers.get('X-Shopify-Shop-Id')
        topic = request.headers.get('X-Shopify-Webhook-Topic')

        if not signature or not shop_id:
            logger.warning("⚠️ Missing webhook headers")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing headers")

        # Get raw body
        body = await request.body()

        # Signature validation (optional for now)
        webhook_secret = None  # TODO: Get from database
        if webhook_secret:
            if not validate_webhook_signature(signature, body, webhook_secret):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

        # Parse JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

        # Extract store ID
        try:
            store_id = int(shop_id) if shop_id else 0
        except ValueError:
            store_id = 0

        # Store webhook event
        store_webhook_event(store_id, topic or "products/updated", data)

        # Process product update
        await process_products_updated(store_id, data)

        logger.info(f"✅ Product updated webhook processed for store {store_id}")
        return JSONResponse({"status": "ok", "message": "Webhook processed"}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing product updated webhook: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Processing error")


@router.get("/webhooks/shopify/health")
async def webhook_health():
    """Health check endpoint for webhook listener"""
    return JSONResponse({
        "status": "ok",
        "service": "shopify-webhooks",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


# ============================================================================
# TESTING / DEBUGGING ENDPOINTS
# ============================================================================

@router.post("/webhooks/shopify/test")
async def test_webhook(request: Request):
    """
    Test endpoint to verify webhook delivery
    (Useful for debugging Shopify webhook configuration)
    """
    try:
        body = await request.body()
        data = json.loads(body) if body else {}

        logger.info(f"🧪 Test webhook received: {data.get('id', 'unknown')}")

        return JSONResponse({
            "status": "ok",
            "message": "Test webhook received successfully",
            "data_received": bool(body)
        })

    except Exception as e:
        logger.error(f"❌ Error in test webhook: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Processing error")
