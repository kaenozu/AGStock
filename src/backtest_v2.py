"""
AGStock バックテスト機能
戦略の過去データ検証
"""

import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """バックテスト結果"""

    symbol: str
    initial_capital: float
    final_capital: float
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    profit_factor: float
    avg_win: float
    avg_loss: float
    trade_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Trade:
    """取引記録"""

    timestamp: str
    symbol: str
    action: str
    quantity: float
    price: float
    pnl: float = 0.0


class BacktestEngine:
    """バックテストエンジン"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []

    def generate_dummy_data(self, symbol: str, days: int = 365, start_price: float = 150.0) -> List[Dict[str, Any]]:
        """ダミー価格データ生成"""
        data = []
        current_price = start_price
        current_date = datetime.now() - timedelta(days=days)

        for _ in range(days):
            change = random.uniform(-0.03, 0.03)
            current_price = current_price * (1 + change)
            current_price = max(current_price, 10.0)

            data.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "open": current_price * random.uniform(0.99, 1.01),
                    "high": current_price * random.uniform(1.0, 1.03),
                    "low": current_price * random.uniform(0.97, 1.0),
                    "close": current_price,
                    "volume": int(random.uniform(1000000, 10000000)),
                }
            )
            current_date += timedelta(days=1)

        return data

    def run_strategy(
        self,
        symbol: str,
        data: List[Dict[str, Any]],
        strategy_type: str = "moving_average",
        short_window: int = 10,
        long_window: int = 30,
    ) -> BacktestResult:
        """戦略バックテスト実行"""
        if not data:
            data = self.generate_dummy_data(symbol)

        capital = self.initial_capital
        position = 0
        entry_price = 0.0
        trades = []
        equity_curve = [capital]
        wins = 0
        losses = 0
        total_pnl = 0.0

        prices = [d["close"] for d in data]

        for i, day in enumerate(data):
            price = day["close"]
            date = day["date"]

            if strategy_type == "moving_average":
                if i < long_window:
                    continue

                short_ma = np.mean(prices[i - short_window : i])
                long_ma = np.mean(prices[i - long_window : i])

                if short_ma > long_ma and position == 0:
                    position = capital / price
                    entry_price = price
                    capital = 0
                    trades.append(
                        Trade(
                            timestamp=date,
                            symbol=symbol,
                            action="BUY",
                            quantity=position,
                            price=price,
                        )
                    )

                elif short_ma < long_ma and position > 0:
                    pnl = (price - entry_price) * position
                    capital = position * price
                    trades.append(
                        Trade(
                            timestamp=date,
                            symbol=symbol,
                            action="SELL",
                            quantity=position,
                            price=price,
                            pnl=pnl,
                        )
                    )
                    if pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                    total_pnl += pnl
                    position = 0

            elif strategy_type == "momentum":
                if i < 10:
                    continue

                returns = (prices[i] / prices[i - 10]) - 1

                if returns > 0.05 and position == 0:
                    position = capital / price
                    entry_price = price
                    capital = 0
                    trades.append(
                        Trade(
                            timestamp=date,
                            symbol=symbol,
                            action="BUY",
                            quantity=position,
                            price=price,
                        )
                    )

                elif returns < -0.03 and position > 0:
                    pnl = (price - entry_price) * position
                    capital = position * price
                    trades.append(
                        Trade(
                            timestamp=date,
                            symbol=symbol,
                            action="SELL",
                            quantity=position,
                            price=price,
                            pnl=pnl,
                        )
                    )
                    if pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                    total_pnl += pnl
                    position = 0

            if position > 0:
                equity_curve.append(position * price)
            else:
                equity_curve.append(capital)

        if position > 0:
            final_price = prices[-1]
            capital = position * final_price
            pnl = (final_price - entry_price) * position
            if pnl > 0:
                wins += 1
            else:
                losses += 1
            total_pnl += pnl
            trades.append(
                Trade(
                    timestamp=data[-1]["date"],
                    symbol=symbol,
                    action="SELL",
                    quantity=position,
                    price=final_price,
                    pnl=pnl,
                )
            )

        total_return = (capital - self.initial_capital) / self.initial_capital

        returns_array = np.diff(equity_curve) / np.array(equity_curve[:-1])
        returns_array = returns_array[~np.isnan(returns_array)]

        if len(returns_array) > 0:
            sharpe_ratio = (
                np.mean(returns_array) / np.std(returns_array) * np.sqrt(252) if np.std(returns_array) > 0 else 0
            )
        else:
            sharpe_ratio = 0

        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdowns = (equity_array - running_max) / running_max
        max_drawdown = abs(min(drawdowns)) if len(drawdowns) > 0 else 0

        total_trades = len(trades)
        winning_trades = wins
        losing_trades = losses

        if total_trades > 0:
            win_rate = winning_trades / total_trades
        else:
            win_rate = 0

        profit_factor = (
            abs(total_pnl / winning_trades) / abs(total_pnl / losing_trades)
            if losing_trades > 0 and wins > 0
            else 1.0 if total_pnl > 0 else 0
        )

        avg_win = total_pnl / winning_trades if winning_trades > 0 else 0
        avg_loss = total_pnl / losing_trades if losing_trades > 0 else 0

        days = len(data)
        annual_return = ((1 + total_return) ** (365 / days) - 1) if days > 0 else 0

        return BacktestResult(
            symbol=symbol,
            initial_capital=self.initial_capital,
            final_capital=capital,
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            trade_history=[
                {
                    "timestamp": t.timestamp,
                    "action": t.action,
                    "quantity": t.quantity,
                    "price": t.price,
                    "pnl": t.pnl,
                }
                for t in trades
            ],
        )

    def compare_strategies(
        self,
        symbol: str,
        data: List[Dict[str, Any]],
        strategies: List[str] = None,
    ) -> Dict[str, BacktestResult]:
        """複数戦略比較"""
        if strategies is None:
            strategies = ["moving_average", "momentum"]

        results = {}
        for strategy in strategies:
            result = self.run_strategy(symbol, data, strategy_type=strategy)
            results[strategy] = result
            logger.info(f"{strategy}: Return={result.total_return:.2%}, Sharpe={result.sharpe_ratio:.2f}")

        return results

    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """權益曲線取得"""
        return [{"value": v} for v in self.equity_curve]


def run_quick_backtest(
    symbol: str = "AAPL",
    initial_capital: float = 100000,
    strategy: str = "moving_average",
) -> BacktestResult:
    """クイックバックテスト実行"""
    engine = BacktestEngine(initial_capital)
    return engine.run_strategy(symbol, [], strategy_type=strategy)


def generate_backtest_report(result: BacktestResult) -> str:
    """バックテストレポート生成"""
    report = f"""
================================================================================
                        BACKTEST REPORT: {result.symbol}
================================================================================

INITIAL CAPITAL:    ${result.initial_capital:,.2f}
FINAL CAPITAL:      ${result.final_capital:,.2f}
TOTAL RETURN:       {result.total_return:+.2%}
ANNUAL RETURN:      {result.annual_return:+.2%}

RISK METRICS:
  Max Drawdown:     {result.max_drawdown:.2%}
  Sharpe Ratio:     {result.sharpe_ratio:.2f}

TRADING STATISTICS:
  Total Trades:     {result.total_trades}
  Winning Trades:   {result.winning_trades}
  Losing Trades:    {result.losing_trades}
  Win Rate:         {result.win_rate:.2%}
  Profit Factor:    {result.profit_factor:.2f}

P&L SUMMARY:
  Average Win:      ${result.avg_win:,.2f}
  Average Loss:     ${result.avg_loss:,.2f}

================================================================================
"""
    return report
