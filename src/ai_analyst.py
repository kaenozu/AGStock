"""
AI Analyst Module
Wraps OpenAI API to provide market analysis and trade reasoning.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIAnalyst:
    def __init__(self, config_path: str = 'config.json'):
        self.config = self._load_config(config_path)
        
        # Try environment variable first, then config file
        self.api_key = os.getenv('OPENAI_API_KEY') or self.config.get('openai', {}).get('api_key', '')
        self.model = os.getenv('OPENAI_MODEL') or self.config.get('openai', {}).get('model', 'gpt-4o')
        
        if self.api_key and self.api_key != "YOUR_OPENAI_API_KEY":
            openai.api_key = self.api_key
            self.client = openai.Client(api_key=self.api_key)
            self.enabled = True
        else:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable or configure in config.json")
            self.client = None
            self.enabled = False

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def generate_response(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """
        Generates a response from OpenAI API.
        """
        if not self.enabled:
            return "AI Analyst is disabled. Please configure OpenAI API key."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            return f"Error generating response: {str(e)}"

    def analyze_market(self, market_data: str) -> str:
        """
        Analyzes provided market data and generates a report.
        """
        system_prompt = """
        You are an expert financial analyst for the AGStock trading system. 
        Your job is to analyze market data and provide a concise, professional daily report.
        Focus on:
        1. Market Trend (Bullish/Bearish/Range)
        2. Key Drivers (if inferable from data)
        3. Risk Assessment
        4. Actionable Insights
        
        Output in Japanese. Use markdown formatting.
        """
        return self.generate_response(system_prompt, market_data)

    def explain_trade(self, trade_details: str) -> str:
        """
        Explains the reasoning behind a specific trade.
        """
        system_prompt = """
        You are a senior trader explaining a trade decision to a junior trader.
        Analyze the provided trade details (technical indicators, regime, etc.) and explain WHY this trade was made.
        Be objective and educational.
        
        Output in Japanese.
        """
        return self.generate_response(system_prompt, trade_details)

if __name__ == "__main__":
    # Test
    analyst = AIAnalyst()
    if analyst.enabled:
        print("AI Analyst initialized successfully.")
    else:
        print("AI Analyst disabled (no API key).")
