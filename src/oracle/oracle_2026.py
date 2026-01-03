import logging
import random
import pandas as pd
from typing import Dict, List, Optional
from src.llm_analyzer import LLMAnalyzer
from src.data_loader import fetch_stock_data, get_latest_price

logger = logging.getLogger(__name__)

MACRO_INDICATORS = {
    "VIX": "^VIX",
    "US10Y": "^TNX",
    "JPY": "JPY=X"
}

class Oracle2026:
    """
    The Oracle of 2026: A scenario-based prediction engine.
    Uses LLM to speculate on future market regimes and stress-test portfolios.
    """
    
    def __init__(self):
        self.analyzer = LLMAnalyzer()
        self.scenarios = [
            "The Neo-Inflation Spike",
            "The Quantum Computing Breakthrough",
            "The East-West Decoupling Accelerator",
            "The Green Hydrogen Revolution",
            "The Great Liquidity Drain"
        ]

    def speculate_scenarios(self) -> List[Dict]:
        """Generate 3 plausible scenarios for 2026."""
        # For prototype, we use a mix of hardcoded templates and LLM expansion
        selected = random.sample(self.scenarios, 3)
        results = []
        
        for name in selected:
            prompt = f"Given the scenario name '{name}', describe its impact on the 2026 stock market in 2 sentences. Include potential winners and losers."
            try:
                # Use the new generic text generation method
                explanation = self.analyzer.generate_text(prompt)
                
                if not explanation or len(explanation) < 10:
                    explanation = f"Experimental data suggests {name} will cause significant shifts in tech and energy sectors."
            except Exception:
                explanation = f"The Divine Oracle predicts that {name} will reshape the financial landscape, favoring resilient assets."
            except Exception:
                explanation = f"The Divine Oracle predicts that {name} will reshape the financial landscape, favoring resilient assets."
                
            results.append({
                "name": name,
                "description": explanation,
                "risk_level": random.choice(["Moderate", "High", "Critical"])
            })
        
        return results

    def assess_portfolio_resilience(self, holdings: List[str]) -> Dict:
        """Calculate a hypothetical resilience score for 2026."""
        score = random.randint(75, 95)
        return {
            "resilience_score": score,
            "status": "Transcendent" if score > 90 else "Robust",
            "recommendation": "Maintain diversification and increase exposure to Oracle-identified growth sectors."
        }

    def get_risk_guidance(self) -> Dict:
        """
        Oracleからのリスク調整ガイダンスを生成。
        実際の市場データ（VIX, US10Y等）に基づいてリスクレベルを決定する。
        """
        # 1. Fetch live macro data
        try:
            data = fetch_stock_data(list(MACRO_INDICATORS.values()), period="5d")
            
            vix_price = self._get_price(data, MACRO_INDICATORS["VIX"])
            us10y_yield = self._get_price(data, MACRO_INDICATORS["US10Y"])
            
            # Default values if fetch fails
            if vix_price is None: vix_price = 20.0
            if us10y_yield is None: us10y_yield = 4.0
            
        except Exception as e:
            logger.warning(f"Oracle macro data fetch failed: {e}. Using fallback.")
            vix_price = 20.0
            us10y_yield = 4.0

        # 2. Derive Logic
        # VIX > 25 indicates high fear
        # US10Y > 4.5 indicates yield pressure
        
        risk_score = 0
        reasons = []
        
        if vix_price > 30:
            risk_score += 3
            reasons.append(f"VIX Extreme ({vix_price:.1f})")
        elif vix_price > 20:
            risk_score += 1
            reasons.append(f"VIX Elevated ({vix_price:.1f})")
            
        if us10y_yield > 4.5:
            risk_score += 1
            reasons.append(f"High Yields ({us10y_yield:.2f}%)")
            
        # 3. Formulate Guidance
        if risk_score >= 3:
            # Critical Defense
            return {
                "var_buffer": 0.05, # +5% VaR buffer
                "max_drawdown_adj": 0.5, # Reduce limits by 50%
                "safety_mode": True,
                "oracle_message": f"⚠️ CRITICAL WARNING: Market stress detected ({', '.join(reasons)}). Engaging maximum defense."
            }
        elif risk_score >= 1:
            # Elevated Caution
            return {
                "var_buffer": 0.02,
                "max_drawdown_adj": 0.8,
                "safety_mode": False,
                "oracle_message": f"⚠️ CAUTION: Volatility rising ({', '.join(reasons)}). Tightening risk parameters."
            }
        else:
            # Normal
            return {
                "var_buffer": 0.0,
                "max_drawdown_adj": 1.0,
                "safety_mode": False,
                "oracle_message": f"✅ STABLE: Macro indicators normal (VIX={vix_price:.1f}). Maintain standard protocol."
            }

    def _get_price(self, data_map: Dict, ticker: str) -> Optional[float]:
        df = data_map.get(ticker)
        if df is not None and not df.empty:
            return float(df["Close"].iloc[-1])
        return None
