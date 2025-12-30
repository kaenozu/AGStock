"""
Centralized Configuration Management using Pydantic.
Replaces dispersed os.getenv calls and hardcoded constants.
"""

from typing import Any, List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from dotenv import load_dotenv

# Load .env file explicitly if present
load_dotenv()


class TradingSettings(BaseSettings):
    """Trading-specific configurations."""
    max_daily_trades: int = Field(5, description="Maximum number of trades per day")
    daily_loss_limit_pct: float = Field(-5.0, description="Daily loss limit in percentage")
    max_position_size: float = Field(0.2, description="Max position size as fraction of portfolio")
    min_cash_reserve: float = Field(200000.0, description="Minimum cash to keep in JPY")

    # Risk Management
    initial_stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.10
    trailing_stop_activation_pct: float = 0.03
    trailing_stop_callback_pct: float = 0.02

    # Timeframes
    default_period: str = "2y"
    default_interval: str = "1d"


class AICommitteeSettings(BaseSettings):
    """AI Committee settings."""
    enabled: bool = True
    model_name: str = "gemini-2.0-flash-exp"
    confidence_threshold: float = 0.7
    debate_rounds: int = 3


class SystemSettings(BaseSettings):
    """System-wide infrastructure settings."""
    gemini_api_key: Optional[SecretStr] = Field(None, validation_alias="GEMINI_API_KEY")
    data_dir: Path = Path("data")
    db_path: Path = Path("data/stock_data.db")
    parquet_dir: Path = Path("data/parquet")
    models_dir: Path = Path("models")
    initial_capital: int = 10000000  # Legacy default

    # Caching
    realtime_ttl_seconds: int = 30
    realtime_backoff_seconds: int = 1

    # Evolution
    evolution_interval_days: int = 7
    elite_retention_pct: float = 0.2

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


class RiskManagementSettings(BaseSettings):
    """Risk management settings."""
    max_position_size: float = 0.2


class Config(BaseSettings):
    """Root Configuration Object."""
    trading: TradingSettings = Field(default_factory=TradingSettings)
    ai: AICommitteeSettings = Field(default_factory=AICommitteeSettings)
    system: SystemSettings = Field(default_factory=SystemSettings)
    risk_management: RiskManagementSettings = Field(default_factory=RiskManagementSettings)

    # Other legacy constants mapped
    tickers_jp: List[str] = ["7203.T", "9984.T", "6758.T", "8035.T", "6861.T"]
    tickers_us: List[str] = ["AAPL", "MSFT", "AMZN", "NVDA", "TSLA"]

    def ensure_dirs(self):
        """Create necessary directories."""
        self.system.data_dir.mkdir(parents=True, exist_ok=True)
        self.system.parquet_dir.mkdir(parents=True, exist_ok=True)
        self.system.models_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """後方互換性のためのドット記法アクセス.
        
        Example:
            config.get("trading.max_daily_trades") -> 5
            config.get("system.initial_capital") -> 10000000
        """
        parts = key.split(".")
        obj: Any = self
        try:
            for part in parts:
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    return default
            return obj
        except (AttributeError, KeyError):
            return default


# Singleton wrapper for backward compatibility
class ConfigSingleton:
    """Singleton wrapper for Config."""
    _instance: Optional["ConfigSingleton"] = None
    _config: dict = {}  # Legacy storage
    _pydantic_config: Optional[Config] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._pydantic_config = Config()
            cls._pydantic_config.ensure_dirs()
        return cls._instance

    def __getattr__(self, name: str):
        """Delegate attribute access to underlying Config."""
        if name.startswith("_"):
            return super().__getattribute__(name)
        return getattr(self._pydantic_config, name)

    def get(self, key: str, default: Any = None) -> Any:
        """後方互換性のためのドット記法アクセス."""
        return self._pydantic_config.get(key, default)


# Global Settings Instance (Pydantic)
settings = Config()
settings.ensure_dirs()

# Backward compatible config instance (Singleton)
config = ConfigSingleton()
