import sys
import os
import importlib
import logging

# Adjust path to find src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UI_Verifier")

def verify_ui_imports():
    """
    Verifies that all modules referenced in the new app.py structure can be imported.
    This simulates the app startup without launching the web server.
    """
    modules_to_check = [
        "src.ui.sidebar",
        "src.ui.briefing_panel",
        "src.simple_dashboard",
        "src.ui.mission_control",
        "src.ui.performance_analyst",
        "src.ui.council_hall",
        "src.agents.committee", # Dependency for Council
        "src.ui.divine_sight",
        "src.ui.ai_hub",
        "src.ui.trading_hub",
        "src.ui.portfolio_panel",
        "src.ui.dojo",
        "src.ui.strategy_arena",
        "src.ui.lab_hub",
        "src.realtime.streamer"
    ]

    logger.info("=== Starting UI Structure Verification ===")
    
    failed = []
    
    for mod_name in modules_to_check:
        try:
            logger.info(f"Checking {mod_name}...")
            importlib.import_module(mod_name)
            logger.info(f"✅ {mod_name} imported successfully.")
        except ImportError as e:
            logger.error(f"❌ Failed to import {mod_name}: {e}")
            failed.append(mod_name)
        except Exception as e:
            logger.error(f"❌ Error importing {mod_name}: {e}")
            failed.append(mod_name)

    if failed:
        logger.error(f"Verification FAILED. {len(failed)} modules broken.")
        return False
    
    logger.info("=== UI Structure Verification SUCCESS ===")
    return True

if __name__ == "__main__":
    if verify_ui_imports():
        sys.exit(0)
    else:
        sys.exit(1)
