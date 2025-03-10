import tweepy
import os
from dotenv import load_dotenv

load_dotenv()  # Load Twitter API keys from a .env file

# Twitter API authentication
api_key = os.getenv("TWITTER_API_KEY")
api_secret = os.getenv("TWITTER_API_SECRET")
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

client = tweepy.Client(bearer_token=bearer_token)

def get_tweets_about_stock(symbol: str, count=10):
    """
    Fetches recent tweets related to a stock symbol.
    """
    query = f"${symbol} OR {symbol} stock -is:retweet lang:en"
    
    try:
        tweets = client.search_recent_tweets(query=query, max_results=count, tweet_fields=["created_at", "text"])
        
        if getattr(tweets, "data", None) is None:
            return {"symbol": symbol, "tweets": []}

        return {
            "symbol": symbol,
            "tweets": [{"text": tweet.text, "created_at": tweet.created_at} for tweet in tweets.data]  # type: ignore
        }
    except Exception as e:
        return {"error": str(e)}