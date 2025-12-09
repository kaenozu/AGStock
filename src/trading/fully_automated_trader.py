"""
完全自動トレーダー - 個人投資家向け

安全策を含む完全自動運用システム
"""
import os
import pandas as pd
import datetime
from typing import Dict, List, Optional, Tuple, Any
import traceback
import logging

# リトライロジック
from tenacity import retry, stop_after_attempt, wait_exponential

# Config & Logging
# Using main branch style imports where possible
# main uses self.load_config method, HEAD uses load_config_from_yaml util. 
# We'll stick to main's method for consistency with standard refactor.
import json
from src.utils.logger import setup_logger, get_logger

from src.constants import NIKKEI_225_TICKERS, SP500_TICKERS, STOXX50_TICKERS
from src.data_loader import fetch_stock_data, get_latest_price, fetch_fundamental_data
from src.strategies import LightGBMStrategy, MLStrategy, CombinedStrategy
from src.paper_trader import PaperTrader
from src.execution import ExecutionEngine

from src.cache_config import install_cache
from src.smart_notifier import SmartNotifier
from src.sentiment import SentimentAnalyzer
from src.backup_manager import BackupManager
from src.agents.committee import InvestmentCommittee
from src.schemas import TradingDecision, AppConfig

# New Features from feat-add-position-guards
from src.regime_detector import MarketRegimeDetector
from src.dynamic_risk_manager import DynamicRiskManager
from src.kelly_criterion import KellyCriterion
from src.dynamic_stop import DynamicStopManager

