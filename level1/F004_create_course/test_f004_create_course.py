"""F004 Create course - Level 1 data-driven test (member: Luong Tan Tai).

One automated test case drives the "Add a new course" form for every row of data/create_course.csv
(TC-004-001 ... TC-004-065 of Project #2). The data file holds only test data and expected results;
the page addresses and element locators are written in this script (Level 1).

Data columns
    fullname ... summary   value typed/selected in the form field of the same name (blank = keep default)
                           dates: YYYY | YYYY-MM-DD | YYYY-MM-DD HH:MM | off
    button                 saveanddisplay | saveandreturn | cancel | none (do not submit)
    expected_outcome       created | error | not_created | options | maxlength
    expected_result        created     -> course heading (Save and display) / course link (Save and return)
                           error       -> "field: message | field: message" shown under the fields
                           not_created -> text of the course search when nothing was saved
                           options     -> "select: value;value;!absent_value"
                           maxlength   -> "field: N" = the browser keeps only N characters
    expected_saved         "field: value | ..." read back from the course settings form after saving
    fix_field/fix_value/fix_button/expected_after_fix   second attempt of the use-case scenarios
    cleanup                text used to find and delete the course afterwards (default: shortname)
    known_defect           defect the case is expected to expose (the case then fails on purpose)
"""
import unittest

from common import config
from common.base import MoodleTestCase
from common.data import expand, split
from common.ddt import data_driven

ADD_FORM = "/course/edit.php?category=1"
ADD_FORM_RETURN = "/course/edit.php?category=1&returnto=catmanage"   # shows the "Save and return" button
TEXT_FIELDS = ["fullname", "shortname", "idnumber"]
SELECT_FIELDS = ["visible", "format", "newsitems", "showgrades", "showreports", "showactivitydates",
                 "enablecompletion", "groupmode", "groupmodeforce"]
DATE_FIELDS = ["startdate", "enddate"]
BUTTONS = {"saveanddisplay": "id=id_saveanddisplay", "saveandreturn": "id=id_saveandreturn",
           "cancel": "id=id_cancel"}
NOT_FOUND = "No courses were found"


def pairs(cell):
    """'a: x | b: y' -> [('a', 'x'), ('b', 'y')]"""
    out = []
    for part in split(cell, "|"):
        field, _, value = part.partition(":")
        out.append((field.strip(), expand(value.strip())))
    return out


@data_driven("data/create_course.csv")
class F004CreateCourse(MoodleTestCase):

    def run_case(self, row):
        m = self.m
        search = row["cleanup"] or expand(row["shortname"])
        if search and search.strip() and search != config.COURSE_SHORTNAME:
            self.addCleanup(m.delete_courses, search)

        m.open(ADD_FORM_RETURN if "saveandreturn" in (row["button"], row["fix_button"]) else ADD_FORM)
        self.verify_text("css=h2", "Add a new course", "form heading")
        self.fill(row)

        outcome, expected = row["expected_outcome"], row["expected_result"]
        if outcome == "maxlength":
            for field, length in pairs(expected):
                self.verify_equal(int(length), len(m.value("id=id_" + field)), "characters kept in " + field)
            return
        if outcome == "options":
            for field, values in pairs(expected):
                offered = m.options("id=id_" + field)
                for v in split(values):
                    if v.startswith("!"):
                        self.verify(v[1:] not in offered, "%s must not offer %s" % (field, v[1:]))
                    else:
                        self.verify(v in offered, "%s must offer %s (offered: %s)" % (field, v, offered))
            return

        m.submit(BUTTONS[row["button"]])
        self.check(outcome, row["button"], expected, row)

        if row["fix_button"]:  # use-case scenario: correct the form (or give up) and submit again
            if row["fix_field"]:
                self.set_field(row["fix_field"], row["fix_value"])
            m.submit(BUTTONS[row["fix_button"]])
            after = "not_created" if row["fix_button"] == "cancel" else "created"
            self.check(after, row["fix_button"], row["expected_after_fix"], row)

    # ------------------------------------------------------------------ steps
    def fill(self, row):
        if any(row[f] for f in SELECT_FIELDS):
            self.m.expand_all()
        for field in TEXT_FIELDS + DATE_FIELDS + SELECT_FIELDS + ["summary"]:
            if row[field]:
                self.set_field(field, row[field], keyboard=row["expected_outcome"] == "maxlength")

    def set_field(self, field, cell, keyboard=False):
        m, value = self.m, expand(cell)
        if field in DATE_FIELDS:
            m.set_date("id_" + field, value)
        elif field in SELECT_FIELDS:
            m.select("id=id_" + field, value)
        elif field == "summary":
            m.set_editor("id_summary_editor", value)
        else:
            m.type("id=id_" + field, value, keyboard=keyboard)

    def check(self, outcome, button, expected, row):
        m = self.m
        if outcome == "error":
            self.verify_present("id=id_fullname", "still on the course form")
            for field, message in pairs(expected):
                self.verify_field_error(field, message)
        elif outcome == "created":
            if button == "saveandreturn":  # back on Manage courses and categories, new course listed
                self.verify_present("xpath=//a[normalize-space(.)=%s]" % xpath_literal(expand(expected)),
                                    "course '%s' in the management list" % expected)
            else:                          # course page opened
                self.verify_text("css=h1", expand(expected), "course page heading")
            if row["expected_saved"]:
                self.check_saved(row)
        elif outcome == "not_created":
            self.verify_not_present("id=id_fullname", "form closed after Cancel")
            m.open("/course/management.php?search=" + (row["cleanup"] or expand(row["shortname"])))
            self.verify_contains("id=region-main", expected, "course search after Cancel")
        else:
            raise ValueError("unknown expected_outcome %r" % outcome)

    def check_saved(self, row):
        """Re-open the settings of the new course and compare the stored values."""
        m = self.m
        ids = [i for i in m.find_course_ids(row["cleanup"] or expand(row["shortname"]))]
        if not self.verify(len(ids) == 1, "exactly one course created (found %d)" % len(ids)):
            return
        m.open("/course/edit.php?id=%d" % ids[0])
        m.expand_all()
        for field, value in pairs(row["expected_saved"]):
            if field in SELECT_FIELDS:
                self.verify_equal(value, m.selected_label("id=id_" + field), "saved " + field)
            elif field == "summary":
                self.verify_equal(value, m.editor_text("id_summary_editor"), "saved summary")
            else:
                self.verify_value("id=id_" + field, value, "saved " + field)


def xpath_literal(s):
    if "'" not in s:
        return "'%s'" % s
    return "concat('%s')" % "', \"'\", '".join(s.split("'"))


if __name__ == "__main__":
    unittest.main()
