"""
FullyAutomatedTraderのテスト
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from src.trading.fully_automated_trader import FullyAutomatedTrader


class TestFullyAutomatedTrader:
    """FullyAutomatedTraderのテストクラス"""

    @pytest.fixture
    def mock_config(self):
        """テスト用コンフィグ"""
        return {
            "risk_guard": {"enabled": True, "daily_loss_limit_pct": -5.0, "max_vix": 40.0},
            "safety": {"require_manual_approval": False, "max_daily_trades": 10},
            "portfolio": {
                "target_japan_pct": 60.0,
                "target_us_pct": 30.0,
                "target_europe_pct": 10.0,
                "allow_small_mid_cap": True,
            },
            "backup": {"enabled": False},
        }

    @pytest.fixture
    def trader(self, mock_config, tmp_path):
        """テスト用のFullyAutomatedTraderインスタンス"""
        # 一時コンフィグファイル作成
        import json

        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(mock_config, f)

        with patch("src.trading.fully_automated_trader.SmartNotifier"):
            with patch("src.trading.fully_automated_trader.PaperTrader"):
                with patch("src.trading.fully_automated_trader.ExecutionEngine"):
                    trader = FullyAutomatedTrader(str(config_file))
                    return trader

    def test_initialization(self, trader):
        """初期化テスト"""
        assert trader is not None
        assert trader.asset_selector is not None
        assert trader.position_manager is not None
        # コンフィグ値の確認
        assert trader.config["portfolio"]["target_japan_pct"] == 60.0

    # def test_calculate_daily_pnl(self, trader):
    #     """日次損益計算テスト - コンポーネントに委譲されたため削除または移動"""
    #     pass

    def test_is_safe_to_trade_daily_loss_limit(self, trader):
        """日次損失制限チェックテスト"""
        # 大きな損失をモック
        trader.pt.get_trade_history.return_value = pd.DataFrame(
            {"timestamp": [pd.Timestamp.now()], "realized_pnl": [-600000]}  # -60万円
        )

        trader.pt.get_current_balance.return_value = {"total_equity": 10000000}

        is_safe, reason = trader.is_safe_to_trade()

        assert is_safe == False
        assert "日次損失制限" in reason

    @patch("yfinance.Ticker")
    def test_is_safe_to_trade_vix_check(self, mock_ticker, trader):
        """VIXチェックテスト"""
        # 高VIXをモック
        mock_vix = Mock()
        mock_vix.history.return_value = pd.DataFrame({"Close": [50]})
        mock_ticker.return_value = mock_vix

        trader.pt.get_trade_history.return_value = pd.DataFrame()
        trader.pt.get_current_balance.return_value = {"total_equity": 10000000}

        # SafetyChecksクラス内でのVIXチェックをモックする必要があるかもしれないが、
        # SafetyChecksはyfinanceを使っているはず
        with patch("src.trading.safety_checks.yf.Ticker", return_value=mock_vix):
             is_safe, reason = trader.is_safe_to_trade()

        assert is_safe == False
        assert "VIX" in reason

    def test_get_target_tickers(self, trader):
        """対象銘柄取得テスト"""
        trader.pt.get_positions.return_value = pd.DataFrame()
        trader.pt.get_current_balance.return_value = {"total_equity": 10000000}
        
        # AssetSelectorのモック
        trader.asset_selector.get_target_tickers = Mock(return_value=["7203.T", "9984.T"])

        tickers = trader.get_target_tickers()

        assert isinstance(tickers, list)
        assert len(tickers) > 0

    def test_filter_by_market_cap(self, trader):
        """時価総額フィルタリングテスト"""
        # 大型株
        # AssetSelectorのメソッドを呼び出す
        result = trader.asset_selector.filter_by_market_cap("TEST", {"marketCap": 10**12})
        assert result == True

        # 極小型株
        result = trader.asset_selector.filter_by_market_cap("TEST", {"marketCap": 10**8})
        assert result == False

    @patch("src.data_loader.fetch_stock_data")
    def test_fetch_data_with_retry_success(self, mock_fetch, trader):
        """リトライ機能成功テスト"""
        mock_fetch.return_value = {"TEST": Mock()}

        # PositionManagerのメソッドを呼び出す
        result = trader.position_manager._fetch_data_with_retry(["TEST"])

        assert result is not None
        assert mock_fetch.called

    @patch("src.data_loader.fetch_stock_data")
    def test_fetch_data_with_retry_failure(self, mock_fetch, trader):
        """リトライ機能失敗テスト"""
        mock_fetch.side_effect = Exception("Network error")

        # PositionManagerのメソッドを呼び出す
        with pytest.raises(Exception):
            trader.position_manager._fetch_data_with_retry(["TEST"])

        # 3回リトライされたか確認
        assert mock_fetch.call_count == 3


    def test_emergency_stop(self, trader):
        """緊急停止テスト"""
        trader.emergency_stop("Test reason")

        assert trader.emergency_stop_triggered == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
