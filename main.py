import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    description="High-performance API for stock technical analysis with tiered subscription model",
    version="1.0.0",
    lifespan=lifespan
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

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(indicators_router, prefix="/api/indicators", tags=["Technical Indicators"])

@app.get("/")
async def root():
    return {"message": "Stock Technical Analysis API", "version": "1.0.0"}

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
