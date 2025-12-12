"""
個人投賁E��向けシンプルダチE��ュボ�EチE(Ultra Simple Version)

一目でわかる賁E��状況E- Zero-Touch Mode
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from src.paper_trader import PaperTrader


def format_currency_jp(amount: float) -> str:
    """日本冁E��丁E�E形式で表示"""
    if amount >= 100000000:
        return f"¥{amount/100000000:.2f}儁E
    elif amount >= 10000:
        return f"¥{amount/10000:.1f}丁E
    else:
        return f"¥{amount:,.0f}"


def _show_market_status():
    """市場開閉状況を表示"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    markets = []
    
    # 東京証券取引所 (9:00-11:30, 12:30-15:00 JST)
    if weekday < 5:  # 平日
        if (9 <= hour < 11) or (hour == 11 and minute < 30) or (12 <= hour < 15 and not (hour == 12 and minute < 30)):
            markets.append(("�E�E 東京", "🟢 取引中", "green"))
        elif 15 <= hour < 24 or hour < 9:
            markets.append(("�E�E 東京", "🔴 閉場", "red"))
        else:
            markets.append(("�E�E 東京", "🟡 昼休み", "orange"))
    else:
        markets.append(("�E�E 東京", "🔴 週末", "red"))
    
    # NY証券取引所 (23:30-6:00 JST = 9:30-16:00 EST)
    if weekday < 5 or (weekday == 0 and hour < 6):
        if (hour >= 23 and minute >= 30) or (hour < 6):
            markets.append(("�E�E NY", "🟢 取引中", "green"))
        else:
            markets.append(("�E�E NY", "🔴 閉場", "red"))
    else:
        markets.append(("�E�E NY", "🔴 週末", "red"))
    
    # 表示
    cols = st.columns(len(markets) + 1)
    with cols[0]:
        st.caption(f"🕐 {now.strftime('%H:%M')}")
    for i, (name, status, color) in enumerate(markets):
        with cols[i + 1]:
            st.markdown(f"**{name}** {status}")


