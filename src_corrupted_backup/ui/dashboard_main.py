# """
# Dashboard Main UI Module
# Handles the market scan results and main dashboard display.
import datetime
import json
import os
import pandas as pd
import streamlit as st
from src.constants import TICKER_NAMES
from src.formatters import get_risk_level
from src.paper_trader import PaperTrader
from src.ui_components import display_best_pick_card, display_error_message, display_sentiment_gauge
from src.regime_detector import RegimeDetector
from src.strategies.orchestrator import StrategyOrchestrator
from src.data_loader import fetch_stock_data
# """
# 
# 
def render_market_scan_tab(sidebar_config):
    pass
#     """
#         Renders the Market Scan tab content.
#             st.header("市場全体スキャン")
#     # --- Phase 62: Regime & Strategy Visualization ---
#         try:
    pass
#             with st.expander("🛡️ 現在の市場レジームと戦略チーム (Active Squad)", expanded=True):
    pass
#                 col1, col2 = st.columns([1, 2])
#     # Fetch Nikkei for representative regime
#                 data = fetch_stock_data(["^N225"], period="3mo")
#                 df = data.get("^N225")
#                     if df is not None and not df.empty:
    pass
#                         detector = RegimeDetector()
#                     orchestrator = StrategyOrchestrator()
#     # Detect
#                     regime = detector.detect_regime(df)
#                     squad = orchestrator.get_active_squad(regime)
#                         with col1:
    pass
#                             st.metric("Detected Regime", regime.upper().replace("_", " "))
#                         if "trending" in regime:
    pass
#                             st.caption("📈 トレンド追随モード")
#                         elif "volatility" in regime:
    pass
#                             st.caption("🌪️ アクティブ防衛モード")
#                         else:
    pass
#                             st.caption("↔️ レンジ対応モード")
#                         with col2:
    pass
#                             st.markdown("**🚀 Active Strategy Squad:**")
#                         squad_names = [s.name for s in squad]
#                         st.write(", ".join([f"`{n}`" for n in squad_names]))
#                 else:
    pass
#                     st.info("市場データを取得してレジームを判定中...")
#         except Exception as e:
    pass
#             st.error(f"レジーム判定エラー: {e}")
#             st.write("指定した銘柄群に対して全戦略をバックテストし、有望なシグナルを検出します。")
#     # Unpack config
#         enable_fund_filter = sidebar_config["enable_fund_filter"]
#         max_per = sidebar_config["max_per"]
#         max_pbr = sidebar_config["max_pbr"]
#         min_roe = sidebar_config["min_roe"]
#         trading_unit = sidebar_config["trading_unit"]
#             cached_results = None
#         if os.path.exists("scan_results.json"):
    pass
#             try:
    pass
#                 with open("scan_results.json", "r", encoding="utf-8") as f:
    pass
#                     data = json.load(f)
#     # Check if data is fresh (e.g., from today)
#                     scan_date = datetime.datetime.strptime(data["scan_date"], "%Y-%m-%d %H:%M:%S")
#                     if scan_date.date() == datetime.date.today():
    pass
#                         cached_results = data
#                         st.success(f"✅ 最新のスキャン結果を読み込みました ({data['scan_date']})")
#             except Exception as e:
    pass
#                 display_error_message(
#                     "data", "スキャン結果の読み込みに失敗しました。ファイルが破損している可能性があります。", str(e)
#                 )
#             run_fresh = False
#     # Button logic
#         if st.button(
#             "市場をスキャンして推奨銘柄を探す (再スキャン)" if cached_results else "市場をスキャンして推奨銘柄を探す",
#             type="primary",
#         ):
    pass
#             run_fresh = True
#             cached_results = None  # Force fresh scan logic
#     # Note: Actual scan logic trigger needs to be handled by the caller or implemented here.
#     # For now, we assume the user will run the scan script or we integrate it later.
#     # Ideally, this button should trigger the full scan process which is currently
#     # embedded in a large block in app.py.
#     # For this refactoring step, we will return 'run_fresh' status so app.py can call the scanner.
#             return True  # Signal to run fresh scan
#             if cached_results and not run_fresh:
    pass
#                 sentiment = cached_results["sentiment"]
#             results_data = cached_results["results"]
#     # === Display Cached Sentiment ===
#             with st.expander("📰 市場センチメント分析", expanded=True):
    pass
#                 display_sentiment_gauge(sentiment["score"], sentiment.get("news_count", 0))
#                     st.subheader("📰 最新ニュース見出し")
#                 if sentiment.get("top_news"):
    pass
#                     for i, news in enumerate(sentiment["top_news"][:5], 1):
    pass
#                         st.markdown(f"{i}. [{news['title']}]({news['link']})")
#     # === Display Cached Results ===
#             results_df = pd.DataFrame(results_data)
#             if not results_df.empty:
    pass
