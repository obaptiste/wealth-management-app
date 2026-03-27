"""Tests for the health-check endpoint."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


def test_health_check_status():
    """GET /health returns 200 and the expected payload."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_body():
    """Health check returns status 'ok' and a version string."""
    client = TestClient(app)
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert "version" in data
    assert isinstance(data["version"], str)
