"""
AGStockへようこそ！
サイドバーから各機能にアクセスしてください。
"""
import streamlit as st

# ページ設定
st.set_page_config(
    page_title="AGStock",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("💰 AGStockへようこそ！")
st.sidebar.success("上のメニューからページを選択してください。")

st.markdown(
    """
    ### 👈 サイドバーから各機能へアクセスできます

    - **🏠 ホーム**: あなたの資産状況や最新の取引を確認できます。
    - **📈 詳細**: 資産の推移グラフや取引履歴の詳細を分析できます。
    - **⚙️ 設定**: 通知などの各種設定を行えます。
    - **🤖 フルオートシステム**: 全自動取引システムの状態確認や操作ができます。
    - **📊 パフォーマンス**: システム全体のパフォーマンスを評価します。
    - **🎯 予測精度**: AIの予測精度をレビューできます。

    ***
    """
)
