"""F003 Add/edit grade item - Level 1 data-driven test.

The 80 cases TC-003-001 ... TC-003-080 of Project #2 are grouped by how they run; each group is fed by one
data file, and all four use the same columns and the same steps:
    data/add_valid.csv     fill the full "New grade item" form, Save, check the Gradebook setup row, reopen
                           the item with Edit and check the stored values
    data/add_invalid.csv   fill the full form, Save, check the message under the field, Cancel, check that
                           nothing was saved (includes the defect cases D003-01..04)
    data/form_rules.csv    dependencies between fields (disabledIf rules) checked on the open form
    data/scenarios.csv     use-case scenarios S2-S10: quick dialog, cancel, edit, correct and save, graded
                           item with rescaling, weights, categories, course total overflow (D003-05)
The data files hold only test data and expected results; page addresses and locators are in this script.

Steps of one case:  precondition -> open form -> before_expected -> fill -> action -> expected_result
                    -> then_set -> then_action -> then_expected  (clean-up always runs afterwards)

Data columns
    precondition   things created first, separated by " | ":
                   item=<name>;<maximum>[;<ID number>[;<decimals>]]   grade item made through the full form
                   grade=<item>;<student full name>;<grade>           grade entered in Single view
                   category=<name>                                     grade category (Add category dialog)
    form           full | quick | edit:<item name> | none   (full = Add > Add grade item > Show more...)
    itemname ... parentcategory   form fields (blank = keep default, {{EMPTY}} = clear);
                   checkboxes: on/off;  locktime / hiddenuntil: YYYY-MM-DD
    action         save | cancel | quick_save | quick_cancel | none
    before_expected / expected_result / then_expected   checks separated by " | ":
        row=<item> / no_row=<item>          row in Gradebook setup is listed / not listed
        range=<item>: <text>                Max grade column of the row
        icon=<item>: <title>                status icon of the row (Hidden, Locked)
        extra_credit=<item>                 the Max grade is marked as extra credit
        weight=<item>: <value>              weight input of the row
        category=<name>                     grade category row is listed
        edit=<item>                         open the item with Edit grade item > Show more...
        value.<field>=<v>                   value of the field on the open form (selects: option value)
        checked.<field> unchecked.<field> enabled.<field> disabled.<field> present.<field> absent.<field>
        static.<field>=<text>               the field is shown as text containing <text>
        error.<field>=<message>             message under the field ("*" = any non-empty message)
        no_text=<text>                      text that must not appear on the page
        modal_title=<text>                  title of the open dialog
        grade=<item>: <student>: <grade>    grade of the student in Single view
        cancel                              click Cancel on the open form
    then_set       field=value | field=value     second step on the same form
    cleanup        items (default: delete every grade item/category through the row menus) |
                   reset (course reset of the gradebook, needed after D003-05)
    known_defect   defect the case is expected to expose (the case then fails on purpose: the expected
                   result is the specified behaviour, not the observed one)
"""
import unittest

from selenium.common.exceptions import WebDriverException

from common import config
from common.base import MoodleTestCase
from common.data import expand, split
from common.ddt import data_driven

# Order matters: a checkbox / select that enables another field is set before that field.
FIELDS = ["itemname", "iteminfo", "idnumber", "gradetype", "scaleid", "rescalegrades", "grademax", "grademin",
          "gradepass", "display", "decimals", "hidden", "hiddenuntil_enabled", "hiddenuntil", "locked",
          "locktime_enabled", "locktime", "weightoverride", "aggregationcoef2", "aggregationcoef",
          "parentcategory"]
SELECTS = {"gradetype", "scaleid", "rescalegrades", "display", "decimals", "parentcategory"}
CHECKBOXES = {"hidden", "hiddenuntil_enabled", "locked", "locktime_enabled", "weightoverride", "aggregationcoef"}
DATES = {"hiddenuntil", "locktime"}

SETUP_PAGE = "/grade/edit/tree/index.php?id=%d"
ADD_MENU = "xpath=//a[@role='button' and @aria-label='Add']"
ADD_ITEM = "xpath=//a[@role='menuitem' and normalize-space(.)='Add grade item']"
ADD_CATEGORY = "xpath=//a[@role='menuitem' and normalize-space(.)='Add category']"
MODAL = "css=.modal.show"
SHOW_MORE = "css=.modal.show a.showadvancedform"
DB_ERROR = "xpath=//p[contains(@class,'errormessage')]"


