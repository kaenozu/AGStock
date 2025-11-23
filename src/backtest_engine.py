import pandas as pd
import numpy as np
from typing import Dict, Any, Type
from src.backtester import Backtester
from src.data_loader import fetch_long_term_data
from src.strategies import Strategy

class HistoricalBacktester:
    def __init__(self, initial_capital: float = 1000000):
        self.initial_capital = initial_capital
        self.backtester = Backtester(initial_capital=initial_capital)

    def run_test(self, ticker: str, strategy_class: Type[Strategy], years: int = 10, **strategy_params) -> Dict[str, Any]:
        """
        Runs a historical backtest for a specific ticker and strategy.
        """
        # 1. Fetch Data
        df = fetch_long_term_data(ticker, years=years)
        if df.empty:
            return {"error": "No data found"}
        
        # 2. Initialize Strategy
        strategy = strategy_class(**strategy_params)
        
        # 3. Run Backtest
        results = self.backtester.run(df, strategy)
        
        if not results:
            return {"error": "Backtest failed"}
        
        # 4. Calculate Additional Long-term Metrics
        
        # CAGR
        final_value = results['final_value']
        cagr = (final_value / self.initial_capital) ** (1 / years) - 1
        
        # Annual Returns
        equity_curve = results['equity_curve'] # Series with index as Date
        equity_curve.index = pd.to_datetime(equity_curve.index)
        
        # Resample to yearly
        yearly_equity = equity_curve.resample('Y').last()
        # Add start value
        start_series = pd.Series([1.0], index=[equity_curve.index[0] - pd.Timedelta(days=1)])
        yearly_equity_combined = pd.concat([start_series, yearly_equity])
        
        annual_returns = yearly_equity_combined.pct_change().dropna()
        # Format index to just year
        annual_returns.index = annual_returns.index.year
        
        # Benchmark (Buy & Hold)
        first_price = df['Close'].iloc[0]
        last_price = df['Close'].iloc[-1]
        buy_hold_return = (last_price - first_price) / first_price
        buy_hold_cagr = (last_price / first_price) ** (1 / years) - 1
        
        # Add to results
        results['cagr'] = cagr
        results['annual_returns'] = annual_returns.to_dict()
        results['buy_hold_return'] = buy_hold_return
        results['buy_hold_cagr'] = buy_hold_cagr
        results['ticker'] = ticker
        results['years'] = years
        results['strategy_name'] = strategy.name
        
        return results

    def compare_strategies(self, ticker: str, strategies: list, years: int = 10) -> pd.DataFrame:
        """
        Runs multiple strategies and returns a comparison DataFrame.
        """
        results_list = []
        
        for strat_cls, params in strategies:
            res = self.run_test(ticker, strat_cls, years, **params)
            if "error" not in res:
                results_list.append({
                    "Strategy": res['strategy_name'],
                    "Total Return": res['total_return'],
                    "CAGR": res['cagr'],
                    "Max Drawdown": res['max_drawdown'],
                    "Sharpe Ratio": res['sharpe_ratio'],
                    "Win Rate": res['win_rate'],
                    "Trades": res['total_trades']
                })
                
        return pd.DataFrame(results_list)
