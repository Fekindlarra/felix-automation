"""
Predictions Router Tests
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_generate_prediction_valid():
    """Test generating prediction with valid data"""
    response = client.post(
        "/api/predictions/generate",
        json={
            "client_id": "client_001",
            "web_score": 75,
            "facebook_score": 85,
            "google_score": 80,
            "business_type": "ecommerce",
            "company_size": "pyme"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["probability"] <= 100
    assert 0 <= data["confidence"] <= 1
    assert isinstance(data["risk_factors"], list)
    assert isinstance(data["positive_factors"], list)
    assert len(data["shap_explanations"]) > 0
    assert data["predicted_timeline_days"] > 0

def test_generate_prediction_low_scores():
    """Test prediction with low scores"""
    response = client.post(
        "/api/predictions/generate",
        json={
            "client_id": "client_002",
            "web_score": 40,
            "facebook_score": 50,
            "google_score": 45,
            "business_type": "services",
            "company_size": "startup"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Low website quality" in data["risk_factors"]

def test_shap_explanations_present():
    """Test SHAP explanations are included"""
    response = client.post(
        "/api/predictions/generate",
        json={
            "client_id": "client_003",
            "web_score": 70,
            "facebook_score": 70,
            "google_score": 70,
            "business_type": "ecommerce",
            "company_size": "pyme"
        }
    )
    data = response.json()
    shap_features = [exp["feature_name"] for exp in data["shap_explanations"]]
    assert "web_score" in shap_features
    assert "facebook_score" in shap_features
    assert "google_score" in shap_features
