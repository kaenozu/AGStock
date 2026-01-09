"""
Phase 29-1: 特徴量エンジニアリング検証スクリプト

新しく追加された特徴量の動作確認とバックテストを実行します。
"""

import logging

import numpy as np
import pandas as pd

from src.advanced_features import generate_phase29_features
from src.backtesting import run_backtest
from src.data_loader import fetch_stock_data
from src.strategies import LightGBMStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_phase29_features():
    """Phase 29-1の特徴量生成をテスト"""
    logger.info("=" * 60)
    logger.info("Phase 29-1: 特徴量エンジニアリング検証")
    logger.info("=" * 60)

    # テスト用データ取得
    ticker = "AAPL"
    logger.info(f"\nテスト銘柄: {ticker}")
    logger.info("データ取得中...")

    df = fetch_stock_data(ticker, period="2y")

    if df is None or len(df) < 100:
        logger.error("データ取得失敗")
        return False

    logger.info(f"取得データ: {len(df)}行")
    logger.info(f"元のカラム数: {len(df.columns)}")

    # Phase 29-1の特徴量を生成
    logger.info("\nPhase 29-1の特徴量を生成中...")
    df_features = generate_phase29_features(df)

    logger.info(f"特徴量追加後のカラム数: {len(df_features.columns)}")
    logger.info(f"追加された特徴量数: {len(df_features.columns) - len(df.columns)}")

    # 新しい特徴量の確認
    logger.info("\n追加された主要特徴量:")
    new_features = [
        "Historical_Volatility",
        "Volatility_Regime",
        "Volatility_Change",
        "ROC_5",
        "ROC_10",
        "ROC_20",
        "Stoch_K",
        "Stoch_D",
        "Williams_R",
        "Ultimate_Osc",
        "Close_lag_1",
        "Close_lag_5",
        "Close_lag_10",
        "Close_std_5",
        "Close_skew_10",
        "Close_kurt_20",
    ]

    for feat in new_features:
        if feat in df_features.columns:
            logger.info(f"  ✓ {feat}")
        else:
            logger.warning(f"  ✗ {feat} (見つかりません)")

    # 統計情報
    logger.info("\n特徴量の統計情報:")
    logger.info(f"  欠損値: {df_features.isna().sum().sum()}")
    logger.info(f"  無限大: {np.isinf(df_features.select_dtypes(include=[np.number])).sum().sum()}")

    # ボラティリティレジームの分布
    if "Volatility_Regime" in df_features.columns:
        regime_counts = df_features["Volatility_Regime"].value_counts()
        logger.info("\nボラティリティレジーム分布:")
        logger.info(f"  低ボラティリティ (0): {regime_counts.get(0, 0)}日")
        logger.info(f"  中ボラティリティ (1): {regime_counts.get(1, 0)}日")
        logger.info(f"  高ボラティリティ (2): {regime_counts.get(2, 0)}日")

    return True


def test_lightgbm_with_new_features():
    """新しい特徴量を使ったLightGBMのバックテスト"""
    logger.info("\n" + "=" * 60)
    logger.info("LightGBMモデル with Phase 29-1特徴量のバックテスト")
    logger.info("=" * 60)

    ticker = "AAPL"
    logger.info(f"\nテスト銘柄: {ticker}")

    # データ取得
    df = fetch_stock_data(ticker, period="2y")

    if df is None or len(df) < 100:
        logger.error("データ取得失敗")
        return False

    # LightGBM戦略でバックテスト
    logger.info("\nLightGBM戦略を実行中...")
    strategy = LightGBMStrategy()

    try:
        results = run_backtest(df, strategy, initial_capital=1000000)

        logger.info("\nバックテスト結果:")
        logger.info(f"  総リターン: {results['total_return']:.2%}")
        logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        logger.info(f"  最大ドローダウン: {results['max_drawdown']:.2%}")
        logger.info(f"  勝率: {results['win_rate']:.2%}")
        logger.info(f"  総取引数: {results['total_trades']}")

        # 成功基準のチェック
        logger.info("\n成功基準チェック:")
        checks = {
            "Sharpe Ratio >= 1.0": results["sharpe_ratio"] >= 1.0,
            "勝率 >= 50%": results["win_rate"] >= 50,
            "最大ドローダウン >= -30%": results["max_drawdown"] >= -0.30,
        }

        for criterion, passed in checks.items():
            status = "✓" if passed else "✗"
            logger.info(f"  {status} {criterion}")

        return all(checks.values())

    except Exception as e:
        logger.error(f"バックテストエラー: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """メイン実行関数"""
    logger.info("Phase 29-1: 特徴量エンジニアリング検証スクリプト")
    logger.info("開始時刻: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("")

    # テスト1: 特徴量生成
    test1_passed = test_phase29_features()

    # テスト2: LightGBMバックテスト
    test2_passed = test_lightgbm_with_new_features()

    # 総合結果
    logger.info("\n" + "=" * 60)
    logger.info("検証結果サマリー")
    logger.info("=" * 60)
    logger.info(f"特徴量生成テスト: {'✓ PASS' if test1_passed else '✗ FAIL'}")
    logger.info(f"LightGBMバックテスト: {'✓ PASS' if test2_passed else '✗ FAIL'}")

    if test1_passed and test2_passed:
        logger.info("\n🎉 Phase 29-1の検証が完了しました！")
        logger.info("すべてのテストに合格しました。")
    else:
        logger.warning("\n⚠️ 一部のテストが失敗しました。")
        logger.warning("詳細を確認してください。")

    logger.info("\n終了時刻: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
