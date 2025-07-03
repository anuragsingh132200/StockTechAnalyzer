from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum

class IndicatorType(str, Enum):
    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"

class IndicatorRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    start_date: date = Field(..., description="Start date for analysis")
    end_date: date = Field(..., description="End date for analysis")
    indicator: IndicatorType = Field(..., description="Type of technical indicator")
    
    # Common parameters
    period: Optional[int] = Field(14, ge=2, le=200, description="Period for the indicator")
    
    # SMA/EMA specific
    window: Optional[int] = Field(None, ge=2, le=200, description="Window size for moving averages")
    
    # MACD specific
    fast_period: Optional[int] = Field(12, ge=2, le=50, description="Fast period for MACD")
    slow_period: Optional[int] = Field(26, ge=2, le=100, description="Slow period for MACD")
    signal_period: Optional[int] = Field(9, ge=2, le=50, description="Signal period for MACD")
    
    # Bollinger Bands specific
    std_dev: Optional[float] = Field(2.0, ge=0.5, le=5.0, description="Standard deviation multiplier for Bollinger Bands")
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class IndicatorDataPoint(BaseModel):
    date: date
    value: Optional[float]
    additional_data: Optional[Dict[str, Any]] = None

class MACDDataPoint(BaseModel):
    date: date
    macd: Optional[float]
    signal: Optional[float]
    histogram: Optional[float]

class BollingerBandsDataPoint(BaseModel):
    date: date
    upper_band: Optional[float]
    middle_band: Optional[float]
    lower_band: Optional[float]

class IndicatorResponse(BaseModel):
    symbol: str
    indicator: IndicatorType
    parameters: Dict[str, Any]
    start_date: date
    end_date: date
    data: List[Any]  # Will be specific data points based on indicator type
    
class AvailableSymbolsResponse(BaseModel):
    symbols: List[str]
    count: int

class StockDataPoint(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int

class StockDataResponse(BaseModel):
    symbol: str
    start_date: date
    end_date: date
    data: List[StockDataPoint]
