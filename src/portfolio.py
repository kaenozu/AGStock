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
        
        # 1. Collect all equity curves
        equity_curves = {}
        
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
                # Store the equity curve (value)
                equity_curves[ticker] = res['equity_curve'] * allocated_capital

        if not equity_curves:
            return None

        # 2. Create unified index
        all_dates = sorted(list(set().union(*[ec.index for ec in equity_curves.values()])))
        full_index = pd.DatetimeIndex(all_dates)
        
        # 3. Reindex and Sum
        portfolio_equity = pd.Series(0.0, index=full_index)
        
        for ticker, ec in equity_curves.items():
            # Reindex to full range, forward fill (hold value), fill initial NaNs with allocated capital
            allocated_capital = self.initial_capital * weights[ticker]
            reindexed_ec = ec.reindex(full_index).ffill().fillna(allocated_capital)
            portfolio_equity += reindexed_ec

        # Handle unallocated cash
        total_weight = sum(weights.values())
        cash_weight = 1.0 - total_weight
        if cash_weight > 0:
            cash_value = self.initial_capital * cash_weight
            portfolio_equity += cash_value

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

    def optimize_portfolio(self, data_map: Dict[str, pd.DataFrame], risk_free_rate: float = 0.0) -> Dict[str, float]:
        """
        Optimizes portfolio weights using Mean-Variance Optimization to maximize Sharpe Ratio.
        """
        from scipy.optimize import minimize
        
        tickers = list(data_map.keys())
        if not tickers:
            return {}
            
        # Prepare data matrix (Daily Returns)
        close_prices = {}
        for ticker, df in data_map.items():
            if df is not None and not df.empty:
                close_prices[ticker] = df['Close']
                
        if not close_prices:
            return {}
            
        prices_df = pd.DataFrame(close_prices)
        returns_df = prices_df.pct_change().dropna()
        
        if returns_df.empty:
            return {t: 1.0/len(tickers) for t in tickers}
            
        mean_returns = returns_df.mean() * 252 # Annualized
        cov_matrix = returns_df.cov() * 252 # Annualized
        
        num_assets = len(tickers)
        
        def negative_sharpe(weights):
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            if portfolio_volatility == 0:
                return 0
            sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
            return -sharpe
            
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0.0, 1.0) for _ in range(num_assets))
        initial_weights = num_assets * [1. / num_assets,]
        
        result = minimize(negative_sharpe, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)
        
        optimized_weights = {}
        for i, ticker in enumerate(tickers):
            optimized_weights[ticker] = result.x[i]
            
        return optimized_weights
