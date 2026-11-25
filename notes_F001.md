# Project #3 Notes — Feature 001: Quiz Settings (`F001`)

| Metadata | Value |
|---|---|
| Course | Software Testing (CO3015) — HCMC University of Technology (VNUHCM) |
| Group | CC01_G07 |
| Student / Member | Tran Ngoc Thoai (2353147) — Student 1 |
| Feature Tested | Feature 001: Quiz Settings (`mod/quiz` Settings, `course/modedit.php?add=quiz`) |
| System Under Test | Moodle LMS 5.1.8 (Build: 20261005) — MuTMS Demo (`http://127.0.0.1:9501`) |
| Test Stack | Python 3.11.9 + Selenium 4.54.0 + `unittest` (headless Chrome) |
| Shared Fixture | `setup/test_00_setup.py` (`11/11` passed in `38 s`, course `KTC01`) |

---

## 1. Level 1 Data-Driven Automation (`level1/F001_quiz_settings/`)

All **81 test cases** (`TC-001-001` .. `TC-001-081`) from Project #2 were ported into `level1/F001_quiz_settings/test_f001_quiz_settings.py` using `@data_driven(...)` and grouped by execution pattern into 4 CSV files under `level1/F001_quiz_settings/data/`:

| Data File | Cases | Range / Scope | Description |
|---|---:|---|---|
| `data/create_valid.csv` | 43 | `TC-001-001, 004, 005, 007, 009–011, 013–026, 029, 032, 033, 038–040, 043, 044, 046, 048, 049, 051–056, 058, 064, 065, 068, 075` | Valid quiz creation via **Save and return to course** or **Save and display**; verifies course listing, course description display, or saved Quiz overview summary. |
| `data/validation_errors.csv` | 28 | `TC-001-002, 003, 006, 008, 012, 027, 028, 030, 031, 034–037, 041, 042, 045, 047, 050, 057, 059–063, 066, 067, 070, 071` | Negative ECP, BVA, and Decision Table validation cases; asserts form remains open and checks exact inline field error (`id_error_<field>`). Includes the 6 `known_defect` cases (`D-01`–`D-06`). |
| `data/ui_rules.csv` | 4 | `TC-001-069, 072, 073, 074` | Decision Table dynamic UI dependency checks (`After the quiz is closed` enablement, `Attempts = 1` / `2` field visibility, `Question behaviour` & `Review options` cross-dependencies). |
| `data/scenarios.csv` | 6 | `TC-001-076` .. `TC-001-081` | End-to-end Use-Case scenarios: `S1` Save & display (`076`), `S3` Cancel (`077`), `S4` Edit + Repaginate (`078`), `S5` Add 3 feedback fields then Save (`079`), `S6` Error -> Fix -> Save (`080`), `S7` Error -> Cancel (`081`). |
| **Total** | **81** | `TC-001-001` .. `TC-001-081` | Full 100% coverage of Project #2 test suite. |

### Level 1 Execution Result (`results/L1_F001.json`)
- **Command:** `.venv\Scripts\python.exe run_tests.py level1/F001_quiz_settings --tag L1_F001`
- **Summary:** `81 cases, 75 passed, 6 failed, 0 errors, 581.8 s`
- **Failed on known defects (expected):** `TC-001-008`, `TC-001-034`, `TC-001-047`, `TC-001-057`, `TC-001-059`, `TC-001-062`
- **Unexpected failures:** `0` (`failed_unexpected: []`, `passed_but_marked_defect: []`)

---

## 2. Level 2 Keyword & Data-Driven Automation (`level2/F001_quiz_settings/`)

Level 2 separates all URLs, locators, flows, and test data from the generic engine (`level2/l2engine.py`, unmodified) using the following files:

