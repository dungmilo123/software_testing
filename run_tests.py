#!/usr/bin/env python3
"""Run test scripts and write a result log (one line per test case ID).

    python run_tests.py level1/F004_create_course                 # one feature folder
    python run_tests.py setup/test_00_setup.py level1/F005_auto_create_groups -k TC_005_03
    python run_tests.py level2 --tag level2-all

Writes results/<tag>.csv and results/<tag>.json (tag = --tag or the folder names) and a PNG screenshot
of the browser for every failing case. Exit code 0 only when every case passed.
"""
import argparse
import csv
import json
import os
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from common import config  # noqa: E402


class LoggingResult(unittest.TextTestResult):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.records = []
        self._t0 = {}

    def startTest(self, test):
        self._t0[test.id()] = time.time()
        super().startTest(test)

    def _record(self, test, status, err=None):
        method = getattr(test, getattr(test, "_testMethodName", ""), None)
        case = getattr(method, "__case__", {}) or {}
        msg = ""
        if err is not None:
            msg = str(err[1]).strip()
            if status == "ERROR":
                msg = "%s: %s" % (err[0].__name__, msg)
        shot = ""
        if status in ("FAIL", "ERROR") and getattr(test, "driver", None) is not None:
            shot_dir = os.path.join(config.RESULTS_DIR, "screenshots")
            os.makedirs(shot_dir, exist_ok=True)
            shot = os.path.join(shot_dir, test.id().split(".")[-1] + ".png")
            try:
                test.driver.save_screenshot(shot)
            except Exception:  # browser already gone
                shot = ""
        self.records.append({
            "test": test.id(),
            "tc_id": case.get("tc_id", test.id().split(".")[-1]),
            "title": case.get("title", (test.shortDescription() or "")),
            "data_file": case.get("_datafile", ""),
            "status": status,
            "known_defect": case.get("known_defect", ""),
            "seconds": round(time.time() - self._t0.get(test.id(), time.time()), 2),
            "message": msg[:2000],
            "screenshot": os.path.relpath(shot, ROOT) if shot else "",
        })

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, "FAIL", err)

    def addError(self, test, err):
        super().addError(test, err)
        if isinstance(test, unittest.TestCase):
            self._record(test, "ERROR", err)
        else:  # setUpClass / module fixture failure
            self.records.append({"test": str(test), "tc_id": str(test), "title": "", "data_file": "",
                                 "status": "ERROR", "known_defect": "", "seconds": 0,
                                 "message": str(err[1])[:2000], "screenshot": ""})

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, "SKIP", (None, reason))


def load(paths, patterns):
    loader = unittest.TestLoader()
    if patterns:
        loader.testNamePatterns = ["*%s*" % p for p in patterns]
    suite = unittest.TestSuite()
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isfile(p):
            d, f = os.path.split(p)
            suite.addTests(loader.discover(d, pattern=f, top_level_dir=d))
        else:
            for dirpath, dirnames, files in sorted(os.walk(p)):
                dirnames.sort()
                if any(f.startswith("test_") and f.endswith(".py") for f in files):
                    suite.addTests(loader.discover(dirpath, pattern="test_*.py", top_level_dir=dirpath))
                    dirnames[:] = []
    return suite


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="test files or folders")
    ap.add_argument("-k", action="append", default=[], help="only test methods containing this text")
    ap.add_argument("--tag", help="name of the result files")
    args = ap.parse_args()
    tag = args.tag or "_".join(os.path.basename(os.path.normpath(p)).replace(".py", "") for p in args.paths)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)

    print("Site under test: %s   browser: %s   headless: %s" % (config.BASE_URL, config.BROWSER, config.HEADLESS))
    suite = load(args.paths, args.k)
    t0 = time.time()
    runner = unittest.TextTestRunner(verbosity=2, resultclass=LoggingResult, stream=sys.stdout)
    result = runner.run(suite)
    elapsed = time.time() - t0

    recs = result.records
    fields = ["tc_id", "title", "status", "known_defect", "seconds", "message", "screenshot", "data_file", "test"]
    with open(os.path.join(config.RESULTS_DIR, tag + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(recs)
    summary = {
        "tag": tag, "base_url": config.BASE_URL, "browser": config.BROWSER,
        "started": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0)), "seconds": round(elapsed, 1),
        "total": len(recs), "passed": sum(r["status"] == "PASS" for r in recs),
        "failed": sum(r["status"] == "FAIL" for r in recs), "errors": sum(r["status"] == "ERROR" for r in recs),
        "failed_known_defect": [r["tc_id"] for r in recs if r["status"] != "PASS" and r["known_defect"]],
        "failed_unexpected": [r["tc_id"] for r in recs if r["status"] in ("FAIL", "ERROR") and not r["known_defect"]],
        "passed_but_marked_defect": [r["tc_id"] for r in recs if r["status"] == "PASS" and r["known_defect"]],
        "cases": recs,
    }
    with open(os.path.join(config.RESULTS_DIR, tag + ".json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)

    print("\n==== %s: %d cases, %d passed, %d failed, %d errors, %.0f s" % (
        tag, summary["total"], summary["passed"], summary["failed"], summary["errors"], elapsed))
    if summary["failed_known_defect"]:
        print("Failed on a known defect (expected): " + ", ".join(summary["failed_known_defect"]))
    if summary["failed_unexpected"]:
        print("UNEXPECTED failures: " + ", ".join(summary["failed_unexpected"]))
    print("Log: %s.csv / .json in %s" % (tag, config.RESULTS_DIR))
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
