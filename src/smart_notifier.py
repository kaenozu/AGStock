"""
スマート通知システム - 個人投資家向け

チャート画像付きの通知、重要度フィルタリング、モバイル対応を提供
"""
import os
import io
import json
import tempfile
from typing import Dict, List, Optional
from datetime import datetime, time as dt_time
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

from src.notifier import Notifier


class SmartNotifier(Notifier):
    """スマート通知機能を提供するクラス"""
    
    def __init__(self, config_or_path="config.json"):
        super().__init__()
        # Accept either a config dict or a path string
        if isinstance(config_or_path, dict):
            self.config = config_or_path
        else:
            self.config = self.load_config(config_or_path)
        self.notification_settings = self.config.get("notifications", {})
        
        # 通知フィルタ設定
        self.min_confidence = self.notification_settings.get("min_confidence", 0.7)
        self.min_expected_return = self.notification_settings.get("min_expected_return", 0.03)
        self.quiet_hours = self.parse_quiet_hours(
            self.notification_settings.get("quiet_hours", "22:00-07:00")
        )
    
    def load_config(self, config_path: str) -> Dict:
        """設定ファイルを読み込む"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def parse_quiet_hours(self, quiet_hours_str: str) -> tuple:
        """静穏時間を解析（例: "22:00-07:00"）"""
        try:
            start_str, end_str = quiet_hours_str.split("-")
            start_hour, start_min = map(int, start_str.split(":"))
            end_hour, end_min = map(int, end_str.split(":"))
            return (dt_time(start_hour, start_min), dt_time(end_hour, end_min))
        except:
            return (dt_time(22, 0), dt_time(7, 0))  # デフォルト
    
    def is_quiet_time(self) -> bool:
        """現在が静穏時間かチェック"""
        now = datetime.now().time()
        start, end = self.quiet_hours
        
        if start < end:
            # 例: 22:00-23:59 (同日内)
            return start <= now <= end
        else:
            # 例: 22:00-07:00 (日をまたぐ)
            return now >= start or now <= end
    
    def should_notify(self, signal: Dict) -> bool:
        """通知すべきかフィルタリング"""
        # 静穏時間チェック
        if self.is_quiet_time():
            return False
        
        # 信頼度チェック
        confidence = signal.get("confidence", 0)
        if confidence < self.min_confidence:
            return False
        
        # 期待リターンチェック
        expected_return = signal.get("expected_return", 0)
        if expected_return < self.min_expected_return:
            return False
        
        return True
    
    def create_mini_chart(self, ticker: str, df: pd.DataFrame, signal_action: str) -> str:
        """ミニチャートを生成してパスを返す"""
        try:
            fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
            
            # 直近30日のデータ
            df_recent = df.tail(30)
            
            # 価格チャート
            ax.plot(df_recent.index, df_recent['Close'], 
                   linewidth=2, color='#00D9FF', label='価格')
            
            # 移動平均線
            if len(df_recent) >= 20:
                sma20 = df_recent['Close'].rolling(20).mean()
                ax.plot(df_recent.index, sma20, 
                       linewidth=1, color='orange', alpha=0.7, label='SMA20')
            
            # シグナルマーカー
            last_price = df_recent['Close'].iloc[-1]
            last_date = df_recent.index[-1]
            
            if signal_action == "BUY":
                ax.scatter([last_date], [last_price], 
                          color='lime', s=200, marker='^', 
                          zorder=5, label='買いシグナル')
            elif signal_action == "SELL":
                ax.scatter([last_date], [last_price], 
                          color='red', s=200, marker='v', 
                          zorder=5, label='売りシグナル')
            
            # スタイル設定
            ax.set_facecolor('#1E1E1E')
            fig.patch.set_facecolor('#1E1E1E')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.tick_params(colors='white')
            ax.yaxis.label.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.title.set_color('white')
            
            ax.set_title(f'{ticker} - 直近30日', fontsize=14, color='white')
            ax.set_ylabel('価格 (円)', fontsize=10, color='white')
            ax.grid(True, alpha=0.2, color='white')
            ax.legend(loc='upper left', facecolor='#2E2E2E', edgecolor='white', labelcolor='white')
            
            # 日付フォーマット
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # 一時ファイルに保存
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix='.png', prefix='chart_'
            )
            fig.savefig(temp_file.name, facecolor='#1E1E1E', dpi=100)
            plt.close(fig)
            
            return temp_file.name
        except Exception as e:
            print(f"チャート生成エラー: {e}")
            return None
    
    def send_trading_signal(self, signal: Dict, df: Optional[pd.DataFrame] = None):
        """
        トレーディングシグナルを通知
        
        Args:
            signal: シグナル情報の辞書
                - ticker: ティッカーシンボル
                - name: 銘柄名
                - action: BUY/SELL
                - price: 現在価格
                - confidence: 信頼度 (0-1)
                - expected_return: 期待リターン (%)
                - risk_level: リスクレベル (低/中/高)
                - explanation: 説明
                - strategy: 戦略名
            df: 価格データ（チャート生成用、オプション）
        """
        # フィルタリング
        if not self.should_notify(signal):
            return
        
        # チャート生成
        chart_path = None
        if df is not None:
            chart_path = self.create_mini_chart(
                signal['ticker'], df, signal['action']
            )
        
        # メッセージ作成
        action_emoji = "💰" if signal['action'] == "BUY" else "📉"
        risk_emoji = {
            "低": "🟢",
            "中": "🟡", 
            "高": "🔴"
        }.get(signal.get('risk_level', '中'), "🟡")
        
        message = f"""
