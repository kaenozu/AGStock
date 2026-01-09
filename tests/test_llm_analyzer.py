import unittest
from unittest.mock import MagicMock, patch

from src.llm_analyzer import LLMAnalyzer


class TestLLMAnalyzer(unittest.TestCase):
    def test_mock_analysis(self):
        # Initialize without API key -> Mock Mode
        analyzer = LLMAnalyzer(api_key=None)

        news_list = [
            {"title": "Company reports record profits and growth", "publisher": "News A"},
            {"title": "Stock falls due to market volatility", "publisher": "News B"},
        ]

        result = analyzer.analyze_news("TEST", news_list)

        self.assertIn("sentiment", result)
        self.assertIn("score", result)
        self.assertIn("reasoning", result)
        self.assertIn("risks", result)

        # Check if keywords influenced score
        # "profit", "growth" -> +0.10
        # "fall", "volatility" (not in list but "fall" is) -> -0.05
        # Base 0.5 -> 0.55
        self.assertAlmostEqual(result["score"], 0.55, delta=0.01)

    @patch("src.llm_analyzer.genai")
    def test_gemini_analysis(self, mock_genai):
        # Mock the API
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            '{"sentiment": "Bullish", "score": 0.9, "reasoning": "Great news", "risks": [], "catalysts": []}'
        )
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        # Initialize with API key
        analyzer = LLMAnalyzer(api_key="dummy_key")
        # Force active for test even if import failed in real env (but we patched it)
        analyzer.is_active = True
        analyzer.model = mock_model

        news_list = [{"title": "Good news", "publisher": "A"}]
        result = analyzer.analyze_news("TEST", news_list)

        self.assertEqual(result["sentiment"], "Bullish")
        self.assertEqual(result["score"], 0.9)

    def test_empty_news(self):
        analyzer = LLMAnalyzer(api_key=None)
        result = analyzer.analyze_news("TEST", [])
        self.assertEqual(result["sentiment"], "Neutral")
        self.assertEqual(result["score"], 0.5)


if __name__ == "__main__":
    unittest.main()
