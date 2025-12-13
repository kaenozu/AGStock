"""
PortfolioManagerのテスト
"""

import numpy as np
import pandas as pd
import pytest

from src.portfolio_manager import PortfolioManager


@pytest.fixture
def portfolio_manager():
    """PortfolioManagerインスタンスを提供"""
    return PortfolioManager(max_correlation=0.7, max_sector_exposure=0.4)


@pytest.fixture
def sector_map():
    """セクターマップを提供"""
    return {
        "AAPL": "Technology",
        "MSFT": "Technology",
        "GOOGL": "Technology",
        "JPM": "Finance",
        "BAC": "Finance",
        "XOM": "Energy",
        "CVX": "Energy",
    }


@pytest.fixture
def correlation_matrix():
    """相関行列を提供"""
    tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "BAC", "XOM", "CVX"]
    # 相関行列を作成（Technology同士は高相関、他は低相関）
    corr_data = [
        [1.00, 0.85, 0.80, 0.30, 0.25, 0.20, 0.15],  # AAPL
        [0.85, 1.00, 0.75, 0.28, 0.22, 0.18, 0.12],  # MSFT
        [0.80, 0.75, 1.00, 0.32, 0.27, 0.22, 0.17],  # GOOGL
        [0.30, 0.28, 0.32, 1.00, 0.65, 0.35, 0.30],  # JPM
        [0.25, 0.22, 0.27, 0.65, 1.00, 0.30, 0.25],  # BAC
        [0.20, 0.18, 0.22, 0.35, 0.30, 1.00, 0.70],  # XOM
        [0.15, 0.12, 0.17, 0.30, 0.25, 0.70, 1.00],  # CVX
    ]
    return pd.DataFrame(corr_data, index=tickers, columns=tickers)


@pytest.fixture
def covariance_matrix():
    """共分散行列を提供"""
    tickers = ["AAPL", "MSFT", "GOOGL", "JPM"]
    # 簡単な共分散行列
    cov_data = [
        [0.04, 0.02, 0.015, 0.01],
        [0.02, 0.03, 0.012, 0.008],
        [0.015, 0.012, 0.035, 0.009],
        [0.01, 0.008, 0.009, 0.025],
    ]
    return pd.DataFrame(cov_data, index=tickers, columns=tickers)


def test_init():
    """初期化のテスト"""
    pm = PortfolioManager(max_correlation=0.8, max_sector_exposure=0.5)
    assert pm.max_correlation == 0.8
    assert pm.max_sector_exposure == 0.5
    assert pm.positions == {}
    assert pm.sector_map == {}


def test_set_sector_map(portfolio_manager, sector_map):
    """セクターマップの設定テスト"""
    portfolio_manager.set_sector_map(sector_map)
    assert portfolio_manager.sector_map == sector_map


def test_check_new_position_empty_portfolio(portfolio_manager, correlation_matrix):
    """空のポートフォリオに新規追加する場合は常にTrue"""
    result = portfolio_manager.check_new_position("AAPL", [], correlation_matrix)
    assert result is True


def test_check_new_position_low_correlation(portfolio_manager, correlation_matrix):
    """相関が低い場合は追加可能"""
    current_portfolio = ["JPM"]
    result = portfolio_manager.check_new_position("AAPL", current_portfolio, correlation_matrix)
    assert result is True  # AAPL-JPM相関は0.30 < 0.7


def test_check_new_position_high_correlation(portfolio_manager, correlation_matrix):
    """相関が高い場合は追加不可"""
    current_portfolio = ["AAPL"]
    result = portfolio_manager.check_new_position("MSFT", current_portfolio, correlation_matrix)
    assert result is False  # AAPL-MSFT相関は0.85 > 0.7


