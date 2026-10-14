"""27a — DUPLICATE-DEFINITION DETECTOR + FROZEN BASELINE.

THE HAZARD. The python renderer and the JS renderer are twins over one artifact, and neither can
import the other. So vocabulary gets hand-copied: driver keywords, column headers, axis names. A
one-sided edit then ships two surfaces that disagree, with nothing red — which is #227's shape and
the reason `test_parity_pins.py` exists at all. Those pins are written one at a time, AFTER someone
notices; this detector is the general form, and it fires on the NEXT one instead.

WHY A BASELINE AND NOT A BAN (operator split, 2026-07-28). Thirteen duplicated sets exist today.
Wiring the detector bare would turn the suite red on merge for thirteen pre-existing facts, which
is a guard nobody can keep. So the known thirteen are FROZEN as accepted-for-now and **the build
fails only on the FOURTEENTH**. Zero curation is required to ship it; curating the thirteen down is
27b, one at a time as each is touched.

WHY IT MATTERS MORE THAN IT SOUNDS: the instance that started this was one INTRODUCED WHILE FIXING
THE SAME CLASS (three copies of the brief label set, two of them added by the fix). 27a closes the
hazard against NEW instances now, rather than after thirteen judgement calls.

SCOPE, STATED HONESTLY. This finds LITERAL SETS — three or more distinct quoted strings inside one
bracket — duplicated across the py↔JS boundary. It does not find duplicated numbers, duplicated
logic, or a set split across two statements. It is a floor on a known-recurring shape, not a
general clone detector, and a baseline entry is an ACCEPTED duplicate rather than a solved one.
"""
from __future__ import annotations

import collections
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

# A bracketed literal holding >= 3 DISTINCT quoted strings. Three is the floor because two-member
# pairs are overwhelmingly incidental ({"a", "b"} appears everywhere and means nothing).
_MIN_MEMBERS = 3
_BRACKET = re.compile(r"[\[\{\(]([^\[\]\{\}\(\)]{6,600}?)[\]\}\)]", re.S)
_QUOTED = re.compile(r"""["']([^"'\n]{1,60})["']""")

#: The duplicates that EXIST TODAY, accepted-for-now so the detector can ship un-curated. Each is
#: the sorted member tuple. Curating one down (27b) means DELETING its line here — which is the
#: whole point: the baseline can only ever shrink, and shrinking it is a diff someone reviews.
BASELINE: frozenset[tuple[str, ...]] = frozenset({
    # (A2, 2026-08-03) The EV-gap BRIDGE keys, guarded before rendering in both twins. Genuinely
    # unavoidable: the JS cannot import the Python constant, and the alternative — rendering the
    # bridge without checking its legs — puts "undefined" on the page, which is #176's defect.
    # Accepted rather than removed, and small enough that a drift shows as a missing bridge line
    # on ONE twin, which the parity pins already catch.
    ('net_debt', 'our_ev', 'shares', 'tev'),
    ('%ile', 'cheap', 'discount', 'ev/ebitda', 'expensive', 'multiple', 'p/e', 'percentile',
     're-rate', 'relative', 'rerate', 'underperform', 'valuation', 'vs iwm'),
    ('Apr', 'Aug', 'Dec', 'Feb', 'Jan', 'Jul', 'Jun', 'Mar', 'May', 'Nov', 'Oct', 'Sep'),
    ('backlog', 'bookings', 'deteriorat', 'growth', 'guidance', 'guide', 'orders', 'revenue',
     'shipment', 'top-line', 'topline', 'volume'),
    ('cost structure', 'earnings quality', 'gross profit', 'margin', 'net profit',
     'non-operating', 'operating leverage', 'opex', 'profitab'),
    ('Conv', 'Coupon', 'Cur', 'Floating', 'Maturity', 'Principal', 'Sec', 'Type'),
    ('competit', 'concentrat', 'customer', 'market share', 'moat', 'peer', 'segment',
     'supplier'),
    ('High', 'Low', 'Mean', 'Median', 'Name'),
    ('FY 2026', 'FY 2027', 'FY 2028', 'NTM'),
    ('Liquidity', 'Operational', 'Overall', 'Solvency'),
    ('character', 'depth', 'idiosyncrasy', 'multiple'),
    # RETIRED 2026-09-01 (R3). This recorded a coincidence, not a shared definition:
    # `AXES_BY_RECIPE[R2]` and the card's `AXIS_ORDER` happened to hold the same four
    # names. They are different objects — one is the axes a RECIPE requires, the other the
    # display order across ALL recipes — and adding R3's `earnings` to the display list
    # separated them. The entry is deleted rather than updated, which is what this pin
    # asks for when a duplicate stops existing.
    ('LTM EBITDA', 'NTM EBITDA', 'NTM Revenue'),
    ('base', 'bear', 'bull'),
})


