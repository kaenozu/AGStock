from src.paper_trader import PaperTrader
import logging

logging.basicConfig(level=logging.INFO)

print("Initializing PaperTrader to trigger balance recalculation...")
pt = PaperTrader()
balance = pt.get_current_balance()
print(f"Recalculated Balance: {balance}")
print("Done.")
