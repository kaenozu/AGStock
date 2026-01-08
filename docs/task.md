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

## Phase 6: Fundamental Analysis (Completed)
- [x] **Data Fetching**
    - [x] Update `data_loader.py` to fetch PER, PBR, ROE, Market Cap using `yfinance`.
    - [x] Implement caching for fundamental data (update weekly/monthly for earnings, daily for price ratios).
- [x] **Filtering Logic**
    - [x] Create `src/fundamentals.py` to handle filtering logic (e.g., PER < 20, ROE > 8%).
    - [x] Integrate fundamental filters into `daily_scan.py`.
- [x] **App Integration**
    - [x] Display fundamental metrics in `app.py` dashboard.

## Phase 7: Refinement & Automation (Completed)
- [x] **Portfolio Logic Refinement**
    - [x] Improve date alignment in `src/portfolio.py`.
    - [x] Allow per-ticker strategy selection in `simulate_portfolio`.
- [x] **App UX Improvements**
    - [x] **Portfolio**: Auto-select best strategy for each stock.
    - [x] **Paper Trading**: Add "One-Click Order" button to Market Scan results.

## Phase 8: Advanced Alpha Generation (Completed)
- [x] **Setup**
    - [x] Install `lightgbm`.
- [x] **Feature Engineering**
    - [x] Create `src/features.py` for advanced indicators (ATR, Volatility, etc.).
- [x] **Model Implementation**
    - [x] Create `LightGBMStrategy` in `src/strategies.py`.
    - [x] Implement Walk-Forward Validation logic.

## Phase 9: Portfolio Optimization (Completed)
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

## Phase 17: CLI & Configuration (Completed)
- [x] **Configuration Management**
    - [x] Create `config.yaml` for centralized settings (capital, risk, notifications).
    - [x] Create `src/config.py` to load and validate configuration.
- [x] **CLI Tool**
    - [x] Create `agstock.py` using `argparse`.
    - [x] Implement commands: `run`, `backtest`, `report`, `backup`.

## Phase 18: Enhanced Backup & Automation (Completed)
- [x] **Automated Backup**
    - [x] Add cron/Task Scheduler setup to `setup.sh`/`setup.bat`.
    - [x] Implement cloud sync option (copy to specified path).
- [x] **Automation Reliability**
    - [x] Add retry logic for data fetching and API calls.
    - [x] Implement comprehensive logging to file.

## Phase 19: Portfolio Rebalancing (Completed)
- [x] **Rebalancing Logic**
    - [x] Add `rebalance_portfolio` function to `src/portfolio.py`.
    - [x] Implement periodic rebalancing (e.g., monthly) in backtester.
- [x] **Simulation**
    - [x] Create rebalancing simulation script.
    - [x] Visualize rebalancing effect on performance.

## Phase 20: Visualization & Reporting (Completed)
- [x] **Interactive Reports**
    - [x] Enhance `backtest_report.py` to generate interactive HTML.
    - [x] Add strategy correlation heatmap.
- [x] **PDF Export**
    - [x] Implement PDF report generation using `reportlab` or `weasyprint`.

## Phase 21: Notification Channels (Completed)
- [x] **Discord Integration**
    - [x] Add Discord webhook support to `src/notifier.py`.
- [x] **Push Notifications**
    - [x] Add Pushover/Pushbullet support.

## Phase 22: Custom Strategy Plugins (Completed)
- [x] **Plugin System**
    - [x] Create `src/strategies/custom/` directory.
    - [x] Implement dynamic strategy loading in `src/strategies.py`.
- [x] **UI Integration**
    - [x] Auto-detect custom strategies in `app.py`.

## Phase 23: Quality Assurance (Completed)
- [x] **Unit Tests**
    - [x] Create unit tests for new components (`tests/`)
    - [x] Set up `black` and `isort` configuration (`pyproject.toml`)
    - [x] Verify all tests pass
