# Project #3 – Data-driven automation testing and non-functional testing (CC01_G07)

Moodle LMS 5.1.8 (MuTMS demo, same site as Project #2), Python 3 + Selenium 4 + unittest.
The scripts started from Katalon Recorder's "Python 2 (WebDriver + unittest)" export structure
(setUp/tearDown, `verificationErrors`, soft `verify*` checks) and were ported to Python 3 / Selenium 4.

```
common/            shared code: config, WebDriver factory, data reader (.csv/.xlsx), data-driven decorator,
                   Moodle page helper, base TestCase
setup/             fixture (port of 00-setup / 99-cleanup), data-driven: students.csv, course.csv, cleanup.csv
level1/F00X_*/     Level 1: one script per feature, test data + expected results in data/*.csv
level2/l2engine.py Level 2 engine (generic); level2/F00X_*/ only data: site.csv, elements.csv, flows.csv, testdata.csv
nonfunctional/     NFR-0X_*: one folder per non-functional requirement (script + data)
run_tests.py       runner: one line per test case ID in results/<tag>.csv/.json, screenshots of failures
```

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt     # Chrome must be installed
export MOODLE_BASE_URL=http://127.0.0.1:9501                          # site under test (default)
.venv/bin/python run_tests.py setup/test_00_setup.py                   # once: users kt_s01..10, course KTC01
.venv/bin/python run_tests.py level1/F005_auto_create_groups --tag L1_F005
.venv/bin/python run_tests.py level2/F005_auto_create_groups --tag L2_F005
.venv/bin/python run_tests.py nonfunctional/NFR-05_F005_accessibility --tag NFR05_F005
.venv/bin/python run_tests.py setup/test_99_cleanup.py                 # at the very end
```

Options: `HEADLESS=0` shows the browser, `BROWSER=firefox`, `-k TC_005_03` runs only matching cases.
A case listed in the `known_defect` column fails on purpose (it checks the specified behaviour that Moodle
violates); the runner prints those separately from unexpected failures.

## Data cell notation (all data files)

| Cell | Meaning |
|---|---|
| (blank) | keep the form default, do not touch the field |
| `{{EMPTY}}` | clear the field |
| `{{N*1333}}` | the text `N` repeated 1333 times (`{{ *3}}` = three spaces) |
| `check1 \| check2` | several checks in one Level 1 `expected_result` cell |
