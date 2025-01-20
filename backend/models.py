from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    portfolios = relationship("Portfolio", back_populates="owner")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Portfolio model
class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="portfolios")
    assets = relationship("Asset", back_populates="portfolio")

# Asset model
class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    quantity = Column(Float)
    purchase_price = Column(Float)
    purchase_date = Column(DateTime)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    portfolio = relationship("Portfolio", back_populates="assets")

# SentimentResult model for sentiment analysis results
class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    sentiment = Column(String)
    confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
