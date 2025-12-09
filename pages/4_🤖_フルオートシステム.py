
import streamlit as st
from src.auto_trader_ui import create_auto_trader_ui

st.set_page_config(
    page_title="フルオート取引システム | AGStock",
    page_icon="🤖",
    layout="wide"
)

create_auto_trader_ui()
