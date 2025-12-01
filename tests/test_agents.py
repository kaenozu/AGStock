import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.agents import (
    TechnicalAnalyst, FundamentalAnalyst, MacroStrategist, 
    RiskManager, PortfolioManager, AgentVote
)

class TestAgents(unittest.TestCase):
    def setUp(self):
        # Create sample stock data
        dates = pd.date_range(end=datetime.now(), periods=100)
        self.stock_df = pd.DataFrame({
            'Close': np.random.rand(100) * 100 + 50,
            'Volume': np.random.rand(100) * 1000
        }, index=dates)
        
        self.news_data = [
            {"title": "Company reports strong profits", "publisher": "News"},
            {"title": "Market volatility rises", "publisher": "News"}
        ]

    def test_technical_analyst(self):
        agent = TechnicalAnalyst()
        data = {"stock_data": self.stock_df}
        vote = agent.vote("TEST", data)
        
        self.assertIsInstance(vote, AgentVote)
        self.assertIn(vote.decision, ["BUY", "SELL", "HOLD"])
        self.assertGreaterEqual(vote.confidence, 0.0)
        self.assertLessEqual(vote.confidence, 1.0)
        self.assertTrue(len(vote.reasoning) > 0)

    def test_fundamental_analyst(self):
        agent = FundamentalAnalyst()
        data = {"news_data": self.news_data}
        vote = agent.vote("TEST", data)
        
        self.assertIsInstance(vote, AgentVote)
        self.assertIn(vote.decision, ["BUY", "SELL", "HOLD"])
        self.assertTrue(len(vote.reasoning) > 0)

    def test_macro_strategist(self):
        agent = MacroStrategist()
        data = {"macro_data": None}  # Will try to fetch or return HOLD
        vote = agent.vote("TEST", data)
        
        self.assertIsInstance(vote, AgentVote)
        self.assertIn(vote.decision, ["BUY", "SELL", "HOLD"])

    def test_risk_manager(self):
        agent = RiskManager()
        data = {"stock_data": self.stock_df}
        vote = agent.vote("TEST", data)
        
        self.assertIsInstance(vote, AgentVote)
        self.assertIn(vote.decision, ["BUY", "SELL", "HOLD"])
        self.assertTrue("Volatility" in vote.reasoning)

    def test_portfolio_manager_buy_consensus(self):
        pm = PortfolioManager()
        
        # All agents say BUY
        votes = [
            AgentVote("Tech", "BUY", 0.8, "Bullish"),
            AgentVote("Fund", "BUY", 0.9, "Good news"),
            AgentVote("Macro", "BUY", 0.7, "Economy strong"),
            AgentVote("Risk", "BUY", 0.6, "Low risk")
        ]
        
        decision = pm.make_decision("TEST", votes)
        self.assertEqual(decision['decision'], "BUY")
        self.assertGreater(decision['score'], 0)

    def test_portfolio_manager_sell_consensus(self):
        pm = PortfolioManager()
        
        # All agents say SELL
        votes = [
            AgentVote("Tech", "SELL", 0.8, "Bearish"),
            AgentVote("Fund", "SELL", 0.9, "Bad news"),
            AgentVote("Macro", "SELL", 0.7, "Recession"),
            AgentVote("Risk", "SELL", 0.9, "High volatility")
        ]
        
        decision = pm.make_decision("TEST", votes)
        self.assertEqual(decision['decision'], "SELL")
        self.assertLess(decision['score'], 0)

    def test_portfolio_manager_risk_veto(self):
        pm = PortfolioManager()
        
        # Most say BUY but Risk Manager says strong SELL
        votes = [
            AgentVote("Tech", "BUY", 0.8, "Bullish"),
            AgentVote("Fund", "BUY", 0.7, "Good"),
            AgentVote("Macro", "HOLD", 0.5, "Neutral"),
            AgentVote("Risk Manager", "SELL", 0.95, "Extreme volatility")
        ]
        
        decision = pm.make_decision("TEST", votes)
        # Should be downgraded to HOLD or SELL due to risk veto
        self.assertNotEqual(decision['decision'], "BUY")

if __name__ == '__main__':
    unittest.main()
