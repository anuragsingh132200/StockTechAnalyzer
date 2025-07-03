import polars as pl
import logging
from typing import List, Optional, Set
from datetime import date, datetime, timedelta
import os

from config import settings
from utils.exceptions import CustomHTTPException

class DataService:
    """Service for managing stock data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data: Optional[pl.DataFrame] = None
        self.available_symbols: Set[str] = set()
        self.data_loaded = False

    async def load_data(self):
        """Load data from parquet file"""
        try:
            if not os.path.exists(settings.PARQUET_DATA_PATH):
                # Create sample data if file doesn't exist
                self.logger.warning(f"Parquet file not found at {settings.PARQUET_DATA_PATH}, creating sample data")
                self._create_sample_data()
            else:
                self.data = pl.read_parquet(settings.PARQUET_DATA_PATH)
            
            # Convert date column to date type if it's not already
            if 'date' in self.data.columns:
                self.data = self.data.with_columns([
                    pl.col("date").cast(pl.Date).alias("date")
                ])
            
            # Get available symbols
            self.available_symbols = set(self.data.select("symbol").unique().to_series().to_list())
            
            self.data_loaded = True
            self.logger.info(f"Data loaded successfully. {len(self.available_symbols)} symbols available")
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise CustomHTTPException(
                status_code=500,
                detail="Failed to load stock data",
                error_code="DATA_LOAD_ERROR"
            )

    def _create_sample_data(self):
        """Create sample data for demonstration"""
        import random
        import numpy as np
        from datetime import date, timedelta
        
        # Generate sample data for demonstration
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        start_date = date.today() - timedelta(days=1095)  # 3 years
        dates = []
        data_rows = []
        
        for i in range(1095):
            current_date = start_date + timedelta(days=i)
            # Skip weekends for stock data
            if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
                dates.append(current_date)
        
        for symbol in symbols:
            base_price = random.uniform(50, 300)
            
            for i, date_val in enumerate(dates):
                # Generate realistic OHLC data with some trend and volatility
                trend = 0.0001 * i  # Small upward trend
                volatility = random.uniform(-0.05, 0.05)
                
                if i == 0:
                    open_price = base_price
                else:
                    open_price = data_rows[-1]['close'] if data_rows and data_rows[-1]['symbol'] == symbol else base_price
                
                change = (trend + volatility) * open_price
                close_price = max(open_price + change, 1.0)  # Ensure positive price
                
                high_price = max(open_price, close_price) * random.uniform(1.001, 1.05)
                low_price = min(open_price, close_price) * random.uniform(0.95, 0.999)
                volume = random.randint(100000, 10000000)
                
                data_rows.append({
                    'date': date_val,
                    'symbol': symbol,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume
                })
        
        self.data = pl.DataFrame(data_rows)
        self.logger.info("Sample data created successfully")

    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols"""
        if not self.data_loaded:
            raise CustomHTTPException(
                status_code=500,
                detail="Data not loaded",
                error_code="DATA_NOT_LOADED"
            )
        return sorted(list(self.available_symbols))

    def get_stock_data(self, symbol: str, start_date: date, end_date: date) -> pl.DataFrame:
        """Get stock data for a specific symbol and date range"""
        if not self.data_loaded:
            raise CustomHTTPException(
                status_code=500,
                detail="Data not loaded",
                error_code="DATA_NOT_LOADED"
            )
        
        if symbol not in self.available_symbols:
            raise CustomHTTPException(
                status_code=404,
                detail=f"Symbol {symbol} not found",
                error_code="SYMBOL_NOT_FOUND"
            )
        
        try:
            filtered_data = self.data.filter(
                (pl.col("symbol") == symbol) &
                (pl.col("date") >= start_date) &
                (pl.col("date") <= end_date)
            ).sort("date")
            
            return filtered_data
            
        except Exception as e:
            self.logger.error(f"Error filtering stock data: {e}")
            raise CustomHTTPException(
                status_code=500,
                detail="Failed to retrieve stock data",
                error_code="DATA_RETRIEVAL_ERROR"
            )

    def validate_date_range_for_tier(self, start_date: date, end_date: date, tier: str):
        """Validate if the date range is allowed for the user's subscription tier"""
        today = date.today()
        
        if tier == "free":
            max_days_back = settings.DATA_ACCESS_FREE
        elif tier == "pro":
            max_days_back = settings.DATA_ACCESS_PRO
        elif tier == "premium":
            max_days_back = settings.DATA_ACCESS_PREMIUM
        else:
            raise CustomHTTPException(
                status_code=400,
                detail="Invalid subscription tier",
                error_code="INVALID_TIER"
            )
        
        earliest_allowed_date = today - timedelta(days=max_days_back)
        
        if start_date < earliest_allowed_date:
            raise CustomHTTPException(
                status_code=403,
                detail=f"Start date too far back for {tier} tier. Earliest allowed: {earliest_allowed_date}",
                error_code="DATE_RANGE_RESTRICTED"
            )
