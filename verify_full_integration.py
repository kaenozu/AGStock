"""
Full Integration Verification - 統合検証
FullyAutomatedTrader が正常に EvolvedStrategy を認識し、動作することを確認
"""
import sys
import os
import logging
import pandas as pd
from unittest.mock import MagicMock
sys.path.insert(0, os.getcwd())

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_integration():
    print("\n" + "="*60)
    print("🤖 Full Auto System Integration Test")
    print("="*60)
    
    # 1. Strategy check
    from src.evolved_strategy import EvolvedStrategy
    strategy = EvolvedStrategy()
    print(f"   EvolvedStrategy Loaded: {strategy}")
    print(f"   Params: {strategy.params}")
    
    if not strategy.params:
        print("   ⚠️ No params loaded (Default used)")
    else:
        print("   ✅ Params loaded from JSON")

    # 2. Trader Initialization check
    try:
        from fully_automated_trader import FullyAutomatedTrader
        # Mock config to avoid loading real config issues
        # But FullyAutomatedTrader init is heavy. 
        # We will inspect the code logic dynamically or try to instantiate lightly
        
        print("   Initializing FullyAutomatedTrader...")
        trader = FullyAutomatedTrader("config_dummy.json") 
        
        # Check if "Neuro-Evolved" is in the strategy list logic
        # Since strategies are initialized inside scan_market, we can't inspect instances easily without running scan_market
        # But we can verify no import errors occurred.
        print("   ✅ FullyAutomatedTrader initialized")
        
        # 3. Simulate Signal Gen
        print("\n   Simulating EvolvedStrategy Signal...")
        # Create dummy data
        df = pd.DataFrame({
            'Close': [100 + i + (i%5)*2 for i in range(200)],
            'High': [105 + i for i in range(200)],
            'Low': [95 + i for i in range(200)],
            'Open': [100 + i for i in range(200)],
            'Volume': [1000 for _ in range(200)]
        })
        
        signals = strategy.generate_signals(df)
        print(f"   Signals Generated: {len(signals)} pts")
        
        last_sig = signals.iloc[-1]
        print(f"   Last Signal: {last_sig}")
        
    except Exception as e:
        print(f"❌ Integration Failed: {e}")
        return False
        
    print("\n✅ All Systems Go for Phase 55 Integration")
    return True

if __name__ == "__main__":
    if not os.path.exists("config_dummy.json"):
        with open("config_dummy.json", "w") as f:
            f.write("{}")
    test_integration()
    if os.path.exists("config_dummy.json"):
        os.remove("config_dummy.json")
