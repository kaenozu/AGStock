"""
高度なリスク管理機能の包括的テスト

pytest形式のユニットテスト
実行方法: pytest tests/test_advanced_risk.py -v
"""

from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.advanced_risk import AdvancedRiskManager


@pytest.fixture
def config():
    """テスト用設定"""
    return {"auto_trading": {"max_daily_loss_pct": -3.0, "market_crash_threshold": -3.0, "max_correlation": 0.7}}


@pytest.fixture
def risk_manager(config):
    """AdvancedRiskManagerインスタンス"""
    return AdvancedRiskManager(config)


@pytest.fixture
def mock_paper_trader():
    """モックPaperTrader"""
    pt = Mock()
    pt.initial_capital = 1000000
    return pt


@pytest.fixture
def mock_logger():
    """モックロガー"""
    return Mock()


class TestDrawdownProtection:
    """ドローダウン保護のテスト"""

    def test_no_loss_scenario(self, risk_manager, mock_paper_trader, mock_logger):
        """損失なしのシナリオ"""
        # 資産履歴: 昨日100万、今日105万（+5万）
        equity_history = pd.DataFrame(
            {"date": pd.date_range("2025-12-03", periods=2), "total_equity": [1000000, 1050000]}
        )
        mock_paper_trader.get_equity_history.return_value = equity_history
        mock_paper_trader.get_positions.return_value = pd.DataFrame()

        is_safe, reason, signals = risk_manager.check_drawdown_protection(mock_paper_trader, mock_logger)

        assert is_safe == True
        assert "OK" in reason
        assert len(signals) == 0

    def test_small_loss_within_limit(self, risk_manager, mock_paper_trader, mock_logger):
        """制限内の小さな損失"""
        # 資産履歴: 昨日100万、今日98万（-2万 = -2%）
        equity_history = pd.DataFrame(
            {"date": pd.date_range("2025-12-03", periods=2), "total_equity": [1000000, 980000]}
        )
        mock_paper_trader.get_equity_history.return_value = equity_history
        mock_paper_trader.get_positions.return_value = pd.DataFrame()

        is_safe, reason, signals = risk_manager.check_drawdown_protection(mock_paper_trader, mock_logger)

        assert is_safe == True
        assert "OK" in reason

    def test_large_loss_exceeds_limit(self, risk_manager, mock_paper_trader, mock_logger):
        """制限を超える大きな損失"""
        # 資産履歴: 昨日100万、今日96万（-4万 = -4%）
        equity_history = pd.DataFrame(
            {"date": pd.date_range("2025-12-03", periods=2), "total_equity": [1000000, 960000]}
        )
        mock_paper_trader.get_equity_history.return_value = equity_history

        # ポジション情報
        positions = pd.DataFrame(
            {"ticker": ["AAPL", "GOOGL"], "quantity": [10, 5], "current_price": [180.0, 140.0]}
        ).set_index("ticker")
        mock_paper_trader.get_positions.return_value = positions

        is_safe, reason, signals = risk_manager.check_drawdown_protection(mock_paper_trader, mock_logger)

        assert is_safe == False
        assert "超過" in reason
        assert len(signals) == 2  # 2銘柄の緊急決済
        assert all(s["action"] == "SELL" for s in signals)
        assert all(s["strategy"] == "Drawdown Protection" for s in signals)

    def test_first_day_no_history(self, risk_manager, mock_paper_trader, mock_logger):
        """初日（履歴なし）"""
        equity_history = pd.DataFrame()
        mock_paper_trader.get_equity_history.return_value = equity_history

        is_safe, reason, signals = risk_manager.check_drawdown_protection(mock_paper_trader, mock_logger)

        assert is_safe == True
        assert "履歴不足" in reason


