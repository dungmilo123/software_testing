"""NFR-01b Usability & Responsive Layout of Quiz Settings (member: Tran Ngoc Thoai, 2353147).

Requirement:
  The "New Quiz" settings form and the saved Quiz view page must remain usable across Desktop
  (1366x900), Tablet (768x1024), and Mobile (375x812) viewports:
  (a) zero horizontal page overflow (documentElement.scrollWidth <= clientWidth),
  (b) essential controls (Name field, Save and display, Save and return, Cancel) are rendered
      within non-zero bounds and interactive,
  (c) client/form validation feedback is visible when submitting empty Name, and
  (d) submitting a valid Quiz succeeds and renders cleanly without horizontal overflow.

Type: non-functional - usability / responsive layout testing.
Approach: Data-driven multi-viewport browser geometry & interaction verification.
Tool: Python 3.11 + Selenium 4 WebDriver + unittest (headless Chrome).
Data: data/responsive.csv.
Detailed viewport metrics are written to results/NFR-01b_usability_<tc_id>.json.
"""
import json
import os
import unittest

from common import config
from common.base import MoodleTestCase
from common.ddt import data_driven


@data_driven("data/responsive.csv")
class NFR01bQuizUsability(MoodleTestCase):

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

    def _layout_metrics(self):
        return self.m.d.execute_script(
            "var de = document.documentElement;"
            "return {scrollWidth: de.scrollWidth, clientWidth: de.clientWidth,"
            " overflowPx: Math.max(0, de.scrollWidth - de.clientWidth)};"
        )

    def _control_rect(self, element_id):
        return self.m.d.execute_script(
            "var el = document.getElementById(arguments[0]);"
            "if (!el) return null;"
            "var r = el.getBoundingClientRect();"
            "return {width: Math.round(r.width), height: Math.round(r.height),"
            " left: Math.round(r.left), right: Math.round(r.right)};",
            element_id,
        )

    def _set_viewport(self, width, height, mobile):
        if config.BROWSER != "firefox":
            self.m.d.execute_cdp_cmd(
                "Emulation.setDeviceMetricsOverride",
                {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": mobile},
            )
        else:
            self.m.d.set_window_size(width, height)

    def _clear_viewport(self):
        if config.BROWSER != "firefox":
            self.m.d.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
        self.m.d.set_window_size(1400, 1000)

    def run_case(self, row):
        m = self.m
        width, height = int(row["width"]), int(row["height"])
        self.addCleanup(m.delete_activities, "quiz")
        self.addCleanup(self._clear_viewport)

        self._set_viewport(width, height, row["viewport_name"] == "mobile")
        m.open("/course/modedit.php?add=quiz&type=&course=%d&section=0&return=0" % self.cid)
        m.wait("id=id_name", visible=True)

        form_metrics = self._layout_metrics()
        controls = {
            cid: self._control_rect(cid)
            for cid in ("id_name", "id_submitbutton", "id_submitbutton2", "id_cancel")
        }

        # 1. No horizontal overflow on New Quiz form
        self.verify(
            form_metrics["overflowPx"] <= 0,
            "%s form horizontal overflow: scrollWidth=%d > clientWidth=%d"
            % (row["viewport_name"], form_metrics["scrollWidth"], form_metrics["clientWidth"]),
        )

        # 2. Essential controls rendered cleanly within viewport width
        for cid, rect in controls.items():
            if self.verify(rect is not None and rect["width"] > 0 and rect["height"] > 0, "%s visible (%s)" % (cid, rect)):
                self.verify(
                    rect["right"] <= form_metrics["clientWidth"] + 2,
                    "%s extends past viewport right edge (%d > %d)" % (cid, rect["right"], form_metrics["clientWidth"]),
                )

        # 3. Validation error visible on empty submit
        m.type("id=id_name", "")
        m.submit("id=id_submitbutton")
        self.verify_field_error("name", "You must supply a value here.")

        # 4. Valid save & display works and saved quiz view has no horizontal overflow
        m.type("id=id_name", row["quiz_name"])
        m.submit("id=id_submitbutton")
        self.verify_text("css=h1", row["quiz_name"], "saved quiz heading")
        view_metrics = self._layout_metrics()
        self.verify(
            view_metrics["overflowPx"] <= 0,
            "%s quiz view horizontal overflow: scrollWidth=%d > clientWidth=%d"
            % (row["viewport_name"], view_metrics["scrollWidth"], view_metrics["clientWidth"]),
        )

        os.makedirs(config.RESULTS_DIR, exist_ok=True)
        out_path = os.path.join(config.RESULTS_DIR, "NFR-01b_usability_%s.json" % row["tc_id"])
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "tc_id": row["tc_id"],
                    "viewport": {"name": row["viewport_name"], "width": width, "height": height},
                    "form_layout": form_metrics,
                    "controls": controls,
                    "view_layout": view_metrics,
                },
                f,
                indent=2,
            )


if __name__ == "__main__":
    unittest.main()
