import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from src.paper_trader import PaperTrader

class ExecutionEngine:
    def __init__(self, paper_trader: PaperTrader):
        self.pt = paper_trader
        self.max_position_size_pct = 0.20 # Max 20% of equity per stock
        self.max_drawdown_limit = 0.15 # Stop trading if DD > 15%

    def check_risk(self) -> bool:
        """
        Checks global risk parameters. Returns True if safe to trade.
        """
        balance = self.pt.get_current_balance()
        initial = self.pt.initial_capital
        current_equity = balance['total_equity']
        
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
        
        if target_amount < price * 100: # Minimum unit
            return 0
            
        # 4. Calculate shares (round down to nearest 100)
        shares = int(target_amount / price / 100) * 100
        
        return shares

    def execute_orders(self, signals: List[Dict], prices: Dict[str, float]):
        """
        Executes a list of trade signals.
        signals: List of dicts {'ticker': str, 'action': 'BUY'/'SELL', 'confidence': float}
        """
        if not self.check_risk():
            return
            
        for signal in signals:
            ticker = signal['ticker']
            action = signal['action']
            confidence = signal.get('confidence', 1.0)
            price = prices.get(ticker)
            
            if not price:
                print(f"Skipping {ticker}: No price data.")
                continue
                
            if action == "BUY":
                qty = self.calculate_position_size(ticker, price, confidence)
                if qty > 0:
                    success = self.pt.execute_trade(ticker, "BUY", qty, price, reason=f"Auto-Trade (Conf: {confidence:.2f})")
                    if success:
                        print(f"EXECUTED: BUY {qty} {ticker} @ {price}")
                    else:
                        print(f"FAILED: BUY {ticker} (Insufficient funds?)")
            
            elif action == "SELL":
                # Sell all held shares
                positions = self.pt.get_positions()
                if ticker in positions.index:
                    qty = positions.loc[ticker, 'quantity']
                    success = self.pt.execute_trade(ticker, "SELL", qty, price, reason="Auto-Trade Exit")
                    if success:
                        print(f"EXECUTED: SELL {qty} {ticker} @ {price}")
