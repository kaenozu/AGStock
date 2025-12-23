import pytest
import pandas as pd
import numpy as np
from src.rl.environment import TradingEnvironment

@pytest.fixture
def sample_df():
    # Create a simple deterministic price path
    # Day 0: 100
    # Day 1: 105 (+5%)
    # Day 2: 100 (-4.7%)
    # Day 3: 110 (+10%)
    data = {
        "Open": [100, 105, 100, 110],
        "High": [100, 105, 100, 110],
        "Low": [100, 105, 100, 110],
        "Close": [100.0, 105.0, 100.0, 110.0],
        "Volume": [1000, 1000, 1000, 1000]
    }
    return pd.DataFrame(data)

def test_initialization(sample_df):
    env = TradingEnvironment(sample_df, initial_balance=10000)
    assert env.balance == 10000
    assert env.shares_held == 0
    assert env.state_size == sample_df.shape[1] + 2  # Original + 2 extra features

def test_buy_with_transaction_cost(sample_df):
    # Fee = 1% for easy calc
    env = TradingEnvironment(sample_df, initial_balance=10000, transaction_cost_pct=0.01) 
    state = env.reset()
    
    # State should include position (0) and unrealized pnl (0)
    assert state[-2] == 0.0
    assert state[-1] == 0.0
    
    # Action 1: BUY
    # Price = 100. Max buy = 10000 / (100 * 1.01) = 10000 / 101 = 99 shares
    # Cost = 99 * 101 = 9999
    # Balance = 1
    next_state, reward, done, info = env.step(1)
    
    assert env.shares_held == 99
    assert env.balance == 10000 - (99 * 100 * 1.01)
    
    # Immediate reward logic:
    # Portfolio Value change. 
    # Old Value = 10000
    # New Value = Balance (1) + Shares(99)*NextPrice(105) = 1 + 10395 = 10396
    # Change = 396
    # Reward = 396 / 10000 * 100 = 3.96 %
    
    # Wait, my logic uses NEXT price for reward calc.
    # Step 0 -> Step 1.
    # Current Step became 1.
    # self.df.iloc[1]["Close"] is 105.
    
    expected_new_val = env.balance + (99 * 105.0)
    expected_reward = ((expected_new_val - 10000) / 10000) * 100
    
    assert info["portfolio_value"] == expected_new_val
    assert np.isclose(reward, expected_reward)
    assert not done

def test_sell_logic(sample_df):
    env = TradingEnvironment(sample_df, initial_balance=10000, transaction_cost_pct=0.0) # 0 fee
    env.reset()
    
    # Buy first
    env.step(1) # Buy at 100. Holds 100 shares. Balance 0.
    
    # Next price is 105. Portfolio Value = 10500.
    # State is now step 1.
    
    # Sell at step 1. Price is 105.
    # Revenue = 100 * 105 = 10500. Balance = 10500. Shares = 0.
    next_state, reward, done, info = env.step(2)
    
    assert env.shares_held == 0
    assert env.balance == 10500.0
    
    # Next price (step 2) is 100.
    # New Portfolio Value = 10500 + 0 = 10500.
    # Prev Portfolio Value was 10500.
    # Reward = 0 change.
    
    assert info["portfolio_value"] == 10500.0
    assert reward == 0.0

def test_observation_pnl(sample_df):
    env = TradingEnvironment(sample_df, initial_balance=10000)
    env.reset()
    
    # Buy at 100
    env.step(1) 
    # Now at step 1 (Price 105). 
    # Unrealized PnL should be (105 - 100) / 100 = 0.05
    
    obs = env._get_observation()
    assert obs[-2] == 1.0 # Position held
    assert np.isclose(obs[-1], 0.05)
