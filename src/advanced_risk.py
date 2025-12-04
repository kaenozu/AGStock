"""
高度なリスク管理機能
- ドローダウン保護
- 市場急落時の緊急停止
- 銘柄相関チェック
"""
import pandas as pd
import numpy as np
from typing import Tuple, List
import yfinance as yf
from src.data_loader import fetch_stock_data


class AdvancedRiskManager:
    """高度なリスク管理クラス"""
    
    def __init__(self, config: dict):
        self.config = config
        self.max_daily_loss_pct = config.get("auto_trading", {}).get("max_daily_loss_pct", -3.0)
        self.market_crash_threshold = config.get("auto_trading", {}).get("market_crash_threshold", -3.0)
        self.max_correlation = config.get("auto_trading", {}).get("max_correlation", 0.7)
    
    def check_drawdown_protection(self, paper_trader, logger) -> Tuple[bool, str, List[dict]]:
        """
        ドローダウン保護: 1日の最大損失を制限
        
        Returns:
            (is_safe, reason, emergency_signals): 
            - is_safe: 取引継続可能ならTrue
            - reason: 理由
            - emergency_signals: 緊急決済が必要な場合のシグナルリスト
        """
        try:
            # 資産履歴から本日の損益を計算
            equity_history = paper_trader.get_equity_history()
            
            if equity_history.empty or len(equity_history) < 2:
                return True, "履歴不足（初日）", []
            
            # 今日と昨日の資産を比較
            today_equity = equity_history.iloc[-1]['total_equity']
            yesterday_equity = equity_history.iloc[-2]['total_equity']
            initial_capital = paper_trader.initial_capital
            
            # 本日の損失率
            daily_pnl = today_equity - yesterday_equity
            daily_loss_pct = (daily_pnl / initial_capital) * 100
            
            logger(f"本日の損益: {daily_pnl:,.0f}円 ({daily_loss_pct:+.2f}%)")
            
            # 制限値チェック
            if daily_loss_pct < self.max_daily_loss_pct:
                logger(f"🚨 ドローダウン保護発動: {daily_loss_pct:.2f}% < {self.max_daily_loss_pct}%", "WARNING")
                
                # 全ポジション緊急決済
                positions = paper_trader.get_positions()
                emergency_signals = []
                
                if not positions.empty:
                    for ticker in positions.index:
                        pos = positions.loc[ticker]
                        emergency_signals.append({
                            'ticker': ticker,
                            'action': 'SELL',
                            'confidence': 1.0,
                            'price': pos.get('current_price', 0),
                            'quantity': pos.get('quantity', 0),
                            'strategy': 'Drawdown Protection',
                            'reason': f'緊急損切り（本日損失: {daily_loss_pct:.2f}%）'
                        })
                
                return False, f"本日の損失が制限値を超過 ({daily_loss_pct:.2f}%)", emergency_signals
            
            return True, "ドローダウン保護: OK", []
            
        except Exception as e:
            logger(f"ドローダウン保護チェックエラー: {e}", "WARNING")
            return True, "チェックエラー（継続）", []
    
    def check_market_crash(self, logger) -> Tuple[bool, str]:
        """
        市場急落時の緊急停止
        日経平均またはS&P500が大幅下落している場合、新規BUYを停止
        
        Returns:
            (allow_buy, reason): BUY可能ならTrue
        """
        try:
            # 日経平均の当日変動率をチェック
            nikkei = yf.Ticker("^N225")
            nikkei_data = nikkei.history(period="5d")
            
            if not nikkei_data.empty and len(nikkei_data) >= 2:
                today_close = nikkei_data['Close'].iloc[-1]
                yesterday_close = nikkei_data['Close'].iloc[-2]
                nikkei_change_pct = ((today_close - yesterday_close) / yesterday_close) * 100
                
                logger(f"日経平均変動率: {nikkei_change_pct:+.2f}%")
                
                if nikkei_change_pct < self.market_crash_threshold:
                    return False, f"日経平均が急落中 ({nikkei_change_pct:.2f}%)"
            
            # S&P500の当日変動率をチェック
            sp500 = yf.Ticker("^GSPC")
            sp500_data = sp500.history(period="5d")
            
            if not sp500_data.empty and len(sp500_data) >= 2:
                today_close = sp500_data['Close'].iloc[-1]
                yesterday_close = sp500_data['Close'].iloc[-2]
                sp500_change_pct = ((today_close - yesterday_close) / yesterday_close) * 100
                
                logger(f"S&P500変動率: {sp500_change_pct:+.2f}%")
                
                if sp500_change_pct < self.market_crash_threshold:
                    return False, f"S&P500が急落中 ({sp500_change_pct:.2f}%)"
            
            return True, "市場環境: 正常"
            
        except Exception as e:
            logger(f"市場急落チェックエラー: {e}", "WARNING")
            # エラー時は保守的に取引を許可
            return True, "市場チェックエラー（継続）"
    
    def check_correlation(self, new_ticker: str, existing_tickers: List[str], logger) -> Tuple[bool, str]:
        """
        銘柄相関チェック: 既存ポジションと相関が高すぎる銘柄を避ける
        
        Args:
            new_ticker: 新規購入候補の銘柄
            existing_tickers: 既存保有銘柄のリスト
            logger: ログ関数
        
        Returns:
            (allow_buy, reason): 購入可能ならTrue
        """
        if not existing_tickers:
            return True, "既存ポジションなし"
        
        try:
            # 新規銘柄と既存銘柄のデータを取得
            all_tickers = [new_ticker] + existing_tickers
            data_map = fetch_stock_data(all_tickers, period="3mo")
            
            if new_ticker not in data_map:
                logger(f"  {new_ticker}: データ取得失敗（相関チェックスキップ）", "WARNING")
                return True, "データ不足"
            
            # 新規銘柄のリターンを計算
            new_df = data_map[new_ticker]
            if new_df.empty or len(new_df) < 20:
                return True, "データ不足"
            
            new_returns = new_df['Close'].pct_change().dropna()
            
            # 既存銘柄との相関を計算
            for existing_ticker in existing_tickers:
                if existing_ticker not in data_map:
                    continue
                
                existing_df = data_map[existing_ticker]
                if existing_df.empty or len(existing_df) < 20:
                    continue
                
                existing_returns = existing_df['Close'].pct_change().dropna()
                
                # 共通の日付でアライン
                aligned = pd.concat([new_returns, existing_returns], axis=1, join='inner')
                aligned.columns = ['new', 'existing']
                
                if len(aligned) < 20:
                    continue
                
                # 相関係数を計算
                correlation = aligned['new'].corr(aligned['existing'])
                
                logger(f"  相関チェック: {new_ticker} vs {existing_ticker} = {correlation:.2f}")
                
                # 相関が高すぎる場合は拒否
                if abs(correlation) > self.max_correlation:
                    return False, f"{existing_ticker}と相関が高すぎる ({correlation:.2f})"
            
            return True, "相関チェック: OK"
            
        except Exception as e:
            logger(f"  相関チェックエラー ({new_ticker}): {e}", "WARNING")
            # エラー時は保守的に許可
            return True, "相関チェックエラー（継続）"
    
    def check_prediction_deterioration(self, paper_trader, logger) -> List[dict]:
        """
        予測悪化チェック: 購入後に予測が悪化した銘柄を早期売却
        
        購入時は+3%の上昇予測だったのに、今日-2%以下になった場合
        → 即座に売却して損失を最小限に
        
        Returns:
            list: 売却シグナルのリスト
        """
        sell_signals = []
        
        try:
            from src.future_predictor import FuturePredictor
            
            positions = paper_trader.get_positions()
            if positions.empty:
                return []
            
            predictor = FuturePredictor()
            
            for ticker in positions.index:
                try:
                    # データ取得
                    data_map = fetch_stock_data([ticker], period="2y")
                    df = data_map.get(ticker)
                    
                    if df is None or df.empty:
                        continue
                    
                    # 予測実行
                    result = predictor.predict_trajectory(df, days_ahead=5)
                    
                    if "error" in result:
                        logger(f"  {ticker}: 予測エラー - {result['error']}")
                        continue
                    
                    predicted_change = result['change_pct']
                    trend = result['trend']
                    
                    # 予測が悪化している場合（-2%以下）
                    if predicted_change < -2.0:
                        pos = positions.loc[ticker]
                        current_price = pos.get('current_price', 0)
                        quantity = pos.get('quantity', 0)
                        entry_price = pos.get('average_price', current_price)
                        unrealized_pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                        
                        logger(f"⚠️ {ticker}: 予測悪化 ({predicted_change:+.1f}%) - 早期売却推奨", "WARNING")
                        
                        sell_signals.append({
                            'ticker': ticker,
                            'action': 'SELL',
                            'confidence': 0.8,
                            'price': current_price,
                            'quantity': quantity,
                            'strategy': 'Prediction Deterioration',
                            'reason': f'予測悪化（{predicted_change:+.1f}%）、含み損益: {unrealized_pnl_pct:+.1f}%'
                        })
                    else:
                        logger(f"  {ticker}: 予測 {predicted_change:+.1f}% ({trend}) - 保持")
                        
                except Exception as e:
                    logger(f"  {ticker}: 予測チェックエラー - {e}", "WARNING")
                    continue
            
            return sell_signals
            
        except Exception as e:
            logger(f"予測悪化チェック全体エラー: {e}", "WARNING")
            return []
