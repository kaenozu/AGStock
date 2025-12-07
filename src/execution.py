from typing import Dict, List
from src.paper_trader import PaperTrader


class ExecutionEngine:
    def __init__(self, paper_trader: PaperTrader, real_broker=None):
        self.pt = paper_trader
        self.real_broker = real_broker
        self.max_position_size_pct = 0.20  # Max 20% of equity per stock
        self.max_drawdown_limit = 0.15  # Stop trading if DD > 15%

    def check_risk(self) -> bool:
        """
        Checks global risk parameters. Returns True if safe to trade.
        """
        balance = self.pt.get_current_balance()
        initial = self.pt.initial_capital
        current_equity = balance['total_equity']

        # 実取引の場合は実残高を確認
        if self.real_broker:
            try:
                real_balance = self.real_broker.get_balance()
                if real_balance and 'total_equity' in real_balance:
                    real_equity = real_balance['total_equity']
                    paper_equity = balance['total_equity']

                    # 乖離チェック（5%以上）
                    diff_pct = abs(real_equity - paper_equity) / paper_equity if paper_equity > 0 else 0
                    if diff_pct > 0.05:
                        print(f"⚠️ WARNING: 実残高と仮想残高の乖離が大 ({diff_pct:.1%})")
                        print(f"   Real: ¥{real_equity:,.0f} vs Paper: ¥{paper_equity:,.0f}")
            except Exception as e:
                print(f"⚠️ 実残高確認エラー: {e}")

        drawdown = (initial - current_equity) / initial

        if drawdown > self.max_drawdown_limit:
            print(f"RISK ALERT: Max Drawdown exceeded ({drawdown:.1%}). Trading halted.")
            return False

        return True

    def calculate_position_size(self, ticker: str, price: float, confidence: float = 1.0) -> int:
        """
        Calculates the number of shares to buy based on risk management.
        """
        balance = self.pt.get_current_balance()
        equity = balance['total_equity']
        cash = balance['cash']

        # 1. Base allocation based on equity
        target_amount = equity * self.max_position_size_pct

        # 2. Adjust by confidence (optional, e.g. from LightGBM prob)
        target_amount *= confidence

        # 3. Cap at available cash
        target_amount = min(target_amount, cash)

        # Determine unit size based on ticker (US stocks have no dot, Japan stocks have .T)
        is_us_stock = '.' not in ticker
        unit_size = 1 if is_us_stock else 100

        if target_amount < price * unit_size:  # Minimum unit
            return 0

        # 4. Calculate shares (round down to nearest unit)
        shares = int(target_amount / price / unit_size) * unit_size

        return shares

    def execute_orders(self, signals: List[Dict], prices: Dict[str, float]) -> List[Dict]:
        """
        Executes a list of trade signals.
        Returns a list of executed trades.
        """
        executed_trades = []

        if not self.check_risk():
            return executed_trades

        for signal in signals:
            ticker = signal['ticker']
            action = signal['action']
            confidence = signal.get('confidence', 1.0)
            price = prices.get(ticker)
            reason = signal.get('reason', 'Auto-Trade')

            if not price:
                print(f"Skipping {ticker}: No price data.")
                continue

            if action == "BUY":
                # Use quantity from signal if available, otherwise calculate
                if 'quantity' in signal:
                    qty = signal['quantity']
                else:
                    qty = self.calculate_position_size(ticker, price, confidence)
                if qty > 0:
                    # 実取引
                    if self.real_broker:
                        print(f"🚀 REAL TRADE: BUY {qty} {ticker} @ {price}")
                        success = self.real_broker.buy_order(ticker, qty, price, order_type="指値")
                        if success:
                            # PaperTraderにも記録して同期
                            self.pt.execute_trade(ticker, "BUY", qty, price, reason=f"Real Trade Sync (Conf: {confidence:.2f})")
                            executed_trades.append({
                                'ticker': ticker, 'action': 'BUY', 'quantity': qty, 'price': price, 'reason': reason
                            })
                    else:
                        # ペーパートレード
                        success = self.pt.execute_trade(ticker, "BUY", qty, price, reason=f"{reason} (Conf: {confidence:.2f})")
                        if success:
                            print(f"EXECUTED: BUY {qty} {ticker} @ {price}")
                            executed_trades.append({
                                'ticker': ticker, 'action': 'BUY', 'quantity': qty, 'price': price, 'reason': reason
                            })
                        else:
                            print(f"FAILED: BUY {ticker} (Insufficient funds?)")

            elif action == "SELL":
                # Sell all held shares
                positions = self.pt.get_positions()
                if ticker in positions.index:
                    qty = positions.loc[ticker, 'quantity']

                    # 実取引
                    if self.real_broker:
                        print(f"🚀 REAL TRADE: SELL {qty} {ticker} @ {price}")
                        # sell_orderはまだ実装していないが、buy_orderと同様のインターフェースを想定
                        print("⚠️ 実取引の売り注文は未実装のためスキップします（安全のため）")
                        success = False
                    else:
                        success = self.pt.execute_trade(ticker, "SELL", qty, price, reason=reason)
                        if success:
                            print(f"EXECUTED: SELL {qty} {ticker} @ {price}")
                            executed_trades.append({
                                'ticker': ticker, 'action': 'SELL', 'quantity': qty, 'price': price, 'reason': reason
                            })

        return executed_trades
