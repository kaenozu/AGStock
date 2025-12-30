import json
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, ConfigDict


class BaseStrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra='ignore')


class UserProfile(BaseStrictModel):
    experience: str = "beginner"
    risk_tolerance: str = "low"
    setup_date: str = "2025-01-01"


class CapitalConfig(BaseStrictModel):
    initial_capital: float = 1000000.0
    currency: str = "JPY"


class RiskConfig(BaseStrictModel):
    max_position_size: float = 0.1
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.1


class AutoTradingConfig(BaseStrictModel):
    mode: str = "semi_auto"
    require_approval: bool = True
    max_daily_trades: int = 5
    daily_loss_limit_pct: float = -5.0
    max_vix: float = 40.0


class NotificationChannel(BaseStrictModel):
    enabled: bool = False
    token: Optional[str] = ""
    webhook_url: Optional[str] = ""


class NotificationsConfig(BaseStrictModel):
    enabled: bool = False
    line: NotificationChannel = Field(default_factory=NotificationChannel)
    discord: NotificationChannel = Field(default_factory=NotificationChannel)
    email: Optional[Dict] = None


class PortfolioTargets(BaseStrictModel):
    japan: float = 50.0
    us: float = 30.0
    europe: float = 10.0
    crypto: float = 5.0
    fx: float = 5.0


class StrategiesConfig(BaseStrictModel):
    enabled: List[str] = ["Combined"]
    weights: Dict[str, float] = {"Combined": 1.0}


class AssetsConfig(BaseStrictModel):
    japan_stocks: bool = True
    us_stocks: bool = True
    europe_stocks: bool = False
    crypto: bool = False
    fx: bool = False


class PaperTradingConfig(BaseStrictModel):
    initial_capital: float = 1000000.0
    enabled: bool = True


class MiniStockConfig(BaseStrictModel):
    enabled: bool = False
    unit_size: int = 1
    spread_rate: float = 0.0022
    min_order_amount: float = 500.0
    broker: str = "rakuten_kabumini"
    description: str = "Rakuten Mini Stock"


class AppConfig(BaseStrictModel):
    user_profile: UserProfile = Field(default_factory=UserProfile)
    capital: CapitalConfig = Field(default_factory=CapitalConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    auto_trading: AutoTradingConfig = Field(default_factory=AutoTradingConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    portfolio_targets: PortfolioTargets = Field(default_factory=PortfolioTargets)
    strategies: StrategiesConfig = Field(default_factory=StrategiesConfig)
    assets: AssetsConfig = Field(default_factory=AssetsConfig)
    paper_trading: PaperTradingConfig = Field(default_factory=PaperTradingConfig)
    mini_stock: MiniStockConfig = Field(default_factory=MiniStockConfig)

# AI Agent Constants & Schemas


class TradingDecision(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class AgentAnalysis(BaseStrictModel):
    """Output structure for an AI agent's analysis"""
    agent_name: str
    role: str
    decision: TradingDecision
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.now)


def load_config(config_path: str = "config.json") -> AppConfig:
    if not os.path.exists(config_path):
        return AppConfig()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AppConfig(**data)
    except (json.JSONDecodeError, ValidationError):
        return AppConfig()
