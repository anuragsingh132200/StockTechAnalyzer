import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database import get_db
from models import User, Subscription
from utils.exceptions import CustomHTTPException

security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_hours = settings.JWT_EXPIRATION_HOURS

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def create_access_token(self, user_id: int, username: str) -> str:
        """Create a JWT access token"""
        expire = datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours)
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise CustomHTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                error_code="TOKEN_EXPIRED"
            )
        except jwt.InvalidTokenError:
            raise CustomHTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                error_code="INVALID_TOKEN"
            )

auth_service = AuthService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user"""
    try:
        payload = auth_service.decode_token(credentials.credentials)
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise CustomHTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                error_code="INVALID_TOKEN_PAYLOAD"
            )
        
        # Get user from database
        async with db as session:
            result = await session.execute(
                select(User).where(User.id == user_id, User.is_active == True)
            )
            user = result.scalar_one_or_none()
            
            if user is None:
                raise CustomHTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                    error_code="USER_NOT_FOUND"
                )
            
            return user
            
    except CustomHTTPException:
        raise
    except Exception as e:
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            error_code="AUTH_FAILED"
        )

async def get_user_with_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> tuple[User, Subscription]:
    """Get current user with their subscription"""
    async with db as session:
        result = await session.execute(
            select(User, Subscription)
            .join(Subscription)
            .where(User.id == current_user.id)
        )
        user_subscription = result.first()
        
        if user_subscription is None:
            raise CustomHTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User subscription not found",
                error_code="SUBSCRIPTION_NOT_FOUND"
            )
        
        return user_subscription[0], user_subscription[1]
