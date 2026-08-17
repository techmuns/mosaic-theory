"""26a — THE EXTRACTION STAMP. Two dossiers of different vintages must be tellable apart.

THE DEFECT (STATE queue item 26a, from the #238 blast-radius diagnosis). After #238 the fleet held
two vintages with nothing distinguishing them: pre-guard financial summaries lack the unusual-items
rows, post-guard summaries carry them, and both date alike. Cross-name comparison in the
verdict-pending cohort silently assumed a common table, so nothing could be re-assembled and no new
name could be underwritten.

THE RED, exactly as the operator specified it: **two dossiers built under different extraction
versions are distinguishable BY THE STAMP ALONE.** The headline test below drives it through the
case that killed the two DERIVED designs — FUBO, whose extraction output is BYTE-IDENTICAL across
#238 because it carries no unusual items. Any identifier computed FROM the output collapses those
two vintages onto one value; a declared version does not. That is the previously-broken case, and
it is the one asserted first.

TEST-LAYER NOTE. The md assertions run on SYNTHETIC dossiers (frozen fixtures), because they are
value-level pins on an exact stamp. The e2e web assertion runs on a COMMITTED artifact and asserts
only phrasing-independent invariants — the stamp present in both tiers, and the two tiers agreeing.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from tests.test_dossier import _minimal_mech
from vinci.dossier import render as dr
from vinci.dossier import schemas as ds
from vinci.dossier.extraction_version import (
    EXTRACTION_VERSION,
    EXTRACTION_VERSION_NAMES,
    EXTRACTION_VERSIONS,
    UNSTAMPED,
    stamp_detail,
    stamp_label,
)

ROOT = Path(__file__).resolve().parents[1]


def _doss(version: str | None) -> ds.Dossier:
    """A dossier whose CONTENT is fixed — only the extraction version varies. This is the FUBO
    shape: two vintages whose extracted output is identical, which is precisely where a derived
    identifier fails and a declared one must not."""
    return ds.Dossier(
        ticker="FUBO", name="fuboTV Inc.", cik="0", reference_date=datetime(2026, 6, 1).date(),
        rank=1, mechanical=_minimal_mech(), synthesis=None, caveats=[], qa_flags=[],
        llm_model=None, assembled_at=datetime(2026, 6, 1, 12, 0), extraction_version=version)


def test_two_vintages_are_distinguishable_by_the_stamp_alone() -> None:
    """THE RED. Identical extracted content, different extractor → the documents must differ, and
    the difference must BE the stamp. Drives the FUBO case: a content-derived identifier hashes
    `6d170d2fe3` on both sides of #238 and reports "same vintage", which is the exact wrong answer
    this item exists to prevent."""
    old, new = dr.render_markdown(_doss("2026-07-01.0")), dr.render_markdown(_doss("2026-07-28.1"))

    assert old != new, (
        "two dossiers of DIFFERENT extraction vintages rendered identically — this is the #238 "
        "state the stamp exists to end, and it is the FUBO false-negative in full: identical "
        "extracted content, so anything derived FROM the content cannot tell them apart")

    # ...and the difference is the stamp, not incidental. Every differing line names a version.
    o_lines, n_lines = old.splitlines(), new.splitlines()
    assert len(o_lines) == len(n_lines), (
        "the two vintages rendered a DIFFERENT NUMBER OF LINES — the fixture holds content fixed, "
        "so the stamp has changed the document's shape rather than one field of it")
    differing = [a for a, b in zip(o_lines, n_lines, strict=True) if a != b]
    assert differing, "same line count and no differing line, yet the documents differ — unexpected"
    assert all("2026-07-01.0" in ln or "2026-07-28.1" in ln for ln in differing), (
        f"lines differ for reasons OTHER than the stamp: {differing}. The fixture holds content "
        "fixed, so any other difference means the render is not deterministic over it")

    # The legacy boundary is the same question: unstamped vs stamped must not read alike either.
    assert dr.render_markdown(_doss(None)) != new
    assert UNSTAMPED in dr.render_markdown(_doss(None))


def test_the_stamp_is_in_the_main_body_not_only_the_audit_tier() -> None:
    """17b's failure, guarded. A stamp a reader never meets cannot stop them comparing two
    vintages — 'the record complete, the harm intact'. So the identifier rides the DOCUMENT DATE in
    the header, above the Brief, not only in Record & reproduce at the end."""
    md = dr.render_markdown(_doss(EXTRACTION_VERSION))
    head = md.split("# Brief")[0]
    assert EXTRACTION_VERSION in head, (
        "the extraction stamp is absent from the header block — it must sit beside the document "
        "date in the MAIN BODY, not be confined to the audit tier")
    assert re.search(rf"_.*·\s*extraction {re.escape(EXTRACTION_VERSION)}_", head), (
        "the stamp is present in the header block but not on the document-date line")
    # and the audit tier carries the LONG form: the version plus what it names
    assert f"**Extraction:** {EXTRACTION_VERSION} — {EXTRACTION_VERSION_NAMES}" in md


def test_a_dossier_predating_the_stamp_round_trips_and_says_it_is_unstamped() -> None:
    """Legacy JSON must still load (every field is optional-safe) AND must not render as though it
    were merely stamp-free. 'Vintage unknown' and 'no divergence here' are different states."""
    payload = json.loads(_doss(EXTRACTION_VERSION).model_dump_json())
    del payload["extraction_version"]                      # a dossier committed before 26a
    legacy = ds.Dossier.model_validate(payload)
    assert legacy.extraction_version is None

    md = dr.render_markdown(legacy)
    assert f"· extraction {UNSTAMPED}_" in md, "an absent stamp must render VISIBLY, never silently"
    assert "vintage unknown" in md, "the audit tier must say WHY it is unstamped"


def test_an_unrecognised_version_is_never_described_with_this_codes_changes() -> None:
    """A dossier built by other code carries a version this code does not declare. Describing it
    with the CURRENT version's changes would attribute this extractor's behaviour to an artifact it
    did not build — a fabricated provenance, which is the one thing the repo never does."""
    detail = stamp_detail("1999-01-01.0")
    assert "1999-01-01.0" in detail and "different extractor" in detail
    assert EXTRACTION_VERSION_NAMES not in detail
    assert stamp_label("1999-01-01.0") == "1999-01-01.0"   # still shown; only the gloss is withheld


def test_the_changelog_forces_a_bump_to_say_what_it_names() -> None:
    """The operator's spec point: *a version string that doesn't say what it's anchored to is the
    same class as every other identifier we've corrected this week.* So the version is not a
    free-standing constant — it is the last row of a table whose other column states the change.
    Bumping without naming the state is then unrepresentable, and this is the check that keeps it
    so. Structural, never a value pin: a legitimate bump must not redden the suite."""
    assert EXTRACTION_VERSIONS, "the changelog is empty — nothing declares the current vintage"
    versions = [v for v, _ in EXTRACTION_VERSIONS]
    assert len(versions) == len(set(versions)), f"duplicate extraction versions: {versions}"
    for ver, names in EXTRACTION_VERSIONS:
        assert ver.strip() and names.strip(), f"version {ver!r} declares no state that it names"
        assert len(names) > 20, (
            f"version {ver!r} names its state in {len(names)} chars — too short to tell a reader "
            "what changed, which is the whole reason the pairing exists")
    assert EXTRACTION_VERSIONS[-1] == (EXTRACTION_VERSION, EXTRACTION_VERSION_NAMES), (
        "the exported current version is not the last changelog row — appending a vintage must "
        "move the stamp, or the table and the stamp disagree about what is current")


def test_both_twins_agree_on_every_stamp_edge_case_e2e() -> None:
    """BEHAVIOURAL twin pin — the machine check for a defect review caught in this PR.

    The changelog pin in test_parity_pins binds the two TABLES. It does not bind the two
    FUNCTIONS, and the untreated helpers diverged on the empty string in BOTH directions:
    python's `stamp_detail("")` said "not a version this code declares" while `stamp_label("")`
    said "unstamped" — self-contradictory on one document — and the JS twin said "unstamped" for
    both, so the surfaces disagreed with each other too. Records are hand-edited, so "" is
    reachable. A table equal on both sides is the only thing that keeps four call sites honest.

    Drives the REAL render path on each side rather than exported helpers, so it pins what a reader
    actually meets."""
    if not shutil.which("node"):
        pytest.skip("node not available")
    cases = ["2026-07-28.1", "1999-01-01.0", "", "   ", None]

    dj = (ROOT / "frontend" / "views" / "shared" / "dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
const {{ renderDossier }} = await import("{dj}");
const bare = {{ ticker: "X", name: "X Co", cik: "0", reference_date: "2026-06-01",
  assembled_at: "2026-06-01T12:00:00", mechanical: {{}}, synthesis: null }};
const strip = (s) => s.replace(/<[^>]*>/g, "").replace(/&amp;/g, "&").replace(/&#39;/g, "'")
  .replace(/&quot;/g, '"').replace(/&lt;/g, "<").replace(/&gt;/g, ">").trim();
const out = [];
for (const v of {json.dumps(cases)}) {{
  const html = renderDossier(v === null ? bare : {{ ...bare, extraction_version: v }}, null);
  const meta = /<div class="ds-meta">([\\s\\S]*?)<\\/div>/.exec(html);
  const det = /"fact-label">Extraction<\\/div>\\s*<div class="fact-val">([\\s\\S]*?)<\\/div>/
    .exec(html);
  // the header line is "<date> · extraction <label>" — take what follows the marker
  const header = meta ? strip(meta[1]) : null;
  out.push({{ label: header ? header.slice(header.indexOf("· extraction ") + 13) : null,
             detail: det ? strip(det[1]) : null }});
}}
console.log(JSON.stringify(out));
"""
    got = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver],
                                    capture_output=True, text=True, check=True, cwd=ROOT).stdout)
    mismatched = [
        f"{v!r}: py=({stamp_label(v)!r}, {stamp_detail(v)!r}) "
        f"js=({js['label']!r}, {js['detail']!r})"
        for v, js in zip(cases, got, strict=True)
        if js["label"] != stamp_label(v) or js["detail"] != stamp_detail(v)
    ]
    assert not mismatched, (
        "the markdown and web twins render the SAME extraction_version differently — a "
        "disagreement about provenance, which is worse than either omitting it:\n"
        + "\n".join(mismatched))

    # ...and no input may produce a BLANK stamp: an invisible label is the silent absence the whole
    # item exists to end, so whitespace-only must normalise to the unstamped wording, not to itself.
    for v, js in zip(cases, got, strict=True):
        assert js["label"].strip(), f"input {v!r} rendered an empty stamp on the web header"
        assert stamp_label(v).strip(), f"input {v!r} rendered an empty stamp on the md header"


