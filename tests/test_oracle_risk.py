import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from src.advanced_risk import AdvancedRiskManager
from src.oracle.oracle_2026 import Oracle2026

def test_oracle_risk_integration():
    print("Testing Oracle-Driven Risk Engine Integration...")
    
    # 1. Initialize
    rm = AdvancedRiskManager()
    oracle = Oracle2026()
    
    initial_loss_limit = rm.max_daily_loss_pct
    initial_conf = rm.confidence_level
    
    print(f"Initial State: Max Daily Loss = {initial_loss_limit}%, Confidence = {initial_conf}")
    
    # 2. Get guidance
    guidance = {
        "var_buffer": 0.02,
        "max_drawdown_adj": 0.8,
        "safety_mode": False,
        "oracle_message": "Test Guidance: High Risk detected."
    }
    
    # 3. Apply guidance
    rm.apply_oracle_guidance(guidance)
    
    print(f"Updated State: Max Daily Loss = {rm.max_daily_loss_pct}%, Confidence = {rm.confidence_level}")
    
    # Assertions
    assert rm.max_daily_loss_pct == initial_loss_limit * 0.8
    assert rm.confidence_level == initial_conf - 0.02
    assert rm.oracle_guidance == guidance
    
    print("✅ Integration Test Passed!")

if __name__ == "__main__":
    test_oracle_risk_integration()
