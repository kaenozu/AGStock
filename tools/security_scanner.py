"""
Security Scanner for AGStock
Scans code for potential security vulnerabilities.
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any

class SecurityScanner:
    """Scan code for security issues."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.vulnerabilities = []
    
    def scan_project(self) -> Dict[str, Any]:
        """Scan entire project for security issues."""
        print("🔒 Scanning for security vulnerabilities...")
        
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if "venv" not in str(f)]
        
        for file_path in python_files:
            self._scan_file(file_path)
        
        return {
            "files_scanned": len(python_files),
            "vulnerabilities": self.vulnerabilities,
            "severity_counts": self._count_by_severity()
        }
    
    def _scan_file(self, file_path: Path):
        """Scan a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for hardcoded secrets
                if self._check_hardcoded_secrets(line):
                    self.vulnerabilities.append({
                        "file": str(file_path),
                        "line": i,
                        "type": "HARDCODED_SECRET",
                        "severity": "CRITICAL",
                        "message": "Potential hardcoded secret detected",
                        "code": line.strip()[:80]
                    })
                
                # Check for SQL injection
                if self._check_sql_injection(line):
                    self.vulnerabilities.append({
                        "file": str(file_path),
                        "line": i,
                        "type": "SQL_INJECTION",
                        "severity": "HIGH",
                        "message": "Potential SQL injection vulnerability",
                        "code": line.strip()[:80]
                    })
                
                # Check for command injection
                if self._check_command_injection(line):
                    self.vulnerabilities.append({
                        "file": str(file_path),
                        "line": i,
                        "type": "COMMAND_INJECTION",
                        "severity": "HIGH",
                        "message": "Potential command injection vulnerability",
                        "code": line.strip()[:80]
                    })
                
                # Check for insecure random
                if 'random.random()' in line or 'random.randint' in line:
                    if 'crypto' not in content and 'security' in str(file_path).lower():
                        self.vulnerabilities.append({
                            "file": str(file_path),
                            "line": i,
                            "type": "WEAK_RANDOM",
                            "severity": "MEDIUM",
                            "message": "Use secrets module for cryptographic randomness",
                            "code": line.strip()[:80]
                        })
                
                # Check for eval/exec (but exclude legitimate library methods)
                if re.search(r'\b(eval|exec)\s*\(', line):
                    # Exclude legitimate uses
                    if not any(pattern in line for pattern in [
                        'model.eval()',  # PyTorch model evaluation mode
                        'df.eval(',      # pandas DataFrame.eval()
                        '.eval(',        # Method calls
                        '# eval',        # Comments
                        '"eval"',        # String literals
                        "'eval'"
                    ]):
                        self.vulnerabilities.append({
                            "file": str(file_path),
                            "line": i,
                            "type": "DANGEROUS_FUNCTION",
                            "severity": "HIGH",
                            "message": "Avoid using eval() or exec() with user input",
                            "code": line.strip()[:80]
                        })
        
        except Exception as e:
            pass
    
    def _check_hardcoded_secrets(self, line: str) -> bool:
        """Check for hardcoded secrets."""
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']{8,}["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']{20,}["\']',
            r'secret\s*=\s*["\'][^"\']{20,}["\']',
            r'token\s*=\s*["\'][^"\']{20,}["\']',
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Exclude common false positives
                if 'os.getenv' not in line and 'config' not in line.lower():
                    return True
        return False
    
    def _check_sql_injection(self, line: str) -> bool:
        """Check for SQL injection vulnerabilities."""
        if 'execute' in line or 'query' in line:
            # Check for string formatting in SQL
            if re.search(r'(execute|query)\s*\([^)]*[%+]', line):
                return True
            if re.search(r'(execute|query)\s*\([^)]*\.format\(', line):
                return True
        return False
    
    def _check_command_injection(self, line: str) -> bool:
        """Check for command injection vulnerabilities."""
        if 'os.system' in line or 'subprocess.call' in line:
            # Check if using user input
            if 'input' in line or 'request' in line:
                return True
        return False
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count vulnerabilities by severity."""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for vuln in self.vulnerabilities:
            severity = vuln.get("severity", "LOW")
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def generate_report(self, output_file: str = "security_report.md"):
        """Generate security report."""
        results = self.scan_project()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# AGStock Security Scan Report\n\n")
            f.write(f"**Generated**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📊 Summary\n\n")
            f.write(f"- **Files Scanned**: {results['files_scanned']}\n")
            f.write(f"- **Total Vulnerabilities**: {len(results['vulnerabilities'])}\n\n")
            
            f.write("## ⚠️ Vulnerabilities by Severity\n\n")
            for severity, count in results['severity_counts'].items():
                emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
                f.write(f"- {emoji.get(severity, '⚪')} **{severity}**: {count}\n")
            
            if results['vulnerabilities']:
                f.write("\n## 🔍 Detailed Findings\n\n")
                
                # Group by severity
                for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                    vulns = [v for v in results['vulnerabilities'] if v['severity'] == severity]
                    if vulns:
                        f.write(f"### {severity} Severity\n\n")
                        for vuln in vulns[:20]:  # Top 20 per severity
                            f.write(f"#### {vuln['type']}\n")
                            f.write(f"- **File**: `{vuln['file']}`\n")
                            f.write(f"- **Line**: {vuln['line']}\n")
                            f.write(f"- **Message**: {vuln['message']}\n")
                            f.write(f"- **Code**: `{vuln.get('code', 'N/A')}`\n\n")
            else:
                f.write("\n✅ No security vulnerabilities detected!\n")
        
        print(f"✅ Security report generated: {output_file}")
        return output_file


def main():
    """Run security scan."""
    print("="*70)
    print("  AGStock Security Scan")
    print("="*70)
    
    scanner = SecurityScanner()
    report_file = scanner.generate_report()
    
    results = scanner.scan_project()
    
    print(f"\n📊 Summary:")
    print(f"  Files scanned: {results['files_scanned']}")
    print(f"  Vulnerabilities found: {len(results['vulnerabilities'])}")
    
    for severity, count in results['severity_counts'].items():
        if count > 0:
            print(f"  {severity}: {count}")
    
    print(f"\n📄 Full report: {report_file}")
    
    # Return exit code based on critical/high issues
    critical_high = results['severity_counts']['CRITICAL'] + results['severity_counts']['HIGH']
    return 0 if critical_high == 0 else 1


if __name__ == "__main__":
    exit(main())
