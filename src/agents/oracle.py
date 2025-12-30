import os
import google.generativeai as genai
import json
import logging
from src.paths import DATA_DIR

logger = logging.getLogger(__name__)


class AGStockOracle:
    """
    AI assistant that knows everything about the system's decisions,
    portfolio, and market outlook. Uses meeting minutes and state for RAG.
    """

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")

    def ask(self, query: str) -> str:
        """Answers user query by looking at system context."""
        if not self.api_key:
            return "GOOGLE_API_KEY が設定されていないため、回答できません。"

        # 1. Fetch Context (Recent Minutes, Regime, Trends)
        context = self._get_system_context()

        prompt = f"""
        あなたは「AGStock Oracle」という、高度な自律型投資システムの専属AIアシスタントです。
        以下のシステム内コンテキスト（最新の会議録、市場レジーム、取引履歴の要約）に基づき、
        ユーザーの質問にプロフェッショナルかつ親しみやすく答えてください。

        【システム・コンテキスト】
        {context}

        【ユーザーの質問】
        {query}

        回答は日本語で、専門的な洞察を含めてください。
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Oracle error: {e}")
            return f"Oracle error: {e}"

    def _get_system_context(self) -> str:
        """Collects relevant files and states as context."""
        ctx = []

        # Latest meeting minutes (last 3 tickers)
        minutes_dir = DATA_DIR / "meeting_minutes"
        if minutes_dir.exists():
            files = sorted(list(minutes_dir.glob("*.json")), reverse=True)[:3]
            for f in files:
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        ctx.append(f"Meeting for {f.stem}: {str(data[-1])[:500]}")
                except Exception:
                    continue

        # State
        try:
            from src.utils.state_engine import state_engine
            ctx.append(f"Current System State: {state_engine.state}")
        except Exception:
            ctx.append("System state unavailable.")

        return "\n\n".join(ctx)
