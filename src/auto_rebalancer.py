"""
Auto Rebalancer Module
Monitors portfolio correlation and automatically rebalances when needed.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from src.paper_trader import PaperTrader
from src.data_loader import fetch_stock_data
from src.portfolio_manager import PortfolioManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoRebalancer:
    def __init__(self, correlation_threshold: float = 0.7, max_positions: int = 10):
        """
        Args:
            correlation_threshold: Correlation above this triggers rebalancing
            max_positions: Maximum number of positions to hold
        """
        self.correlation_threshold = correlation_threshold
        self.max_positions = max_positions
        self.pt = PaperTrader()
        self.portfolio_manager = PortfolioManager()
    
    def check_rebalance_needed(self) -> Tuple[bool, List[Tuple[str, str, float]]]:
        """
        Check if rebalancing is needed.
        
        Returns:
            (needs_rebalance, high_correlation_pairs)
        """
        positions = self.pt.get_positions()
        
        if positions.empty or len(positions) < 2:
            return False, []
        
        tickers = positions['ticker'].tolist()
        
        # Fetch price data for correlation analysis
        try:
            data_map = fetch_stock_data(tickers, period="6mo")
            price_df = pd.DataFrame({
                t: df['Close'] for t, df in data_map.items() 
                if df is not None and not df.empty
            })
            
            if price_df.empty:
                logger.warning("No price data available for correlation analysis")
                return False, []
            
            # Calculate correlation matrix
            corr_matrix = price_df.pct_change().corr()
            
            # Find high correlation pairs
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > self.correlation_threshold:
                        ticker1 = corr_matrix.columns[i]
                        ticker2 = corr_matrix.columns[j]
                        high_corr_pairs.append((ticker1, ticker2, corr_val))
            
            needs_rebalance = len(high_corr_pairs) > 0
            
            if needs_rebalance:
                logger.info(f"Rebalancing needed: {len(high_corr_pairs)} high correlation pairs found")
            
            return needs_rebalance, high_corr_pairs
            
        except Exception as e:
            logger.error(f"Error checking rebalance: {e}")
            return False, []
    
    def suggest_replacement(self, ticker_to_replace: str, avoid_tickers: List[str]) -> Optional[str]:
        """
        Suggest a replacement ticker with low correlation.
        
        Args:
            ticker_to_replace: Ticker to replace
            avoid_tickers: Tickers to avoid (current holdings)
            
        Returns:
            Suggested replacement ticker or None
        """
        # Simple implementation: suggest from a predefined pool
        # In production, this could use sector analysis, fundamental screening, etc.
        
        # Japanese stock pool (example)
        candidate_pool = [
            "6758.T",  # Sony
            "9984.T",  # SoftBank
            "6861.T",  # Keyence
            "4063.T",  # Shin-Etsu Chemical
            "6367.T",  # Daikin
            "4502.T",  # Takeda Pharmaceutical
            "8306.T",  # Mitsubishi UFJ
            "9433.T",  # KDDI
            "2914.T",  # JT
            "4568.T",  # Daiichi Sankyo
        ]
        
        # Filter out current holdings
        candidates = [t for t in candidate_pool if t not in avoid_tickers]
        
        if not candidates:
            logger.warning("No replacement candidates available")
            return None
        
        # For now, return first candidate
        # TODO: Implement correlation-based selection
        return candidates[0]
    
    def execute_rebalance(self, dry_run: bool = True) -> List[Dict]:
        """
        Execute rebalancing.
        
        Args:
            dry_run: If True, only simulate (don't execute trades)
            
        Returns:
            List of actions taken
        """
        needs_rebalance, high_corr_pairs = self.check_rebalance_needed()
        
        if not needs_rebalance:
            logger.info("No rebalancing needed")
            return []
        
        actions = []
        positions = self.pt.get_positions()
        current_tickers = positions['ticker'].tolist()
        
        # For each high correlation pair, replace the smaller position
        processed_tickers = set()
        
        for ticker1, ticker2, corr in high_corr_pairs:
            if ticker1 in processed_tickers or ticker2 in processed_tickers:
                continue
            
            # Get position sizes
            pos1 = positions[positions['ticker'] == ticker1].iloc[0]
            pos2 = positions[positions['ticker'] == ticker2].iloc[0]
            
            value1 = pos1['quantity'] * pos1['current_price']
            value2 = pos2['quantity'] * pos2['current_price']
            
            # Replace the smaller position
            if value1 < value2:
                ticker_to_replace = ticker1
                quantity_to_sell = pos1['quantity']
                price = pos1['current_price']
            else:
                ticker_to_replace = ticker2
                quantity_to_sell = pos2['quantity']
                price = pos2['current_price']
            
            # Suggest replacement
            replacement = self.suggest_replacement(ticker_to_replace, current_tickers)
            
            if replacement:
                action = {
                    'type': 'REBALANCE',
                    'sell': {
                        'ticker': ticker_to_replace,
                        'quantity': quantity_to_sell,
                        'price': price,
                        'reason': f'High correlation ({corr:.2f}) with {ticker1 if ticker_to_replace == ticker2 else ticker2}'
                    },
                    'buy': {
                        'ticker': replacement,
                        'reason': 'Replacement for diversification'
                    }
                }
                
                if not dry_run:
                    # Execute sell
                    self.pt.execute_trade(
                        ticker_to_replace, 
                        "SELL", 
                        quantity_to_sell, 
                        price,
                        reason=action['sell']['reason']
                    )
                    logger.info(f"Sold {quantity_to_sell} shares of {ticker_to_replace}")
                    
                    # TODO: Execute buy for replacement
                    # Need current price for replacement ticker
                    
                actions.append(action)
                processed_tickers.add(ticker_to_replace)
                current_tickers.remove(ticker_to_replace)
                current_tickers.append(replacement)
        
        logger.info(f"Rebalancing {'simulated' if dry_run else 'executed'}: {len(actions)} actions")
        return actions

if __name__ == "__main__":
    # Test
    rebalancer = AutoRebalancer()
    needs_rebalance, pairs = rebalancer.check_rebalance_needed()
    print(f"Needs rebalance: {needs_rebalance}")
    if pairs:
        print("High correlation pairs:")
        for t1, t2, corr in pairs:
            print(f"  {t1} <-> {t2}: {corr:.2f}")
