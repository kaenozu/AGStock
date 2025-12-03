import pytest
import time
import pandas as pd
import numpy as np
from src.sector_rotation import SectorRotationEngine
from src.regime import RegimeDetector
from unittest.mock import patch

class TestPerformance:
    @pytest.fixture
    def mock_stock_data(self):
        dates = pd.date_range(start="2023-01-01", periods=100)
        data = {}
        for ticker in ["XLF", "XLE", "XLK", "XLV", "XLP", "XLI", "XLY", "XLU", "XLRE"]:
            df = pd.DataFrame({
                "Open": np.random.rand(100) * 100,
                "High": np.random.rand(100) * 100,
                "Low": np.random.rand(100) * 100,
                "Close": np.random.rand(100) * 100,
                "Volume": np.random.randint(1000, 10000, 100)
            }, index=dates)
            data[ticker] = df
        return data

    @pytest.fixture
    def mock_macro_data(self):
        dates = pd.date_range(start="2023-01-01", periods=100)
        data = {}
        for ticker in ["VIX", "SP500", "US10Y", "US02Y", "GOLD"]:
            df = pd.DataFrame({
                "Open": np.random.rand(100) * 100,
                "High": np.random.rand(100) * 100,
                "Low": np.random.rand(100) * 100,
                "Close": np.random.rand(100) * 100,
                "Volume": np.random.randint(1000, 10000, 100)
            }, index=dates)
            data[ticker] = df
        return data

    def test_sector_rotation_performance(self, mock_stock_data):
        """Test performance of SectorRotationEngine calculations."""
        with patch("src.sector_rotation.fetch_stock_data", return_value=mock_stock_data):
            engine = SectorRotationEngine()
            
            start_time = time.time()
            engine.fetch_sector_data()
            fetch_time = time.time() - start_time
            
            start_time = time.time()
            engine.calculate_sector_performance()
            calc_time = time.time() - start_time
            
            start_time = time.time()
            engine.calculate_optimal_weights(cycle="expansion")
            weight_time = time.time() - start_time
            
            print("\nSector Rotation Performance:")
            print(f"Fetch Time: {fetch_time:.4f}s")
            print(f"Calc Time: {calc_time:.4f}s")
            print(f"Weight Time: {weight_time:.4f}s")
            
            # Assertions for reasonable performance (adjust thresholds as needed)
            assert calc_time < 0.1, "Sector performance calculation too slow"
            assert weight_time < 0.05, "Weight calculation too slow"

    def test_regime_detection_performance(self, mock_macro_data):
        """Test performance of RegimeDetector."""
        detector = RegimeDetector()
        
        start_time = time.time()
        detector.fit(mock_macro_data)
        fit_time = time.time() - start_time
        
        start_time = time.time()
        detector.predict_current_regime(mock_macro_data)
        predict_time = time.time() - start_time
        
        print("\nRegime Detection Performance:")
        print(f"Fit Time: {fit_time:.4f}s")
        print(f"Predict Time: {predict_time:.4f}s")
        
        # Assertions
        assert fit_time < 10.0, "Regime fitting too slow"
        assert predict_time < 0.1, "Regime prediction too slow"
