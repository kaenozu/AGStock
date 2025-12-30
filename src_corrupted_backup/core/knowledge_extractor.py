import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import google.generativeai as genai
logger = logging.getLogger(__name__)
class KnowledgeExtractor:
#     """
#     Analyzes the Eternal Archive to discover universal trading patterns.
#     Uses LLM to synthesize insights from historical decisions.
#     """
def __init__(self, archive_dir: str = "data/eternal_archive"):
        pass
        self.archive_dir = archive_dir
        self.knowledge_base_path = os.path.join(archive_dir, "knowledge", "universal_patterns.json")
        self._init_gemini()
    def _init_gemini(self):
        pass
#         """
#         Init Gemini.
#                 self.has_gemini = False
#         api_key = os.getenv("GEMINI_API_KEY")
#         if api_key:
#             genai.configure(api_key=api_key)
#             self.model = genai.GenerativeModel("gemini-1.5-pro")
#             self.has_gemini = True
#     """
def extract_universal_laws(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
#         """
#         Uses AI to discover patterns across multiple decisions.
#                 if not self.has_gemini or not decisions:
#                     return {"status": "SKIPPED", "reason": "No Gemini or insufficient data"}
# # Prepare summary for LLM
#         summary = self._prepare_decision_summary(decisions)
#             prompt = f"""
You are a master quantitative analyst reviewing the decision history of an AI trading system.
                Analyze the following {len(decisions)} trading decisions and extract:
                    1. Universal patterns that led to high-confidence decisions
        2. Market conditions that consistently correlate with success
        3. Agent combinations that produce the most reliable signals
        4. Warning signs that preceded failed predictions
                Decision Summary:
                    {summary}
                Output your findings in JSON format:
                    {{
            "universal_laws": [
                {{"law": "description", "confidence": 0.0-1.0, "evidence_count": N}}
            ],
            "optimal_conditions": {{"condition": "description"}},
            "risk_signals": ["signal1", "signal2"],
            "meta_insights": "Overall strategic recommendation"
        }}
                    try:
                        response = self.model.generate_content(prompt)
            extracted = self._parse_json_response(response.text)
# Save to knowledge base
self._update_knowledge_base(extracted)
                logger.info(f"🧠 [KNOWLEDGE] Extracted {len(extracted.get('universal_laws', []))} universal laws")
            return extracted
            except Exception as e:
                logger.error(f"Knowledge extraction failed: {e}")
            return {"status": "ERROR", "error": str(e)}
    def get_relevant_insights(self, current_context: Dict[str, Any]) -> List[str]:
        pass
#         """
#         Retrieves relevant historical insights for current market context.
#                 if not os.path.exists(self.knowledge_base_path):
#                     return []
#             try:
#                 with open(self.knowledge_base_path, "r", encoding="utf-8") as f:
#                     knowledge = json.load(f)
#                 insights = []
#             paradigm = current_context.get("paradigm", "UNKNOWN")
# # Find relevant laws
#             for law in knowledge.get("universal_laws", []):
#                 if paradigm.lower() in law.get("law", "").lower():
#                     insights.append(f"📖 {law['law']} (信頼度: {law['confidence']:.0%})")
# # Add risk signals if applicable
#             for signal in knowledge.get("risk_signals", []):
#                 insights.append(f"⚠️ リスクシグナル: {signal}")
#                 return insights[:5]  # Top 5 most relevant
#             except Exception as e:
#                 logger.error(f"Failed to retrieve insights: {e}")
#             return []
#     """
def _prepare_decision_summary(self, decisions: List[Dict[str, Any]]) -> str:
#         """Condenses decisions into a readable summary for LLM."""
summary_lines = []
            for i, dec in enumerate(decisions[:50], 1):  # Limit to 50 for token efficiency
            paradigm = dec.get("context", {}).get("paradigm", "?")
            decision = dec.get("decision", "?")
            confidence = dec.get("confidence", 0.0)
            consensus = dec.get("deliberation", {}).get("consensus_strength", 0.0)
                summary_lines.append(
                f"{i}. {dec.get('ticker')} | {paradigm} | {decision} | "
                f"Conf: {confidence:.2f} | Consensus: {consensus:.2f}"
            )
            return "\n".join(summary_lines)
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
#         """Extracts JSON from LLM response."""
try:
            # Try to find JSON block
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            else:
                json_str = text.strip()
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {}
    def _update_knowledge_base(self, new_knowledge: Dict[str, Any]):
        pass
        existing = {}
        if os.path.exists(self.knowledge_base_path):
            with open(self.knowledge_base_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
# Merge logic (simple append for now)
if "universal_laws" not in existing:
            existing["universal_laws"] = []
            existing["universal_laws"].extend(new_knowledge.get("universal_laws", []))
        existing["last_updated"] = datetime.now().isoformat()
        existing["meta_insights"] = new_knowledge.get("meta_insights", "")
            os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
        with open(self.knowledge_base_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)


# """
