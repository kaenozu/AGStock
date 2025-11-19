"""
Performance Dashboard for Paper Trading

Displays comprehensive performance metrics and visualizations
for your paper trading portfolio.

Usage: python view_performance.py
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def calculate_sharpe_ratio(returns, risk_free_rate=0.001):
    """Calculate Sharpe Ratio (annualized)"""
    if len(returns) < 2:
        return 0.0
    excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0.0

def calculate_max_drawdown(equity_curve):
    """Calculate maximum drawdown"""
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max
    return drawdown.min()

def load_paper_trading_data():
    """Load data from paper trading database"""
    db_path = "paper_trading.db"
    
    if not Path(db_path).exists():
        print("❌ No paper trading database found.")
        print("   Run 'python paper_trade.py' first to start paper trading.")
        return None, None, None
    
    conn = sqlite3.connect(db_path)
    
    # Load balance history
    balance_df = pd.read_sql_query('''
        SELECT date, cash, total_equity 
        FROM balance 
        ORDER BY date
    ''', conn)
    balance_df['date'] = pd.to_datetime(balance_df['date'])
    
    # Load current positions
    positions_df = pd.read_sql_query('''
        SELECT ticker, quantity, entry_price, entry_date, current_price, unrealized_pnl
        FROM positions
    ''', conn)
    
    # Load trade history
    trades_df = pd.read_sql_query('''
        SELECT date, ticker, action, quantity, price, reason
        FROM orders
        ORDER BY date DESC
    ''', conn)
    trades_df['date'] = pd.to_datetime(trades_df['date'])
    
    conn.close()
    
    return balance_df, positions_df, trades_df

def display_performance_metrics(balance_df):
    """Display key performance metrics"""
    if balance_df.empty:
        return
    
    initial_capital = balance_df['total_equity'].iloc[0]
    current_equity = balance_df['total_equity'].iloc[-1]
    total_return = (current_equity - initial_capital) / initial_capital
    
    # Calculate daily returns
    balance_df['daily_return'] = balance_df['total_equity'].pct_change()
    
    # Sharpe Ratio
    sharpe = calculate_sharpe_ratio(balance_df['daily_return'].dropna())
    
    # Max Drawdown
    max_dd = calculate_max_drawdown(balance_df['total_equity'])
    
    # Days trading
    days_trading = len(balance_df)
    
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE METRICS")
    print("=" * 60)
    print(f"Initial Capital:    ¥{initial_capital:,.0f}")
    print(f"Current Equity:     ¥{current_equity:,.0f}")
    print(f"Total Return:       {total_return*100:+.2f}%")
    print(f"Max Drawdown:       {max_dd*100:.2f}%")
    print(f"Sharpe Ratio:       {sharpe:.2f}")
    print(f"Days Trading:       {days_trading}")
    print("=" * 60)

def display_current_positions(positions_df):
    """Display current open positions"""
    print("\n" + "=" * 60)
    print("💼 CURRENT POSITIONS")
    print("=" * 60)
    
    if positions_df.empty:
        print("No open positions.")
    else:
        from src.constants import TICKER_NAMES
        
        total_value = 0
        total_pnl = 0
        
        for _, pos in positions_df.iterrows():
            name = TICKER_NAMES.get(pos['ticker'], pos['ticker'])
            value = pos['quantity'] * pos['current_price']
            pnl_pct = (pos['unrealized_pnl'] / (pos['entry_price'] * pos['quantity'])) * 100
            
            print(f"\n{name} ({pos['ticker']})")
            print(f"  Quantity:        {pos['quantity']} shares")
            print(f"  Entry Price:     ¥{pos['entry_price']:,.0f}")
            print(f"  Current Price:   ¥{pos['current_price']:,.0f}")
            print(f"  Position Value:  ¥{value:,.0f}")
            print(f"  Unrealized P&L:  ¥{pos['unrealized_pnl']:,.0f} ({pnl_pct:+.1f}%)")
            
            total_value += value
            total_pnl += pos['unrealized_pnl']
        
        print(f"\nTotal Position Value: ¥{total_value:,.0f}")
        print(f"Total Unrealized P&L: ¥{total_pnl:,.0f}")
    
    print("=" * 60)

def display_recent_trades(trades_df, limit=10):
    """Display recent trade history"""
    print("\n" + "=" * 60)
    print(f"📝 RECENT TRADES (Last {limit})")
    print("=" * 60)
    
    if trades_df.empty:
        print("No trades yet.")
    else:
        from src.constants import TICKER_NAMES
        
        for _, trade in trades_df.head(limit).iterrows():
            name = TICKER_NAMES.get(trade['ticker'], trade['ticker'])
            print(f"\n{trade['date'].strftime('%Y-%m-%d')}: {trade['action']} {name}")
            print(f"  Quantity: {trade['quantity']} @ ¥{trade['price']:,.0f}")
            print(f"  Reason: {trade['reason']}")
    
    print("=" * 60)

def plot_equity_curve(balance_df):
    """Plot equity curve"""
    if balance_df.empty or len(balance_df) < 2:
        return
    
    plt.figure(figsize=(12, 6))
    plt.plot(balance_df['date'], balance_df['total_equity'], linewidth=2, color='#2E86AB')
    plt.axhline(y=balance_df['total_equity'].iloc[0], color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
    plt.fill_between(balance_df['date'], balance_df['total_equity'], balance_df['total_equity'].iloc[0], 
                     where=(balance_df['total_equity'] >= balance_df['total_equity'].iloc[0]), 
                     alpha=0.3, color='green', label='Profit')
    plt.fill_between(balance_df['date'], balance_df['total_equity'], balance_df['total_equity'].iloc[0], 
                     where=(balance_df['total_equity'] < balance_df['total_equity'].iloc[0]), 
                     alpha=0.3, color='red', label='Loss')
    
    plt.title('Paper Trading Equity Curve', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Equity (¥)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save plot
    plt.savefig('logs/equity_curve.png', dpi=150)
    print("\n📈 Equity curve saved to logs/equity_curve.png")
    
    # Try to show plot
    try:
        plt.show()
    except:
        pass

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("📊 PAPER TRADING PERFORMANCE DASHBOARD")
    print("=" * 60)
    
    # Load data
    balance_df, positions_df, trades_df = load_paper_trading_data()
    
    if balance_df is None:
        return
    
    # Display metrics
    display_performance_metrics(balance_df)
    display_current_positions(positions_df)
    display_recent_trades(trades_df)
    
    # Plot equity curve
    plot_equity_curve(balance_df)
    
    print("\n✅ Dashboard complete!\n")

if __name__ == "__main__":
    main()
