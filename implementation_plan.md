# Implementation Plan - Realistic Trading System Refactor

This plan aims to transform the current "theoretical" trading system into a robust, realistic engine capable of actual market application.

## User Review Required

> [!IMPORTANT]
> **Performance Drop Expected**: By removing "look-ahead bias" and adding transaction costs, the reported win rates and returns will significantly drop. This is not a bug; it is the **reality** of the market.
> **Execution Logic Change**: Trades will now be executed at the **Next Day's Open** price, not the current day's Close price.

## Proposed Changes

### Phase 1: Core Backtester Overhaul (Highest Priority)
The goal is to make the simulation mathematically correct and realistic.

#### [MODIFY] [src/backtester.py](file:///c:/gemini-thinkpad/AGStock/src/backtester.py)
- **Remove Look-ahead Bias**: Change execution logic to use `df['Open'].shift(-1)` for entry/exit prices.
- **Add Costs**: Introduce `commission` (default 0.1%) and `slippage` parameters.
- **Risk Management**: Implement `stop_loss` (e.g., -5%) and `take_profit` (e.g., +10%) logic within the trade loop.
- **New Metrics**: Calculate `Max Drawdown` (maximum peak-to-valley loss) to assess risk.

### Phase 2: Strategy Improvements
Basic strategies need safeguards.

#### [MODIFY] [src/strategies.py](file:///c:/gemini-thinkpad/AGStock/src/strategies.py)
- **Trend Filter**: Add an optional `trend_filter` (e.g., SMA 200) to all strategies. Only take long positions if the trend is up.
- **Combined Strategy**: Create a new strategy class that combines multiple signals (e.g., RSI + MACD).

### Phase 3: Verification & Reporting
We need to see the "real" numbers.

#### [MODIFY] [verify_accuracy.py](file:///c:/gemini-thinkpad/AGStock/verify_accuracy.py)
- Update to use the new Backtester parameters.
- Split data: Use the first 80% of data for optimization (if any) and the last 20% for "Out-of-Sample" testing to verify true performance.
- Report `Max Drawdown` and `Risk-Reward Ratio`.

## Verification Plan

### Automated Tests
1.  **Sanity Check**: Run `verify_accuracy.py` on a single ticker with known price movements to verify that trades happen at the *next day's open*.
2.  **Cost Impact**: Run the same strategy with 0% cost vs 0.1% cost to verify that performance decreases as expected.
3.  **Stop Loss Check**: Verify that trades are closed early if the price hits the stop loss level.

### Manual Verification
- I will generate a new `report.md` and compare it with the old one to demonstrate the difference between "fantasy" and "reality".
