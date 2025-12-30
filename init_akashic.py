import sys
import os
import logging

# Adjust path finding
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.database import init_db
from src.db.manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AkashicInitializer")

def main():
    logger.info("🏛️ Initializing The Akashic Records (Database)...")
    try:
        init_db()
        logger.info("✅ Database tables created successfully.")
        
        # Log an initial event
        db = DatabaseManager()
        db.log_event("DEPLOY", "System Initialized", "Akashic Records Created")
        db.close()
        logger.info("✅ Initial event logged.")
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
