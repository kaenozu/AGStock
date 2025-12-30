
import logging
import traceback
import sys
import os

# Ensure src is in path
sys.path.append(os.getcwd())

from src.config import settings
from src.data_manager import DataManager
from src.evolution_engine import EvolutionEngine

logger = logging.getLogger("SystemVerification")
logging.basicConfig(level=logging.INFO)

def verify_all_enhancements():
    logger.info("🔍 Verifying System Enhancements...")
    results = {}

    # 1. Config Verification
    try:
        logger.info("1. Creating Config Instance...")
        # Accessing settings forces load and validation
        db_path = settings.system.db_path
        logger.info(f"✅ Config loaded. DB Path: {db_path}")
        results["Config"] = "PASS"
    except Exception as e:
        logger.error(f"❌ Config failed: {e}")
        results["Config"] = "FAIL"

    # 2. Hybrid Data Manager (Parquet)
    try:
        logger.info("2. Testing Hybrid Data Layer...")
        dm = DataManager()
        
        # Save test
        import pandas as pd
        import numpy as np
        dates = pd.date_range(end=pd.Timestamp.now(), periods=10)
        df = pd.DataFrame(np.random.randn(10, 5), index=dates, columns=["Open", "High", "Low", "Close", "Volume"])
        dm.save_data(df, "TEST_TICKER")
        
        # Load test
        loaded_df = dm.load_data("TEST_TICKER")
        if not loaded_df.empty and len(loaded_df) == 10:
            logger.info("✅ Parquet Save/Load successful.")
            results["DataLayer"] = "PASS"
        else:
            logger.error("❌ Data load mismatch.")
            results["DataLayer"] = "FAIL"
            
    except Exception as e:
        logger.error(f"❌ Data Layer failed: {e}")
        traceback.print_exc()
        results["DataLayer"] = "FAIL"

    # 3. Evolution Engine
    try:
        logger.info("3. Testing Evolution Engine...")
        engine = EvolutionEngine(population_size=5)
        # Mock data map to avoid network calls
        import pandas as pd
        import numpy as np
        dates = pd.date_range(end=pd.Timestamp.now(), periods=100) # Need enough points for ma
        df = pd.DataFrame(np.random.randn(100, 5) + 100, index=dates, columns=["Open", "High", "Low", "Close", "Volume"])
        
        mock_data = {"TEST": df}
        engine.population = [] # reset
        engine.initialize_population()
        engine.evolve(mock_data)
        
        if engine.generation == 1:
            logger.info("✅ Evolution generation complete.")
            results["Evolution"] = "PASS"
        else:
             results["Evolution"] = "FAIL"
             
    except Exception as e:
        logger.error(f"❌ Evolution Engine failed: {e}")
        traceback.print_exc()
        results["Evolution"] = "FAIL"

    logger.info("="*30)
    logger.info("FINAL RESULTS:")
    for k, v in results.items():
        logger.info(f"{k}: {v}")
    
    if all(v == "PASS" for v in results.values()):
        print("ALL_SYSTEMS_GO")
    else:
        print("SYSTEM_VERIFICATION_FAILED")

if __name__ == "__main__":
    verify_all_enhancements()
