"""
Multi-Model Hyperparameter Optimization
Orchestrates tuning for various prediction models (LSTM, LightGBM, Transformer).
"""

import logging
from typing import Any, Dict, List
import numpy as np

# These functions should be moved or imported properly
# For now, we'll keep the logic here for the transition
from src.hyperparameter_tuning import (
    optimize_lstm_params,
    optimize_lgbm_params,
    optimize_transformer_params
)

logger = logging.getLogger(__name__)

class MultiModelOptimizer:
    """Class to optimize multiple model types."""

    def __init__(self, cv_folds: int = 3):
        self.cv_folds = cv_folds
        self.best_params = {}

    def optimize_all_models(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_types: List[str] = ["lstm", "lgbm", "transformer"],
        n_trials_per_model: int = 20,
    ) -> Dict[str, Dict[str, Any]]:
        """Run optimization for all specified model types."""
        logger.info(f"🚀 Starting multi-model optimization: {model_types}")

        for model_type in model_types:
            logger.info(f"Optimizing {model_type} model...")
            try:
                if model_type == "lstm":
                    self.best_params[model_type] = optimize_lstm_params(X, y, n_trials=n_trials_per_model)
                elif model_type == "lgbm":
                    # Note: LightGBM might need specific data format, but let's assume it's handled in tuning.py
                    self.best_params[model_type] = optimize_lgbm_params(X, y, n_trials=n_trials_per_model)
                elif model_type == "transformer":
                    self.best_params[model_type] = optimize_transformer_params(X, y, n_trials=n_trials_per_model)
                
                logger.info(f"✅ Completed optimization for {model_type}")
            except Exception as e:
                logger.error(f"❌ Optimization failed for {model_type}: {e}")

        return self.best_params
