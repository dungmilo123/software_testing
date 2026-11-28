#!/usr/bin/env bash
# Run the complete F002 Project #3 suite (Level 1 + Level 2 + NFR-02).
# Known-defect cases (TC-002-048/052/066) fail on purpose, so the script continues
# and prints the result files at the end instead of stopping on the first non-zero exit.
set -uo pipefail
cd "$(dirname "$0")"

export MOODLE_BASE_URL="${MOODLE_BASE_URL:-http://127.0.0.1:9501}"
PY="${PY:-.venv/bin/python}"

"$PY" run_tests.py setup/test_00_setup.py --tag setup_F002 || true
"$PY" run_tests.py level1/F002_assignment_settings --tag L1_F002 || true
"$PY" run_tests.py level2/F002_assignment_settings --tag L2_F002 || true
"$PY" run_tests.py nonfunctional/NFR-02_F002_xss --tag NFR02_F002 || true

echo
echo "Results:"
ls -1 results/L1_F002.json results/L2_F002.json results/NFR02_F002.json 2>/dev/null || true
