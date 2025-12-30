import logging
import pandas as pd
import numpy as np
from typing import Dict, List

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Portfolio Risk Parity Manager (Phase 72)
    Manages overall portfolio risk, correlation, and position sizing.
    """

    def __init__(self, target_risk: float = 0.02):
        self.target_risk = target_risk  # Target risk per position or portfolio?
        self.max_correlation = 0.7

    def calculate_risk_parity_weights(
        self, tickers: List[str], price_history: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Calculate weights such that each asset contributes equally to the portfolio risk.
        Position Size \u221d 1 / Volatility
        """
        vols = {}
        for ticker in tickers:
            df = price_history.get(ticker)
            if df is not None and len(df) > 20:
                # Annualized volatility of daily returns
                returns = df["Close"].pct_change().dropna()
                vol = returns.std() * np.sqrt(252)
                vols[ticker] = max(vol, 0.01)  # Avoid division by zero
            else:
                vols[ticker] = 0.3  # Default 30% vol

        # Inverse volatility weighting
        inv_vols = {t: 1.0 / v for t, v in vols.items()}
        total_inv_vol = sum(inv_vols.values())

        weights = {t: v / total_inv_vol for t, v in inv_vols.items()}
        return weights

    def analyze_correlations(
        self, price_history: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for given tickers.
        """
        returns_dict = {}
        for ticker, df in price_history.items():
            if df is not None and not df.empty:
                returns_dict[ticker] = df["Close"].pct_change()

        if not returns_dict:
            return pd.DataFrame()

        returns_df = pd.DataFrame(returns_dict).dropna()
        return returns_df.corr()

    def get_diversification_suggestions(
        self, holdings: List[str], price_history: Dict[str, pd.DataFrame]
    ) -> List[str]:
        """
        Identify highly correlated pairs and suggest reductions.
        """
        corr_matrix = self.analyze_correlations(price_history)
        if corr_matrix.empty:
            return []

        suggestions = []
        tickers = corr_matrix.columns
        for i in range(len(tickers)):
            for j in range(i + 1, len(tickers)):
                t1, t2 = tickers[i], tickers[j]
                corr = corr_matrix.loc[t1, t2]
                if corr > self.max_correlation:
                    suggestions.append(
                        f"Warning: {t1} and {t2} are highly correlated ({corr:.2f}). Consider reducing one."
                    )

        return suggestions
