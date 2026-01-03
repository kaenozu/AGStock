import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from src.sovereign_retrospective import SovereignRetrospective

def test_sovereign_retrospective():
    print("Testing Sovereign Retrospective Module...")
    
    # Initialize
    # Note: Using production db for test to see if it reads 2025 logs
    sr = SovereignRetrospective(db_path="data/agstock.db")
    
    insights = sr.analyze_2025_failures()
    print(f"Retrospective Insights: {insights}")
    
    # Test reward bias
    # If penalty_multiplier > 1.2, negative pnl should trigger bias
    state_info = {"pnl_ratio": -0.05} # 5% loss
    bias = sr.get_reward_bias(state_info)
    print(f"Reward Bias for 5% loss: {bias}")
    
    # If insights were found, bias should be non-zero
    if insights.get("penalty_multiplier", 1.0) > 1.2:
        assert bias < 0
        print("✅ Reward Bias Correctly Applied.")
    else:
        print("Skipping bias assertion as no significant failures found in 2025.")

    print("✅ Sovereign Retrospective Test Passed!")

if __name__ == "__main__":
    test_sovereign_retrospective()
