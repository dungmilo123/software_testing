"""NFR-02 Security: stored XSS / HTML injection in Assignment name and description (Naman Chahar, 2560173).

Requirement
  User-supplied HTML in the Assignment name, Description and Activity instructions must be sanitised:
  script elements and event-handler attributes must never execute on the Assignment view or settings
  pages, and no raw <script> tag or onerror handler containing the test payload may be rendered.

Type: non-functional - security testing (stored cross-site scripting / HTML injection).
Approach: data-driven Selenium suite that saves one payload per case in the Assignment settings form,
  watches for a JavaScript dialog, then inspects the rendered view and edit pages for executable
  script/event-handler markup.
Tool: Python 3 + Selenium 4 + unittest (headless Chromium).
Data: data/xss_cases.csv.
Per-case evidence is written to results/NFR-02_xss_<tc_id>.json.
"""
import json
import os
import re

from selenium.common.exceptions import NoAlertPresentException, TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common import config
from common.base import MoodleTestCase
from common.data import expand
from common.ddt import data_driven

HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = re.compile(r"<script[^>]*>[^<]*XSSNFR02", re.I)
HANDLER = re.compile(r"<[^>]*\bonerror\s*=\s*[\"']?[^>]*XSSNFR02", re.I)


@data_driven("data/xss_cases.csv")
class NFR02AssignmentXSS(MoodleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cid = cls.m.course_id(config.COURSE_SHORTNAME)
        cls.m.delete_activities("assign")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.m.delete_activities("assign")
        finally:
            super().tearDownClass()

    def run_case(self, row):
        m = self.m
        self.addCleanup(m.delete_activities, "assign")
        tc = row["tc_id"]
        field = row["field"]
        payload = expand(row["payload"])
        name = "XSS %s" % tc

        m.open("/course/modedit.php?add=assign&type=&course=%d&section=0&return=0" % self.cid)
        m.expand_all()
        m.type("id=id_name", name)
        for prefix in ("id_allowsubmissionsfromdate", "id_duedate", "id_cutoffdate", "id_gradingduedate"):
            cb = "id=%s_enabled" % prefix
            if m.exists(cb) and m.find(cb).is_selected():
                m.set_checkbox(cb, False)
        if field == "name":
            m.type("id=id_name", payload)
        elif field == "description":
            m.set_editor("id_introeditor", payload)
        elif field == "activity":
            m.set_editor("id_activityeditor", payload)
        else:
            raise ValueError("unknown field %r" % field)

        try:
            m.submit("id=id_submitbutton")
        except UnexpectedAlertPresentException:
            a = m.d.switch_to.alert
            pre_alert = a.text
            a.accept()
        else:
            pre_alert = None
        alert = self._alert_text() or pre_alert
        try:
            executed = m.d.execute_script("return window.__xss || null")
        except UnexpectedAlertPresentException:
            a = m.d.switch_to.alert
            alert = alert or a.text
            a.accept()
            executed = m.d.execute_script("return window.__xss || null")
        self.verify(alert is None, "%s: JavaScript alert executed: %r" % (tc, alert))
        self.verify(executed is None, "%s: JavaScript payload executed (window.__xss=%r)" % (tc, executed))

        view_html = self._region_html()
        self._verify_source(tc, "view", view_html, payload)

        # The settings form re-renders the stored value; check the form region too (textarea values are escaped).
        link = "xpath=//a[contains(@href,'modedit.php?update=')]"
        if m.exists(link):
            m.open(m.attribute(link, "href"))
            m.expand_all()
            self._verify_source(tc, "settings", self._region_html(), payload)

        self._write_evidence(tc, row, alert, executed, view_html, m.d.current_url)

    def _region_html(self):
        return self.m.d.execute_script(
            "var e=document.getElementById('region-main'); return e ? e.innerHTML : document.body.innerHTML;")

    def _alert_text(self):
        """Return the text of a JavaScript dialog if one appears within 1.5 s, otherwise None."""
        try:
            WebDriverWait(self.m.d, 1.5).until(EC.alert_is_present())
            alert = self.m.d.switch_to.alert
            text = alert.text
            alert.accept()
            return text
        except (TimeoutException, NoAlertPresentException):
            return None

    def _verify_source(self, tc, page, source, payload):
        script_hit = MARKER.search(source)
        handler_hit = HANDLER.search(source)
        self.verify(script_hit is None, "%s/%s: raw executable <script> payload found: %r"
                    % (tc, page, script_hit.group(0)[:120] if script_hit else ""))
        self.verify(handler_hit is None, "%s/%s: raw onerror handler found: %r"
                    % (tc, page, handler_hit.group(0)[:120] if handler_hit else ""))

    def _write_evidence(self, tc, row, alert, executed, region_html, url):
        os.makedirs(config.RESULTS_DIR, exist_ok=True)
        evidence = {
            "tc_id": tc,
            "title": row["title"],
            "field": row["field"],
            "payload": row["payload"],
            "alert_fired": alert,
            "executed_marker": executed,
            "raw_script_found": bool(MARKER.search(region_html)),
            "raw_onerror_found": bool(HANDLER.search(region_html)),
            "url": url,
            "heading": self.m.text("css=h1") if self.m.exists("css=h1") else "",
            "region_excerpt": region_html[region_html.find("XSSNFR02") - 120:region_html.find("XSSNFR02") + 200]
            if "XSSNFR02" in region_html else "",
        }
        with open(os.path.join(config.RESULTS_DIR, "NFR-02_xss_%s.json" % tc), "w", encoding="utf-8") as f:
            json.dump(evidence, f, indent=2, ensure_ascii=False)
        print("\n  %s (%s): alert=%r script=%s onerror=%s"
              % (tc, row["field"], alert, evidence["raw_script_found"], evidence["raw_onerror_found"]))
