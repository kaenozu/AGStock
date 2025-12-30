import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class NewsShockDefense:
    """
    Monitors news headlines for high-impact 'Shock' words.
    Triggers immediate emergency actions.
    """

    CRITICAL_KEYWORDS = {
        "WAR": ["戦争", "開戦", "空爆", "侵攻", "WAR", "INVASION"],
        "ECONOMIC_SHOCK": [
            "暴落",
            "連鎖倒産",
            "デフォルト",
            "CRASH",
            "BANKRUPTCY",
            "DEFAULT",
        ],
        "PANDEMIC": [
            "パンデミック",
            "緊急事態宣言",
            "ロックダウン",
            "PANDEMIC",
            "LOCKDOWN",
        ],
        "POLICY_SHOCK": [
            "想定外の利上げ",
            "緊急利上げ",
            "財務相辞任",
            "UNEXPECTED RATE HIKE",
        ],
    }

    def detect_shock_events(
        self, news_items: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """
        Scans a list of news items for critical keywords.
        Returns the first detected shock event if found.
        """
        for item in news_items:
            title = item.get("title", "").upper()
            summary = item.get("summary", "").upper()
            content = title + " " + summary

            for category, keywords in self.CRITICAL_KEYWORDS.items():
                for kw in keywords:
                    if kw.upper() in content:
                        logger.critical(
                            f"🔥 SHOCK EVENT DETECTED [{category}]: {title}"
                        )
                        return {
                            "category": category,
                            "keyword": kw,
                            "title": title,
                            "timestamp": item.get("published", "Now"),
                        }
        return None

    def judge_shock_with_llm(self, news_items: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        Uses LLM for nuanced 'Shock' detection that keywords might miss.
        """
        import os
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Take the top 5 recent news for bulk analysis
        headlines = [f"- {item.get('title')}" for item in news_items[:5]]
        text = "\n".join(headlines)

        prompt = f"""
        以下の最新ニュースヘッドラインを読み、市場がパニックに陥るような重大な悪材料（ショックイベント）が含まれているか判定してください。

        【ニュース一覧】
        {text}

        【判定基準】
        1. 地政学リスク（戦争、テロ）
        2. 経済ショック（歴史的な暴落、大手銀行破綻）
        3. 政策ショック（想定外の金利引き上げ、大統領解任等）

        もし重大なショックがある場合は以下のJSON形式で返してください。なければ None とだけ返してください。
        {{
            "shock_detected": true,
            "category": "WAR/ECONOMIC/POLICY",
            "reason": "詳細な理由（日本語）",
            "impact_score": 0.0-1.0
        }}
        """

        try:
            response = model.generate_content(prompt)
            if "shock_detected" in response.text:
                import json
                # Extract JSON from response
                start = response.text.find("{")
                end = response.text.rfind("}") + 1
                data = json.loads(response.text[start:end])
                logger.critical(f"🧠 LLM SHOCK JUDGMENT: {data['reason']}")
                return data
        except Exception as e:
            logger.error(f"LLM Shock judgment failed: {e}")

        return None

    def get_emergency_action(self, shock_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines what to do based on the shock event.
        """
        # If it's an LLM detected shock, we use impact_score
        impact = shock_event.get("impact_score", 0.5)
        category = shock_event.get("category", "UNKNOWN")

        if category in ["WAR", "ECONOMIC_SHOCK"] or impact > 0.8:
            return {
                "action": "PARTIAL_LIQUIDATE",
                "percentage": 50 if impact < 0.9 else 80,
                "reason": f"Emergency Liquidation triggered by LLM Vision ({category}): {shock_event.get('reason', 'Critical')[:50]}...",
            }
        else:
            return {
                "action": "TIGHTEN_STOP_LOSS",
                "stop_pct": 2.0,
                "reason": f"Risk Mitigation triggered by {category}",
            }
