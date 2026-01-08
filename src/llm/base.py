"""
LLM基底クラス

すべてのLLMプロバイダーの共通インターフェース。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """LLM基底クラス"""
    
    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        self._is_available: Optional[bool] = None
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """テキストを生成"""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """チャット形式で応答"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """利用可能かチェック"""
        pass
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """センチメント分析（デフォルト実装）"""
        prompt = f"""Analyze the sentiment of the following text and respond with JSON:
        
Text: {text}

Response format:
{{"sentiment": "positive/negative/neutral", "score": 0.0-1.0, "reasoning": "brief explanation"}}
"""
        try:
            response = self.generate(prompt)
            import json
            # JSONを抽出
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            return json.loads(response.strip())
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return {"sentiment": "neutral", "score": 0.5, "reasoning": "Analysis failed"}
    
    def analyze_market(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """市場分析（デフォルト実装）"""
        prompt = f"""You are a financial analyst. Analyze the following market data:

{data}

Provide analysis in JSON format:
{{"outlook": "bullish/bearish/neutral", "confidence": 0.0-1.0, "key_factors": ["factor1", "factor2"], "recommendation": "brief recommendation"}}
"""
        try:
            response = self.generate(prompt)
            import json
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            return json.loads(response.strip())
        except Exception as e:
            logger.warning(f"Market analysis failed: {e}")
            return {"outlook": "neutral", "confidence": 0.5, "key_factors": [], "recommendation": "Analysis unavailable"}