- [ ] **Code Quality**
    - [ ] Create pre-commit hook setup.

## Phase 24: Sentiment Analysis (Completed)
- [x] **News Aggregation**
    - [x] Fetch news headlines via RSS or API (e.g., NewsAPI).
- [x] **Sentiment Scoring**
    - [x] Implement basic NLP (Natural Language Processing) to score sentiment (Positive/Negative).
- [x] **Signal Filtering**
    - [x] Filter "Buy" signals if sentiment is strongly negative.

## Phase 25: Deep Learning (Completed)
- [x] **Model Development**
    - [x] Implement LSTM or Transformer model for time-series prediction.
- [x] **Integration**
    - [x] Add as a new strategy class (`DeepLearningStrategy`).

## Phase 26: Sentiment Analysis Enhancement (Completed)
- [x] **Data Persistence**
    - [x] Add sentiment history database storage.
    - [x] Implement historical data retrieval methods.
- [x] **Visualization**
    - [x] Create sentiment timeline chart (7/30 days).
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

## Phase 6: Fundamental Analysis (Completed)
- [x] **Data Fetching**
    - [x] Update `data_loader.py` to fetch PER, PBR, ROE, Market Cap using `yfinance`.
    - [x] Implement caching for fundamental data (update weekly/monthly for earnings, daily for price ratios).
- [x] **Filtering Logic**
    - [x] Create `src/fundamentals.py` to handle filtering logic (e.g., PER < 20, ROE > 8%).
    - [x] Integrate fundamental filters into `daily_scan.py`.
- [x] **App Integration**
    - [x] Display fundamental metrics in `app.py` dashboard.

## Phase 7: Refinement & Automation (Completed)
- [x] **Portfolio Logic Refinement**
    - [x] Improve date alignment in `src/portfolio.py`.
    - [x] Allow per-ticker strategy selection in `simulate_portfolio`.
- [x] **App UX Improvements**
    - [x] **Portfolio**: Auto-select best strategy for each stock.
    - [x] **Paper Trading**: Add "One-Click Order" button to Market Scan results.

## Phase 8: Advanced Alpha Generation (Completed)
- [x] **Setup**
    - [x] Install `lightgbm`.
- [x] **Feature Engineering**
    - [x] Create `src/features.py` for advanced indicators (ATR, Volatility, etc.).
- [x] **Model Implementation**
    - [x] Create `LightGBMStrategy` in `src/strategies.py`.
    - [x] Implement Walk-Forward Validation logic.

## Phase 9: Portfolio Optimization (Completed)
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

## Phase 17: CLI & Configuration (Completed)
- [x] **Configuration Management**
    - [x] Create `config.yaml` for centralized settings (capital, risk, notifications).
    - [x] Create `src/config.py` to load and validate configuration.
- [x] **CLI Tool**
    - [x] Create `agstock.py` using `argparse`.
    - [x] Implement commands: `run`, `backtest`, `report`, `backup`.

## Phase 18: Enhanced Backup & Automation (Completed)
- [x] **Automated Backup**
    - [x] Add cron/Task Scheduler setup to `setup.sh`/`setup.bat`.
    - [x] Implement cloud sync option (copy to specified path).
- [x] **Automation Reliability**
    - [x] Add retry logic for data fetching and API calls.
    - [x] Implement comprehensive logging to file.

## Phase 19: Portfolio Rebalancing (Completed)
- [x] **Rebalancing Logic**
    - [x] Add `rebalance_portfolio` function to `src/portfolio.py`.
    - [x] Implement periodic rebalancing (e.g., monthly) in backtester.
- [x] **Simulation**
    - [x] Create rebalancing simulation script.
    - [x] Visualize rebalancing effect on performance.

## Phase 20: Visualization & Reporting (Completed)
- [x] **Interactive Reports**
    - [x] Enhance `backtest_report.py` to generate interactive HTML.
    - [x] Add strategy correlation heatmap.
