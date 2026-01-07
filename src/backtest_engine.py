<<<<<<< HEAD
from typing import Any, Dict, Type

import pandas as pd

from .backtester import Backtester
from .data_loader import fetch_stock_data
from .strategies import Strategy


class HistoricalBacktester:
    def __init__(self, initial_capital: float = 1000000):
        self.initial_capital = initial_capital
        self.backtester = Backtester(initial_capital=initial_capital)

    def run_test(
        self,
        ticker: str,
        strategy_class: Type[Strategy],
        years: int = 10,
        **strategy_params,
    ) -> Dict[str, Any]:
        """
        Runs a historical backtest for a specific ticker and strategy.
        """
        # 1. Fetch Data
        data_map = fetch_stock_data([ticker], period=f"{years}y")
        df = data_map.get(ticker)

        if df is None or df.empty:
            return {"error": "No data found"}

        # 2. Initialize Strategy
        strategy = strategy_class(**strategy_params)

        # 3. Run Backtest
        results = self.backtester.run(df, strategy)

        if not results:
            return {"error": "Backtest failed"}

        # 4. Calculate Additional Long-term Metrics

        # CAGR
        final_value = results["final_value"]
        cagr = (final_value / self.initial_capital) ** (1 / years) - 1

        # Annual Returns
        equity_curve = results["equity_curve"]  # Series with index as Date
        equity_curve.index = pd.to_datetime(equity_curve.index)

        # Resample to yearly
        yearly_equity = equity_curve.resample("Y").last()
        # Add start value
        start_series = pd.Series([1.0], index=[equity_curve.index[0] - pd.Timedelta(days=1)])
        yearly_equity_combined = pd.concat([start_series, yearly_equity])

        annual_returns = yearly_equity_combined.pct_change().dropna()
        # Format index to just year
        annual_returns.index = annual_returns.index.year

        # Benchmark (Buy & Hold)
        first_price = df["Close"].iloc[0]
        last_price = df["Close"].iloc[-1]
        buy_hold_return = (last_price - first_price) / first_price
        buy_hold_cagr = (last_price / first_price) ** (1 / years) - 1

        # Add to results
        results["cagr"] = cagr
        results["annual_returns"] = annual_returns.to_dict()
        results["buy_hold_return"] = buy_hold_return
        results["buy_hold_cagr"] = buy_hold_cagr
        results["ticker"] = ticker
        results["years"] = years
        results["strategy_name"] = strategy.name

        return results

    def compare_strategies(self, ticker: str, strategies: list, years: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Runs multiple strategies and returns comparison metrics and equity curves.

        Returns:
            metrics_df: DataFrame with performance metrics
            equity_curves_df: DataFrame with equity curves (col=strategy_name)
        """
        results_list = []
        equity_curves = pd.DataFrame()

        for strat_cls, params in strategies:
            try:
                # Instantiate strategy to get name if possible
                strat_name = strat_cls(**params).name
            except BaseException:
                strat_name = getattr(strat_cls, "name", str(strat_cls))

            res = self.run_test(ticker, strat_cls, years, **params)

            if "error" not in res:
                strat_name = res["strategy_name"]
                results_list.append(
                    {
                        "Strategy": strat_name,
                        "Total Return": res["total_return"],
                        "CAGR": res["cagr"],
                        "Max Drawdown": res["max_drawdown"],
                        "Sharpe Ratio": res["sharpe_ratio"],
                        "Win Rate": res["win_rate"],
                        "Trades": res["total_trades"],
                    }
                )

                # Add equity curve
                curve = res["equity_curve"]
                curve.name = strat_name
                if equity_curves.empty:
                    equity_curves = pd.DataFrame(curve)
                else:
                    equity_curves = equity_curves.join(curve, how="outer")
            else:
                # Handle error case
                pass

        # Fill NaN (forward fill then zero fill)
        equity_curves = equity_curves.ffill().fillna(1.0)

        return pd.DataFrame(results_list), equity_curves
=======
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.data_loader import fetch_stock_data
from src.backtesting.engine import BacktestEngine as CoreEngine

class HistoricalBacktester:
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital

    def compare_strategies(self, ticker, strategies_with_params, years=3):
        """
        Compare multiple strategies on a single ticker.
        strategies_with_params: List of (StrategyClass, params_dict)
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        # Fetch data
        data_map = fetch_stock_data([ticker], start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
        df = data_map.get(ticker)
        
        if df is None or df.empty:
            return pd.DataFrame(), pd.DataFrame()

        metrics_results = []
        equity_curves = {}

        for strat_class, params in strategies_with_params:
            try:
                # Instantiate strategy
                strategy = strat_class(**params)
                strat_name = strat_class.__name__
                
                # Run backtest using CoreEngine
                engine = CoreEngine(initial_capital=self.initial_capital)
                result = engine.run(df, strategy)
                
                if result:
                    metrics_results.append({
                        "Strategy": strat_name,
                        "Total Return": result["total_return"],
                        "CAGR": (1 + result["total_return"])**(1/years) - 1 if years > 0 else 0,
                        "Max Drawdown": result["max_drawdown"],
                        "Sharpe Ratio": result["sharpe_ratio"],
                        "Win Rate": result["win_rate"],
                        "Trades": result["total_trades"]
                    })
                    equity_curves[strat_name] = result["equity_curve"]
            except Exception as e:
                print(f"Error backtesting {strat_class.__name__}: {e}")

        metrics_df = pd.DataFrame(metrics_results)
        equity_df = pd.DataFrame(equity_curves)
        
        return metrics_df, equity_df
>>>>>>> 9ead59c0c8153a0969ef2e94b492063a605db31f
