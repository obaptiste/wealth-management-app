# main.py
import logging
import sys
from fastapi import FastAPI, Depends, HTTPException, status, Query, Path
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
import yfinance as yf
from functools import lru_cache
from typing import List, Optional, Dict, Any, cast

# Import local modules
from .database import get_db_dependency
from .models import User, Portfolio, Asset, SentimentResult, AssetPriceHistory
from .schemas import (
    UserCreate, UserOut, Token, PortfolioCreate, PortfolioOut,
    PortfolioUpdate, PortfolioWithSummary, PortfolioSummary, AssetCreate, AssetOut,
    AssetUpdate, AssetWithPerformance, TextInput, SentimentOut,
    SentimentBatchResult
)
from .auth import (
    authenticate_user, create_access_token, get_current_user,
    get_current_active_user, get_password_hash
)

from contextlib import asynccontextmanager
from .config import settings
import globalSetting
from .twitter_fetcher import get_tweets_about_stock

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    # Place startup code here (if any)
    yield
    # Shutdown events
    # Place shutdown code here (if any)

# Create FastAPI application
app = FastAPI(
    title="Wealth Management API",
    description="API for managing financial portfolios and performing sentiment analysis",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else ["https://yourfrontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Starting up application")
    
    # Initialize sentiment analysis model
    try:
        from transformers import pipeline
        globalSetting.sentiment_model = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        logger.info("Sentiment analysis model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load sentiment analysis model: {str(e)}")
        globalSetting.sentiment_model = None

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down application")

# Health check endpoint
@app.get("/health", tags=["System"])
def health_check():
    """Check if the API is running."""
    return {"status": "ok", "version": "1.0.0"}

# Authentication endpoints
@app.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_dependency)
):
    """Generate a JWT token for authentication."""
    # Authenticate user
    authentication_result = await authenticate_user(db, form_data.username, form_data.password)
    
    if not authentication_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the user data from database
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication succeeded but user data not found",
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Return token
    expires_at = datetime.now(timezone.utc) + access_token_expires
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at
    }

@app.post("/auth/register", response_model=UserOut, tags=["Authentication"])
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_dependency)
):
    """Register a new user."""
    # Check if email is already registered
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False
    )
    
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info(f"User created: {new_user.username}")
        return new_user
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user"
        )

@app.get("/auth/me", response_model=UserOut, tags=["Authentication"])
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get information about the currently authenticated user."""
    return current_user

# Portfolio Management Endpoints
@app.post("/portfolios", response_model=PortfolioOut, tags=["Portfolios"])
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new portfolio for the current user."""
    # Create portfolio
    new_portfolio = Portfolio(
        name=portfolio_data.name,
        description=portfolio_data.description,
        owner_id=current_user.id
    )
    
    try:
        db.add(new_portfolio)
        await db.commit()
        await db.refresh(new_portfolio)
        logger.info(f"Portfolio created: {new_portfolio.name}")
        return new_portfolio
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the portfolio"
        )

