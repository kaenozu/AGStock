import os
import sys
import time
import shutil
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.utils.error_handler import autonomous_error_handler
from src.utils.state_engine import state_engine

@autonomous_error_handler(name="ChaosMonkey", notification_enabled=False)
def trigger_chaos():
    print("🐒 Chaos Monkey: Disrupting system...")
    state_engine.update_state("chaos_active", True)
    
    # Simulate a critical failure
    raise RuntimeError("BOOM! An unexpected system failure occurred during trade execution.")

def verify_chaos():
    print("🔍 Verifying system response to chaos...")
    
    # 1. Run the failing function
    try:
        trigger_chaos()
    except Exception:
        pass # Handle by decorator

    # 2. Check for snapshot
    from src.paths import LOGS_DIR
    snapshot_dir = LOGS_DIR / "snapshots"
    
    snapshots = list(snapshot_dir.glob("snapshot_*.json"))
    print(f"Found {len(snapshots)} snapshots.")
    
    if len(snapshots) > 0:
        latest = max(snapshots, key=os.path.getctime)
        print(f"✅ SYSTEM SNAPSHOT (Time Travel Debug) VERIFIED: {latest.name}")
        
        with open(latest, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)
            assert data["module"] == "ChaosMonkey"
            assert data["function"] == "trigger_chaos"
            print("   - Snapshot content: SUCCESS")
    else:
        print("❌ FAILED: No snapshot created!")
        sys.exit(1)

if __name__ == "__main__":
    verify_chaos()
    print("\n✨ CHAOS MONKEY TEST PASSED ✨")
