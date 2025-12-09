import pandas as pd
from src.execution import ExecutionEngine
from src.portfolio_rebalancer import PortfolioRebalancer


class DummyPaperTrader:
    def __init__(self, positions: pd.DataFrame, total_equity: float = 100000, cash: float = 50000):
        self._positions = positions
        self._balance = {"total_equity": total_equity, "cash": cash}
        self.initial_capital = total_equity

    def get_positions(self) -> pd.DataFrame:
        return self._positions

    def get_current_balance(self):
        return self._balance

    def execute_trade(self, *args, **kwargs):
        # simplify: pretend success without touching positions
        return True


def test_execution_sell_skips_missing_ticker(monkeypatch):
    positions = pd.DataFrame([
        {"ticker": "HOLD", "quantity": 10, "entry_price": 100, "current_price": 110}
    ]).set_index("ticker", drop=False)
    pt = DummyPaperTrader(positions)
    engine = ExecutionEngine(pt)
    monkeypatch.setattr(engine, "check_risk", lambda: True)

    signals = [{"ticker": "UNKNOWN", "action": "SELL", "reason": "test"}]
    trades = engine.execute_orders(signals, {"UNKNOWN": 110.0})

    assert trades == []  # 安全にスキップされること


def test_rebalancer_skips_empty_ticker_and_generates_signal():
    positions = pd.DataFrame([
        {"ticker": None, "quantity": 10, "current_price": 100},
        {"ticker": "AAA", "quantity": 10, "current_price": 10},
    ]).set_index("ticker", drop=False)
    pt = DummyPaperTrader(positions, total_equity=1000, cash=200)

    logger_messages = []
    rebal = PortfolioRebalancer({
        "rebalance": {
            "max_single_position": 5.0,  # 5% を超えたらリバランス
            "max_region": {"japan": 100.0, "us": 100.0, "europe": 100.0}
        }
    })

    analysis = rebal.analyze_portfolio(pt, logger_messages.append)

    assert None not in analysis["position_ratios"]
    assert analysis["needs_rebalance"] is True

    signals = rebal.generate_rebalance_signals(pt, logger_messages.append)
    assert len(signals) == 1
    assert signals[0]["ticker"] == "AAA"
