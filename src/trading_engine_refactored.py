"""
リファクタリングされた取引エンジン
複雑度を下げ、保守性を向上
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TradeSignal:
    """取引シグナルのデータクラス"""

    ticker: str
    action: str  # BUY, SELL, HOLD
    quantity: int
    price: float
    reason: str
    confidence: float = 0.0
    timestamp: Optional[datetime] = None


@dataclass
class Position:
    """ポジションのデータクラス"""

    ticker: str
    quantity: int
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    pnl_pct: float


class TradingEngineRefactored:
    """
    リファクタリングされた取引エンジン

    複雑な機能を小さな単位に分割し、
    単一責任の原則を適用
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.cash_balance: float = config.get("initial_balance", 1000000)
        self.risk_manager = RiskManager(config)
        self.signal_generator = SignalGenerator(config)
        self.portfolio_manager = PortfolioManager(config)

    def process_trading_day(self, market_data: Dict[str, pd.DataFrame]) -> List[Trade]:
        """
        取引日の処理を実行

        Args:
            market_data: 銘柄別市場データ

        Returns:
            実行された取引リスト
        """
        # 1. ポジションの更新
        self._update_positions(market_data)

        # 2. シグナル生成
        signals = self._generate_signals(market_data)

        # 3. リスク管理適用
        filtered_signals = self._apply_risk_filters(signals)

        # 4. 取引実行
        trades = self._execute_trades(filtered_signals)

        # 5. ポートフォリオ再均衡
        self._rebalance_portfolio_if_needed()

        return trades

    def _update_positions(self, market_data: Dict[str, pd.DataFrame]) -> None:
        """ポジションを更新"""
        for ticker, position in self.positions.items():
            if ticker in market_data:
                current_price = market_data[ticker]["Close"].iloc[-1]
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                position.unrealized_pnl = position.market_value - (position.quantity * position.entry_price)
                position.pnl_pct = position.unrealized_pnl / (position.quantity * position.entry_price)

    def _generate_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[TradeSignal]:
        """取引シグナルを生成"""
        signals = []

        for ticker, data in market_data.items():
            signal = self.signal_generator.generate_signal(ticker, data)
            if signal:
                signals.append(signal)

        return signals

    def _apply_risk_filters(self, signals: List[TradeSignal]) -> List[TradeSignal]:
        """リスクフィルターを適用"""
        return self.risk_manager.filter_signals(signals, self.positions, self.cash_balance)

    def _execute_trades(self, signals: List[TradeSignal]) -> List[Trade]:
        """取引を実行"""
        trades = []

        for signal in signals:
            trade = self._execute_single_trade(signal)
            if trade:
                trades.append(trade)

        return trades

    def _execute_single_trade(self, signal: TradeSignal) -> Optional[Trade]:
        """単一取引を実行"""
        trade_value = signal.quantity * signal.price

        if signal.action == "BUY":
            if self.cash_balance >= trade_value:
                self._process_buy_trade(signal, trade_value)
                return Trade.from_signal(signal)

        elif signal.action == "SELL":
            if signal.ticker in self.positions:
                self._process_sell_trade(signal, trade_value)
                return Trade.from_signal(signal)

        return None

    def _process_buy_trade(self, signal: TradeSignal, trade_value: float) -> None:
        """買い取引を処理"""
        self.cash_balance -= trade_value

        if signal.ticker in self.positions:
            # 既存ポジションの平均価格を更新
            position = self.positions[signal.ticker]
            total_quantity = position.quantity + signal.quantity
            total_cost = (position.quantity * position.entry_price) + trade_value
            position.entry_price = total_cost / total_quantity
            position.quantity = total_quantity
        else:
            # 新規ポジション
            self.positions[signal.ticker] = Position(
                ticker=signal.ticker,
                quantity=signal.quantity,
                entry_price=signal.price,
                current_price=signal.price,
                market_value=trade_value,
                unrealized_pnl=0.0,
                pnl_pct=0.0,
            )

        logger.info(f"BUY: {signal.quantity} shares of {signal.ticker} at {signal.price}")

    def _process_sell_trade(self, signal: TradeSignal, trade_value: float) -> None:
        """売り取引を処理"""
        position = self.positions[signal.ticker]

        if signal.quantity >= position.quantity:
            # 全部売却
            self.cash_balance += position.quantity * signal.price
            del self.positions[signal.ticker]
        else:
            # 部分売却
            position.quantity -= signal.quantity
            position.market_value = position.quantity * signal.price
            position.unrealized_pnl = position.market_value - (position.quantity * position.entry_price)
            self.cash_balance += trade_value

        logger.info(f"SELL: {signal.quantity} shares of {signal.ticker} at {signal.price}")

    def _rebalance_portfolio_if_needed(self) -> None:
        """必要に応じてポートフォリオを再均衡"""
        should_rebalance = self.portfolio_manager.should_rebalance(self.positions)

        if should_rebalance:
            target_weights = self.portfolio_manager.calculate_target_weights()
            self._apply_rebalancing(target_weights)

    def _apply_rebalancing(self, target_weights: Dict[str, float]) -> None:
        """リバランスを適用"""
        current_weights = self._calculate_current_weights()

        for ticker, target_weight in target_weights.items():
            current_weight = current_weights.get(ticker, 0)
            weight_diff = target_weight - current_weight

            if abs(weight_diff) > 0.05:  # 5%以上の差があれば調整
                self._generate_rebalance_signal(ticker, weight_diff)

    def _calculate_current_weights(self) -> Dict[str, float]:
        """現在のポートフォリオウェイトを計算"""
        total_value = self._calculate_total_portfolio_value()

        if total_value == 0:
            return {}

        weights = {}
        for ticker, position in self.positions.items():
            weights[ticker] = position.market_value / total_value

        return weights

    def _calculate_total_portfolio_value(self) -> float:
        """総ポートフォリオ価値を計算"""
        position_value = sum(pos.market_value for pos in self.positions.values())
        return position_value + self.cash_balance

    def _generate_rebalance_signal(self, ticker: str, weight_diff: float) -> None:
        """リバランスシグナルを生成"""
        total_value = self._calculate_total_portfolio_value()
        target_value = abs(weight_diff) * total_value

        if ticker in self.positions:
            price = self.positions[ticker].current_price
            quantity = int(target_value / price)

            if weight_diff > 0:
                signal = TradeSignal(
                    ticker=ticker,
                    action="BUY",
                    quantity=quantity,
                    price=price,
                    reason=f"Rebalance: weight diff {weight_diff:.2f}",
                )
            else:
                signal = TradeSignal(
                    ticker=ticker,
                    action="SELL",
                    quantity=min(quantity, self.positions[ticker].quantity),
                    price=price,
                    reason=f"Rebalance: weight diff {weight_diff:.2f}",
                )

            self._execute_single_trade(signal)