- [x] **PDF Export**
    - [x] Implement PDF report generation using `reportlab` or `weasyprint`.

## Phase 21: Notification Channels (Completed)
- [x] **Discord Integration**
    - [x] Add Discord webhook support to `src/notifier.py`.
- [x] **Push Notifications**
    - [x] Add Pushover/Pushbullet support.

## Phase 22: Custom Strategy Plugins (Completed)
- [x] **Plugin System**
    - [x] Create `src/strategies/custom/` directory.
    - [x] Implement dynamic strategy loading in `src/strategies.py`.
- [x] **UI Integration**
    - [x] Auto-detect custom strategies in `app.py`.

## Phase 23: Quality Assurance (Completed)
- [x] **Unit Tests**
    - [x] Create unit tests for new components (`tests/`)
    - [x] Set up `black` and `isort` configuration (`pyproject.toml`)
    - [x] Verify all tests pass
- [ ] **Code Quality**
    - [ ] Create pre-commit hook setup.

## Phase 24: Sentiment Analysis (Completed)
- [x] **News Aggregation**
    - [x] Fetch news headlines via RSS or API (e.g., NewsAPI).
- [x] **Sentiment Scoring**
    - [x] Implement basic NLP (Natural Language Processing) to score sentiment (Positive/Negative).
- [x] **Signal Filtering**
    - [x] Filter "Buy" signals if sentiment is strongly negative.

## Phase 25: Deep Learning (Completed)
- [x] **Model Development**
    - [x] Implement LSTM or Transformer model for time-series prediction.
- [x] **Integration**
    - [x] Add as a new strategy class (`DeepLearningStrategy`).

## Phase 26: Sentiment Analysis Enhancement (Completed)
- [x] **Data Persistence**
    - [x] Add sentiment history database storage.
    - [x] Implement historical data retrieval methods.
- [x] **Visualization**
    - [x] Create sentiment timeline chart (7/30 days).
    - [x] Add news headlines display widget.
    - [x] Implement sentiment gauge indicator.
- [x] **UX Improvements**
    - [x] Move sentiment to dedicated expandable section.

## Phase 27: UI Simplification (Completed)
- [x] **Beginner-Friendly Interface**
    - [x] Add `get_signal_explanation` to strategies
    - [x] Implement "Today's Best Pick" section
    - [x] Simplify result cards
    - [x] Add Risk Level indicators
    - [x] Hide advanced details behind "Details" toggle.

- [x] Phase 28: Workflow Automation
  - [x] Enhance `daily_scan.py` to output rich JSON
  - [x] Modify `app.py` to auto-load latest results
  - [x] Implement background auto-run on launch

- [x] Phase 29: Robo-Advisor Mode (Portfolio Automation)
  - [x] Update `daily_scan.py` to calculate optimal portfolio allocation
  - [x] Save portfolio weights to `scan_results.json`
  - [x] Display "AI Recommended Portfolio" in `app.py`

- [x] Phase 30: Crypto Support
  - [x] Add Crypto tickers to `src/constants.py`
  - [x] Enable Crypto scanning in `daily_scan.py`
  - [x] Update `app.py` to support Crypto market selection

- [x] Phase 31: Budget-Friendly Features (Odd Lot Support)
  - [x] Add "Trading Unit" toggle (100 shares vs 1 share) in `app.py` sidebar
  - [x] Update order logic to handle Odd Lot (S-kabu/Mini-kabu) trading
  - [x] Update Robo-Advisor to calculate shares based on selected unit

- [x] Phase 32: High Dividend Strategy (Income Gain Focus)
  - [x] Update `src/data_loader.py` to fetch Dividend Yield
  - [x] Create `DividendStrategy` in `src/strategies.py`
  - [x] Update `daily_scan.py` to include Dividend Strategy
  - [x] Add "High Dividend" section to `app.py`

