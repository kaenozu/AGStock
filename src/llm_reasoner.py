"""
LLM Reasoner - 市場推論エンジン
ニュースと市場データを基に、株価変動の「理由」を推論する。
外部API（OpenAI）またはローカルAI（Ollama）をサポート。
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

import requests

logger = logging.getLogger(__name__)


class LLMReasoner:
    """LLMによる市場分析・推論クラス"""

    def __init__(self):
        self.provider = "ollama"  # デフォルトはローカル
        self.openai_api_key = None
        self.openai_client = None

        # 設定
        self.openai_model_name = "gpt-4o-mini"
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_model = "llama3"

        self._load_config()
        self._initialize_provider()

    def _load_config(self):
        """設定ファイルからAPIキーを読み込む"""
        try:
            config_path = "config.json"
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                    self.openai_api_key = os.getenv("OPENAI_API_KEY") or config.get("openai_api_key")
                    # プレースホルダーチェック
                    if self.openai_api_key and "YOUR_" in self.openai_api_key:
                        self.openai_api_key = None
        except Exception as e:
            logger.warning(f"Could not load config.json: {e}")

    def _initialize_provider(self):
        """プロバイダーの初期化"""
        if HAS_OPENAI and self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                self.provider = "openai"
                logger.info("Using OpenAI provider.")
                return
            except Exception as e:
                logger.error(f"Failed to init OpenAI: {e}")

        self.provider = "ollama"
        logger.info("Using Ollama (local) as primary provider.")

    def ask(self, prompt: str, json_mode: bool = False) -> Any:
        """汎用的な問い合わせ"""
        if self.provider == "openai":
            return self._call_openai(prompt, json_mode)
        else:
            return self._call_ollama(prompt, json_mode)

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """構造化データを取得"""
        return self.ask(prompt, json_mode=True)

    def chat_with_context(self, user_message: str, history: List[Dict[str, str]], context_data: str) -> str:
        """会話履歴とコンテキストを考慮したチャット"""
        system_prompt = f"""
あなたは高度な投資AIアシスタント「Ghostwriter」です。
以下のコンテキスト情報を踏まえ、ユーザーの質問に日本語で専門的に回答してください。

### コンテキスト
{context_data}

### 回答ガイドライン
1. データに基づいた客観的な分析を行ってください。
2. 不確実な場合はその旨を伝え、リスクについても言及してください。
3. 投資助言ではないことを明示しつつ、有益な視点を提供してください。
"""
        full_prompt = f"{system_prompt}\n\n"
        for msg in history:
            role = "User" if msg["role"] == "user" else "Ghostwriter"
            full_prompt += f"{role}: {msg['content']}\n"
        
        full_prompt += f"User: {user_message}\nGhostwriter:"
        
        return self.ask(full_prompt)

    def _call_openai(self, prompt: str, json_mode: bool) -> Any:
        try:
            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": self.openai_model_name,
                "messages": messages,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = self.openai_client.chat.completions.create(**kwargs)
            text = response.choices[0].message.content
            return json.loads(text) if json_mode else text
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return self._get_fallback_response(str(e)) if json_mode else f"Error: {e}"

    def _call_ollama(self, prompt: str, json_mode: bool) -> Any:
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
            }
            if json_mode:
                payload["format"] = "json"

            response = requests.post(self.ollama_url, json=payload, timeout=60)
            if response.status_code == 200:
                text = response.json().get("response", "")
                return json.loads(text) if json_mode else text
            return self._get_fallback_response(f"HTTP {response.status_code}") if json_mode else "Ollama Error"
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self._get_fallback_response(str(e)) if json_mode else "Ollama connection failed"

    def _get_fallback_response(self, error_msg: str) -> Dict[str, Any]:
        return {
            "status": "error",
            "message": f"分析に失敗しました: {error_msg}",
            "sentiment": "NEUTRAL",
            "score": 0.5
        }

# Singleton
_reasoner = None

def get_llm_reasoner() -> LLMReasoner:
    global _reasoner
    if _reasoner is None:
        _reasoner = LLMReasoner()
    return _reasoner