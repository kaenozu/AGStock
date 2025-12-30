
import pandas as pd
import numpy as np
from src.paper_trader import PaperTrader
from src.dynamic_risk_manager import DynamicRiskManager
from src.regime_detector import RegimeDetector
from src.data_loader import fetch_stock_data

def check_tp_sl():
    pt = PaperTrader()
    positions = pt.get_positions()
    rd = RegimeDetector()
    rm = DynamicRiskManager(rd)
    
    print("\n=== 利確・損切りライン（詳細分析） ===\n")
    
    if positions.empty:
        print("現在保有している銘柄はありません。")
        return

    for _, row in positions.iterrows():
        ticker = row['ticker'] if 'ticker' in row else row.name
        avg_price = float(row['entry_price'])
        current_price = float(row['current_price'])
        pnl_pct = (current_price - avg_price) / avg_price
        
        # データの取得（余裕をもって3ヶ月分）
        data = fetch_stock_data([ticker], period='3mo')
        df = data.get(ticker)
        
        if df is not None and len(df) >= 20:
            # パラメータの更新（ボラティリティ調整含む）
            params = rm.update_parameters(df)
            regime = params.get('regime', 'NORMAL')
            tp_threshold = params.get('take_profit', 0.10)
            sl_threshold = params.get('stop_loss', 0.05)
        else:
            # データ不足時のデフォルト
            regime = "DATA_INSUFFICIENT"
            tp_threshold = 0.10
            sl_threshold = 0.05
            
        tp_price = avg_price * (1 + tp_threshold)
        sl_price = avg_price * (1 - sl_threshold)
        
        # 5%利益ロックの判定
        lock_active = pnl_pct > 0.05
        lock_price = avg_price * 1.005 if lock_active else avg_price * 1.05
        
        # 固定ターゲット(20%)
        target_profit_20 = avg_price * 1.20
        
        # 現在の逆指値（DBから）
        stop_price_db = float(row.get('stop_price', 0.0))
        
        print(f"■ {ticker}")
        print(f"  保有単価: {avg_price:,.1f}円")
        print(f"  現在価格: {current_price:,.1f}円 (損益: {pnl_pct:+.2%})")
        print(f"  市場状況: {regime}")
        print(f"  --------------------------------------")
        print(f"  【利確判断エリア】")
        print(f"  ・動的利確想定 ({tp_threshold:+.1%}): {tp_price:,.1f}円 (あと {max(0, tp_price - current_price):,.1f}円)")
        print(f"  ・目標達成 (20%): {target_profit_20:,.1f}円")
        print(f"  ")
        print(f"  【撤退・防衛エリア】")
        if lock_active:
            print(f"  ・利益ロック (発動中): {avg_price * 1.005:,.1f}円 (買値付近で確保)")
        else:
            print(f"  ・利益ロック (未発動): {lock_price:,.1f}円 (+5%利益でここに引き上げ)")
        
        print(f"  ・システムの逆指値: {stop_price_db:,.1f}円")
        
        # 乖離の警告
        if stop_price_db > 0 and current_price <= stop_price_db:
             print(f"  ⚠️ ALERT: 現在価格が逆指値を下回っています。次回のスキャンで決済される可能性があります。")
        
        print("")

if __name__ == "__main__":
    check_tp_sl()
