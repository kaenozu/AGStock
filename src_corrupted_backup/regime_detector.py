from enum import Enum
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
class MarketRegime(Enum):
        BULL = "Bull (強気)"
    BEAR = "Bear (弱気)"
    SIDEWAYS = "Sideways (レンジ)"
    VOLATILE = "Volatile (高ボラティリティ)"
    UNCERTAIN = "Uncertain (不透明)"
    TRENDING_UP = "Trending Up"
    TRENDING_DOWN = "Trending Down"
    HIGH_VOLATILITY = "High Volatility"
    LOW_VOLATILITY = "Low Volatility"
    RANGING = "Ranging"
class RegimeDetector:
#     """
#     Detects the current market regime based on technical indicators.
#     Used to adjust trading strategies dynamically.
#     """
    def __init__(
        self, window_short: int = 50, window_long: int = 200, adx_threshold: int = 20, vix_threshold: float = 25.0
#     """
#     ):
#         pass
#             self.window_short = window_short
#         self.window_long = window_long
#         self.adx_threshold = adx_threshold
#         self.vix_threshold = vix_threshold
#         self.regimes = {r.name.lower(): r for r in MarketRegime}
#         self.current_regime: Optional[str] = None
#         self.regime_history: List[Dict] = []
#     def detect_regime(self, df: pd.DataFrame, vix_value: Optional[float] = None) -> str:
#         """
Analyzes DataFrame to determine market regime.
        df requires: 'Close', 'High', 'Low'
                trend = self._detect_trend_fallback(df, self.window_short)
        volatility = self._detect_volatility_fallback(df, self.window_short, vix_value)
        regime = self._classify_regime(trend, volatility)
            self.current_regime = regime
        self.regime_history.append(
            {
                "timestamp": pd.Timestamp.utcnow().isoformat(),
                "regime": regime,
                "trend": trend,
                "volatility": volatility,
            }
        )
        return regime
#     """
#     def _detect_trend_fallback(self, df: pd.DataFrame, window: int) -> str:
#         pass
#     def _detect_volatility_fallback(self, df: pd.DataFrame, window: int, vix_value: Optional[float] = None) -> str:
#         pass
#     def _classify_regime(self, trend: str, volatility: str) -> str:
#         pass
#     def get_regime_strategy(self, regime: Optional[str] = None) -> Dict:
#         pass
#     def get_regime_signal(self, df: pd.DataFrame) -> Dict:
#         """
High-level compatibility method for UI display.
                regime = self.detect_regime(df)
        descriptions = {
            "trending_up": "強い上昇トレンドです。買い戦略が有効です。",
            "trending_down": "下降トレンドが継続しています。警戒が必要です。",
            "ranging": "方向感のないレンジ相場です。逆張りが検討されます。",
            "high_volatility": "ボラティリティが急増しています。ストップロスを広げてください。",
            "low_volatility": "市場は極めて静かです。ブレイクアウトに注意して下さい。",
        }
        return {"regime_name": regime.upper(), "description": descriptions.get(regime, "市場環境を分析中です。")}
#     """
#     def get_regime_history(self, n: Optional[int] = None) -> List[Dict]:
#         pass
#     def get_regime_statistics(self) -> Dict:
#         """
Get Regime Statistics.
            Returns:
                Description of return value
                        if not self.regime_history:
                            return {"message": "No regime data available"}
            counts = {}
        for h in self.regime_history:
            counts[h["regime"]] = counts.get(h["regime"], 0) + 1
            total = len(self.regime_history)
        percentages = {k: v / total for k, v in counts.items()}
        most_common = max(counts, key=counts.get)
            return {
            "current_regime": self.current_regime,
            "total_observations": total,
            "regime_counts": counts,
            "regime_percentages": percentages,
            "most_common_regime": most_common,
        }
# Backward-compatible alias expected by tests
# """
class MarketRegimeDetector(RegimeDetector):
    pass
#     """Alias for legacy references."""


# """
