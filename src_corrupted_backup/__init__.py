# """
# AGStock Core Package
# """

__version__ = "2.0.0"
__author__ = "AGStock Development Team"


def __getattr__(name):
    if name == "ContinualLearningSystem":
        from .continual_learning import ContinualLearningSystem

        return ContinualLearningSystem
    elif name in ["EnsemblePredictor", "Predictor"]:
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
    elif name in ["RiskAdjustedPredictor", "RiskManager"]:
        from .risk_adjusted_prediction import RiskAdjustedPredictor

        return RiskAdjustedPredictor
    elif name == "ScenarioBasedPredictor":
        from .scenario_analyzer import ScenarioBasedPredictor

        return ScenarioBasedPredictor
    elif name == "SentimentEnhancedPredictor":
        from .sentiment_analytics import SentimentEnhancedPredictor

        return SentimentEnhancedPredictor
    elif name in ["XAIFramework", "AIAnalyzer"]:
        from .xai_explainer import XAIFramework

        return XAIFramework
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
