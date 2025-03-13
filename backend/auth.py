# auth.py
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging
from typing import Optional, Dict, Any, Union

from .database import get_db_dependency
from .models import User
from .schemas import TokenData
from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

# OAuth2 password bearer for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Password context for password hashing and verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plain password matches a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the provided data and expiration.
    
    Args:
        data: A dictionary containing the data to encode in the token.
        expires_delta: Optional timedelta for token expiration. If not provided,
                      uses the default expiration from settings.
    
    Returns:
        A JWT token string.
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    # Add expiration to the payload
    to_encode.update({"exp": expire})
    
    # Encode the token
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user from the database by email."""
    try:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()
    except Exception as e:
        logger.error(f"Database error while getting user by email: {str(e)}")
        return None

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Union[User, bool]:
    """
    Authenticate a user with email and password.
    
    Args:
        db: Database session.
        email: User's email.
        password: User's password.
    
    Returns:
        User object if authentication is successful, False otherwise.
    """
    try:
        # Get user by email
        user = await get_user_by_email(db, email)
        
        # Check if user exists
        if not user:
            return False
        
        # Verify password - use is not None rather than direct boolean evaluation
        if user.hashed_password is None or not verify_password(password, str(user.hashed_password)):
            return False
        
        return user
    except Exception as e:
        logger.error(f"Error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during authentication: {str(e)}"
        )

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_dependency)
) -> User:
    """
    Get the current user by validating the JWT token.
    
    Args:
        token: JWT token from the Authorization header.
        db: Database session.
    
    Returns:
        User object for the authenticated user.
    
    Raises:
        HTTPException: If the token is invalid or the user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        # Extract user ID from token
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        if user_id is None:
            raise credentials_exception
        
        # Create token data
        token_data = TokenData(id=user_id)
    except JWTError as e:
        logger.error(f"Token validation error: {str(e)}")
        raise credentials_exception
    
    try:
        # Get user from database
        if token_data.id is None:
            raise credentials_exception
        result = await db.execute(select(User).where(User.id == int(token_data.id)))
        user = result.scalars().first()
        
        if user is None:
            logger.warning(f"User with ID {token_data.id} not found")
            raise credentials_exception
            
        return user
    except ValueError:
        # Handle case where token_data.id is not a valid integer
        logger.error(f"Invalid user ID in token: {token_data.id}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Database error while getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: User object from get_current_user dependency.
    
    Returns:
        User object if the user is active.
    
    Raises:
        HTTPException: If the user is not active.
    """
    # Check if user has is_active attribute and if it's False
    if hasattr(current_user, 'is_active') and current_user.is_active is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user