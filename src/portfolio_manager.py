"""
Portfolio Manager for AGStock (Phase 30-3)

This module handles portfolio-level risk management:
1. Correlation Risk: Prevent concentration in highly correlated assets.
2. Sector Risk: Limit exposure to specific sectors.
3. Position Sizing: Adjust position sizes based on portfolio volatility.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, max_correlation: float = 0.7, max_sector_exposure: float = 0.4):
        self.max_correlation = max_correlation
        self.max_sector_exposure = max_sector_exposure
        self.positions = {} # {ticker: size}
        self.sector_map = {} # {ticker: sector}
        
    def set_sector_map(self, sector_map: Dict[str, str]):
        self.sector_map = sector_map
        
    def check_new_position(self, ticker: str, current_portfolio: List[str], correlation_matrix: pd.DataFrame) -> bool:
        """
        Check if adding a new position violates risk constraints.
        
        Args:
            ticker: Ticker to add
            current_portfolio: List of tickers currently held
            correlation_matrix: DataFrame of correlation matrix
            
        Returns:
            True if safe to add, False otherwise
        """
        if not current_portfolio:
            return True
            
        # 1. Correlation Check
        if correlation_matrix is not None and not correlation_matrix.empty:
            if ticker in correlation_matrix.index:
                correlations = correlation_matrix.loc[ticker, current_portfolio]
                if (correlations > self.max_correlation).any():
                    logger.warning(f"Rejecting {ticker}: High correlation with existing portfolio")
                    return False
                    
        # 2. Sector Check
        if self.sector_map:
            sector = self.sector_map.get(ticker)
            if sector:
                sector_counts = [self.sector_map.get(t) for t in current_portfolio]
                sector_exposure = sector_counts.count(sector) / len(current_portfolio) if current_portfolio else 0
                
                if sector_exposure >= self.max_sector_exposure:
                    logger.warning(f"Rejecting {ticker}: Sector limit reached for {sector}")
                    return False
                    
        return True
        
    def calculate_portfolio_volatility(self, weights: Dict[str, float], cov_matrix: pd.DataFrame) -> float:
        """
        Calculate portfolio volatility.
        """
        if not weights or cov_matrix is None or cov_matrix.empty:
            return 0.0
            
        tickers = list(weights.keys())
        w = np.array([weights[t] for t in tickers])
        
        # Ensure cov_matrix has all tickers
        valid_tickers = [t for t in tickers if t in cov_matrix.index]
        if len(valid_tickers) != len(tickers):
            return 0.0
            
        sub_cov = cov_matrix.loc[valid_tickers, valid_tickers]
        
        port_var = np.dot(w.T, np.dot(sub_cov, w))
        return np.sqrt(port_var)