def create_simple_dashboard():
    """Ultra Simple Dashboard - Zero-Touch Mode"""
    
    st.title("💼 マイポ�Eトフォリオ")
    
    # チE�Eタ取征E(Initialize early/before auto-trade logic)
    pt = PaperTrader()

    # 市場開閉状況を表示
    _show_market_status()
    
    # 自動更新トグル
    col_refresh1, col_refresh2 = st.columns([3, 1])
    with col_refresh2:
        auto_refresh = st.checkbox("🔄 自動更新", value=False, help="30秒ごとに自動更新")
    
    if auto_refresh:
        import time
        st_autorefresh = st.empty()
        with st_autorefresh:
            st.caption("⏳ 30秒後に自動更新されまぁE..")
        time.sleep(0.1)  # Allow UI to render
        # Use st.experimental_rerun() after 30 seconds via JavaScript
        st.markdown("""
        <script>
        setTimeout(function() {
            window.location.reload();
        }, 30000);
        </script>
        """, unsafe_allow_html=True)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 自動取引�Eタン (True Full-Auto)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    col_auto1, col_auto2 = st.columns([1, 3])
    with col_auto1:
        run_auto = st.button("🚀 自動スキャン & 取弁E, type="primary", help="AIが市場をスキャンして自動で取引を実行しまぁE)
    
    if run_auto:
        with st.spinner("🤁EAIが市場をスキャン中..."):
            try:
                from src.trading.fully_automated_trader import FullyAutomatedTrader
                
                trader = FullyAutomatedTrader()
                
                # 安�EチェチE��
                is_safe, reason = trader.is_safe_to_trade()
                if not is_safe:
                    st.warning(f"⚠�E�E取引を中止しました: {reason}")
                else:
                    # ポジション評価
                    st.info("📊 保有ポジションを評価中...")
                    exit_signals = trader.evaluate_positions()
                    if exit_signals:
                        st.info(f"📤 {len(exit_signals)}件の決済シグナルを実行中...")
                        trader.execute_signals(exit_signals)
                    
                    # 市場スキャン
                    st.info("🔍 市場をスキャン中...")
                    buy_signals = trader.scan_market()
                    if buy_signals:
                        st.info(f"📥 {len(buy_signals)}件の購入シグナルを実行中...")
                        trader.execute_signals(buy_signals)
                        st.success(f"✁E{len(buy_signals)}件の取引を実行しました�E�E)
                        st.balloons()
                    else:
                        st.info("📊 現時点で良ぁE��グナルが見つかりませんでした。次回�Eスキャンをお征E��ください、E)
                    
                    # 価格更新
                    pt.update_daily_equity()
                    
            except Exception as e:
                st.error(f"❁Eエラーが発生しました: {e}")
    
    # チE�Eタ取征E
    # pt = PaperTrader() # Moved to top
    balance = pt.get_current_balance()
    positions = pt.get_positions()
    equity_history = pt.get_equity_history()
    
    total_equity = balance['total_equity']
    cash = balance['cash']
    unrealized_pnl = balance['unrealized_pnl']
    
    # 日次損益計箁E
    if len(equity_history) >= 2:
        yesterday_equity = equity_history.iloc[-2]['total_equity']
        daily_pnl = total_equity - yesterday_equity
        daily_change_pct = (daily_pnl / yesterday_equity) if yesterday_equity > 0 else 0
    else:
        daily_pnl = 0
        daily_change_pct = 0
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. スチE�Eタスバナー (1行で全て表示)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 総賁E��", 
            value=format_currency_jp(total_equity),
            delta=f"{daily_change_pct:+.2%}"
        )
    
    with col2:
        cash_ratio = cash / total_equity if total_equity > 0 else 0
        status_emoji = "🟢" if 0.2 <= cash_ratio <= 0.5 else "🟡"
        st.metric(
            label=f"{status_emoji} 現金比率",
            value=f"{cash_ratio:.0%}",
            delta=None
        )
    
    with col3:
        num_positions = len(positions)
        st.metric(
            label="📊 保有銘柄",
            value=f"{num_positions}銘柄",
            delta=None
        )
    
    st.divider()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. ポ�Eトフォリオ診断 (Risk Radar) - Phase 6
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # --- 持E��計箁E---
    # 1. 雁E��度スコア (PortfolioRiskAnalyzer使用)
    from src.portfolio_risk import PortfolioRiskAnalyzer
    risk_analyzer = PortfolioRiskAnalyzer()
    
    if num_positions == 0:
        diversity_score = 0
    else:
        diversity_score = risk_analyzer.calculate_concentration_score(positions)
        
    # 2. 賁E��効玁E
    cash_ratio = cash / total_equity if total_equity > 0 else 0
    if 0.1 <= cash_ratio <= 0.4:
         efficiency_score = 100
    elif cash_ratio < 0.1:
         efficiency_score = 60
    else:
         efficiency_score = max(0, 100 - (cash_ratio - 0.4) * 200)

    # 3. AI期征E�� (含み益銘柁E��)
    if not positions.empty and 'unrealized_pnl' in positions.columns:
        profitable_positions = len(positions[positions['unrealized_pnl'] > 0])
        sentiment_score = (profitable_positions / num_positions) * 100
    else:
        sentiment_score = 50

    # 4. 安定性 (含み損回避度)
    if not positions.empty and 'unrealized_pnl_pct' in positions.columns:
        min_pnl_pct = positions['unrealized_pnl_pct'].min()
        if min_pnl_pct < -0.1:
            stability_score = 40
        elif min_pnl_pct < -0.05:
            stability_score = 70
        else:
            stability_score = 95
    else:
        stability_score = 100

    # --- レーダーチャート描画 ---
    radar_data = pd.DataFrame(dict(
        r=[diversity_score, efficiency_score, sentiment_score, stability_score],
        theta=['刁E��劁E, '賁E��効玁E, 'AI期征E��', '安定性']
    ))
    
    col_radar1, col_radar2 = st.columns([1, 1])
    
    with col_radar1:
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_data['r'],
            theta=radar_data['theta'],
            fill='toself',
            name='Stats',
            line_color='#00D9FF',
            fillcolor='rgba(0, 217, 255, 0.2)'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
                bgcolor='rgba(0,0,0,0)'
            ),
            showlegend=False,
            height=280,
            margin=dict(l=30, r=30, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_radar2:
        # 総合スコア
        total_score = int((diversity_score + efficiency_score + sentiment_score + stability_score) / 4)
        if total_score >= 80:
            rank, r_color, desc = "S", "#00ff9d", "Professional State"
        elif total_score >= 60:
            rank, r_color, desc = "A", "#00D9FF", "Good Condition"
        elif total_score >= 40:
            rank, r_color, desc = "B", "#FFA500", "Balance Needed"
        else:
            rank, r_color, desc = "C", "#FF4444", "Caution"

        st.markdown(f"""
        ### ランク: <span style='color:{r_color}'>{rank}</span>
        **総合スコア: {total_score}**
        
        {desc}
        """, unsafe_allow_html=True)
        
        # リスク警呁E
        if not positions.empty:
            alerts = risk_analyzer.get_risk_alerts(positions)
            if alerts:
                st.markdown("---")
                for alert in alerts:
                    if alert['level'] == 'warning':
                        st.warning(alert['message'])
                    else:
                        st.info(alert['message'])

    st.divider()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. AI スチE�Eタス (シンプル)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if unrealized_pnl >= 0:
        st.success(f"✁E**全自動運用中** - 含み盁E {format_currency_jp(unrealized_pnl)}")
    else:
        st.warning(f"⚠�E�E**全自動運用中** - 含み搁E {format_currency_jp(abs(unrealized_pnl))}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2.5 シスチE��活動ログ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    import os
    import json
    
    with st.expander("🤁EAIの活動状況E, expanded=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("**📡 監視状況E*")
            st.markdown("- 🎯 対象市場: 日本株 (N225)")
            st.markdown("- 📊 監視銘柁E��: 225銘柄")
            st.markdown("- ⏰ スキャン間隔: 1時間")
        
        with col_b:
            # Last scan info
            last_scan = "未実衁E
            if os.path.exists("scan_results.json"):
                try:
                    with open("scan_results.json", "r", encoding="utf-8") as f:
                        scan_data = json.load(f)
                        last_scan = scan_data.get("scan_date", "不�E")
                except Exception:
                    last_scan = "読み込みエラー"
            
            st.markdown("**🕐 最終スキャン**")
            st.markdown(f"- {last_scan}")
        
        # Recent trades
        trade_history = pt.get_trade_history()
        if not trade_history.empty:
            st.markdown("**📝 直近�E取弁E(最新5件)**")
            recent_trades = trade_history.tail(5)[['timestamp', 'ticker', 'action', 'quantity', 'price']].copy()
            recent_trades.columns = ['日晁E, '銘柄', '売買', '数釁E, '価格']
            st.dataframe(recent_trades, use_container_width=True, hide_index=True)
        else:
            st.info("まだ取引�Eありません、EIが最適なタイミングを征E��てぁE��す、E)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. ポジション一覧 (コンパクチE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not positions.empty:
        st.subheader("📋 保有ポジション")
        from src.constants import TICKER_NAMES
        
        display_df = positions.copy()
        # Add Name and Acquisition Cost
        display_df['銘柄吁E] = display_df['ticker'].map(lambda x: TICKER_NAMES.get(x, x))
        display_df['取得��顁E] = display_df['entry_price'] * display_df['quantity']
        display_df['時価評価顁E] = display_df['current_price'] * display_df['quantity']
        
        display_df['コーチE] = display_df['ticker']
        display_df['株数'] = display_df['quantity'].apply(lambda x: f"{x:,}")
        display_df['取得単価'] = display_df['entry_price'].apply(lambda x: f"¥{x:,.0f}")
        display_df['現在価格'] = display_df['current_price'].apply(lambda x: f"¥{x:,.0f}")
        display_df['取得��顁E] = display_df['取得��顁E].apply(lambda x: f"¥{x:,.0f}")
        display_df['時価評価顁E] = display_df['時価評価顁E].apply(lambda x: f"¥{x:,.0f}")
        
        display_df['損�Eりライン'] = (display_df['entry_price'] * 0.90).apply(lambda x: f"¥{x:,.0f}")  # -10%
        display_df['損益'] = display_df['unrealized_pnl'].apply(lambda x: f"¥{x:+,.0f}")
        display_df['損益玁E] = display_df['unrealized_pnl_pct'].apply(lambda x: f"{x:+.1%}")
        
        # 購入日があれ�E表示
        cols = ['銘柄吁E, 'コーチE, '株数', '取得単価', '取得��顁E, '現在価格', '時価評価顁E, '損益', '損益玁E]
        if 'entry_date' in display_df.columns:
            display_df['購入日'] = pd.to_datetime(display_df['entry_date']).dt.strftime('%Y/%m/%d')
            cols.insert(1, '購入日')
        
        st.dataframe(
            display_df[cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("🤁EAI銘柄選定中... ポジションはまだありません")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3.5 月次パフォーマンスヒ�Eト�EチE�E
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with st.expander("📊 月次パフォーマンス", expanded=False):
        from src.performance import PerformanceAnalyzer
        
        analyzer = PerformanceAnalyzer()
        monthly_data = analyzer.get_monthly_heatmap_data()
        perf_summary = analyzer.get_performance_summary()
        
        if not monthly_data.empty:
            # サマリー表示
            col_s1, col_s2, col_s3 = st.columns(3)
            
            with col_s1:
                st.metric("総取引回数", f"{perf_summary['total_trades']}囁E)
            with col_s2:
                st.metric("勝率", f"{perf_summary['win_rate']:.1f}%")
            with col_s3:
                st.metric("累計損盁E, f"¥{perf_summary['total_return']:+,.0f}")
            
            st.markdown("---")
            
            # ヒ�Eト�EチE�E
            import plotly.express as px
            
            # ピ�EチE��チE�Eブル作�E
            pivot_data = monthly_data.pivot(index='month_name', columns='year', values='monthly_return')
            
            fig_heatmap = px.imshow(
                pivot_data,
                labels=dict(x="年", y="朁E, color="損益 (冁E"),
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0,
                aspect="auto"
            )
            
            fig_heatmap.update_layout(
                title="月次パフォーマンス ヒ�Eト�EチE�E",
                height=400,
                xaxis_title="年",
                yaxis_title="朁E
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # ベスチEワースト月
            if perf_summary['best_month']:
                col_b, col_w = st.columns(2)
                with col_b:
                    best = perf_summary['best_month']
                    st.success(f"🏆 最高月: {best['year']}年{best['month']}朁E(+¥{best['return']:,.0f})")
                with col_w:
                    worst = perf_summary['worst_month']
                    st.error(f"📉 最低月: {worst['year']}年{worst['month']}朁E(¥{worst['return']:+,.0f})")
        else:
            st.info("まだ取引履歴がありません。取引を開始するとパフォーマンスが表示されます、E)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4. 賁E��推移チャーチE(シンプル)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not equity_history.empty and len(equity_history) > 1:
        with st.expander("📈 賁E��推移を表示", expanded=False):
            recent_equity = equity_history.tail(30)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=recent_equity['date'],
                y=recent_equity['total_equity'],
                mode='lines',
                name='総賁E��',
                line=dict(color='#00D9FF', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 217, 255, 0.1)'
            ))
            
            fig.update_layout(
                height=250,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title=None,
                yaxis_title=None,
                showlegend=False,
                template='plotly_dark'
            )
            
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    create_simple_dashboard()
