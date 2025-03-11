import pytest
import httpx
import respx
import pandas as pd
from backend.main import get_stock_data  # Replace `main` with the actual module name where the function is defined
import unittest.mock as mock

@pytest.mark.asyncio
@respx.mock
async def test_get_stock_data_success():
    # Mocking the API response
    stock_symbol = "AAPL"
    mock_url = f"https://api.example.com/stocks/{stock_symbol}"
    
    # Mock response data
    mock_data = {
        "symbol": "AAPL",
        "price": 150.0,  # Mocked latest closing price
        "change": -1.5,  # Mocked price change
    }
        
    # Set up mock request and response
    route = respx.get(mock_url).mock(return_value=httpx.Response(200, json=mock_data))
    
    # Call the function you're testing
    data = await get_stock_data(stock_symbol)
    
    # Assertions to ensure function works as expected
    assert data["symbol"] == "AAPL"
    assert data["price"] == 150.0
    assert data["change"] == -1.5
    assert route.called, "The API endpoint was not called"
    assert route.call_count == 1, "The API endpoint was called more than once"

@pytest.mark.asyncio
@respx.mock
async def test_get_stock_data_404():
    # Mocking the API response for a 404
    stock_symbol = "INVALID"
    mock_url = f"https://api.example.com/stocks/{stock_symbol}"
    
    # Set up mock request and response
    respx.get(mock_url).mock(return_value=httpx.Response(404, json={"detail": "Stock not found"}))
    
    # Call the function you're testing and handle the exception
    with pytest.raises(Exception, match="Stock not found"):
        await get_stock_data(stock_symbol)


@mock.patch('yfinance.Ticker')
@pytest.mark.asyncio
async def test_get_stock_data(mock_ticker):
    mock_instance = mock_ticker.return_value
    mock_instance.history.return_value = pd.DataFrame({
        'Open': [145.0],
        'Close': [150.0],
        'High': [152.0],
        'Low': [144.0]
        }, 
        index=[pd.Timestamp('2023-01-01')])
        
    # Call function and test
    data = await get_stock_data("AAPL")
    assert data["symbol"] == "AAPL"
    assert data["price"] == 150.0