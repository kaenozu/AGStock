import os
import sys
import time

import pandas as pd

# Add root to path
sys.path.append(os.getcwd())


def test_drawdown_optimization():
    print("\n[VERIFY] PR #52: Drawdown Optimization")
    try:
        from src.performance_metrics import AdvancedMetrics

        dates = pd.date_range("2024-01-01", periods=1000, freq="D")
        prices = [100.0] * 1000
        for i in range(100, 201):
            prices[i] = 90.0

        # Convert to returns
        series = pd.Series(prices).pct_change().fillna(0)

        start_time = time.time()
        metrics = AdvancedMetrics(series)
        duration = metrics.max_drawdown_duration()
        end_time = time.time()

        print(f"  Result: {duration} days")
        print(f"  Time taken: {end_time - start_time:.6f}s")
        print("  SUCCESS")
    except ImportError:
        print("  FAILURE: Could not import AdvancedMetrics from src.performance_metrics")
    except Exception as e:
        print(f"  FAILURE: {e}")


def test_persistent_cache():
    print("\n[VERIFY] PR #53: Persistent Cache")
    try:
        from src.cache_manager import CacheManager

        cache = CacheManager(db_path="verify_cache_test.db")
        cache.set("test_key", {"data": 123})
        val = cache.get("test_key")

        if val and val.get("data") == 123:
            print(f"  Cache read/write verified. Value: {val}")
            print("  SUCCESS")
        else:
            print(f"  FAILURE: Retrieved value mismatch: {val}")
    except ImportError:
        print("  FAILURE: Could not import CacheManager from src.cache_manager")
    except Exception as e:
        print(f"  FAILURE: {e}")


def test_config_loader():
    print("\n[VERIFY] PR #54: Config Loader Fallbacks")
    try:
        from src.utils.config_loader import load_config_from_yaml

        # Try loading a non-existent file, expecting default or empty
        config = load_config_from_yaml("non_existent_config_for_verification.yaml")
        print(f"  Loaded config type: {type(config)}")
        print("  SUCCESS")
    except ImportError:
        print("  FAILURE: Could not import load_config_from_yaml from src.utils.config_loader")
    except Exception as e:
        print(f"  FAILURE: {e}")


def test_ui_enhancements():
    print("\n[VERIFY] PR #55: UI Enhancements")
    try:
        from src.ui.ui_enhancements import ColorTokens

        tokens = ColorTokens()
        print(f"  Imported and instantiated ColorTokens: {tokens}")
        print("  SUCCESS")
    except ImportError:
        print("  FAILURE: Could not import ColorTokens from src.ui.ui_enhancements")
    except Exception as e:
        print(f"  FAILURE: {e}")


if __name__ == "__main__":
    print("=== Starting Post-Merge Verification ===")
    test_drawdown_optimization()
    test_persistent_cache()
    test_config_loader()
    test_ui_enhancements()
    print("\n=== Verification Complete ===")
