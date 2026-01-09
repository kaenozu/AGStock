import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.backtester import Backtester
from src.cache_config import install_cache
from src.constants import ALL_STOCKS
from src.data_loader import fetch_stock_data
from src.strategies import (BollingerBandsStrategy, CombinedStrategy,
                            LightGBMStrategy, MLStrategy, RSIStrategy)


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Calculate annualized Sharpe Ratio."""
    if returns.std() == 0:
        return 0.0
    excess_returns = returns - risk_free_rate / 252
    return np.sqrt(252) * excess_returns.mean() / returns.std()


def calculate_win_rate(trades: pd.DataFrame) -> float:
    """Calculate win rate from trade history."""
    if trades.empty:
        return 0.0
    winning_trades = trades[trades["pnl"] > 0]
    return len(winning_trades) / len(trades)


def run_strategy_backtest(ticker: str, df: pd.DataFrame, strategy, initial_capital: float = 1000000):
    """Run backtest for a single ticker and strategy."""
    bt = Backtester(initial_capital=initial_capital, position_size=1.0)
    result = bt.run(df, strategy)
    return result


def generate_backtest_report():
    """Generate comprehensive backtest report for all strategies."""
    print("=== Backtest Report Generator ===")
    print(f"Started at: {datetime.datetime.now()}")

    # Setup
    install_cache()

    # Test tickers (use subset for speed)
    test_tickers = ALL_STOCKS[:20]  # Sample 20 from global universe (JP, US, EU mix)

    # Strategies to compare
    strategies = {
        "RSI": RSIStrategy(),
        "Bollinger": BollingerBandsStrategy(),
        "Combined": CombinedStrategy(),
        "ML (RF)": MLStrategy(),
        "LightGBM": LightGBMStrategy(),
    }

    print(f"\nFetching data for {len(test_tickers)} tickers...")
    data_map = fetch_stock_data(test_tickers, period="2y")

    # Store results
    results = {name: [] for name in strategies.keys()}

    print("\nRunning backtests...")
    for ticker in test_tickers:
        df = data_map.get(ticker)
        if df is None or df.empty:
            continue

        print(f"  Testing {ticker}...")
        for name, strategy in strategies.items():
            try:
                result = run_strategy_backtest(ticker, df, strategy)
                if result:
                    results[name].append(
                        {
                            "ticker": ticker,
                            "total_return": result["total_return"],
                            "sharpe_ratio": result["sharpe_ratio"],
                            "max_drawdown": result["max_drawdown"],
                            "num_trades": result["num_trades"],
                        }
                    )
            except Exception as e:
                print(f"    Error with {name} on {ticker}: {e}")

    # Aggregate results
    print("\n=== Performance Summary ===")
    summary = {}

    for name, res_list in results.items():
        if not res_list:
            continue

        df_res = pd.DataFrame(res_list)
        summary[name] = {
            "Avg Return": df_res["total_return"].mean(),
            "Median Return": df_res["total_return"].median(),
            "Avg Sharpe": df_res["sharpe_ratio"].mean(),
            "Avg Max DD": df_res["max_drawdown"].mean(),
            "Win Rate": (df_res["total_return"] > 0).sum() / len(df_res),
            "Total Trades": df_res["num_trades"].sum(),
        }

    summary_df = pd.DataFrame(summary).T
    print(summary_df.to_string())

    # Save to CSV
    summary_df.to_csv("backtest_summary.csv")
    print("\n✓ Saved: backtest_summary.csv")

    # Create visualizations
    print("\nGenerating visualizations...")

    # 1. Strategy Comparison Chart
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=("Average Return", "Sharpe Ratio", "Max Drawdown", "Win Rate"),
        specs=[[{"type": "bar"}, {"type": "bar"}], [{"type": "bar"}, {"type": "bar"}]],
    )

    strategies_list = list(summary.keys())

    fig.add_trace(
        go.Bar(
            x=strategies_list,
            y=[summary[s]["Avg Return"] for s in strategies_list],
            name="Avg Return",
            marker_color="lightblue",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=strategies_list,
            y=[summary[s]["Avg Sharpe"] for s in strategies_list],
            name="Sharpe Ratio",
            marker_color="lightgreen",
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Bar(
            x=strategies_list,
            y=[summary[s]["Avg Max DD"] for s in strategies_list],
            name="Max Drawdown",
            marker_color="salmon",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=strategies_list, y=[summary[s]["Win Rate"] for s in strategies_list], name="Win Rate", marker_color="gold"
        ),
        row=2,
        col=2,
    )

    fig.update_layout(title_text="Strategy Performance Comparison", showlegend=False, height=800)

    fig.write_html("backtest_comparison.html")
    print("✓ Saved: backtest_comparison.html")

    # Generate PDF Report
    try:
        generate_pdf_report(summary_df)
        print("✓ Saved: backtest_report.pdf")
    except Exception as e:
        print(f"⚠ PDF generation failed: {e}")

    print("\n=== Report Complete ===")
    return summary_df


def generate_pdf_report(summary_df: pd.DataFrame):
    """Generate a PDF report using ReportLab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                    Table, TableStyle)

    doc = SimpleDocTemplate("backtest_report.pdf", pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("AGStock Backtest Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated: {datetime.datetime.now()}", styles["Normal"]))
    elements.append(Spacer(1, 24))

    # Table
    # Convert DataFrame to list of lists
    data = [summary_df.columns.to_list()] + summary_df.values.tolist()
    # Round numbers for display
    formatted_data = [data[0]]
    for row in data[1:]:
        formatted_row = []
        for item in row:
            if isinstance(item, float):
                formatted_row.append(f"{item:.4f}")
            else:
                formatted_row.append(str(item))
        formatted_data.append(formatted_row)

    # Add Index (Strategy Name)
    formatted_data[0].insert(0, "Strategy")
    for i, idx in enumerate(summary_df.index):
        formatted_data[i + 1].insert(0, idx)

    t = Table(formatted_data)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    elements.append(t)

    doc.build(elements)


if __name__ == "__main__":
    generate_backtest_report()
