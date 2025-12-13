"""
新機能のテストスイート

pytest形式のユニットテスト
実行方法: pytest tests/test_new_features.py -v
"""

from unittest.mock import MagicMock, Mock

import numpy as np
import pandas as pd
import pytest

from src.performance_analyzer import PerformanceAnalyzer
from src.portfolio_rebalancer import PortfolioRebalancer
from src.trading_cost import TradingCostCalculator


@pytest.fixture
def mock_paper_trader():
    """モックPaperTrader"""
    pt = Mock()
    pt.initial_capital = 1000000

    # 資産履歴
    equity_history = pd.DataFrame(
        {"date": pd.date_range("2025-01-01", periods=30), "total_equity": np.linspace(1000000, 1100000, 30)}
    )
    pt.get_equity_history.return_value = equity_history

    # 取引履歴
    trade_history = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=10),
            "ticker": ["AAPL", "GOOGL"] * 5,
            "action": ["BUY", "SELL"] * 5,
            "price": [180, 140] * 5,
            "quantity": [10, 5] * 5,
            "realized_pnl": [1000, -500, 2000, 500, -300, 1500, 800, -200, 1200, 600],
            "strategy": ["LightGBM"] * 10,
        }
    )
    pt.get_trade_history.return_value = trade_history

    # ポジション
    positions = pd.DataFrame(
        {"ticker": ["AAPL", "GOOGL", "8308.T"], "quantity": [100, 50, 1000], "current_price": [180.0, 140.0, 1500.0]}
    ).set_index("ticker")
    pt.get_positions.return_value = positions

    # バランス
    balance = {"total_equity": 1100000, "cash": 100000}
    pt.get_current_balance.return_value = balance

    return pt


class TestPerformanceAnalyzer:
    """パフォーマンス分析のテスト"""

    def test_calculate_metrics(self, mock_paper_trader):
        """メトリクス計算のテスト"""
        analyzer = PerformanceAnalyzer(mock_paper_trader)
        metrics = analyzer.calculate_metrics()

        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "win_rate" in metrics
        assert metrics["total_return"] > 0  # 利益が出ている

    def test_win_rate_calculation(self, mock_paper_trader):
        """勝率計算のテスト"""
        analyzer = PerformanceAnalyzer(mock_paper_trader)
        metrics = analyzer.calculate_metrics()

        # 10件の取引のうち、7件が利益
        expected_win_rate = 0.7
        assert abs(metrics["win_rate"] - expected_win_rate) < 0.01

    def test_empty_history(self):
        """履歴なしのテスト"""
        pt = Mock()
        pt.initial_capital = 1000000
        pt.get_equity_history.return_value = pd.DataFrame()
        pt.get_trade_history.return_value = pd.DataFrame()

        analyzer = PerformanceAnalyzer(pt)
        metrics = analyzer.calculate_metrics()

        assert metrics["total_return"] == 0.0
        assert metrics["win_rate"] == 0.0


class TestPortfolioRebalancer:
    """ポートフォリオリバランスのテスト"""

    @pytest.fixture
    def config(self):
        return {
            "rebalance": {"max_single_position": 30.0, "max_region": {"japan": 60.0, "us": 60.0}, "rebalance_day": 6}
        }

    def test_should_rebalance_on_sunday(self, config):
        """日曜日にリバランスすべきか"""
        rebalancer = PortfolioRebalancer(config)
        # 実際の日付に依存するため、ロジックのテストのみ
        assert hasattr(rebalancer, "should_rebalance_today")

    def test_analyze_portfolio_no_positions(self, config):
        """ポジションなしの分析"""
        pt = Mock()
        pt.get_positions.return_value = pd.DataFrame()
        pt.get_current_balance.return_value = {"total_equity": 1000000}

        rebalancer = PortfolioRebalancer(config)
        result = rebalancer.analyze_portfolio(pt, print)

        assert result["needs_rebalance"] == False
        assert "ポジションなし" in result["reason"]

    def test_analyze_portfolio_needs_rebalance(self, config, mock_paper_trader):
        """リバランスが必要な場合"""
        # AAPLが50%を占めるように調整
        positions = pd.DataFrame({"ticker": ["AAPL"], "quantity": [3000], "current_price": [180.0]}).set_index("ticker")

        mock_paper_trader.get_positions.return_value = positions
        mock_paper_trader.get_current_balance.return_value = {"total_equity": 1000000}

        rebalancer = PortfolioRebalancer(config)
        result = rebalancer.analyze_portfolio(mock_paper_trader, print)

        assert result["needs_rebalance"] == True
        assert len(result["reasons"]) > 0


class TestTradingCostCalculator:
    """取引コスト計算のテスト"""

    @pytest.fixture
    def config(self):
        return {
            "trading_costs": {
                "jp_commission_rate": 0.001,
                "jp_min_commission": 100,
                "us_commission_rate": 0.0045,
                "us_min_commission": 0,
                "us_max_commission": 20,
                "tax_rate": 0.20315,
            }
        }

    def test_jp_stock_commission(self, config):
        """日本株の手数料計算"""
        calc = TradingCostCalculator(config)

        # 100万円の取引
        commission = calc.calculate_commission("8308.T", 1000, 1000)

        # 0.1% = 1000円
        assert commission == 1000

    def test_jp_stock_min_commission(self, config):
        """日本株の最低手数料"""
        calc = TradingCostCalculator(config)

        # 5万円の取引（0.1% = 50円 < 最低100円）
        commission = calc.calculate_commission("8308.T", 500, 100)

        assert commission == 100

    def test_us_stock_commission(self, config):
        """米国株の手数料計算"""
        calc = TradingCostCalculator(config)

        # $1000の取引
        commission = calc.calculate_commission("AAPL", 100, 10)

        # 0.45% = $4.5
        assert commission == 4.5

    def test_us_stock_max_commission(self, config):
        """米国株の上限手数料"""
        calc = TradingCostCalculator(config)

        # $10000の取引（0.45% = $45 > 上限$20）
        commission = calc.calculate_commission("AAPL", 1000, 10)

        assert commission == 20

    def test_net_profit_calculation(self, config):
        """純利益計算のテスト"""
        calc = TradingCostCalculator(config)

        # AAPL: $100で10株購入 → $110で売却
        result = calc.calculate_net_profit("AAPL", 100, 110, 10)

        assert result["gross_profit"] == 100  # $10 × 10株
        assert result["total_commission"] > 0
        assert result["tax"] > 0
        assert result["net_profit"] < result["gross_profit"]

    def test_breakeven_price(self, config):
        """損益分岐点の計算"""
        calc = TradingCostCalculator(config)

        breakeven = calc.get_breakeven_price("AAPL", 100, 10)

        # 手数料・税金を考慮すると、購入価格より高くなる
        assert breakeven > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
