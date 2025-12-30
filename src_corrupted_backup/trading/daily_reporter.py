# """
# Daily Reporter Component
# Responsible for generating daily reports, notifications, and running self-reflection loops.
import datetime
import logging
from typing import Any, Dict, Optional
import pandas as pd
import google.generativeai as genai
from src.smart_notifier import SmartNotifier
from src.paper_trader import PaperTrader
from src.feedback_loop import DailyReviewer
from src.data.feedback_store import FeedbackStore
from src.evolution.strategy_generator import StrategyGenerator
from src.evolution.genetic_optimizer import GeneticOptimizer
from src.data_loader import fetch_stock_data
# """
class DailyReporter:
    def __init__(
        self,
        config: Dict[str, Any],
#         """
#         paper_trader: PaperTrader,
#         logger: logging.Logger,
#         config_path: str = "config.json",
#     ):
    pass
#         pass
#         self.config = config
#         self.pt = paper_trader
#         self.logger = logger
#         self.config_path = config_path
#             try:
    pass
#                 self.notifier = SmartNotifier(self.config)
#             self.feedback_store = FeedbackStore()
#             self.genetic_optimizer = GeneticOptimizer()
#             self.logger.info("DailyReporter components initialized.")
#         except Exception as e:
    pass
#             self.logger.error(f"DailyReporter component initialization failed: {e}")
#     def send_daily_report(self) -> None:
    pass
#         """日次レポートを送信"""
#         balance = self.pt.get_current_balance()
#         daily_pnl = self._calculate_daily_pnl()
# # 今日の取引履歴
#         history = self.pt.get_trade_history()
#         today = datetime.date.today()
#             if not history.empty and "timestamp" in history.columns:
    pass
#                 if not pd.api.types.is_datetime64_any_dtype(history["timestamp"]):
    pass
#                     history["timestamp"] = pd.to_datetime(history["timestamp"])
#             today_trades = history[history["timestamp"].dt.date == today]
#         else:
    pass
#             today_trades = pd.DataFrame()
# # 勝率計算
#         win_rate = 0.0
#         if not history.empty and "realized_pnl" in history.columns:
    pass
#             wins = len(history[history["realized_pnl"] > 0])
#             total = len(history[history["realized_pnl"] != 0])
#             win_rate = wins / total if total > 0 else 0.0
# # シグナル情報
#         signals_info = []
#         if not today_trades.empty:
    pass
#             for _, trade in today_trades.iterrows():
    pass
#                 signals_info.append(
#                     {"action": trade["action"], "ticker": trade["ticker"], "name": trade.get("name", trade["ticker"])}
#                 )
# # サマリー送信
#         summary = {
#             "date": today.strftime("%Y-%m-%d"),
#             "total_value": float(balance.get("total_equity", 0.0)),
#             "daily_pnl": daily_pnl,
#             "monthly_pnl": self._calculate_monthly_pnl(),
#             "win_rate": win_rate,
#             "signals": signals_info,
#             "top_performer": "計算中",
#             "advice": self.get_advice(daily_pnl, float(balance.get("total_equity", 0.0))),
#         }
#             self.notifier.send_daily_summary_rich(summary)
#     def get_advice(self, daily_pnl: float, total_equity: float) -> str:
    pass
#         """アドバイスを生成"""
#         if daily_pnl > 0:
    pass
#             return "好調な市場環境です。トレンドフォローを継続しましょう。"
#         else:
    pass
#             return "市場は不安定です。リスク管理を徹底し、ポジションサイズを抑制してください。"
#     def run_post_market_analysis(self) -> None:
    pass
#         """Phase 63: Post-market autonomous feedback loop"""
#         self.logger.info("🔄 Running Post-Market Analysis...")
#             try:
    pass
#                 reviewer = DailyReviewer(self.config_path)
#             result = reviewer.run_daily_review()
#                 metrics = result.get("metrics", {})
#             adjustments = result.get("adjustments", {})
#             journal = result.get("journal", "")
#                 self.logger.info(
#                 f"📊 Daily Metrics: Win Rate={metrics.get('win_rate', 0):.1f}%, P&L=¥{metrics.get('daily_pnl', 0):,.0f}"
#             )
#                 if adjustments and "reason" in adjustments:
    pass
#                     self.logger.info(f"⚙️ Auto-Adjustment: {adjustments['reason']}")
#             else:
    pass
#                 self.logger.info("✅ No parameter adjustments needed")
#                 self.logger.info(f"📝 AI Journal: {journal[:100]}...")
#         except Exception as e:
    pass
#             self.logger.error(f"Post-market analysis failed: {e}")
#     def run_self_reflection(self) -> None:
    pass
#         """Phase 76: AI Self-Reflection & Feedback Loop"""
#         self.logger.info("🧐 AI自己反省フェーズ開始...")
#             try:
    pass
#                 failures = self.feedback_store.get_recent_failures(limit=3)
#             if not failures:
    pass
#                 self.logger.info("分析対象の失敗トレードはありません。")
#                 return
#                 model = genai.GenerativeModel("gemini-1.5-flash")
#                 for f in failures:
    pass
#                     if f.get("reflection_log"):
    pass
#                         continue
#                     ticker = f["ticker"]
#                 self.logger.info(f"分析中: {ticker} (ID: {f['id']})")
#                     prompt = f"""
あなたは自律型投資AIの「反省モジュール」です。
以下の失敗したトレード（予測が外れた取引）の原因を深く分析してください。
【トレード情報】
銘柄: {ticker}
判断: {f['decision']}
当時の理由: {f['rationale']}
結果: 1週間後の収益率 {f['return_1w']*100:.2f}% (目標に達せず)
生データ（抜粋）: {str(f['raw_data'])[:500]}
【タスク】
1. なぜ当時の判断が間違っていたか、3つの可能性を挙げてください。
2. 次回、同様の状況で失敗を避けるための「教訓」を1つ、簡潔に日本語で作成してください。
出力形式:
        分析レポート: <詳細な分析内容>
教訓: <教訓の内容>
response = model.generate_content(prompt)
                text = response.text
                    try:
                        reflection = text.split("教訓:")[0].replace("分析レポート:", "").strip()
                    lesson = text.split("教訓:")[1].strip()
                except Exception:
                    reflection = text
                    lesson = "不明瞭な結果。慎重な取引を継続する。"
                    self.feedback_store.save_reflection(f["id"], reflection, lesson)
                self.logger.info(f"✅ {ticker} の反省完了: {lesson[:50]}...")
            except Exception as e:
                self.logger.warning(f"自己反省エラー: {e}")
#     """
#     def run_strategy_evolution(self) -> None:
    pass
#         """Phase 81: AI Strategy Code Evolution"""
#         if datetime.datetime.now().weekday() == 5:  # Saturday
#             self.logger.info("🧬 AI戦略進化プロセスを開始...")
#             try:
    pass
#                 generator = StrategyGenerator()
#                 generator.evolve_strategies()
#                 self.logger.info("✅ 戦略進化プロセス完了")
#             except Exception as e:
    pass
#                 self.logger.warning(f"戦略進化エラー: {e}")
#     def run_genetic_evolution(self, committee_agents: list) -> None:
    pass
#         """Phase 83: Multi-Agent RL Evolution"""
#         if datetime.datetime.now().weekday() == 5:
    pass
#             if committee_agents:
    pass
#                 self.logger.info("🧬 エージェント遺伝的進化プロセスを開始...")
#                 self.genetic_optimizer.evolve_agents(committee_agents)
#                 self.logger.info("✅ エージェント進化完了")
#     def run_performance_update(self, committee=None) -> None:
    pass
#         """Phase 84/87: Update outcomes, weights, and generate briefing"""
#         self.logger.info("📊 パフォーマンス・データ更新（自己学習）開始...")
#         try:
    pass
#             positions = self.pt.get_positions()
#             monitored_tickers = []
#             if not positions.empty:
    pass
#                 monitored_tickers.extend(
#                     positions["ticker"].tolist() if "ticker" in positions.columns else positions.index.tolist()
#                 )
#                 if monitored_tickers:
    pass
#                     data_map = fetch_stock_data(monitored_tickers, period="5d")
#                 for ticker in monitored_tickers:
    pass
#                     if ticker in data_map and not data_map[ticker].empty:
    pass
#                         last_price = data_map[ticker]["Close"].iloc[-1]
#                         self.feedback_store.update_outcomes(ticker, last_price)
#                 if committee and hasattr(committee, "arena"):
    pass
#                     committee.arena.update_agent_performance()
#                 self.logger.info("✅ 戦略アリーナとバンディットの学習を更新しました。")
# # Phase 26: Sync outcomes to Akashic Records (RAG)
#             try:
    pass
#                 from src.core.memory_annotator import MemoryAnnotator
#                     annotator = MemoryAnnotator()
#                 annotator.sync_outcomes()
#                 self.logger.info("✅ アカシック・レコード（長期記憶）の同期を完了しました。")
#             except Exception as e:
    pass
#                 self.logger.warning(f"アカシック同期エラー: {e}")
# # Phase 28: Council Meta-Learning (Meritocracy Update)
#             try:
    pass
#                 if committee and hasattr(committee, "council"):
    pass
#                     from src.data.feedback_store import FeedbackStore
#                         fs = FeedbackStore()
#                     recent = fs.get_all_decisions(limit=20)
#                     for r in recent:
    pass
#                         ticker = r["ticker"]
#                         ret = r.get("return_1w", 0)
#                         if ret > 0.01:
    pass
#                             outcome = "BULL"
#                         elif ret < -0.01:
    pass
#                             outcome = "BEAR"
#                         else:
    pass
#                             outcome = "NEUTRAL"
#                         committee.council.update_meritocracy(ticker, outcome)
#                     self.logger.info("✅ アバター評議会の実力主義（メリットシステム）を更新しました。")
#             except Exception as e:
    pass
#                 self.logger.warning(f"評議会更新エラー: {e}")
# # Phase 30: Oracle Dynasty Update (Self-Governance)
#             try:
    pass
#                 if committee and hasattr(committee, "dynasty") and committee.dynasty:
    pass
#                     balance = self.pt.get_current_balance()
#                     portfolio_metrics = {
#                         "total_equity": float(balance.get("total_equity", 0.0)),
#                         "daily_pnl": self._calculate_daily_pnl(),
#                         "monthly_pnl": self._calculate_monthly_pnl(),
#                     }
#                     committee.dynasty.evaluate_performance(portfolio_metrics)
# # Update Terminus Ledger for Dynasty persistence
#                     if hasattr(committee, "terminus"):
    pass
#                         committee.terminus.generate_survival_ledger(
#                             portfolio_state=portfolio_metrics,
#                             dynasty_state=committee.dynasty.state,
#                             personality_weights={"logic": 0.6, "intuition": 0.4},
#                         )
#                     self.logger.info("👑 王朝の繁栄記録（Dynasty Record）と終末プロトコルを更新しました。")
#             except Exception as e:
    pass
#                 self.logger.warning(f"王朝更新エラー: {e}")
from src.evolution.briefing_generator import BriefingGenerator
bg = BriefingGenerator()
            bg.generate_briefing()
            self.logger.info("✅ 最新のAIブリーフィングが生成されました。")
# Phase 31: Monthly Knowledge Extraction & Legacy Report
try:
                from datetime import datetime
                    current_day = datetime.now().day
# Run knowledge extraction on the 1st of each month
if current_day == 1:
                    from src.core.knowledge_extractor import KnowledgeExtractor
from src.core.legacy_reporter import LegacyReporter
from src.core.archive_manager import ArchiveManager
archive = ArchiveManager()
                    extractor = KnowledgeExtractor()
                    reporter = LegacyReporter()
# Extract universal patterns from last month
self.logger.info("🧠 [ARCHIVE] 月次知見抽出を開始します...")
                    patterns = archive.extract_knowledge_patterns(lookback_days=30)
# Generate monthly chronicle
last_month = datetime.now().replace(day=1).strftime("%Y/%m")
                    decisions_summary = {
                        "total": patterns.get("total_decisions", 0),
                        "successful": 0,  # Would calculate from actual data
                        "win_rate": 0.0,
                        "notable_events": [],
                    }
                        performance_metrics = {"monthly_return": 0.0}  # Would get from portfolio
                        dynasty_state = committee.dynasty.state if committee and committee.dynasty else {}
                        chronicle_path = reporter.generate_monthly_chronicle(
                        month=last_month,
                        decisions_summary=decisions_summary,
                        performance_metrics=performance_metrics,
                        dynasty_state=dynasty_state,
                    )
                        self.logger.info(f"📜 [LEGACY] 月次年代記が生成されました: {chronicle_path}")
            except Exception as e:
                self.logger.warning(f"知見抽出エラー: {e}")
            except Exception as e:
                self.logger.warning(f"パフォーマンス更新エラー: {e}")
    def _calculate_daily_pnl(self) -> float:
#         """Helper to calculate daily PnL from PT"""
try:
            history = self.pt.get_trade_history()
            if history.empty:
                return 0.0
                today = datetime.date.today()
            if not pd.api.types.is_datetime64_any_dtype(history["timestamp"]):
                history["timestamp"] = pd.to_datetime(history["timestamp"])
                today_trades = history[history["timestamp"].dt.date == today]
            if today_trades.empty:
                return 0.0
                return float(today_trades["realized_pnl"].sum()) if "realized_pnl" in today_trades.columns else 0.0
        except Exception:
            return 0.0
    def _calculate_monthly_pnl(self) -> float:
#         """Helper to calculate monthly PnL from PT"""
try:
            today = datetime.date.today()
            month_start = datetime.date(today.year, today.month, 1)
            history = self.pt.get_trade_history(limit=1000, start_date=month_start)
            if history.empty:
                return 0.0
                if not pd.api.types.is_datetime64_any_dtype(history["timestamp"]):
                    history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")
                history = history.dropna(subset=["timestamp"])
            month_trades = history[history["timestamp"].dt.date >= month_start]
                return (
                float(month_trades["realized_pnl"].sum())
                if not month_trades.empty and "realized_pnl" in month_trades.columns
                else 0.0
            )
        except Exception:
            return 0.0
