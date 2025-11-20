# Task List

## Phase 1: Core Backtester & Strategy Refactor (Completed)
- [x] **Refactor Backtester**
    - [x] Implement `Backtester` class with `commission`, `slippage`, `initial_capital`.
    - [x] Implement `run()` method with "Next Day Open" execution logic.
    - [x] Add `stop_loss` and `take_profit` logic.
    - [x] Calculate `Max Drawdown`.
- [x] **Enhance Strategies**
    - [x] Add `trend_period` (SMA 200) filter to base `Strategy` class.
    - [x] Update `SMACrossoverStrategy`, `RSIStrategy`, `BollingerBandsStrategy`.
    - [x] Create `CombinedStrategy` (RSI + BB + Trend).
- [x] **Verification**
    - [x] Update `verify_accuracy.py` to use new Backtester.
    - [x] Generate `report.md` with realistic metrics.

## Phase 2: AI Optimization & Daily Signals (Completed)
- [x] **AI Optimization**
    - [x] Create `Optimizer` class using `optuna`.
    - [x] Create `optimize_parameters.py` script.
    - [x] Save best parameters to `best_params.json`.
- [x] **Daily Signal Report**
    - [x] Create `daily_scan.py`.
    - [x] Load optimized parameters.
    - [x] Output actionable "BUY/SELL" list for tomorrow.
- [x] **App Upgrade**
    - [x] Integrate `CombinedStrategy` into `app.py`.
    - [x] Display `Max Drawdown` and `Win Rate`.
    - [x] Visualize Equity Curve and Trade Markers.

## Phase 3: Advanced Features (Completed)
- [x] **Short Selling & Risk Management**
    - [x] Implement `allow_short` in Backtester.
    - [x] Implement `position_size` in Backtester.
    - [x] Update App UI for Short/Risk controls.
- [x] **Machine Learning Strategy**
    - [x] Implement `MLStrategy` using Random Forest.
    - [x] Integrate ML into App and Daily Scan.

## Phase 4: Portfolio Management (Completed)
- [x] **Portfolio Logic**
    - [x] Create `src/portfolio.py` for correlation and portfolio backtesting.
- [x] **App Integration**
    - [x] Add "Portfolio Simulation" mode to `app.py`.

## Phase 5: Paper Trading (Completed)
- [x] **Paper Trading Engine**
    - [x] Create `src/paper_trader.py` with SQLite database.
    - [x] Implement order execution and balance tracking.
- [x] **Daily Script**
    - [x] Create `paper_trade.py` for daily trading routine.
- [x] **App Integration**
    - [x] Add "Paper Trading Dashboard" tab to `app.py`.

## Phase 6: Fundamental Analysis (Planned)
- [ ] **Data Fetching**
    - [ ] Update `data_loader.py` to fetch PER/PBR.
- [ ] **Filtering**
    - [ ] Add fundamental filters to `daily_scan.py`.

## Phase 7: Refinement & Automation (Completed)
- [x] **Portfolio Logic Refinement**
    - [x] Improve date alignment in `src/portfolio.py`.
    - [x] Allow per-ticker strategy selection in `simulate_portfolio`.
- [x] **App UX Improvements**
    - [x] **Portfolio**: Auto-select best strategy for each stock.
    - [x] **Paper Trading**: Add "One-Click Order" button to Market Scan results.

## Phase 8: Advanced Alpha Generation (In Progress)
- [x] **Setup**
    - [x] Install `lightgbm`.
- [x] **Feature Engineering**
    - [x] Create `src/features.py` for advanced indicators (ATR, Volatility, etc.).
- [x] **Model Implementation**
    - [x] Create `LightGBMStrategy` in `src/strategies.py`.
    - [x] Implement Walk-Forward Validation logic.

## Phase 9: Portfolio Optimization (In Progress)
- [x] **Logic Implementation**
    - [x] Add `optimize_portfolio` method to `src/portfolio.py` (Mean-Variance).
- [x] **App Integration**
    - [x] Add "Optimization" section to Portfolio tab in `app.py`.

## Phase 10: Macro Factors & Market Regime (Completed)
- [x] **Data Fetching**
    - [x] Update `data_loader.py` to fetch Macro data (USD/JPY, ^GSPC, ^TNX).
- [x] **Feature Engineering**
    - [x] Update `src/features.py` to include Macro correlations.
- [x] **Model Update**
    - [x] Retrain `LightGBMStrategy` with Macro features.

## Phase 11: Automated Execution (Completed)
- [x] **Execution Engine**
    - [x] Create `src/execution.py` to handle order logic (Size, Limit/Market).
- [x] **Automation Script**
    - [x] Create `auto_trader.py` to run the full pipeline (Data -> Predict -> Trade).
    - [x] Implement "Risk Checks" (Max drawdown limit, Max position size).

## Phase 12: Backtest Visualization & Reporting (Completed)
- [x] **Report Generator**
    - [x] Create `backtest_report.py` to run comprehensive backtests.
    - [x] Generate performance metrics (Sharpe, Win Rate, Monthly Returns).
- [x] **Visualization**
    - [x] Create equity curves comparison chart.
    - [x] Generate confusion matrix for LightGBM predictions.
    - [x] Create monthly returns heatmap.

## Phase 13: Global Market Expansion (Completed)
- [x] **Universe Expansion**
    - [x] Add US stocks (S&P 500 constituents) to `src/constants.py`.
    - [x] Add European stocks (STOXX 50) to `src/constants.py`.
- [x] **App Integration**
    - [x] Update `app.py` to allow market selection (Japan/US/Europe/All).
- [x] **Testing**
    - [x] Run backtest on global portfolio.

## Phase 14: Notification System (Completed)
- [x] **Slack Integration**
    - [x] Create `src/notifier.py` with Slack webhook support.
    - [x] Add notification for strong BUY signals.
- [x] **Email Integration**
    - [x] Add email notification support.
    - [x] Create daily summary email template.

## Phase 15: GitHub Actions Automation (Completed)
- [x] **Workflow Setup**
    - [x] Create `.github/workflows/daily_scan.yml`.
    - [x] Configure cron schedule (17:00 JST daily).
- [x] **Reporting**
    - [x] Auto-save results to `reports/` folder.
    - [x] Create Issue on error.

## Phase 16: Dashboard Enhancement (Completed)
- [x] **Real-time Features**
    - [x] Add real-time price updates.
    - [x] Create performance heatmap.
- [x] **Alert System**
    - [x] Add custom alert configuration.
    - [x] Implement price threshold notifications.
