# Project #3 Notes — Feature 003: Add/edit grade item (`F003`)

| Metadata | Value |
|---|---|
| Course | Software Testing (CO3015) — HCMC University of Technology (VNUHCM) |
| Group | CC01_G07 |
| Student / Member | _<Le Cong Danh (2352154)>_ — Feature 003 |
| Feature Tested | Feature 003: Add/edit grade item (Grades → Gradebook setup → Add → Add grade item / Edit grade item) |
| System Under Test | Moodle LMS 5.1.8 — MuTMS Demo (`http://127.0.0.1:9501`) |
| Test Stack | Python 3.14 + Selenium 4 + `unittest`, headless Brave 158 (Chromium) driven by ChromeDriver 158 |
| Shared Fixture | `setup/test_00_setup.py` (`11/11` passed, course `KTC01`, students `kt_s01`..`kt_s10`) |

---

## 1. Level 1 Data-Driven Automation (`level1/F003_grade_item/`)

All **80 test cases** (`TC-003-001` .. `TC-003-080`) of Project #2 are run by one script,
`test_f003_grade_item.py`, decorated with `@data_driven(...)`. The cases are grouped by how they run into four
CSV files that share the same columns (form fields, action, checks, `known_defect`):

| Data File | Cases | Scope |
|---|---:|---|
| `data/add_valid.csv` | 45 | Fill the full *New grade item* form, **Save changes**, check the Gradebook setup row (Max grade, Hidden/Locked icons, extra credit mark), reopen the item with **Edit grade item** and check every stored value. ECP/BVA of name, ID number, grade type, range, grade to pass, decimals, display type, hidden/locked, extra credit, storage maximum. |
| `data/add_invalid.csv` | 14 | Fill, Save, check the exact message under the field (`id_error_<field>`), Cancel, check that nothing was saved. Includes the defect cases `007`, `013`, `018`, `071`. |
| `data/form_rules.csv` | 4 | Decision-table field dependencies on the open form: Letter display disables decimals (`066`), Hidden until disables Hidden (`067`), Lock after date (`068`), Weight adjusted enables Weight (`075`). |
| `data/scenarios.csv` | 17 | Use-case scenarios S2–S10: quick dialog save/cancel, cancel the full form, edit name / maximum / info, cancel edit, correct-then-save, graded item with rescale Yes/No, adjusted weights 0/25/100, item in another category, course-total overflow (`080`). |
| **Total** | **80** | 100 % of the Project #2 suite |

The data cells use the team notation (`{{EMPTY}}`, `{{N*1334}}`, blank = keep default). The checks are written in
the `expected_result`, `before_expected` and `then_expected` columns, e.g.
`row=F003-052 | range=F003-052: 100.00 | icon=F003-052: Hidden | edit=F003-052 | checked.hidden | cancel`.
Preconditions (`item=…`, `grade=…`, `category=…`) are created through the UI before the case, and every case
cleans up after itself through the row menus (or a gradebook course reset after `080`).

### Level 1 Execution Result (`results/L1_F003.json`)
- **Command:** `CHROME_BINARY=/usr/bin/brave .venv/bin/python run_tests.py level1/F003_grade_item --tag L1_F003`
- **Summary:** `80 cases, 75 passed, 5 failed, 0 errors, 1451 s`
- **Failed on known defects (expected):** `TC-003-007`, `TC-003-013`, `TC-003-018`, `TC-003-071`, `TC-003-080`
- **Unexpected failures:** `0` (`failed_unexpected: []`, `passed_but_marked_defect: []`)

---

## 2. Level 2 Keyword & Data-Driven Automation (`level2/F003_grade_item/`)

The generic engine `level2/l2engine.py` is used unchanged; this folder contains only data:

