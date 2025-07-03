import logging
from typing import List
from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from auth import get_user_with_subscription
from models import User, Subscription, SubscriptionTier
from schemas.indicator_schemas import (
    IndicatorRequest, IndicatorResponse, AvailableSymbolsResponse,
    StockDataResponse, StockDataPoint, IndicatorType
)
from services.technical_indicators import TechnicalIndicatorService
from services.data_service import DataService
from services.cache_service import CacheService
from services.rate_limiter import RateLimiterService
from utils.exceptions import CustomHTTPException

indicators_router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
technical_service = TechnicalIndicatorService()
rate_limiter = RateLimiterService()

def get_data_service(request: Request) -> DataService:
    return request.app.state.data_service

def get_cache_service(request: Request) -> CacheService:
    return request.app.state.cache_service

@indicators_router.get("/symbols", response_model=AvailableSymbolsResponse)
async def get_available_symbols(
    data_service: DataService = Depends(get_data_service),
    user_subscription: tuple = Depends(get_user_with_subscription),
    db: AsyncSession = Depends(get_db)
):
    """Get list of available stock symbols"""
    try:
        user, subscription = user_subscription
        
        # Check rate limit
        is_allowed, rate_info = await rate_limiter.check_rate_limit(
            user, subscription, "symbols", db
        )
        
        if not is_allowed:
            raise CustomHTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Daily limit: {rate_info['daily_limit']}",
                error_code="RATE_LIMIT_EXCEEDED"
            )
        
        symbols = data_service.get_available_symbols()
        
        return AvailableSymbolsResponse(
            symbols=symbols,
            count=len(symbols)
        )
        
    except CustomHTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        raise CustomHTTPException(
            status_code=500,
            detail="Failed to retrieve available symbols",
            error_code="SYMBOLS_RETRIEVAL_ERROR"
        )

