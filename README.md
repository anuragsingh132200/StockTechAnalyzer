<div align="center">
  <h1>📈 Stock Technical Analysis API</h1>
  <p>A high-performance backend API for stock technical analysis with tiered subscription-based access</p>
  
  ![Architecture Diagram](static/image.png)
  
  [![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.115.14-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Docker](https://img.shields.io/badge/Docker-✓-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
  [![Redis](https://img.shields.io/badge/Redis-6.2+-DC382D?logo=redis&logoColor=white)](https://redis.io/)
</div>

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Docker Setup](#docker-setup)
- [API Documentation](#-api-documentation)
- [Subscription Tiers](#-subscription-tiers)
- [Technical Indicators](#-technical-indicators)
- [Rate Limiting](#-rate-limiting)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

- **Multiple Technical Indicators**:
  - Simple Moving Average (SMA)
  - Exponential Moving Average (EMA)
  - Relative Strength Index (RSI)
  - Moving Average Convergence Divergence (MACD)
  - Bollinger Bands

- **Tiered Subscription Model**:
  - Free, Pro, and Premium tiers with different access levels
  - Rate limiting based on subscription tier
  - Data access restrictions by tier

- **High Performance**:
  - Asynchronous API endpoints
  - Redis caching for frequently accessed data
  - Optimized data processing with Polars

- **Security**:
  - JWT Authentication
  - Secure password hashing
  - Rate limiting and request throttling

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
- **Data Processing**: [Polars](https://www.pola.rs/) & [Pandas](https://pandas.pydata.org/)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy](https://www.sqlalchemy.org/)
- **Caching**: [Redis](https://redis.io/)
- **Authentication**: JWT (JSON Web Tokens)
- **API Documentation**: OpenAPI (Swagger UI & ReDoc)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions (sample configuration included)
- **Monitoring**: Prometheus & Grafana (optional)

## 🏗️ Architecture

### High-Level Architecture

![High-Level Architecture](static/one.png)

### Data Flow

1. **Request Handling**:
   - Client sends authenticated requests to the API
   - Rate limiting middleware checks subscription tier and request count
   - Authentication middleware validates JWT tokens

2. **Data Processing**:
   - For indicator calculations, the system first checks Redis cache
   - If not cached, data is loaded from the PostgreSQL database
   - Technical indicators are calculated using Polars for high performance
   - Results are cached in Redis for future requests

3. **Response**:
   - Results are formatted and returned to the client
   - Response includes metadata about the calculation

### Database Schema

![Database Schema](static/two.png)

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 13+
- Redis 6.2+

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/stock-tech-analyzer.git
   cd stock-tech-analyzer
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Initialize the database**:
   ```bash
   python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
   ```

5. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

### Docker Setup

1. **Build and start the services**:
   ```bash
   docker-compose up --build
   ```

2. **Access the services**:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - pgAdmin: http://localhost:5050
     - Email: admin@example.com
     - Password: admin

## 📚 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication

All endpoints (except `/auth` routes) require authentication. Include the JWT token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

### Example Requests

**Get SMA (Simple Moving Average)**:
```http
GET /api/indicators/sma?symbol=AAPL&period=20
Authorization: Bearer <your_jwt_token>
```

**Get RSI (Relative Strength Index)**:
```http
GET /api/indicators/rsi?symbol=MSFT&period=14
Authorization: Bearer <your_jwt_token>
```

## 💎 Subscription Tiers

| Feature | Free | Pro | Premium |
|---------|------|-----|---------|
| Requests/Day | 50 | 500 | Unlimited |
| Indicators | SMA, EMA | SMA, EMA, RSI, MACD | All Indicators |
| Historical Data | 3 months | 1 year | Full 3 years |
| Rate Limit | 10 req/min | 50 req/min | 100 req/min |

## 📊 Technical Indicators

### Available Indicators

1. **Simple Moving Average (SMA)**
   - Calculates the average price over a specific period
   - Configurable window size

2. **Exponential Moving Average (EMA)**
   - Weighted average that gives more importance to recent prices
   - Configurable span

3. **Relative Strength Index (RSI)**
   - Momentum oscillator measuring speed and change of price movements
   - Standard period: 14 days

4. **Moving Average Convergence Divergence (MACD)**
   - Trend-following momentum indicator
   - Configurable fast, slow, and signal periods

5. **Bollinger Bands**
   - Volatility bands placed above and below a moving average
   - Configurable period and standard deviation

## ⚡ Rate Limiting

Rate limiting is applied based on subscription tier:

- **Free Tier**: 50 requests per day
- **Pro Tier**: 500 requests per day
- **Premium Tier**: Unlimited requests

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum number of requests allowed
- `X-RateLimit-Remaining`: Remaining number of requests
- `X-RateLimit-Reset`: Time when the rate limit resets

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
poetry install --with test

# Run tests
pytest

# Run with coverage report
pytest --cov=.
```

## 🚀 Deployment

### Production Deployment

1. **Set up a production database**:
   - Create a managed PostgreSQL instance
   - Set up a Redis instance

2. **Configure environment variables**:
   ```bash
   # .env.production
   DATABASE_URL=postgresql://user:password@production-db:5432/stock_analysis
   REDIS_URL=redis://production-redis:6379/0
   SECRET_KEY=your-secure-secret-key
   DEBUG=False
   ENVIRONMENT=production
   ```

3. **Build and deploy with Docker**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

### Kubernetes Deployment

Sample Kubernetes manifests are provided in the `k8s/` directory.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please open an issue or contact [your-email@example.com](mailto:your-email@example.com).

---

<div align="center">
  Made with ❤️ by Your Name
</div>

## Features

- **Technical Indicators**:
  - Simple Moving Average (SMA)
  - Exponential Moving Average (EMA)
  - Relative Strength Index (RSI)
  - Moving Average Convergence Divergence (MACD)
  - Bollinger Bands

- **Subscription Tiers**:
  - **Free**: 50 requests/day, SMA/EMA, last 3 months data
  - **Pro**: 500 requests/day, SMA/EMA/RSI/MACD, last 1 year data
  - **Premium**: Unlimited requests, all indicators, full 3 years data

- **Tech Stack**:
  - Python 3.9+
  - FastAPI
  - Polars (for high-performance data processing)
  - SQLAlchemy + PostgreSQL
  - Redis (caching)
  - JWT Authentication

## Setup

1. **Prerequisites**:
   - Python 3.9+
   - PostgreSQL
   - Redis
   - Poetry (recommended) or pip

2. **Install dependencies**:
   ```bash
   # Using poetry
   poetry install
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file in the root directory with:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/stock_analysis
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

4. **Database Setup**:
   ```bash
   # Create database tables
   python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
   ```

## Running the Application

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.
```

## Project Structure

```
.
├── main.py                 # Application entry point
├── requirements.txt        # Project dependencies
├── .env.example           # Example environment variables
├── README.md              # This file
├── database.py            # Database configuration
├── models.py              # SQLAlchemy models
├── schemas/               # Pydantic schemas
│   ├── auth_schemas.py
│   └── indicator_schemas.py
├── services/              # Business logic
│   ├── technical_indicators.py
│   ├── data_service.py
│   ├── cache_service.py
│   └── rate_limiter.py
└── routes/                # API routes
    ├── auth_routes.py
    └── indicators_routes.py
```

## Architecture

### High-Level Design

```
┌─────────────┐     ┌─────────────┐     ┌───────────────────┐
│   Client    │────▶│    API      │────▶│  Rate Limiting    │
└─────────────┘     │  Gateway    │     └─────────┬─────────┘
                    └──────┬──────┘               │
                           │               ┌──────▼──────┐
                    ┌──────▼──────┐        │  Auth &     │
                    │   Cache     │        │  AuthZ      │
                    │  (Redis)    │        └──────┬──────┘
                    └──────┬──────┘               │
                           │               ┌──────▼──────┐
                    ┌──────▼──────┐        │  Business   │
                    │   Data      │        │  Logic      │
                    │  (Polars)   │        └──────┬──────┘
                    └─────────────┘               │
                                          ┌──────▼──────┐
                                          │  Database   │
                                          │ (PostgreSQL)│
                                          └─────────────┘
```

## Rate Limiting

Rate limiting is implemented based on user subscription tier:
- Free: 50 requests/day
- Pro: 500 requests/day
- Premium: Unlimited

## Data Loading Strategy

The OHLC data is loaded from a Parquet file into memory using Polars for high-performance processing. The data is:
- Lazily loaded on first request
- Cached in memory for subsequent requests
- Automatically filtered based on user's subscription tier

## Security Considerations

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting to prevent abuse
- Input validation using Pydantic models
- Environment variables for sensitive configuration

## Performance Optimizations

- Efficient data processing with Polars
- Redis caching for frequently accessed data
- Asynchronous processing with FastAPI
- Optimized database queries with SQLAlchemy

## Deployment

### Docker

```bash
docker-compose up --build
```

### Kubernetes

Helm charts and Kubernetes manifests are provided in the `deploy/` directory.

## License

MIT
