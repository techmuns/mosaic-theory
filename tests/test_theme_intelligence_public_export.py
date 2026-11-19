"""THE REGISTRY EXPORT IS PUBLIC (operator ruling 2026-11-19, "Fix source + scrub tip"): the
`theme-intelligence-state` branch of this public repository is the registry of record, so only
titles, figures and SHORT quotes may leave the machine.

The incident, at state a74c4e30:
- 31,207 distinct characters of report body misfiled as section headings: the PDF reader merged a
  paragraph set in large type into ONE heading, of up to 1,204 characters;
- a 2,042-character and five 911-character claim quotes;
- 77 absolute local paths, in `evidence_location`, a run's `output_dir` and its warnings.

Pinned here:
- the reader reads large type running past a heading's length as a paragraph;
- an export carries no source text over its cap, no misfiled section and no local path;
- a claim's shortened quote keeps its figure;
- the committed fixtures pass the same guard.

HYPOTHETICAL articles and synthetic text; no network, no model call.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.display import DESK_QUOTE_MAX_CHARS
from vinci.theme_intelligence.documents import HEADING_MAX_CHARS, Declared, read_document
from vinci.theme_intelligence.public import claim_quote
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import RunStatus

ROOT = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 11, 19)
_ABS = re.compile(r"(?:^|(?<=[\s'\"(\[=])|(?<=file://))(?:/[\w.-]+/[^\s'\"()\[\]<>,;]|[A-Za-z]:\\)")


def violations(obj: Any, where: str) -> list[str]:
    """Every text field an export may not carry: a source's words (`quote`, `sentence`, a claims
    row's `statement`) over `DESK_QUOTE_MAX_CHARS`, a `section` over `HEADING_MAX_CHARS`, an
    absolute local path. JSON held as text (a model's raw answer) is read as JSON."""
    out: list[str] = []

    def walk(o: Any, path: str) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str):
                    limit = (DESK_QUOTE_MAX_CHARS if k in ("quote", "sentence")
                             or (k == "statement" and where.startswith("claims"))
                             else HEADING_MAX_CHARS if k == "section" else None)
                    if limit is not None and len(v) > limit:
                        out.append(f"{path}.{k}: {len(v)} > {limit}")
                walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for v in o:
                walk(v, f"{path}[]")
        elif isinstance(o, str):
            if o[:1] in "[{":
                try:
                    walk(json.loads(o), path)
                    return
                except ValueError:
                    pass
            if _ABS.search(o):
                out.append(f"{path}: a local path")

    walk(obj, where)
    return out


def export_violations(export_dir: Path) -> list[str]:
    return [v for f in sorted(export_dir.glob("*.jsonl"))
            for line in f.read_text(encoding="utf-8").splitlines()
            for v in violations(json.loads(line), f.stem)]


# --- the reader: large type running past a heading's length is a paragraph ---------------------

def _pdf(lines: list[tuple[float, float, str]]) -> bytes:
    """A one-page PDF: each (font size, baseline y, text) a line of Helvetica at x = 72."""
    body = "".join(f"BT /F1 {s} Tf 72 {y} Td ({t}) Tj ET\n" for s, y, t in lines)
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R "
            "/Resources << /Font << /F1 4 0 R >> >> >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            f"<< /Length {len(body)} >>\nstream\n{body}endstream"]
    out, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += (f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n"
            + "".join(f"{o:010d} 00000 n \n" for o in offsets)
            + f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
            ).encode("latin-1")
    return out


BODY = "Synthetic body text describes the grid build in plain words for the reader here"
BIG = ["Synthetic large type opens this report with a long summary of the view",
       "that runs over several lines in a bigger font than the body text below",
       "and carries the argument the way a lead paragraph does in a research note",
       "before the sections begin, which no heading of a report ever does at all"]


def _large_type_pdf(tmp_path: Path, big: list[str]) -> Path:
    lines = [(18.0, 720 - 22 * i, t) for i, t in enumerate(big)]  # wrapped: the gap < its size
    y0 = 720 - 22 * len(big) - 30
    lines += [(10.0, y0 - 13 * i, f"{BODY} {i}.") for i in range(12)]
    p = tmp_path / "large_type.pdf"
    p.write_bytes(_pdf(lines))
    return p


