# Walkthrough - Deep Learning Strategy Implementation

## Overview
Implemented a Deep Learning strategy using LSTM (Long Short-Term Memory) to predict stock price movements. This strategy leverages `tensorflow` to build a neural network that learns from historical price sequences.

## Changes

### 1. Dependencies
- Added `tensorflow` to `requirements.txt`.

### 2. Strategy Implementation (`src/strategies.py`)
- Added `DeepLearningStrategy` class.
- **Model Architecture**:
    - LSTM (50 units) + Dropout (0.2)
    - LSTM (50 units) + Dropout (0.2)
    - Dense (25 units)
    - Dense (1 unit, Output)
- **Logic**:
    - Trains on historical Close prices (Lookback: 60 days).
    - Predicts the "Next Day" price.
    - Generates **BUY** signal if Predicted Price > Current Price * (1 + threshold).
    - Generates **SELL** signal if Predicted Price < Current Price * (1 - threshold).

### 3. App Integration (`app.py`)
- Registered `DeepLearningStrategy` in the main application.
- It is now available in the strategy selector for Backtesting and Portfolio Simulation.

## Verification Results

### Automated Test
Ran `tests/test_dl_strategy.py` to verify model training and signal generation.

**Result**: SUCCESS
```
Signals generated. Length: 200.
SUCCESS: Signal length matches data length.
```
The model successfully trained on dummy data and generated valid signals without errors.

## Next Steps
- **Performance Tuning**: The current implementation trains on the entire history for demonstration. For strict backtesting, a Walk-Forward Validation approach (similar to `LightGBMStrategy`) should be implemented to avoid look-ahead bias.
- **Hyperparameter Optimization**: `lookback`, `epochs`, and `batch_size` can be optimized using Optuna.
