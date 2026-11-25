"""NFR-01 Performance of "New Quiz" and "Save and display" (member: Tran Ngoc Thoai, 2353147).

Requirement:
  Response time of opening the "New Quiz" settings form and submitting "Save and display"
  must achieve average < 2.0 s and 95th percentile < 3.0 s across 10 measured iterations
  (after 1 warm-up iteration).

Type: non-functional - response-time performance testing.
Approach: Data-driven Selenium timing harness using Python time.perf_counter() for end-to-end
  page transition latency alongside browser Navigation Timing API telemetry.
Tool: Python 3.11 + Selenium 4 WebDriver + unittest (headless Chrome).
Data: data/performance.csv.
Detailed per-iteration telemetry is written to results/NFR-01_perf_<tc_id>.json.
"""
import json
import math
import os
import statistics
import time
import unittest

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common import config
from common.base import MoodleTestCase
from common.ddt import data_driven


def percentile_nearest_rank(values, pct):
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return ordered[idx]


@data_driven("data/performance.csv")
class NFR01QuizPerformance(MoodleTestCase):

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

    def run_case(self, row):
        m = self.m
        self.addCleanup(m.delete_activities, "quiz")

        warmup = int(row["warmup"])
        iterations = int(row["iterations"])
        max_avg_s = float(row["max_avg_s"])
        max_p95_s = float(row["max_p95_s"])
        op = row["operation"]
        cfg = row["quiz_config"]

        samples = []
        nav_timings = []

        for idx in range(-warmup, iterations):
            is_warmup = idx < 0
            if op == "open_new_quiz":
                elapsed, nav = self._measure_open_new_quiz()
            elif op == "save_and_display":
                label = "%s_%d" % (row["tc_id"], idx)
                elapsed, nav = self._measure_save_and_display(cfg, label)
            else:
                raise ValueError("unknown operation %r" % op)

            if not is_warmup:
                samples.append(round(elapsed, 4))
                nav_timings.append(nav)

        avg_s = round(statistics.mean(samples), 4)
        min_s = round(min(samples), 4)
        max_s = round(max(samples), 4)
        p95_s = round(percentile_nearest_rank(samples, 95), 4)

        os.makedirs(config.RESULTS_DIR, exist_ok=True)
        out_path = os.path.join(config.RESULTS_DIR, "NFR-01_perf_%s.json" % row["tc_id"])
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "tc_id": row["tc_id"],
                    "title": row["title"],
                    "operation": op,
                    "quiz_config": cfg,
                    "warmup": warmup,
                    "iterations": iterations,
                    "thresholds_s": {"avg": max_avg_s, "p95": max_p95_s},
                    "summary_s": {"min": min_s, "avg": avg_s, "p95": p95_s, "max": max_s},
                    "samples_s": samples,
                    "navigation_timing_ms": nav_timings,
                },
                f,
                indent=2,
            )

        print(
            "\n  %s (%s/%s): min=%.3fs avg=%.3fs p95=%.3fs max=%.3fs"
            % (row["tc_id"], op, cfg, min_s, avg_s, p95_s, max_s)
        )
        self.verify(avg_s < max_avg_s, "average response time %.3fs >= %.3fs" % (avg_s, max_avg_s))
        self.verify(p95_s < max_p95_s, "95th percentile %.3fs >= %.3fs" % (p95_s, max_p95_s))

    def _nav_entry(self):
        return self.m.d.execute_script(
            "var e = performance.getEntriesByType('navigation')[0];"
            "return e ? {redirectCount: e.redirectCount,"
            " redirectEnd: Math.round(e.redirectEnd),"
            " responseEnd: Math.round(e.responseEnd),"
            " domContentLoaded: Math.round(e.domContentLoadedEventEnd),"
            " loadEventEnd: Math.round(e.loadEventEnd)} : {};"
        )

    def _measure_open_new_quiz(self):
        m = self.m
        m.open("/course/view.php?name=" + config.COURSE_SHORTNAME)
        url = "/course/modedit.php?add=quiz&type=&course=%d&section=0&return=0" % self.cid
        t0 = time.perf_counter()
        m.open(url)
        WebDriverWait(m.d, config.WAIT, poll_frequency=0.05).until(
            EC.visibility_of_element_located((By.ID, "id_name"))
        )
        elapsed = time.perf_counter() - t0
        return elapsed, self._nav_entry()

    def _measure_save_and_display(self, cfg, quiz_name):
        m = self.m
        m.open("/course/modedit.php?add=quiz&type=&course=%d&section=0&return=0" % self.cid)
        m.wait("id=id_name", visible=True)
        m.type("id=id_name", quiz_name)

        if cfg == "full":
            m.expand_all()
            m.set_editor("id_introeditor", "<p>Performance test description</p>")
            m.set_date("id_timeopen", "2027-11-10 09:00")
            m.set_date("id_timeclose", "2027-11-20 17:00")
            m.set_checkbox("id=id_timelimit_enabled", True)
            m.type("id=id_timelimit_number", "30")
            m.select("id=id_timelimit_timeunit", "minutes")
            m.type("id=id_gradepass", "5.5")
            m.select("id=id_attempts", "3")
            m.select("id=id_grademethod", "Average grade")
            m.select("id=id_questionsperpage", "Every 2 questions")
            m.select("id=id_preferredbehaviour", "Immediate feedback")
            m.select("id=id_seb_requiresafeexambrowser", "Yes – Use SEB client config")
            m.type("id=id_seb_allowedbrowserexamkeys", "a" * 64)
            m.set_editor("id_feedbacktext_0", "<p>Well done</p>")
            m.type("id=id_feedbackboundaries_0", "50%")
            m.set_editor("id_feedbacktext_1", "<p>Keep studying</p>")

        btn = m.find("id=id_submitbutton")
        old_html = m.d.find_element(By.TAG_NAME, "html")

        def _navigated(_):
            try:
                old_html.is_enabled()
                return False
            except WebDriverException:
                return True

        # Use direct JS click + 50 ms polling to measure Moodle's real POST-redirect-GET latency
        # without Selenium's ~1.15 s ElementClickInterceptedException retry overhead.
        t0 = time.perf_counter()
        m.d.execute_script("arguments[0].click();", btn)
        WebDriverWait(m.d, config.WAIT * 2, poll_frequency=0.05).until(_navigated)
        m.wait_ready()
        WebDriverWait(m.d, config.WAIT, poll_frequency=0.05).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "a[href*='modedit.php?update=']"))
        )
        elapsed = time.perf_counter() - t0
        return elapsed, self._nav_entry()


if __name__ == "__main__":
    unittest.main()
