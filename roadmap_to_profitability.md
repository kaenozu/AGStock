# Roadmap to Profitability: AI Trading System Architecture

To build a truly profitable system, we need to move beyond simple technical indicators and address the entire trading pipeline. Here is the comprehensive list of requirements.

## 1. Universe Selection (銘柄選定)
**Current**: Nikkei 225 (225 stocks).
**Recommendation**: **500 - 1000 stocks**.
- **Why**: 225 is too small. AI needs more samples to learn patterns. High-liquidity mid-cap stocks often have more inefficiencies (profit opportunities) than efficient large-caps like Toyota.
- **Action**: Expand to TOPIX 500 or Top 1000 by liquidity.

## 2. Data Infrastructure (データ基盤)
**Current**: `yfinance` (Free, Daily OHLCV).
**Recommendation**: **Paid/Reliable Data + Alternative Data**.
- **Price Data**: J-Quants (JPX official) or Alpaca Japan. `yfinance` has delays and missing data.
- **Fundamental Data**: PER, PBR, Earnings surprises, Dividend dates.
- **Macro Data**: USD/JPY, US 10Y Yield, S&P500 trends (Japanese market is highly correlated with US).
- **Sentiment**: News sentiment (optional but powerful).

## 3. Alpha Generation (予測アルゴリズム)
**Current**: Random Forest, Technical Indicators (RSI, SMA).
**Recommendation**: **Ensemble of Models**.
- **Algorithm**:
    - **LightGBM / XGBoost**: The industry standard for tabular data. Handles noise better than Random Forest.
    - **LSTM / Transformer**: For capturing time-series sequences (e.g., "chart patterns").
- **Target**: Don't just predict "Up/Down". Predict **"Return / Volatility"** (Sharpe Ratio).
- **Feature Engineering**:
    - **Relative Strength**: Performance vs Sector index.
    - **Volatility**: ATR, Bollinger Band Width.
    - **Volume Profiles**: Is buying pressure increasing?

## 4. Portfolio Construction (ポートフォリオ構築)
**Current**: Equal weight, Correlation check.
**Recommendation**: **Mean-Variance Optimization / Risk Parity**.
- **Logic**: Instead of "Buy Top 5 equally", allocate risk equally.
- **Constraint**: "Max 20% in one sector" to avoid sector rotation risk.
- **Market Neutral**: Combine Long (Buy) and Short (Sell) to profit even if the market crashes.

## 5. Execution & Risk Management (売買・リスク管理)
**Current**: Manual/One-click, Stop Loss (5%).
**Recommendation**: **Fully Automated + Dynamic Risk**.
- **Execution**: Automated limit orders. Don't buy at "Open" blindly; use limit orders to save spread costs.
- **Dynamic Position Sizing**:
    - High Volatility -> Smaller Position.
    - Low Volatility -> Larger Position.
    - **Kelly Criterion**: Bet size based on model confidence.

## 6. Critical Concerns (懸念点)
1.  **Overfitting (過学習)**: The AI memorizes the past but fails in the future.
    - *Solution*: Walk-Forward Validation (train on 2020, test on 2021, train on 2021, test on 2022...).
2.  **Regime Change (相場環境の変化)**: Bull market strategies fail in Bear markets.
    - *Solution*: Detect "Market Regime" (Bull/Bear/Sideways) and switch strategies.
3.  **Costs (コスト)**: Trading fees and slippage kill AI strategies.
    - *Solution*: Focus on "Swing Trading" (holding days/weeks) rather than Day Trading to reduce turnover.

## Summary of Additions Needed
1.  [ ] **Data**: Switch to J-Quants or reliable source.
2.  [ ] **Model**: Upgrade to LightGBM + Walk-Forward Validation.
3.  [ ] **Features**: Add Fundamental & Macro factors.
4.  [ ] **Portfolio**: Implement Sector constraints and Volatility sizing.
5.  [ ] **Automation**: Fully automated order execution script.
