# """
# The Training Dojo UI


# Lazy loading
# """
#
#
def render():
    pass
    #     """
    #         Render.
    #             st.markdown("<h1 style='text-align: center;'>🥋 The Training Dojo</h1>", unsafe_allow_html=True)
    #         st.markdown(
    #             "<p style='text-align: center; color: gray;'>Train your AI agents to become master traders.</p>",
    #             unsafe_allow_html=True,
    #         )
    #             tab_train, tab_cinema, tab_lab = st.tabs(["🏋️ Train (Dojo)", "🎬 Replay (Cinema)", "🧬 Models (Lab)"])
    #     from src.rl.trainer import TrainingSessionManager
    #             manager = TrainingSessionManager()
    #     # --- TAB 1: TRAIN ---
    #         with tab_train:
    #             col1, col2 = st.columns([1, 2])
    #                 with col1:
    #                     st.subheader("Training Config")
    #                 ticker = st.text_input("Ticker Symbol", value="7203.T")
    #                 episodes = st.number_input("Episodes", min_value=10, max_value=1000, value=50, step=10)
    #     # Control Buttons
    #                 if not manager.get_status()["is_running"]:
    #                     if st.button("🔥 Start Training", type="primary"):
    #                         manager.start_training(ticker, episodes)
    #                         st.rerun()
    #                 else:
    #                     if st.button("🛑 Stop Training", type="secondary"):
    #                         manager.stop_training()
    #                         st.rerun()
    #                     status = manager.get_status()
    #                 st.info(f"Status: {status['status_message']}")
    #                     if status["is_running"]:
    #                         st.progress(status["progress"])
    #                     st.caption(f"Episode: {status['current_episode']} / {status['total_episodes']}")
    #     # Auto-refresh logic
    #     import time
    #                         time.sleep(1)
    #                     st.rerun()
    #                 with col2:
    #                     st.subheader("Live Performance")
    #                 metrics = manager.get_status()["metrics"]
    #                 if metrics:
    #                     df_metrics = pd.DataFrame(metrics)
    #     # Plot Reward
    #                     fig_reward = px.line(df_metrics, x="episode", y="reward", title="Episode Reward (Profitability)")
    #                     fig_reward.update_layout(template="plotly_dark", height=300)
    #                     st.plotly_chart(fig_reward, use_container_width=True)
    #     # Plot Loss
    #                     fig_loss = px.line(
    #                         df_metrics, x="episode", y="loss", title="Training Loss (Error)", color_discrete_sequence=["orange"]
    #                     )
    #                     fig_loss.update_layout(template="plotly_dark", height=300)
    #                     st.plotly_chart(fig_loss, use_container_width=True)
    #                 else:
    #                     st.info("Waiting for training data...")
    #     # --- TAB 2: CINEMA ---
    #         with tab_cinema:
    #             st.subheader("Replay Cinema")
    #             st.caption("Visualize the AI's trading decisions from the latest training run.")
    #                 status = manager.get_status()
    #             trades = status.get("trade_history", [])
    #                 if not trades:
    #                     st.warning("No trade history available. Run a training session first.")
    #             else:
    #                 # We need price data to plot
    #     # Ideally we should store the price history in the session manager too, but for now we rely on re-fetching or implicit knowledge
    #     # Actually, to make a nice chart, we need the full price series.
    #     # Let's try to fetch data for the ticker used in training (we need to store ticker in manager state)
    #     # WORKAROUND: Just plot the trade points if full history unavailable, OR fetch same ticker again.
    #                     df_trades = pd.DataFrame(trades)
    #                     tick_size = 100  # Mock size for nice chart if no full data
    #     # Simple Scatter Plot of Trades
    #                 fig = px.scatter(
    #                     df_trades,
    #                     x="step",
    #                     y="price",
    #                     color="action",
    #                     symbol="action",
    #                     color_discrete_map={"BUY": "green", "SELL": "red"},
    #                     title="AI Trading Decisions (Latest Episode)",
    #                     hover_data=["date", "price"],
    #                 )
    #                 fig.update_traces(marker_size=12)
    #                 fig.update_layout(template="plotly_dark", height=500)
    #                     st.plotly_chart(fig, use_container_width=True)
    #                     with st.expander("Detailed Trade Log"):
    #                         st.dataframe(df_trades, use_container_width=True)
    #     # --- TAB 3: LAB ---
    #         with tab_lab:
    #             st.subheader("Model Laboratory")
    #             model_files = glob.glob("models/rl/*.pth")
    #                 if model_files:
    #                     df_models = pd.DataFrame({"Model File": model_files})
    #                 st.dataframe(df_models, use_container_width=True)
    #                     selected_model = st.selectbox("Select Model to Deploy", model_files)
    #                     if st.button("🚀 Deploy to Production"):
    #                         try:
    #                             import shutil
    #     # Copy to production path
    #                         prod_path = "models/production/active_agent.pth"
    #                         os.makedirs("models/production", exist_ok=True)
    #                         shutil.copy(selected_model, prod_path)
    #                             st.success(f"Deployed {selected_model} to {prod_path}!")
    #                         st.balloons()
    #     # Update config or system state if needed (Mock for now)
    #                         st.info("System will use this model for next trade execution.")
    #                             except Exception as e:
    #                                 st.error(f"Deployment failed: {e}")
    #                 else:


#                 st.info("No trained models found. Go to the Dojo tab to train one.")
#     """