@indicators_router.get("/data/{symbol}", response_model=StockDataResponse)
async def get_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
    data_service: DataService = Depends(get_data_service),
    cache_service: CacheService = Depends(get_cache_service),
    user_subscription: tuple = Depends(get_user_with_subscription),
    db: AsyncSession = Depends(get_db)
):
    """Get raw stock data for a symbol"""
    try:
        from datetime import datetime
        
        user, subscription = user_subscription
        
        # Check rate limit
        is_allowed, rate_info = await rate_limiter.check_rate_limit(
            user, subscription, "stock_data", db
        )
        
        if not is_allowed:
            raise CustomHTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Daily limit: {rate_info['daily_limit']}",
                error_code="RATE_LIMIT_EXCEEDED"
            )
        
        # Parse dates
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Validate date range for subscription tier
        data_service.validate_date_range_for_tier(
            start_date_obj, end_date_obj, subscription.tier.value
        )
        
        # Check cache first
        cache_key_params = {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date
        }
        cached_data = await cache_service.get("stock_data", **cache_key_params)
        
        if cached_data:
            logger.info(f"Returning cached stock data for {symbol}")
            return StockDataResponse(**cached_data)
        
        # Get data from service
        df = data_service.get_stock_data(symbol, start_date_obj, end_date_obj)
        
        # Convert to response format
        stock_data = [
            StockDataPoint(
                date=row['date'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
            for row in df.to_dicts()
        ]
        
        response = StockDataResponse(
            symbol=symbol,
            start_date=start_date_obj,
            end_date=end_date_obj,
            data=stock_data
        )
        
        # Cache the response
        await cache_service.set("stock_data", response.model_dump(), **cache_key_params)
        
        return response
        
    except CustomHTTPException:
        raise
    except ValueError as e:
        raise CustomHTTPException(
            status_code=400,
            detail=f"Invalid date format: {str(e)}",
            error_code="INVALID_DATE_FORMAT"
        )
    except Exception as e:
        logger.error(f"Error getting stock data: {e}")
        raise CustomHTTPException(
            status_code=500,
            detail="Failed to retrieve stock data",
            error_code="STOCK_DATA_ERROR"
        )

@indicators_router.post("/calculate", response_model=IndicatorResponse)
async def calculate_indicator(
    request_data: IndicatorRequest,
    data_service: DataService = Depends(get_data_service),
    cache_service: CacheService = Depends(get_cache_service),
    user_subscription: tuple = Depends(get_user_with_subscription),
    db: AsyncSession = Depends(get_db)
):
    """Calculate technical indicator for a stock"""
    try:
        user, subscription = user_subscription
        
        # Check rate limit
        is_allowed, rate_info = await rate_limiter.check_rate_limit(
            user, subscription, "calculate_indicator", db
        )
        
        if not is_allowed:
            raise CustomHTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Daily limit: {rate_info['daily_limit']}",
                error_code="RATE_LIMIT_EXCEEDED"
            )
        
        # Validate indicator access for subscription tier
        allowed_indicators = _get_allowed_indicators(subscription.tier)
        if request_data.indicator not in allowed_indicators:
            raise CustomHTTPException(
                status_code=403,
                detail=f"Indicator {request_data.indicator} not available for {subscription.tier.value} tier",
                error_code="INDICATOR_NOT_ALLOWED"
            )
        
        # Validate date range for subscription tier
        data_service.validate_date_range_for_tier(
            request_data.start_date, request_data.end_date, subscription.tier.value
        )
        
        # Generate cache key
        cache_key_params = {
            "symbol": request_data.symbol,
            "start_date": str(request_data.start_date),
            "end_date": str(request_data.end_date),
            "indicator": request_data.indicator.value,
            "parameters": request_data.model_dump(exclude={"symbol", "start_date", "end_date", "indicator"})
        }
        
        # Check cache first
        cached_data = await cache_service.get("indicator", **cache_key_params)
        if cached_data:
            logger.info(f"Returning cached indicator data for {request_data.symbol}")
            return IndicatorResponse(**cached_data)
        
        # Get stock data
        df = data_service.get_stock_data(
            request_data.symbol, 
            request_data.start_date, 
            request_data.end_date
        )
        
        if df.height == 0:
            raise CustomHTTPException(
                status_code=404,
                detail=f"No data found for symbol {request_data.symbol} in the specified date range",
                error_code="NO_DATA_FOUND"
            )
        
        # Prepare parameters
        parameters = {}
        if request_data.indicator in [IndicatorType.SMA, IndicatorType.EMA]:
            parameters['period'] = request_data.window or request_data.period
        elif request_data.indicator == IndicatorType.RSI:
            parameters['period'] = request_data.period
        elif request_data.indicator == IndicatorType.MACD:
            parameters.update({
                'fast_period': request_data.fast_period,
                'slow_period': request_data.slow_period,
                'signal_period': request_data.signal_period
            })
        elif request_data.indicator == IndicatorType.BOLLINGER_BANDS:
            parameters.update({
                'period': request_data.period,
                'std_dev': request_data.std_dev
            })
        
        # Calculate indicator
        indicator_data = technical_service.process_indicator_request(
            df, request_data.indicator, parameters
        )
        
        response = IndicatorResponse(
            symbol=request_data.symbol,
            indicator=request_data.indicator,
            parameters=parameters,
            start_date=request_data.start_date,
            end_date=request_data.end_date,
            data=indicator_data
        )
        
        # Cache the response
        await cache_service.set("indicator", response.model_dump(), **cache_key_params)
        
        return response
        
    except CustomHTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating indicator: {e}")
        raise CustomHTTPException(
            status_code=500,
            detail="Failed to calculate indicator",
            error_code="INDICATOR_CALCULATION_ERROR"
        )

@indicators_router.get("/rate-limit-status")
async def get_rate_limit_status(
    user_subscription: tuple = Depends(get_user_with_subscription),
    db: AsyncSession = Depends(get_db)
):
    """Get current rate limit status for the user"""
    try:
        user, subscription = user_subscription
        
        status = await rate_limiter.get_user_rate_limit_status(user, subscription, db)
        return status
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        raise CustomHTTPException(
            status_code=500,
            detail="Failed to retrieve rate limit status",
            error_code="RATE_LIMIT_STATUS_ERROR"
        )

def _get_allowed_indicators(tier: SubscriptionTier) -> List[IndicatorType]:
    """Get allowed indicators for a subscription tier"""
    if tier == SubscriptionTier.FREE:
        return [IndicatorType.SMA, IndicatorType.EMA]
    elif tier == SubscriptionTier.PRO:
        return [IndicatorType.SMA, IndicatorType.EMA, IndicatorType.RSI, IndicatorType.MACD]
    elif tier == SubscriptionTier.PREMIUM:
        return list(IndicatorType)
    else:
        return []
