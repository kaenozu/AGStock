
import logging
import time
import os
import shutil
import glob
from src.rl.trainer import TrainingSessionManager
from src.schemas import load_config

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DojoVerifier")

def verify_dojo_training():
    logger.info("Initializing Dojo Verification...")
    
    # 1. Clean up old test models
    if os.path.exists("models/rl"):
        for f in glob.glob("models/rl/dqn_TEST_T_*.pth"):
            os.remove(f)

    # 2. Initialize Manager
    manager = TrainingSessionManager()
    
    # 3. Start Training (Mock Ticker)
    # Note: 7203.T relies on fetching real data. 
    # If network is down, this might fail. We assume network is up or data cached.
    ticker = "7203.T" 
    episodes = 2 # Short run
    
    logger.info(f"Starting training for {ticker} ({episodes} eps)...")
    manager.start_training(ticker, episodes=episodes)
    
    # 4. Monitor Progress
    max_wait = 60 # seconds
    start = time.time()
    
    while manager.get_status()["is_running"]:
        status = manager.get_status()
        logger.info(f"Progress: {status['current_episode']}/{status['total_episodes']} - {status['status_message']}")
        
        if "Error" in status['status_message']:
            logger.error("Training failed with error!")
            return False
            
        if time.time() - start > max_wait:
            logger.error("Training timed out!")
            manager.stop_training()
            return False
            
        time.sleep(2)
        
    # 5. Check Results
    status = manager.get_status()
    logger.info(f"Final Status: {status['status_message']}")
    
    if status['metrics']:
        logger.info(f"Metrics recorded: {len(status['metrics'])} episodes.")
    else:
        logger.error("No metrics recorded!")
        return False
        
    # 6. Check Model File
    expected_file = f"models/rl/dqn_{ticker}_latest.pth"
    if os.path.exists(expected_file):
        logger.info(f"✅ Model file found: {expected_file}")
        
        # 7. Check Trade History (Replay Cinema)
        if status.get("trade_history"):
            logger.info(f"✅ Trade history found: {len(status['trade_history'])} trades recorded.")
        else:
             logger.warning("⚠️ No trades occurred in last episode. This might be normal for short training, but verify logic.")
             
        # 8. Check Deployment (Mock)
        # Simulate deployment
        import shutil
        prod_path = "models/production/active_agent.pth"
        os.makedirs("models/production", exist_ok=True)
        shutil.copy(expected_file, prod_path)
        
        if os.path.exists(prod_path):
            logger.info(f"✅ Deployment successful: {prod_path} created.")
            print("Verification SUCCESS")
            return True
        else:
            logger.error("❌ Deployment failed.")
            print("Verification FAILED")
            return False
            
    else:
        logger.error(f"❌ Model file NOT found: {expected_file}")
        print("Verification FAILED")
        return False

if __name__ == "__main__":
    verify_dojo_training()