🔔 トレーディングシグナル

{action_emoji} {signal['action']} 推奨
━━━━━━━━━━━━━━━
銘柄: {signal['name']} ({signal['ticker']})
現在価格: ¥{signal['price']:,.0f}
期待リターン: +{signal.get('expected_return', 0):.1%}
信頼度: {signal.get('confidence', 0):.0%}
リスク: {risk_emoji} {signal.get('risk_level', '中')}

💡 理由:
{signal.get('explanation', '詳細なし')}

📊 戦略: {signal.get('strategy', '不明')}
""".strip()
        
        # LINE通知
        line_config = self.notification_settings.get("line", {})
        if line_config.get("enabled"):
            self.send_line_notify(message, image_path=chart_path, token=line_config.get("token"))
        
        # Discord通知
        discord_config = self.notification_settings.get("discord", {})
        if discord_config.get("enabled"):
            self.send_discord_webhook(message, webhook_url=discord_config.get("webhook_url"))
        
        # チャート削除
        if chart_path and os.path.exists(chart_path):
            try:
                os.unlink(chart_path)
            except:
                pass
    
    def send_line_notify(self, message: str, image_path: Optional[str] = None, 
                        token: Optional[str] = None):
        """LINE Notifyで通知を送信"""
        if not token:
            return
        
        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"message": message}
        files = {}
        
        if image_path and os.path.exists(image_path):
            files = {"imageFile": open(image_path, "rb")}
        
        try:
            response = requests.post(url, headers=headers, data=payload, 
                                    files=files, timeout=10)
            if response.status_code == 200:
                print("✓ LINE通知送信成功")
            else:
                print(f"✗ LINE通知失敗: {response.status_code}")
        except Exception as e:
            print(f"✗ LINE通知エラー: {e}")
        finally:
            if files:
                files["imageFile"].close()
    
    def send_discord_webhook(self, message: str, webhook_url: Optional[str] = None):
        """Discord Webhookで通知を送信"""
        if not webhook_url:
            return
        
        payload = {"content": message}
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 204:
                print("✓ Discord通知送信成功")
            else:
                print(f"✗ Discord通知失敗: {response.status_code}")
        except Exception as e:
            print(f"✗ Discord通知エラー: {e}")
    
    def send_daily_summary_rich(self, summary: Dict):
        """
        リッチな日次サマリーを送信
        
        Args:
            summary: サマリー情報
                - date: 日付
                - total_value: 総資産
                - daily_pnl: 日次損益
                - monthly_pnl: 月次損益
                - win_rate: 勝率
                - signals: シグナルリスト
                - top_performer: トップパフォーマー
                - advice: アドバイス
        """
        # 静穏時間チェック
        if self.is_quiet_time():
            return
        
        # メッセージ作成
        pnl_emoji = "📈" if summary.get('daily_pnl', 0) >= 0 else "📉"
        
        signals_text = "なし"
        if summary.get('signals'):
            signals_text = "\n".join([
                f"  • {s['action']} {s['ticker']} ({s['name']})"
                for s in summary['signals'][:5]  # 最大5件
            ])
        
        message = f"""
📊 本日のサマリー ({summary.get('date', datetime.now().strftime('%Y-%m-%d'))})

💼 ポートフォリオ
━━━━━━━━━━━━━━━
総資産: ¥{summary.get('total_value', 0):,.0f}
本日損益: {pnl_emoji} ¥{summary.get('daily_pnl', 0):+,.0f}
今月損益: ¥{summary.get('monthly_pnl', 0):+,.0f}
勝率: {summary.get('win_rate', 0):.0%}

🎯 本日のシグナル:
{signals_text}

🏆 トップパフォーマー:
{summary.get('top_performer', 'データなし')}

💡 アドバイス:
{summary.get('advice', '通常運用を継続してください')}
""".strip()
        
        # 各種通知
        line_config = self.notification_settings.get("line", {})
        if line_config.get("enabled"):
            self.send_line_notify(message, token=line_config.get("token"))
        
        discord_config = self.notification_settings.get("discord", {})
        if discord_config.get("enabled"):
            self.send_discord_webhook(message, webhook_url=discord_config.get("webhook_url"))
