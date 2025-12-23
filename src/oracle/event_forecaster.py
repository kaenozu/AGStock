import logging
import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
import pandas as pd

logger = logging.getLogger(__name__)

class EventForecaster:
    """
    Oracle Mode: Predicts upcoming market events based on 
    historical patterns and recent news synthesis.
    """

    def __init__(self):
        self.model_name = "gemini-1.5-pro"
        
    def forecast_upcoming_events(self, market_data: pd.DataFrame, news_summary: str) -> Dict[str, Any]:
        """
        Generates a 3-5 day probabilistic forecast.
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"forecast": "No API Key", "probability": 0.0}

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(self.model_name)

        # Truncate data for token limits
        recent_price = market_data.tail(10).to_string()
        
        prompt = f"""
        Analyze the following market data and news context:
        ---
        RECENT PRICE DATA (Tail):
        {recent_price}
        
        NEWS SUMMARY:
        {news_summary}
        ---
        Based on this, act as a 'Market Oracle'. Predict the most likely major event 
        that will occur in the next 3-5 trading days (e.g., 'Tech sector correction due to interest rate fears', 
        'Breakout in energy stocks').
        
        Return JSON format:
        {{
            "event_prediction": "Description",
            "probability_pct": 0-100,
            "impact_level": "High/Medium/Low",
            "recommended_action": "e.g., Increase cash, Buy puts, Accumulate semiconductors"
        }}
        """

        try:
            response = model.generate_content(prompt)
            # Simple cleanup for JSON extraction if needed
            text = response.text.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(text)
        except Exception as e:
            logger.error(f"Oracle forecast failed: {e}")
            return {"event_prediction": "Unclear", "probability_pct": 0, "impact_level": "N/A"}
