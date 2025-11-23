# Core System Enhancement Plan

## Goal Description
Enhance the core components of AGStock to improve reliability, performance, and simulation accuracy.
1.  **Robust Data Management**: Implement a local database (SQLite) to cache historical data, enabling faster backtests and reducing API dependency.
2.  **Unified Backtesting Engine**: Refactor the backtester to natively support multi-asset portfolios, enabling accurate simulation of rebalancing, correlation-based strategies, and complex money management.

## User Review Required
> [!IMPORTANT]
> This refactor involves significant changes to `src/backtester.py` and `src/data_loader.py`. Existing strategies should remain compatible, but the `Backtester` class interface will be updated to support multi-asset data.

## Proposed Changes

### Data Management Layer
#### [NEW] [src/data_manager.py](file:///c:/gemini-thinkpad/AGStock/src/data_manager.py)
- Create `DataManager` class.
- **Storage**: Use `sqlite3` to store OHLCV data. Schema: `(ticker, date, open, high, low, close, volume)`.
- **Methods**:
    - `save_data(df, ticker)`: Upsert data into DB.
    - `load_data(ticker, start_date, end_date)`: Query data from DB.
    - `update_data(tickers)`: Fetch latest data from yfinance and append to DB (Incremental Update).
    - `get_latest_date(ticker)`: Check last available date in DB.

#### [MODIFY] [src/data_loader.py](file:///c:/gemini-thinkpad/AGStock/src/data_loader.py)
- Integrate `DataManager`.
- Update `fetch_stock_data` to first check local DB, then fetch missing range from API, save to DB, and return combined data.

### Backtesting Engine
#### [MODIFY] [src/backtester.py](file:///c:/gemini-thinkpad/AGStock/src/backtester.py)
- Refactor `Backtester` to handle a **Dictionary of DataFrames** (`Dict[str, pd.DataFrame]`) instead of a single DataFrame.
- **Event Loop**: Iterate through a unified date index.
- **Portfolio State**: Track `cash` and `holdings` (dict of shares) centrally.
- **Order Processing**:
    - Support `Market` orders (Open/Close).
    - Support `TargetWeight` logic for rebalancing.
- **Reporting**: Calculate portfolio-level metrics (Total Equity, Drawdown) natively.

#### [MODIFY] [src/portfolio.py](file:///c:/gemini-thinkpad/AGStock/src/portfolio.py)
- Update `simulate_portfolio` and `simulate_rebalancing` to use the new `Backtester` engine instead of ad-hoc loops.
- This ensures consistent logic for slippage, commission, and execution across all modes.

## Verification Plan

### Automated Tests
- **Data Manager Tests**:
    - Verify data saving and loading from SQLite.
    - Verify incremental updates (fetching only new data).
    - `pytest tests/test_data_manager.py`
- **Backtester Tests**:
    - Verify single-asset backtest results match previous version (regression test).
    - Verify multi-asset portfolio backtest with rebalancing.
    - `pytest tests/test_backtester_v2.py`

### Manual Verification
- **App Functionality**:
    - Run `streamlit run app.py`.
    - Verify "Market Scan" works (uses Data Manager).
    - Verify "Portfolio Simulation" works (uses new Backtester).
    - Verify "Paper Trading" continues to work.
