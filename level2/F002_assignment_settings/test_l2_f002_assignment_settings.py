"""F002 Assignment Settings - Level 2 (member: Naman Chahar, 2560173).

No URL, locator, or test step is written here: site.csv, elements.csv, flows.csv and testdata.csv
(plus helpers.py) are passed to the generic engine level2/l2engine.py, which creates one test per
data row (all 85 Project #2 cases).
"""
import os

from level2.l2engine import build_test_class

L2F002AssignmentSettings = build_test_class(
    os.path.dirname(os.path.abspath(__file__)), "L2F002AssignmentSettings")
