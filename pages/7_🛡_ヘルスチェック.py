import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.risk_guard import RiskGuard
from src.smart_notifier import SmartNotifier


st.set_page_config(page_title="ヘルスチェック", layout="wide")


@st.cache_data
def load_risk_state(path: str = "risk_state.json"):
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


st.title("🛡 システム健全性パネル")
state = load_risk_state()

col1, col2 = st.columns(2)

with col1:
    st.subheader("リスク状態")
    initial_value = state.get("daily_start_value", 1_000_000)
    guard = RiskGuard(
        initial_portfolio_value=initial_value,
        daily_loss_limit_pct=state.get("daily_loss_limit_pct", -5.0),
        max_position_size_pct=state.get("max_position_size_pct", 10.0),
        max_vix=state.get("max_vix", 40.0),
        max_drawdown_limit_pct=state.get("max_drawdown_limit_pct", -20.0),
    )
    guard.consecutive_losses = state.get("consecutive_losses", guard.consecutive_losses)

    st.metric("日次開始資産", f"{guard.daily_start_value:,.0f}")
    st.metric("HWM", f"{guard.high_water_mark:,.0f}")
    st.metric("日次損失リミット", f"{guard.daily_loss_limit_pct}%")
    st.metric("DDリミット", f"{guard.max_drawdown_limit_pct}%")
    st.metric("最大ポジション", f"{guard.max_position_size_pct}%")
    st.metric("最大VIX", guard.max_vix)
    st.metric("連続損失", f"{guard.consecutive_losses}/{guard.max_consecutive_losses}")
    st.write(f"サーキット: {guard.circuit_breaker_triggered}, ドローダウン停止: {guard.drawdown_triggered}")

with col2:
    st.subheader("リアルタイム入力")
    latency = st.number_input("レイテンシ (ms)", min_value=0.0, value=0.0, step=50.0)
    slippage = st.number_input("スリッページ (%)", min_value=0.0, value=0.0, step=0.1)
    consecutive = st.number_input(
        "連続損失回数", min_value=0, value=guard.consecutive_losses, step=1, format="%d"
    )
    current_value = st.number_input("現在ポートフォリオ価値", min_value=0.0, value=guard.daily_start_value, step=1000.0)
    vix = st.number_input("現在のVIX", min_value=0.0, value=0.0, step=0.5)

    if st.button("評価する"):
        halt, reason = guard.should_halt_trading(
            current_portfolio_value=current_value,
            vix_level=vix,
            latency_ms=latency,
            slippage_pct=slippage,
            consecutive_losses=consecutive,
        )
        if halt:
            st.error(f"取引停止推奨: {reason}")
        else:
            st.success("継続可能")

st.divider()
st.subheader("通知")
notif_config = st.text_input("config.json パス", value="config.json")
tickers = st.text_input("データ品質チェック対象（カンマ区切り）", value="^N225,^GSPC,AAPL")
period = st.text_input("期間 (yfinance形式)", value="6mo")

def _build_quality_summary(tickers_list, period_str):
    try:
        from src.data_loader import fetch_stock_data
        from src.data_quality_guard import assess_quality, should_block_trading
    except Exception as exc:
        return [f"quality check failed: {exc}"]

    data = fetch_stock_data(tickers_list, period=period_str, interval="1d", use_async=False)
    lines = []
    for t, df in data.items():
        metrics = assess_quality(df)
        reason = should_block_trading(metrics)
        status = "BLOCK" if reason else "OK"
        lines.append(
            f"{t:10} | missing={metrics['missing_ratio']:.2%} "
            f"| zmax={metrics['max_abs_zscore']:.1f} "
            f"| jump={metrics['max_price_jump_pct']:.1f}% "
            f"| {status}{': ' + reason if reason else ''}"
        )
    return sorted(lines)


if st.button("Slack/Discord/LINEに健全性レポートを送る"):
    notifier = SmartNotifier(config_path=notif_config)
    tq = [t.strip() for t in tickers.split(",") if t.strip()]
    risk_lines = [
        "[Risk]",
        f"daily_start={guard.daily_start_value:,.0f} HWM={guard.high_water_mark:,.0f}",
        f"loss_limit={guard.daily_loss_limit_pct}% dd_limit={guard.max_drawdown_limit_pct}% pos_limit={guard.max_position_size_pct}% VIX<{guard.max_vix}",
        f"consec_losses={guard.consecutive_losses}/{guard.max_consecutive_losses} circuit={guard.circuit_breaker_triggered} drawdown_halt={guard.drawdown_triggered}",
    ]
    quality_lines = ["[Data Quality]"] + _build_quality_summary(tq, period)
    body = "\n".join(risk_lines + quality_lines)
    ok = notifier.send_text(body, title="System Health")
    if ok:
        st.success("送信しました")
    else:
        st.warning("送信できませんでした（通知チャネル未設定の可能性）")