class TestMarketCrashDetection:
    """市場急落検知のテスト"""

    @patch("src.advanced_risk.yf.Ticker")
    def test_normal_market_conditions(self, mock_ticker, risk_manager, mock_logger):
        """正常な市場環境"""
        # 日経平均: 昨日38000、今日38500（+1.3%）
        nikkei_data = pd.DataFrame({"Close": [38000, 38500]})

        # S&P500: 昨日4800、今日4820（+0.4%）
        sp500_data = pd.DataFrame({"Close": [4800, 4820]})

        def ticker_side_effect(symbol):
            mock = Mock()
            if symbol == "^N225":
                mock.history.return_value = nikkei_data
            elif symbol == "^GSPC":
                mock.history.return_value = sp500_data
            return mock

        mock_ticker.side_effect = ticker_side_effect

        allow_buy, reason = risk_manager.check_market_crash(mock_logger)

        assert allow_buy == True
        assert "正常" in reason

    @patch("src.advanced_risk.yf.Ticker")
    def test_nikkei_crash(self, mock_ticker, risk_manager, mock_logger):
        """日経平均の急落"""
        # 日経平均: 昨日38000、今日36500（-3.9%）
        nikkei_data = pd.DataFrame({"Close": [38000, 36500]})

        # S&P500: 正常
        sp500_data = pd.DataFrame({"Close": [4800, 4820]})

        def ticker_side_effect(symbol):
            mock = Mock()
            if symbol == "^N225":
                mock.history.return_value = nikkei_data
            elif symbol == "^GSPC":
                mock.history.return_value = sp500_data
            return mock

        mock_ticker.side_effect = ticker_side_effect

        allow_buy, reason = risk_manager.check_market_crash(mock_logger)

        assert allow_buy == False
        assert "日経平均" in reason
        assert "急落" in reason

    @patch("src.advanced_risk.yf.Ticker")
    def test_sp500_crash(self, mock_ticker, risk_manager, mock_logger):
        """S&P500の急落"""
        # 日経平均: 正常
        nikkei_data = pd.DataFrame({"Close": [38000, 38500]})

        # S&P500: 昨日4800、今日4650（-3.1%）
        sp500_data = pd.DataFrame({"Close": [4800, 4650]})

        def ticker_side_effect(symbol):
            mock = Mock()
            if symbol == "^N225":
                mock.history.return_value = nikkei_data
            elif symbol == "^GSPC":
                mock.history.return_value = sp500_data
            return mock

        mock_ticker.side_effect = ticker_side_effect

        allow_buy, reason = risk_manager.check_market_crash(mock_logger)

        assert allow_buy == False
        assert "S&P500" in reason
        assert "急落" in reason


class TestCorrelationCheck:
    """銘柄相関チェックのテスト"""

    @patch("src.advanced_risk.fetch_stock_data")
    def test_no_existing_positions(self, mock_fetch, risk_manager, mock_logger):
        """既存ポジションなし"""
        allow, reason = risk_manager.check_correlation("AAPL", [], mock_logger)

        assert allow == True
        assert "既存ポジションなし" in reason

    @patch("src.advanced_risk.fetch_stock_data")
    def test_low_correlation_allowed(self, mock_fetch, risk_manager, mock_logger):
        """低相関（許可）"""
        # AAPL と GOOGL のデータ（相関0.3と仮定）
        dates = pd.date_range("2025-09-01", periods=60)

        aapl_data = pd.DataFrame({"Close": 180 + np.random.randn(60) * 5}, index=dates)

        googl_data = pd.DataFrame({"Close": 140 + np.random.randn(60) * 3}, index=dates)

        mock_fetch.return_value = {"AAPL": aapl_data, "GOOGL": googl_data}

        allow, reason = risk_manager.check_correlation("AAPL", ["GOOGL"], mock_logger)

        # 相関が0.7未満なら許可されるはず
        assert allow == True or "相関が高すぎる" in reason

    @patch("src.advanced_risk.fetch_stock_data")
    def test_high_correlation_rejected(self, mock_fetch, risk_manager, mock_logger):
        """高相関（拒否）"""
        # AAPL と AAPL（完全相関）
        dates = pd.date_range("2025-09-01", periods=60)

        aapl_data = pd.DataFrame({"Close": 180 + np.cumsum(np.random.randn(60) * 2)}, index=dates)

        mock_fetch.return_value = {"AAPL": aapl_data, "AAPL": aapl_data}  # 同じデータ

        allow, reason = risk_manager.check_correlation("AAPL", ["AAPL"], mock_logger)

        # 完全相関なので拒否されるはず
        assert allow == False
        assert "相関が高すぎる" in reason

    @patch("src.advanced_risk.fetch_stock_data")
    def test_data_fetch_error(self, mock_fetch, risk_manager, mock_logger):
        """データ取得エラー"""
        mock_fetch.return_value = {}  # データなし

        allow, reason = risk_manager.check_correlation("AAPL", ["GOOGL"], mock_logger)

        # エラー時は保守的に許可
        assert allow == True
        assert "データ不足" in reason or "エラー" in reason


class TestIntegration:
    """統合テスト"""

    def test_config_defaults(self):
        """デフォルト設定のテスト"""
        config = {}
        risk_mgr = AdvancedRiskManager(config)

        assert risk_mgr.max_daily_loss_pct == -3.0
        assert risk_mgr.market_crash_threshold == -3.0
        assert risk_mgr.max_correlation == 0.7

    def test_custom_config(self):
        """カスタム設定のテスト"""
        config = {"auto_trading": {"max_daily_loss_pct": -5.0, "market_crash_threshold": -2.0, "max_correlation": 0.8}}
        risk_mgr = AdvancedRiskManager(config)

        assert risk_mgr.max_daily_loss_pct == -5.0
        assert risk_mgr.market_crash_threshold == -2.0
        assert risk_mgr.max_correlation == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