- [x] Phase 33: Dividend Growth Analysis & Visualization
  - [x] Fetch historical dividend data (5 years)
  - [x] Calculate dividend growth rate (CAGR)
  - [x] Count consecutive dividend increase years
  - [x] Add dividend trend chart to UI
  - [x] Update high dividend section with growth metrics

- [x] Phase 34: Notification System (LINE/Discord)
  - [x] Implement LINE Notify integration
  - [x] Implement Discord Webhook integration
  - [x] Create notification formatter for scan results
  - [x] Add notification settings to config
  - [x] Update daily_scan.py to send notifications

- [x] Phase 35: Performance Analysis Dashboard
  - [x] Calculate cumulative P&L from paper trading history
  - [x] Create strategy-wise performance metrics
  - [x] Add benchmark comparison (Nikkei 225)
  - [x] Implement monthly/weekly performance reports
  - [x] Create interactive performance dashboard in app.py
- [x] Phase 36: Historical Backtesting (10-Year Validation)
  - [x] Create `src/backtest_engine.py` for long-term simulation
  - [x] Implement `fetch_historical_data` (10 years) in `data_loader.py`
  - [x] Create `HistoricalBacktester` class with CAGR, MaxDD, Sharpe metrics
  - [x] Add "Historical Validation" tab to `app.py`
  - [x] Visualize long-term equity curve and annual returns
- [x] Phase 37: Chart Pattern Recognition (Technical Analysis)
  - [x] Create `src/patterns.py` for pattern detection algorithms
  - [x] Implement `detect_double_bottom`, `detect_head_and_shoulders`
  - [x] Implement `detect_triangle` (Ascending/Descending)
  - [x] Integrate into `daily_scan.py` and `app.py` with visualization
  - [ ] Update `daily_scan.py` to scan for patterns
  - [x] Add "Pattern Scan" section to `app.py`

- [x] Phase 38: Deep Learning Strategy Refinement (Fix Data Leakage)
  - [x] Refactor `DeepLearningStrategy` in `src/strategies.py`
  - [x] Implement Walk-Forward Validation logic
  - [x] Add `Volume` and `Volatility` features
  - [x] Update `data_loader.py` to fetch sufficient history
  - [x] Create `verify_dl_strategy.py` for leakage testing
  - [x] Verify with synthetic data

- [x] Phase 39: Fundamental Analysis Integration
  - [x] Update `daily_scan.py` to fetch fundamental data
  - [x] Implement filtering logic (PER, PBR, ROE) in `daily_scan.py`
  - [x] Add "Fundamental Filters" sidebar to `app.py`
  - [x] Display fundamental metrics (badges) in `app.py` results

- [x] Phase 40: Advanced Portfolio Optimization
  - [x] Update `src/portfolio.py` with Efficient Frontier logic
  - [x] Implement Monte Carlo simulation for portfolio generation
  - [x] Add "Portfolio" tab to `app.py` with interactive charts
  - [x] Visualize Efficient Frontier and Correlation Matrix

- [x] Phase 41: System Polish & Final Documentation
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

## Phase 17: CLI & Configuration (Completed)
- [x] **Configuration Management**
    - [x] Create `config.yaml` for centralized settings (capital, risk, notifications).
    - [x] Create `src/config.py` to load and validate configuration.
- [x] **CLI Tool**
    - [x] Create `agstock.py` using `argparse`.
    - [x] Implement commands: `run`, `backtest`, `report`, `backup`.

## Phase 18: Enhanced Backup & Automation (Completed)
- [x] **Automated Backup**
    - [x] Add cron/Task Scheduler setup to `setup.sh`/`setup.bat`.
    - [x] Implement cloud sync option (copy to specified path).
- [x] **Automation Reliability**
    - [x] Add retry logic for data fetching and API calls.
    - [x] Implement comprehensive logging to file.

