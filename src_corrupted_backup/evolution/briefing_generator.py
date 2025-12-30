import logging
import os
import json
import google.generativeai as genai
from typing import Dict, Any
from src.data.feedback_store import FeedbackStore
from datetime import datetime
logger = logging.getLogger(__name__)
class BriefingGenerator:
#     """
#     Generates a personalized AI Private Banking briefing using Gemini.
#     Synthesizes learning, evolution, and simulation results into a narrative.
#     """
def __init__(self, briefing_path: str = "last_briefing.json"):
        pass
        self.feedback_store = FeedbackStore()
        self.briefing_path = briefing_path
        self._init_gemini()
    def _init_gemini(self):
        pass
#         """
#         Init Gemini.
#                 self.has_gemini = False
#         api_key = os.getenv("GEMINI_API_KEY")
#         if api_key:
#             genai.configure(api_key=api_key)
#             self.model = genai.GenerativeModel("gemini-1.5-flash")
#             self.has_gemini = True
#     """
def generate_briefing(self) -> str:
#         """
#         Gathers system activity data and generates a narrative briefing.
#                 if not self.has_gemini:
#                     return "Gemini API Key が設定されていないため、ブリーフィングを生成できません。"
# # 1. Gather Data
#         leaderboard = self.feedback_store.get_agent_leaderboard()
#         recent_failures = self.feedback_store.get_recent_failures(limit=3)
#             evolved_dir = "src/strategies/evolved"
#         evolved_files = []
#         if os.path.exists(evolved_dir):
#             evolved_files = [f for f in os.listdir(evolved_dir) if f.endswith(".py") and f != "__init__.py"]
#             evolved_files.sort(reverse=True)  # Newest first
# # Phase 30: Dynasty Status
#         dynasty_info = "Status operational."
#         try:
#             from src.core.dynasty_manager import DynastyManager
#                 dm = DynastyManager()
#             dynasty_info = dm.get_briefing_snippet()
#         except Exception:
#             pass
# # 2. Construct Prompt
#         prompt = f"""
You are a prestigious AI Private Banker for the AGStock trading system.
        Summarize the system's latest status and "evolution" for the user in professional yet friendly Japanese.
                Current Stats:
                    - Agent Performance: {leaderboard}
        - Recent Failures analyzed: {len(recent_failures)}
        - Total Evolved Strategies: {len(evolved_files)}
        - Newest Strategy: {evolved_files[0] if evolved_files else 'None'}
        - Dynasty Outlook: {dynasty_info}
                Instructions:
                    1. Start with a polite greeting.
        2. Mention one specific learning (Reflection) if available.
        3. Explain how the system has improved (e.g., "昨夜、失敗パターンを分析し、ボラティリティ耐性を強化した新しい戦略を生成しました").
        4. Mention that the new strategy passed the Digital Twin Stress Test (Digital Twin シミュレーターによるストレステストを合格済み).
        5. Encourage the user for the day's market.
        6. Keep it concise (approx 300-500 Japanese characters).
                    try:
                        response = self.model.generate_content(prompt)
            briefing_text = response.text
# Save for UI
data = {"timestamp": datetime.now().isoformat(), "content": briefing_text}
            with open(self.briefing_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                return briefing_text
        except Exception as e:
            logger.error(f"Failed to generate briefing: {e}")
            return f"ブリーフィングの生成中にエラーが発生しました: {e}"
    def get_last_briefing(self) -> Dict[str, Any]:
        pass
#         """
#         Get Last Briefing.
#             Returns:
    pass
#                 Description of return value
#                 if os.path.exists(self.briefing_path):
    pass
#                     with open(self.briefing_path, "r", encoding="utf-8") as f:
    pass
#                         return json.load(f)
#         return {"timestamp": None, "content": "まだブリーフィングがありません。夜間の更新をお待ちください。"}
# 
# 
