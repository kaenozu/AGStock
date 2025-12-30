import pytest
import pandas as pd
import numpy as np
import os
from unittest.mock import MagicMock, patch
from src.evolution.strategy_generator import StrategyGenerator
from src.portfolio.correlation_engine import CorrelationEngine
from src.agents.rl_agent_wrapper import RLAgentWrapper
from src.evolution.genetic_optimizer import GeneticOptimizer
from src.agents.base_agent import BaseAgent
from src.schemas import AgentAnalysis, TradingDecision

# ---- Phase 81 Tests ----
def test_strategy_generation():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"}):
        with patch("google.generativeai.GenerativeModel") as mock_model:
            mock_instance = mock_model.return_value
            mock_instance.generate_content.return_value.text = """
            ```python
            class TestStrategy(BaseStrategy):
                pass
            ```
            """
            
            generator = StrategyGenerator()
            # Mock feedback
            generator.feedback_store = MagicMock()
            generator.feedback_store.get_recent_failures.return_value = [{"ticker": "TEST", "decision": "BUY", "rationale": "Test", "outcome": "FAILURE"}]
            
            generator.evolve_strategies()
            
            # Check file creation (mocked but logic runs)
            # We can't check file unless we let it write. 
            # But generate_content is mocked, so response text is controlled.
            # The prompt construction is key.
            mock_instance.generate_content.assert_called_once()
            print("StrategyGenerator: Prompt sent to Gemini.")

# ---- Phase 82 Tests ----
def test_correlation_engine():
    engine = CorrelationEngine()
    
    # Mock data fetch
    with patch("src.portfolio.correlation_engine.fetch_stock_data") as mock_fetch:
        # Create correlated data
        dates = pd.date_range("2023-01-01", periods=100)
        # Base random walk
        np.random.seed(42)
        returns = np.random.normal(0.01, 0.02, 100)
        price_s1 = 100 * np.cumprod(1 + returns)
        
        s1 = pd.Series(price_s1, index=dates, name="Close")
        s2 = pd.Series(price_s1 * 1.05 + 5, index=dates, name="Close") # Perfectly correlated returns (+ offset doesn't change return correlation much if scaling is constant)
        # Actually s2 = s1 * k  => r2 = r1. Perfect correlation.
        
        # Inversely correlated
        returns_inv = -returns
        price_s3 = 100 * np.cumprod(1 + returns_inv)
        s3 = pd.Series(price_s3, index=dates, name="Close")
        
        def side_effect(ticker, period):
            if ticker == "A": return pd.DataFrame({"Close": s1})
            if ticker == "B": return pd.DataFrame({"Close": s2})
            if ticker == "C": return pd.DataFrame({"Close": s3})
            return pd.DataFrame()
            
        mock_fetch.side_effect = side_effect
        
        engine.calculate_correlations(["A", "B", "C"])
        
        print("DEBUG: Matrix columns:", engine.correlation_matrix.columns)
        print("DEBUG: Matrix:\n", engine.correlation_matrix)

        # Check A-B correlation (should be > 0.9)
        risk = engine.check_new_ticker_risk("A", ["B"])
        print(f"DEBUG: Risk A-B: {risk}")
        
        assert risk is not None, "Risk check failed for A-B"
        assert "Correlation" in risk
        print(f"Correlation Check A-B: {risk}")
        
        # Check B-C (should be < -0.9)
        # get recommendations
        recs = engine.analyze_portfolio_risk([{"ticker": "B"}, {"ticker": "C"}])
        assert any(r["type"] == "HEDGE_DETECTED" for r in recs)
        print("CorrelationEngine: High correlation and Hedge detection verified.")

# ---- Phase 83 Tests ----
class MockAgent(BaseAgent):
    def __init__(self, name="TestAgent"):
        self.name = name
    def analyze(self, data):
        return AgentAnalysis(
            agent_name=self.name, 
            role="TestRole",
            decision=TradingDecision.BUY, 
            reasoning="Test", 
            confidence=0.8
        )

def test_rl_agent_wrapper():
    base = MockAgent()
    rl = RLAgentWrapper(base)
    rl.epsilon = 0.0 # Force exploitation
    
    # State LOW_VOL
    data = {"macro_data": {"vix": {"value": 15}}}
    
    # 1. Analyze
    analysis = rl.analyze(data)
    assert analysis.agent_name.startswith("TestAgent")
    
    # 2. Update Reward
    rl.last_action = 0 # Trust
    rl.last_state = "STATE_LOW_VOL"
    rl.update_reward(1.0) # Good outcome
    
    # Check Q-Table update
    q_val = rl.q_table["STATE_LOW_VOL"][0]
    assert q_val > 0.0
    print(f"RL Agent: Q-value updated to {q_val}")

def test_genetic_optimizer():
    fs = MagicMock()
    # Mock leaderboard
    fs.get_agent_leaderboard.return_value = {
        "visual_pred": {"accuracy": 0.3}, # Low -> Mutate
        "tech_pred": {"accuracy": 0.8}    # High -> Stabilize
    }
    
    gen = GeneticOptimizer()
    gen.fs = fs
    
    # Mock Agents
    agent1 = MagicMock()
    agent1.name = "VisualOracle_RL"
    agent1.epsilon = 0.1
    
    agent2 = MagicMock()
    agent2.name = "MarketAnalyst_RL"
    agent2.epsilon = 0.1
    
    gen.evolve_agents([agent1, agent2])
    
    # Agent 1 (Low Acc) -> Epsilon Increase
    assert agent1.epsilon > 0.1
    print(f"Genetic Mutation: {0.1} -> {agent1.epsilon}")
    
    # Agent 2 (High Acc) -> Epsilon Decrease
    assert agent2.epsilon < 0.1
    print(f"Genetic Selection: {0.1} -> {agent2.epsilon}")

if __name__ == "__main__":
    test_strategy_generation()
    test_correlation_engine()
    test_rl_agent_wrapper()
    test_genetic_optimizer()
