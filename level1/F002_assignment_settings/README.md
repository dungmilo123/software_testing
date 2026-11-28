# Level 1 — F002 Assignment Settings

Data-driven Selenium test (Python 3 + unittest) for **all 85** Project #2 cases.

| File | Cases |
|---|---|
| `data/create.csv` | Valid saves, defaults, ECP field combinations, BVA valid boundaries, DT valid rules |
| `data/validation.csv` | Invalid values and the three known defects |
| `data/ui.csv` | Decision Table dynamic visibility/enabled dependencies |
| `data/scenarios.csv` | Use-Case S1–S8 |
| `test_f002_assignment_settings.py` | One `@data_driven` class; URLs/locators are in this script (Level 1) |

Run:

```bash
cd /home/naman/miloo-software-testing
.venv/bin/python run_tests.py level1/F002_assignment_settings --tag L1_F002
```

Known defects (`TC-002-048`, `TC-002-052`, `TC-002-066`) are marked in the `known_defect` column and
fail on purpose; the runner lists them separately from unexpected failures.
