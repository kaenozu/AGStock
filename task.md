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

## Phase 4: Portfolio Management (Planned)
- [ ] **Portfolio Logic**
    - [ ] Create `src/portfolio.py` for correlation and portfolio backtesting.
- [ ] **App Integration**
    - [ ] Add "Portfolio Simulation" mode to `app.py`.

## Phase 5: Paper Trading (Completed)
- [x] **Paper Trading Engine**
    - [x] Create `src/paper_trader.py` with SQLite database.
    - [x] Implement order execution and balance tracking.
- [x] **Daily Script**
    - [x] Create `paper_trade.py` for daily trading routine.


## Phase 6: Fundamental Analysis (Planned)
- [ ] **Data Fetching**
    - [ ] Update `data_loader.py` to fetch PER/PBR.
- [ ] **Filtering**
    - [ ] Add fundamental filters to `daily_scan.py`.