def lit(s):
    """XPath string literal for any text."""
    if "'" not in s:
        return "'%s'" % s
    return "concat('%s')" % "', \"'\", '".join(s.split("'"))


def row_xp(name):
    return ("//tr[@data-itemid][.//span[contains(@class,'gradeitemheader') and normalize-space(.)=%s]]"
            % lit(name))


def category_xp(name):
    return "//tr[@data-category][.//div[@class='rowtitle' and normalize-space(.)=%s]]" % lit(name)


def checks(cell):
    """'a=x | b: y | flag' -> [('a', 'x'), ('flag', None)] (values decoded with the cell notation)."""
    out = []
    for part in split(cell, "|"):
        key, eq, value = part.partition("=")
        out.append((key.strip(), expand(value.strip()) if eq else None))
    return out


def pair(value):
    """'<name>: <text>' -> ('<name>', '<text>')"""
    name, _, text = value.partition(": ")
    return name.strip(), text.strip()


@data_driven("data/add_valid.csv", "data/add_invalid.csv", "data/form_rules.csv", "data/scenarios.csv")
class F003GradeItem(MoodleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cid = cls.m.course_id(config.COURSE_SHORTNAME)
        cls.reset_gradebook()  # PREP-003: start with an empty gradebook

    @classmethod
    def tearDownClass(cls):
        try:
            cls.reset_gradebook()  # POST-003
        finally:
            super().tearDownClass()

    # ------------------------------------------------------------------ one test case
    def run_case(self, row):
        self.quick = False
        self.addCleanup(self.cleanup, row.get("cleanup") or "items")
        self.prepare(row.get("precondition", ""))
        self.open_form(row.get("form", ""))
        self.check(row.get("before_expected", ""))
        self.fill([(f, row[f]) for f in FIELDS if row.get(f)])
        self.act(row.get("action", ""))
        self.check(row.get("expected_result", ""))
        if row.get("then_set") or row.get("then_action"):
            self.fill([(k.strip(), v.strip()) for k, v in (p.split("=", 1) for p in split(row["then_set"], "|"))])
            self.act(row.get("then_action", ""))
            self.check(row.get("then_expected", ""))

    # ------------------------------------------------------------------ navigation
    def open_setup(self):
        m = self.m
        m.open(SETUP_PAGE % self.cid)
        m.dismiss_tour()
        m.pause(1000)  # the Add / row menus get their JavaScript after the page has loaded

    def on_setup(self):
        if "/grade/edit/tree/index.php" not in self.m.d.current_url or self.m.exists(DB_ERROR):
            self.open_setup()

    def open_dialog(self, menuitem):
        m = self.m
        self.open_setup()
        m.click(ADD_MENU)
        m.click(menuitem)
        m.wait(MODAL + " form", visible=True)
        m.pause(500)

    def show_more(self):
        m = self.m
        m.wait(SHOW_MORE, visible=True)
        m.click(SHOW_MORE)
        m.wait("id=id_itemname")
        m.wait_ready()
        m.pause(1000)  # disabledIf rules of the full form

    def open_form(self, form):
        self.quick = False
        if not form or form == "none":
            return
        if form == "full":
            self.open_dialog(ADD_ITEM)
            self.show_more()
        elif form == "quick":
            self.open_dialog(ADD_ITEM)
            self.quick = True
        elif form.startswith("edit:"):
            self.open_edit(form[5:].strip())
        else:
            raise ValueError("unknown form %r" % form)

    def open_edit(self, name):
        m = self.m
        self.on_setup()
        m.click("xpath=%s//button[contains(@class,'cellmenubtn')]" % row_xp(name))
        m.click("xpath=%s//a[@aria-label='Edit grade item']" % row_xp(name))
        self.show_more()
        self.quick = False

    # ------------------------------------------------------------------ form
    def locator(self, field):
        if self.quick:  # the quick dialog uses random ids: address its fields by name
            return "%s [name='%s']" % (MODAL, field)
        return "id=id_" + field

    def fill(self, pairs):
        m = self.m
        for field, cell in pairs:
            value = expand(cell)
            if value is None:
                continue
            if field in SELECTS:
                m.select(self.locator(field), value)
            elif field in CHECKBOXES:
                m.set_checkbox(self.locator(field), value.lower() in ("on", "yes", "1", "true"))
            elif field in DATES:
                m.set_date("id_" + field, value)
            else:
                m.type(self.locator(field), value)

    def act(self, action):
        m = self.m
        if action == "save":
            m.submit("id=id_submitbutton")
        elif action == "cancel":
            m.submit("id=id_cancel")
        elif action in ("quick_save", "quick_cancel"):
            m.click("%s [data-action='%s']" % (MODAL, action[6:]))
            m.wait_gone(MODAL)
            m.wait_ready()
            m.pause(1000)
            self.quick = False
        elif action not in ("", "none"):
            raise ValueError("unknown action %r" % action)

    # ------------------------------------------------------------------ checks
    def check(self, cell):
        m = self.m
        for key, exp in checks(cell):
            if key == "row":
                self.on_setup()
                self.verify_present("xpath=" + row_xp(exp), "row '%s' in Gradebook setup" % exp[:40])
            elif key == "no_row":
                self.on_setup()
                self.verify_not_present("xpath=" + row_xp(exp), "row '%s' in Gradebook setup" % exp[:40])
            elif key == "range":
                name, text = pair(exp)
                self.on_setup()
                self.verify_text("xpath=%s/td[contains(@class,'column-range')]" % row_xp(name), text,
                                 "Max grade of '%s'" % name[:40])
            elif key == "icon":
                name, title = pair(exp)
                self.on_setup()
                self.verify_present("xpath=%s/td[contains(@class,'column-status')]//i[@title=%s]"
                                    % (row_xp(name), lit(title)), "'%s' icon of '%s'" % (title, name))
            elif key == "extra_credit":
                self.on_setup()
                self.verify_present("xpath=%s/td[contains(@class,'column-range')]//abbr[@title='Extra credit']"
                                    % row_xp(exp), "extra credit mark of '%s'" % exp)
            elif key == "weight":
                name, value = pair(exp)
                self.on_setup()
                self.verify_value("xpath=%s//input[starts-with(@name,'weight_')]" % row_xp(name), value,
                                  "weight of '%s'" % name)
            elif key == "category":
                self.on_setup()
                self.verify_present("xpath=" + category_xp(exp), "category '%s'" % exp)
            elif key == "edit":
                self.open_edit(exp)
            elif key.startswith("value."):
                self.verify_value(self.locator(key[6:]), exp, "field " + key[6:])
            elif key.split(".")[0] in ("checked", "unchecked", "enabled", "disabled"):
                state, field = key.split(".", 1)
                try:
                    el = m.find(self.locator(field), timeout=5)
                    actual = el.is_selected() if state in ("checked", "unchecked") else el.is_enabled()
                    self.verify_equal(state in ("checked", "enabled"), actual, "%s state of %s" % (state, field))
                except WebDriverException:
                    self.verify(False, "field %s not found" % field)
            elif key.startswith("present."):
                self.verify_present(self.locator(key[8:]), "field " + key[8:])
            elif key.startswith("absent."):
                self.verify_not_present(self.locator(key[7:]), "editable field " + key[7:])
            elif key.startswith("static."):
                self.verify_contains("id=fitem_id_" + key[7:], exp, "field " + key[7:])
            elif key.startswith("error."):
                field = key[6:]
                if exp == "*":
                    self.verify(m.field_error(field) != "",
                                "a validation message is expected under '%s' (page shows: %s)"
                                % (field, self.page_error() or "no message"))
                else:
                    self.verify_field_error(field, exp)
            elif key == "no_text":
                self.verify(exp not in m.page_text(), "page must not show %r" % exp)
            elif key == "modal_title":
                self.verify_text(MODAL + " .modal-title", exp, "dialog title")
            elif key == "grade":
                item, student, grade = [x.strip() for x in exp.split(": ")]
                self.open_singleview(item)
                self.verify_value(self.grade_input(student), grade, "grade of %s in %s" % (student, item))
            elif key == "cancel":
                m.submit("id=id_cancel")
            else:
                raise ValueError("unknown check %r" % key)

    def page_error(self):
        return self.m.text(DB_ERROR) if self.m.exists(DB_ERROR) else ""

    # ------------------------------------------------------------------ preconditions
    def prepare(self, cell):
        m = self.m
        for key, value in checks(cell):
            args = value.split(";")
            if key == "item":  # name; maximum [; ID number [; decimals]]
                self.open_form("full")
                self.fill([("itemname", args[0]), ("grademax", args[1])]
                          + ([("idnumber", args[2])] if len(args) > 2 and args[2] else [])
                          + ([("decimals", args[3])] if len(args) > 3 and args[3] else []))
                self.act("save")
                self.verify_present("xpath=" + row_xp(args[0]), "precondition item '%s'" % args[0])
            elif key == "category":
                self.open_dialog(ADD_CATEGORY)
                m.type(MODAL + " input[name='fullname']", value)
                m.click(MODAL + " [data-action='save']")
                m.wait("xpath=" + category_xp(value))
                m.wait_ready()
            elif key == "grade":  # item; student; grade
                self.set_grade(*[a.strip() for a in args])
            else:
                raise ValueError("unknown precondition %r" % key)

    def open_singleview(self, item):
        m = self.m
        self.on_setup()
        itemid = m.attribute("xpath=" + row_xp(item), "data-itemid")
        m.open("/grade/report/singleview/index.php?id=%d&item=grade&itemid=%s" % (self.cid, itemid))
        m.pause(1500)

    @staticmethod
    def grade_input(student):
        return ("xpath=//tr[.//a[contains(normalize-space(.),%s)]]//input[starts-with(@name,'finalgrade_')]"
                % lit(student))

    def set_grade(self, item, student, grade):
        m = self.m
        self.open_singleview(item)
        if not m.find("css=input[name='setmode']").is_selected():  # Edit mode is a per-session switch
            m.click("css=input[name='setmode']")
            m.wait_ready()
            m.pause(1500)
        m.type(self.grade_input(student), grade)
        m.submit("xpath=//input[@type='submit' and @value='Save']")
        self.verify_present("xpath=//div[contains(@class,'alert') and contains(.,'Grades were set for 1 items')]",
                            "precondition grade of %s" % student)

    # ------------------------------------------------------------------ clean-up
    def cleanup(self, how):
        if how == "reset":
            self.reset_gradebook()
        else:
            self.delete_all_items()

    def delete_all_items(self):
        """Delete every manual grade item, then every grade category, through the row menus (Delete)."""
        m = self.m
        rows = ("//tr[@data-itemid][contains(@class,'item')][not(contains(@class,'courseitem'))]"
                "[not(contains(@class,'categoryitem'))]",
                "//tr[@data-category][contains(@class,'category')][not(contains(@class,'coursecategory'))]")
        for _ in range(40):
            self.open_setup()
            if m.exists(DB_ERROR):  # gradebook broken (course total overflow): only a reset helps
                self.reset_gradebook()
                return
            target = next((r for r in rows if m.exists("xpath=" + r)), None)
            if target is None:
                return
            first = "xpath=(%s)[1]" % target
            m.click(first + "//button[contains(@class,'cellmenubtn')]")
            m.click(first + "//a[@aria-label='Delete']")
            m.submit("xpath=//div[contains(@class,'modal') and contains(@class,'show')]//button[normalize-space(.)='Delete']")

    @classmethod
    def reset_gradebook(cls):
        """Course reset with only 'Delete all items and categories', then run the queued regrade task."""
        m = cls.m
        m.open("/course/reset.php?id=%d" % cls.cid)
        m.click("id=id_deselectall")
        m.expand_all()
        m.set_checkbox("id=id_reset_gradebook_items", True)
        m.click("id=id_submitbutton")
        m.submit("xpath=//div[contains(@class,'modal') and contains(@class,'show')]//button[@data-action='delete']")
        m.wait("xpath=//table//tr[td[normalize-space(.)='All items and categories'] and td[normalize-space(.)='Done']]")
        # The container has no cron: the regrade queued by the reset is started from the gradebook page.
        m.open("/grade/report/grader/index.php?id=%d" % cls.cid)
        m.dismiss_tour()
        if m.exists("xpath=//a[normalize-space(.)='Run now']"):
            m.submit("xpath=//a[normalize-space(.)='Run now']")
            if m.exists("xpath=//button[normalize-space(.)='Run ad hoc tasks now?']"):
                m.submit("xpath=//button[normalize-space(.)='Run ad hoc tasks now?']")
            m.wait("xpath=//*[contains(text(),'Regrade complete.')]", timeout=60)


if __name__ == "__main__":
    unittest.main()
