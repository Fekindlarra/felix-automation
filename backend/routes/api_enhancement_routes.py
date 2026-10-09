import re
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 3: REST API Enhancement
Advanced filtering, sorting, bulk operations, export, and webhooks
"""

import logging
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from backend.auth import verify_admin_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api-enhancement"])

# ============================================================================
# ADVANCED ANALYTICS FILTERING & SORTING
# ============================================================================


EVENTOS_WEBHOOK_VALIDOS = re.compile(
    r"^(anomaly\.(critical|high|medium|low)|prediction\.(high|low)|recommendation\.(urgent|high))$"
)


def validar_eventos_webhook(eventos: List[str]) -> List[str]:
    """Valida cada evento contra el patrón (pydantic 2.5 no permite pattern en List[str])."""
    for evento in eventos:
        if not EVENTOS_WEBHOOK_VALIDOS.match(evento):
            raise ValueError(f"Evento de webhook no válido: {evento}")
    return eventos


@router.get("/analytics/predictions/advanced")
async def get_predictions_advanced(
    token: str,
    min_probability: int = Query(0, ge=0, le=100),
    max_probability: int = Query(100, ge=0, le=100),
    min_confidence: int = Query(0, ge=0, le=100),
    stage: Optional[str] = Query(None, pattern="^(prospecto|propuesta|negociacion|cerrado)$"),
    sort_by: str = Query("probability", pattern="^(probability|confidence|timeline)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Advanced prediction filtering with multiple criteria and sorting

    Query Parameters:
    - min_probability: Minimum probability (0-100)
    - max_probability: Maximum probability (0-100)
    - min_confidence: Minimum confidence (0-100)
    - stage: Filter by pipeline stage
    - sort_by: Sort by 'probability', 'confidence', or 'timeline'
    - sort_order: 'asc' or 'desc'
    - limit: Max results (1-500)
    - offset: Pagination offset
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        from analytics.dashboard_integration import DashboardIntegration

        orchestrator = get_orchestrator()
        dashboard = DashboardIntegration(orchestrator)
        data = dashboard.generate_dashboard_data()

        predictions = data.get('predictions', {}).get('top_10', [])

        # Apply filters
        filtered = [
            p for p in predictions
            if min_probability <= float(p.get('probability', '0').rstrip('%')) <= max_probability
            and float(p.get('confidence', '0').rstrip('%')) >= min_confidence
            and (stage is None or dashboard.orchestrator.get_client(p.get('client_id')).stage == stage)
        ]

        # Apply sorting
        if sort_by == 'probability':
            filtered.sort(
                key=lambda x: float(x.get('probability', '0').rstrip('%')),
                reverse=(sort_order == 'desc')
            )
        elif sort_by == 'confidence':
            filtered.sort(
                key=lambda x: float(x.get('confidence', '0').rstrip('%')),
                reverse=(sort_order == 'desc')
            )
        elif sort_by == 'timeline':
            filtered.sort(
                key=lambda x: x.get('timeline_days', 0),
                reverse=(sort_order == 'desc')
            )

        # Apply pagination
        total = len(filtered)
        paginated = filtered[offset:offset + limit]

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "filters": {
                "probability_range": f"{min_probability}-{max_probability}",
                "min_confidence": min_confidence,
                "stage": stage
            },
            "sorting": {"by": sort_by, "order": sort_order},
            "predictions": paginated
        }

    except Exception as e:
        logger.error(f"❌ Failed to get advanced predictions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving predictions"
        )


@router.get("/analytics/anomalies/advanced")
async def get_anomalies_advanced(
    token: str,
    severity: Optional[str] = Query(None, pattern="^(CRITICAL|HIGH|MEDIUM|LOW)$"),
    min_affected_clients: int = Query(0, ge=0),
    date_from: Optional[str] = Query(None),  # ISO format: 2026-10-01
    date_to: Optional[str] = Query(None),
    sort_by: str = Query("severity", pattern="^(severity|affected_clients|timestamp)$"),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Advanced anomaly filtering with date range and severity levels

    Query Parameters:
    - severity: Filter by CRITICAL, HIGH, MEDIUM, or LOW
    - min_affected_clients: Minimum number of affected clients
    - date_from: Filter anomalies from this date (ISO format)
    - date_to: Filter anomalies until this date (ISO format)
    - sort_by: Sort by 'severity', 'affected_clients', or 'timestamp'
    - limit: Max results (1-500)
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        from analytics.dashboard_integration import DashboardIntegration

        orchestrator = get_orchestrator()
        dashboard = DashboardIntegration(orchestrator)
        data = dashboard.generate_dashboard_data()

        anomalies = data.get('anomalies', {}).get('active', [])

        # Apply severity filter
        if severity:
            anomalies = [a for a in anomalies if a.get('severity') == severity]

        # Apply sorting
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        if sort_by == 'severity':
            anomalies.sort(
                key=lambda x: severity_order.get(x.get('severity'), 4)
            )
        elif sort_by == 'affected_clients':
            anomalies.sort(
                key=lambda x: x.get('client_id', 0),
                reverse=True
            )

        # Apply pagination
        total = len(anomalies)
        paginated = anomalies[:limit]

        return {
            "total": total,
            "limit": limit,
            "filters": {
                "severity": severity,
                "min_affected_clients": min_affected_clients,
                "date_range": f"{date_from} to {date_to}" if date_from and date_to else "all"
            },
            "sorting": {"by": sort_by},
            "anomalies": paginated
        }

    except Exception as e:
        logger.error(f"❌ Failed to get advanced anomalies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving anomalies"
        )


# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/clients/bulk-update-stage")
async def bulk_update_client_stage(
    token: str,
    client_ids: List[int],
    new_stage: str = Query(..., pattern="^(prospecto|propuesta|negociacion|cerrado)$")
):
    """
    Update multiple clients' pipeline stage in one operation

    Body:
    {
        "client_ids": [1, 2, 3, 4],
        "new_stage": "propuesta"
    }
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator

        orchestrator = get_orchestrator()
        updated_count = 0

        for client_id in client_ids:
            client = orchestrator.get_client(client_id)
            if client:
                client.stage = new_stage
                orchestrator.save_client(client)
                updated_count += 1

        logger.info(f"✅ Updated {updated_count}/{len(client_ids)} clients to stage: {new_stage}")

        return {
            "status": "success",
            "total_attempted": len(client_ids),
            "total_updated": updated_count,
            "new_stage": new_stage
        }

    except Exception as e:
        logger.error(f"❌ Bulk update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in bulk update operation"
        )