| File | Purpose |
|---|---|
| `site.csv` | Named page paths (`course_page=/course/view.php?name=KTC01`, `base_url` inherited from `MOODLE_BASE_URL`). |
| `elements.csv` | 76 element definitions (`name, locator, kind, description`) ordered by UI parent-child dependency so `fill` configures enabling checkboxes/selects before dependent inputs. |
| `flows.csv` | 105 flow steps across 15 reusable keyword flows (`before_all`, `after_all`, `delete_quizzes`, `open_form`, `create_return`, `create_display`, `create_seb_manual`, `validation_error`, `add_feedback_error`, `add_feedback_save`, `ui_dt1_after_close`, `ui_dt2_attempts_1`, `ui_dt2_attempts_2`, `ui_dt3_behaviour`, `uc_cancel`, `uc_edit_repaginate`, `uc_error_fix_save`, `uc_error_cancel`). |
| `testdata.csv` | All 81 rows (`TC-001-001` .. `TC-001-081`) with input columns, multi-check `expected_element[_N]` / `expected_result[_N]`, follow-up parameters, and `known_defect` annotations. |
| `helpers.py` | Small feature-specific helpers invoked via `helper` in `flows.csv`: `open_new_quiz`, `expand_form_sections`, `set_password` (unmasks Moodle 5.1 `passwordunmask` fields immediately before typing because blur re-hides them), `verify_visible`, and `verify_hidden`. |
| `test_l2_f001_quiz_settings.py` | 5-line entry point calling `build_test_class(..., "L2F001QuizSettings")`. |

### Level 2 Execution Result (`results/L2_F001.json`)
- **Command:** `.venv\Scripts\python.exe run_tests.py level2/F001_quiz_settings --tag L2_F001`
- **Summary:** `81 cases, 75 passed, 6 failed, 0 errors, 646.4 s`
- **Failed on known defects (expected):** `TC-001-008`, `TC-001-034`, `TC-001-047`, `TC-001-057`, `TC-001-059`, `TC-001-062`
- **Unexpected failures:** `0` (`failed_unexpected: []`, `passed_but_marked_defect: []`)

---

## 3. Adaptations vs. Project #2 (with Reasons)

1. **Direct form URL vs. Activity Chooser modal:** In Project #2 (Katalon), each test opened `KTC01`, toggled Edit mode, and clicked through the Activity Chooser modal. In Project #3, `open_form` navigates directly to `/course/modedit.php?add=quiz&type=&course=<cid>&section=0&return=0`, eliminating modal animation flakiness while exercising the exact same Quiz Settings form (`mod/quiz/mod_form.php`).
2. **Future year (`2027`) in `TC-001-005`, `TC-001-023`, `TC-001-069`:** Project #2 used `2026-11-20 17:00` when executed on `2026-11-11`, so Moodle displayed `Closes:`. Because Project #3 was executed on `2026-11-25`, `2026-11-20` had moved into the past, causing Moodle to display `Closed:` instead of `Closes:`. Updating `timeclose` to `2027-11-20 17:00` restores the intended future-close-date condition and `Closes:` assertion.
3. **JS click on `Expand all` / `Show more...` & `passwordunmask` handling:** Moodle 5.1's sticky footer (`#sticky-footer`) intercepts standard Selenium clicks on lower `a.moreless-toggler` links, and Moodle's `passwordunmask` widget re-hides the `<input>` on blur. Expanding sections via JS clicks and unmasking password fields right before typing resolves both without modifying `common/` or `level2/l2engine.py`.
4. **Course page verification after `Save and return`:** Opening `/course/view.php?name=KTC01` before verifying the created quiz card ensures deterministic assertion regardless of Moodle section-anchor redirects.

---

## 4. Known Defects Confirmed (`D-01` – `D-06`)

All 6 defects discovered in Project #2 were reproduced identically in both Level 1 and Level 2:

