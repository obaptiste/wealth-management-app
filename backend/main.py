# main.py
import asyncio
import logging
import sys
from fastapi import FastAPI, Depends, HTTPException, status, Query, Path
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime, timedelta, timezone
import yfinance as yf
from functools import lru_cache
from typing import List, Optional, Dict, Any, cast

# Import local modules
from .database import get_db_dependency
from .models import (
    User,
    Portfolio,
    Asset,
    SentimentResult,
    AssetPriceHistory,
    InsuranceProduct,
    PensionPlan,
    WatchlistItem,
)
from .portfolio_snapshots import (
    capture_portfolio_snapshot,
    get_portfolio_snapshot_by_date,
    get_portfolio_snapshot_history,
)
from .snapshot_jobs import run_daily_snapshot_scheduler
from .schemas import (
    UserCreate, UserOut, Token, PortfolioCreate, PortfolioOut,
    PortfolioUpdate, PortfolioWithSummary, PortfolioSummary, AssetCreate, AssetOut,
    AssetUpdate, AssetWithPerformance, TextInput, SentimentOut,
    SentimentBatchResult, CurrencyConversionRequest, CurrencyConversionResponse,
    ExchangeRatesResponse, InsuranceProductOut, InsuranceRecommendationRequest,
    InsuranceRecommendation, InsuranceRecommendationsResponse, PensionPlanCreate,
    PensionPlanUpdate, PensionPlanOut, PensionCalculationRequest, PensionCalculationResponse,
    PensionProjection, WatchlistItemCreate, WatchlistItemOut, WatchlistItemSentiment,
    PortfolioSnapshotOut, PortfolioSnapshotHistoryResponse,
)
from .auth import (
    authenticate_user, create_access_token, get_current_user,
    get_current_active_user, get_password_hash
)

from contextlib import asynccontextmanager
from .config import settings
from . import globalSetting
from .twitter_fetcher import get_tweets_about_stock

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
snapshot_scheduler_task: Optional[asyncio.Task[None]] = None
snapshot_scheduler_stop_event: Optional[asyncio.Event] = None


async def refresh_today_snapshot_after_asset_write(
    db: AsyncSession,
    portfolio_id: int,
    current_user: User,
) -> None:
    """Best-effort daily snapshot refresh after portfolio mutations."""

    try:
        snapshot = await capture_portfolio_snapshot(db, portfolio_id, current_user.id)
        if snapshot is not None:
            logger.info(
                "Refreshed portfolio snapshot for portfolio %s as of %s",
                portfolio_id,
                snapshot.as_of,
            )
    except Exception as exc:
        await db.rollback()
        logger.warning(
            "Portfolio snapshot refresh failed for portfolio %s after asset mutation: %s",
            portfolio_id,
            exc,
        )

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
    global snapshot_scheduler_task
    global snapshot_scheduler_stop_event

    logger.info("Starting up application")
    
    # Initialize sentiment analysis model
    try:
        from transformers import pipeline
        globalSetting.sentiment_model = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        logger.info("Sentiment analysis model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load sentiment analysis model: {str(e)}")
        globalSetting.sentiment_model = None

    if settings.snapshot_scheduler_enabled:
        snapshot_scheduler_stop_event = asyncio.Event()
        snapshot_scheduler_task = asyncio.create_task(
            run_daily_snapshot_scheduler(snapshot_scheduler_stop_event)
        )
        logger.info(
            "Daily snapshot scheduler enabled for this process at %02d:%02d UTC",
            settings.snapshot_capture_hour_utc,
            settings.snapshot_capture_minute_utc,
        )

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global snapshot_scheduler_task
    global snapshot_scheduler_stop_event

    if snapshot_scheduler_stop_event is not None:
        snapshot_scheduler_stop_event.set()

    if snapshot_scheduler_task is not None:
        snapshot_scheduler_task.cancel()
        try:
            await snapshot_scheduler_task
        except asyncio.CancelledError:
            logger.info("Daily snapshot scheduler stopped")
        snapshot_scheduler_task = None
        snapshot_scheduler_stop_event = None

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
    result = await db.execute(select(User).where(User.email == form_data.username))
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
        # Eagerly reload with assets so Pydantic serialisation works in async context
        result = await db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.assets))
            .where(Portfolio.id == new_portfolio.id)
        )
        new_portfolio = result.scalars().first()
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
            .options(selectinload(Portfolio.assets))
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
        # Get portfolio (eagerly load assets to avoid async lazy-load errors)
        result = await db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.assets))
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
                asset_quantity = float(getattr(asset, "quantity"))
                asset_purchase_price = float(getattr(asset, "purchase_price"))
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
                    portfolio_id=int(str(asset.portfolio_id)),
                    current_price=float(latest_price),
                    current_value=float(asset_value),
                    profit_loss=float(profit_loss),
                    profit_loss_percent=float(profit_loss_percent),
                    created_at=cast(datetime, asset.created_at),
                    updated_at=cast(datetime, asset.updated_at),
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
                    notes=str(asset.notes) if asset.notes is not None else None,
                    portfolio_id=int(str(asset.portfolio_id)),
                    current_price=asset_purchase_price,
                    current_value=float(asset_value),
                    profit_loss=0.0,
                    profit_loss_percent=0.0,
                    created_at=cast(datetime, asset.created_at),
                    updated_at=cast(datetime, asset.updated_at),
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
            created_at=cast(datetime, portfolio.created_at),
            updated_at=cast(datetime, portfolio.updated_at),
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
            # Eagerly reload with assets so Pydantic serialisation works in async context
            result = await db.execute(
                select(Portfolio)
                .options(selectinload(Portfolio.assets))
                .where(Portfolio.id == portfolio.id)
            )
            portfolio = result.scalars().first()
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

