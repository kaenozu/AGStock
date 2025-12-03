import unittest
import os
import shutil
import pandas as pd
import numpy as np
from src.ml_pipeline import ModelRegistry, ContinuousLearner
from src.strategies import DeepLearningStrategy

class TestMLPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_models"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        self.registry = ModelRegistry(base_dir=self.test_dir)
        self.learner = ContinuousLearner(self.registry)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_registry_save_load(self):
        model_name = "TestModel"
        dummy_model = {"a": 1}
        metrics = {"accuracy": 0.9}
        
        version = self.registry.register_model(model_name, dummy_model, metrics)
        self.assertIsNotNone(version)
        
        loaded_model, meta = self.registry.get_latest_model(model_name)
        self.assertEqual(loaded_model["a"], 1)
        self.assertEqual(meta["metrics"]["accuracy"], 0.9)

    def test_continuous_learner_mock_train(self):
        # Mock training function
        def mock_train(data):
            return {"model": "dummy"}, {"accuracy": 0.85}
            
        data = pd.DataFrame({"A": [1, 2, 3]})
        result = self.learner.train_and_evaluate("MockStrategy", mock_train, data)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("version", result)
        
        # Verify it's in registry
        latest = self.registry.get_latest_model("MockStrategy")
        self.assertIsNotNone(latest)

    def test_deep_learning_strategy_integration(self):
        # Create dummy data for DL strategy
        dates = pd.date_range(start='2020-01-01', periods=400)
        df = pd.DataFrame({
            'Close': np.random.rand(400) * 100,
            'Volume': np.random.rand(400) * 1000,
            'Open': np.random.rand(400) * 100,
            'High': np.random.rand(400) * 100,
            'Low': np.random.rand(400) * 100
        }, index=dates)
        
        strategy = DeepLearningStrategy(lookback=10, epochs=1, batch_size=2, trend_period=10, train_window_days=50, predict_window_days=10)
        
        # Test train method
        model, metrics = strategy.train(df)
        self.assertIsNotNone(model)
        self.assertIn("loss", metrics)
        
        # Register model
        version = self.registry.register_model("Deep Learning (LSTM)", model, metrics)
        self.assertIsNotNone(version)
        
        # Load strategy with model path
        _, meta = self.registry.get_latest_model("Deep Learning (LSTM)")
        loaded_strategy = DeepLearningStrategy(model_path=meta["path"])
        self.assertIsNotNone(loaded_strategy.model)

if __name__ == '__main__':
    unittest.main()
