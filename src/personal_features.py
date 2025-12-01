"""
個人利用便利機能モジュール

ワンクリックで使える便利機能を提供
"""
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import streamlit as st

from src.paper_trader import PaperTrader
from src.data_loader import fetch_stock_data
from src.logging_config import get_logger

logger = get_logger(__name__)


class QuickActions:
    """ワンクリックアクション"""
    
    def __init__(self):
        self.pt = PaperTrader()
        self.config_file = "quick_settings.json"
        self.favorites = self._load_favorites()
    
    def _load_favorites(self) -> List[str]:
        """お気に入り銘柄を読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('favorites', [])
        except FileNotFoundError:
            return []
    
    def _save_favorites(self):
        """お気に入り銘柄を保存"""
        try:
            config = {'favorites': self.favorites}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving favorites: {e}")
    
    def add_favorite(self, ticker: str):
        """お気に入りに追加"""
        if ticker not in self.favorites:
            self.favorites.append(ticker)
            self._save_favorites()
            return True
        return False
    
    def remove_favorite(self, ticker: str):
        """お気に入りから削除"""
        if ticker in self.favorites:
            self.favorites.remove(ticker)
            self._save_favorites()
            return True
        return False
    
    def quick_buy(self, ticker: str, amount: float) -> bool:
        """ワンクリック購入"""
        try:
            # 現在価格取得
            data = fetch_stock_data([ticker], period="1d")
            if ticker not in data or data[ticker].empty:
                logger.error(f"Failed to get price for {ticker}")
                return False
            
            current_price = data[ticker]['Close'].iloc[-1]
            quantity = int(amount / current_price)
            
            if quantity <= 0:
                logger.error(f"Insufficient amount: {amount}")
                return False
            
            # 購入実行
            self.pt.execute_trade(
                ticker, 
                "BUY", 
                quantity, 
                current_price,
                reason="Quick buy"
            )
            
            logger.info(f"Quick buy: {quantity} shares of {ticker} at {current_price}")
            return True
            
        except Exception as e:
            logger.error(f"Quick buy failed: {e}")
            return False
    
    def quick_sell_all(self, ticker: str) -> bool:
        """ワンクリック全売却"""
        try:
            positions = self.pt.get_positions()
            
            if positions.empty:
                return False
            
            position = positions[positions['ticker'] == ticker]
            if position.empty:
                logger.warning(f"No position for {ticker}")
                return False
            
            quantity = position.iloc[0]['quantity']
            current_price = position.iloc[0]['current_price']
            
            # 売却実行
            self.pt.execute_trade(
                ticker,
                "SELL",
                quantity,
                current_price,
                reason="Quick sell all"
            )
            
            logger.info(f"Quick sell: {quantity} shares of {ticker} at {current_price}")
            return True
            
        except Exception as e:
            logger.error(f"Quick sell failed: {e}")
            return False
    
    def get_daily_summary(self) -> Dict:
        """今日のサマリー"""
        try:
            balance = self.pt.get_balance()
            positions = self.pt.get_positions()
            history = self.pt.get_trade_history()
            
            # 今日の取引
            today = datetime.now().date()
            today_trades = history[
                pd.to_datetime(history['timestamp']).dt.date == today
            ] if not history.empty else pd.DataFrame()
            
            # 今日の損益
            today_pnl = today_trades['pnl'].sum() if not today_trades.empty else 0
            
            return {
                'balance': balance,
                'positions_count': len(positions),
                'total_value': balance + positions['value'].sum() if not positions.empty else balance,
                'today_trades': len(today_trades),
                'today_pnl': today_pnl,
                'positions': positions
            }
            
        except Exception as e:
            logger.error(f"Error getting daily summary: {e}")
            return {}


class AutoAlerts:
    """自動アラート機能"""
    
    def __init__(self):
        self.alerts_file = "auto_alerts.json"
        self.alerts = self._load_alerts()
    
    def _load_alerts(self) -> List[Dict]:
        """アラート設定を読み込み"""
        try:
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _save_alerts(self):
        """アラート設定を保存"""
        try:
            with open(self.alerts_file, 'w', encoding='utf-8') as f:
                json.dump(self.alerts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving alerts: {e}")
    
    def add_price_alert(self, ticker: str, target_price: float, condition: str):
        """価格アラート追加"""
        alert = {
            'type': 'price',
            'ticker': ticker,
            'target_price': target_price,
            'condition': condition,  # 'above' or 'below'
            'created_at': datetime.now().isoformat()
        }
        self.alerts.append(alert)
        self._save_alerts()
    
    def check_alerts(self) -> List[Dict]:
        """アラートをチェック"""
        triggered = []
        
        for alert in self.alerts:
            if alert['type'] == 'price':
                ticker = alert['ticker']
                
                # 現在価格取得
                data = fetch_stock_data([ticker], period="1d")
                if ticker not in data or data[ticker].empty:
                    continue
                
                current_price = data[ticker]['Close'].iloc[-1]
                target = alert['target_price']
                condition = alert['condition']
                
                # 条件チェック
                if (condition == 'above' and current_price > target) or \
                   (condition == 'below' and current_price < target):
                    triggered.append({
                        **alert,
                        'current_price': current_price,
                        'triggered_at': datetime.now().isoformat()
                    })
        
        return triggered


class SmartDashboard:
    """スマートダッシュボード"""
    
    @staticmethod
    def render_quick_panel():
        """クイックアクションパネル"""
        st.subheader("⚡ クイックアクション")
        
        qa = QuickActions()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**お気に入り銘柄**")
            if qa.favorites:
                for ticker in qa.favorites:
                    st.write(f"• {ticker}")
            else:
                st.info("お気に入りなし")
        
        with col2:
            st.write("**ワンクリック購入**")
            ticker = st.text_input("銘柄コード", key="quick_buy_ticker")
            amount = st.number_input("金額（円）", value=10000, step=1000, key="quick_buy_amount")
            
            if st.button("💰 購入", type="primary", key="quick_buy_btn"):
                if qa.quick_buy(ticker, amount):
                    st.success(f"{ticker}を購入しました")
                else:
                    st.error("購入に失敗しました")
        
        with col3:
            st.write("**ワンクリック売却**")
            positions = qa.pt.get_positions()
            
            if not positions.empty:
                sell_ticker = st.selectbox(
                    "銘柄選択",
                    positions['ticker'].tolist(),
                    key="quick_sell_ticker"
                )
                
                if st.button("💸 全売却", type="secondary", key="quick_sell_btn"):
                    if qa.quick_sell_all(sell_ticker):
                        st.success(f"{sell_ticker}を売却しました")
                    else:
                        st.error("売却に失敗しました")
            else:
                st.info("保有ポジションなし")
    
    @staticmethod
    def render_daily_summary():
        """今日のサマリー"""
        st.subheader("📊 今日のサマリー")
        
        qa = QuickActions()
        summary = qa.get_daily_summary()
        
        if summary:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("残高", f"¥{summary['balance']:,.0f}")
            
            with col2:
                st.metric("保有銘柄数", summary['positions_count'])
            
            with col3:
                st.metric("総資産", f"¥{summary['total_value']:,.0f}")
            
            with col4:
                pnl_color = "normal" if summary['today_pnl'] >= 0 else "inverse"
                st.metric(
                    "今日の損益",
                    f"¥{summary['today_pnl']:,.0f}",
                    delta=f"{summary['today_pnl']:+,.0f}",
                    delta_color=pnl_color
                )
    
    @staticmethod
    def render_favorites_manager():
        """お気に入り管理"""
        st.subheader("⭐ お気に入り管理")
        
        qa = QuickActions()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**追加**")
            new_ticker = st.text_input("銘柄コード", key="add_fav")
            if st.button("追加", key="add_fav_btn"):
                if qa.add_favorite(new_ticker):
                    st.success(f"{new_ticker}を追加しました")
                    st.rerun()
                else:
                    st.warning("既に登録されています")
        
        with col2:
            st.write("**削除**")
            if qa.favorites:
                remove_ticker = st.selectbox(
                    "銘柄選択",
                    qa.favorites,
                    key="remove_fav"
                )
                if st.button("削除", key="remove_fav_btn"):
                    if qa.remove_favorite(remove_ticker):
                        st.success(f"{remove_ticker}を削除しました")
                        st.rerun()
            else:
                st.info("お気に入りなし")


if __name__ == "__main__":
    # テスト
    qa = QuickActions()
    
    # お気に入り追加
    qa.add_favorite("7203.T")
    qa.add_favorite("6758.T")
    
    print(f"Favorites: {qa.favorites}")
    
    # サマリー取得
    summary = qa.get_daily_summary()
    print(f"Summary: {summary}")
