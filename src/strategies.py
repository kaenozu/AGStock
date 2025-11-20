import pandas as pd
import numpy as np
import ta
from typing import Optional
from sklearn.ensemble import RandomForestClassifier

class Strategy:
    def __init__(self, name: str, trend_period: int = 200) -> None:
        self.name = name
        self.trend_period = trend_period

    def apply_trend_filter(self, df: pd.DataFrame, signals: pd.Series) -> pd.Series:
        if self.trend_period <= 0:
            return signals
        
        trend_sma = df['Close'].rolling(window=self.trend_period).mean()
        
        filtered_signals = signals.copy()
        
        # Filter Longs: Can only Buy if Close > SMA(200)
        # Note: This might filter out "Reversal" strategies at the bottom.
        # But for safety, trading with the trend is better.
        long_condition = df['Close'] > trend_sma
        filtered_signals.loc[(signals == 1) & (~long_condition)] = 0
        
        # Filter Shorts: Can only Short if Close < SMA(200)
        short_condition = df['Close'] < trend_sma
        filtered_signals.loc[(signals == -1) & (~short_condition)] = 0
        
        return filtered_signals

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

class SMACrossoverStrategy(Strategy):
    def __init__(self, short_window: int = 5, long_window: int = 25, trend_period: int = 200) -> None:
        super().__init__(f"SMA Crossover ({short_window}/{long_window})", trend_period)
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
        
        signals = pd.Series(0, index=df.index)
        
        short_sma = df['Close'].rolling(window=self.short_window).mean()
        long_sma = df['Close'].rolling(window=self.long_window).mean()
        
        # Golden Cross
        signals.loc[(short_sma > long_sma) & (short_sma.shift(1) <= long_sma.shift(1))] = 1
        # Dead Cross
        signals.loc[(short_sma < long_sma) & (short_sma.shift(1) >= long_sma.shift(1))] = -1
        
        return self.apply_trend_filter(df, signals)

class RSIStrategy(Strategy):
    def __init__(self, period: int = 14, lower: float = 30, upper: float = 70, trend_period: int = 200) -> None:
        super().__init__(f"RSI ({period}) Reversal", trend_period)
        self.period = period
        self.lower = lower
        self.upper = upper

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
        
        rsi_indicator = ta.momentum.RSIIndicator(close=df['Close'], window=self.period)
        rsi = rsi_indicator.rsi()
        signals = pd.Series(0, index=df.index)
        
        if rsi is None or rsi.isna().all():
            return signals

        prev_rsi = rsi.shift(1)
        
        # Buy: Cross above lower
        signals.loc[(prev_rsi < self.lower) & (rsi >= self.lower)] = 1
        # Sell: Cross below upper
        signals.loc[(prev_rsi > self.upper) & (rsi <= self.upper)] = -1
        
        return self.apply_trend_filter(df, signals)

class BollingerBandsStrategy(Strategy):
    def __init__(self, length: int = 20, std: float = 2, trend_period: int = 200) -> None:
        super().__init__(f"Bollinger Bands ({length}, {std})", trend_period)
        self.length = length
        self.std = std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
        
        bollinger = ta.volatility.BollingerBands(close=df['Close'], window=self.length, window_dev=self.std)
        lower_band = bollinger.bollinger_lband()
        upper_band = bollinger.bollinger_hband()
        
        signals = pd.Series(0, index=df.index)
        
        # Buy: Touch Lower
        signals.loc[df['Close'] < lower_band] = 1
        # Sell: Touch Upper
        signals.loc[df['Close'] > upper_band] = -1
        
        return self.apply_trend_filter(df, signals)

class CombinedStrategy(Strategy):
    def __init__(self, rsi_period: int = 14, bb_length: int = 20, bb_std: float = 2, trend_period: int = 200) -> None:
        super().__init__("Combined (RSI + BB)", trend_period)
        self.rsi_period = rsi_period
        self.bb_length = bb_length
        self.bb_std = bb_std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
            
        # RSI
        rsi = ta.momentum.RSIIndicator(close=df['Close'], window=self.rsi_period).rsi()
        
        # BB
        bb = ta.volatility.BollingerBands(close=df['Close'], window=self.bb_length, window_dev=self.bb_std)
        lower_band = bb.bollinger_lband()
        upper_band = bb.bollinger_hband()
        
        signals = pd.Series(0, index=df.index)
        
        # Buy: RSI < 30 AND Close < Lower Band
        signals.loc[(rsi < 30) & (df['Close'] < lower_band)] = 1
        
        # Sell: RSI > 70 AND Close > Upper Band
        signals.loc[(rsi > 70) & (df['Close'] > upper_band)] = -1
        
        return self.apply_trend_filter(df, signals)

