"""
LLMプロバイダー統合モジュール

複数のLLMプロバイダー（Ollama, Gemini, OpenAI等）を統一インターフェースで提供。
"""

import logging
import os
from enum import Enum
from functools import lru_cache
from typing import Dict, List, Optional, Any

from .base import BaseLLM

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLMプロバイダー"""
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENAI = "openai"
    MOCK = "mock"


class OllamaLLM(BaseLLM):
    """Ollama（ローカルLLM）"""
    
    def __init__(self, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        super().__init__(model_name)
        self.base_url = base_url
    
    def is_available(self) -> bool:
        if self._is_available is not None:
            return self._is_available
        
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            self._is_available = response.status_code == 200
        except Exception:
            self._is_available = False
        
        return self._is_available
    
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise RuntimeError("Ollama is not available")
        
        import requests
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                **kwargs
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.is_available():
            raise RuntimeError("Ollama is not available")
        
        import requests
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                **kwargs
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")


class GeminiLLM(BaseLLM):
    """Google Gemini"""
    
    def __init__(self, model_name: str = "gemini-pro", api_key: Optional[str] = None):
        super().__init__(model_name)
        self.api_key = api_key or os.getenv("AGSTOCK_GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._model = None
    
    def _get_model(self):
        if self._model is None and self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
        return self._model
    
    def is_available(self) -> bool:
        if self._is_available is not None:
            return self._is_available
        
        self._is_available = self._get_model() is not None
        return self._is_available
    
    def generate(self, prompt: str, **kwargs) -> str:
        model = self._get_model()
        if model is None:
            raise RuntimeError("Gemini is not available")
        
        response = model.generate_content(prompt)
        return response.text
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Geminiのchat形式に変換
        model = self._get_model()
        if model is None:
            raise RuntimeError("Gemini is not available")
        
        chat = model.start_chat(history=[])
        for msg in messages:
            if msg["role"] == "user":
                response = chat.send_message(msg["content"])
        
        return response.text if response else ""


class OpenAILLM(BaseLLM):
    """OpenAI GPT"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        super().__init__(model_name)
        self.api_key = api_key or os.getenv("AGSTOCK_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self._client = None
    
    def _get_client(self):
        if self._client is None and self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
        return self._client
    
    def is_available(self) -> bool:
        if self._is_available is not None:
            return self._is_available
        
        self._is_available = self._get_client() is not None
        return self._is_available
    
    def generate(self, prompt: str, **kwargs) -> str:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        if client is None:
            raise RuntimeError("OpenAI is not available")
        
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content


class MockLLM(BaseLLM):
    """モックLLM（テスト・フォールバック用）"""
    
    def __init__(self, model_name: str = "mock"):
        super().__init__(model_name)
    
    def is_available(self) -> bool:
        return True
    
    def generate(self, prompt: str, **kwargs) -> str:
        return f"[Mock Response] Received prompt of {len(prompt)} characters"
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return f"[Mock Response] Received {len(messages)} messages"
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        return {"sentiment": "neutral", "score": 0.5, "reasoning": "Mock analysis"}
    
    def analyze_market(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"outlook": "neutral", "confidence": 0.5, "key_factors": ["mock"], "recommendation": "Mock recommendation"}


@lru_cache(maxsize=4)
def get_llm(provider: Optional[str] = None, model_name: Optional[str] = None) -> BaseLLM:
    """
    LLMインスタンスを取得（自動フォールバック付き）
    
    優先順位:
    1. 指定されたプロバイダー
    2. Ollama（ローカル）
    3. Gemini（API）
    4. OpenAI（API）
    5. Mock（フォールバック）
    """
    # 明示的に指定された場合
    if provider:
        provider_enum = LLMProvider(provider.lower())
        if provider_enum == LLMProvider.OLLAMA:
            return OllamaLLM(model_name or "llama2")
        elif provider_enum == LLMProvider.GEMINI:
            return GeminiLLM(model_name or "gemini-pro")
        elif provider_enum == LLMProvider.OPENAI:
            return OpenAILLM(model_name or "gpt-3.5-turbo")
        else:
            return MockLLM()
    
    # 自動選択（利用可能なものを順番に試す）
    providers = [
        OllamaLLM(model_name or "llama2"),
        GeminiLLM(model_name or "gemini-pro"),
        OpenAILLM(model_name or "gpt-3.5-turbo"),
    ]
    
    for llm in providers:
        if llm.is_available():
            logger.info(f"Using LLM provider: {llm.__class__.__name__}")
            return llm
    
    # すべて利用不可の場合はモック
    logger.warning("No LLM provider available, using mock")
    return MockLLM()


def list_available_providers() -> List[str]:
    """利用可能なプロバイダーをリスト"""
    available = []
    
    if OllamaLLM().is_available():
        available.append("ollama")
    if GeminiLLM().is_available():
        available.append("gemini")
    if OpenAILLM().is_available():
        available.append("openai")
    
    available.append("mock")  # 常に利用可能
    return available
