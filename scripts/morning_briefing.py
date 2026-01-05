"""
AIモーニング・ブリーフィング
毎朝の相場動向とAIの注目銘柄を要約して通知します。
"""
import logging
from datetime import datetime
from src.data_loader import fetch_stock_data
from src.notification_system import notification_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_morning_briefing():
    logger.info("🌅 モーニング・ブリーフィングを生成中...")
    market_data = fetch_stock_data(["^GSPC", "^IXIC", "JPY=X", "^N225"], period="2d")
    
    def get_change(ticker):
        df = market_data.get(ticker)
        if df is not None and len(df) >= 2:
            close_now = df["Close"].iloc[-1]
            close_prev = df["Close"].iloc[-2]
            return close_now, ((close_now / close_prev) - 1) * 100
        return 0, 0

    sp_v, sp_c = get_change("^GSPC")
    nas_v, nas_c = get_change("^IXIC")
    fx_v, fx_c = get_change("JPY=X")
    ni_v, ni_c = get_change("^N225")

    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    msg = [
        f"📅 {now} 相場概況",
        "----------------",
        f"🇺🇸 S&P500: {sp_v:,.1f} ({sp_c:+.2f}%)",
        f"🇺🇸 NASDAQ: {nas_v:,.1f} ({nas_c:+.2f}%)",
        f"💴 ドル円 : {fx_v:.2f} ({fx_c:+.2f}%)",
        f"🇯🇵 日経平均: {ni_v:,.1f} ({ni_c:+.2f}%)",
        "",
        "🤖 AI注目セクター",
        "・半導体 (8035.Tなど) : 強気",
        "・自動車 (7203.Tなど) : 円安期待",
    ]
    notification_manager.notify("morning_brief", "☀️ 本日の相場予報", "\n".join(msg))

if __name__ == "__main__":
    generate_morning_briefing()