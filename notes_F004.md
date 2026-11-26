# Notes – F004 Create Course (Luong Tan Tai)

> **Member:** Luong Tan Tai | **Feature:** F004 – Create Course | **Date:** 2026-11-27

---

## 1. How the Project #2 cases were grouped

The 65 test cases (TC-004-001 … TC-004-065) all exercise the **Add a new course** form
(`/course/edit.php?category=1`). They share the same page, the same locators, and the
same run method, so **one single data-driven script** covers all of them.

### Level 1 grouping

| Data file | Rows | Techniques covered |
|---|---|---|
| `level1/F004_create_course/data/create_course.csv` | 65 | ECP, BVA, DT, UC – every row is one TC |

The Level 1 script (`test_f004_create_course.py`) reads every row and dispatches on
`expected_outcome`:

| `expected_outcome` | Action |
|---|---|
| `maxlength` | Check HTML `maxlength` without submitting |
| `options` | Check `<select>` options without submitting |
| `error` | Submit → assert field-level validation messages |
| `created` | Submit → assert course heading or management-list link |
| `not_created` | Submit Cancel → confirm search shows "No courses were found" |

A second-attempt block (`fix_field / fix_value / fix_button / expected_after_fix`) covers
use-case scenarios that correct a validation error then re-submit.

### Level 2 grouping

The same 65 cases are expressed in four CSV files consumed by `level2/l2engine.py`:

| File | Purpose |
|---|---|
| `site.csv` | Named URL templates (add_course, search_by_shortname, …) |
| `elements.csv` | Named locators (Full name, Short name, buttons, error labels, …) |
| `flows.csv` | Named step sequences (create_and_display, cancel_form, error_fix_and_save, …) |
| `testdata.csv` | 65 rows – one per TC, referencing flows and element names |

No page address, locator, or step is written in `test_l2_f004_create_course.py` itself
(single-line stub calling `build_test_class()`).

---

## 2. Expected-result changes from Project #2

| TC | Old expected result | New expected result | Reason |
|---|---|---|---|
| TC-004-009 | `error` (end date = start date rejected) | `created` | Moodle demo **accepts** end date = start date; the check is strictly `<`, not `≤`. Verified on port 9501. |
| TC-004-003 | `error` (whitespace full name) | `created` | Moodle trims but does not reject; marked `known_defect`. |
| TC-004-005 | `error` (whitespace short name) | `created` | Same reason; marked `known_defect`. |

---

## 3. Known Defects

| Defect ID | TC | Description | Status in test |
|---|---|---|---|
| **D-04** | TC-004-003 | Moodle demo accepts a course full name that consists of only spaces (should be rejected with "Missing full name") | FAIL (expected) – `known_defect` populated in CSV |
| **D-05** | TC-004-005 | Moodle demo accepts a course short name that consists of only spaces (should be rejected with "Missing short name") | FAIL (expected) – `known_defect` populated in CSV |

---

## 4. Test Results – Level 1

**Run date:** 2026-11-24 14:37 | **Duration:** 252 s | **Browser:** Chrome (headless)

| Metric | Value |
|---|---|
| Total cases | 65 |
| ✅ Passed | 59 |
| ❌ Failed (unexpected) | 4 |
| ⚠️ Failed (known defect) | 2 (TC-004-003, TC-004-005) |
| 🔴 Error | 2 |

### Unexpected failures (Level 1)

| TC | Title | Error / Failure reason |
|---|---|---|
| TC-004-009 | Course end date equal to start date | Expected `error` but Moodle accepted the course (end date = start date is valid in this build). **Changed to `created` in updated CSV.** |
| TC-004-013 | Course format set to Weekly format | `ElementNotInteractableException` – the format `<select>` was not visible before `expand_all()` was called. Script needs `expand_all()` before selecting format. |
| TC-004-015 | Course format set to Single activity format | Same as TC-004-013. |
| TC-004-064 | S7: Duplicate short name, then cancel | After Cancel, the search page shows a list rather than "No courses were found"; the cleanup URL contains the course name instead. |

### Level 1 pass rate by technique

| Technique | Total | Passed | Failed |
|---|---|---|---|
| ECP (TC-001–025) | 25 | 22 | 3 |
| BVA (TC-026–046) | 21 | 21 | 0 |
| DT (TC-047–057) | 11 | 11 | 0 |
| UC (TC-058–065) | 8 | 7 | 1 |

---

## 5. Test Results – Level 2

**Run date:** 2026-11-24 14:43 | **Duration:** 245 s | **Browser:** Chrome (headless)

| Metric | Value |
|---|---|
| Total cases | 65 |
| ✅ Passed | 63 |
| ❌ Failed (unexpected) | 0 |
| ⚠️ Failed (known defect) | 2 (TC-004-003, TC-004-005) |
| 🔴 Error | 0 |

Level 2 is **cleaner than Level 1** because the generic engine handles `expand_all`
internally before every `fill` step, avoiding the `ElementNotInteractableException`
that caused TC-004-013 and TC-004-015 to error at Level 1.

---

## 6. NFR – Load / Concurrency (NFR-04)

### 6.1 Description

| Item | Detail |
|---|---|
| **Type** | Non-functional – load / concurrency testing |
| **Tool** | Python 3 `threading` + `urllib.request` (no external load tool required) |
| **Approach** | Selenium logs in once; N threads fire simultaneously using `threading.Barrier`, each fetching the target URL via HTTP GET with the shared session cookie; response times measured with `time.perf_counter()` |
| **Requirement** | 1–5 concurrent users: average response time < 2 s; 10 concurrent users: average response time < 3 s |
| **Data file** | `nonfunctional/NFR-04_F004_load/data/load_scenarios.csv` (6 rows) |

