"""
Custom Exception Hierarchy for AGStock
Provides specific exception types for better error handling.
"""


class AGStockException(Exception):
    """Base exception for all AGStock errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DataFetchError(AGStockException):
    """Raised when data fetching fails."""
    pass


class DataValidationError(AGStockException):
    """Raised when data validation fails."""
    pass


class TradingError(AGStockException):
    """Raised when trading operations fail."""
    pass


class InsufficientFundsError(TradingError):
    """Raised when there are insufficient funds for a trade."""
    pass


class InvalidOrderError(TradingError):
    """Raised when an order is invalid."""
    pass


class StrategyError(AGStockException):
    """Raised when strategy execution fails."""
    pass


class PredictionError(AGStockException):
    """Raised when prediction fails."""
    pass


class ConfigurationError(AGStockException):
    """Raised when configuration is invalid."""
    pass


class APIError(AGStockException):
    """Raised when external API calls fail."""
    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    pass


class CacheError(AGStockException):
    """Raised when cache operations fail."""
    pass
