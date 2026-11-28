# Level 2 — F002 Assignment Settings

This folder is **data only**. The shared engine `../l2engine.py` reads:

| File | Purpose |
|---|---|
| `site.csv` | `base_url` (blank = `MOODLE_BASE_URL`) and named page (`course_page`). |
| `elements.csv` | Every input, button and message, with its locator and kind (`text`, `editor`, `select`, `checkbox`, `date`, `label`, `button`). No locator is written in a test class. |
| `flows.csv` | Reusable actions: open form, fill, save display/return, validate, cancel, UI, S1–S8 scenarios. |
| `testdata.csv` | 85 rows, one per `TC-002-*`; each row has the input values, `flow`, `expected_element`, `expected_result`, and `known_defect`. |
| `helpers.py` | Small page helpers that need dynamic data (course id, grouping G1, choicedropdown `Grant attempts`, assignment settings URL). |
| `test_l2_f002_assignment_settings.py` | One line: `build_test_class(...)`. |

Run:

```bash
cd /home/naman/miloo-software-testing
.venv/bin/python run_tests.py level2/F002_assignment_settings --tag L2_F002
```

The data mirrors the Level 1 grouping and keeps all 85 `tc_id` values. Visibility checks from the
Decision Table cases are exercised in Level 1; Level 2 verifies the primary saved/error outcome for
each case while demonstrating that URLs, locators and steps are fully externalised.
