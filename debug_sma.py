import sys
import os
import traceback

sys.path.append(os.path.abspath("."))

try:
    print("Importing...")
    from src.strategies.technical import SMACrossoverStrategy
    print("Imported.")
    
    print("Instantiating...")
    s = SMACrossoverStrategy()
    print(f"Created: {s.name}")
except Exception:
    traceback.print_exc()
