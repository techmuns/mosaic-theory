"""`horizon_read` reads each metric's revision counts from its OWN block.

THE DEFECT, MEASURED 2026-10-07 on the 26 committed names. Each Revisions block ended at the next
metric on `_METRICS`, so `_revisions_windows` scanned on through every block in between and kept
the LAST one's windows: 114 printed lines carried another block's counts, 24 lines the metric's own
block carries were dropped (the wrong block had no figure there), and 2 showed counts where the
metric's own block has none. AMZN's 'Net Income (GAAP) FQ3 2026 … 3m 41↑/4↓' were TEV's; its own
block reads 24↑/8↓. The field is a synthesis input.

The CIQ-backed tests read the licensed workbooks on disk and SKIP without them (never committed).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, clean_num
from vinci.dossier.refresh import (
    RefreshRefusedError,
    horizon_read_transform,
    moved_cited_counts,
    refresh_dossier,
)

ROOT = Path(__file__).resolve().parents[1]
COMMITTED = sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json"))


def _bundle(ticker: str) -> CiqBundle:
    """The name's bundle, or SKIP — the licensed workbooks are never committed."""
    from vinci.config import get_config
    from vinci.dossier.manual_store import LocalFolderStore

    files = LocalFolderStore(get_config().data_dir / "manual" / "ciq").files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


def _lines(value: str) -> set[str]:
    return set(value.split("  [")[0].split("; "))


def _own_block_lines(rows: list[list[Any]]) -> set[str]:
    """The lines a metric's OWN block yields, read independently of `_block_starts`: a block runs
    from its title to the next PERIOD HEADER (the next block's 'FQ…/FY…' row)."""
    out: set[str] = set()
    for bi in cs._metric_starts(rows, cs._METRICS):
        header = rows[bi + 1]
        stop = next((k for k in range(bi + 2, len(rows)) if any(
            isinstance(c, str) and c.strip().startswith(("FQ", "FY")) for c in rows[k])), len(rows))
        window_rows: dict[str, dict[str, int]] = {}
        cur: str | None = None
        for k in range(bi + 1, stop):
            lbl = str(rows[k][0]).strip()
            wk = next((w for w, name in cs._REV_WINDOWS if lbl == name), None)
            if wk is not None:
                cur = wk
                window_rows[wk] = {}
            elif cur is not None and lbl in ("Upward", "Downward"):
                window_rows[cur][lbl] = k
        for col in cs._first_fq_cols(header):
            parts = []
            for wk, _name in cs._REV_WINDOWS:
                w = window_rows.get(wk) or {}
                up = clean_num(rows[w["Upward"]][col]) if "Upward" in w else None
                dn = clean_num(rows[w["Downward"]][col]) if "Downward" in w else None
                if up is not None or dn is not None:
                    parts.append(f"{wk} {int(up or 0)}↑/{int(dn or 0)}↓")
            if parts:
                label = f"{str(rows[bi][0]).strip()} {str(header[col]).strip()}"
                out.add(f"{label}: " + ", ".join(parts))
    return out


@pytest.mark.parametrize("ticker", COMMITTED)
def test_every_line_is_its_own_blocks_counts(ticker: str) -> None:
    """ACROSS THE CORPUS: the whole field equals what each metric's own block says — no line from a
    neighbour, none dropped, none invented."""
    b = _bundle(ticker)
    value = cs.horizon_read(b).value
    assert value is not None
    assert _lines(value) == _own_block_lines(b.sheet("estimates", "Revisions"))


@pytest.mark.parametrize("ticker", COMMITTED)
def test_the_fix_moves_only_metrics_whose_block_ended_in_the_wrong_place(ticker: str) -> None:
    """A metric whose block the two boundings end at the SAME row prints the same line under both;
    only a mis-bounded metric may move. This is what licenses correcting a stored page in place."""
    b = _bundle(ticker)
    rows = b.sheet("estimates", "Revisions")
    listed = cs._metric_starts(rows, cs._METRICS)
    blocks = cs._block_starts(rows)
    moved_ok = {str(rows[bi][0]).strip() for i, bi in enumerate(listed)
                if (listed[i + 1] if i + 1 < len(listed) else len(rows))
                != next((s for s in blocks if s > bi), len(rows))}
    old, new = cs.horizon_read_as_assembled(b), cs.horizon_read(b).value
    assert old is not None and new is not None
    for line in _lines(old) ^ _lines(new):
        assert line.split(" FQ")[0] in moved_ok, (
            f"{ticker}: a correctly bounded metric moved: {line}")


