"""
予測精度を測定するスクリプト
"""

from datetime import datetime, timedelta

from src.prediction_backtester import PredictionBacktester


def main():
    pb = PredictionBacktester()

    # 過去60日間の検証期間を設定
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    print("=" * 50)
    print("予測精度検証 (7203.T - Toyota)")
    print(f"期間: {start_date} ~ {end_date}")
    print("=" * 50)

    results = pb.run_backtest("7203.T", start_date, end_date, prediction_days=5)

    if "error" in results:
        print(f"エラー: {results['error']}")
        return

    metrics = results.get("metrics", {})

    print(f"予測回数: {metrics.get('total_samples', 0)}")
    print(f"方向精度: {metrics.get('direction_accuracy', 0):.1f}%")
    print(f"勝率 (取引可能予測): {metrics.get('win_rate', 0):.1f}%")
    print(f"MAE: {metrics.get('mae', 0):.2f}%")
    print(f"RMSE: {metrics.get('rmse', 0):.2f}%")
    print(f"95%信頼区間: ±{metrics.get('confidence_interval_95', 0):.2f}%")


if __name__ == "__main__":
    main()