## Phase 19: Portfolio Rebalancing (Completed)
- [x] **Rebalancing Logic**
    - [x] Add `rebalance_portfolio` function to `src/portfolio.py`.
    - [x] Implement periodic rebalancing (e.g., monthly) in backtester.
- [x] **Simulation**
    - [x] Create rebalancing simulation script.
    - [x] Visualize rebalancing effect on performance.

## Phase 20: Visualization & Reporting (Completed)
- [x] **Interactive Reports**
    - [x] Enhance `backtest_report.py` to generate interactive HTML.
    - [x] Add strategy correlation heatmap.
- [x] **PDF Export**
    - [x] Implement PDF report generation using `reportlab` or `weasyprint`.

## Phase 21: Notification Channels (Completed)
- [x] **Discord Integration**
    - [x] Add Discord webhook support to `src/notifier.py`.
- [x] **Push Notifications**
    - [x] Add Pushover/Pushbullet support.

## Phase 22: Custom Strategy Plugins (Completed)
- [x] **Plugin System**
    - [x] Create `src/strategies/custom/` directory.
    - [x] Implement dynamic strategy loading in `src/strategies.py`.
- [x] **UI Integration**
    - [x] Auto-detect custom strategies in `app.py`.

## Phase 23: Quality Assurance (Completed)
- [x] **Unit Tests**
    - [x] Create unit tests for new components (`tests/`)
    - [x] Set up `black` and `isort` configuration (`pyproject.toml`)
    - [x] Verify all tests pass
- [ ] **Code Quality**
    - [ ] Create pre-commit hook setup.

## Phase 24: Sentiment Analysis (Completed)
- [x] **News Aggregation**
    - [x] Fetch news headlines via RSS or API (e.g., NewsAPI).
- [x] **Sentiment Scoring**
    - [x] Implement basic NLP (Natural Language Processing) to score sentiment (Positive/Negative).
- [x] **Signal Filtering**
    - [x] Filter "Buy" signals if sentiment is strongly negative.

## Phase 25: Deep Learning (Completed)
- [x] **Model Development**
    - [x] Implement LSTM or Transformer model for time-series prediction.
- [x] **Integration**
    - [x] Add as a new strategy class (`DeepLearningStrategy`).

## Phase 26: Sentiment Analysis Enhancement (Completed)
- [x] **Data Persistence**
    - [x] Add sentiment history database storage.
    - [x] Implement historical data retrieval methods.
- [x] **Visualization**
    - [x] Create sentiment timeline chart (7/30 days).
    - [x] Add news headlines display widget.
    - [x] Implement sentiment gauge indicator.
- [x] **UX Improvements**
    - [x] Move sentiment to dedicated expandable section.

## Phase 27: UI Simplification (Completed)
- [x] **Beginner-Friendly Interface**
    - [x] Add `get_signal_explanation` to strategies
    - [x] Implement "Today's Best Pick" section
    - [x] Simplify result cards
    - [x] Add Risk Level indicators
    - [x] Hide advanced details behind "Details" toggle.

- [x] Phase 28: Workflow Automation
  - [x] Enhance `daily_scan.py` to output rich JSON
  - [x] Modify `app.py` to auto-load latest results
  - [x] Implement background auto-run on launch

- [x] Phase 29: Robo-Advisor Mode (Portfolio Automation)
  - [x] Update `daily_scan.py` to calculate optimal portfolio allocation
  - [x] Save portfolio weights to `scan_results.json`
  - [x] Display "AI Recommended Portfolio" in `app.py`

- [x] Phase 30: Crypto Support
  - [x] Add Crypto tickers to `src/constants.py`
  - [x] Enable Crypto scanning in `daily_scan.py`
  - [x] Update `app.py` to support Crypto market selection

- [x] Phase 31: Budget-Friendly Features (Odd Lot Support)
  - [x] Add "Trading Unit" toggle (100 shares vs 1 share) in `app.py` sidebar
  - [x] Update order logic to handle Odd Lot (S-kabu/Mini-kabu) trading
  - [x] Update Robo-Advisor to calculate shares based on selected unit

