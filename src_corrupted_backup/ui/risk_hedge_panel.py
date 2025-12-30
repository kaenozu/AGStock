# """
# Risk Hedge UI Panel
# オプション戦略に基づいたリスクヘッジ助言の表示
import streamlit as st
from src.strategies.options_strategy import OptionsEngine
# """
def render_risk_hedge_panel(portfolio_data: dict, market_vix: float):
    st.subheader("🛡️ リスクヘッジ助言 (Risk Hedging)")
        engine = OptionsEngine()
    advice = engine.get_hedge_advice(portfolio_data, market_vix)
# ステータス表示
status = advice["status"]
    if status == "CAUTION":
        st.warning(f"⚠️ **市場警戒モード** (VIX: {market_vix:.1f})")
    else:
        st.success(f"✅ **平常モード** (VIX: {market_vix:.1f})")
        st.info(advice["advice"])
# 詳細データ
col1, col2 = st.columns(2)
    with col1:
        st.metric("推定ヘッジコスト", f"¥{advice['hedge_cost_estimate']:,.0f}")
        st.caption(f"ポートフォリオの {advice['hedge_cost_pct']:.2f}%")
        with col2:
            st.metric("推奨プット権利行使価格", f"現値の -{100 - advice['recommended_strike_pct']}%")
        st.caption(f"満期まで {advice['expiry_days']} 日")
# ヘッジシミュレーター（簡易版）
with st.expander("📊 ヘッジ効果シミュレーター"):
        drop_pct = st.slider("想定下落率 (%)", 0, 30, 10)
# 下落時のポートフォリオ価値
loss_no_hedge = portfolio_data.get("equity", 1000000) * (drop_pct / 100)
# プットオプションの利益（簡易計算）
# プット価格の変動 = -Delta * S_change (実際はガンマ等も効くが簡易化)
put_profit = abs(advice["put_delta"]) * (portfolio_data.get("equity", 1000000) * (drop_pct / 100))
            net_loss = loss_no_hedge - put_profit + advice["hedge_cost_estimate"]
            st.write(f"下落 {drop_pct}% 時の影響:")
        st.write(f"- ヘッジなし損失: ¥{loss_no_hedge:,.0f}")
        st.write(f"- プット利益(推定): ¥{put_profit:,.0f}")
        st.write(f"- **最終損益 (ネット): ¥{net_loss:,.0f}**")
            st.progress(max(0, min(100, int((1 - net_loss / loss_no_hedge) * 100))) if loss_no_hedge > 0 else 0)
        st.caption("ヘッジによる損失緩和率")
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render_risk_hedge_panel({"equity": 10000000}, 28.5)

# """  # Force Balanced
# """
