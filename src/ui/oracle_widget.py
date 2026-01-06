"""
Divine Oracle Widget - Real-time Oracle Status Display for Streamlit
"""

import streamlit as st
from src.oracle.oracle_2026 import Oracle2026


def render_oracle_widget():
    """
    Render the Divine Oracle Status Widget.
    Shows current market risk assessment from Oracle 2026.
    """
    st.markdown("---")
    st.markdown("## 🔮 Divine Oracle Status")

    try:
        oracle = Oracle2026()
        guidance = oracle.get_risk_guidance()

        oracle_msg = guidance.get("oracle_message", "Silent")
        safety_mode = guidance.get("safety_mode", False)
        var_buffer = guidance.get("var_buffer", 0.0)
        max_dd_adj = guidance.get("max_drawdown_adj", 1.0)

        # Determine status color and icon
        if safety_mode:
            status = "🛑 CRITICAL"
            status_color = "#FF4444"
            status_bg = "rgba(255, 68, 68, 0.2)"
        elif var_buffer > 0:
            status = "⚠️ CAUTION"
            status_color = "#FFAA00"
            status_bg = "rgba(255, 170, 0, 0.2)"
        else:
            status = "✅ STABLE"
            status_color = "#44FF44"
            status_bg = "rgba(68, 255, 68, 0.2)"

        # Main Status Card
        st.markdown(
            f"""
        <div style="
            background: {status_bg};
            border: 2px solid {status_color};
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
        ">
            <h2 style="color: {status_color}; margin: 0; text-align: center;">
                {status}
            </h2>
            <p style="text-align: center; color: #AAAAAA; margin-top: 10px;">
                {oracle_msg}
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Metrics Row
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="🛡️ Risk Buffer",
                value=f"+{var_buffer*100:.1f}%",
                delta="Active" if var_buffer > 0 else "Inactive",
                delta_color="inverse" if var_buffer > 0 else "off",
            )

        with col2:
            st.metric(
                label="📉 Drawdown Limit",
                value=f"x{max_dd_adj:.1f}",
                delta="Reduced" if max_dd_adj < 1.0 else "Normal",
                delta_color="inverse" if max_dd_adj < 1.0 else "off",
            )

        with col3:
            trading_status = "🚫 HALTED" if safety_mode else "🟢 ACTIVE"
            st.metric(label="💹 Trading Status", value=trading_status)

    except Exception as e:
        st.error(f"Oracle Connection Failed: {e}")
        st.info("The Oracle is silent. Market data may be unavailable.")


def render_oracle_sidebar():
    """
    Compact Oracle widget for sidebar.
    """
    try:
        oracle = Oracle2026()
        guidance = oracle.get_risk_guidance()

        safety_mode = guidance.get("safety_mode", False)
        var_buffer = guidance.get("var_buffer", 0.0)

        if safety_mode:
            st.sidebar.error("🛑 Oracle: CRITICAL - Trading Halted")
        elif var_buffer > 0:
            st.sidebar.warning(f"⚠️ Oracle: CAUTION (+{var_buffer*100:.0f}% buffer)")
        else:
            st.sidebar.success("✅ Oracle: STABLE - Systems Normal")

    except Exception:
        st.sidebar.info("🔮 Oracle: Offline")
