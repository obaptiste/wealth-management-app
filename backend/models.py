# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime, timezone

from .database import Base

class TimestampMixin:
    """Mixin that adds created_at and updated_at columns to models."""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )

class User(Base, TimestampMixin):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    portfolios = relationship("Portfolio", back_populates="owner")
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class Portfolio(Base, TimestampMixin):
    """Portfolio model for managing a collection of assets."""
    
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="portfolios")
    assets = relationship("Asset", back_populates="portfolio", cascade="all, delete-orphan")
    
    # Add composite index for faster lookups by owner
    __table_args__ = (
        Index('idx_portfolio_owner_name', 'owner_id', 'name'),
    )
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"

class Asset(Base, TimestampMixin):
    """Asset model for representing a financial asset in a portfolio."""
    
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    quantity = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="assets")
    price_history = relationship("AssetPriceHistory", back_populates="asset", cascade="all, delete-orphan")
    
    # Add index for faster symbol lookups within a portfolio
    __table_args__ = (
        Index('idx_asset_portfolio_symbol', 'portfolio_id', 'symbol'),
    )
    
    def __repr__(self):
        return f"<Asset(id={self.id}, symbol='{self.symbol}', quantity={self.quantity})>"

class AssetPriceHistory(Base, TimestampMixin):
    """Model for tracking historical prices of assets."""
    
    __tablename__ = "asset_price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Relationships
    asset = relationship("Asset", back_populates="price_history")
    
    # Add index for faster timestamp lookups
    __table_args__ = (
        Index('idx_price_history_asset_time', 'asset_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AssetPriceHistory(id={self.id}, asset_id={self.asset_id}, price={self.price})>"

class SentimentResult(Base, TimestampMixin):
    """Model for storing sentiment analysis results."""
    
    __tablename__ = "sentiment_results"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    sentiment = Column(String(20), nullable=False)  # positive, negative, neutral
    confidence = Column(Float, nullable=False)
    source_text = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SentimentResult(id={self.id}, symbol='{self.symbol}', sentiment='{self.sentiment}')>"