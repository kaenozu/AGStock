"""
ホームダッシュボード - 概要表示とクイックアクション
"""
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from src.ui_components import (
    display_best_pick_card,
    display_error_message
)
from src.formatters import format_currency, get_risk_level
from src.paper_trader import PaperTrader


def show_home_page():
    """ホームダッシュボードを表示"""
    
    st.header("🏠 ホームダッシュボード")
    st.markdown("本日のマーケット概要と推奨アクションを表示します。")
    
    # === KPIメトリクス ===
    col1, col2, col3 = st.columns(3)
    
    # キャッシュデータの読み込み
    cached_results = None
    if os.path.exists("scan_results.json"):
        try:
            with open("scan_results.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                scan_date = datetime.strptime(data['scan_date'], '%Y-%m-%d %H:%M:%S')
                if scan_date.date() == datetime.now().date():
                    cached_results = data
        except Exception as e:
            display_error_message(
                "data",
                "スキャン結果の読み込みに失敗しました。",
                str(e)
            )
    
    # Paper Trader情報
    pt = PaperTrader()
    balance = pt.get_current_balance()
    
    with col1:
        signal_count = len(cached_results['results']) if cached_results else 0
        buy_signals = sum(1 for r in cached_results['results'] if r['Action'] == 'BUY') if cached_results else 0
        st.metric("推奨シグナル", f"{buy_signals}件", f"全{signal_count}件")
    
    with col2:
        total_equity = balance['total_equity']
        profit = total_equity - pt.initial_capital
        profit_pct = (profit / pt.initial_capital) * 100
        st.metric(
            "ポートフォリオ評価額",
            format_currency(total_equity),
            f"{profit_pct:+.2f}%"
        )
    
    with col3:
        if cached_results and 'sentiment' in cached_results:
            sentiment_score = cached_results['sentiment']['score']
            sentiment_label = cached_results['sentiment']['label']
            st.metric("市場センチメント", sentiment_label, f"{sentiment_score:.2f}")
        else:
            st.metric("市場センチメント", "N/A", "")
    
    st.markdown("---")
    
    # === 今日のイチオシ ===
    if cached_results and cached_results['results']:
        results_df = pd.DataFrame(cached_results['results'])
        actionable_df = results_df[results_df['Action'] != 'HOLD'].copy()
        
        if not actionable_df.empty:
            actionable_df = actionable_df.sort_values(by="Return", ascending=False)
            best_pick = actionable_df.iloc[0]
            
            # リスクレベル判定
            risk_level = get_risk_level(best_pick.get('Max Drawdown', -0.15))
            
            # 注文コールバック
            def handle_order(ticker, action, price):
                trade_action = "BUY" if "BUY" in action else "SELL"
                trading_unit = st.session_state.get('trading_unit', 100)
                
                if pt.execute_trade(ticker, trade_action, trading_unit, price, reason="Home Best Pick"):
                    st.balloons()
                    st.success(f"{best_pick['Name']} を {trading_unit}株 {trade_action} しました！")
                else:
                    st.error("注文に失敗しました（資金不足または保有株不足）。")
            
            # 追加情報
            additional_info = {}
            if 'PER' in best_pick and pd.notna(best_pick['PER']):
                additional_info['PER'] = best_pick['PER']
            if 'PBR' in best_pick and pd.notna(best_pick['PBR']):
                additional_info['PBR'] = best_pick['PBR']
            if 'ROE' in best_pick and pd.notna(best_pick['ROE']):
                additional_info['ROE'] = best_pick['ROE']
            
            display_best_pick_card(
                ticker=best_pick['Ticker'],
                name=best_pick['Name'],
                action=best_pick['Action'],
                price=best_pick['Last Price'],
                explanation=best_pick.get('Explanation', ''),
                strategy=best_pick['Strategy'],
                risk_level=risk_level,
                on_order_click=handle_order,
                additional_info=additional_info if additional_info else None
            )
        else:
            st.info("現在、有効な推奨シグナルはありません。")
    else:
        st.info("まだスキャンが実行されていません。「市場分析」タブでスキャンを開始してください。")
    
    st.markdown("---")
    
    # === クイックアクション ===
    st.subheader("🚀 クイックアクション")
    
    st.info("💡 クイックアクションは現在開発中です。ダッシュボードから各機能にアクセスしてください。")
    
    # col_a, col_b, col_c = st.columns(3)
    # 
    # with col_a:
    #     if st.button("🔍 市場をスキャン", use_container_width=True, type="primary"):
    #         st.switch_page("pages/analysis.py")
    # 
    # with col_b:
    #     if st.button("💼 ポートフォリオ", use_container_width=True):
    #         st.switch_page("pages/portfolio.py")
    # 
    # with col_c:
    #     if st.button("📝 取引する", use_container_width=True):
    #         st.switch_page("pages/trade.py")
    
    st.markdown("---")
    
    # === 最近の取引履歴 ===
    st.subheader("📋 最近の取引")
    
    history = pt.get_trade_history(limit=5)
    if not history.empty:
        # 表示用にフォーマット
        display_history = history.copy()
        display_history['price'] = display_history['price'].apply(lambda x: format_currency(x))
        display_history = display_history[['timestamp', 'ticker', 'action', 'quantity', 'price']]
        display_history.columns = ['日時', '銘柄', 'アクション', '数量', '価格']
        
        st.dataframe(display_history, use_container_width=True, hide_index=True)
        
        if st.button("すべての取引履歴を見る"):
            st.switch_page("pages/trade.py")
    else:
        st.info("まだ取引履歴がありません。")
    
    st.markdown("---")
    
    # === システムステータス ===
    with st.expander("⚙️ システムステータス", expanded=False):
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            st.markdown("**データキャッシュ**")
            if cached_results:
                st.success(f"✅ 最新（{cached_results['scan_date']}）")
            else:
                st.warning("⚠️ データなし")
            
            st.markdown("**Paper Trading**")
            positions = pt.get_positions()
            st.info(f"📊 保有銘柄: {len(positions)}件")
        
        with status_col2:
            st.markdown("**通知設定**")
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    line_enabled = config.get("notifications", {}).get("line", {}).get("enabled", False)
                    if line_enabled:
                        st.success("✅ LINE通知: 有効")
                    else:
                        st.info("ℹ️ LINE通知: 無効")
            except:
                st.warning("⚠️ 設定ファイルなし")
            
            st.markdown("**リスク管理**")
            risk_enabled = st.session_state.get('risk_guard_enabled', True)
            if risk_enabled:
                st.success("✅ RiskGuard: 有効")
            else:
                st.warning("⚠️ RiskGuard: 無効")


if __name__ == "__main__":
    show_home_page()
