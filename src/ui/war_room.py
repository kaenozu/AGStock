import streamlit as st
import pandas as pd
import time
from datetime import datetime
import random


def render_war_room():
    # CSS for War Room Atmosphere (Red/Black Theme)
    st.markdown(
        """
        <style>
        .war-room-header {
            font-family: 'Courier New', monospace;
            color: #ff3b3b;
            border-bottom: 2px solid #ff3b3b;
            padding-bottom: 10px;
            text-transform: uppercase;
            animation: pulse-red 2s infinite;
        }
        @keyframes pulse-red {
            0% { text-shadow: 0 0 0px #ff0000; }
            50% { text-shadow: 0 0 10px #ff0000; }
            100% { text-shadow: 0 0 0px #ff0000; }
        }
        .alert-box {
            background-color: #3b0000;
            border: 1px solid #ff0000;
            color: #ffcccc;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
        }
        .stat-card-war {
            background-color: #111;
            border: 1px solid #333;
            padding: 10px;
            text-align: center;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<h1 class="war-room-header">🌐 Global Sentiment War Room</h1>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            '<div class="stat-card-war"><h3>DEFCON</h3><h1 style="color:orange">3</h1></div>', unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            '<div class="stat-card-war"><h3>VIX Live</h3><h1 style="color:#ff3b3b">24.5</h1></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="stat-card-war"><h3>News Vol</h3><h1 style="color:cyan">High</h1></div>', unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            '<div class="stat-card-war"><h3>Active Alerts</h3><h1 style="color:yellow">2</h1></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Real-time Feed Simulation
    st.subheader("📡 Intercepted Intelligence Stream")

    # Auto-refresh loop control
    if "war_room_active" not in st.session_state:
        st.session_state["war_room_active"] = False

    start_btn = st.button("🔴 ACTIVATE LIVE MONITORING")
    if start_btn:
        st.session_state["war_room_active"] = not st.session_state["war_room_active"]

    if st.session_state["war_room_active"]:
        placeholder = st.empty()

        # Mock keywords that trigger alerts
        DANGER_KEYWORDS = ["Crash", "Plunge", "War", "Sanctions", "Suspension", "Panic"]

        # Mock news production
        news_ticker = [
            "BOJ holds extraordinary meeting regarding yield curve control.",
            "Tech sector sees mild correction as AI hype cools down.",
            "BREAKING: Semiconductor supply chain disrupted by new sanctions.",
            "Yen plunges to 155 against USD.",
            "Market sentiment remains cautious ahead of CPI data.",
            "Elon Musk tweets about new crypto payment system.",
            "Global liquidity index drops below critical threshold.",
            "FLASH CRASH detected in futures market.",
        ]

        # Simulation Loop (Only runs a few seconds to avoid locking UI forever in Streamlit)
        # In a real app, this would be handled by st.fragment or run_every
        logs = []
        for i in range(10):  # Show 10 updates then user has to refresh
            now = datetime.now().strftime("%H:%M:%S")
            headline = random.choice(news_ticker)
            is_danger = any(k in headline for k in DANGER_KEYWORDS)

            log_html = f"""
                <div class="alert-box" style="border-color: {'#ff0000' if is_danger else '#444'}; background-color: {'#3b0000' if is_danger else '#111'};">
                    <span style="color: #888;">[{now}]</span> <strong>{headline}</strong>
                </div>
            """
            logs.insert(0, log_html)

            with placeholder.container():
                st.markdown("".join(logs[:5]), unsafe_allow_html=True)
                if is_danger:
                    st.error("⚠️ CRITICAL ALERT DETECTED")

            time.sleep(0.8)

        st.warning("Monitor paused. Click Activate to resume.")
    else:
        st.info("Monitoring Standby. Click Activate to start scanning global feeds.")
