#global setting contains the global variables and functions that are used across the application
from models import SentimentResult

class SentimentResult:
    def __init__(self):
        # Initialize your model here
        pass

    def predict(self, text):
        # Add prediction logic here
        return "positive"  # Example output

sentiment_model = SentimentResult()

def get_sentiment_model():
    global sentiment_model
    return sentiment_model