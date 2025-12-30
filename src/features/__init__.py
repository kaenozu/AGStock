"""AGStock features module (maintains backward compatibility)"""

# 既存のエクスポート（future_predictor等が依存）
try:
    from src.enhanced_features import add_technical_indicators
except ImportError:
    def add_technical_indicators(*args, **kwargs):
        raise NotImplementedError("add_technical_indicators not available")

# 新機能
try:
    from src.features.earnings_calendar import (
        EarningsCalendar,
        get_earnings_calendar,
    )
    from src.features.sentiment_indicators import (
        SentimentIndicators,
        SentimentData,
        MarketSentiment,
        get_sentiment_indicators,
    )
    from src.features.drip import (
        DRIPManager,
        DRIPStrategy,
        get_drip_manager,
    )
    from src.features.tax_optimizer import (
        TaxOptimizer,
        HarvestingStrategy,
        get_tax_optimizer,
    )
    from src.features.sector_rotation import (
        SectorRotation,
        EconomicCycle,
        get_sector_rotation,
    )
    NEW_FEATURES_AVAILABLE = True
except ImportError:
    NEW_FEATURES_AVAILABLE = False

__all__ = [
    "add_technical_indicators",
    # 新機能
    "EarningsCalendar",
    "get_earnings_calendar",
    "SentimentIndicators",
    "SentimentData",
    "MarketSentiment",
    "get_sentiment_indicators",
    "DRIPManager",
    "DRIPStrategy",
    "get_drip_manager",
    "TaxOptimizer",
    "HarvestingStrategy",
    "get_tax_optimizer",
    "SectorRotation",
    "EconomicCycle",
    "get_sector_rotation",
]
