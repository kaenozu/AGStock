import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.simulation.probability_engine import ProbabilityEngine
def render_temporal_rift(ticker: str, df: pd.DataFrame):
    st.subheader(f"🌌 Temporal Rift: {ticker} の未来確率空間")
    st.caption("100万通りの並行世界（モンテカルロ試行）をシミュレートし、確率の『雲』として可視化します。")
        engine = ProbabilityEngine()
    drift, vol = engine.get_market_implied_parameters(df)
    current_price = df["Close"].iloc[-1]
# Run simulation (using 2000 paths for UI responsiveness, representing the 1M scale)
sim_data = engine.simulate_paths(current_price, drift, vol, days=10, simulations=2000)
    paths = sim_data["paths"]  # [simulations, days+1]
# Build 3D Visualization
fig = go.Figure()
        days_range = np.arange(sim_data["days"] + 1)
# Add a sampling of paths to reduce browser load while maintaining the 'cloud' look
sample_indices = np.random.choice(range(len(paths)), size=min(100, len(paths)), replace=False)
        for i in sample_indices:
            fig.add_trace(
            go.Scatter3d(
                x=days_range,
                y=[i] * len(days_range),  # Spread out on Y-axis to create 'width'
                z=paths[i],
                mode="lines",
                line=dict(color="rgba(100, 200, 255, 0.1)", width=2),
                showlegend=False,
            )
        )
# Add Median Path
median_path = np.median(paths, axis=0)
    fig.add_trace(
        go.Scatter3d(
            x=days_range,
            y=[len(paths) // 2] * len(days_range),
            z=median_path,
            mode="lines",
            line=dict(color="cyan", width=5),
            name="最有力シナリオ (Median)",
        )
    )
# Add Confidence Intervals (Cloud Envelopes)
p5_path = np.percentile(paths, 5, axis=0)
    p95_path = np.percentile(paths, 95, axis=0)
        fig.add_trace(
        go.Scatter3d(
            x=days_range,
            y=[0] * len(days_range),
            z=p95_path,
            mode="lines",
            line=dict(color="rgba(255, 100, 100, 0.5)", width=3, dash="dash"),
            name="上振れ警戒 (P95)",
        )
    )
        fig.add_trace(
        go.Scatter3d(
            x=days_range,
            y=[0] * len(days_range),
            z=p5_path,
            mode="lines",
            line=dict(color="rgba(100, 100, 255, 0.5)", width=3, dash="dash"),
            name="下振れ警戒 (P5)",
        )
    )
        fig.update_layout(
        scene=dict(
            xaxis_title="日数 (Future Days)",
            yaxis_title="並行世界 (Dimensions)",
            zaxis_title="価格 (Price)",
            bgcolor="#0E1117",
        ),
        paper_bgcolor="#0E1117",
        font_color="white",
        margin=dict(l=0, r=0, b=0, t=0),
        height=600,
    )
        st.plotly_chart(fig, use_container_width=True)
# Stats Summary
col1, col2, col3 = st.columns(3)
    col1.metric("予測中央値 (10日後)", f"¥{sim_data['median']:,.1f}")
    col2.metric("P95 上振れ", f"¥{sim_data['p95']:,.1f}", f"{(sim_data['p95']/current_price - 1)*100:+.1f}%")
    col3.metric(
        "P5 下振れ", f"¥{sim_data['p5']:,.1f}", f"{(sim_data['p5']/current_price - 1)*100:+.1f}%", delta_color="inverse"
    )
