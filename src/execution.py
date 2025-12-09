from typing import Dict, List
import json
from src.paper_trader import PaperTrader


class ExecutionEngine:
    def __init__(self, paper_trader: PaperTrader, real_broker=None, config_path: str = "config.json"):
        self.pt = paper_trader
        self.real_broker = real_broker
        self.max_position_size_pct = 0.20  # Max 20% of equity per stock
        self.max_drawdown_limit = 0.15  # Stop trading if DD > 15%
        
        # ミニ株設定を読み込み
        self.config = self._load_config(config_path)
        self.mini_stock_config = self.config.get("mini_stock", {})
        self.mini_stock_enabled = self.mini_stock_config.get("enabled", False)
        
    def _load_config(self, config_path: str) -> dict:
        """設定ファイルを読み込み"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    
    def get_japan_unit_size(self) -> int:
        """日本株の売買単位を取得（ミニ株対応）"""
        if self.mini_stock_enabled:
            return self.mini_stock_config.get("unit_size", 1)
        return 100  # 通常の単元株
    
    def calculate_trading_fee(self, amount: float, is_mini_stock: bool = False, 
                               order_type: str = "寄付") -> float:
        """
        取引手数料を計算
        
        楽天証券かぶミニ（2024年現在）:
        - 売買手数料: 無料
        - スプレッド: リアルタイム取引のみ 0.22%
        - 寄付取引: スプレッドなし（完全無料）
        
        Args:
            amount: 取引金額
            is_mini_stock: ミニ株取引かどうか
            order_type: 注文タイプ（"寄付" or "リアルタイム"）
        """
        if is_mini_stock and self.mini_stock_enabled:
            if order_type == "リアルタイム":
                # リアルタイム取引のみスプレッド0.22%
                spread_rate = self.mini_stock_config.get("spread_rate", 0.0022)
                return amount * spread_rate
            else:
                # 寄付取引は完全無料
                return 0
        else:
            # 単元株: 楽天証券の無料化（2023年10月〜）
            return 0

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
        ミニ株対応: 日本株は設定に基づき1株または100株単位
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

        # Determine unit size based on ticker
        # US stocks (no dot in ticker) = 1 share units
        # Japan stocks (.T suffix) = configurable (1 for mini, 100 for standard)
        is_us_stock = '.' not in ticker
        is_japan_stock = ticker.endswith('.T')
        
        if is_us_stock:
            unit_size = 1
        elif is_japan_stock:
            unit_size = self.get_japan_unit_size()
        else:
            unit_size = 1  # その他 (欧州株など)
        
        # ミニ株の最小注文金額チェック
        min_order = self.mini_stock_config.get("min_order_amount", 500)
        if self.mini_stock_enabled and target_amount < min_order:
            return 0

        if target_amount < price * unit_size:  # Minimum unit
            return 0

        # 4. Calculate shares (round down to nearest unit)
        shares = int(target_amount / price / unit_size) * unit_size
        
        # ミニ株の場合、手数料を考慮した実質投資額をログ
        if self.mini_stock_enabled and is_japan_stock:
            fee = self.calculate_trading_fee(shares * price, is_mini_stock=True)
            print(f"📊 ミニ株計算: {shares}株 x ¥{price:,.0f} = ¥{shares*price:,.0f} (手数料: ¥{fee:,.0f})")

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
