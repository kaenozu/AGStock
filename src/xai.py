"""
説明可能AI (XAI) モジュール

SHAP (SHapley Additive exPlanations) を使用して、
モデルの予測根拠を可視化・説明します。
"""

import shap
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class XAIManager:
    """
    XAIマネージャー
    
    モデルの予測に対する説明を提供します。
    現在はLightGBMモデルに最適化されています。
    """
    
    def __init__(self):
        self.explainers = {}
        
    def get_shap_values(self, model: Any, X: pd.DataFrame) -> Any:
        """
        SHAP値を計算
        
        Args:
            model: 学習済みモデル (LightGBMなど)
            X: 特徴量データフレーム
            
        Returns:
            shap_values: SHAP値オブジェクト
        """
        try:
            # モデルID（簡易的にハッシュ値などを使うべきだが、ここではオブジェクトID）
            model_id = id(model)
            
            if model_id not in self.explainers:
                # TreeExplainerは決定木ベースのモデル（LightGBM, XGBoost, RF）に高速
                self.explainers[model_id] = shap.TreeExplainer(model)
                
            explainer = self.explainers[model_id]
            shap_values = explainer.shap_values(X)
            
            # LightGBMの二値分類の場合、shap_valuesはリストで返ることがある
            # [0]が負例、[1]が正例。通常は[1]（上昇予測）を見る
            if isinstance(shap_values, list):
                return shap_values[1]
            return shap_values
            
        except Exception as e:
            logger.error(f"Error calculating SHAP values: {e}")
            return None
            
    def plot_feature_importance(self, shap_values: np.ndarray, X: pd.DataFrame, top_n: int = 10) -> go.Figure:
        """
        特徴量重要度をプロット（SHAP summary plot風）
        
        Args:
            shap_values: SHAP値の配列
            X: 特徴量データフレーム
            top_n: 表示する上位特徴量数
            
        Returns:
            fig: Plotly Figure
        """
        if shap_values is None or X.empty:
            return go.Figure()
            
        # 平均絶対SHAP値を計算して重要度とする
        if isinstance(shap_values, list):
             # 多クラス分類などの場合
             mean_abs_shap = np.mean(np.abs(shap_values[0]), axis=0) # 仮
        else:
             mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        
        # 特徴量名と重要度のペアを作成
        feature_importance = pd.DataFrame({
            'Feature': X.columns,
            'Importance': mean_abs_shap
        }).sort_values(by='Importance', ascending=True).tail(top_n)
        
        # プロット
        fig = px.bar(
            feature_importance, 
            x='Importance', 
            y='Feature', 
            orientation='h',
            title=f"AIが重視した特徴量 (Top {top_n})",
            labels={'Importance': '平均SHAP値 (影響度)', 'Feature': '特徴量'},
            color='Importance',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            showlegend=False,
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
        
    def plot_prediction_reason(self, shap_values: np.ndarray, X: pd.DataFrame, row_index: int = -1) -> go.Figure:
        """
        特定の予測に対する理由をプロット（Waterfall plot風）
        
        Args:
            shap_values: SHAP値の配列
            X: 特徴量データフレーム
            row_index: 説明対象の行インデックス（デフォルトは最新）
            
        Returns:
            fig: Plotly Figure
        """
        if shap_values is None or X.empty:
            return go.Figure()
            
        # 対象行のSHAP値と特徴量値
        if isinstance(shap_values, list):
             target_shap = shap_values[1][row_index]
        else:
             target_shap = shap_values[row_index]
             
        target_features = X.iloc[row_index]
        
        # データフレーム作成
        contributions = pd.DataFrame({
            'Feature': X.columns,
            'Contribution': target_shap,
            'Value': target_features.values
        })
        
        # 寄与度の絶対値でソートして上位を表示
        contributions['AbsContribution'] = contributions['Contribution'].abs()
        top_contributions = contributions.sort_values(by='AbsContribution', ascending=True).tail(10)
        
        # Waterfallチャートの代わりにBarチャートで表現（PlotlyのWaterfallは少し扱いが難しいので）
        # 正の寄与（価格上昇要因）と負の寄与（下落要因）を色分け
        top_contributions['Type'] = top_contributions['Contribution'].apply(lambda x: 'Positive (Buy)' if x > 0 else 'Negative (Sell)')
        top_contributions['Color'] = top_contributions['Contribution'].apply(lambda x: 'green' if x > 0 else 'red')
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=top_contributions['Feature'],
            x=top_contributions['Contribution'],
            orientation='h',
            marker_color=top_contributions['Color'],
            text=top_contributions['Value'].apply(lambda x: f"{x:.2f}"),
            textposition='auto',
            hovertemplate="<b>%{y}</b><br>SHAP Value: %{x:.4f}<br>Feature Value: %{text}<extra></extra>"
        ))
        
        fig.update_layout(
            title="今回の予測の決定要因 (なぜこの予測なのか？)",
            xaxis_title="予測への寄与度 (SHAP値)",
            yaxis_title="特徴量",
            height=400,
            showlegend=False
        )
        
        # ゼロライン
        fig.add_vline(x=0, line_width=1, line_color="white")
        
        return fig

    def generate_explanation_text(self, shap_values: np.ndarray, X: pd.DataFrame, row_index: int = -1) -> str:
        """
        予測理由の自然言語説明を生成
        
        Args:
            shap_values: SHAP値
            X: 特徴量
            row_index: 対象行
            
        Returns:
            explanation: 説明テキスト
        """
        if shap_values is None or X.empty:
            return "説明を生成できませんでした。"
            
        if isinstance(shap_values, list):
             target_shap = shap_values[1][row_index]
        else:
             target_shap = shap_values[row_index]
             
        contributions = pd.DataFrame({
            'Feature': X.columns,
            'Contribution': target_shap
        }).sort_values(by='Contribution', key=abs, ascending=False)
        
        top_3 = contributions.head(3)
        
        explanation = "AIの判断根拠:\n"
        
        for _, row in top_3.iterrows():
            feature = row['Feature']
            contrib = row['Contribution']
            effect = "上昇" if contrib > 0 else "下落"
            strength = "強く" if abs(contrib) > 0.1 else "わずかに"
            
            # 特徴量名の日本語化（簡易マッピング）
            feature_jp = feature
            if "RSI" in feature: feature_jp = "RSI（買われすぎ/売られすぎ）"
            elif "SMA" in feature: feature_jp = "移動平均線乖離"
            elif "MACD" in feature: feature_jp = "MACDトレンド"
            elif "Close" in feature: feature_jp = "直近価格"
            elif "Volume" in feature: feature_jp = "出来高"
            
            explanation += f"- **{feature_jp}** が価格を{strength}{effect}させる要因として働きました。\n"
            
        return explanation

# シングルトン
_xai_manager = None

def get_xai_manager() -> XAIManager:
    global _xai_manager
    if _xai_manager is None:
        _xai_manager = XAIManager()
    return _xai_manager
