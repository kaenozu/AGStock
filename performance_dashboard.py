#!/usr/bin/env python3
"""
AGStock Performance Monitoring Dashboard
リアルタイムシステムパフォーマンス監視ダッシュボード
"""

import streamlit as st
import psutil
import time
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import json
import os
from typing import Dict, List, Any
import threading
import asyncio


class PerformanceMonitor:
    """システムパフォーマンス監視クラス"""

    def __init__(self):
        self.start_time = datetime.now()
        self.performance_history = []
        self.alerts = []
        self.thresholds = {
            "cpu_warning": 80,
            "cpu_critical": 95,
            "memory_warning": 80,
            "memory_critical": 95,
            "disk_warning": 85,
            "disk_critical": 95,
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス取得"""
        try:
            metrics = {
                "timestamp": datetime.now(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent
                if os.name != "nt"
                else psutil.disk_usage("C:").percent,
                "memory_available": psutil.virtual_memory().available / (1024**3),  # GB
                "memory_total": psutil.virtual_memory().total / (1024**3),  # GB
                "cpu_count": psutil.cpu_count(),
                "load_avg": None,  # Windowsではサポートされていないため無効化
                "uptime": (datetime.now() - self.start_time).total_seconds(),
            }

            # ネットワーク統計
            net_io = psutil.net_io_counters()
            metrics["network_bytes_sent"] = net_io.bytes_sent
            metrics["network_bytes_recv"] = net_io.bytes_recv

            # プロセス情報
            metrics["process_count"] = len(psutil.pids())

            return metrics

        except Exception as e:
            st.error(f"システムメトリクス取得エラー: {e}")
            return {}

    def get_trading_performance(self) -> Dict[str, Any]:
        """取引パフォーマンスメトリクス取得"""
        try:
            # 過去の取引データから計算
            trading_log_file = "logs/trading_log.json"
            if os.path.exists(trading_log_file):
                with open(trading_log_file, "r") as f:
                    logs = json.load(f)

                recent_logs = [log for log in logs[-100:] if log.get("timestamp")]

                if recent_logs:
                    total_trades = len(recent_logs)
                    successful_trades = len(
                        [log for log in recent_logs if log.get("status") == "success"]
                    )
                    avg_execution_time = (
                        sum(log.get("execution_time", 0) for log in recent_logs)
                        / total_trades
                    )

                    return {
                        "total_trades": total_trades,
                        "success_rate": (successful_trades / total_trades) * 100,
                        "avg_execution_time_ms": avg_execution_time * 1000,
                        "last_trade_time": recent_logs[-1].get("timestamp")
                        if recent_logs
                        else None,
                    }

            return {
                "total_trades": 0,
                "success_rate": 0,
                "avg_execution_time_ms": 0,
                "last_trade_time": None,
            }

        except Exception as e:
            st.error(f"取引パフォーマンス取得エラー: {e}")
            return {}

    def check_alerts(self, metrics: Dict[str, Any]) -> List[str]:
        """アラートチェック"""
        new_alerts = []

        if metrics.get("cpu_percent", 0) > self.thresholds["cpu_critical"]:
            new_alerts.append("🚨 CPU使用率が危機的レベルです！")
        elif metrics.get("cpu_percent", 0) > self.thresholds["cpu_warning"]:
            new_alerts.append("⚠️ CPU使用率が警告レベルです")

        if metrics.get("memory_percent", 0) > self.thresholds["memory_critical"]:
            new_alerts.append("🚨 メモリ使用率が危機的レベルです！")
        elif metrics.get("memory_percent", 0) > self.thresholds["memory_warning"]:
            new_alerts.append("⚠️ メモリ使用率が警告レベルです")

        if metrics.get("disk_percent", 0) > self.thresholds["disk_critical"]:
            new_alerts.append("🚨 ディスク使用率が危機的レベルです！")
        elif metrics.get("disk_percent", 0) > self.thresholds["disk_warning"]:
            new_alerts.append("⚠️ ディスク使用率が警告レベルです")

        return new_alerts

    def update_history(self, metrics: Dict[str, Any]):
        """パフォーマンス履歴更新"""
        self.performance_history.append(metrics)
        # 履歴を100件に制限
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]


def create_gauge_chart(
    value: float, title: str, max_value: float = 100, thresholds: tuple = (70, 90)
) -> go.Figure:
    """ゲージチャート作成"""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title},
            delta={"reference": thresholds[0]},
            gauge={
                "axis": {"range": [None, max_value]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, thresholds[0]], "color": "lightgray"},
                    {"range": [thresholds[0], thresholds[1]], "color": "yellow"},
                    {"range": [thresholds[1], max_value], "color": "lightcoral"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": thresholds[1],
                },
            },
        )
    )

    fig.update_layout(height=300)
    return fig


def create_time_series_chart(
    data: List[Dict], metric: str, title: str, color: str = "blue"
) -> go.Figure:
    """時系列チャート作成"""
    if not data:
        return go.Figure()

    df = pd.DataFrame(data)
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df[metric],
            mode="lines+markers",
            name=title,
            line=dict(color=color, width=2),
            marker=dict(size=4),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="時刻",
        yaxis_title=metric,
        height=300,
        showlegend=False,
    )

    return fig


def main():
    """メイン実行関数"""
    st.set_page_config(
        page_title="AGStock パフォーマンス監視",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🔍 AGStock パフォーマンス監視ダッシュボード")
    st.markdown("---")

    # パフォーマンスモニター初期化
    if "monitor" not in st.session_state:
        st.session_state.monitor = PerformanceMonitor()
        st.session_state.auto_refresh = True

    monitor = st.session_state.monitor

    # サイドバー設定
    st.sidebar.title("⚙️ 設定")

    # 自動更新
    st.session_state.auto_refresh = st.sidebar.checkbox(
        "🔄 自動更新", value=st.session_state.auto_refresh
    )

    if st.session_state.auto_refresh:
        refresh_interval = st.sidebar.selectbox("更新間隔", [1, 5, 10, 30], index=1)
    else:
        refresh_interval = None

    # しきい値設定
    st.sidebar.subheader("🚨 アラートしきい値")
    monitor.thresholds["cpu_warning"] = st.sidebar.slider(
        "CPU警告 (%)", 50, 95, monitor.thresholds["cpu_warning"]
    )
    monitor.thresholds["cpu_critical"] = st.sidebar.slider(
        "CPU危機 (%)", 70, 100, monitor.thresholds["cpu_critical"]
    )
    monitor.thresholds["memory_warning"] = st.sidebar.slider(
        "メモリ警告 (%)", 50, 95, monitor.thresholds["memory_warning"]
    )
    monitor.thresholds["memory_critical"] = st.sidebar.slider(
        "メモリ危機 (%)", 70, 100, monitor.thresholds["memory_critical"]
    )

    # メトリクス取得
    system_metrics = monitor.get_system_metrics()
    trading_metrics = monitor.get_trading_performance()

    # 履歴更新
    if system_metrics:
        monitor.update_history(system_metrics)
        new_alerts = monitor.check_alerts(system_metrics)
        monitor.alerts.extend(new_alerts)

    # アラート表示
    if monitor.alerts:
        st.error("🚨 アラート")
        for alert in monitor.alerts[-5:]:  # 最新5件
            st.error(alert)

        if st.button("🗑️ アラートをクリア"):
            monitor.alerts = []

    # メインダッシュボード
    col1, col2, col3 = st.columns(3)

    with col1:
        if system_metrics:
            fig_cpu = create_gauge_chart(
                system_metrics.get("cpu_percent", 0), "CPU使用率 (%)"
            )
            st.plotly_chart(fig_cpu, use_container_width=True)

    with col2:
        if system_metrics:
            fig_memory = create_gauge_chart(
                system_metrics.get("memory_percent", 0), "メモリ使用率 (%)"
            )
            st.plotly_chart(fig_memory, use_container_width=True)

    with col3:
        if system_metrics:
            fig_disk = create_gauge_chart(
                system_metrics.get("disk_percent", 0), "ディスク使用率 (%)"
            )
            st.plotly_chart(fig_disk, use_container_width=True)

    # システム情報
    st.subheader("📊 システム情報")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("CPUコア数", system_metrics.get("cpu_count", "N/A"))

    with col2:
        memory_gb = f"{system_metrics.get('memory_available', 0):.1f}/{system_metrics.get('memory_total', 0):.1f} GB"
        st.metric("利用可能メモリ", memory_gb)

    with col3:
        uptime_hours = system_metrics.get("uptime", 0) / 3600
        st.metric("稼働時間", f"{uptime_hours:.1f} 時間")

    with col4:
        st.metric("プロセス数", system_metrics.get("process_count", "N/A"))

    # 取引パフォーマンス
    st.subheader("💹 取引パフォーマンス")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("総取引数", trading_metrics.get("total_trades", 0))

    with col2:
        success_rate = trading_metrics.get("success_rate", 0)
        st.metric("成功率", f"{success_rate:.1f}%")

    with col3:
        exec_time = trading_metrics.get("avg_execution_time_ms", 0)
        st.metric("平均実行時間", f"{exec_time:.1f} ms")

    with col4:
        last_trade = trading_metrics.get("last_trade_time", "N/A")
        st.metric("最終取引", last_trade[:19] if last_trade != "N/A" else "N/A")

    # 履歴グラフ
    if len(monitor.performance_history) > 1:
        st.subheader("📈 パフォーマンス履歴")

        col1, col2 = st.columns(2)

        with col1:
            fig_cpu_history = create_time_series_chart(
                monitor.performance_history, "cpu_percent", "CPU使用率履歴", "blue"
            )
            st.plotly_chart(fig_cpu_history, use_container_width=True)

        with col2:
            fig_memory_history = create_time_series_chart(
                monitor.performance_history,
                "memory_percent",
                "メモリ使用率履歴",
                "green",
            )
            st.plotly_chart(fig_memory_history, use_container_width=True)

    # ネットワーク統計
    if system_metrics and "network_bytes_sent" in system_metrics:
        st.subheader("🌐 ネットワーク統計")
        col1, col2 = st.columns(2)

        with col1:
            bytes_sent_gb = system_metrics["network_bytes_sent"] / (1024**3)
            st.metric("送信データ", f"{bytes_sent_gb:.2f} GB")

        with col2:
            bytes_recv_gb = system_metrics["network_bytes_recv"] / (1024**3)
            st.metric("受信データ", f"{bytes_recv_gb:.2f} GB")

    # 自動更新
    if st.session_state.auto_refresh and refresh_interval:
        st.markdown(f"🔄 {refresh_interval}秒ごとに自動更新中...")
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