@router.post("/analytics/bulk-refresh")
async def bulk_refresh_analytics(
    token: str,
    client_ids: Optional[List[int]] = None,
    analysis_type: str = Query("full", pattern="^(full|quick)$")
):
    """
    Refresh analytics for multiple clients

    Query Parameters:
    - client_ids: List of client IDs (if empty, refresh all)
    - analysis_type: 'full' or 'quick' analysis
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        from analytics.dashboard_integration import DashboardIntegration

        orchestrator = get_orchestrator()
        dashboard = DashboardIntegration(orchestrator)

        # If no specific clients provided, analyze all
        if not client_ids:
            data = dashboard.generate_dashboard_data()
            result_count = len(data.get('predictions', {}).get('top_10', []))
        else:
            result_count = len(client_ids)

        logger.info(f"✅ Refreshed analytics for {result_count} clients ({analysis_type})")

        return {
            "status": "success",
            "clients_analyzed": result_count,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Bulk refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in bulk refresh operation"
        )


# ============================================================================
# EXPORT FUNCTIONALITY
# ============================================================================

@router.get("/analytics/export/csv")
async def export_predictions_csv(
    token: str,
    min_probability: int = Query(0, ge=0, le=100)
):
    """
    Export predictions to CSV format
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        from analytics.dashboard_integration import DashboardIntegration

        orchestrator = get_orchestrator()
        dashboard = DashboardIntegration(orchestrator)
        data = dashboard.generate_dashboard_data()

        predictions = data.get('predictions', {}).get('top_10', [])
        filtered = [
            p for p in predictions
            if float(p.get('probability', '0').rstrip('%')) >= min_probability
        ]

        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['client_id', 'client_name', 'probability', 'confidence', 'timeline_days', 'status']
        )
        writer.writeheader()
        writer.writerows(filtered)

        csv_content = output.getvalue()
        output.close()

        logger.info(f"✅ Exported {len(filtered)} predictions to CSV")

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=predictions.csv"}
        )

    except Exception as e:
        logger.error(f"❌ CSV export failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting to CSV"
        )


