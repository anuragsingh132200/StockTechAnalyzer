# Stock Technical Analysis API

## Overview

This is a high-performance FastAPI-based backend system for stock technical analysis with a tiered subscription model. The application provides technical indicators calculation for stock data through RESTful APIs, implementing authentication, authorization, rate limiting, and caching mechanisms. The system is designed to handle multiple subscription tiers (Free, Pro, Premium) with different access levels and rate limits.

## System Architecture

### Technology Stack
- **Backend Framework**: FastAPI with Python 3.9+
- **Database**: PostgreSQL with SQLAlchemy ORM (async)
- **Data Processing**: Polars for high-performance data manipulation
- **Caching**: Redis for performance optimization
- **Authentication**: JWT-based authentication with bcrypt password hashing
- **ASGI Server**: Uvicorn for async request handling

### Architecture Pattern
The application follows a layered architecture with clear separation of concerns:
- **Routes Layer**: FastAPI routers handling HTTP requests
- **Services Layer**: Business logic and data processing
- **Models Layer**: SQLAlchemy models for database entities
- **Schemas Layer**: Pydantic models for request/response validation
- **Utils Layer**: Common utilities and configurations

## Key Components

### Authentication & Authorization
- JWT-based authentication system with configurable expiration
- User registration and login with secure password hashing using bcrypt
- Subscription-based authorization with three tiers: Free, Pro, Premium
- Session management and token validation middleware

### Data Management
- **DataService**: Handles loading and management of stock OHLC data from Parquet files
- Supports multiple stock symbols with 3 years of historical data
- Efficient data filtering based on subscription tier access periods
- Fallback mechanism to generate sample data if source file is unavailable

### Technical Indicators
- **TechnicalIndicatorService**: Implements various technical analysis indicators
- Supported indicators: SMA, EMA, RSI, MACD, Bollinger Bands
- Configurable parameters for each indicator (periods, windows, multipliers)
- High-performance calculations using Polars DataFrame operations

### Rate Limiting
- **RateLimiterService**: Implements subscription-based rate limiting
- Daily request limits: Free (50), Pro (500), Premium (unlimited)
- Per-endpoint rate tracking with database persistence
- Automatic rate limit reset based on daily windows

### Caching System
- **CacheService**: Redis-based caching for improved performance
- Configurable TTL (5 minutes default)
- Hash-based cache key generation for complex parameters
- Graceful fallback when Redis is unavailable

## Data Flow

1. **Authentication Flow**:
   - User registers/logs in → JWT token generated → Token validated on subsequent requests
   - User subscription tier determined → Access permissions established

2. **Request Processing Flow**:
   - Incoming request → Rate limit check → Authentication validation → Data retrieval → Indicator calculation → Response caching → JSON response

3. **Data Access Flow**:
   - Request parameters validated → Subscription tier access period applied → Data filtered from Parquet source → Technical indicators calculated → Results formatted and returned

## External Dependencies

### Database Dependencies
- PostgreSQL for user management, subscriptions, and rate limiting data
- Connection pooling with configurable pool size and overflow
- Async database operations using asyncpg driver

### Cache Dependencies
- Redis for performance caching (optional but recommended)
- Configurable connection parameters and timeout settings
- Graceful degradation when cache is unavailable

### Data Dependencies
- Parquet file containing stock OHLC data (3 years historical data)
- Support for multiple stock symbols with date, open, high, low, close, volume columns
- Sample data generation capability for demonstration purposes

## Deployment Strategy

### Environment Configuration
- Environment-based configuration through config.py
- Configurable database URLs, JWT secrets, Redis connections
- Separate settings for development, staging, and production environments

### Application Lifecycle
- Startup: Database initialization, cache service setup, data loading
- Runtime: Async request handling with connection pooling
- Shutdown: Graceful cleanup of database connections and cache

### Scalability Considerations
- Async database operations for high concurrency
- Connection pooling for efficient resource utilization
- Redis caching for reduced database load
- Stateless design for horizontal scaling capability

## Changelog

```
Changelog:
- July 03, 2025. Initial setup
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```