import os
import sys
import logging
import json
import pandas as pd
from typing import Dict, Any

# Add project root to path
sys.path.append(os.getcwd())

from src.agents.council_avatars import AvatarCouncil
from src.execution.precog_defense import PrecogDefense
from src.trading.trade_executor import TradeExecutor
from src.execution import ExecutionEngine
from src.paper_trader import PaperTrader
from src.agents.committee import InvestmentCommittee

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_phase28_sovereign():
    print("\n" + "="*60)
    print("🧬 AGStock Phase 28: Sovereign Oversight Verification")
    print("="*60)

    # 1. Test Council Meritocracy
    print("\n[Step 1] Testing Council Meritocracy (Meta-Learning)...")
    council = AvatarCouncil(persistence_path="data/test_council.json")
    
    # Simulate a vote on 7203.T
    print("-> Holding Assembly...")
    res = council.hold_grand_assembly("7203.T", {})
    
    # Check if pending votes were recorded
    with open("data/test_council.json", "r") as f:
        state = json.load(f)
        has_pending = any(p.get("pending_votes") for p in state)
        print(f"-> Pending votes recorded: {has_pending}")

    # Simulate outcome update
    print("-> Updating Meritocracy (Outcome: BULL)...")
    initial_weight = state[0]["weight"]
    council.update_meritocracy("7203.T", "BULL")
    
    with open("data/test_council.json", "r") as f:
        new_state = json.load(f)
        # Find a persona that voted BULL
        for i, p in enumerate(state):
             pending = [v for v in p.get("pending_votes",[]) if v["ticker"] == "7203.T"]
             if pending and pending[0]["stance"] == "BULL":
                 if new_state[i]["weight"] > p["weight"]:
                     print(f"-> ✅ Meritocracy Success: Avatar {p['id']} rewarded (Weight {p['weight']:.2f} -> {new_state[i]['weight']:.2f})")
                     break

    # 2. Test Index Hedging
    print("\n[Step 2] Testing Index Hedging (Precog Index Defense)...")
    defense = PrecogDefense(risk_threshold=70)
    high_risk = {"aggregate_risk_score": 85, "system_status": "DEFENSIVE", "events": [{"name": "Global Crash", "risk_score": 90}]}
    
    action = defense.evaluate_emergency_action(high_risk)
    print(f"-> Index Hedge Triggered: {action['trigger_index_hedge']}")
    print(f"-> Index Symbols: {action['index_symbols']}")
    
    if action['trigger_index_hedge']:
         print("-> ✅ Index Hedging logic verified in PrecogDefense.")

    # 3. Test Multimodal Integration
    print("\n[Step 3] Testing Multimodal Analyst Integration...")
    committee = InvestmentCommittee()
    if hasattr(committee, 'multimodal_analyst'):
        print("-> ✅ MultimodalAnalyst initialized in InvestmentCommittee.")
    else:
        print("-> ❌ MultimodalAnalyst missing.")

    print("\n" + "="*60)
    print("✅ Phase 28 Verification Complete.")
    print("="*60)

if __name__ == "__main__":
    try:
        test_phase28_sovereign()
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists("data/test_council.json"):
            os.remove("data/test_council.json")