- [x] Phase 32: High Dividend Strategy (Income Gain Focus)
  - [x] Update `src/data_loader.py` to fetch Dividend Yield
  - [x] Create `DividendStrategy` in `src/strategies.py`
  - [x] Update `daily_scan.py` to include Dividend Strategy
  - [x] Add "High Dividend" section to `app.py`

- [x] Phase 33: Dividend Growth Analysis & Visualization
  - [x] Fetch historical dividend data (5 years)
  - [x] Calculate dividend growth rate (CAGR)
  - [x] Count consecutive dividend increase years
  - [x] Add dividend trend chart to UI
  - [x] Update high dividend section with growth metrics

- [x] Phase 34: Notification System (LINE/Discord)
  - [x] Implement LINE Notify integration
  - [x] Implement Discord Webhook integration
  - [x] Create notification formatter for scan results
  - [x] Add notification settings to config
  - [x] Update daily_scan.py to send notifications

- [x] Phase 35: Performance Analysis Dashboard
  - [x] Calculate cumulative P&L from paper trading history
  - [x] Create strategy-wise performance metrics
  - [x] Add benchmark comparison (Nikkei 225)
  - [x] Implement monthly/weekly performance reports
  - [x] Create interactive performance dashboard in app.py
- [x] Phase 36: Historical Backtesting (10-Year Validation)
  - [x] Create `src/backtest_engine.py` for long-term simulation
  - [x] Implement `fetch_historical_data` (10 years) in `data_loader.py`
  - [x] Create `HistoricalBacktester` class with CAGR, MaxDD, Sharpe metrics
  - [x] Add "Historical Validation" tab to `app.py`
  - [x] Visualize long-term equity curve and annual returns
- [x] Phase 37: Chart Pattern Recognition (Technical Analysis)
  - [x] Create `src/patterns.py` for pattern detection algorithms
  - [x] Implement `detect_double_bottom`, `detect_head_and_shoulders`
  - [x] Implement `detect_triangle` (Ascending/Descending)
  - [x] Integrate into `daily_scan.py` and `app.py` with visualization
  - [ ] Update `daily_scan.py` to scan for patterns
  - [x] Add "Pattern Scan" section to `app.py`

- [x] Phase 38: Deep Learning Strategy Refinement (Fix Data Leakage)
  - [x] Refactor `DeepLearningStrategy` in `src/strategies.py`
  - [x] Implement Walk-Forward Validation logic
  - [x] Add `Volume` and `Volatility` features
  - [x] Update `data_loader.py` to fetch sufficient history
  - [x] Create `verify_dl_strategy.py` for leakage testing
  - [x] Verify with synthetic data

- [x] Phase 39: Fundamental Analysis Integration
  - [x] Update `daily_scan.py` to fetch fundamental data
  - [x] Implement filtering logic (PER, PBR, ROE) in `daily_scan.py`
  - [x] Add "Fundamental Filters" sidebar to `app.py`
  - [x] Display fundamental metrics (badges) in `app.py` results

- [x] Phase 40: Advanced Portfolio Optimization
  - [x] Update `src/portfolio.py` with Efficient Frontier logic
  - [x] Implement Monte Carlo simulation for portfolio generation
  - [x] Add "Portfolio" tab to `app.py` with interactive charts
  - [x] Visualize Efficient Frontier and Correlation Matrix

- [x] Phase 41: System Polish & Final Documentation
  - [x] Clean up temporary files (move tests, delete injectors)
  - [x] Add "Live Mode" (Auto-Refresh) to `app.py`
  - [x] Create `USER_MANUAL.md`
  - [x] Final Verification

