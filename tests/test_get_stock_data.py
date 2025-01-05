# tests/test_stock_data.py
import pytest
import httpx
import respx
from main import get_stock_data  # Assuming your function is in stock_data.py

@pytest.mark.asyncio
@respx.mock
async def test_get_stock_data():
    # Mocking the API response
    stock_symbol = "AAPL"
    mock_url = f"https://api.example.com/stocks/{stock_symbol}"
    
    # Mock response data
    mock_data = {
        "symbol": "AAPL",
        "price": 150.0,
        "change": -1.5,
    }
    
    # Set up mock request and response
    respx.get(mock_url).mock(return_value=httpx.Response(200, json=mock_data))
    
    # Call the function you're testing
    data = await get_stock_data(stock_symbol)
    
    # Assertions to ensure function works as expected
    assert data["symbol"] == "AAPL"
    assert data["price"] == 150.0
    assert data["change"] == -1.5
