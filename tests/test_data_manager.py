"""
DataManagerのテスト
"""

import os
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.data_manager import DataManager


@pytest.fixture
def temp_db(tmp_path):
    """一時的なデータベースパスを提供"""
    db_path = tmp_path / "test_stock_data.db"
    return str(db_path)


@pytest.fixture
def data_manager(temp_db):
    """DataManagerインスタンスを提供"""
    return DataManager(db_path=temp_db)


@pytest.fixture
def sample_stock_data():
    """サンプルの株価データを提供"""
    dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
    data = {
        "Open": [100, 102, 101, 103, 105, 104, 106, 108, 107, 109],
        "High": [105, 107, 106, 108, 110, 109, 111, 113, 112, 114],
        "Low": [98, 100, 99, 101, 103, 102, 104, 106, 105, 107],
        "Close": [102, 101, 103, 105, 104, 106, 108, 107, 109, 111],
        "Volume": [1000000] * 10,
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


def test_init_creates_database(temp_db):
    """データベースが正しく初期化されることを確認"""
    dm = DataManager(db_path=temp_db)
    assert os.path.exists(temp_db)

    # テーブルが作成されているか確認
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_data'")
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == "stock_data"


def test_save_data(data_manager, sample_stock_data):
    """データの保存が正しく動作することを確認"""
    ticker = "AAPL"
    data_manager.save_data(sample_stock_data, ticker)

    # データが保存されたか確認 (ticker_metadataテーブルを確認)
    conn = sqlite3.connect(data_manager.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT data_points FROM ticker_metadata WHERE ticker = ?", (ticker,))
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == len(sample_stock_data)


def test_save_empty_data(data_manager):
    """空のデータフレームを保存しても問題ないことを確認"""
    empty_df = pd.DataFrame()
    data_manager.save_data(empty_df, "TEST")
    # エラーが発生しないことを確認（例外が発生しなければOK）


def test_save_none_data(data_manager):
    """Noneを保存しても問題ないことを確認"""
    data_manager.save_data(None, "TEST")
    # エラーが発生しないことを確認


def test_load_data(data_manager, sample_stock_data):
    """データの読み込みが正しく動作することを確認"""
    ticker = "AAPL"
    data_manager.save_data(sample_stock_data, ticker)

    loaded_data = data_manager.load_data(ticker)

    assert not loaded_data.empty
    assert len(loaded_data) == len(sample_stock_data)
    assert list(loaded_data.columns) == ["Open", "High", "Low", "Close", "Volume"]


def test_load_data_with_date_range(data_manager, sample_stock_data):
    """日付範囲を指定したデータ読み込みが正しく動作することを確認"""
    ticker = "AAPL"
    data_manager.save_data(sample_stock_data, ticker)

    start_date = datetime(2023, 1, 3)
    end_date = datetime(2023, 1, 7)

    loaded_data = data_manager.load_data(ticker, start_date=start_date, end_date=end_date)

    assert not loaded_data.empty
    assert len(loaded_data) == 5  # 1/3から1/7まで5日間


def test_load_nonexistent_ticker(data_manager):
    """存在しないティッカーを読み込んだ場合、空のDataFrameが返ることを確認"""
    loaded_data = data_manager.load_data("NONEXISTENT")
    assert loaded_data.empty


def test_get_latest_date(data_manager, sample_stock_data):
    """最新日付の取得が正しく動作することを確認"""
    ticker = "AAPL"
    data_manager.save_data(sample_stock_data, ticker)

    latest_date = data_manager.get_latest_date(ticker)

    assert latest_date is not None
    expected_date = sample_stock_data.index[-1]
    assert latest_date.date() == expected_date.date()


def test_get_latest_date_nonexistent(data_manager):
    """存在しないティッカーの最新日付を取得した場合、Noneが返ることを確認"""
    latest_date = data_manager.get_latest_date("NONEXISTENT")
    assert latest_date is None


def test_upsert_data(data_manager, sample_stock_data):
    """同じデータを再保存した場合、更新されることを確認"""
    ticker = "AAPL"

    # 最初の保存
    data_manager.save_data(sample_stock_data, ticker)

    # データを変更して再保存
    modified_data = sample_stock_data.copy()
    modified_data["Close"] = modified_data["Close"] + 10
    data_manager.save_data(modified_data, ticker)

    # 読み込んで確認
    loaded_data = data_manager.load_data(ticker)

    # レコード数は変わらない
    assert len(loaded_data) == len(sample_stock_data)

    # 値が更新されている
    assert loaded_data["Close"].iloc[0] == modified_data["Close"].iloc[0]


def test_vacuum_db(data_manager, sample_stock_data):
    """VACUUMコマンドが正しく実行されることを確認"""
    ticker = "AAPL"
    data_manager.save_data(sample_stock_data, ticker)

    # VACUUMを実行（エラーが発生しないことを確認）
    data_manager.vacuum_db()

    # データが正常に読み込めることを確認
    loaded_data = data_manager.load_data(ticker)
    assert not loaded_data.empty


def test_multiple_tickers(data_manager, sample_stock_data):
    """複数のティッカーのデータを保存・読み込みできることを確認"""
    tickers = ["AAPL", "GOOGL", "MSFT"]

    for ticker in tickers:
        data_manager.save_data(sample_stock_data, ticker)

    for ticker in tickers:
        loaded_data = data_manager.load_data(ticker)
        assert not loaded_data.empty
        assert len(loaded_data) == len(sample_stock_data)
