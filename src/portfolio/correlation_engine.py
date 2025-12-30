import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class CorrelationEngine:
    """
    Analyzes cross-asset correlations to detect portfolio risk concentration.
    Supports Stocks, Crypto (via tickers like BTC-USD), and FX.
    """
    def __init__(self, lookback_period: str = "3mo"):
        self.lookback_period = lookback_period
        self._correlation_matrix = pd.DataFrame()

    def calculate_correlations(self, tickers: List[str], prices_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculates correlation matrix from price data.
        """
        if len(tickers) < 2:
            return pd.DataFrame()

        close_prices = {}
        for t in tickers:
            if t in prices_dict and not prices_dict[t].empty:
                close_prices[t] = prices_dict[t]['Close']
        
        if len(close_prices) < 2:
            return pd.DataFrame()

        df = pd.DataFrame(close_prices)
        self._correlation_matrix = df.pct_change().corr()
        return self._correlation_matrix

    def get_risk_warnings(self, threshold: float = 0.85) -> List[Dict[str, Any]]:
        """
        Checks for high correlation pairs.
        """
        if self._correlation_matrix.empty:
            return []

        warnings = []
        tickers = self._correlation_matrix.columns
        checked_pairs = set()

        for t1 in tickers:
            for t2 in tickers:
                if t1 == t2 or (t1, t2) in checked_pairs or (t2, t1) in checked_pairs:
                    continue
                checked_pairs.add((t1, t2))
                
                corr = self._correlation_matrix.loc[t1, t2]
                if corr > threshold:
                    warnings.append({
                        "type": "HIGH_CORRELATION",
                        "tickers": [t1, t2],
                        "correlation": round(corr, 2),
                        "message": f"High correlation ({corr:.2f}) detected between {t1} and {t2}."
                    })
        return warnings
