import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from src.trading.fully_automated_trader import FullyAutomatedTrader

def run_oracle_dry_run():
    print("\n" + "="*60)
    print(f"🌌 AGStock Sovereign Dry Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # Configure logging to stdout
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        print("1. Initializing Fully Automated Trader...")
        trader = FullyAutomatedTrader()
        
        # Manually invoke Oracle check (usually happens in loop)
        print("\n2. Invoking Oracle 2026 Risk Guidance...")
        if hasattr(trader, "oracle_2026"):
            guidance = trader.oracle_2026.get_risk_guidance()
            print(f"   🔮 ORACLE MESSAGE: {guidance['oracle_message']}")
            print(f"   🛡️ RISK ADJUSTMENTS: Drawdown x{guidance['max_drawdown_adj']}, VaR Buffer +{guidance['var_buffer']}")
        else:
            print("   ⚠️ Oracle not found on trader instance.")

        print("\n3. Checking System Safety (Real-time macro data)...")
        is_safe, reason = trader.is_safe_to_trade()
        if is_safe:
            print(f"   ✅ SYSTEM STATUS: GREEN (Safe to Trade). Reason: {reason}")
            
            # Run a limited market scan mock
            print("\n4. Simulation: Running Market Scan (Dry Mode)...")
            # We don't want to actually trade, just scan
            # But trader.scan_market() fetches data. Let's try it.
            # It returns signals, doesn't execute them.
            signals = trader.scan_market()
            
            print(f"\n   📊 SCAN RESULT: {len(signals)} signals generated.")
            for sig in signals:
                print(f"      - {sig['action']} {sig['ticker']} @ {sig['price']} ({sig['reason']})")
                
        else:
            print(f"   🛑 SYSTEM STATUS: RED (Trading Halted). Reason: {reason}")
            
        print("\n" + "="*60)
        print("🌌 Dry Run Completed. The Sovereign is watching.")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ FATAL ERROR During Dry Run: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_oracle_dry_run()
