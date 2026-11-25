"""F001 Quiz Settings - Level 2 (member: Tran Ngoc Thoai, 2353147).

No URL, locator, or test step is hardcoded here: site.csv, elements.csv, flows.csv,
testdata.csv, and feature helpers.py are passed to the generic engine level2/l2engine.py,
generating one test method per data row (81 cases total).
"""
import os

from level2.l2engine import build_test_class

L2F001QuizSettings = build_test_class(os.path.dirname(os.path.abspath(__file__)), "L2F001QuizSettings")
