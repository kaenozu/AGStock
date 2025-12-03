"""
Advanced Backtest Engine
Provides sophisticated backtesting capabilities including walk-forward analysis,
Monte Carlo simulation, and realistic cost modeling.
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedBacktester:
    def __init__(self, 
                 initial_capital: float = 1000000,
                 commission_rate: float = 0.001,
                 slippage_bps: float = 5.0):
        """
        Args:
            initial_capital: Starting capital
            commission_rate: Commission as fraction (0.001 = 0.1%)
            slippage_bps: Slippage in basis points
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_bps = slippage_bps
    
    def walk_forward_analysis(self,
                              data: pd.DataFrame,
                              strategy_func,
                              train_period_days: int = 252,
                              test_period_days: int = 63,
                              step_days: int = 21) -> Dict:
        """
        Perform walk-forward analysis.
        
        Args:
            data: Price data
            strategy_func: Strategy function that returns signals
            train_period_days: Training period length
            test_period_days: Testing period length
            step_days: Step size for rolling window
            
        Returns:
            Dictionary with results
        """
        results = []
        data = data.sort_index()
        
        start_date = data.index[0]
        end_date = data.index[-1]
        
        current_date = start_date + timedelta(days=train_period_days)
        
        while current_date + timedelta(days=test_period_days) <= end_date:
            # Training period
            train_start = current_date - timedelta(days=train_period_days)
            train_end = current_date
            train_data = data.loc[train_start:train_end]
            
            # Testing period
            test_start = current_date
            test_end = current_date + timedelta(days=test_period_days)
            test_data = data.loc[test_start:test_end]
            
            if len(train_data) > 0 and len(test_data) > 0:
                # Train strategy
                strategy_params = strategy_func(train_data, mode='train')
                
                # Test strategy
                test_signals = strategy_func(test_data, mode='test', params=strategy_params)
                
                # Calculate performance
                perf = self._calculate_performance(test_data, test_signals)
                
                results.append({
                    'train_start': train_start,
                    'train_end': train_end,
                    'test_start': test_start,
                    'test_end': test_end,
                    'return': perf['total_return'],
                    'sharpe': perf['sharpe_ratio'],
                    'max_dd': perf['max_drawdown']
                })
            
            current_date += timedelta(days=step_days)
        
        return {
            'results': pd.DataFrame(results),
            'avg_return': np.mean([r['return'] for r in results]),
            'avg_sharpe': np.mean([r['sharpe'] for r in results]),
            'consistency': np.sum([r['return'] > 0 for r in results]) / len(results)
        }
    
    def monte_carlo_simulation(self,
                               returns: pd.Series,
                               n_simulations: int = 1000,
                               n_days: int = 252) -> Dict:
        """
        Run Monte Carlo simulation.
        
        Args:
            returns: Historical returns
            n_simulations: Number of simulations
            n_days: Number of days to simulate
            
        Returns:
            Simulation results
        """
        mean_return = returns.mean()
        std_return = returns.std()
        
        simulations = []
        
        for _ in range(n_simulations):
            # Generate random returns
            sim_returns = np.random.normal(mean_return, std_return, n_days)
            
            # Calculate cumulative returns
            cum_returns = (1 + sim_returns).cumprod()
            final_value = self.initial_capital * cum_returns[-1]
            
            simulations.append({
                'final_value': final_value,
                'total_return': (final_value - self.initial_capital) / self.initial_capital,
                'max_drawdown': self._calculate_max_drawdown(cum_returns)
            })
        
        sim_df = pd.DataFrame(simulations)
        
        return {
            'simulations': sim_df,
            'mean_final_value': sim_df['final_value'].mean(),
            'median_final_value': sim_df['final_value'].median(),
            'percentile_5': sim_df['final_value'].quantile(0.05),
            'percentile_95': sim_df['final_value'].quantile(0.95),
            'prob_profit': (sim_df['total_return'] > 0).mean(),
            'var_95': sim_df['total_return'].quantile(0.05)
        }
    
    def calculate_realistic_costs(self,
                                  trades: pd.DataFrame,
                                  price_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate realistic trading costs including slippage and commission.
        
        Args:
            trades: DataFrame with trade information
            price_data: Price data for slippage calculation
            
        Returns:
            Trades with costs
        """
        trades = trades.copy()
        
        for idx, trade in trades.iterrows():
            ticker = trade['ticker']
            quantity = trade['quantity']
            
            # Get price at trade time
            if ticker in price_data.columns:
                price = price_data.loc[trade['timestamp'], ticker]
                
                # Calculate slippage (worse execution price)
                slippage = price * (self.slippage_bps / 10000)
                if trade['action'] == 'BUY':
                    execution_price = price + slippage
                else:
                    execution_price = price - slippage
                
                # Calculate commission
                commission = execution_price * quantity * self.commission_rate
                
                trades.at[idx, 'execution_price'] = execution_price
                trades.at[idx, 'slippage_cost'] = slippage * quantity
                trades.at[idx, 'commission'] = commission
                trades.at[idx, 'total_cost'] = slippage * quantity + commission
        
        return trades
    
    def stress_test(self,
                   strategy_func,
                   scenarios: List[Dict]) -> Dict:
        """
        Perform stress testing under various scenarios.
        
        Args:
            strategy_func: Strategy to test
            scenarios: List of scenario definitions
            
        Returns:
            Stress test results
        """
        results = []
        
        for scenario in scenarios:
            name = scenario['name']
            data = scenario['data']
            
            # Run strategy
            signals = strategy_func(data)
            perf = self._calculate_performance(data, signals)
            
            results.append({
                'scenario': name,
                'return': perf['total_return'],
                'sharpe': perf['sharpe_ratio'],
                'max_dd': perf['max_drawdown'],
                'volatility': perf['volatility']
            })
        
        return pd.DataFrame(results)
    
    def _calculate_performance(self, data: pd.DataFrame, signals: pd.Series) -> Dict:
        """Calculate strategy performance metrics."""
        if signals.empty or data.empty:
            return {
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'volatility': 0
            }
        
        # Calculate returns
        returns = data['Close'].pct_change()
        strategy_returns = returns * signals.shift(1)
        strategy_returns = strategy_returns.dropna()
        
        if len(strategy_returns) == 0:
            return {
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'volatility': 0
            }
        
        # Metrics
        total_return = (1 + strategy_returns).prod() - 1
        sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
        max_dd = self._calculate_max_drawdown((1 + strategy_returns).cumprod())
        volatility = strategy_returns.std() * np.sqrt(252)
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_dd,
            'volatility': volatility
        }
    
    def _calculate_max_drawdown(self, cum_returns: pd.Series) -> float:
        """Calculate maximum drawdown."""
        running_max = cum_returns.cummax()
        drawdown = (cum_returns - running_max) / running_max
        return drawdown.min()

if __name__ == "__main__":
    # Test
    backtester = AdvancedBacktester()
    
    # Generate sample data
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
    prices = pd.DataFrame({
        'Close': 1000 * (1 + np.random.randn(len(dates)).cumsum() * 0.01)
    }, index=dates)
    
    # Simple strategy
    def simple_strategy(data, mode='test', params=None):
        if mode == 'train':
            return {'sma_period': 20}
        else:
            sma = data['Close'].rolling(window=params['sma_period']).mean()
            signals = (data['Close'] > sma).astype(int)
            return signals
    
    # Walk-forward analysis
    wf_results = backtester.walk_forward_analysis(prices, simple_strategy)
    print("Walk-Forward Analysis:")
    print(f"  Average Return: {wf_results['avg_return']:.2%}")
    print(f"  Average Sharpe: {wf_results['avg_sharpe']:.2f}")
    print(f"  Consistency: {wf_results['consistency']:.1%}")
