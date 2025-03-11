import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend import models
from backend.database import get_db
from sqlalchemy.future import select



@pytest.mark.asyncio
async def test_update_portfolio():
    # Ensure portfolio exists
    async with get_db() as db:
        portfolio = models.Portfolio(id=1, name="Initial Portfolio", owner_id=1)  # Adjust user_id
        db.add(portfolio)
        await db.commit()

    # Update portfolio
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put(
            "/portfolio/1",
            json={
                "name": "Updated Portfolio Name",
                "assets": [
                    {
                        "symbol": "AAPL",
                        "quantity": 10,
                        "purchase_price": 150.0,
                        "purchase_date": "2023-01-01T00:00:00Z"
                    }
                ]
            }
        )
    assert response.status_code == 200, f"Response status code is not 200. Body: {response.text}"

    # Verify updates
    async with get_db() as db:
        result = await db.execute(select(models.Portfolio).where(models.Portfolio.id == 1))
        updated_portfolio = result.scalars().first()
        assert updated_portfolio.name == "Updated Portfolio Name", "Portfolio name was not updated"
        assert len(updated_portfolio.assets) == 1, "Portfolio assets were not updated"