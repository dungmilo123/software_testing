"""F001 Quiz Settings - Level 1 data-driven test (member: Tran Ngoc Thoai, 2353147).

All 81 test cases (TC-001-001 .. TC-001-081) from Project #2 are grouped by execution pattern
into four CSV files under data/:
    data/create_valid.csv       43 valid creation cases (Save and return / Save and display)
    data/validation_errors.csv  28 invalid input / validation cases (including 6 known defects)
    data/ui_rules.csv            4 Decision Table dynamic UI dependency checks
    data/scenarios.csv           6 Use-Case end-to-end scenarios (S1, S3-S7)

Page URLs and element locators stay in this script (Level 1); the CSV files hold only
test data and expected results.
"""
import unittest

from selenium.webdriver.common.by import By

from common import config
from common.base import MoodleTestCase
from common.data import expand, split
from common.ddt import data_driven

FIELDS = [
    "name", "introeditor", "showdescription",
    "timeopen", "timeclose", "timelimit_enabled", "timelimit_number", "timelimit_timeunit",
    "overduehandling", "graceperiod_enabled", "graceperiod_number", "graceperiod_timeunit",
    "gradepass", "attempts", "grademethod",
    "questionsperpage", "navmethod",
    "shuffleanswers", "preferredbehaviour", "canredoquestions", "attemptonlast",
    "marksduring", "attemptimmediately", "rightansweropen", "overallfeedbackclosed",
    "showuserpicture", "decimalpoints", "questiondecimalpoints", "showblocks",
    "seb_requiresafeexambrowser", "seb_linkquitseb", "seb_quitpassword",
    "seb_activateurlfiltering", "seb_allowedbrowserexamkeys",
    "quizpassword", "subnet",
    "delay1_enabled", "delay1_number", "delay1_timeunit",
    "delay2_enabled", "delay2_number", "delay2_timeunit",
    "browsersecurity",
    "feedbacktext_0", "feedbackboundaries_0", "feedbacktext_1", "feedbackboundaries_1",
]
DATES = {"timeopen", "timeclose"}
EDITORS = {"introeditor", "feedbacktext_0", "feedbacktext_1"}
SELECTS = {
    "timelimit_timeunit", "overduehandling", "graceperiod_timeunit",
    "attempts", "grademethod", "questionsperpage", "navmethod",
    "shuffleanswers", "preferredbehaviour", "canredoquestions", "attemptonlast",
    "showuserpicture", "decimalpoints", "questiondecimalpoints", "showblocks",
    "seb_requiresafeexambrowser", "seb_activateurlfiltering",
    "delay1_timeunit", "delay2_timeunit", "browsersecurity",
}
CHECKBOXES = {
    "showdescription", "timelimit_enabled", "graceperiod_enabled",
    "marksduring", "attemptimmediately", "rightansweropen", "overallfeedbackclosed",
    "maxmarksduring", "delay1_enabled", "delay2_enabled", "repaginatenow",
}
PASSWORDS = {"quizpassword", "seb_quitpassword"}
BUTTONS = {
    "save_display": "id=id_submitbutton",
    "save_return": "id=id_submitbutton2",
    "cancel": "id=id_cancel",
}


def checks(cell):
    """'a=x | b=y | flag' -> [('a', 'x'), ('b', 'y'), ('flag', None)]"""
    out = []
    for part in split(cell, "|"):
        key, eq, value = part.partition("=")
        out.append((key.strip(), expand(value.strip()) if eq else None))
    return out


