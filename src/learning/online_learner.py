"""
Online Learning System
Continuously updates models with new data and detects concept drift.
"""

import logging
from typing import Dict, Any
from collections import deque
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

logger = logging.getLogger(__name__)


class OnlineLearner:
    """
    Implements online (incremental) learning with concept drift detection.
    """

    def __init__(
        self,
        base_model: Any,
        window_size: int = 1000,
        drift_threshold: float = 0.2,
        retrain_interval: int = 100,
    ):
        """
        Args:
            base_model: Model with partial_fit() or incremental learning
            window_size: Size of sliding window for drift detection
            drift_threshold: Threshold for drift detection
            retrain_interval: Retrain after this many samples
        """
        self.base_model = base_model
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.retrain_interval = retrain_interval

        # Tracking
        self.sample_count = 0
        self.last_retrain = 0
        self.performance_history = deque(maxlen=window_size)
        self.drift_detected = False

    def partial_fit(self, X: pd.DataFrame, y: pd.Series) -> "OnlineLearner":
        """
        Incrementally update model with new data.

        Args:
            X: New features
            y: New targets

        Returns:
            Self
        """
        # Check if model supports partial_fit
        if hasattr(self.base_model, "partial_fit"):
            self.base_model.partial_fit(X, y)
        else:
            # Full retrain if partial_fit not supported
            self.base_model.fit(X, y)

        self.sample_count += len(X)

        # Check for drift
        if self.sample_count % 10 == 0:  # Check every 10 samples
            self._check_drift(X, y)

        # Periodic full retrain
        if self.sample_count - self.last_retrain >= self.retrain_interval:
            logger.info(f"Periodic retrain at sample {self.sample_count}")
            self.last_retrain = self.sample_count

        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions."""
        return self.base_model.predict(X)

    def _check_drift(self, X: pd.DataFrame, y: pd.Series):
        """
        Detect concept drift by monitoring prediction error.
        """
        # Make prediction
        y_pred = self.predict(X)

        # Calculate error
        error = mean_squared_error(y, y_pred)
        self.performance_history.append(error)

        if len(self.performance_history) < self.window_size // 2:
            return

        # Compare recent vs historical performance
        recent_error = np.mean(list(self.performance_history)[-50:])
        historical_error = np.mean(list(self.performance_history)[:-50])

        # Detect drift
        if recent_error > historical_error * (1 + self.drift_threshold):
            if not self.drift_detected:
                logger.warning(
                    f"Concept drift detected! "
                    f"Recent error: {recent_error:.4f}, "
                    f"Historical: {historical_error:.4f}"
                )
                self.drift_detected = True
        else:
            self.drift_detected = False

    def should_retrain(self) -> bool:
        """Check if model should be retrained."""
        return self.drift_detected or (
            self.sample_count - self.last_retrain >= self.retrain_interval
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        return {
            "sample_count": self.sample_count,
            "last_retrain": self.last_retrain,
            "drift_detected": self.drift_detected,
            "recent_error": np.mean(list(self.performance_history)[-50:])
            if self.performance_history
            else 0,
            "avg_error": np.mean(self.performance_history)
            if self.performance_history
            else 0,
        }
