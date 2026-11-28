"""NFR-03 Access control of the gradebook (F003 Add/edit grade item).

Requirement: only users allowed to manage grades (teacher, manager, administrator) can see or change grade
items. Every gradebook URL of the feature must refuse
  (a) a visitor who is not logged in  -> redirected to the login page, nothing of the gradebook shown;
  (b) a logged-in student of the course -> Moodle's "Sorry, but you do not currently have permissions to do
      that (...)" error, no form, no grade item data;
and a refused request must not change anything: after a delete / hide link or a forged POST of the Edit
form (sent with the student's own valid sesskey, so only the capability check can stop it) the grade item
is still there with its name, maximum and visibility unchanged.
Two control cases (student's own User report, administrator's Gradebook setup) show that the checks can
tell "allowed" from "refused".

Type: non-functional - security testing (authentication and authorization / access control).
Approach: data-driven negative testing of direct URL access with three browser sessions (guest, student,
admin); forged POST requests are sent with fetch() from inside the browser session of the role.
Tool: Selenium WebDriver + unittest (same framework as Level 1).
Data: data/access.csv (one row per URL and role), data/fixture.csv (grade item and student account).
For each case the final URL, the message and the item state are written to results/NFR-03_access_<tc>.json.
"""
import json
import os
import re
import unittest

from common import config
from common.base import MoodleTestCase
from common.data import read_rows
from common.ddt import data_driven
from common.driver import make_driver
from common.moodle import Moodle

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = {r["key"]: r["value"] for r in read_rows(os.path.join(HERE, "data", "fixture.csv"))}
ERROR = "xpath=//p[contains(@class,'errormessage')]"
ROW = "xpath=//tr[@data-itemid][.//span[contains(@class,'gradeitemheader') and normalize-space(.)='%s']]"
MODAL = "css=.modal.show"


