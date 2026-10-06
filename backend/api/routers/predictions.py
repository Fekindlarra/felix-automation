"""
Predictions Router
ML-based sales probability predictions with SHAP explainability
Integrates with WebSocket for real-time dashboard updates
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import numpy as np
import pandas as pd
import logging
from datetime import datetime

from database import get_db
from models import Prediction, Client

# Import WebSocket manager for broadcasting
from .websocket import manager as ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()

class PredictionRequest(BaseModel):
    client_id: str
    web_score: int
    facebook_score: int
    google_score: int
    business_type: str
    company_size: str

class ExplainabilityFeature(BaseModel):
    feature_name: str
    impact: float
    direction: str  # "positive" or "negative"

class PredictionResponse(BaseModel):
    client_id: str
    probability: float
    confidence: float
    risk_factors: List[str]
    positive_factors: List[str]
    shap_explanations: List[ExplainabilityFeature]
    predicted_timeline_days: int

@router.post("/generate", response_model=PredictionResponse)
async def generate_prediction(request: PredictionRequest, db: Session = Depends(get_db)):
    """
    Generate ML-based sales probability prediction using trained RandomForest model

    Input:
    - client_id: Unique client identifier
    - web_score: 0-100 web audit score
    - facebook_score: 0-100 Facebook Ads score
    - google_score: 0-100 Google Ads score
    - business_type: Type of business
    - company_size: Size of company

    Output:
    - probability: 0-100 conversion probability
    - confidence: 0-1 model confidence
    - risk_factors: Negative indicators
    - positive_factors: Positive indicators
    - shap_explanations: Feature importance (ML-based)

    BROADCAST: Sends prediction to all WebSocket clients subscribed to this client_id
    """
    from ml_pipeline import pipeline

    try:
        # Load trained model if not already loaded
        if pipeline.model is None:
            logger.info("📂 Loading trained ML model...")
            pipeline.load()

        # Prepare input data for model
        input_df = pd.DataFrame([{
            'web_score': request.web_score,
            'facebook_score': request.facebook_score,
            'google_score': request.google_score,
            'business_type': request.business_type,
            'company_size': request.company_size,
            'emails_sent': 0,  # Default values for features not in request
            'emails_opened': 0,
        }])

        # Get predictions from ML model
        predictions, probabilities, shap_values = pipeline.predict(input_df)

        # Convert probability (0-1) to percentage (0-100)
        probability = int(probabilities[0] * 100)
        confidence = probabilities[0]

        # Get explanation with SHAP values
        explanation = pipeline.explain_prediction(input_df, prediction_idx=0)
        probability_explained = int(explanation['probability'] * 100)

        # Build risk and positive factors
        risk_factors = []
        positive_factors = []

        # Add factors from explanations
        for factor in explanation.get('positive_factors', []):
            positive_factors.append(f"{factor['feature']} ({factor['impact']:.1%})")

        for factor in explanation.get('negative_factors', []):
            risk_factors.append(f"{factor['feature']} ({factor['impact']:.1%})")

        # Add score-based factors
        if request.web_score < 60:
            risk_factors.append("Low website quality")
        elif request.web_score > 80:
            positive_factors.append("Strong website presence")

        if request.facebook_score < 60:
            risk_factors.append("Weak Facebook engagement")
        elif request.facebook_score > 80:
            positive_factors.append("Active Facebook campaigns")

        if request.google_score < 60:
            risk_factors.append("Underutilized Google Ads")
        elif request.google_score > 80:
            positive_factors.append("Optimized Google Ads")

        # Convert explanations to SHAP-style format
        shap_explanations = []
        for feature, impact in sorted(
            pipeline.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]:
            shap_explanations.append(
                ExplainabilityFeature(
                    feature_name=feature,
                    impact=float(impact),
                    direction="positive" if impact > 0 else "negative"
                )
            )

        # Timeline prediction (inverse relationship with probability)
        timeline_days = max(7, int((100 - probability) / 10))

        response = PredictionResponse(
            client_id=request.client_id,
            probability=probability,
            confidence=round(float(confidence), 2),
            risk_factors=list(set(risk_factors))[:5],  # Limit to 5 unique factors
            positive_factors=list(set(positive_factors))[:5],  # Limit to 5 unique factors
            shap_explanations=shap_explanations,
            predicted_timeline_days=timeline_days,
        )

        logger.info(f"✅ Prediction generated for {request.client_id}: {probability}% conversion probability")

        # Record ML prediction for A/B test comparison if active
        try:
            import sqlite3
            ml_prob = confidence  # Use confidence as probability for comparison

            # Try to find and record in ab_test_ml_predictions if test is active
            try:
                sqlite_conn = sqlite3.connect('data/pipeline.sqlite')
                sqlite_conn.row_factory = sqlite3.Row
                cursor = sqlite_conn.cursor()

                # Get active test for this client (if any)
                cursor.execute("""
                    SELECT id FROM ab_tests WHERE active = 1 LIMIT 1
                """)
                active_test = cursor.fetchone()

                if active_test:
                    test_id = active_test['id']

                    # Calculate rule-based probability for comparison
                    avg_score = (request.web_score + request.facebook_score + request.google_score) / 3
                    rules_prob = avg_score * 0.9 / 100.0  # Normalize to 0-1

                    if request.business_type == "ecommerce":
                        rules_prob = min(1.0, rules_prob + 0.05)

                    # Record both predictions
                    cursor.execute("""
                        INSERT OR REPLACE INTO ab_test_ml_predictions
                        (test_id, client_id, ml_probability, rules_probability, created_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (test_id, request.client_id, ml_prob, rules_prob))

                    sqlite_conn.commit()
                    logger.info(f"📊 Recorded ML vs rules comparison for test {test_id}, client {request.client_id}")

                sqlite_conn.close()
            except Exception as comparison_error:
                logger.warning(f"⚠️ Could not record comparison data: {comparison_error}")
        except Exception as e:
            logger.warning(f"⚠️ Skipping comparison recording: {e}")

        # 📡 BROADCAST TO WEBSOCKET: Send prediction to all connected clients
        try:
            broadcast_payload = {
                "client_id": request.client_id,
                "probability": probability,
                "confidence": round(float(confidence), 2),
                "risk_factors": response.risk_factors,
                "positive_factors": response.positive_factors,
                "timeline_days": timeline_days,
                "timestamp": datetime.now().isoformat(),
                "model_version": "ml_v1.0.0",
            }

            await ws_manager.broadcast_prediction(broadcast_payload)
            logger.info(f"✅ Prediction broadcasted for client {request.client_id}")
        except Exception as e:
            logger.error(f"⚠️ Failed to broadcast prediction: {e}")
            # Continue anyway - WebSocket failure shouldn't stop prediction generation

        return response

    except Exception as e:
        logger.error(f"❌ Error generating prediction: {e}", exc_info=True)
        # Fallback to simple rule-based prediction if model fails
        avg_score = (request.web_score + request.facebook_score + request.google_score) / 3
        probability = int(avg_score * 0.9)
        if request.business_type == "ecommerce":
            probability = min(100, probability + 5)

        scores = [request.web_score, request.facebook_score, request.google_score]
        variance = np.var(scores)
        confidence = max(0.5, 1.0 - (variance / 1000))

        risk_factors = []
        positive_factors = []

        if request.web_score < 60:
            risk_factors.append("Low website quality")
        else:
            positive_factors.append("Strong website presence")

        if request.facebook_score > 80:
            positive_factors.append("Active Facebook campaigns")
        else:
            risk_factors.append("Weak Facebook engagement")

        if request.google_score > 80:
            positive_factors.append("Optimized Google Ads")
        else:
            risk_factors.append("Underutilized Google Ads")

        shap_explanations = [
            ExplainabilityFeature(
                feature_name="web_score",
                impact=0.3,
                direction="positive" if request.web_score > 70 else "negative"
            ),
            ExplainabilityFeature(
                feature_name="facebook_score",
                impact=0.25,
                direction="positive" if request.facebook_score > 70 else "negative"
            ),
            ExplainabilityFeature(
                feature_name="google_score",
                impact=0.25,
                direction="positive" if request.google_score > 70 else "negative"
            ),
        ]

        timeline_days = max(7, int(100 - probability) // 5)

        response = PredictionResponse(
            client_id=request.client_id,
            probability=probability,
            confidence=round(float(confidence), 2),
            risk_factors=risk_factors,
            positive_factors=positive_factors,
            shap_explanations=shap_explanations,
            predicted_timeline_days=timeline_days,
        )

        logger.warning(f"⚠️ Using fallback rule-based prediction for {request.client_id}")

        # Record rule-based prediction for comparison (since ML failed)
        try:
            import sqlite3
            rules_prob = confidence

            try:
                sqlite_conn = sqlite3.connect('data/pipeline.sqlite')
                sqlite_conn.row_factory = sqlite3.Row
                cursor = sqlite_conn.cursor()

                # Get active test for this client (if any)
                cursor.execute("""
                    SELECT id FROM ab_tests WHERE active = 1 LIMIT 1
                """)
                active_test = cursor.fetchone()

                if active_test:
                    test_id = active_test['id']

                    # For fallback, use rules prob for both since ML failed
                    cursor.execute("""
                        INSERT OR REPLACE INTO ab_test_ml_predictions
                        (test_id, client_id, ml_probability, rules_probability, created_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (test_id, request.client_id, rules_prob, rules_prob))

                    sqlite_conn.commit()
                    logger.info(f"📊 Recorded fallback prediction for test {test_id}, client {request.client_id}")

                sqlite_conn.close()
            except Exception as comparison_error:
                logger.warning(f"⚠️ Could not record fallback comparison data: {comparison_error}")
        except Exception as e:
            logger.warning(f"⚠️ Skipping fallback comparison recording: {e}")

        return response

@router.get("/{client_id}", response_model=PredictionResponse)
async def get_prediction(client_id: str):
    """
    Get latest prediction for a client

    Retrieves from cache/database
    """
    # TODO: Look up from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No prediction found for client {client_id}"
    )

@router.get("/{client_id}/history")
async def get_prediction_history(client_id: str, limit: int = 10):
    """
    Get prediction history for a client

    Shows accuracy over time and model improvements
    """
    return {
        "client_id": client_id,
        "predictions": [],
        "message": "History endpoint - TODO"
    }