# Portfolio Snapshot Endpoints
@app.post(
    "/portfolios/{portfolio_id}/snapshots/capture",
    response_model=PortfolioSnapshotOut,
    tags=["Portfolio Snapshots"],
)
async def capture_portfolio_snapshot_endpoint(
    portfolio_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Capture or refresh today's persisted snapshot for a portfolio."""

    try:
        snapshot = await capture_portfolio_snapshot(db, portfolio_id, current_user.id)
        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found",
            )
        return snapshot
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error capturing portfolio snapshot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while capturing the portfolio snapshot",
        )


@app.get(
    "/portfolios/{portfolio_id}/snapshots",
    response_model=PortfolioSnapshotHistoryResponse,
    tags=["Portfolio Snapshots"],
)
async def list_portfolio_snapshots(
    portfolio_id: int = Path(..., ge=1),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Return persisted daily portfolio value history."""

    try:
        history = await get_portfolio_snapshot_history(
            db,
            portfolio_id,
            current_user.id,
            days=days,
        )
        if history is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found",
            )
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing portfolio snapshots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching portfolio snapshot history",
        )


@app.get(
    "/portfolios/{portfolio_id}/snapshots/{snapshot_date}",
    response_model=PortfolioSnapshotOut,
    tags=["Portfolio Snapshots"],
)
async def get_portfolio_snapshot(
    portfolio_id: int = Path(..., ge=1),
    snapshot_date: date = Path(...),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Return a single persisted snapshot by portfolio and date."""

    try:
        snapshot = await get_portfolio_snapshot_by_date(
            db,
            portfolio_id,
            current_user.id,
            snapshot_date,
        )
        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio snapshot not found",
            )
        return snapshot
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio snapshot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the portfolio snapshot",
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

        await refresh_today_snapshot_after_asset_write(db, portfolio_id, current_user)
        
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
                purchase_date=cast(datetime, asset.purchase_date),
                notes=str(asset.notes) if asset.notes is not None else None,
                portfolio_id=int(str(asset.portfolio_id)),
                current_price=float(latest_price),
                current_value=float(asset_value),
                profit_loss=float(profit_loss),
                profit_loss_percent=float(profit_loss_percent),
                created_at=cast(datetime, asset.created_at),
                updated_at=cast(datetime, asset.updated_at),
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
            # Return asset with default values for performance metrics
            asset_quantity = float(str(asset.quantity))
            asset_purchase_price = float(str(asset.purchase_price))
            
            return AssetWithPerformance(
                id=int(str(asset.id)),
                symbol=str(asset.symbol),
                quantity=asset_quantity,
                purchase_price=asset_purchase_price,
                purchase_date=cast(datetime, asset.purchase_date),
                notes=str(asset.notes) if str(asset.notes) else None,
                portfolio_id=int(str(asset.portfolio_id)),
                current_price=asset_purchase_price,
                current_value=asset_quantity * asset_purchase_price,
                profit_loss=0.0,
                profit_loss_percent=0.0,
                created_at=cast(datetime, asset.created_at),
                updated_at=cast(datetime, asset.updated_at),
                last_updated=datetime.now(timezone.utc)
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

        await refresh_today_snapshot_after_asset_write(db, portfolio_id, current_user)
        
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

        await refresh_today_snapshot_after_asset_write(db, portfolio_id, current_user)
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
            "date": str(latest.name) if latest.name is not None else datetime.now(timezone.utc).isoformat()
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
                "date": str(date) if date is not None else None,
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

# Currency Conversion Endpoints
@lru_cache(maxsize=128)
def get_exchange_rates_from_api(base: str = "USD") -> Dict[str, Any]:
    """Fetch exchange rates from a free API (cached)."""
    import requests
    try:
        # Using exchangerate-api.com free tier (no API key needed for basic usage)
        response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{base}")
        if response.status_code == 200:
            data = response.json()
            return {
                "base": data["base"],
                "rates": data["rates"],
                "last_updated": datetime.now(timezone.utc)
            }
        else:
            # Fallback to mock data if API fails
            logger.warning(f"Exchange rate API returned status {response.status_code}, using mock data")
            return get_mock_exchange_rates(base)
    except Exception as e:
        logger.error(f"Error fetching exchange rates: {str(e)}, using mock data")
        return get_mock_exchange_rates(base)

def get_mock_exchange_rates(base: str = "USD") -> Dict[str, Any]:
    """Return mock exchange rates as fallback."""
    mock_rates = {
        "USD": {"EUR": 0.92, "GBP": 0.79, "JPY": 149.50, "CHF": 0.88, "CAD": 1.35, "AUD": 1.52, "CNY": 7.24},
        "EUR": {"USD": 1.09, "GBP": 0.86, "JPY": 162.50, "CHF": 0.96, "CAD": 1.47, "AUD": 1.65, "CNY": 7.88},
        "GBP": {"USD": 1.27, "EUR": 1.16, "JPY": 189.00, "CHF": 1.12, "CAD": 1.71, "AUD": 1.93, "CNY": 9.19},
    }

    if base not in mock_rates:
        base = "USD"

    rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.50, "CHF": 0.88, "CAD": 1.35, "AUD": 1.52, "CNY": 7.24}
    if base != "USD":
        # Convert all rates relative to the base currency
        base_to_usd = 1.0 / rates[base]
        rates = {k: v * base_to_usd for k, v in rates.items()}

    return {
        "base": base,
        "rates": rates,
        "last_updated": datetime.now(timezone.utc)
    }

