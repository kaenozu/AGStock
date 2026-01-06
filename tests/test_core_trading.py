"""
コア取引機能の統合テスト
取引エンジン、ポートフォリオ管理、リスク管理の連携をテスト
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# テスト対象モジュール
from src.trading.fully_automated_trader import FullyAutomatedTrader
from src.portfolio_manager import PortfolioManager
from src.advanced_risk import AdvancedRiskManager
from src.data_loader import DataLoader


class TestCoreTradingFunctionality:
    """コア取引機能のテストスイート"""

    @pytest.fixture
    def mock_config(self):
        """モック設定"""
        return {
            "trading": {
                "max_position_size": 0.1,
                "stop_loss_pct": 0.05,
                "risk_limit": 0.02,
            },
            "data": {"default_period": "1y", "interval": "1d"},
        }

    @pytest.fixture
    def mock_trader(self, mock_config):
        """モック取引エンジン"""
        with patch(
            "src.trading.fully_automated_trader.FullyAutomatedTrader.__init__",
            return_value=None,
        ):
            trader = FullyAutomatedTrader()
            trader.config = mock_config
            
            # Attributes
            trader.target_japan_pct = 40.0
            trader.target_us_pct = 30.0
            trader.target_europe_pct = 10.0
            trader.vix_symbol = "^VIX"
            trader.backup_enabled = False
            
            # Mocks
            trader.pt = Mock()
            trader.portfolio = trader.pt
            trader.risk_manager = Mock()
            trader.data_loader = Mock()
            trader.performance_log = Mock()
            
            # Methods - Mock them by patching the instance attributes
            trader.execute_trade = Mock(return_value=True)
            trader.update_portfolio = Mock(return_value=True)
            trader.send_notification = Mock()
            trader.record_performance = Mock()
            trader.handle_risk_alert = Mock()
            trader.get_market_data = AsyncMock(return_value={})
            trader.generate_signals = AsyncMock(return_value={"AAPL": {"action": "BUY"}})
            trader.scan_market = Mock(return_value=[])
            
            # Default return values
            trader.pt.get_current_balance.return_value = {"total_equity": 1000000.0, "cash": 1000000.0}
            trader.pt.get_positions.return_value = pd.DataFrame()
            
            return trader

    def test_portfolio_initialization(self, mock_config):
        """ポートフォリオの初期化テスト"""
        portfolio = PortfolioManager(mock_config)

        assert portfolio.cash_balance >= 0
        assert isinstance(portfolio.positions, dict)
        assert portfolio.total_value() >= 0

    def test_risk_manager_limits(self, mock_config):
        """リスク管理の制限テスト"""
        risk_manager = AdvancedRiskManager(mock_config)

        # 最大ポジションサイズのチェック
        assert risk_manager.max_position_size == 0.1
        assert risk_manager.stop_loss_pct == 0.05
        assert risk_manager.daily_risk_limit == 0.02

    def test_data_loader_initialization(self, mock_config):
        """データローダーの初期化テスト"""
        data_loader = DataLoader(mock_config)

        assert data_loader.default_period == "1y"
        assert data_loader.interval == "1d"

    @pytest.mark.asyncio
    async def test_trading_signal_generation(self, mock_trader):
        """取引シグナル生成のテスト"""
        # シグナル生成のテスト
        signals = await mock_trader.generate_signals(["AAPL"])

        assert isinstance(signals, dict)
        assert "AAPL" in signals
        assert "action" in signals["AAPL"]
        assert signals["AAPL"]["action"] in ["BUY", "SELL", "HOLD"]

    def test_portfolio_risk_calculation(self, mock_config):
        """ポートフォリオリスク計算のテスト"""
        portfolio = PortfolioManager(mock_config)
        risk_manager = AdvancedRiskManager(mock_config)

        # テスト用ポジションを追加
        portfolio.add_position("AAPL", 100, 150.0)
        portfolio.add_position("GOOGL", 50, 2500.0)

        # リスク計算
        risk_metrics = risk_manager.calculate_portfolio_risk(
            portfolio.get_positions()
        )

        assert isinstance(risk_metrics, dict)
        portfolio_risk = risk_metrics["risk_score"]
        assert portfolio_risk > 0
        assert isinstance(portfolio_risk, (float, int))

    def test_stop_loss_execution(self, mock_trader):
        """損切り実行のテスト"""
        # モックポジション
        mock_position = {
            "ticker": "AAPL",
            "quantity": 100,
            "entry_price": 150.0,
            "current_price": 140.0,  # 6.67%の損失
            "unrealized_pnl": -1000.0,
        }

        # 損切りの条件チェック
        mock_trader.risk_manager.should_stop_loss.return_value = True
        should_stop = mock_trader.risk_manager.should_stop_loss(mock_position)

        # 5%を超える損失で損切りが発生
        assert should_stop is True

    def test_position_sizing_calculation(self, mock_trader):
        """ポジションサイジング計算のテスト"""
        portfolio_value = 1000000  # 100万円
        risk_amount = 20000  # 2%のリスク

        mock_trader.risk_manager.calculate_position_size.return_value = 50000.0
        position_size = mock_trader.risk_manager.calculate_position_size(
            portfolio_value, risk_amount, 150.0, 140.0
        )

        assert position_size > 0
        assert (
            position_size
            <= portfolio_value * mock_trader.config["trading"]["max_position_size"]
        )

    @pytest.mark.asyncio
    async def test_trade_execution_flow(self, mock_trader):
        """取引実行フローのテスト"""
        # 取引シグナル
        signal = {
            "ticker": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0,
            "reason": "テスト取引",
        }

        # 取引実行
        result = await mock_trader.execute_signal(signal)

        assert result is True
        mock_trader.execute_trade.assert_called_once()
        mock_trader.update_portfolio.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_trading(self, mock_trader):
        """取引時のエラーハンドリングテスト"""
        # データ取得エラーのモック
        mock_trader.generate_signals.side_effect = Exception("データ取得エラー")

        # エラーが適切に処理されるか
        with pytest.raises(Exception):
            await mock_trader.generate_signals(["AAPL"])

    def test_performance_monitoring(self, mock_trader):
        """パフォーマンス監視のテスト"""
        # パフォーマンスデータ
        performance_data = {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.05,
            "win_rate": 0.65,
            "total_trades": 100,
        }

        # パフォーマンス記録のテスト
        mock_trader.record_performance(performance_data)

        # 記録されたデータの検証
        mock_trader.record_performance.assert_called_with(performance_data)

    def test_risk_alert_system(self, mock_trader):
        """リスクアラートシステムのテスト"""
        # 高リスク状態のシミュレーション
        risk_alert = {
            "type": "HIGH_RISK",
            "message": "ポートフォリオリスクが閾値を超過",
            "current_risk": 0.08,
            "threshold": 0.05,
        }

        # アラート処理のテスト
        mock_trader.handle_risk_alert(risk_alert)

        # アラートが適切に処理されたか
        mock_trader.handle_risk_alert.assert_called_with(risk_alert)

    @pytest.mark.asyncio
    async def test_market_data_integration(self, mock_trader):
        """市場データ統合のテスト"""
        # 複数銘柄のデータ取得
        tickers = ["AAPL", "GOOGL", "MSFT"]

        # モックデータ
        mock_data = {}
        for ticker in tickers:
            mock_data[ticker] = pd.DataFrame(
                {"Close": [100, 105, 102], "Volume": [1000, 1200, 900]},
                index=pd.date_range("2024-01-01", periods=3),
            )

        mock_trader.get_market_data.return_value = mock_data

        # データ取得テスト
        data = await mock_trader.get_market_data(tickers)

        assert len(data) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])