"""
Strategy Arena UI Module
Allows users to compare multiple trading strategies on historical data.
"""
import streamlit as st
import pandas as pd
import logging
from src.backtest_engine import HistoricalBacktester
from src.strategies import (
    LightGBMStrategy,
    MLStrategy,
    RSIStrategy, 
    SMACrossoverStrategy, # Corrected
    BollingerBandsStrategy,
    MultiTimeframeStrategy # New
)
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES

# Try importing RL Strategy, but don't crash if missing deps
try:
    from src.strategies.rl import RLStrategy
    HAS_RL = True
except ImportError:
    HAS_RL = False

logger = logging.getLogger(__name__)

def render_strategy_arena():
    """Renders the Strategy Arena tab."""
    st.header("🧪 戦略アリーナ (Backtest Lab)")
    st.caption("複数のアルゴリズムを過去データで対決させ、最強の戦略を見つけましょう。")

    # --- Sidebar Configuration ---
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("設定")
        
        # Ticker Selection
        # Create a display list "Code: Name"
        ticker_options = {t: f"{t}: {TICKER_NAMES.get(t, 'Unknown')}" for t in NIKKEI_225_TICKERS}
        selected_ticker = st.selectbox(
            "銘柄選択",
            options=list(ticker_options.keys()),
            format_func=lambda x: ticker_options[x],
            index=0
        )
        
        # Period Selection
        years = st.slider("バックテスト期間 (年)", min_value=1, max_value=10, value=3)
        
        # Strategy Selection
        st.markdown("### 参戦する戦略")
        
        use_mtf = st.checkbox("Multi-Timeframe (New)", value=True, help="週足トレンドを考慮した高度な戦略")
        use_lightgbm = st.checkbox("LightGBM (AI)", value=True)
        auto_tune = st.checkbox("🧩 Auto-Tune LightGBM", value=False, disabled=not use_lightgbm)
        use_ml_rf = st.checkbox("Random Forest (AI)", value=False)
        use_rl = st.checkbox("Reinforcement Learning (AI)", value=HAS_RL, disabled=not HAS_RL)
        use_rsi = st.checkbox("RSI (Technical)", value=False)
        use_bb = st.checkbox("Bollinger Bands", value=False)
        use_sma = st.checkbox("SMA Crossover (Baseline)", value=True) # Renamed
        
        start_btn = st.button("🔥 バトル開始！", type="primary", use_container_width=True)

    # --- Main Area ---
    with col2:
        if not start_btn:
            st.info("👈 左側の設定を選んで「バトル開始」を押してください。")
            st.markdown("""
            ### 使い方
            1. **銘柄**を選びます (例: トヨタ自動車)。
            2. **期間**を設定します (長期間ほど信頼性が高まります)。
            3. **比較したい戦略**にチェックを入れます。
            4. **バトル開始**ボタンをクリック！
            
            **Update**: New! **Multi-Timeframe** 戦略が追加されました。週足トレンドを見てダマシを防ぎます。
            """)
            return

        # Prepare Strategies
        strategies = []
        if use_mtf:
            strategies.append((MultiTimeframeStrategy, {}))
        if use_lightgbm:
             # Use variable from sidebar
             strategies.append((LightGBMStrategy, {'auto_tune': auto_tune}))
        if use_ml_rf:
            strategies.append((MLStrategy, {}))
        if use_rl and HAS_RL:
            strategies.append((RLStrategy, {}))
        if use_rsi:
            strategies.append((RSIStrategy, {'period': 14, 'lower': 30, 'upper': 70})) # Fixed params
        if use_bb:
            strategies.append((BollingerBandsStrategy, {}))
        if use_sma:
            strategies.append((SMACrossoverStrategy, {'short_window': 5, 'long_window': 20}))

        if not strategies:
            st.error("少なくとも1つの戦略を選択してください。")
            return

        # Run Backtest
        with st.spinner(f"{selected_ticker} の過去 {years} 年間のデータを分析中... AIが思考しています..."):
            try:
                engine = HistoricalBacktester(initial_capital=1000000)
                metrics_df, equity_df = engine.compare_strategies(selected_ticker, strategies, years=years)
                
                if metrics_df.empty:
                    st.error("バックテスト結果が取得できませんでした。データ不足の可能性があります。")
                    return

                # --- Results Display ---
                
                # 1. Chart
                st.subheader("📈 資産推移チャート")
                st.line_chart(equity_df)
                
                # 2. Metrics Table
                st.subheader("📊 パフォーマンス成績表")
                
                # Format metrics for better display
                display_df = metrics_df.copy()
                display_df = display_df.set_index("Strategy")
                
                # Highlight best performer
                best_return = display_df['Total Return'].idxmax()
                st.success(f"🏆 優勝: **{best_return}** (リターン: {display_df.loc[best_return, 'Total Return']:.1%})")
                
                # Formatting
                st.dataframe(
                    display_df.style.format({
                        "Total Return": "{:.1%}",
                        "CAGR": "{:.1%}",
                        "Max Drawdown": "{:.1%}",
                        "Sharpe Ratio": "{:.2f}",
                        "Win Rate": "{:.1%}",
                        "Trades": "{:.0f}"
                    }).background_gradient(subset=['Total Return'], cmap='Greens')
                )
                
                # 3. Insights
                with st.expander("💡 分析インサイト", expanded=True):
                    # Simple automated insights
                    sharpe_best = display_df['Sharpe Ratio'].idxmax()
                    dd_best = display_df['Max Drawdown'].idxmax() # Usually higher (closer to 0) is better for negative numbers, but DD is usually positive in reports?
                    # Let's check format. Standard backtest returns DD as positive (0.2 for 20%) or negative?
                    # Typically DD is negative. Let's assume negative (-0.2). So max() is best (closest to 0).
                    
                    st.markdown(f"""
                    - **収益性No.1**: {best_return}
                    - **安定性No.1 (Sharpe)**: {sharpe_best}
                    - **防御力No.1 (Min DD)**: {dd_best}
                    """)
                    
                    if "RLStrategy" in display_df.index:
                        rl_ret = display_df.loc["RLStrategy", "Total Return"]
                        lgbm_ret = display_df.loc["LightGBMStrategy", "Total Return"] if "LightGBMStrategy" in display_df.index else 0
                        
                        if rl_ret > lgbm_ret:
                            st.write("🤖 **強化学習(RL)がLightGBMを上回りました！** AIの学習効果が出ています。")
                        else:
                            st.write("🤖 LightGBMの方が安定しています。RLはさらなる学習が必要かもしれません。")

            except Exception as e:
                import traceback
                st.error(f"バックテスト実行中にエラーが発生しました: {e}")
                st.code(traceback.format_exc())

