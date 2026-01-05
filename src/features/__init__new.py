"""AGStock 新機能モジュール"""

from agstock.src.features.earnings_calendar import (
    EarningsCalendar,
    get_earnings_calendar,
)
from agstock.src.features.sentiment_indicators import (
    SentimentIndicators,
    SentimentData,
    MarketSentiment,
    get_sentiment_indicators,
)
from agstock.src.features.drip import (
    DRIPManager,
    DRIPStrategy,
    get_drip_manager,
)
from agstock.src.features.tax_optimizer import (
    TaxOptimizer,
    HarvestingStrategy,
    get_tax_optimizer,
)
from agstock.src.features.sector_rotation import (
    SectorRotation,
    EconomicCycle,
    get_sector_rotation,
)

__all__ = [
    # Earnings Calendar
    "EarningsCalendar",
    "get_earnings_calendar",
    # Sentiment
    "SentimentIndicators",
    "SentimentData",
    "MarketSentiment",
    "get_sentiment_indicators",
    # DRIP
    "DRIPManager",
    "DRIPStrategy",
    "get_drip_manager",
    # Tax
    "TaxOptimizer",
    "HarvestingStrategy",
    "get_tax_optimizer",
    # Sector Rotation
    "SectorRotation",
    "EconomicCycle",
    "get_sector_rotation",
]
