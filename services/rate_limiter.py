import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import HTTPException, status

from models import User, Subscription, RateLimit, SubscriptionTier
from config import settings
from utils.exceptions import CustomHTTPException

class RateLimiterService:
    """Service for handling rate limiting based on subscription tiers"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tier_limits = {
            SubscriptionTier.FREE: settings.RATE_LIMIT_FREE,
            SubscriptionTier.PRO: settings.RATE_LIMIT_PRO,
            SubscriptionTier.PREMIUM: settings.RATE_LIMIT_PREMIUM
        }

    async def check_rate_limit(self, 
                              user: User, 
                              subscription: Subscription, 
                              endpoint: str,
                              db: AsyncSession) -> Tuple[bool, Dict[str, int]]:
        """
        Check if user has exceeded rate limit for the endpoint
        Returns: (is_allowed, rate_limit_info)
        """
        try:
            current_time = datetime.now(timezone.utc)
            window_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get or create rate limit record for today
            result = await db.execute(
                select(RateLimit).where(
                    RateLimit.user_id == user.id,
                    RateLimit.endpoint == endpoint,
                    RateLimit.window_start >= window_start
                )
            )
            rate_limit_record = result.scalar_one_or_none()
            
            # Get the limit for user's subscription tier
            daily_limit = self.tier_limits.get(subscription.tier, settings.RATE_LIMIT_FREE)
            
            if rate_limit_record is None:
                # Create new rate limit record
                rate_limit_record = RateLimit(
                    user_id=user.id,
                    endpoint=endpoint,
                    requests_count=1,
                    window_start=window_start
                )
                db.add(rate_limit_record)
                current_count = 1
            else:
                # Update existing record
                current_count = rate_limit_record.requests_count + 1
                await db.execute(
                    update(RateLimit)
                    .where(RateLimit.id == rate_limit_record.id)
                    .values(requests_count=current_count)
                )
            
            await db.commit()
            
            # Check if limit exceeded
            is_allowed = current_count <= daily_limit
            
            rate_limit_info = {
                "requests_made": current_count,
                "daily_limit": daily_limit,
                "remaining": max(0, daily_limit - current_count),
                "reset_time": int((window_start + timedelta(days=1)).timestamp())
            }
            
            if not is_allowed:
                self.logger.warning(
                    f"Rate limit exceeded for user {user.id} on endpoint {endpoint}. "
                    f"Count: {current_count}, Limit: {daily_limit}"
                )
            
            return is_allowed, rate_limit_info
            
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            # In case of error, allow the request but log it
            return True, {
                "requests_made": 0,
                "daily_limit": daily_limit,
                "remaining": daily_limit,
                "reset_time": int((window_start + timedelta(days=1)).timestamp())
            }

    async def increment_rate_limit(self, 
                                  user: User, 
                                  endpoint: str,
                                  db: AsyncSession):
        """Increment rate limit counter for user and endpoint"""
        try:
            current_time = datetime.now(timezone.utc)
            window_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get existing rate limit record
            result = await db.execute(
                select(RateLimit).where(
                    RateLimit.user_id == user.id,
                    RateLimit.endpoint == endpoint,
                    RateLimit.window_start >= window_start
                )
            )
            rate_limit_record = result.scalar_one_or_none()
            
            if rate_limit_record:
                await db.execute(
                    update(RateLimit)
                    .where(RateLimit.id == rate_limit_record.id)
                    .values(requests_count=RateLimit.requests_count + 1)
                )
            else:
                # Create new record
                new_record = RateLimit(
                    user_id=user.id,
                    endpoint=endpoint,
                    requests_count=1,
                    window_start=window_start
                )
                db.add(new_record)
            
            await db.commit()
            
        except Exception as e:
            self.logger.error(f"Error incrementing rate limit: {e}")

    async def get_user_rate_limit_status(self, 
                                       user: User, 
                                       subscription: Subscription,
                                       db: AsyncSession) -> Dict[str, any]:
        """Get current rate limit status for user"""
        try:
            current_time = datetime.now(timezone.utc)
            window_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get all rate limit records for today
            result = await db.execute(
                select(RateLimit).where(
                    RateLimit.user_id == user.id,
                    RateLimit.window_start >= window_start
                )
            )
            rate_limit_records = result.scalars().all()
            
            daily_limit = self.tier_limits.get(subscription.tier, settings.RATE_LIMIT_FREE)
            
            total_requests = sum(record.requests_count for record in rate_limit_records)
            
            return {
                "subscription_tier": subscription.tier.value,
                "daily_limit": daily_limit,
                "total_requests_today": total_requests,
                "remaining_requests": max(0, daily_limit - total_requests),
                "reset_time": int((window_start + timedelta(days=1)).timestamp()),
                "endpoints": {
                    record.endpoint: record.requests_count 
                    for record in rate_limit_records
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting rate limit status: {e}")
            return {
                "subscription_tier": subscription.tier.value,
                "daily_limit": 0,
                "total_requests_today": 0,
                "remaining_requests": 0,
                "reset_time": 0,
                "endpoints": {}
            }

    async def cleanup_old_rate_limits(self, db: AsyncSession, days_old: int = 7):
        """Clean up old rate limit records"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            await db.execute(
                delete(RateLimit).where(RateLimit.window_start < cutoff_date)
            )
            await db.commit()
            
            self.logger.info(f"Cleaned up rate limit records older than {days_old} days")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old rate limits: {e}")
