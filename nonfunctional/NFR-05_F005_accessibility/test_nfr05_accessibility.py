"""NFR-05 Accessibility of "Auto-create groups" (member: Duong Cong Chi Dung).

Requirement: the Auto-create groups pages conform to WCAG 2.1 level A and AA, i.e.
  (a) an automated audit finds no violation of impact "critical" or "serious", and
  (b) a keyboard-only user can fill the form, preview the groups and reach the validation messages
      (WCAG 2.1.1 Keyboard, 3.3.1 Error identification, 4.1.2 Name/Role/Value).
Type: non-functional - accessibility testing.  Tool: axe-core 4.10 (Deque, vendor/axe.min.js) injected
into the page with Selenium WebDriver; keyboard checks driven with Selenium key events.
Data: data/axe_pages.csv (page states, WCAG rule tags, blocking impacts), data/keyboard.csv.
Every axe violation (also the non-blocking ones) is written to results/NFR-05_axe_<tc>.json.
"""
import json
import os
import unittest

from selenium.webdriver.common.keys import Keys

from common import config
from common.base import MoodleTestCase
from common.data import expand, split
from common.ddt import data_driven

HERE = os.path.dirname(os.path.abspath(__file__))
AXE = os.path.join(HERE, "..", "vendor", "axe.min.js")


@data_driven("data/axe_pages.csv", runner="axe_case")
@data_driven("data/keyboard.csv", runner="keyboard_case")
class NFR05Accessibility(MoodleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cid = cls.m.course_id(config.COURSE_SHORTNAME)
        with open(AXE, encoding="utf-8") as f:
            cls.axe_js = f.read()

    def open_form(self):
        self.m.open("/group/autogroup.php?courseid=%d" % self.cid)

    # ------------------------------------------------------------------ (a) automated WCAG audit
    def axe_case(self, row):
        m = self.m
        if row["state"] == "groups":
            m.open("/group/index.php?id=%d" % self.cid)
        else:
            self.open_form()
            if row["namingscheme"]:
                m.type("id=id_namingscheme", expand(row["namingscheme"]))
            if row["number"]:
                m.type("id=id_number", expand(row["number"]))
            if row["action"] == "preview":
                m.submit("id=id_preview")
        m.d.execute_script(self.axe_js)
        result = m.d.execute_async_script(
            "var done=arguments[arguments.length-1];"
            "axe.run(document,{runOnly:{type:'tag',values:arguments[0]}})"
            ".then(r=>done({violations:r.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,"
            "helpUrl:v.helpUrl,tags:v.tags,nodes:v.nodes.map(n=>n.target.join(' '))})),passes:r.passes.length}))"
            ".catch(e=>done({error:String(e)}));", split(row["wcag_tags"]))
        self.assertNotIn("error", result, result.get("error"))
        os.makedirs(config.RESULTS_DIR, exist_ok=True)
        with open(os.path.join(config.RESULTS_DIR, "NFR-05_axe_%s.json" % row["tc_id"]), "w") as f:
            json.dump(dict(result, page=m.d.current_url, tc_id=row["tc_id"]), f, indent=1)
        print("\n  %s: %d rules passed, violations: %s" % (row["tc_id"], result["passes"],
              ", ".join("%s(%s, %d nodes)" % (v["id"], v["impact"], len(v["nodes"])) for v in result["violations"]) or "none"))
        blocking = [v for v in result["violations"] if v["impact"] in split(row["blocking_impacts"])]
        self.verify_equal(0, len(blocking), "%s - found: %s" % (row["expected_result"], "; ".join(
            "%s [%s] %s on %s" % (v["id"], v["impact"], v["help"], v["nodes"][:3]) for v in blocking)))

    # ------------------------------------------------------------------ (b) keyboard-only use
    def tab_to(self, element_id, max_tabs):
        body = self.m.d.switch_to.active_element
        for _ in range(max_tabs):
            if self.m.d.execute_script("return document.activeElement && document.activeElement.id") == element_id:
                return True
            body.send_keys(Keys.TAB)
            body = self.m.d.switch_to.active_element
        return False

    def keyboard_case(self, row):
        m, max_tabs = self.m, int(row["max_tabs"])
        self.open_form()
        m.d.execute_script("document.activeElement && document.activeElement.blur(); window.scrollTo(0,0);")
        for field in ("namingscheme", "number"):
            if not self.verify(self.tab_to("id_" + field, max_tabs), "id_%s reachable with Tab" % field):
                return
            active = m.d.switch_to.active_element
            active.send_keys(Keys.CONTROL, "a")
            active.send_keys(Keys.DELETE)
            value = expand(row[field])
            if value:
                active.send_keys(value)
        if not self.verify(self.tab_to(row["submit_with"], max_tabs), "%s reachable with Tab" % row["submit_with"]):
            return
        m.d.switch_to.active_element.send_keys(Keys.ENTER)
        m.pause(500)
        m.wait_ready()
        if row["expected_result"].startswith("Groups"):
            self.verify_text("xpath=//table[contains(@class,'generaltable')]/thead/tr/th[1]",
                             row["expected_result"], "preview opened from the keyboard")
        else:
            self.verify_field_error("number", row["expected_result"])
            num = m.find("id=id_number")
            described = (num.get_attribute("aria-describedby") or "") + " " + (num.get_attribute("aria-invalid") or "")
            self.verify("id_error_number" in described or "true" in described,
                        "error is exposed to assistive technology (aria-describedby/aria-invalid): %r" % described)


if __name__ == "__main__":
    unittest.main()
