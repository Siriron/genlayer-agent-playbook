#!/usr/bin/env python3
"""
check_limits.py — count portal-form text against the real limits (never estimate; docs/knowledge/10, 17).

Usage:
  python scripts/check_limits.py oneliner  "text"        # max 180
  python scripts/check_limits.py description "text"      # max 1000
  python scripts/check_limits.py outcome "text"          # max 500
  python scripts/check_limits.py contract-description "text"   # max 1000 (Contracts track)
  python scripts/check_limits.py github-description "text"     # GitHub repo description max 350
Reads from stdin if the text argument is omitted.
"""
import sys

LIMITS = {"oneliner": 180, "description": 1000, "outcome": 500,
          "contract-description": 1000, "github-description": 350}

if len(sys.argv) < 2 or sys.argv[1] not in LIMITS:
    print(__doc__); sys.exit(2)
field = sys.argv[1]
text = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read().rstrip("\n")
n = len(text)
lim = LIMITS[field]
print(f"{field}: {n}/{lim} characters — {'OK' if n <= lim else 'OVER by ' + str(n - lim)}")
sys.exit(0 if n <= lim else 1)
