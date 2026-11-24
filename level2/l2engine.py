"""Level 2 engine: data-driven tests whose test data AND test items (site URLs, page elements, the steps
of each flow) all come from files. The engine itself knows nothing about a particular Moodle form.

A feature folder contains
    site.csv      key,value                     base_url (blank = MOODLE_BASE_URL) and named page paths
    elements.csv  name,locator,kind,description  every element the flows touch; kind tells how to set it:
                  text | keyboard (typed key by key, browser maxlength applies) | select (visible label) |
                  checkbox (on/off) | date (YYYY[-MM-DD[ HH:MM]] or off) | editor (TinyMCE) |
                  button | link | label (read-only: messages, headings)
    flows.csv     flow,step,keyword,target,value  the steps of each flow (keywords below)
    testdata.csv  tc_id,title,flow,<one column per input element name>,
                  expected_element,expected_result[,expected_element_2,expected_result_2 ...]
                  plus any extra column a flow refers to as ${column}

Keywords (target = element name, page key, flow name or URL; value may use ${column} of the data row)
    open <page|path>               open a page of site.csv (or a path/URL)
    fill                           set every input element whose name is a column with a non-blank value
    set <element> <value>          set one element according to its kind
    click / submit <element>       click (submit = click and wait for the next page)
    click_if_present / submit_if_present <element>
    pause <ms>
    helper <method> <args>         call a function of the folder's optional helpers.py (fn(moodle, *args))
                                   or else a Moodle page helper (e.g. expand_all, delete_activities quiz);
                                   args are separated by ';'
    call <flow>                    run another flow
    cleanup <flow> [condition]     run that flow after the case even if a check failed (skipped when the
                                   condition, e.g. ${cleanup}, is blank)
    verify_expected                check every expected_element_N / expected_result_N pair of the row
    verify <element> <expected>    one check (same rules as expected_result)
Expected cells: plain text = exact text (labels) / value (inputs) / selected label (selects);
    {{PRESENT}} {{ABSENT}} {{CONTAINS=text}} {{NOTCONTAINS=text}} {{NOTEMPTY}} {{LEN=n}} {{OPTIONS=a;b;!c}}
    {{CHECKED}} {{UNCHECKED}}
    {{ENABLED}} {{DISABLED}}
Data cells use the notation of common.data (blank = keep default, {{EMPTY}}, {{X*n}}).
Flows named before_all / after_all run once around all cases of the folder (like PREP / POST).
"""
import importlib.util
import os
import re

from selenium.common.exceptions import WebDriverException

from common import config
from common.base import MoodleTestCase
from common.data import expand, read_rows, split
from common.ddt import data_driven

INPUT_KINDS = {"text", "keyboard", "select", "checkbox", "date", "editor"}
_VAR = re.compile(r"\$\{([^}]+)\}")


class Feature:
    def __init__(self, folder):
        self.folder = folder
        self.site = {r["key"]: r["value"] for r in read_rows(os.path.join(folder, "site.csv"))}
        self.elements = {r["name"]: r for r in read_rows(os.path.join(folder, "elements.csv"))}
        self.element_order = [r["name"] for r in read_rows(os.path.join(folder, "elements.csv"))]
        self.flows = {}
        for r in read_rows(os.path.join(folder, "flows.csv")):
            self.flows.setdefault(r["flow"], []).append(r)
        for steps in self.flows.values():
            steps.sort(key=lambda s: int(s["step"]))
        self.helpers = None
        helpers_py = os.path.join(folder, "helpers.py")
        if os.path.exists(helpers_py):
            spec = importlib.util.spec_from_file_location("l2helpers_" + os.path.basename(folder), helpers_py)
            self.helpers = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.helpers)

    @property
    def base_url(self):
        return self.site.get("base_url") or config.BASE_URL