def test_large_type_running_past_a_headings_length_is_a_paragraph(tmp_path: Path) -> None:
    doc = read_document(_large_type_pdf(tmp_path, BIG), Declared(source_id="gs_research")).doc
    assert len(" ".join(BIG)) > HEADING_MAX_CHARS  # the fixture's shape
    # main: ONE "heading" of every large line, the section of every body block after it
    assert all(len(b.section or "") <= HEADING_MAX_CHARS for b in doc.blocks)
    assert not [b for b in doc.blocks if b.kind == "heading" and len(b.text) > HEADING_MAX_CHARS]
    big = [b for b in doc.blocks if b.kind == "paragraph" and BIG[0][:30] in b.text]
    assert len(big) == 1 and BIG[-1][-20:] in big[0].text  # its lines are ONE paragraph


def test_a_heading_wrapped_onto_two_lines_is_still_one_heading(tmp_path: Path) -> None:
    """NEGATIVE: a real heading set on two lines stays one heading, the section after it."""
    two = ["Synthetic grid outlook", "for the coming year"]
    doc = read_document(_large_type_pdf(tmp_path, two), Declared(source_id="gs_research")).doc
    heads = [b for b in doc.blocks if b.kind == "heading"]
    assert [h.text for h in heads] == [" ".join(two)]
    assert {b.section for b in doc.blocks if b.kind == "paragraph"} == {" ".join(two)}


# --- the export ----------------------------------------------------------------------------------

def _exactly(text: str, n: int) -> str:
    while len(text) < n:
        text = f"{text} {text}"
    out = text[:n - 1]
    return (out[:-1] + "s" if out.endswith(" ") else out) + "."


#: a forecast table read as one block; its claim's figure ("net 95") lies past the cap
TABLE = _exactly("Synthetic supply forecasts, calendar year 2027, net issuance by country, "
                 "billions: " + "; ".join(f"Country {i:02d} gross {100 + 7 * i} net {20 + 3 * i}"
                                          for i in range(31)), 913)
#: body text misfiled as a heading (the incident: up to 1,204 characters)
MISFILED = _exactly("Synthetic large type carries the argument of the note across many lines", 600)


def _exported(tmp_path: Path) -> tuple[Path, Counter[str]]:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("public-export", "Test Publisher", date(2026, 11, 12), [("paragraph", TABLE)])
    doc = art.doc()
    doc = replace(doc, blocks=tuple(b.model_copy(update={"section": MISFILED})
                                    for b in doc.blocks))
    ingest(pipe, doc, extraction(
        [claim("c1", "b001", TABLE, "Country 25 net supply", metric="net issuance", value=95,
               value_text="net 95", unit="bn", period="2027", scope="Country 25")],
        [hyp("h1", "Synthetic supply wave", node="ai_infrastructure.power",
             mechanism="supply_constraint", supporting=["c1"])]), as_of=AS_OF,
        publisher=art.publisher)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    write_run_outputs(pipe.store, run.run_id, tmp_path / "out")  # records an absolute output_dir
    cut: Counter[str] = Counter()
    pipe.store.export_jsonl(tmp_path / "export", cut=cut)
    return tmp_path / "export", cut


def test_an_export_carries_no_source_text_over_its_cap_and_no_local_path(tmp_path: Path) -> None:
    export, cut = _exported(tmp_path)
    assert TABLE.index("net 95") > DESK_QUOTE_MAX_CHARS  # the fixture's shape
    # main: the 913-character quote, the 600-character section and the absolute output_dir
    assert export_violations(export) == []
    assert cut["claims.quote"] == 1 and cut["article_versions.blocks[].section"] >= 1
    assert any("local path" in k for k in cut)
    [row] = [json.loads(json.loads(x)["payload"]) for x in
             (export / "claims.jsonl").read_text().splitlines()]
    assert "net 95" in row["quote"] and len(row["quote"]) <= DESK_QUOTE_MAX_CHARS  # figure kept