@app.get("/portfolios", response_model=List[PortfolioOut], tags=["Portfolios"])
async def get_portfolios(
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """Get all portfolios for the current user."""
    try:
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        portfolios = result.scalars().all()
        return portfolios
    except Exception as e:
        logger.error(f"Error fetching portfolios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching portfolios"
        )

@app.get("/portfolios/{portfolio_id}", response_model=PortfolioWithSummary, tags=["Portfolios"])
async def get_portfolio(
    portfolio_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific portfolio by ID with performance summary."""
    try:
        # Get portfolio
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .where(Portfolio.owner_id == current_user.id)
        )
        portfolio = result.scalars().first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Calculate portfolio summary
        total_cost = 0.0
        total_value = 0.0
        assets_with_performance = []
        
        for asset in portfolio.assets:
            # Get latest price
            try:
                stock = yf.Ticker(str(asset.symbol))
                latest_price = stock.history(period="1d")["Close"].iloc[-1]
                
                # Calculate performance - convert to float to avoid type issues
                asset_quantity = float(asset.quantity)
                asset_purchase_price = float(asset.purchase_price)
                asset_cost = asset_quantity * asset_purchase_price
                asset_value = asset_quantity * float(latest_price)
                profit_loss = asset_value - asset_cost
                profit_loss_percent = (profit_loss / asset_cost) * 100 if asset_cost > 0 else 0
                
                # Add to totals
                total_cost += asset_cost
                total_value += asset_value
                
                # Add to assets list - use proper type conversions for all numeric values
                asset_data = AssetWithPerformance(
                    id=int(str(asset.id)),
                    symbol=str(asset.symbol),
                    quantity=asset_quantity,
                    purchase_price=asset_purchase_price,
                    purchase_date=cast(datetime, asset.purchase_date),
                    notes=str(asset.notes) if asset.notes is not None else None,
                    portfolio_id=int(asset.portfolio_id),
                    current_price=float(latest_price),
                    current_value=float(asset_value),
                    profit_loss=float(profit_loss),
                    profit_loss_percent=float(profit_loss_percent),
                    created_at=asset.created_at,
                    updated_at=asset.updated_at,
                    last_updated=datetime.now(timezone.utc)
                )
                assets_with_performance.append(asset_data)
            except Exception as e:
                logger.warning(f"Error fetching price for {asset.symbol}: {str(e)}")
                # Include asset with default performance values
                asset_quantity = float(asset.quantity)
                asset_purchase_price = float(asset.purchase_price)
                asset_value = asset_quantity * asset_purchase_price
                
                asset_data = AssetWithPerformance(
                    id=int(str(asset.id)),
                    symbol=str(asset.symbol),
                    quantity=asset_quantity,
                    purchase_price=asset_purchase_price,
                    purchase_date=cast(datetime, asset.purchase_date),
                    notes=str(asset.notes) if asset.notes else None,
                    portfolio_id=int(asset.portfolio_id),
                    current_price=asset_purchase_price,
                    current_value=float(asset_value),
                    profit_loss=0.0,
                    profit_loss_percent=0.0,
                    created_at=asset.created_at,
                    updated_at=asset.updated_at,
                    last_updated=datetime.now(timezone.utc)
                )
                assets_with_performance.append(asset_data)
        
        # Create summary
        total_profit_loss = total_value - total_cost
        total_profit_loss_percent = (total_profit_loss / total_cost) * 100 if total_cost > 0 else 0
        
        summary = PortfolioSummary(
            total_value=total_value,
            total_cost=total_cost,
            total_profit_loss=total_profit_loss,
            total_profit_loss_percent=total_profit_loss_percent,
            last_updated=datetime.now(timezone.utc)
        )
        
        # Create response - ensure all SQLAlchemy Column values are converted to Python primitives
        response = PortfolioWithSummary(
            id=int(str(portfolio.id)),
            name=str(portfolio.name),
            description=str(portfolio.description) if portfolio.description is not None else None,
            owner_id=int(str(portfolio.owner_id)),
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
            assets=assets_with_performance,
            summary=summary
        )
        
        return response
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the portfolio"
        )

@app.put("/portfolios/{portfolio_id}", response_model=PortfolioOut, tags=["Portfolios"])
async def update_portfolio(
    portfolio_data: PortfolioUpdate,
    portfolio_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing portfolio."""
    try:
        # Get portfolio
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .where(Portfolio.owner_id == current_user.id)
        )
        portfolio = result.scalars().first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Update fields
        if portfolio_data.name is not None:
            setattr(portfolio, "name", portfolio_data.name)
        
        if portfolio_data.description is not None:
            setattr(portfolio, "description", portfolio_data.description)
        
        # Save changes
        try:
            await db.commit()
            await db.refresh(portfolio)
            logger.info(f"Portfolio updated: {portfolio.name}")
            return portfolio
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating portfolio: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the portfolio"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the portfolio"
        )

