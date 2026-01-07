<<<<<<< HEAD
"""
日次バックテスト/健全性メトリクスを保存するスクリプト。
paper_trading.db の履歴があればそれを利用し、なければデモデータで埋める。
"""

import datetime
from pathlib import Path

import pandas as pd

from src import demo_data
from src.paper_trader import PaperTrader


def compute_metrics() -> pd.DataFrame:
    pt = PaperTrader()
    try:
        equity_df = pd.DataFrame(pt.get_equity_history(), columns=["date", "total_equity"])
        if equity_df.empty:
            equity_df = demo_data.generate_equity_history(days=90)
        equity_df["date"] = pd.to_datetime(equity_df["date"])
        equity_df["return"] = equity_df["total_equity"].pct_change()
        win_rate = float((equity_df["return"] > 0).mean())
        sharpe = float(
            equity_df["return"].mean() / (equity_df["return"].std() + 1e-6) * (252 ** 0.5)
        ) if not equity_df["return"].dropna().empty else 0.0
        today = datetime.date.today()
        return pd.DataFrame([{"date": today, "win_rate": win_rate, "sharpe": sharpe}])
    finally:
        pt.close()


def main():
    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "backtest_history.csv"

    today_metrics = compute_metrics()

    if out_path.exists():
        try:
            hist = pd.read_csv(out_path)
            hist = pd.concat([hist, today_metrics], ignore_index=True)
            hist = hist.drop_duplicates(subset=["date"], keep="last")
        except Exception:
            hist = today_metrics
    else:
        hist = today_metrics

    hist.to_csv(out_path, index=False)
    print(f"Saved backtest metrics to {out_path} ({len(hist)} rows)")


if __name__ == "__main__":
    main()
=======
import pandas as pd
import numpy as np
from src.paper_trader import PaperTrader

def compute_metrics():
    """
    Compute daily metrics for the trading system.
    Returns a DataFrame with columns: win_rate, sharpe, total_equity
    """
    pt = PaperTrader()
    try:
        history = pt.get_trade_history()
        equity_history = pt.get_equity_history()
        
        if not equity_history:
            return pd.DataFrame()
            
        df_equity = pd.DataFrame(equity_history, columns=["date", "total_equity"])
        df_equity["date"] = pd.to_datetime(df_equity["date"])
        df_equity.set_index("date", inplace=True)
        
        # Calculate returns
        df_equity["returns"] = df_equity["total_equity"].pct_change()
        
        # Win rate from history
        if not history.empty and "realized_pnl" in history.columns:
            wins = (history["realized_pnl"] > 0).sum()
            total = len(history)
            win_rate = wins / total if total > 0 else 0.5
        else:
            win_rate = 0.5
            
        # Sharpe ratio
        returns = df_equity["returns"].dropna()
        if len(returns) > 1:
            sharpe = (returns.mean() / (returns.std() + 1e-6)) * np.sqrt(252)
        else:
            sharpe = 0.0
            
        # Create result row
        result = pd.DataFrame({
            "win_rate": [win_rate],
            "sharpe": [sharpe],
            "total_equity": [df_equity["total_equity"].iloc[-1] if not df_equity.empty else 0]
        }, index=[df_equity.index[-1] if not df_equity.empty else pd.Timestamp.now()])
        
        return result
    except Exception:
        return pd.DataFrame()
    finally:
        pt.close()
>>>>>>> 9ead59c0c8153a0969ef2e94b492063a605db31f
