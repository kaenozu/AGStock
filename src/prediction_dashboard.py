"""
予測精度分析ダッシュボード
バックテスト結果を可視化し、予測の信頼性を評価します。
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.prediction_backtester import PredictionBacktester
from datetime import datetime, timedelta

def create_prediction_analysis_dashboard():
    """
    予測精度分析ダッシュボードを表示
    """
    st.title("🎯 予測精度分析")
    st.markdown("---")
    
    # バックテスト設定
    st.subheader("📊 バックテスト設定")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ticker = st.text_input("ティッカー", value="8308.T")
    
    with col2:
        # デフォルトは過去3ヶ月
        default_start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        start_date = st.date_input("開始日", value=pd.to_datetime(default_start))
    
    with col3:
        end_date = st.date_input("終了日", value=datetime.now())
    
    prediction_days = st.slider("予測日数", min_value=1, max_value=10, value=5)
    
    if st.button("🚀 バックテスト実行", type="primary", use_container_width=True):
        with st.spinner("バックテスト実行中...（数分かかる場合があります）"):
            backtester = PredictionBacktester()
            
            result = backtester.run_backtest(
                ticker=ticker,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                prediction_days=prediction_days
            )
            
            if "error" in result:
                st.error(f"❌ エラー: {result['error']}")
                return
            
            # 結果を session_state に保存
            st.session_state['backtest_result'] = result
    
    # 結果表示
    if 'backtest_result' in st.session_state:
        result = st.session_state['backtest_result']
        
        st.markdown("---")
        st.subheader("📈 バックテスト結果")
        
        # メトリクス表示
        metrics = result['metrics']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "方向性正解率",
                f"{metrics['direction_accuracy']:.1f}%",
                help="UP/DOWN/FLATの予測が実際と一致した割合"
            )
        
        with col2:
            st.metric(
                "Win Rate",
                f"{metrics['win_rate']:.1f}%",
                help="予測に従って取引した場合の勝率"
            )
        
        with col3:
            st.metric(
                "平均誤差 (MAE)",
                f"{metrics['mae']:.2f}%",
                help="予測変動率と実際の変動率の平均誤差"
            )
        
        with col4:
            st.metric(
                "予測回数",
                f"{metrics['total_samples']}回",
                help="バックテストで実行した予測の総数"
            )
        
        # 詳細グラフ
        st.markdown("---")
        st.subheader("📊 詳細分析")
        
        predictions_df = pd.DataFrame(result['predictions'])
        
        # 1. 予測 vs 実際の変動率
        fig1 = go.Figure()
        
        fig1.add_trace(go.Scatter(
            x=predictions_df['date'],
            y=predictions_df['predicted_change_pct'],
            mode='lines+markers',
            name='予測変動率',
            line=dict(color='blue', width=2)
        ))
        
        fig1.add_trace(go.Scatter(
            x=predictions_df['date'],
            y=predictions_df['actual_change_pct'],
            mode='lines+markers',
            name='実際の変動率',
            line=dict(color='green', width=2)
        ))
        
        fig1.update_layout(
            title="予測変動率 vs 実際の変動率",
            xaxis_title="日付",
            yaxis_title="変動率 (%)",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # 2. 誤差の分布
        fig2 = go.Figure()
        
        errors = predictions_df['predicted_change_pct'] - predictions_df['actual_change_pct']
        
        fig2.add_trace(go.Histogram(
            x=errors,
            nbinsx=30,
            name='誤差分布',
            marker_color='lightblue'
        ))
        
        fig2.update_layout(
            title="予測誤差の分布",
            xaxis_title="誤差 (%)",
            yaxis_title="頻度",
            height=300
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # 3. トレンド予測の精度
        st.markdown("### 🎯 トレンド予測の詳細")
        
        trend_comparison = predictions_df.groupby(['predicted_trend', 'actual_trend']).size().unstack(fill_value=0)
        
        if not trend_comparison.empty:
            st.dataframe(trend_comparison, use_container_width=True)
        
        # 4. 予測詳細テーブル
        st.markdown("### 📋 予測詳細")
        
        display_df = predictions_df[[
            'date', 'current_price', 'predicted_price', 'actual_price',
            'predicted_change_pct', 'actual_change_pct', 'predicted_trend', 'actual_trend'
        ]].copy()
        
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
        display_df.columns = [
            '日付', '基準価格', '予測価格', '実際価格',
            '予測変動%', '実際変動%', '予測トレンド', '実際トレンド'
        ]
        
        # 数値フォーマット
        for col in ['基準価格', '予測価格', '実際価格']:
            display_df[col] = display_df[col].apply(lambda x: f"¥{x:,.2f}")
        
        for col in ['予測変動%', '実際変動%']:
            display_df[col] = display_df[col].apply(lambda x: f"{x:+.2f}%")
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # ダウンロードボタン
        csv = predictions_df.to_csv(index=False)
        st.download_button(
            label="📥 結果をCSVでダウンロード",
            data=csv,
            file_name=f"backtest_{result['ticker']}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
