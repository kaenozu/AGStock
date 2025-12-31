"""TradingEnvironmentのテスト"""
import pytest
import pandas as pd
import numpy as np
from src.rl.environment import TradingEnvironment


@pytest.fixture
def sample_df():
    """lookback_window=20をサポートする十分なデータを作成"""
    np.random.seed(42)
    n_days = 50  # lookback_window=20に対応
    base_price = 100.0
    prices = [base_price]
    for _ in range(n_days - 1):
        change = np.random.uniform(-0.02, 0.02)
        prices.append(prices[-1] * (1 + change))
    prices = np.array(prices)
    data = {
        "Open": prices * 0.995,
        "High": prices * 1.01,
        "Low": prices * 0.99,
        "Close": prices,
        "Volume": [1000] * n_days
    }
    return pd.DataFrame(data)


def test_initialization(sample_df):
    """TradingEnvironmentの初期化テスト"""
    env = TradingEnvironment(sample_df, initial_balance=10000)
    assert env.balance == 10000
    assert env.shares_held == 0
    assert env.state_size == sample_df.select_dtypes(include=[np.number]).shape[1] + 2


def test_buy_with_transaction_cost(sample_df):
    """BUYアクションと取引コストのテスト"""
    env = TradingEnvironment(sample_df, initial_balance=10000, transaction_cost_pct=0.01)
    state = env.reset()
    
    # State should include position (0) and unrealized pnl (0)
    assert state[-2] == 0.0
    assert state[-1] == 0.0
    
    # Action 1: BUY
    initial_balance = env.balance
    next_state, reward, done, info = env.step(1)
    
    # 購入後は株数が0より大きくなる
    assert env.shares_held > 0
    # 残高は減少する
    assert env.balance < initial_balance
    # ポートフォリオ価値は記録される
    assert "value" in info
    assert not done


def test_sell_logic(sample_df):
    """SELLアクションのテスト"""
    env = TradingEnvironment(sample_df, initial_balance=10000, transaction_cost_pct=0.0)
    env.reset()
    
    # Buy first
    env.step(1)
    shares_after_buy = env.shares_held
    assert shares_after_buy > 0
    
    # Sell
    next_state, reward, done, info = env.step(2)
    
    # 売却後は株数が0
    assert env.shares_held == 0
    # 残高は売却代金を含む
    assert env.balance > 0
    # ポートフォリオ価値は記録される
    assert "value" in info


def test_observation_pnl(sample_df):
    """観測状態に含まれるPnLのテスト"""
    env = TradingEnvironment(sample_df, initial_balance=10000)
    env.reset()
    
    # Buy
    env.step(1)
    
    obs = env._get_observation()
    # Position held は 1.0
    assert obs[-2] == 1.0
    # Unrealized PnLは数値（具体的な値は価格に依存）
    assert isinstance(obs[-1], (float, np.floating))


def test_hold_action(sample_df):
    """HOLDアクションのテスト"""
    env = TradingEnvironment(sample_df, initial_balance=10000)
    env.reset()
    
    initial_balance = env.balance
    initial_shares = env.shares_held
    
    # Action 0: HOLD
    next_state, reward, done, info = env.step(0)
    
    # HOLDでは何も変わらない
    assert env.balance == initial_balance
    assert env.shares_held == initial_shares


def test_episode_termination(sample_df):
    """エピソード終了のテスト"""
    env = TradingEnvironment(sample_df, initial_balance=10000)
    env.reset()
    
    # 最後までステップを実行
    done = False
    steps = 0
    max_steps = len(sample_df) - env.lookback_window
    while not done and steps < max_steps + 10:  # Safety limit
        _, _, done, _ = env.step(0)  # HOLD
        steps += 1
    
    assert done, "Episode should terminate when data is exhausted"
