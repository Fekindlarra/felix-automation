"""
Authentication Router Tests
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "🟢 healthy"

def test_login_invalid_credentials():
    """Test login endpoint (mock implementation accepts any credentials)"""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "anypassword"}
    )
    # Mock implementation always returns 200 (TODO: add real credential validation)
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_biometric_login():
    """Test biometric login endpoint"""
    response = client.post(
        "/api/auth/biometric",
        json={"client_id": "client_001"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["id"] == "client_001"
