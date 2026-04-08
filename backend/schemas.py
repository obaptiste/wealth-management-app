# schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any, Literal
from datetime import date, datetime
import re

# Base user schemas
class UserBase(BaseModel):
    """Base schema for user data."""
    username: str = Field(..., min_length=3, max_length=100)
    email: str

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """Schema for updating user data."""
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class UserOut(UserBase):
    """Schema for user data returned to clients."""
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class User(UserOut):
    """Complete user schema for internal use."""
    is_superuser: bool
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Authentication schemas
class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str
    expires_at: datetime

class TokenData(BaseModel):
    """Schema for token payload data."""
    id: Optional[str] = None
    scopes: List[str] = []

# Asset schemas
class AssetBase(BaseModel):
    """Base schema for asset data."""
    symbol: str = Field(..., min_length=1, max_length=20, pattern=r'^[A-Z0-9.]{1,20}$')
    quantity: float = Field(..., gt=0)
    purchase_price: float = Field(..., gt=0)
    purchase_date: datetime
    notes: Optional[str] = None

class AssetCreate(AssetBase):
    """Schema for creating a new asset."""
    pass

class AssetUpdate(BaseModel):
    """Schema for updating asset data."""
    symbol: Optional[str] = Field(None, min_length=1, max_length=20, pattern=r'^[A-Z0-9.]{1,20}$')
    quantity: Optional[float] = Field(None, gt=0)
    purchase_price: Optional[float] = Field(None, gt=0)
    purchase_date: Optional[datetime] = None
    notes: Optional[str] = None

class AssetOut(AssetBase):
    """Schema for asset data returned to clients."""
    id: int
    portfolio_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AssetWithPerformance(AssetOut):
    """Schema for asset data with performance metrics."""
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    last_updated: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# Portfolio schemas
class PortfolioBase(BaseModel):
    """Base schema for portfolio data."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio."""
    pass

class PortfolioUpdate(BaseModel):
    """Schema for updating portfolio data."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class PortfolioSummary(BaseModel):
    """Schema for portfolio performance summary."""
    total_value: float
    total_cost: float
    total_profit_loss: float
    total_profit_loss_percent: float
    last_updated: datetime

class PortfolioOut(PortfolioBase):
    """Schema for portfolio data returned to clients."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    assets: List[AssetOut] = []
    
    model_config = ConfigDict(from_attributes=True)

class PortfolioWithSummary(PortfolioOut):
    """Schema for portfolio data with performance summary."""
    summary: Optional[PortfolioSummary] = None
    
    model_config = ConfigDict(from_attributes=True)


class PortfolioSnapshotHoldingOut(BaseModel):
    """Schema for a single holding captured in a portfolio snapshot."""

    asset_id: Optional[int] = None
    symbol: str
    quantity: float
    price: float
    current_value: float
    allocation_percent: float
    total_cost: float
    profit_loss: float
    profit_loss_percent: float

    model_config = ConfigDict(from_attributes=True)


class PortfolioSnapshotOut(BaseModel):
    """Detailed portfolio snapshot response."""

    portfolio_id: int
    as_of: date
    captured_at: datetime
    summary: PortfolioSummary
    holdings: List[PortfolioSnapshotHoldingOut]


class HistoricalSnapshotPoint(BaseModel):
    """Single chart point derived from a persisted portfolio snapshot."""

    as_of: date
    portfolio_value: float


class PortfolioSnapshotHistoryResponse(BaseModel):
    """Historical portfolio snapshot series."""

    portfolio_id: int
    from_date: date
    to_date: date
    points: List[HistoricalSnapshotPoint]


class PortfolioSnapshotComparisonSummaryOut(BaseModel):
    """Summary deltas between two portfolio snapshots."""

    current_value: float
    previous_value: float
    value_change: float
    value_change_percent: float
    current_cost: float
    previous_cost: float
    cost_change: float
    current_profit_loss: float
    previous_profit_loss: float
    profit_loss_change: float
    current_profit_loss_percent: float
    previous_profit_loss_percent: float
    profit_loss_percent_change: float


class PortfolioSnapshotHoldingDeltaOut(BaseModel):
    """Holding-level delta between two portfolio snapshots."""

    asset_id: Optional[int] = None
    symbol: str
    status: Literal["added", "removed", "changed", "unchanged"]
    current_quantity: float
    previous_quantity: float
    quantity_change: float
    current_price: float
    previous_price: float
    price_change: float
    current_value: float
    previous_value: float
    value_change: float
    current_allocation_percent: float
    previous_allocation_percent: float
    allocation_percent_change: float
    current_profit_loss: float
    previous_profit_loss: float
    profit_loss_change: float


class PortfolioSnapshotComparisonOut(BaseModel):
    """Detailed comparison between two persisted portfolio snapshots."""

    portfolio_id: int
    current_as_of: date
    previous_as_of: date
    summary: PortfolioSnapshotComparisonSummaryOut
    holdings: List[PortfolioSnapshotHoldingDeltaOut]

# Sentiment analysis schemas
class TextInput(BaseModel):
    """Schema for text input for sentiment analysis."""
    text: str = Field(..., min_length=1)

