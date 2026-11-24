"""Remove the shared fixture (Python port of the Project #2 suite 99-cleanup), data-driven by data/cleanup.csv.

    python run_tests.py setup/test_99_cleanup.py
"""
import unittest

from common.base import MoodleTestCase
from common.ddt import data_driven

FILTERED = "xpath=//select[@id='id_ausers']/option[starts-with(normalize-space(.),'All filtered (')]"


@data_driven("data/cleanup.csv")
class Cleanup99(MoodleTestCase):

    def run_case(self, row):
        if row["object"] == "course":
            self.m.delete_courses(row["name"], keep=())
            self.m.open("/course/management.php?search=" + row["name"])
            self.verify_contains("id=region-main", row["expected_result"], "course search")
        else:
            self.delete_users(row["name"])
            self.verify_equal(0, self.count_users(row["name"]), row["expected_result"])

    def filter_users(self, prefix):
        m = self.m
        m.open("/admin/user/user_bulk.php")
        if m.exists("xpath=//input[@name='removeall' and @value='Remove all filters']"):
            m.submit("xpath=//input[@name='removeall' and @value='Remove all filters']")
        m.submit("xpath=//input[@name='removeall' and @value='Remove all']")
        m.click("xpath=//fieldset[@id='id_newfilter']//a[normalize-space(.)='Show more...']")
        m.wait("css=#id_newfilter a.moreless-toggler[aria-expanded='true']")
        m.pause(500)
        m.select("id=id_username_op", "starts with")
        m.type("id=id_username", prefix)
        m.submit("id=id_addfilter")

    def count_users(self, prefix):
        self.filter_users(prefix)
        text = self.m.text(FILTERED)  # "All filtered (10/160)"
        return int(text.split("(")[1].split("/")[0])

    def delete_users(self, prefix):
        m = self.m
        if self.count_users(prefix) == 0:
            return
        m.submit("xpath=//input[@name='addall']")
        m.select("id=id_action", "Delete")
        m.submit("id=id_doaction")
        m.submit("xpath=//form[contains(@action,'user_bulk_delete.php')]//button[@type='submit']")
        m.open("/admin/user/user_bulk.php")
        if m.exists("xpath=//input[@name='removeall' and @value='Remove all filters']"):
            m.submit("xpath=//input[@name='removeall' and @value='Remove all filters']")


if __name__ == "__main__":
    unittest.main()