@app.post("/currency/convert", response_model=CurrencyConversionResponse, tags=["Currency"])
async def convert_currency(request: CurrencyConversionRequest):
    """Convert an amount from one currency to another using real-time exchange rates."""
    try:
        from_currency = request.from_currency.upper()
        to_currency = request.to_currency.upper()
        amount = request.amount

        # Get exchange rates
        rates_data = get_exchange_rates_from_api(from_currency)
        rates = rates_data["rates"]

        if to_currency not in rates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Currency {to_currency} not supported"
            )

        # Calculate conversion
        exchange_rate = rates[to_currency]
        converted_amount = amount * exchange_rate

        return CurrencyConversionResponse(
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            converted_amount=converted_amount,
            exchange_rate=exchange_rate,
            last_updated=rates_data["last_updated"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting currency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during currency conversion: {str(e)}"
        )

@app.get("/currency/rates", response_model=ExchangeRatesResponse, tags=["Currency"])
async def get_exchange_rates(base: str = Query("USD", min_length=3, max_length=3)):
    """Get current exchange rates for a base currency."""
    try:
        base = base.upper()
        rates_data = get_exchange_rates_from_api(base)

        return ExchangeRatesResponse(
            base=rates_data["base"],
            rates=rates_data["rates"],
            last_updated=rates_data["last_updated"]
        )
    except Exception as e:
        logger.error(f"Error fetching exchange rates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching exchange rates: {str(e)}"
        )

@app.get("/currency/supported", tags=["Currency"])
async def get_supported_currencies():
    """Get list of supported currencies."""
    currencies = {
        "USD": "United States Dollar",
        "EUR": "Euro",
        "GBP": "British Pound Sterling",
        "JPY": "Japanese Yen",
        "CHF": "Swiss Franc",
        "CAD": "Canadian Dollar",
        "AUD": "Australian Dollar",
        "CNY": "Chinese Yuan",
        "INR": "Indian Rupee",
        "BRL": "Brazilian Real",
        "ZAR": "South African Rand",
        "RUB": "Russian Ruble",
        "KRW": "South Korean Won",
        "MXN": "Mexican Peso",
        "SGD": "Singapore Dollar",
        "HKD": "Hong Kong Dollar",
        "NOK": "Norwegian Krone",
        "SEK": "Swedish Krona",
        "DKK": "Danish Krone",
        "NZD": "New Zealand Dollar"
    }
    return {"currencies": currencies}

# Insurance Recommendation Endpoints
async def seed_insurance_products(db: AsyncSession):
    """Seed insurance products if they don't exist."""
    result = await db.execute(select(func.count(InsuranceProduct.id)))
    count = result.scalar()

    if count == 0:
        products = [
            InsuranceProduct(
                name="Basic Life Insurance",
                type="life",
                description="Affordable life insurance coverage for young professionals",
                coverage_amount=250000,
                monthly_premium=25,
                min_age=18,
                max_age=65
            ),
            InsuranceProduct(
                name="Premium Life Insurance",
                type="life",
                description="Comprehensive life insurance with higher coverage",
                coverage_amount=1000000,
                monthly_premium=100,
                min_age=25,
                max_age=60,
                min_income=50000
            ),
            InsuranceProduct(
                name="Health Insurance Plus",
                type="health",
                description="Comprehensive health coverage with low deductibles",
                coverage_amount=500000,
                monthly_premium=350,
                min_age=18,
                max_age=75
            ),
            InsuranceProduct(
                name="Disability Income Protection",
                type="disability",
                description="Replace 60% of your income if you become disabled",
                coverage_amount=100000,
                monthly_premium=50,
                min_age=25,
                max_age=65,
                min_income=30000
            ),
            InsuranceProduct(
                name="Family Health Plan",
                type="health",
                description="Health coverage for families with children",
                coverage_amount=1000000,
                monthly_premium=600,
                min_age=25,
                max_age=65
            ),
        ]

        for product in products:
            db.add(product)

        await db.commit()
        logger.info(f"Seeded {len(products)} insurance products")

@app.get("/insurance/products", response_model=List[InsuranceProductOut], tags=["Insurance"])
async def get_insurance_products(db: AsyncSession = Depends(get_db_dependency)):
    """Get all available insurance products."""
    try:
        # Seed products if needed
        await seed_insurance_products(db)

        result = await db.execute(select(InsuranceProduct))
        products = result.scalars().all()
        return products
    except Exception as e:
        logger.error(f"Error fetching insurance products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching insurance products: {str(e)}"
        )

@app.post("/insurance/recommendations", response_model=InsuranceRecommendationsResponse, tags=["Insurance"])
async def get_insurance_recommendations(
    request: InsuranceRecommendationRequest,
    db: AsyncSession = Depends(get_db_dependency)
):
    """Get personalized insurance product recommendations based on user data."""
    try:
        # Seed products if needed
        await seed_insurance_products(db)

        # Get all products
        result = await db.execute(select(InsuranceProduct))
        products = result.scalars().all()

        # Filter and score products
        recommendations = []

        for product in products:
            # Check age eligibility
            if request.age < product.min_age or request.age > product.max_age:
                continue

            # Check income eligibility
            if product.min_income and request.income < product.min_income:
                continue

            # Calculate recommendation score
            score = 50.0  # Base score
            reason_parts = []

            # Life insurance scoring
            if product.type == "life":
                if not request.has_life_insurance:
                    score += 20
                    reason_parts.append("You don't have life insurance yet")

                if request.dependents > 0:
                    score += request.dependents * 10
                    reason_parts.append(f"You have {request.dependents} dependent(s)")

                if request.income >= 50000 and product.coverage_amount >= 500000:
                    score += 15
                    reason_parts.append("Higher coverage matches your income level")

            # Health insurance scoring
            elif product.type == "health":
                if not request.has_health_insurance:
                    score += 30
                    reason_parts.append("Health insurance is essential")

                if request.dependents > 0 and "family" in product.name.lower():
                    score += 20
                    reason_parts.append("Family plan recommended for dependents")

            # Disability insurance scoring
            elif product.type == "disability":
                if request.income >= 30000:
                    score += 15
                    reason_parts.append("Protect your income in case of disability")

                if request.dependents > 0:
                    score += 10
                    reason_parts.append("Income protection important for dependents")

            # Risk tolerance adjustment
            if request.risk_tolerance == "low":
                score += 10
                reason_parts.append("Recommended for low risk tolerance")
            elif request.risk_tolerance == "high" and product.monthly_premium < 100:
                score += 5

            # Affordability check
            affordability_ratio = product.monthly_premium / (request.income / 12)
            if affordability_ratio > 0.1:  # More than 10% of monthly income
                score -= 20
                reason_parts.append("Premium is relatively high for your income")
            elif affordability_ratio < 0.05:
                score += 10
                reason_parts.append("Affordable premium for your income level")

            # Cap score at 100
            score = min(score, 100)

            # Only recommend if score is above threshold
            if score >= 40:
                recommendations.append(
                    InsuranceRecommendation(
                        product=InsuranceProductOut(
                            id=product.id,
                            name=product.name,
                            type=product.type,
                            description=product.description,
                            coverage_amount=product.coverage_amount,
                            monthly_premium=product.monthly_premium,
                            min_age=product.min_age,
                            max_age=product.max_age,
                            min_income=product.min_income,
                            created_at=product.created_at,
                            updated_at=product.updated_at
                        ),
                        score=round(score, 2),
                        reason=". ".join(reason_parts) if reason_parts else "Good general coverage option"
                    )
                )

        # Sort by score
        recommendations.sort(key=lambda x: x.score, reverse=True)

        # Calculate totals
        total_coverage = sum(r.product.coverage_amount for r in recommendations[:3])  # Top 3
        total_premium = sum(r.product.monthly_premium for r in recommendations[:3])

        return InsuranceRecommendationsResponse(
            recommendations=recommendations,
            total_recommended_coverage=total_coverage,
            total_monthly_premium=total_premium
        )
    except Exception as e:
        logger.error(f"Error generating insurance recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating recommendations: {str(e)}"
        )

# Pension Planning Endpoints
@app.get("/pension/plans", response_model=List[PensionPlanOut], tags=["Pension"])
async def get_pension_plans(
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Get all pension plans for the current user."""
    try:
        result = await db.execute(
            select(PensionPlan)
            .where(PensionPlan.user_id == current_user.id)
        )
        plans = result.scalars().all()
        return plans
    except Exception as e:
        logger.error(f"Error fetching pension plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching pension plans: {str(e)}"
        )

@app.get("/pension/plans/{plan_id}", response_model=PensionPlanOut, tags=["Pension"])
async def get_pension_plan(
    plan_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific pension plan by ID."""
    try:
        result = await db.execute(
            select(PensionPlan)
            .where(PensionPlan.id == plan_id)
            .where(PensionPlan.user_id == current_user.id)
        )
        plan = result.scalars().first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pension plan not found"
            )

        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pension plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the pension plan: {str(e)}"
        )

