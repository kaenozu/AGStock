"""
Hyperparameter Optimization using Optuna
Automatically finds optimal hyperparameters for models.
"""

import logging
from typing import Dict, Any, Callable, Optional
import optuna
from optuna.samplers import TPESampler
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)


class HyperparameterOptimizer:
    """
    Optimizes model hyperparameters using Bayesian optimization (Optuna).
    """
    
    def __init__(
        self,
        n_trials: int = 100,
        timeout: Optional[int] = None,
        n_jobs: int = 1
    ):
        """
        Args:
            n_trials: Number of optimization trials
            timeout: Timeout in seconds
            n_jobs: Number of parallel jobs
        """
        self.n_trials = n_trials
        self.timeout = timeout
        self.n_jobs = n_jobs
        self.best_params = None
        self.best_score = None
        
    def optimize_lgbm(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        metric: str = 'neg_mean_squared_error'
    ) -> Dict[str, Any]:
        """
        Optimize LightGBM hyperparameters.
        
        Args:
            X: Training features
            y: Training targets
            metric: Scoring metric
        
        Returns:
            Best hyperparameters
        """
        logger.info("Optimizing LightGBM hyperparameters")
        
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'max_depth': trial.suggest_int('max_depth', 3, 12),
                'num_leaves': trial.suggest_int('num_leaves', 20, 100),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
                'subsample': trial.suggest_float('subsample', 0.5, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
            }
            
            from lightgbm import LGBMRegressor
            model = LGBMRegressor(**params, random_state=42, verbose=-1)
            
            # Cross-validation score
            scores = cross_val_score(
                model, X, y,
                cv=5,
                scoring=metric,
                n_jobs=1
            )
            
            return scores.mean()
        
        study = optuna.create_study(
            direction='maximize',
            sampler=TPESampler(seed=42)
        )
        
        study.optimize(
            objective,
            n_trials=self.n_trials,
            timeout=self.timeout,
            n_jobs=self.n_jobs,
            show_progress_bar=True
        )
        
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        logger.info(f"Best score: {self.best_score:.4f}")
        logger.info(f"Best params: {self.best_params}")
        
        return self.best_params
    
    def optimize_xgboost(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        metric: str = 'neg_mean_squared_error'
    ) -> Dict[str, Any]:
        """
        Optimize XGBoost hyperparameters.
        
        Args:
            X: Training features
            y: Training targets
            metric: Scoring metric
        
        Returns:
            Best hyperparameters
        """
        logger.info("Optimizing XGBoost hyperparameters")
        
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'max_depth': trial.suggest_int('max_depth', 3, 12),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'subsample': trial.suggest_float('subsample', 0.5, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
                'gamma': trial.suggest_float('gamma', 1e-8, 1.0, log=True),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
            }
            
            from xgboost import XGBRegressor
            model = XGBRegressor(**params, random_state=42, verbosity=0)
            
            scores = cross_val_score(
                model, X, y,
                cv=5,
                scoring=metric,
                n_jobs=1
            )
            
            return scores.mean()
        
        study = optuna.create_study(
            direction='maximize',
            sampler=TPESampler(seed=42)
        )
        
        study.optimize(
            objective,
            n_trials=self.n_trials,
            timeout=self.timeout,
            n_jobs=self.n_jobs,
            show_progress_bar=True
        )
        
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        logger.info(f"Best score: {self.best_score:.4f}")
        logger.info(f"Best params: {self.best_params}")
        
        return self.best_params
    
    def optimize_custom(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_builder: Callable,
        param_space: Dict[str, Any],
        metric: str = 'neg_mean_squared_error'
    ) -> Dict[str, Any]:
        """
        Optimize custom model hyperparameters.
        
        Args:
            X: Training features
            y: Training targets
            model_builder: Function that builds model from params
            param_space: Parameter search space
            metric: Scoring metric
        
        Returns:
            Best hyperparameters
        """
        logger.info("Optimizing custom model hyperparameters")
        
        def objective(trial):
            # Build params from search space
            params = {}
            for param_name, param_config in param_space.items():
                if param_config['type'] == 'int':
                    params[param_name] = trial.suggest_int(
                        param_name,
                        param_config['low'],
                        param_config['high']
                    )
                elif param_config['type'] == 'float':
                    params[param_name] = trial.suggest_float(
                        param_name,
                        param_config['low'],
                        param_config['high'],
                        log=param_config.get('log', False)
                    )
                elif param_config['type'] == 'categorical':
                    params[param_name] = trial.suggest_categorical(
                        param_name,
                        param_config['choices']
                    )
            
            # Build model
            model = model_builder(params)
            
            # Evaluate
            scores = cross_val_score(
                model, X, y,
                cv=5,
                scoring=metric,
                n_jobs=1
            )
            
            return scores.mean()
        
        study = optuna.create_study(
            direction='maximize',
            sampler=TPESampler(seed=42)
        )
        
        study.optimize(
            objective,
            n_trials=self.n_trials,
            timeout=self.timeout,
            n_jobs=self.n_jobs,
            show_progress_bar=True
        )
        
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        logger.info(f"Best score: {self.best_score:.4f}")
        logger.info(f"Best params: {self.best_params}")
        
        return self.best_params
