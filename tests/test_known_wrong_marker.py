"""THE KNOWN-WRONG MARKER MECHANISM — a sealed record marked as false without being written to.

WHAT THIS IS FOR. When a committed record could pass every existing check while resting on something
demonstrably wrong, a `known_wrong.json` sidecar states the falsehood beside it: the record stays
untouched, and the rendered view carries a banner, because a rendered view is not the record.
GAP vs ERROR is the whole point — a gap is a number we do not have; an error is a number we have and
can demonstrate is wrong, and a reader who files an error under "stale" underestimates it.

FUBO'S INSTANCE IS RETIRED (2026-08-13, operator ruling). The sidecar's own clearing condition was
*"a post-combination re-assembly exists. Until then this file stands and `dossier.json` stays
sealed."* One now exists, and four of its five items were verified CURED on the fresh artifact
before the file was removed:

  share-count           `shares_out` 30,200,000 from the CIQ bridge; 30.2M x $9.70 = $292.9M against
                        a stated cap of $293.0M — 0.03% apart. This was the 11.1x error.
  caveat-text-pre-fix   the P/E caveat asserting a normalized/adjusted denominator is gone from
                        `caveats` entirely.
  agreement-bug         `13.1x rest on` appears nowhere in the page body. (Checked with the banner's
                        own blockquote STRIPPED — a first pass matched the marker quoting itself,
                        which is the seal's text, not the page's.)
  pre-combination-entity  Hulu, Newco, Class B, reverse split and noncontrolling interest are all
                        present; the page describes the post-combination issuer.

The fifth, `g3-never-valued`, was a READING CAUTION ("FUBO's admission is not a valuation judgment")
rather than a known-false figure, and retired with the rest.

THE MECHANISM STAYS PINNED. The tests below no longer name FUBO: they exercise the sidecar on a
temporary marker, so the machinery is proven for the NEXT record that needs sealing rather than
rotting the moment one instance clears. That distinction is why this module was rewritten instead of
deleted.
"""
from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSSIERS = ROOT / "data" / "dossiers"


def test_no_record_is_sealed_without_this_module_being_updated() -> None:
    """THE ROSTER, so a seal cannot appear or vanish silently. A new sidecar is a deliberate act and
    should be recorded here with its evidence, exactly as FUBO's was; a sidecar that shows up
    unannounced is a page asserting its own figures are false with nobody having said why."""
    sealed = sorted(p.parent.name for p in DOSSIERS.glob("*/known_wrong.json"))
    assert sealed == [], (
        f"{sealed} carry a known-wrong sidecar. If that is intended, document the items and their "
        f"evidence in this module's docstring; if it is not, the file is stray and the page is "
        f"telling readers its numbers are false")


def test_a_name_without_a_marker_renders_unchanged() -> None:
    """The banner is per-name and silent by default — every unmarked dossier must be untouched."""
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    for ticker in ("SMPL", "AORT", "FUBO"):
        path = DOSSIERS / ticker / "dossier.json"
        if not path.is_file():
            continue
        md = render_markdown(Dossier.model_validate_json(path.read_text()))
        assert "KNOWN-WRONG" not in md, f"{ticker} rendered a marker it has no file for"


def test_a_marker_reaches_the_rendered_page_above_the_numbers(tmp_path: pathlib.Path) -> None:
    """THE POSITIVE HALF, on a TEMPORARY marker rather than a live name. A banner that renders below
    the figures it disowns is a banner a reader meets too late, so it must lead the page.

    Written against a real committed record with a sidecar dropped beside it and removed after, so
    the mechanism is exercised end to end without any name having to stay broken to prove it.
    """
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    host = next((d for d in sorted(DOSSIERS.iterdir()) if (d / "dossier.json").is_file()), None)
    if host is None:
        pytest.skip("no committed dossier to host a temporary marker")
    marker = host / "known_wrong.json"
    assert not marker.exists(), f"{host.name} is already sealed — pick an unsealed host"

    marker.write_text(json.dumps({
        "ticker": host.name, "kind": "known_wrong", "recorded": "2026-08-13",
        "items": [{"id": "t", "claim": "A test claim.", "known_false": "why it is false"}],
    }))
    try:
        md = render_markdown(Dossier.model_validate_json((host / "dossier.json").read_text()))
        assert "KNOWN-WRONG" in md, "the marker did not reach the rendered page"
        banner = md.index("KNOWN-WRONG")
        # ABOVE THE NUMBERS: the first figure-bearing line must come after the warning.
        first_number = next((md.index(ln) for ln in md.splitlines()
                             if "$" in ln and ln.strip().startswith(("-", "|"))), len(md))
        assert banner < first_number, "the banner renders below the figures it disowns"
    finally:
        marker.unlink()


def test_a_broken_marker_fails_loud_instead_of_vanishing(tmp_path: pathlib.Path) -> None:
    """REVIEW FINDING (#308), and the reason this module survives FUBO. The first cut swallowed
    OSError/ValueError and returned no lines, so a corrupt or empty marker made the banner DISAPPEAR
    while the file sat there looking like the page was marked. The page then renders CLEAN and looks
    valid — the exact state the seal exists to prevent, reached through the mechanism built to
    prevent it.

    ABSENT and BROKEN are different states. Absent is silence and correct. Broken is a warning that
    failed, and rendering past it is the harm."""
    from vinci.dossier.render import _known_wrong_lines

    host = next((d for d in sorted(DOSSIERS.iterdir()) if (d / "dossier.json").is_file()), None)
    if host is None:
        pytest.skip("no committed dossier to host a temporary marker")
    marker = host / "known_wrong.json"
    assert not marker.exists(), f"{host.name} is already sealed — pick an unsealed host"

    try:
        for bad, _why in (("{ not json", "malformed"),
                          (json.dumps({"ticker": host.name, "items": []}), "empty items"),
                          (json.dumps({"ticker": host.name}), "no items key")):
            marker.write_text(bad)
            with pytest.raises(ValueError, match="known-wrong|names no items|cannot be read"):
                _known_wrong_lines(host.name)
    finally:
        marker.unlink()

    # ABSENT still renders nothing — the fix must not turn silence into an error for every name.
    assert _known_wrong_lines(host.name) == []
