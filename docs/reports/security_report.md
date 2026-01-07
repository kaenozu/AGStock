# AGStock Security Scan Report

**Generated**: 2025-12-29 17:44:28

## 📊 Summary

- **Files Scanned**: 676
- **Total Vulnerabilities**: 2

## ⚠️ Vulnerabilities by Severity

- 🔴 **CRITICAL**: 0
- 🟠 **HIGH**: 2
- 🟡 **MEDIUM**: 0
- 🟢 **LOW**: 0

## 🔍 Detailed Findings

### HIGH Severity

#### DANGEROUS_FUNCTION
- **File**: `tools\security_scanner.py`
- **Line**: 86
- **Message**: Avoid using eval() or exec() with user input
- **Code**: `# Check for eval/exec (but exclude legitimate library methods)`

#### DANGEROUS_FUNCTION
- **File**: `tools\security_scanner.py`
- **Line**: 102
- **Message**: Avoid using eval() or exec() with user input
- **Code**: `"message": "Avoid using eval() or exec() with user input",`

