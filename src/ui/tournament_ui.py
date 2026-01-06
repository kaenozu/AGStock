import streamlit as st
import pandas as pd
from src.trading.tournament_manager import TournamentManager, PERSONALITIES
from src.utils.currency import CurrencyConverter


def render_tournament_ui():
    st.header("🏆 並行世界トーナメント (Multiversal Shadow Tournament)")
    st.markdown(
        """
    ここでは、性格の異なる4人のAIトレーダーが、同じ市場シグナルを元に独自の判断で資産を競い合っています。
    現在の市場レジームにおいて、どの性格のAIが最も適応しているかを確認できます。
    """
    )

    try:
        tm = TournamentManager()
        leaderboard = tm.get_leaderboard()

        if leaderboard.empty:
            st.warning("トーナメントデータがまだ蓄積されていません。日次ルーティンを実行してください。")
            return

        # Top Performing Advisor
        winner_advise = tm.get_winner_advise()
        st.success(winner_advise)

        # Leaderboard Cards
        st.subheader("現在のリーダーボード")
        cols = st.columns(len(leaderboard))

        for i, (_, row) in enumerate(leaderboard.iterrows()):
            with cols[i]:
                # Medal emoji for top rankings
                rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👤"
                st.markdown(f"### {rank_emoji} {row['Name']}")

                total_equity = row["Total Equity"]
                pnl = row["Daily PnL"]
                color = "green" if pnl >= 0 else "red"

                st.metric(label="総資産", value=f"¥{total_equity:,.0f}", delta=f"¥{pnl:,.0f}")
                st.info(row["Description"])

        # Detailed Stats Table
        st.subheader("詳細統計")
        display_df = leaderboard.copy()
        display_df["Total Equity"] = display_df["Total Equity"].map(lambda x: f"¥{x:,.0f}")
        display_df["Daily PnL"] = display_df["Daily PnL"].map(lambda x: f"¥{x:,.0f}")
        display_df["Unrealized PnL"] = display_df["Unrealized PnL"].map(lambda x: f"¥{x:,.0f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Performance Chart
        st.subheader("資産推移 (Equity Curves)")
        equity_data = {}
        for acc_id in PERSONALITIES.keys():
            trader = tm.traders[acc_id]
            history = trader.get_equity_history(days=30)
            if not history.empty:
                history = history.set_index("date")["total_equity"]
                equity_data[PERSONALITIES[acc_id]["name"]] = history

        if equity_data:
            chart_df = pd.DataFrame(equity_data).ffill()
            st.line_chart(chart_df)
        else:
            st.info("チャートを表示するための十分な履歴がありません。")

    except Exception as e:
        st.error(f"トーナメントデータの表示中にエラーが発生しました: {e}")
        import traceback

        st.code(traceback.format_exc())