# Create logger
logger = logging.getLogger(__name__)

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
        self.notifier = SmartNotifier(self.config) # Combined usage

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

        # ポートフォリオ配分目標
        self.target_japan_pct: float = 50.0
        self.target_us_pct: float = 30.0
        self.target_europe_pct: float = 20.0

        self.allow_small_mid_cap: bool = True
        self.backup_enabled: bool = True
        self.emergency_stop_triggered: bool = False
        
        # New Risk Modules (from feat-add-position-guards)
        try:
            self.regime_detector = MarketRegimeDetector()
            self.risk_manager = DynamicRiskManager(self.regime_detector)
            self.kelly_criterion = KellyCriterion()
            self.dynamic_stop_manager = DynamicStopManager()
            # self.advanced_risk = AdvancedRiskManager(self.config) # Class missing, disabled
            self.log("Phase 30-1 & 30-3: リアルタイム適応学習・高度リスク管理モジュール初期化完了")
        except Exception as e:
             self.log(f"高度リスク管理モジュールの初期化エラー: {e}", "WARNING")

        self.log("フル自動トレーダー初期化完了")

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # デフォルト設定
            return {
                "paper_trading": {"initial_capital": 1000000},
                "auto_trading": {
                    "max_daily_trades": 5,
                    "daily_loss_limit_pct": -5.0,
                    "max_vix": 40.0
                },
                "notifications": {"line": {"enabled": False}}
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
            if 'timestamp' not in history.columns:
                self.log("取引履歴にtimestampカラムがありません", "WARNING")
                return 0.0

            today = datetime.date.today()

            # timestampをdatetimeに変換
            if not pd.api.types.is_datetime64_any_dtype(history['timestamp']):
                history['timestamp'] = pd.to_datetime(history['timestamp'])

            today_trades = history[history['timestamp'].dt.date == today]

            if today_trades.empty:
                return 0.0

            # realized_pnlカラムがあれば使用
            if 'realized_pnl' in today_trades.columns:
                pnl = float(today_trades['realized_pnl'].sum())
            else:
                pnl = 0.0

            return pnl
        except Exception as e:
            self.log(f"日次損益計算エラー: {e}", "WARNING")
            return 0.0

    def is_safe_to_trade(self) -> Tuple[bool, str]:
        """取引が安全か確認"""
        # 1. 日次損失制限チェック
        daily_pnl = self.calculate_daily_pnl()
        balance = self.pt.get_current_balance()
        total_equity = float(balance.get('total_equity', 0.0))
        cash = float(balance.get('cash', 0.0))

        daily_loss_pct = (daily_pnl / total_equity) * 100 if total_equity > 0 else 0

        daily_loss_limit = float(self.risk_config.get("daily_loss_limit_pct", -5.0))
        if daily_loss_pct < daily_loss_limit:
            return False, f"日次損失制限を超過: {daily_loss_pct:.2f}%"

        # 2. 市場ボラティリティチェック
        try:
            import yfinance as yf
            vix_ticker = self.config.get("market_indices", {}).get("vix", "^VIX")
            vix = yf.Ticker(vix_ticker)
            vix_data = vix.history(period="1d")
            if not vix_data.empty:
                current_vix = float(vix_data['Close'].iloc[-1])
                max_vix = float(self.risk_config.get("max_vix", 40.0))
                if current_vix > max_vix:
                    return False, f"市場ボラティリティが高すぎます (VIX: {current_vix:.1f})"
        except Exception:
            pass  # VIXデータ取得失敗時は続行

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
                    f"🚨 緊急停止が発生しました\n理由: {reason}\n\n自動トレードを停止しました。",
                    token=token
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
        if 'ticker' in positions.columns:
            tickers = positions['ticker'].tolist()
        else:
            tickers = positions.index.tolist()
            
        tickers = [str(t) for t in tickers if t]
        
        if not tickers:
            return []

        data_map = self._fetch_data_with_retry(tickers)
        signals: List[Dict] = []

        for idx, position in positions.iterrows():
            ticker = str(position.get('ticker', idx))
            if not ticker:
                continue

            df = data_map.get(ticker)
            if df is None or df.empty:
                continue

            latest_price = get_latest_price(df)
            entry_price = float(position.get('entry_price') or position.get('avg_price') or 0.0)
            quantity = float(position.get('quantity', 0))
            if entry_price == 0 or quantity <= 0 or latest_price is None:
                self.log(f"エントリー価格または数量が不明/無効: {ticker}", "WARNING")
                continue

            pnl_pct = (latest_price - entry_price) / entry_price
            
            # Unrealized pct from DB or calc
            unrealized_pct = float(position.get('unrealized_pnl_pct', pnl_pct * 100))

            # Dynamic Stop Manager logic
            if hasattr(self, 'dynamic_stop_manager'):
                highest_price = float(position.get('highest_price') or entry_price)
                if highest_price < latest_price:
                    highest_price = latest_price # Update local known highest
                
                # Update manager internal state from DB/current
                self.dynamic_stop_manager.highest_prices[ticker] = highest_price
                self.dynamic_stop_manager.entry_prices[ticker] = entry_price
                # If DB has stop_price, load it
                db_stop = float(position.get('stop_price') or 0.0)
                if db_stop > 0:
                    self.dynamic_stop_manager.stops[ticker] = db_stop

                new_stop = self.dynamic_stop_manager.update_stop(ticker, latest_price, df)
                new_highest = self.dynamic_stop_manager.highest_prices.get(ticker, latest_price)
                
                # Write back to DB
                self.pt.update_position_stop(ticker, new_stop, new_highest)

                should_exit, exit_reason = self.dynamic_stop_manager.check_exit(ticker, latest_price)
                if should_exit:
                    signals.append({
                        'ticker': ticker,
                        'action': 'SELL',
                        'reason': exit_reason,
                        'confidence': 1.0,
                        'price': latest_price,
                        'quantity': quantity
                    })
                    self.log(f"Exit Signal ({ticker}): {exit_reason}")
                    continue

                # DynamicRiskManager take profit
                try:
                    params = self.risk_manager.current_params
                    take_profit_threshold = params.get('take_profit', 0.10)
                    if pnl_pct > take_profit_threshold:
                        signals.append({
                            'ticker': ticker,
                            'action': 'SELL',
                            'reason': f'利確({pnl_pct:.1%}、閾値{take_profit_threshold:.1%})',
                            'confidence': 1.0,
                            'price': latest_price,
                            'quantity': quantity
                        })
                        self.log(f"利確判断: {ticker} ({pnl_pct:.1%})")
                        continue
                except Exception:
                    pass
            
            # Fallback / Additional Logic (ATR Support etc from HEAD)
            # ATRベースの下支えとトレーリング利確
            if len(df) >= 20:
                high = df['High']
                low = df['Low']
                close = df['Close']

                tr1 = high - low
                tr2 = (high - close.shift()).abs()
                tr3 = (low - close.shift()).abs()
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr = tr.rolling(window=14).mean().iloc[-1]

                stop_loss_price = entry_price - (atr * 2)
                
                # Check for dynamic stop existing on self
                current_stop_price = 0.0
                if hasattr(self, 'dynamic_stop_manager'):
                     current_stop_price = self.dynamic_stop_manager.stops.get(ticker, 0.0)
                
                # Only use basic ATR logic if dynamic manager didn't set a higher stop
                target_stop = max(stop_loss_price, current_stop_price)

                if latest_price <= target_stop and target_stop > 0:
                     # Avoid double signaling if dynamic stop already caught it
                     # But simple check:
                     self.log(f"🛑 {ticker}: フォールバックストップロス ({latest_price} <= {target_stop})")
                     signals.append({
                        'ticker': ticker,
                        'action': 'SELL',
                        'confidence': 1.0,
                        'price': latest_price,
                        'quantity': quantity,
                        'strategy': 'Fallback ATR Stop',
                        'reason': f'ATRベース損切り'
                    })
                     continue

                if unrealized_pct >= 5.0:
                    recent_high = df['High'].tail(20).max()
                    trailing_stop_price = recent_high * 0.97

                    if latest_price <= trailing_stop_price:
                        self.log(f"📈 {ticker}: トレーリングストップ発動 (利益確定 +{unrealized_pct:.1f}%)")
                        signals.append({
                            'ticker': ticker,
                            'action': 'SELL',
                            'confidence': 1.0,
                            'price': latest_price,
                            'quantity': quantity,
                            'strategy': 'Trailing Stop',
                            'reason': f'利益確定 (+{unrealized_pct:.1f}%)'
                        })
                        continue

                if unrealized_pct >= 20.0:
                    self.log(f"🎯 {ticker}: 目標利益達成 (+{unrealized_pct:.1f}%)")
                    signals.append({
                        'ticker': ticker,
                        'action': 'SELL',
                        'confidence': 1.0,
                        'price': latest_price,
                        'quantity': quantity,
                        'strategy': 'Target Profit',
                        'reason': f'目標利益達成 (+{unrealized_pct:.1f}%)'
                    })

        return signals

    def get_target_tickers(self) -> List[str]:
        """ポートフォリオバランスに基づいて対象銘柄を返す"""
        positions = self.pt.get_positions()
        balance = self.pt.get_current_balance()

        # 現在の地域別比率計算
        japan_value = 0.0
        us_value = 0.0
        europe_value = 0.0

        for idx, pos in positions.iterrows():
            ticker = str(pos.get('ticker', idx))
            val = pos.get('market_value')
            if val is None:
                val = float(pos['quantity']) * float(pos['current_price'])
            else:
                val = float(val)

            if ticker in NIKKEI_225_TICKERS:
                japan_value += val
            elif any(ticker.startswith(t) for t in ['', '.'] if ticker in SP500_TICKERS):
                us_value += val
            else:
                europe_value += val

        total_value = float(balance.get('total_equity', 0.0))

        if total_value > 0:
            japan_pct = (japan_value / total_value) * 100
            us_pct = (us_value / total_value) * 100
            europe_pct = (europe_value / total_value) * 100
        else:
            japan_pct = us_pct = europe_pct = 0.0

        self.log(f"現在の地域配分: 日本{japan_pct:.1f}% 米国{us_pct:.1f}% 欧州{europe_pct:.1f}%")

        # 目標との差分を計算し、優先的にスキャンする地域を決定
        tickers: List[str] = []

        # 日本株（基本常にスキャン、ただし割合を抑える）
        japan_count = 30 if japan_pct < self.target_japan_pct else 15
        tickers.extend(NIKKEI_225_TICKERS[:japan_count])

        # 米国株（不足している場合は多めに）
        us_count = 20 if us_pct < self.target_us_pct else 10
        tickers.extend(SP500_TICKERS[:us_count])

        # 欧州株（不足している場合は追加）
        europe_count = 10 if europe_pct < self.target_europe_pct else 5
        tickers.extend(STOXX50_TICKERS[:europe_count])

        return tickers

    def filter_by_market_cap(self, ticker: str, fundamentals: Optional[Dict[str, Any]]) -> bool:
        """時価総額で銘柄をフィルタリング（中小型株も許可）"""
        if not self.allow_small_mid_cap:
            return True  # フィルタなし
            
        if not fundamentals:
            return False

        market_cap = fundamentals.get('marketCap', 0)

        # 0円の場合はデータ取得失敗なので許可
        if market_cap == 0:
            return True

        # 10億円以上なら許可（極小型株は除外）
        # 1,000,000,000
        if market_cap >= 1_000_000_000:
            return True

        return False

    def scan_market(self) -> List[Dict[str, Any]]:
        """市場をスキャンして新規シグナルを検出（グローバル分散対応）"""
        self.log("市場スキャン開始...")

        # センチメント分析
        try:
            sa = SentimentAnalyzer()
            sentiment = sa.get_market_sentiment()
            self.log(f"市場センチメント: {sentiment['label']} ({sentiment['score']:.2f})")

            # ネガティブセンチメント時はBUYを抑制
            allow_buy = sentiment['score'] >= -0.2
        except Exception as e:
            self.log(f"センチメント分析エラー: {e}", "WARNING")
            allow_buy = True

        # 対象銘柄（グローバル分散）
        tickers = self.get_target_tickers()
        self.log(f"対象銘柄数: {len(tickers)}")

        # データ取得（リトライ付き）
        data_map = self._fetch_data_with_retry(tickers)

        # 戦略初期化
        strategies = [
            ("LightGBM", LightGBMStrategy(lookback_days=365, threshold=0.005)),
            ("ML Random Forest", MLStrategy()),  # デフォルト引数を使用
            ("Combined", CombinedStrategy())
        ]

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
                 if 'ticker' in positions.columns:
                     is_held = ticker in positions['ticker'].values
                 else:
                     is_held = ticker in positions.index

            # 各戦略でシグナル生成
            for strategy_name, strategy in strategies:
                try:
                    sig_series = strategy.generate_signals(df)

                    if sig_series.empty:
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

                        pe = fundamentals.get('trailingPE') if fundamentals else None

                        # PERが極端に高い場合はスキップ
                        if pe and pe > 50:
                            continue

                        latest_price = get_latest_price(df)

                        # 地域を判定
                        if ticker in NIKKEI_225_TICKERS:
                            region = '日本'
                        elif ticker in SP500_TICKERS:
                            region = '米国'
                        else:
                            region = '欧州'

                        signals.append({
                            'ticker': ticker,
                            'action': 'BUY',
                            'confidence': 0.85,
                            'price': latest_price,
                            'strategy': strategy_name,
                            'reason': f'{strategy_name}による買いシグナル（{region}）'
                        })
                        break  # 1銘柄につき1シグナル

                    # SELLシグナル（保有中の場合）
                    elif last_signal == -1 and is_held:
                        latest_price = get_latest_price(df)

                        signals.append({
                            'ticker': ticker,
                            'action': 'SELL',
                            'confidence': 0.85,
                            'price': latest_price,
                            'strategy': strategy_name,
                            'reason': f'{strategy_name}による売りシグナル'
                        })
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

        # 最大取引数制限
        signals = signals[:self.max_daily_trades]

        self.log(f"{len(signals)}件のシグナルを実行します")

        # 価格マップ作成
        prices = {str(s['ticker']): float(s['price']) for s in signals if s.get('price')}

        # 注文実行
        self.engine.execute_orders(signals, prices)

    def send_daily_report(self) -> None:
        """日次レポートを送信"""
        balance = self.pt.get_current_balance()
        daily_pnl = self.calculate_daily_pnl()

        # 今日の取引履歴
        history = self.pt.get_trade_history()
        today = datetime.date.today()
        
        # timestamp to datetime if not
        if not history.empty and 'timestamp' in history.columns:
            if not pd.api.types.is_datetime64_any_dtype(history['timestamp']):
                history['timestamp'] = pd.to_datetime(history['timestamp'])
            today_trades = history[history['timestamp'].dt.date == today]
        else:
             today_trades = pd.DataFrame()

        # 勝率計算
        win_rate = 0.0
        if not history.empty and 'realized_pnl' in history.columns:
            wins = len(history[history['realized_pnl'] > 0])
            total = len(history[history['realized_pnl'] != 0])
            win_rate = wins / total if total > 0 else 0.0

        # シグナル情報
        signals_info = []
        if not today_trades.empty:
            for _, trade in today_trades.iterrows():
                signals_info.append({
                    'action': trade['action'],
                    'ticker': trade['ticker'],
                    'name': trade.get('name', trade['ticker'])
                })

        # サマリー送信
        summary = {
            'date': today.strftime('%Y-%m-%d'),
            'total_value': float(balance.get('total_equity', 0.0)),
            'daily_pnl': daily_pnl,
            'monthly_pnl': 0,  # TODO: 月次損益計算
            'win_rate': win_rate,
            'signals': signals_info,
            'top_performer': '計算中',
            'advice': self.get_advice(daily_pnl, float(balance.get('total_equity', 0.0)))
        }

        self.notifier.send_daily_summary_rich(summary)

    def get_advice(self, daily_pnl: float, total_equity: float) -> str:
        """アドバイスを生成"""
        if daily_pnl < 0:
            return "⚠️ 本日はマイナスでした。リスク管理を見直しましょう。"
        elif daily_pnl > 0:
            return "✅ 素晴らしい結果です！この調子でいきましょう。"
        else:
            return "⏸️ 本日は取引なしか、損益なしでした。"