class MLStrategy(Strategy):
    def __init__(self, name: str = "AI Random Forest", trend_period: int = 0) -> None:
        # Trend period 0 because ML should learn the trend itself
        super().__init__(name, trend_period)
        self.model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or len(df) < 100:
            return pd.Series(dtype=int)
            
        data = df.copy()
        
        # --- Feature Engineering ---
        # 1. RSI
        data['RSI'] = ta.momentum.RSIIndicator(close=data['Close'], window=14).rsi()
        
        # 2. SMA Ratio (Price / SMA20)
        sma20 = data['Close'].rolling(window=20).mean()
        data['SMA_Ratio'] = data['Close'] / sma20
        
        # 3. Volatility (Std Dev / Close)
        data['Volatility'] = data['Close'].rolling(window=20).std() / data['Close']
        
        # 4. Returns Lag
        data['Ret_1'] = data['Close'].pct_change(1)
        data['Ret_5'] = data['Close'].pct_change(5)
        
        # Drop NaNs created by indicators
        data.dropna(inplace=True)
        
        if len(data) < 50:
            return pd.Series(0, index=df.index)
            
        # --- Target Creation ---
        # Target: 1 if Next Day Return > 0, else 0
        data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
        
        # Drop last row (NaN target)
        valid_data = data.iloc[:-1].copy()
        
        features = ['RSI', 'SMA_Ratio', 'Volatility', 'Ret_1', 'Ret_5']
        X = valid_data[features]
        y = valid_data['Target']
        
        # --- Train/Test Split ---
        # Train on first 70%, Predict on last 30%
        # This simulates "Learning from the past"
        split_idx = int(len(X) * 0.7)
        
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        if len(X_train) < 10:
            return pd.Series(0, index=df.index)
            
        self.model.fit(X_train, y_train)
        
        # Predict
        # We predict for the TEST set
        predictions = self.model.predict(X_test)
        
        # Map predictions to signals
        # Pred 1 -> Buy (1)
        # Pred 0 -> Sell (-1) (Short if allowed, or just Exit)
        
        signals = pd.Series(0, index=df.index)
        
        # Align predictions with original index
        # X_test index corresponds to the days we make the prediction (for tomorrow)
        test_indices = X_test.index
        
        pred_series = pd.Series(predictions, index=test_indices)
        
        signals.loc[test_indices] = pred_series.apply(lambda x: 1 if x == 1 else -1)
        
        # Note: Signals for the training period remain 0 (Hold)
        
        return signals

import lightgbm as lgb
from src.features import add_advanced_features

class LightGBMStrategy(Strategy):
    def __init__(self, lookback_days=365, threshold=0.005):
        super().__init__("LightGBM Alpha")
        self.lookback_days = lookback_days
        self.threshold = threshold
        self.model = None
        self.feature_cols = ['ATR', 'BB_Width', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Diff', 
                             'Dist_SMA_20', 'Dist_SMA_50', 'Dist_SMA_200', 'OBV', 'Volume_Change']

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # 1. Feature Engineering
        data = add_advanced_features(df)
        
        # Need enough data for lookback + features
        min_required = self.lookback_days + 50
        if len(data) < min_required:
            return pd.Series(0, index=df.index)
            
        signals = pd.Series(0, index=df.index)
        
        # 2. Walk-Forward Validation
        # We simulate a realistic scenario:
        # Retrain the model every 'retrain_period' days (e.g., 90 days / ~60 trading days)
        # Train on [Start : Current_Date], Predict [Current_Date : Current_Date + Period]
        
        retrain_period = 60 # Approx 3 months of trading days
        
        # Start predicting after the initial lookback period
        start_idx = self.lookback_days
        end_idx = len(data)
        
        current_idx = start_idx
        
        while current_idx < end_idx:
            # Define Training Data (All history up to current point)
            # To avoid training on ancient history that might be irrelevant, 
            # we could limit the training window (e.g., last 2 years).
            # For now, let's use an expanding window but capped at 5 years if needed.
            
            train_end = current_idx
            train_start = max(0, train_end - 1000) # Max 1000 days history
            
            train_df = data.iloc[train_start:train_end].dropna()
            
            # Define Prediction Window (Next 'retrain_period' days)
            pred_end = min(current_idx + retrain_period, end_idx)
            test_df = data.iloc[current_idx:pred_end].dropna()
            
            if train_df.empty or test_df.empty:
                current_idx += retrain_period
                continue
                
            # Prepare X, y
            X_train = train_df[self.feature_cols]
            y_train = (train_df['Return_1d'] > 0).astype(int)
            
            # Train
            params = {'objective': 'binary', 'metric': 'binary_logloss', 'verbosity': -1, 'seed': 42}
            train_data = lgb.Dataset(X_train, label=y_train)
            self.model = lgb.train(params, train_data, num_boost_round=100)
            
            # Predict for the chunk
            X_test = test_df[self.feature_cols]
            if not X_test.empty:
                preds = self.model.predict(X_test)
                
                # Generate Signals for this chunk
                chunk_signals = pd.Series(0, index=X_test.index)
                chunk_signals[preds > 0.55] = 1
                chunk_signals[preds < 0.45] = -1
                
                signals.loc[chunk_signals.index] = chunk_signals
            
            # Move to next chunk
            current_idx += retrain_period
            
        return signals
