import logging
import sys
import os



# Add the root project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import globalSetting

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
import models, schemas, database
import datetime
from transformers import pipeline  # type: ignore
import yfinance as yf
from .auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from schemas import TextInput, UserOut
from models import User
from database import async_session
from functools import lru_cache
from twitter_fetcher import get_tweets_about_stock



# Create FastAPI instance
app = FastAPI()

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token generation and validation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get DB session
async def get_db():
    session = database.async_session()
    try:
        yield session
    finally:
        session.close()
        

#health check
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Cache for storing stock data

@lru_cache(maxsize=100)

def get_stock_data_from_cache(symbol: str):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1mo")
    if not data.empty:
        latest_data = data.iloc[-1]
        return {
            "symbol": symbol,
            "price": latest_data["Close"],
            "change": latest_data["Close"] - latest_data["Open"],
        }
    return {"symbol": symbol, "price": None, "change": None}

@app.get("/stock-data/{symbol}")
async def get_stock_data(symbol: str):
    try:
        return get_stock_data_from_cache(symbol)
    except Exception as e:
        logging.error(f"An error occurred while fetching stock data for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching stock data: {str(e)}")

detailed_stock_cache = {}

@app.get("/stock-data/{symbol}/detailed")
async def get_detailed_stock_data(symbol: str):
    # Check if data is in cache
    if symbol in detailed_stock_cache and (datetime.datetime.now() - detailed_stock_cache[symbol]['timestamp']).seconds < 300:  # Cache for 5 minutes
        return detailed_stock_cache[symbol]['data']

    # amazonq-ignore-next-line
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1mo")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching stock data: {str(e)}")
    
    # Get the last row of the DataFrame
    if not data.empty:
        latest_data = data.iloc[-1]
        result = {
            "symbol": symbol,
            "price": latest_data["Close"],  # Last closing price
            "change": latest_data["Close"] - latest_data["Open"],  # Price change
        }
    else:
        result = {"symbol": symbol, "price": None, "change": None}

    # Cache the result
    detailed_stock_cache[symbol] = {'data': result, 'timestamp': datetime.datetime.now()}

    return result

@app.get("/stock-tweets/{symbol}")
async def get_stock_tweets(symbol: str):
    try:
        return get_tweets_about_stock(symbol)
    except Exception as e:
        logging.error(f"An error occurred while fetching tweets for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching tweets: {str(e)}")

@app.post("/analyse_tweets")
async def analyse_tweets(symbol: str, sentiment_model=Depends(lambda: globalSetting.sentiment_model)):
    """
    Fetches tweets about a stock and performs sentiment analysis.
    """
    tweets_data = get_tweets_about_stock(symbol)

    if "error" in tweets_data:
        raise HTTPException(status_code=500, detail=tweets_data["error"])

    tweets = tweets_data["tweets"]
    if not tweets:
        return {"symbol": symbol, "sentiment": "No recent tweets found"}

    try:
        texts = [tweet if isinstance(tweet, str) else tweet.get("text", "") for tweet in tweets]
        results = sentiment_model(texts)

        # Aggregate sentiment scores
        positive = sum(1 for r in results if r["label"] == "positive")
        negative = sum(1 for r in results if r["label"] == "negative")
        neutral = sum(1 for r in results if r["label"] == "neutral")
        total = len(results)

        sentiment_summary = {
            "positive": round((positive / total) * 100, 2),
            "negative": round((negative / total) * 100, 2),
            "neutral": round((neutral / total) * 100, 2),
        }

        return {
            "symbol": symbol,
            "total_tweets": total,
            "sentiment_summary": sentiment_summary,
            "detailed_sentiments": results
        }

    except Exception as e:
        logging.error(f"Error analyzing sentiment for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing sentiment: {str(e)}")

# Sentiment Analysis
@app.on_event("startup")
async def load_sentiment_model():
    globalSetting.sentiment_model = pipeline("sentiment-analysis", model="ProsusAI/finbert")

@app.post("/analyse_text")
async def analyse_text(input: TextInput, sentiment_model=Depends(lambda: globalSetting.sentiment_model)):
    try:
        result = sentiment_model(input.text)
        return {"sentiment": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during sentiment analysis: {str(e)}")

# Login and Token Generation
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the access token: {str(e)}"
        )

# User Registration
@app.post("/register", response_model=UserOut)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create a new user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        await db.rollback()
       
        logging.error("An error occurred while creating the user", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while creating the user")

# Portfolio Management
@app.post("/portfolio/", response_model=schemas.PortfolioOut)
async def create_portfolio(
    portfolio: schemas.PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        new_portfolio = models.Portfolio(**portfolio.dict(), user_id=current_user.id)
        db.add(new_portfolio)
        await db.commit()
        await db.refresh(new_portfolio)
        return new_portfolio
    except Exception as e:
        await db.rollback()
        logging.error(f"An error occurred while creating the portfolio: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while creating the portfolio")

@app.put("/portfolio/{id}", response_model=schemas.PortfolioOut)
async def update_portfolio(id: int, portfolio: schemas.PortfolioUpdate, db: AsyncSession = Depends(get_db)):
    try:
        query = select(models.Portfolio).where(models.Portfolio.id == id)
        result = await db.execute(query)
        db_portfolio = result.scalar_one_or_none()

        if not db_portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Update the fields that are provided
        if portfolio.name is not None:
            setattr(db_portfolio, "name", portfolio.name)
        if portfolio.assets is not None:
            db_portfolio.assets = portfolio.assets

        await db.commit()
        await db.refresh(db_portfolio)
        return db_portfolio
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        await db.rollback()
        logging.error(f"An error occurred while updating the portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while updating the portfolio: {str(e)}")