@data_driven(
    "data/create_valid.csv",
    "data/validation_errors.csv",
    "data/ui_rules.csv",
    "data/scenarios.csv",
)
class F001QuizSettings(MoodleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cid = cls.m.course_id(config.COURSE_SHORTNAME)
        cls.m.delete_activities("quiz")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.m.delete_activities("quiz")
        finally:
            super().tearDownClass()

    # ------------------------------------------------------------------ dispatch
    def run_case(self, row):
        datafile = row.get("_datafile", "")
        if "ui_rules" in datafile or "init_check" in row:
            self._run_ui_rule(row)
        elif "scenario" in row:
            self._run_scenario(row)
        elif "action" in row:
            self._run_create_valid(row)
        else:
            self._run_validation_error(row)

    def _run_create_valid(self, row):
        self.addCleanup(self.m.delete_activities, "quiz")
        self.open_form()
        self.fill([(f, row[f]) for f in FIELDS if row.get(f)])
        self.m.submit(BUTTONS[row["action"]])
        self.check(row["expected_result"])

    def _run_validation_error(self, row):
        # Cleanup protects KTC01 when defect cases (D-03, D-04, D-05) erroneously save a quiz.
        self.addCleanup(self.m.delete_activities, "quiz")
        self.open_form()
        if row.get("add_feedback_fields", "").lower() == "yes":
            self.add_more_feedback_fields()
        self.fill([(f, row[f]) for f in FIELDS if row.get(f)])
        self.m.submit(BUTTONS["save_return"])
        self.check(row["expected_result"])

    def _run_ui_rule(self, row):
        self.open_form()
        if row["init_check"]:
            self.check(row["init_check"])
        if row["step1_set"]:
            self.fill(self._kv_pairs(row["step1_set"]))
        if row["step1_check"]:
            self.check(row["step1_check"])
        if row["step2_set"]:
            self.fill(self._kv_pairs(row["step2_set"]))
        if row["step2_check"]:
            self.check(row["step2_check"])

    def _run_scenario(self, row):
        sc = row["scenario"]
        if sc != "cancel":
            self.addCleanup(self.m.delete_activities, "quiz")
        self.open_form()
        if sc == "add_feedback_save":
            self.add_more_feedback_fields()
        self.fill([(f, row[f]) for f in FIELDS if row.get(f)])

        if sc in ("save_display", "add_feedback_save"):
            btn = "save_display" if sc == "save_display" else "save_return"
            self.m.submit(BUTTONS[btn])
            self.check(row["expected_result"])
        elif sc == "cancel":
            self.m.submit(BUTTONS["cancel"])
            self.check(row["expected_result"])
        elif sc == "edit_repaginate":
            self.m.submit(BUTTONS["save_display"])
            self.check(row["expected_result"])
            self.m.submit("xpath=//a[contains(@href,'modedit.php?update=')]")
            self.verify_present("id=id_repaginatenow", "Repaginate now checkbox on edit form")
            self.expand_form_sections()
            self.fill(self._kv_pairs(row["then_set"]))
            self.m.submit(BUTTONS[row["then_action"]])
            self.check(row["then_expected"])
        elif sc in ("error_fix_save", "error_cancel"):
            first_btn = "save_display" if sc == "error_fix_save" else "save_return"
            self.m.submit(BUTTONS[first_btn])
            self.check(row["expected_result"])
            if row["then_set"]:
                self.fill(self._kv_pairs(row["then_set"]))
            self.m.submit(BUTTONS[row["then_action"]])
            self.check(row["then_expected"])
        else:
            raise ValueError("unknown scenario %r" % sc)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _kv_pairs(cell):
        pairs = []
        for part in split(cell, "|"):
            k, _, v = part.partition("=")
            pairs.append((k.strip(), v.strip()))
        return pairs

    def open_form(self):
        self.m.open("/course/modedit.php?add=quiz&type=&course=%d&section=0&return=0" % self.cid)
        self.verify_text("css=#region-main h2", "New Quiz", "form heading")
        self.expand_form_sections()

    def expand_form_sections(self):
        self.m.expand_all()
        for hdr in self.m.d.find_elements(By.CSS_SELECTOR, "fieldset.collapsible a.fheader.collapsed"):
            self.m.d.execute_script("arguments[0].scrollIntoView({block:'center'});", hdr)
            self.m.d.execute_script("arguments[0].click();", hdr)
        for toggler in self.m.d.find_elements(By.CSS_SELECTOR, "a.moreless-toggler"):
            if toggler.is_displayed() and "Show more" in (toggler.text or ""):
                self.m.d.execute_script("arguments[0].scrollIntoView({block:'center'});", toggler)
                self.m.d.execute_script("arguments[0].click();", toggler)
        self.m.pause(200)

    def add_more_feedback_fields(self):
        self.m.submit("id=id_boundary_add_fields")
        self.m.wait("id=id_feedbackboundaries_1")
        self.expand_form_sections()

    def fill(self, pairs):
        m = self.m
        for field, cell in pairs:
            field, value = field.strip(), expand(cell)
            if value is None:
                continue
            if field in DATES:
                m.set_date("id_" + field, value)
            elif field in EDITORS:
                m.set_editor("id_" + field, value)
            elif field in SELECTS:
                m.select("id=id_" + field, value)
            elif field in CHECKBOXES:
                m.set_checkbox("id=id_" + field, value.lower() in ("on", "yes", "1", "true", "checked"))
            else:
                if field in PASSWORDS:
                    edit_btn = "css=#fitem_id_%s [data-passwordunmask='edit']" % field
                    if m.visible(edit_btn):
                        m.click(edit_btn)
                m.type("id=id_" + field, value)

    def check(self, cell):
        m = self.m
        for key, exp in checks(cell):
            if key in ("quiz", "quiz_present", "no_quiz", "course_desc") and "/course/view.php" not in m.d.current_url:
                m.open("/course/view.php?name=" + config.COURSE_SHORTNAME)
            if key == "quiz":
                self.verify_present(
                    "xpath=//li[contains(@class,'activity') and contains(@class,'quiz')]"
                    "//a[contains(normalize-space(.),%s)]" % lit(exp),
                    "quiz '%s' on course page" % exp,
                )
            elif key == "quiz_present":
                self.verify_present("css=li.activity.quiz", "quiz activity on course page")
            elif key == "no_quiz":
                self.verify_not_present("css=li.activity.quiz", "any quiz activity")
            elif key == "course_desc":
                self.verify_present(
                    "xpath=//li[contains(@class,'activity') and contains(@class,'quiz')]"
                    "[contains(.,%s)]" % lit(exp),
                    "course description containing %r" % exp,
                )
            elif key == "heading":
                self.verify_text("css=h1", exp, "page heading")
            elif key == "region_contains":
                self.verify_contains("id=region-main", exp, "region-main")
            elif key.startswith("error."):
                field = key[6:]
                if exp == "*":
                    self.verify(m.field_error(field) != "", "an error message is expected under '%s'" % field)
                else:
                    self.verify_field_error(field, exp)
            elif key == "no_text":
                if exp.startswith("."):
                    self.verify_not_present("css=" + exp, "element %s" % exp)
                else:
                    self.verify(exp not in m.page_text(), "page must not show %r" % exp)
            elif key == "form_present":
                self.verify_present("id=id_name", "still on Quiz settings form")
            elif key == "visible":
                self.verify(m.visible("id=" + exp), "element %s should be visible" % exp)
            elif key == "not_visible":
                self.verify(not m.visible("id=" + exp), "element %s should be hidden" % exp)
            elif key == "enabled":
                self.verify(m.find("id=" + exp).is_enabled(), "element %s should be enabled" % exp)
            elif key == "disabled":
                self.verify(not m.find("id=" + exp).is_enabled(), "element %s should be disabled" % exp)
            elif key == "present":
                self.verify_present("id=" + exp, "element %s" % exp)
            else:
                raise ValueError("unknown check %r" % key)


def lit(s):
    """XPath string literal for any text."""
    if "'" not in s:
        return "'%s'" % s
    return "concat('%s')" % "', \"'\", '".join(s.split("'"))


if __name__ == "__main__":
    unittest.main()
