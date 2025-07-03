import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from database import get_db
from models import User, Subscription, SubscriptionTier
from schemas.auth_schemas import (
    UserCreate, UserLogin, LoginResponse, UserResponse, 
    SubscriptionResponse, UserWithSubscription
)
from auth import auth_service, get_current_user, get_user_with_subscription
from utils.exceptions import CustomHTTPException

auth_router = APIRouter()
logger = logging.getLogger(__name__)

@auth_router.post("/register", response_model=LoginResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    try:
        async with db as session:
            # Check if username already exists
            result = await session.execute(
                select(User).where(User.username == user_data.username)
            )
            if result.scalar_one_or_none():
                raise CustomHTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists",
                    error_code="USERNAME_EXISTS"
                )
            
            # Check if email already exists
            result = await session.execute(
                select(User).where(User.email == user_data.email)
            )
            if result.scalar_one_or_none():
                raise CustomHTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists",
                    error_code="EMAIL_EXISTS"
                )
            
            # Create new user
            hashed_password = auth_service.hash_password(user_data.password)
            new_user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password
            )
            session.add(new_user)
            await session.flush()  # Get the user ID
            
            # Create default subscription (Free tier)
            subscription = Subscription(
                user_id=new_user.id,
                tier=SubscriptionTier.FREE,
                is_active=True
            )
            session.add(subscription)
            await session.commit()
            
            # Refresh to get all data
            await session.refresh(new_user)
            await session.refresh(subscription)
            
            # Generate token
            access_token = auth_service.create_access_token(
                user_id=new_user.id,
                username=new_user.username
            )
            
            logger.info(f"User registered successfully: {new_user.username}")
            
            return LoginResponse(
                access_token=access_token,
                user=UserResponse.model_validate(new_user),
                subscription=SubscriptionResponse.model_validate(subscription)
            )
            
    except CustomHTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user registration: {e}")
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
            error_code="REGISTRATION_FAILED"
        )

@auth_router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return token"""
    try:
        async with db as session:
            # Get user by username
            result = await session.execute(
                select(User, Subscription)
                .join(Subscription)
                .where(User.username == login_data.username, User.is_active == True)
            )
            user_subscription = result.first()
            
            if not user_subscription:
                raise CustomHTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                    error_code="INVALID_CREDENTIALS"
                )
            
            user, subscription = user_subscription
            
            # Verify password
            if not auth_service.verify_password(login_data.password, user.hashed_password):
                raise CustomHTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                    error_code="INVALID_CREDENTIALS"
                )
            
            # Generate token
            access_token = auth_service.create_access_token(
                user_id=user.id,
                username=user.username
            )
            
            logger.info(f"User logged in successfully: {user.username}")
            
            return LoginResponse(
                access_token=access_token,
                user=UserResponse.model_validate(user),
                subscription=SubscriptionResponse.model_validate(subscription)
            )
            
    except CustomHTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user login: {e}")
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
            error_code="LOGIN_FAILED"
        )

@auth_router.get("/me", response_model=UserWithSubscription)
async def get_current_user_info(
    user_subscription: tuple = Depends(get_user_with_subscription)
):
    """Get current user information"""
    user, subscription = user_subscription
    
    user_response = UserResponse.model_validate(user)
    subscription_response = SubscriptionResponse.model_validate(subscription)
    
    return UserWithSubscription(
        **user_response.model_dump(),
        subscription=subscription_response
    )

@auth_router.post("/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    tier: SubscriptionTier,
    user_subscription: tuple = Depends(get_user_with_subscription),
    db: AsyncSession = Depends(get_db)
):
    """Upgrade user subscription tier"""
    try:
        user, subscription = user_subscription
        
        # Validate tier upgrade
        tier_order = [SubscriptionTier.FREE, SubscriptionTier.PRO, SubscriptionTier.PREMIUM]
        current_tier_index = tier_order.index(subscription.tier)
        new_tier_index = tier_order.index(tier)
        
        if new_tier_index <= current_tier_index:
            raise CustomHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only upgrade to a higher tier",
                error_code="INVALID_TIER_UPGRADE"
            )
        
        async with db as session:
            # Update subscription
            subscription.tier = tier
            subscription.updated_at = datetime.now(timezone.utc)
            
            # Set expiration for premium tier (for demo purposes)
            if tier == SubscriptionTier.PREMIUM:
                from datetime import timedelta
                subscription.expires_at = datetime.now(timezone.utc) + timedelta(days=365)
            
            session.add(subscription)
            await session.commit()
            await session.refresh(subscription)
            
            logger.info(f"User {user.username} upgraded to {tier.value} tier")
            
            return SubscriptionResponse.model_validate(subscription)
            
    except CustomHTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Subscription upgrade failed",
            error_code="UPGRADE_FAILED"
        )
