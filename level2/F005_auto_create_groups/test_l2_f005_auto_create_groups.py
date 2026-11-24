"""F005 Auto-create groups - Level 2 (member: Duong Cong Chi Dung).

No URL, locator or step is written here: site.csv, elements.csv, flows.csv, testdata.csv (and the small
helpers.py) in this folder are given to the generic engine level2/l2engine.py, one test per data row.
"""
import os

from level2.l2engine import build_test_class

L2F005AutoCreateGroups = build_test_class(os.path.dirname(os.path.abspath(__file__)), "L2F005AutoCreateGroups")
