import streamlit as st
import os
from src.llm_reasoner import get_llm_reasoner

STRATEGY_DIR = "src/strategies/custom"


def render_gen_lab():
    """Gemini 2.0 Generative Strategy Lab"""
    st.header("✨ Generative Lab (Powered by Gemini 2.0)")
    st.caption("自然言語で投資戦略を記述すると、AIが即座にPythonコードを生成・実装します。")

    reasoner = get_llm_reasoner()

    # Check Provider
    if reasoner.provider == "gemini":
        st.success(f"🚀 Connected to Brain: {reasoner.gemini_model_name} (Ultra-Fast)")
    else:
        st.warning(f"⚠️ Connected to Brain: {reasoner.provider} (Gemini推奨)")

    # Input Area
    with st.form("gen_strategy_form"):
        st.markdown("### 💡 どんな戦略を作りますか？")
        prompt_text = st.text_area(
            "戦略のアイデアを入力 (例: RSIが30以下かつゴールデンクロスで買い、5%利益で利確)",
            height=100,
            placeholder="ここにアイデアを入力...",
        )

        col1, col2 = st.columns([1, 2])
        with col1:
            class_name_input = st.text_input("戦略クラス名 (英語)", value="MyGeminiStrategy")

        submitted = st.form_submit_button("🚀 戦略を生成する")

    if submitted and prompt_text:
        with st.spinner("Gemini 2.0 is thinking... (Generating Code)"):
            try:
                generated_code = reasoner.generate_strategy_code(prompt_text, class_name_input)

                # Simple cleanup if markdown blocks remain (though prompt asks not to)
                cleaned_code = generated_code.replace("```python", "").replace("```", "")

                st.session_state["gen_code"] = cleaned_code
                st.session_state["gen_class"] = class_name_input
                st.success("✨ コード生成完了！")

            except Exception as e:
                st.error(f"生成エラー: {e}")

    # Display Generated Code
    if "gen_code" in st.session_state:
        st.markdown("### 📜 生成されたコード")
        code = st.session_state["gen_code"]
        st.code(code, language="python")

        # Save Logic
        if st.button("💾 この戦略をシステムに保存"):
            try:
                os.makedirs(STRATEGY_DIR, exist_ok=True)
                file_path = f"{STRATEGY_DIR}/{st.session_state['gen_class'].lower()}.py"

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)

                # Init file check
                init_path = f"{STRATEGY_DIR}/__init__.py"
                if not os.path.exists(init_path):
                    with open(init_path, "w", encoding="utf-8") as f:
                        f.write("")

                st.success(f"✅ 保存しました: {file_path}")
                st.info("「戦略アリーナ」タブでバックテストが可能です！")

                # Clear state
                del st.session_state["gen_code"]
                if hasattr(st, "rerun"):
                    st.experimental_rerun()

            except Exception as e:
                st.error(f"保存エラー: {e}")
