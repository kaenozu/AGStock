# """
# Market Scanner Component
# Responsible for scanning the market, monitoring health, and generating signals using the Strategy Orchestrator.
import datetime
import logging
from typing import Any, Dict, List, Optional
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential
from src.constants import (
    DEFAULT_VOLATILITY_SYMBOL,
    FALLBACK_VOLATILITY_SYMBOLS,
    NIKKEI_225_TICKERS,
    SP500_TICKERS,
)
from src.data_loader import (
    fetch_fundamental_data,
    fetch_stock_data,
    get_latest_price,
)
# """
class MarketScanner:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        pass
        self.config = config
        self.logger = logger
        self.allow_small_mid_cap: bool = True
        self._last_vix_level: Optional[float] = None
# Initialize sub-components (Lazy Load to speed up import)
try:
            from src.data.universe_manager import UniverseManager
from src.data.whale_tracker import WhaleTracker
from src.data.feedback_store import FeedbackStore
from src.regime_detector import RegimeDetector
from src.sentiment import SentimentAnalyzer
from src.strategies.orchestrator import StrategyOrchestrator
from src.utils.parameter_optimizer import ParameterOptimizer
from src.utils.self_healing import SelfHealingEngine
self.universe_manager = UniverseManager()
            self.regime_detector = RegimeDetector()
            self.orchestrator = StrategyOrchestrator(self.config)
            self.self_healing = SelfHealingEngine()
            self.whale_tracker = WhaleTracker()
            self.param_optimizer = ParameterOptimizer(self.config)
            self.feedback_store = FeedbackStore()
            self.logger.info("MarketScanner components initialized.")
        except Exception as e:
            self.logger.error(f"MarketScanner component initialization failed: {e}")
        except Exception as e:
            self.logger.error(f"MarketScanner component initialization failed: {e}")
    def scan_market(self, pt_positions: pd.DataFrame) -> List[Dict[str, Any]]:
#         """市場をスキャンして新規シグナルを検出"""
# V4 Singularity: Self-Healing & Parameter Optimization
self.self_healing.monitor_and_heal()
        vix = self._get_vix_level() or 20.0
# Get simple performance summary for optimizer
perf = {"win_rate": 0.55}  # Placeholder
# Phase 80: Fetch recent lessons for qualitative feedback
recent_lessons = self.feedback_store.get_lessons_for_ticker("%", limit=10)
        new_params = self.param_optimizer.optimize_parameters(perf, vix, recent_lessons=recent_lessons)
            self.logger.info(
            f'🧬 自己最適化適用: TP={new_params.get("take_profit_pct")}, SL={new_params.get("stop_loss_pct")}'
        )
        self.logger.info("市場スキャン開始...")
# センチメント分析
allow_buy = True
        sentiment_penalty = 1.0
        try:
            from src.sentiment import SentimentAnalyzer
                sa = SentimentAnalyzer()
            sentiment = sa.get_market_sentiment()
            self.logger.info(f"市場センチメント: {sentiment['label']} ({sentiment['score']:.2f})")
                score = float(sentiment.get("score", 0.0))
            if score < -0.35:
                sentiment_penalty = 0.5
            elif score < -0.15:
                sentiment_penalty = 0.75
        except Exception as e:
            self.logger.warning(f"センチメント分析エラー: {e}")
# 対象銘柄（グローバル分散）
tickers = self.get_target_tickers(pt_positions)
        self.logger.info(f"対象銘柄数: {len(tickers)}")
# データ取得（リトライ付き）
data_map = self._fetch_data_with_retry(tickers)
            signals: List[Dict[str, Any]] = []
            for ticker in tickers:
                df = data_map.get(ticker)
            if df is None or df.empty:
                continue
# 既にポジションを持っているかチェック
is_held = False
            if not pt_positions.empty:
                if "ticker" in pt_positions.columns:
                    is_held = ticker in pt_positions["ticker"].values
                else:
                    is_held = ticker in pt_positions.index
# Phase 62: レジーム適応型戦略選択
regime = self.regime_detector.detect_regime(df, vix)
            active_squad = self.orchestrator.get_active_squad(regime)
# 各戦略でシグナル生成
for strategy in active_squad:
                strategy_name = strategy.name
                try:
                    sig_series = strategy.generate_signals(df)
                        if sig_series.empty:
                            # 🐋 Whale Flow Detection
                        whale_alert = self.whale_tracker.detect_whale_movement(ticker, df)
                        if whale_alert["detected"]:
                            self.logger.info(
                                f"🐋 WHALE ALERT ({ticker}): {whale_alert['action_type']} (Ratio: {whale_alert['volume_ratio']})"
                            )
                        continue
                        last_signal = sig_series.iloc[-1]
# BUYシグナル
if last_signal == 1 and not is_held and allow_buy:
                        # ファンダメンタルチェック
                        fundamentals = fetch_fundamental_data(ticker)
# 時価総額チェック
if not self.filter_by_market_cap(ticker, fundamentals):
                            self.logger.info(f"  {ticker}: 時価総額が小さすぎるためスキップ")
                            continue
                            pe = fundamentals.get("trailingPE") if fundamentals else None
