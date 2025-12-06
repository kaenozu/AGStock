import unittest
import numpy as np
import pandas as pd
from src.kelly_criterion import KellyCriterion


class TestKellyCriterion(unittest.TestCase):
    """Tests for Kelly Criterion class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.kelly = KellyCriterion(half_kelly=False, max_position_size=0.5)
        self.half_kelly = KellyCriterion(half_kelly=True, max_position_size=0.5)
    
    def test_initialization(self):
        """Test KellyCriterion initialization"""
        self.assertIsNotNone(self.kelly)
        self.assertFalse(self.kelly.half_kelly)
        self.assertEqual(self.kelly.max_position_size, 0.5)
    
    def test_calculate_size_basic(self):
        """Test basic Kelly calculation"""
        # win_rate=0.6, win_loss_ratio=2 -> kelly = (0.6*2 - 0.4)/2 = 0.4
        result = self.kelly.calculate_size(win_rate=0.6, win_loss_ratio=2.0)
        self.assertAlmostEqual(result, 0.4, places=2)
    
    def test_calculate_size_half_kelly(self):
        """Test half Kelly calculation"""
        result = self.half_kelly.calculate_size(win_rate=0.6, win_loss_ratio=2.0)
        # Should be half of full Kelly
        self.assertAlmostEqual(result, 0.2, places=2)
    
    def test_calculate_size_negative_edge(self):
        """Test Kelly returns 0 for negative edge"""
        result = self.kelly.calculate_size(win_rate=0.4, win_loss_ratio=1.0)
        self.assertEqual(result, 0.0)
    
    def test_calculate_size_zero_ratio(self):
        """Test Kelly with zero win/loss ratio"""
        result = self.kelly.calculate_size(win_rate=0.6, win_loss_ratio=0.0)
        self.assertEqual(result, 0.0)
    
    def test_calculate_size_max_cap(self):
        """Test that position size is capped at max"""
        # This should give large Kelly, but capped at 0.5
        result = self.kelly.calculate_size(win_rate=0.8, win_loss_ratio=5.0)
        self.assertLessEqual(result, 0.5)
    
    def test_calculate_from_history_wins_only(self):
        """Test calculation from historical returns - all wins"""
        returns = pd.Series([0.01, 0.02, 0.03, 0.015, 0.025])
        result = self.kelly.calculate_from_history(returns)
        # All wins -> should return max position size
        self.assertEqual(result, 0.5)
    
    def test_calculate_from_history_losses_only(self):
        """Test calculation from historical returns - all losses"""
        returns = pd.Series([-0.01, -0.02, -0.03])
        result = self.kelly.calculate_from_history(returns)
        # All losses -> should return 0
        self.assertEqual(result, 0.0)
    
    def test_calculate_from_history_mixed(self):
        """Test calculation from mixed returns"""
        returns = pd.Series([0.02, -0.01, 0.03, -0.01, 0.02, -0.015])
        result = self.kelly.calculate_from_history(returns)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 0.5)
    
    def test_calculate_from_history_empty(self):
        """Test with empty returns"""
        returns = pd.Series([])
        result = self.kelly.calculate_from_history(returns)
        self.assertEqual(result, 0.0)


if __name__ == '__main__':
    unittest.main()
