"""NO LOCAL PATH LEAVES THE MACHINE, and the PDF reader keeps a headline that opens large type.

The operator, 2026-11-20: "No rewrite, fix paths ahead". The registry of record is the public
`theme-intelligence-state` branch. At state a74c4e30 it held 77 path fields: `evidence_location`
17, a run's `output_dir` 57, the tracebacks in a run's `warnings` 3 (#1143 review, findings 6 and
10).

Pinned here:
- **the guard** refuses every home-directory and username shape the review found, and passes a
  figure, a URL and a relative name;
- **a traceback** is named before its cut, so no cut point leaves part of a home directory;
- **a new run and version** store their paths relative to the data directory, and a re-render
  without `--out` writes there, never in the current directory;
- **an export** writes rows stored before this change relative, and every other row as stored;
- **`export-state` and `state push`** refuse a path the rewrite does not know;
- **the reader** reads large type past a heading's length as a paragraph, keeps a headline that
  opens it (finding 8) and does not merge type of another size.

HYPOTHETICAL articles and synthetic text; no network, no model call.
"""

from __future__ import annotations

import json
import subprocess
import traceback
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import Hypo, claim, extraction, fetched, hyp, make_pipeline
from vinci.theme_intelligence import localpaths, state
from vinci.theme_intelligence.__main__ import main as cli
from vinci.theme_intelligence.documents import HEADING_MAX_CHARS, Declared, read_document
from vinci.theme_intelligence.localpaths import (
    TRACEBACK_CHARS,
    export_findings,
    path_findings,
    run_dir,
    traceback_text,
)
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import IssueSeverity, RunStatus, VerificationIssue
from vinci.theme_intelligence.store import Store

AS_OF = date(2026, 11, 20)

# --- the guard ------------------------------------------------------------------------------------

#: every shape the #1143 review found the old filter missing, and the tip's own shapes
REFUSED = [
    "/Users/someone/dev/mosaic-theory/data/theme_intelligence/runs/R-1",
    "/Users/Alice Smith/x.pdf",
    r"C:\Users\Alice Smith\x.pdf",
    "C:/Users/alice/x.pdf",
    "see `/Users/someone/x`",
    "path:/Users/someone/x",
    "</Users/someone/x>",
    "file://localhost/Users/someone/x",
    r"\\server\share\alice\x.pdf",
    "~/dev/mosaic-theory/x",
    "/home/runner/work/mosaic-theory/x.py",
    'sers/work/Documents/GitHub/mosaic-theory/vinci/x.py", line 5, in f',  # a cut traceback
    "RUN ERROR: boom\nrs/work/Documents/x.py\", line 5",  # cut further in, on its own line
    "/private/tmp/claude-501/-Users-work-Documents-GitHub-mosaic-theory/s/documents/a.pdf",
    "a session folder -Users-work-Documents-GitHub-x/s/a.pdf, no temporary root",
    "/Users/someone/[draft]/r.pdf",
]
PASSED = [
    "$40 /kW/month",
    "(/kWh/yr)",
    "https://www.goldmansachs.com/insights/articles/ai-capex",
    "https://www.example.com/home/insights/a-note",
    "11/19/2026 and 3/4 of the market",
    "AI users/customers grew",
    "runs/R-20261119T150131Z-market",
    "http_cache/abc.body",
    "documents/abc.pdf",
    'vinci/theme_intelligence/pipeline.py", line 5, in run',
    "⟨local path⟩/x.pdf",
]


@pytest.mark.parametrize("text", REFUSED)
def test_every_home_directory_or_username_shape_is_refused(text: str) -> None:
    assert path_findings(text), text


@pytest.mark.parametrize("text", PASSED)
def test_a_figure_a_url_or_a_relative_name_is_not_a_path(text: str) -> None:
    assert path_findings(text) == [], text


def test_the_guard_reads_every_string_of_an_export_json_in_text_included(tmp_path: Path) -> None:
    out = tmp_path / "export"
    out.mkdir()
    payload = json.dumps({"detail": "ok", "deep": {"list": ["fine", REFUSED[0]]}})
    (out / "verification_issues.jsonl").write_text(
        json.dumps({"issue_id": "VI-1", "payload": payload}) + "\n")
    (out / "runs.jsonl").write_text(json.dumps({"run_id": "R-1", "payload": "{}"}) + "\n")
    found = export_findings(out)
    assert found == ["verification_issues.jsonl VI-1 .payload.deep.list[]: "
                     "a macOS home directory"]
    assert "someone" not in found[0]  # the shape is named, never the path


# --- a traceback is named before its cut ----------------------------------------------------------