@data_driven("data/access.csv", runner="access_case")
class NFR03AccessControl(MoodleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()  # admin session
        cls.cid = cls.m.course_id(config.COURSE_SHORTNAME)
        cls.item = FIXTURE["item_name"]
        cls.itemid = cls.create_item()
        cls.sessions = {"admin": cls.m}

    @classmethod
    def tearDownClass(cls):
        try:
            for role, m in cls.sessions.items():
                if role != "admin":
                    m.d.quit()
            cls.delete_item()
        finally:
            super().tearDownClass()

    # ------------------------------------------------------------------ fixture (as admin, through the UI)
    @classmethod
    def open_setup(cls):
        cls.m.open("/grade/edit/tree/index.php?id=%d" % cls.cid)
        cls.m.dismiss_tour()
        cls.m.pause(1000)

    @classmethod
    def create_item(cls):
        m = cls.m
        cls.open_setup()
        if not m.exists(ROW % cls.item):
            m.click("xpath=//a[@role='button' and @aria-label='Add']")
            m.click("xpath=//a[@role='menuitem' and normalize-space(.)='Add grade item']")
            m.wait(MODAL + " form", visible=True)
            m.pause(500)
            m.type(MODAL + " input[name='itemname']", cls.item)
            m.type(MODAL + " input[name='grademax']", FIXTURE["item_max"])
            m.click(MODAL + " [data-action='save']")
            m.wait_gone(MODAL)
            cls.open_setup()
        return m.attribute(ROW % cls.item, "data-itemid")

    @classmethod
    def delete_item(cls):
        m = cls.m
        cls.open_setup()
        while m.exists(ROW % cls.item):
            m.click(ROW % cls.item + "//button[contains(@class,'cellmenubtn')]")
            m.click(ROW % cls.item + "//a[@aria-label='Delete']")
            m.submit("xpath=//div[contains(@class,'modal') and contains(@class,'show')]//button[normalize-space(.)='Delete']")
            cls.open_setup()

    def item_state(self):
        """What the administrator sees of the fixture item: name, maximum, hidden flag."""
        m = self.m
        self.open_setup()
        rows = m.d.find_elements("xpath", "//tr[@data-itemid='%s']" % self.itemid)
        if not rows:
            return {"exists": False}
        return {"exists": True, "name": m.text("xpath=//tr[@data-itemid='%s']//span[contains(@class,'gradeitemheader')]" % self.itemid),
                "max": m.text("xpath=//tr[@data-itemid='%s']/td[contains(@class,'column-range')]" % self.itemid),
                "hidden": rows[0].get_attribute("data-hidden")}

    # ------------------------------------------------------------------ sessions
    def session(self, role):
        if role not in self.sessions:
            m = Moodle(make_driver())
            if role == "student":
                m.login(FIXTURE["student_user"], FIXTURE["student_password"])
            elif role != "guest":
                raise ValueError("unknown role %r" % role)
            self.sessions[role] = m
        return self.sessions[role]

    def fill(self, text, m):
        sesskey = m.d.execute_script("return window.M && M.cfg ? M.cfg.sesskey : 'x'") if text and "{sesskey}" in text else ""
        return (text or "").format(cid=self.cid, itemid=self.itemid, item=self.item, sesskey=sesskey)

    # ------------------------------------------------------------------ one case
    def access_case(self, row):
        role, expected = row["role"], row["expected"]
        m = self.session(role)
        before = self.item_state() if row["check_item"] else None
        if role != "admin" and m.d.current_url.startswith("data:"):
            m.open("/")  # a page of the site is needed to read the sesskey / send fetch() from

        path = self.fill(row["path"], m)
        if row["method"] == "post":
            m.open("/my/" if role != "guest" else "/")
            resp = m.d.execute_async_script(
                "var done=arguments[arguments.length-1];"
                "fetch(arguments[0],{method:'POST',credentials:'same-origin',"
                "headers:{'Content-Type':'application/x-www-form-urlencoded'},body:arguments[1]})"
                ".then(r=>r.text().then(t=>done({url:r.url,status:r.status,text:t})))"
                ".catch(e=>done({url:'',status:0,text:String(e)}));",
                m.url(path), self.fill(row["post_data"], m))
            final_url = resp["url"]
            doc = resp["text"]
            message = _error_from_html(doc)
            page = doc
        else:
            m.open(path)
            final_url = m.d.current_url
            message = m.text(ERROR) if m.exists(ERROR) else ""
            page = m.page_text()

        exp = self.fill(row["expected_result"], m)
        if expected == "login":
            self.verify(exp in final_url, "%s: expected a redirect to %s, ended on %s" % (role, exp, final_url))
        elif expected == "denied":
            self.verify(exp in message, "%s: expected refusal %r, got %r (url %s)" % (role, exp, message, final_url))
            self.verify(not m.exists("id=id_itemname") or row["method"] == "post", "the grade item form must not be shown")
        elif expected == "allowed":
            self.verify(message == "" and "/login/index.php" not in final_url,
                        "%s: access should be allowed, got %r at %s" % (role, message, final_url))
            self.verify(exp in page, "%s: page should show %r" % (role, exp))
        else:
            raise ValueError("unknown expected %r" % expected)

        hidden_text = self.fill(row["must_not_show"], m)
        if hidden_text:
            self.verify(hidden_text not in (page if row["method"] == "post" else m.page_text()),
                        "%s: page must not reveal %r" % (role, hidden_text))

        after = None
        if row["check_item"] == "unchanged":
            after = self.item_state()
            self.verify_equal(before, after, "grade item after the refused request")

        os.makedirs(config.RESULTS_DIR, exist_ok=True)
        with open(os.path.join(config.RESULTS_DIR, "NFR-03_access_%s.json" % row["tc_id"]), "w", encoding="utf-8") as f:
            json.dump({"tc_id": row["tc_id"], "role": role, "method": row["method"], "request": path,
                       "final_url": final_url, "message": message, "expected": expected,
                       "expected_result": exp, "item_before": before, "item_after": after}, f, indent=1)


def _error_from_html(html):
    """Text of Moodle's <p class="errormessage"> in a fetched page ('' when there is none)."""
    mo = re.search(r'<p[^>]*class="[^"]*errormessage[^"]*"[^>]*>(.*?)</p>', html or "", re.S)
    if not mo:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", mo.group(1))).strip()


if __name__ == "__main__":
    unittest.main()
