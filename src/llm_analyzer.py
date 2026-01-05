import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import google.generativeai
try:
    import google.generativeai as genai

    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    genai = None
    logger.warning("google.generativeai not installed. LLM features will use mock data.")


class LLMAnalyzer:
    """
    Analyzes financial data using Large Language Models (Gemini).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = None
        self.is_active = False

        if HAS_GEMINI and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-pro")
                self.is_active = True
                logger.info("LLMAnalyzer initialized with Gemini API.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
        else:
            logger.info("LLMAnalyzer running in MOCK mode (No API Key or Library).")

    def analyze_news(self, ticker: str, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes a list of news items for a specific ticker.
        Returns a structured dictionary with sentiment, reasoning, and risks.
        """
        if not news_list:
            return {
                "sentiment": "Neutral",
                "score": 0.5,
                "reasoning": "No news available for analysis.",
                "risks": [],
                "catalysts": [],
            }

        if self.is_active and self.model:
            return self._analyze_with_gemini(ticker, news_list)
        else:
            return self._analyze_mock(ticker, news_list)

    def generate_text(self, prompt: str) -> str:
        """
        Generates free-form text using the LLM.
        """
        if self.is_active and self.model:
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Gemini text generation failed: {e}")
                return ""
        return ""

    def _analyze_with_gemini(self, ticker: str, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Real analysis using Gemini API.
        """
        # Prepare prompt
        news_text = "\n".join([f"- {item.get('title', '')} ({item.get('publisher', '')})" for item in news_list[:10]])

        prompt = f"""
        You are a senior financial analyst. Analyze the following recent news headlines for {ticker}.

        News:
            pass
        {news_text}

        Provide a structured analysis in JSON format with the following keys:
            pass
        - sentiment: "Bullish", "Bearish", or "Neutral"
        - score: A float between 0.0 (Bearish) and 1.0 (Bullish)
        - reasoning: A concise summary of why (max 3 sentences).
        - risks: A list of potential risks mentioned or implied.
        - catalysts: A list of potential positive catalysts.

        Output ONLY valid JSON.
        """

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            # Clean up potential markdown code blocks
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            elif text.startswith("```"):
                text = text.replace("```", "")

            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return self._analyze_mock(ticker, news_list)

    def _analyze_mock(self, ticker: str, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Mock analysis for demonstration or fallback.
        """
        # Simple keyword based mock
        bullish_keywords = [
            "up",
            "rise",
            "gain",
            "profit",
            "growth",
            "high",
            "buy",
            "outperform",
        ]
        bearish_keywords = [
            "down",
            "fall",
            "loss",
            "drop",
            "low",
            "sell",
            "underperform",
            "risk",
        ]

        score = 0.5
        found_bullish = []
        found_bearish = []

        for item in news_list:
            title = item.get("title", "").lower()
            for kw in bullish_keywords:
                if kw in title:
                    score += 0.05
                    found_bullish.append(kw)
            for kw in bearish_keywords:
                if kw in title:
                    score -= 0.05
                    found_bearish.append(kw)

        score = max(0.0, min(1.0, score))

        if score > 0.6:
            sentiment = "Bullish"
        elif score < 0.4:
            sentiment = "Bearish"
        else:
            sentiment = "Neutral"

        return {
            "sentiment": sentiment,
            "score": score,
            "reasoning": (
                f"Mock Analysis: Detected {len(found_bullish)} positive and "
                f"{len(found_bearish)} negative keywords in {len(news_list)} headlines."
            ),
            "risks": ["Market volatility (Mock)", "Sector rotation (Mock)"],
            "catalysts": ["Earnings surprise (Mock)", "New product launch (Mock)"],
        }