class SentimentOut(BaseModel):
    """Schema for sentiment analysis results."""
    sentiment: str
    confidence: float
    
    model_config = ConfigDict(from_attributes=True)

class SentimentBatchResult(BaseModel):
    """Schema for batch sentiment analysis results."""
    symbol: str
    sentiment_summary: Dict[str, float]
    total_tweets: int
    detailed_sentiments: Optional[List[Dict[str, Any]]] = None

# Currency conversion schemas
class CurrencyConversionRequest(BaseModel):
    """Schema for currency conversion request."""
    from_currency: str = Field(..., alias="from", min_length=3, max_length=3)
    to_currency: str = Field(..., alias="to", min_length=3, max_length=3)
    amount: float = Field(..., gt=0)

    model_config = ConfigDict(populate_by_name=True)

class CurrencyConversionResponse(BaseModel):
    """Schema for currency conversion response."""
    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    exchange_rate: float
    last_updated: datetime

class ExchangeRatesResponse(BaseModel):
    """Schema for exchange rates response."""
    base: str
    rates: Dict[str, float]
    last_updated: datetime

# Insurance schemas
class InsuranceProductBase(BaseModel):
    """Base schema for insurance product data."""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    coverage_amount: float = Field(..., gt=0)
    monthly_premium: float = Field(..., gt=0)
    min_age: int = Field(..., ge=0, le=120)
    max_age: int = Field(..., ge=0, le=120)
    min_income: Optional[float] = Field(None, ge=0)

class InsuranceProductOut(InsuranceProductBase):
    """Schema for insurance product data returned to clients."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InsuranceRecommendationRequest(BaseModel):
    """Schema for insurance recommendation request."""
    age: int = Field(..., ge=18, le=120)
    income: float = Field(..., gt=0)
    dependents: int = Field(..., ge=0)
    has_health_insurance: bool = False
    has_life_insurance: bool = False
    risk_tolerance: str = Field(..., pattern=r'^(low|medium|high)$')

class InsuranceRecommendation(BaseModel):
    """Schema for insurance recommendation."""
    product: InsuranceProductOut
    score: float = Field(..., ge=0, le=100)
    reason: str

class InsuranceRecommendationsResponse(BaseModel):
    """Schema for insurance recommendations response."""
    recommendations: List[InsuranceRecommendation]
    total_recommended_coverage: float
    total_monthly_premium: float

# Pension planning schemas
class PensionPlanBase(BaseModel):
    """Base schema for pension plan data."""
    name: str = Field(..., min_length=1, max_length=100)
    current_age: int = Field(..., ge=18, le=120)
    target_retirement_age: int = Field(..., ge=18, le=120)
    monthly_contribution: float = Field(..., gt=0)
    current_savings: float = Field(default=0.0, ge=0)
    expected_return: float = Field(..., gt=0, le=30)  # Annual return percentage

class PensionPlanCreate(PensionPlanBase):
    """Schema for creating a new pension plan."""
    pass

class PensionPlanUpdate(BaseModel):
    """Schema for updating pension plan data."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_retirement_age: Optional[int] = Field(None, ge=18, le=120)
    monthly_contribution: Optional[float] = Field(None, gt=0)
    current_savings: Optional[float] = Field(None, ge=0)
    expected_return: Optional[float] = Field(None, gt=0, le=30)

class PensionPlanOut(PensionPlanBase):
    """Schema for pension plan data returned to clients."""
    id: int
    user_id: int
    projected_value: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PensionCalculationRequest(BaseModel):
    """Schema for pension calculation request."""
    current_age: int = Field(..., ge=18, le=120)
    retirement_age: int = Field(..., ge=18, le=120)
    monthly_contribution: float = Field(..., gt=0)
    current_savings: float = Field(default=0.0, ge=0)
    expected_return: float = Field(..., gt=0, le=30)  # Annual return percentage

class PensionProjection(BaseModel):
    """Schema for pension projection data."""
    age: int
    year: int
    total_contributions: float
    investment_returns: float
    total_value: float

class PensionCalculationResponse(BaseModel):
    """Schema for pension calculation response."""
    retirement_age: int
    years_to_retirement: int
    total_contributions: float
    projected_value: float
    monthly_retirement_income: float  # Assuming 4% withdrawal rate
    projections: List[PensionProjection]


# Watchlist schemas

class WatchlistItemSentiment(BaseModel):
    """Latest sentiment snapshot attached to a watchlist item."""
    symbol: str
    # score is derived: positive → +confidence, negative → -confidence, neutral → 0.0
    score: float
    # Raw FinBERT label: "positive" | "negative" | "neutral"
    label: str
    confidence: float
    # source_text from the SentimentResult row, or "sentiment_model" if null
    source: str
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistItemCreate(BaseModel):
    """Schema for adding a symbol to the watchlist."""
    symbol: str = Field(..., min_length=1, max_length=20, pattern=r'^[A-Z0-9.]{1,20}$')
    display_name: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class WatchlistItemOut(BaseModel):
    """Schema for a watchlist item returned to clients."""
    symbol: str
    display_name: Optional[str] = None
    added_at: datetime
    notes: Optional[str] = None
    latest_sentiment: Optional[WatchlistItemSentiment] = None

    model_config = ConfigDict(from_attributes=True)
