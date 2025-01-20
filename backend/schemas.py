from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime


class UserBase(BaseModel):
    name: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)  # For Pydantic v2.x


class User(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)  # For Pydantic v2.x


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None


class AssetBase(BaseModel):
    symbol: str
    quantity: float
    purchase_price: float
    purchase_date: datetime


class AssetCreate(AssetBase):
    pass


class Asset(AssetBase):
    id: int
    portfolio_id: int

    model_config = ConfigDict(from_attributes=True)  # For Pydantic v2.x


class PortfolioOut(BaseModel):
    id: int
    name: str
    owner_id: int
    assets: List[Asset] = []

    model_config = ConfigDict(from_attributes=True)  # For Pydantic v2.x


class PortfolioBase(BaseModel):
    name: str


class PortfolioCreate(PortfolioBase):
    pass


class Portfolio(PortfolioBase):
    id: int
    owner_id: int
    assets: List[Asset] = []

    model_config = ConfigDict(from_attributes=True)  # For Pydantic v2.x


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    assets: Optional[List[Asset]] = None

    model_config = ConfigDict(from_attributes=True)  # For Pydantic v2.x


class AssetUpdate(BaseModel):
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    purchase_price: Optional[float] = None
    purchase_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)  # For Pydantic v2.x


class TextInput(BaseModel):
    text: str