class KeywordRunner:
    def __init__(self, test, feature, row):
        self.t, self.f, self.row = test, feature, row
        self.m = test.m

    # ------------------------------------------------------------------ variables / elements
    def sub(self, text):
        def rep(mo):
            key = mo.group(1)
            if key == "BASE":
                return self.f.base_url
            if key not in self.row:
                raise KeyError("flow uses ${%s} but the data row has no such column" % key)
            v = expand(self.row[key])
            return "" if v is None else v
        return _VAR.sub(rep, text or "")

    def element(self, name):
        name = self.sub(name)
        if name not in self.f.elements:
            raise KeyError("element %r is not defined in elements.csv" % name)
        e = self.f.elements[name]
        return self.sub(e["locator"]), e["kind"]

    def page(self, target):
        target = self.sub(target)
        return self.sub(self.f.site.get(target, target))

    # ------------------------------------------------------------------ actions
    def set(self, name, value):
        loc, kind = self.element(name)
        m = self.m
        if kind == "select":
            m.select(loc, value)
        elif kind == "checkbox":
            m.set_checkbox(loc, value.strip().lower() in ("on", "yes", "1", "true", "checked"))
        elif kind == "date":
            m.set_date(loc.split("=", 1)[1], value)       # locator id=<prefix>, e.g. id=id_startdate
        elif kind == "editor":
            m.set_editor(loc.split("=", 1)[1], value)     # locator id=<textarea id>
        elif kind in ("text", "keyboard"):
            m.type(loc, value, keyboard=kind == "keyboard")
        else:
            raise ValueError("element %r (%s) cannot be set" % (name, kind))

    def run_flow(self, name):
        if name not in self.f.flows:
            raise KeyError("flow %r is not defined in flows.csv" % name)
        for step in self.f.flows[name]:
            self.step(step["keyword"].strip(), step["target"], step["value"])

    def step(self, kw, target, value):
        m = self.m
        if kw == "open":
            m.open(self.page(target))
        elif kw == "fill":
            for name in self.f.element_order:
                if self.f.elements[name]["kind"] in INPUT_KINDS and self.row.get(name):
                    self.set(name, expand(self.row[name]))
        elif kw == "set":
            single = re.fullmatch(r"\$\{([^}]+)\}", value.strip())
            if single:                      # value taken from one data column: blank cell = keep default
                cell = self.row.get(single.group(1), "")
                if cell:
                    self.set(target, expand(cell))
            else:
                self.set(target, expand(self.sub(value)) or "")
        elif kw in ("click", "submit"):
            loc, _ = self.element(target)
            m.click(loc) if kw == "click" else m.submit(loc)
        elif kw in ("click_if_present", "submit_if_present"):
            loc, _ = self.element(target)
            if m.exists(loc):
                m.click(loc) if kw == "click_if_present" else m.submit(loc)
        elif kw == "pause":
            m.pause(int(value or target))
        elif kw == "helper":
            args = [self.sub(a) for a in split(value)]
            fn = getattr(self.f.helpers, target, None)
            if fn is not None:                 # helpers.py of the feature folder: fn(moodle, *args)
                fn(m, *args)
            else:                              # generic Moodle page helper (common/moodle.py)
                getattr(m, target)(*args)
        elif kw == "call":
            self.run_flow(self.sub(target))
        elif kw == "cleanup":
            # cleanup <flow> [<condition>]: registered only when the condition (e.g. ${cleanup}) is not blank
            flow = self.sub(target)
            if flow and (not value or self.sub(value).strip()):
                self.t.addCleanup(self.run_cleanup, flow)
        elif kw == "verify_expected":
            n = 1
            while True:
                suffix = "" if n == 1 else "_%d" % n
                if "expected_element" + suffix not in self.row:
                    break
                el, exp = self.row["expected_element" + suffix], self.row.get("expected_result" + suffix, "")
                if el:
                    self.verify(el, exp)
                n += 1
        elif kw == "verify":
            self.verify(self.sub(target), value)
        else:
            raise ValueError("unknown keyword %r" % kw)

    def run_cleanup(self, flow):
        try:
            self.run_flow(flow)
        except WebDriverException as e:  # cleanup must not hide the verdict of the case
            print("cleanup flow %s failed: %s" % (flow, str(e).splitlines()[0]))

    # ------------------------------------------------------------------ checks
    def verify(self, name, expected_cell):
        t, m = self.t, self.m
        loc, kind = self.element(name)
        exp = self.sub(expected_cell)
        what = "%s (%s)" % (name, loc)
        special = re.match(r"^\{\{([A-Z]+)(?:=(.*))?\}\}$", exp, re.S)
        if special:
            op, arg = special.group(1), special.group(2)
            if op == "PRESENT":
                t.verify_present(loc, what)
            elif op == "ABSENT":
                t.verify_not_present(loc, what)
            elif op == "CONTAINS":
                t.verify_contains(loc, expand(arg), what)
            elif op == "NOTCONTAINS":
                text = m.text(loc, timeout=1) if m.exists(loc) else ""
                t.verify(expand(arg) not in text, "%s must not contain %r" % (what, expand(arg)))
            elif op == "NOTEMPTY":
                text = m.text(loc, timeout=1) if m.exists(loc) else ""
                t.verify(text != "", "%s must show a message" % what)
            elif op == "LEN":
                t.verify_equal(int(arg), len(m.value(loc) or ""), "length of " + what)
            elif op == "OPTIONS":
                offered = m.options(loc)
                for v in split(arg):
                    if v.startswith("!"):
                        t.verify(v[1:] not in offered, "%s must not offer %s" % (what, v[1:]))
                    else:
                        t.verify(v in offered, "%s must offer %s (offered %s)" % (what, v, offered))
            elif op in ("CHECKED", "UNCHECKED"):
                t.verify_equal(op == "CHECKED", m.find(loc).is_selected(), "checked state of " + what)
            elif op in ("ENABLED", "DISABLED"):
                t.verify_equal(op == "ENABLED", m.find(loc).is_enabled(), "enabled state of " + what)
            elif op == "EMPTY":
                self.compare(loc, kind, "", what)
            else:
                raise ValueError("unknown expectation %s" % exp)
            return
        self.compare(loc, kind, expand(exp) or "", what)

    def compare(self, loc, kind, exp, what):
        t, m = self.t, self.m
        try:
            if kind == "select":
                t.verify_equal(exp, m.selected_label(loc), what)
            elif kind == "editor":
                t.verify_equal(exp, m.editor_text(loc.split("=", 1)[1]), what)
            elif kind in ("text", "keyboard"):
                t.verify_value(loc, exp, what)
            else:
                t.verify_text(loc, exp, what)
        except WebDriverException:
            t.verify(False, "%s: element not found (expected %r)" % (what, exp[:60]))


def build_test_class(folder, class_name):
    """Create the unittest class for one Level 2 feature folder (one test method per testdata.csv row).

    Optional flows 'before_all' / 'after_all' in flows.csv run once before the first / after the last
    case (the PREP / POST cases of the Project #2 suites); a failed check in them stops the class."""
    feature = Feature(folder)

    class _L2(MoodleTestCase):
        base_url = feature.base_url

        @classmethod
        def _class_flow(cls, name):
            if name not in feature.flows:
                return
            t = cls("run_case")
            t.verificationErrors = []
            KeywordRunner(t, feature, {}).run_flow(name)
            if t.verificationErrors:
                raise AssertionError("%s flow: %s" % (name, t.verificationErrors))

        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls._class_flow("before_all")

        @classmethod
        def tearDownClass(cls):
            try:
                cls._class_flow("after_all")
            finally:
                super().tearDownClass()

        def run_case(self, row):
            KeywordRunner(self, feature, row).run_flow(row["flow"])

    _L2.__name__ = _L2.__qualname__ = class_name
    return data_driven(os.path.join(folder, "testdata.csv"))(_L2)
