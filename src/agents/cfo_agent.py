"""
CFO Agent
システムの財務状況（PnL, リスク, パフォーマンス）を自然言語で説明する。
資産運用の透明性を高め、戦略的な助言を行う。
"""

import logging
import json
from src.paper_trader import PaperTrader
from src.agents.macro_agent import MacroAgent
from src.llm_reasoner import get_llm_reasoner

logger = logging.getLogger(__name__)


class CFOAgent:
    """
    AGStockファンドの最高財務責任者（CFO）として振る舞う。
    """
    def __init__(self):
        self.pt = PaperTrader()
        self.macro = MacroAgent()
        self.reasoner = get_llm_reasoner()

    def answer_query(self, query: str) -> str:
        """
        現在の資産状況とマクロ環境を踏まえて、ユーザーの質問に答える。
        """
        # コンテキストの収集
        balance = self.pt.get_current_balance()
        positions = self.pt.get_positions()
        macro_sentiment = self.macro.get_macro_sentiment()
        
        context = {
            "portfolio": {
                "total_equity": balance.get("total_equity", 0),
                "cash": balance.get("cash", 0),
                "unrealized_pnl": balance.get("unrealized_pnl", 0),
                "positions": positions.to_dict('records') if not positions.empty else []
            },
            "macro": macro_sentiment
        }

        prompt = f"""
あなたはAGStockのAI CFOです。ファンドオーナーからの質問に日本語で専門的に答えてください。
あなたの口調は、信頼感があり、洞察に満ち、透明性の高いものである必要があります。

【現在の資産状況】
{json.dumps(context, ensure_ascii=False)}

【オーナーの質問】
"{query}"

【タスク】
コンテキストに基づき、簡潔かつ深い戦略的な回答を提供してください。
損失が出ている場合はその理由をマクロ環境や戦略の観点から説明し、現在のリスクについて言及してください。
"""
        try:
            return self.reasoner.ask(prompt)
        except Exception as e:
            logger.error(f"CFO query failed: {e}")
            return "申し訳ありません。財務データの解析中にエラーが発生しました。"