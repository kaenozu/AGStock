"""
高度なリスク管理機能

- ドローダウン保護
- 市場急落検知
- 銘柄間相関チェック
"""
import logging
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
import yfinance as yf

from src.data_loader import fetch_stock_data

logger = logging.getLogger(__name__)


class AdvancedRiskManager:
    """高度なリスク管理マネージャー"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初期化
        
        Args:
            config: 設定辞書
        """
        auto_config = config.get("auto_trading", {})
        self.max_daily_loss_pct = auto_config.get("max_daily_loss_pct", -3.0)
        self.market_crash_threshold = auto_config.get("market_crash_threshold", -3.0)
        self.max_correlation = auto_config.get("max_correlation", 0.7)
    
    def check_drawdown_protection(
        self, 
        paper_trader, 
        log_func
    ) -> Tuple[bool, str, List[Dict]]:
        """
        ドローダウン保護チェック
        
        Args:
            paper_trader: PaperTraderインスタンス
            log_func: ログ関数
        
        Returns:
            (is_safe, reason, emergency_signals)
            - is_safe: 安全であればTrue
            - reason: 理由文字列
            - emergency_signals: 緊急決済シグナルのリスト
        """
        try:
            equity_history = paper_trader.get_equity_history()
            
            if equity_history is None or equity_history.empty or len(equity_history) < 2:
                return True, "履歴不足でチェックスキップ", []
            
            # 前日と当日の資産額を取得
            previous_equity = equity_history['total_equity'].iloc[-2]
            current_equity = equity_history['total_equity'].iloc[-1]
            
            # 日次損益率を計算
            daily_return_pct = ((current_equity - previous_equity) / previous_equity) * 100
            
            if daily_return_pct < self.max_daily_loss_pct:
                # 日次損失が限度を超過
                log_func(f"⚠️ ドローダウン保護発動: 日次損失 {daily_return_pct:.2f}%")
                
                # 全ポジションの緊急決済シグナルを生成
                positions = paper_trader.get_positions()
                emergency_signals = []
                
                if not positions.empty:
                    for ticker in positions.index:
                        pos = positions.loc[ticker]
                        quantity = int(pos.get('quantity', 0))
                        current_price = float(pos.get('current_price', 0))
                        
                        if quantity > 0:
                            emergency_signals.append({
                                'ticker': ticker,
                                'action': 'SELL',
                                'quantity': quantity,
                                'price': current_price,
                                'strategy': 'Drawdown Protection'
                            })
                
                reason = f"日次損失が限度を超過 ({daily_return_pct:.2f}% < {self.max_daily_loss_pct}%)"
                return False, reason, emergency_signals
            
            return True, f"OK: 日次損益 {daily_return_pct:+.2f}%", []
            
        except Exception as e:
            logger.error(f"ドローダウンチェックエラー: {e}")
            return True, f"チェックエラー: {e}", []
    
    def check_market_crash(self, log_func) -> Tuple[bool, str]:
        """
        市場急落検知
        
        Args:
            log_func: ログ関数
        
        Returns:
            (allow_buy, reason)
            - allow_buy: 買いを許可するか
            - reason: 理由文字列
        """
        try:
            # 日経平均とS&P500のデータを取得
            nikkei = yf.Ticker("^N225")
            sp500 = yf.Ticker("^GSPC")
            
            nikkei_data = nikkei.history(period="5d")
            sp500_data = sp500.history(period="5d")
            
            # 日経平均のチェック
            if len(nikkei_data) >= 2:
                nikkei_prev = nikkei_data['Close'].iloc[-2]
                nikkei_curr = nikkei_data['Close'].iloc[-1]
                nikkei_change = ((nikkei_curr - nikkei_prev) / nikkei_prev) * 100
                
                if nikkei_change < self.market_crash_threshold:
                    reason = f"日経平均が急落中 ({nikkei_change:.2f}%)"
                    log_func(f"⚠️ {reason}")
                    return False, reason
            
            # S&P500のチェック
            if len(sp500_data) >= 2:
                sp500_prev = sp500_data['Close'].iloc[-2]
                sp500_curr = sp500_data['Close'].iloc[-1]
                sp500_change = ((sp500_curr - sp500_prev) / sp500_prev) * 100
                
                if sp500_change < self.market_crash_threshold:
                    reason = f"S&P500が急落中 ({sp500_change:.2f}%)"
                    log_func(f"⚠️ {reason}")
                    return False, reason
            
            return True, "市場は正常"
            
        except Exception as e:
            logger.error(f"市場チェックエラー: {e}")
            # エラー時は保守的に許可
            return True, f"チェックエラー: {e}"
    
    def check_correlation(
        self, 
        new_ticker: str, 
        existing_tickers: List[str], 
        log_func
    ) -> Tuple[bool, str]:
        """
        銘柄間相関チェック
        
        Args:
            new_ticker: 新規購入候補の銘柄
            existing_tickers: 既存ポジションの銘柄リスト
            log_func: ログ関数
        
        Returns:
            (allow, reason)
            - allow: 購入を許可するか
            - reason: 理由文字列
        """
        if not existing_tickers:
            return True, "既存ポジションなし"
        
        try:
            # 全銘柄のデータを取得
            all_tickers = [new_ticker] + existing_tickers
            data = fetch_stock_data(all_tickers, period="3mo")
            
            if not data or new_ticker not in data:
                return True, "データ不足のためスキップ"
            
            new_ticker_prices = data[new_ticker]['Close']
            
            for existing_ticker in existing_tickers:
                if existing_ticker not in data:
                    continue
                
                existing_prices = data[existing_ticker]['Close']
                
                # インデックスを揃える
                combined = pd.concat([new_ticker_prices, existing_prices], axis=1).dropna()
                if len(combined) < 20:
                    continue
                
                # 相関係数を計算
                correlation = combined.iloc[:, 0].corr(combined.iloc[:, 1])
                
                if abs(correlation) > self.max_correlation:
                    reason = f"{new_ticker}と{existing_ticker}の相関が高すぎる ({correlation:.2f})"
                    log_func(f"⚠️ {reason}")
                    return False, reason
            
            return True, "相関チェックOK"
            
        except Exception as e:
            logger.error(f"相関チェックエラー: {e}")
            return True, f"エラーのためスキップ: {e}"