#                 actionable_df = results_df[results_df["Action"] != "HOLD"].copy()
#     # Apply Fundamental Filters
#                 if enable_fund_filter:
    pass
#                     original_count = len(actionable_df)
#     # PER
#                     if "PER" in actionable_df.columns:
    pass
#                         actionable_df = actionable_df[(actionable_df["PER"].notna()) & (actionable_df["PER"] <= max_per)]
#     # PBR
#                     if "PBR" in actionable_df.columns:
    pass
#                         actionable_df = actionable_df[(actionable_df["PBR"].notna()) & (actionable_df["PBR"] <= max_pbr)]
#     # ROE
#                     if "ROE" in actionable_df.columns:
    pass
#                         actionable_df = actionable_df[
#                             (actionable_df["ROE"].notna()) & (actionable_df["ROE"] >= min_roe / 100.0)
#                         ]
#                         filtered_count = len(actionable_df)
#                     if original_count > filtered_count:
    pass
#                         st.info(
#                             f"財務フィルタにより {original_count} 件中 {original_count - filtered_count} 件が除外されました。"
#                         )
#                     actionable_df = actionable_df.sort_values(by="Return", ascending=False)
#     # 1. Today's Best Pick
#                 if not actionable_df.empty:
    pass
#                     best_pick = actionable_df.iloc[0]
#     # リスクレベル判定（統一版）
#                     risk_level = get_risk_level(best_pick.get("Max Drawdown", -0.15))
#     # 追加情報の準備
#                     additional_info = {}
#                     if "PER" in best_pick and pd.notna(best_pick["PER"]):
    pass
#                         additional_info["PER"] = best_pick["PER"]
#                     if "PBR" in best_pick and pd.notna(best_pick["PBR"]):
    pass
#                         additional_info["PBR"] = best_pick["PBR"]
#                     if "ROE" in best_pick and pd.notna(best_pick["ROE"]):
    pass
#                         additional_info["ROE"] = best_pick["ROE"]
#     # 注文コールバック
#     """


def handle_best_pick_order(ticker, action, price):
    pass
#     """
#                         Handle Best Pick Order.
#                             Args:
    pass
#                                 ticker: Description of ticker
#                             action: Description of action
#                             price: Description of price
#                                             pt = PaperTrader()
#                         trade_action = "BUY" if "BUY" in action else "SELL"
#                         if pt.execute_trade(
#                             ticker, trade_action, trading_unit, price, reason=f"Best Pick: {best_pick['Strategy']}"
#                         ):
    pass
#                             st.balloons()
#                             st.success(f"{best_pick['Name']} を {trading_unit}株 {trade_action} しました！")
#                         else:
    pass
#                             display_error_message(
#                                 "permission",
#                                 "注文に失敗しました。資金不足または保有株式が不足しています。",
#                                 f"Ticker: {ticker}, Action: {trade_action}, Unit: {trading_unit}",
#                             )
#     # 改善版コンポーネントで表示
#                     display_best_pick_card(
#                         ticker=best_pick["Ticker"],
#                         name=best_pick["Name"],
#                         action=best_pick["Action"],
#                         price=best_pick["Last Price"],
#                         explanation=best_pick.get("Explanation", ""),
#                         strategy=best_pick["Strategy"],
#                         risk_level=risk_level,
#                         on_order_click=handle_best_pick_order,
#                         additional_info=additional_info if additional_info else None,
#                     )
#     # Ask AI Button
#                     if st.button(
#                         f"🤖 この銘柄 ({best_pick['Name']}) についてAIに聞く", key=f"ask_ai_{best_pick['Ticker']}"
#                     ):
    pass
#                         st.session_state["chat_initial_input"] = (
#                             f"{best_pick['Name']} ({best_pick['Ticker']}) の詳細な分析をお願いします。なぜこの戦略が推奨されたのですか？"
#                         )
#                         st.info("「💬 AIチャット」タブへ移動して、送信ボタンを押してください ↗")
#     # 1.5. AI Robo-Advisor Portfolio
#                 if "portfolio" in cached_results and cached_results["portfolio"]:
    pass
#                     portfolio = cached_results["portfolio"]
#                     st.markdown("---")
#                     with st.expander("💰 AIロボアドバイザー・ポートフォリオ", expanded=False):
    pass
#                         st.write(f"**推奨銘柄数**: {portfolio['total_assets']}銘柄")
#                         st.write("AIが最適なリスク・リターン比率で配分を計算しました。")
#     # Display weights as pie chart
#                         weights_df = pd.DataFrame(
#                             [{"銘柄": TICKER_NAMES.get(t, t), "配分比率": w * 100} for t, w in portfolio["weights"].items()]
#                         )
#                         st.dataframe(weights_df)
#             return False  # Normal end
# 
#     """  # Force Balanced
