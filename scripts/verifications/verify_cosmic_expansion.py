import os
import sys
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CosmicVerifier")

def verify_cosmic_expansion():
    logger.info("🌌 Starting Cosmic Expansion Verification...")
    
    # 1. Verify Assets (Egregore)
    logger.info("--- Phase 17: Egregore Assets ---")
    avatars = ["bull.png", "bear.png", "neutral.png"]
    missing = []
    for a in avatars:
        path = f"assets/avatars/{a}"
        if os.path.exists(path):
            logger.info(f"✅ Found avatar: {path}")
        else:
            logger.error(f"❌ Missing avatar: {path}")
            missing.append(a)
    
    if not missing:
        logger.info("✅ All Egregore assets present.")
    
    # 2. Verify Quantum Ledger (Phase 16)
    logger.info("--- Phase 16: Quantum Soul ---")
    try:
        from src.core.quantum_ledger import QuantumLedger
        ledger = QuantumLedger("data/test_ledger.json")
        ledger.add_block({"test": "Cosmic Hello"})
        latest = ledger.get_latest_block()
        logger.info(f"✅ Quantum Ledger Initialized. Latest Hash: {latest.hash[:10]}...")
        
        # Verify Persistence
        ledger2 = QuantumLedger("data/test_ledger.json")
        if ledger2.get_latest_block().hash == latest.hash:
            logger.info("✅ Persistence Verified.")
        else:
            logger.error("❌ Persistence Failed.")
            
        # Clean up
        os.remove("data/test_ledger.json")
    except Exception as e:
        logger.error(f"❌ Quantum Ledger Failed: {e}")

    # 3. Verify Hologram Import (Phase 15)
    logger.info("--- Phase 15: Holographic Universe ---")
    try:
        from src.ui.hologram import render_hologram_deck
        logger.info("✅ Hologram UI Module Imported Successfully.")
    except Exception as e:
        logger.error(f"❌ Hologram Import Failed: {e}")

    # 4. Verify Egregore Import
    try:
        from src.ui.egregore import render_sidebar_egregore
        logger.info("✅ Egregore UI Module Imported Successfully.")
    except Exception as e:
        logger.error(f"❌ Egregore Import Failed: {e}")

    # 5. Verify Oracle Link Import (Phase 18)
    try:
        from src.ui.oracle_link import render_oracle_chat
        logger.info("✅ Oracle Link UI Module Imported Successfully.")
    except Exception as e:
        logger.error(f"❌ Oracle Link Import Failed: {e}")

    logger.info("🎉 Cosmic Verification Complete.")

if __name__ == "__main__":
    verify_cosmic_expansion()
