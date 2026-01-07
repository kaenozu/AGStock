import sys
import os
import logging

# Elogging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Validation")

try:
    print("--- 1. LLMReasoner E ---")
    from src.llm_reasoner import get_llm_reasoner
    reasoner = get_llm_reasoner()
    print(f"Provider: {reasoner.provider}")
    
    # Eock EEE    response = reasoner.ask("EEE)"
    print(f"Response: {response[:50]}...")

    print("\n--- 2. Oracle2026 E ---")
    from src.oracle.oracle_2026 import Oracle2026
    oracle = Oracle2026()
    guidance = oracle.get_risk_guidance()
    print(f"Oracle Message: {guidance.get('oracle_message')}")

    print("\n--- 3. FullyAutomatedTrader E ---")
    from src.trading.fully_automated_trader import FullyAutomatedTrader
    # EE    trader = FullyAutomatedTrader()
    print("Trader initialized successfully.")
    
    print("\n--- 4. EEEEE---")
    from src.data_manager import DataManager
    dm = DataManager()
    removed = dm.sync_storage()
    print(f"Synced storage. Removed entries: {removed}")

    print("\n--- 5. E ---")
    from src.strategies.technical import SMACrossoverStrategy
    import pandas as pd
    strategy = SMACrossoverStrategy()
    # EE    short_df = pd.DataFrame({"Close": [100, 101, 102, 103, 104, 105], "High": [106]*6, "Low": [99]*6, "Volume": [1000]*6})
    result = strategy.analyze(short_df)
    print(f"Guard Result (short but enough for analyze): {result}")

    print("\nEEEE)"

except Exception as e:
    logger.error(f"EEE: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)