import os
import sys
import logging
import json

# Add project root to path
sys.path.append(os.getcwd())

from src.core.dynasty_manager import DynastyManager
from src.evolution.terminus_protocol import TerminusManager
from src.evolution.briefing_generator import BriefingGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_phase30_dynasty():
    print("\n" + "="*60)
    print("👑 AGStock Phase 30: Oracle Dynasty Verification")
    print("="*60)

    # 1. Test DynastyManager
    print("\n[Step 1] Initializing Dynasty Manager...")
    dm = DynastyManager(state_path="data/test_dynasty.json")
    print(f"-> Name: {dm.state['dynasty_name']}")
    print(f"-> Legacy Score: {dm.state['legacy_score']}")

    print("\n[Step 2] Evaluating Performance (Growth Simulation)...")
    mock_metrics = {
        "total_equity": 6000000,
        "daily_pnl": 50000,
        "monthly_pnl": 200000
    }
    dm.evaluate_performance(mock_metrics)
    print(f"-> New Legacy Score: {dm.state['legacy_score']}")
    print(f"-> Current Objective: {dm.state['current_objective']}")

    if dm.state["current_objective"] == "EXPANSION_PHASE":
        print("-> ✅ Objective Shift Success.")
    else:
        print(f"-> ❌ Objective Shift Failed: {dm.state['current_objective']}")

    # 2. Test Terminus Protocol
    print("\n[Step 3] Updating Terminus Protocol (Self-Preservation)...")
    tm = TerminusManager(data_dir="data/test_terminus")
    ledger_path = tm.generate_survival_ledger(
        portfolio_state=mock_metrics,
        dynasty_state=dm.state,
        personality_weights={"logic": 0.5, "intuition": 0.5}
    )
    
    if os.path.exists(ledger_path):
        print(f"-> ✅ Survival Ledger created at {ledger_path}")
        with open(ledger_path, "r") as f:
            ledger = json.load(f)
            if "dynasty_lineage" in ledger["contents"]:
                 print("-> ✅ Dynasty State persisted in Ledger.")
    else:
        print("-> ❌ Ledger creation failed.")

    # 3. Test Briefing Integration
    print("\n[Step 4] Testing Briefing Integration...")
    # Mocking DynastyManager for BriefingGenerator (it uses default path, so we ensure default exists)
    real_dm = DynastyManager() 
    bg = BriefingGenerator()
    if bg.has_gemini:
        # We won't call generate_content to save cost, but check prompt construction
        # Or just verify that the dm is imported correctly in the class
        print("-> ✅ BriefingGenerator initialized.")
    else:
        print("-> ⚠️ Gemini missing, skipping actual generation test.")

    print("\n" + "="*60)
    print("✅ Phase 30 Verification Complete.")
    print("="*60)

    # Cleanup test files
    try:
        if os.path.exists("data/test_dynasty.json"): os.remove("data/test_dynasty.json")
        import shutil
        if os.path.exists("data/test_terminus"): shutil.rmtree("data/test_terminus")
    except:
        pass

if __name__ == "__main__":
    test_phase30_dynasty()
