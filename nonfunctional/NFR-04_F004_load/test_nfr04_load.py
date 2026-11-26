"""NFR-04 Load / Concurrency for F004 "Create course" (member: Luong Tan Tai).

Non-functional requirement
    The "Add a new course" form and the Course management page must remain responsive
    under concurrent load:
      - 1 and 5 concurrent users:  average page-load time < 2 s
      - 10 concurrent users:       average page-load time < 3 s

Type:   Non-functional – load / concurrency testing
Tool:   Python standard library (threading + urllib.request) with Selenium login to
        obtain a valid session cookie, then concurrent HTTP GET requests measured with
        time.perf_counter().  No external load-testing tool required.
Approach:
    1. The test class logs in once with Selenium to get the Moodle session cookie.
    2. For each scenario row, N threads fire simultaneously, each fetching the target URL
       with the shared session cookie via urllib.request (no browser overhead).
    3. Per-thread response times are recorded; average and 95th-percentile are computed.
    4. The test fails if the threshold (avg_lt_2s or avg_lt_3s) is exceeded.
Data:   data/load_scenarios.csv – one row per scenario.

Result columns written to results/NFR04_F004.json:
    concurrent_users, avg_s, p95_s, threshold, status
"""
import statistics
import threading
import time
import unittest
import urllib.request

from common import config
from common.base import MoodleTestCase
from common.ddt import data_driven

THRESHOLDS = {
    "avg_lt_2s": 2.0,
    "avg_lt_3s": 3.0,
}


# Browsers identify themselves; Moodle may reject plain urllib requests without User-Agent.
_HEADERS = {
    "Cookie": "",           # filled per-call
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/158.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Generous per-request timeout: we want to *measure* slowness, not mask it.
_REQUEST_TIMEOUT = 120   # seconds


def _fetch_time(url: str, cookie: str, results: list, idx: int) -> None:
    """Fetch *url* with the given session *cookie* and store elapsed seconds."""
    headers = dict(_HEADERS)
    headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    t0 = time.perf_counter()
    try:
        # Follow redirects (default) so a login-redirect loop is counted as one
        # slow response rather than a connection error.
        opener = urllib.request.build_opener(
            urllib.request.HTTPRedirectHandler()
        )
        with opener.open(req, timeout=_REQUEST_TIMEOUT) as resp:
            resp.read()          # consume body so the connection is properly closed
    except Exception as exc:
        results[idx] = exc      # propagate the error so the caller can inspect it
        return
    results[idx] = time.perf_counter() - t0


@data_driven("data/load_scenarios.csv")
class NFR04Load(MoodleTestCase):
    """Load / concurrency tests for the Create-course feature (F004)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Extract the Moodle session cookie from the already-logged-in browser.
        cls.session_cookie = "; ".join(
            "%s=%s" % (c["name"], c["value"])
            for c in cls.driver.get_cookies()
        )

    def run_case(self, row: dict) -> None:
        n_users = int(row["concurrent_users"])
        url = config.BASE_URL + row["url_path"]
        threshold_key = row["expected_result"]
        limit = THRESHOLDS[threshold_key]

        # --- run N threads simultaneously ---
        times: list = [None] * n_users
        threads = [
            threading.Thread(target=_fetch_time, args=(url, self.session_cookie, times, i))
            for i in range(n_users)
        ]
        barrier = threading.Barrier(n_users)   # synchronise start

        def _run(t, results, idx):
            barrier.wait()
            _fetch_time(url, self.session_cookie, results, idx)

        threads = [
            threading.Thread(target=_run, args=(None, times, i))
            for i in range(n_users)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)

        # --- evaluate ---
        errors = [t for t in times if isinstance(t, Exception)]
        ok_times = [t for t in times if isinstance(t, float)]

        self.assertEqual(
            0, len(errors),
            "HTTP errors during load: %s" % "; ".join(str(e) for e in errors)
        )
        self.assertGreater(len(ok_times), 0, "No successful responses recorded")

        avg = statistics.mean(ok_times)
        p95 = sorted(ok_times)[int(len(ok_times) * 0.95) - 1] if len(ok_times) >= 2 else ok_times[-1]

        print("\n  %s [%d users] avg=%.3fs  p95=%.3fs  limit=%.1fs"
              % (row["tc_id"], n_users, avg, p95, limit))

        self.assertLessEqual(
            avg, limit,
            "%s: average response time %.3f s exceeds limit %.1f s "
            "(url=%s, users=%d)" % (row["tc_id"], avg, limit, row["url_path"], n_users)
        )


if __name__ == "__main__":
    unittest.main()
