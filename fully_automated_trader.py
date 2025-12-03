"""
完全自動トレーダー - 個人投資家向け

安全策を含む完全自動運用システム
"""
import sys
import os
import json
import pandas as pd
import datetime
from typing import Dict, List
import traceback
import time

# リトライロジック
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.constants import ALL_STOCKS, NIKKEI_225_TICKERS, SP500_TICKERS, STOXX50_TICKERS, MARKETS
from src.data_loader import fetch_stock_data, get_latest_price, fetch_fundamental_data, CRYPTO_PAIRS, FX_PAIRS
from src.strategies import (
    LightGBMStrategy, MLStrategy, CombinedStrategy, DividendStrategy
)
from src.paper_trader import PaperTrader
from src.execution import ExecutionEngine

# 新機能統合
from src.cache_config import install_cache
from src.smart_notifier import SmartNotifier
from src.risk_guard import RiskGuard
from src.sentiment import SentimentAnalyzer

# Phase 30-1: リアルタイム適応学習
from src.regime_detector import MarketRegimeDetector
from src.dynamic_risk_manager import DynamicRiskManager
from src.online_learning import OnlineLearner
from src.kelly_criterion import KellyCriterion
from src.dynamic_stop import DynamicStopManager


class FullyAutomatedTrader:
    """完全自動トレーダー（安全策付き）"""
    
    def __init__(self, config_path: str = "config.json"):
        """初期化"""
        # 設定読み込み
        self.config = self.load_config(config_path)
        
        # コアコンポーネント
        initial_capital = self.config.get("paper_trading", {}).get("initial_capital", 1000000)
        self.pt = PaperTrader(initial_capital=initial_capital)
        self.notifier = SmartNotifier(config_path)
        
        # リスク設定
        self.risk_config = self.config.get("auto_trading", {})
        self.max_daily_trades = self.risk_config.get("max_daily_trades", 5)
        
        # ポートフォリオ配分目標
        self.target_japan_pct = 40
        self.target_us_pct = 30
        self.target_europe_pct = 10
        self.target_crypto_pct = 10
        self.target_fx_pct = 10
        
        # 資産クラス設定
        self.asset_config = self.config.get("assets", {
            "japan_stocks": True,
            "us_stocks": True,
            "europe_stocks": True,
            "crypto": False,
            "fx": False
        })
        
        # その他設定
        self.allow_small_mid_cap = True
        self.backup_enabled = True
        self.emergency_stop_triggered = False
        
        # ログファイル
        self.log_file = "logs/auto_trader.log"
        os.makedirs("logs", exist_ok=True)
        
        # バックアップマネージャー（オプション機能としてNoneを初期化）
        self.backup_manager = None
        
        # 実行エンジン
        self.engine = ExecutionEngine(self.pt)
        
        # Phase 30-1: リアルタイム適応学習
        self.regime_detector = MarketRegimeDetector()
        self.risk_manager = DynamicRiskManager(self.regime_detector)
        self.kelly_criterion = KellyCriterion()
        self.dynamic_stop_manager = DynamicStopManager()
        self.log("Phase 30-1 & 30-3: リアルタイム適応学習・高度リスク管理モジュール初期化完了")
        
        self.log("フル自動トレーダー初期化完了")
    
    def load_config(self, config_path: str) -> dict:
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
    
    def log(self, message: str, level: str = "INFO"):
        """ログ出力"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except:
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
                pnl = today_trades['realized_pnl'].sum()
            else:
                pnl = 0.0
            
            return pnl
        except Exception as e:
            self.log(f"日次損益計算エラー: {e}", "WARNING")
            return 0.0
    
    def is_safe_to_trade(self) -> tuple[bool, str]:
        """取引が安全か確認"""
        # 1. 日次損失制限チェック
        daily_pnl = self.calculate_daily_pnl()
        balance = self.pt.get_current_balance()
        total_equity = balance['total_equity']
        
        daily_loss_pct = (daily_pnl / total_equity) * 100 if total_equity > 0 else 0
        
        if daily_loss_pct < self.risk_config.get("daily_loss_limit_pct", -5.0):
            return False, f"日次損失制限を超過: {daily_loss_pct:.2f}%"
        
        # 2. 市場ボラティリティチェック
        try:
            import yfinance as yf
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="1d")
            if not vix_data.empty:
                current_vix = vix_data['Close'].iloc[-1]
                if current_vix > self.risk_config.get("max_vix", 40.0):
                    return False, f"市場ボラティリティが高すぎます (VIX: {current_vix:.1f})"
        except:
            pass  # VIXデータ取得失敗時は続行
        
        # 3. 残高チェック
        if balance['cash'] < 10000:  # 最低1万円
            return False, "現金残高が不足しています"
        
        return True, "OK"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_data_with_retry(self, tickers: List[str]) -> Dict:
        """
        リトライロジック付きでデータ取得
        
        Args:
            tickers: 銘柄リスト
            
        Returns:
            データマップ
        """
        try:
            self.log(f"データ取得中... ({len(tickers)}銘柄)")
            data_map = fetch_stock_data(tickers, period="2y")
            self.log(f"データ取得完了: {len(data_map)}銘柄")
            return data_map
        except Exception as e:
            self.log(f"データ取得失敗（リトライします）: {e}", "WARNING")
            raise  # リトライのために例外を再throw
    
    def emergency_stop(self, reason: str):
        """
        緊急停止を実行
        
        Args:
            reason: 緊急停止の理由
        """
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
            self.notifier.send_line_notify(
                f"🚨 緊急停止が発生しました\n理由: {reason}\n\n自動トレードを停止しました。",
                token=self.config.get("notifications", {}).get("line", {}).get("token")
            )
        except:
            pass  # 通知失敗しても緊急停止は継続
    
    def evaluate_positions(self) -> List[Dict]:
        """既存ポジションを評価（損切り・利確判断）"""
        positions = self.pt.get_positions()
        actions = []
        
        if positions.empty:
            return actions
        
        for idx, position in positions.iterrows():
            try:
                ticker = position.get('ticker', idx)
                
                # 最新価格取得
                data = fetch_stock_data([ticker], period="5d")
                if not data or ticker not in data:
                    continue
                
                latest_price = get_latest_price(data[ticker])
                
                if latest_price is None:
                    continue
                
                # エントリー価格取得（avg_priceまたはentry_price）
                entry_price = position.get('entry_price') or position.get('avg_price')
                if entry_price is None:
                    self.log(f"エントリー価格が見つかりません: {ticker}", "WARNING")
                    continue
                
                # 損益率計算
                pnl_pct = (latest_price - entry_price) / entry_price
                
                # Phase 30-3: Dynamic Stop Manager Integration
                # Load persistent stop/high from DB
                current_stop = position.get('stop_price', 0)
                highest_price = position.get('highest_price', entry_price)
                
                # Update DSM state
                self.dynamic_stop_manager.highest_prices[ticker] = highest_price
                
                # Update stop based on latest data
                new_stop = self.dynamic_stop_manager.update_stop(ticker, latest_price, data[ticker])
                new_highest = self.dynamic_stop_manager.highest_prices.get(ticker, latest_price)
                
                # Save back to DB
                self.pt.update_position_stop(ticker, new_stop, new_highest)
                
                # Check exit condition
                should_exit, exit_reason = self.dynamic_stop_manager.check_exit(ticker, latest_price)
                
                if should_exit:
                    actions.append({
                        'ticker': ticker,
                        'action': 'SELL',
                        'reason': exit_reason,
                        'confidence': 1.0,
                        'price': latest_price
                    })
                    self.log(f"Exit Signal ({ticker}): {exit_reason}")
                
                # Fallback to DynamicRiskManager thresholds if DSM doesn't trigger
                # (Optional: DSM usually covers stop loss, but maybe keep take profit from DRM?)
                # For now, let's trust DSM for stops, but maybe add DRM take profit if DSM doesn't have it?
                # DSM has profit locking but maybe not target profit.
                
                # Check DRM take profit as secondary
                try:
                    params = self.risk_manager.current_params
                    take_profit_threshold = params.get('take_profit', 0.10)
                    if pnl_pct > take_profit_threshold:
                         # Only if DSM didn't trigger
                         if not should_exit:
                            actions.append({
                                'ticker': ticker,
                                'action': 'SELL',
                                'reason': f'利確（{pnl_pct:.1%}、閾値{take_profit_threshold:.1%}）',
                                'confidence': 1.0,
                                'price': latest_price
                            })
                            self.log(f"利確判断: {ticker} ({pnl_pct:.1%})")
                except:
                    pass
            
            except Exception as e:
                self.log(f"ポジション評価エラー ({ticker}): {e}", "WARNING")
        
        return actions
    
        return tickers
    
    def get_target_tickers(self) -> List[str]:
        """ポートフォリオバランスに基づいて対象銘柄を返す"""
        positions = self.pt.get_positions()
        balance = self.pt.get_current_balance()
        
        # 現在の地域別比率計算
        japan_value = 0
        us_value = 0
        europe_value = 0
        crypto_value = 0
        fx_value = 0
        
        for _, pos in positions.iterrows():
            ticker = pos['ticker']
            value = pos.get('market_value', pos['quantity'] * pos['current_price'])
            
            if ticker in CRYPTO_PAIRS:
                crypto_value += value
            elif ticker in FX_PAIRS:
                fx_value += value
            elif ticker in NIKKEI_225_TICKERS:
                japan_value += value
            elif any(ticker.startswith(t) for t in ['', '.'] if ticker in SP500_TICKERS):
                us_value += value
            else:
                europe_value += value
        
        total_value = balance['total_equity']
        
        if total_value > 0:
            japan_pct = (japan_value / total_value) * 100
            us_pct = (us_value / total_value) * 100
            europe_pct = (europe_value / total_value) * 100
            crypto_pct = (crypto_value / total_value) * 100
            fx_pct = (fx_value / total_value) * 100
        else:
            japan_pct = us_pct = europe_pct = crypto_pct = fx_pct = 0
        
        self.log(f"現在の資産配分: 日本{japan_pct:.1f}% 米国{us_pct:.1f}% 欧州{europe_pct:.1f}% Crypto{crypto_pct:.1f}% FX{fx_pct:.1f}%")
        
        # 目標との差分を計算し、優先的にスキャンする地域を決定
        tickers = []
        
        # 日本株
        if self.asset_config.get("japan_stocks", True):
            japan_count = 30 if japan_pct < self.target_japan_pct else 15
            tickers.extend(NIKKEI_225_TICKERS[:japan_count])
        
        # 米国株
        if self.asset_config.get("us_stocks", True):
            us_count = 20 if us_pct < self.target_us_pct else 10
            tickers.extend(SP500_TICKERS[:us_count])
        
        # 欧州株
        if self.asset_config.get("europe_stocks", True):
            europe_count = 10 if europe_pct < self.target_europe_pct else 5
            tickers.extend(STOXX50_TICKERS[:europe_count])
            
        # 暗号資産
        if self.asset_config.get("crypto", False):
            tickers.extend(CRYPTO_PAIRS)
            
        # FX
        if self.asset_config.get("fx", False):
            tickers.extend(FX_PAIRS)
        
        return tickers
    
    def filter_by_market_cap(self, ticker: str, fundamentals: dict) -> bool:
        """時価総額で銘柄をフィルタリング（中小型株も許可）"""
        if not self.allow_small_mid_cap:
            return True  # フィルタなし
        
        market_cap = fundamentals.get('marketCap', 0)
        
        # 0円の場合はデータ取得失敗なので許可
        if market_cap == 0:
            return True
        
        # 10億円以上なら許可（極小型株は除外）
        if market_cap >= 1_000_000_000:
            return True
        
        return False
    
    def scan_market(self) -> List[Dict]:
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
            ("ML Random Forest", MLStrategy()),
            ("Combined", CombinedStrategy()),
            ("High Dividend", DividendStrategy())  # 修正済みの安全な高配当戦略を追加
        ]
        
        signals = []
        
        for ticker in tickers:
            df = data_map.get(ticker)
            if df is None or df.empty:
                continue
            
            # 既にポジションを持っているかチェック
            positions = self.pt.get_positions()
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
                        
                        # Phase 30-3: Kelly Criterion for Position Sizing
                        # Calculate optimal size
                        balance = self.pt.get_current_balance()
                        equity = balance['total_equity']
                        cash = balance['cash']
                        
                        # Use default win rate/ratio if no history, or use actual history
                        # For now, use conservative defaults or fetch from history
                        # history = self.pt.get_trade_history()
                        # ... calculate win rate ...
                        # For simplicity, assume 55% win rate, 1.5 ratio for new signals
                        kelly_pct = self.kelly_criterion.calculate_size(win_rate=0.55, win_loss_ratio=1.5)
                        
                        # Adjust by Regime (DynamicRiskManager)
                        regime_multiplier = self.risk_manager.current_params.get('position_size', 1.0)
                        final_size_pct = kelly_pct * regime_multiplier
                        
                        # Calculate quantity
                        target_amount = equity * final_size_pct
                        target_amount = min(target_amount, cash) # Cap at cash
                        
                        # 米国株かどうか判定（ティッカーにドットがない、または特定のリストに含まれる）
                        is_us_stock = '.' not in ticker
                        
                        if is_us_stock:
                            # 米国株は1株単位
                            quantity = int(target_amount / latest_price)
                            if quantity < 1:
                                # 資金不足でも最低1株は買えるかチェック（積極的モードの場合）
                                if cash >= latest_price:
                                    quantity = 1
                                else:
                                    self.log(f"  {ticker}: 資金不足のためスキップ (必要: {latest_price:.2f}, 保有: {cash:.2f})")
                                    continue
                        else:
                            # 日本株は100株単位
                            quantity = int(target_amount / latest_price / 100) * 100
                            if quantity < 100:
                                # 資金不足でも最低100株は買えるかチェック
                                if cash >= latest_price * 100:
                                    quantity = 100
                                else:
                                    self.log(f"  {ticker}: 算出数量が少なすぎるためスキップ ({quantity})")
                                    continue

                        signals.append({
                            'ticker': ticker,
                            'action': 'BUY',
                            'confidence': 0.85,
                            'price': latest_price,
                            'quantity': quantity,
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
    
    def execute_signals(self, signals: List[Dict]):
        """シグナルを実行"""
        if not signals:
            self.log("実行するシグナルなし")
            return
        
        # 最大取引数制限
        signals = signals[:self.max_daily_trades]
        
        self.log(f"{len(signals)}件のシグナルを実行します")
        
        # 価格マップ作成
        prices = {s['ticker']: s['price'] for s in signals}
        
        # 注文実行
        self.engine.execute_orders(signals, prices)
    
    def send_daily_report(self):
        """日次レポートを送信"""
        balance = self.pt.get_current_balance()
        daily_pnl = self.calculate_daily_pnl()
        
        # 今日の取引履歴
        history = self.pt.get_trade_history()
        today = datetime.date.today()
        
        if not history.empty:
            # timestampまたはdateカラムを使用
            time_col = 'timestamp' if 'timestamp' in history.columns else 'date'
            if time_col in history.columns:
                # datetime型に変換
                history[time_col] = pd.to_datetime(history[time_col])
                today_trades = history[history[time_col].dt.date == today]
            else:
                today_trades = pd.DataFrame()
        else:
            today_trades = pd.DataFrame()
            
        # 勝率計算
        if not history.empty:
            wins = len(history[history['realized_pnl'] > 0])
            total = len(history[history['realized_pnl'] != 0])
            win_rate = wins / total if total > 0 else 0
        else:
            win_rate = 0
        
        # シグナル情報
        signals_info = []
        for _, trade in today_trades.iterrows():
            signals_info.append({
                'action': trade['action'],
                'ticker': trade['ticker'],
                'name': trade.get('name', trade['ticker'])
            })
        
        # サマリー送信
        summary = {
            'date': today.strftime('%Y-%m-%d'),
            'total_value': balance['total_equity'],
            'daily_pnl': daily_pnl,
            'monthly_pnl': 0,  # TODO: 月次損益計算
            'win_rate': win_rate,
            'signals': signals_info,
            'top_performer': '計算中',
            'advice': self.get_advice(daily_pnl, balance['total_equity'])
        }
        
        # チャート画像生成
        image_path = None
        try:
            from src.visualizer import ReportVisualizer
            visualizer = ReportVisualizer()
            
            # 資産履歴があればチャート生成
            equity_history = self.pt.get_equity_history()
            if not equity_history.empty:
                image_path = visualizer.generate_equity_chart(equity_history)
                self.log(f"チャート画像生成完了: {image_path}")
        except Exception as e:
            self.log(f"チャート画像生成失敗: {e}", "WARNING")
        
        self.notifier.send_daily_summary_rich(summary, image_path=image_path)
    
    def get_advice(self, daily_pnl: float, total_equity: float) -> str:
        """アドバイスを生成"""
        if daily_pnl < 0:
            return "⚠️ 本日はマイナスでした。リスク管理を見直しましょう。"
        elif daily_pnl > total_equity * 0.02:
            return "🎉 素晴らしい成績です！このまま継続しましょう。"
        else:
            return "✅ 通常運用を継続してください。"
    
    def daily_routine(self):
        """毎日の定期実行ルーチン"""
        self.log("=" * 60)
        self.log(f"自動トレーダー開始: {datetime.datetime.now()}")
        self.log("=" * 60)
        
        try:
            # 1. リスクチェック
            is_safe, reason = self.is_safe_to_trade()
            if not is_safe:
                self.log(f"⚠️ 取引中止: {reason}", "WARNING")
                self.notifier.send_line_notify(
                    f"⚠️ 本日の自動取引は中止されました\n理由: {reason}",
                    token=self.config.get("notifications", {}).get("line", {}).get("token")
                )
                return
            
            # 2. 既存ポジション評価
            self.log("ポジション評価開始...")
            position_actions = self.evaluate_positions()
            
            if position_actions:
                self.log(f"{len(position_actions)}件のポジション調整")
                self.execute_signals(position_actions)
            
            # 3. 新規シグナルスキャン
            new_signals = self.scan_market()
            
            # 4. 新規シグナル実行
            if new_signals:
                self.execute_signals(new_signals)
            
            # 5. 日次エクイティ更新
            self.pt.update_daily_equity()
            
            # 6. 日次レポート送信
            self.send_daily_report()
            
            self.log("自動トレーダー正常終了")
        
        except Exception as e:
            self.log(f"❌ エラー発生: {e}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            
            # エラー通知
            self.notifier.send_line_notify(
                f"❌ 自動トレーダーでエラーが発生しました\n{str(e)}",
                token=self.config.get("notifications", {}).get("line", {}).get("token")
            )


    def check_market_hours(self) -> bool:
        """
        市場取引時間中（9:00-15:00 JST）かどうかをチェック
        Returns:
            bool: 取引時間外ならTrue（実行許可）、取引時間中ならFalse（実行禁止）
        """
        now = datetime.datetime.now()
        current_time = now.time()
        
        # JST 9:00 - 15:00
        market_start = datetime.time(9, 0)
        market_end = datetime.time(15, 0)
        
        # 平日のみチェック
        if now.weekday() < 5:  # 0=Mon, 4=Fri
            if market_start <= current_time <= market_end:
                return False
        
        return True

    def daily_routine(self, force_run: bool = False):
        """日次ルーチン実行"""
        self.log("============================================================")
        self.log(f"自動トレーダー開始: {datetime.datetime.now()}")
        self.log("============================================================")
        
        # 市場時間チェック
        if not force_run and not self.check_market_hours():
            self.log("⚠️ 現在は市場取引時間中です (9:00-15:00 JST)", "WARNING")
            self.log("   不正確なデータによる誤判断を防ぐため、処理を停止します。", "WARNING")
            self.log("   強制実行する場合は force_run=True を指定してください。", "WARNING")
            return

        try:
            # 1. Phase 30-1: 市場レジーム検出とリスクパラメータ更新
            self.log("Phase 30-1: 市場レジーム検出開始...")
            try:
                # 日経平均のデータを取得してレジーム検出
                market_data = fetch_stock_data(["^N225"], period="3mo")
                if market_data and "^N225" in market_data:
                    df_market = market_data["^N225"]
                    
                    # レジーム検出
                    regime = self.regime_detector.detect_regime(df_market)
                    self.log(f"検出されたレジーム: {regime}")
                    
                    # リスクパラメータ更新
                    params = self.risk_manager.update_parameters(df_market)
                    self.log(f"リスクパラメータ更新: 損切り={params['stop_loss']*100:.2f}%, "
                           f"利確={params['take_profit']*100:.2f}%, "
                           f"ポジションサイズ={params['position_size']:.2f}")
                    
                    # レジーム情報をログ
                    regime_stats = self.regime_detector.get_regime_statistics()
                    self.log(f"レジーム統計: {regime_stats}")
                else:
                    self.log("市場データ取得失敗、デフォルトパラメータを使用", "WARNING")
            except Exception as e:
                self.log(f"レジーム検出エラー: {e}", "WARNING")
            
            # 2. リスクチェック
            is_safe, reason = self.is_safe_to_trade()
            if not is_safe:
                self.log(f"⚠️ 取引中止: {reason}", "WARNING")
                self.notifier.send_line_notify(
                    f"⚠️ 本日の自動取引は中止されました\n理由: {reason}",
                    token=self.config.get("notifications", {}).get("line", {}).get("token")
                )
                return
            
            # 3. 既存ポジション評価
            self.log("ポジション評価開始...")
            position_actions = self.evaluate_positions()
            
            if position_actions:
                self.log(f"{len(position_actions)}件のポジション調整")
                self.execute_signals(position_actions)
            
            # 4. 新規シグナルスキャン
            new_signals = self.scan_market()
            
            # 5. 新規シグナル実行
            if new_signals:
                self.execute_signals(new_signals)
            
            # 6. 日次エクイティ更新
            self.pt.update_daily_equity()
            
            # 7. 日次レポート送信（Phase 30-1のレジーム情報を含む）
            self.send_daily_report()
            
            self.log("自動トレーダー正常終了")
        
        except Exception as e:
            self.log(f"❌ エラー発生: {e}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            
            # エラー通知
            try:
                if self.notifier:
                    self.notifier.send_line_notify(
                        f"❌ 自動トレーダーでエラーが発生しました\n{str(e)}",
                        token=self.config.get("notifications", {}).get("line", {}).get("token")
                    )
            except Exception as notify_error:
                self.log(f"エラー通知の送信に失敗しました: {notify_error}", "ERROR")


def main():
    """メイン関数"""
    # キャッシュ設定
    install_cache()
    
    # 完全自動トレーダー実行
    trader = FullyAutomatedTrader()
    
    # コマンドライン引数で強制実行を確認
    force_run = "--force" in sys.argv
    trader.daily_routine(force_run=force_run)


if __name__ == "__main__":
    main()
