import datetime

import pandas as pd

from src.data_loader import fetch_stock_data
from src.paper_trader import PaperTrader


def investigate_bac():
    print("=== BAC 損失要因調査 ===\n")

    # 1. 取引履歴の確認
    pt = PaperTrader()
    history = pt.get_trade_history()
    bac_trades = history[history["ticker"] == "BAC"]

    if bac_trades.empty:
        print("BACの取引履歴が見つかりませんでした。")
        return

    last_buy = bac_trades.iloc[-1]
    buy_date = pd.to_datetime(last_buy["timestamp"])
    buy_price = last_buy["price"]

    print(f"購入日時: {buy_date}")
    print(f"購入価格: ${buy_price:.2f}")

    # 2. 購入後の価格推移
    print("\n--- 価格推移分析 ---")
    # 5日間のデータを取得（1時間足があればベストだが、yfinanceの制限により日足または短いインターバル）
    # ここでは詳細を見るために '5d' 期間の '60m' インターバルを試す
    try:
        import yfinance as yf

        df = yf.download("BAC", period="5d", interval="60m", progress=False)

        # CloseカラムがMultiIndexの場合のケア
        if isinstance(df.columns, pd.MultiIndex):
            current_price = df["Close"].iloc[-1].item()
            bac_start = df["Open"].iloc[0].item()
        else:
            current_price = float(df["Close"].iloc[-1])
            bac_start = float(df["Open"].iloc[0])

        print(f"現在価格: ${current_price:.2f}")
        print(f"騰落率:   {((current_price - buy_price) / buy_price) * 100:.2f}%")

        post_buy_df = df[df.index >= buy_date.tz_localize(df.index.tz)]
        if not post_buy_df.empty:
            print(f"期間中高値: ${post_buy_df['High'].max():.2f}")
            print(f"期間中安値: ${post_buy_df['Low'].min():.2f}")
    except Exception as e:
        print(f"詳細データ取得エラー: {e}")

    # 3. ニュースの確認
    print("\n--- 関連ニュース ---")
    try:
        # fetch_newsが見つからないため、yfinanceのTickerオブジェクトから直接取得
        ticker_obj = yf.Ticker("BAC")
        news_list = ticker_obj.news
        if news_list:
            for i, article in enumerate(news_list[:3], 1):
                print(f"{i}. {article.get('title', 'No Title')}")
                print(f"   {article.get('link', 'No Link')}")
        else:
            print("ニュースが見つかりませんでした。")
    except Exception as e:
        print(f"ニュース取得エラー: {e}")

    # 4. セクター比較 (XLF: Financial Select Sector SPDR Fund)
    print("\n--- 金融セクター比較 (XLF) ---")
    try:
        xlf_df = yf.download("XLF", period="5d", interval="60m", progress=False)
        if isinstance(xlf_df.columns, pd.MultiIndex):
            xlf_current = xlf_df["Close"].iloc[-1].item()
            xlf_start = xlf_df["Open"].iloc[0].item()
        else:
            xlf_current = float(xlf_df["Close"].iloc[-1])
            xlf_start = float(xlf_df["Open"].iloc[0])

        bac_change = ((current_price - bac_start) / bac_start) * 100
        xlf_change = ((xlf_current - xlf_start) / xlf_start) * 100

        print(f"BAC 5日間騰落率: {bac_change:.2f}%")
        print(f"XLF 5日間騰落率: {xlf_change:.2f}%")

        if bac_change < xlf_change:
            print("=> BACはセクター平均よりアンダーパフォームしています（個別要因の可能性）。")
        else:
            print("=> セクター全体の下落に連動しているようです。")

    except Exception as e:
        print(f"セクター比較エラー: {e}")


if __name__ == "__main__":
    investigate_bac()
