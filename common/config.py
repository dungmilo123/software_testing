"""Run-time settings shared by every script (Level 1, Level 2, non-functional).

All values can be overridden with environment variables so the same code runs against any copy of the
Moodle demo without editing a file:

    MOODLE_BASE_URL   site under test              (default http://127.0.0.1:9501)
    MOODLE_ADMIN_USER / MOODLE_ADMIN_PASS          (default admin / admin)
    BROWSER           chrome | firefox             (default chrome)
    CHROME_BINARY     path of another Chromium browser to drive with chromedriver, e.g. /usr/bin/brave
    HEADLESS          1 = no browser window, 0 = visible browser (default 1)
    RESULTS_DIR       where run logs and failure screenshots go (default ./results)
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = os.environ.get("MOODLE_BASE_URL", "http://127.0.0.1:9501").rstrip("/")
ADMIN_USER = os.environ.get("MOODLE_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("MOODLE_ADMIN_PASS", "admin")
BROWSER = os.environ.get("BROWSER", "chrome").lower()
CHROME_BINARY = os.environ.get("CHROME_BINARY", "")
HEADLESS = os.environ.get("HEADLESS", "1") != "0"
RESULTS_DIR = os.environ.get("RESULTS_DIR", os.path.join(ROOT, "results"))

# Shared fixture created by setup/test_00_setup.py (same data as the Project #2 suites)
COURSE_SHORTNAME = "KTC01"
COURSE_FULLNAME = "KT Test Course"

# Explicit-wait timeout (seconds) used by every helper
WAIT = float(os.environ.get("WAIT", "15"))
