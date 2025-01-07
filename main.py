from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select  # Added this
from passlib.context import CryptContext
from backend import models, schemas, database
from transformers import pipeline
import yfinance as yf
from backend.auth import authenticate_user, create_access_token, get_current_user, get_password_hash  # Ensure this is imported
from backend.schemas import TextInput, UserOut
from backend.models import User
from backend.database import async_session

# Create FastAPI instance
app = FastAPI()

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token generation and validation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get DB session
async def get_db():
    async with database.async_session() as session:
        yield session
        

@app.get("/stock-data/{symbol}")
async def get_stock_data(symbol: str):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1mo")
    
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

    return result


# Sentiment Analysis
sentiment_model = pipeline("sentiment-analysis", model="ProsusAI/finbert")

@app.post("/analyse_text")
async def analyse_text(input: TextInput):
    result = sentiment_model(input.text)
    return {"sentiment": result}

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
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# User Registration
@app.post("/register", response_model=UserOut)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    query = await db.execute(User.__table__.select().where(User.email == user.email))
    existing_user = query.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create a new user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# Portfolio Management
@app.post("/portfolio/", response_model=schemas.PortfolioOut)
async def create_portfolio(
    portfolio: schemas.PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_portfolio = models.Portfolio(**portfolio.dict(), user_id=current_user.id)
    db.add(new_portfolio)
    await db.commit()
    await db.refresh(new_portfolio)
    return new_portfolio

@app.put("/portfolio/{id}", response_model=schemas.PortfolioOut)
async def update_portfolio(id: int, portfolio: schemas.PortfolioUpdate, db: AsyncSession = Depends(get_db)):
    query = select(models.Portfolio).where(models.Portfolio.id == id)
    result = await db.execute(query)
    db_portfolio = result.scalar_one_or_none()

    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Update the fields that are provided
    if portfolio.name:
        db_portfolio.name = portfolio.name
    if portfolio.assets:
        db_portfolio.assets = portfolio.assets

    await db.commit()
    await db.refresh(db_portfolio)
    return db_portfolio
