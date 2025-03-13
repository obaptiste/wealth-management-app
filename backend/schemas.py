# schemas.py
from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import re

# Base user schemas
class UserBase(BaseModel):
    """Base schema for user data."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
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