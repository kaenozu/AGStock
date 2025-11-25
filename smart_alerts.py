"""
スマートアラートシステム - 重要なイベントのみ通知

条件ベースで重要度を判定し、必要な時だけ通知
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict
import yfinance as yf

from src.paper_trader import PaperTrader
from src.smart_notifier import SmartNotifier
from src.data_loader import fetch_stock_data, get_latest_price


class SmartAlerts:
    """スマートアラートシステム"""
    
    def __init__(self, config_path: str = "config.json"):
        self.pt = PaperTrader()
        self.notifier = SmartNotifier(config_path)
        self.config = self._load_config(config_path)
        self.alert_config = self.config.get("alerts", {})
    
    def _load_config(self, path: str) -> dict:
        """設定読み込み"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
                
                # デフォルトアラート設定
                if "alerts" not in config:
                    config["alerts"] = {
                        "daily_loss_threshold": -3.0,  # -3%
                        "position_change_threshold": 10.0,  # 10%
                        "vix_threshold": 30.0,
                        "large_profit_threshold": 5.0,  # +5%
                        "enabled": True
                    }
                
                return config
        except:
            return {
                "alerts": {
                    "daily_loss_threshold": -3.0,
                    "position_change_threshold": 10.0,
                    "vix_threshold": 30.0,
                    "large_profit_threshold": 5.0,
                    "enabled": True
                }
            }
    
    def check_daily_loss(self) -> List[Dict]:
        """日次損失チェック"""
        alerts = []
        
        equity_history = self.pt.get_equity_history()
        if len(equity_history) < 2:
            return alerts
        
        today_equity = equity_history.iloc[-1]['equity']
        yesterday_equity = equity_history.iloc[-2]['equity']
        
        daily_change_pct = ((today_equity - yesterday_equity) / yesterday_equity) * 100
        threshold = self.alert_config.get("daily_loss_threshold", -3.0)
        
        if daily_change_pct < threshold:
            alerts.append({
                "type": "DAILY_LOSS",
                "severity": "HIGH",
                "title": "⚠️ 日次損失アラート",
                "message": f"本日の資産が{abs(daily_change_pct):.1f}%減少しました（閾値: {abs(threshold):.1f}%）",
                "value": daily_change_pct
            })
        
        return alerts
    
    def check_position_volatility(self) -> List[Dict]:
        """保有銘柄の大きな変動をチェック"""
        alerts = []
        
        positions = self.pt.get_positions()
        if positions.empty:
            return alerts
        
        threshold = self.alert_config.get("position_change_threshold", 10.0)
        
        for idx, pos in positions.iterrows():
            ticker = pos.get('ticker', idx)
            entry_price = pos.get('entry_price') or pos.get('avg_price')
            
            if entry_price is None:
                continue
            
            try:
                # 最新価格取得
                data = fetch_stock_data([ticker], period="5d")
                if not data or ticker not in data:
                    continue
                
                current_price = get_latest_price(data[ticker])
                if current_price is None:
                    continue
                
                change_pct = ((current_price - entry_price) / entry_price) * 100
                
                # 大きな変動（プラス/マイナス両方）
                if abs(change_pct) > threshold:
                    severity = "MEDIUM" if change_pct > 0 else "HIGH"
                    emoji = "📈" if change_pct > 0 else "📉"
                    
                    alerts.append({
                        "type": "POSITION_VOLATILITY",
                        "severity": severity,
                        "title": f"{emoji} {ticker} 大幅変動",
                        "message": f"{ticker}が{change_pct:+.1f}%変動しました（現在価格: ¥{current_price:,.0f}）",
                        "ticker": ticker,
                        "value": change_pct
                    })
            except Exception as e:
                continue
        
        return alerts
    
    def check_vix_spike(self) -> List[Dict]:
        """VIX急騰チェック"""
        alerts = []
        threshold = self.alert_config.get("vix_threshold", 30.0)
        
        try:
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="2d")
            
            if len(vix_data) < 2:
                return alerts
            
            current_vix = vix_data['Close'].iloc[-1]
            prev_vix = vix_data['Close'].iloc[-2]
            
            # VIXが閾値超え
            if current_vix > threshold:
                vix_change = current_vix - prev_vix
                
                alerts.append({
                    "type": "VIX_SPIKE",
                    "severity": "HIGH" if current_vix > 40 else "MEDIUM",
                    "title": "🚨 VIX急騰アラート",
                    "message": f"VIXが{current_vix:.1f}に上昇（前日比{vix_change:+.1f}）- 市場が不安定です",
                    "value": current_vix
                })
        except:
            pass
        
        return alerts
    
    def check_large_profit_opportunity(self) -> List[Dict]:
        """大きな利益確定機会をチェック"""
        alerts = []
        threshold = self.alert_config.get("large_profit_threshold", 5.0)
        
        positions = self.pt.get_positions()
        if positions.empty:
            return alerts
        
        for idx, pos in positions.iterrows():
            ticker = pos.get('ticker', idx)
            entry_price = pos.get('entry_price') or pos.get('avg_price')
            
            if entry_price is None:
                continue
            
            try:
                data = fetch_stock_data([ticker], period="5d")
                if not data or ticker not in data:
                    continue
                
                current_price = get_latest_price(data[ticker])
                if current_price is None:
                    continue
                
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                
                # 大きな利益
                if profit_pct > threshold:
                    alerts.append({
                        "type": "PROFIT_OPPORTUNITY",
                        "severity": "LOW",
                        "title": f"💰 {ticker} 利益確定機会",
                        "message": f"{ticker}が{profit_pct:+.1f}%上昇中（現在価格: ¥{current_price:,.0f}）- 利確を検討",
                        "ticker": ticker,
                        "value": profit_pct
                    })
            except:
                continue
        
        return alerts
    
    def run_all_checks(self) -> List[Dict]:
        """すべてのチェックを実行"""
        if not self.alert_config.get("enabled", True):
            return []
        
        all_alerts = []
        
        # 各チェック実行
        all_alerts.extend(self.check_daily_loss())
        all_alerts.extend(self.check_position_volatility())
        all_alerts.extend(self.check_vix_spike())
        all_alerts.extend(self.check_large_profit_opportunity())
        
        # 重要度でソート（HIGH > MEDIUM > LOW）
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        all_alerts.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        return all_alerts
    
    def send_alerts(self, alerts: List[Dict]):
        """アラートを送信"""
        if not alerts:
            print("アラートなし")
            return
        
        # メッセージ作成
        msg = f"""
🔔 AGStock アラート通知
{datetime.now().strftime('%Y-%m-%d %H:%M')}

{'='*40}
"""
        
        for alert in alerts:
            severity_emoji = {
                "HIGH": "🚨",
                "MEDIUM": "⚠️",
                "LOW": "💡"
            }
            emoji = severity_emoji.get(alert['severity'], "ℹ️")
            
            msg += f"\n{emoji} {alert['title']}\n{alert['message']}\n"
        
        msg += f"\n{'='*40}\n"
        
        print(msg)
        
        # 通知送信（HIGH severity のみ）
        high_alerts = [a for a in alerts if a['severity'] == "HIGH"]
        
        if high_alerts:
            line_config = self.config.get("notifications", {}).get("line", {})
            if line_config.get("enabled"):
                self.notifier.send_line_notify(msg, token=line_config.get("token"))
    
    def run(self):
        """アラートシステム実行"""
        print("スマートアラートシステム起動...")
        alerts = self.run_all_checks()
        
        if alerts:
            print(f"\n{len(alerts)}件のアラートを検出")
            self.send_alerts(alerts)
        else:
            print("\nアラートなし - すべて正常")


def main():
    """メイン実行"""
    alert_system = SmartAlerts()
    alert_system.run()


if __name__ == "__main__":
    main()
