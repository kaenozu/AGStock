# Implementation Plan - Short Selling & Risk Management

This plan implements the "Short Selling" and "Position Sizing" features to further enhance profitability and risk control.

## User Review Required

> [!WARNING]
> **Short Selling Risk**: Short selling involves unlimited risk (theoretically). The system includes Stop Loss, but gaps in market price can still cause larger-than-expected losses.
> **Margin Requirements**: Real-world shorting requires a margin account. This simulation assumes you can borrow shares.

## Proposed Changes

### 1. Core Backtester Upgrade
Enable the system to profit from falling prices.

#### [MODIFY] [src/backtester.py](file:///c:/gemini-thinkpad/AGStock/src/backtester.py)
- Add `allow_short` (bool) parameter to `__init__`.
- Update `run` method to handle `current_position = -1`.
- Implement "Flip" logic:
    - Signal `-1` when Long: Sell to Close + Sell to Open (Short).
    - Signal `1` when Short: Buy to Cover + Buy to Open (Long).
- Add `position_size` (float) parameter (default 1.0) to simulate portfolio allocation.

### 2. Strategy Updates
Ensure strategies work well with shorting.

#### [MODIFY] [src/strategies.py](file:///c:/gemini-thinkpad/AGStock/src/strategies.py)
- Review `CombinedStrategy` and others.
- (Most standard strategies already output -1 for Sell, which naturally maps to Short if enabled).

### 3. App Integration
Add controls to the GUI.

#### [MODIFY] [app.py](file:///c:/gemini-thinkpad/AGStock/app.py)
- Add checkbox "空売りを許可する (Allow Short Selling)".
- Add slider "ポジションサイズ (Position Size)" (10% - 100%).
- Update charts to show "Short Entry" (Purple Triangle) and "Short Exit" (Blue Triangle) if needed, or reuse existing markers.

### 4. Daily Scan Update
Report short opportunities.

#### [MODIFY] [daily_scan.py](file:///c:/gemini-thinkpad/AGStock/daily_scan.py)
- Update logic to recommend "SELL (SHORT)" actions if `allow_short` is enabled.

## Verification Plan

### Automated Tests
- **test_backtester.py**: Add test case for `allow_short=True`. Verify that a price drop results in a profit.
- **test_backtester.py**: Add test case for `position_size=0.5`. Verify that returns are halved (approx).

### Manual Verification
- Run `app.py`, enable Short Selling, and check if the Equity Curve improves for downtrend stocks (e.g., check a stock that performed poorly in 2022/2023 if any).
