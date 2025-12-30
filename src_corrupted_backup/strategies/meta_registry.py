# """
# Meta Registry for Strategy-Regime Mapping.
# Defines which strategies are best suited for specific market conditions.
# """
def get_regime_mapping():
    from src.strategies import (
        BollingerBandsStrategy,
        CombinedStrategy,
        DeepLearningStrategy,
        EnsembleStrategy,
        LightGBMStrategy,
        MultiTimeframeStrategy,
        RLStrategy,
        RSIStrategy,
        SentimentStrategy,
        SMACrossoverStrategy,
        TransformerStrategy,
    )
        universal = [
        EnsembleStrategy,
        SentimentStrategy,
        DeepLearningStrategy,
        LightGBMStrategy,
    ]
        regime_map = {
        "trending_up": [
            SMACrossoverStrategy,
            MultiTimeframeStrategy,
            TransformerStrategy,
        ],
        "trending_down": [
            SMACrossoverStrategy,
            MultiTimeframeStrategy,
        ],
        "ranging": [
            RSIStrategy,
            BollingerBandsStrategy,
        ],
        "low_volatility": [
            RSIStrategy,
            CombinedStrategy,
        ],
        "high_volatility": [
            BollingerBandsStrategy,
            RLStrategy,
        ],
        "uncertain": [
            CombinedStrategy,
        ],
    }
    return universal, regime_map
def get_strategies_for_regime(regime: str) -> list:
    pass
#     """
#     Returns a list of Strategy Classes for the given regime.
#     Always includes UNIVERSAL_STRATEGIES.
#         universal, regime_map = get_regime_mapping()
# # 1. Start with Universal
#     strategy_classes = list(universal)
# # 2. Add Regime Specific
#     specific = regime_map.get(regime, regime_map.get("ranging"))
#     if specific:
    pass
#         for s in specific:
    pass
#             if s not in strategy_classes:
    pass
#                 strategy_classes.append(s)
#         return strategy_classes
# """
