"""F005 Auto-create groups - Level 1 data-driven test (member: Duong Cong Chi Dung).

The 63 cases TC-005-001 ... TC-005-063 of Project #2 are grouped by how they run; each group is one
automated test fed by one data file:
    data/preview.csv    fill the form, press Preview, check the preview table or the field errors
    data/create.csv     fill the form, press Submit (Create groups), check the groups that were created
    data/scenarios.csv  cases that need data prepared first (existing groups/grouping, suspended user)
                        or a second step (correct a value, cancel)
The data files hold only test data and expected results; page addresses and locators are in this script.

Data columns
    precondition   groups=<scheme>;<count>;<allocation> | grouping=<scheme>;<count>;<grouping name> |
                   suspend=<username>          (prepared before the case, removed after it)
    namingscheme ... groupingname   form fields (blank = default); checkboxes: on/off
    action         preview | create | cancel | none
    expected_result checks separated by " | ":
        groups=N / users=N            preview header "Groups (N)" / "User count (N)"
        rowK.name= rowK.members= rowK.count=   cells of preview row K
        no_members_column             preview has no "Group members" column (No allocation)
        error.<field>=<message>       message under the field ("*" = any non-empty message)
        no_text=<text>                text that must not appear on the page (exception messages)
        group=<option>  no_group=<prefix>  no_groups   groups listed on the Groups page
        grouping=<name>: <groups>     row of the Groupings page
        messaging=<group option>: Yes|No   "Group messaging" stored for that group
        nosmallgroups=enabled|disabled     state of "Prevent last small group"
    then_set / then_action / then_expected   optional second step on the same form
    known_defect   defect the case is expected to expose (the case then fails on purpose)
"""
import re
import unittest

from selenium.webdriver.common.by import By

from common import config
from common.base import MoodleTestCase
from common.data import expand, split
from common.ddt import data_driven

FIELDS = ["namingscheme", "groupby", "number", "roleid", "allocateby", "nosmallgroups", "notingroup",
          "includeonlyactiveenrol", "enablemessaging", "grouping", "groupingname"]
SELECTS = {"groupby", "roleid", "allocateby", "enablemessaging", "grouping"}
CHECKBOXES = {"nosmallgroups", "notingroup", "includeonlyactiveenrol"}
BUTTONS = {"preview": "id=id_preview", "create": "id=id_submitbutton", "cancel": "id=id_cancel"}
PREVIEW = "//table[contains(@class,'generaltable')]"
COLUMN = {"name": 1, "members": 2, "count": 3}


def checks(cell):
    """'a=x | b=y | flag' -> [('a', 'x'), ('b', 'y'), ('flag', None)]"""
    out = []
    for part in split(cell, "|"):
        key, eq, value = part.partition("=")
        out.append((key.strip(), expand(value.strip()) if eq else None))
    return out


