from typing import Dict, Any, List
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.agents.market_analyst import MarketAnalyst
from src.agents.risk_manager import RiskManager
from src.schemas import AgentAnalysis, TradingDecision, AppConfig
import logging

logger = logging.getLogger(__name__)

class InvestmentCommittee:
    """
    Orchestrates the debate between multiple AI agents and forms a consensus decision.
    """
    def __init__(self, config: AppConfig = None):
        self.market_analyst = MarketAnalyst()
        self.risk_manager = RiskManager(config.risk if config else None)
        self.agents: List[BaseAgent] = [self.market_analyst, self.risk_manager]
        self.last_meeting_result: Dict[str, Any] = None

    def review_candidate(self, ticker: str, signal_data: Dict[str, Any]) -> TradingDecision:
        """
        Reviews a specific trade candidate derived from the automated trader.
        """
        logger.info(f"🔍 Committee reviewing candidate: {ticker}")
        
        # Construct data payload for agents
        # MarketAnalyst expects 'news' and 'market_stats'
        # we synthesize this from the signal data
        
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
            "market_stats": {
                "price": signal_data.get("price"),
                "vix": signal_data.get("vix", 20.0), # Default safety
                "daily_change": 0.0 # Placeholder
            },
            "portfolio": {
                 # RiskManager uses this, but might default safely if missing
                 # Ideally we should pass real portfolio state here
                 "cash": 1000000, # Mock safe buffer
                 "total_equity": 1000000,
                 "positions": []
            }
        }
        
        result = self.hold_meeting(data)
        return TradingDecision(result["final_decision"])

    def hold_meeting(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conducts a 'committee meeting' where every agent analyzes the data.
        Returns a consolidated report and final decision.
        """
        logger.info("🏛️ Opening Investment Committee Meeting")
        
        analyses: List[AgentAnalysis] = []
        
        # 1. Gather Opinions
        for agent in self.agents:
            try:
                logger.info(f"Asking {agent.name} for opinion...")
                analysis = agent.analyze(data)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"Agent {agent.name} failed to report: {e}")
        
        # 2. Form Consensus (Simple Majority with Risk Veto)
        final_decision, rationale = self._form_consensus(analyses)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "analyses": [a.model_dump() for a in analyses],
            "final_decision": final_decision.value,
            "rationale": rationale,
            "participants": [a.name for a in self.agents]
        }
        
        self.last_meeting_result = result
        logger.info(f"🏛️ Meeting Adjourned. Decision: {final_decision.value}")
        return result

    def _form_consensus(self, analyses: List[AgentAnalysis]) -> tuple[TradingDecision, str]:
        """
        Vote counting logic.
        RiskManager has veto power on BUYs if it detects high risk.
        """
        votes = {
            TradingDecision.BUY: 0,
            TradingDecision.SELL: 0,
            TradingDecision.HOLD: 0
        }
        
        risk_veto = False
        veto_reason = ""
        
        for a in analyses:
            votes[a.decision] += 1
            if a.agent_name == "RiskManager" and a.decision == TradingDecision.SELL:
                risk_veto = True
                veto_reason = f"Risk Veto: {a.reasoning}"
        
        # Veto Logic
        if risk_veto:
            return TradingDecision.HOLD, f"Safety Override: {veto_reason}"
            
        # Majority Vote
        if votes[TradingDecision.BUY] > votes[TradingDecision.SELL] and votes[TradingDecision.BUY] > votes[TradingDecision.HOLD]:
            return TradingDecision.BUY, "Majority voted BUY."
            
        if votes[TradingDecision.SELL] > votes[TradingDecision.BUY]:
            return TradingDecision.SELL, "Majority voted SELL."
            
        return TradingDecision.HOLD, "No majority consensus or neutral sentiment."
