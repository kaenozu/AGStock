import logging
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.agents.base_agent import BaseAgent
from src.agents.market_analyst import MarketAnalyst
from src.agents.risk_manager import RiskManager
from src.agents.macro_analyst import MacroStrategist
from src.enhanced_ensemble_predictor import EnhancedEnsemblePredictor
from src.schemas import AgentAnalysis, AppConfig, TradingDecision
from src.data.macro_loader import MacroLoader
from src.agents.strategy_arena import StrategyArena
from src.agents.agent_spawner import AgentSpawner
from src.simulation.digital_twin import DigitalTwin
from src.execution.news_shock_defense import NewsShockDefense
from src.execution.position_sizer import PositionSizer
from src.oracle.event_forecaster import EventForecaster
from src.agents.shadow_council import ShadowCouncil
from src.data.earnings_history import EarningsHistory
from src.data.feedback_store import FeedbackStore

logger = logging.getLogger(__name__)


class InvestmentCommittee:
    """
    Orchestrates the debate between multiple AI agents and forms a consensus decision.
    """

    def __init__(self, config: AppConfig = None):
        self.market_analyst = MarketAnalyst()
        self.risk_manager = RiskManager(config.risk if config else None)
        self.macro_strategist = MacroStrategist()
        self.agents: List[BaseAgent] = [self.market_analyst, self.risk_manager, self.macro_strategist]
        self.last_meeting_result: Dict[str, Any] = None
        # Initialize the advanced predictor
        self.predictor = EnhancedEnsemblePredictor()
        # Initial History Managers
        self.macro_loader = MacroLoader()
        self.arena = StrategyArena()
        self.spawner = AgentSpawner()
        self.twin = DigitalTwin()
        self.defense = NewsShockDefense()
        self.sizer = PositionSizer()
        self.oracle = EventForecaster()
        self.shadow_council = ShadowCouncil()
        self.last_forecast = None
        self.earnings_history = EarningsHistory()
        self.feedback_store = FeedbackStore()

    def review_candidate(self, ticker: str, signal_data: Dict[str, Any]) -> TradingDecision:
        """
        Reviews a specific trade candidate derived from the automated trader.
        """
        logger.info(f"🔍 Committee reviewing candidate: {ticker}")

        # Fetch latest earnings report if not already provided
        earnings_report = signal_data.get("earnings_report")
        if not earnings_report:
            latest = self.earnings_history.get_latest_for_ticker(ticker)
            if latest:
                logger.info(f"Found existing earnings report for {ticker}")
                earnings_report = latest.get("analysis")

        # Construct data payload for agents
        macro_data = self.macro_loader.fetch_macro_data()
        
        sentiment_score = signal_data.get("sentiment_score", 0.0)
        sentiment_label = "POSITIVE" if sentiment_score > 0 else "NEGATIVE" if sentiment_score < 0 else "NEUTRAL"

        synthesized_news = (
            f"Ticker: {ticker}. "
            f"Technical Signal: {signal_data.get('action')} by {signal_data.get('strategy')}. "
            f"Reason: {signal_data.get('reason')}. "
            f"Global Market Sentiment is {sentiment_label}."
        )

        data = {
            "ticker": ticker,
            "news": synthesized_news,
            "earnings_report": earnings_report, # New injection point
            "macro_data": macro_data, # New injection point
            "market_stats": {
                "price": signal_data.get("price"),
                "vix": macro_data.get("vix", {}).get("value", 20.0),
                "daily_change": 0.0,
            },
        }

        # Try to generate a real prediction report if features are available
        pred_report = signal_data.get("prediction_report")
        if not pred_report:
            # If features are passed (ideal case)
            features = signal_data.get("features")
            if features is not None:
                try:
                    # self.predictor.predict_point returns a dict with 'final_prediction', 'confidence_score', etc.
                    raw_pred = self.predictor.predict_point(features)
                    
                    # Convert raw_pred to the format MarketAnalyst expects
                    current_price = signal_data.get("price", 100.0)
                    pred_price = raw_pred.get("final_prediction", current_price)
                    
                    # Determine Ensemble Decision
                    ensemble_decision = "HOLD"
                    if pred_price > current_price * 1.005: # 0.5% threshold
                        ensemble_decision = "UP"
                    elif pred_price < current_price * 0.995:
                        ensemble_decision = "DOWN"
                        
                    pred_report = {
                        "ensemble_decision": ensemble_decision,
                        "confidence": raw_pred.get("confidence_score", 0.0),
                        "components": raw_pred.get("ensemble_signals", {}),
                        "market_regime": raw_pred.get("market_regime", "UNKNOWN")
                    }
                except Exception as e:
                    logger.warning(f"Failed to run predictor in committee: {e}")
        
        # Fallback if still None
        if not pred_report:
             pred_report = {
                "ensemble_decision": "UNKNOWN",
                "confidence": 0.0,
                "components": {},
                "market_regime": "UNKNOWN"
            }

        data["prediction_report"] = pred_report
        data["portfolio"] = {
                "cash": 1000000,
                "total_equity": 1000000,
                "positions": [],
        }

        result = self.hold_meeting(data)
        
        # Save decision for follow-up evaluation
        self.feedback_store.save_decision(
            ticker=ticker,
            decision=result["final_decision"],
            rationale=result["rationale"],
            current_price=signal_data.get("price", 0.0),
            raw_data=data
        )
        
        return TradingDecision(result["final_decision"])

    def hold_meeting(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conducts a 'committee meeting' where every agent analyzes the data.
        Returns a consolidated report and final decision.
        """
        logger.info("🏛️ Opening Investment Committee Meeting")
        ticker = data.get("ticker", "Unknown")

        analyses: List[AgentAnalysis] = []

        # 0. News Shock Defense (High-speed interrupt)
        news = data.get("news", [])
        # 'news' might be a string in this system's context, let's wrap it if needed or check type
        news_list = [{"title": data["news"]}] if isinstance(data.get("news"), str) else news
        shock = self.defense.detect_shock_events(news_list)
        # 0.5. Oracle Forecast (Weekly/Daily prediction)
        if not self.last_forecast:
            self.last_forecast = self.oracle.forecast_upcoming_events(pd.DataFrame(), str(news_list))
        if shock:
            action = self.defense.get_emergency_action(shock)
            data["emergency_action"] = action
            logger.warning(f"EMERGENCY INTERRUPT: {action['action']} due to {shock['category']}")

        # 0. Inject Self-Learning Context (lessons learned)
        lessons = self.feedback_store.get_lessons_for_ticker(ticker)
        recent_failures = self.feedback_store.get_recent_failures()
        
        kb_text = ""
        if lessons:
            kb_text += "\n【過去の銘柄別教訓】\n"
            for l in lessons:
                kb_text += f"- {l['timestamp'][:10]}: {l['decision']} -> {l['outcome']} (収益率: {l['return_1w']*100:.1f}%)\n"
        
        if recent_failures:
            kb_text += "\n【最近の全体的な失敗事例】\n"
            for f in recent_failures:
                kb_text += f"- {f['ticker']} ({f['timestamp'][:10]}): {f['rationale'][:50]}... -> 結果: {f['outcome']}\n"
        
        if kb_text:
            data["lessons_learned"] = kb_text
            logger.info("Injected self-learning context into meeting data.")

        # 1. Gather Opinions (including spawned specialists)
        current_score = data.get("macro_data", {}).get("macro_score", 50)
        spawned_agents = self.spawner.spawn_agents_for_regime(current_score)
        all_agents = self.agents + spawned_agents
        
        for agent in all_agents:
            try:
                logger.info(f"Asking {agent.name} for opinion...")
                analysis = agent.analyze(data)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"Agent {agent.name} failed to report: {e}")

        # 2. Form Consensus (Simple Majority with Risk Veto)
        final_decision, rationale = self._form_consensus(analyses)
        # 2.5. Shadow Council Debate (Final Approval)
        council_result = self.shadow_council.hold_debate(
            ticker=ticker,
            proposed_action=final_decision.value,
            data_context=f"Analyses: {analyses}\nForecast: {self.last_forecast}"
        )
        if council_result['consensus'] == 'REJECT':
            from src.schemas import TradingDecision
            final_decision = TradingDecision.HOLD
            rationale = "Shadow Council rejected: " + council_result['debate_log']

        result = {
            "timestamp": datetime.now().isoformat(),
            "analyses": [a.model_dump() for a in analyses],
            "final_decision": final_decision.value,
            "rationale": rationale,
            "participants": [a.name for a in all_agents],
            "spawned_agents": [a.name for a in spawned_agents]
        }

        # 3. Shadow Simulation (Digital Twin)
        current_price = data.get("market_stats", {}).get("price", 0.0)
        self.twin.record_decision(ticker, final_decision.value, current_price)

        # 4. Position Sizing
        equity = data.get("portfolio", {}).get("total_equity", 1000000)
        win_rate = 0.6 # Placeholder for realized win-rate
        sizing = self.sizer.calculate_size(ticker, equity, win_rate)
        result["sizing_recommendation"] = sizing

        self.last_meeting_result = result
        logger.info(f"🏛️ Meeting Adjourned. Decision: {final_decision.value}")
        return result

    def conduct_debate(
        self, ticker: str, market_data: Dict[str, Any], position: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Simulates a conversational debate among agents for UI display.
        Returns a list of message objects: {"agent": "Name", "message": "Content", "decision": "BUY/SELL"}
        """
        debate_log = []

        # 1. Market Analyst Starts
        ma_analysis = self.market_analyst.analyze({"ticker": ticker, "market_stats": market_data})
        debate_log.append(
            {
                "agent": "MarketAnalyst",
                "avatar": "📈",
                "message": f"Analyzing {ticker}... My Technical/Fundamental models suggest: {ma_analysis.decision.value}.\nReason: {ma_analysis.reasoning}",
                "decision": ma_analysis.decision.value,
            }
        )

        # 2. Risk Manager Responds
        # Risk Manager needs portfolio context usually, we provide what we have
        risk_data = {
            "ticker": ticker,
            "portfolio": {"positions": [position] if position else []},
            "market_stats": market_data,
        }
        rm_analysis = self.risk_manager.analyze(risk_data)

        response_tone = "agrees" if rm_analysis.decision == ma_analysis.decision else "disagrees"
        debate_log.append(
            {
                "agent": "RiskManager",
                "avatar": "🛡️",
                "message": f"I have reviewed the risk profile. I {response_tone} with the analyst.\nMy assessment: {rm_analysis.decision.value}.\nRisk Factors: {rm_analysis.reasoning}",
                "decision": rm_analysis.decision.value,
            }
        )

        # 3. Macro Strategist Adds Context
        macro_data = self.macro_loader.fetch_macro_data()
        ms_analysis = self.macro_strategist.analyze({"ticker": ticker, "macro_data": macro_data})
        debate_log.append(
            {
                "agent": "MacroStrategist",
                "avatar": "🌐",
                "message": f"Adding global perspective... {ms_analysis.reasoning}\nMy macro assessment: {ms_analysis.decision.value}.",
                "decision": ms_analysis.decision.value,
            }
        )

        # 4. Chair (Committee) Concludes
        final_decision, rationale = self._form_consensus([ma_analysis, rm_analysis, ms_analysis])
        debate_log.append(
            {
                "agent": "Chairperson",
                "avatar": "🏛️",
                "message": f"After hearing all perspectives (Technical, Risk, and Macro), the committee rules: {final_decision.value}.\nRationale: {rationale}",
                "decision": final_decision.value,
            }
        )

        return debate_log

    def _form_consensus(self, analyses: List[AgentAnalysis]) -> tuple[TradingDecision, str]:
        """
        Vote counting logic.
        RiskManager has veto power on BUYs if it detects high risk.
        """
        votes = {TradingDecision.BUY: 0, TradingDecision.SELL: 0, TradingDecision.HOLD: 0}

        risk_veto = False
        veto_reason = ""

        weights = self.arena.get_weights()

        for a in analyses:
            weight = weights.get(a.agent_name, 1.0)
            votes[a.decision] += weight
            
            if a.agent_name == "RiskManager" and a.decision == TradingDecision.SELL:
                risk_veto = True
                veto_reason = f"Risk Veto based on: {a.reasoning}"

        # Veto Logic
        if risk_veto:
            return TradingDecision.HOLD, f"Risk Manager exercised Veto. ({veto_reason})"

        # Majority Vote
        if (
            votes[TradingDecision.BUY] > votes[TradingDecision.SELL]
            and votes[TradingDecision.BUY] > votes[TradingDecision.HOLD]
        ):
            return TradingDecision.BUY, "Majority voted BUY."

        if votes[TradingDecision.SELL] > votes[TradingDecision.BUY]:
            return TradingDecision.SELL, "Majority voted SELL."

        return TradingDecision.HOLD, "No clear majority or neutral sentiment."
