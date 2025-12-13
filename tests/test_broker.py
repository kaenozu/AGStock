"""
brokerのテスト
"""

from datetime import datetime

import pytest

from src.broker import Broker, Order, Position


def test_position_creation():
    """Positionの作成テスト"""
    position = Position(
        ticker="AAPL", quantity=100, average_entry_price=150.0, current_price=155.0, unrealized_pnl=500.0
    )

    assert position.ticker == "AAPL"
    assert position.quantity == 100
    assert position.average_entry_price == 150.0
    assert position.current_price == 155.0
    assert position.unrealized_pnl == 500.0


def test_position_to_dict():
    """Positionのto_dictメソッドのテスト"""
    position = Position(ticker="GOOGL", quantity=50, average_entry_price=2800.0)

    result = position.to_dict()

    assert result["ticker"] == "GOOGL"
    assert result["quantity"] == 50
    assert result["average_entry_price"] == 2800.0
    assert "current_price" in result
    assert "unrealized_pnl" in result


def test_order_creation():
    """Orderの作成テスト"""
    order = Order(ticker="MSFT", action="BUY", quantity=200, order_type="MARKET")

    assert order.ticker == "MSFT"
    assert order.action == "BUY"
    assert order.quantity == 200
    assert order.order_type == "MARKET"
    assert order.price == 0.0


def test_order_with_price():
    """価格指定のOrderのテスト"""
    order = Order(ticker="TSLA", action="SELL", quantity=50, order_type="LIMIT", price=250.0)

    assert order.ticker == "TSLA"
    assert order.action == "SELL"
    assert order.order_type == "LIMIT"
    assert order.price == 250.0


def test_broker_is_abstract():
    """Brokerが抽象クラスであることを確認"""
    with pytest.raises(TypeError):
        Broker()


class ConcreteBroker(Broker):
    """テスト用の具象ブローカークラス"""

    def get_cash(self):
        return 10000.0

    def get_positions(self):
        return {}

    def get_portfolio_value(self, current_prices):
        return 10000.0

    def execute_order(self, order, current_price, timestamp):
        pass

    def get_trade_history(self):
        return []

    def save_state(self):
        pass

    def load_state(self):
        pass


def test_broker_concrete_implementation():
    """具象ブローカーの実装テスト"""
    broker = ConcreteBroker()

    assert broker.get_cash() == 10000.0
    assert broker.get_positions() == {}
    assert broker.get_portfolio_value({}) == 10000.0
    assert broker.get_trade_history() == []
