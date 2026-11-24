"""Shared test fixture (Python port of the Project #2 suite 00-setup), data-driven.

    data/students.csv  one row per student account to create
    data/course.csv    the course KTC01 and the users to enrol into it

Run once before the feature scripts:  python run_tests.py setup/test_00_setup.py
Re-running is safe: an existing account/course/enrolment is reported and left as it is.
"""
import unittest

from selenium.webdriver.common.by import By

from common.base import MoodleTestCase
from common.data import split
from common.ddt import data_driven


@data_driven("data/students.csv", runner="create_student")
@data_driven("data/course.csv", runner="create_course")
class Setup00(MoodleTestCase):

    def create_student(self, row):
        m = self.m
        m.open("/user/editadvanced.php?id=-1")
        m.type("id=id_username", row["username"])
        m.click("css=#fitem_id_newpassword [data-passwordunmask='edit']")
        m.type("id=id_newpassword", row["password"])
        m.type("id=id_firstname", row["firstname"])
        m.type("id=id_lastname", row["lastname"])
        m.type("id=id_email", row["email"])
        m.submit("id=id_submitbutton")
        if m.field_error("username") == "This username already exists, choose another":
            return  # fixture already present
        self.verify_present("xpath=//a[contains(@href,'/user/profile.php') and contains(normalize-space(.),'%s %s')]"
                            % (row["firstname"], row["lastname"]), "new user listed")

    def create_course(self, row):
        m = self.m
        if not m.find_course_ids(row["shortname"]):
            m.open("/course/edit.php?category=1")
            m.type("id=id_fullname", row["fullname"])
            m.type("id=id_shortname", row["shortname"])
            m.type("id=id_idnumber", row["idnumber"])
            m.submit("id=id_saveanddisplay")
        cid = m.course_id(row["shortname"])
        self.verify_text("css=h1", row["fullname"], "course heading")

        # enrol the students with the manual enrolment method (default role Student)
        m.open("/enrol/instances.php?id=%d" % cid)
        m.submit("xpath=//a[contains(@href,'/enrol/manual/manage.php')]")
        wanted = ["(%s@" % u for u in split(row["enrol_users"])]
        pending = [o for o in m.d.find_elements(By.CSS_SELECTOR, "#addselect option")
                   if any(w in o.text for w in wanted)]
        if pending:
            for o in pending:
                m.d.execute_script("arguments[0].selected=true;", o)
            m.submit("id=add")
        for u in split(row["enrol_users"]):
            self.verify_present("xpath=//select[@id='removeselect']//option[contains(.,'%s@example.com')]" % u,
                                "%s enrolled" % u)
        m.open("/user/index.php?id=%d" % cid)
        self.verify_text("css=[data-region='participant-count']", row["expected_participants"], "participant count")


if __name__ == "__main__":
    unittest.main()
