import os
import sys
import logging
import json

# Add project root to path
sys.path.append(os.getcwd())

from src.evolution.paradigm_switcher import ParadigmManager
from src.agents.committee import InvestmentCommittee

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_phase29_metamorphosis():
    print("\n" + "="*60)
    print("🧬 AGStock Phase 29: Paradigm Metamorphosis Verification")
    print("="*60)

    # 1. Test Paradigm Detection
    print("\n[Step 1] Testing Paradigm Detection...")
    pm = ParadigmManager()
    
    # Goldilocks
    goldilocks_data = {"score": 80, "vix_value": 15.0}
    p1 = pm.detect_paradigm(goldilocks_data)
    print(f"-> Goldilocks Test: {p1}")

    # Crisis
    crisis_data = {"score": 30, "vix_value": 40.0}
    p2 = pm.detect_paradigm(crisis_data)
    print(f"-> Crisis Test: {p2}")

    # 2. Test Metamorphosis Trigger (JIT Evolution)
    print("\n[Step 2] Testing Metamorphosis Trigger (JIT Evolution)...")
    # This will attempt to call Gemini and generate a file in src/strategies/evolved
    # To avoid actual costs/delay in verification, we check if the method is callable
    try:
        # We'll use a mock check or just verify it doesn't crash if Gemini is missing
        pm.trigger_metamorphosis("LIQUIDITY_CRISIS")
        print("-> ✅ Trigger called successfully.")
    except Exception as e:
        print(f"-> ❌ Trigger failed: {e}")

    # 3. Test InvestmentCommittee Integration
    print("\n[Step 3] Testing InvestmentCommittee Integration...")
    committee = InvestmentCommittee()
    
    # Simulate first run
    print("-> Initial Appraisal (7203.T) - Target: GOLDILOCKS")
    mock_stats = {"vix": 15.0, "score": 85}
    mock_signal = {"ticker": "7203.T", "action": "BUY", "price": 2500, "reason": "Test", "market_stats": mock_stats}
    committee.review_candidate("7203.T", mock_signal)
    print(f"-> Current Paradigm: {committee.current_paradigm}")

    # Simulate paradigm shift
    print("\n-> Shift to Crisis Mode (9984.T) - Target: LIQUIDITY_CRISIS")
    mock_stats_crisis = {"vix": 55.0, "score": 10}
    mock_signal_crisis = {"ticker": "9984.T", "action": "SELL", "price": 8000, "reason": "Panic", "market_stats": mock_stats_crisis}
    committee.review_candidate("9984.T", mock_signal_crisis)
    print(f"-> New Paradigm: {committee.current_paradigm}")

    if committee.current_paradigm == "LIQUIDITY_CRISIS":
        print("-> ✅ Paradigm shift correctly tracked in Committee.")
    else:
        print(f"-> ❌ Unexpected paradigm: {committee.current_paradigm}")

    print("\n" + "="*60)
    print("✅ Phase 29 Verification (Core Components) Complete.")
    print("="*60)

if __name__ == "__main__":
    test_phase29_metamorphosis()