| File | Purpose |
|---|---|
| `site.csv` | Base URL (blank = `MOODLE_BASE_URL`) and the course page `/course/view.php?name=KTC01`. |
| `elements.csv` | 63 elements (`name, locator, kind, description`): navigation (Grades link, report menu, Add menu), quick dialog fields (addressed by `name`, because the dialog uses random ids), every field of the full form in dependency order, the error label of each field, the Moodle exception message, and row elements parameterised by data columns (`Target row`, `Target row max grade`, `Reference row weight`, `Student grade`, …). |
| `flows.csv` | 168 steps in 25 flows: `before_all`/`after_all` (gradebook reset), `open_setup` (course → Grades → Gradebook setup, through the menus), `open_full`, `edit_target`, `create_ref`, `create_category`, `add_valid`, `add_invalid`, `add_invalid_ref`, `form_rule`, `lock_after`, `cancel_full`, `edit_item`, `edit_item_reopen`, `correct_then_save`, `graded_item_rules`, `rescale`, `quick_dialog`, `weight`, `category_item`, `course_total_overflow`, plus the clean-up flows. |
| `testdata.csv` | All 80 rows with input columns named after the elements, parameters (`target`, `ref_name`, `student`, …) and up to four `expected_element_N` / `expected_result_N` pairs; `known_defect` as in Level 1. |
| `helpers.py` | What the keyword language cannot express: deleting every grade item (a loop), Single view of an item (its id is read from the page), entering a grade, and the gradebook course reset plus the regrade task it queues (the demo container has no cron). |
| `test_l2_f003_grade_item.py` | 5-line entry point calling `build_test_class(...)`. |

### Level 2 Execution Result (`results/L2_F003.json`)
- **Command:** `CHROME_BINARY=/usr/bin/brave .venv/bin/python run_tests.py level2/F003_grade_item --tag L2_F003`
- **Summary:** `80 cases, 75 passed, 5 failed, 0 errors, 2176 s`
- **Failed on known defects (expected):** `TC-003-007`, `TC-003-013`, `TC-003-018`, `TC-003-071`, `TC-003-080`
- **Unexpected failures:** `0` (`failed_unexpected: []`, `passed_but_marked_defect: []`)
- **Debugging before the final run:** the first run had 3 unexpected failures (`057`, `060`, `077`), all mistakes in
  `testdata.csv`: a check of a Gradebook setup row was placed while the Edit form was open. After the fix, one run
  stopped once in `077` with a timeout while opening the row menu (timing); a 500 ms pause was added to `edit_target`.

---

## 3. Adaptations vs. Project #2 (with reasons)

1. **Browser:** Chrome is not installed on the test machine. The shared `common/config.py` / `common/driver.py` got an
   opt-in `CHROME_BINARY` variable, so the suites drive Brave (Chromium) through ChromeDriver. Without the variable
   nothing changes for the other members; `BROWSER=firefox` also works.
2. **Defect cases expect the specified behaviour:** In Project #2 the five defect cases verified the observed
   "Error writing to database" and passed. Following the team convention of Project #3, they now check what the
   specification requires (a validation message under the field, nothing saved; for `080` the second item is saved)
   and are marked in `known_defect`, so they fail on purpose and the runner reports them separately.
3. **Gradebook setup opened by its address in Level 1:** Level 1 opens `/grade/edit/tree/index.php?id=<course>` directly
   instead of clicking Grades → report menu → Gradebook setup on every case (the course id is read from the course
   page). The Add / Edit dialogs and *Show more...* are still used through the UI. Level 2 keeps the full menu path.
4. **Quick dialog fields by name:** the *New grade item* dialog gives its inputs random ids
   (`id_itemname_<random>`), so they are located by `name` inside `.modal.show`.
5. **Clean-up through the row menus:** each case deletes the items and categories it created (Actions → Delete),
   instead of a course reset, because a reset queues a regrade task that never runs without cron. A reset (followed
   by *Run now*) is used only before/after the whole suite and after `TC-003-080`, which breaks the gradebook.

---

## 4. Known Defects Confirmed (`D003-01` – `D003-05`)

All five Project #2 defects were reproduced in both Level 1 and Level 2:

| Defect | Test Case | Input | Observed behaviour (Moodle 5.1.8) |
|---|---|---|---|
| **D003-01** | `TC-003-007` | Item name of 1334 characters | Page "Error writing to database" (too long for column `itemname`); no field validation. |
| **D003-02** | `TC-003-013` | ID number of 256 characters | Page "Error writing to database" (too long for column `idnumber`). |
| **D003-03** | `TC-003-018` | Maximum grade empty | Page "Error writing to database" (`grademax` cannot be null); the field is not marked required. |
| **D003-04** | `TC-003-071` | Maximum grade 100000 | Page "Error writing to database" (out of range for `grademax`). |
| **D003-05** | `TC-003-080` | Item with maximum 99999.99999, then a second item with maximum 10 | Page "Error writing to database" (course total out of range); every Grades page shows the error until the gradebook is reset. |

