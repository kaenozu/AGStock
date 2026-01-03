import sys
import os
import unittest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from src.oracle.oracle_2026 import Oracle2026
from src.advanced_risk import AdvancedRiskManager
from src.sovereign_retrospective import SovereignRetrospective
from src.rl_environment import TradingEnvironment

class TestDivineIntegration(unittest.TestCase):
    def setUp(self):
        # Setup dummy data for environment
        self.df = pd.DataFrame({
            'Open': np.random.rand(100) * 100,
            'High': np.random.rand(100) * 105,
            'Low': np.random.rand(100) * 95,
            'Close': np.random.rand(100) * 100,
            'Volume': np.random.rand(100) * 1000,
            'RSI': np.random.rand(100) * 100,
            'Volatility': np.random.rand(100) * 10
        })

    def test_full_chain(self):
        print("\n--- Testing Sovereign Update Chain ---")
        
        # 1. Oracle Guidance -> Risk Manager
        print("1. Oracle Guidance -> Risk Manager")
        oracle = Oracle2026()
        rm = AdvancedRiskManager()
        
        guidance = oracle.get_risk_guidance()
        print(f"   Guidance: {guidance['oracle_message']}")
        
        initial_loss = rm.max_daily_loss_pct
        rm.apply_oracle_guidance(guidance)
        print(f"   Max Loss Adjusted: {initial_loss} -> {rm.max_daily_loss_pct}")
        
        self.assertAlmostEqual(rm.max_daily_loss_pct, initial_loss * guidance['max_drawdown_adj'])
        
        # 2. Retrospective -> Environment
        print("2. Retrospective -> Environment")
        sr = SovereignRetrospective()
        insights = sr.analyze_2025_failures()
        print(f"   2025 Retrospective Insights found: {insights.get('failed_trade_count', 0)} failures")
        
        env = TradingEnvironment(self.df)
        
        # Check if environment reward reflects retrospective bias
        # Force a state where bias would trigger if penalty exists
        state_info = {"pnl_ratio": -0.05}
        bias = sr.get_reward_bias(state_info)
        print(f"   Calculated Reward Bias (5% loss): {bias}")
        
        # Run a small step
        state = env.reset()
        next_state, reward, done, info = env.step(1) # BUY
        print(f"   Step reward after BUY: {reward}")
        
        # 3. UI logic check (mock)
        print("3. UI Logic Consistency")
        self.assertIn('oracle_message', guidance)
        self.assertIn('penalty_multiplier', insights)
        
        print("✅ Sovereign Integration Test successful.")

if __name__ == '__main__':
    unittest.main()
