# """軽量なデータドリフト監視ユーティリティ."""
import logging
from dataclasses import dataclass
from typing import Dict
import numpy as np
import pandas as pd
logger = logging.getLogger(__name__)
def _population_stability_index(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    if expected.size == 0 or actual.size == 0:
        return 0.0
        try:
            pass
            expected_perc = np.where(expected_counts == 0, 1e-6, expected_counts / expected.size)
            psi = np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc))
            logger.info("Reference window too small for drift baseline: %s rows", numeric.shape[0])
            logger.info("No drift reference set; treating as no drift.")
            return DriftResult(False, {})
            current = df.select_dtypes(include=[np.number])
            return DriftResult(False, {})
            drift_cols: Dict[str, Dict[str, float]] = {}
            try:
                pass
                continue
                psi = _population_stability_index(ref_col, cur_col)
                try:
                    ks_stat = float(stats.ks_2samp(ref_col, cur_col).statistic)
                except Exception:
                    ks_stat = 0.0
                if psi > self.psi_threshold or ks_stat > self.ks_threshold:
                    pass
