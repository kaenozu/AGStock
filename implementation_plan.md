# Implementation Plan - Future Enhancements (Phase 4 & 5)

This plan outlines the next steps to transform AGStock into a professional-grade trading platform, focusing on Portfolio Management and Real-time Paper Trading.

## User Review Required

> [!IMPORTANT]
> **Data Sources**: Fundamental data (PER/PBR) might require more reliable API sources than yfinance, but we will attempt to use yfinance first.
> **Persistence**: Paper trading requires saving state (current positions, cash) to a local database (SQLite).

## Proposed Changes

### Phase 4: Portfolio Management (Risk Diversification)
Move from single-stock analysis to portfolio-level analysis.

#### [NEW] [src/portfolio.py](file:///c:/gemini-thinkpad/AGStock/src/portfolio.py)
- **Correlation Matrix**: Calculate correlation between selected stocks to warn about concentrated risk.
- **Portfolio Backtest**: Run backtests on multiple stocks simultaneously, respecting total capital constraints.
- **Rebalancing Logic**: (Optional) Periodically rebalance portfolio weights.

#### [MODIFY] [app.py](file:///c:/gemini-thinkpad/AGStock/app.py)
- Add "Portfolio Simulation" mode.
- Allow selecting multiple stocks (e.g., Top 5 from AI ranking).
- Display "Portfolio Equity Curve" vs "Benchmark (Nikkei 225)".

### Phase 5: Paper Trading (Forward Test)
Track real-time performance without risking real money.

#### [NEW] [paper_trade.py](file:///c:/gemini-thinkpad/AGStock/paper_trade.py)
- **Database**: Use `sqlite3` to store:
    - `balance`: Current cash.
    - `positions`: Current holdings (Ticker, Quantity, Entry Price).
    - `orders`: History of orders.
- **Daily Routine**:
    1. Update current prices of holdings.
    2. Check for Exit signals (SL/TP or Strategy Exit).
    3. Check for Entry signals (from `daily_scan`).
    4. Execute trades (update DB).
    5. Log daily equity.

#### [MODIFY] [app.py](file:///c:/gemini-thinkpad/AGStock/app.py)
- Add "Paper Trading Dashboard" tab.
- Show current virtual portfolio status, open profit/loss, and trade history.

### Phase 6: Fundamental Filters (Bonus)
Filter stocks based on value.

#### [MODIFY] [src/data_loader.py](file:///c:/gemini-thinkpad/AGStock/src/data_loader.py)
- Fetch `info` from yfinance (PER, PBR, Dividend Yield).

#### [MODIFY] [daily_scan.py](file:///c:/gemini-thinkpad/AGStock/daily_scan.py)
- Add filters: e.g., "Only buy if PER < 15".

## Verification Plan

### Automated Tests
- **test_portfolio.py**: Verify correlation calculations and portfolio return aggregation.
- **test_paper_trade.py**: Verify database operations (buy/sell updates balance correctly).

### Manual Verification
- **Portfolio**: Compare a diversified portfolio (5 stocks) vs single stock. Check if Drawdown is reduced.
- **Paper Trading**: Run `paper_trade.py` for a few days (simulated) and check if the database updates correctly.
