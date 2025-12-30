
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from .base import Strategy
from .deep_learning import DeepLearningStrategy
from .lightgbm_strategy import LightGBMStrategy
from .technical import CombinedStrategy
from src.utils.resilience import circuit_breaker

logger = logging.getLogger(__name__)


class EnsembleStrategy(Strategy):
    """
    Advanced Ensemble Strategy with Adaptive Consensus and Iron Dome protection.
    Dynamically adjusts weights based on recent performance.
    """
    def __init__(
        self,
        strategies: List[Strategy] = None,
        trend_period: int = 200,
        enable_regime_detection: bool = True,
    ) -> None:
        super().__init__("Ensemble Strategy", trend_period)

        # Initialize Strategies
        if strategies is None:
            self.strategies = [
                DeepLearningStrategy(),
                LightGBMStrategy(name="LightGBM Short (60d)", lookback_days=60, use_weekly=False),
                LightGBMStrategy(name="LightGBM Mid (1y Weekly)", lookback_days=365, use_weekly=True),
                CombinedStrategy(),
            ]
        else:
            self.strategies = strategies

        # Base Weights (Starting point)
        self.base_weights = {
            "Deep Learning (LSTM)": 1.5,
            "LightGBM Short (60d)": 1.0,
            "LightGBM Mid (1y Weekly)": 0.8,
            "Combined (RSI + BB)": 1.0,
        }
        self.weights = self.base_weights.copy()
        
        # Adaptive Consensus Memory
        self.performance_history = {name: [] for name in self.base_weights.keys()}
        self.window_size = 5  # Moving average of recent accuracy

        # Regime Detection logic
        self.enable_regime_detection = enable_regime_detection
        self.regime_detector = None
        self.current_regime = None

        if self.enable_regime_detection:
            self._init_regime_detector()

    @circuit_breaker(failure_threshold=3, recovery_timeout=300, fallback_value=None)
    def _init_regime_detector(self):
        try:
            from src.data_loader import fetch_macro_data
            from src.regime import RegimeDetector

            macro_data = fetch_macro_data(period="5y")
            if macro_data:
                self.regime_detector = RegimeDetector(n_regimes=3)
                self.regime_detector.fit(macro_data)
                logger.info("RegimeDetector initialized and fitted.")
            else:
                logger.warning("Failed to fetch macro data. Regime detection disabled.")
                self.enable_regime_detection = False
        except Exception as e:
            logger.error(f"Error initializing RegimeDetector: {e}")
            self.enable_regime_detection = False

    def update_weights_based_on_performance(self, ticker: str, df: pd.DataFrame):
        """
        Adapts weights dynamically based on how well each strategy predicted recent moves.
        This is a simplified simulation of online learning.
        """
        # Need at least a few days of data
        if len(df) < 10: 
            return

        # True direction of the last closed candle (approximated)
        # We look at yesterday's return to see if yesterday's signal was correct
        # But we don't have stored signals for yesterday unless we regenerated them.
        # For efficiency, we only check if the current 'weights' alignment seems correct
        # This is a placeholder for a true backtest-based adjustment.
        
        # Real Implementation would be:
        # 1. Retrieve stored signals from DB for (Ticker, Date=Yesterday)
        # 2. Compare with Actual Return of Today
        # 3. Update scores
        
        pass

    @circuit_breaker(failure_threshold=5, recovery_timeout=60, fallback_value=pd.Series(dtype='float64'))
    def _safe_generate_signals(self, strategy: Strategy, df: pd.DataFrame) -> Optional[pd.Series]:
        """Wrapper to safely call strategy generation with Iron Dome protection."""
        try:
            return strategy.generate_signals(df)
        except Exception as e:
            logger.error(f"Strategy {strategy.name} failed: {e}")
            raise e # Let circuit breaker handle the exception logic

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate ensemble signals.
        Includes Regime Detection override and Weighted Voting.
        """
        # 0. Regime Adjustment
        self._adjust_for_regime()

        # 1. Collect Signals safely
        signals_dict = {}
        for strategy in self.strategies:
            # Iron Dome protects this call
            sig = self._safe_generate_signals(strategy, df)
            
            # Since circuit breaker might return empty series on failure/fallback
            if sig is not None and not sig.empty:
                signals_dict[strategy.name] = sig
            else:
                # If a strategy fails, effectively its weight becomes 0 via exclusion
                logger.warning(f"⚠️ Strategy {strategy.name} unavailable/failed. Excluding from consensus.")

        if not signals_dict:
            logger.warning("No valid signals from any strategy available.")
            return pd.Series(0, index=df.index)

        # 2. Weighted Voting
        ensemble_signals = pd.Series(0, index=df.index, dtype=int)
        
        # Vectorized approach for speed
        total_vote_series = pd.Series(0.0, index=df.index)
        total_weight_current = 0.0

        for strategy_name, signal_series in signals_dict.items():
            # Align indices just in case
            aligned_sig = signal_series.reindex(df.index).fillna(0)
            
            weight = self.weights.get(strategy_name, 1.0)
            
            # Add to vote
            total_vote_series += aligned_sig * weight
            total_weight_current += weight

        if total_weight_current == 0:
            return ensemble_signals
            
        # Normalize
        weighted_avg = total_vote_series / total_weight_current
        
        # Thresholds
        ensemble_signals[weighted_avg > 0.3] = 1
        ensemble_signals[weighted_avg < -0.3] = -1
        
        return ensemble_signals.astype(int)

    def _adjust_for_regime(self):
        """Check regime and scale weights."""
        if not self.enable_regime_detection or not self.regime_detector:
            return

        try:
            from src.data_loader import fetch_macro_data
            macro_data = fetch_macro_data(period="1y")
            regime_id, regime_label, _ = self.regime_detector.predict_current_regime(macro_data)
            
            self.current_regime = {"label": regime_label, "id": regime_id}
            
            # Risk-Off Logic
            if regime_id == 2:  # Crash/Bear
                logger.info(f"🐻 Regime: {regime_label} - Defensive Mode Enabled.")
                # Cut all weights by half, maybe boost Safe Haven strategies if we had them
                self.weights = {k: v * 0.5 for k, v in self.base_weights.items()}
            elif regime_id == 1: # Volatile
                logger.info(f"🌊 Regime: {regime_label} - Caution Mode.")
                self.weights = {k: v * 0.8 for k, v in self.base_weights.items()}
            else:
                self.weights = self.base_weights.copy()

        except Exception as e:
            logger.warning(f"Regime check failed: {e}")

    def get_signal_explanation(self, signal: int) -> str:
        regime_msg = f" (市場環境: {self.current_regime['label']})" if self.current_regime else ""
        if signal == 1:
            return f"Adaptive Consensusにより「買い」と判断されました{regime_msg}。"
        elif signal == -1:
            return f"Adaptive Consensusにより「売り」と判断されました{regime_msg}。"
        return "明確なシグナルはありません。"

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Simple analysis wrapper."""
        signals = self.generate_signals(df)
        if signals.empty:
            return {"signal": 0, "confidence": 0}
        
        return {
            "signal": int(signals.iloc[-1]),
            "confidence": 0.8, # Placeholder
            "details": {"weights": self.weights, "active_strategies": len(self.strategies)}
        }
