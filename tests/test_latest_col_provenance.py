""""The last column is the latest" is a claim about the export, so it gets checked.

TWO AUDIT P2s, one root. Nine decision-path extractors take `_latest_col`'s value as the LATEST and
stamp it with the period label returned beside it. Nothing asserted that the export runs
chronologically left to right — it was inherited from how CIQ happens to write the file, and if it
ever ran the other way the VALUE and its LABEL would be wrong together.

That is the shape `_capital_summary` already refuses on, and the one item 20 records arriving
through the DATA PROVIDER rather than through the code: `source_ref="Close (latest)"` sitting on a
months-old value in three dossiers. `book_value_per_share` carried the literal remaining instance —
a stamp reading `Book Value/Share (latest)` that named no period at all.

MEASURED BEFORE BUILDING: the ascending convention holds across all 19 committed bundles (Balance
Sheet / Income Statement / Cash Flow, both frequencies — 0 violations). So the guard is DEFENSIVE,
exactly as `_capital_summary`'s was when it shipped, and it costs nothing today: every caller
already handles the `None` returned for an empty row, so a refusal travels an existing path.

WHAT THE UNDATED STAMP WAS HIDING, and the reason this is not cosmetic: on **2 of 19 names (ONON,
UBER) the landed column is a `Press Release` column**, not a fiscal period — a pre-filing figure on
a different basis from the audited balance sheet beside it, presented identically. Naming the
column is what makes those two visible.
"""
from __future__ import annotations

import pytest

from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, excel_date
from vinci.dossier.manual_store import LocalFolderStore


def _bundles() -> list[tuple[str, CiqBundle]]:
    root = get_config().data_dir / "manual" / "ciq"
    if not root.is_dir() or not any(root.iterdir()):
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    ms = LocalFolderStore(root)
    out = []
    for tk in sorted(p.name for p in root.iterdir() if p.is_dir()):
        files = ms.files(tk)
        if files:
            out.append((tk, CiqBundle.from_files(tk, files)))
    return out


# ─── the guard ──────────────────────────────────────────────────────────────────────────────────
def test_a_descending_export_is_refused_rather_than_mislabelled() -> None:
    """THE POSITIVE HALF, on rows shaped like the sheets this reads. A right-to-left export makes
    the rightmost column the OLDEST; returning it would hand a caller a stale value stamped with a
    stale period and call it the latest. Refusing is what `_capital_summary` already does, and the
    house rule it follows: refuse rather than mislabel."""
    ascending = [
        ["Fiscal Period", 46112.0, 46203.0],   # 2026-03-31 → 2026-06-30
        ["Book Value/Share", 9.0, 11.0],
    ]
    got = cs._latest_col(ascending, 1, 0)
    assert got is not None, "an ascending export must still resolve"
    col, value, _ = got
    assert (col, value) == (2, 11.0), "the rightmost column is the latest when order is ascending"

    descending = [
        ["Fiscal Period", 46203.0, 46112.0],   # 2026-06-30 → 2026-03-31  (backwards)
        ["Book Value/Share", 11.0, 9.0],
    ]
    assert cs._latest_col(descending, 1, 0) is None, (
        "a descending export returned a value: the last column is the OLDEST there, so both the "
        "figure and the period stamped beside it would be wrong")


def test_an_unreadable_header_degrades_rather_than_refusing() -> None:
    """THE NEGATIVE HALF — a PROVEN violation is required, never an unparseable header. Only
    columns whose dates decode are compared (as `_capital_summary` does), so a sheet labelled
    "LTM" / "FY2025" / "Press Release …" still resolves. Refusing on those would blank out real
    values across the fleet to guard against an ordering nobody has demonstrated."""
    rows = [
        ["Fiscal Period", "LTM", "Press Release Jun-30-2026"],
        ["Book Value/Share", 9.0, 11.0],
    ]
    got = cs._latest_col(rows, 1, 0)
    assert got is not None and got[1] == 11.0, (
        "an undated header triggered a refusal — 'order unknown' is not 'order violated'")

    # ONE decodable date cannot establish an ordering either.
    single = [["Fiscal Period", 46203.0, "n/a"], ["Book Value/Share", 11.0, 12.0]]
    assert cs._latest_col(single, 1, 0) is not None


