"""F002 Assignment Settings - Level 1 data-driven test (member: Naman Chahar, 2560173).

All 85 test cases (TC-002-001 .. TC-002-085) from Project #2 are grouped by execution pattern:
    data/create.csv       valid saves (defaults, fields, BVA boundaries, DT rules)
    data/validation.csv   invalid input / validation cases (including the three known defects)
    data/ui.csv           Decision Table dynamic UI dependency checks
    data/scenarios.csv    Use-Case end-to-end scenarios (S1-S8)

Page URLs and element locators stay in this script (Level 1); the CSV files hold only
test data and expected results.  The data files are the same content as the Project #2 workbook,
one row per TC id.
"""
import re
import unittest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from common import config
from common.base import MoodleTestCase
from common.data import expand, split
from common.ddt import data_driven

# logical data column -> (kind, locator) used when a saved value is checked
SAVED = {
    "intro": ("editor", "id_introeditor"),
    "activity": ("editor", "id_activityeditor"),
    "showdescription": ("checked", "id_showdescription"),
    "submissionattachments": ("checked", "id_submissionattachments"),
    "allow_enabled": ("checked", "id_allowsubmissionsfromdate_enabled"),
    "due_enabled": ("checked", "id_duedate_enabled"),
    "cutoff_enabled": ("checked", "id_cutoffdate_enabled"),
    "gradingdue_enabled": ("checked", "id_gradingduedate_enabled"),
    "alwaysshowdescription": ("checked", "id_alwaysshowdescription"),
    "file_enabled": ("checked", "id_assignsubmission_file_enabled"),
    "file_maxfiles": ("selected", "id_assignsubmission_file_maxfiles"),
    "file_maxsize": ("selected", "id_assignsubmission_file_maxsizebytes"),
    "file_types": ("value", "id_assignsubmission_file_filetypes"),
    "onlinetext_enabled": ("checked", "id_assignsubmission_onlinetext_enabled"),
    "wordlimit": ("value", "id_assignsubmission_onlinetext_wordlimit"),
    "wordlimit_enabled": ("checked", "id_assignsubmission_onlinetext_wordlimit_enabled"),
    "comments_enabled": ("checked", "id_assignfeedback_comments_enabled"),
    "commentinline": ("selected", "id_assignfeedback_comments_commentinline"),
    "feedback_file_enabled": ("checked", "id_assignfeedback_file_enabled"),
    "editpdf_enabled": ("checked", "id_assignfeedback_editpdf_enabled"),
    "submissiondrafts": ("selected", "id_submissiondrafts"),
    "requiresubmissionstatement": ("selected", "id_requiresubmissionstatement"),
    "maxattempts": ("selected", "id_maxattempts"),
    "attemptreopenmethod": ("value", "id_attemptreopenmethod"),
    "teamsubmission": ("selected", "id_teamsubmission"),
    "preventsubmissionnotingroup": ("selected", "id_preventsubmissionnotingroup"),
    "requireallteammemberssubmit": ("selected", "id_requireallteammemberssubmit"),
    "grouping": ("selected", "id_teamsubmissiongroupingid"),
    "sendnotifications": ("selected", "id_sendnotifications"),
    "sendlatenotifications": ("selected", "id_sendlatenotifications"),
    "sendstudentnotifications": ("selected", "id_sendstudentnotifications"),
    "grade_type": ("selected", "id_grade_modgrade_type"),
    "grade_point": ("value", "id_grade_modgrade_point"),
    "gradepass": ("value", "id_gradepass"),
    "blindmarking": ("selected", "id_blindmarking"),
    "hidegrader": ("selected", "id_hidegrader"),
    "markingworkflow": ("selected", "id_markingworkflow"),
    "markingallocation": ("selected", "id_markingallocation"),
    "markinganonymous": ("selected", "id_markinganonymous"),
    "gradepenalty": ("selected", "id_gradepenalty"),
    "times_enabled": ("checked", "id_timelimit_enabled"),
    "time_limit": ("value", "id_timelimit_number"),
}

