import logging
import sys
import os

# Adjust path to find src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.council_avatars import AvatarCouncil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CouncilVerifier")

def test_council_votes():
    logger.info("Testing Council Vote Detail Exposure...")
    
    council = AvatarCouncil()
    logger.info(f"Initialized Council with {council.avatar_count} avatars.")
    
    ticker = "9984.T"
    data = {}
    
    result = council.hold_grand_assembly(ticker, data)
    
    # 1. Check Avg Score
    avg = result.get("avg_score")
    logger.info(f"Consensus Score: {avg:.2f}")
    
    # 2. Check Clusters
    clusters = result.get("clusters")
    logger.info(f"Clusters: {clusters}")
    
    # 3. Check All Votes (New Feature)
    all_votes = result.get("all_votes")
    if not all_votes:
        logger.error("❌ 'all_votes' key missing or empty!")
        return False
        
    logger.info(f"✅ 'all_votes' found. Count: {len(all_votes)}")
    
    # 4. Check Individual Vote Structure
    sample = all_votes[0]
    required_keys = ["id", "name", "score", "stance", "quote"]
    missing = [k for k in required_keys if k not in sample]
    
    if missing:
        logger.error(f"❌ Missing keys in vote object: {missing}")
        return False
        
    logger.info(f"✅ Vote Structure Verified: {sample}")
    
    logger.info("Council Hall Backend Verification SUCCESS")
    return True

if __name__ == "__main__":
    if test_council_votes():
        sys.exit(0)
    else:
        sys.exit(1)
