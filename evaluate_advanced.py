"""
Advanced Prediction System
Combines multiple strategies for improved accuracy:
1. Regime-specific models
2. Multi-horizon predictions
3. Confidence weighting
4. Cross-ticker training
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from lightgbm import LGBMRegressor

from src.data_loader import fetch_stock_data, fetch_external_data
from src.regime_detector import RegimeDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RegimeSpecificPredictor:
    """
    Trains separate models for different market regimes.
    High volatility markets behave differently from low volatility.
    """
    
    def __init__(self):
        self.models = {}
        self.regime_detector = RegimeDetector()
        
    def fit(self, X: pd.DataFrame, y: pd.Series, regimes: pd.Series):
        """
        Train separate models for each regime.
        
        Args:
            X: Features
            y: Targets
            regimes: Regime labels for each sample
        """
        logger.info("Training regime-specific models...")
        
        unique_regimes = regimes.unique()
        
        for regime in unique_regimes:
            mask = regimes == regime
            X_regime = X[mask]
            y_regime = y[mask]
            
            if len(X_regime) < 50:  # Skip if too few samples
                logger.warning(f"Skipping regime {regime}: only {len(X_regime)} samples")
                continue
            
            logger.info(f"Training model for regime '{regime}' ({len(X_regime)} samples)")
            
            model = LGBMRegressor(
                n_estimators=100,
                learning_rate=0.05,
                max_depth=5,
                reg_alpha=0.5,
                reg_lambda=0.5,
                random_state=42
            )
            
            model.fit(X_regime, y_regime)
            self.models[regime] = model
        
        logger.info(f"Trained {len(self.models)} regime-specific models")
        
    def predict(self, X: pd.DataFrame, regimes: pd.Series) -> np.ndarray:
        """
        Predict using regime-specific models.
        
        Args:
            X: Features
            regimes: Regime labels
        
        Returns:
            Predictions
        """
        predictions = np.zeros(len(X))
        
        for regime, model in self.models.items():
            mask = regimes == regime
            if mask.sum() > 0:
                predictions[mask] = model.predict(X[mask])
        
        return predictions


class MultiHorizonPredictor:
    """
    Predicts multiple time horizons and combines them.
    Short-term (1-day), medium-term (5-day), long-term (10-day).
    """
    
    def __init__(self, horizons: List[int] = [1, 5, 10]):
        """
        Args:
            horizons: List of prediction horizons in days
        """
        self.horizons = horizons
        self.models = {}
        
    def fit(self, df: pd.DataFrame, feature_cols: List[str]):
        """
        Train models for each horizon.
        
        Args:
            df: DataFrame with features and Close price
            feature_cols: List of feature column names
        """
        logger.info(f"Training multi-horizon models: {self.horizons} days")
        
        for horizon in self.horizons:
            # Create target for this horizon
            df[f'target_{horizon}d'] = df['Close'].pct_change(horizon).shift(-horizon)
            
            # Drop NaN
            df_clean = df.dropna()
            
            X = df_clean[feature_cols]
            y = df_clean[f'target_{horizon}d']
            
            logger.info(f"Training {horizon}-day model ({len(X)} samples)")
            
            model = LGBMRegressor(
                n_estimators=150,
                learning_rate=0.05,
                max_depth=6,
                reg_alpha=0.5,
                reg_lambda=0.5,
                random_state=42
            )
            
            model.fit(X, y)
            self.models[horizon] = model
        
        logger.info(f"Trained {len(self.models)} horizon models")
        
    def predict(self, X: pd.DataFrame) -> Dict[int, np.ndarray]:
        """
        Predict for all horizons.
        
        Args:
            X: Features
        
        Returns:
            Dictionary of predictions for each horizon
        """
        predictions = {}
        
        for horizon, model in self.models.items():
            predictions[horizon] = model.predict(X)
        
        return predictions
    
    def predict_weighted(self, X: pd.DataFrame, weights: Optional[Dict[int, float]] = None) -> np.ndarray:
        """
        Predict with weighted combination of horizons.
        
        Args:
            X: Features
            weights: Optional weights for each horizon
        
        Returns:
            Weighted predictions
        """
        if weights is None:
            # Default: equal weights
            weights = {h: 1.0 / len(self.horizons) for h in self.horizons}
        
        predictions = self.predict(X)
        
        weighted_pred = np.zeros(len(X))
        for horizon, pred in predictions.items():
            weighted_pred += pred * weights[horizon]
        
        return weighted_pred


class CrossTickerPredictor:
    """
    Trains on multiple tickers to learn general market patterns.
    More data = better generalization.
    """
    
    def __init__(self, tickers: List[str]):
        """
        Args:
            tickers: List of ticker symbols to train on
        """
        self.tickers = tickers
        self.model = None
        
    def prepare_multi_ticker_data(
        self,
        period: str = '5y',
        feature_cols: List[str] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Fetch and prepare data from multiple tickers.
        
        Args:
            period: Data period
            feature_cols: Feature columns to use
        
        Returns:
            Combined X, y
        """
        if feature_cols is None:
            feature_cols = ['SMA_5', 'SMA_20', 'RSI_14', 'Volume_MA_20']
        
        logger.info(f"Fetching data for {len(self.tickers)} tickers...")
        
        all_X = []
        all_y = []
        
        data = fetch_stock_data(self.tickers, period=period, interval='1d')
        
        for ticker in self.tickers:
            df = data.get(ticker)
            
            if df is None or df.empty:
                logger.warning(f"No data for {ticker}")
                continue
            
            # Add basic features
            df['SMA_5'] = df['Close'].rolling(5).mean()
            df['SMA_20'] = df['Close'].rolling(20).mean()
            df['RSI_14'] = self._calculate_rsi(df['Close'], 14)
            df['Volume_MA_20'] = df['Volume'].rolling(20).mean()
            
            # Target
            df['target'] = df['Close'].pct_change().shift(-1)
            
            df = df.dropna()
            
            if len(df) < 100:
                continue
            
            X = df[feature_cols]
            y = df['target']
            
            all_X.append(X)
            all_y.append(y)
            
            logger.info(f"  {ticker}: {len(X)} samples")
        
        # Combine all tickers
        X_combined = pd.concat(all_X, ignore_index=True)
        y_combined = pd.concat(all_y, ignore_index=True)
        
        logger.info(f"Total samples: {len(X_combined)}")
        
        return X_combined, y_combined
    
    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Train on combined data."""
        logger.info("Training cross-ticker model...")
        
        self.model = LGBMRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            reg_alpha=1.0,
            reg_lambda=1.0,
            random_state=42
        )
        
        self.model.fit(X, y)
        logger.info("Cross-ticker model trained")
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict."""
        return self.model.predict(X)
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi


