"""
Prediction Breakdown UI Component
各モデルの予測詳細を表示するStreamlitコンポーネント
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any

def render_prediction_breakdown(prediction_result: Dict[str, Any]):
    """
    予測結果の詳細な内訳を表示
    
    Args:
        prediction_result: EnhancedEnsemblePredictor.predict_point() の結果
    """
    
    st.subheader("📊 予測モデル詳細分析")
    
    # Extract data
    final_prediction = prediction_result.get("final_prediction", 0)
    confidence = prediction_result.get("confidence_score", 0)
    ensemble_signals = prediction_result.get("ensemble_signals", {})
    market_regime = prediction_result.get("market_regime", "UNKNOWN")
    
    # Top summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="アンサンブル予測",
            value=f"¥{final_prediction:,.2f}",
            delta=f"{((final_prediction / prediction_result.get('current_price', final_prediction)) - 1) * 100:.2f}%"
        )
    
    with col2:
        st.metric(
            label="信頼度スコア",
            value=f"{confidence:.1%}"
        )
        st.progress(confidence)
    
    with col3:
        regime_emoji = {
            "Bullish": "📈",
            "Bearish": "📉",
            "Sideways": "➡️",
            "UNKNOWN": "❓"
        }
        st.metric(
            label="市場レジーム",
            value=f"{regime_emoji.get(market_regime, '❓')} {market_regime}"
        )
    
    st.divider()
    
    # Model-by-model breakdown
    st.subheader("🔍 モデル別予測内訳")
    
    if ensemble_signals:
        # Define model colors and names
        model_info = {
            "LGBM": {"color": "#1f77b4", "name": "LightGBM", "icon": "🌳"},
            "Prophet": {"color": "#2ca02c", "name": "Prophet", "icon": "📅"},
            "LSTM": {"color": "#ff7f0e", "name": "LSTM", "icon": "🧠"},
            "TFT": {"color": "#9467bd", "name": "Transformer", "icon": "⚡"},
            "Advanced": {"color": "#8c564b", "name": "Advanced LSTM", "icon": "🚀"}
        }
        
        # Create columns for each model
        num_models = len(ensemble_signals)
        cols = st.columns(min(num_models, 3))
        
        for idx, (model_key, signal_value) in enumerate(ensemble_signals.items()):
            col_idx = idx % 3
            with cols[col_idx]:
                info = model_info.get(model_key, {"color": "#gray", "name": model_key, "icon": "📊"})
                
                # Model card
                st.markdown(f"### {info['icon']} {info['name']}")
                
                # Signal value (could be change %, price, etc.)
                if isinstance(signal_value, (int, float)):
                    signal_pct = signal_value * 100 if abs(signal_value) < 1 else signal_value
                    
                    # Color based on signal
                    if signal_pct > 0:
                        st.markdown(f"<h2 style='color: green;'>+{signal_pct:.2f}%</h2>", unsafe_allow_html=True)
                    elif signal_pct < 0:
                        st.markdown(f"<h2 style='color: red;'>{signal_pct:.2f}%</h2>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<h2 style='color: gray;'>{signal_pct:.2f}%</h2>", unsafe_allow_html=True)
                else:
                    st.write(signal_value)
        
        # Visualization: Bar chart of model signals
        st.subheader("📊 モデル信号の比較")
        
        fig = go.Figure()
        
        model_names = []
        signal_values = []
        colors = []
        
        for model_key, signal_value in ensemble_signals.items():
            if isinstance(signal_value, (int, float)):
                info = model_info.get(model_key, {"color": "#gray", "name": model_key})
                model_names.append(info['name'])
                signal_values.append(signal_value * 100 if abs(signal_value) < 1 else signal_value)
                colors.append(info['color'])
        
        fig.add_trace(go.Bar(
            x=model_names,
            y=signal_values,
            marker_color=colors,
            text=[f"{v:.2f}%" for v in signal_values],
            textposition='outside'
        ))
        
        fig.update_layout(
            title="各モデルの予測シグナル",
            xaxis_title="モデル",
            yaxis_title="変化率 (%)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("モデル別の詳細データが利用できません")
    
    # Additional insights (if available)
    with st.expander("🔬 詳細な分析情報"):
        st.json(prediction_result)


def render_model_confidence_breakdown(ensemble_weights: Dict[str, float]):
    """
    各モデルの重み（信頼度）を表示
    
    Args:
        ensemble_weights: モデル名 -> 重み のマッピング
    """
    st.subheader("⚖️ モデル重み配分")
    
    if not ensemble_weights:
        st.info("重み情報が利用できません")
        return
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=list(ensemble_weights.keys()),
        values=list(ensemble_weights.values()),
        hole=0.3
    )])
    
    fig.update_layout(
        title="アンサンブル内のモデル重み",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Table view
    df = pd.DataFrame({
        "モデル": list(ensemble_weights.keys()),
        "重み": [f"{v:.1%}" for v in ensemble_weights.values()]
    })
    
    st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    # Demo
    st.set_page_config(page_title="Prediction Breakdown Demo", layout="wide")
    
    st.title("予測詳細分析 - デモ")
    
    # Mock data
    mock_result = {
        "final_prediction": 3250.50,
        "current_price": 3200.00,
        "confidence_score": 0.78,
        "market_regime": "Bullish",
        "ensemble_signals": {
            "LGBM": 0.025,
            "Prophet": 0.018,
            "LSTM": 0.032,
            "TFT": -0.005,
            "Advanced": 0.021
        }
    }
    
    render_prediction_breakdown(mock_result)
    
    st.divider()
    
    mock_weights = {
        "LGBM": 0.30,
        "Prophet": 0.20,
        "LSTM": 0.25,
        "TFT": 0.10,
        "Advanced": 0.15
    }
    
    render_model_confidence_breakdown(mock_weights)