@dataclass
class Trade:
    """取引データクラス"""

    ticker: str
    action: str
    quantity: int
    price: float
    value: float
    timestamp: datetime
    reason: str

    @classmethod
    def from_signal(cls, signal: TradeSignal) -> "Trade":
        """シグナルから取引を作成"""
        return cls(
            ticker=signal.ticker,
            action=signal.action,
            quantity=signal.quantity,
            price=signal.price,
            value=signal.quantity * signal.price,
            timestamp=signal.timestamp or datetime.now(),
            reason=signal.reason,
        )


class RiskManager:
    """リスク管理クラス"""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.max_position_size = config.get("max_position_size", 0.1)
        self.stop_loss_pct = config.get("stop_loss_pct", 0.05)
        self.max_daily_loss = config.get("max_daily_loss", 0.02)

    def filter_signals(
        self,
        signals: List[TradeSignal],
        positions: Dict[str, Position],
        cash_balance: float,
    ) -> List[TradeSignal]:
        """シグナルをリスクフィルター"""
        filtered = []

        for signal in signals:
            if self._is_signal_valid(signal, positions, cash_balance):
                filtered.append(signal)

        return filtered

    def _is_signal_valid(self, signal: TradeSignal, positions: Dict[str, Position], cash_balance: float) -> bool:
        """シグナルの妥当性チェック"""
        total_value = sum(pos.market_value for pos in positions.values()) + cash_balance
        trade_value = signal.quantity * signal.price

        # ポジションサイズ制限
        if signal.action == "BUY":
            if trade_value > total_value * self.max_position_size:
                return False

        # 損切りの確認
        if signal.action == "SELL" and signal.ticker in positions:
            position = positions[signal.ticker]
            if position.pnl_pct < -self.stop_loss_pct:
                signal.reason = "Stop loss triggered"
                return True

        return True