def calculate_pension_value(
    current_age: int,
    retirement_age: int,
    monthly_contribution: float,
    current_savings: float,
    expected_return: float
) -> float:
    """Calculate future pension value using compound interest formula."""
    years = retirement_age - current_age
    monthly_rate = (expected_return / 100) / 12
    months = years * 12

    # Future value of current savings
    fv_current = current_savings * ((1 + monthly_rate) ** months)

    # Future value of monthly contributions (annuity)
    if monthly_rate > 0:
        fv_contributions = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    else:
        fv_contributions = monthly_contribution * months

    return fv_current + fv_contributions

@app.post("/pension/plans", response_model=PensionPlanOut, tags=["Pension"])
async def create_pension_plan(
    plan_data: PensionPlanCreate,
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new pension plan for the current user."""
    try:
        # Validate retirement age
        if plan_data.target_retirement_age <= plan_data.current_age:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target retirement age must be greater than current age"
            )

        # Calculate projected value
        projected_value = calculate_pension_value(
            plan_data.current_age,
            plan_data.target_retirement_age,
            plan_data.monthly_contribution,
            plan_data.current_savings,
            plan_data.expected_return
        )

        # Create pension plan
        new_plan = PensionPlan(
            name=plan_data.name,
            user_id=current_user.id,
            current_age=plan_data.current_age,
            target_retirement_age=plan_data.target_retirement_age,
            monthly_contribution=plan_data.monthly_contribution,
            current_savings=plan_data.current_savings,
            expected_return=plan_data.expected_return,
            projected_value=projected_value
        )

        db.add(new_plan)
        await db.commit()
        await db.refresh(new_plan)
        logger.info(f"Pension plan created: {new_plan.name}")

        return new_plan
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating pension plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the pension plan: {str(e)}"
        )

@app.put("/pension/plans/{plan_id}", response_model=PensionPlanOut, tags=["Pension"])
async def update_pension_plan(
    plan_data: PensionPlanUpdate,
    plan_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing pension plan."""
    try:
        result = await db.execute(
            select(PensionPlan)
            .where(PensionPlan.id == plan_id)
            .where(PensionPlan.user_id == current_user.id)
        )
        plan = result.scalars().first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pension plan not found"
            )

        # Update fields
        if plan_data.name is not None:
            plan.name = plan_data.name

        if plan_data.target_retirement_age is not None:
            plan.target_retirement_age = plan_data.target_retirement_age

        if plan_data.monthly_contribution is not None:
            plan.monthly_contribution = plan_data.monthly_contribution

        if plan_data.current_savings is not None:
            plan.current_savings = plan_data.current_savings

        if plan_data.expected_return is not None:
            plan.expected_return = plan_data.expected_return

        # Recalculate projected value
        plan.projected_value = calculate_pension_value(
            plan.current_age,
            plan.target_retirement_age,
            plan.monthly_contribution,
            plan.current_savings,
            plan.expected_return
        )

        await db.commit()
        await db.refresh(plan)
        logger.info(f"Pension plan updated: {plan.name}")

        return plan
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating pension plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the pension plan: {str(e)}"
        )

