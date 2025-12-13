import logging
import sys
import warnings
from datetime import datetime

import pandas as pd
import yfinance as yf

# 警告を抑制
warnings.filterwarnings("ignore")

# ロガー設定
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# 必要なモジュールをインポート
try:
    from src.strategies import (LightGBMStrategy, MLStrategy, RSIStrategy,
                                SMACrossoverStrategy)
except ImportError:
    # パスが通っていない場合の対策
    sys.path.append(".")
    from src.strategies import (LightGBMStrategy, MLStrategy, RSIStrategy,
                                SMACrossoverStrategy)


def fetch_data(ticker, period="2y"):
    """株価データを取得"""
    try:
        df = yf.download(ticker, period=period, progress=False)
        if df.empty:
            return None

        # MultiIndexカラムのフラット化 (yfinance v0.2.0以降の対応)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        return None


def evaluate_strategy(strategy, df, ticker):
    """戦略を評価する"""
    try:
        # シグナル生成
        signals = strategy.generate_signals(df)

        if signals.empty or signals.sum() == 0:
            return None

        # 評価用データ作成
        eval_df = pd.DataFrame(index=df.index)
        eval_df["Close"] = df["Close"]
        eval_df["Signal"] = signals

        # 翌日のリターン
        eval_df["Next_Return"] = eval_df["Close"].pct_change().shift(-1)

        # 予測の正解判定
        # Signal=1 (Buy) で Next_Return > 0 なら正解
        # Signal=-1 (Sell) で Next_Return < 0 なら正解

        # シグナルが出た日のみ抽出
        trades = eval_df[eval_df["Signal"] != 0].copy()

        if trades.empty:
            return None

        trades["Correct"] = ((trades["Signal"] == 1) & (trades["Next_Return"] > 0)) | (
            (trades["Signal"] == -1) & (trades["Next_Return"] < 0)
        )

        accuracy = trades["Correct"].mean()
        trade_count = len(trades)

        # 累積リターン (簡易計算: シグナル * 翌日リターン)
        trades["Strategy_Return"] = trades["Signal"] * trades["Next_Return"]
        total_return = trades["Strategy_Return"].sum()

        return {
            "strategy": strategy.name,
            "ticker": ticker,
            "accuracy": accuracy,
            "trades": trade_count,
            "total_return": total_return,
        }

    except Exception as e:
        logger.error(f"Error evaluating {strategy.name} for {ticker}: {e}")
        return None


def main():
    print("=" * 60)
    print("🤖 AGStock AI予測精度検証レポート")
    print("=" * 60)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("検証期間: 直近2年間")
    print("-" * 60)

    tickers = {"7203.T": "トヨタ自動車", "6758.T": "ソニーG", "8306.T": "三菱UFJ", "9984.T": "ソフトバンクG"}

    strategies = [
        SMACrossoverStrategy(),
        RSIStrategy(),
        MLStrategy(name="AI (Random Forest)"),
        LightGBMStrategy(lookback_days=365),
    ]

    results = []

    for ticker, name in tickers.items():
        print(f"\n📊 {name} ({ticker}) の分析中...")
        df = fetch_data(ticker)

        if df is None:
            print("  ❌ データ取得失敗")
            continue

        for strategy in strategies:
            print(f"  Running {strategy.name}...", end="\r")
            res = evaluate_strategy(strategy, df, ticker)
            if res:
                results.append(res)
                print(f"  ✅ {strategy.name}: 正解率 {res['accuracy']:.1%} ({res['trades']}回)")
            else:
                print(f"  ⚠️ {strategy.name}: 取引なし/エラー")

    print("\n" + "=" * 60)
    print("🏆 総合ランキング (正解率順)")
    print("=" * 60)

    if not results:
        print("データがありません")
        return

    df_results = pd.DataFrame(results)

    # 戦略ごとの平均正解率
    strategy_stats = (
        df_results.groupby("strategy")
        .agg({"accuracy": "mean", "trades": "sum", "total_return": "mean"})
        .sort_values("accuracy", ascending=False)
    )

    print(f"{'戦略名':<25} | {'平均正解率':<10} | {'総取引数':<8} | {'平均リターン'}")
    print("-" * 65)

    for strategy, row in strategy_stats.iterrows():
        print(f"{strategy:<25} | {row['accuracy']:.1%}      | {int(row['trades']):<8} | {row['total_return']:.2%}")

    print("-" * 65)

    best_strategy = strategy_stats.index[0]
    best_acc = strategy_stats.iloc[0]["accuracy"]

    print("\n💡 結論:")
    print(f"最も精度が高いのは **{best_strategy}** で、平均正解率は **{best_acc:.1%}** です。")

    if best_acc > 0.55:
        print("これは市場平均を有意に上回っており、実運用で利益を出せる可能性が高いです。")
    elif best_acc > 0.5:
        print("市場平均をわずかに上回っていますが、リスク管理が重要です。")
    else:
        print("予測精度は改善の余地があります。他の指標と組み合わせることを推奨します。")


if __name__ == "__main__":
    main()
