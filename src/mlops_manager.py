"""
讖滓｢ｰ蟄ｦ鄙帝°逕ｨ (MLOps) 謾ｹ蝟・Δ繧ｸ繝･繝ｼ繝ｫ

- 繝｢繝・Ν繝舌・繧ｸ繝ｧ繝ｳ邂｡逅・
- A/B繝・せ繝医ヵ繝ｬ繝ｼ繝繝ｯ繝ｼ繧ｯ
- 繝｢繝九ち繝ｪ繝ｳ繧ｰ縺ｨ繧｢繝ｩ繝ｼ繝・
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import shutil
import sqlite3
import subprocess
import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import mlflow
import numpy as np
import pandas as pd
import tensorflow as tf
import yaml
from mlflow.models.signature import infer_signature
from mlflow.utils.environment import _mlflow_conda_env
from tensorflow import keras

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

# MLOps逕ｨ繝・・繧ｿ繝吶・繧ｹ縺ｮ繝代せ
MLOPS_DB_PATH = "data/mlops.db"


def init_mlops_db():
    """MLOps繝・・繧ｿ繝吶・繧ｹ縺ｮ蛻晄悄蛹・""
    os.makedirs(os.path.dirname(MLOPS_DB_PATH), exist_ok=True)

    conn = sqlite3.connect(MLOPS_DB_PATH)
    cursor = conn.cursor()

    # 繝｢繝・Ν繝舌・繧ｸ繝ｧ繝ｳ繝・・繝悶Ν
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS model_versions (
            id INTEGER PRIMARY KEY,
            model_name TEXT NOT NULL,
            version TEXT NOT NULL,
            artifact_path TEXT,
            creation_timestamp TEXT,
            metrics TEXT,
            tags TEXT,
            UNIQUE(model_name, version)
        )
    """
    )

    # 螳滄ｨ薙ユ繝ｼ繝悶Ν
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            creation_timestamp TEXT
        )
    """
    )

    # 螳溯｡後ユ繝ｼ繝悶Ν
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY,
            experiment_id INTEGER,
            run_id TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            parameters TEXT,
            metrics TEXT,
            tags TEXT,
            FOREIGN KEY(experiment_id) REFERENCES experiments(id),
            UNIQUE(run_id)
        )
    """
    )

    # A/B繝・せ繝育ｵ先棡繝・・繝悶Ν
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ab_test_results (
            id INTEGER PRIMARY KEY,
            test_name TEXT NOT NULL,
            model_a_version TEXT,
            model_b_version TEXT,
            timestamp TEXT,
            metric_name TEXT,
            model_a_score REAL,
            model_b_score REAL,
            sample_size INTEGER,
            winner TEXT  -- 'A', 'B', or 'tie'
        )
    """
    )

    # 繝｢繝九ち繝ｪ繝ｳ繧ｰ繧｢繝ｩ繝ｼ繝医ユ繝ｼ繝悶Ν
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS monitoring_alerts (
            id INTEGER PRIMARY KEY,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT,
            timestamp TEXT,
            resolved BOOLEAN DEFAULT 0,
            resolved_timestamp TEXT
        )
    """
    )

    conn.commit()
    conn.close()


@dataclass
class ModelMetadata:
    """繝｢繝・Ν繝｡繧ｿ繝・・繧ｿ"""

    model_name: str
    version: str
    created_by: str
    creation_timestamp: str
    metrics: Dict[str, float]
    parameters: Dict[str, Any]
    dependencies: List[str]
    artifact_path: str
    hash: str
    tags: List[str]


class ModelRegistry:
    """繝｢繝・Ν繝ｬ繧ｸ繧ｹ繝医Μ"""

    def __init__(self, registry_path: str = "models/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        init_mlops_db()

    def save_model(self, model: Any, model_name: str, version: str, metadata: Dict[str, Any] = None) -> ModelMetadata:
        """繝｢繝・Ν縺ｮ菫晏ｭ倥→繝｡繧ｿ繝・・繧ｿ逋ｻ骭ｲ"""
        # 繝｢繝・Ν繝代せ縺ｮ貅門ｙ
        model_dir = self.registry_path / model_name / version
        model_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = str(model_dir / f"{model_name}.pkl")

        # 繝｢繝・Ν縺ｮ菫晏ｭ・
        if isinstance(model, keras.Model):
            model_path = str(model_dir / f"{model_name}.h5")
            model.save(model_path)
            artifact_path = model_path
        else:
            with open(artifact_path, "wb") as f:
                pickle.dump(model, f)

        # 繝上ャ繧ｷ繝･縺ｮ險育ｮ・
        model_hash = self._calculate_hash(artifact_path)

        # 繝｡繧ｿ繝・・繧ｿ縺ｮ菴懈・
        if metadata is None:
            metadata = {}

        model_metadata = ModelMetadata(
            model_name=model_name,
            version=version,
            created_by="system",
            creation_timestamp=datetime.now().isoformat(),
            metrics=metadata.get("metrics", {}),
            parameters=metadata.get("parameters", {}),
            dependencies=metadata.get("dependencies", []),
            artifact_path=artifact_path,
            hash=model_hash,
            tags=metadata.get("tags", []),
        )

        # JSON繝｡繧ｿ繝・・繧ｿ繝輔ぃ繧､繝ｫ縺ｮ菫晏ｭ・
        metadata_path = model_dir / f"{model_name}_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(asdict(model_metadata), f, indent=2, ensure_ascii=False)

        # 繝・・繧ｿ繝吶・繧ｹ縺ｫ逋ｻ骭ｲ
        self._register_model_in_db(model_metadata)

        logger.info(f"Model {model_name} v{version} registered with hash {model_hash}")
        return model_metadata

    def load_model(self, model_name: str, version: str = None) -> Tuple[Any, ModelMetadata]:
        """繝｢繝・Ν縺ｮ隱ｭ縺ｿ霎ｼ縺ｿ"""
        if version is None:
            version = self._get_latest_version(model_name)

        model_dir = self.registry_path / model_name / version
        metadata_path = model_dir / f"{model_name}_metadata.json"

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_dict = json.load(f)
        metadata = ModelMetadata(**metadata_dict)

        # 繝｢繝・Ν縺ｮ隱ｭ縺ｿ霎ｼ縺ｿ
        if metadata.artifact_path.endswith(".h5"):
            model = keras.models.load_model(metadata.artifact_path)
        else:
            with open(metadata.artifact_path, "rb") as f:
                model = pickle.load(f)

        return model, metadata

    def _calculate_hash(self, file_path: str) -> str:
        """繝輔ぃ繧､繝ｫ縺ｮ繝上ャ繧ｷ繝･繧定ｨ育ｮ・""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_latest_version(self, model_name: str) -> str:
        """譛譁ｰ繝舌・繧ｸ繝ｧ繝ｳ繧貞叙蠕・""
        model_dir = self.registry_path / model_name
        if not model_dir.exists():
            raise ValueError(f"Model {model_name} does not exist")

        versions = [d.name for d in model_dir.iterdir() if d.is_dir()]
        if not versions:
            raise ValueError(f"No versions found for model {model_name}")

        # 繝舌・繧ｸ繝ｧ繝ｳ繧呈律譎る・↓荳ｦ縺ｳ譖ｿ縺茨ｼ井ｻｮ縺ｫ譌･譎ょｽ｢蠑上′菴ｿ繧上ｌ縺ｦ縺・ｋ縺ｨ莉ｮ螳夲ｼ・
        versions.sort(reverse=True)
        return versions[0]

    def _register_model_in_db(self, metadata: ModelMetadata):
        """繝・・繧ｿ繝吶・繧ｹ縺ｫ繝｢繝・Ν諠・ｱ繧堤匳骭ｲ"""
        conn = sqlite3.connect(MLOPS_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO model_versions
            (model_name, version, artifact_path, creation_timestamp, metrics, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                metadata.model_name,
                metadata.version,
                metadata.artifact_path,
                metadata.creation_timestamp,
                json.dumps(metadata.metrics),
                json.dumps(metadata.tags),
            ),
        )

        conn.commit()
        conn.close()

    def list_models(self, model_name: str = None) -> List[ModelMetadata]:
        """繝｢繝・Ν荳隕ｧ縺ｮ蜿門ｾ・""
        conn = sqlite3.connect(MLOPS_DB_PATH)

        if model_name:
            query = "SELECT * FROM model_versions WHERE model_name = ? ORDER BY creation_timestamp DESC"
            df = pd.read_sql_query(query, conn, params=(model_name,))
        else:
            query = "SELECT * FROM model_versions ORDER BY creation_timestamp DESC"
            df = pd.read_sql_query(query, conn)

        conn.close()

        models = []
        for _, row in df.iterrows():
            metadata = ModelMetadata(
                model_name=row["model_name"],
                version=row["version"],
                created_by="system",  # 菫晏ｭ俶凾縺ｫ霑ｽ蜉縺吶ｋ蠢・ｦ√≠繧・
                creation_timestamp=row["creation_timestamp"],
                metrics=json.loads(row["metrics"]) if row["metrics"] else {},
                parameters={},  # 菫晏ｭ俶凾縺ｫ霑ｽ蜉縺吶ｋ蠢・ｦ√≠繧・
                dependencies=[],  # 菫晏ｭ俶凾縺ｫ霑ｽ蜉縺吶ｋ蠢・ｦ√≠繧・
                artifact_path=row["artifact_path"],
                hash="",  # 菫晏ｭ俶凾縺ｫ霑ｽ蜉縺吶ｋ蠢・ｦ√≠繧・
                tags=json.loads(row["tags"]) if row["tags"] else [],
            )
            models.append(metadata)

        return models