def test_a_traceback_is_named_before_its_cut_so_no_cut_leaves_a_home_directory() -> None:
    # 30 DISTINCT frames (a repeated one is folded into "[Previous line repeated …]")
    src = "".join(f"def f{i}():\n    f{i + 1}()\n" for i in range(30))
    src += "def f30():\n    raise FileNotFoundError('/Users/someone/projects/x/missing.pdf')\n"
    ns: dict[str, Any] = {}
    exec(compile(src, "/Users/someone/projects/deep/folder/module.py", "exec"), ns)  # noqa: S102
    try:
        ns["f0"]()
    except FileNotFoundError:
        raw = traceback.format_exc()
        full = traceback_text(limit=10 ** 9)
        stored = traceback_text()
    # CONTROL: the old way, `format_exc()[-1500:]`, leaves a path at some cut point
    assert any(path_findings(raw[-k:]) for k in range(1, len(raw) + 1))
    assert len(full) > TRACEBACK_CHARS  # the fixture's shape: the cut falls inside the frames
    assert [k for k in range(1, len(full) + 1) if path_findings(full[-k:])] == []
    assert stored == full[-TRACEBACK_CHARS:] and "⟨local path⟩/module.py" in stored
    assert "tests/test_theme_intelligence_local_paths.py" in full  # this file, named relative


# --- a new run and version store their paths relative ---------------------------------------------

def _run(tmp_path: Path) -> tuple[Pipeline, str]:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("local-paths", "Test Publisher", date(2026, 11, 12),
               [("paragraph", "Synthetic grid demand rose 12% in 2026, the note says.")])
    doc = art.doc()
    fr = replace(fetched(doc), cache_path=pipe.paths.http_cache / "abc.body")
    pipe.process_document(doc, fr, url=doc.canonical_url, source_id="manual", as_of=AS_OF,
                          fixture=extraction(
                              [claim("c1", "b001", "Synthetic grid demand rose 12% in 2026",
                                     "Grid demand rose 12%", metric="grid demand", value=12,
                                     value_text="12%", unit="%", period="2026")],
                              [hyp("h1", "Synthetic grid wave", node="ai_infrastructure.power",
                                   mechanism="supply_constraint", supporting=["c1"])]),
                          publisher_override=art.publisher)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe, run.run_id


