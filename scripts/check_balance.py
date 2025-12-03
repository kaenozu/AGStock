from src.paper_trader import PaperTrader

pt = PaperTrader()
balance = pt.get_current_balance()
print(f"総資産: ¥{balance['total_equity']:,}")
print(f"現金: ¥{balance['cash']:,}")
pt.close()