@router.get("/analytics/export/json")
async def export_analytics_json(
    token: str,
    include_predictions: bool = Query(True),
    include_anomalies: bool = Query(True),
    include_recommendations: bool = Query(True)
):
    """
    Export complete analytics to JSON format
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        from analytics.dashboard_integration import DashboardIntegration

        orchestrator = get_orchestrator()
        dashboard = DashboardIntegration(orchestrator)
        data = dashboard.generate_dashboard_data()

        # Build selective export
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }

        if include_predictions:
            export_data['data']['predictions'] = data.get('predictions')
        if include_anomalies:
            export_data['data']['anomalies'] = data.get('anomalies')
        if include_recommendations:
            export_data['data']['recommendations'] = data.get('recommendations')

        json_content = json.dumps(export_data, indent=2)

        logger.info(f"✅ Exported analytics to JSON")

        return StreamingResponse(
            iter([json_content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=analytics_export.json"}
        )

    except Exception as e:
        logger.error(f"❌ JSON export failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting to JSON"
        )


# ============================================================================
# RATE LIMITING & API KEYS
# ============================================================================

@router.post("/api-keys/generate")
async def generate_api_key(
    token: str,
    key_name: str,
    rate_limit: int = Query(100, ge=1, le=10000)  # requests per hour
):
    """
    Generate a new API key with rate limiting
    """
    verify_admin_token(token)

    try:
        import secrets

        api_key = f"fxa_{secrets.token_hex(32)}"

        # Store in database
        if hasattr(token, '__self__'):
            from backend.app import get_orchestrator
            orchestrator = get_orchestrator()

            cursor = orchestrator.db_conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    key_name TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    rate_limit INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_used DATETIME
                )
            """)

            cursor.execute("""
                INSERT INTO api_keys (id, key_name, api_key, rate_limit)
                VALUES (?, ?, ?, ?)
            """, (
                secrets.token_hex(16),
                key_name,
                api_key,
                rate_limit
            ))

            orchestrator.db_conn.commit()

        logger.info(f"✅ Generated API key: {key_name}")

        return {
            "status": "success",
            "api_key": api_key,
            "key_name": key_name,
            "rate_limit": f"{rate_limit} requests/hour",
            "warning": "⚠️ Save this key securely - you won't see it again"
        }

    except Exception as e:
        logger.error(f"❌ API key generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating API key"
        )


@router.get("/api-keys/list")
async def list_api_keys(token: str):
    """
    List all active API keys (without showing the full key)
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        orchestrator = get_orchestrator()

        cursor = orchestrator.db_conn.cursor()
        cursor.execute("""
            SELECT id, key_name, rate_limit, created_at, last_used
            FROM api_keys
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        keys = [
            {
                'id': row[0],
                'key_name': row[1],
                'rate_limit': row[2],
                'created_at': row[3],
                'last_used': row[4]
            }
            for row in rows
        ]

        return {"total": len(keys), "keys": keys}

    except Exception as e:
        logger.error(f"❌ Failed to list API keys: {str(e)}")
        return {"total": 0, "keys": []}


# ============================================================================
# WEBHOOKS
# ============================================================================

