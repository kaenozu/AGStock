"""
AGStock AI予測システムの統合エントリーポ点

このモジュールは、すべての高度なAI予測機能を統合し、
一貫性のあるAPIを通して利用可能にします。
"""

# 補助機能
from .continual_learning import ContinualLearningSystem

# 主要予測器
from .enhanced_ensemble_predictor import EnhancedEnsemblePredictor as EnsemblePredictor
from .mlops_manager import MLopsManager
from .multi_asset_analytics import MultiAssetPredictor
from .realtime_analytics import RealTimeAnalyticsPipeline
from .risk_adjusted_prediction import RiskAdjustedPredictor
from .scenario_analyzer import ScenarioBasedPredictor
from .sentiment_analytics import SentimentEnhancedPredictor
from .xai_explainer import XAIFramework

# バージョン情報
__version__ = "2.0.0"
__author__ = "AGStock Development Team"

# 一貫性のあるエイリアス
Predictor = EnsemblePredictor

AIAnalyzer = XAIFramework
RiskManager = RiskAdjustedPredictor
