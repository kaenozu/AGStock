"""
Phase 55 検証スクリプト
Neuro-Evolutionの速度と学習効果を確認
"""

import logging
import os
import sys
import time

sys.path.insert(0, os.getcwd())

# ログ設定
logging.basicConfig(level=logging.INFO)
logging.getLogger("src.data_loader").setLevel(logging.ERROR)


def test_evolution_speed_and_learning():
    print("\n" + "=" * 60)
    print("🧬 Neuro-Evolution 実験 (Speed & Learning)")
    print("=" * 60)

    from src.data_loader import fetch_stock_data
    from src.neuro_evolution import get_neuro_evolution_engine

    # 1. データ準備
    print("1. データ準備中...")
    data_map = fetch_stock_data(["^N225"], period="5y")  # 5年分
    df = data_map["^N225"]
    print(f"   データ数: {len(df)}行")

    if len(df) < 100:
        print("❌ データ不足")
        return False

    engine = get_neuro_evolution_engine()

    # 2. 初期化
    print("\n2. 個体群初期化")
    engine.initialize_population()

    # 3. 5世代進化実験
    print("\n3. 5世代進化スタート (Speed Check)")
    start_time = time.time()

    history = engine.run_evolution(df, generations=5)

    elapsed = time.time() - start_time
    avg_time = elapsed / 5

    print(f"\n⏱️ 完了: {elapsed:.2f}秒 (平均 {avg_time:.3f}秒/世代)")

    # 4. 結果確認
    print("\n4. 学習推移")
    first_score = history[0]["best_score"]
    last_score = history[-1]["best_score"]

    for i, res in enumerate(history):
        print(f"   Gen {res['generation']}: Score {res['best_score']:.4f} | Gene: {res['best_gene']}")

    print(f"\n📈 スコア改善: {first_score:.4f} -> {last_score:.4f}")

    # 判定
    is_fast_enough = avg_time < 2.0  # 2秒以下なら十分高速
    is_improving = last_score >= first_score  # 少なくとも悪化はしていないこと

    if is_fast_enough and is_improving:
        print("\n✅ Verification Passed: High speed & Stable evolution")
        return True
    else:
        print("\n⚠️ Verification Warning")
        if not is_fast_enough:
            print("   - Too slow")
        if not is_improving:
            print("   - Not improving")
        return False


if __name__ == "__main__":
    test_evolution_speed_and_learning()
