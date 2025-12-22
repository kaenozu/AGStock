import os
import json
import unittest
import sys
from unittest.mock import MagicMock, patch

# Deep mocking for TensorFlow ecosystem
pd_mock = MagicMock()
pd_mock.tseries = MagicMock()
pd_mock.tseries.offsets = MagicMock()
sys.modules["pandas"] = pd_mock
sys.modules["pandas.tseries"] = pd_mock.tseries
sys.modules["pandas.tseries.offsets"] = pd_mock.tseries.offsets

sys.modules["streamlit"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["src.rag.pdf_loader"] = MagicMock()

# TensorFlow mocking
tf_mock = MagicMock()
sys.modules["tensorflow"] = tf_mock
sys.modules["tensorflow.keras"] = tf_mock.keras
sys.modules["tensorflow.keras.layers"] = tf_mock.keras.layers
sys.modules["tensorflow.keras.models"] = tf_mock.keras.models
sys.modules["tensorflow.keras.optimizers"] = tf_mock.keras.optimizers
sys.modules["tensorflow.keras.callbacks"] = tf_mock.keras.callbacks

from src.data.earnings_history import EarningsHistory
from src.analysis.pdf_reader import EarningsAnalyzer

class TestEarningsHunter(unittest.TestCase):
    
    def setUp(self):
        self.test_db = "test_earnings.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
            
    def tearDown(self):
        import gc
        import time
        gc.collect()
        
        # Retry removal a few times
        for _ in range(3):
            try:
                if os.path.exists(self.test_db):
                    os.remove(self.test_db)
                break
            except PermissionError:
                time.sleep(0.1)

    def test_history_persistence(self):
        """Test database save and load."""
        print("Testing DB persistence...")
        history = EarningsHistory(db_path=self.test_db)
        
        sample_data = {
            "company_name": "TestCorp",
            "period": "FY2025 Q1",
            "score": 85,
            "summary": "Great results.",
            "bullish_factors": ["High growth"],
            "key_metrics": {"revenue": "100M"}
        }
        
        saved = history.save_analysis(sample_data)
        self.assertTrue(saved)
        
        items = history.get_history()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["company_name"], "TestCorp")
        self.assertEqual(items[0]["analysis"]["score"], 85)
        print("DB persistence OK.")

    @patch("src.analysis.pdf_reader.get_llm_reasoner")
    def test_analyzer_logic(self, mock_get_llm):
        """Test analyzer prompt construction and parsing."""
        print("Testing Analyzer logic...")
        
        # Mock LLM
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "company_name": "MockCo",
            "score": 50,
            "summary": "Mock summary"
        }
        mock_get_llm.return_value = mock_llm
        
        analyzer = EarningsAnalyzer()
        result = analyzer.analyze_report("Sample PDF text content")
        
        self.assertEqual(result["company_name"], "MockCo")
        self.assertEqual(result["score"], 50)
        
        # Verify prompt contained text
        args, _ = mock_llm.generate_json.call_args
        self.assertIn("Sample PDF text content", args[0])
        print("Analyzer logic OK.")

if __name__ == "__main__":
    unittest.main()
