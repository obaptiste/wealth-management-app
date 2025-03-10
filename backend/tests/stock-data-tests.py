"""
Stock data retrieval tests for the wealth management API.
Tests the stock data endpoints with proper mocking.
"""
import pytest
import respx
from httpx import AsyncClient, Response
import json

from backend.main import app
from unittest.mock import patch, MagicMock


# Sample mock data for stock responses
MOCK_STOCK_DATA = {
    "AAPL": {
        "symbol": "AAPL",
        "price": 150.25,
        "change": 2.75
    },
    "MSFT": {
        "symbol": "MSFT",
        "price": 290.45,
        "change": -1.23
    },
    "GOOGL": {
        "symbol": "GOOGL",
        "price": 2750.10,
        "change": 15.40
    }
}


class MockYFTicker:
    """Mock class for the yfinance Ticker object."""
    
    def __init__(self, symbol):
        self.symbol = symbol
        
    def history(self, period=None):
        """Mock the history method to return sample data."""
        import pandas as pd
        import numpy as np
        
        # Create mock DataFrame based on the symbol
        if self.symbol in MOCK_STOCK_DATA:
            price = MOCK_STOCK_DATA[self.symbol]["price"]
            change = MOCK_STOCK_DATA[self.symbol]["change"]
            
            # Create a simple DataFrame with one row
            df = pd.DataFrame({
                "Open": [price - change],
                "High": [price + 5],
                "Low": [price - 5],
                "Close": [price],
                "Volume": [1000000]
            }, index=[pd.Timestamp("2023-01-01")])
            
            return df
        
        # Return empty DataFrame if symbol not found
        return pd.DataFrame()


@pytest.mark.asyncio
@patch("backend.main.yf.Ticker", MockYFTicker)
async def test_get_stock_data():
    """Test fetching stock data for a valid symbol."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/stock-data/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert isinstance(data["price"], (int, float))
        assert isinstance(data["change"], (int, float))


@pytest.mark.asyncio
@patch("backend.main.yf.Ticker", MockYFTicker)
async def test_get_stock_data_unknown_symbol():
    """Test fetching stock data for an unknown symbol."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/stock-data/UNKNOWN")
        
        assert response.status_code == 200  # Still returns 200 with nulls
        data = response.json()
        assert data["symbol"] == "UNKNOWN"
        assert data["price"] is None
        assert data["change"] is None


@pytest.mark.asyncio
@patch("backend.main.yf.Ticker", MockYFTicker)
async def test_get_detailed_stock_data():
    """Test fetching detailed stock data."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/stock-data/MSFT/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "MSFT"
        assert isinstance(data["price"], (int, float))
        assert isinstance(data["change"], (int, float))


@pytest.mark.asyncio
@patch("backend.main.get_tweets_about_stock")
async def test_get_stock_tweets(mock_get_tweets):
    """Test fetching tweets about a stock."""
    # Setup mock tweets response
    mock_get_tweets.return_value = {
        "symbol": "AAPL",
        "tweets": [
            {"text": "Apple is doing great!", "created_at": "2023-01-01T12:00:00Z"},
            {"text": "Just bought some $AAPL", "created_at": "2023-01-01T12:30:00Z"}
        ]
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/stock-tweets/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert len(data["tweets"]) == 2
        assert "text" in data["tweets"][0]
