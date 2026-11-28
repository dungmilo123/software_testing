# F002 — Assignment Settings (Naman Chahar, 2560173)

Project #3 hand-off: Level 1, Level 2 and NFR-02 security for the Project #2 Feature 002 test cases.

## 1. Scope and grouping

All **85** Project #2 cases (`TC-002-001`..`TC-002-085`) are covered, one data row per case.

| Level | Folder | Grouping |
|---|---|---|
| Level 1 | `level1/F002_assignment_settings/` | `data/create.csv` (valid saves), `data/validation.csv` (invalid/defect cases), `data/ui.csv` (Decision Table UI dependencies), `data/scenarios.csv` (Use-Case S1–S8) |
| Level 2 | `level2/F002_assignment_settings/` | `site.csv`, `elements.csv`, `flows.csv`, `testdata.csv`, `helpers.py`; all locators/URLs/steps are data, the generic engine is unchanged |
| NFR-02 | `nonfunctional/NFR-02_F002_xss/` | `data/xss_cases.csv` + Selenium script |

The case grouping mirrors `level1/F005_auto_create_groups`: cases that differ only in data share one CSV and one `@data_driven` script. Every row keeps its original `tc_id` for traceability.

## 2. Changed / calibrated expected results

These were validated against the live Moodle 5.1.8 instance (MuTMS, `http://127.0.0.1:9501`) rather than copied blindly from the Project #2 workbook:

| Case | Project #2 expectation | Live result | Treatment |
|---|---|---|---|
| `TC-002-048` | Word limit `-1` rejected | **Accepted and saved** | `known_defect` D-01; the case fails on purpose |
| `TC-002-052` | Word limit `1000000` rejected | **Accepted and saved** past `maxlength=6` | `known_defect` D-03; the case fails on purpose |
| `TC-002-066` | Grade to pass `-1` rejected | **Accepted and saved** | `known_defect` D-02; the case fails on purpose |
| `TC-002-010` | Time limit field present | Field only exists when *Enable timed assignments* is on | `setUpClass` enables the site setting before the run |
| `TC-002-034` | Grade penalties field present | Grade-penalty module feature is **not enabled** on this Moodle build | Saved check is skipped with an explicit log note; the case still verifies creation |

Exact live messages used in the data files:

- empty name: `You must supply a value here.`
- 1334-character name: `Maximum of 1333 characters`
- due date <= allow-from: `Due date must be after the allow submissions from date.`
- cut-off earlier than due: `Cut-off date cannot be earlier than the due date.`
- grading due earlier than due: `Remind me to grade by date cannot be earlier than the due date.`
- max grade out of range: `Invalid grade value. This must be an integer between 1 and 100` (under `fgroup_id_error_grade`)
- grade to pass above max: `The grade to pass can not be greater than the maximum possible grade 100`
- non-numeric word limit / grade to pass: `You must enter a number here.`
- anonymous + until-pass: `Reopen until pass option is incompatible with anonymous submissions, because the grades are not released to the gradebook until the student identities are revealed.`

## 3. NFR-02 — Security: XSS / HTML injection

- **Type:** non-functional security testing (stored XSS / HTML injection).
- **Requirement:** user HTML in Assignment **name**, **description** and **activity instructions** must be sanitised; scripts and event handlers must never execute on the view or settings pages.
- **Approach:** Selenium saves each payload, watches for a JavaScript dialog **and** a `window.__xss` execution marker, then inspects the rendered `region-main` DOM for a raw `<script>...XSSNFR02` element or an `onerror` handler containing the marker.
- **Tool:** Python 3 + Selenium 4 + unittest, headless Chromium.
- **Data:** `data/xss_cases.csv` (8 payloads: `<script>`, `<img onerror>`, attribute breakout, encoded text, safe markup + script).
- **Evidence:** `results/NFR-02_xss_NFR-02-0X.json`.

### Finding — NFR-02-D-01 (stored XSS in Description)

The suite found that the Assignment **Description** (`introeditor`, PARAM_RAW) accepts a raw
`<script>` payload and executes it when the Assignment view page is rendered. The **name** field
(PARAM_TEXT) and the **Activity instructions** field are sanitised correctly in the same run.

- Cases: `NFR-02-03` (`<script>...`) and `NFR-02-07` (`<b>...</b><script>...`).
- Evidence: `results/NFR-02_xss_NFR-02-03.json`, `results/NFR-02_xss_NFR-02-07.json`
  (`alert_fired`, `executed_marker`, `raw_script_found`).
- Scope: payload is entered by an admin/teacher in the settings form; it is a stored XSS sink for
  privileged users and should still be sanitised before rendering.
- Treatment: recorded as a **known defect** in the NFR data, so the NFR run reports it separately
  from unexpected failures.

## 4. How to run

```bash
cd /home/naman/miloo-software-testing
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export MOODLE_BASE_URL=http://127.0.0.1:9501
.venv/bin/python run_tests.py setup/test_00_setup.py --tag setup
.venv/bin/python run_tests.py level1/F002_assignment_settings --tag L1_F002
.venv/bin/python run_tests.py level2/F002_assignment_settings --tag L2_F002
.venv/bin/python run_tests.py nonfunctional/NFR-02_F002_xss --tag NFR02_F002
.venv/bin/python run_tests.py setup/test_99_cleanup.py --tag cleanup
```

`HEADLESS=0` shows the browser; `-k TC_002_0xx` runs a single case.

## 5. Results

Full-run logs: `results/L1_F002.json`, `results/L2_F002.json`, `results/NFR02_F002.json`.

| Suite | Cases | Pass | Fail (known defect) | Unexpected |
|---|---:|---:|---:|---:|
| Level 1 | 85 | 82 | 3 (`TC-002-048`, `TC-002-052`, `TC-002-066`) | 0 |
| Level 2 | 85 | 82 | 3 (`TC-002-048`, `TC-002-052`, `TC-002-066`) | 0 |
| NFR-02 | 8 | 6 | 2 (`NFR-02-03`, `NFR-02-07` — NFR-02-D-01) | 0 |

The three Level 1/2 failures are the known Moodle defects: word limit `-1`, word limit `1000000`, and
grade to pass `-1`. They are expected to fail because the tests assert the **required** (safe) behaviour.

## 6. Notes / limitations

- Level 1 keeps the original Project #2 expected results where the live behaviour matches; the three known defects remain intentional failures and are listed in the result JSON's `failed_known_defect`.
- Level 1 uses a class-level teardown to delete all assignments created by the suite; each case uses a unique assignment name, so a defect that saves an invalid value cannot mask later cases.
- Level 2 is a thin data layer over the shared `level2/l2engine.py`; it does not duplicate the engine. Every URL, locator and flow step comes from CSV.
- The `G1` grouping/group needed by `TC-002-025` and `TC-002-085` is created by a helper and removed after the run.
- `TC-002-034` cannot verify the saved Grade penalties value on this build because the grade-penalty feature is disabled; enabling it is a site configuration change outside the test scope.
- NFR-02-D-01 is a real finding: the Description field executes a raw `<script>` payload. It is marked `known_defect` so the NFR suite reports it separately from unexpected failures; it should be included in the security section of the group report.
- No test changes default user passwords or tests login/logout.
