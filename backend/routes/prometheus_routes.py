#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Week 2: Prometheus Metrics Endpoints
Expose monitoring metrics in Prometheus-compatible format
"""

import logging
from fastapi import APIRouter, Response
from datetime import datetime, timezone

from backend.prometheus_exporter import get_prometheus_exporter

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_class=Response)
async def prometheus_metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus text format (application/openmetrics-text)

    Example:
        GET /metrics

    Response Format:
        # HELP metric_name Description
        # TYPE metric_name gauge
        metric_name{label="value"} 42.5
    """
    try:
        exporter = get_prometheus_exporter()
        metrics_text = exporter.export_metrics()

        logger.info("📊 Prometheus metrics exported successfully")

        return Response(
            content=metrics_text,
            media_type="text/plain; version=0.0.4; charset=utf-8",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error exporting Prometheus metrics: {str(e)}")
        return Response(
            content=f"# Error exporting metrics: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )


@router.get("/metrics/health", response_class=Response)
async def prometheus_health_metrics():
    """
    Health-specific metrics only

    Useful for quick health checks without full metrics load
    """
    try:
        exporter = get_prometheus_exporter()
        metrics_text = exporter._export_health_metrics()

        return Response(
            content="\n".join(metrics_text),
            media_type="text/plain; version=0.0.4",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error exporting health metrics: {str(e)}")
        return Response(
            content=f"# Error: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )


@router.get("/metrics/alerts", response_class=Response)
async def prometheus_alert_metrics():
    """
    Alert metrics only

    Shows active alerts by severity (info, warning, critical)
    """
    try:
        exporter = get_prometheus_exporter()
        metrics_text = exporter.export_alert_metrics()

        return Response(
            content=metrics_text,
            media_type="text/plain; version=0.0.4",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error exporting alert metrics: {str(e)}")
        return Response(
            content=f"# Error: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )


@router.get("/metrics/performance", response_class=Response)
async def prometheus_performance_metrics():
    """
    Performance metrics only

    Operation latencies with min/max/avg/p95/p99
    """
    try:
        exporter = get_prometheus_exporter()
        metrics_text = exporter._export_performance_metrics()

        return Response(
            content="\n".join(metrics_text),
            media_type="text/plain; version=0.0.4",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error exporting performance metrics: {str(e)}")
        return Response(
            content=f"# Error: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )


@router.get("/metrics/websocket", response_class=Response)
async def prometheus_websocket_metrics():
    """
    WebSocket metrics only

    Connections, events, latency, errors
    """
    try:
        exporter = get_prometheus_exporter()
        metrics_text = exporter._export_websocket_metrics()

        return Response(
            content="\n".join(metrics_text),
            media_type="text/plain; version=0.0.4",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error exporting WebSocket metrics: {str(e)}")
        return Response(
            content=f"# Error: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )


@router.get("/metrics/config")
async def prometheus_scrape_config():
    """
    Get recommended Prometheus scrape configuration

    Returns YAML-compatible configuration that Prometheus should use
    to scrape metrics from this server
    """
    try:
        exporter = get_prometheus_exporter()
        config = exporter.get_scrape_config()

        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": config,
            "instructions": {
                "step1": "Copy the scrape_configs to your prometheus.yml",
                "step2": "Restart Prometheus: prometheus --config.file=prometheus.yml",
                "step3": "Visit http://localhost:9090 to see metrics",
                "step4": "Create Grafana dashboards using these metrics"
            }
        }
    except Exception as e:
        logger.error(f"Error getting Prometheus config: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
