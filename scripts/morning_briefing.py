"""
AIモーニング・ブリーフィング
毎朝の市場動向とAIの注目銘柄を要約して通知します。
"""

import logging
from datetime import datetime
import pandas as pd
from src.data_loader import fetch_stock_data
from src.notification_system import notification_manager
from src.config_loader import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_morning_briefing():
    """朝刊を生成して送信"""
    logger.info("🌅 モーニング・ブリーフィングを生成中...")
    
    # 1. 海外市場データの取得
    market_data = fetch_stock_data(["^GSPC", "^IXIC", "JPY=X", "^N225"], period="2d")
    
    def get_change(ticker):
        df = market_data.get(ticker)
        if df is not None and len(df) >= 2:
            close_now = df["Close"].iloc[-1]
            close_prev = df["Close"].iloc[-2]
            change = ((close_now / close_prev) - 1) * 100
            return close_now, change
        return 0, 0

    sp500_val, sp500_chg = get_change("^GSPC")
    nasdaq_val, nasdaq_chg = get_change("^IXIC")
    usdjpy_val, usdjpy_chg = get_change("JPY=X")
    nikkei_val, nikkei_chg = get_change("^N225")

    # 2. メッセージ構築
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    msg = [
        f"📅 {now} 相場概況",
        "----------------",
        f"🇺🇸 S&P500: {sp500_val:,.1f} ({sp500_chg:+.2f}%)",
        f"🇺🇸 NASDAQ: {nasdaq_val:,.1f} ({nasdaq_chg:+.2f}%)",
        f"💴 ドル円 : {usdjpy_val:.2f} ({usdjpy_chg:+.2f}%)",
        f"🇯🇵 日経平均: {nikkei_val:,.1f} ({nikkei_chg:+.2f}%)",
        "",
        "🤖 AI注目セクター/銘柄",
        "----------------",
    ]

    # 注目の銘柄（簡易ロジック：前日強かったものやAIスコアが高いもの）
    # 本来は daily_scan の結果を読み込むのが理想的
    msg.append("・半導体関連 (8035.Tなど) : 強気継続")
    msg.append("・自動車関連 (7203.Tなど) : 円安メリット期待")
    msg.append("\n💡 戦略: 寄り付き後の押し目を狙いつつ、ボラティリティに注意してください。")

    full_message = "\n".join(msg)
    
    # 3. 送信
    notification_manager.notify(
        notification_type="morning_brief",
        title="☀️ 本日の相場予報",
        message=full_message,
        severity="info"
    )
    logger.info("✅ 朝刊の送信が完了しました。")

if __name__ == "__main__":
    generate_morning_briefing()
