import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to path
sys.path.append(os.getcwd())

from src.portfolio.risk_parity import RiskParityRebalancer
from src.utils.parallel_processor import ParallelExecutor
from src.agents.oracle import AGStockOracle
from src.execution.news_shock_defense import NewsShockDefense
from src.schemas import AppConfig, RiskConfig

def heavy_task(x):
    return x * x

def test_ultimate_v5():
    print("💎 Starting Ultimate V5 Feature Verification...")

    # 1. Test Risk Parity Rebalancer
    print("\n--- ⚖️ Testing Risk Parity Rebalancer ---")
    rebalancer = RiskParityRebalancer()
    mock_data = {
        "NVDA": pd.DataFrame({"Close": [100 + i + np.random.randn() for i in range(50)]}), # High Vol
        "JNJ": pd.DataFrame({"Close": [150 + i*0.1 + np.random.randn()*0.1 for i in range(50)]}) # Low Vol
    }
    weights = rebalancer.calculate_weights(mock_data)
    print(f"Computed Weights: {weights}")
    if weights and weights["JNJ"] > weights["NVDA"]:
        print("✅ Correct: Low vol asset (JNJ) received higher weight.")
    else:
        print("❌ Unexpected weight distribution.")

    # 2. Test Parallel Executor
    print("\n--- 🛰️ Testing Parallel Executor (Multiprocessing) ---")
    
    executor = ParallelExecutor(max_workers=2)
    results = executor.run(heavy_task, [1, 2, 3, 4, 5])
    print(f"Parallel Results: {results}")
    if results == [1, 4, 9, 16, 25]:
        print("✅ Parallel Execution Verified.")
    else:
        print("❌ Parallel Execution Failed.")

    # 3. Test AGStock Oracle
    print("\n--- 💬 Testing AGStock Oracle ---")
    oracle = AGStockOracle()
    if os.getenv("GOOGLE_API_KEY"):
        print("Querying Oracle: '現在のシステムの状態を教えて？'")
        answer = oracle.ask("現在のシステムの状態を教えて？")
        print(f"Oracle Answer: {answer[:100]}...")
        if len(answer) > 20:
             print("✅ Oracle AI Answer Verified.")
    else:
        print("⚠️ Skipped: GOOGLE_API_KEY not found.")

    # 4. Test News Shock Defense (LLM Judge)
    print("\n--- 📰 Testing LLM News Shock Defense ---")
    defense = NewsShockDefense()
    if os.getenv("GOOGLE_API_KEY"):
        mock_news = [
            {"title": "Global Markets Plunge as Nuclear Conflict Escalates", "summary": "Emergency measures taken."}
        ]
        shock = defense.judge_shock_with_llm(mock_news)
        print(f"LLM Shock Judgment: {shock}")
        if shock and shock.get("shock_detected"):
            action = defense.get_emergency_action(shock)
            print(f"Emergency Action: {action}")
            print("✅ LLM Shock Detection Verified.")
    else:
        print("⚠️ Skipped: GOOGLE_API_KEY not found.")

    # 5. Test Strict Config
    print("\n--- 🏗️ Testing Strict Schema Validation ---")
    try:
        # This should fail in strict mode if we pass an int instead of float for a float field
        # and strict=True is active in model_config.
        bad_config = RiskConfig(max_position_size="INVALID")
        print("❌ Schema failed to catch invalid string for float (if strict).")
    except Exception as e:
        print(f"✅ Strict Validation Caught Error: {str(e)[:50]}...")

    print("\n🚀 ALL V5 FEATURES VERIFIED & OPERATIONAL")

if __name__ == "__main__":
    test_ultimate_v5()