class SignalGenerator:
    """シグナル生成クラス"""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.strategy = config.get("strategy", "simple_ma")

    def generate_signal(self, ticker: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """取引シグナルを生成"""
        if self.strategy == "simple_ma":
            return self._generate_ma_signal(ticker, data)
        elif self.strategy == "rsi":
            return self._generate_rsi_signal(ticker, data)

        return None

    def _generate_ma_signal(self, ticker: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """移動平均シグナル"""
        if len(data) < 50:
            return None

        short_ma = data["Close"].rolling(10).mean().iloc[-1]
        long_ma = data["Close"].rolling(30).mean().iloc[-1]
        current_price = data["Close"].iloc[-1]

        if short_ma > long_ma and current_price > short_ma:
            return TradeSignal(
                ticker=ticker,
                action="BUY",
                quantity=100,
                price=current_price,
                reason="Golden cross",
                confidence=0.7,
            )
        elif short_ma < long_ma and current_price < short_ma:
            return TradeSignal(
                ticker=ticker,
                action="SELL",
                quantity=100,
                price=current_price,
                reason="Death cross",
                confidence=0.7,
            )

        return None

    def _generate_rsi_signal(self, ticker: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """RSIシグナル"""
        if len(data) < 20:
            return None

        # RSI計算
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        current_rsi = rsi.iloc[-1]
        current_price = data["Close"].iloc[-1]

        if current_rsi < 30:  # 買われすぎ
            return TradeSignal(
                ticker=ticker,
                action="BUY",
                quantity=100,
                price=current_price,
                reason="RSI oversold",
                confidence=0.8,
            )
        elif current_rsi > 70:  # 売られすぎ
            return TradeSignal(
                ticker=ticker,
                action="SELL",
                quantity=100,
                price=current_price,
                reason="RSI overbought",
                confidence=0.8,
            )

        return None


class PortfolioManager:
    """ポートフォリオ管理クラス"""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.rebalance_threshold = config.get("rebalance_threshold", 0.1)
        self.target_weights = config.get("target_weights", {})

    def should_rebalance(self, positions: Dict[str, Position]) -> bool:
        """リバランスが必要か判定"""
        if not self.target_weights:
            return False

        current_weights = self._calculate_current_weights(positions)

        for ticker, target_weight in self.target_weights.items():
            current_weight = current_weights.get(ticker, 0)
            if abs(current_weight - target_weight) > self.rebalance_threshold:
                return True

        return False

    def calculate_target_weights(self) -> Dict[str, float]:
        """目標ウェイトを計算"""
        return self.target_weights

    def _calculate_current_weights(self, positions: Dict[str, Position]) -> Dict[str, float]:
        """現在のウェイトを計算"""
        total_value = sum(pos.market_value for pos in positions.values())

        if total_value == 0:
            return {}

        weights = {}
        for ticker, position in positions.items():
            weights[ticker] = position.market_value / total_value

        return weights
