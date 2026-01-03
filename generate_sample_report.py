from src.reporting.sovereign_report import SovereignReporter

def main():
    print("Generating Sovereign Report...")
    reporter = SovereignReporter()
    filename = reporter.save_report("reports/Sample_Sovereign_Report_2026.md")
    print(f"✅ Report generated: {filename}")
    
    with open(filename, "r", encoding="utf-8") as f:
        print("\n--- REPORT CONTENT BEGIN ---\n")
        print(f.read())
        print("\n--- REPORT CONTENT END ---\n")

if __name__ == "__main__":
    main()
