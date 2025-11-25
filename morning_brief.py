"""
モーニングブリーフ - 毎朝の市況レポート

前日の結果・今日の推奨・市場状況を1つのメッセージにまとめて配信
"""
import json
from datetime import datetime, timedelta, date
import pandas as pd
from typing import Dict, List
import yfinance as yf

from src.paper_trader import PaperTrader
from src.sentiment import SentimentAnalyzer
from src.smart_notifier import SmartNotifier
from src.data_loader import fetch_stock_data, get_latest_price
from src.strategies import CombinedStrategy


class MorningBrief:
    """モーニングブリーフ生成クラス"""
    
    def __init__(self, config_path: str = "config.json"):
        self.pt = PaperTrader()
        self.notifier = SmartNotifier(config_path)
        self.config = self._load_config(config_path)
    
    def _load_config(self, path: str) -> dict:
        """設定読み込み"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    
    def get_market_overview(self) -> Dict:
        """主要市場の概況"""
        indices = {
            "日経平均": "^N225",
            "S&P500": "^GSPC",
            "VIX": "^VIX"
        }
        
        overview = {}
        for name, ticker in indices.items():
            try:
                data = yf.Ticker(ticker).history(period="2d")
                if len(data) >= 2:
                    current = data['Close'].iloc[-1]
                    previous = data['Close'].iloc[-2]
                    change_pct = ((current - previous) / previous) * 100
                    
                    overview[name] = {
                        "value": current,
                        "change_pct": change_pct,
                        "emoji": "📈" if change_pct > 0 else "📉"
                    }
            except:
                overview[name] = None
        
        return overview
    
    def get_portfolio_summary(self) -> Dict:
        """ポートフォリオサマリー"""
        balance = self.pt.get_current_balance()
        positions = self.pt.get_positions()
        
        return {
            "total_equity": balance['total_equity'],
            "cash": balance['cash'],
            "unrealized_pnl": balance['unrealized_pnl'],
            "num_positions": len(positions)
        }
    
    def get_market_sentiment(self) -> Dict:
        """市場センチメント"""
        try:
            sa = SentimentAnalyzer()
            sentiment = sa.get_market_sentiment()
            return {
                "score": sentiment['score'],
                "label": sentiment['label'],
                "emoji": "😊" if sentiment['score'] > 0.2 else "😐" if sentiment['score'] > -0.2 else "😨"
            }
        except:
            return {"score": 0, "label": "不明", "emoji": "😐"}
    
    def generate_brief(self) -> str:
        """ブリーフ生成"""
        # データ取得
        market = self.get_market_overview()
        portfolio = self.get_portfolio_summary()
        sentiment = self.get_market_sentiment()
        
        # メッセージ作成
        msg = f"""
📊 AGStock モーニングブリーフ
{datetime.now().strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━━━━━
📈 主要指数（前日比）
━━━━━━━━━━━━━━━━━━━
"""
        
        for name, data in market.items():
            if data:
                msg += f"{data['emoji']} {name}: {data['value']:,.0f} ({data['change_pct']:+.2f}%)\n"
        
        msg += f"""
━━━━━━━━━━━━━━━━━━━
💼 ポートフォリオ
━━━━━━━━━━━━━━━━━━━
総資産: ¥{portfolio['total_equity']:,.0f}
現金: ¥{portfolio['cash']:,.0f}
含み損益: ¥{portfolio['unrealized_pnl']:+,.0f}
保有銘柄: {portfolio['num_positions']}銘柄

━━━━━━━━━━━━━━━━━━━
📰 市場センチメント
━━━━━━━━━━━━━━━━━━━
{sentiment['emoji']} {sentiment['label']} ({sentiment['score']:.2f})

━━━━━━━━━━━━━━━━━━━
💡 今日の戦略
━━━━━━━━━━━━━━━━━━━
"""
        
        # VIXチェック
        if "VIX" in market and market["VIX"]:
            vix = market["VIX"]["value"]
            if vix > 30:
                msg += "⚠️ VIX高騰中 - リスク管理を徹底\n"
            elif vix < 15:
                msg += "✅ 低ボラティリティ - 安定した相場\n"
            else:
                msg += "📊 通常の戦略で運用\n"
        
        # センチメントベース
        if sentiment['score'] > 0.3:
            msg += "📝 積極的な買い場を探す\n"
        elif sentiment['score'] < -0.3:
            msg += "⚠️ 慎重に。新規買いは控えめに\n"
        
        msg += "\n🤖 良い1日を！\n"
        
        return msg.strip()
    
    def send_brief(self):
        """ブリーフを送信"""
        brief = self.generate_brief()
        
        print(brief)
        
        # LINE/Discord送信
        line_config = self.config.get("notifications", {}).get("line", {})
        discord_config = self.config.get("notifications", {}).get("discord", {})
        
        if line_config.get("enabled"):
            self.notifier.send_line_notify(brief, token=line_config.get("token"))
        
        if discord_config.get("enabled"):
            self.notifier.send_discord_webhook(brief, webhook_url=discord_config.get("webhook_url"))
        
        return brief


def main():
    """メイン実行"""
    brief_generator = MorningBrief()
    brief_generator.send_brief()


if __name__ == "__main__":
    main()
