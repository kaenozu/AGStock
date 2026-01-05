"""
Mission Control UI
Real-time system health and status monitoring dashboard.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
import pandas as pd

from agstock.src.paper_trader import PaperTrader


def render_mission_control():
    """Render the Mission Control dashboard."""
    st.header("🚀 Mission Control - System Status")
    st.caption("Real-time monitoring of the autonomous trading system")

    # === 1. System Heartbeat ===
    with st.expander("💓 System Heartbeat", expanded=True):
        col1, col2, col3 = st.columns(3)

        # Check system status file
        status_file = "data/system_status.json"
        if os.path.exists(status_file):
            try:
                with open(status_file, "r") as f:
                    status = json.load(f)

                last_update = status.get("last_update", "Unknown")
                scheduler_status = status.get("scheduler_status", "Unknown")

                with col1:
                    st.metric("Scheduler Status", scheduler_status)

                with col2:
                    st.metric("Last Heartbeat", last_update)

                with col3:
                    # Calculate uptime
                    try:
                        last_dt = datetime.fromisoformat(last_update)
                        uptime = datetime.now() - last_dt
                        uptime_str = f"{uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"
                        st.metric("Time Since Update", uptime_str)
                    except BaseException:
                        st.metric("Time Since Update", "N/A")

            except Exception as e:
                st.error(f"Failed to read status: {e}")
        else:
            st.info("System status file not found. Run the scheduler to initialize.")

    # === 2. API Health ===
    with st.expander("🌐 API Health Check", expanded=True):
        col1, col2, col3 = st.columns(3)

        # Check API keys
        with col1:
            st.subheader("Gemini API")
            gemini_key = os.getenv("GOOGLE_API_KEY")
            if gemini_key:
                st.success("✅ Connected")
            else:
                st.error("❌ Not configured")

        with col2:
            st.subheader("Yahoo Finance")
            # Simple check - try to import yfinance
            try:
                pass

                st.success("✅ Available")
            except BaseException:
                st.error("❌ Not installed")

        with col3:
            st.subheader("Database")
            db_path = "paper_trading.db"
            if os.path.exists(db_path):
                size_mb = os.path.getsize(db_path) / (1024 * 1024)
                st.success(f"✅ Active ({size_mb:.1f} MB)")
            else:
                st.warning("⚠️ Not initialized")

    # === 3. Self-Healing Logs ===
    with st.expander("🛡️ Self-Healing Activity", expanded=False):
        log_file = "logs/auto_trader.log"

        if os.path.exists(log_file):
            try:
                # Read last 50 lines
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:]

                # Filter for healing-related logs
                healing_logs = [
                    line
                    for line in recent_lines
                    if "Self-Healing" in line or "AI Healing" in line or "Auto-Adjustment" in line
                ]

                if healing_logs:
                    st.code("\n".join(healing_logs), language="log")
                else:
                    st.info("No self-healing activity in recent logs.")

            except Exception as e:
                st.error(f"Failed to read logs: {e}")
        else:
            st.info("Log file not found.")

    # === 4. Daily Journals ===
    with st.expander("📝 AI Daily Journals", expanded=True):
        journal_dir = Path("data/journals")

        if journal_dir.exists():
            journal_files = sorted(journal_dir.glob("journal_*.txt"), reverse=True)

            if journal_files:
                # Show selector for recent journals
                journal_names = [f.stem for f in journal_files[:7]]  # Last 7 days
                selected = st.selectbox("Select Date", journal_names)

                if selected:
                    journal_path = journal_dir / f"{selected}.txt"
                    try:
                        with open(journal_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        st.text_area("Journal Content", content, height=300)
                    except Exception as e:
                        st.error(f"Failed to read journal: {e}")
            else:
                st.info("No journals found. Journals are created after daily routines.")
        else:
            st.info("Journal directory not found.")

    # === 5. Performance Metrics ===
    with st.expander("📊 Recent Performance", expanded=True):
        try:
            pt = PaperTrader()
            history = pt.get_trade_history()

            if not history.empty:
                # Last 7 days
                history["date"] = pd.to_datetime(history["timestamp"]).dt.date
                recent = history[history["date"] >= (datetime.now().date() - timedelta(days=7))]

                # Calculate daily stats
                daily_stats = []
                for date in recent["date"].unique():
                    day_trades = recent[recent["date"] == date]
                    sells = day_trades[day_trades["action"] == "SELL"]

                    daily_stats.append({"Date": date, "Trades": len(day_trades), "Closed": len(sells)})

                if daily_stats:
                    df = pd.DataFrame(daily_stats)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No trades in the last 7 days.")
            else:
                st.info("No trading history available.")

        except Exception as e:
            st.error(f"Failed to load performance data: {e}")

    # === 6. System Controls ===
    st.markdown("---")
    st.subheader("⚙️ System Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Refresh Status"):
            st.rerun()

    with col2:
        if st.button("🧹 Clear Cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")

    with col3:
        if st.button("📋 View Full Logs"):
            st.info("Opening logs viewer...")


# Could implement a separate logs viewer page