@router.post("/webhooks/register")
async def register_webhook(
    token: str,
    webhook_url: str,
    events: List[str] = Query(default=["anomaly.critical"]),
    active: bool = Query(True)
):
    """
    Register a webhook to receive event notifications

    Query Parameters:
    - webhook_url: URL to receive POST requests
    - events: List of events to subscribe to
    - active: Enable/disable webhook
    """
    verify_admin_token(token)
    events = validar_eventos_webhook(events)

    try:
        import secrets
        from backend.app import get_orchestrator

        orchestrator = get_orchestrator()
        webhook_id = secrets.token_hex(16)

        cursor = orchestrator.db_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                webhook_url TEXT NOT NULL,
                events TEXT NOT NULL,
                active BOOLEAN,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_triggered DATETIME
            )
        """)

        cursor.execute("""
            INSERT INTO webhooks (id, webhook_url, events, active)
            VALUES (?, ?, ?, ?)
        """, (
            webhook_id,
            webhook_url,
            json.dumps(events),
            active
        ))

        orchestrator.db_conn.commit()

        logger.info(f"✅ Registered webhook: {webhook_url} for events: {events}")

        return {
            "status": "success",
            "webhook_id": webhook_id,
            "webhook_url": webhook_url,
            "events": events,
            "active": active
        }

    except Exception as e:
        logger.error(f"❌ Webhook registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering webhook"
        )


@router.get("/webhooks/list")
async def list_webhooks(token: str):
    """
    List all registered webhooks
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        orchestrator = get_orchestrator()

        cursor = orchestrator.db_conn.cursor()
        cursor.execute("""
            SELECT id, webhook_url, events, active, created_at, last_triggered
            FROM webhooks
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        webhooks = [
            {
                'id': row[0],
                'webhook_url': row[1],
                'events': json.loads(row[2]),
                'active': row[3],
                'created_at': row[4],
                'last_triggered': row[5]
            }
            for row in rows
        ]

        return {"total": len(webhooks), "webhooks": webhooks}

    except Exception as e:
        logger.error(f"❌ Failed to list webhooks: {str(e)}")
        return {"total": 0, "webhooks": []}


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(token: str, webhook_id: str):
    """
    Delete a registered webhook
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        orchestrator = get_orchestrator()

        cursor = orchestrator.db_conn.cursor()
        cursor.execute("DELETE FROM webhooks WHERE id = ?", (webhook_id,))
        orchestrator.db_conn.commit()

        logger.info(f"✅ Deleted webhook: {webhook_id}")

        return {"status": "success", "webhook_id": webhook_id}

    except Exception as e:
        logger.error(f"❌ Webhook deletion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting webhook"
        )


# ============================================================================
# COMPARISON & TRENDS
# ============================================================================

@router.get("/analytics/compare")
async def compare_periods(
    token: str,
    period1_start: str,  # ISO format: 2026-09-01
    period1_end: str,
    period2_start: str,
    period2_end: str
):
    """
    Compare analytics between two time periods

    Query Parameters:
    - period1_start, period1_end: First period (ISO date format)
    - period2_start, period2_end: Second period (ISO date format)
    """
    verify_admin_token(token)

    try:
        from backend.app import get_orchestrator
        from analytics.analytics_scheduler import AnalyticsScheduler

        orchestrator = get_orchestrator()
        scheduler = AnalyticsScheduler(orchestrator)

        # Get trends for both periods
        cursor = orchestrator.db_conn.cursor()

        # Period 1 stats
        cursor.execute("""
            SELECT COUNT(*) as runs, AVG(execution_time) as avg_time
            FROM scheduler_jobs
            WHERE timestamp BETWEEN ? AND ? AND status = 'success'
        """, (period1_start, period1_end))
        period1_data = cursor.fetchone()

        # Period 2 stats
        cursor.execute("""
            SELECT COUNT(*) as runs, AVG(execution_time) as avg_time
            FROM scheduler_jobs
            WHERE timestamp BETWEEN ? AND ? AND status = 'success'
        """, (period2_start, period2_end))
        period2_data = cursor.fetchone()

        return {
            "period1": {
                "start": period1_start,
                "end": period1_end,
                "runs": period1_data[0] if period1_data else 0,
                "avg_execution_time": period1_data[1] if period1_data else 0
            },
            "period2": {
                "start": period2_start,
                "end": period2_end,
                "runs": period2_data[0] if period2_data else 0,
                "avg_execution_time": period2_data[1] if period2_data else 0
            },
            "comparison": {
                "runs_change": ((period2_data[0] - period1_data[0]) / period1_data[0] * 100) if period1_data[0] > 0 else 0,
                "execution_time_change": ((period2_data[1] - period1_data[1]) / period1_data[1] * 100) if period1_data[1] > 0 else 0
            }
        }

    except Exception as e:
        logger.error(f"❌ Comparison failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error comparing periods"
        )
