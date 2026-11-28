# NFR-02 — Security: XSS / HTML injection (F002)

**Type:** non-functional security testing (stored cross-site scripting / HTML injection).
**Requirement:** user HTML in the Assignment **name**, **description** and **activity instructions** must be
sanitised; scripts and event handlers must never execute on the Assignment view or settings page.

**Approach:** Selenium saves one payload per data row, watches for a JavaScript dialog, then inspects
the rendered `region-main` DOM for a raw `<script>...XSSNFR02` element or an `onerror` handler containing
the marker.

**Tool:** Python 3 + Selenium 4 + unittest, headless Chromium.
**Data:** `data/xss_cases.csv` — 8 payloads: `<script>`, `<img onerror>`, attribute breakout, encoded text,
and safe markup mixed with a script.

**Evidence:** `results/NFR-02_xss_<tc_id>.json` (alert fired, raw script/onerror detection, heading,
URL, DOM excerpt).

Run:

```bash
cd /home/naman/miloo-software-testing
.venv/bin/python run_tests.py nonfunctional/NFR-02_F002_xss --tag NFR02_F002
```
