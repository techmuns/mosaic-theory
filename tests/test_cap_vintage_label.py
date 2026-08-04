"""The cap's clause-(e) vintage label names the CAP's date — never a neighbouring panel's.

WHY THIS EXISTS (O3, 2026-08-04). The Snapshot prints a live EOD close beside a frozen CIQ market
cap. Clause (e) requires the older value to render *marked as such, with its vintage date*, and the
renderer did print a date — **the wrong panel's**. `render.py` fed `_brief_snapshot(cap_as_of=…)`
from `valuation.implied_expectations.multiples_as_of`, the MULTIPLES sheet, because the cap's own
vintage existed ONLY inside `market_cap.source_ref` and there was nothing structured to bind to.

**Wrong on 11 of 11 committed names.** Worst: IT rendered a cap as-of `2026-06-25` as `2026-07-27`
— five weeks presented as three days. MVST erred the other way (`2026-05-15` for a `2026-06-24`
cap). A stamp naming the wrong object is worse than no stamp: this one concealed precisely the gap
it existed to disclose, and it did so at the moment SMPL's cap-vs-spot divergence went from 0.3% to
9.2% and nothing else covers it (`reconcile_cap`'s result is a gate input, never stored or
rendered).

THE FIX IS A DIRECTION, NOT A LOOKUP. `comps_as_of_date` is the ONE derivation; `comps_as_of`
renders it, `_comps_asof_suffix` stamps that onto every comps `source_ref`, and
`StockInfo.market_cap_as_of` carries the value. Recovering the date by regex over the rendered
suffix would have been the second parser of one display string — the bug class the handbook names.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import vinci.dossier.render as dr
import vinci.dossier.schemas as ds

ROOT = Path(__file__).resolve().parents[1]

_P = ds.Sourced.present


def _py_code(src: str) -> str:
    """Python source with COMMENTS AND STRINGS REMOVED — what the interpreter acts on.

    The first cut of the scans below matched the bare word and went red on the comments that
    EXPLAIN the fix: a guard that fires because you documented why it exists teaches you to delete
    the documentation. A source scan must read code, never prose."""
    import io
    import tokenize

    out: list[str] = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type not in (tokenize.COMMENT, tokenize.STRING):
            out.append(tok.string)
    return " ".join(out)


def _js_code(src: str) -> str:
    """JS source with `//` line comments removed — same reason as `_py_code`."""
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in src.splitlines())


def _si(**over: object) -> ds.StockInfo:
    """A PRESENT StockInfo. Frozen fixture — value pins live here, never on a re-drawn artifact."""
    base: dict[str, object] = {
        "price": _P(11.32, source_ref="EOD"), "high_52w": _P(34.19, source_ref="EOD"),
        "low_52w": _P(9.88, source_ref="EOD"), "shares_out": _P(88460545.0, source_ref="EDGAR"),
        "book_value_ps": _P(16.03, source_ref="CIQ"), "market_cap": _P(909.4, source_ref="CIQ"),
        "as_of": dt.date(2026, 8, 3), "market_cap_as_of": dt.date(2026, 7, 24)}
    base.update(over)
    return ds.StockInfo(**base)  # type: ignore[arg-type]


def test_the_label_states_the_caps_own_vintage() -> None:
    """POSITIVE PIN. SMPL's real shape: an 2026-08-03 close beside a 2026-07-24 cap."""
    body = " ".join(dr._brief_snapshot("Nasdaq", _si()))
    assert "CMP $11.32 (2026-08-03)" in body
    assert "cap $909M (2026-07-24)" in body, body


def test_a_cap_with_no_vintage_prints_no_date_rather_than_borrowing_one() -> None:
    """NEGATIVE PIN, and the REAL OBSERVED FAILURE SHAPE — this is how the defect got in.

    Every committed dossier predates `market_cap_as_of`, so on those the field is None while
    `implied_expectations.multiples_as_of` is sitting right there, populated and plausible. That is
    exactly the state in which the renderer reached for the neighbour. It must now print no cap
    date at all: an unlabelled cap is a disclosure gap, a MISLABELLED one is a false statement, and
    the false statement is the worse failure. Re-assembly is what supplies the real date."""
    body = " ".join(dr._brief_snapshot("Nasdaq", _si(market_cap_as_of=None)))
    assert "cap $909M" in body, body
    assert re.search(r"cap \$909M \(\d{4}-\d{2}-\d{2}\)", body) is None, (
        "a cap with NO recorded vintage rendered a date anyway — the renderer is falling back to "
        f"some other panel's as-of, which is the O3 defect returning: {body}")


def test_the_label_is_not_reachable_from_the_multiples_panel_at_all() -> None:
    """THE REGRESSION PIN. `_brief_snapshot` must not accept a cap date from its caller — the
    parameter that carried `multiples_as_of` is GONE, so the wrong panel cannot be re-wired in by
    passing it. A signature pin rather than a value pin, because the defect was a WIRING choice."""
    import inspect

    params = list(inspect.signature(dr._brief_snapshot).parameters)
    assert params == ["exchange", "si"], (
        f"_brief_snapshot takes {params} — a third parameter is how `multiples_as_of` reached the "
        "cap label; the vintage must come off the StockInfo, not off the call site")
    code = _py_code(inspect.getsource(dr._brief_snapshot))
    assert "market_cap_as_of" in code, "the label no longer reads the cap's own vintage"
    assert "multiples_as_of" not in code, "the multiples panel is back in the cap label"


def test_a_cap_dated_the_same_day_as_the_price_states_no_vintage() -> None:
    """The label exists to disclose a GAP. Same day → no gap → no parenthetical, which is why the
    absent-date assertion above cannot simply be 'a date is always printed'."""
    body = " ".join(dr._brief_snapshot("Nasdaq", _si(market_cap_as_of=dt.date(2026, 8, 3))))
    assert "cap $909M" in body and "cap $909M (" not in body, body


def test_the_string_is_rendered_from_the_structured_date_not_beside_it() -> None:
    """ONE DERIVATION, and the direction is the point. `comps_as_of` (the string the source_ref
    carries) must be built from `comps_as_of_date` (the value the field carries), so the two cannot
    drift apart — the property that made the guidance-vintage fix hold. Asserted structurally: the
    string function calls the date function and does not re-scan the sheet itself."""
    import inspect

    from vinci.dossier import ciq_sheets as cs

    code = _py_code(inspect.getsource(cs.comps_as_of))
    assert "comps_as_of_date" in code, (
        "comps_as_of no longer reads comps_as_of_date — two independent derivations of one vintage "
        "is how the string and the field start disagreeing")
    assert "_scan_asof_header" not in code and "_sidecar_as_of" not in code, (
        "comps_as_of re-derives the date itself instead of rendering the shared derivation")


def test_the_web_twin_reads_the_same_field() -> None:
    """BOTH TWINS. The md and the web card render the same label from the same fact; the web one
    carried the identical wiring bug and must not keep it. Source-scanned, the established pattern
    for twin parity in this suite."""
    js = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    m = re.search(r"if \(ok\(si\.market_cap\)\) \{(.*?)\n  \}", js, re.S)
    assert m, "the web cap label is gone — twin parity cannot be checked"
    body = _js_code(m.group(1))
    assert "si.market_cap_as_of" in body, (
        "the web cap label does not read the cap's own vintage — the md twin was fixed and the "
        "web one left on the neighbouring panel")
    assert "multiples_as_of" not in body, (
        "the web cap label still reads implied_expectations.multiples_as_of — a DIFFERENT panel's "
        "date, which is the O3 defect surviving in the twin that actually gets read on screen")
