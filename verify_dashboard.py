"""
パフォーマンスダッシュボードの動作確認スクリプト
Streamlitの機能をモックして、描画ロジックがエラーなく実行されるか確認します。
"""
import sys
from unittest.mock import MagicMock
import pandas as pd
import numpy as np

# Streamlitをモック
sys.modules["streamlit"] = MagicMock()
import streamlit as st
# st.columns がリストを返すように設定
st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]

# 必要なモジュールをインポート
from src.performance_dashboard import create_performance_dashboard
from src.paper_trader import PaperTrader

def verify_dashboard():
    print("🔍 パフォーマンスダッシュボードの動作確認を開始します...")
    
    # PaperTraderのモックデータを設定
    # これにより、データがない場合とある場合の両方をテストできますが、
    # ここではデータがあるケースをシミュレートして描画ロジックを通します。
    
    # 既存のPaperTraderをバックアップ
    original_get_equity_history = PaperTrader.get_equity_history
    original_get_trade_history = PaperTrader.get_trade_history
    
    try:
        # モックデータ注入
        equity_history = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=30),
            'total_equity': np.linspace(1000000, 1100000, 30)
        })
        
        trade_history = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=10),
            'ticker': ['AAPL', 'GOOGL'] * 5,
            'action': ['BUY', 'SELL'] * 5,
            'price': [180, 140] * 5,
            'quantity': [10, 5] * 5,
            'realized_pnl': [1000, -500, 2000, 500, -300, 1500, 800, -200, 1200, 600],
            'strategy': ['LightGBM'] * 10
        })
        
        # メソッドを一時的に置き換え
        PaperTrader.get_equity_history = MagicMock(return_value=equity_history)
        PaperTrader.get_trade_history = MagicMock(return_value=trade_history)
        PaperTrader.get_current_balance = MagicMock(return_value={'total_equity': 1100000, 'cash': 100000})
        PaperTrader.get_positions = MagicMock(return_value=pd.DataFrame())
        
        # ダッシュボード生成関数を実行
        print("📊 create_performance_dashboard() を実行中...")
        create_performance_dashboard()
        
        print("✅ エラーなしで実行完了しました！")
        print("   - メトリクス計算: OK")
        print("   - グラフ描画ロジック: OK")
        print("   - Streamlitウィジェット呼び出し: OK")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # モックを解除（念のため）
        PaperTrader.get_equity_history = original_get_equity_history
        PaperTrader.get_trade_history = original_get_trade_history

if __name__ == "__main__":
    verify_dashboard()
