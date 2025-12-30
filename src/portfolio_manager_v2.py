"""
Portfolio Manager V2 - AIポートフォリオ管理
現代ポートフォリオ理論(MPT)に基づく最適化とリバランス
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class PortfolioManagerV2:
    """AIポートフォリオマネージャー"""

    def __init__(self, risk_free_rate: float = 0.01):
        self.risk_free_rate = risk_free_rate

    def optimize_portfolio(
        self, price_data: Dict[str, pd.DataFrame], lookback_days: int = 252
    ) -> Dict[str, float]:
        """
        シャープレシオ最大化によるポートフォリオ最適化

        Args:
            price_data: {ticker: dataframe} の辞書
            lookback_days: 相関計算に使う期間

        Returns:
            {ticker: weight} 最適ウェイト
        """
        # 1. 共通期間のリターンデータフレームを作成
        df_closes = pd.DataFrame()

        for ticker, df in price_data.items():
            if "Close" in df.columns:
                df_closes[ticker] = df["Close"]

        # 直近データに絞る
        df_closes = df_closes.iloc[-lookback_days:]

        # 欠損値がある銘柄は除外（Cryptoと株で休日が違うため重要）
        # 前方埋めしてから、どうしても埋まらない（上場前など）ものを削除
        df_closes = df_closes.fillna(method="ffill").dropna(axis=1)

        if df_closes.empty or len(df_closes.columns) < 2:
            return {
                col: 1.0 if i == 0 else 0.0 for i, col in enumerate(df_closes.columns)
            }

        # 日次リターン
        returns = df_closes.pct_change().dropna()

        # 平均リターンと共分散行列
        mean_returns = returns.mean() * 252  # 年率換算
        cov_matrix = returns.cov() * 252

        num_assets = len(mean_returns)

        # 最適化関数 (シャープレシオの負値を最小化)
        def neg_sharpe_ratio(weights):
            weights = np.array(weights)
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_volatility = np.sqrt(
                np.dot(weights.T, np.dot(cov_matrix, weights))
            )
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_volatility
            return -sharpe

        # 制約条件: ウェイトの合計 = 1
        constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}

        # 境界条件: 各ウェイトは 0.0 ~ 1.0 (空売りなし)
        bounds = tuple((0.0, 1.0) for _ in range(num_assets))

        # 初期値: 均等配分
        init_guess = num_assets * [
            1.0 / num_assets,
        ]

        try:
            result = minimize(
                neg_sharpe_ratio,
                init_guess,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )

            if result.success:
                optimized_weights = {}
                for ticker, weight in zip(mean_returns.index, result.x):
                    # 1%未満は0とする（微小ポジション整理）
                    if weight < 0.01:
                        weight = 0.0
                    optimized_weights[ticker] = float(weight)

                # 正規化（削除した分を再配分）
                total = sum(optimized_weights.values())
                if total > 0:
                    optimized_weights = {
                        k: v / total for k, v in optimized_weights.items()
                    }

                return optimized_weights
            else:
                logger.warning(f"Portfolio optimization failed: {result.message}")
                return {
                    tick: 1.0 / num_assets for tick in mean_returns.index
                }  # 均等配分

        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return {}

    def calculate_rebalance_needs(
        self,
        current_positions: Dict[str, float],
        target_weights: Dict[str, float],
        total_equity: float,
    ) -> Dict[str, str]:
        """
        リバランス指示の生成

        Args:
            current_positions: {ticker: 現在の評価額}
            target_weights: {ticker: 目標ウェイト 0.0~1.0}
            total_equity: 総資産額

        Returns:
            {ticker: "BUY xxx JPY" / "SELL xxx JPY"}
        """
        instructions = {}

        for ticker, target_w in target_weights.items():
            target_amt = total_equity * target_w
            current_amt = current_positions.get(ticker, 0.0)

            diff = target_amt - current_amt

            # しきい値（例えば資産の5%以上ズレたら動く）
            threshold = total_equity * 0.05

            if diff > threshold:
                instructions[ticker] = f"BUY {diff:,.0f} JPY"
            elif diff < -threshold:
                instructions[ticker] = f"SELL {abs(diff):,.0f} JPY"

        return instructions
