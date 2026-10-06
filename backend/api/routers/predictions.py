"""
Predictions Router
ML-based sales probability predictions with SHAP explainability
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
import numpy as np

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
async def generate_prediction(request: PredictionRequest):
    """
    Generate ML-based sales probability prediction

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
    - shap_explanations: Feature importance (SHAP values)
    """

    # TODO: Load actual ML model (scikit-learn RandomForest)

    # Mock prediction logic
    avg_score = (request.web_score + request.facebook_score + request.google_score) / 3

    # Base probability from average score
    probability = int(avg_score * 0.9)  # 90% of score

    # Adjust for business type
    if request.business_type == "ecommerce":
        probability = min(100, probability + 5)

    # Confidence based on score consistency
    scores = [request.web_score, request.facebook_score, request.google_score]
    variance = np.var(scores)
    confidence = max(0.5, 1.0 - (variance / 1000))

    # Identify risk/positive factors
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

    # SHAP-style explanations (mock)
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
        ExplainabilityFeature(
            feature_name="business_type_ecommerce",
            impact=0.15,
            direction="positive" if request.business_type == "ecommerce" else "negative"
        ),
    ]

    # Timeline prediction (days to close)
    timeline_days = max(7, int(100 - probability) // 5)

    return PredictionResponse(
        client_id=request.client_id,
        probability=probability,
        confidence=round(float(confidence), 2),
        risk_factors=risk_factors,
        positive_factors=positive_factors,
        shap_explanations=shap_explanations,
        predicted_timeline_days=timeline_days,
    )

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
