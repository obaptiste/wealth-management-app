# globalSetting.py
"""
Global settings and functions that are used across the application.
"""
from typing import Optional
from datetime import datetime

# Import models with proper relative import to avoid circular imports
from .models import SentimentResult as SentimentResultModel
from pydantic import BaseModel

class PortfolioSummary(BaseModel):
    total_value: float
    total_cost: float
    total_profit_loss: float
    total_profit_loss_percent: float
    last_updated: datetime

class SentimentAnalyser:
    def __init__(self):
        # Initialize your model here
        pass

    def predict(self, text):
        # Add prediction logic here
        return "positive"  # Example output
    
    def analyze(self, text):
        # Handle single text input
        if isinstance(text, str):
            sentiment = self.predict(text)
            return [{"label": sentiment, "score": 0.95}]
        else:
            # Return empty result for invalid input
            return [{"label": "neutral", "score": 0.5}]
    
    def __call__(self, texts):
        # Handle batch processing (list of texts)
        results = []
        for text in texts:
            sentiment = self.predict(text)
            results.append({"label": sentiment, "score": 0.95})
        return results

# Initialize the sentiment model
sentiment_model = SentimentAnalyser()

def get_sentiment_model():
    global sentiment_model
    return sentiment_model