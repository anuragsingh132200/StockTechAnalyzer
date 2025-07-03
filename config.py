import os
from typing import Optional

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/stock_analysis")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Redis Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL: int = 300  # 5 minutes
    
    # Rate Limiting
    RATE_LIMIT_FREE: int = 50
    RATE_LIMIT_PRO: int = 500
    RATE_LIMIT_PREMIUM: int = 10000  # Effectively unlimited
    
    # Data Access Periods (in days)
    DATA_ACCESS_FREE: int = 90  # 3 months
    DATA_ACCESS_PRO: int = 365  # 1 year
    DATA_ACCESS_PREMIUM: int = 1095  # 3 years
    
    # File paths
    PARQUET_DATA_PATH: str = os.getenv("PARQUET_DATA_PATH", "./attached_assets/stocks_ohlc_data_1751553774887.parquet")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
