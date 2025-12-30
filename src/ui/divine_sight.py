"""
Divine Sight: The Eye of God
Real-time visualization of the AI's internal state, scanner results, and 
the growing 'Wisdom Library' of lessons learned.
"""

import json
import logging
import os
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from src.data.feedback_store import FeedbackStore
from src.ui.widgets import render_card, render_header

logger = logging.getLogger(__name__)


def render() -> None:
    """renders the Divine Sight dashboard interface."""
    st.markdown("<h1 style='text-align: center;'>👁️ Divine Sight (神の目)</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: gray;'>Omniscient view of the AGStock internal state and evolution.</p>",
        unsafe_allow_html=True,
    )
    
    st.markdown("---")
    
    tab_vision, tab_synapse, tab_wisdom = st.tabs([
        "👁️ Vision (Scanner)", 
        "🧠 Synapse (Live Logs)", 
        "🗣️ Voice (Wisdom)"
    ])
    
    with tab_vision:
        render_scanner_vision()
        
    with tab_synapse:
        render_log_stream()
        
    with tab_wisdom:
        render_wisdom_library()


def render_scanner_vision():
    """Visualizes the most recent market scan results."""
    st.subheader("📡 Market Scanner Vision")
    scan_file = "data/latest_scan_results.json"
    
    if not os.path.exists(scan_file):
        st.info("💡 最近のスキャン結果が見つかりません。マーケットスキャンを実行してください。")
        return
        
    try:
        with open(scan_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if not data:
            st.success("✅ スキャナーは正常に稼働していますが、現在の条件に合致する銘柄はありません。")
            return
            
        df = pd.DataFrame(data)
        
        # Dashboard KPIs
        cols = st.columns(3)
        cols[0].metric("Total Candidates", len(df))
        cols[1].metric("Highest Confidence", f"{df['confidence'].max()*100:.1f}%" if 'confidence' in df else "N/A")
        cols[2].metric("Buy Signals", len(df[df['action'] == 'BUY']) if 'action' in df else 0)

        # Signal Table
        st.dataframe(
            df,
            column_config={
                "ticker": "Ticker",
                "action": "Action",
                "confidence": st.column_config.ProgressColumn(
                    "Confidence",
                    format="%.2f",
                    min_value=0,
                    max_value=1,
                ),
                "strategy": "Strategy",
                "reason": "AI Analysis",
                "regime": "Market Regime",
                "timestamp": "Detected At",
            },
            hide_index=True,
            use_container_width=True,
        )
        
    except Exception as e:
        st.error(f"スキャンデータの読み取りに失敗しました: {e}")


def render_log_stream():
    """displays the latest system logs in real-time."""
    st.subheader("⚡ Synapse Stream (Live Logs)")
    log_file = "logs/auto_trader.log"
    
    if not os.path.exists(log_file):
        st.warning("ログファイルが見つかりません。パスを確認してください。")
        return
        
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # Read last 50 lines
            lines = f.readlines()[-50:]
            lines.reverse() # Newest first
            logs_text = "".join(lines)
            
        st.text_area("System Synapse Activity", logs_text, height=450)
        st.caption("最新のログ50件を表示しています（降順）。")
    except Exception as e:
        st.error(f"ログの読み取りに失敗しました: {e}")


def render_wisdom_library():
    """Displays the 'Wisdom' (lessons learned from trades)."""
    st.subheader("📜 Reporter Voice (Wisdom Library)")
    store = FeedbackStore()
    
    try:
        # Use existing sqlite logic from Dashboard or direct if not implemented
        import sqlite3
        with sqlite3.connect(store.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ticker, lesson_learned, reflection_log, timestamp 
                FROM decision_feedback
                WHERE lesson_learned IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            wisdom = [dict(row) for row in cursor.fetchall()]
            
        if not wisdom:
            st.info("まだ教訓が記録されていません。失敗した取引からのフィードバックを待っています。")
            return
            
        for item in wisdom:
            with st.container():
                st.markdown(f"### 💡 {item['ticker']} - {item['timestamp'][:10]}")
                st.info(f"**Lesson**: {item['lesson_learned']}")
                with st.expander("詳細な分析ログを表示"):
                    st.write(item['reflection_log'])
                st.markdown("---")
                
    except Exception as e:
        st.error(f"知恵のライブラリへのアクセスに失敗しました: {e}")