| Defect ID | Test Case | Summary | Observed Behaviour (MuTMS / Moodle 5.1.8) |
|---|---|---|---|
| **D-01** | `TC-001-057` | Require password length = 256 (`V29`) | Unhandled `dmlwriteexception: Error writing to database` (column `password` is `CHAR(255)` with no form `maxlength` validation). |
| **D-02** | `TC-001-059` | Require network address length = 256 (`V30`) | Unhandled `dmlwriteexception: Error writing to database` (column `subnet` is `CHAR(255)` with no form `maxlength` validation). |
| **D-03** | `TC-001-047` | Grade to pass = `-1` (`V10`) | Negative grade `-1` is silently accepted and saved (`course/moodleform_mod.php` only validates `> grademax`, never `< 0`). |
| **D-04** | `TC-001-008` | Time limit = `abc` when enabled (`V6`) | `PARAM_FLOAT` silently coerces `'abc'` to `0` and saves the quiz with no validation error. |
| **D-05** | `TC-001-062` | Overall feedback boundary = `'0'` (`V35`) | PHP `empty('0')` evaluates to `true`, terminating the boundary loop in `mod/quiz/mod_form.php` and saving `'0'` silently. |
| **D-06** | `TC-001-034` | Overall feedback boundary = `'abc'` (`V35`) | Displays out-of-range error instead of format error due to unparenthesized `&&`/`||` + PHP 8 string comparison. |

---

## 5. Non-Functional Testing (`nonfunctional/`)

Two distinct non-functional suites were implemented and executed for Feature 001 to satisfy both the group assignment (`NFR-01` Performance) and the Project #3 specification requirement of at least two NFRs per student (`NFR-01b` Usability / Responsive Layout).

