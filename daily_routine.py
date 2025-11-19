"""
Automated Daily Trading Routine

Run this script once per day (e.g., after market close) to:
1. Scan for new trading signals
2. Execute paper trades
3. Generate performance report
4. Save summary to file

Usage: python daily_routine.py
"""

import sys
import os
import json
import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

def log(message, level="INFO"):
    """Log message to console and file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    print(log_message)
    
    with open("logs/daily_routine.log", "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

def run_daily_scan():
    """Run daily signal scanner"""
    log("=" * 60)
    log("STEP 1: Scanning for trading signals...")
    log("=" * 60)
    
    try:
        # Import and run daily_scan logic
        from src.data_loader import fetch_stock_data
        from src.strategies import RSIStrategy, CombinedStrategy, MLStrategy
        from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES
        
        # Load best params
        try:
            with open("best_params.json", "r") as f:
                best_params = json.load(f)
        except FileNotFoundError:
            best_params = {}
            log("No best_params.json found, using default strategies", "WARNING")
        
        # Scan top 50 stocks for speed
        tickers = NIKKEI_225_TICKERS[:50]
        data_map = fetch_stock_data(tickers, period="1y")
        
        signals = []
        for ticker in tickers:
            if ticker not in data_map or data_map[ticker].empty:
                continue
            
            df = data_map[ticker]
            
            # Use best strategy if available
            if ticker in best_params and best_params[ticker]:
                best_strat_name = max(best_params[ticker], key=lambda x: best_params[ticker][x]['train_return'])
                if "RSI" in best_strat_name:
                    strategy = RSIStrategy()
                elif "Combined" in best_strat_name:
                    strategy = CombinedStrategy()
                else:
                    strategy = RSIStrategy()
            else:
                strategy = RSIStrategy()
            
            sig_series = strategy.generate_signals(df)
            if sig_series.empty:
                continue
            
            last_signal = sig_series.iloc[-1]
            
            if last_signal == 1:
                signals.append({
                    'ticker': ticker,
                    'name': TICKER_NAMES.get(ticker, ticker),
                    'action': 'BUY',
                    'price': df['Close'].iloc[-1],
                    'strategy': strategy.name
                })
            elif last_signal == -1:
                signals.append({
                    'ticker': ticker,
                    'name': TICKER_NAMES.get(ticker, ticker),
                    'action': 'SELL (SHORT)',
                    'price': df['Close'].iloc[-1],
                    'strategy': strategy.name
                })
        
        log(f"Found {len(signals)} signals")
        
        if signals:
            for sig in signals[:5]:  # Show top 5
                log(f"  {sig['action']}: {sig['name']} @ ¥{sig['price']:,.0f} ({sig['strategy']})")
        
        return signals
        
    except Exception as e:
        log(f"Error in daily scan: {e}", "ERROR")
        return []

def run_paper_trading():
    """Execute paper trading routine"""
    log("\n" + "=" * 60)
    log("STEP 2: Executing paper trades...")
    log("=" * 60)
    
    try:
        from src.paper_trader import PaperTrader
        
        trader = PaperTrader()
        
        # Update positions
        trader.update_positions_prices()
        positions = trader.get_positions()
        
        log(f"Current positions: {len(positions)}")
        
        # Update equity
        total_equity = trader.update_daily_equity()
        balance = trader.get_current_balance()
        total_return = ((total_equity - trader.initial_capital) / trader.initial_capital) * 100
        
        log(f"Total Equity: ¥{total_equity:,.0f}")
        log(f"Total Return: {total_return:+.2f}%")
        
        trader.close()
        
        return {
            'equity': total_equity,
            'return': total_return,
            'positions': len(positions)
        }
        
    except Exception as e:
        log(f"Error in paper trading: {e}", "ERROR")
        return None

def generate_summary(signals, paper_trading_result):
    """Generate daily summary report"""
    log("\n" + "=" * 60)
    log("DAILY SUMMARY")
    log("=" * 60)
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    summary = {
        'date': today,
        'signals_found': len(signals),
        'paper_trading': paper_trading_result
    }
    
    # Save to file
    summary_file = f"logs/summary_{today}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    log(f"Summary saved to {summary_file}")
    
    # Console summary
    log(f"\nDate: {today}")
    log(f"Signals Found: {len(signals)}")
    
    if paper_trading_result:
        log(f"Paper Trading Equity: ¥{paper_trading_result['equity']:,.0f}")
        log(f"Paper Trading Return: {paper_trading_result['return']:+.2f}%")
        log(f"Open Positions: {paper_trading_result['positions']}")
    
    log("\n" + "=" * 60)
    log("Daily routine completed successfully!")
    log("=" * 60)

def main():
    """Main routine"""
    log("\n" + "=" * 60)
    log("AUTOMATED DAILY TRADING ROUTINE")
    log("=" * 60)
    
    # Step 1: Scan for signals
    signals = run_daily_scan()
    
    # Step 2: Execute paper trades
    paper_result = run_paper_trading()
    
    # Step 3: Generate summary
    generate_summary(signals, paper_result)

if __name__ == "__main__":
    main()
