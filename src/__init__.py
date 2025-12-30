"""
AGStock AI予測システムの統合エントリーポ点

このモジュールは、すべての高度なAI予測機能を統合し、
一貫性のあるAPIを通して利用可能にします。
"""

# 補助機能
# Lazy loading implemented via __getattr__ to avoid heavy imports (TensorFlow etc.) on startup

# バージョン情報
__version__ = "2.0.0"
__author__ = "AGStock Development Team"


def __getattr__(name):
    if name == "ContinualLearningSystem":
        from .continual_learning import ContinualLearningSystem

        return ContinualLearningSystem

    elif name == "EnsemblePredictor" or name == "Predictor":
        from .enhanced_ensemble_predictor import EnhancedEnsemblePredictor

        return EnhancedEnsemblePredictor

    elif name == "MLopsManager":
        from .mlops_manager import MLopsManager

        return MLopsManager

    elif name == "MultiAssetPredictor":
        from .multi_asset_analytics import MultiAssetPredictor

        return MultiAssetPredictor

    elif name == "RealTimeAnalyticsPipeline":
        from .realtime_analytics import RealTimeAnalyticsPipeline

        return RealTimeAnalyticsPipeline

    elif name == "RiskAdjustedPredictor" or name == "RiskManager":
        from .risk_adjusted_prediction import RiskAdjustedPredictor

        return RiskAdjustedPredictor

    elif name == "ScenarioBasedPredictor":
        from .scenario_analyzer import ScenarioBasedPredictor

        return ScenarioBasedPredictor

    elif name == "SentimentEnhancedPredictor":
        from .sentiment_analytics import SentimentEnhancedPredictor

        return SentimentEnhancedPredictor

    elif name == "XAIFramework" or name == "AIAnalyzer":
        from .xai_explainer import XAIFramework

        return XAIFramework

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
