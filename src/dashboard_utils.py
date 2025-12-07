"""
ダッシュボード用ユーティリティ関数
"""
import streamlit as st
import pandas as pd
import datetime
import time
import subprocess
from src.paper_trader import PaperTrader

def check_and_execute_missed_trades():
    """
    起動時に前日の取引が未実行なら自動実行する関数
    
    ダッシュボードの起動時に呼び出すことで、
    15:30に起動していなくても自動取引を補完します。
    """
    # セッション状態で1回だけ実行
    if 'auto_trade_checked' in st.session_state:
        return
    
    st.session_state.auto_trade_checked = True
    
    try:
        pt = PaperTrader()
        
        # 最後の取引日を確認
        history = pt.get_trade_history(limit=1)
        today = datetime.date.today()
        
        # 取引履歴がない、または最後の取引が今日でない場合
        should_trade = False
        
        if history.empty:
            should_trade = True
        else:
            # 日付カラムの特定
            date_col = 'date'
            if 'date' not in history.columns and 'timestamp' in history.columns:
                date_col = 'timestamp'
                
            if date_col in history.columns:
                last_trade_date = pd.to_datetime(history[date_col].iloc[0]).date()
                # 平日で、最後の取引が昨日以前なら実行
                if today.weekday() < 5 and last_trade_date < today:
                    should_trade = True
        
        if should_trade:
            # バックグラウンドで自動取引実行
            with st.spinner("📊 前回の取引を実行中..."):
                # fully_automated_trader.py を実行
                result = subprocess.run(
                    ["python", "fully_automated_trader.py", "--force"],
                    capture_output=True,
                    text=True,
                    timeout=180  # 3分タイムアウト
                )
                
                if result.returncode == 0:
                    st.success("✅ 前回の取引を自動実行しました！")
                    time.sleep(2)
                    st.experimental_rerun()
                else:
                    st.error(f"自動取引エラー: {result.stderr}")
        
        pt.close()
        
    except Exception as e:
        # エラーは無視（通常の表示を続ける）
        print(f"Auto-trade check error: {e}")
        pass
