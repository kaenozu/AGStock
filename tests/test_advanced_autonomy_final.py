import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.agents.committee import InvestmentCommittee
from src.data.feedback_store import FeedbackStore
from src.data.macro_loader import MacroLoader
from src.data.earnings_history import EarningsHistory

class TestAdvancedAutonomy(unittest.TestCase):

    @patch('src.data.macro_loader.yf.download')
    def test_macro_loader(self, mock_yf):
        # Mock yfinance data
        columns = pd.MultiIndex.from_tuples([
            ('Close', '^VIX'),
            ('Close', '^TNX'),
            ('Close', 'USDJPY=X'),
            ('Close', '^SOX'),
            ('Close', 'CL=F'),
            ('Close', '^N225'),
            ('Close', '^GSPC')
        ])
        mock_df = pd.DataFrame([
            [20.0, 4.0, 150.0, 5000.0, 75.0, 33000.0, 5000.0],
            [22.0, 4.1, 151.0, 5100.0, 76.0, 33100.0, 5050.0]
        ], columns=columns)
        mock_yf.return_value = mock_df

        loader = MacroLoader()
        data = loader.fetch_macro_data()
        
        self.assertIn('vix', data)
        self.assertIn('macro_score', data)
        self.assertGreater(data['macro_score'], 0)
        print(f"Macro Score: {data['macro_score']}")

    def test_feedback_store(self):
        fs = FeedbackStore(":memory:")
        fs.save_decision("7203.T", "BUY", "Strong fundamentals", 2500.0, {"test": "data"})
        
        # Manually update outcome for testing
        fs.update_outcomes("7203.T", 2600.0) # Should not update yet (too early)
        
        # Mock time to 7 days later
        import datetime
        import sqlite3
        
        # Test basic retrieval
        lessons = fs.get_lessons_for_ticker("7203.T")
        self.assertEqual(len(lessons), 0) # No outcomes updated yet

    @patch('src.agents.committee.InvestmentCommittee.hold_meeting')
    @patch('src.data.macro_loader.MacroLoader.fetch_macro_data')
    @patch('src.data.feedback_store.FeedbackStore.get_lessons_for_ticker')
    def test_committee_integration(self, mock_lessons, mock_macro, mock_meeting):
        config = MagicMock()
        committee = InvestmentCommittee(config)
        
        mock_macro.return_value = {"vix": {"value": 15.0}, "macro_score": 85.0}
        mock_lessons.return_value = [{"timestamp": "2025-01-01", "decision": "BUY", "outcome": "SUCCESS", "return_1w": 0.05}]
        mock_meeting.return_value = {"final_decision": "BUY", "rationale": "Test rationale"}
        
        signal_data = {"price": 100.0, "sentiment_score": 0.5, "action": "BUY", "strategy": "Test"}
        decision = committee.review_candidate("7203.T", signal_data)
        
        self.assertEqual(decision.value, "BUY")
        print("Committee review passed with injected lessons and macro.")

if __name__ == '__main__':
    unittest.main()
