import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import pandas as pd
if TYPE_CHECKING:
        from src.schemas import AppConfig
logger = logging.getLogger(__name__)
class InvestmentCommittee:
#     """
#     Orchestrates the debate between multiple AI agents and forms a consensus decision.
#     """
def __init__(self, config: "AppConfig" = None):
        pass
        self._initialize_core_agents(config)
        self._initialize_infrastructure()
        self._initialize_specialists()
        self._initialize_evolution_modules()
    def _initialize_core_agents(self, config: Optional["AppConfig"]):
        pass
from src.agents.market_analyst import MarketAnalyst
from src.agents.risk_manager import RiskManager
from src.agents.macro_analyst import MacroStrategist
from src.agents.rl_agent_wrapper import RLAgentWrapper
from src.agents.base_agent import BaseAgent
from src.enhanced_ensemble_predictor import EnhancedEnsemblePredictor
from src.agents.strategy_arena import StrategyArena
from src.agents.agent_spawner import AgentSpawner
self.market_analyst = MarketAnalyst()
        self.risk_manager = RiskManager(config.risk if config else None)
        self.macro_strategist = MacroStrategist()
# Phase 83: Multi-Agent RL Arena - Wrap agents with RL layer
self.market_analyst_rl = RLAgentWrapper(self.market_analyst, name_suffix="_RL")
        self.risk_manager_rl = RLAgentWrapper(self.risk_manager, name_suffix="_RL")
        self.macro_strategist_rl = RLAgentWrapper(self.macro_strategist, name_suffix="_RL")
            self.agents: List[BaseAgent] = [self.market_analyst_rl, self.risk_manager_rl, self.macro_strategist_rl]
            self.predictor = EnhancedEnsemblePredictor()
        self.arena = StrategyArena()
        self.spawner = AgentSpawner()
    def _initialize_infrastructure(self):
        pass
#         """Initialize data loaders, stores, and operational tools."""
from src.data.macro_loader import MacroLoader
from src.data.earnings_history import EarningsHistory
from src.data.feedback_store import FeedbackStore
from src.execution.news_shock_defense import NewsShockDefense
from src.execution.position_sizer import PositionSizer
from src.oracle.event_forecaster import EventForecaster
from src.core.experience_manager import ExperienceManager
self.macro_loader = MacroLoader()
        self.earnings_history = EarningsHistory()
        self.feedback_store = FeedbackStore()
        self.experience_manager = ExperienceManager()
        self.defense = NewsShockDefense()
        self.sizer = PositionSizer()
        self.oracle = EventForecaster()
# Phase 28: Multimodal PDF Analyst
try:
            from src.rag.multimodal_analyst import DeepMultimodalAnalyst
                self.multimodal_analyst = DeepMultimodalAnalyst()
        except ImportError:
            self.multimodal_analyst = None
            self.last_meeting_result: Dict[str, Any] = None
        self.last_forecast = None
    def _initialize_specialists(self):
        pass
#         """Initialize specialized analysis agents (Phases 85-160)."""
from src.agents.macro_agent import MacroAgent  # Phase 85
from src.evolution.chart_vision import ChartVisionEngine  # Phase 92
from src.rag.deep_hunter import DeepHunterRAG  # Phase 93
from src.evolution.paradigm_switcher import ParadigmManager  # Phase 99
from src.evolution.swarm_intel import SwarmIntelligence  # Phase 150
from src.agents.intuition_engine import IntuitionEngine  # Phase 160
self.macro_agent = MacroAgent()  # Phase 85
        self.chart_vision = ChartVisionEngine()  # Phase 92
        self.deep_hunter = DeepHunterRAG()  # Phase 93
        self.paradigm_manager = ParadigmManager()  # Phase 99
        self.swarm = SwarmIntelligence()  # Phase 150
        self.intuition = IntuitionEngine()  # Phase 160
    def _initialize_evolution_modules(self):
        pass
#         """Initialize evolution, simulation, and high-level council modules (Phases 300+)."""
from src.simulation.digital_twin import DigitalTwin
from src.agents.shadow_council import ShadowCouncil
from src.evolution.terminus_protocol import TerminusManager  # Phase 300
from src.agents.council_avatars import AvatarCouncil  # Phase 700
self.twin = DigitalTwin()
        self.shadow_council = ShadowCouncil()
        self.terminus = TerminusManager()  # Phase 300
        self.council = AvatarCouncil()  # Phase 700
# Phase 29: Paradigm Metamorphosis
self.current_paradigm = "UNKNOWN"
# Phase 30: Oracle Dynasty
try:
            from src.core.dynasty_manager import DynastyManager
                self.dynasty = DynastyManager()
        except ImportError:
            self.dynasty = None
# Phase 31: Eternal Archive
try:
            from src.core.archive_manager import ArchiveManager
