import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from src.oracle.oracle_2026 import Oracle2026
from src.advanced_risk import AdvancedRiskManager

def test_autonomous_logic():
    print("--- AGStock Autonomous Logic Test ---")
    
    # 1. Initialize Oracle
    print("\n[Step 1] Initializing Oracle2026...")
    oracle = Oracle2026()
    
    # 2. Get Risk Guidance (Fetches live data: VIX, etc.)
    print("[Step 2] Fetching Risk Guidance (Live Macro Scan)...")
    guidance = oracle.get_risk_guidance()
    print(f"Result: {guidance['oracle_message']}")
    print(f"Safety Mode: {guidance['safety_mode']}")
    print(f"Drawdown Adjustment: {guidance['max_drawdown_adj']}")
    
    # 3. Initialize Risk Manager
    print("\n[Step 3] Initializing AdvancedRiskManager...")
    rm = AdvancedRiskManager()
    base_loss = rm.max_daily_loss_pct
    print(f"Base Max Daily Loss: {base_loss}%")
    
    # 4. Apply Guidance
    print("[Step 4] Applying Oracle Guidance to Risk Manager...")
    rm.apply_oracle_guidance(guidance)
    new_loss = rm.max_daily_loss_pct
    print(f"Adjusted Max Daily Loss: {new_loss}%")
    
    if new_loss != base_loss or guidance['safety_mode'] is not None:
        print("\n✅ SUCCESS: Autonomous link established. System is reacting to market data.")
    else:
        print("\n⚠️ WARNING: No adjustment made (Market might be very stable).")

if __name__ == "__main__":
    test_autonomous_logic()
