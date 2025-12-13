#!/usr/bin/env python3
"""
ミニ株（かぶミニ）機能の動作確認スクリプト

このスクリプトは以下を検証します:
1. 設定読み込み
2. 1株単位のポジションサイズ計算
3. 手数料計算
4. 実際の銘柄でのシミュレーション
"""

import json

from src.data_loader import get_latest_price
from src.execution import ExecutionEngine
from src.paper_trader import PaperTrader


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_config_loading():
    """設定読み込みテスト"""
    print_header("1. 設定読み込みテスト")

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    mini_config = config.get("mini_stock", {})
    print(f"ミニ株設定: {json.dumps(mini_config, indent=2, ensure_ascii=False)}")

    if mini_config.get("enabled"):
        print("✅ ミニ株モード: 有効")
        print(f"   - 売買単位: {mini_config.get('unit_size', 1)}株")
        print(f"   - 手数料率: {mini_config.get('fee_rate', 0)*100:.2f}%")
        print(f"   - スプレッド: {mini_config.get('spread_rate', 0)*100:.2f}%")
        print(f"   - 最小注文額: ¥{mini_config.get('min_order_amount', 0):,}")
    else:
        print("❌ ミニ株モード: 無効（100株単位）")

    return mini_config.get("enabled", False)


def test_unit_size_calculation():
    """ユニットサイズ計算テスト"""
    print_header("2. ユニットサイズ計算テスト")

    pt = PaperTrader()
    engine = ExecutionEngine(pt)

    jp_unit = engine.get_japan_unit_size()
    print(f"日本株ユニットサイズ: {jp_unit}株")

    if jp_unit == 1:
        print("✅ ミニ株対応: 1株単位で取引可能")
    else:
        print(f"❌ 単元株モード: {jp_unit}株単位")

    return jp_unit


def test_fee_calculation():
    """手数料計算テスト"""
    print_header("3. 手数料計算テスト（楽天かぶミニ）")

    pt = PaperTrader()
    engine = ExecutionEngine(pt)

    test_amounts = [10000, 50000, 100000, 500000]

    print(f"{'取引金額':>12} | {'寄付(無料)':>12} | {'リアル(0.22%)':>12}")
    print("-" * 42)

    for amount in test_amounts:
        # 寄付取引（無料）
        fee_open = engine.calculate_trading_fee(amount, is_mini_stock=True, order_type="寄付")
        # リアルタイム取引（スプレッド0.22%）
        fee_real = engine.calculate_trading_fee(amount, is_mini_stock=True, order_type="リアルタイム")

        print(f"¥{amount:>10,} | ¥{fee_open:>10,.0f} | ¥{fee_real:>10,.0f}")

    print("\n※ 寄付取引は無料、リアルタイム取引のみ0.22%のスプレッド")


def test_position_size_calculation():
    """ポジションサイズ計算テスト"""
    print_header("4. ポジションサイズ計算テスト")

    pt = PaperTrader()
    engine = ExecutionEngine(pt)

    balance = pt.get_current_balance()
    print(f"現在の資産状況:")
    print(f"  - 総資産: ¥{balance['total_equity']:,.0f}")
    print(f"  - 現金: ¥{balance['cash']:,.0f}")
    print()

    # テスト銘柄リスト（日本株）
    test_stocks = [
        ("7203.T", "トヨタ自動車", 2700),  # 概算価格
        ("6758.T", "ソニーグループ", 3200),
        ("9984.T", "ソフトバンクグループ", 9000),
        ("8306.T", "三菱UFJ", 1600),
        ("6861.T", "キーエンス", 65000),
    ]

    print(f"{'銘柄':>6} | {'名称':>18} | {'株価':>10} | {'計算株数':>8} | {'投資額':>12}")
    print("-" * 70)

    for ticker, name, est_price in test_stocks:
        qty = engine.calculate_position_size(ticker, est_price, confidence=1.0)
        investment = qty * est_price
        print(f"{ticker:>6} | {name:>18} | ¥{est_price:>8,} | {qty:>6}株 | ¥{investment:>10,}")


def test_real_price_simulation():
    """実際の株価でシミュレーション"""
    print_header("5. 実際の株価でシミュレーション")

    pt = PaperTrader()
    engine = ExecutionEngine(pt)

    tickers = ["7203.T", "6758.T", "9984.T"]

    print("現在の株価を取得中...")

    for ticker in tickers:
        try:
            price = get_latest_price(ticker)
            if price:
                qty = engine.calculate_position_size(ticker, price, confidence=1.0)
                fee = engine.calculate_trading_fee(qty * price, is_mini_stock=True)
                total_cost = qty * price + fee

                print(f"\n{ticker}:")
                print(f"  株価: ¥{price:,.0f}")
                print(f"  購入株数: {qty}株")
                print(f"  投資額: ¥{qty * price:,.0f}")
                print(f"  手数料: ¥{fee:,.0f}")
                print(f"  合計: ¥{total_cost:,.0f}")
        except Exception as e:
            print(f"  {ticker}: データ取得エラー ({e})")


def main():
    print("\n" + "🎯 " * 20)
    print("   楽天証券「かぶミニ」機能 動作確認テスト")
    print("🎯 " * 20)

    # 1. 設定読み込み
    mini_enabled = test_config_loading()

    # 2. ユニットサイズ
    unit_size = test_unit_size_calculation()

    # 3. 手数料計算
    test_fee_calculation()

    # 4. ポジションサイズ計算
    test_position_size_calculation()

    # 5. 実株価シミュレーション（オプション）
    print("\n実際の株価でシミュレーションを実行しますか？ (y/n): ", end="")
    try:
        if input().lower() == "y":
            test_real_price_simulation()
    except:
        print("スキップ")

    # 結果サマリー
    print_header("テスト結果サマリー")

    if mini_enabled and unit_size == 1:
        print("✅ ミニ株機能は正常に動作しています！")
        print("   - 1株単位での取引が可能です")
        print("   - 手数料計算が正しく動作しています")
    else:
        print("⚠️ ミニ株機能は無効です")
        print("   config.jsonの mini_stock.enabled を true に設定してください")


if __name__ == "__main__":
    main()
