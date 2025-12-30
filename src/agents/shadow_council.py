import logging
import os
from typing import Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)


class ShadowCouncil:
    """
    Hive Intelligence: A collection of AI personas that debate
    trading decisions to eliminate bias.
    """

    def __init__(self):
        self.personas = {
            "The Quant": "Focuses strictly on statistical anomalies, RSI, Volatility, and Mean Reversion. Cold and data-driven.",
            "The Contrarian": "Looks for 'crowded trades' and sentiment extremes. Skeptical of the consensus.",
            "The Growth Hunter": "Focuses on momentum, disruption, and long-term TAM. Optimistic about tech and innovation.",
            "The Value Guardian": "Focuses on margin of safety, P/E ratios, and balance sheet health. Extremely risk-averse.",
        }

    def hold_debate(
        self, ticker: str, proposed_action: str, data_context: str
    ) -> Dict[str, Any]:
        """
        Runs a structured debate among the council members.
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"consensus": "ABSTAIN", "reason": "No Council Access"}

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        debate_log = []
        votes = {"APPROVE": 0, "REJECT": 0}

        for name, mission in self.personas.items():
            prompt = f"""
            Act as '{name}'. Your mission: {mission}
            Question: Should we {proposed_action} {ticker}?
            ---
            DATA CONTEXT:
                pass
            {data_context[-1500:]}
            ---
            Provide a 2-sentence reasoning and then output 'VOTE: APPROVE' or 'VOTE: REJECT'.
            """
            try:
                response = model.generate_content(prompt)
                resp_text = response.text
                debate_log.append(f"[{name}]: {resp_text}")

                if "VOTE: APPROVE" in resp_text:
                    votes["APPROVE"] += 1
                else:
                    votes["REJECT"] += 1
            except Exception as e:
                logger.error(f"Council member {name} failed: {e}")

        # Consensus logic
        consensus = "APPROVE" if votes["APPROVE"] > votes["REJECT"] else "REJECT"
        if votes["APPROVE"] == votes["REJECT"]:
            consensus = (
                "HOLD"  # Tie-breaker is safety (Value Guardian usually wins in spirit)
            )

        return {
            "ticker": ticker,
            "consensus": consensus,
            "votes": votes,
            "debate_log": "\n".join(debate_log),
        }