@app.delete("/pension/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Pension"])
async def delete_pension_plan(
    plan_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a pension plan."""
    try:
        result = await db.execute(
            select(PensionPlan)
            .where(PensionPlan.id == plan_id)
            .where(PensionPlan.user_id == current_user.id)
        )
        plan = result.scalars().first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pension plan not found"
            )

        await db.delete(plan)
        await db.commit()
        logger.info(f"Pension plan deleted: {plan.name}")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting pension plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the pension plan: {str(e)}"
        )

@app.post("/pension/calculate", response_model=PensionCalculationResponse, tags=["Pension"])
async def calculate_pension_projection(request: PensionCalculationRequest):
    """Calculate pension projections without saving to database."""
    try:
        # Validate retirement age
        if request.retirement_age <= request.current_age:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retirement age must be greater than current age"
            )

        years_to_retirement = request.retirement_age - request.current_age
        monthly_rate = (request.expected_return / 100) / 12

        # Calculate year-by-year projections
        projections = []
        total_contributions = request.current_savings
        total_value = request.current_savings

        for year in range(1, years_to_retirement + 1):
            # Add 12 months of contributions
            for _ in range(12):
                total_value = total_value * (1 + monthly_rate) + request.monthly_contribution
                total_contributions += request.monthly_contribution

            investment_returns = total_value - total_contributions

            projections.append(
                PensionProjection(
                    age=request.current_age + year,
                    year=year,
                    total_contributions=round(total_contributions, 2),
                    investment_returns=round(investment_returns, 2),
                    total_value=round(total_value, 2)
                )
            )

        # Calculate monthly retirement income (4% withdrawal rate annually)
        monthly_retirement_income = (total_value * 0.04) / 12

        return PensionCalculationResponse(
            retirement_age=request.retirement_age,
            years_to_retirement=years_to_retirement,
            total_contributions=round(total_contributions, 2),
            projected_value=round(total_value, 2),
            monthly_retirement_income=round(monthly_retirement_income, 2),
            projections=projections
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating pension projection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during pension calculation: {str(e)}"
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

# ---------------------------------------------------------------------------
# Watchlist endpoints
# ---------------------------------------------------------------------------

def _sentiment_to_score(sentiment: str, confidence: float) -> float:
    """Map raw FinBERT sentiment label + confidence to a [-1, 1] score."""
    if sentiment == "positive":
        return confidence
    if sentiment == "negative":
        return -confidence
    return 0.0


async def _latest_sentiment_for_symbol(
    db: AsyncSession, symbol: str
) -> Optional[WatchlistItemSentiment]:
    """Return the most recent SentimentResult for a symbol, or None."""
    result = await db.execute(
        select(SentimentResult)
        .where(SentimentResult.symbol == symbol)
        .order_by(SentimentResult.created_at.desc())
        .limit(1)
    )
    row = result.scalars().first()
    if row is None:
        return None
    return WatchlistItemSentiment(
        symbol=row.symbol,
        score=_sentiment_to_score(row.sentiment, row.confidence),
        label=row.sentiment,
        confidence=row.confidence,
        source=row.source_text or "sentiment_model",
        analyzed_at=row.created_at,
    )


@app.get("/watchlist", response_model=List[WatchlistItemOut], tags=["Watchlist"])
async def get_watchlist(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dependency),
):
    """Return all symbols on the authenticated user's watchlist, with latest sentiment."""
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == current_user.id)
        .order_by(WatchlistItem.created_at.asc())
    )
    items = result.scalars().all()

    # Enrich each item with the latest sentiment (one query per symbol).
    # For typical watchlist sizes (< 50 symbols) this is acceptable.
    output: List[WatchlistItemOut] = []
    for item in items:
        latest_sentiment = await _latest_sentiment_for_symbol(db, item.symbol)
        output.append(
            WatchlistItemOut(
                symbol=item.symbol,
                display_name=item.display_name,
                added_at=item.created_at,
                notes=item.notes,
                latest_sentiment=latest_sentiment,
            )
        )
    return output


