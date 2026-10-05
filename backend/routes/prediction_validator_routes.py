#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 4: Prediction Validator API Routes
REST endpoints for tracking prediction accuracy, adjusting confidence scores,
and identifying retraining opportunities.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from typing import Optional

from orchestrator import FelixAutomationOrchestrator
from analytics.prediction_validator import PredictionValidator

logger = logging.getLogger(__name__)
router = APIRouter()

# Global validator instance
validator_instance = None


def get_validator(orchestrator: FelixAutomationOrchestrator) -> PredictionValidator:
    """Get or create validator instance"""
    global validator_instance
    if validator_instance is None:
        validator_instance = PredictionValidator(orchestrator)
    return validator_instance


# ============================================================================
# PREDICTION RECORDING ENDPOINTS
# ============================================================================

@router.post("/api/predictions/record")
async def record_prediction(
    token: str,
    client_id: int,
    probability: float,
    confidence: float,
    pipeline_stage: str = "prospecto",
    factors: list = None,
    model_version: str = "v1.0",
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Record a prediction made by ConversionPredictor.

    Args:
        token: Admin authentication token
        client_id: Client ID
        probability: Predicted conversion probability (0-100)
        confidence: Confidence score (0-100)
        pipeline_stage: Predicted pipeline stage
        factors: List of factors influencing prediction
        model_version: Model version used

    Returns:
        Dict with prediction_id and confirmation
    """
    # Verify admin token
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        validator = get_validator(orch)

        prediction_data = {
            'probability': probability,
            'confidence': confidence,
            'pipeline_stage': pipeline_stage,
            'factors': factors or [],
            'model_version': model_version
        }

        prediction_id = validator.record_prediction(client_id, prediction_data)

        return {
            "status": "success",
            "prediction_id": prediction_id,
            "client_id": client_id,
            "probability": probability,
            "confidence": confidence
        }

    except Exception as e:
        logger.error(f"❌ Error recording prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/predictions/{prediction_id}/outcome")
async def record_outcome(
    prediction_id: str,
    token: str,
    converted: bool,
    actual_stage: str = "unknown",
    closed_value: float = 0,
    days_to_conversion: int = None,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Record actual outcome for a prediction.

    Args:
        prediction_id: ID of the prediction
        token: Admin authentication token
        converted: Did the client convert?
        actual_stage: Actual pipeline stage reached
        closed_value: Revenue if closed
        days_to_conversion: Days from prediction to conversion

    Returns:
        Dict with confirmation and accuracy metrics
    """
    # Verify admin token
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        validator = get_validator(orch)

        outcome_data = {
            'converted': converted,
            'actual_stage': actual_stage,
            'closed_value': closed_value,
            'days_to_conversion': days_to_conversion
        }

        success = validator.record_outcome(prediction_id, outcome_data)

        if not success:
            raise HTTPException(status_code=404, detail="Prediction not found")

        return {
            "status": "success",
            "prediction_id": prediction_id,
            "actual_converted": converted,
            "actual_stage": actual_stage,
            "outcome_recorded": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error recording outcome: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ACCURACY METRICS ENDPOINTS
# ============================================================================

@router.get("/api/predictions/metrics/accuracy")
async def get_accuracy_metrics(
    token: str,
    days: int = 30,
    model_version: str = None,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Get accuracy metrics for predictions.

    Args:
        token: Admin authentication token
        days: Timeframe to analyze (default 30 days)
        model_version: Specific model version (None = all)

    Returns:
        Dict with precision, recall, F1, accuracy, calibration metrics
    """
    # Verify admin token
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        validator = get_validator(orch)
        metrics = validator.calculate_accuracy_metrics(days=days, model_version=model_version)

        return {
            "status": "success",
            "timeframe_days": days,
            "model_version": model_version or "all",
            **metrics
        }

    except Exception as e:
        logger.error(f"❌ Error calculating metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/predictions/metrics/by-model")
async def get_model_comparison(
    token: str,
    days: int = 30,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Compare prediction accuracy across different model versions.

    Args:
        token: Admin authentication token
        days: Timeframe to analyze

    Returns:
        Dict with performance metrics per model version
    """
    # Verify admin token
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        validator = get_validator(orch)
        metrics = validator.get_model_performance_by_version(days=days)

        return {
            "status": "success",
            "timeframe_days": days,
            "models": metrics
        }

    except Exception as e:
        logger.error(f"❌ Error comparing models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONFIDENCE ADJUSTMENT ENDPOINTS
# ============================================================================

@router.post("/api/predictions/confidence/adjust")
async def adjust_confidence_scores(
    token: str,
    client_id: int = None,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Adjust confidence scores based on historical accuracy.

    Args:
        token: Admin authentication token
        client_id: Specific client (None = all)

    Returns:
        Dict with adjustment summary
    """
    # Verify admin token
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        validator = get_validator(orch)
        result = validator.adjust_confidence_scores(client_id=client_id)

        return {
            "status": "success",
            **result
        }

    except Exception as e:
        logger.error(f"❌ Error adjusting confidence: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RETRAINING ENDPOINTS
# ============================================================================

@router.get("/api/predictions/retraining/recommendations")
async def get_retraining_recommendations(
    token: str,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Get recommendations for model retraining.

    Analyzes recent performance and suggests retraining if:
    - F1 score is dropping significantly
    - F1 score is consistently low
    - Calibration error is high
    - Precision or recall is too low

    Args:
        token: Admin authentication token

    Returns:
        Dict with retraining needs and reasons
    """
    # Verify admin token
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        validator = get_validator(orch)
        recommendations = validator.get_retraining_recommendations()

        return {
            "status": "success",
            **recommendations
        }

    except Exception as e:
        logger.error(f"❌ Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HISTORY ENDPOINTS
# ============================================================================

@router.get("/api/predictions/history")
async def get_prediction_history(
    token: str,
    client_id: int = None,
    limit: int = 50,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Get prediction history for analysis.

    Args:
        token: Admin authentication token
        client_id: Specific client (None = all)
        limit: Maximum records (default 50, max 500)

    Returns:
        List of prediction records with outcomes
    """
    # Verify admin token
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        limit = min(limit, 500)  # Cap at 500

        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        validator = get_validator(orch)
        history = validator.get_prediction_history(client_id=client_id, limit=limit)

        return {
            "status": "success",
            "total": len(history),
            "client_id": client_id,
            "predictions": history
        }

    except Exception as e:
        logger.error(f"❌ Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/predictions/{prediction_id}")
async def get_prediction_details(
    prediction_id: str,
    token: str,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Get details for a specific prediction.

    Args:
        prediction_id: ID of the prediction
        token: Admin authentication token

    Returns:
        Dict with full prediction details and outcomes
    """
    # Verify admin token
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        cursor = orch.db.execute(
            "SELECT * FROM predictions WHERE prediction_id = ?",
            (prediction_id,)
        )
        pred = cursor.fetchone()

        if not pred:
            raise HTTPException(status_code=404, detail="Prediction not found")

        import json
        return {
            "status": "success",
            "prediction_id": pred[0],
            "client_id": pred[1],
            "probability": pred[2],
            "confidence": pred[3],
            "predicted_stage": pred[4],
            "actual_conversion": pred[5],
            "model_version": pred[6],
            "created_at": pred[7],
            "accuracy_metrics": json.loads(pred[8]) if pred[8] else None,
            "record_status": pred[9]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/api/predictions/stats/overview")
async def get_predictions_overview(
    token: str,
    days: int = 30,
    orchestrator: FelixAutomationOrchestrator = None
):
    """
    Get high-level overview of prediction statistics.

    Args:
        token: Admin authentication token
        days: Timeframe to analyze

    Returns:
        Dict with counts and summary statistics
    """
    # Verify admin token
    from backend.auth import verify_admin_token
    try:
        verify_admin_token(token)
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        from orchestrator import FelixAutomationOrchestrator
        from datetime import datetime, timedelta

        orch = FelixAutomationOrchestrator()
        orch.connect_database()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # Get counts
        cursor = orch.db.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status='validated' THEN 1 ELSE 0 END) as validated,
                SUM(CASE WHEN actual_conversion=1 THEN 1 ELSE 0 END) as actual_conversions,
                AVG(probability) as avg_predicted_prob,
                AVG(confidence) as avg_confidence
            FROM predictions
            WHERE created_at > ?
            """,
            (cutoff,)
        )

        row = cursor.fetchone()
        total, pending, validated, conversions, avg_prob, avg_conf = row

        return {
            "status": "success",
            "timeframe_days": days,
            "total_predictions": total or 0,
            "pending_outcomes": pending or 0,
            "validated_outcomes": validated or 0,
            "actual_conversions": conversions or 0,
            "avg_predicted_probability": round(avg_prob or 0, 1),
            "avg_confidence": round(avg_conf or 0, 1),
            "outcome_rate": round((validated / total * 100) if total and total > 0 else 0, 1)
        }

    except Exception as e:
        logger.error(f"❌ Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
