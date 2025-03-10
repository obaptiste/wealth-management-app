import pytest
from unittest.mock import patch, MagicMock
from backend.twitter_fetcher import get_tweets_about_stock


@pytest.fixture
def mock_tweepy_client():
    """Mock the tweepy Client class"""
    with patch("backend.twitter_fetcher.client") as mock_client:
        yield mock_client


def test_get_tweets_success(mock_tweepy_client):
    """Test successful tweet retrieval"""
    # Create mock tweet objects
    mock_tweet1 = MagicMock()
    mock_tweet1.text = "AAPL stock is rising!"
    mock_tweet1.created_at = "2023-01-01T12:00:00Z"
    
    mock_tweet2 = MagicMock()
    mock_tweet2.text = "Bought some $AAPL today"
    mock_tweet2.created_at = "2023-01-01T12:30:00Z"
    
    # Set up the mock response
    mock_response = MagicMock()
    mock_response.data = [mock_tweet1, mock_tweet2]
    mock_tweepy_client.search_recent_tweets.return_value = mock_response
    
    # Call the function
    result = get_tweets_about_stock("AAPL", count=2)
    
    # Check results
    assert result["symbol"] == "AAPL"
    assert len(result["tweets"]) == 2
    assert result["tweets"][0] == "AAPL stock is rising!"
    assert result["tweets"][1] == "Bought some $AAPL today"
    
    # Check that the API was called correctly
    mock_tweepy_client.search_recent_tweets.assert_called_once()
    args, kwargs = mock_tweepy_client.search_recent_tweets.call_args
    assert "AAPL" in kwargs["query"]
    assert kwargs["max_results"] == 2


def test_get_tweets_empty_response(mock_tweepy_client):
    """Test behavior when no tweets are found"""
    mock_response = MagicMock()
    mock_response.data = None
    mock_tweepy_client.search_recent_tweets.return_value = mock_response
    
    result = get_tweets_about_stock("UNKNOWN")
    
    assert result["symbol"] == "UNKNOWN"
    assert result["tweets"] == []


def test_get_tweets_api_error(mock_tweepy_client):
    """Test behavior when the API raises an exception"""
    mock_tweepy_client.search_recent_tweets.side_effect = Exception("Rate limit exceeded")
    
    result = get_tweets_about_stock("AAPL")
    
    assert "error" in result
    assert "Rate limit exceeded" in result["error"]