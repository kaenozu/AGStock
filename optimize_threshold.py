"""
購入閾値の最適化シミュレーション
過去データを用いて、最適な「購入判定ライン（予測上昇率）」を調査します。
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.prediction_backtester import PredictionBacktester


def optimize_threshold():
    # 調査対象銘柄（時間短縮のため1銘柄に絞る）
    tickers = [
        "8308.T",  # りそな (銀行)
    ]

    # 期間設定 (過去3ヶ月)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    print(f"🔍 最適化シミュレーション開始 ({start_date} ~ {end_date})")
    print("-" * 60)

    backtester = PredictionBacktester()
    all_predictions = []

    # 1. 全銘柄の予測データを収集
    for ticker in tickers:
        print(f"📥 データ収集中: {ticker}...")
        result = backtester.run_backtest(ticker=ticker, start_date=start_date, end_date=end_date, prediction_days=5)

        if "error" not in result:
            all_predictions.extend(result["predictions"])
        else:
            print(f"  ❌ エラー: {result['error']}")

    if not all_predictions:
        print("❌ 有効なデータが集まりませんでした")
        return

    print(f"\n📊 データ収集完了: 全{len(all_predictions)}サンプル")

    # 予測値の分布を確認
    pred_values = [p["predicted_change_pct"] for p in all_predictions]
    if pred_values:
        print(
            f"予測値の統計: 最大={max(pred_values):.2f}%, 最小={min(pred_values):.2f}%, 平均={np.mean(pred_values):.2f}%"
        )

    print("-" * 60)

    # 2. 閾値ごとのパフォーマンスを計算
    # マイナスの閾値も含めて調査
    thresholds = [-2.0, -1.0, 0.0, 0.5, 1.0, 1.5, 2.0]

    print(f"{'閾値':<10} | {'取引回数':<10} | {'勝率':<10} | {'平均利益':<10} | {'期待値':<10}")
    print("-" * 60)

    best_threshold = 2.0
    best_score = -float("inf")

    for threshold in thresholds:
        # この閾値を超えた場合のみエントリー
        trades = [p for p in all_predictions if p["predicted_change_pct"] >= threshold]

        count = len(trades)
        if count == 0:
            print(f"+{threshold:.1f}%     | 0          | -          | -          | -")
            continue

        # 勝率 (実際のリターンがプラスだった割合)
        wins = [t for t in trades if t["actual_change_pct"] > 0]
        win_rate = len(wins) / count * 100

        # 平均利益 (実際のリターンの平均)
        avg_return = np.mean([t["actual_change_pct"] for t in trades])

        # 期待値 (勝率 * 平均利益... 簡易版)
        # ここでは単純に「合計リターン」をスコアとする
        total_return = sum([t["actual_change_pct"] for t in trades])

        print(
            f"+{threshold:.1f}%     | {count:<10} | {win_rate:.1f}%     | {avg_return:+.2f}%     | {total_return:+.1f}%"
        )

        # 最適な閾値を判定 (取引回数が5回以上かつ合計リターンが最大)
        if count >= 5 and total_return > best_score:
            best_score = total_return
            best_threshold = threshold

    print("-" * 60)
    print(f"🏆 推奨閾値: +{best_threshold:.1f}%")


if __name__ == "__main__":
    optimize_threshold()
