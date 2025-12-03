import os
import json
import logging
import joblib
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelRegistry:
    """
    Manages model artifacts and metadata.
    Stores models in a local directory structure.
    """
    def __init__(self, base_dir: str = "models"):
        self.base_dir = base_dir
        self.registry_file = os.path.join(base_dir, "registry.json")
        self._ensure_dir()
        self.registry = self._load_registry()

    def _ensure_dir(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def _load_registry(self) -> Dict[str, Any]:
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                return {"models": {}}
        return {"models": {}}

    def _save_registry(self):
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.registry, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def register_model(self, model_name: str, model_artifact: Any, metrics: Dict[str, float], version_tag: str = None) -> str:
        """
        Saves a model artifact and updates the registry.
        Returns the version ID.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_id = version_tag or f"v_{timestamp}"
        
        model_dir = os.path.join(self.base_dir, model_name)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
            
        artifact_path = os.path.join(model_dir, f"{version_id}.joblib")
        
        try:
            joblib.dump(model_artifact, artifact_path)
            
            if model_name not in self.registry["models"]:
                self.registry["models"][model_name] = []
            
            metadata = {
                "version": version_id,
                "timestamp": timestamp,
                "path": artifact_path,
                "metrics": metrics
            }
            
            self.registry["models"][model_name].append(metadata)
            self._save_registry()
            
            logger.info(f"Registered model {model_name} version {version_id}")
            return version_id
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            return None

    def get_latest_model(self, model_name: str) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        Retrieves the latest version of a model and its metadata.
        """
        if model_name not in self.registry["models"] or not self.registry["models"][model_name]:
            return None
        
        # Sort by timestamp descending
        versions = sorted(self.registry["models"][model_name], key=lambda x: x["timestamp"], reverse=True)
        latest_meta = versions[0]
        
        try:
            model = joblib.load(latest_meta["path"])
            return model, latest_meta
        except Exception as e:
            logger.error(f"Failed to load model artifact: {e}")
            return None

    def get_best_model(self, model_name: str, metric: str = "accuracy") -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        Retrieves the best performing model based on a metric.
        Assumes higher is better for the metric.
        """
        if model_name not in self.registry["models"] or not self.registry["models"][model_name]:
            return None
            
        versions = self.registry["models"][model_name]
        # Filter versions that have the metric
        valid_versions = [v for v in versions if metric in v["metrics"]]
        
        if not valid_versions:
            return self.get_latest_model(model_name)
            
        best_meta = max(valid_versions, key=lambda x: x["metrics"][metric])
        
        try:
            model = joblib.load(best_meta["path"])
            return model, best_meta
        except Exception as e:
            logger.error(f"Failed to load model artifact: {e}")
            return None

class ContinuousLearner:
    """
    Orchestrates the training and evaluation of models.
    """
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def train_and_evaluate(self, model_name: str, trainer_func, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs the training function and registers the model.
        
        trainer_func: A function that takes data and returns (model, metrics)
        """
        logger.info(f"Starting training for {model_name}...")
        try:
            model, metrics = trainer_func(data)
            version_id = self.registry.register_model(model_name, model, metrics)
            
            return {
                "status": "success",
                "version": version_id,
                "metrics": metrics
            }
        except Exception as e:
            logger.error(f"Training failed for {model_name}: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