from src.core.knowledge_extractor import KnowledgeExtractor
self.archive = ArchiveManager()
            self.knowledge = KnowledgeExtractor()
        except ImportError:
            self.archive = None
            self.knowledge = None
    def review_candidate(self, ticker: str, signal_data: Dict[str, Any]) -> "TradingDecision":
        pass
        Conducts a 'committee meeting' where every agent analyzes the data.
        Returns a consolidated report and final decision.
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
                kb_text += (
                    f"- {l['timestamp'][:10]}: {l['decision']} -> {l['outcome']} (収益率: {l['return_1w']*100:.1f}%)\n"
                )
            if recent_failures:
                kb_text += "\n【最近の全体的な失敗事例】\n"
            for f in recent_failures:
                kb_text += (
                    f"- {f['ticker']} ({f['timestamp'][:10]}): {f['rationale'][:50]}... -> 結果: {f['outcome']}\n"
                )
            if kb_text:
                data["lessons_learned"] = kb_text
            logger.info("Injected self-learning context into meeting data.")
# Phase 26: Semantic Lesson Retrieval (Akashic RAG)
context_query = f"{ticker} | {data.get('news', '')}"
        semantic_lessons = self.experience_manager.retrieve_lessons(context_query)
        if semantic_lessons:
            rag_text = "\n【アカシック・レコードの断片（極めて類似した過去のケース）】\n"
            for sl in semantic_lessons:
                meta = sl["metadata"]
                status = meta.get("status", "PENDING")
                pnl = meta.get("pnl", 0.0)
                rag_text += f"- 過去の文脈: {sl['context'][:100]}...\n"
                rag_text += f"  決定: {meta.get('decision')} | 結果: {status} (PnL: {pnl:.2f}%)\n"
                if "lessons_learned" in data:
                    data["lessons_learned"] += rag_text
            else:
                data["lessons_learned"] = rag_text
            logger.info("Injected semantic lessons into meeting data.")
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
context = data.get("market_stats", {})
        final_decision, rationale = self._form_consensus(analyses, context=context)
# 2.5. Shadow Council Debate (Final Approval)
        council_result = self.shadow_council.hold_debate(
            ticker=ticker,
            proposed_action=final_decision.value,
            data_context=f"Analyses: {analyses}\nForecast: {self.last_forecast}",
        )
        if council_result["consensus"] == "REJECT":
            from src.schemas import TradingDecision
                final_decision = TradingDecision.HOLD
            rationale = "Shadow Council rejected: " + council_result["debate_log"]
            result = {
            "timestamp": datetime.now().isoformat(),
            "analyses": [a.model_dump() for a in analyses],
            "final_decision": final_decision.value,
            "rationale": rationale,
            "participants": [a.name for a in all_agents],
            "spawned_agents": [a.name for a in spawned_agents],
        }
# 3. Shadow Simulation (Digital Twin)
current_price = data.get("market_stats", {}).get("price", 0.0)
        self.twin.record_decision(ticker, final_decision.value, current_price)
# 4. Position Sizing
equity = data.get("portfolio", {}).get("total_equity", 1000000)
        win_rate = 0.6  # Placeholder for realized win-rate
        sizing = self.sizer.calculate_size(ticker, equity, win_rate)
        result["sizing_recommendation"] = sizing
            self.last_meeting_result = result
        logger.info(f"🏛️ Meeting Adjourned. Decision: {final_decision.value}")
        return result
