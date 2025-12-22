"""
完全自動トレーダー - 個人投資家向け

安全策を含む完全自動運用システム
"""

import datetime
# Config & Logging
# Using main branch style imports where possible
# main uses self.load_config method, HEAD uses load_config_from_yaml util.
# We'll stick to main's method for consistency with standard refactor.
import json
import logging
import os
import traceback
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
# リトライロジック
from tenacity import retry, stop_after_attempt, wait_exponential

from src.agents.committee import InvestmentCommittee
from src.backup_manager import BackupManager
from src.cache_config import install_cache
from src.constants import (
    DEFAULT_VOLATILITY_SYMBOL,
    FALLBACK_VOLATILITY_SYMBOLS,
    NIKKEI_225_TICKERS,
    SP500_TICKERS,
    STOXX50_TICKERS,
)
from src.data_loader import (
    CRYPTO_PAIRS,
    FX_PAIRS,
    fetch_fundamental_data,
    fetch_stock_data,
    get_latest_price,
)
from src.dynamic_risk_manager import DynamicRiskManager
from src.dynamic_stop import DynamicStopManager
from src.execution import ExecutionEngine
from src.kelly_criterion import KellyCriterion
from src.paper_trader import PaperTrader
# New Features from feat-add-position-guards
from src.regime_detector import RegimeDetector
from src.schemas import AppConfig, TradingDecision
from src.sentiment import SentimentAnalyzer
from src.smart_notifier import SmartNotifier
from src.strategies import CombinedStrategy, LightGBMStrategy, MLStrategy
from src.strategies.orchestrator import StrategyOrchestrator
from src.feedback_loop import DailyReviewer
from src.utils.logger import get_logger, setup_logger
from src.data.universe_manager import UniverseManager
from src.utils.self_healing import SelfHealingEngine
from src.utils.parameter_optimizer import ParameterOptimizer
from src.data.whale_tracker import WhaleTracker
from src.agents.ai_veto_agent import AIVetoAgent
from src.agents.social_analyst import SocialAnalyst
from src.trading.portfolio_manager import PortfolioManager
from src.utils.self_learning import SelfLearningPipeline

# Create logger
logger = logging.getLogger(__name__)

DEFAULT_PORTFOLIO_TARGETS = {"japan": 40, "us": 30, "europe": 10, "crypto": 10, "fx": 10}


