

def render_singularity_core():
    #         """
    #         st.markdown(
    #         f"""
    #     <div style="margin-bottom: 2rem;">
    #         <h1 style="display: flex; align-items: center; margin-bottom: 0.5rem;">
    #             <span style="font-size: 2rem; margin-right: 0.5rem;">🧬</span> The Singularity
    #         </h1>
    #         <div style="color: {DS.COLORS['text_secondary']}; font-size: 1.1rem;">
    #             Autonomous Strategy Evolution Engine. Describe a strategy, and the AI will write the Python code.
    #         </div>
    #     </div>
    #     """,
    #         unsafe_allow_html=True,
    #     )
    #         col1, col2 = st.columns([1, 1])
    #         with col1:
    pass
    #             st.subheader("Genetic Definition")
    #         prompt = st.text_area(
    #             "Strategy Logic / Hypothesis",
    #             height=200,
    #             placeholder="Example: Create a trend-following strategy that buys when "
    #                         "20-day SMA crosses above 50-day SMA, but only if RSI is below 70.",
    #         )
    #             name_input = st.text_input("Strategy Name (Optional)", placeholder="MySuperStrategy")
    #             generate_btn = st.button("🧬 Evolve New Strategy", type="primary")
    #         with col2:
    #             st.subheader("Genome Preview (Code)")
    #         code_placeholder = st.empty()
    #             if generate_btn:
    #                 if not prompt:
    #                     st.error("Please define the strategy logic first.")
    #             else:
    #                 with st.spinner("Compiling genetic code..."):
    #                     try:
    #                         evo = EvoCoder()
    #                         filename = evo.evolve_strategy(prompt, generated_name=name_input or None)
    # # Read back the file
    #                         filepath = os.path.join(evo.output_dir, filename)
    #                         with open(filepath, "r", encoding="utf-8") as f:
    #                             code = f.read()
    #                             code_placeholder.code(code, language="python")
    #                             st.success(f"Evolution Complete! Saved to {filename}")
    #                         st.info("⚠️ Restart the application to load the new strategy into the Trading Hub.")
    # # Button to clear cache?
    #                         if st.button("Clear Cache & Reload (Try)"):
    #                             st.cache_resource.clear()
    #                             st.experimental_rerun()
    #                         except Exception as e:
    #                             st.error(f"Evolution failed: {e}")
    #         else:
    #             code_placeholder.info("Waiting for genetic input...")
    #         st.divider()
    #         with st.expander("📂 Existing Evolutions"):
    #             try:
    #                 custom_dir = "src/strategies/custom"
    #             if os.path.exists(custom_dir):
    #                 files = [f for f in os.listdir(custom_dir) if f.endswith(".py") and f != "__init__.py"]
    #                 if files:
    #                     selected_file = st.selectbox("View Strategy Code", files)
    #                     if selected_file:
    #                         with open(os.path.join(custom_dir, selected_file), "r", encoding="utf-8") as f:
    #                             st.code(f.read(), language="python")
    #                 else:
    #                     st.caption("No custom strategies found.")
    #         except Exception:


#             pass
