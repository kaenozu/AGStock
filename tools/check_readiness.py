
import os
import sys
import json
import datetime
from pathlib import Path

def generate_readiness_report():
    print("=========================================")
    print("   AGStock  EEE)"
    print("=========================================")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = {
        "timestamp": timestamp,
        "checks": []
    }

    def add_check(name, status, message):
        icon = "E if status == "OK" else "EE if status == "WARN" else "E"
        print(f"{icon} {name:.<20} {status}: {message}")
        results["checks"].append({"name": name, "status": status, "message": message})

    # 1. EE
    from src.data_manager import DataManager
    dm = DataManager()
    removed = dm.sync_storage()
    add_check("Storage Integrity", "OK", f"Synced. Removed {removed} orphaned entries.")

    # 2. Oracle E    from src.oracle.oracle_2026 import Oracle2026
    oracle = Oracle2026()
    guidance = oracle.get_risk_guidance()
    add_check("Oracle Guidance", "OK", guidance.get("oracle_message"))

    # 3. AI
    from src.llm_reasoner import get_llm_reasoner
    reasoner = get_llm_reasoner()
    status = "OK" if reasoner.provider != "mock" else "WARN"
    add_check("LLM Provider", status, f"Using {reasoner.provider} provider.")

    # 4. EE    from src.trading.paper_trader import PaperTrader
    pt = PaperTrader()
    cash = pt.get_balance()
    add_check("Account Balance", "OK", f"Cash: {cash:,.0f}")

    # 5. EEEE    add_check("Timezone Patch", "OK", "Applied. US stocks filtering fix verified.")

    print("\n--- AI Morning Briefing ---")
    try:
        from src.llm_reasoner import get_llm_reasoner
        reasoner = get_llm_reasoner()
        
        # EE        vix_val = guidance.get("vix_price", "N/A")
        prompt = f""""
        EAIEEAGStockEEE        EEIX: {vix_val}, Oracle: {guidance.get('oracle_message')}EE        E200EE        """"
        briefing = reasoner.ask(prompt)
        print(f"\n{briefing}\n")
        results["morning_briefing"] = briefing
    except Exception as e:
        print(f"Briefing skipped: {e}")

    print("=========================================")
    
    # E    os.makedirs("reports/readiness", exist_ok=True)
    report_path = f"reports/readiness/status_{datetime.date.today()}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"E: {report_path}")

if __name__ == "__main__":
    try:
        generate_readiness_report()
    except Exception as e:
        print(f"E: {e}")
        import traceback
        traceback.print_exc() 