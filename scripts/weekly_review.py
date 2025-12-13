"""
週次パフォーマンスレビュー

過去1週間のペーパートレード結果をまとめて表示します。
使い方: python weekly_review.py
"""

from datetime import datetime, timedelta

import pandas as pd

from src.formatters import format_currency, format_percentage
from src.paper_trader import PaperTrader


def print_header(title):
    """セクションヘッダーを表示"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """サブセクションヘッダーを表示"""
    print(f"\n📊 {title}")
    print("-" * 70)


def weekly_review():
    """週次レビューを実行"""
    pt = PaperTrader()

    # 期間設定
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    print_header(
        f"📈 週次パフォーマンスレビュー ({start_date.strftime('%Y-%m-%d')} 〜 {end_date.strftime('%Y-%m-%d')})"
    )

    # 1. 資産サマリー
    print_section("💰 資産状況")
    balance = pt.get_current_balance()
    initial_capital = pt.initial_capital

    print(f"総資産:        {format_currency(balance['total_equity'])}")
    print(f"現金:          {format_currency(balance['cash'])}")
    print(f"投資額:        {format_currency(balance['invested_amount'])}")
    print(
        f"含み損益:      {format_currency(balance['unrealized_pnl'])} ({format_percentage(balance['unrealized_pnl'] / balance['invested_amount'] if balance['invested_amount'] > 0 else 0)})"
    )
    print(f"\n期間収益率:    {format_percentage((balance['total_equity'] - initial_capital) / initial_capital)}")

    # 2. 週間取引サマリー
    print_section("📝 週間取引サマリー")
    history = pt.get_trade_history()

    if history.empty:
        print("⚠️ 取引履歴がありません")
    else:
        # timestampカラムまたはdateカラムを使用（フォールバック処理）
        time_col = None
        if "timestamp" in history.columns:
            time_col = "timestamp"
            history["timestamp"] = pd.to_datetime(history["timestamp"])
        elif "date" in history.columns:
            time_col = "date"
            history["date"] = pd.to_datetime(history["date"])
            print("ℹ️ timestampカラムがないため、dateカラムを使用します")

        if time_col:
            week_trades = history[history[time_col] >= start_date]
        else:
            print("⚠️ 日時情報が見つかりません。全ての取引を表示します。")
            week_trades = history

        if week_trades.empty:
            print("⚠️ 今週の取引はありません")
        else:
            buy_count = len(week_trades[week_trades["action"] == "BUY"])
            sell_count = len(week_trades[week_trades["action"] == "SELL"])

            print(f"取引回数: {len(week_trades)}回 (買: {buy_count}回 / 売: {sell_count}回)")

            if "realized_pnl" in week_trades.columns:
                total_pnl = week_trades["realized_pnl"].sum()
                print(f"確定損益: {format_currency(total_pnl)}")

    # 3. 銘柄別パフォーマンス
    print_section("🏆 銘柄別パフォーマンス (現在保有)")
    positions = pt.get_positions()

    if positions.empty:
        print("現在ポジションはありません")
    else:
        positions_sorted = positions.sort_values("unrealized_pnl", ascending=False)

        print(f"\n{'銘柄':<12} {'数量':>8} {'取得単価':>12} {'現在値':>12} {'含み損益':>14} {'損益率':>10}")
        print("-" * 70)

        for idx, pos in positions_sorted.head(10).iterrows():
            ticker = pos.get("ticker", idx)
            qty = pos.get("quantity", 0)
            entry = pos.get("entry_price", 0)
            current = pos.get("current_price", 0)
            pnl = pos.get("unrealized_pnl", 0)
            pnl_pct = pos.get("unrealized_pnl_pct", 0)

            pnl_str = "+" if pnl >= 0 else ""
            print(
                f"{ticker:<12} {qty:>8} {format_currency(entry):>12} {format_currency(current):>12} {pnl_str}{format_currency(pnl):>13} {format_percentage(pnl_pct/100):>10}"
            )

    # 4. 勝率と統計
    print_section("📊 トレード統計")

    closed_trades = history[history["action"] == "SELL"].copy()

    if not closed_trades.empty and "realized_pnl" in closed_trades.columns:
        wins = len(closed_trades[closed_trades["realized_pnl"] > 0])
        losses = len(closed_trades[closed_trades["realized_pnl"] < 0])
        total_closed = len(closed_trades)

        win_rate = wins / total_closed if total_closed > 0 else 0

        avg_win = closed_trades[closed_trades["realized_pnl"] > 0]["realized_pnl"].mean() if wins > 0 else 0
        avg_loss = closed_trades[closed_trades["realized_pnl"] < 0]["realized_pnl"].mean() if losses > 0 else 0

        profit_factor = abs(avg_win * wins / (avg_loss * losses)) if losses > 0 and avg_loss != 0 else 0

        print(f"総決済数:      {total_closed}回")
        print(f"勝ちトレード:  {wins}回")
        print(f"負けトレード:  {losses}回")
        print(f"勝率:          {format_percentage(win_rate)}")
        print(f"平均利益:      {format_currency(avg_win)}")
        print(f"平均損失:      {format_currency(avg_loss)}")
        print(f"プロフィット・ファクター: {profit_factor:.2f}")
    else:
        print("まだ決済された取引がありません")

    # 5. 資産推移
    print_section("📈 資産推移 (直近7日)")
    equity_history = pt.get_equity_history()

    if not equity_history.empty:
        equity_history["date"] = pd.to_datetime(equity_history["date"])
        recent = equity_history[equity_history["date"] >= start_date].tail(7)

        if not recent.empty:
            print(f"\n{'日付':<12} {'総資産':>15} {'前日比':>15}")
            print("-" * 45)

            prev_equity = None
            for _, row in recent.iterrows():
                date_str = row["date"].strftime("%Y-%m-%d")
                equity = row["total_equity"]

                if prev_equity is not None:
                    change = equity - prev_equity
                    change_pct = change / prev_equity if prev_equity > 0 else 0
                    change_str = (
                        f"{'+' if change >= 0 else ''}{format_currency(change)} ({format_percentage(change_pct)})"
                    )
                else:
                    change_str = "-"

                print(f"{date_str:<12} {format_currency(equity):>15} {change_str:>15}")
                prev_equity = equity

    # 6. 今週の気づき・改善点
    print_section("💡 レビューポイント")
    print(
        """
1. システムの判断は妥当でしたか？
   - どの銘柄を買い、どの銘柄を売りましたか？
   - タイミングは適切でしたか？

2. リスク管理は機能していますか？
   - 想定以上の損失は出ていませんか？
   - ポジションサイズは適切ですか？

3. 来週に向けた改善点は？
   - パラメータ調整が必要ですか？
   - 除外すべき銘柄はありますか？
    """
    )

    print("\n" + "=" * 70)
    print("  📝 次週も引き続きペーパートレードで検証を続けましょう")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        weekly_review()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
