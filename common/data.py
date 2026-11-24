"""Reading test data files (.csv or .xlsx) and decoding the cell notation used in them.

Cell notation (same in every data file):
    (blank cell)     leave the field untouched (keep the form default)
    {{EMPTY}}        clear the field (submit an empty value)
    {{X*n}}          the text X repeated n times, e.g. {{N*1333}}, {{ *3}} = three spaces
    abc{{Z*5}}def    patterns can be mixed with literal text
    a\\nb            literal backslash-n in a cell becomes a line break
"""
import csv
import os
import re

_REPEAT = re.compile(r"\{\{(.+?)\*(\d+)\}\}", re.S)


def read_rows(path):
    """Return the data rows of a .csv (UTF-8) or .xlsx file as a list of dicts (header = first row).

    Rows whose first cell starts with '#' are comments and are skipped.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        sheet = load_workbook(path, read_only=True, data_only=True).active
        values = [["" if v is None else str(v) for v in r] for r in sheet.iter_rows(values_only=True)]
        header, body = values[0], values[1:]
        rows = [dict(zip(header, r)) for r in body]
    else:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        first = next(iter(r.values()), "") or ""
        if not any((v or "").strip() for v in r.values()) or first.startswith("#"):
            continue
        out.append({k.strip(): (v if v is not None else "") for k, v in r.items() if k})
    return out


def expand(value):
    """Decode a data cell. Returns None for a blank cell ("do not touch"), otherwise the real string."""
    if value is None or value == "":
        return None
    if value == "{{EMPTY}}":
        return ""
    value = _REPEAT.sub(lambda m: m.group(1) * int(m.group(2)), value)
    return value.replace("\\n", "\n")


def split(value, sep=";"):
    """Split a multi-value cell such as 'topics;weeks;!social' into stripped items."""
    if not value:
        return []
    return [p.strip() for p in value.split(sep) if p.strip()]


def describe(value, limit=60):
    """Short printable form of a (possibly very long) value for logs and assertion messages."""
    if value is None:
        return "<default>"
    if isinstance(value, str) and len(value) > limit:
        return "%r... (%d chars)" % (value[:20], len(value))
    return repr(value)
