# AGStock API Reference

## Overview
AGStock provides a comprehensive RESTful API for AI-powered investment trading system integration.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, API uses simple rate limiting. Authentication can be enabled via configuration.

## Endpoints

### Health & System

#### GET /health
System health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "uptime_seconds": 1250.5,
  "components": {
    "database": "connected",
    "ai_system": "active",
    "market_data": "active"
  }
}
```

### Portfolio Management

#### GET /api/v1/portfolio
Retrieve current portfolio information.

**Response:**
```json
{
  "total_value": 1245678.90,
  "cash_balance": 125000.00,
  "positions": {
    "AAPL": {"shares": 100, "value": 175000},
    "MSFT": {"shares": 150, "value": 56250}
  },
  "daily_return": 0.0285,
  "total_return": 0.245,
  "timestamp": "2026-01-05T10:30:00Z"
}
```

#### POST /api/v1/portfolio
Save portfolio state.

**Request:**
```json
{
  "total_value": 1300000,
  "cash_balance": 120000,
  "positions": {"AAPL": {"shares": 110}},
  "daily_return": 0.05,
  "total_return": 0.30
}
```

### Trading

#### GET /api/v1/trades
Retrieve trading history.

**Parameters:**
- `symbol` (optional): Filter by stock symbol
- `limit` (optional): Number of trades (default: 50)

**Response:**
```json
[
  {
    "trade_id": "trade_001",
    "symbol": "AAPL",
    "action": "BUY",
    "quantity": 100,
    "price": 175.50,
    "total": 17550.00,
    "status": "completed",
    "timestamp": "2026-01-05T09:15:00Z"
  }
]
```

#### POST /api/v1/trades
Create new trade.

**Request:**
```json
{
  "symbol": "AAPL",
  "action": "BUY",
  "quantity": 50,
  "order_type": "market"
}
```

### Market Data

#### GET /api/v1/market/{symbol}
Get market data for specific symbol.

**Response:**
```json
{
  "symbol": "AAPL",
  "price": 175.25,
  "change_percent": 1.25,
  "volume": 52341000,
  "timestamp": "2026-01-05T10:30:00Z"
}
```

### Alerts

#### GET /api/v1/alerts
Retrieve alert history.

**Parameters:**
- `status` (optional): Filter by status (active, resolved)
- `severity` (optional): Filter by severity (info, warning, critical)
- `limit` (optional): Number of alerts (default: 50)

**Response:**
```json
[
  {
    "alert_id": "alert_001",
    "alert_type": "price_alert",
    "message": "AAPL price movement: +3.5%",
    "severity": "warning",
    "status": "active",
    "timestamp": "2026-01-05T09:45:00Z"
  }
]
```

#### POST /api/v1/alerts
Create new alert.

**Request:**
```json
{
  "alert_type": "price_alert",
  "title": "Significant Price Movement",
  "message": "AAPL is up 5.2% today",
  "severity": "warning"
}
```

### Configuration

#### GET /api/v1/config
Get system configuration (sensitive data redacted).

**Response:**
```json
{
  "app": {
    "name": "AGStock",
    "version": "3.0.0",
    "mode": "production"
  },
  "trading": {
    "enabled": false,
    "paper_trading": true
  }
}
```

### Audit

#### GET /api/v1/audit
Get audit logs.

**Parameters:**
- `module` (optional): Filter by module
- `action` (optional): Filter by action
- `limit` (optional): Number of logs (default: 100)

## Rate Limiting
- Default: 60 requests per minute
- Burst limit: 10 requests

## Error Handling

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error

### Error Response Format
```json
{
  "error": "Error description",
  "details": {
    "code": "ERROR_CODE",
    "timestamp": "2026-01-05T10:30:00Z"
  }
}
```

## WebSocket Support
Real-time data streaming is available via WebSocket at `/ws`. Currently supports:
- Portfolio updates
- Trade execution notifications
- Market data updates
- Alert notifications

## SDKs and Libraries

### Python
```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Get portfolio
response = requests.get("http://localhost:8000/api/v1/portfolio")
portfolio = response.json()
```

### JavaScript
```javascript
// Using fetch
const response = await fetch('http://localhost:8000/api/v1/portfolio');
const portfolio = await response.json();
```

## API Documentation
Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Support
For API support and questions:
- Documentation: `docs/API_Reference.md`
- Examples: `examples/`
- Issues: GitHub Issues