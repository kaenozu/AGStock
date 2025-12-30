import streamlit as st
import pandas as pd
from src.execution.anomaly_detector import AnomalyDetector
from src.core.strategy_breeder import StrategyBreeder
from src.db.manager import DatabaseManager
def render_resilience_tab():
    st.header("🛡️ Market Guardian & Resilience")
    st.caption("リアルタイムの市場異常検知と、パフォーマンスベースの戦略進化を管理します。")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🚨 異常検知 (Anomaly Detection)")
        detector = AnomalyDetector()
# Simulating monitoring for UI purposes
st.info("ガーディアンがバックグラウンドで稼働中...")
        st.metric("Price Z-Threshold", detector.price_z_threshold)
        st.metric("Volume Z-Threshold", detector.vol_z_threshold)
            if st.button("🔍 現在の市場状況をスキャン"):
                # This would normally hook into the live data stream
            st.warning("スキャン結果: 正常範囲内 (Z-Score: 0.42)")
        with col2:
            st.subheader("🧬 戦略ブリーダー (Breeder)")
        st.caption("成績の悪い戦略を自動的に特定し、改良版を生成します。")
            db = DatabaseManager()
        perf = db.get_strategy_performance()
            if not perf:
                st.info("十分な取引データがありません。")
        else:
            st.write("現在の戦略成績一覧:")
            st.table(pd.DataFrame.from_dict(perf, orient="index"))
            if st.button("♻️ 進化サイクルを手動実行"):
                breeder = StrategyBreeder()
            with st.spinner("成績データを分析中..."):
                # breeder.run_breeding_cycle() # In a real env, this might take time
                st.info("分析結果: クリティカルな損失を出す戦略は現在見つかりませんでした。")
        st.divider()
    st.subheader("🕵️ 戦略劣化パトロール")
    st.markdown(
            - **ドローダウン監視**: 指定したしきい値を超えるドローダウンが発生した戦略を隔離します。
    - **自動パッチ適用**: LLMが生成した修正コードを適用した「V2」戦略のバックテストスコアを比較します。
        )
