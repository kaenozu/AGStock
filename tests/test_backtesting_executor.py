"""BacktestExecutorのテストモジュール。"""
import pytest
import pandas as pd
import numpy as np
from src.backtesting.executor import BacktestExecutor
from src.strategies import Order, OrderType


@pytest.fixture
def executor():
    """BacktestExecutorのインスタンスを作成するフィクスチャ"""
    return BacktestExecutor(commission=0.001, slippage=0.001)


def test_executor_initialization(executor):
    """BacktestExecutorが正しく初期化されることを確認"""
    assert executor.commission == 0.001
    assert executor.slippage == 0.001


def test_execute_market_buy_order(executor):
    """市場注文（買い）の執行テスト"""
    signal = Order(
        ticker="7203.T",
        action="BUY",
        type=OrderType.MARKET,
        quantity=100,
        price=None  # 市場価格で執行
    )
    
    # 適当な初期状態
    holdings = {"7203.T": 0.0}
    entry_prices = {"7203.T": 0.0}
    cash = 1_000_000
    exec_price = 2000
    ticker = "7203.T"
    today_high = 2010
    today_low = 1990
    aligned_data = {"7203.T": pd.DataFrame({"High": [2010], "Low": [1990]}, index=[pd.Timestamp.now()])}
    trailing_stop = None
    stop_loss = 0.05
    take_profit = 0.1
    trades = []
    trailing_stop_levels = {"7203.T": 0.0}
    highest_prices = {"7203.T": 0.0}
    current_portfolio_value = 1_000_000

    cash, holdings, entry_prices, exit_executed, trades = executor.execute_order(
        signal, holdings, entry_prices, cash, exec_price, ticker, today_high, today_low,
        aligned_data, trailing_stop, stop_loss, take_profit, trades, trailing_stop_levels, highest_prices, current_portfolio_value
    )

    # 買い注文が執行されたことを確認
    assert holdings["7203.T"] > 0
    assert cash < 1_000_000  # 手数料とスリッページ込みで現金が減少
    assert entry_prices["7203.T"] == exec_price
    assert not exit_executed
    assert len(trades) == 0  # 新規ポジションのため取引履歴には追加されない


def test_execute_market_sell_order(executor):
    """市場注文（売り）の執行テスト"""
    signal = Order(
        ticker="7203.T",
        action="SELL",
        type=OrderType.MARKET,
        quantity=100,
        price=None  # 市場価格で執行
    )

    # 売却するための初期状態（保有している）
    holdings = {"7203.T": 100.0}
    entry_prices = {"7203.T": 2000.0}
    cash = 900_000  # 100株×2000円で買ったため
    exec_price = 2100  # 売却価格（利益確定）
    ticker = "7203.T"
    today_high = 2110
    today_low = 2090
    aligned_data = {"7203.T": pd.DataFrame({"High": [2110], "Low": [2090]}, index=[pd.Timestamp.now()])}
    trailing_stop = None
    stop_loss = 0.05
    take_profit = 0.1
    trades = []
    trailing_stop_levels = {"7203.T": 0.0}
    highest_prices = {"7203.T": 0.0}
    current_portfolio_value = 1_000_000

    # ポジションクローズのための信号は、保有数が0でない時に有効
    # このテストでは、直接保有数を指定して売る操作を模倣
    # よって、保有株数が0でなければ売り注文は実行される
    # 今回は保有株数100の状態でSELL信号を送れば、クローズになるはず
    cash, holdings, entry_prices, exit_executed, trades = executor.execute_order(
        signal, holdings, entry_prices, cash, exec_price, ticker, today_high, today_low,
        aligned_data, trailing_stop, stop_loss, take_profit, trades, trailing_stop_levels, highest_prices, current_portfolio_value
    )

    # 売り注文が執行されたことを確認
    assert holdings["7203.T"] == 0.0
    assert cash > 900_000  # 利益が入る
    assert entry_prices["7203.T"] == 0.0
    assert exit_executed
    assert len(trades) == 1  # 取引履歴が追加されている
    assert trades[0]["return"] > 0  # 利益であること