### 5.1 NFR-01: Performance Testing (`nonfunctional/NFR-01_F001_performance/`)
- **Testing Type:** Non-functional — Response-time performance testing.
- **Requirement:** Opening **New Quiz** and submitting **Save and display** must achieve `average < 2.0 s` and `95th percentile < 3.0 s`.
- **Testing Approach & Tool:** Data-driven Selenium timing harness (`test_nfr01_performance.py` + `data/performance.csv`) using Python `time.perf_counter()` for end-to-end transition latency (from navigation/submit click until `document.readyState == 'complete'` and target element visibility, using direct JS click + 50 ms polling on `Save and display` so Selenium's native `ElementClickInterceptedException` retry overhead of ~`1.15 s` does not skew server latency) plus Chrome `performance.getEntriesByType('navigation')[0]` telemetry. Each scenario runs **1 warm-up** iteration (discarded) followed by **10 measured iterations**. Detailed sample telemetry is exported to `results/NFR-01_perf_<tc_id>.json`.
- **Command:** `.venv\Scripts\python.exe run_tests.py nonfunctional/NFR-01_F001_performance --tag NFR01_F001`
- **Measured Results (`results/NFR01_F001.json`):**

| Case ID | Operation | Config | Min (s) | Avg (s) | P95 (s) | Max (s) | Thresholds | Verdict |
|---|---|---|---:|---:|---:|---:|---|---|
| `NFR-01-01` | Open `New Quiz` form | default | 0.583 | **0.741** | **1.000** | 1.000 | avg < 2.0s, p95 < 3.0s | **PASS** |
| `NFR-01-02` | `Save and display` | minimal (Name only) | 0.807 | **1.272** | **1.626** | 1.626 | avg < 2.0s, p95 < 3.0s | **PASS** |
| `NFR-01-03` | `Save and display` | full (Timing + Grade + Layout + SEB + Feedback) | 0.949 | **1.387** | **1.852** | 1.852 | avg < 2.0s, p95 < 3.0s | **PASS** |

- **Analysis:** All three scenarios meet both thresholds (`avg < 2.0 s` and `p95 < 3.0 s`). Opening **New Quiz** averages `0.741 s` (`p95 = 1.000 s`), while **Save and display** (which executes a full HTTP `POST /course/modedit.php` -> `303` redirect -> `GET /mod/quiz/view.php` cycle, `redirectCount = 1`) averages `1.272 s` (`p95 = 1.626 s`) for minimal settings and `1.387 s` (`p95 = 1.852 s`) for a full configuration. Notice that an initial run wrapping `common/moodle.py`'s `m.submit()` had reported `avg ~ 2.35–2.38 s` only because Moodle's sticky footer intercepted native WebDriver clicks on `id_submitbutton` and triggered a ~`1.15 s` ChromeDriver retry before falling back to JS click; removing that client-side click-retry overhead aligns the measured wall-clock time with Chrome's `Navigation Timing` (`loadEventEnd` `0.75–1.77 s`).

### 5.2 NFR-01b: Usability & Responsive Layout Testing (`nonfunctional/NFR-01b_F001_usability/`)
- **Testing Type:** Non-functional — Usability / Responsive Layout testing.
- **Requirement:** Across Desktop (`1366x900`), Tablet (`768x1024`), and Mobile (`375x812`), both the **New Quiz** form and saved **Quiz view** page must render with `0 px` horizontal overflow (`scrollWidth <= clientWidth`), keep essential controls (`id_name`, `id_submitbutton`, `id_submitbutton2`, `id_cancel`) visible within the viewport, display inline validation errors on empty submit, and save cleanly.
- **Testing Approach & Tool:** Data-driven multi-viewport Selenium test (`test_nfr01b_usability.py` + `data/responsive.csv`) using Chrome DevTools Protocol `Emulation.setDeviceMetricsOverride` (avoiding Windows desktop minimum-width window clamping at `375 px`) and DOM bounding-box/overflow inspection. Detailed geometry metrics are saved to `results/NFR-01b_usability_<tc_id>.json`.
- **Command:** `.venv\Scripts\python.exe run_tests.py nonfunctional/NFR-01b_F001_usability --tag NFR01b_F001`
- **Measured Results (`results/NFR01b_F001.json`):**

| Case ID | Viewport | Form `scrollWidth / clientWidth` | Form Overflow | `id_name` Width | View `scrollWidth / clientWidth` | View Overflow | Verdict |
|---|---|---:|---:|---:|---:|---:|---|
| `NFR-01b-01` | Desktop (`1366x900`) | `1351 / 1351` | `0 px` | `506 px` | `1366 / 1366` | `0 px` | **PASS** |
| `NFR-01b-02` | Tablet (`768x1024`) | `753 / 753` | `0 px` | `452 px` | `768 / 768` | `0 px` | **PASS** |
| `NFR-01b-03` | Mobile (`375x812`) | `375 / 375` | `0 px` | `329 px` | `375 / 375` | `0 px` | **PASS** |

- **Observation:** At `375x812` mobile width, Moodle's Bootstrap layout cleanly shrinks `id_name` (`329 px`) and wraps `Save and display` (`left: 23, right: 159`) and `Cancel` (`left: 163, right: 233`) onto a second row below `Save and return to course` (`left: 23, right: 219`), keeping horizontal overflow at `0 px` on both the form and the saved quiz view.

---

## 6. AI Usage Declaration

| Item | Details |
|---|---|
| AI tool | Antigravity IDE coding agent (`Gemini / Google DeepMind`) |
| Student and team ownership | The student provided the Project #2 Feature 001 test assets (`spec.py`, `cases.json`, `F001_quiz_settings_report.md`), the team's Project #3 scaffold (`common/`, `level2/l2engine.py`, `run_tests.py`, `Work tutorial.txt`), answered two structured clarification rounds to decide scope (81/81 cases in Level 1 & Level 2, 4 Level 1 CSV groups, 2 NFRs: Performance + Usability/Responsive Layout, strict preservation of shared team code, English deliverables), started Docker Desktop and the local MuTMS 5.1.8 demo (`http://127.0.0.1:9501`), and reviewed outputs before submission. |
| How AI assisted | AI read Project #2 (`spec.py`, `F001_quiz_settings_report.md`) and Project #3's shared framework (`common/`, `level2/l2engine.py`, `F005` reference implementation), clarified design decisions via `/grill-me`, generated the Level 1 script + 4 CSVs, Level 2 data/flow/helper files, and both NFR suites (`NFR-01` Performance and `NFR-01b` Usability), executed all suites against `http://127.0.0.1:9501`, diagnosed and fixed Moodle 5.1 DOM quirks (sticky-footer click interception on `Show more...` and `id_submitbutton` during performance timing, `passwordunmask` blur re-hide, `2027` future date for `Closes:`, and CDP viewport emulation for `375 px` mobile width), and compiled these notes and manual run instructions from observed test logs and JSON artifacts. |

### Exact prompts entered by the user
1. Prompt 1:
   > `/grill-me hiện tại mình đang thực hiện Assignment 3 có trong folder Ass3, assignment 3 sẽ liên quan trực tiếp đến công việc đã thực hiện ở Assignment 2 trước đó trong folder Ass2. Bạn có thể lấy ra các tài nguyên ở assignment 2 trước đó để xem nhé. Và mình là student 1 tương ứng với các công việc của F001 đã làm trước đó. Nếu bạn cần mình trả lời các câu hỏi để làm rõ assignment 3 thì cứ tự nhiên hỏi nhé. Sau đó chúng ta sẽ cùng nhau bắt tay vào làm assignment 3`
2. Prompt 2 (Round 1 design decisions):
   > `Q1. Mình đã đổi tên lại thành Ass\Ass3\software_testing_proj3 rồi nhé nên bạn đừng lo về đường dẫn này`
   > `Q2. Làm 2 NFR (NFR-01 Performance theo đúng yêu cầu nhóm + 1 NFR phụ cho F001) để an toàn tối đa theo rubric đề bài`
   > `Q.3. Port đầy đủ 81/81 test cases cho cả Level 1 và Level 2, gắn known_defect cho đúng 6 defect`
   > `Q.4. Đồng ý chia 4 file CSV theo 4 nhóm hành vi trên để bảng dữ liệu gọn, dễ đọc và đúng tinh thần gom nhóm của đề bài.`
   > `Q.5. Giữ nguyên tuyệt đối common/ và level2/l2engine.py, chỉ dùng helpers.py cục bộ trong level2/F001_quiz_settings/ khi thật sự cần.`
   > `Q.6. Tạo .venv và chạy thực tế toàn bộ suite trên http://127.0.0.1:9501 để kiểm chứng và xuất đủ results/*.json + .csv.`
   > `Bạn hãy thực hiện đúng theo hướng dẫn của nhóm và làm cẩn thận để không ảnh hưởng đến repo chung của nhóm nhé`
3. Prompt 3 (Round 2 design decisions):
   > `Q.7 đồng ý nhé`
   > `Q.8 Mình thấy Phương Án A phù hợp nhất nhé`
   > `Q.9 Okok nhé. Nhớ tạo folder trước rồi mới tạo file tương ứng cho từng folder nè. Làm điều tương tự với folder Level 1, Level 2 để không bị sai cú phép tên nhé.`
   > `Q.10 Tạo tất cả các files bằng Tiếng Anh không riêng gì file notes_F001.md ngoài ra mục AI Usage Declaration thì bạn có thể tham khảo trong mục này ở Ass2 trước đó tui đã có làm và làm theo format đó nhé`
4. Prompt 4 (Local Moodle demo ready):
   > `Mình đã bật docker và chạy Demo ở ass2, bạn kiểm tra thử và chạy kiểm thực tế nhé`
5. Prompt 5 (NFR-01 failure investigation):
   > `Cho tui hỏi trong 2 test case fail của NFR-01 Performance thì liệu cái này do thực tế nó như vậy hay chúng ta có thể làm cho nó pass`
6. Prompt 6 (Update NFR-01 timing harness and provide manual run guide):
   > `OKok nhé, bạn hãy cập nhật hàm và số liệu mới nhất. Sau đó bạn hãy hướng dẫn mình các bước để mình có thể tự chạy thủ công các test trong assignment 3 này luôn nhé`