CHECKBOXES = {
    "showdescription", "submissionattachments", "alwaysshowdescription", "file_enabled",
    "onlinetext_enabled", "wordlimit_enabled", "comments_enabled", "feedback_file_enabled",
    "editpdf_enabled", "times_enabled",
}
ERROR_FIELDS = {"wordlimit": "assignsubmission_onlinetext_wordlimit"}
SELECTS = {
    "file_maxfiles", "file_maxsize", "commentinline", "submissiondrafts", "requiresubmissionstatement",
    "maxattempts", "teamsubmission", "preventsubmissionnotingroup", "requireallteammemberssubmit",
    "grouping", "sendnotifications", "sendlatenotifications", "sendstudentnotifications",
    "grade_type", "blindmarking", "hidegrader", "markingworkflow", "markingallocation", "markinganonymous",
    "gradepenalty", "time_unit",
}
DATE_PREFIX = {
    "allow": "id_allowsubmissionsfromdate",
    "date": "id_duedate",
    "cutoff": "id_cutoffdate",
    "gradingdue": "id_gradingduedate",
}
TEXT = {
    "name": "id_name", "file_types": "id_assignsubmission_file_filetypes",
    "wordlimit": "id_assignsubmission_onlinetext_wordlimit", "grade_point": "id_grade_modgrade_point",
    "gradepass": "id_gradepass", "time_limit": "id_timelimit_number",
}
BUTTONS = {"display": "id=id_submitbutton", "return": "id=id_submitbutton2", "cancel": "id=id_cancel"}


def checks(cell):
    """'a=x | b=y | flag' -> [('a', 'x'), ('b', 'y'), ('flag', None)]"""
    out = []
    for part in split(cell, "|"):
        key, eq, value = part.partition("=")
        out.append((key.strip(), expand(value.strip()) if eq else None))
    return out


