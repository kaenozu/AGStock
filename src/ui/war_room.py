import streamlit as st
import pandas as pd
import time
from datetime import datetime
import random
from src.trading.collective_intelligence import CollectiveIntelligenceManager


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
        .consensus-box {
            background-color: #002200;
            border: 1px solid #00ff00;
            color: #ccffcc;
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

    st.markdown('<h1 class="war-room-header">🌐 DAO Global Sentiment War Room</h1>', unsafe_allow_html=True)

    cim = CollectiveIntelligenceManager()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            '<div class="stat-card-war"><h3>DAO NODES</h3><h1 style="color:cyan">12</h1></div>', unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            '<div class="stat-card-war"><h3>VIX Live</h3><h1 style="color:#ff3b3b">24.5</h1></div>',
            unsafe_allow_html=True,
        )
    with col3:
        consensus = cim.get_consensus_signals()
        st.markdown(
            f'<div class="stat-card-war"><h3>CONSENSUS</h3><h1 style="color:lime">{len(consensus)}</h1></div>', unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            '<div class="stat-card-war"><h3>DEFCON</h3><h1 style="color:orange">3</h1></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Consensus Section
    if consensus:
        st.subheader("🤝 DAO Consensus Signals")
        for c in consensus:
            st.markdown(f"""
                <div class="consensus-box">
                    <strong>[CONSENSUS] {c['ticker']}</strong>: {c['action']} 
                    (Agreement: {c['agreement']*100:.0f}%, Confidence: {c['avg_confidence']*100:.0f}%, Nodes: {c['num_nodes']})
                </div>
            """, unsafe_allow_html=True)

    # Global Map Section
    import plotly.express as px
    st.subheader("🌍 DAO Node Distribution & Signal Map")
    node_data = pd.DataFrame({
        'City': ['Tokyo', 'New York', 'London', 'Singapore', 'Zurich', 'Hong Kong'],
        'Lat': [35.6895, 40.7128, 51.5074, 1.3521, 47.3769, 22.3193],
        'Lon': [139.6917, -74.0060, -0.1278, 103.8198, 8.5417, 114.1694],
        'Status': ['Online', 'Online', 'Online', 'Online', 'Online', 'Online'],
        'Signals': [5, 3, 2, 4, 1, 3]
    })
    fig = px.scatter_geo(node_data, lat='Lat', lon='Lon', hover_name='City',
                         size='Signals', color='Status',
                         projection="natural earth",
                         color_discrete_map={'Online': 'lime'})
    fig.update_geos(showcountries=True, countrycolor="#333", showocean=True, oceancolor="#000",
                    showcoastlines=True, coastlinecolor="#444", bgcolor="#000")
    fig.update_layout(height=400, margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

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
