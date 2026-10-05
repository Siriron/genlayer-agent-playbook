#!/usr/bin/env bash
# audit_all.sh — run every mechanical pre-handoff check on a contract.
# Usage: bash scripts/audit_all.sh contracts/my_contract.py
set -u
C="${1:?usage: audit_all.sh <contract.py>}"
rc=0
python3 "$(dirname "$0")/audit_contract.py" "$C" || rc=1
if command -v genvm-lint >/dev/null 2>&1; then
  echo "=== genvm-lint check ==="; genvm-lint check "$C" || rc=1
else
  echo "genvm-lint not installed: pip install genvm-linter  (first run downloads ~310 MB; needs network)"; rc=1
fi
if [ -d tests ]; then
  echo "=== pytest (direct mode) ==="; pytest tests -q -p no:cacheprovider || rc=1
else
  echo "no tests/ directory — repository-only review requires direct-mode tests (templates/direct-mode-test-template.py)"; rc=1
fi
exit $rc