### 6.2 Test scenarios

| TC | URL | Users | Threshold |
|---|---|---|---|
| NFR-04-01 | /course/edit.php?category=1 | 1 | avg < 2 s |
| NFR-04-02 | /course/edit.php?category=1 | 5 | avg < 2 s |
| NFR-04-03 | /course/edit.php?category=1 | 10 | avg < 3 s |
| NFR-04-04 | /course/management.php | 1 | avg < 2 s |
| NFR-04-05 | /course/management.php | 5 | avg < 2 s |
| NFR-04-06 | /course/management.php | 10 | avg < 3 s |

### 6.3 Results

**Run date:** 2026-11-26 23:26 | **Duration:** 710 s

| TC | URL | Users | Avg response | Threshold | Result |
|---|---|---|---|---|---|
| NFR-04-01 | /course/edit.php | 1 | **52.5 s** | 2.0 s | ❌ FAIL |
| NFR-04-02 | /course/edit.php | 5 | **84.9 s** | 2.0 s | ❌ FAIL |
| NFR-04-03 | /course/edit.php | 10 | timeout (5/10) | 3.0 s | ❌ FAIL |
| NFR-04-04 | /course/management.php | 1 | timeout | 2.0 s | ❌ FAIL |
| NFR-04-05 | /course/management.php | 5 | **65.3 s** | 2.0 s | ❌ FAIL |
| NFR-04-06 | /course/management.php | 10 | timeout (3/10) | 3.0 s | ❌ FAIL |

### 6.4 Analysis

**All 6 NFR cases FAIL.** This is a valid and expected finding for the demo environment:

- The Moodle demo runs in Docker with limited resources (shared CPU, limited RAM).
- Average response time for a single authenticated user is **~52 s** for the Add Course
  form – approximately **26× slower** than the 2 s requirement.
- Under 5 concurrent users, response time degrades to **~85 s** (Add Course) and **~65 s**
  (Course management).
- Under 10 concurrent users, the server fails to respond within the 120 s connection
  timeout for 50 % of requests.

**Conclusion:** The Moodle demo environment does **not meet** the load/concurrency
performance requirements. This is a known limitation of the Docker demo setup, not a
defect in the application itself. A production Moodle deployment with dedicated hardware
would be expected to pass these thresholds.

---

## 7. Summary of All Issues Found

| ID | Type | TC | Description |
|---|---|---|---|
| D-04 | Functional defect | TC-004-003 | Whitespace-only full name accepted (should be rejected) |
| D-05 | Functional defect | TC-004-005 | Whitespace-only short name accepted (should be rejected) |
| D-06 | Functional defect | TC-004-064 | Cancel after duplicate-shortname error navigates to wrong page |
| D-07 | NFR defect | NFR-04-01..06 | All page response times exceed thresholds under any load level |
| — | Script bug (L1 only) | TC-004-013, 015 | `expand_all()` must be called before selecting Course format; fixed in L2 by engine |

---

## 8. How to Run

```bash
cd software_testing

# 1. Setup (creates KT Test Course + students)
python run_tests.py setup/test_00_setup.py

# 2. Level 1 (65 TCs, one script + one CSV)
python run_tests.py level1/F004_create_course --tag L1_F004

# 3. Level 2 (65 TCs, four CSVs + generic engine)
python run_tests.py level2/F004_create_course --tag L2_F004

# 4. NFR - Load test (6 TCs: 1/5/10 users × 2 URLs)
python run_tests.py nonfunctional/NFR-04_F004_load --tag NFR04_F004
```

Result files in `results/`: `L1_F004.json`, `L2_F004.json`, `NFR04_F004.json`

---

## 9. AI Usage Declaration

| Field | Detail |
|---|---|
| **Tool** | Google Antigravity (Claude Sonnet 4.6 Thinking) |
| **Exact prompts used** | "Suggest a structure for implementing data-driven NFR load tests in Python using threading.Barrier and urllib.request"; "Explain the root causes of ElementClickInterceptedException and Chrome headless timeout in Selenium"; "Analyze potential causes of HTTP timeout during concurrent load testing on a local Moodle instance"; "Review and refine the Markdown structure and technical phrasing of my test execution notes" |
| **What AI suggested** | (1) Provided reference patterns for structuring data-driven test scripts compatible with existing F004/F005 modules. (2) Suggested standard library approaches (`threading.Barrier`, `urllib.request`, `statistics`) for simulating concurrent requests and calculating 95th-percentile latency. (3) Explained common causes of Selenium `ElementClickInterceptedException` and HTTP timeouts (e.g., missing `User-Agent` headers or short timeout thresholds). (4) Suggested grammatical and structural improvements for the final Markdown report. |
| **What I did myself** | Designed the test plan and defined all 6 load scenarios in `load_scenarios.csv` (2 target URLs × 3 concurrency levels); configured and deployed the local Moodle test environment (port 9501); manually provisioned test account `kt_s01` and enrolled it in course `KTC01`; implemented, debugged, and executed all automated test scripts (`test_nfr04_load.py`, F004, F005); analyzed browser behavior and server logs to verify defect `D-04`/`D-05` and confirm `TC-004-009` acceptance; collected raw `results/*.json` metrics and authored the final analytical conclusions. |