def test_web_twin_renders_the_stamp_in_both_tiers_e2e() -> None:
    """The twin surface, on a COMMITTED artifact. Phrasing-independent per the TEST-LAYER rule: the
    stamp reaches the header AND Record & reproduce, and a record with no stamp says 'unstamped'
    rather than rendering an empty slot that reads as agreement."""
    if not shutil.which("node"):
        pytest.skip("node not available")
    dj = (ROOT / "frontend" / "views" / "shared" / "dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const bare = {{ ticker: "X", name: "X Co", cik: "0", reference_date: "2026-06-01",
  assembled_at: "2026-06-01T12:00:00", mechanical: {{}}, synthesis: null }};
const stamped = renderDossier({{ ...bare, extraction_version: "2026-07-28.1" }}, null);
const other   = renderDossier({{ ...bare, extraction_version: "2026-07-01.0" }}, null);
const legacy  = renderDossier(bare, null);
// Scope the header check to the ds-meta ELEMENT. Slicing to end-of-document instead would be
// satisfied by the Record & reproduce stamp far below — the assertion would pass with the header
// stamp deleted, which is the failure it exists to catch.
const meta = /<div class="ds-meta">([\\s\\S]*?)<\\/div>/.exec(stamped);
console.log(JSON.stringify({{
  headerHasStamp: !!meta && meta[1].indexOf("2026-07-28.1") >= 0,
  auditHasStamp: stamped.indexOf(">Extraction</div>") >= 0,
  vintagesDiffer: stamped !== other,
  legacyIsVisiblyUnstamped: legacy.indexOf("unstamped") >= 0,
}}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    r = json.loads(out.stdout)
    assert r["headerHasStamp"], "the web header must carry the stamp beside the document date"
    assert r["auditHasStamp"], "Record & reproduce must carry the Extraction row"
    assert r["vintagesDiffer"], (
        "two vintages rendered identically on the web twin — the md surface distinguishes them and "
        "the web does not, which is the #227 asymmetry on the stamp itself")
    assert r["legacyIsVisiblyUnstamped"], "an unstamped record must SAY so on the web twin too"


def test_every_committed_stamp_names_a_vintage_this_code_declares() -> None:
    """A committed stamp must resolve to a REAL row — the check the 2026-08-16.1 amendment owes.

    `EXTRACTION_VERSIONS` is append-only precisely so a row an artifact references is never
    rewritten under it. The follow-up to #461 AMENDED the `2026-08-16.1` row, because its
    `Close [ISO]` clause described behaviour #460 reverted. That was legitimate ONLY because no
    artifact carried that version — measured 0 of 14.
    IS referenced and the suite names the dossiers left pointing at nothing.

    IT ALSO CATCHES A TYPO'D BUMP. `stamp_detail` degrades gracefully at RENDER time ("not a
    version this code declares"), right for the reader but it means an invented stamp ships
    silently, visible only to whoever opens that one page. This fails at COMMIT time instead.

    WHAT IT DELIBERATELY DOES NOT CATCH, recorded as accepted risk in STATE rather than left
    implied: a MIXED-vintage dossier. `own-history-refresh` re-extracts four valuation fields with
    current code and never restamps, so the 13 names touched by #460's pass carry post-#459
    valuation output under a `2026-07-28.1` stamp. NEITHER stamp is honest there — the new one would
    claim the whole document was re-extracted, which is the false "these two are comparable" this
    module exists to prevent, and the old one under-claims by four fields. Detecting it needs the
    artifact to record that a refresh ran: a schema change, and its own PR."""
    root = Path(__file__).resolve().parents[1]
    declared = {v for v, _ in EXTRACTION_VERSIONS}
    orphaned, scanned = [], 0
    for path in sorted((root / "data" / "dossiers").glob("*/dossier.json")):
        stamp = (json.loads(path.read_text()).get("extraction_version") or "").strip()
        if not stamp:
            continue  # assembled before 26a — `stamp_label` renders "unstamped", which is honest
        scanned += 1
        if stamp not in declared:
            orphaned.append(f"{path.parent.name}={stamp}")
    assert scanned, "no committed dossier carries a stamp — the guard ran vacuously"
    assert not orphaned, (
        f"committed dossier(s) stamp a vintage this code does not declare: {orphaned}. Either a "
        f"row "
        f"was amended or deleted while an artifact still referenced it — which is what append-only "
        f"forbids — or a bump was typo'd. Declared: {sorted(declared)}.")