def test_a_claim_quote_keeps_its_figure_and_a_short_one_is_untouched() -> None:
    q = claim_quote(TABLE, "net 95")
    assert "net 95" in q and len(q) <= DESK_QUOTE_MAX_CHARS and q.startswith("…")
    assert q.strip("…") in TABLE  # verbatim between its cuts
    head = claim_quote(TABLE, "net 20")  # the figure is in the head: the head is kept
    assert head.startswith("Synthetic supply") and head.endswith("…")
    assert claim_quote("A short quote of 9%.", "9%") == "A short quote of 9%."  # NEGATIVE


def test_the_export_round_trips_and_a_row_it_leaves_alone_is_written_as_stored(
        tmp_path: Path) -> None:
    from vinci.theme_intelligence.store import Store

    export, _cut = _exported(tmp_path)
    copy = Store.import_jsonl(export, tmp_path / "imported.db")
    assert copy.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 1
    # NEGATIVE: a table no rule touches is byte-identical to its stored payloads
    raw = {r[0]: r[1] for r in copy.conn.execute("SELECT thesis_id, payload FROM theses")}
    exported = {json.loads(x)["thesis_id"]: json.loads(x)["payload"]
                for x in (export / "theses.jsonl").read_text().splitlines()}
    assert raw == exported


def test_a_path_under_any_root_is_scrubbed_and_a_url_or_ratio_is_not() -> None:
    """Codex on #1143 (P2): the path rule named its roots, so a data folder under /workspace,
    /mnt, /srv or /data reached the public branch whole."""
    from vinci.theme_intelligence.public import public_path

    for p in ("/workspace/run/ti/runs/R-1", "/mnt/disk/x/y.txt", "/srv/data/z.json",
              "/data/ti/documents/a.pdf", '"/opt/hostedtoolcache/py/x.py'):
        lead = p[:len(p) - len(p.lstrip('"'))]  # a quote before the path stays
        assert public_path(f"wrote {p} today", Path("/elsewhere/ti")) == (
            f"wrote {lead}⟨local path⟩/{Path(p).name} today")
        assert violations({"output_dir": p}, "runs") == ["runs.output_dir: a local path"]
    # NEGATIVE: a URL's path, a ratio, a word pair and a lone root are not local paths
    for text in ("https://example.test/hypothetical/a/b", "AI/ML demand", "2026/27 and 3/4",
                 "rose 5% y/y", "a /tmp folder", "$/kW/month",
                 "site.test/en/press-detail/-/detail/x"):
        assert public_path(text, Path("/elsewhere/ti")) == text
        assert violations({"note": text}, "runs") == []


def test_the_guard_reads_every_rule_and_the_committed_fixtures_pass_it() -> None:
    assert violations({"quote": "x" * 401}, "claims") == ["claims.quote: 401 > 400"]
    assert violations({"quote": "x" * 400, "section": "s" * 150}, "claims") == []  # NEGATIVE
    assert violations({"blocks": [{"section": "s" * 151}]}, "article_versions") == [
        "article_versions.blocks[].section: 151 > 150"]
    assert violations({"output_dir": "/Users/someone/x"}, "runs") == [
        "runs.output_dir: a local path"]
    assert violations({"hypotheses": json.dumps([{"quote": "q" * 401}])}, "extractions") == [
        "extractions.hypotheses[].quote: 401 > 400"]  # a raw answer held as text
    assert violations({"statement": "m" * 600}, "thesis_versions") == []  # model text: no cap
    fixtures = ROOT / "tests" / "fixtures" / "theme_intelligence"
    found = [v for p in sorted(fixtures.rglob("*.json*"))
             for line in (p.read_text(encoding="utf-8").splitlines() if p.suffix == ".jsonl"
                          else [p.read_text(encoding="utf-8")])
             for v in violations(json.loads(line), p.name)]
    assert not found, f"{len(found)} (showing {min(10, len(found))} of {len(found)}): {found[:10]}"

