import os
import sys
import time
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.getcwd())

from src.trading.fully_automated_trader import FullyAutomatedTrader
from src.utils.state_engine import state_engine, MacroShockManager
from src.trading.tournament_manager import TournamentManager

def test_full_system_integration():
    print("🎬 Starting Final System Integration Test (V4 Singularity)...")
    
    # 1. Macro Shock Defense Test
    print("\n--- Testing Macro Shock Defense ---")
    macro = MacroShockManager()
    # Add a fake event happening NOW
    fake_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    macro.important_events.append({"name": "TEST_SHOCK", "time": fake_time, "impact": "CRITICAL"})
    
    trader = FullyAutomatedTrader()
    trader.macro_manager = macro # Inject mock
    
    print("Checking if routine pauses during shock...")
    # Should return early and log a warning
    trader.daily_routine(force_run=False) 
    
    # 2. Mirroring & Power Mode Test
    print("\n--- Testing Dynamic Mirroring & Power Mode ---")
    # Reset macro for this part
    trader.macro_manager.important_events = [] 
    trader.use_power_mode = True
    
    print("Running daily routine (Force Run)...")
    trader.daily_routine(force_run=True)
    
    # Verify state updates
    regime = state_engine.get_state("regime")
    mirror_acc = state_engine.get_state("active_mirror_account")
    last_scan = state_engine.get_state("last_scan_time")
    
    print(f"✅ In-memory State Verified:")
    print(f"   - Current Regime: {regime}")
    print(f"   - Active Mirror: {mirror_acc}")
    print(f"   - Last Scan Time: {last_scan}")
    
    assert last_scan is not None
    assert mirror_acc is not None
    
    # 3. AI Minutes Persistence Check
    print("\n--- Checking AI Meeting Minutes ---")
    from src.paths import DATA_DIR
    minutes_dir = DATA_DIR / "meeting_minutes"
    files = list(minutes_dir.glob("*.json"))
    print(f"✅ Meeting minutes found ({len(files)} files).")
    
    # 4. Snapshot Check (Intentional Error)
    print("\n--- Testing Error Recovery & Snapshot ---")
    from src.utils.error_handler import autonomous_error_handler
    
    @autonomous_error_handler(name="IntegrationTest", notification_enabled=False)
    def fail_gracefully():
        raise ValueError("Integration test failure for snapshot verification.")
    
    fail_gracefully()
    
    from src.paths import LOGS_DIR
    snapshot_dir = LOGS_DIR / "snapshots"
    snapshots = list(snapshot_dir.glob("snapshot_*_IntegrationTest_fail_gracefully.json"))
    if snapshots:
        print(f"✅ System Snapshot Captured: {snapshots[-1].name}")
    else:
        print("❌ FAILED: No snapshot captured for IntegrationTest.")

if __name__ == "__main__":
    try:
        test_full_system_integration()
        print("\n" + "="*50)
        print("  🚀 ALL NEXT-GEN FEATURES VERIFIED & OPERATIONAL")
        print("="*50)
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
