import logging
import google.generativeai as genai
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MorningStrategyMemo:
    """
    Synthesizes Nightwatch data into a concrete plan for the Japanese market.
    """

    def __init__(self, api_key: str = None):
        if api_key:
            genai.configure(api_key=api_key)

    def generate_memo(self, night_data: Dict[str, Any]) -> str:
        """Uses LLM to interpret US data for Japan."""
        if "error" in night_data:
            return "米国市場データの取得に失敗しました。通常通りのリスク管理を継続してください。"

        prompt = f"""
あなたは凄腕の証券アナリストです。昨晩の米国市場の動きを受け、今日の日本市場の戦略メモ（朝刊）を作成してください。

【昨晩の米国市場データ】
{night_data}

【出力要件】
1. 今日の日本市場の概況予測（寄り付きの気配など）を150文字程度で。
2. 注目のセクター（例：米半導体高なら、アドバンテストや東エレク等への言及）を3つ。
3. 投資家へのアドバイス（例：ドル安なら輸出株注意、など）。
4. 全体的な強気度を 0-100 で。

日本語で簡潔に、箇条書きで出力してください。
"""


# try:
#             model = genai.GenerativeModel("gemini-1.5-flash") # Use flash for speed
