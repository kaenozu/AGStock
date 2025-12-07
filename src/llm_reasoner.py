"""
LLM Reasoner - 市場推論エンジン
ニュースと市場データを基に、株価変動の「理由」を推論する
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
import requests

logger = logging.getLogger(__name__)

class LLMReasoner:
    """LLMによる市場分析・推論クラス"""
    
    def __init__(self):
        self.provider = "gemini" # or "ollama"
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # config.jsonからも読み込む
        if not self.api_key:
            try:
                import json
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.api_key = config.get("gemini_api_key")
            except:
                pass

        self.model_name = "gemini-pro"
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_model = "llama3" # or "mistral", "gemma"
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            logger.warning("GEMINI_API_KEY not found. Switching to Ollama (if available).")
            self.provider = "ollama"

    def ask(self, prompt: str) -> str:
        """
        汎用的な質問への回答を生成（テキスト形式）
        """
        if self.provider == "gemini" and self.api_key:
            return self._call_gemini(prompt, json_mode=False)
        else:
            return self._call_ollama(prompt, json_mode=False)

    def analyze_market_impact(self, news_text: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ニュースと市場データからインパクトを分析
        """
        prompt = self._create_prompt(news_text, market_data)
        
        if self.provider == "gemini" and self.api_key:
            return self._call_gemini(prompt, json_mode=True)
        else:
            return self._call_ollama(prompt, json_mode=True)

    def _create_prompt(self, news_text: str, market_data: Dict[str, Any]) -> str:
        """プロンプト生成"""
        return f"""
        あなたはプロの金融アナリストです。以下の市場データとニュースに基づいて、
        市場の状況と今後の予測をJSON形式で出力してください。
        
        ## 市場データ
        {json.dumps(market_data, ensure_ascii=False)}
        
        ## 最新ニュース
        {news_text}
        
        ## 出力フォーマット (JSONのみ)
        {{
            "sentiment": "BULLISH/BEARISH/NEUTRAL",
            "reasoning": "簡潔な分析理由（100文字以内）",
            "key_drivers": ["要因1", "要因2"],
            "impact_level": "HIGH/MEDIUM/LOW"
        }}
        """

    def _call_gemini(self, prompt: str, json_mode: bool = False) -> Any:
        """Gemini API呼び出し"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            if json_mode:
                # JSON部分を抽出
                cleaned_text = self._clean_json_text(text)
                return json.loads(cleaned_text)
            else:
                return text
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            if json_mode:
                return self._get_fallback_response()
            else:
                return f"Error: {e}"

    def _call_ollama(self, prompt: str, json_mode: bool = False) -> Any:
        """Ollama API呼び出し"""
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
            }
            if json_mode:
                payload["format"] = "json"
                
            response = requests.post(self.ollama_url, json=payload, timeout=60) # Timeout extended for reports
            if response.status_code == 200:
                result = response.json()
                text = result['response']
                return json.loads(text) if json_mode else text
            else:
                logger.error(f"Ollama error: {response.status_code}")
                if json_mode:
                    return self._get_fallback_response()
                else:
                    return f"Error: {response.status_code}"
                    
        except Exception as e:
            logger.error(f"Ollama connection error: {e}")
            if json_mode:
                return self._get_fallback_response("Ollama not connected")
            else:
                 return f"Error: {e}"

    def _clean_json_text(self, text: str) -> str:
        """Markdownのコードブロックなどを除去"""
        text = text.replace("```json", "").replace("```", "").strip()
        return text

    def _get_fallback_response(self, reason: str = "Analysis failed") -> Dict[str, Any]:
        """エラー時のフォールバック"""
        return {
            "sentiment": "NEUTRAL",
            "reasoning": f"AI分析を実行できませんでした: {reason}",
            "key_drivers": [],
            "impact_level": "LOW"
        }

# シングルトン
_reasoner = None

def get_llm_reasoner() -> LLMReasoner:
    global _reasoner
    if _reasoner is None:
        _reasoner = LLMReasoner()
    return _reasoner
