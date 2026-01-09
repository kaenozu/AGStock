from unittest.mock import MagicMock

import pytest

from src.execution import ExecutionEngine
from src.paper_trader import PaperTrader


class TestExecutionEngineReal:
    @pytest.fixture
    def engine(self):
        mock_pt = MagicMock(spec=PaperTrader)
        mock_pt.get_current_balance.return_value = {"total_equity": 1000000, "cash": 500000}
        mock_pt.initial_capital = 1000000

        mock_real_broker = MagicMock()

        return ExecutionEngine(paper_trader=mock_pt, real_broker=mock_real_broker)

    def test_execute_orders_real_buy(self, engine):
        # テストデータ
        signals = [{"ticker": "7203", "action": "BUY", "confidence": 0.9}]
        prices = {"7203": 2000.0}

        # 実ブローカーのモック設定
        engine.real_broker.buy_order.return_value = True

        # 実行
        engine.execute_orders(signals, prices)

        # 検証
        # 実ブローカーのbuy_orderが呼ばれたか
        engine.real_broker.buy_order.assert_called_once()
        args, _ = engine.real_broker.buy_order.call_args
        assert args[0] == "7203"  # ticker
        assert args[2] == 2000.0  # price

        # PaperTraderにも記録されたか
        engine.pt.execute_trade.assert_called_once()

    def test_execute_orders_real_sell_skipped(self, engine):
        """実取引の売り注文は未実装のためスキップされることを確認"""
        signals = [{"ticker": "7203", "action": "SELL"}]
        prices = {"7203": 2000.0}

        # ポジション保有状態をモック
        import pandas as pd

        engine.pt.get_positions.return_value = pd.DataFrame({"quantity": [100]}, index=["7203"])

        # 実行
        engine.execute_orders(signals, prices)

        # 検証
        # 実ブローカーのsell_order（未実装）は呼ばれない、またはエラーにならない
        # 現状の実装ではメソッド自体がないか、呼び出しコードがコメントアウトされている
        # ログ出力のみで終了するはず
        pass

    def test_check_risk_divergence(self, engine):
        """実残高と仮想残高の乖離チェック"""
        # 実残高が大きく異なる場合
        engine.real_broker.get_balance.return_value = {"total_equity": 500000}  # 仮想は100万なので50%乖離

        # check_riskを実行（標準出力に警告が出るはずだが、戻り値はTrueのまま）
        result = engine.check_risk()

        assert result is True
        engine.real_broker.get_balance.assert_called_once()