# --- the transform that lands the correction on a committed page --------------------------------


def _amzn_mech(stored_value: str) -> dict[str, Any]:
    mech: dict[str, Any] = json.loads(
        (ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())["mechanical"]
    mech["catalyst_path"]["horizon_read"]["value"] = stored_value
    return mech


def test_a_page_built_from_this_export_is_corrected_and_nothing_else_moves() -> None:
    """The stored string is the pre-fix bounding's, from THIS export (rebuilt byte-for-byte), so the
    transform replaces it with the correct one and leaves every other field alone."""
    b = _bundle("AMZN")
    as_of = json.loads((ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())[
        "mechanical"]["catalyst_path"]["as_of"]["value"]
    old = cs.horizon_read_as_assembled(b, as_of=as_of)
    assert old is not None
    before = _amzn_mech(old)
    after = horizon_read_transform("AMZN")(before)
    assert after["catalyst_path"]["horizon_read"]["value"] == cs.horizon_read(b, as_of=as_of).value
    after["catalyst_path"]["horizon_read"]["value"] = old
    assert after == before, "the transform moved something other than horizon_read"


def test_a_page_this_export_cannot_rebuild_is_left_alone() -> None:
    """NEGATIVE: a stored string the pre-fix bounding does not reproduce came from another export or
    another renderer. Correcting it in place would mix vintages; it waits for a re-assembly."""
    _bundle("AMZN")
    stored = "EPS (GAAP) FQ3 2026: 1m 9↑/9↓  [from some other export]"
    after = horizon_read_transform("AMZN")(_amzn_mech(stored))
    assert after["catalyst_path"]["horizon_read"]["value"] == stored


# --- the count-sized refusal ---------------------------------------------------------------------


def test_a_count_the_prose_cites_may_not_vanish_from_the_page() -> None:
    """`moved_cited_claims` guards money and lets every count through. A count the prose cites that
    the refreshed layer no longer carries anywhere is refused — in either spelling the stored prose
    can hold, since a dict claim is serialised with JSON's ASCII escaping."""
    before = {"a": "EPS FY 2026: 3↑/0↓ last mo", "b": "Net Income: 3m 41↑/4↓"}
    after = {"a": "EPS FY 2026: 3↑/0↓ last mo", "b": "Net Income: 3m 24↑/8↓"}
    cites_vanished = {"synthesis": {"bull_points": [{"claim": "breadth 41↑/4↓ is strong"}]}}
    cites_kept = {"synthesis": {"bull_points": [{"claim": "breadth 3↑/0↓ last month"}]}}
    assert moved_cited_counts(before, after, cites_vanished) == [
        "revision count 41↑/4↓ (no longer on the page)"]
    assert moved_cited_counts(before, after, cites_kept) == []


def test_the_refresh_path_refuses_when_a_cited_count_vanishes(tmp_path: Path) -> None:
    """END TO END on AMZN's real prose, which cites the 3↑/0↓ last-month breadth. A refresh that
    makes that count vanish from every field is refused and writes nothing."""
    src = ROOT / "data" / "dossiers" / "AMZN"
    folder = tmp_path / "AMZN"
    folder.mkdir()
    for name in ("dossier.json", "dossier.md"):
        (folder / name).write_text((src / name).read_text())
    before = (folder / "dossier.json").read_text()
    assert "3\\u2191/0\\u2193" in before or "3↑/0↓" in before, "AMZN's prose no longer cites it"

    def erase(mech: dict[str, Any]) -> dict[str, Any]:
        text = json.dumps(mech, ensure_ascii=False).replace("3↑/0↓", "9↑/9↓")
        out: dict[str, Any] = json.loads(text)
        return out

    with pytest.raises(RefreshRefusedError, match="revision count 3↑/0↓"):
        refresh_dossier(folder / "dossier.json", transform=erase)
    assert (folder / "dossier.json").read_text() == before
