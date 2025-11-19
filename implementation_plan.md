# Implementation Plan - Advanced Features

This plan focuses on maximizing profitability through AI optimization and improving daily usability.

## User Review Required

> [!IMPORTANT]
> **Computation Time**: Optimization (Phase 1) can be time-consuming as it runs thousands of simulations.
> **Overfitting Risk**: While Optuna finds the "best" past parameters, we must be careful not to overfit. We will use a simple validation approach (train on 80%, test on 20%) to mitigate this.

## Proposed Changes

### Phase 1: AI Parameter Optimization (Priority: High)
Use `optuna` to find the best strategy parameters for each specific stock.

#### [NEW] [src/optimizer.py](file:///c:/gemini-thinkpad/AGStock/src/optimizer.py)
- Define objective functions for Optuna.
- Optimize:
    - **RSI**: Period, Upper/Lower thresholds.
    - **Bollinger Bands**: Length, Std Dev.
    - **Trend Filter**: SMA Period.
    - **Stop Loss / Take Profit**: Levels.

#### [NEW] [optimize_parameters.py](file:///c:/gemini-thinkpad/AGStock/optimize_parameters.py)
- Script to run the optimizer for all target tickers.
- Saves results to `best_params.json`.

#### [MODIFY] [requirements.txt](file:///c:/gemini-thinkpad/AGStock/requirements.txt)
- Add `optuna`.

### Phase 2: Daily Signal Report (Priority: Medium)
Turn the system into a daily tool.

#### [NEW] [daily_scan.py](file:///c:/gemini-thinkpad/AGStock/daily_scan.py)
- Loads `best_params.json`.
- Fetches the latest data (up to today).
- Checks if a signal is generated for "Tomorrow Open".
- Outputs a clear list: "BUY these", "SELL these".

### Phase 3: Visualization & App Upgrade (Priority: Low)
Make the results visible.

#### [MODIFY] [app.py](file:///c:/gemini-thinkpad/AGStock/app.py)
- Integrate the new `Backtester` and `Strategies`.
- Show Equity Curve (Asset growth chart).
- Visualize Buy/Sell points on the main chart.

## Verification Plan

### Automated Tests
We will create a `tests/` directory.

- **test_optimizer.py**: Verify that Optuna can run a few trials and produce a valid parameter set.
- **test_backtester.py**: Verify the "Next Day Open" execution logic and cost calculations.
- **test_strategies.py**: Verify that strategies produce correct signals given mock data.

### Manual Verification
- Run `optimize_parameters.py` for a few tickers and verify `best_params.json` is created.
- Run `daily_scan.py` and check if the output matches the latest chart situation.
