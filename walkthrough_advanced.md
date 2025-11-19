# Advanced Features Walkthrough

I have implemented the advanced features to maximize profitability and usability.

## 1. AI Parameter Optimization (Optuna)

We now have an AI engine that finds the "best" parameters for each stock.

### How to use
Run the following command to start optimization:
```bash
python optimize_parameters.py
```
- It will test thousands of combinations for "RSI Reversal" and "Combined" strategies.
- Results are saved to `best_params.json`.
- **Note**: This process can take time (minutes to hours depending on the number of trials).

## 2. Daily Signal Report

A script to tell you exactly what to buy/sell tomorrow.

### How to use
Run this command every evening (after market close):
```bash
python daily_scan.py
```
- It loads the optimized parameters from `best_params.json` (if available).
- It scans all 40 tickers for buy/sell signals for the **Next Day Open**.
- Output is displayed in the terminal and saved to `daily_signals.csv`.

## 3. App Upgrades (Pro Version)

The Streamlit app has been upgraded to "Pro" specifications.

- **Equity Curve**: Now you can see the asset growth chart, not just the final return.
- **Visual Trade Markers**: Buy (Green Triangle) and Sell (Red Triangle) markers are shown on the price chart.
- **Max Drawdown**: Added risk metrics to the results table.
- **Combined Strategy**: The new robust strategy is now available in the app.

### How to run
```bash
run_app.bat
```
(Or `streamlit run app.py`)
