"""
戦略モジュール

このモジュールは後方互換性のため、全ての戦略クラスを
インポートして提供します。
"""

# 基底クラス
from src.strategies.base import Strategy, Order, OrderType

# テクニカル戦略（将来的に分割予定）
from src.strategies_legacy import (
    SMACrossoverStrategy,
    RSIStrategy,
    BollingerBandsStrategy,
    CombinedStrategy,
)

# ML戦略（将来的に分割予定）
from src.strategies_legacy import (
    MLStrategy,
    LightGBMStrategy,
    DeepLearningStrategy,
    TransformerStrategy,
    RLStrategy,
    GRUStrategy,
    AttentionLSTMStrategy,
)

# ファンダメンタル戦略
from src.strategies_legacy import DividendStrategy

# アンサンブル戦略
from src.strategies_legacy import (
    EnsembleStrategy,
    MultiTimeframeStrategy,
    SentimentStrategy,
)

# ユーティリティ
from src.strategies_legacy import load_custom_strategies

__all__ = [
    # Base
    'Strategy',
    'Order',
    'OrderType',
    
    # Technical
    'SMACrossoverStrategy',
    'RSIStrategy',
    'BollingerBandsStrategy',
    'CombinedStrategy',
    
    # ML
    'MLStrategy',
    'LightGBMStrategy',
    'DeepLearningStrategy',
    'TransformerStrategy',
    'RLStrategy',
    'GRUStrategy',
    'AttentionLSTMStrategy',
    
    # Fundamental
    'DividendStrategy',
    
    # Ensemble
    'EnsembleStrategy',
    'MultiTimeframeStrategy',
    'SentimentStrategy',
    
    # Utilities
    'load_custom_strategies',
]