def test_check_new_position_sector_limit(portfolio_manager, sector_map, correlation_matrix):
    """セクター制限のテスト"""
    portfolio_manager.set_sector_map(sector_map)

    # Technology株を2つ保有（全体の2/5 = 40%）
    current_portfolio = ["AAPL", "MSFT", "JPM", "BAC", "XOM"]

    # さらにTechnology株を追加しようとすると拒否される
    result = portfolio_manager.check_new_position("GOOGL", current_portfolio, correlation_matrix)
    assert result is False


def test_check_new_position_sector_ok(portfolio_manager, sector_map, correlation_matrix):
    """セクター制限内であれば追加可能"""
    portfolio_manager.set_sector_map(sector_map)

    # Technology株を1つ保有（全体の1/3 = 33% < 40%）
    current_portfolio = ["AAPL", "JPM", "XOM"]

    # 相関が低ければ追加可能（MSFTはAAPLと相関が高いので別の銘柄で）
    result = portfolio_manager.check_new_position("BAC", current_portfolio, correlation_matrix)
    assert result is True


def test_check_new_position_no_correlation_matrix(portfolio_manager):
    """相関行列がない場合でも動作する"""
    result = portfolio_manager.check_new_position("AAPL", ["MSFT"], None)
    assert result is True


def test_check_new_position_empty_correlation_matrix(portfolio_manager):
    """空の相関行列でも動作する"""
    empty_corr = pd.DataFrame()
    result = portfolio_manager.check_new_position("AAPL", ["MSFT"], empty_corr)
    assert result is True


def test_check_new_position_ticker_not_in_matrix(portfolio_manager, correlation_matrix):
    """相関行列に存在しないティッカーでも動作する"""
    result = portfolio_manager.check_new_position("UNKNOWN", ["AAPL"], correlation_matrix)
    assert result is True


def test_calculate_portfolio_volatility(portfolio_manager, covariance_matrix):
    """ポートフォリオボラティリティの計算テスト"""
    weights = {"AAPL": 0.25, "MSFT": 0.25, "GOOGL": 0.25, "JPM": 0.25}

    volatility = portfolio_manager.calculate_portfolio_volatility(weights, covariance_matrix)

    assert volatility > 0
    assert isinstance(volatility, float)
    # 手計算での検証（おおよその値）
    assert 0.1 < volatility < 0.3


def test_calculate_portfolio_volatility_empty_weights(portfolio_manager, covariance_matrix):
    """空のウェイトの場合は0を返す"""
    volatility = portfolio_manager.calculate_portfolio_volatility({}, covariance_matrix)
    assert volatility == 0.0


def test_calculate_portfolio_volatility_no_cov_matrix(portfolio_manager):
    """共分散行列がない場合は0を返す"""
    weights = {"AAPL": 0.5, "MSFT": 0.5}
    volatility = portfolio_manager.calculate_portfolio_volatility(weights, None)
    assert volatility == 0.0


def test_calculate_portfolio_volatility_empty_cov_matrix(portfolio_manager):
    """空の共分散行列の場合は0を返す"""
    weights = {"AAPL": 0.5, "MSFT": 0.5}
    empty_cov = pd.DataFrame()
    volatility = portfolio_manager.calculate_portfolio_volatility(weights, empty_cov)
    assert volatility == 0.0


def test_calculate_portfolio_volatility_missing_ticker(portfolio_manager, covariance_matrix):
    """共分散行列に存在しないティッカーがある場合は0を返す"""
    weights = {"AAPL": 0.5, "UNKNOWN": 0.5}
    volatility = portfolio_manager.calculate_portfolio_volatility(weights, covariance_matrix)
    assert volatility == 0.0


def test_calculate_portfolio_volatility_single_asset(portfolio_manager, covariance_matrix):
    """単一資産の場合、そのボラティリティを返す"""
    weights = {"AAPL": 1.0}
    volatility = portfolio_manager.calculate_portfolio_volatility(weights, covariance_matrix)

    # AAPL単独のボラティリティは sqrt(0.04) = 0.2
    assert abs(volatility - 0.2) < 0.001
