"""
Meta Learner - メタ学習エンジン
AutoML、ハイパーパラメータ自動調整、新戦略の自動発見
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from typing import Dict, List, Tuple, Any
import optuna
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """モデル設定"""
    name: str
    model_class: Any
    param_space: Dict


class MetaLearner:
    """メタ学習クラス"""
    
    # モデル候補
    MODEL_CANDIDATES = [
        ModelConfig(
            name='RandomForest',
            model_class=RandomForestClassifier,
            param_space={
                'n_estimators': (50, 500),
                'max_depth': (3, 20),
                'min_samples_split': (2, 20),
                'min_samples_leaf': (1, 10)
            }
        ),
        ModelConfig(
            name='GradientBoosting',
            model_class=GradientBoostingClassifier,
            param_space={
                'n_estimators': (50, 300),
                'learning_rate': (0.01, 0.3),
                'max_depth': (3, 10),
                'subsample': (0.6, 1.0)
            }
        ),
        ModelConfig(
            name='LogisticRegression',
            model_class=LogisticRegression,
            param_space={
                'C': (0.001, 100.0),
                'penalty': ['l1', 'l2'],
                'solver': ['liblinear', 'saga']
            }
        )
    ]
    
    def __init__(self, n_trials: int = 50, cv_folds: int = 5):
        """
        Args:
            n_trials: Optunaの試行回数
            cv_folds: クロスバリデーションのフォールド数
        """
        self.n_trials = n_trials
        self.cv_folds = cv_folds
        self.best_model = None
        self.best_params = None
        self.best_score = -np.inf
    
    def auto_optimize(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        自動最適化
        
        Args:
            X: 特徴量
            y: ターゲット
            
        Returns:
            最適化結果
        """
        results = []
        
        for model_config in self.MODEL_CANDIDATES:
            print(f"Optimizing {model_config.name}...")
            
            # Optunaで最適化
            study = optuna.create_study(
                direction='maximize',
                sampler=optuna.samplers.TPESampler(seed=42)
            )
            
            def objective(trial):
                params = {}
                for param_name, param_range in model_config.param_space.items():
                    if isinstance(param_range, tuple):
                        if isinstance(param_range[0], int):
                            params[param_name] = trial.suggest_int(param_name, *param_range)
                        else:
                            params[param_name] = trial.suggest_float(param_name, *param_range)
                    elif isinstance(param_range, list):
                        params[param_name] = trial.suggest_categorical(param_name, param_range)
                
                model = model_config.model_class(**params, random_state=42)
                score = cross_val_score(model, X, y, cv=self.cv_folds, scoring='accuracy').mean()
                
                return score
            
            study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)
            
            # 結果記録
            results.append({
                'model': model_config.name,
                'best_score': study.best_value,
                'best_params': study.best_params
            })
            
            # 最良モデル更新
            if study.best_value > self.best_score:
                self.best_score = study.best_value
                self.best_params = study.best_params
                self.best_model = model_config.model_class(**study.best_params, random_state=42)
        
        # 最良モデルを訓練
        if self.best_model:
            self.best_model.fit(X, y)
        
        return {
            'best_model': self.best_model.__class__.__name__ if self.best_model else None,
            'best_score': self.best_score,
            'best_params': self.best_params,
            'all_results': results
        }
    
    def generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        特徴量自動生成
        
        Args:
            data: 価格データ
            
        Returns:
            特徴量DataFrame
        """
        features = pd.DataFrame(index=data.index)
        
        # 基本特徴量
        features['returns'] = data['Close'].pct_change()
        features['log_returns'] = np.log(data['Close'] / data['Close'].shift(1))
        
        # 移動平均
        for window in [5, 10, 20, 50]:
            features[f'sma_{window}'] = data['Close'].rolling(window).mean()
            features[f'ema_{window}'] = data['Close'].ewm(span=window).mean()
        
        # ボラティリティ
        for window in [5, 10, 20]:
            features[f'volatility_{window}'] = data['Close'].pct_change().rolling(window).std()
        
        # モメンタム
        for period in [5, 10, 20]:
            features[f'momentum_{period}'] = data['Close'] - data['Close'].shift(period)
            features[f'roc_{period}'] = (data['Close'] - data['Close'].shift(period)) / data['Close'].shift(period)
        
        # RSI
        for period in [14, 28]:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            features[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = data['Close'].ewm(span=12).mean()
        ema_26 = data['Close'].ewm(span=26).mean()
        features['macd'] = ema_12 - ema_26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']
        
        # ボリンジャーバンド
        for window in [20]:
            sma = data['Close'].rolling(window).mean()
            std = data['Close'].rolling(window).std()
            features[f'bb_upper_{window}'] = sma + (std * 2)
            features[f'bb_lower_{window}'] = sma - (std * 2)
            features[f'bb_width_{window}'] = (features[f'bb_upper_{window}'] - features[f'bb_lower_{window}']) / sma
        
        # 出来高特徴量
        if 'Volume' in data.columns:
            features['volume_sma_20'] = data['Volume'].rolling(20).mean()
            features['volume_ratio'] = data['Volume'] / features['volume_sma_20']
        
        return features.dropna()
    
    def discover_strategies(self, data: pd.DataFrame, 
                           min_sharpe: float = 1.0) -> List[Dict]:
        """
        新戦略の自動発見
        
        Args:
            data: 価格データ
            min_sharpe: 最小シャープレシオ
            
        Returns:
            発見された戦略リスト
        """
        # 特徴量生成
        features = self.generate_features(data)
        
        # ターゲット生成（翌日のリターンが正なら1）
        target = (data['Close'].shift(-1) / data['Close'] - 1 > 0).astype(int)
        target = target.loc[features.index]
        
        # 自動最適化
        result = self.auto_optimize(features, target)
        
        # 戦略評価
        if self.best_model:
            predictions = self.best_model.predict(features)
            
            # シグナル生成
            signals = pd.Series(0, index=features.index)
            signals[predictions == 1] = 1
            signals[predictions == 0] = -1
            
            # バックテスト
            returns = data['Close'].pct_change()
            strategy_returns = signals.shift(1) * returns
            
            # パフォーマンス計算
            cumulative_return = (1 + strategy_returns).cumprod()[-1] - 1
            sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
            
            if sharpe_ratio >= min_sharpe:
                return [{
                    'name': f'Auto_{self.best_model.__class__.__name__}',
                    'model': self.best_model,
                    'params': self.best_params,
                    'sharpe_ratio': sharpe_ratio,
                    'cumulative_return': cumulative_return,
                    'accuracy': result['best_score']
                }]
        
        return []


if __name__ == "__main__":
    # テスト
    from src.data_loader import fetch_stock_data
    
    # データ取得
    data_map = fetch_stock_data(["7203.T"], period="2y")
    data = data_map.get("7203.T")
    
    if data is not None and not data.empty:
        # メタ学習
        learner = MetaLearner(n_trials=20)
        
        # 戦略発見
        strategies = learner.discover_strategies(data, min_sharpe=0.5)
        
        print(f"発見された戦略: {len(strategies)}個")
        for strategy in strategies:
            print(f"  {strategy['name']}: Sharpe={strategy['sharpe_ratio']:.2f}, Return={strategy['cumulative_return']:.2%}")
