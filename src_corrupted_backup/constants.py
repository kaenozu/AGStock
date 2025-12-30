# """Project-wide constants (trimmed to essential values for tests and defaults)."""

# Force Reload
from datetime import timedelta

# Realtime / caching defaults
DEFAULT_REALTIME_TTL_SECONDS = 30
DEFAULT_REALTIME_BACKOFF_SECONDS = 1
DEFAULT_PAPER_TRADER_REFRESH_INTERVAL = 300
PAPER_TRADER_REALTIME_FALLBACK_DEFAULT = False
STALE_DATA_MAX_AGE = timedelta(days=2)
MINIMUM_DATA_POINTS = 50
MARKET_SUMMARY_CACHE_KEY = "market_summary_snapshot"
MARKET_SUMMARY_TTL = 1800
FUNDAMENTAL_CACHE_TTL = 86400
# Volatility symbols
DEFAULT_VOLATILITY_SYMBOL = "^VIX"
FALLBACK_VOLATILITY_SYMBOLS = ["^VIX", "^VXO"]
# Asset universes (small but deterministic for tests)
NIKKEI_225_TICKERS = ["7203.T", "9984.T", "6758.T"]  # Toyota, SoftBank, Sony
JP_STOCKS = NIKKEI_225_TICKERS
SP500_TICKERS = ["AAPL", "MSFT", "AMZN"]
STOXX50_TICKERS = ["ASML.AS", "SAP.DE", "TTE.PA"]
# Name mapping (must align 1:1 with NIKKEI_225_TICKERS for tests)
TICKER_NAMES = {
    "7203.T": "Toyota Motor",
    "9984.T": "SoftBank Group",
    "6758.T": "Sony Group",
}
# Crypto / FX pairs (minimal)
CRYPTO_PAIRS = ["BTC-USD", "ETH-USD"]
FX_PAIRS = ["USDJPY", "EURUSD"]
# Basic market labels used in UI tabs (dict形式でマーケット→ティッカーリスト)
MARKETS = {
    "Japan": NIKKEI_225_TICKERS,
    "US": SP500_TICKERS,
    "Europe": STOXX50_TICKERS,
    "Crypto": CRYPTO_PAIRS,
    "FX": FX_PAIRS,
}
# Backtest defaults
BACKTEST_DEFAULT_INITIAL_CAPITAL = 1_000_000
BACKTEST_DEFAULT_POSITION_SIZE = 0.1
BACKTEST_DEFAULT_COMMISSION_RATE = 0.0005
BACKTEST_DEFAULT_SLIPPAGE_RATE = 0.0005
BACKTEST_DEFAULT_STOP_LOSS_PCT = 0.05
BACKTEST_DEFAULT_TAKE_PROFIT_PCT = 0.10
BACKTEST_MIN_TRAINING_PERIOD_DAYS = 252
BACKTEST_RETRAIN_PERIOD_DAYS = 30
# Sector rotation mappings (minimal set)
SECTOR_ETFS = {
    "XLK": "Technology",
    "XLE": "Energy",
    "XLU": "Utilities",
    "XLV": "Healthcare",
    "XLF": "Financials",
    "XLI": "Industrials",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
}
# Simple market index map (used lightly)
