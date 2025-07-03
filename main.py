import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from database import init_db, get_db
from models import User, Subscription
from routes.auth_routes import auth_router
from routes.indicators_routes import indicators_router
from utils.exceptions import CustomHTTPException
from utils.logging_config import setup_logging
from services.cache_service import CacheService
from services.data_service import DataService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    setup_logging()
    logging.info("Starting FastAPI application")
    
    # Initialize database
    await init_db()
    
    # Initialize cache service
    cache_service = CacheService()
    app.state.cache_service = cache_service
    
    # Initialize data service
    data_service = DataService()
    await data_service.load_data()
    app.state.data_service = data_service
    
    logging.info("Application startup complete")
    
    yield
    
    # Shutdown
    logging.info("Shutting down application")


app = FastAPI(
    title="Stock Technical Analysis API",
    description="""
    ## Professional Stock Technical Analysis API 📊

    This API provides comprehensive technical analysis tools for stock market data with a tiered subscription model.

    ### Features:
    * **JWT Authentication** - Secure user registration and login
    * **Technical Indicators** - SMA, EMA, RSI, MACD, Bollinger Bands
    * **Rate Limiting** - Subscription-based daily limits (50/500/unlimited)
    * **Data Access** - Historical data based on tier (3 months/1 year/3 years)
    * **Caching** - Redis-powered performance optimization
    * **Real Data** - 1168+ stock symbols with 3 years of historical data

    ### Getting Started:
    1. **Register** a new account at `/api/auth/register`
    2. **Login** to get your JWT token at `/api/auth/login`
    3. **Use the token** in the Authorization header: `Bearer <your-token>`
    4. **Test endpoints** using this interactive documentation

    ### Subscription Tiers:
    - **Free**: 50 requests/day, SMA & EMA indicators, 3 months data
    - **Pro**: 500 requests/day, SMA, EMA, RSI & MACD indicators, 1 year data  
    - **Premium**: Unlimited requests, all indicators, 3 years data

    ### Authentication:
    Use the **Authorize** button below to add your JWT token for testing protected endpoints.
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(CustomHTTPException)
async def custom_exception_handler(request: Request, exc: CustomHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "error_code": exc.error_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "error_code": "INTERNAL_ERROR"}
    )

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(indicators_router, prefix="/api/indicators", tags=["Technical Indicators"])

@app.get("/")
async def root():
    return FileResponse('static/index.html')

@app.get("/api")
async def api_info():
    return {
        "message": "Stock Technical Analysis API", 
        "version": "1.0.0",
        "documentation": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "authentication": "/api/auth",
            "indicators": "/api/indicators",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        log_level="info"
    )
