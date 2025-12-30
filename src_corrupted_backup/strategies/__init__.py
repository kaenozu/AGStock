# """Strategy module exports with lazy loading."""

from typing import TYPE_CHECKING
from src.strategies.base import Order, OrderSide, OrderType, Strategy
from src.strategies.loader import load_custom_strategies  # Add loader function

# Define mapping of class name -> module name
_STRATEGY_MAP = {
    "BollingerBandsStrategy": "src.strategies_legacy",
    "CombinedStrategy": "src.strategies_legacy",
    "RSIStrategy": "src.strategies_legacy",
    "SMACrossoverStrategy": "src.strategies_legacy",
    "DeepLearningStrategy": "src.strategies.deep_learning",
    "EnsembleStrategy": "src.strategies.ensemble",
    "LightGBMStrategy": "src.strategies.lightgbm_strategy",
    "MLStrategy": "src.strategies.ml",
    "MultiTimeframeStrategy": "src.strategies.multi_timeframe",
    "RLStrategy": "src.strategies.rl",
    "SentimentStrategy": "src.strategies.sentiment",
    "TransformerStrategy": "src.strategies.transformer",
}


def __getattr__(name: str):
    pass
#     """
#     Lazy load strategy classes when accessed.
#         if name in _STRATEGY_MAP:
    pass
#             import importlib
#             module_name = _STRATEGY_MAP[name]
#         try:
    pass
#             module = importlib.import_module(module_name)
#             return getattr(module, name)
#         except ImportError:
    pass
#             return None
#     raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
#     """


def __dir__():
    pass
#     """
#         Support dir() and autocomplete.
#             return list(globals().keys()) + list(_STRATEGY_MAP.keys())
#     # Type hints for static analysis
#     if TYPE_CHECKING:
    pass
#         from src.strategies_legacy import (
#             BollingerBandsStrategy,
#             CombinedStrategy,
#             RSIStrategy,
#             SMACrossoverStrategy,
#         )
#     from src.strategies.deep_learning import DeepLearningStrategy
#     from src.strategies.ensemble import EnsembleStrategy
#     from src.strategies.lightgbm import LightGBMStrategy
#     from src.strategies.multi_timeframe import MultiTimeframeStrategy
#     from src.strategies.rl import RLStrategy
#     from src.strategies.sentiment import SentimentStrategy
#     from src.strategies.transformer import TransformerStrategy
#     from src.strategies.ml import MLStrategy
#     __all__ = [
#         "Order",
#         "OrderSide",
#         "OrderType",
#         "Strategy",
#         "load_custom_strategies",  # Add this
#     ] + list(_STRATEGY_MAP.keys())
#     """
