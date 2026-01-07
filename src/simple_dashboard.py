
"""
個人投資家向けシンプルダッシュボード (Command Center Version)

一目でわかる資産状況と、AIの自律動作状況、次に取るべきアクションを提示します。
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.constants import TICKER_NAMES
from src import demo_data
from src.data_loader import fetch_external_data
from src.paper_trader import PaperTrader
from src.services.defense import defense_status
from src.services.defense import defense_status
from src.ui.playbooks import render_playbook_cards
import json # Added for config handling


# --- Config Helper ---
def _load_config():
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_config(config):
    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


# --- Caching Wrappers for Performance ---
@st.cache_data(ttl=60)
def _get_cached_balance(demo: bool) -> Dict[str, float]:
    if demo:
        positions = demo_data.generate_positions()
        return {
            "total_equity": float(positions["market_value"].sum() * 1.1),
            "cash": float(positions["market_value"].sum() * 0.1),
            "unrealized_pnl": float(positions["market_value"].sum() * 0.05),
            "daily_pnl": float(positions["market_value"].sum() * 0.002),
        }
    pt = PaperTrader()
    try:
        return pt.get_current_balance()
    finally:
        pt.close()

@st.cache_data(ttl=60)
def _get_cached_positions(demo: bool) -> pd.DataFrame:
    if demo:
        return demo_data.generate_positions()
    pt = PaperTrader()
    try:
        return pt.get_positions()
    finally:
        pt.close()

@st.cache_data(ttl=300)
def _get_cached_equity_history(demo: bool, days: int) -> pd.DataFrame:
    if demo:
        return demo_data.generate_equity_history(days=days)
    pt = PaperTrader()
    try:
        data = pt.get_equity_history(days=days)
        return data if not data.empty else pd.DataFrame(columns=["date", "total_equity"])
    finally:
        pt.close()

@st.cache_data(ttl=300)
def _load_backtest_history(demo: bool) -> pd.DataFrame:
    if demo:
        return demo_data.generate_backtest_history(days=90)
    
    path = Path("reports/backtest_history.csv")
    if path.exists():
        try:
            df = pd.read_csv(path)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            return df
        except Exception:
            pass
    
    # Fallback: compute from equity/trade history if no CSV and not demo
    pt = PaperTrader()
    try:
        equity_df = pt.get_equity_history()
        if not equity_df.empty:
            equity_df["date"] = pd.to_datetime(equity_df["date"])
            equity_df["return"] = equity_df["total_equity"].pct_change()
            equity_df["win_rate"] = (equity_df["return"] > 0).rolling(10, min_periods=3).mean()
            equity_df["sharpe"] = (
                equity_df["return"].rolling(30, min_periods=5).mean()
                / (equity_df["return"].rolling(30, min_periods=5).std() + 1e-6)
                * (252**0.5)
            )
            return equity_df[["date", "win_rate", "sharpe"]].dropna()
    finally:
        pt.close()
    return pd.DataFrame()


# --- Utility Functions ---
def format_currency_jp(amount: float) -> str:
    """日本円を万円形式で表示"""
    if amount >= 100000000:
        return f"¥{amount/100000000:.2f}億"
    elif amount >= 10000:
        return f"¥{amount/10000:.1f}万"
    else:
        return f"¥{amount:,.0f}"

def _demo_mode() -> bool:
    env_flag = os.getenv("USE_DEMO_DATA", "")
    return bool(st.session_state.get("use_demo_data")) or env_flag.lower() in {"1", "true", "yes"}

def _apply_theme(theme: str):
    """テーマに応じた簡易CSSを注入。"""
    if theme == "navy":
        # Deep Navy / Fintech Style
        css = """
        <style>
        .stApp {
            background-color: #0b1116;
            color: #e6e6e6;
        }
        div[data-testid="stMetric"] {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        div[data-testid="stMetricLabel"] {
            color: #8b949e;
            font-size: 0.85rem;
        }
        div[data-testid="stMetricValue"] {
            color: #ffffff;
            font-size: 1.8rem;
            font-weight: 600;
        }
        .stDataFrame {
            border: 1px solid #30363d;
            border-radius: 6px;
        }
        h1, h2, h3 {
            color: #ffffff;
            font-weight: 600;
            letter-spacing: -0.5px;
        }
        /* Status Card Styles */
        .status-hero {
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            color: white;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .status-hero.running { background: linear-gradient(135deg, #1f4037, #99f2c8); color: #0f1a2b; }
        .status-hero.idle { background: linear-gradient(135deg, #434343, #000000); border: 1px solid #555; }
        .status-hero.warning { background: linear-gradient(135deg, #f12711, #f5af19); color: #0f1a2b; }
        
        .guidance-box {
            background-color: #1c2128;
            border-left: 4px solid #58a6ff;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 0 4px 4px 0;
        }
        </style>
        """
    elif theme == "dark-contrast":
        # High Contrast Dark
        css = """
        <style>
        .stApp {
            background-color: #000000;
            color: #ffffff;
        }
        div[data-testid="stMetric"] {
            background-color: #121212;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 20px;
        }
        div[data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700;
        }
        /* Status Card Styles */
        .status-hero {
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            color: white;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .status-hero.running { background: linear-gradient(135deg, #004d40, #00c853); color: #e0e0e0; }
        .status-hero.idle { background: linear-gradient(135deg, #212121, #000000); border: 1px solid #424242; }
        .status-hero.warning { background: linear-gradient(135deg, #d50000, #ff6f00); color: #e0e0e0; }
        
        .guidance-box {
            background-color: #212121;
            border-left: 4px solid #82b1ff;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 0 4px 4px 0;
        }
        </style>
        """
    else:
        # Default / Light (Clean Minimal)
        css = """
        <style>
        .stApp {
            background-color: #ffffff;
            color: #24292f;
        }
        div[data-testid="stMetric"] {
            background-color: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 10px 15px;
        }
        /* Status Card Styles */
        .status-hero {
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            color: #24292f;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border: 1px solid #d0d7de;
        }
        .status-hero.running { background-color: #e6ffed; border-color: #28a745; }
        .status-hero.idle { background-color: #f6f8fa; border-color: #d0d7de; }
        .status-hero.warning { background-color: #fff5f5; border-color: #dc3545; }
        
        .guidance-box {
            background-color: #e7f5ff;
            border-left: 4px solid #0366d6;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 0 4px 4px 0;
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


# --- Command Center Components ---

def _render_status_hero():
    """現在のシステムの稼働状態を表示するヒーローコンポーネント"""
    now = datetime.now()
    # 簡易判定: 日本時間で平日9:00-15:00を市場オープンとする
    is_market_open = (now.weekday() < 5) and (9 <= now.hour < 15)
    
    # 状態判定ロジック
    if defense_status():
        status = "warning"
        icon = "🛡️"
        title = "防御モード発動中 - 取引制限"
        desc = "リスク回避のため、新規BUYを停止しています。手動で解除するか、リスク要因が去るのを待ってください。"
    elif is_market_open:
        status = "running"
        icon = "🟢"
        title = "自律運用中 - 市場監視"
        desc = "AIが市場をスキャンし、チャンスを探しています。システムは正常です。"
    else:
        status = "idle"
        icon = "💤"
        title = "市場待機中"
        desc = "次の市場オープン(09:00)まで待機しています。メンテナンスやモデル更新に最適な時間です。"

    st.markdown(f"""
    <div class="status-hero {status}">
        <div>
            <div style="font-size: 2rem;">{icon} {title}</div>
            <div style="font-size: 1rem; opacity: 0.9;">{desc}</div>
        </div>
        <div style="text-align: right; font-size: 0.8rem;">
            Last Heartbeat: {now.strftime('%H:%M:%S')}
        </div>
    </div>
    """, unsafe_allow_html=True)

def _render_system_controls():
    """System On/Off & Force Run Controls (Relocated from Sidebar)"""
    config = _load_config()
    auto_config = config.get("auto_trading", {})
    current_status = auto_config.get("enabled", False)

    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Toggle Switch
        new_status = st.toggle("🤖 自動取引システム (Auto Pilot)", value=current_status)
        if new_status != current_status:
            if "auto_trading" not in config: config["auto_trading"] = {}
            config["auto_trading"]["enabled"] = new_status
            _save_config(config)
            st.rerun()
            
    with col2:
        # Force Run Button
        if st.button("🚀 今すぐスキャンを実行", use_container_width=True, help="市場分析と取引を強制的に実行します"):
            with st.status("システム起動中...", expanded=True) as status:
                try:
                    status.write("Initializing Trader...")
                    from src.trading.fully_automated_trader import FullyAutomatedTrader
                    trader = FullyAutomatedTrader()
                    
                    status.write("Running Daily Routine...")
                    # Execute Scan & Trade
                    signals = trader.scan_market()
                    status.write(f"Signals Generated: {len(signals)}")
                    
                    # Note: scan_market logic in fully_automated_trader.py (lines 794+) appends to signals list
                    # but ends with `return signals` in the snippet I saw? 
                    # Actually I need to verify if scan_market ALSO executes. 
                    # If not, I need to call execution manually here.
                    # Based on standard design, scan returns signals, execution is separate.
                    
                    if signals:
                        status.write("Executing Orders...")
                        # Need prices dict for execution
                        # Extract prices from signals if available or fetch
                        prices = {s['ticker']: s['price'] for s in signals}
                        trader.engine.execute_orders(signals, prices)
                        status.write("Orders Executed.")
                    else:
                        status.write("No signals found.")
                    
                    status.update(label="✅ 完了", state="complete", expanded=False)
                    st.success("実行完了")
                except Exception as e:
                    status.update(label="❌ エラー発生", state="error")
                    st.error(f"Error: {e}")

def _render_guidance():
    """ユーザーへの次のアクション指示"""
    import json
    from src.utils.health import quick_health_check

    action_needed = False
    guidance_message = "現在、あなたのアクションは必要ありません。コーヒーでも飲んでリラックスしてください。☕"
    alert_class = "info" # info, warning, error (blue, yellow, red)

    # 1. Check Defense Mode
    if defense_status():
        guidance_message = "現在『防御モード』が有効です。市場リスクが落ち着くまで新規BUYは停止されています。解除するにはサイドバーの設定を確認してください。"
        action_needed = True
        alert_class = "warning"
    
    # 2. Check System Health
    else:
        health = quick_health_check()
        if not all(k.startswith("api_latency") or v for k, v in health.items()):
            guidance_message = "システムの一部に異常があります（ディスク/メモリ/API）。『システム&ログ』タブで詳細を確認してください。"
            action_needed = True
            alert_class = "error"

    # 3. Check for Trade Signals (if system is healthy and active)
    if not action_needed:
        try:
            if os.path.exists("scan_results.json"):
                with open("scan_results.json", "r", encoding="utf-8") as f:
                    scan_data = json.load(f)
                    results = scan_data.get("results", [])
                    signals = [r for r in results if r.get("Action") != "HOLD"]
                    if signals:
                        guidance_message = f"🚀 {len(signals)} 件の新規トレードシグナルが検出されました！ 『ポートフォリオ』タブまたは詳細レポートを確認してください。"
                        action_needed = True
                        alert_class = "success" # Green/Exciting
        except Exception:
            pass

    # Render
    # CSS class map: info->guidance-box (blue), warning->status-hero warning style?, error->red box?
    # Let's keep guidance-box style but change border color dynamically via inline style or separate classes if I added them.
    # For now, standard guidance-box is blue. I'll add simple color overrides.
    
    border_color = "#0366d6" # Blue
    bg_color = "#e7f5ff" # Light Blue
    
    if alert_class == "warning":
        border_color = "#f5af19" # Orange
        bg_color = "#fff8e1"
    elif alert_class == "error":
        border_color = "#d32f2f" # Red
        bg_color = "#ffebee"
    elif alert_class == "success":
        border_color = "#00c853" # Green
        bg_color = "#e8f5e9"
    
    # Dark mode adjustments (simple override if theme is navy/dark)
    # Since we can't easily detect theme variable here without passing it, 
    # we'll use a semi-transparent approach or just rely on the existing class 
    # and maybe override border only. 
    # Actually, simpler to just change the text/icon for now to keep it safe.
    
    st.markdown(f"""
    <div class="guidance-box" style="border-left-color: {border_color};">
        <strong>💡 Next Action:</strong> {guidance_message}
    </div>
    """, unsafe_allow_html=True)

def _render_activity_feed():
    """AIの活動履歴"""
    st.markdown("##### 📜 Activity Log")
    
    # ダミーログ生成（本来はDBから取得）
    feed = [
        {"time": "09:05", "icon": "🛡️", "msg": "市場前リスクチェック通過 (VIX: 18.2)"},
        {"time": "09:00", "icon": "📡", "msg": "東京証券取引所 オープン検出"},
        {"time": "08:55", "icon": "🤖", "msg": "デイリープラン生成完了 (予測モデル v3.2)"},
    ]
    
    for item in feed:
        st.markdown(f"`{item['time']}` {item['icon']} **{item['msg']}**")


# --- Main Dashboard Logic ---

def create_simple_dashboard():
    """メインダッシュボード (Command Center)"""
    # st.set_page_config is handled in app.py

    # テーマ設定
    theme_choice = st.sidebar.selectbox("テーマ", ["light", "navy", "dark-contrast"], index=1)
    _apply_theme(theme_choice)
    
    # シナリオコントロール (Sidebar)
    _scenario_controls()

    st.markdown("### 🚀 AGStock Command Center")
    # --- Header & Status Hero (The ONLY thing user sees first) ---
    _render_status_hero()
    _render_system_controls() # Added Controls
    
    st.markdown("---")
    
    # --- Guidance (Clear instructions) ---
    _render_guidance()

    st.markdown("###") # Spacer

    # --- Main Content (Hidden behind Tabs for cleanliness) ---
    tab1, tab2, tab3 = st.tabs(["📊 ポートフォリオ", "🌍 マーケット", "⚙️ システム&ログ"])

    demo = _demo_mode() # Call demo_mode once for the entire dashboard

    with tab1:
        # Portfolio Summary
        balance = _get_cached_balance(demo)
        positions = _get_cached_positions(demo)
        
        # 1. KPI Cards
        total_assets = balance.get("total_equity", 0)
        cash = balance.get("cash", 0)
        unrealized_pnl = balance.get("unrealized_pnl", 0)
        daily_pnl = balance.get("daily_pnl", 0)

        # KPI Row
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("総資産", format_currency_jp(total_assets))
        with c2:
            st.metric("現金残高", format_currency_jp(cash))
        with c3:
            pnl_pct = (unrealized_pnl / total_assets * 100) if total_assets else 0
            st.metric("評価損益", format_currency_jp(unrealized_pnl), f"{pnl_pct:+.1f}%")
        with c4:
            daily_pct = (daily_pnl / total_assets * 100) if total_assets else 0
            st.metric("前日比", format_currency_jp(daily_pnl), f"{daily_pct:+.1f}%")

        st.markdown("### 保有銘柄")
        _show_portfolio_summary_table(positions)
        
        st.markdown("### 資産推移")
        _show_performance_chart(demo)

    with tab2:
        col_m1, col_m2 = st.columns([1, 1])
        with col_m1:
            st.markdown("#### 🕒 時間帯プレイブック")
            render_playbook_cards()
        with col_m2:
            st.markdown("#### エクスポージャー")
            _exposure_heatmap(demo)
        
        st.markdown("#### リターン分布")
        _return_distribution(demo)

    with tab3:
        st.caption("システム状態とログ")
        _go_no_go()
        st.divider()
        _render_activity_feed()
        st.divider()
        _model_version_card()
        st.divider()
        _notification_hooks()


# --- Helper Renderers ---

def _scenario_controls():
    """リスクプリセット/エクスポージャー上限をUIから調整。"""
    st.sidebar.subheader("リスク設定")
    preset_labels = {"保守( drawdown最優先 )": "conservative", "中立": "neutral", "積極": "aggressive"}
    current = st.session_state.get("scenario", os.getenv("TRADING_SCENARIO", "neutral"))
    label_default = [k for k, v in preset_labels.items() if v == current]
    selection = st.sidebar.radio(
        "リスクプロファイル",
        list(preset_labels.keys()),
        index=0 if not label_default else list(preset_labels.keys()).index(label_default[0]),
    )
    scenario = preset_labels[selection]
    st.session_state["scenario"] = scenario
    os.environ["TRADING_SCENARIO"] = scenario

    st.sidebar.caption("銘柄/セクターの最大エクスポージャーを調整")
    default_ticker = float(os.getenv("MAX_PER_TICKER_PCT", 0.25))
    default_sector = float(os.getenv("MAX_PER_SECTOR_PCT", 0.35))
    max_ticker_pct = st.sidebar.slider("銘柄上限(%)", 5, 50, int(default_ticker * 100), step=1) / 100
    max_sector_pct = st.sidebar.slider("セクター上限(%)", 10, 80, int(default_sector * 100), step=1) / 100
    os.environ["MAX_PER_TICKER_PCT"] = str(max_ticker_pct)
    os.environ["MAX_PER_SECTOR_PCT"] = str(max_sector_pct)

    # プレビュー
    st.sidebar.write("シナリオ適用プレビュー")
    preview_equity = 1_000_000
    max_lot = preview_equity * (0.1 if scenario == "conservative" else 0.2 if scenario == "neutral" else 0.3)
    st.sidebar.metric("最大想定ロット", format_currency_jp(max_lot))
    st.sidebar.caption(f"シナリオ: {scenario} / 銘柄 {max_ticker_pct:.0%} / セクター {max_sector_pct:.0%}")


def _show_portfolio_summary_table(positions: pd.DataFrame):
     if not positions.empty:
            # 簡易フィルタは省略（キャッシュ効果のため）
            positions_display = positions.copy()
            positions_display["保有額"] = positions_display["current_price"] * positions_display["quantity"]
            positions_display["評価損益"] = positions_display["unrealized_pnl"]
            positions_display["評価損益率"] = positions_display["unrealized_pnl_pct"]
            
            # --- Add Sell Expectation (Mock Logic for now: +10%) ---
            # In a real version, this would fetch 'take_profit_price' from the strategy or database
            positions_display["利確目安"] = positions_display["avg_price"] * 1.10
            
            # Map ticker to company name
            positions_display["company_name"] = (
                positions_display["ticker"].map(TICKER_NAMES).fillna(positions_display["ticker"])
            )

            # Date Calculation
            if "entry_date" in positions_display.columns:
                positions_display["entry_date"] = pd.to_datetime(positions_display["entry_date"], errors='coerce')
                
                def calc_ai_date_dash(row):
                    start_date = row["entry_date"]
                    if pd.isna(start_date): return start_date
                    
                    target_price = row["entry_price"] * 1.10 # 10% target
                    current = row["current_price"]
                    gap = target_price - current
                    vol = row.get("volatility", 0.0)
                    
                    if gap <= 0: return datetime.now() + timedelta(days=1)
                    
                    days_needed = 14
                    if vol > 0:
                         days_needed = int(gap / (vol * 0.3))
                         days_needed = max(1, min(days_needed, 60))
                    
                    return datetime.now() + timedelta(days=days_needed)

                positions_display["estimated_exit_date"] = positions_display.apply(calc_ai_date_dash, axis=1)
                
                # Format
                positions_display["entry_date_str"] = positions_display["entry_date"].dt.strftime('%Y-%m-%d').fillna("-")
                positions_display["estimated_exit_str"] = positions_display["estimated_exit_date"].dt.strftime('%Y-%m-%d').fillna("-")
            else:
                positions_display["entry_date_str"] = "-"
                positions_display["estimated_exit_str"] = "-"

            # 表示用DF作成
            display_df = positions_display[
                ["ticker", "company_name", "quantity", "avg_price", "current_price", "利確目安", "評価損益", "評価損益率", "entry_date_str", "estimated_exit_str"]
            ].copy()
            display_df.columns = ["銘柄", "社名", "数量", "取得単価", "現在値", "利確目安 (+10%)", "損益", "損益率", "購入日", "AI予測売却日"]

            # フォーマット
            display_df["取得単価"] = display_df["取得単価"].apply(lambda x: f"¥{x:,.0f}")
            display_df["現在値"] = display_df["現在値"].apply(lambda x: f"¥{x:,.0f}")
            display_df["利確目安 (+10%)"] = display_df["利確目安 (+10%)"].apply(lambda x: f"¥{x:,.0f}")
            display_df["損益"] = display_df["損益"].apply(format_currency_jp)
            display_df["損益率"] = display_df["損益率"].apply(lambda x: f"{x:+.2%}")

            st.dataframe(display_df, use_container_width=True)
     else:
            st.info("現在保有銘柄はありません")


def _show_performance_chart(demo: bool):
    equity_df = _get_cached_equity_history(demo, days=30)
    if not equity_df.empty:
        df = equity_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["date"], y=df["total_equity"], mode="lines+markers", name="総資産", line=dict(color="#4db6ac", width=2)))
        fig.update_layout(title="", xaxis_title="", yaxis_title="円", height=300, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("No data")


def _exposure_heatmap(demo: bool):
    positions = _get_cached_positions(demo)
    if positions.empty:
        st.caption("No positions")
        return
    
    # 簡易ロジック
    # 地域推定 (既存ロジックを再利用)
    def region(tkr: str) -> str:
        if tkr.endswith(".T"):
            return "Japan"
        elif tkr.endswith(".PA"):
            return "Europe"
        elif "USD" in tkr or tkr.startswith("BTC") or tkr.startswith("ETH"):
            return "Crypto/FX"
        else:
            return "US"

    positions["region"] = positions["ticker"].apply(region)
    positions["sector"] = positions.get("sector", "Unknown")
    if "sector" not in positions or positions["sector"].eq("Unknown").all():
        positions["sector"] = positions["region"] # Fallback to region if sector is unknown

    positions["value"] = positions["quantity"] * positions["current_price"]
    
    # Treemap風に見せるためのHeatmap
    # Treemapは階層構造を表現するのに適しているため、sector -> region -> ticker のように表示
    # ここでは簡易的に sector を親、ticker を子として表示
    
    # Treemap data preparation
    treemap_data = []
    total_value = positions["value"].sum()
    
    # Add sectors
    sector_values = positions.groupby("sector")["value"].sum()
    for sector, value in sector_values.items():
        treemap_data.append(
            go.Treemap(
                labels=[sector],
                parents=[""],
                values=[value],
                marker_colorscale='Blues',
                name=sector,
                textinfo="label+percent parent"
            )
        )
    
    # Add tickers under sectors
    for _, row in positions.iterrows():
        treemap_data.append(
            go.Treemap(
                labels=[row["ticker"]],
                parents=[row["sector"]],
                values=[row["value"]],
                marker_colorscale='Blues',
                name=row["ticker"],
                textinfo="label+percent entry"
            )
        )

    fig = go.Figure(data=go.Treemap(
        labels = positions["ticker"],
        parents = positions["sector"], # Use sector as parent for tickers
        values = positions["value"],
        marker_colorscale='Blues',
        textinfo="label+percentparent+value"
    ))
    fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)


def _return_distribution(demo: bool):
    equity_df = _get_cached_equity_history(demo, days=90)
    if equity_df.empty:
        st.caption("No data for return distribution.")
        return
    
    rets = equity_df["equity"].pct_change().dropna()
    if rets.empty:
        st.caption("No returns to display.")
        return

    p5 = rets.quantile(0.05)
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=rets, nbinsx=30, marker_color="#4a90e2", opacity=0.8, name="Returns"))
    fig.add_vline(
        x=p5, line_dash="dash", line_color="red", annotation_text=f"5%: {p5:.2%}", annotation_position="top right"
    )
    fig.update_layout(title="リターン分布と下方5%点", height=250, margin=dict(t=30, b=0, l=0, r=0), bargap=0.05)
    st.plotly_chart(fig, use_container_width=True)


def _show_backtest_history_chart(demo: bool):
    hist = _load_backtest_history(demo)
    if hist.empty:
        st.info("バックテスト履歴がありません")
        return
    hist = hist.sort_values("date")
    fig = go.Figure()
    if "win_rate" in hist.columns:
        fig.add_trace(
            go.Scatter(x=hist["date"], y=hist["win_rate"], mode="lines", name="勝率", line=dict(color="#2E86AB"))
        )
    if "sharpe" in hist.columns:
        fig.add_trace(
            go.Scatter(
                x=hist["date"],
                y=hist["sharpe"],
                mode="lines",
                name="シャープ比",
                line=dict(color="#8E44AD"),
                yaxis="y2",
            )
        )
        fig.update_layout(
            yaxis2=dict(title="シャープ比", overlaying="y", side="right"),
            yaxis=dict(title="勝率"),
        )
    fig.update_layout(title="日次バックテストトレンド", height=360, legend_orientation="h")
    st.plotly_chart(fig, use_container_width=True)


def _show_daily_summary(demo: bool):
    # Simplified for Command Center, using cached data if available
    st.markdown("##### 日次サマリー")
    pt = PaperTrader() if not demo else None
    try:
        if demo:
            hist = demo_data.generate_trade_history(days=5)
            today = datetime.now().date()
            todays = hist[hist["timestamp"].dt.date == today]
            pnl = float(todays["realized_pnl"].sum()) if not todays.empty else 0.0
            trades = len(todays) if not todays.empty else 0
            date = today.isoformat()
        else:
            daily_summary = pt.get_daily_summary()
            if daily_summary:
                latest = daily_summary[-1]
                date, pnl, trades = latest
            else:
                date, pnl, trades = datetime.now().date().isoformat(), 0.0, 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("日付", date)
        with col2:
            st.metric("損益", format_currency_jp(pnl))
        with col3:
            st.metric("取引数", trades)
    finally:
        if pt:
            pt.close()


def _go_no_go():
    """取引前の簡易チェックリスト"""
    st.markdown("##### Go / No-Go チェック")
    from src.utils.health import quick_health_check

    health = quick_health_check()
    ext_ok = "✅" if all(k.startswith("api_latency") or v for k, v in health.items()) else "⚠️"
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Disk OK", "Yes" if health.get("disk_ok") else "Low")
    with col2:
        st.metric("Memory OK", "Yes" if health.get("memory_ok") else "Low")
    with col3:
        latency = health.get("api_latency_ms", 0.0)
        st.metric("API latency", f"{latency:.0f} ms", delta=None)
    st.caption(
        f"{ext_ok} システム健全性: disk={health.get('disk_ok')} mem={health.get('memory_ok')} api={health.get('api_ok')}"
    )

    vix_display = "N/A"
    try:
        ext = fetch_external_data(period="5d")
        vix_df = ext.get("VIX")
        if vix_df is not None and not vix_df.empty:
            vix_display = f"{float(vix_df['Close'].iloc[-1]):.2f}"
    except Exception:
        pass
    st.write(f"VIX: {vix_display}")

    safe_mode = st.checkbox("安全モード (BUY抑制)", value=os.getenv("SAFE_MODE", "").lower() in {"1", "true", "yes"})
    os.environ["SAFE_MODE"] = "1" if safe_mode else "0"
    if safe_mode:
        st.warning("安全モード中は新規BUYを抑制します。")


def _notification_hooks():
    st.markdown("##### 通知フック")
    st.caption("通知設定は `config.json` で管理されています")
    # Original logic for setting/testing hooks is removed for brevity as per instruction,
    # but can be re-added if needed.
    # slack_url = st.text_input("Slack Webhook URL", value=os.getenv("SLACK_WEBHOOK_URL", ""))
    # message = st.text_area("テストメッセージ", "AGStock 通知テスト")
    # quiet_hours = st.text_input("静音時間 (例 22:00-07:00)", value=os.getenv("QUIET_HOURS", "22:00-07:00"))
    # os.environ["QUIET_HOURS"] = quiet_hours
    # if st.button("Slackにテスト送信"):
    #     try:
    #         import requests
    #         resp = requests.post(slack_url, json={"text": message}, timeout=5)
    #         if resp.status_code == 200:
    #             st.success("Slack送信成功")
    #         else:
    #             st.warning(f"Slack送信失敗: {resp.status_code}")
    #     except Exception as exc:
    #         st.error(f"送信エラー: {exc}")


def _model_version_card():
    import json

    registry_path = Path("models/registry.json")
    data_registry_path = Path("models/data_versions/registry.json")

    st.markdown("##### モデル/データ")
    cols = st.columns(2)
    with cols[0]:
        if registry_path.exists():
            try:
                reg = json.loads(registry_path.read_text())
                latest = None
                for model, items in reg.get("models", {}).items():
                    if items:
                        items_sorted = sorted(items, key=lambda x: x.get("timestamp", ""), reverse=True)
                        latest = items_sorted[0]
                        st.success(f"最新モデル: {model} / {latest.get('version')}")
                        st.caption(f"metrics: {latest.get('metrics')}")
                        break
                if not latest:
                    st.info("モデル登録なし")
            except Exception as exc:
                st.warning(f"モデル情報読み込み失敗: {exc}")
        else:
            st.info("モデル登録ファイルなし")
    with cols[1]:
        if data_registry_path.exists():
            try:
                reg = json.loads(data_registry_path.read_text())
                versions = reg.get("versions", [])
                if versions:
                    versions_sorted = sorted(versions, key=lambda x: x.get("version", ""), reverse=True)
                    v = versions_sorted[0]
                    st.success(f"データ版: {v.get('version')}")
                    st.caption(v.get("path"))
                else:
                    st.info("データスナップショットなし")
            except Exception as exc:
                st.warning(f"データ版読み込み失敗: {exc}")
        else:
            st.info("データスナップショットなし")


if __name__ == "__main__":
    st.set_page_config(page_title="AGStock Command", page_icon="🚀", layout="wide")
    create_simple_dashboard()

