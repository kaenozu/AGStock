import os
import sys

import pandas as pd

from src.data_loader import fetch_stock_data, get_latest_price
from src.paper_trader import PaperTrader


def main():
    try:
        pt = PaperTrader()
        balance = pt.get_current_balance()
        positions = pt.get_positions()

        print(f"--- 資産状況 ({pd.Timestamp.now()}) ---")
        print(f"初期資金: {pt.initial_capital:,.0f} JPY")
        print(f"現金残高: {balance['cash']:,.0f} JPY")

        # ポートフォリオの現在価値を計算
        current_equity = balance["cash"]
        total_unrealized = 0

        if not positions.empty:
            print("\n--- 保有ポジション ---")
            tickers = positions["ticker"].tolist()
            # 最新価格を取得（1日分で十分）
            data_map = fetch_stock_data(tickers, period="1d")

            for idx, row in positions.iterrows():
                ticker = row["ticker"]
                qty = row["quantity"]
                entry = row["entry_price"]

                current_price = entry  # 取得失敗時は取得価格を使用
                if ticker in data_map and not data_map[ticker].empty:
                    current_price = get_latest_price(data_map[ticker])

                market_value = qty * current_price
                current_equity += market_value

                pnl = (current_price - entry) * qty
                pnl_pct_pos = ((current_price - entry) / entry) * 100

                total_unrealized += pnl

                print(
                    f"{ticker:<8} {qty:>5}株 | 取得: {entry:>8,.1f} -> 現在: {current_price:>8,.1f} | 評価額: {market_value:>10,.0f} | 損益: {pnl:>+8,.0f} ({pnl_pct_pos:>+6.2f}%)"
                )
        else:
            print("\n保有ポジションはありません。")

        total_pnl = current_equity - pt.initial_capital
        total_pnl_pct = (total_pnl / pt.initial_capital) * 100

        print(f"\n--- サマリー ---")
        print(f"総資産評価額: {current_equity:,.0f} JPY")
        print(f"トータル損益: {total_pnl:+,.0f} JPY ({total_pnl_pct:+.2f}%)")
        print(f"うち含み損益: {total_unrealized:+,.0f} JPY")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
