import numpy as np
import pandas as pd
import ta
from numpy.lib.stride_tricks import sliding_window_view


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds basic technical indicators (RSI, MACD, BB).
    Kept for backward compatibility and baseline models.
    """
    df = df.copy()

    # RSI
    if "RSI" not in df.columns:
        df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()

    # MACD
    if "MACD" not in df.columns:
        macd = ta.trend.MACD(df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_Signal"] = macd.macd_signal()
        df["MACD_Diff"] = macd.macd_diff()

    # Bollinger Bands
    if "BB_High" not in df.columns:
        bb = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
        df["BB_High"] = bb.bollinger_hband()
        df["BB_Low"] = bb.bollinger_lband()
        df["BB_Mid"] = bb.bollinger_mavg()

    return df


def add_frequency_features(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Adds frequency domain features using FFT on rolling windows.
    Captures cyclical patterns in price changes.
    """
    df = df.copy()

    # Use log returns for stationarity
    log_ret = np.log(df["Close"] / df["Close"].shift(1)).fillna(0).to_numpy()

    if len(log_ret) < window:
        df["Freq_Power"] = np.nan
        return df

    # Vectorized dominant frequency calculation using sliding windows to avoid
    # per-window Python function calls.
    hanning_window = np.hanning(window)
    windows = sliding_window_view(log_ret, window_shape=window)
    windowed = windows * hanning_window

    spectra = np.fft.fft(windowed, axis=1)
    power_spectrum = np.abs(spectra[:, : window // 2])

    if power_spectrum.shape[1] > 1:
        dominant_power = power_spectrum[:, 1:].max(axis=1)
    else:
        dominant_power = np.zeros(power_spectrum.shape[0])

    freq_power = np.empty_like(log_ret, dtype=float)
    freq_power[: window - 1] = np.nan
    freq_power[window - 1 :] = dominant_power

    df["Freq_Power"] = freq_power

    return df


def add_sentiment_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds market sentiment features from the database.
    """
    from src.sentiment import SentimentAnalyzer

    df = df.copy()

    try:
        sa = SentimentAnalyzer()
        # Fetch enough history to cover the dataframe
        # Assuming df is recent, fetch last 365 days
        history = sa.get_sentiment_history(days=365)

        if not history:
            df["Sentiment_Score"] = 0.0
            return df

        sent_df = pd.DataFrame(history)
        sent_df["timestamp"] = pd.to_datetime(sent_df["timestamp"])
        sent_df.set_index("timestamp", inplace=True)

        # Resample to daily average
        daily_sent = sent_df["score"].resample("D").mean()

        # Merge
        # df index should be datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Join (left join to keep stock dates)
        # We need to ensure timezones match or are naive
        if df.index.tz is not None:
            daily_sent = daily_sent.tz_localize(df.index.tz)

        df["Sentiment_Score"] = daily_sent.reindex(df.index).fillna(method="ffill").fillna(0.0)

    except Exception as e:
        print(f"Error adding sentiment features: {e}")
        df["Sentiment_Score"] = 0.0

    return df


def add_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds advanced technical indicators for ML models.
    Now integrates comprehensive time-series features from src.advanced_features.
    """
    if df is None or len(df) < 50:
        return df

    # Import the new advanced features module
    try:
        from src.advanced_features import generate_phase29_features

        # Use the comprehensive Phase 29-1 feature generation
        df = generate_phase29_features(df)
    except ImportError:
        print("Could not import src.advanced_features, falling back to basic features")
        df = df.copy()

    # 1. Volatility Indicators (Legacy support if needed, but covered by new module)
    # ATR (Average True Range) - Measures volatility
    if "ATR" not in df.columns:
        try:
            df["ATR"] = ta.volatility.AverageTrueRange(
                df["High"], df["Low"], df["Close"], window=14
            ).average_true_range()
        except Exception as e:
            print(f"Error calculating ATR: {e}")
            df["ATR"] = 0.0

    # Bollinger Band Width
    if "BB_Width" not in df.columns:
        try:
            bb = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
            df["BB_Width"] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
        except Exception:
            df["BB_Width"] = 0.0

    # 2. Momentum Indicators
    # RSI
    if "RSI" not in df.columns:
        df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()

    # MACD
    if "MACD" not in df.columns:
        macd = ta.trend.MACD(df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_Signal"] = macd.macd_signal()
        df["MACD_Diff"] = macd.macd_diff()

    # 3. Trend Indicators
    # SMA/EMA Ratios (Distance from trend)
    df["SMA_20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator()
    df["SMA_50"] = ta.trend.SMAIndicator(df["Close"], window=50).sma_indicator()
    df["SMA_200"] = ta.trend.SMAIndicator(df["Close"], window=200).sma_indicator()

    df["SMA_Ratio"] = df["SMA_20"] / df["SMA_50"]
    df["Dist_SMA_20"] = (df["Close"] - df["SMA_20"]) / df["SMA_20"]
    df["Dist_SMA_50"] = (df["Close"] - df["SMA_50"]) / df["SMA_50"]
    df["Dist_SMA_200"] = (df["Close"] - df["SMA_200"]) / df["SMA_200"]

    # 4. Volume Indicators
    # OBV (On-Balance Volume) - Cumulative buying/selling pressure
    if "OBV" not in df.columns:
        df["OBV"] = ta.volume.OnBalanceVolumeIndicator(df["Close"], df["Volume"]).on_balance_volume()
    # Volume Change
    if "Volume_Change" not in df.columns:
        df["Volume_Change"] = df["Volume"].pct_change()

    # Volatility (Simple)
    if "Volatility" not in df.columns:
        df["Volatility"] = df["Close"].rolling(window=20).std() / df["Close"]

    # Past Returns (Features)
    if "Ret_1" not in df.columns:
        df["Ret_1"] = df["Close"].pct_change(1)
    if "Ret_5" not in df.columns:
        df["Ret_5"] = df["Close"].pct_change(5)

    # 5. New Advanced Features (FFT, Sentiment)
    df = add_frequency_features(df)
    df = add_sentiment_features(df)

    # 6. Target Variable (for training)
    # Return over next N days
    df["Return_1d"] = df["Close"].pct_change().shift(-1)  # Next day return
    df["Return_5d"] = df["Close"].pct_change(5).shift(-5)  # Next week return

    # Clean NaNs created by windows
    # Don't drop here, let the strategy handle it to preserve recent data for prediction

    return df


def add_macro_features(df: pd.DataFrame, macro_data: dict) -> pd.DataFrame:
    """
    Adds macro economic features to the dataframe.
    """
    df = df.copy()

    if not macro_data:
        return df

    # Align dates
    # Macro data might have different trading days (US holidays vs JP holidays)
    # We forward fill macro data to align with stock data

    # Ensure df index is timezone-naive for alignment
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    for name, macro_df in macro_data.items():
        # Calculate daily return/change for macro factor
        if name == "US10Y":
            # Yield change (basis points)
            macro_feat = macro_df["Close"].diff()
        else:
            # Price return
            macro_feat = macro_df["Close"].pct_change()

        # Ensure macro_feat index is timezone-naive
        if macro_feat.index.tz is not None:
            macro_feat.index = macro_feat.index.tz_localize(None)

        # Reindex to match stock df
        # ffill to propagate last known value (e.g. during JP holiday if US open, or vice versa)
        aligned_feat = macro_feat.reindex(df.index, method="ffill")

        df[f"{name}_Ret"] = aligned_feat

        # Add rolling correlation (e.g. 20 days)
        # Correlation between Stock Close Return and Macro Return
        stock_ret = df["Close"].pct_change()
        df[f"{name}_Corr"] = stock_ret.rolling(window=20).corr(aligned_feat)

    return df
