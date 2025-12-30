"""
Check current portfolio status
"""

from src.paper_trader import PaperTrader

def main():
    pt = PaperTrader()
    
    # Get balance
    balance = pt.get_current_balance()
    
    # Get positions
    positions = pt.get_positions()
    
    print("\n" + "="*50)
    print("ポートフォリオ概要")
    print("="*50)
    print(f"総資産:     ¥{balance['total_equity']:,.0f}")
    print(f"現金:       ¥{balance['cash']:,.0f}")
    print(f"投資額:     ¥{balance['invested_amount']:,.0f}")
    print(f"含み損益:   ¥{balance['unrealized_pnl']:,.0f}")
    
    if balance['invested_amount'] > 0:
        pnl_pct = (balance['unrealized_pnl'] / balance['invested_amount']) * 100
        print(f"含み損益率: {pnl_pct:+.2f}%")
    
    print(f"本日損益:   ¥{balance['daily_pnl']:,.0f}")
    
    print("\n" + "="*50)
    print("保有ポジション")
    print("="*50)
    
    if not positions.empty:
        for _, pos in positions.iterrows():
            ticker = pos['ticker']
            qty = int(pos['quantity'])
            entry = pos['entry_price']
            current = pos['current_price']
            pnl = pos['unrealized_pnl']
            pnl_pct = pos['unrealized_pnl_pct']
            
            print(f"\n{ticker}:")
            print(f"  数量:     {qty:,} 株")
            print(f"  取得単価: ¥{entry:,.2f}")
            print(f"  現在価格: ¥{current:,.2f}")
            print(f"  含み損益: ¥{pnl:,.0f} ({pnl_pct:+.2f}%)")
    else:
        print("\nポジションなし")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