def test_the_ascending_convention_holds_on_every_committed_bundle() -> None:
    """THE MEASUREMENT THE GUARD RESTS ON, kept as a live check rather than a claim in a docstring.
    If a future export ever violates it, this reddens and names the sheet — which is the moment to
    decide whether the guard's refusal is the right remedy for that name, rather than discovering
    it through a wrong figure on a page."""
    checked, violations = 0, []
    for tk, b in _bundles():
        for sheet, hdrfn in (("Balance Sheet", cs._bs_period_header),
                             ("Income Statement", cs._period_header),
                             ("Cash Flow", cs._period_header)):
            for freq in ("annual", "quarterly"):
                try:
                    rows = b.sheet("financials", sheet, freq=freq)
                except Exception:
                    continue
                hdr = hdrfn(rows)
                if hdr is None:
                    continue
                checked += 1
                dates = [d for j in range(1, len(rows[hdr]))
                         if (d := excel_date(rows[hdr][j])) is not None]
                if len(dates) > 1 and dates != sorted(dates):
                    violations.append(f"{tk}/{sheet}/{freq}")
    assert checked, "no sheet was read — the corpus sweep found nothing to check"
    assert not violations, (
        f"the ascending convention no longer holds on {violations} — `_latest_col` now REFUSES "
        f"there, so those fields go UNKNOWN. That is the guard working, but decide deliberately "
        f"whether refusal is right for that name before re-assembling")


# ─── the stamp ──────────────────────────────────────────────────────────────────────────────────
def test_the_book_value_stamp_names_its_period_and_never_says_latest() -> None:
    """THE LITERAL `…(latest)` INSTANCE item 20 warns about. An undated stamp asserting recency
    cannot be checked by a reader and cannot go stale visibly. Asserted over the live corpus as a
    PROPERTY of every stamp rather than a table of expected dates, so a re-pull cannot rot it."""
    seen = 0
    for tk, b in _bundles():
        s = cs.book_value_per_share(b)
        if s.value is None:
            continue
        seen += 1
        ref = s.source_ref or ""
        assert "(latest)" not in ref, (
            f"{tk}: the stamp still claims recency without naming a period — {ref!r}")
        assert "Book Value/Share (" in ref, f"{tk}: the stamp names no column at all — {ref!r}"
        inside = ref.split("Book Value/Share (", 1)[1].rstrip(")")
        assert inside.strip(), f"{tk}: empty period in the stamp — {ref!r}"
        # a raw Excel SERIAL is not a period a reader can use — it must be a date or the column's
        # own words, never the number CIQ stores underneath
        assert not inside.replace(".", "").isdigit(), (
            f"{tk}: the stamp carries a raw serial {inside!r} instead of a decoded date — the "
            f"rendered label was parsed where the structured cell was one index away")
    assert seen, "no name yielded a book value — the assertion never ran"


def test_a_press_release_basis_is_visible_in_the_stamp() -> None:
    """WHAT THE UNDATED STAMP HID. Some names' rightmost Balance-Sheet column is a `Press Release`
    column — a pre-filing figure on a different basis from the audited sheet beside it. Under
    `(latest)` both looked identical. Observed on ONON and UBER at build time; asserted as
    "wherever that column is what we land on, the stamp says so", so it holds whoever it is."""
    from vinci.dossier.ciq import CiqUnavailableError

    checked = 0
    for tk, b in _bundles():
        try:
            bs = b.sheet("financials", "Balance Sheet", freq="annual")
        except CiqUnavailableError:
            continue
        hdr = cs._bs_period_header(bs)
        ri = next((i for i, r in enumerate(bs)
                   if r and str(r[0]).strip() == "Book Value/Share"), None)
        if hdr is None or ri is None:
            continue
        got = cs._latest_col(bs, ri, hdr)
        if got is None:
            continue
        col, _, _ = got
        if excel_date(bs[hdr][col]) is not None:
            continue                      # a normal dated period column
        checked += 1
        ref = cs.book_value_per_share(b).source_ref or ""
        label = " ".join(str(bs[hdr][col]).split())
        assert label in ref, (
            f"{tk}: landed on a non-period column {label!r} and the stamp does not say so — "
            f"{ref!r}. That basis difference is exactly what an undated stamp hides")
    if not checked:
        pytest.skip("no name currently lands on a non-period column (ONON/UBER did at build time)")
