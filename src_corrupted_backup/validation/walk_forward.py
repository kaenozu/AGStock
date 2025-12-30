# """
# Walk-Forward Validation
# Implements time series cross-validation to prevent data leakage and overfitting.
# """

import logging
from typing import List, Tuple, Dict, Any
from datetime import timedelta
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error

logger = logging.getLogger(__name__)


class WalkForwardValidator:
    #     """
    #     Walk-forward validation for time series models.
    #     Prevents look-ahead bias and provides realistic performance estimates.
    #     """

    def __init__(
        self,
        train_period_days: int = 730,  # 2 years
        test_period_days: int = 30,  # 1 month
        step_days: int = 30,  # Move forward 1 month each iteration
    ) -> None:
        #         """Initialize WalkForwardValidator."""
        self.train_period_days = train_period_days
        self.test_period_days = test_period_days
        self.step_days = step_days

    def split_time_series(
        self, df: pd.DataFrame, date_column: str = "Date"
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        #         """Create train/test splits for walk-forward validation."""
        if date_column in df.columns:
            df = df.set_index(date_column)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        splits = []
        start_date = df.index.min()
        end_date = df.index.max()
        current_date = start_date + timedelta(days=self.train_period_days)

        while current_date + timedelta(days=self.test_period_days) <= end_date:
            train_start = current_date - timedelta(days=self.train_period_days)
            train_end = current_date
            test_start = current_date
            test_end = current_date + timedelta(days=self.test_period_days)

            train_df = df[(df.index >= train_start) & (df.index < train_end)]
            test_df = df[(df.index >= test_start) & (df.index < test_end)]

            if not train_df.empty and not test_df.empty:
                splits.append((train_df, test_df))

            current_date += timedelta(days=self.step_days)

        logger.info(f"Created {len(splits)} walk-forward splits")
        return splits

    def validate_model(
        self,
        model,
        df: pd.DataFrame,
        feature_columns: List[str],
        target_column: str = "target",
    ) -> Dict[str, Any]:
        #         """Perform walk-forward validation on a model."""
        splits = self.split_time_series(df)
        all_predictions = []
        all_actuals = []
        directional_correct = 0
        total_predictions = 0

        for i, (train_df, test_df) in enumerate(splits):
            X_train = train_df[feature_columns]
            y_train = train_df[target_column]
            X_test = test_df[feature_columns]
            y_test = test_df[target_column]

            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                all_predictions.extend(y_pred)
                all_actuals.extend(y_test.values)

                for pred, actual in zip(y_pred, y_test.values):
                    if (pred > 0 and actual > 0) or (pred < 0 and actual < 0):
                        directional_correct += 1
                    total_predictions += 1
            except Exception as e:
                logger.error(f"Split {i} failed: {e}")

        all_predictions = np.array(all_predictions)
        all_actuals = np.array(all_actuals)

        metrics = {
            "directional_accuracy": directional_correct / total_predictions
            if total_predictions > 0
            else 0,
            "mape": mean_absolute_percentage_error(all_actuals, all_predictions),
            "mae": np.mean(np.abs(all_actuals - all_predictions)),
            "total_predictions": total_predictions,
        }
        return metrics
