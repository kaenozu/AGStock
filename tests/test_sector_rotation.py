import numpy as np
import pandas as pd
import pytest

from src.sector_rotation import SectorRotationEngine


@pytest.fixture
def mock_sector_data():
    """Create mock sector ETF data."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")

    # Create data for XLK (Tech) - Strong performer
    xlk_data = pd.DataFrame({"Close": np.linspace(100, 120, 100) + np.random.normal(0, 2, 100)}, index=dates)

    # Create data for XLE (Energy) - Moderate performer
    xle_data = pd.DataFrame({"Close": np.linspace(80, 90, 100) + np.random.normal(0, 1.5, 100)}, index=dates)

    # Create data for XLU (Utilities) - Weak performer
    xlu_data = pd.DataFrame({"Close": np.linspace(60, 58, 100) + np.random.normal(0, 1, 100)}, index=dates)

    return {"XLK": xlk_data, "XLE": xle_data, "XLU": xlu_data}


def test_sector_rotation_initialization():
    """Test SectorRotationEngine can be initialized."""
    engine = SectorRotationEngine(lookback_period="1y")
    assert engine.lookback_period == "1y"
    assert len(engine.sector_tickers) > 0


def test_calculate_sector_performance(mock_sector_data, monkeypatch):
    """Test sector performance calculation."""
    engine = SectorRotationEngine()
    engine.sector_data = mock_sector_data

    performance = engine.calculate_sector_performance(period_days=30)

    assert isinstance(performance, dict)
    assert "XLK" in performance
    assert "XLE" in performance
    # XLK should have positive performance
    assert performance["XLK"] > 0


def test_get_top_sectors(mock_sector_data):
    """Test getting top performing sectors."""
    engine = SectorRotationEngine()
    engine.sector_data = mock_sector_data
    engine.calculate_sector_performance(period_days=30)

    top_sectors = engine.get_top_sectors(n=2)

    assert len(top_sectors) <= 2
    assert isinstance(top_sectors, list)
    # First should be the best performer (XLK or XLE based on mock data)
    assert top_sectors[0][1] > top_sectors[1][1]  # First has higher performance


def test_recommend_sectors_by_cycle():
    """Test sector recommendation by economic cycle."""
    engine = SectorRotationEngine()

    # Test different cycles
    early_recovery = engine.recommend_sectors_by_cycle("early_recovery")
    assert "XLF" in early_recovery  # Financial
    assert "XLK" in early_recovery  # Technology

    recession = engine.recommend_sectors_by_cycle("recession")
    assert "XLU" in recession  # Utilities
    assert "XLV" in recession  # Healthcare


def test_calculate_optimal_weights(mock_sector_data):
    """Test optimal weight calculation."""
    engine = SectorRotationEngine()
    engine.sector_data = mock_sector_data
    engine.calculate_sector_performance()

    weights = engine.calculate_optimal_weights(cycle="expansion", use_momentum=True)

    assert isinstance(weights, dict)
    # Weights should sum to 1.0
    assert abs(sum(weights.values()) - 1.0) < 0.01
    # All weights should be non-negative
    assert all(w >= 0 for w in weights.values())


def test_analyze_cycle_from_regime():
    """Test cycle analysis from regime ID."""
    engine = SectorRotationEngine()

    # Test regime mapping
    assert engine.analyze_cycle_from_regime(0) == "expansion"
    assert engine.analyze_cycle_from_regime(1) == "early_recession"
    assert engine.analyze_cycle_from_regime(2) == "recession"


def test_get_sector_heatmap_data(mock_sector_data):
    """Test heatmap data generation."""
    engine = SectorRotationEngine()
    engine.sector_data = mock_sector_data

    heatmap_df = engine.get_sector_heatmap_data(periods=[7, 30])

    assert not heatmap_df.empty
    assert "Sector" in heatmap_df.columns
    assert "7d" in heatmap_df.columns
    assert "30d" in heatmap_df.columns
