import json
import logging
from typing import Any, Dict, List, Optional

from src.paper_trader import PaperTrader

logger = logging.getLogger(__name__)


class ExecutionEngine:
    def __init__(self, paper_trader: PaperTrader, real_broker: Any = None, config_path: str = "config.json") -> None:
        self.pt = paper_trader
        self.real_broker = real_broker
        self.max_position_size_pct: float = 0.20  # Max 20% of equity per stock
        self.max_drawdown_limit: float = 0.15  # Stop trading if DD > 15%

        # ミニ株設定を読み込み
        self.config: Dict[str, Any] = self._load_config(config_path)
        self.mini_stock_config: Dict[str, Any] = self.config.get("mini_stock", {})
        self.mini_stock_enabled: bool = self.mini_stock_config.get("enabled", False)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def get_japan_unit_size(self) -> int:
        """日本株の売買単位を取得（ミニ株対応）"""
        if self.mini_stock_enabled:
            return int(self.mini_stock_config.get("unit_size", 1))
        return 100  # 通常の単元株

    def calculate_trading_fee(self, amount: float, is_mini_stock: bool = False, order_type: str = "寄付") -> float:
        """取引手数料を計算"""
        if is_mini_stock and self.mini_stock_enabled:
            if order_type == "リアルタイム":
                spread_rate = float(self.mini_stock_config.get("spread_rate", 0.0022))
                return amount * spread_rate
            else:
                return 0.0
        else:
            return 0.0

    def check_risk(self) -> bool:
        """Checks global risk parameters. Returns True if safe to trade."""
        balance = self.pt.get_current_balance()
        initial = float(self.pt.initial_capital)
        current_equity = float(balance.get("total_equity", 0.0))

        if initial <= 0:
            logger.warning("Initial capital is zero or invalid.")
            return False

        if self.real_broker:
            try:
                real_balance = self.real_broker.get_balance()
                if real_balance and "total_equity" in real_balance:
                    real_equity = float(real_balance["total_equity"])
                    paper_equity = current_equity
                    diff_pct = abs(real_equity - paper_equity) / paper_equity if paper_equity > 0 else 0
                    if diff_pct > 0.05:
                        logger.warning(f"⚠️ WARNING: 実残高と仮想残高の乖離が大 ({diff_pct:.1%})")
            except Exception as e:
                logger.error(f"⚠️ 実残高確認エラー: {e}")

        drawdown = (initial - current_equity) / initial
        if drawdown > self.max_drawdown_limit:
            logger.error(f"RISK ALERT: Max Drawdown exceeded ({drawdown:.1%}). Trading halted.")
            return False

        return True

    def calculate_position_size(self, ticker: str, price: float, confidence: float = 1.0) -> int:
        """Calculates the number of shares to buy based on risk management."""
        balance = self.pt.get_current_balance()
        equity = float(balance.get("total_equity", 0.0))
        cash = float(balance.get("cash", 0.0))

        target_amount = equity * self.max_position_size_pct
        target_amount *= confidence
        target_amount = min(target_amount, cash)

        if target_amount <= 0:
            return 0

        is_us_stock = "." not in ticker
        is_japan_stock = ticker.endswith(".T")

        if is_us_stock:
            unit_size = 1
        elif is_japan_stock:
            unit_size = self.get_japan_unit_size()
        else:
            unit_size = 1

        min_order = float(self.mini_stock_config.get("min_order_amount", 500.0))
        if self.mini_stock_enabled and target_amount < min_order:
            return 0

        if target_amount < price * unit_size:
            return 0

        shares = int(target_amount / price / unit_size) * unit_size
        return shares

    def execute_orders(self, signals: List[Dict[str, Any]], prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Executes a list of trade signals. Returns a list of executed trades."""
        executed_trades: List[Dict[str, Any]] = []

        if not self.check_risk():
            return executed_trades

        for signal in signals:
            ticker = signal.get("ticker")
            if not ticker or not isinstance(ticker, str):
                continue

            action = signal.get("action")
            confidence = float(signal.get("confidence", 1.0))
            price = prices.get(ticker)
            reason = str(signal.get("reason", "Auto-Trade"))

            if not price:
                logger.info(f"Skipping {ticker}: No price data.")
                continue

            if action == "BUY":
                qty = int(signal.get("quantity", 0))
                if qty == 0:
                    qty = self.calculate_position_size(ticker, price, confidence)

                if qty > 0:
                    if self.real_broker:
                        logger.info(f"🚀 REAL TRADE: BUY {qty} {ticker} @ {price}")
                        try:
                            success = self.real_broker.buy_order(ticker, qty, price, order_type="指値")
                        except Exception as e:
                            logger.error(f"Real broker error: {e}")
                            success = False

                        if success:
                            self.pt.execute_trade(
                                ticker, "BUY", qty, price, reason=f"Real Trade Sync (Conf: {confidence:.2f})"
                            )
                            executed_trades.append(
                                {"ticker": ticker, "action": "BUY", "quantity": qty, "price": price, "reason": reason}
                            )
                    else:
                        success = self.pt.execute_trade(
                            ticker, "BUY", qty, price, reason=f"{reason} (Conf: {confidence:.2f})"
                        )
                        if success:
                            logger.info(f"EXECUTED: BUY {qty} {ticker} @ {price}")
                            executed_trades.append(
                                {"ticker": ticker, "action": "BUY", "quantity": qty, "price": price, "reason": reason}
                            )
                        else:
                            logger.warning(f"FAILED: BUY {ticker} (Insufficient funds?)")

            elif action == "SELL":
                positions = self.pt.get_positions()

                if not positions.empty and "ticker" in positions.columns and ticker in positions["ticker"].values:
                    row = positions[positions["ticker"] == ticker].iloc[0]
                    qty = int(row["quantity"])

                    if self.real_broker:
                        logger.info(f"🚀 REAL TRADE: SELL {qty} {ticker} @ {price}")
                        logger.warning("⚠️ 実取引の売り注文は未実装のためスキップします（安全のため）")
                        success = False
                    else:
                        success = self.pt.execute_trade(ticker, "SELL", qty, price, reason=reason)
                        if success:
                            logger.info(f"EXECUTED: SELL {qty} {ticker} @ {price}")
                            executed_trades.append(
                                {"ticker": ticker, "action": "SELL", "quantity": qty, "price": price, "reason": reason}
                            )

        return executed_trades