@data_driven("data/preview.csv", "data/create.csv", "data/scenarios.csv")
class F005AutoCreateGroups(MoodleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cid = cls.m.course_id(config.COURSE_SHORTNAME)
        cls.reset_groups()  # PREP-005: start without groups/groupings

    @classmethod
    def tearDownClass(cls):
        cls.reset_groups()  # POST-005
        super().tearDownClass()

    # ------------------------------------------------------------------ one test case
    def run_case(self, row):
        if row["action"] == "create" or row["then_action"] == "create" or row["precondition"]:
            self.addCleanup(self.reset_groups)
        self.prepare(row["precondition"])

        self.open_form()
        self.fill([(f, row[f]) for f in FIELDS if row[f]])
        self.act(row["action"])
        self.check(row["expected_result"])

        if row["then_set"] or row["then_action"]:
            self.fill([(k, v) for k, v in (p.split("=", 1) for p in split(row["then_set"], "|"))])
            self.act(row["then_action"])
            self.check(row["then_expected"])

    # ------------------------------------------------------------------ steps
    def open_form(self):
        self.m.open("/group/autogroup.php?courseid=%d" % self.cid)
        self.verify_text("xpath=//div[@role='main']//h2", "Auto-create groups", "form heading")
        self.m.expand_all()

    def fill(self, pairs):
        m = self.m
        for field, cell in pairs:
            field, value = field.strip(), expand(cell)
            loc = "id=id_" + field
            if field in SELECTS:
                m.select(loc, value)
            elif field in CHECKBOXES:
                m.set_checkbox(loc, value.lower() in ("on", "yes", "1", "true"))
            else:
                m.type(loc, value)

    def act(self, action):
        if action in BUTTONS:
            self.m.submit(BUTTONS[action])
        elif action not in ("", "none"):
            raise ValueError("unknown action %r" % action)

    def check(self, cell):
        m = self.m
        for key, exp in checks(cell):
            if key == "groups":
                self.verify_text(PREVIEW + "/thead/tr/th[1]", "Groups (%s)" % exp, "preview: number of groups")
            elif key == "users":
                self.verify_text(PREVIEW + "/thead/tr/th[3]", "User count (%s)" % exp, "preview: user count")
            elif re.match(r"row\d+\.", key):
                r, col = key[3:].split(".")
                self.verify_text("%s/tbody/tr[%s]/td[%d]" % (PREVIEW, r, COLUMN[col]), exp, "preview " + key)
            elif key == "no_members_column":
                self.verify_not_present("xpath=%s/thead/tr/th[2]" % PREVIEW, "Group members column")
            elif key.startswith("error."):
                field = key[6:]
                if exp == "*":
                    self.verify(m.field_error(field) != "", "an error message is expected under '%s'" % field)
                else:
                    self.verify_field_error(field, exp)
            elif key == "no_text":
                self.verify(exp not in m.page_text(), "page must not show %r" % exp)
            elif key == "group":
                self.verify_present("xpath=//select[@id='groups']//option[normalize-space(.)=%s]" % lit(exp),
                                    "group '%s' on the Groups page" % exp)
            elif key == "no_group":
                self.verify_not_present("xpath=//select[@id='groups']//option[starts-with(normalize-space(.),%s)]"
                                        % lit(exp), "group starting with '%s'" % exp)
            elif key == "no_groups":
                m.open("/group/index.php?id=%d" % self.cid)
                self.verify_not_present("xpath=//select[@id='groups']//option", "any group")
            elif key == "grouping":
                name, groups = [x.strip() for x in exp.split(":", 1)]
                m.open("/group/groupings.php?id=%d" % self.cid)
                row = "//table[contains(@class,'generaltable')]/tbody/tr[td[1][normalize-space(.)=%s]]" % lit(name)
                self.verify_text("xpath=%s/td[2]" % row, groups, "groups of grouping " + name)
            elif key == "messaging":
                option, want = [x.strip() for x in exp.rsplit(":", 1)]
                el = m.d.find_elements(By.XPATH, "//select[@id='groups']//option[normalize-space(.)=%s]" % lit(option))
                if self.verify(bool(el), "group '%s' on the Groups page" % option):
                    m.open("/group/group.php?courseid=%d&id=%s" % (self.cid, el[0].get_attribute("value")))
                    self.verify_equal(want, m.selected_label("id=id_enablemessaging"), "Group messaging of " + option)
            elif key == "nosmallgroups":
                self.verify_equal(exp == "enabled", m.find("id=id_nosmallgroups").is_enabled(),
                                  "'Prevent last small group' enabled")
            else:
                raise ValueError("unknown check %r" % key)

    # ------------------------------------------------------------------ preconditions / cleanup
    def prepare(self, cell):
        for key, value in checks(cell):
            args = split(value)
            if key == "groups":       # scheme; count; allocation
                self.open_form()
                self.fill([("namingscheme", args[0]), ("number", args[1]), ("allocateby", args[2])])
                self.act("create")
                self.verify_present("id=showautocreategroupsform", "precondition groups created")
            elif key == "grouping":   # scheme; count; grouping name
                self.open_form()
                self.fill([("namingscheme", args[0]), ("number", args[1]), ("grouping", "New grouping"),
                           ("groupingname", args[2])])
                self.act("create")
                self.verify_present("id=showautocreategroupsform", "precondition grouping created")
            elif key == "suspend":
                self.set_enrolment_status(value, "Suspended")
                self.addCleanup(self.set_enrolment_status, value, "Active")
            else:
                raise ValueError("unknown precondition %r" % key)

    def set_enrolment_status(self, username, status):
        m = self.m
        m.open("/user/index.php?id=%d&perpage=5000" % self.cid)
        link = "xpath=//tr[contains(.,'%s@example.com')]//a[@data-action='editenrolment']" % username
        m.open(m.attribute(link, "href"))
        m.select("id=id_status", status)
        m.submit("id=id_submitbutton")

    @classmethod
    def reset_groups(cls):
        """Course reset with only 'Delete all groups' and 'Delete all groupings' (as PREP/POST-005)."""
        m = cls.m
        m.open("/course/reset.php?id=%d" % cls.cid)
        m.click("id=id_deselectall")
        m.expand_all()
        m.set_checkbox("id=id_reset_groups_remove", True)
        m.set_checkbox("id=id_reset_groupings_remove", True)
        m.click("id=id_submitbutton")
        m.submit("xpath=//div[contains(@class,'modal') and contains(@class,'show')]//button[@data-action='delete']")
        m.wait("xpath=//table//tr[td[normalize-space(.)='All groups'] and td[normalize-space(.)='Done']]")


def lit(s):
    """XPath string literal for any text."""
    if "'" not in s:
        return "'%s'" % s
    return "concat('%s')" % "', \"'\", '".join(s.split("'"))


if __name__ == "__main__":
    unittest.main()
