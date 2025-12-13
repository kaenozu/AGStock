"""
KellyCriterionのテスト
"""

import numpy as np
import pandas as pd
import pytest

from src.kelly_criterion import KellyCriterion


@pytest.fixture
def kelly_full():
    """フルケリー（half_kelly=False）のインスタンス"""
    return KellyCriterion(half_kelly=False, max_position_size=0.2)


@pytest.fixture
def kelly_half():
    """ハーフケリー（half_kelly=True）のインスタンス"""
    return KellyCriterion(half_kelly=True, max_position_size=0.2)


def test_init():
    """初期化のテスト"""
    kelly = KellyCriterion(half_kelly=True, max_position_size=0.3)
    assert kelly.half_kelly is True
    assert kelly.max_position_size == 0.3


def test_calculate_size_positive_edge(kelly_full):
    """ポジションサイズ計算：優位性あり"""
    # 勝率60%, 勝敗比2.0の場合
    # Kelly = (0.6 * 2 - 0.4) / 2 = 0.4
    # しかし max_position_size=0.2 でキャップされる
    win_rate = 0.6
    win_loss_ratio = 2.0

    size = kelly_full.calculate_size(win_rate, win_loss_ratio)

    # キャップされて0.2になる
    assert size == 0.2


def test_calculate_size_half_kelly(kelly_half):
    """ポジションサイズ計算：ハーフケリー"""
    # 勝率60%, 勝敗比2.0の場合
    # Full Kelly = 0.4, Half Kelly = 0.2
    win_rate = 0.6
    win_loss_ratio = 2.0

    size = kelly_half.calculate_size(win_rate, win_loss_ratio)

    expected = ((0.6 * 2.0 - 0.4) / 2.0) * 0.5
    assert abs(size - expected) < 0.001


def test_calculate_size_negative_edge(kelly_full):
    """ポジションサイズ計算：優位性なし（負のエッジ）"""
    # 勝率40%, 勝敗比1.0の場合
    # Kelly = (0.4 * 1 - 0.6) / 1 = -0.2 -> 0.0
    win_rate = 0.4
    win_loss_ratio = 1.0

    size = kelly_full.calculate_size(win_rate, win_loss_ratio)

    assert size == 0.0


def test_calculate_size_zero_win_loss_ratio(kelly_full):
    """ポジションサイズ計算：勝敗比が0"""
    win_rate = 0.6
    win_loss_ratio = 0.0

    size = kelly_full.calculate_size(win_rate, win_loss_ratio)

    assert size == 0.0


def test_calculate_size_negative_win_loss_ratio(kelly_full):
    """ポジションサイズ計算：勝敗比が負"""
    win_rate = 0.6
    win_loss_ratio = -1.0

    size = kelly_full.calculate_size(win_rate, win_loss_ratio)

    assert size == 0.0


def test_calculate_size_max_cap(kelly_full):
    """ポジションサイズ計算：最大サイズでキャップ"""
    # 非常に高い優位性（勝率80%, 勝敗比5.0）
    # Kelly = (0.8 * 5 - 0.2) / 5 = 0.76
    # しかし max_position_size=0.2 でキャップされる
    win_rate = 0.8
    win_loss_ratio = 5.0

    size = kelly_full.calculate_size(win_rate, win_loss_ratio)

    assert size == 0.2


def test_calculate_from_history_positive_returns():
    """履歴からの計算：利益が出ている場合"""
    kelly = KellyCriterion(half_kelly=False, max_position_size=0.2)

    # 勝ち6回、負け4回
    returns = pd.Series([0.05, 0.03, -0.02, 0.04, -0.01, 0.06, -0.015, 0.02, 0.03, -0.025])

    size = kelly.calculate_from_history(returns)

    # サイズが計算されることを確認
    assert size > 0
    assert size <= 0.2


def test_calculate_from_history_all_wins():
    """履歴からの計算：全て勝ち"""
    kelly = KellyCriterion(half_kelly=False, max_position_size=0.2)

    returns = pd.Series([0.05, 0.03, 0.04, 0.06, 0.02])

    size = kelly.calculate_from_history(returns)

    # 負けがないので最大サイズ
    assert size == 0.2


def test_calculate_from_history_all_losses():
    """履歴からの計算：全て負け"""
    kelly = KellyCriterion(half_kelly=False, max_position_size=0.2)

    returns = pd.Series([-0.02, -0.03, -0.01, -0.025, -0.015])

    size = kelly.calculate_from_history(returns)

    # 勝ちがないので0
    assert size == 0.0


def test_calculate_from_history_empty_series():
    """履歴からの計算：空のシリーズ"""
    kelly = KellyCriterion(half_kelly=False, max_position_size=0.2)

    returns = pd.Series([])

    size = kelly.calculate_from_history(returns)

    assert size == 0.0


def test_calculate_from_history_none():
    """履歴からの計算：None"""
    kelly = KellyCriterion(half_kelly=False, max_position_size=0.2)

    size = kelly.calculate_from_history(None)

    assert size == 0.0


def test_calculate_from_history_zero_avg_loss():
    """履歴からの計算：平均損失が0（極端なケース）"""
    kelly = KellyCriterion(half_kelly=False, max_position_size=0.2)

    # 負けがあるが平均損失が0になるケース（実際にはあり得ないが）
    # 実装上、avg_lossは abs(losses.mean()) なので0にはならないが、
    # 念のため損失が非常に小さい場合をテスト
    returns = pd.Series([0.05, 0.03, -0.0001, 0.04, 0.06])

    size = kelly.calculate_from_history(returns)

    # 損失が非常に小さいので、サイズは大きくなる（キャップされる）
    assert size > 0


def test_calculate_from_history_realistic_scenario():
    """履歴からの計算：現実的なシナリオ"""
    kelly = KellyCriterion(half_kelly=True, max_position_size=0.2)

    # 勝率55%, 平均勝ち3%, 平均負け2%
    np.random.seed(42)
    wins = np.random.uniform(0.01, 0.05, 55)
    losses = np.random.uniform(-0.04, -0.01, 45)
    returns = pd.Series(np.concatenate([wins, losses]))

    size = kelly.calculate_from_history(returns)

    # ハーフケリーなので控えめなサイズ
    assert 0 < size < 0.2


def test_calculate_from_history_breakeven():
    """履歴からの計算：損益分岐点付近"""
    kelly = KellyCriterion(half_kelly=False, max_position_size=0.2)

    # 勝率50%, 勝敗比1.0（損益分岐点）
    returns = pd.Series([0.02, -0.02, 0.03, -0.03, 0.01, -0.01])

    size = kelly.calculate_from_history(returns)

    # 優位性がないので0に近い
    assert size >= 0
    assert size < 0.05


def test_different_max_position_sizes():
    """異なる最大ポジションサイズのテスト"""
    kelly_small = KellyCriterion(half_kelly=False, max_position_size=0.1)
    kelly_large = KellyCriterion(half_kelly=False, max_position_size=0.5)

    # 非常に高い優位性
    win_rate = 0.8
    win_loss_ratio = 5.0

    size_small = kelly_small.calculate_size(win_rate, win_loss_ratio)
    size_large = kelly_large.calculate_size(win_rate, win_loss_ratio)

    # 異なる上限でキャップされる
    assert size_small == 0.1
    assert size_large == 0.5
