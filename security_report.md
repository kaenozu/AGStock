# AGStock Security Scan Report

**Generated**: 2026-01-08 14:02:26

## 📊 Summary

- **Files Scanned**: 822
- **Total Vulnerabilities**: 5

## ⚠️ Vulnerabilities by Severity

- 🔴 **CRITICAL**: 0
- 🟠 **HIGH**: 5
- 🟡 **MEDIUM**: 0
- 🟢 **LOW**: 0

## 🔍 Detailed Findings

### HIGH Severity

#### SQL_INJECTION
- **File**: `community_dashboard.py`
- **Line**: 101
- **Message**: Potential SQL injection vulnerability
- **Code**: `cursor.execute("UPDATE users SET reputation = reputation + 1 WHERE id = ?", (aid`

#### DANGEROUS_FUNCTION
- **File**: `main.py`
- **Line**: 321
- **Message**: Avoid using eval() or exec() with user input
- **Code**: `exec(import_stmt)`

#### DANGEROUS_FUNCTION
- **File**: `src\security\secure_data_manager.py`
- **Line**: 63
- **Message**: Avoid using eval() or exec() with user input
- **Code**: `r"exec(\\s|\\+)+(s|x)p\\w+",`

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

