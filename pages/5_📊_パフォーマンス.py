
import streamlit as st
from src.performance_dashboard import create_performance_dashboard

st.set_page_config(
    page_title="パフォーマンス分析 | AGStock",
    page_icon="📊",
    layout="wide"
)

create_performance_dashboard()
