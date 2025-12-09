"""
Ghostwriter UI Module
自動生成された投資レポートを表示する
"""
import streamlit as st
import os
import glob
import logging

def render_reports_tab():
    """レポートタブを表示"""
    st.header("📰 The Ghostwriter Reports")
    st.caption("AIヘッジファンドマネージャーによる週次運用報告書")
    
    reports_dir = "reports"
    
    # ディレクトリ確認
    if not os.path.exists(reports_dir):
        st.info("📭 まだレポートはありません。今週の金曜日に最初のレポートが届きます。")
        # 手動生成ボタン（デバッグ用・初週用）
        if st.button("📝 今すぐレポートを生成する (Beta)"):
            with st.spinner("AIがレポートを執筆中..."):
                try:
                    from src.ghostwriter import Ghostwriter
                    gw = Ghostwriter()
                    path = gw.generate_weekly_report()
                    st.success("✅ レポートが完成しました！")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"生成エラー: {e}")
        return

    # ファイル一覧取得（新しい順）
    files = glob.glob(os.path.join(reports_dir, "*.md"))
    files.sort(key=os.path.getmtime, reverse=True)
    
    if not files:
        st.info("📭 まだレポートはありません。")
        if st.button("📝 今すぐレポートを生成する (Beta)"):
            with st.spinner("AIがレポートを執筆中..."):
                from src.ghostwriter import Ghostwriter
                gw = Ghostwriter()
                gw.generate_weekly_report()
                st.experimental_rerun()
        return

    # レイアウト: 左にリスト、右に本文
    col_list, col_content = st.columns([1, 3])
    
    # 選択状態管理
    if 'selected_report' not in st.session_state:
        st.session_state.selected_report = files[0]
        
    with col_list:
        st.markdown("### 📚 バックナンバー")
        for f in files:
            # ファイル名から日付抽出 (weekly_report_20231201_120000.md)
            basename = os.path.basename(f)
            display_name = basename.replace("weekly_report_", "").replace(".md", "")
            try:
                # 日付フォーマット変換
                date_part = display_name.split("_")[0] # 20231201
                display_date = f"{date_part[:4]}/{date_part[4:6]}/{date_part[6:]}"
            except:
                display_date = display_name
                
            # 選択ボタン
            is_selected = (f == st.session_state.selected_report)
            label = f"📄 {display_date}"
            if is_selected:
                label = f"👉 {display_date}"
                
            if st.button(label, key=f, use_container_width=True, type="primary" if is_selected else "secondary"):
                st.session_state.selected_report = f
                st.experimental_rerun()

    with col_content:
        target_file = st.session_state.selected_report
        if os.path.exists(target_file):
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # カード風に表示
            st.markdown(f"""
            <div style="background: white; padding: 2rem; border-radius: 12px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                {content}
            </div>
            """, unsafe_allow_html=False) # Markdownとしてレンダリング (HTMLタグは含めない)
            
            # ここではMarkdownコンテンツ自体を表示したいので st.markdown(content) を使うべき
            # Boxに入れるために st.markdown 自体は使えないので、コンテナを使う
            
            with st.container():
                 st.markdown(content)
                 
            st.caption("---")
            st.caption("※ このレポートはAIによって自動生成されています。")
