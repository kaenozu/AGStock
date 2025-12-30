# """
# 動的アンサンブル最適化モジュール
#     各モデルの過去のパフォーマンスに基づいて、アンサンブルのウェイトを動的に調整します。
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


# """
#
#
class DynamicEnsemble:
    (self,)
    #     """
    #         learning_rate: float = 0.1,
    #         window_size: int = 20,
    #         state_file: str = "ensemble_state.json",
    #     ):
        pass
    #         """
    self.learning_rate = learning_rate
    self.window_size = window_size
    self.weights = {s.name: 1.0 / len(strategies) for s in strategies}
    self.history = []  # [{'date': date, 'predictions': {name: pred}, 'actual': return}]
    self.performance = {s.name: 0.0 for s in strategies}
    # 永続化ファイルのパス
    self.state_file = state_file
    self.load_state()
    #     """
    #         実際のリターンに基づいてウェイトを更新
    #             Args:
        pass
    #                 ticker: 銘柄コード
    #             date: 日付
    #         # 履歴に追加
    #         record = {
    #             "date": date.strftime("%Y-%m-%d"),
    #             "ticker": ticker,
    #             "predictions": predictions,
    #             "actual": actual_return,
    #         }
    #         self.history.append(record)
    # # 古い履歴を削除
    #         if len(self.history) > 1000:
        pass
    #             self.history.pop(0)
    # # パフォーマンス評価とウェイト更新
    #         self._recalculate_weights()
    #         self.save_state()
    #     """
    #     """過去の履歴からウェイトを再計算"""
    if not self.history:
        pass
    # 直近の履歴を取得
    recent_history = self.history[-self.window_size :]
    # 正解ラベル（プラスなら1、マイナスなら-1）
    # 予測が正解と同じ方向ならスコア加算
    # 逆方向なら減点
    # スコアを正規化してウェイトに変換（Softmax的なアプローチ）
    total_score = sum(max(0, s) for s in scores.values())
    # EMAでウェイトを更新
    # スコアが全て0以下の場合は均等割り
    各モデルの予測を統合して最終予測を返す
    predictions = {}
    # 各戦略の予測を取得
    # スコア計算
    # 加重平均
    try:
        state = {
            "weights": self.weights,
            "history": self.history[-100:],
        }  # 最新100件のみ保存
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save ensemble state: {e}")
    if os.path.exists(self.state_file):
        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
                self.weights = state.get("weights", self.weights)
                self.history = state.get("history", [])
        except Exception as e:
            logger.error(f"Failed to load ensemble state: {e}")
