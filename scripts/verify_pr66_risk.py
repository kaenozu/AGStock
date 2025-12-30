import sys
import os
import logging
import pandas as pd
# Add project root to path
sys.path.append(os.getcwd())

from src.advanced_risk import AdvancedRiskManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyRisk")

def test_risk_init():
    print("Testing AdvancedRiskManager Initialization...")
    risk = AdvancedRiskManager()
    print("✅ Initialization successful")
    return risk

def test_risk_check(risk):
    print("Testing Market Crash Check...")
    # Mocking logger
    allow, reason = risk.check_market_crash(logger)
    print(f"Result: allow={allow}, reason={reason}")
    print("✅ Market Crash Check executed (result depends on market data)")

if __name__ == "__main__":
    try:
        risk = test_risk_init()
        test_risk_check(risk)
        print("\n✅ All PR #66 Risk Checks Passed!")
    except Exception as e:
        print(f"\n❌ Risk Check Failed: {e}")
        import traceback
        traceback.print_exc()
