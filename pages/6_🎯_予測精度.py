import streamlit as st

from src.prediction_dashboard import create_prediction_analysis_dashboard

st.set_page_config(page_title="予測精度分析 | AGStock", page_icon="🎯", layout="wide")

create_prediction_analysis_dashboard()