@data_driven(
    "data/create.csv",
    "data/validation.csv",
    "data/ui.csv",
    "data/scenarios.csv",
)
class F002AssignmentSettings(MoodleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cid = cls.m.course_id(config.COURSE_SHORTNAME)
        cls.ensure_time_limit_enabled()
        cls.m.delete_activities("assign")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.m.delete_activities("assign")
            cls.remove_grouping()
        finally:
            super().tearDownClass()

    # ------------------------------------------------------------------ dispatch
    def run_case(self, row):
        if row["precheck"].startswith("prep.grouping"):
            self.ensure_grouping()
        if row["group"] == "ui":
            self._run_ui(row)
        elif row["group"] == "scenario":
            self._run_scenario(row)
        else:
            self._run_simple(row)

    def _run_simple(self, row):
        # cleanup protects KTC01 when a known-defect case erroneously saves an assignment
        # Class-level tearDownClass deletes all assignments; per-case deletion is not needed and keeps the run fast.
        self.open_form()
        self.apply_dates(row)
        self.fill(row)
        if row["precheck"]:
            self.check(row["precheck"])
        self.m.submit(BUTTONS[row["button"]])
        self.check(row["expected"])

    def _run_ui(self, row):
        # Class-level tearDownClass deletes all assignments; per-case deletion is not needed and keeps the run fast.
        self.open_form()
        self.apply_dates(row)
        if row["tc_id"] == "TC-002-077":
            # DT5 asserts that the dependent fields are hidden before workflow/anonymous are enabled
            self.check(row["precheck"])
        self.fill(row)
        if row["precheck"] and row["tc_id"] != "TC-002-077":
            self.check(row["precheck"])
        if row["then_set"]:
            self.fill_pairs(self._kv_pairs(row["then_set"]))
        if row["then_check"]:
            self.check(row["then_check"])
        self.m.submit(BUTTONS[row["button"]])
        self.check(row["expected"])

    def _run_scenario(self, row):
        # Class-level tearDownClass deletes all assignments; per-case deletion is not needed and keeps the run fast.
        sc = row["tc_id"]
        if sc == "TC-002-079":
            self.open_form(); self.apply_dates(row); self.fill(row)
            self.m.submit(BUTTONS["return"]); self.check(row["expected"])
        elif sc == "TC-002-080":
            self.open_form(); self.apply_dates(row); self.fill(row)
            self.m.submit(BUTTONS["cancel"]); self.check(row["expected"])
        elif sc == "TC-002-081":
            self.open_form(); self.apply_dates(row); self.fill(row)
            self.m.submit(BUTTONS["display"]); self.check(row["expected"])
            self.m.type("id=id_name", expand(row["then_set"].split("=", 1)[1]))
            self.m.submit(BUTTONS["display"]); self.check(row["then_check"])
        elif sc == "TC-002-082":
            self.open_form(); self.apply_dates(row); self.fill(row)
            self.m.submit(BUTTONS["display"]); self.check(row["expected"])
            self.m.set_date("id_" + "duedate", expand(row["then_set"].split("=", 1)[1]))
            self.m.submit(BUTTONS["display"]); self.check(row["then_check"])
        elif sc == "TC-002-083":
            self.open_form(); self.apply_dates(row); self.fill(row)
            self.m.submit(BUTTONS["return"]); self.check(row["expected"])
            self.open_activity_settings(expand(row["name"]))
            pairs = dict(p.split("=", 1) for p in split(row["then_set"], "|"))
            self.m.type("id=id_name", expand(pairs["name"]))
            self.m.type("id=id_grade_modgrade_point", expand(pairs["grade_point"]))
            self.m.submit(BUTTONS["display"]); self.check(row["then_check"])
        else:  # 078, 084, 085
            self.open_form(); self.apply_dates(row); self.fill(row)
            self.m.submit(BUTTONS["display"]); self.check(row["expected"])

    # ------------------------------------------------------------------ form
    def open_form(self):
        self.m.open("/course/modedit.php?add=assign&type=&course=%d&section=0&return=0" % self.cid)
        self.verify_text("css=#region-main h2", "New Assignment", "form heading")
        self.m.expand_all()

    def apply_dates(self, row):
        mode = row["dates_mode"]
        if mode in ("off", "custom"):
            for prefix in DATE_PREFIX.values():
                cb = "id=%s_enabled" % prefix
                if self.m.exists(cb) and self.m.find(cb).is_selected():
                    self.m.set_checkbox(cb, False)
        if mode == "custom":
            for key, prefix in DATE_PREFIX.items():
                if row[key]:
                    self.m.set_date(prefix, expand(row[key]))

    def fill(self, row):
        # order matters: dependent fields are enabled before their dependants are set
        self.set_text("name", row["name"])
        if row["intro"]:
            self.m.set_editor("id_introeditor", expand(row["intro"]))
        if row["activity"]:
            self.m.set_editor("id_activityeditor", expand(row["activity"]))
        for key in ("showdescription", "submissionattachments"):
            if row[key]:
                self.set_check(row[key], key)
        if row["alwaysshowdescription"]:
            self.set_check(row["alwaysshowdescription"], "alwaysshowdescription")

        for key in ("file_enabled", "onlinetext_enabled", "comments_enabled",
                    "feedback_file_enabled", "editpdf_enabled"):
            if row[key]:
                self.set_check(row[key], key)
        if row["file_maxfiles"]:
            self.set_select(row["file_maxfiles"], "file_maxfiles")
        if row["file_maxsize"]:
            self.set_select_contains(row["file_maxsize"], "file_maxsize")
        if row["file_types"]:
            self.set_text("file_types", row["file_types"])
        if row["wordlimit_enabled"]:
            self.set_check(row["wordlimit_enabled"], "wordlimit_enabled")
        if row["wordlimit"]:
            self.set_text("wordlimit", row["wordlimit"])
        if row["commentinline"]:
            self.set_select(row["commentinline"], "commentinline")

        for key in ("submissiondrafts", "requiresubmissionstatement"):
            if row[key]:
                self.set_select(row[key], key)
        if row["maxattempts"]:
            self.set_select(row["maxattempts"], "maxattempts")
        if row["attemptreopenmethod"]:
            self.m.select("id=id_attemptreopenmethod", "value=" + row["attemptreopenmethod"])
        if row["teamsubmission"]:
            self.set_select(row["teamsubmission"], "teamsubmission")
        for key in ("preventsubmissionnotingroup", "requireallteammemberssubmit"):
            if row[key]:
                self.set_select(row[key], key)
        if row["grouping"]:
            self.set_select(row["grouping"], "grouping")

        for key in ("sendnotifications", "sendlatenotifications", "sendstudentnotifications"):
            if row[key]:
                self.set_select(row[key], key)
        if row["grade_type"]:
            self.set_select(row["grade_type"], "grade_type")
        if row["grade_type"] == "Scale":
            scale = "id=id_grade_modgrade_scale"
            if self.m.exists(scale):
                opts = [o.text for o in Select(self.m.find(scale)).options if o.text.strip()]
                if opts:
                    self.m.select(scale, "Default competence scale" if "Default competence scale" in opts else opts[0])
        if row["grade_point"]:
            self.set_text("grade_point", row["grade_point"])
        if row["gradepass"]:
            self.set_text("gradepass", row["gradepass"])

        for key in ("blindmarking", "hidegrader", "markingworkflow"):
            if row[key]:
                self.set_select(row[key], key)
        for key in ("markingallocation", "markinganonymous"):
            if row[key]:
                self.set_select(row[key], key)
        if row["gradepenalty"] and self.m.exists("id=id_gradepenalty"):
            self.set_select(row["gradepenalty"], "gradepenalty")

        if row["times_enabled"]:
            self.set_check(row["times_enabled"], "times_enabled")
            if row["time_limit"]:
                self.set_text("time_limit", row["time_limit"])
            if row["time_unit"]:
                self.set_select(row["time_unit"], "time_unit")

    def fill_pairs(self, pairs):
        for key, value in pairs:
            if key in DATE_PREFIX:
                self.m.set_date(DATE_PREFIX[key], expand(value))
            elif key in CHECKBOXES:
                self.set_check(expand(value), key)
            elif key in SELECTS:
                self.set_select(expand(value), key)
            else:
                self.set_text(key, expand(value))

    @staticmethod
    def _kv_pairs(cell):
        pairs = []
        for part in split(cell, "|"):
            k, _, v = part.partition("=")
            pairs.append((k.strip(), v.strip()))
        return pairs

    def set_text(self, key, value):
        self.m.type("id=" + TEXT[key], expand(value))

    def set_check(self, value, key):
        self.m.set_checkbox("id=" + (TEXT.get(key) or {
            "showdescription": "id_showdescription",
            "submissionattachments": "id_submissionattachments",
            "alwaysshowdescription": "id_alwaysshowdescription",
            "file_enabled": "id_assignsubmission_file_enabled",
            "onlinetext_enabled": "id_assignsubmission_onlinetext_enabled",
            "wordlimit_enabled": "id_assignsubmission_onlinetext_wordlimit_enabled",
            "comments_enabled": "id_assignfeedback_comments_enabled",
            "feedback_file_enabled": "id_assignfeedback_file_enabled",
            "editpdf_enabled": "id_assignfeedback_editpdf_enabled",
            "times_enabled": "id_timelimit_enabled",
        }[key]), str(value).strip().lower() in ("on", "yes", "1", "true", "checked"))

    def set_select(self, value, key):
        loc = {
            "file_maxfiles": "id=id_assignsubmission_file_maxfiles",
            "file_maxsize": "id=id_assignsubmission_file_maxsizebytes",
            "commentinline": "id=id_assignfeedback_comments_commentinline",
            "submissiondrafts": "id=id_submissiondrafts",
            "requiresubmissionstatement": "id=id_requiresubmissionstatement",
            "maxattempts": "id=id_maxattempts",
            "teamsubmission": "id=id_teamsubmission",
            "preventsubmissionnotingroup": "id=id_preventsubmissionnotingroup",
            "requireallteammemberssubmit": "id=id_requireallteammemberssubmit",
            "grouping": "id=id_teamsubmissiongroupingid",
            "sendnotifications": "id=id_sendnotifications",
            "sendlatenotifications": "id=id_sendlatenotifications",
            "sendstudentnotifications": "id=id_sendstudentnotifications",
            "grade_type": "id=id_grade_modgrade_type",
            "blindmarking": "id=id_blindmarking",
            "hidegrader": "id=id_hidegrader",
            "markingworkflow": "id=id_markingworkflow",
            "markingallocation": "id=id_markingallocation",
            "markinganonymous": "id=id_markinganonymous",
            "gradepenalty": "id=id_gradepenalty",
            "time_unit": "id=id_timelimit_timeunit",
        }[key]
        self.m.select(loc, expand(value))

    def set_select_contains(self, value, key):
        loc = {
            "file_maxsize": "id=id_assignsubmission_file_maxsizebytes",
        }[key]
        el = self.m.find(loc)
        wanted = re.sub(r"\s+", "", expand(value)).lower()
        for o in Select(el).options:
            if wanted in re.sub(r"\s+", "", o.text).lower():
                self.m.select(loc, o.text)
                return
        raise AssertionError("option containing %r not found in %s" % (wanted, loc))

    # ------------------------------------------------------------------ checks
    def check(self, cell):
        for key, expected in checks(cell or ""):
            if key == "prep.grouping":
                continue
            if key.startswith("error."):
                field = key[6:]
                self.verify_field_error(ERROR_FIELDS.get(field, field), expected)
            elif key.startswith("error_group."):
                field = key[12:]
                actual = self.m.text("id=fgroup_id_error_" + field, timeout=1) if self.m.exists(
                    "id=fgroup_id_error_" + field) else ""
                self.verify(expected == "*" and actual != "" or expected in actual,
                            "error under %s: expected %r, got %r" % (field, expected, actual))
            elif key == "heading":
                self.verify_equal(expand(expected), self.m.text("css=h1"), "page heading")
            elif key == "course_contains":
                self.m.open("/course/view.php?name=" + config.COURSE_SHORTNAME)
                self.verify_contains("id=region-main", expand(expected), "course page")
            elif key == "no_course_contains":
                self.m.open("/course/view.php?name=" + config.COURSE_SHORTNAME)
                self.verify(expand(expected) not in self.m.page_text(), "course page must not show %r" % expected)
            elif key in ("visible", "hidden", "enabled", "disabled"):
                loc = "id=" + expected
                present = self.m.exists(loc)
                if key in ("visible", "hidden"):
                    actual = present and self.m.find(loc).is_displayed()
                    self.verify_equal(key == "visible", actual, "%s %s" % (key, expected))
                else:
                    actual = present and self.m.find(loc).is_enabled()
                    self.verify_equal(key == "enabled", actual, "%s %s" % (key, expected))
            elif key.startswith("saved."):
                self.check_saved(key[6:], expected)
            else:
                raise ValueError("unknown check %r" % key)

    def check_saved(self, field, expected):
        if field not in SAVED:
            raise ValueError("unknown saved field %r" % field)
        kind, loc = SAVED[field]
        raw = loc[3:] if loc.startswith("id=") else loc
        full = "id=" + raw
        self.open_settings()
        if not self.m.exists(full):
            print("  note: %s is not present in this Moodle configuration; skipping saved check" % field)
            return
        if kind == "editor":
            actual = self.m.editor_text(raw)
        elif kind == "checked":
            actual = "on" if self.m.find(full).is_selected() else "off"
        elif kind == "selected":
            actual = self.m.selected_label(full)
        else:
            actual = self.m.value(full)
        if field == "file_maxsize":
            self.verify(re.sub(r"\s+", "", expand(expected) or "").lower() in re.sub(r"\s+", "", actual or "").lower(),
                        "saved %s: expected %r in %r" % (field, expected, actual))
        elif field == "wordlimit" and (expand(expected) in ("", None) or "EMPTY" in str(expected)):
            self.verify(actual in ("", "0"), "saved wordlimit: expected empty, got %r" % actual)
        else:
            self.verify_equal(expand(expected), actual, "saved " + field)

    def open_settings(self):
        if "modedit.php" in self.m.d.current_url:
            return
        link = "xpath=//a[contains(@href,'modedit.php?update=')]"
        if not self.m.exists(link):
            raise AssertionError("Settings link not found on " + self.m.d.current_url)
        self.m.open(self.m.attribute(link, "href"))
        self.m.expand_all()

    def open_activity_settings(self, name):
        self.m.open("/course/view.php?name=" + config.COURSE_SHORTNAME)
        self.m.click("xpath=//a[contains(@href,'/mod/assign/view.php?id=') and contains(normalize-space(.),%s)]"
                     % xpath_literal(name))
        self.open_settings()

    # ------------------------------------------------------------------ fixture helpers
    @classmethod
    def ensure_time_limit_enabled(cls):
        m = cls.m
        m.open("/admin/settings.php?section=modsettingassign")
        cb = "id=id_s_assign_enabletimelimit"
        if m.exists(cb) and not m.find(cb).is_selected():
            m.set_checkbox(cb, True)
            m.submit("xpath=//button[normalize-space(.)='Save changes']")

    @classmethod
    def ensure_grouping(cls):
        m = cls.m
        m.open("/group/index.php?id=%d" % cls.cid)
        if not any(o.text.strip() == "G1" for o in Select(m.find("id=groups")).options):
            m.click("xpath=//button[normalize-space(.)='Create group']")
            m.wait("id=id_name", visible=True)
            m.type("id=id_name", "G1")
            m.submit("id=id_submitbutton")

        m.open("/group/groupings.php?id=%d" % cls.cid)
        if "G1" not in m.text("id=region-main"):
            m.click("xpath=//button[normalize-space(.)='Create grouping']")
            m.wait("id=id_name", visible=True)
            m.type("id=id_name", "G1")
            m.submit("id=id_submitbutton")

        m.open("/group/groupings.php?id=%d" % cls.cid)
        rows = m.d.find_elements(By.XPATH, "//tr[td[normalize-space(.)='G1']]")
        if rows and "None" in rows[0].text:
            assign = rows[0].find_elements(By.XPATH, ".//a[contains(@href,'/group/assign.php?id=')]")
            if assign:
                m.open(assign[0].get_attribute("href"))
                options = m.d.find_elements(By.CSS_SELECTOR, "select#addselect option")
                if options:
                    m.d.execute_script("arguments[0].selected=true;", options[0])
                    m.submit("id=add")

    @classmethod
    def remove_grouping(cls):
        """Best-effort removal of the temporary G1 grouping/group."""
        try:
            m = cls.m
            m.open("/group/groupings.php?id=%d" % cls.cid)
            for link in m.d.find_elements(By.XPATH, "//tr[td[normalize-space(.)='G1']]//a[contains(@href,'grouping.php') and contains(@href,'delete=1')]"):
                m.open(link.get_attribute("href"))
            m.open("/group/index.php?id=%d" % cls.cid)
            for link in m.d.find_elements(By.XPATH, "//tr[td[normalize-space(.)='G1']]//a[contains(@href,'group.php') and contains(@href,'delete=1')]"):
                m.open(link.get_attribute("href"))
        except Exception as e:
            print("  note: grouping cleanup skipped: %s" % str(e).splitlines()[0])


def xpath_literal(s):
    if "'" not in s:
        return "'%s'" % s
    return "concat('%s')" % "', \"'\", '".join(s.split("'"))


if __name__ == "__main__":
    unittest.main()
