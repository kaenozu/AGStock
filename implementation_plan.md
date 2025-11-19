# Implementation Plan - Machine Learning Strategy (Random Forest)

To truly live up to the name "AI Stock Predictor", I will implement a Machine Learning strategy using **Random Forest**. This model will learn complex, non-linear relationships between technical indicators to predict future price movements.

## User Review Required

> [!IMPORTANT]
> **Training Time**: ML models require training time. The app might be slightly slower when selecting this strategy.
> **Data Requirements**: ML needs sufficient historical data to learn patterns. It works best with "5y" or "Max" data.

## Proposed Changes

### 1. Dependencies
Add machine learning libraries.

#### [MODIFY] [requirements.txt](file:///c:/gemini-thinkpad/AGStock/requirements.txt)
- Add `scikit-learn`.

### 2. Strategy Implementation
Create a new strategy class that uses `RandomForestClassifier`.

#### [MODIFY] [src/strategies.py](file:///c:/gemini-thinkpad/AGStock/src/strategies.py)
- Import `RandomForestClassifier` from `sklearn.ensemble`.
- Implement `MLStrategy` class:
    - **Feature Engineering**: Calculate RSI, SMA ratios (Price/SMA), Volatility, Momentum.
    - **Target Creation**: Create a target variable (e.g., "Price Up > 0% tomorrow").
    - **Training**: Train the model on historical data (Rolling window or Walk-Forward).
    - **Prediction**: Generate signals based on model probability.

### 3. App Integration
Make the ML strategy available in the GUI.

#### [MODIFY] [app.py](file:///c:/gemini-thinkpad/AGStock/app.py)
- Add `MLStrategy` to the `strategies` list.
- (Optional) Display "Model Confidence" or "Feature Importance" if possible.

## Verification Plan

### Automated Tests
- **test_strategies.py**: Add a test for `MLStrategy`. Verify it can train and generate signals without errors.

### Manual Verification
- Run `app.py`, select `MLStrategy`, and verify it produces a backtest result.
- Compare its performance (Equity Curve) against standard strategies like RSI.