class FullyAutomatedTrader:
    """完全自動トレーダー（安全策付き）"""

    def __init__(self, config_path: str = "config.json") -> None:
        """初期化"""
        # 設定読み込み
        self.config: Dict[str, Any] = self.load_config(config_path)

        # ログファイル
        self.log_file: str = "logs/auto_trader.log"
        os.makedirs("logs", exist_ok=True)
        setup_logger("AutoTrader", "logs", "auto_trader.log")
        self.logger = get_logger("AutoTrader")

        # コアコンポーネント
        self.pt = PaperTrader()
        self.notifier = SmartNotifier(self.config)  # Combined usage

        # ボラティリティ指標キャッシュ
        self._last_vix_level: Optional[float] = None

        # バックアップマネージャー
        self.backup_manager: Optional[BackupManager] = None
        try:
            self.backup_manager = BackupManager()
        except Exception:
            self.logger.warning("BackupManager initialization failed.")

        # 実行エンジン
        self.engine = ExecutionEngine(self.pt)

        # AI Investment Committee
        self.ai_config = self.config.get("ai_committee", {})
        self.ai_enabled = self.ai_config.get("enabled", False)

        if self.ai_enabled:
            try:
                # AppConfigへ変換して初期化（簡易的）
                app_config = AppConfig(**self.config) if self.config else None
                self.committee = InvestmentCommittee(app_config)
                self.log("🤖 AI投資委員会: 有効 (Active)")
            except Exception as e:
                self.log(f"AI委員会初期化エラー: {e}", "ERROR")
                self.committee = None
                self.ai_enabled = False
        else:
            self.committee = None
            self.log("🤖 AI投資委員会: 無効 (Disabled)")

        # リスク設定
        self.risk_config: Dict[str, Any] = self.config.get("auto_trading", {})
        self.max_daily_trades: int = int(self.risk_config.get("max_daily_trades", 5))

        # ポートフォリオ配分目標（configから取得、未設定時はデフォルト）
        self._load_portfolio_targets()

        self.allow_small_mid_cap: bool = True
        self.backup_enabled: bool = True
        self.emergency_stop_triggered: bool = False

        # New Risk Modules (from feat-add-position-guards)
        try:
            self.regime_detector = RegimeDetector()
            self.orchestrator = StrategyOrchestrator(self.config) # Added
            self.risk_manager = DynamicRiskManager(self.regime_detector)
            self.kelly_criterion = KellyCriterion()
            self.dynamic_stop_manager = DynamicStopManager()
            self.universe_manager = UniverseManager()
            self.self_healing = SelfHealingEngine()
            self.param_optimizer = ParameterOptimizer(self.config)
            self.whale_tracker = WhaleTracker()
            self.portfolio_manager = PortfolioManager()
            self.learning_pipeline = SelfLearningPipeline(self.config)
            self.ai_veto_agent = AIVetoAgent(self.config)
            self.social_analyst = SocialAnalyst(self.config)
            
            self.log('Phase 73: Self-Learning Pipeline (Optima) initialized')
            self.log('Phase 73: Social Heat Analyst initialized')
            self.log('Phase 72: Portfolio Risk Parity Manager initialized')
            self.log('Phase 5: WhaleTracker (Institutional Flow) initialized')
            self.log('Phase 4: Global Selection & Self-Correction initialized')
            # self.advanced_risk = AdvancedRiskManager(self.config) # Class missing, disabled
            self.log("Phase 62: Strategy Orchestrator & Regime Detector initialized")
        except Exception as e:
            self.log(f"高度リスク管理モジュールの初期化エラー: {e}", "WARNING")

        self.log("フル自動トレーダー初期化完了")

    def _load_portfolio_targets(self) -> None:
        """config.json から地域別ターゲット配分を読み込み"""
        portfolio_targets = self.config.get("portfolio_targets", DEFAULT_PORTFOLIO_TARGETS)
        self.target_japan_pct = float(portfolio_targets.get("japan", DEFAULT_PORTFOLIO_TARGETS["japan"]))
        self.target_us_pct = float(portfolio_targets.get("us", DEFAULT_PORTFOLIO_TARGETS["us"]))
        self.target_europe_pct = float(portfolio_targets.get("europe", DEFAULT_PORTFOLIO_TARGETS["europe"]))
        self.target_crypto_pct = float(portfolio_targets.get("crypto", DEFAULT_PORTFOLIO_TARGETS["crypto"]))
        self.target_fx_pct = float(portfolio_targets.get("fx", DEFAULT_PORTFOLIO_TARGETS["fx"]))
        total_pct = (
            self.target_japan_pct
            + self.target_us_pct
            + self.target_europe_pct
            + self.target_crypto_pct
            + self.target_fx_pct
        )
        if abs(total_pct - 100.0) > 0.5:
            self.log(f"ポートフォリオ配分の合計が100%ではありません: {total_pct:.1f}% (警告)", "WARNING")

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # デフォルト設定
            return {
                "paper_trading": {"initial_capital": 1000000},
                "auto_trading": {"max_daily_trades": 5, "daily_loss_limit_pct": -5.0, "max_vix": 40.0},
                "notifications": {"line": {"enabled": False}},
            }

    def log(self, message: str, level: str = "INFO") -> None:
        """ログ出力"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)

        if level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "CRITICAL":
            self.logger.critical(message)
        else:
            self.logger.debug(message)

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except Exception:
            pass  # ログ書き込み失敗しても続行

    def calculate_daily_pnl(self) -> float:
        """本日の損益を計算"""
        try:
            # 今日の取引履歴から計算
            history = self.pt.get_trade_history()

            if history.empty:
                return 0.0

            # timestampカラムがない場合は0を返す
            if "timestamp" not in history.columns:
                self.log("取引履歴にtimestampカラムがありません", "WARNING")
                return 0.0

            today = datetime.date.today()

            # timestampをdatetimeに変換
            if not pd.api.types.is_datetime64_any_dtype(history["timestamp"]):
                history["timestamp"] = pd.to_datetime(history["timestamp"])

            today_trades = history[history["timestamp"].dt.date == today]

            if today_trades.empty:
                return 0.0

            # realized_pnlカラムがあれば使用
            if "realized_pnl" in today_trades.columns:
                pnl = float(today_trades["realized_pnl"].sum())
            else:
                pnl = 0.0

            return pnl
        except Exception as e:
            self.log(f"日次損益計算エラー: {e}", "WARNING")
            return 0.0

    def calculate_monthly_pnl(self, history_limit: int = 1000) -> float:
        """当月の損益を計算"""
        try:
            today = datetime.date.today()
            month_start = datetime.date(today.year, today.month, 1)
            history = self.pt.get_trade_history(limit=history_limit, start_date=month_start)
            if history.empty:
                return 0.0

            if "timestamp" not in history.columns:
                self.log("取引履歴にtimestampカラムがありません（monthly_pnl計算スキップ）", "WARNING")
                return 0.0

            if not pd.api.types.is_datetime64_any_dtype(history["timestamp"]):
                history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")

            history = history.dropna(subset=["timestamp"])
            if history.empty:
                return 0.0

            month_trades = history[history["timestamp"].dt.date >= month_start]

            if month_trades.empty or "realized_pnl" not in month_trades.columns:
                return 0.0

            return float(month_trades["realized_pnl"].sum())
        except Exception as e:
            self.log(f"月次損益計算エラー: {e}", "WARNING")
            return 0.0

    def _get_vix_level(self) -> Optional[float]:
        """
        最新のVIX/代替ボラ指標を取得。失敗時は最後の成功値を返す。
        - config.volatility_symbols にリストがあれば優先
        - market_indices.vix があれば先頭に使う
        """
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

        # Ensure defaults are present for safety
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
                self.log(f"ボラティリティ指標取得失敗: {sym} ({exc})", "WARNING")
                continue

        return self._last_vix_level

    def is_safe_to_trade(self) -> Tuple[bool, str]:
        """取引が安全か確認"""
        # 1. 日次損失制限チェック
        daily_pnl = self.calculate_daily_pnl()
        balance = self.pt.get_current_balance()
        total_equity = float(balance.get("total_equity", 0.0))
        cash = float(balance.get("cash", 0.0))

        daily_loss_pct = (daily_pnl / total_equity) * 100 if total_equity > 0 else 0

        daily_loss_limit = float(self.risk_config.get("daily_loss_limit_pct", -5.0))
        if daily_loss_pct < daily_loss_limit:
            return False, f"日次損失制限を超過: {daily_loss_pct:.2f}%"

        # 2. 市場ボラティリティチェック
        vix_level = self._get_vix_level()
        max_vix = float(self.risk_config.get("max_vix", 40.0))
        if vix_level is not None:
            if vix_level > max_vix:
                return False, f"市場ボラティリティが高すぎます (VIX: {vix_level:.1f})"
        else:
            self.log("VIX取得に失敗しました（キャッシュも無し）: ボラティリティチェックをスキップ", "WARNING")

        # 3. 残高チェック
        if cash < 10000:  # 最低1万円
            return False, "現金残高が不足しています"

        return True, "OK"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_data_with_retry(self, tickers: List[str]) -> Dict[str, pd.DataFrame]:
        """
        リトライロジック付きでデータ取得
        """
        try:
            self.log(f"データ取得中... ({len(tickers)}銘柄)")
            data_map = fetch_stock_data(tickers, period="2y")
            self.log(f"データ取得完了: {len(data_map)}銘柄")
            return data_map
        except Exception as e:
            self.log(f"データ取得失敗（リトライします）: {e}", "WARNING")
            raise  # リトライのために例外を再throw

    def emergency_stop(self, reason: str) -> None:
        """緊急停止を実行"""
        self.emergency_stop_triggered = True
        self.log(f"🚨 緊急停止: {reason}", "CRITICAL")

        # バックアップ作成
        if self.backup_enabled and self.backup_manager:
            try:
                backup_path = self.backup_manager.auto_backup()
                if backup_path:
                    self.log(f"緊急バックアップ作成: {backup_path}")
            except Exception as e:
                self.log(f"緊急バックアップ失敗: {e}", "ERROR")

        # 通知送信
        try:
            token = self.config.get("notifications", {}).get("line", {}).get("token")
            if token:
                self.notifier.send_line_notify(
                    f"🚨 緊急停止が発生しました\n理由: {reason}\n\n自動トレードを停止しました。", token=token
                )
        except Exception:
            pass  # 通知失敗しても緊急停止は継続

    def evaluate_positions(self) -> List[Dict]:
        """
        保有ポジションを評価し、損切り・利確のシグナルを生成 (Merged from feat-add-position-guards)
        - DynamicStopManager でのストップ更新・保存
        - ATRベースの下支え
        - トレーリング／固定利確
        """
        positions = self.pt.get_positions()
        if positions.empty:
            return []

        # Get tickers safely
        # Handle case where ticker is index or column
        if "ticker" in positions.columns:
            tickers = positions["ticker"].tolist()
        else:
            tickers = positions.index.tolist()

        tickers = [str(t) for t in tickers if t]

        if not tickers:
            return []

        data_map = self._fetch_data_with_retry(tickers)
        signals: List[Dict] = []

        for idx, position in positions.iterrows():
            ticker = str(position.get("ticker", idx))
            if not ticker:
                continue

            df = data_map.get(ticker)
            if df is None or df.empty:
                continue

            latest_price = get_latest_price(df)
            entry_price = float(position.get("entry_price") or position.get("avg_price") or 0.0)
            quantity = float(position.get("quantity", 0))
            if entry_price == 0 or quantity <= 0 or latest_price is None:
                self.log(f"エントリー価格または数量が不明/無効: {ticker}", "WARNING")
                continue

            pnl_pct = (latest_price - entry_price) / entry_price

            # Unrealized pct from DB or calc
            unrealized_pct = float(position.get("unrealized_pnl_pct", pnl_pct * 100))

            # Dynamic Stop Manager logic
            if hasattr(self, "dynamic_stop_manager"):
                highest_price = float(position.get("highest_price") or entry_price)
                if highest_price < latest_price:
                    highest_price = latest_price  # Update local known highest

                # Update manager internal state from DB/current
                self.dynamic_stop_manager.highest_prices[ticker] = highest_price
                self.dynamic_stop_manager.entry_prices[ticker] = entry_price
                # If DB has stop_price, load it
                db_stop = float(position.get("stop_price") or 0.0)
                if db_stop > 0:
                    self.dynamic_stop_manager.stops[ticker] = db_stop

                new_stop = self.dynamic_stop_manager.update_stop(ticker, latest_price, df)
                new_highest = self.dynamic_stop_manager.highest_prices.get(ticker, latest_price)

                # Write back to DB
                self.pt.update_position_stop(ticker, new_stop, new_highest)

                should_exit, exit_reason = self.dynamic_stop_manager.check_exit(ticker, latest_price)
                if should_exit:
                    signals.append(
                        {
                            "ticker": ticker,
                            "action": "SELL",
                            "reason": exit_reason,
                            "confidence": 1.0,
                            "price": latest_price,
                            "quantity": quantity,
                        }
                    )
                    self.log(f"Exit Signal ({ticker}): {exit_reason}")
                    continue

                # DynamicRiskManager take profit
                try:
                    params = self.risk_manager.current_params
                    take_profit_threshold = params.get("take_profit", 0.10)
                    if pnl_pct > take_profit_threshold:
                        signals.append(
                            {
                                "ticker": ticker,
                                "action": "SELL",
                                "reason": f"利確({pnl_pct:.1%}、閾値{take_profit_threshold:.1%})",
                                "confidence": 1.0,
                                "price": latest_price,
                                "quantity": quantity,
                            }
                        )
                        self.log(f"利確判断: {ticker} ({pnl_pct:.1%})")
                        continue
                except Exception:
                    pass

            # Fallback / Additional Logic (ATR Support etc from HEAD)
            # ATRベースの下支えとトレーリング利確
            if len(df) >= 20:
                high = df["High"]
                low = df["Low"]
                close = df["Close"]

                tr1 = high - low
                tr2 = (high - close.shift()).abs()
                tr3 = (low - close.shift()).abs()
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr = tr.rolling(window=14).mean().iloc[-1]

                stop_loss_price = entry_price - (atr * 2)

                # Check for dynamic stop existing on self
                current_stop_price = 0.0
                if hasattr(self, "dynamic_stop_manager"):
                    current_stop_price = self.dynamic_stop_manager.stops.get(ticker, 0.0)

                # Only use basic ATR logic if dynamic manager didn't set a higher stop
                target_stop = max(stop_loss_price, current_stop_price)

                if latest_price <= target_stop and target_stop > 0:
                    # Avoid double signaling if dynamic stop already caught it
                    # But simple check:
                    self.log(f"🛑 {ticker}: フォールバックストップロス ({latest_price} <= {target_stop})")
                    signals.append(
                        {
                            "ticker": ticker,
                            "action": "SELL",
                            "confidence": 1.0,
                            "price": latest_price,
                            "quantity": quantity,
                            "strategy": "Fallback ATR Stop",
                            "reason": f"ATRベース損切り",
                        }
                    )
                    continue

                if unrealized_pct >= 5.0:
                    recent_high = df["High"].tail(20).max()
                    trailing_stop_price = recent_high * 0.97

                    if latest_price <= trailing_stop_price:
                        self.log(f"📈 {ticker}: トレーリングストップ発動 (利益確定 +{unrealized_pct:.1f}%)")
                        signals.append(
                            {
                                "ticker": ticker,
                                "action": "SELL",
                                "confidence": 1.0,
                                "price": latest_price,
                                "quantity": quantity,
                                "strategy": "Trailing Stop",
                                "reason": f"利益確定 (+{unrealized_pct:.1f}%)",
                            }
                        )
                        continue

                if unrealized_pct >= 20.0:
                    self.log(f"🎯 {ticker}: 目標利益達成 (+{unrealized_pct:.1f}%)")
                    signals.append(
                        {
                            "ticker": ticker,
                            "action": "SELL",
                            "confidence": 1.0,
                            "price": latest_price,
                            "quantity": quantity,
                            "strategy": "Target Profit",
                            "reason": f"目標利益達成 (+{unrealized_pct:.1f}%)",
                        }
                    )

        return signals

    def get_target_tickers(self) -> List[str]:
        """UniverseManagerから動的にグローバル銘柄を取得"""
        # 保有ポジション
        positions = self.pt.get_positions()
        pos_tickers = [str(t) for t in (positions['ticker'] if 'ticker' in positions.columns else positions.index).tolist() if t]
        
        # AIによる推薦銘柄（25銘柄+）
        ai_candidates = self.universe_manager.get_top_candidates(limit=25)
        result = list(dict.fromkeys(pos_tickers + ai_candidates))
        self.log(f'🌌 グローバル・ユニバース展開: {len(result)}銘柄をスキャンの対象に設定')
        return result

    def filter_by_market_cap(self, ticker: str, fundamentals: Optional[Dict[str, Any]]) -> bool:
        """時価総額で銘柄をフィルタリング（中小型株も許可）"""
        if not self.allow_small_mid_cap:
            return True  # フィルタなし

        if not fundamentals:
            return False

        market_cap = fundamentals.get("marketCap", 0)

        # 0円の場合はデータ取得失敗なので許可
        if market_cap == 0:
            return True

        # 10億円以上なら許可（極小型株は除外）
        # 1,000,000,000
        if market_cap >= 1_000_000_000:
            return True

        return False

    def scan_market(self) -> List[Dict[str, Any]]:
        # V4 Singularity: Self-Healing & Parameter Optimization
        self.self_healing.monitor_and_heal()
        vix = self._get_vix_level() or 20.0
        # Get simple performance summary for optimizer
        perf = {'win_rate': 0.55} # Placeholder until RealStats linked
        new_params = self.param_optimizer.optimize_parameters(perf, vix)
        self.log(f'🧬 自己最適化適用: TP={new_params["take_profit_pct"]}, SL={new_params["stop_loss_pct"]}')
        """市場をスキャンして新規シグナルを検出（グローバル分散対応）"""
        self.log("市場スキャン開始...")

        # センチメント分析
        allow_buy = True
        sentiment_penalty = 1.0
        try:
            sa = SentimentAnalyzer()
            sentiment = sa.get_market_sentiment()
            self.log(f"市場センチメント: {sentiment['label']} ({sentiment['score']:.2f})")

            score = float(sentiment.get("score", 0.0))
            if score < -0.35:
                sentiment_penalty = 0.5
            elif score < -0.15:
                sentiment_penalty = 0.75
        except Exception as e:
            self.log(f"センチメント分析エラー: {e}", "WARNING")

        # 対象銘柄（グローバル分散）
        tickers = self.get_target_tickers()
        self.log(f"対象銘柄数: {len(tickers)}")

        # データ取得（リトライ付き）
        data_map = self._fetch_data_with_retry(tickers)

        # 戦略初期化 (Phase 62: Dynamic Orchestration)
        # strategies = [] # Removed static list

        signals: List[Dict[str, Any]] = []

        for ticker in tickers:
            df = data_map.get(ticker)
            if df is None or df.empty:
                continue

            # 既にポジションを持っているかチェック
            positions = self.pt.get_positions()
            is_held = False
            if not positions.empty:
                # Check 'ticker' column or index
                if "ticker" in positions.columns:
                    is_held = ticker in positions["ticker"].values
                else:
                    is_held = ticker in positions.index

            # Phase 62: レジーム適応型戦略選択
            # VIXはscan_market冒頭で取得済み
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
                        if whale_alert['detected']:
                            self.log(f"🐋 WHALE ALERT ({ticker}): {whale_alert['action_type']} (Ratio: {whale_alert['volume_ratio']})")
                        continue

                    last_signal = sig_series.iloc[-1]

                    # BUYシグナル
                    if last_signal == 1 and not is_held and allow_buy:
                        # ファンダメンタルチェック
                        fundamentals = fetch_fundamental_data(ticker)

                        # 時価総額チェック
                        if not self.filter_by_market_cap(ticker, fundamentals):
                            self.log(f"  {ticker}: 時価総額が小さすぎるためスキップ")
                            continue

                        pe = fundamentals.get("trailingPE") if fundamentals else None

                        # PERが極端に高い場合はスキップ
                        if pe and pe > 50:
                            continue

                        latest_price = get_latest_price(df)
                        if latest_price is None or latest_price <= 0:
                            continue

                        # Kelly Criterion に基づく数量計算（センチメントで抑制）
                        try:
                            win_rate = float(self.config.get("kelly_win_rate", 0.55))
                            win_loss_ratio = float(self.config.get("kelly_win_loss_ratio", 1.5))
                            kelly_fraction = self.kelly_criterion.calculate_size(win_rate, win_loss_ratio)
                        except Exception:
                            kelly_fraction = 0.1

                        kelly_fraction = max(0.0, kelly_fraction * sentiment_penalty)
                        balance = self.pt.get_current_balance()
                        equity = float(balance.get("total_equity", 0.0))
                        cash = float(balance.get("cash", equity))
                        position_value = min(equity, cash) * kelly_fraction

                        unit_size = self.engine.get_japan_unit_size() if ticker.endswith(".T") else 1
                        quantity = int(position_value // (latest_price * unit_size)) * unit_size

                        if quantity <= 0:
                            self.log(f"  {ticker}: ケリー計算で数量0のためスキップ", "WARNING")
                            continue

                        # 地域を判定
                        if ticker in NIKKEI_225_TICKERS:
                            region = "日本"
                        elif ticker in SP500_TICKERS:
                            region = "米国"
                        else:
                            region = "欧州"

                        signals.append(
                            {
                                "ticker": ticker,
                                "action": "BUY",
                                "confidence": 0.85,
                                "price": latest_price,
                                "strategy": strategy_name,
                                "quantity": quantity,
                                "kelly_fraction": kelly_fraction,
                                "reason": f"{strategy_name}による買いシグナル（{region}）",
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
                            }
                        )
                        break

                except Exception as e:
                    self.log(f"シグナル生成エラー ({ticker}, {strategy_name}): {e}", "WARNING")

        self.log(f"検出シグナル数: {len(signals)}")
        return signals

    def execute_signals(self, signals: List[Dict[str, Any]]) -> None:
        """シグナルを実行"""
        if not signals:
            self.log("実行するシグナルなし")
            return

        # Phase 72: Risk Parity Adjustment
        # Fetch history for all tickers in signals for volatility analysis
        tickers = list(set([s["ticker"] for s in signals]))
        history = self.dm.get_stock_data_multiple(tickers, days=100)
        
        if history:
            weights = self.portfolio_manager.calculate_risk_parity_weights(tickers, history)
            for sig in signals:
                ticker = sig["ticker"]
                if ticker in weights:
                    # Adjust confidence based on risk parity weight (relative to equal weight)
                    # This scales the position size in ExecutionEngine
                    equal_weight = 1.0 / len(tickers)
                    adjustment = weights[ticker] / equal_weight
                    sig["confidence"] = sig.get("confidence", 1.0) * adjustment
                    # self.log(f"Risk Parity Adjustment ({ticker}): x{adjustment:.2f}")

        # 1. AI Veto (Qualitative Filter) & Social Analyst
        self.log("🚀 AI Review (Veto & Social Heat) 開始...")
        approved_signals = []
        for sig in signals:
            ticker = sig["ticker"]
            action = sig["action"]
            
            # AI Veto
            is_safe, veto_reason = self.ai_veto_agent.review_signal(
                ticker, action, sig["price"], sig["reason"]
            )
            
            # Social Heat (Phase 73)
            social_data = self.social_analyst.analyze_heat(ticker)
            heat = social_data.get("heat_level", 5.0)
            social_risk = social_data.get("social_risk", "LOW")
            
            if not is_safe:
                self.log(f"  ❌ VETO: {ticker} - {veto_reason}", "WARNING")
                continue
            
            if social_risk == "HIGH" and heat > 8.0:
                self.log(f"  ❌ SOCIAL VETO: {ticker} - 過熱・ハイリスク検知 (Heat: {heat})", "WARNING")
                continue

            # Apply social adjustment to confidence
            sentiment_adj = 1.0
            if social_data.get("sentiment") == "EXTREME_HYPE":
                sentiment_adj = 0.8  # Reduce size for hype
            elif social_data.get("sentiment") == "PANIC":
                sentiment_adj = 0.5  # Heavy reduction for panic
                
            sig["confidence"] *= sentiment_adj
            approved_signals.append(sig)

        if not approved_signals:
            self.log("すべてのシグナルがAIによって拒否されました。")
            return

        # 2. 最大取引数制限 (承認済みの中から選択)
        approved_signals = approved_signals[: self.max_daily_trades]

        self.log(f"{len(approved_signals)}件のシグナルを実行します")

        # 3. 価格マップ作成
        prices = {str(s["ticker"]): float(s["price"]) for s in approved_signals if s.get("price")}

        # 4. 注文実行
        self.engine.execute_orders(approved_signals, prices)

    def send_daily_report(self) -> None:
        """日次レポートを送信"""
        balance = self.pt.get_current_balance()
        daily_pnl = self.calculate_daily_pnl()

        # 今日の取引履歴
        history = self.pt.get_trade_history()
        today = datetime.date.today()

        # timestamp to datetime if not
        if not history.empty and "timestamp" in history.columns:
            if not pd.api.types.is_datetime64_any_dtype(history["timestamp"]):
                history["timestamp"] = pd.to_datetime(history["timestamp"])
            today_trades = history[history["timestamp"].dt.date == today]
        else:
            today_trades = pd.DataFrame()

        # 勝率計算
        win_rate = 0.0
        if not history.empty and "realized_pnl" in history.columns:
            wins = len(history[history["realized_pnl"] > 0])
            total = len(history[history["realized_pnl"] != 0])
            win_rate = wins / total if total > 0 else 0.0

        # シグナル情報
        signals_info = []
        if not today_trades.empty:
            for _, trade in today_trades.iterrows():
                signals_info.append(
                    {"action": trade["action"], "ticker": trade["ticker"], "name": trade.get("name", trade["ticker"])}
                )

        # サマリー送信
        summary = {
            "date": today.strftime("%Y-%m-%d"),
            "total_value": float(balance.get("total_equity", 0.0)),
            "daily_pnl": daily_pnl,
            "monthly_pnl": self.calculate_monthly_pnl(),
            "win_rate": win_rate,
            "signals": signals_info,
            "top_performer": "計算中",
            "advice": self.get_advice(daily_pnl, float(balance.get("total_equity", 0.0))),
        }

        self.notifier.send_daily_summary_rich(summary)

    def get_advice(self, daily_pnl: float, total_equity: float) -> str:
        """アドバイスを生成"""
        # シンプルなアドバイス（LLMに置き換え可能）
        if daily_pnl > 0:
            return "好調な市場環境です。トレンドフォローを継続しましょう。"
        else:
            return "市場は不安定です。リスク管理を徹底し、ポジションサイズを抑制してください。"
    
    def run_post_market_analysis(self) -> None:
        """Phase 63: Post-market autonomous feedback loop"""
        self.log("🔄 Running Post-Market Analysis...")
        
        try:
            reviewer = DailyReviewer(self.config_path)
            result = reviewer.run_daily_review()
            
            metrics = result.get("metrics", {})
            adjustments = result.get("adjustments", {})
            journal = result.get("journal", "")
            
            self.log(f"📊 Daily Metrics: Win Rate={metrics.get('win_rate', 0):.1f}%, P&L=¥{metrics.get('daily_pnl', 0):,.0f}")
            
            if adjustments and "reason" in adjustments:
                self.log(f"⚙️ Auto-Adjustment: {adjustments['reason']}")
            else:
                self.log("✅ No parameter adjustments needed")
            
            self.log(f"📝 AI Journal: {journal[:100]}...")  # Preview
            
        except Exception as e:
            self.log(f"Post-market analysis failed: {e}", "ERROR")

    def daily_routine(self, force_run: bool = False) -> None:
        """日常業務を実行"""
        self.log(f"--- 日次ルーティン開始 (Force: {force_run}) ---")
        
        # 1. 安全確認
        if not force_run:
            safe, reason = self.is_safe_to_trade()
            if not safe:
                self.log(f"取引停止: {reason}", "WARNING")
                return

        # 1.5. Phase 73: Self-Learning (Weekend Check)
        if self.learning_pipeline.should_run():
            self.log("🤖 週末：自己学習パイプラインを起動中...")
            try:
                # Use a few key tickers for optimization
                self.learning_pipeline.run_optimization(tickers=["7203.T", "9984.T", "^GSPC", "AAPL", "MSFT"])
                self.log("✅ 自己学習が完了しました。")
            except Exception as e:
                self.log(f"自己学習エラー: {e}", "WARNING")

        # 2. 市場スキャン & シグナル生成
        # scan_market内部でUniverseManagerやWhaleTrackerも動く
        self.scan_market()

        # 3. レポート送信
        self.send_daily_report()
        
        # 4. Phase 63: Post-Market Analysis & Self-Tuning
        self.run_post_market_analysis()
        
        self.log("--- 日次ルーティン完了 ---")
