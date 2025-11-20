import pandas as pd
import numpy as np
import ta

def add_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds advanced technical indicators for ML models.
    """
    df = df.copy()
    
    # 1. Volatility Indicators
    # ATR (Average True Range) - Measures volatility
    df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
    # Bollinger Band Width - Measures volatility expansion/contraction
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_Width'] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
    
    # 2. Momentum Indicators
    # RSI
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    # MACD
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Diff'] = macd.macd_diff()
    
    # 3. Trend Indicators
    # SMA/EMA Ratios (Distance from trend)
    df['SMA_20'] = ta.trend.SMAIndicator(df['Close'], window=20).sma_indicator()
    df['SMA_50'] = ta.trend.SMAIndicator(df['Close'], window=50).sma_indicator()
    df['SMA_200'] = ta.trend.SMAIndicator(df['Close'], window=200).sma_indicator()
    
    df['Dist_SMA_20'] = (df['Close'] - df['SMA_20']) / df['SMA_20']
    df['Dist_SMA_50'] = (df['Close'] - df['SMA_50']) / df['SMA_50']
    df['Dist_SMA_200'] = (df['Close'] - df['SMA_200']) / df['SMA_200']
    
    # 4. Volume Indicators
    # OBV (On-Balance Volume) - Cumulative buying/selling pressure
    df['OBV'] = ta.volume.OnBalanceVolumeIndicator(df['Close'], df['Volume']).on_balance_volume()
    # Volume Change
    df['Volume_Change'] = df['Volume'].pct_change()
    
    # 5. Target Variable (for training)
    # Return over next N days
    df['Return_1d'] = df['Close'].pct_change().shift(-1) # Next day return
    df['Return_5d'] = df['Close'].pct_change(5).shift(-5) # Next week return
    
    # Clean NaNs created by windows
    # Don't drop here, let the strategy handle it to preserve recent data for prediction
    
    return df
