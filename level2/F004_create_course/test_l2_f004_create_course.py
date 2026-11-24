"""F004 Create course - Level 2 (member: Luong Tan Tai).

No URL, locator or step is written here: site.csv, elements.csv, flows.csv and testdata.csv in this
folder are given to the generic engine (level2/l2engine.py), which creates one test per data row.
"""
import os

from level2.l2engine import build_test_class

L2F004CreateCourse = build_test_class(os.path.dirname(os.path.abspath(__file__)), "L2F004CreateCourse")