@app.post("/watchlist", response_model=WatchlistItemOut, status_code=status.HTTP_201_CREATED, tags=["Watchlist"])
async def add_to_watchlist(
    payload: WatchlistItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dependency),
):
    """Add a symbol to the authenticated user's watchlist."""
    # Reject duplicates
    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.symbol == payload.symbol,
        )
    )
    if existing.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Symbol '{payload.symbol}' is already on your watchlist",
        )

    new_item = WatchlistItem(
        user_id=current_user.id,
        symbol=payload.symbol,
        display_name=payload.display_name,
        notes=payload.notes,
    )
    try:
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        logger.info(f"Watchlist: user {current_user.id} added {payload.symbol}")
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Symbol '{payload.symbol}' is already on your watchlist",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding watchlist item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while adding the symbol",
        )

    latest_sentiment = await _latest_sentiment_for_symbol(db, new_item.symbol)
    return WatchlistItemOut(
        symbol=new_item.symbol,
        display_name=new_item.display_name,
        added_at=new_item.created_at,
        notes=new_item.notes,
        latest_sentiment=latest_sentiment,
    )


@app.delete("/watchlist/{symbol}", status_code=status.HTTP_204_NO_CONTENT, tags=["Watchlist"])
async def remove_from_watchlist(
    symbol: str = Path(..., min_length=1, max_length=20),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dependency),
):
    """Remove a symbol from the authenticated user's watchlist."""
    symbol = symbol.upper()
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.symbol == symbol,
        )
    )
    item = result.scalars().first()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol '{symbol}' not found on your watchlist",
        )

    try:
        await db.delete(item)
        await db.commit()
        logger.info(f"Watchlist: user {current_user.id} removed {symbol}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error removing watchlist item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while removing the symbol",
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
