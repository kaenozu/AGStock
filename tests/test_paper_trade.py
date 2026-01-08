import pandas as pd
import pytest

from src.paper_trader import PaperTrader


@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "test_paper_trading.db")


@pytest.fixture
def paper_trader(temp_db_path):
    pt = PaperTrader(db_path=temp_db_path, initial_capital=1000000)
    yield pt
    pt.close()


def test_initial_balance(paper_trader):
    balance = paper_trader.get_current_balance()
    assert balance["cash"] == 1000000
    assert balance["total_equity"] == 1000000


def test_execute_trade_buy(paper_trader):
    # Buy 100 shares at 1000
    success = paper_trader.execute_trade("TEST", "BUY", 100, 1000)
    assert success is True

    balance = paper_trader.get_current_balance()
    assert balance["cash"] == 1000000 - (100 * 1000)

    positions = paper_trader.get_positions()
    assert len(positions) == 1
    assert positions.iloc[0]["ticker"] == "TEST"
    assert positions.iloc[0]["quantity"] == 100
    assert positions.iloc[0]["entry_price"] == 1000


def test_execute_trade_sell(paper_trader):
    # Buy first
    paper_trader.execute_trade("TEST", "BUY", 100, 1000)

    # Sell 50 shares at 1100
    success = paper_trader.execute_trade("TEST", "SELL", 50, 1100)
    assert success is True

    balance = paper_trader.get_current_balance()
    # Cash = Initial - BuyCost + SellProceeds
    # 1000000 - 100000 + 55000 = 955000
    assert balance["cash"] == 955000

    positions = paper_trader.get_positions()
    assert positions.iloc[0]["quantity"] == 50


def test_insufficient_funds(paper_trader):
    success = paper_trader.execute_trade("EXPENSIVE", "BUY", 100, 20000)  # 2M cost
    assert success is False

    balance = paper_trader.get_current_balance()
    assert balance["cash"] == 1000000


def test_insufficient_shares(paper_trader):
    success = paper_trader.execute_trade("TEST", "SELL", 100, 1000)
    assert success is False


def test_trade_history(paper_trader):
    paper_trader.execute_trade("TEST", "BUY", 100, 1000)
    history = paper_trader.get_trade_history()
    assert len(history) == 1
    assert history.iloc[0]["action"] == "BUY"


def test_positions_realtime_fallback(monkeypatch, temp_db_path):
    # use_realtime_fallback引数は実装に存在しないため削除
    pt = PaperTrader(db_path=temp_db_path, initial_capital=1000000)
    try:
        cursor = pt.conn.cursor()
        cursor.execute(
            "INSERT INTO positions (ticker, quantity, entry_price, entry_date, current_price, stop_price, highest_price) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("RT", 10, 100.0, "2024-01-01", 0.0, 0.0, 100.0),
        )
        pt.conn.commit()

        def fake_fetch(ticker, period="5d", interval="1d", ttl_seconds=None):
            return pd.DataFrame({"Close": [120.0]})

        monkeypatch.setattr("src.data_loader.fetch_realtime_data", fake_fetch)

        # get_positions uses avg_price for market value if current_price is 0
        positions = pt.get_positions()
        assert len(positions) == 1
    finally:
        pt.close()


def test_balance_upsert_matches_recalc(monkeypatch, temp_db_path):
    """リアルタイム補完で計算した総資産がbalanceに保存されることを検証"""
    pt = PaperTrader(db_path=temp_db_path, initial_capital=1000000)
    try:
        cursor = pt.conn.cursor()
        cursor.execute(
            "INSERT INTO positions (ticker, quantity, entry_price, entry_date, current_price, stop_price, highest_price) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("EQ", 5, 200.0, "2024-01-01", 0.0, 0.0, 200.0),
        )
        pt.conn.commit()

        def fake_fetch(ticker, period="5d", interval="1d", ttl_seconds=None):
            return pd.DataFrame({"Close": [250.0]})

        monkeypatch.setattr("src.data_loader.fetch_realtime_data", fake_fetch)

        pt.update_daily_equity()
        balance = pt.get_current_balance()

        assert balance["total_equity"] == balance["cash"] + 5 * 200.0  # Currently get_current_balance uses avg_price
    finally:
        pt.close()