def test_a_new_run_and_version_store_their_paths_relative_to_the_data_directory(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pipe, rid = _run(tmp_path)
    run = pipe.store.run(rid)
    assert run is not None and run.output_dir == f"runs/{rid}"
    locs = {v.evidence_location for a in pipe.store.articles()
            for v in pipe.store.article_versions(a.article_id)}
    assert locs == {"http_cache/abc.body"}
    # finding 10: a re-render without --out writes under the data directory, wherever it is run
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    write_run_outputs(pipe.store, rid)
    assert (pipe.paths.runs / rid / "manifest.json").exists()
    assert list(elsewhere.iterdir()) == []
    pipe.store.export_jsonl(tmp_path / "export")
    assert export_findings(tmp_path / "export") == []


def test_a_failed_runs_error_message_is_scrubbed_where_it_is_stored(tmp_path: Path) -> None:
    """Every caller stores `f"{type}: {exc}\n{traceback_text()}"`: the MESSAGE half is scrubbed
    by `finish_run` itself (review round 0), not only by an export."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    run = pipe.finish_run(RunStatus.FAILED, error="FileNotFoundError: /Users/someone/Downloads/"
                          "report.pdf\nTraceback …")
    assert run.warnings and path_findings(run.warnings[-1]) == []
    assert "⟨local path⟩/report.pdf" in run.warnings[-1]


@pytest.mark.parametrize(("stored", "expected"), [
    (None, "runs/R-1"),
    ("runs/R-1", "runs/R-1"),
    ("data/theme_intelligence/runs/R-1", "runs/R-1"),  # relative to another working directory
])
def test_a_runs_readout_resolves_under_the_data_directory(
        tmp_path: Path, stored: str | None, expected: str) -> None:
    assert run_dir(tmp_path, "R-1", stored) == tmp_path / expected
    assert run_dir(tmp_path, "R-1", "/elsewhere/runs/R-1") == Path("/elsewhere/runs/R-1")


# --- an export writes rows stored before this change relative -------------------------------------

#: the tip's real shapes (state a74c4e30), the username replaced
LEGACY_RUN_DIRS = ["/Users/someone/dev/mosaic-theory/data/theme_intelligence/runs/{rid}",
                   "data/theme_intelligence/runs/{rid}",
                   "/private/tmp/claude-501/-Users-work-Documents-GitHub-x/s/runs/{rid}"]
LEGACY_WARNING = (
    "RUN ERROR: InvalidAnswerError: extraction: the model's answer fails its schema\n"
    # cut by [-1500:] inside the home directory: only the frame rewrite repairs this line
    'sers/someone/Documents/GitHub/mosaic-theory/.claude/worktrees/t/vinci/theme_intelligence/'
    'pipeline.py", line 1034, in run_article\n'
    '  File "/Users/someone/Documents/GitHub/mosaic-theory/.claude/worktrees/t/vinci/'
    'theme_intelligence/extract.py", line 88, in parse\n'
    '  File "/Users/someone/.venv/lib/python3.12/site-packages/pydantic/main.py", line 5, in v\n'
    "pydantic.ValidationError: 1 error\n"
    "OSError: [Errno 2] '/Users/someone/Downloads/report.pdf'")  # a home path beyond any frame
LEGACY_LOCATIONS = [
    "/Users/someone/dev/mosaic-theory/data/theme_intelligence/documents/abc.pdf",
    "data/theme_intelligence/http_cache/abc.body",
    "/private/tmp/claude-501/-Users-work-Documents-GitHub-x/s/merge_work/documents/abc.pdf"]


def _legacy(pipe: Pipeline, rid: str, k: int) -> None:
    run = pipe.store.run(rid)
    assert run is not None
    pipe.store.upsert_run(run.model_copy(update={
        "output_dir": LEGACY_RUN_DIRS[k].format(rid=rid), "warnings": [LEGACY_WARNING]}))
    art = pipe.store.articles()[0]
    v = pipe.store.article_versions(art.article_id)[0]
    pipe.store.add_article_version(v.model_copy(update={
        "version_id": f"AV-legacy{k:07d}", "content_sha256": f"{k:064d}",
        "evidence_location": LEGACY_LOCATIONS[k]}))


@pytest.mark.parametrize("k", [0, 1, 2])
def test_an_export_writes_old_rows_relative_and_every_other_row_as_stored(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, k: int) -> None:
    pipe, rid = _run(tmp_path)
    _legacy(pipe, rid, k)
    with monkeypatch.context() as m:  # the export as it was before this change
        m.setattr(localpaths, "exported_payload", lambda _t, p: p)
        pipe.store.export_jsonl(tmp_path / "before")
    pipe.store.export_jsonl(tmp_path / "after")
    assert export_findings(tmp_path / "before")  # CONTROL: the old export carries the paths
    assert export_findings(tmp_path / "after") == []
    changed: dict[str, int] = {}
    for f in sorted((tmp_path / "before").glob("*.jsonl")):
        old = f.read_text().splitlines()
        new = (tmp_path / "after" / f.name).read_text().splitlines()
        assert len(old) == len(new)
        for a, b in zip(old, new, strict=True):
            if a == b or f.stem == "meta":
                continue
            changed[f.stem] = changed.get(f.stem, 0) + 1
            pa, pb = json.loads(json.loads(a)["payload"]), json.loads(json.loads(b)["payload"])
            moved = {key for key in pa if pa[key] != pb[key]}
            assert moved <= {"output_dir", "warnings", "evidence_location"}, moved
    assert changed == {"runs": 1, "article_versions": 1}  # the legacy rows, no other
    run = Store.import_jsonl(tmp_path / "after", tmp_path / "imported.db").run(rid)
    assert run is not None and run.output_dir == f"runs/{rid}"
    w = run.warnings[0]
    assert '\nvinci/theme_intelligence/pipeline.py", line 1034' in w
    assert 'File "vinci/theme_intelligence/extract.py", line 88' in w
    assert 'File "<site-packages>/pydantic/main.py", line 5' in w


# --- export-state and state push refuse a path the rewrite does not know --------------------------

def _with_unknown_path(tmp_path: Path) -> Pipeline:
    """A row whose writer does NOT scrub (straight to the store; `_issue` would scrub it), in a
    field no export rewrites: only the guard stands between it and the branch."""
    pipe, rid = _run(tmp_path)
    pipe.store.add_issue(VerificationIssue(
        issue_id="VI-unscrubbed0001", run_id=rid, scope="run", ref_id=rid,
        severity=IssueSeverity.INFO, code="TEST_NOTE",
        detail="read from /Users/someone/Downloads/report.pdf", created_at=datetime.now(tz=UTC)))
    return pipe


def test_export_state_refuses_a_path_and_writes_nothing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pipe = _with_unknown_path(tmp_path)
    pipe.store.close()
    out = tmp_path / "registry"
    assert cli(["--data-dir", str(pipe.paths.root), "export-state", "--out", str(out)]) == 1
    assert not list(out.glob("*.jsonl")) if out.exists() else True
    err = capsys.readouterr().err
    assert "verification_issues.jsonl" in err and "a macOS home directory" in err
    assert "someone" not in err


def test_state_push_refuses_a_path(tmp_path: Path) -> None:
    pipe = _with_unknown_path(tmp_path)
    pipe.store.close()
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--quiet", "--bare", str(remote)], check=True)
    with pytest.raises(state.StateSyncError, match="refusing to push: .*a macOS home directory"):
        state.push(pipe.paths.root, str(remote))


# --- the reader: large type past a heading's length is a paragraph; its headline stays ------------

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
HEADLINE = "1. Synthetic returns"


def _read(tmp_path: Path, big: list[tuple[float, str]]) -> list[Any]:
    lines = [(s, 720 - 22 * i, t) for i, (s, t) in enumerate(big)]  # wrapped: the gap < its size
    y0 = 720 - 22 * len(big) - 30
    lines += [(10.0, y0 - 13 * i, f"{BODY} {i}.") for i in range(12)]
    p = tmp_path / "large_type.pdf"
    p.write_bytes(_pdf(lines))
    return list(read_document(p, Declared(source_id="gs_research")).doc.blocks)


def test_large_type_running_past_a_headings_length_is_a_paragraph(tmp_path: Path) -> None:
    blocks = _read(tmp_path, [(18.0, t) for t in BIG])
    assert len(" ".join(BIG)) > HEADING_MAX_CHARS  # the fixture's shape
    assert all(len(b.section or "") <= HEADING_MAX_CHARS for b in blocks)
    assert not [b for b in blocks if b.kind == "heading"]  # a full first line is no headline
    big = [b for b in blocks if b.kind == "paragraph" and BIG[0][:30] in b.text]
    assert len(big) == 1 and BIG[-1][-20:] in big[0].text  # its lines are ONE paragraph


def test_a_headline_that_opens_large_type_stays_the_heading(tmp_path: Path) -> None:
    """Finding 8: "1. Diversified returns", then its paragraph in the same large type."""
    blocks = _read(tmp_path, [(18.0, HEADLINE), *((18.0, t) for t in BIG)])
    heads = [b for b in blocks if b.kind == "heading"]
    assert [h.text for h in heads] == [HEADLINE]
    big = [b for b in blocks if b.kind == "paragraph" and BIG[0][:30] in b.text]
    assert len(big) == 1 and big[0].text.startswith(BIG[0][:30])  # it starts at the next line
    assert {b.section for b in blocks if b.kind == "paragraph"} == {HEADLINE}


#: a WIDE headline on two lines, in a bigger type than the large type after it: the width rule
#: cannot tell it from a paragraph (its first line fills the column), the type size can
WIDE = ["Synthetic investment focus: selected beneficiaries of",
        "lower energy prices"]


def test_a_heading_in_its_own_type_size_is_not_merged_into_large_type(tmp_path: Path) -> None:
    blocks = _read(tmp_path, [*((22.0, t) for t in WIDE), *((18.0, t) for t in BIG)])
    assert [h.text for h in blocks if h.kind == "heading"] == [" ".join(WIDE)]
    assert {b.section for b in blocks if b.kind == "paragraph"} == {" ".join(WIDE)}


def test_a_heading_wrapped_onto_two_lines_is_still_one_heading(tmp_path: Path) -> None:
    """NEGATIVE: a real heading set on two lines stays one heading, the section after it."""
    two = ["Synthetic grid outlook", "for the coming year"]
    blocks = _read(tmp_path, [(18.0, t) for t in two])
    assert [h.text for h in blocks if h.kind == "heading"] == [" ".join(two)]
    assert {b.section for b in blocks if b.kind == "paragraph"} == {" ".join(two)}


# --- round 2 (A's review of #1156): the scrub never keeps a username; scratch folders refused --

@pytest.mark.parametrize(("text", "names"), [
    ("PermissionError: '/Users/work'", ["work"]),
    ("/Users/Alice Smith/Downloads/x.pdf", ["Alice", "Smith"]),
    (r"C:\Users\Alice Smith\x.pdf", ["Alice", "Smith"]),
    ("/home/alice: not a directory", ["alice"]),
    ("open /private/var/folders/w1/abc/T/pytest-of-alice/x.pdf", ["alice", "folders"]),
    ("/tmp/pytest-of-alice", ["alice"]),
])
def test_the_scrub_never_keeps_a_username_or_a_home_directory(
        text: str, names: list[str]) -> None:
    """S1: a path ending, or cut, at its username keeps no part of it as a "file name"."""
    out = localpaths.scrub_text(text)
    assert path_findings(out) == [], out
    assert [n for n in names if n in out] == [], out


def test_this_machines_home_is_replaced_whole_and_only_whole(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """S1 and M7: a home outside /Users and /home is scrubbed too, and only at a boundary —
    "/Users/macbook" is not "/Users/mac" + "book"."""
    monkeypatch.setenv("HOME", "/opt/someone")
    assert "someone" not in localpaths.scrub_text("open /opt/someone/notes/x.pdf failed")
    monkeypatch.setenv("HOME", "/Users/mac")
    out = localpaths.scrub_text("cannot read /Users/macbook/x.pdf")
    assert "book" not in out.replace("x.pdf", "") and path_findings(out) == [], out


@pytest.mark.parametrize("text", [
    "/private/var/folders/w1/abc/T/pytest-of-alice/x.pdf",
    "saved to /var/folders/w1/abc/T/x.pdf earlier",
    "read /tmp/x/y.pdf",
    "/private/tmp/claude-501/0c5e1f2a-9d1b-4f6e-8a1b-2c3d4e5f6a7b/x.pdf",
    "/home/alice",
    "/root/x.pdf",
    "~alice/notes.txt",
    "//server/share/x.pdf",
    "%2FUsers%2Falice%2Fx.pdf",
    "/Volumes/Alice Backup/x.pdf",
    "/users/alice/x.pdf",
])
def test_a_scratch_folder_and_the_rarer_home_shapes_are_refused(text: str) -> None:
    """S2 and N3."""
    assert path_findings(text), text


@pytest.mark.parametrize("text", [
    "https://api.example.com/Users/123",  # N4: a URL's path is no home directory
    "https://www.example.com/users/123/profile",
    "https://www.example.com/root-cause/analysis",
    "https://www.example.com/tmp/x",
    "a 3/4 share and 10/20 vision",
    "~3/4 of the market and about ~10/20 basis points",
])
def test_a_url_or_a_fraction_is_still_not_a_path(text: str) -> None:
    assert path_findings(text) == [], text


@pytest.mark.parametrize("home", ["/", "/root"])
def test_a_short_home_never_turns_every_slash_into_a_finding(
        home: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """N2: with HOME=/ every slash was refused; with HOME=/root a URL's /root-cause was."""
    monkeypatch.setenv("HOME", home)
    assert path_findings("runs/R-1 and 3/4 at https://www.example.com/root-cause") == []


def test_a_dict_key_holding_a_path_is_refused_and_never_printed(tmp_path: Path) -> None:
    """N1: keys are scanned, and a refusal prints the field without the key's text."""
    out = tmp_path / "export"
    out.mkdir()
    payload = json.dumps({"counts": {"/Users/someone/x.pdf": 1}})
    (out / "runs.jsonl").write_text(json.dumps({"run_id": "R-1", "payload": payload}) + "\n")
    found = export_findings(out)
    assert found and all("someone" not in f for f in found), found


def test_an_issue_or_a_warning_built_from_an_exception_is_scrubbed_where_it_is_stored(
        tmp_path: Path) -> None:
    """N5: an exception message reaches `verification_issues` through `_issue` — scrubbed there,
    before its id is hashed, so a message naming no path keeps the id it always had."""
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("ingest", as_of=AS_OF)
    pipe._issue("run", run.run_id, IssueSeverity.WARN, "TEST_NOTE",
                "PermissionError: [Errno 13] '/Users/someone/Downloads/report.pdf'")
    pipe._issue("run", run.run_id, IssueSeverity.WARN, "TEST_NOTE", "no path here")
    details = {i.detail for i in pipe.store.issues(run_id=run.run_id)}
    assert "no path here" in details
    assert all(path_findings(d) == [] for d in details), details


def test_a_refusal_names_the_way_out(tmp_path: Path) -> None:
    """N5: a stored row is append-only, so the refusal says how a registry is rebuilt."""
    pipe = _with_unknown_path(tmp_path)
    pipe.store.close()
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--quiet", "--bare", str(remote)], check=True)
    with pytest.raises(state.StateSyncError, match="state pull --force"):
        state.push(pipe.paths.root, str(remote))


def test_a_path_outside_the_data_directory_keeps_only_its_file_name(tmp_path: Path) -> None:
    """N7."""
    assert localpaths.data_relative(tmp_path / "data" / "runs" / "R-1", tmp_path / "data") \
        == "runs/R-1"
    assert localpaths.data_relative("/elsewhere/cache/x.body", tmp_path) == "⟨local path⟩/x.body"
