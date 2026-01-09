"""
SimpleDashboardのテスト
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.simple_dashboard import SimpleDashboard


class TestSimpleDashboard:
    """SimpleDashboardのテストクラス"""

    @pytest.fixture
    def mock_paper_trader(self):
        """モックPaperTrader"""
        pt = Mock()

        # get_current_balance
        pt.get_current_balance.return_value = {
            "cash": 3000000,
            "total_equity": 10000000,
            "invested_amount": 7000000,
            "unrealized_pnl": 0,
        }

        # get_positions
        pt.get_positions.return_value = pd.DataFrame(
            {
                "ticker": ["7203.T", "9984.T"],
                "quantity": [100, 50],
                "entry_price": [1000, 5000],
                "current_price": [1050, 5100],
                "market_value": [105000, 255000],
                "unrealized_pnl": [5000, 5000],
                "unrealized_pnl_pct": [5.0, 2.0],
            }
        )

        # get_trade_history
        pt.get_trade_history.return_value = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-01", periods=5),
                "ticker": ["7203.T"] * 5,
                "action": ["BUY", "SELL", "BUY", "SELL", "BUY"],
                "quantity": [100] * 5,
                "price": [1000, 1050, 1000, 1020, 1000],
                "total_amount": [100000, 105000, 100000, 102000, 100000],
            }
        )

        return pt

    def test_init(self, mock_paper_trader):
        """初期化テスト"""
        dashboard = SimpleDashboard(mock_paper_trader)
        assert dashboard is not None
        assert dashboard.pt == mock_paper_trader

    def test_display_metrics(self, mock_paper_trader):
        """メトリクス表示テスト"""
        dashboard = SimpleDashboard(mock_paper_trader)

        with patch("streamlit.metric") as mock_metric:
            dashboard.display_metrics()

            # メトリクスが表示されたか
            assert mock_metric.called

    def test_calculate_risk_level(self, mock_paper_trader):
        """リスクレベル計算テスト"""
        dashboard = SimpleDashboard(mock_paper_trader)

        # VIXが低い場合
        with patch("yfinance.Ticker") as mock_ticker:
            mock_vix = Mock()
            mock_vix.history.return_value = pd.DataFrame({"Close": [15]})
            mock_ticker.return_value = mock_vix

            risk_level = dashboard.calculate_risk_level()
            assert risk_level in ["低", "中", "高"]

    def test_get_advice(self, mock_paper_trader):
        """アドバイス取得テスト"""
        dashboard = SimpleDashboard(mock_paper_trader)

        advice = dashboard.get_advice()

        assert isinstance(advice, list)
        assert len(advice) > 0

    def test_format_currency_jp(self):
        """日本語数値フォーマットテスト"""
        from src.simple_dashboard import format_currency_jp

        # 1万円未満
        assert format_currency_jp(5000) == "¥5,000"

        # 1万円台
        assert format_currency_jp(50000) == "¥5.0万円"

        # 100万円台
        assert format_currency_jp(5000000) == "¥500万円"

        # 1億円以上
        assert format_currency_jp(500000000) == "¥5.0億円"

    def test_get_trend_indicator(self):
        """トレンドインジケーターテスト"""
        from src.simple_dashboard import get_trend_indicator

        # プラス
        indicator = get_trend_indicator(1000)
        assert "📈" in indicator
        assert "green" in indicator

        # マイナス
        indicator = get_trend_indicator(-1000)
        assert "📉" in indicator
        assert "red" in indicator

        # ゼロ
        indicator = get_trend_indicator(0)
        assert "➡️" in indicator


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
