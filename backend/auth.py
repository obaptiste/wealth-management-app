# auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends, HTTPException, status
from typing import Optional
from .database import async_session
from .models import User
from .schemas import UserCreate, TokenData
from .config import settings
from fastapi.security import OAuth2PasswordBearer
from . import models, schemas

# Settings for OAuth2 and JWT token generation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Secret key and algorithm from config
try:
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
except AttributeError as e:
    raise RuntimeError(f"Configuration error: {e}")

# Password context for hashing and verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependency to get DB session
async def get_db():
    session = async_session()
    try:
        yield session
    finally:
        session.close()  # Reverted back to synchronous call since close() is not awaitable

        session.close()

# Verify a password against its hashed version
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Hash a plain password
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Create a JWT access token with an expiration time
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    from datetime import timezone
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Authenticate a user with email and password
async def authenticate_user(db: AsyncSession, email: str, password: str):
    try:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during authentication: {str(e)}"
        )

# Get the current user by validating the JWT token
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token and extract the user ID (sub)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=user_id)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token decode error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Query the database for the user with the given user_id
        result = await db.execute(select(User).where(User.id == token_data.id))
        user = result.scalars().first()
        if user is None:
            raise credentials_exception
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query error: {str(e)}"
        )
    return user

# Check if the current user is active
async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
