import pandas as pd
import pytest

from src.strategies.lightgbm_strategy import LightGBMStrategy


def _evaluate_signals(signals: pd.Series, actual: pd.Series) -> tuple[float, float]:
    actionable = signals != 0
    if actionable.sum() == 0:
        return 0.0, 0.0

    predicted_direction = signals[actionable].replace({-1: 0}).astype(int).to_numpy()
    aligned_actual = actual[actionable].to_numpy()
    accuracy = (predicted_direction == aligned_actual).mean()
    coverage = actionable.mean()
    return accuracy, coverage


def test_calibrate_thresholds_increase_coverage_and_accuracy():
    strategy = LightGBMStrategy()

    # 予測確率は上昇寄りだが、デフォルト閾値では多くが中立扱いになるケースを再現
    probs = pd.Series([0.62, 0.58, 0.57, 0.56, 0.45, 0.44, 0.43, 0.42, 0.41, 0.40])
    actual = pd.Series([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])

    tuned_upper, tuned_lower = strategy._calibrate_thresholds(probs, actual)

    tuned_signals = strategy._generate_signals_from_probs(probs, tuned_upper, tuned_lower)
    default_signals = strategy._generate_signals_from_probs(probs, 0.60, 0.40)

    tuned_accuracy, tuned_coverage = _evaluate_signals(tuned_signals, actual)
    default_accuracy, default_coverage = _evaluate_signals(default_signals, actual)

    # 精度を下げずに、より多くの予測を有効化できることを確認
    assert tuned_accuracy >= default_accuracy
    assert tuned_coverage > default_coverage

    # 校正後の閾値がデータ分布に合わせて緩和されることを確認
    assert tuned_upper < 0.60
    assert tuned_lower > 0.40
