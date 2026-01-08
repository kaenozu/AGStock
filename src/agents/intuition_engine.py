"""
Intuition Engine
市場の微細な変化（ノイズ）から「直感的な」方向性を検知する。
数値化しにくい市場の「空気感」をLLMを通じて解釈する。
"""

import logging
import json
from typing import Dict, Any
from src.llm_reasoner import get_llm_reasoner

logger = logging.getLogger(__name__)


class IntuitionEngine:
    """
    市場の生データからテクニカル指標を超えた「違和感」や「兆候」を読み取る。
    """
    def __init__(self):
        self.reasoner = get_llm_reasoner()

    def get_instinct(self, ticker: str, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        市場コンテキストから直感的なスコアを算出する。
        """
        prompt = f"""
あなたは30年の経験を持つ伝説的なクオンツ・トレーダーです。
以下の {ticker} に関する市場データ（ノイズを含む）を分析し、
テクニカル指標には現れない「市場の焦り」や「蓄積」を感じ取ってください。

【市場データ】
{json.dumps(market_context, ensure_ascii=False)}

【タスク】
直感的な判断を以下のJSON形式で返してください。
{{
    "instinct_score": 0, // 0（パニック売り）〜 100（確信的な買い）
    "instinct_direction": "ACCUMULATE" | "DISTRIBUTE" | "BRACE_FOR_IMPACT" | "CALM",
    "whisper": "市場がささやいている一言（日本語）"
}}
"""
        try:
            return self.reasoner.generate_json(prompt)
        except Exception as e:
            logger.error(f"Intuition engine failed for {ticker}: {e}")
            return {
                "instinct_score": 50, 
                "instinct_direction": "CALM", 
                "whisper": "シグナルが不明瞭です。静観を推奨します。"
            }