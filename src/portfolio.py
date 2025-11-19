import pandas as pd
import numpy as np
from typing import Dict, List, Any
from src.backtester import Backtester
from src.strategies import Strategy

class PortfolioManager:
    def __init__(self, initial_capital: float = 10000000):
        self.initial_capital = initial_capital

    def calculate_correlation(self, data_map: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculates the correlation matrix of daily returns for the given stocks.
        """
        close_prices = {}
        for ticker, df in data_map.items():
            if df is not None and not df.empty:
                close_prices[ticker] = df['Close']
        
        if not close_prices:
            return pd.DataFrame()

        prices_df = pd.DataFrame(close_prices)
        # Calculate daily returns
        returns_df = prices_df.pct_change().dropna()
        # Calculate correlation
        return returns_df.corr()

    def simulate_portfolio(self, data_map: Dict[str, pd.DataFrame], strategies: Dict[str, Strategy], weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Simulates a portfolio by running backtests on individual stocks and aggregating results.
        
        Args:
            data_map: Dictionary of Ticker -> DataFrame
            strategies: Dictionary of Ticker -> Strategy instance
            weights: Dictionary of Ticker -> Weight (0.0 to 1.0, sum should be <= 1.0)
            
        Returns:
            Dict containing 'equity_curve', 'total_return', 'max_drawdown', 'individual_results'
        """
        
        individual_results = {}
        portfolio_equity = pd.Series(0.0, dtype=float)
        
        # Align dates: Find common date range or just union?
        # Union is better, filling missing with 0 change (cash)
        
        # First, run backtests
        for ticker, weight in weights.items():
            if ticker not in data_map or data_map[ticker] is None:
                continue
                
            df = data_map[ticker]
            strategy = strategies.get(ticker)
            if not strategy:
                continue
                
            # Allocate capital
            allocated_capital = self.initial_capital * weight
            
            # Run Backtest
            # We use position_size=1.0 relative to the *allocated* capital
            bt = Backtester(initial_capital=allocated_capital, position_size=1.0)
            res = bt.run(df, strategy)
            
            if res:
                individual_results[ticker] = res
                
                # Equity curve of this component
                # res['equity_curve'] is cumulative return (e.g. 1.05, 0.98)
                # We need value: allocated_capital * res['equity_curve']
                
                # Reindex to handle different start dates?
                # For simplicity, assume data_map covers similar periods or handle alignment later.
                component_value = allocated_capital * res['equity_curve']
                
                if portfolio_equity.empty:
                    portfolio_equity = component_value
                else:
                    # Add to portfolio equity, aligning indices (filling 0 for missing dates is wrong, should fill with initial capital?)
                    # Better: Fill forward?
                    # Let's use an outer join sum.
                    portfolio_equity = portfolio_equity.add(component_value, fill_value=0)
                    
        # Handle unallocated cash (if weights sum < 1.0)
        total_weight = sum(weights.values())
        cash_weight = 1.0 - total_weight
        if cash_weight > 0:
            cash_value = self.initial_capital * cash_weight
            # Add constant cash value (assuming 0 interest)
            # We need an index. Use the portfolio_equity index.
            if not portfolio_equity.empty:
                portfolio_equity += cash_value

        if portfolio_equity.empty:
            return None

        # Fill NaNs (if any)
        portfolio_equity = portfolio_equity.ffill().fillna(self.initial_capital)

        # Calculate Metrics
        total_return = (portfolio_equity.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # Max Drawdown
        running_max = portfolio_equity.cummax()
        drawdown = (portfolio_equity - running_max) / running_max
        max_drawdown = drawdown.min()

        return {
            "equity_curve": portfolio_equity,
            "total_return": total_return,
            "max_drawdown": max_drawdown,
            "individual_results": individual_results
        }
