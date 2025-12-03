"""
Monitoring Dashboard Module
Real-time system monitoring and health visualization.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import psutil
from src.metrics_collector import MetricsCollector
from src.anomaly_detector import AnomalyDetector

def render_monitoring_dashboard():
    st.header("📊 システム監視ダッシュボード")
    st.write("リアルタイムでシステムの状態を監視します。")
    
    # Auto-refresh
    if st.checkbox("自動更新 (30秒)", value=True):
        st.rerun()
    
    # System Health
    render_system_health()
    
    st.markdown("---")
    
    # Metrics
    col1, col2 = st.columns(2)
    
    with col1:
        render_api_metrics()
    
    with col2:
        render_trade_metrics()
    
    st.markdown("---")
    
    # Alerts
    render_alerts()

def render_system_health():
    st.subheader("🏥 システムヘルス")
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # CPU
    cpu_color = "normal" if cpu_percent < 70 else "inverse"
    col1.metric(
        "CPU使用率",
        f"{cpu_percent:.1f}%",
        delta=None,
        delta_color=cpu_color
    )
    
    # Memory
    mem_color = "normal" if memory.percent < 80 else "inverse"
    col2.metric(
        "メモリ使用率",
        f"{memory.percent:.1f}%",
        delta=None,
        delta_color=mem_color
    )
    
    # Disk
    disk_color = "normal" if disk.percent < 85 else "inverse"
    col3.metric(
        "ディスク使用率",
        f"{disk.percent:.1f}%",
        delta=None,
        delta_color=disk_color
    )
    
    # Uptime
    try:
        import time
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = uptime_seconds / 3600
        col4.metric(
            "稼働時間",
            f"{uptime_hours:.1f}h"
        )
    except:
        col4.metric("稼働時間", "N/A")
    
    # Health status
    if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
        st.error("⚠️ システムリソースが逼迫しています")
    elif cpu_percent > 70 or memory.percent > 80 or disk.percent > 85:
        st.warning("⚡ システムリソースに注意が必要です")
    else:
        st.success("✅ システムは正常に動作しています")

def render_api_metrics():
    st.subheader("📡 API メトリクス")
    
    try:
        collector = MetricsCollector()
        
        # Success rate
        success_rate = collector.get_api_success_rate(hours=24)
        
        col1, col2 = st.columns(2)
        col1.metric("成功率 (24h)", f"{success_rate:.1%}")
        
        # Recent errors
        errors = collector.get_recent_errors(limit=5)
        
        if errors:
            st.write("**最近のエラー:**")
            error_df = pd.DataFrame(errors, columns=['時刻', 'タイプ', 'メッセージ', 'モジュール'])
            st.dataframe(error_df, hide_index=True, use_container_width=True)
        else:
            st.info("エラーなし")
            
    except Exception as e:
        st.error(f"メトリクス取得エラー: {e}")

def render_trade_metrics():
    st.subheader("💹 トレードメトリクス")
    
    try:
        from src.paper_trader import PaperTrader
        pt = PaperTrader()
        
        # Today's trades
        history = pt.get_trade_history()
        
        if not history.empty and 'timestamp' in history.columns:
            history['timestamp'] = pd.to_datetime(history['timestamp'])
            today = datetime.now().date()
            today_trades = history[history['timestamp'].dt.date == today]
            
            col1, col2 = st.columns(2)
            col1.metric("本日の取引", f"{len(today_trades)}件")
            
            if 'realized_pnl' in today_trades.columns:
                today_pnl = today_trades['realized_pnl'].sum()
                col2.metric("本日の損益", f"¥{today_pnl:,.0f}")
        else:
            st.info("取引データなし")
            
    except Exception as e:
        st.error(f"トレードメトリクス取得エラー: {e}")

def render_alerts():
    st.subheader("🚨 アラート履歴")
    
    try:
        detector = AnomalyDetector()
        anomalies = detector.run_all_checks()
        
        if anomalies:
            for anomaly in anomalies:
                severity = anomaly['severity']
                message = anomaly['message']
                
                if severity == 'CRITICAL':
                    st.error(f"🔴 **CRITICAL**: {message}")
                elif severity == 'WARNING':
                    st.warning(f"🟡 **WARNING**: {message}")
                else:
                    st.info(f"🔵 **INFO**: {message}")
        else:
            st.success("✅ アラートなし - システムは正常です")
            
    except Exception as e:
        st.error(f"アラート取得エラー: {e}")

if __name__ == "__main__":
    render_monitoring_dashboard()