@app.delete("/portfolios/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Portfolios"])
async def delete_portfolio(
    portfolio_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a portfolio."""
    try:
        # Get portfolio
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .where(Portfolio.owner_id == current_user.id)
        )
        portfolio = result.scalars().first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Delete portfolio
        await db.delete(portfolio)
        await db.commit()
        logger.info(f"Portfolio deleted: {portfolio.name}")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the portfolio"
        )

# Asset Management Endpoints
@app.post("/portfolios/{portfolio_id}/assets", response_model=AssetOut, tags=["Assets"])
async def create_asset(
    asset_data: AssetCreate,
    portfolio_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Add a new asset to a portfolio."""
    try:
        # Verify portfolio exists and belongs to user
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .where(Portfolio.owner_id == current_user.id)
        )
        portfolio = result.scalars().first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Create asset - setattr approach instead of direct assignment to avoid Column type errors
        new_asset = Asset()
        setattr(new_asset, "symbol", asset_data.symbol.upper())
        setattr(new_asset, "quantity", asset_data.quantity)
        setattr(new_asset, "purchase_price", asset_data.purchase_price)
        setattr(new_asset, "purchase_date", asset_data.purchase_date)
        setattr(new_asset, "notes", asset_data.notes)
        setattr(new_asset, "portfolio_id", portfolio_id)
        
        # Add asset to database
        db.add(new_asset)
        await db.commit()
        await db.refresh(new_asset)
        logger.info(f"Asset created: {new_asset.symbol} in portfolio {portfolio_id}")
        
        # Get current market price
        try:
            stock = yf.Ticker(str(new_asset.symbol))
            latest_price = stock.history(period="1d")["Close"].iloc[-1]
            
            # Store price history - explicitly convert to primitives
            price_history = AssetPriceHistory(
                asset_id=cast(int, new_asset.id),
                price=float(latest_price),
                timestamp=datetime.now(timezone.utc)
            )
            db.add(price_history)
            await db.commit()
        except Exception as e:
            logger.warning(f"Could not fetch current price for {new_asset.symbol}: {str(e)}")
        
        return new_asset
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the asset"
        )

@app.get("/portfolios/{portfolio_id}/assets", response_model=List[AssetOut], tags=["Assets"])
async def get_assets(
    portfolio_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """Get all assets in a portfolio."""
    try:
        # Verify portfolio exists and belongs to user
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .where(Portfolio.owner_id == current_user.id)
        )
        portfolio = result.scalars().first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Get assets
        result = await db.execute(
            select(Asset)
            .where(Asset.portfolio_id == portfolio_id)
            .offset(skip)
            .limit(limit)
        )
        assets = result.scalars().all()
        
        return assets
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching assets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching assets"
        )

@app.get("/portfolios/{portfolio_id}/assets/{asset_id}", response_model=AssetWithPerformance, tags=["Assets"])
async def get_asset(
    portfolio_id: int = Path(..., ge=1),
    asset_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific asset with performance metrics."""
    try:
        # Verify portfolio exists and belongs to user
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .where(Portfolio.owner_id == current_user.id)
        )
        portfolio = result.scalars().first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Get asset
        result = await db.execute(
            select(Asset)
            .where(Asset.id == asset_id)
            .where(Asset.portfolio_id == portfolio_id)
        )
        asset = result.scalars().first()
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        # Try to get current market price
        try:
            stock = yf.Ticker(str(asset.symbol))
            latest_price = stock.history(period="1d")["Close"].iloc[-1]
            
            # Calculate performance
            asset_quantity = cast(float, asset.quantity)
            asset_purchase_price = cast(float, asset.purchase_price)
            asset_cost = asset_quantity * asset_purchase_price
            asset_value = asset_quantity * latest_price
            profit_loss = asset_value - asset_cost
            profit_loss_percent = (profit_loss / asset_cost) * 100 if asset_cost > 0 else 0
            
            # Create response with performance data
            asset_with_performance = AssetWithPerformance(
                id=int(str(asset.id)),
                symbol=str(asset.symbol),
                quantity=asset_quantity,
                purchase_price=asset_purchase_price,
                purchase_date=asset.purchase_date,
                notes=str(asset.notes) if asset.notes else None,
                portfolio_id=int(asset.portfolio_id),
                current_price=float(latest_price),
                current_value=float(asset_value),
                profit_loss=float(profit_loss),
                profit_loss_percent=float(profit_loss_percent),
                created_at=asset.created_at,
                updated_at=asset.updated_at,
                last_updated=datetime.now(timezone.utc)
            )
            
            # Store price history
            price_history = AssetPriceHistory(
                asset_id=asset.id,
                price=float(latest_price),
                timestamp=datetime.now(timezone.utc)
            )
            db.add(price_history)
            await db.commit()
            
            return asset_with_performance
        except Exception as e:
            logger.warning(f"Could not fetch current price for {asset.symbol}: {str(e)}")
            
            # Return asset without performance data
            return AssetWithPerformance(
                id=int(asset.id),
                symbol=str(asset.symbol),
                quantity=float(asset.quantity),
                purchase_price=float(asset.purchase_price),
                purchase_date=asset.purchase_date,
                notes=str(asset.notes) if asset.notes else None,
                portfolio_id=int(asset.portfolio_id),
                created_at=asset.created_at,
                updated_at=asset.updated_at
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the asset"
        )

@app.put("/portfolios/{portfolio_id}/assets/{asset_id}", response_model=AssetOut, tags=["Assets"])
async def update_asset(
    asset_data: AssetUpdate,
    portfolio_id: int = Path(..., ge=1),
    asset_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing asset."""
    try:
        # Verify portfolio exists and belongs to user
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .where(Portfolio.owner_id == current_user.id)
        )
        portfolio = result.scalars().first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Get asset
        result = await db.execute(
            select(Asset)
            .where(Asset.id == asset_id)
            .where(Asset.portfolio_id == portfolio_id)
        )
        asset = result.scalars().first()
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        # Update fields using setattr to avoid Column type issues
        if asset_data.symbol is not None:
            setattr(asset, "symbol", asset_data.symbol.upper())
        
        if asset_data.quantity is not None:
            setattr(asset, "quantity", asset_data.quantity)
        
        if asset_data.purchase_price is not None:
            setattr(asset, "purchase_price", asset_data.purchase_price)
        
        if asset_data.purchase_date is not None:
            setattr(asset, "purchase_date", asset_data.purchase_date)
            
        if asset_data.notes is not None:
            setattr(asset, "notes", asset_data.notes)
        
        # Save changes
        await db.commit()
        await db.refresh(asset)
        logger.info(f"Asset updated: {asset.symbol}")
        
        return asset
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the asset"
        )