# """
def conduct_debate(
        self,
        ticker: str,
#         """
#         market_data: Dict[str, Any],
#         position: Optional[Dict[str, Any]] = None,
#         market_df: Optional[pd.DataFrame] = None,
#     ) -> List[Dict[str, str]]:
#         """
Simulates a conversational debate among agents for UI display.
        Returns a list of message objects: {"agent": "Name", "message": "Content", "decision": "BUY/SELL"}
                # Fix: Create a data context that subsequent 'Phase' blocks expect
        data = {
            "ticker": ticker,
            "market_stats": market_data,
            "portfolio": {"positions": [position] if position else []},
        }
# Inject additional context if available to match hold_meeting logic
# Phase 29: Paradigm Metamorphosis Detection
macro_stats = data.get("market_stats", {})
        macro_stats["vix_value"] = macro_stats.get("vix", 18.0)
        macro_score = macro_stats.get("macro_score", macro_stats.get("score", 50))
        macro_stats["score"] = macro_score
            new_paradigm = self.paradigm_manager.detect_paradigm(macro_stats)
        debate_log = []
            if new_paradigm != self.current_paradigm:
                logger.warning(f"🎭 PARADIGM SHIFT DETECTED: {self.current_paradigm} -> {new_paradigm}")
            self.paradigm_manager.trigger_metamorphosis(new_paradigm)
            self.current_paradigm = new_paradigm
            debate_log.append(
                {
                    "agent": "System",
                    "avatar": "🎭",
                    "message": f"🎭 相場パラダイムの変容を検知しました: `{new_paradigm}`。システムを最適化中...",
                    "decision": "HOLD",
                }
            )
# Inject additional context if available to match hold_meeting logic
data["deep_hunt"] = self.deep_hunter.analyze_deep_shift(ticker, {}) if hasattr(self, "deep_hunter") else None
        data["swarm_pulse"] = self.swarm.get_swarm_pulse(ticker) if hasattr(self, "swarm") else None
        data["quantum_instinct"] = (
            self.intuition.get_instinct(ticker, market_data) if hasattr(self, "intuition") else None
        )
        data["council_results"] = self.council.hold_grand_assembly(ticker, data) if hasattr(self, "council") else None
# Phase 26: Akashic Memory Insight (Log before other agents)
try:
            context_query = f"{ticker} | {market_data.get('market_trend', '')}"
            semantic_lessons = self.experience_manager.retrieve_lessons(context_query, n_results=1)
            if semantic_lessons:
                lesson = semantic_lessons[0]
                debate_log.append(
                    {
                        "agent": "AkashicMemory",
                        "avatar": "📜",
                        "message": f"📜 過去の記憶を呼び出しています... \n類似局面の教訓: {lesson['context'][:100]}...\n前回の結果: {lesson['metadata'].get('status')} (PnL: {lesson['metadata'].get('pnl', 0)*100:.1f}%)",
                        "decision": "NEUTRAL",
                    }
                )
        except Exception as e:
            logger.warning(f"Akashic retrieval failed in debate: {e}")
# Phase 27: Precog Intelligence Preview
try:
            from src.oracle.precog_engine import PrecogEngine
from src.news_collector import get_news_collector
news = get_news_collector().fetch_market_news(limit=5)
            news_text = " ".join([n["title"] for n in news])
            precog = PrecogEngine().get_upcoming_events_analysis(news_text)
                if precog.get("aggregate_risk_score", 0) > 50:
                    debate_log.append(
                    {
                        "agent": "Precog",
                        "avatar": "🔮",
                        "message": f"🔮 未来予報: 警戒イベントを検知しました。 \nリスクスコア: {precog['aggregate_risk_score']}% | ステータス: {precog['system_status']}\n主な要因: {precog['events'][0]['name'] if precog['events'] else 'Macro Volatility'}",
                        "decision": "SELL" if precog["aggregate_risk_score"] > 75 else "NEUTRAL",
                    }
                )
        except Exception as e:
            logger.warning(f"Precog retrieval failed in debate: {e}")
# 0. Phase 92: Chart Vision Analysis
visual_findings = None
        if market_df is not None:
            visual_findings = self.chart_vision.analyze_chart_vision(market_df, ticker)
            if visual_findings:
                debate_log.append(
                    {
                        "agent": "VisualOracle",
                        "avatar": "👁️",
                        "message": f"I've analyzed the chart images. Findings: {visual_findings.get('visual_rationale')}\nPatterns: {', '.join(visual_findings.get('patterns', []))}",
                        "decision": visual_findings.get("verdict", "NEUTRAL"),
                        "support": visual_findings.get("support"),
                        "resistance": visual_findings.get("resistance"),
                    }
                )
# 0.1 Phase 93: Deep Hunter Analysis
deep_hunt = data.get("deep_hunt")
        if deep_hunt and "error" not in deep_hunt:
            debate_log.append(
                {
                    "agent": "DeepHunter",
                    "avatar": "🕵️",
                    "message": f"Deep analysis complete. Skepticism Score: {deep_hunt.get('skepticism_score')}/100. \nVerdict: {deep_hunt.get('deep_verdict')}\nBroken Commitments: {', '.join(deep_hunt.get('broken_commitments', []))}",
                    "decision": "SELL" if deep_hunt.get("skepticism_score", 0) > 70 else "NEUTRAL",
                }
            )
# 0.2 Phase 99: Paradigm Switcher
paradigm = data.get("paradigm")
        if paradigm:
            debate_log.append(
                {
                    "agent": "ParadigmManager",
                    "avatar": "🗺️",
                    "message": f"Global Paradigm Shift detected: **{paradigm}** mode active. Strategy filtering applied.",
                    "decision": "NEUTRAL",
                }
            )
# 0.3 Phase 150: Omniscient Swarm
swarm_pulse = data.get("swarm_pulse")
        if swarm_pulse:
            debate_log.append(
                {
                    "agent": "SwarmIntelligence",
                    "avatar": "📡",
                    "message": f"📡 Swarm Pulse: {swarm_pulse.get('collective_sentiment'):.2f} alignment. \nInsight: {swarm_pulse.get('whispers')}",
                    "decision": "BUY" if swarm_pulse.get("collective_sentiment", 0) > 0.3 else "NEUTRAL",
                }
            )
# 0.4 Phase 160: Quantum Intuition
instinct = data.get("quantum_instinct")
        if instinct and "error" not in instinct:
            debate_log.append(
                {
                    "agent": "QuantumOracle",
                    "avatar": "🧠",
                    "message": f"🧠 Instinctive Signal: {instinct.get('instinct_direction')}. Score: {instinct.get('instinct_score')}/100. \nGut Feeling: {instinct.get('wild_card')}",
                    "decision": (
                        "BUY"
                        if instinct.get("instinct_score", 0) > 75
                        else "SELL" if instinct.get("instinct_score", 0) < 25 else "NEUTRAL"
                    ),
                }
            )
# 0.5 Phase 700: Council of Avatars
council = data.get("council_results")
        if council:
            clusters = council.get("clusters", {})
            debate_log.append(
                {
                    "agent": "AvatarCouncil",
                    "avatar": "🏛️",
                    "message": f"🏛️ Grand Assembly Verdict: Consensus Score {council.get('avg_score'):.1f}/100. \nClusters: {clusters.get('Bulls')} Bulls, {clusters.get('Bears')} Bears, {clusters.get('Neutral')} Neutral. \nVoices: {', '.join(council.get('sample_shouts', []))}",
                    "decision": (
                        "BUY"
                        if council.get("avg_score", 0) > 60
                        else "SELL" if council.get("avg_score", 0) < 40 else "NEUTRAL"
                    ),
                }
            )
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
context = {"ticker": ticker, "market_stats": market_data}
        final_decision, rationale = self._form_consensus([ma_analysis, rm_analysis, ms_analysis], context=context)
        debate_log.append(
            {
                "agent": "Chairperson",
                "avatar": "🏛️",
                "message": f"After hearing all perspectives (Technical, Risk, and Macro), the committee rules: {final_decision.value}.\nRationale: {rationale}",
                "decision": final_decision.value,
            }
        )
            return debate_log
# """
def _form_consensus(self, analyses: List["AgentAnalysis"], context: Optional[Dict[str, Any]] = None):
        pass
#         """
#         Vote counting logic.
#         RiskManager has veto power on BUYs if it detects high risk.
#         Phase 84: Now uses Contextual Bandit weights if context is provided.
#         from src.schemas import TradingDecision
#             votes = {TradingDecision.BUY: 0, TradingDecision.SELL: 0, TradingDecision.HOLD: 0}
#             risk_veto = False
#         veto_reason = ""
# # Phase 78/84: Dynamic Weighting
#         agent_names = [a.agent_name for a in analyses]
#         base_weights = self.arena.get_weights(context=context, strategies=agent_names)
#         leaderboard = self.feedback_store.get_agent_leaderboard()
# # Map class names to leaderboard keys
#         name_map = {
#             "VisualOracle": "visual_pred",
#             "SocialAnalyst": "social_pred",
#             "EnhancedEnsemblePredictor": "tech_pred",
#             "MarketAnalyst": "tech_pred",
#         }
#             for a in analyses:
    pass
#                 # 1. Start with static arena weight or 1.0
#             weight = base_weights.get(a.agent_name, 1.0)
# # 2. Adjust by dynamic accuracy if available
#             lb_key = name_map.get(a.agent_name)
#             if lb_key and lb_key in leaderboard:
    pass
#                 acc = leaderboard[lb_key]["accuracy"]
#                 if acc > 0:
    pass
#                     # Accuracy centered at 0.5. 0.6 Accuracy -> 1.2x boost. 0.4 Accuracy -> 0.8x penalty.
#                     adjustment = acc / 0.5
#                     weight *= adjustment
#                     logger.info(f"Dynamic weighting for {a.agent_name}: x{adjustment:.2f} (Acc: {acc:.2f})")
#                 votes[a.decision] += weight
#                 if a.agent_name == "RiskManager" and a.decision == TradingDecision.SELL:
    pass
#                     risk_veto = True
#                 veto_reason = f"Risk Veto based on: {a.reasoning}"
# # Veto Logic
#         if risk_veto:
    pass
#             return TradingDecision.HOLD, f"Risk Manager exercised Veto. ({veto_reason})"
# # Majority Vote
#         if (
#             votes[TradingDecision.BUY] > votes[TradingDecision.SELL]
#             and votes[TradingDecision.BUY] > votes[TradingDecision.HOLD]
#         ):
    pass
#             return TradingDecision.BUY, "Majority voted BUY."
#             if votes[TradingDecision.SELL] > votes[TradingDecision.BUY]:
    pass
#                 return TradingDecision.SELL, "Majority voted SELL."
#             return TradingDecision.HOLD, "No clear majority or neutral sentiment."
# 
# 
