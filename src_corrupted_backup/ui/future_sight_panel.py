import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from src.evolution.future_sight import FutureSightEngine
def render_future_sight_chart(ticker: str, df: pd.DataFrame):
#     st.markdown(f"""" 🔮 AI Future Sight: {ticker}")
#         engine = FutureSightEngine()
#         with st.spinner("AIが将来のシナリオを描画中..."):
#             forecast = engine.project_future(df, ticker)
#         if not forecast:
#             st.warning("将来予測の生成に失敗しました。Geminiのアクセスを確認してください。")
# # Just render normal chart as fallback
#         fig = go.Figure(
#             data=[go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"])]
#         )
#         st.plotly_chart(fig, use_container_width=True)
#         return
# # Create figure
#     fig = go.Figure()
# # 1. Historical Data
#     fig.add_trace(
#         go.Candlestick(
#             x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Historical"
#         )
#     )
# # 2. Future Scenarios
#     colors = {
#         "base": "rgba(100, 149, 237, 0.7)",  # CornflowerBlue
#         "bull": "rgba(50, 205, 50, 0.7)",  # LimeGreen
#         "bear": "rgba(255, 69, 0, 0.7)",  # OrangeRed
#     }
#         for scenario, data in forecast.items():
#             f_df = pd.DataFrame(data)
#         f_df["Date"] = pd.to_datetime(f_df["Date"])
# # Add as separate candlestick series with specific colors
# # For simplicity, we can also use line charts for Bull/Bear and Candlestick for Base
#         if scenario == "base":
#             fig.add_trace(
#                 go.Candlestick(
#                     x=f_df["Date"],
#                     open=f_df["Open"],
#                     high=f_df["High"],
#                     low=f_df["Low"],
#                     close=f_df["Close"],
#                     name=f"Forecast (Base)",
#                     increasing_line_color=colors[scenario],
#                     decreasing_line_color=colors[scenario],
#                     opacity=0.8,
#                 )
#             )
#         else:
#             fig.add_trace(
#                 go.Scatter(
#                     x=f_df["Date"],
#                     y=f_df["Close"],
#                     mode="lines+markers",
#                     name=f"Forecast ({scenario})",
#                     line=dict(color=colors[scenario], dash="dash"),
#                     opacity=0.6,
#                 )
#             )
#         fig.update_layout(
#         title=f"{ticker} - Future Sight Projection (5 Days)",
#         yaxis_title="Price",
#         xaxis_title="Date",
#         template="plotly_dark",
#         xaxis_rangeslider_visible=False,
#     )
#         st.plotly_chart(fig, use_container_width=True)
# # Text explanation
#     with st.expander("📝 AIの視点"):
#         st.markdown(
#             f"""
        この予測は、直近30日の価格パターン、ボラティリティ、および同様の過去事例との比較に基づき、Gemini 1.5 Flash が生成した非決定論的なシナリオです。
                - **BASE**: 現状のトレンドと出来高から最も確度が高いと判断される経路。
        - **BULL**: ポジティブなニュースやテクニカルな反発が起きた場合のターゲット。
        - **BEAR**: サポートラインの割り込みやマクロ的な悪化を想定した警戒域。
                )


