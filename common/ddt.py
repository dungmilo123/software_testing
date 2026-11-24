"""Minimal data-driven test generator for unittest (no third-party package needed).

    @data_driven("data/create_course.csv")
    class CreateCourseTest(MoodleTestCase):
        def run_case(self, row): ...

turns every data row into its own test method ``test_TC_004_001`` so unittest reports one result per
test case ID. The row is attached to the method (``__case__``) so the runner can print the title and the
known-defect note next to the verdict.
"""
import os
import re
import sys

from common.data import read_rows


def _method_name(tc_id):
    return "test_" + re.sub(r"\W+", "_", tc_id).strip("_")


def data_driven(*paths, id_field="tc_id", runner="run_case"):
    """Class decorator: one test method per row of the given data files (paths relative to the module)."""

    def wrap(cls):
        module_dir = os.path.dirname(os.path.abspath(sys.modules[cls.__module__].__file__))
        for p in paths:
            full = p if os.path.isabs(p) else os.path.join(module_dir, p)
            for row in read_rows(full):
                name = _method_name(row[id_field])
                if hasattr(cls, name):
                    raise ValueError("duplicate test case id %s in %s" % (row[id_field], full))

                def test(self, _row=row):
                    getattr(self, runner)(_row)

                test.__name__ = name
                test.__doc__ = "%s %s" % (row[id_field], row.get("title", ""))
                test.__case__ = dict(row, _datafile=os.path.basename(full))
                setattr(cls, name, test)
        return cls

    return wrap
