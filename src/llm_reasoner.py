"""
LLM Reasoner - 市場推論エンジン
ニュースと市場データを基に、株価変動の「理由」を推論する
Supports: Gemini, OpenAI, Ollama
"""

import json
import logging
import os
from typing import Any, Dict

try:
    import google.generativeai as genai
    import PIL.Image

    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from openai import OpenAI

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

import requests

logger = logging.getLogger(__name__)


class LLMReasoner:
    """LLMによる市場分析・推論クラス (Gemini / OpenAI / Ollama)"""

    def __init__(self):
        self.provider = "ollama"  # Default fallback
        self.gemini_api_key = None
        self.openai_api_key = None
        self.openai_client = None

        # Model Names
        self.gemini_model_name = "gemini-2.0-flash-exp"  # Latest experimental model
        self.openai_model_name = "gpt-4o-mini"
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_model = "llama3"

        # Load from config.json
        self._load_keys_from_config()

        # Initialize with best available provider
        self._initialize_provider()

    def _load_keys_from_config(self):
        """Load API keys from config.json, ignoring placeholders."""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)

                def is_valid(k):
                    return k and k != "YOUR_API_KEY_HERE" and not k.startswith("YOUR_")

                self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")  # From ENV
                if not self.gemini_api_key:
                    k = config.get("gemini_api_key") or config.get("gemini", {}).get("api_key")
                    if is_valid(k):
                        self.gemini_api_key = k

                self.openai_api_key = os.getenv("OPENAI_API_KEY")
                if not self.openai_api_key:
                    k = config.get("openai_api_key") or config.get("ai_committee", {}).get("api_key")
                    if is_valid(k):
                        self.openai_api_key = k

        except Exception as e:
            logger.warning(f"Could not load config.json: {e}")

    def _initialize_provider(self):
        """Set up the best available LLM provider"""
        # Priority: Gemini > OpenAI > Ollama (Flip priority to favor Gemini as requested in Phase 28/29)
        if HAS_GEMINI and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel(self.gemini_model_name)
            self.provider = "gemini"
            logger.info("Using Gemini provider.")
        elif HAS_OPENAI and self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.provider = "openai"
            logger.info("Using OpenAI provider.")
        else:
            self.provider = "ollama"
            logger.warning("No valid API keys found. Falling back to Ollama (local).")

    # --- For backward compatibility ---
    @property
    def api_key(self):
        return self.gemini_api_key or self.openai_api_key

    def set_api_key(self, api_key: str):
        """Set Gemini API key dynamically (legacy method)"""
        self.set_gemini_key(api_key)

    def set_gemini_key(self, api_key: str):
        """Set Gemini API key and switch provider"""
        self.gemini_api_key = api_key
        if HAS_GEMINI and api_key:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel(self.gemini_model_name)
            self.provider = "gemini"
            logger.info("Switched to Gemini provider.")

    def set_openai_key(self, api_key: str):
        """Set OpenAI API key and switch provider"""
        self.openai_api_key = api_key
        if HAS_OPENAI and api_key:
            self.openai_client = OpenAI(api_key=api_key)
            self.provider = "openai"
            logger.info("Switched to OpenAI provider.")

    def ask(self, prompt: str) -> str:
        """汎用的な質問への回答を生成（テキスト形式）"""
        if self.provider == "openai":
            return self._call_openai(prompt, json_mode=False)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, json_mode=False)
        else:
            return self._call_ollama(prompt, json_mode=False)

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """構造化データ取得"""
        if self.provider == "gemini":
            return self._call_gemini(prompt, json_mode=True)
        elif self.provider == "openai":
            return self._call_openai(prompt, json_mode=True)
        else:
            return self._call_ollama(prompt, json_mode=True)

    def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """画像分析 (マルチモーダル)"""
        if self.provider != "gemini":
            logger.warning(f"Vision analysis is only supported for Gemini. Current: {self.provider}")
            return self._get_fallback_response("Vision not supported for this provider")

        try:
            img = PIL.Image.open(image_path)
            response = self.gemini_model.generate_content([prompt, img])
            text = response.text

            cleaned_text = self._clean_json_text(text)
            return json.loads(cleaned_text)
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return self._get_fallback_response(str(e))

    def analyze_market_impact(self, news_text: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """ニュースと市場データからインパクトを分析"""
        prompt = self._create_prompt(news_text, market_data)

        if self.provider == "openai":
            return self._call_openai(prompt, json_mode=True)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, json_mode=True)
        else:
            return self._call_ollama(prompt, json_mode=True)

    def chat_with_context(self, user_message: str, history: list, context_data: str) -> str:
        """コンテキストを考慮してチャット応答を生成"""
        system_prompt = f"""
        あなたはAI投資システムの高度なアシスタント「Ghostwriter」です。
        以下の市場・ポートフォリオ状況（Context）を踏まえて、ユーザーの質問に日本語で答えてください。

## 現在の状況 (Context)
        {context_data}

        回答のガイドライン:
            pass
        1. 専門家として振る舞い、論理的に回答してください。
        2. データに基づかない推測をする場合は、その旨を明示してください。
        3. 投資助言ではないことを含ませつつ、有益な視点を提供してください。
        """

        full_prompt = f"{system_prompt}\n\n## 会話履歴\n"
        for msg in history:
            role = "User" if msg["role"] == "user" else "Ghostwriter"
            full_prompt += f"{role}: {msg['content']}\n"

        full_prompt += f"User: {user_message}\nGhostwriter:"

        return self.ask(full_prompt)

    def analyze_news_sentiment(self, news_list: list) -> Dict[str, Any]:
        """Analyze a list of news items and return sentiment score and reasoning."""
        if not news_list:
            return self._get_fallback_response("No news provided")

        news_text = ""
        for i, item in enumerate(news_list):
            news_text += f"{i + 1}. {item.get('title', '')} ({item.get('published', '')})\n"

        prompt = f"""
        あなたはAIヘッジファンドのチーフアナリストです。
        以下の最新ニュースを分析し、現在の市場センチメントをスコアリングしてください。

## 最新ニュース
        {news_text}

## 分析タスク
        1. ニュース全体のセンチメントを -10 (超弱気) 〜 +10 (超強気) で評価してください。
        2. その理由を簡潔に要約してください。
        3. 特に注目すべきトピックがあれば挙げてください。

## 出力フォーマット (JSONのみ)
        {{
            "sentiment_score": 0,
            "sentiment_label": "BULLISH/BEARISH/NEUTRAL",
            "reasoning": "分析理由（日本語で150文字以内）",
            "key_topics": ["トピック1", "トピック2"],
            "trading_implication": "投資家へのアドバイス（日本語）"
        }}
        """

        if self.provider == "openai":
            return self._call_openai(prompt, json_mode=True)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, json_mode=True)
        else:
            return self._call_ollama(prompt, json_mode=True)

    def analyze_earnings_report(self, pdf_text: str) -> Dict[str, Any]:
        """決算短信などのPDFテキストを分析"""
        # Truncate text if too long (approx 50k chars to be safe for smaller models, though 128k context helps)
        max_chars = 60000
        if len(pdf_text) > max_chars:
            pdf_text = pdf_text[:max_chars] + "...(truncated)..."

        prompt = f"""
        あなたはベテランの証券アナリストです。
        以下の決算資料（テキスト抽出版）を読み込み、投資家向けに要約・評価してください。

## 決算資料テキスト
        {pdf_text}

## 分析フォーマット (JSONのみ)
        {{
            "score": 0,  // 0〜10のスコア (10が最高、5が中立)
            "summary": "全体の要約（日本語で200文字程度）",
            "good_points": ["良い点1", "良い点2", "良い点3"],
            "bad_points": ["懸念点1", "懸念点2", "懸念点3"],
            "outlook": "今後の見通しと投資判断（日本語で）"
        }}
        """

        # User Request: Prioritize Gemini for this specific feature
        if self.gemini_api_key:
            # Lazy initialization if not set
            if not hasattr(self, "gemini_model") or self.gemini_model is None:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(self.gemini_model_name)

            return self._call_gemini(prompt, json_mode=True)
        elif self.provider == "openai":
            return self._call_openai(prompt, json_mode=True)
        else:
            return self._call_ollama(prompt, json_mode=True)

    def generate_strategy_code(self, description: str, class_name: str = "CustomGenStrategy") -> str:
        """ユーザーの説明に基づいて戦略コード(Python)を生成"""
        prompt = f"""
        あなたはPythonのエキスパートであり、定量的トレーディングのスペシャリストです。
        以下の要件に基づいて、`src.strategies.base.Strategy` を継承した独自の戦略クラスを実装してください。

## ユーザーの要件
        "{description}"

## 実装ガイドライン
        1. クラス名は `{class_name}` としてください。
        2. `generate_signals(self, df: pd.DataFrame) -> pd.Series` メソッドを実装してください。
           - `df` には 'Close', 'High', 'Low', 'Volume' カラムが含まれます。
           - 戻り値は 1 (買い), -1 (売り), 0 (様子見) の Series です。
        3. 必要なTA-Libやpandasの計算ロジックを含めてください。
        4. 説明コメントを日本語で記述してください。
        5. 出力はPythonコードのみ（Markdownの ```python 等は不要）にしてください。

## テンプレート
        from src.strategies.base import Strategy
        import pandas as pd
        import talib

        class {class_name}(Strategy):
            def __init__(self):
                super().__init__("{class_name}")

            def generate_signals(self, df: pd.DataFrame) -> pd.Series:
# ここにロジックを実装
                pass
        """

        # User Request: Prioritize Gemini 2.0 for coding tasks
        if self.gemini_api_key:
            if not hasattr(self, "gemini_model") or self.gemini_model is None:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(self.gemini_model_name)

            return self._call_gemini(prompt, json_mode=False)
        elif self.provider == "openai":
            return self._call_openai(prompt, json_mode=False)
        else:
            return self._call_ollama(prompt, json_mode=False)

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

    def _call_openai(self, prompt: str, json_mode: bool = False) -> Any:
        """OpenAI API呼び出し"""
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

            if json_mode:
                return json.loads(text)
            return text

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            if json_mode:
                return self._get_fallback_response(str(e))
            return f"Error: {e}"

    def _call_gemini(self, prompt: str, json_mode: bool = False) -> Any:
        """Gemini API呼び出し"""
        try:
            response = self.gemini_model.generate_content(prompt)
            text = response.text

            if json_mode:
                cleaned_text = self._clean_json_text(text)
                return json.loads(cleaned_text)
            else:
                return text

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            if json_mode:
                return self._get_fallback_response(str(e))
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

            response = requests.post(self.ollama_url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                text = result["response"]
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
            "sentiment_score": 0,
            "sentiment_label": "NEUTRAL",
            "reasoning": f"AI分析を実行できませんでした: {reason}",
            "key_drivers": [],
            "key_topics": [],
            "impact_level": "LOW",
            "trading_implication": "分析を再試行してください。",
        }


# シングルトン
_reasoner = None


def get_llm_reasoner() -> LLMReasoner:
    global _reasoner
    if _reasoner is None:
        _reasoner = LLMReasoner()
    return _reasoner
