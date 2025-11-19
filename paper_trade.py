"""
Paper Trading Script - Run this daily to execute virtual trades

This script:
1. Updates current positions with latest prices
2. Checks for exit signals (stop loss, take profit, or strategy exit)
3. Checks for new entry signals from daily_scan
4. Executes trades and updates the database
5. Logs daily equity
"""

import sys
import json
import pandas as pd
from src.paper_trader import PaperTrader
from src.data_loader import fetch_stock_data
from src.strategies import RSIStrategy, CombinedStrategy, MLStrategy
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES

def get_strategy(name):
    """Get strategy instance by name"""
    if "RSI" in name:
        return RSIStrategy(14, 30, 70)
    elif "Combined" in name:
        return CombinedStrategy()
    elif "AI Random Forest" in name:
        return MLStrategy()
    return RSIStrategy()  # Default

def main():
    print("=== Paper Trading Daily Routine ===\n")
    
    # Initialize paper trader
    trader = PaperTrader()
    
    # Step 1: Update current positions
    print("1. Updating position prices...")
    trader.update_positions_prices()
    positions = trader.get_positions()
    
    if not positions.empty:
        print(f"   Current positions: {len(positions)}")
        for _, pos in positions.iterrows():
            pnl_pct = (pos['unrealized_pnl'] / (pos['entry_price'] * pos['quantity'])) * 100
            print(f"   - {TICKER_NAMES.get(pos['ticker'], pos['ticker'])}: {pos['quantity']} shares, P&L: ¥{pos['unrealized_pnl']:,.0f} ({pnl_pct:+.1f}%)")
    else:
        print("   No open positions.")
    
    # Step 2: Check for exit signals
    print("\n2. Checking for exit signals...")
    if not positions.empty:
        tickers = positions['ticker'].tolist()
        data_map = fetch_stock_data(tickers, period="1y")
        
        for _, pos in positions.iterrows():
            ticker = pos['ticker']
            if ticker not in data_map or data_map[ticker].empty:
                continue
            
            df = data_map[ticker]
            current_price = df['Close'].iloc[-1]
            entry_price = pos['entry_price']
            
            # Simple stop loss / take profit
            pnl_pct = (current_price - entry_price) / entry_price
            
            should_exit = False
            reason = ""
            
            if pnl_pct <= -0.05:  # 5% stop loss
                should_exit = True
                reason = "Stop Loss"
            elif pnl_pct >= 0.10:  # 10% take profit
                should_exit = True
                reason = "Take Profit"
            
            if should_exit:
                print(f"   EXIT: {TICKER_NAMES.get(ticker, ticker)} - {reason} (P&L: {pnl_pct*100:+.1f}%)")
                trader.execute_trade(ticker, "SELL", pos['quantity'], current_price, reason)
    
    # Step 3: Check for new entry signals
    print("\n3. Checking for new entry signals...")
    
    # Load best params if available
    try:
        with open("best_params.json", "r") as f:
            best_params = json.load(f)
    except FileNotFoundError:
        best_params = {}
    
    # Scan for signals (simplified version of daily_scan)
    balance = trader.get_current_balance()
    available_cash = balance['cash']
    
    print(f"   Available cash: ¥{available_cash:,.0f}")
    
    if available_cash > 100000:  # Only trade if we have at least 100k
        # Fetch data for top candidates
        tickers = NIKKEI_225_TICKERS[:50]  # Scan top 50 for speed
        data_map = fetch_stock_data(tickers, period="1y")
        
        signals = []
        for ticker in tickers:
            if ticker not in data_map or data_map[ticker].empty:
                continue
            
            df = data_map[ticker]
            
            # Use best strategy if available, otherwise default
            if ticker in best_params and best_params[ticker]:
                best_strat_name = max(best_params[ticker], key=lambda x: best_params[ticker][x]['train_return'])
                strategy = get_strategy(best_strat_name)
            else:
                strategy = RSIStrategy()
            
            sig_series = strategy.generate_signals(df)
            if sig_series.empty:
                continue
            
            last_signal = sig_series.iloc[-1]
            
            if last_signal == 1:  # Buy signal
                signals.append({
                    'ticker': ticker,
                    'price': df['Close'].iloc[-1],
                    'strategy': strategy.name
                })
        
        # Execute top signal if any
        if signals:
            # Sort by some criteria (for now, just take first)
            top_signal = signals[0]
            ticker = top_signal['ticker']
            price = top_signal['price']
            
            # Calculate quantity (use 20% of available cash)
            allocation = available_cash * 0.2
            quantity = int(allocation / price)
            
            if quantity > 0:
                print(f"   BUY: {TICKER_NAMES.get(ticker, ticker)} x {quantity} @ ¥{price:,.0f} ({top_signal['strategy']})")
                trader.execute_trade(ticker, "BUY", quantity, price, top_signal['strategy'])
            else:
                print(f"   Signal found but insufficient funds for {ticker}")
        else:
            print("   No buy signals found.")
    else:
        print("   Insufficient cash for new trades.")
    
    # Step 4: Update daily equity
    print("\n4. Updating daily equity...")
    total_equity = trader.update_daily_equity()
    total_return = ((total_equity - trader.initial_capital) / trader.initial_capital) * 100
    print(f"   Total Equity: ¥{total_equity:,.0f} (Return: {total_return:+.2f}%)")
    
    # Step 5: Display summary
    print("\n=== Summary ===")
    print(f"Cash: ¥{balance['cash']:,.0f}")
    print(f"Positions Value: ¥{total_equity - balance['cash']:,.0f}")
    print(f"Total Equity: ¥{total_equity:,.0f}")
    print(f"Total Return: {total_return:+.2f}%")
    
    trader.close()
    print("\nPaper trading routine completed.")

if __name__ == "__main__":
    main()
