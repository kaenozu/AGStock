from typing import Any, Dict, Type
import pandas as pd
from src.backtester import Backtester
from src.data_loader import fetch_stock_data
from src.strategies import Strategy


class HistoricalBacktester:
    def __init__(self, initial_capital: float = 1000000):
        pass
        self.initial_capital = initial_capital
        self.backtester = Backtester(initial_capital=initial_capital)


#     """
#     ) -> Dict[str, Any]:
    pass
#         """
# 1. Fetch Data
# 2. Initialize Strategy
# 3. Run Backtest
# 4. Calculate Additional Long-term Metrics
# CAGR
# Annual Returns
# Resample to yearly
# Add start value
# Format index to just year
# Benchmark (Buy & Hold)
# Add to results
#     """
#     def compare_strategies(self, ticker: str, strategies: list, years: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    pass
#         """


# Instantiate strategy to get name if possible
# Add equity curve
# Handle error case
# Fill NaN (forward fill then zero fill)