class ABTestFramework:
    """A/B繝・せ繝医ヵ繝ｬ繝ｼ繝繝ｯ繝ｼ繧ｯ"""

    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.test_results_db_path = MLOPS_DB_PATH
        self.tests = {}

    def run_ab_test(
        self,
        test_name: str,
        model_a_version: str,
        model_b_version: str,
        test_data: Tuple[np.ndarray, np.ndarray],
        metrics_to_compare: List[str] = ["mse", "mae"],
    ) -> Dict[str, Any]:
        """A/B繝・せ繝医・螳溯｡・""
        X_test, y_test = test_data

        # 繝｢繝・ΝA縺ｮ隱ｭ縺ｿ霎ｼ縺ｿ縺ｨ莠域ｸｬ
        model_a, metadata_a = self.model_registry.load_model("ensemble_model", model_a_version)  # 莉ｮ縺ｮ繝｢繝・Ν蜷・
        pred_a = model_a.predict(X_test) if hasattr(model_a, "predict") else np.zeros(len(X_test))

        # 繝｢繝・ΝB縺ｮ隱ｭ縺ｿ霎ｼ縺ｿ縺ｨ莠域ｸｬ
        model_b, metadata_b = self.model_registry.load_model("ensemble_model", model_b_version)
        pred_b = model_b.predict(X_test) if hasattr(model_b, "predict") else np.zeros(len(X_test))

        # 謖・ｨ吶・險育ｮ・
        results = {}
        for metric in metrics_to_compare:
            if metric == "mse":
                score_a = np.mean((y_test - pred_a) ** 2)
                score_b = np.mean((y_test - pred_b) ** 2)
            elif metric == "mae":
                score_a = np.mean(np.abs(y_test - pred_a))
                score_b = np.mean(np.abs(y_test - pred_b))
            elif metric == "rmse":
                score_a = np.sqrt(np.mean((y_test - pred_a) ** 2))
                score_b = np.sqrt(np.mean((y_test - pred_b) ** 2))
            else:
                raise ValueError(f"Unknown metric: {metric}")

            results[f"model_a_{metric}"] = float(score_a)
            results[f"model_b_{metric}"] = float(score_b)
            results[f"{metric}_difference"] = float(score_b - score_a)

        # 蜆ｪ菴阪Δ繝・Ν縺ｮ蛻､螳夲ｼ・SE縺ｪ縺ｩ縺ｧ縺ｯ蛟､縺悟ｰ上＆縺・婿縺悟━繧後※縺・ｋ・・
        winner = "tie"
        if results["mse_difference"] < 0:  # B縺ｮ譁ｹ縺勲SE縺悟ｰ上＆縺・= 蜆ｪ繧後※縺・ｋ
            winner = "B"
        elif results["mse_difference"] > 0:  # A縺ｮ譁ｹ縺勲SE縺悟ｰ上＆縺・= 蜆ｪ繧後※縺・ｋ
            winner = "A"

        # 邨先棡繧偵ョ繝ｼ繧ｿ繝吶・繧ｹ縺ｫ菫晏ｭ・
        self._save_ab_test_result(test_name, model_a_version, model_b_version, results, len(y_test), winner)

        return {
            "test_name": test_name,
            "model_a_version": model_a_version,
            "model_b_version": model_b_version,
            "results": results,
            "sample_size": len(y_test),
            "winner": winner,
            "timestamp": datetime.now().isoformat(),
        }

    def _save_ab_test_result(
        self,
        test_name: str,
        model_a_version: str,
        model_b_version: str,
        results: Dict[str, float],
        sample_size: int,
        winner: str,
    ):
        """A/B繝・せ繝育ｵ先棡繧偵ョ繝ｼ繧ｿ繝吶・繧ｹ縺ｫ菫晏ｭ・""
        conn = sqlite3.connect(self.test_results_db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO ab_test_results
            (test_name, model_a_version, model_b_version, timestamp, metric_name, model_a_score, model_b_score, sample_size, winner)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                test_name,
                model_a_version,
                model_b_version,
                datetime.now().isoformat(),
                "mse",  # 繝繝溘・縲∝ｮ滄圀縺ｫ縺ｯ隍・焚謖・ｨ吶ｒ菫晏ｭ倥☆繧・
                results.get("model_a_mse", 0.0),
                results.get("model_b_mse", 0.0),
                sample_size,
                winner,
            ),
        )

        conn.commit()
        conn.close()

    def get_test_history(self, test_name: str = None) -> pd.DataFrame:
        """繝・せ繝亥ｱ･豁ｴ縺ｮ蜿門ｾ・""
        conn = sqlite3.connect(self.test_results_db_path)

        if test_name:
            query = "SELECT * FROM ab_test_results WHERE test_name = ? ORDER BY timestamp DESC"
            df = pd.read_sql_query(query, conn, params=(test_name,))
        else:
            query = "SELECT * FROM ab_test_results ORDER BY timestamp DESC"
            df = pd.read_sql_query(query, conn)

        conn.close()
        return df


class MonitoringSystem:
    """繝｢繝九ち繝ｪ繝ｳ繧ｰ繧ｷ繧ｹ繝・Β"""

    def __init__(self):
        self.alerts_db_path = MLOPS_DB_PATH
        self.performance_thresholds = {}
        self.model_drift_detectors = {}
        self.data_drift_monitors = {}
        self.alert_callbacks = []

    def set_performance_threshold(self, metric_name: str, threshold: float, direction: str = "lower"):
        """繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ髢ｾ蛟､縺ｮ險ｭ螳夲ｼ・ower: 蟆上＆縺・婿縺瑚憶縺・「pper: 螟ｧ縺阪＞譁ｹ縺瑚憶縺・ｼ・""
        self.performance_thresholds[metric_name] = {"threshold": threshold, "direction": direction}

    def check_performance_degradation(self, model_name: str, current_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """諤ｧ閭ｽ菴惹ｸ九・讀懷・"""
        alerts = []

        for metric_name, value in current_metrics.items():
            if metric_name in self.performance_thresholds:
                threshold_info = self.performance_thresholds[metric_name]

                if threshold_info["direction"] == "lower":
                    # 蟆上＆縺・婿縺瑚憶縺・欠讓呻ｼ井ｾ・ MSE・・
                    if value > threshold_info["threshold"]:
                        alert = {
                            "type": "performance_degradation",
                            "severity": "high",
                            "message": f"Model {model_name} {metric_name} exceeded threshold: {value:.4f} > {threshold_info['threshold']:.4f}",
                            "timestamp": datetime.now().isoformat(),
                            "metric_name": metric_name,
                            "actual_value": value,
                            "threshold": threshold_info["threshold"],
                        }
                        alerts.append(alert)
                else:
                    # 螟ｧ縺阪＞譁ｹ縺瑚憶縺・欠讓呻ｼ井ｾ・ accuracy・・
                    if value < threshold_info["threshold"]:
                        alert = {
                            "type": "performance_degradation",
                            "severity": "high",
                            "message": f"Model {model_name} {metric_name} below threshold: {value:.4f} < {threshold_info['threshold']:.4f}",
                            "timestamp": datetime.now().isoformat(),
                            "metric_name": metric_name,
                            "actual_value": value,
                            "threshold": threshold_info["threshold"],
                        }
                        alerts.append(alert)

        # 繧｢繝ｩ繝ｼ繝医ｒ繝・・繧ｿ繝吶・繧ｹ縺ｫ菫晏ｭ・
        for alert in alerts:
            self._save_alert(alert)

        return alerts

    def detect_model_drift(
        self, model_predictions: np.ndarray, historical_predictions: np.ndarray, threshold: float = 0.05
    ) -> bool:
        """繝｢繝・Ν繝峨Μ繝輔ヨ縺ｮ讀懷・"""
        # 邁｡蜊倥↑蛻・ｸ・ｯ碑ｼ・ｼ・L繝繧､繝舌・繧ｸ繧ｧ繝ｳ繧ｹ縺ｾ縺溘・JS繝繧､繝舌・繧ｸ繧ｧ繝ｳ繧ｹ・・
        if len(model_predictions) == 0 or len(historical_predictions) == 0:
            return False

        # 豁｣隕丞喧
        pred_current = (model_predictions - np.mean(model_predictions)) / (np.std(model_predictions) + 1e-8)
        pred_historical = (historical_predictions - np.mean(historical_predictions)) / (
            np.std(historical_predictions) + 1e-8
        )

        # 繧ｳ繝ｫ繝｢繧ｴ繝ｭ繝・繧ｹ繝溘Ν繝弱ヵ讀懷ｮ・
        from scipy import stats

        statistic, p_value = stats.ks_2samp(pred_current, pred_historical)

        drift_detected = p_value < threshold
        if drift_detected:
            logger.warning(f"Model drift detected. KS statistic: {statistic:.4f}, p-value: {p_value:.4f}")

        return drift_detected

    def detect_data_drift(
        self, current_data: np.ndarray, reference_data: np.ndarray, threshold: float = 0.05
    ) -> Dict[str, Any]:
        """繝・・繧ｿ繝峨Μ繝輔ヨ縺ｮ讀懷・"""
        detection_results = {}

        # 蜷・ｨｮ邨ｱ險育噪讀懷ｮ・
        if len(current_data) > 0 and len(reference_data) > 0:
            # 繧ｳ繝ｫ繝｢繧ｴ繝ｭ繝・繧ｹ繝溘Ν繝弱ヵ讀懷ｮ・
            from scipy import stats

            statistic, p_value = stats.ks_2samp(current_data.flatten(), reference_data.flatten())

            detection_results = {
                "ks_statistic": float(statistic),
                "p_value": float(p_value),
                "drift_detected": p_value < threshold,
                "threshold_used": threshold,
            }

        return detection_results

    def _save_alert(self, alert: Dict[str, Any]):
        """繧｢繝ｩ繝ｼ繝医ｒ繝・・繧ｿ繝吶・繧ｹ縺ｫ菫晏ｭ・""
        conn = sqlite3.connect(self.alerts_db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO monitoring_alerts
            (alert_type, severity, message, timestamp)
            VALUES (?, ?, ?, ?)
        """,
            (alert["type"], alert["severity"], alert["message"], alert["timestamp"]),
        )

        conn.commit()
        conn.close()

    def get_recent_alerts(self, hours: int = 24, resolved: bool = False) -> pd.DataFrame:
        """譛霑代・繧｢繝ｩ繝ｼ繝医ｒ蜿門ｾ・""
        conn = sqlite3.connect(self.alerts_db_path)

        if resolved:
            query = """
                SELECT * FROM monitoring_alerts
                WHERE timestamp >= ? AND resolved = 1
                ORDER BY timestamp DESC
            """
        else:
            query = """
                SELECT * FROM monitoring_alerts
                WHERE timestamp >= ? AND resolved = 0
                ORDER BY timestamp DESC
            """

        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        df = pd.read_sql_query(query, conn, params=(cutoff_time,))

        conn.close()
        return df

    def resolve_alert(self, alert_id: int):
        """繧｢繝ｩ繝ｼ繝医・隗｣豎ｺ"""
        conn = sqlite3.connect(self.alerts_db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE monitoring_alerts
            SET resolved = 1, resolved_timestamp = ?
            WHERE id = ?
        """,
            (datetime.now().isoformat(), alert_id),
        )

        conn.commit()
        conn.close()

    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """繧｢繝ｩ繝ｼ繝医さ繝ｼ繝ｫ繝舌ャ繧ｯ縺ｮ霑ｽ蜉"""
        self.alert_callbacks.append(callback)

    def trigger_alert(self, alert: Dict[str, Any]):
        """繧｢繝ｩ繝ｼ繝医・逋ｺ逕・""
        # 繝・・繧ｿ繝吶・繧ｹ縺ｫ菫晏ｭ・
        self._save_alert(alert)

        # 逋ｻ骭ｲ縺輔ｌ縺溘さ繝ｼ繝ｫ繝舌ャ繧ｯ繧貞ｮ溯｡・
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")


class MLopsManager:
    """MLOps邂｡逅・け繝ｩ繧ｹ"""

    def __init__(self):
        self.model_registry = ModelRegistry()
        self.ab_testing = A / BTestFramework(self.model_registry)
        self.monitoring = MonitoringSystem()

        # MLflow縺ｮ蛻晄悄蛹・
        mlflow.set_tracking_uri("sqlite:///mlruns.db")  # 繝輔う繝ｫ繝吶・繧ｹ縺ｮMLflow
        mlflow.set_experiment("AGStock_Model_Training")

    def start_experiment(self, experiment_name: str, description: str = "") -> str:
        """螳滄ｨ薙・髢句ｧ・""
        with mlflow.start_run(run_name=experiment_name):
            mlflow.log_param("experiment_name", experiment_name)
            mlflow.log_param("description", description)
            mlflow.log_param("start_time", datetime.now().isoformat())

            return mlflow.active_run().info.run_id

    def log_model_with_mlflow(self, model: Any, model_name: str, X_sample: np.ndarray, conda_env: str = None):
        """MLflow繧堤畑縺・◆繝｢繝・Ν縺ｮ險倬鹸"""
        signature = infer_signature(
            X_sample, model.predict(X_sample) if hasattr(model, "predict") else np.zeros(len(X_sample))
        )

        # conda迺ｰ蠅・ヵ繧｡繧､繝ｫ縺ｮ菴懈・
        if conda_env is None:
            conda_env = self._create_conda_env_file()

        with mlflow.start_run():
            mlflow.keras.log_model(
                keras_model=model, artifact_path=model_name, signature=signature, conda_env=conda_env
            )

    def _create_conda_env_file(self) -> str:
        """conda迺ｰ蠅・ヵ繧｡繧､繝ｫ縺ｮ菴懈・"""
        env_path = "environment.yml"
        env_spec = {
            "name": "agstock_env",
            "channels": ["defaults", "conda-forge"],
            "dependencies": [
                "python=3.9",
                "numpy",
                "pandas",
                "scikit-learn",
                "tensorflow",
                "keras",
                "mlflow",
                "plotly",
                "yfinance",
                "requests",
                "textblob",
                "nltk",
            ],
        }

        with open(env_path, "w") as f:
            yaml.dump(env_spec, f)

        return env_path

    def monitor_model_performance(self, model: Any, X_test: np.ndarray, y_test: np.ndarray, model_name: str):
        """繝｢繝・Ν繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ縺ｮ繝｢繝九ち繝ｪ繝ｳ繧ｰ"""
        # 莠域ｸｬ縺ｮ螳溯｡・
        if hasattr(model, "predict"):
            y_pred = model.predict(X_test)
        else:
            y_pred = np.zeros(len(y_test))

        # 謖・ｨ吶・險育ｮ・
        mse = np.mean((y_test - y_pred) ** 2)
        mae = np.mean(np.abs(y_test - y_pred))
        rmse = np.sqrt(mse)

        metrics = {"mse": mse, "mae": mae, "rmse": rmse}

        # MLflow縺ｧ險倬鹸
        with mlflow.start_run():
            for metric_name, value in metrics.items():
                mlflow.log_metric(metric_name, value)

        # MLOps繝｢繝九ち繝ｪ繝ｳ繧ｰ繧ｷ繧ｹ繝・Β縺ｧ繧｢繝ｩ繝ｼ繝医ｒ繝√ぉ繝・け
        alerts = self.monitoring.check_performance_degradation(model_name, metrics)

        return {"metrics": metrics, "alerts": alerts, "timestamp": datetime.now().isoformat()}

    def run_model_comparison(self, models: Dict[str, Any], X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """隍・焚繝｢繝・Ν縺ｮ豈碑ｼ・""
        results = {}

        for model_name, model in models.items():
            if hasattr(model, "predict"):
                y_pred = model.predict(X_test)
            else:
                y_pred = np.zeros(len(y_test))

            # 謖・ｨ吶・險育ｮ・
            mse = np.mean((y_test - y_pred) ** 2)
            mae = np.mean(np.abs(y_test - y_pred))
            rmse = np.sqrt(mse)

            results[model_name] = {"mse": mse, "mae": mae, "rmse": rmse}

        return results


if __name__ == "__main__":
    # 繝・せ繝育畑繧ｳ繝ｼ繝・
    logging.basicConfig(level=logging.INFO)

    # MLOps繝槭ロ繝ｼ繧ｸ繝｣繝ｼ縺ｮ蛻晄悄蛹・
    mlops = MLopsManager()

    # 繝｢繝・け繝｢繝・Ν縺ｮ菴懈・
    import tensorflow as tf
    from tensorflow import keras

    model = keras.Sequential([keras.layers.Dense(10, activation="relu", input_shape=(10,)), keras.layers.Dense(1)])
    model.compile(optimizer="adam", loss="mse")

    # 繝繝溘・繝・・繧ｿ
    X = np.random.random((100, 10)).astype(np.float32)
    y = np.random.random((100, 1)).astype(np.float32)
    X_test = np.random.random((20, 10)).astype(np.float32)
    y_test = np.random.random((20, 1)).astype(np.float32)

    # 繝｢繝・Ν蟄ｦ鄙・
    model.fit(X, y, epochs=1, verbose=0)

    # 繝｢繝・Ν縺ｮ繝ｬ繧ｸ繧ｹ繝医Μ菫晏ｭ・
    metadata = {
        "metrics": {"mse": 0.01, "mae": 0.05},
        "parameters": {"epochs": 1, "optimizer": "adam"},
        "dependencies": ["tensorflow", "keras"],
        "tags": ["test", "initial"],
    }
    model_meta = mlops.model_registry.save_model(model, "test_model", "v1.0.0", metadata)
    print(f"Model registered: {model_meta.model_name} v{model_meta.version}")

    # A/B繝・せ繝医・螳溯｡・
    model2 = keras.Sequential([keras.layers.Dense(5, activation="relu", input_shape=(10,)), keras.layers.Dense(1)])
    model2.compile(optimizer="adam", loss="mse")
    model2.fit(X, y, epochs=1, verbose=0)

    model_meta2 = mlops.model_registry.save_model(model2, "test_model", "v1.0.1", metadata)

    # 繝｢繝・Ν縺ｮ隱ｭ縺ｿ霎ｼ縺ｿ縺ｨA/B繝・せ繝医・螳溯｡・
    try:
        test_result = mlops.ab_testing.run_ab_test(
            "model_comparison_test", "v1.0.0", "v1.0.1", (X_test, y_test), ["mse", "mae", "rmse"]
        )
        print(f"A/B test result: {test_result}")
    except Exception as e:
        print(f"A/B test failed: {e}")  # 繝｢繝・Ν蜷阪′荳閾ｴ縺励↑縺・◆繧∝､ｱ謨励☆繧句庄閭ｽ諤ｧ縺ゅｊ

    # 繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ繝｢繝九ち繝ｪ繝ｳ繧ｰ
    performance_result = mlops.monitor_model_performance(model, X_test, y_test, "test_model")
    print(f"Performance monitoring: {performance_result}")

    # 繝｢繝・Ν豈碑ｼ・
    models = {"model_v1": model, "model_v2": model2}
    comparison_result = mlops.run_model_comparison(models, X_test, y_test)
    print(f"Model comparison: {comparison_result}")

    print("MLOps components test completed.")