# PERが極端に高い場合はスキップ
if pe and pe > 50:
                            continue
                            latest_price = get_latest_price(df)
                        if latest_price is None or latest_price <= 0:
                            continue
                            quantity = 0
                        region = self._get_region(ticker)
                            signals.append(
                            {
                                "ticker": ticker,
                                "action": "BUY",
                                "confidence": 0.85,
                                "price": latest_price,
                                "strategy": strategy_name,
                                "quantity": quantity,
                                "reason": f"{strategy_name}による買いシグナル（{region}）",
                                "regime": regime,
                                "history": df.copy(),
                            }
                        )
                        break  # 1銘柄につき1シグナル
# SELLシグナル（保有中の場合）
elif last_signal == -1 and is_held:
                        latest_price = get_latest_price(df)
                        signals.append(
                            {
                                "ticker": ticker,
                                "action": "SELL",
                                "confidence": 0.85,
                                "price": latest_price,
                                "strategy": strategy_name,
                                "reason": f"{strategy_name}による売りシグナル",
                                "regime": regime,
                                "history": df.copy(),
                            }
                        )
                        break
                    except Exception as e:
                        self.logger.warning(f"シグナル生成エラー ({ticker}, {strategy_name}): {e}")
# Phase 3: Divine Sight - Save scan results for UI visualization
try:
            import json
import os
output_data = []
            for sig in signals:
                # Convert non-serializable objects
                item = {
                    "ticker": sig["ticker"],
                    "action": sig["action"],
                    "confidence": sig["confidence"],
                    "price": sig["price"],
                    "strategy": sig["strategy"],
                    "reason": sig["reason"],
                    "regime": sig["regime"],
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                output_data.append(item)
                os.makedirs("data", exist_ok=True)
            with open("data/latest_scan_results.json", "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            self.logger.info("Saved scan results to data/latest_scan_results.json")
# --- Persistence Layer (Akashic Records) ---
from src.db.manager import DatabaseManager
db = DatabaseManager()
            for sig in output_data:
                # Map action to integer signal
                sig_int = 1 if sig["action"] == "BUY" else -1 if sig["action"] == "SELL" else 0
# Try to extract technicals if available? For now pass None
# In future we can enrich this
db.log_scan(ticker=sig["ticker"], signal=sig_int, confidence=sig["confidence"], reasoning=sig["reason"])
            db.close()
            self.logger.info("Saved scan results to Akashic Records (DB).")
# -------------------------------------------
except Exception as e:
            self.logger.warning(f"Failed to save scan results for visualization/DB: {e}")
            self.logger.info(f"検出シグナル数: {len(signals)}")
        return signals
    def get_target_tickers(self, positions: pd.DataFrame) -> List[str]:
#         """UniverseManagerから動的にグローバル銘柄を取得"""
# 保有ポジション
        pos_tickers = [
            str(t) for t in (positions["ticker"] if "ticker" in positions.columns else positions.index).tolist() if t
        ]
# AIによる推薦銘柄（25銘柄+）
ai_candidates = self.universe_manager.get_top_candidates(limit=25)
        result = list(dict.fromkeys(pos_tickers + ai_candidates))
        self.logger.info(f"🌌 グローバル・ユニバース展開: {len(result)}銘柄をスキャンの対象に設定")
        return result
    def filter_by_market_cap(self, ticker: str, fundamentals: Optional[Dict[str, Any]]) -> bool:
#         """時価総額で銘柄をフィルタリング"""
if not self.allow_small_mid_cap:
            return True
            if not fundamentals:
                return False
            market_cap = fundamentals.get("marketCap", 0)
        if market_cap == 0:
            return True
# 10億円以上
if market_cap >= 1_000_000_000:
            return True
            return False
    def _get_vix_level(self) -> Optional[float]:
#         """最新のVIX/代替ボラ指標を取得"""
fallback_list: List[str] = []
        try:
            cfg_vix = self.config.get("market_indices", {}).get("vix")
            if cfg_vix:
                fallback_list.append(str(cfg_vix))
        except Exception:
            pass
            try:
                vol_list = self.config.get("volatility_symbols")
            if vol_list and isinstance(vol_list, list) and all(isinstance(s, str) for s in vol_list if s):
                fallback_list.extend([str(s) for s in vol_list if s])
        except Exception:
            pass
            if not fallback_list:
                fallback_list = [DEFAULT_VOLATILITY_SYMBOL]
            for sym in FALLBACK_VOLATILITY_SYMBOLS:
                if sym not in fallback_list:
                    fallback_list.append(sym)
            for sym in fallback_list:
                try:
                    import yfinance as yf
                    vix = yf.Ticker(sym)
                hist = vix.history(period="5d", interval="1d")
                if hist is None or hist.empty or "Close" not in hist.columns:
                    continue
                val = float(hist["Close"].iloc[-1])
                self._last_vix_level = val
                return val
            except Exception as exc:
                self.logger.debug(f"ボラティリティ指標取得失敗: {sym} ({exc})")
                continue
            return self._last_vix_level
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_data_with_retry(self, tickers: List[str]) -> Dict[str, pd.DataFrame]:
        pass
#         """
#         Fetch Data With Retry.
#             Args:
#                 tickers: Description of tickers
#             Returns:
#                 Description of return value
#                 try:
#                     self.logger.info(f"データ取得中... ({len(tickers)}銘柄)")
#             data_map = fetch_stock_data(tickers, period="2y")
#             self.logger.info(f"データ取得完了: {len(data_map)}銘柄")
#             return data_map
#         except Exception as e:
#             self.logger.warning(f"データ取得失敗（リトライします）: {e}")
#             raise
# """
def _get_region(self, ticker: str) -> str:
        pass # Force Balanced
