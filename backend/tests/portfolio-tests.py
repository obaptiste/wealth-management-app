"""
Portfolio management tests for the wealth management API.
Tests creating, updating, and retrieving portfolios.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
import json

from backend.main import app


async def get_auth_token(client):
    """Helper function to get authentication token."""
    # Register a test user if not already registered
    await client.post(
        "/register",
        json={
            "username": "Portfolio Test User",
            "email": "portfolio_test@example.com",
            "password": "portfoliopass123"
        }
    )
    
    # Get token
    response = await client.post(
        "/token",
        data={
            "username": "portfolio_test@example.com",
            "password": "portfoliopass123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_portfolio():
    """Test portfolio creation."""
    async with AsyncClient(base_url="http://test") as client:
        # Get auth token
        token = await get_auth_token(client)
        
        # Create portfolio
        response = await client.post(
            "/portfolio/",
            json={
                "name": "Test Portfolio"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        portfolio_data = response.json()
        assert portfolio_data["name"] == "Test Portfolio"
        assert "id" in portfolio_data
        assert "owner_id" in portfolio_data


@pytest.mark.asyncio
async def test_update_portfolio():
    """Test portfolio updating."""
    async with AsyncClient(base_url="http://test") as client:
        # Get auth token
        token = await get_auth_token(client)
        
        # Create a portfolio first
        create_response = await client.post(
            "/portfolio/",
            json={
                "name": "Portfolio to Update"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        portfolio_id = create_response.json()["id"]
        
        # Update the portfolio
        update_response = await client.put(
            f"/portfolio/{portfolio_id}",
            json={
                "name": "Updated Portfolio Name",
                "assets": [
                    {
                        "symbol": "AAPL",
                        "quantity": 10,
                        "purchase_price": 150.0,
                        "purchase_date": datetime.now(timezone.utc).isoformat()
                    }
                ]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["name"] == "Updated Portfolio Name"
        assert len(updated_data["assets"]) == 1
        assert updated_data["assets"][0]["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_update_nonexistent_portfolio():
    """Test updating a portfolio that doesn't exist."""
    async with AsyncClient(base_url="http://test") as client:
        # Get auth token
        token = await get_auth_token(client)
        
        # Try to update a non-existent portfolio
        response = await client.put(
            "/portfolio/99999",  # Assuming this ID doesn't exist
            json={
                "name": "This Should Fail"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
        assert "Portfolio not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_unauthorized_portfolio_access():
    """Test accessing portfolio endpoints without authentication."""
    async with AsyncClient(base_url="http://test") as client:
        # Try to create a portfolio without authentication
        response = await client.post(
            "/portfolio/",
            json={
                "name": "Unauthorized Portfolio"
            }
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