- [x] Phase 42: Ensemble Learning (Multiple Models)
    - [x] Create `src/ensemble.py` for voting logic
    - [x] Implement `EnsembleStrategy` in `src/strategies.py`
    - [x] Integrate into `app.py`
- [x] Phase 43: UI Polish (Pro Design)
    - [x] Create `assets/style.css` (Dark Mode, Glassmorphism)
    - [x] Apply custom fonts and animations
- [x] Phase 44: Core System Enhancements (Data & Backtest)
    - [x] Implement `src/data_manager.py` (SQLite Data Cache)
    - [x] Refactor `src/data_loader.py` to use Data Manager
    - [x] Refactor `src/backtester.py` (Unified Portfolio Engine)
    - [x] Update `src/portfolio.py` to use new Backtester
    - [x] Create tests for Data Manager and Backtester
- [x] Phase 45: Smart Notifications (Rich Messages)
    - [x] Integrate Line/Discord API
    - [x] Send charts and summary reports

- [x] Phase 46: Core Improvements & Practicality
    - [x] Implement Anomaly Detector (Daily P&L tracking)
    - [x] Implement Auto Rebalancer (Correlation-based)
    - [x] Create One-click Startup Script (quick_start.py)
    - [x] Automate Weekly HTML Reports

- [x] Phase 47: Morning Dashboard (5-minute routine)
    - [x] Create Morning Dashboard for mobile/desktop
    - [x] Implement Portfolio Health Check
    - [x] One-tap Action Approval system

- [x] Phase 48: AI Strategy Advisor (Weekend Review)
    - [x] Implement Weekly Performance Scorecard
    - [x] AI-driven strategy weight optimization suggestions
    - [x] Simulation for next week's performance

- [x] Phase 49: Setup Wizard
    - [x] Interactive 5-step configuration generator
    - [x] Experience-based risk parameter presets

- [x] Phase 50: Performance Optimization
    - [x] Implement Disk Cache system (TTL support)
    - [x] Implement Batch Processor for data fetching
    - [x] Memory footprint optimization for DataFrames

- [x] Phase 51: Unified Dashboard (Pro Version)
    - [x] Integrate Home, Morning, Weekend, Lab, and Config into a single UI
    - [x] Glassmorphism 2.0 Design implementation

- [x] Phase 52-63: Advanced Autonomous Intelligence
    - [x] Implement **Mission Control** (Real-time System Monitoring)
    - [x] Implement **Advanced Risk Manager** & **Oracle 2026** (Divine Guidance)
    - [x] Implement **Neural Monitor** & **Neuromancer** (Deep model insights)
    - [x] Implement **Genetic Lab** (Strategy Evolution)
    - [x] Implement **War Room** (Global Market Simulation)

- [x] Phase 64: System Maintenance & Architecture Sync
    - [x] Update `production_readiness_check.py` for modern folder structure
    - [x] Rewrite `run_all.py` to support new modules and proper imports
    - [x] Synchronize documentation with implementation reality
    - [x] Perform full system routine test (Smart Alerts verified)

- [x] Phase 65: Quantum Hybrid Optimization
    - [x] Implement QUBO-based asset selection (Selecting K best stocks)
    - [x] Implement Hybrid Optimization (Selection by Annealing + Allocation by Classical)
    - [x] Update `PortfolioManager` to support Hybrid mode
    - [x] Update UI to display selection reasons

- [x] Phase 66: Multimodal Sentiment Analysis
    - [x] Create `MultimodalAnalyzer` using Gemini 2.0 Flash
    - [x] Implement text-based sentiment/summary extraction
    - [x] Implement Audio/Vision analysis infrastructure
    - [x] Integrate Multimodal Analysis into Earnings Analyst UI

- [x] Phase 67: Decentralized Autonomous Trading Network (DAO-Ready)
    - [x] Implement collective intelligence sharing (Simulated DAO API)
    - [x] Create Consensus Engine for multi-node signal weighting
    - [x] Integrate DAO signals into War Room UI