#: JS GENERATED from the python source, not a hand-copied twin: `publish` writes the research
#: desk's script (vinci/theme_intelligence/desk.py `JS`) into the published folder byte for byte on
#: every publish, so it cannot drift (pinned equal by tests/test_theme_intelligence_publish.py).
GENERATED_FROM_PYTHON = ROOT / "frontend" / "theme-intelligence"


def _literal_sets(path: pathlib.Path) -> set[frozenset[str]]:
    """Every bracketed literal of >= 3 DISTINCT quoted strings in one file.

    Duplicate members inside one bracket are skipped: a repeated string is a formatting artifact
    (a wrapped call, a dict of identical values), not a vocabulary set."""
    out: set[frozenset[str]] = set()
    for m in _BRACKET.finditer(path.read_text()):
        members = _QUOTED.findall(m.group(1))
        if len(members) >= _MIN_MEMBERS and len(set(members)) == len(members):
            out.add(frozenset(members))
    return out


def _duplicated_across_twins() -> dict[tuple[str, ...], tuple[list[str], list[str]]]:
    """Literal sets present in BOTH a python file and a JS file → where each side holds it."""
    py: dict[frozenset[str], list[str]] = collections.defaultdict(list)
    js: dict[frozenset[str], list[str]] = collections.defaultdict(list)
    for p in sorted((ROOT / "vinci").rglob("*.py")):
        for s in _literal_sets(p):
            py[s].append(str(p.relative_to(ROOT)))
    for p in sorted((ROOT / "frontend").rglob("*.js")):
        if "node_modules" in str(p) or p.is_relative_to(GENERATED_FROM_PYTHON):
            continue
        for s in _literal_sets(p):
            js[s].append(str(p.relative_to(ROOT)))
    return {tuple(sorted(s)): (py[s], js[s]) for s in set(py) & set(js)}


def test_no_new_literal_set_is_duplicated_across_the_python_js_twins() -> None:
    """THE GUARD: the build fails on the FOURTEENTH duplicate, not the first thirteen.

    A NEW duplicated vocabulary set means one truth now has two maintained copies that cannot
    import each other — so a one-sided edit ships a web page and a markdown page that disagree,
    silently. Either import it (where both sides are python), or add a parity pin binding the two
    copies, or — if it is genuinely incidental short domain vocabulary — add it to BASELINE with
    that argument in the diff.
    """
    found = _duplicated_across_twins()
    assert found, (
        "the detector found NO duplicated sets at all — it has stopped working (a regex or a path "
        "moved), and a detector that finds nothing passes for the wrong reason")

    new = sorted(set(found) - BASELINE)
    assert not new, "NEW duplicated literal set(s) across the py↔JS twins:\n" + "\n".join(
        f"  {list(k)}\n      py: {found[k][0]}\n      js: {found[k][1]}" for k in new)


def test_the_baseline_records_only_duplicates_that_still_exist() -> None:
    """The baseline may only SHRINK. An entry whose duplicate is gone is a curated win (27b) and
    must be deleted from the list — otherwise the baseline slowly becomes a list of things that
    used to be true, and the detector's real coverage drifts away from its stated coverage while
    staying green. That is the assertion-integrity class applied to this guard's own bookkeeping."""
    found = _duplicated_across_twins()
    stale = sorted(BASELINE - set(found))
    assert not stale, (
        "BASELINE entries whose duplicate no longer exists — delete them, the curation is done:\n"
        + "\n".join(f"  {list(k)}" for k in stale))
