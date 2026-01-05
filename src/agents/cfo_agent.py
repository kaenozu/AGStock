import logging
from agstock.src.paper_trader import PaperTrader
from agstock.src.data.feedback_store import FeedbackStore
from agstock.src.agents.macro_agent import MacroAgent

logger = logging.getLogger(__name__)


class CFOAgent:
    pass


#     """
#     Acts as the Chief Financial Officer (CFO) of the AGStock fund.
#     Explains PnL, risks, and performance trends using natural language.
#     """
def __init__(self):
    self.pt = PaperTrader()
    self.fs = FeedbackStore()
    self.macro = MacroAgent()
    self._init_gemini()
    #     def _init_gemini(self):


#         """
#             Init Gemini.
#                     self.has_gemini = False
#         api_key = os.getenv("GEMINI_API_KEY")
#         if api_key:
#     pass
#             genai.configure(api_key=api_key)
#             self.model = genai.GenerativeModel('gemini-1.5-flash')
#             self.has_gemini = True
#     """
def answer_query(self, query: str) -> str:
    pass
    #         """
    #         Gathers system context and answers a user query about the fund.
    #                 if not self.has_gemini:


#                     return "CFO機能を有効にするには Gemini API キーが必要です。"
# # 1. Gather Context
#         balance = self.pt.get_current_balance()
#         positions = self.pt.get_positions()
#         macro_sentiment = self.macro.get_macro_sentiment()
#         leaderboard = self.fs.get_agent_leaderboard()
# # Format context for prompt
#         context = {
#             "portfolio": {
#                 "total_equity": balance.get("total_equity", 0),
#                 "cash": balance.get("cash", 0),
#                 "profit_loss": balance.get("total_pnl", 0),
#                 "positions": positions.to_dict('records') if not positions.empty else []
#             },
#             "macro": macro_sentiment,
#             "ai_intelligence": leaderboard
#         }
# # 2. Prompt
#         prompt = f"""
# You are the AI CFO of AGStock, an autonomous AI trading system.
# You are talking to the owner of the fund in Japanese.
#         Your tone should be professional, insightful, and transparent.
#                 CURRENT FUND CONTEXT:
#                     {context}
#                 USER QUERY:
#                     "{query}"
#                 TASK:
#                     Answer the query based on the context. If the query is about "why we lost money" or "current risks",
#         link it to the macro situation or specific strategy performances.
#         Provide a concise but deep strategic answer.
#                     try:
#                         response = self.model.generate_content(prompt)
#             return response.text
#         except Exception as e:
#             logger.error(f"CFO query failed: {e}")
#             return "申し訳ありません。現在データの解析中にエラーが発生しました。"
