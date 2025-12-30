
"""
Centralized Configuration Management using Pydantic.
Replaces dispersed os.getenv calls and hardcoded constants.
"""

import os
from typing import List, Dict, Optional, Any
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
    
    # Caching
    realtime_ttl_seconds: int = 30
    realtime_backoff_seconds: int = 1
    
    # Evolution
    evolution_interval_days: int = 7
    elite_retention_pct: float = 0.2

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # Ignore extra env vars

class Config(BaseSettings):
    """Root Configuration Object."""
    trading: TradingSettings = Field(default_factory=TradingSettings)
    ai: AICommitteeSettings = Field(default_factory=AICommitteeSettings)
    system: SystemSettings = Field(default_factory=SystemSettings)
    
    # Other legacy constants mapped
    tickers_jp: List[str] = ["7203.T", "9984.T", "6758.T", "8035.T", "6861.T"]
    tickers_us: List[str] = ["AAPL", "MSFT", "AMZN", "NVDA", "TSLA"]
    
    def ensure_dirs(self):
        """Create necessary directories."""
        self.system.data_dir.mkdir(parents=True, exist_ok=True)
        self.system.parquet_dir.mkdir(parents=True, exist_ok=True)
        self.system.models_dir.mkdir(parents=True, exist_ok=True)

# Global Settings Instance
settings = Config()
settings.ensure_dirs()