@app.delete("/portfolios/{portfolio_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Assets"])
async def delete_asset(
    portfolio_id: int = Path(..., ge=1),
    asset_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an asset."""
    try:
        # Verify portfolio exists and belongs to user
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .where(Portfolio.owner_id == current_user.id)
        )
        portfolio = result.scalars().first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Get asset
        result = await db.execute(
            select(Asset)
            .where(Asset.id == asset_id)
            .where(Asset.portfolio_id == portfolio_id)
        )
        asset = result.scalars().first()
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        # Delete asset
        await db.delete(asset)
        await db.commit()
        logger.info(f"Asset deleted: {asset.symbol}")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the asset"
        )

# Stock Data Endpoints
@app.get("/stocks/{symbol}", tags=["Stocks"])
async def get_stock_data(symbol: str):
    """Get current data for a stock symbol."""
    try:
        # Normalize symbol
        symbol = symbol.upper()
        
        # Fetch stock data
        stock = yf.Ticker(symbol)
        history = stock.history(period="1d")
        
        if history.empty:
            return {
                "symbol": symbol,
                "price": None,
                "change": None,
                "error": "No data available for this symbol"
            }
        
        # Get latest data
        latest = history.iloc[-1]
        
        # Format response
        return {
            "symbol": symbol,
            "price": latest["Close"],
            "change": latest["Close"] - latest["Open"],
            "change_percent": ((latest["Close"] - latest["Open"]) / latest["Open"]) * 100,
            "volume": latest["Volume"],
            "high": latest["High"],
            "low": latest["Low"],
            "date": latest.name.isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching stock data: {str(e)}"
        )

@app.get("/stocks/{symbol}/history", tags=["Stocks"])
async def get_stock_history(
    symbol: str,
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")
):
    """Get historical data for a stock symbol."""
    try:
        # Normalize symbol
        symbol = symbol.upper()
        
        # Fetch stock data
        stock = yf.Ticker(symbol)
        history = stock.history(period=period)
        
        if history.empty:
            return {
                "symbol": symbol,
                "history": [],
                "error": "No historical data available for this symbol"
            }
        
        # Format response
        history_data = []
        for date, row in history.iterrows():
            history_data.append({
                "date": date.isoformat(),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"]
            })
        
        return {
            "symbol": symbol,
            "period": period,
            "history": history_data
        }
    except Exception as e:
        logger.error(f"Error fetching stock history for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching stock history: {str(e)}"
        )

# Sentiment Analysis Endpoints
@app.post("/sentiment/analyze", response_model=SentimentOut, tags=["Sentiment Analysis"])
async def analyze_text(
    text_input: TextInput,
    db: AsyncSession = Depends(get_db_dependency)
):
    """Analyze the sentiment of provided text."""
    try:
        # Check if sentiment model is available
        if not globalSetting.sentiment_model:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Sentiment analysis service is not available"
            )
        
        # Analyze text
        result = globalSetting.sentiment_model.analyze(text_input.text)[0]
        
        # Extract sentiment and confidence
        sentiment = result["label"]
        confidence = result["score"]
        
        # Store result in database
        try:
            # Extract potential stock symbol (simple heuristic)
            symbol = None
            text_words = text_input.text.upper().split()
            for word in text_words:
                if word.startswith("$") and len(word) > 1:
                    symbol = word[1:]
                    break
            
            # Store result
            if symbol:
                sentiment_result = SentimentResult(
                  symbol=symbol,
                    sentiment=sentiment,
                    confidence=confidence,
                    source_text=text_input.text
                )
                db.add(sentiment_result)
                await db.commit()
        except Exception as e:
            logger.warning(f"Error storing sentiment result: {str(e)}")
            # Continue processing - this error shouldn't affect the response
        
        # Return result
        return {
            "sentiment": sentiment,
            "confidence": confidence
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during sentiment analysis: {str(e)}"
        )

@app.post("/sentiment/analyze-tweets", response_model=SentimentBatchResult, tags=["Sentiment Analysis"])
async def analyze_tweets(
    symbol: str = Query(..., min_length=1, max_length=10, regex="^[A-Za-z0-9.]{1,10}$"),
    count: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_dependency)
):
    """Fetch and analyze tweets about a stock symbol."""
    try:
        # Normalize symbol
        symbol = symbol.upper()
        
        # Fetch tweets
        tweets_data = get_tweets_about_stock(symbol, count)
        
        # Check for errors
        if "error" in tweets_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=tweets_data["error"]
            )
        
        # Check if tweets were found
        tweets = tweets_data.get("tweets", [])
        if not tweets:
            return {
                "symbol": symbol,
                "sentiment_summary": {"positive": 0, "negative": 0, "neutral": 100},
                "total_tweets": 0
            }
        
        # Check if sentiment model is available
        if not globalSetting.sentiment_model:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Sentiment analysis service is not available"
            )
        
        # Extract tweet texts
        tweet_texts = []
        for tweet in tweets:
            if isinstance(tweet, dict) and "text" in tweet:
                tweet_texts.append(tweet["text"])
            elif isinstance(tweet, str):
                tweet_texts.append(tweet)
        
        # Analyze sentiment
        results = globalSetting.sentiment_model(tweet_texts)
        
        # Aggregate sentiment scores
        positive = sum(1 for r in results if r["label"] == "positive")
        negative = sum(1 for r in results if r["label"] == "negative")
        neutral = sum(1 for r in results if r["label"] == "neutral")
        total = len(results)
        
        # Calculate percentages
        sentiment_summary = {
            "positive": round((positive / total) * 100, 2) if total > 0 else 0,
            "negative": round((negative / total) * 100, 2) if total > 0 else 0,
            "neutral": round((neutral / total) * 100, 2) if total > 0 else 0
        }
        
        # Store aggregated sentiment in database
        try:
            # Determine overall sentiment
            max_sentiment = max(sentiment_summary.items(), key=lambda x: x[1])
            overall_sentiment = max_sentiment[0]
            confidence = max_sentiment[1] / 100
            
            sentiment_result = SentimentResult(
                symbol=symbol,
                sentiment=overall_sentiment,
                confidence=confidence,
                source_text=f"Aggregated from {total} tweets"
            )
            db.add(sentiment_result)
            await db.commit()
        except Exception as e:
            logger.warning(f"Error storing tweet sentiment result: {str(e)}")
            # Continue processing - this error shouldn't affect the response
        
        # Return results
        return {
            "symbol": symbol,
            "sentiment_summary": sentiment_summary,
            "total_tweets": total,
            "detailed_sentiments": [
                {
                    "text": tweet_texts[i] if i < len(tweet_texts) else "",
                    "sentiment": result["label"],
                    "confidence": result["score"]
                }
                for i, result in enumerate(results)
            ]
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error analyzing tweets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during tweet analysis: {str(e)}"
        )

@app.get("/sentiment/history/{symbol}", tags=["Sentiment Analysis"])
async def get_sentiment_history(
    symbol: str = Path(..., min_length=1, max_length=10, regex="^[A-Za-z0-9.]{1,10}$"),
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db_dependency)
):
    """Get historical sentiment analysis for a symbol."""
    try:
        # Normalize symbol
        symbol = symbol.upper()
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Query sentiment history
        result = await db.execute(
            select(SentimentResult)
            .where(SentimentResult.symbol == symbol)
            .where(SentimentResult.created_at >= start_date)
            .order_by(SentimentResult.created_at)
        )
        sentiment_history = result.scalars().all()
        
        # Process results
        daily_sentiments = {}
        for sentiment in sentiment_history:
            day = sentiment.created_at.date().isoformat()
            
            if day not in daily_sentiments:
                daily_sentiments[day] = {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "total": 0
                }
            
            daily_sentiments[day][sentiment.sentiment.lower()] += 1
            daily_sentiments[day]["total"] += 1
        
        # Calculate percentages
        sentiment_trends = []
        for day, counts in daily_sentiments.items():
            total = counts["total"]
            if total > 0:
                sentiment_trends.append({
                    "date": day,
                    "positive": round((counts["positive"] / total) * 100, 2),
                    "negative": round((counts["negative"] / total) * 100, 2),
                    "neutral": round((counts["neutral"] / total) * 100, 2),
                    "total_analyzed": total
                })
        
        # Sort by date
        sentiment_trends.sort(key=lambda x: x["date"])
        
        return {
            "symbol": symbol,
            "days_analyzed": days,
            "sentiment_trends": sentiment_trends
        }
    except Exception as e:
        logger.error(f"Error fetching sentiment history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching sentiment history: {str(e)}"
        )

# For backward compatibility with older API endpoints
# These should be considered deprecated and eventually removed
@app.post("/token", response_model=Token, tags=["Deprecated"])
async def login_legacy(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_dependency)
):
    """Legacy token endpoint for backward compatibility."""
    return await login_for_access_token(form_data, db)

@app.post("/register", response_model=UserOut, tags=["Deprecated"])
async def register_legacy(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_dependency)
):
    """Legacy registration endpoint for backward compatibility."""
    return await register_user(user_data, db)

@app.post("/analyse_text", tags=["Deprecated"])
async def analyse_text_legacy(
    text_input: TextInput,
    db: AsyncSession = Depends(get_db_dependency)
):
    """Legacy sentiment analysis endpoint for backward compatibility."""
    return await analyze_text(text_input, db)

@app.post("/analyse_tweets", tags=["Deprecated"])
async def analyse_tweets_legacy(
    symbol: str = Query(...),
    db: AsyncSession = Depends(get_db_dependency)
):
    """Legacy tweet analysis endpoint for backward compatibility."""
    return await analyze_tweets(symbol=symbol, count=10, db=db)

@app.get("/stock-data/{symbol}", tags=["Deprecated"])
async def get_stock_data_legacy(symbol: str):
    """Legacy stock data endpoint for backward compatibility."""
    return await get_stock_data(symbol)

@app.get("/stock-data/{symbol}/detailed", tags=["Deprecated"])
async def get_detailed_stock_data_legacy(symbol: str):
    """Legacy detailed stock data endpoint for backward compatibility."""
    return await get_stock_data(symbol)

@app.get("/stock-tweets/{symbol}", tags=["Deprecated"])
async def get_stock_tweets_legacy(symbol: str):
    """Legacy stock tweets endpoint for backward compatibility."""
    try:
        return get_tweets_about_stock(symbol)
    except Exception as e:
        logger.error(f"Error fetching tweets for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching tweets: {str(e)}"
        )

# If this file is run directly, start the application
if __name__ == "__main__":
    import uvicorn
    
    # Use a more production-ready server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
        workers=4 if settings.is_production else 1
    )