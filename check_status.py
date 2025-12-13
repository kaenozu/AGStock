import pandas as pd

from src.paper_trader import PaperTrader


def main():
    pt = PaperTrader()
    bal = pt.get_current_balance()
    pos = pt.get_positions()
    hist = pt.get_trade_history()

    print("\n=== Current Status ===")
    print(f"Total Equity: {bal['total_equity']:,.0f} JPY")
    print(f"Cash:         {bal['cash']:,.0f} JPY")
    print(f"PnL:          {bal['total_equity'] - pt.initial_capital:,.0f} JPY")

    print("\n=== Positions ===")
    if not pos.empty:
        # Select relevant columns for cleaner output
        cols = ["ticker", "quantity", "entry_price", "current_price", "unrealized_pnl"]
        # Add current price if available, otherwise fetch or just show what is there
        print(pos[cols] if set(cols).issubset(pos.columns) else pos)
    else:
        print("No open positions.")

    print("\n=== Recent Trades (Last 5) ===")
    if not hist.empty:
        print(hist.tail(5)[["timestamp", "ticker", "action", "quantity", "price", "realized_pnl"]])
    else:
        print("No trade history.")


if __name__ == "__main__":
    main()
