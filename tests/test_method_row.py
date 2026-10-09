"""The screening-context Method row names WHOSE bit `applicable` is (2026-10-09).

THE DEFECT. The row printed the anchor's `applicable` beside whatever recipe the page is TAGGED.
That bit is R1's — whether R1's arithmetic, the rows beneath it, can anchor the name — so after the
operator's R4 re-tags UBER's page read "R4_forward_ev_ebit | NOT applicable": a verdict on R4 the
bit never made. AORT read "R2_NEEDED | applicable", the same coupling the other way. It is the
render twin of the gate coupling STATE row 10 records (#670).

THE FIX. Beside an R1 tag the plain word stays, so every R1 page is byte-identical. Beside any
other tag the note says "R1 screen: applicable" / "R1 screen: NOT applicable". Preview approved
2026-10-09.

Pinned on the COMMITTED pages, in both twins (the md renderer and `dossier.js`), as INVARIANTS
against each page's own anchor — never a pinned word for one name, since a page's bit can move.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
from typing import Any

import pytest

from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
PAGES = sorted(p.parent.name for p in DOSS.glob("*/dossier.json"))


def _expected_note(anchor: dict[str, Any]) -> str:
    fit = "applicable" if anchor.get("applicable") else "NOT applicable"
    return fit if str(anchor.get("recipe_hint") or "").startswith("R1") else f"R1 screen: {fit}"


def _md_note(doc: dict[str, Any]) -> str:
    md = render_markdown(Dossier.model_validate(doc))
    row = next(ln for ln in md.splitlines() if ln.startswith("| Method |"))
    return [c.strip() for c in row.strip("|").split("|")][2]


def _web_notes(docs: dict[str, dict[str, Any]], tmp: pathlib.Path) -> dict[str, str]:
    src = tmp / "pages.json"
    src.write_text(json.dumps(docs))
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { renderDossier } = await import(pathToFileURL(process.argv[1]).href);
const out = {};
for (const [t, d] of Object.entries(JSON.parse(readFileSync(process.argv[2])))) {
  const re = /<tr><td>Method<\/td><td[^>]*>.*?<\/td><td class="muted">(.*?)<\/td><\/tr>/;
  const m = renderDossier(d, null).match(re);
  out[t] = m ? m[1] : null;
}
process.stdout.write(JSON.stringify(out));
"""
    out = subprocess.run(
        ["node", "--input-type=module", "-e", driver,
         str(ROOT / "frontend" / "views" / "shared" / "dossier.js"), str(src)],
        capture_output=True, text=True, check=True)
    notes: dict[str, str] = json.loads(out.stdout)
    return notes


def _page(t: str) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads((DOSS / t / "dossier.json").read_text())
    return doc


def test_every_committed_page_names_whose_bit_it_is_in_markdown() -> None:
    seen = {"R1": 0, "other": 0}
    for t in PAGES:
        doc = _page(t)
        if not doc.get("anchor"):
            continue
        assert _md_note(doc) == _expected_note(doc["anchor"]), t
        seen["R1" if str(doc["anchor"]["recipe_hint"]).startswith("R1") else "other"] += 1
    assert seen["R1"] >= 10 and seen["other"] >= 5, f"too few pages of each kind checked: {seen}"


@pytest.mark.skipif(not shutil.which("node"), reason="node unavailable")
def test_the_web_twin_says_the_same_on_every_committed_page(tmp_path: pathlib.Path) -> None:
    """md/web PARITY, page by page — the two twins print one note."""
    docs = {t: _page(t) for t in PAGES if _page(t).get("anchor")}
    web = _web_notes(docs, tmp_path)
    for t, doc in docs.items():
        assert web[t] == _expected_note(doc["anchor"]) == _md_note(doc), t


@pytest.mark.skipif(not shutil.which("node"), reason="node unavailable")
def test_a_non_r1_tag_never_carries_the_bare_verdict(tmp_path: pathlib.Path) -> None:
    """NEGATIVE PIN, CONSTRUCTED both ways on one real page: the R4 tag that prompted this, on a
    page whose R1 declines and on one whose R1 computes. Neither twin may print a bare
    "applicable"/"NOT applicable" beside it."""
    docs = {}
    for applicable in (False, True):
        doc = _page("UBER")
        doc["anchor"].update(recipe_hint="R4_forward_ev_ebit", applicable=applicable)
        docs[f"R4-{applicable}"] = doc
    web = _web_notes(docs, tmp_path)
    for key, doc in docs.items():
        want = ("R1 screen: applicable" if doc["anchor"]["applicable"]
                else "R1 screen: NOT applicable")
        assert _md_note(doc) == want and web[key] == want, key


def test_an_r1_tag_keeps_the_plain_word() -> None:
    """POSITIVE PIN for byte-identity: an R1-tagged page prints exactly what it printed before —
    the plain word, no prefix."""
    r1 = [t for t in PAGES
          if str((_page(t).get("anchor") or {}).get("recipe_hint", "")).startswith("R1")]
    assert r1
    for t in r1:
        note = _md_note(_page(t))
        assert note in ("applicable", "NOT applicable") and not re.match(r"R1 screen", note), t