---

## 5. Non-Functional Testing (`nonfunctional/NFR-03_F003_access_control/`)

One non-functional requirement was tested for Feature 003, as chosen by the student: **NFR-03 Access control**.

- **Testing type:** Non-functional — security testing (authentication and authorization / access control).
- **Requirement:** Only users who may manage grades can see or change grade items. Every gradebook URL of the feature
  must refuse (a) a visitor who is not logged in (redirect to the login page, nothing of the gradebook shown) and
  (b) a logged-in student of the course (Moodle permission error, no form, no item data). A refused request must not
  change anything.
- **Approach:** Data-driven negative testing of direct URL access with three browser sessions (not logged in,
  student `kt_s01`, administrator). A fixture item `NFR03-target` is created first. The delete and hide links and a
  forged POST of the Edit form are sent with the **student's own valid sesskey**, so only the capability check can stop
  them; the POST is sent with `fetch()` from inside the role's session. After each of these the administrator checks
  that the item still has the same name, maximum and visibility. Two control cases show that the checks can tell
  "allowed" from "refused".
- **Tool:** Selenium WebDriver + `unittest` (same framework as Level 1). Data: `data/access.csv` (18 rows: role,
  method, URL template, expected outcome), `data/fixture.csv`. Each case writes its evidence (final URL, message,
  item before/after) to `results/NFR-03_access_<tc_id>.json`.
- **Command:** `CHROME_BINARY=/usr/bin/brave .venv/bin/python run_tests.py nonfunctional/NFR-03_F003_access_control --tag NFR03_F003`
- **Result (`results/NFR03_F003.json`):** `18 cases, 18 passed, 0 failed, 67 s`

| Case | Role | Request | Outcome |
|---|---|---|---|
| NFR-03-01..05 | not logged in | Gradebook setup, New item form, Edit form, Grader report, Single view | Redirect to `/login/index.php` |
| NFR-03-06, 07 | not logged in | delete link; forged POST of the Edit form | Redirect to login; item unchanged |
| NFR-03-08..11 | student | Gradebook setup, New item form, Edit form, New category form | "Sorry, but you do not currently have permissions to do that (Manage grade items)." |
| NFR-03-12, 13 | student | Grader report, Single view | "… (View grader report)." / "… (View single view)." |
| NFR-03-14 | student | hide link with valid sesskey | "No permission to hide!"; item still visible |
| NFR-03-15, 16 | student | delete link / forged POST with valid sesskey | "… (Manage grade items)"; item unchanged |
| NFR-03-17 | student (control) | own User report | Allowed |
| NFR-03-18 | admin (control) | Gradebook setup | Allowed, item listed |

- **Analysis:** The requirement is met: all 16 refusal cases were refused and none of the attempted changes reached
  the database. One observation: the hide action refuses with its own short message "No permission to hide!"
  instead of the standard permission page that names the missing capability. This is a consistency/usability issue,
  not a security one.

---

## 6. AI Usage Declaration

| Item | Details |
|---|---|
| AI tool | Claude Code (Anthropic), model Claude Opus 4.8, command-line coding agent |


### Prompts entered by the student (verbatim)
1. > Hi Claude, here is my assignement 3 for software testing, try reading and analyzing this folder with my some of my work was done here first and analyze if my work is done correctly, if yes, keep doing with the remaining parts and fix it if its wrong, note that the moodle project is in demo folder in /SW_Testing. Feel free to ask me anything you need for this
2. > before doing so, my scope will be this Level 1 + Level 2 + NFR access control: student / not-logged-in users must be refused on the gradebook URLs.
3. > for the katalon I suggest using brave
4. Answers to the AI's multiple-choice questions: "One NFR only"; defect cases "Team convention: fail"; Moodle demo "You start it"; browser "Add CHROME_BINARY for Brave".