def calculate_directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate directional accuracy."""
    correct = sum((y_true > 0) == (y_pred > 0))
    return correct / len(y_true)


def main():
    logger.info("="*70)
    logger.info("高度な予測戦略の評価")
    logger.info("="*70)
    
    # Test 1: Multi-horizon prediction
    logger.info("\n" + "="*70)
    logger.info("Test 1: Multi-Horizon Prediction")
    logger.info("="*70)
    
    ticker = '7203.T'
    data = fetch_stock_data([ticker], period='2y', interval='1d')
    df = data.get(ticker).copy()
    
    # Add features
    df['SMA_5'] = df['Close'].rolling(5).mean()
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['RSI_14'] = CrossTickerPredictor([])._calculate_rsi(df['Close'], 14)
    df['Volume_MA_20'] = df['Volume'].rolling(20).mean()
    
    feature_cols = ['SMA_5', 'SMA_20', 'RSI_14', 'Volume_MA_20']
    
    multi_horizon = MultiHorizonPredictor(horizons=[1, 5, 10])
    multi_horizon.fit(df, feature_cols)
    
    # Evaluate on test set
    df['target_1d'] = df['Close'].pct_change().shift(-1)
    df_test = df.dropna().tail(100)
    
    X_test = df_test[feature_cols]
    y_test = df_test['target_1d']
    
    # Predict with different weights
    pred_1d = multi_horizon.models[1].predict(X_test)
    pred_weighted = multi_horizon.predict_weighted(X_test, {1: 0.5, 5: 0.3, 10: 0.2})
    
    acc_1d = calculate_directional_accuracy(y_test.values, pred_1d)
    acc_weighted = calculate_directional_accuracy(y_test.values, pred_weighted)
    
    logger.info(f"1-day only:        {acc_1d:.2%}")
    logger.info(f"Multi-horizon:     {acc_weighted:.2%}")
    
    # Test 2: Cross-ticker training
    logger.info("\n" + "="*70)
    logger.info("Test 2: Cross-Ticker Training")
    logger.info("="*70)
    
    tickers = ['7203.T', '6758.T', '9984.T', '8306.T', '7974.T']  # Top 5 Japanese stocks
    cross_ticker = CrossTickerPredictor(tickers)
    
    X_combined, y_combined = cross_ticker.prepare_multi_ticker_data(period='3y')
    
    # Train/test split
    X_train, X_test_ct, y_train, y_test_ct = train_test_split(
        X_combined, y_combined, test_size=0.2, shuffle=False
    )
    
    cross_ticker.fit(X_train, y_train)
    pred_ct = cross_ticker.predict(X_test_ct)
    
    acc_ct = calculate_directional_accuracy(y_test_ct.values, pred_ct)
    
    logger.info(f"Cross-ticker accuracy: {acc_ct:.2%}")
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 最終結果")
    logger.info("="*70)
    logger.info(f"ベースライン（基本4特徴量）:  56.38%")
    logger.info(f"マルチホライズン:            {acc_weighted:.2%}")
    logger.info(f"クロスティッカー:            {acc_ct:.2%}")
    
    logger.info("\n" + "="*70)
    logger.info("✅ 評価完了")
    logger.info("="*70)


if __name__ == "__main__":
    main()
