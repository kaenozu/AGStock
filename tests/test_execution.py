"""
ExecutionEngineのテスト
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.execution import ExecutionEngine
from src.paper_trader import PaperTrader


@pytest.fixture
def paper_trader():
    """モックのPaperTraderを提供"""
    pt = Mock(spec=PaperTrader)
    pt.initial_capital = 1000000
    pt.get_current_balance.return_value = {
        'cash': 800000,
        'total_equity': 1000000
    }
    pt.get_positions.return_value = Mock()
    return pt


@pytest.fixture
def execution_engine(paper_trader):
    """ExecutionEngineインスタンスを提供"""
    return ExecutionEngine(paper_trader)


@pytest.fixture
def real_broker():
    """モックの実ブローカーを提供"""
    broker = Mock()
    broker.get_balance.return_value = {
        'cash': 800000,
        'total_equity': 1000000
    }
    broker.buy_order.return_value = True
    return broker


def test_init(paper_trader):
    """初期化のテスト"""
    engine = ExecutionEngine(paper_trader)
    assert engine.pt == paper_trader
    assert engine.real_broker is None
    assert engine.max_position_size_pct == 0.20
    assert engine.max_drawdown_limit == 0.15


def test_init_with_real_broker(paper_trader, real_broker):
    """実ブローカー付きの初期化テスト"""
    engine = ExecutionEngine(paper_trader, real_broker)
    assert engine.real_broker == real_broker


def test_check_risk_safe(execution_engine, paper_trader):
    """リスクチェック：安全な状態"""
    paper_trader.get_current_balance.return_value = {
        'cash': 900000,
        'total_equity': 1050000
    }
    
    result = execution_engine.check_risk()
    assert result is True


def test_check_risk_max_drawdown_exceeded(execution_engine, paper_trader):
    """リスクチェック：最大ドローダウン超過"""
    # 15%以上のドローダウン（1,000,000 -> 840,000 = 16%減）
    paper_trader.get_current_balance.return_value = {
        'cash': 840000,
        'total_equity': 840000
    }
    
    result = execution_engine.check_risk()
    assert result is False


def test_check_risk_with_real_broker(paper_trader, real_broker):
    """リスクチェック：実ブローカーとの乖離確認"""
    engine = ExecutionEngine(paper_trader, real_broker)
    
    # 実残高と仮想残高が一致
    real_broker.get_balance.return_value = {
        'total_equity': 1000000
    }
    
    result = engine.check_risk()
    assert result is True


def test_check_risk_with_real_broker_divergence(paper_trader, real_broker, capsys):
    """リスクチェック：実残高と仮想残高の乖離"""
    engine = ExecutionEngine(paper_trader, real_broker)
    
    # 実残高が大きく異なる（6%の乖離）
    real_broker.get_balance.return_value = {
        'total_equity': 1060000
    }
    
    result = engine.check_risk()
    captured = capsys.readouterr()
    
    assert result is True  # 警告は出るが取引は継続
    assert "WARNING" in captured.out


def test_check_risk_with_real_broker_error(paper_trader, real_broker, capsys):
    """リスクチェック：実ブローカーエラー時の処理"""
    engine = ExecutionEngine(paper_trader, real_broker)
    
    # 実ブローカーがエラーを返す
    real_broker.get_balance.side_effect = Exception("Connection error")
    
    result = engine.check_risk()
    captured = capsys.readouterr()
    
    assert result is True  # エラーでも取引は継続
    assert "実残高確認エラー" in captured.out


def test_calculate_position_size_us_stock(execution_engine, paper_trader):
    """ポジションサイズ計算：米国株"""
    paper_trader.get_current_balance.return_value = {
        'cash': 800000,
        'total_equity': 1000000
    }
    
    # 20%の1000000 = 200000円分、confidence=1.0
    # 価格が100円なら2000株
    qty = execution_engine.calculate_position_size('AAPL', 100, confidence=1.0)
    assert qty == 2000


def test_calculate_position_size_japan_stock(execution_engine, paper_trader):
    """ポジションサイズ計算：日本株（100株単位）"""
    paper_trader.get_current_balance.return_value = {
        'cash': 800000,
        'total_equity': 1000000
    }
    
    # 20%の1000000 = 200000円分、confidence=1.0
    # 価格が1000円なら200株（100株単位で丸め）
    qty = execution_engine.calculate_position_size('7203.T', 1000, confidence=1.0)
    assert qty == 200


def test_calculate_position_size_with_confidence(execution_engine, paper_trader):
    """ポジションサイズ計算：信頼度による調整"""
    paper_trader.get_current_balance.return_value = {
        'cash': 800000,
        'total_equity': 1000000
    }
    
    # confidence=0.5なら半分のサイズ
    qty = execution_engine.calculate_position_size('AAPL', 100, confidence=0.5)
    assert qty == 1000  # 2000 * 0.5


def test_calculate_position_size_insufficient_cash(execution_engine, paper_trader):
    """ポジションサイズ計算：現金不足"""
    paper_trader.get_current_balance.return_value = {
        'cash': 50000,  # 少ない現金
        'total_equity': 1000000
    }
    
    # 現金が少ないので小さいサイズになる
    qty = execution_engine.calculate_position_size('AAPL', 100, confidence=1.0)
    assert qty == 500  # 50000 / 100


def test_calculate_position_size_too_expensive(execution_engine, paper_trader):
    """ポジションサイズ計算：価格が高すぎて買えない"""
    paper_trader.get_current_balance.return_value = {
        'cash': 50000,
        'total_equity': 1000000
    }
    
    # 1株が100000円なので買えない
    qty = execution_engine.calculate_position_size('AAPL', 100000, confidence=1.0)
    assert qty == 0


def test_execute_orders_buy_success(execution_engine, paper_trader, capsys):
    """注文実行：買い注文成功"""
    paper_trader.execute_trade.return_value = True
    
    signals = [
        {'ticker': 'AAPL', 'action': 'BUY', 'confidence': 0.8}
    ]
    prices = {'AAPL': 150}
    
    execution_engine.execute_orders(signals, prices)
    
    # execute_tradeが呼ばれたことを確認
    paper_trader.execute_trade.assert_called_once()
    
    captured = capsys.readouterr()
    assert "EXECUTED: BUY" in captured.out


def test_execute_orders_buy_with_quantity(execution_engine, paper_trader):
    """注文実行：数量指定の買い注文"""
    paper_trader.execute_trade.return_value = True
    
    signals = [
        {'ticker': 'AAPL', 'action': 'BUY', 'quantity': 100, 'confidence': 0.8}
    ]
    prices = {'AAPL': 150}
    
    execution_engine.execute_orders(signals, prices)
    
    # 指定された数量で呼ばれたことを確認
    args = paper_trader.execute_trade.call_args
    assert args[0][2] == 100  # quantity


def test_execute_orders_buy_failed(execution_engine, paper_trader, capsys):
    """注文実行：買い注文失敗"""
    paper_trader.execute_trade.return_value = False
    
    signals = [
        {'ticker': 'AAPL', 'action': 'BUY', 'confidence': 0.8}
    ]
    prices = {'AAPL': 150}
    
    execution_engine.execute_orders(signals, prices)
    
    captured = capsys.readouterr()
    assert "FAILED: BUY" in captured.out


def test_execute_orders_no_price(execution_engine, paper_trader, capsys):
    """注文実行：価格データなし"""
    signals = [
        {'ticker': 'AAPL', 'action': 'BUY', 'confidence': 0.8}
    ]
    prices = {}  # 価格データなし
    
    execution_engine.execute_orders(signals, prices)
    
    captured = capsys.readouterr()
    assert "Skipping AAPL: No price data" in captured.out


def test_execute_orders_sell(execution_engine, paper_trader, capsys):
    """注文実行：売り注文"""
    import pandas as pd
    
    # ポジションを持っている状態
    positions_df = pd.DataFrame({
        'quantity': [100]
    }, index=['AAPL'])
    paper_trader.get_positions.return_value = positions_df
    paper_trader.execute_trade.return_value = True
    
    signals = [
        {'ticker': 'AAPL', 'action': 'SELL'}
    ]
    prices = {'AAPL': 160}
    
    execution_engine.execute_orders(signals, prices)
    
    # 売り注文が実行されたことを確認
    paper_trader.execute_trade.assert_called_once()
    args = paper_trader.execute_trade.call_args
    assert args[0][1] == 'SELL'
    assert args[0][2] == 100  # 保有数量


def test_execute_orders_risk_check_failed(execution_engine, paper_trader):
    """注文実行：リスクチェック失敗で取引中止"""
    paper_trader.get_current_balance.return_value = {
        'cash': 800000,
        'total_equity': 800000  # 20%のドローダウン
    }
    
    signals = [
        {'ticker': 'AAPL', 'action': 'BUY', 'confidence': 0.8}
    ]
    prices = {'AAPL': 150}
    
    execution_engine.execute_orders(signals, prices)
    
    # execute_tradeが呼ばれないことを確認
    paper_trader.execute_trade.assert_not_called()


def test_execute_orders_with_real_broker(paper_trader, real_broker, capsys):
    """注文実行：実ブローカーでの取引"""
    engine = ExecutionEngine(paper_trader, real_broker)
    
    signals = [
        {'ticker': 'AAPL', 'action': 'BUY', 'quantity': 100}
    ]
    prices = {'AAPL': 150}
    
    engine.execute_orders(signals, prices)
    
    # 実ブローカーとペーパートレーダー両方が呼ばれる
    real_broker.buy_order.assert_called_once()
    paper_trader.execute_trade.assert_called_once()
    
    captured = capsys.readouterr()
    assert "REAL TRADE" in captured.out


# === ミニ株対応テスト ===

def test_get_japan_unit_size_mini_enabled(paper_trader):
    """ミニ株有効時のユニットサイズ（1株）"""
    with patch('builtins.open', MagicMock()):
        with patch('json.load') as mock_json:
            mock_json.return_value = {
                "mini_stock": {"enabled": True, "unit_size": 1}
            }
            engine = ExecutionEngine(paper_trader)
            assert engine.get_japan_unit_size() == 1


def test_get_japan_unit_size_mini_disabled(paper_trader):
    """ミニ株無効時のユニットサイズ（100株）"""
    with patch('builtins.open', MagicMock()):
        with patch('json.load') as mock_json:
            mock_json.return_value = {
                "mini_stock": {"enabled": False}
            }
            engine = ExecutionEngine(paper_trader)
            assert engine.get_japan_unit_size() == 100


def test_calculate_trading_fee(paper_trader):
    """ミニ株手数料計算"""
    with patch('builtins.open', MagicMock()):
        with patch('json.load') as mock_json:
            mock_json.return_value = {
                "mini_stock": {
                    "enabled": True,
                    "fee_rate": 0.0022,
                    "spread_rate": 0.005
                }
            }
            engine = ExecutionEngine(paper_trader)
            # 10000円の取引で 0.72% = 72円
            fee = engine.calculate_trading_fee(10000, is_mini_stock=True)
            assert fee == pytest.approx(72, rel=0.01)


def test_calculate_position_size_mini_stock(paper_trader):
    """ミニ株対応のポジションサイズ計算（1株単位）"""
    paper_trader.get_current_balance.return_value = {
        'cash': 50000,
        'total_equity': 100000
    }
    
    with patch('builtins.open', MagicMock()):
        with patch('json.load') as mock_json:
            mock_json.return_value = {
                "mini_stock": {
                    "enabled": True, 
                    "unit_size": 1,
                    "min_order_amount": 500
                }
            }
            engine = ExecutionEngine(paper_trader)
            
            # 20%の100000 = 20000円、価格3000円なら6株
            qty = engine.calculate_position_size('7203.T', 3000, confidence=1.0)
            assert qty == 6
