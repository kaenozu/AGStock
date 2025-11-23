import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from src.data_manager import DataManager
from src.backtester import Backtester
from src.strategies import Strategy
from src.portfolio import PortfolioManager

# --- Mock Strategy ---
class MockStrategy(Strategy):
    def __init__(self, signal_series):
        super().__init__("MockStrategy")
        self.signal_series = signal_series

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # Return pre-defined signals reindexed to df
        return self.signal_series.reindex(df.index).fillna(0)

# --- Data Manager Tests ---
def test_data_manager_save_load(tmp_path):
    db_path = str(tmp_path / "test_stock.db")
    dm = DataManager(db_path=db_path)
    
    # Create dummy data
    dates = pd.date_range(start="2023-01-01", periods=5)
    df = pd.DataFrame({
        'Open': [100, 101, 102, 103, 104],
        'High': [105, 106, 107, 108, 109],
        'Low': [95, 96, 97, 98, 99],
        'Close': [102, 103, 104, 105, 106],
        'Volume': [1000, 1100, 1200, 1300, 1400]
    }, index=dates)
    
    dm.save_data(df, "TEST")
    
    loaded_df = dm.load_data("TEST")
    
    assert not loaded_df.empty
    assert len(loaded_df) == 5
    assert loaded_df.index[0] == dates[0]
    assert loaded_df['Close'].iloc[-1] == 106
    
    # Test incremental update (upsert)
    new_dates = pd.date_range(start="2023-01-06", periods=2)
    new_df = pd.DataFrame({
        'Open': [110, 111],
        'High': [115, 116],
        'Low': [105, 106],
        'Close': [112, 113],
        'Volume': [1500, 1600]
    }, index=new_dates)
    
    dm.save_data(new_df, "TEST")
    
    loaded_df_2 = dm.load_data("TEST")
    assert len(loaded_df_2) == 7
    assert loaded_df_2['Close'].iloc[-1] == 113
    
    # Test get_latest_date
    latest = dm.get_latest_date("TEST")
    assert latest == new_dates[-1]

# --- Unified Backtester Tests ---
def test_unified_backtester_single_asset():
    # Setup Data
    dates = pd.date_range(start="2023-01-01", periods=10)
    df = pd.DataFrame({
        'Open': [100]*10, 'High': [110]*10, 'Low': [90]*10, 'Close': [100, 101, 102, 103, 104, 105, 104, 103, 102, 101],
        'Volume': [1000]*10
    }, index=dates)
    
    # Strategy: Buy on Day 1, Sell on Day 5
    signals = pd.Series(0, index=dates)
    signals.iloc[0] = 1 # Buy at Open of Day 2 (Exec Day 1 Signal) -> Day 2 Open
    signals.iloc[4] = -1 # Sell at Open of Day 6
    
    strat = MockStrategy(signals)
    
    bt = Backtester(initial_capital=10000, commission=0.0, slippage=0.0)
    res = bt.run(df, strat)
    
    assert res is not None
    assert res['total_trades'] == 1
    # Entry: Day 2 Open (100). Exit: Day 6 Open (100). Return: 0?
    # Wait, prices are constant Open=100.
    # Close prices change.
    # My Backtester executes at Open.
    # Day 0 Signal 1 -> Buy Day 1 Open (100).
    # Day 4 Signal -1 -> Sell Day 5 Open (100).
    # PnL should be 0.
    
    # Let's make Open prices change to verify PnL.
    df['Open'] = df['Close'] # Open = Close for simplicity
    
    # Day 0: Close 100. Signal 1.
    # Day 1: Open 101. Buy @ 101.
    # Day 4: Close 104. Signal -1.
    # Day 5: Open 105. Sell @ 105.
    # Profit: 4 per share.
    # Return: 4/101 approx 3.96%
    
    bt = Backtester(initial_capital=10000, commission=0.0, slippage=0.0)
    res = bt.run(df, strat, stop_loss=10.0, take_profit=10.0)
    
    assert res['total_trades'] == 1
    assert res['num_trades'] == 1  # Verify alias
    assert 'sharpe_ratio' in res
    assert 'signals' in res
    assert 'positions' in res
    assert isinstance(res['sharpe_ratio'], (int, float))
    
    trade = res['trades'][0]
    assert trade['entry_price'] == 101
    assert trade['exit_price'] == 105
    assert trade['return'] == pytest.approx((105-101)/101)

def test_unified_backtester_multi_asset():
    dates = pd.date_range(start="2023-01-01", periods=5)
    
    # Asset A: Flat
    df_a = pd.DataFrame({'Open': [100]*5, 'High': [100]*5, 'Low': [100]*5, 'Close': [100]*5, 'Volume': [1000]*5}, index=dates)
    # Asset B: Doubles
    df_b = pd.DataFrame({'Open': [10, 20, 30, 40, 50], 'High': [10]*5, 'Low': [10]*5, 'Close': [10, 20, 30, 40, 50], 'Volume': [1000]*5}, index=dates)
    
    data_map = {'A': df_a, 'B': df_b}
    
    # Strategy: Buy B on Day 0.
    sig_a = pd.Series(0, index=dates)
    sig_b = pd.Series(0, index=dates)
    sig_b.iloc[0] = 1
    
    strategies = {'A': MockStrategy(sig_a), 'B': MockStrategy(sig_b)}
    
    # 50% allocation to B
    bt = Backtester(initial_capital=10000, commission=0.0, slippage=0.0, position_size={'A': 0.5, 'B': 0.5})
    # Disable SL/TP to verify Buy & Hold
    res = bt.run(data_map, strategies, stop_loss=10.0, take_profit=10.0)
    
    # Check B trade
    # Day 0 Signal 1 -> Buy Day 1 Open (20).
    # Allocation: 5000. Shares: 250.
    # Held until end.
    # Final Value: Cash (5000) + Shares (250 * 50 = 12500) = 17500.
    # Total Return: 75%.
    
    assert res['final_value'] == 17500
    assert res['total_return'] == 0.75

# --- Portfolio Manager Integration Tests ---
def test_portfolio_manager_integration():
    pm = PortfolioManager(initial_capital=10000, commission=0.0, slippage=0.0)
    
    dates = pd.date_range(start="2023-01-01", periods=5)
    df_a = pd.DataFrame({'Open': [100]*5, 'High': [100]*5, 'Low': [100]*5, 'Close': [100]*5, 'Volume': [1000]*5}, index=dates)
    df_b = pd.DataFrame({'Open': [10, 20, 30, 40, 50], 'High': [10]*5, 'Low': [10]*5, 'Close': [10, 20, 30, 40, 50], 'Volume': [1000]*5}, index=dates)
    
    data_map = {'A': df_a, 'B': df_b}
    
    sig_a = pd.Series(0, index=dates)
    sig_b = pd.Series(0, index=dates)
    sig_b.iloc[0] = 1
    
    strategies = {'A': MockStrategy(sig_a), 'B': MockStrategy(sig_b)}
    weights = {'A': 0.5, 'B': 0.5}
    
    res = pm.simulate_portfolio(data_map, strategies, weights, stop_loss=10.0, take_profit=10.0)
    
    assert res is not None
    assert res['total_return'] == 0.75
    assert 'equity_curve' in res
