#!/usr/bin/env python3
"""
取引状況をリセットしてミニ株のフル検証を行うスクリプト
"""

import sqlite3
import os
import json
from src.paper_trader import PaperTrader
from src.execution import ExecutionEngine
from src.data_loader import get_latest_price


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def reset_paper_trading():
    """ペーパートレードのデータをリセット"""
    print_header("1. 取引データのリセット")
    
    # テスト用に別のDBファイルを使用
    db_path = "paper_trading_test.db"
    
    # 既存テストDBを削除
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"✅ 既存データを削除しました")
        except Exception as e:
            print(f"⚠️ 既存DBの削除に失敗: {e}")
    
    # 初期資本を取得
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    initial_capital = config.get("paper_trading", {}).get("initial_capital", 500000)
    
    # 新しいPaperTraderを作成（テスト用DBパスを指定）
    pt = PaperTrader(db_path=db_path, initial_capital=initial_capital)
    balance = pt.get_current_balance()
    
    print(f"✅ 取引データをリセットしました")
    print(f"   - 初期資本: ¥{initial_capital:,}")
    print(f"   - 現在の現金: ¥{balance['cash']:,}")
    print(f"   - 総資産: ¥{balance['total_equity']:,}")
    
    return pt


def test_mini_stock_trading(pt: PaperTrader):
    """ミニ株取引のテスト"""
    print_header("2. ミニ株取引シミュレーション")
    
    engine = ExecutionEngine(pt)
    
    # ミニ株設定確認
    print(f"ミニ株モード: {'有効' if engine.mini_stock_enabled else '無効'}")
    print(f"売買単位: {engine.get_japan_unit_size()}株")
    print()
    
    # テスト銘柄
    test_stocks = [
        ("7203.T", "トヨタ自動車"),
        ("6758.T", "ソニーグループ"),
        ("8306.T", "三菱UFJ"),
    ]
    
    print("株価を取得中...")
    from src.data_loader import fetch_stock_data
    
    for ticker, name in test_stocks:
        try:
            # 株価データを取得
            data = fetch_stock_data([ticker], period="5d")
            df = data.get(ticker)
            
            if df is not None and not df.empty:
                price = df['Close'].iloc[-1]
                
                # ポジションサイズ計算
                qty = engine.calculate_position_size(ticker, price, confidence=1.0)
                
                if qty > 0:
                    # 実際に買い注文
                    success = pt.execute_trade(ticker, "BUY", qty, price, reason="ミニ株テスト")
                    
                    if success:
                        fee = engine.calculate_trading_fee(qty * price, is_mini_stock=True)
                        print(f"✅ {name}({ticker})")
                        print(f"   株価: ¥{price:,.0f}")
                        print(f"   購入: {qty}株")
                        print(f"   投資額: ¥{qty * price:,.0f}")
                        print(f"   手数料: ¥{fee:,.0f}")
                else:
                    print(f"⚠️ {name}({ticker}): 購入資金不足 (株価: ¥{price:,.0f})")
            else:
                print(f"❌ {name}({ticker}): 株価取得失敗")
        except Exception as e:
            print(f"❌ {name}({ticker}): エラー - {e}")
        print()


def show_final_status(pt: PaperTrader):
    """最終状態を表示"""
    print_header("3. 最終状態")
    
    balance = pt.get_current_balance()
    positions = pt.get_positions()
    
    print(f"資産状況:")
    print(f"  - 現金: ¥{balance['cash']:,.0f}")
    print(f"  - 投資額: ¥{balance['invested_amount']:,.0f}")
    print(f"  - 総資産: ¥{balance['total_equity']:,.0f}")
    print()
    
    if not positions.empty:
        print("保有ポジション:")
        for _, pos in positions.iterrows():
            ticker = pos['ticker']
            qty = pos['quantity']
            entry_price = pos['entry_price']
            current_price = pos.get('current_price', entry_price)
            pnl = (current_price - entry_price) * qty
            pnl_pct = (current_price / entry_price - 1) * 100
            
            print(f"  {ticker}: {qty}株 @ ¥{entry_price:,.0f}")
            print(f"    現在値: ¥{current_price:,.0f} ({pnl_pct:+.2f}%)")
    else:
        print("保有ポジション: なし")


def main():
    print("\n" + "🎯 " * 20)
    print("   ミニ株機能 フル検証テスト")
    print("🎯 " * 20)
    
    # 1. リセット
    pt = reset_paper_trading()
    
    # 2. ミニ株取引テスト
    test_mini_stock_trading(pt)
    
    # 3. 最終状態表示
    show_final_status(pt)
    
    print_header("テスト完了")
    print("✅ ミニ株機能のフル検証が完了しました！")


if __name__ == "__main__":
    main()
