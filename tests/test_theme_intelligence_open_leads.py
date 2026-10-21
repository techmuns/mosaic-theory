"""STATE §5.0 row 32 (8): the theme-intelligence leads still open on 2026-10-20 — the figure ledger
reading a figure REFERENCE as a figure ((i)), QA's content-hash check, the desk's counter-evidence
gate and its Articles follow-up (the three batch-B leads), and the weekly run's paid cache (U31f).

Each was measured on the 132 local registries before it was changed
(`docs/records/2026-10-20-theme-intelligence-open-leads.md`); the pins here run the real functions
on the committed fixtures, with the corpus's own sentences where the lead was a sentence.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from tests.test_theme_intelligence_batch_b import (
    _contested,
    _current,
    _jpm_run,
    _preview_only_unreadable,
)
from tests.theme_intelligence_support import CALM_DIR, load_document
from vinci.theme_intelligence import desk as dk
from vinci.theme_intelligence.completeness import scan_article
from vinci.theme_intelligence.priority import F8_CONTESTED, counter_verdict
from vinci.theme_intelligence.qa import run_qa

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "theme-intelligence-weekly.yml"


# --- (i) the figure ledger: a reference to a figure, table or section is not a figure ----------

#: The four sentences of the local corpus whose number the ledger read and should not have —
#: verbatim as the completeness reports stored them (2026-10-20; 4 of 27,758 stored figures).
_REFERENCES = {
    "23": "Spending freezes and executive decrees can contribute at the margin (see Figure | | | "
          "; | 23), as evidenced by the government's expenditure cuts.",
    "165": "The Clean Air Act requires a decision within a year of a complete application "
           "( section 165(c) ); no national data on actual times exists.",
    "39.169": 'Texas Utilities Code §39.169, "Co-location of Large Load Customer With Existing '
              'Generation Resource," covers certain net-metering arrangements.',
    "10.0": "Source: Penn World Table 10.0, using Solow Residual with Bottom-Up regional "
            "aggregation.",
}


def _ledger_cores(text: str) -> set[str]:
    doc = load_document(CALM_DIR)  # a real parsed page; one of its blocks carries the sentence
    block = doc.blocks[0].model_copy(update={
        "block_id": "b900", "kind": "paragraph", "text": text,
        "sha256": hashlib.sha256(text.encode()).hexdigest()})
    return {f.core for f in scan_article(dataclasses.replace(doc, blocks=(block,))).figures}


def test_a_figure_reference_is_not_a_figure() -> None:
    """Lead (i), open since 2026-10-11: "see Figure | | ; | 23" was a figure of 23. A number that
    NAMES a figure, table, section or statute is read as a reference — debris between the word
    and the number included."""
    for core, sentence in _REFERENCES.items():
        assert core not in _ledger_cores(sentence), (core, sentence)


def test_the_figures_beside_a_reference_are_still_read() -> None:
    """NEGATIVE: the rule takes the referenced number only. A figure in the same sentence, a
    percentage-point figure ("5 pp" — the probe's own false positive) and a number after a
    capitalised word that is no reference word are all still in the ledger."""
    assert "40%" in _ledger_cores("Figure 3 shows prices up 40% since March.")
    assert "3" not in _ledger_cores("Figure 3 shows prices up 40% since March.")
    assert {"2", "5", "10"} <= _ledger_cores(
        "2026 May YTD - 2024 LATAM countries 2 pp 5 pp 10 pp")
    assert "23%" in _ledger_cores("Table: revenue grew 23% in the quarter.")
    assert "30" in _ledger_cores("Utilities fell over 30 sessions, the longest run since 2008.")
    # words between the reference word and the number: a figure, not a reference
    assert "12" in _ledger_cores("The table shows 12 regions growing faster than the rest.")


# --- the batch-B lead: QA's hash check reads the content AS STORED -----------------------------

def _hash_check(pipe: Any, run_id: str) -> Any:
    return next(c for c in run_qa(pipe.store, run_id).checks
                if c.name == "version content hashes recompute")


def _insert_version(pipe: Any, thesis_id: str, content: dict[str, Any], sha: str) -> None:
    row = pipe.store.conn.execute("SELECT as_of, payload FROM thesis_versions WHERE thesis_id=? "
                                  "AND version=1", (thesis_id,)).fetchone()
    payload = json.loads(row[1])
    payload.update({"version": 2, "content": content, "content_sha": sha})
    pipe.store.conn.execute("INSERT INTO thesis_versions (thesis_id, version, as_of, payload) "
                            "VALUES (?, 2, ?, ?)", (thesis_id, row[0], json.dumps(payload)))


def test_a_version_written_before_a_field_was_added_still_recomputes(tmp_path: Path) -> None:
    """THE PILOT'S SHAPE: six versions written before `s07_what_could_go_wrong.price_context`
    existed. Their stored bytes hash to their stored sha exactly; re-serialising them through
    today's model adds `"price_context": []` and moves the hash, so QA failed intact versions
    (969 of 1,011 stored versions across the local registries). The check now hashes what is
    stored."""
    pipe, rid = _jpm_run(tmp_path)
    th = pipe.store.theses()[0]
    content = json.loads(pipe.store.conn.execute(
        "SELECT payload FROM thesis_versions WHERE thesis_id=? AND version=1",
        (th.thesis_id,)).fetchone()[0])["content"]
    assert "price_context" in content["s07_what_could_go_wrong"]
    del content["s07_what_could_go_wrong"]["price_context"]
    sha = hashlib.sha256(json.dumps(content, separators=(",", ":"),
                                    ensure_ascii=False).encode()).hexdigest()
    _insert_version(pipe, th.thesis_id, content, sha)
    v2 = pipe.store.thesis_version(th.thesis_id, 2)
    assert v2 is not None and v2.content_sha == sha  # it parses, the field defaulted
    check = _hash_check(pipe, rid)
    assert check.ok, check.detail


def test_a_stored_version_whose_content_changed_still_fails(tmp_path: Path) -> None:
    """NEGATIVE: the check still catches what it exists for — stored content that no longer
    matches its recorded hash (one word changed, the sha kept)."""
    pipe, rid = _jpm_run(tmp_path)
    th = pipe.store.theses()[0]
    payload = json.loads(pipe.store.conn.execute(
        "SELECT payload FROM thesis_versions WHERE thesis_id=? AND version=1",
        (th.thesis_id,)).fetchone()[0])
    content = payload["content"]
    content["header"]["title"] = content["header"]["title"] + " (edited)"
    _insert_version(pipe, th.thesis_id, content, payload["content_sha"])
    check = _hash_check(pipe, rid)
    assert not check.ok and f"{th.thesis_id} v2" in check.detail


# --- the batch-B lead: the desk's counter-evidence gate reads the stored verdict ---------------

def test_a_contested_watch_shows_its_counter_evidence_gate_beside_other_failures(
        tmp_path: Path) -> None:
    """THE CONSTRUCTED CASE: a WATCH held by an independent contradiction AND by its exposure and
    catalyst gates. The gate was inferred by elimination — only when every other gate passed — so
    this thesis never showed it (15 of 16 such versions locally). NEGATIVE: the contradicting
    thesis carries no verdict and gets no such gate."""
    pipe, _rid, tid, other = _contested(tmp_path)
    v = _current(pipe, tid)
    assert counter_verdict(v.priority) == F8_CONTESTED
    gs = dk.gates(v, [], dk.near_term_reading(pipe.store, v))
    failing = [g.name for g in gs if not g.ok]
    assert "Not outweighed by counter-evidence" in failing and len(failing) >= 3, failing
    (g,) = [x for x in gs if x.name == "Not outweighed by counter-evidence"]
    assert "contradict" in g.detail
    o = _current(pipe, other)
    assert counter_verdict(o.priority) is None
    assert not [x for x in dk.gates(o, [], dk.near_term_reading(pipe.store, o))
                if x.name == "Not outweighed by counter-evidence"]


# --- the batch-B lead: the Articles follow-up is the ONE partial-awaiting-full rule ------------

def _article_row(pipe: Any, aid: str) -> Any:
    run = max(pipe.store.runs(), key=lambda r: r.started_at)
    weeks = dk.desk_weeks(pipe.store, run)
    rows = [r for w in weeks for r in dk.week_articles(dk._Registry(pipe.store), w,
                                                        latest=w is weeks[-1])
            if r.article_id == aid]
    assert rows, "the article must be on the Articles screen"
    return rows[-1]


def test_unreadable_pages_ask_for_a_visual_check_not_the_full_report(tmp_path: Path) -> None:
    """A supplied document whose pages could not be read: Uploads and the weekly report ask for
    a VISUAL check; the Articles screen asked for "the full report" — the document already
    supplied (8 rows locally). Now it asks what the shared rule asks, and points to Uploads."""
    pipe, _run, aid = _preview_only_unreadable(tmp_path)
    row = _article_row(pipe, aid)
    assert row.state == "PARTIAL"
    assert row.follow_up == "Check the unreadable pages" and row.follow_link == "uploads.html"


def test_back_matter_only_asks_for_nothing_and_says_why(tmp_path: Path, monkeypatch: Any) -> None:
    """NEGATIVE: unreadable pages that are back matter only leave the analysis whole — the rule
    asks nothing, and the row says so rather than asking for a report (11 rows locally)."""
    from vinci.theme_intelligence import report as rp

    pipe, _run, aid = _preview_only_unreadable(tmp_path)
    real = rp.unread_documents

    def back_matter(documents: Any, retired: set[str]) -> Any:
        return {k: d.model_copy(update={"quarantined": tuple(
            q.model_copy(update={"kind": "back_matter"}) for q in d.quarantined)})
            for k, d in real(documents, retired).items()}

    monkeypatch.setattr(dk, "unread_documents", back_matter)
    row = _article_row(pipe, aid)
    assert row.state == "PARTIAL" and not row.follow_link
    assert row.follow_up == "Nothing to ask — only back-matter pages could not be read"


# --- U31f: the weekly run keeps the answers it paid for, a failed run included ---------------

def _steps(text: str) -> list[str]:
    """The workflow's steps as text blocks, in order (each begins at its `- name:` / `- uses:`)."""
    return re.split(r"\n(?=      - (?:name|uses):)", text)


def cache_violations(text: str) -> list[str]:
    """What keeps a failed run's paid answers from being saved: the combined `actions/cache`
    (saved only when the job succeeds), no separate save, a save that does not run `always()`, a
    save before the scan, or a key without the attempt (a re-run cannot write the same key)."""
    out: list[str] = []
    steps = _steps(text)
    names = [s.split("\n", 1)[0] for s in steps]
    if any(re.search(r"uses:\s*actions/cache@", s) for s in steps):
        out.append("combined actions/cache: saved only when the job succeeds")
    save = [i for i, s in enumerate(steps) if "actions/cache/save@" in s]
    scan = [i for i, n in enumerate(names) if n.strip().endswith("name: Scan")]
    if not save:
        out.append("no actions/cache/save step")
    elif not re.search(r"if:\s*always\(\)", steps[save[0]]):
        out.append("the save step does not run always()")
    elif not scan or save[0] < scan[0]:
        out.append("the save step runs before the scan")
    for s in steps:
        if "actions/cache/" in s and "github.run_attempt" not in s:
            out.append("a cache key without the run attempt")
    return out


def test_the_weekly_run_saves_its_llm_cache_even_when_the_job_fails() -> None:
    """U31f, open since 2026-10-14: the job fails on purpose when the scan fails or QA does not
    pass, and the combined `actions/cache` saved only on success — a failed run's paid answers
    were thrown away and the retry paid again. Restore and save are now two steps, the save
    `always()`, after the scan, keyed by run AND attempt."""
    assert cache_violations(WORKFLOW.read_text()) == []


def test_the_combined_cache_main_carried_is_rejected() -> None:
    """NEGATIVE: the lint rejects the form the workflow carried until this change."""
    before = """
      - name: Restore the LLM cache (content-addressed; a miss only costs money and time)
        uses: actions/cache@v4
        with:
          path: data/theme_intelligence/llm_cache
          key: theme-intelligence-llm-${{ github.run_id }}
          restore-keys: theme-intelligence-llm-

      - name: Scan
        id: scan
        run: python -m vinci.theme_intelligence scan
"""
    got = cache_violations(before)
    assert "combined actions/cache: saved only when the job succeeds" in got
    assert "no actions/cache/save step" in got


def test_the_dates_in_this_file_are_the_measurement_dates() -> None:
    """The corpus counts above were measured on one date; a pin that quotes them states it."""
    assert dt.date(2026, 10, 20).isoformat() in Path(__file__).read_text()


# --- the first Actions run: a secret with surrounding whitespace is refused by name -------------

def test_a_padded_secret_is_refused_by_name_before_any_request(monkeypatch: Any) -> None:
    """2026-10-20: the first Actions run's ANTHROPIC_API_KEY carried trailing whitespace, and the
    run died in the HTTP client as "Connection error" ("Illegal header value"). `require_env`
    now refuses it by name, never printing it. NEGATIVE: a clean value is returned as it is."""
    import pytest

    from vinci.config import require_env

    monkeypatch.setenv("VINCI_TEST_SECRET", "sk-test-value ")
    with pytest.raises(RuntimeError, match="VINCI_TEST_SECRET.*whitespace") as e:
        require_env("VINCI_TEST_SECRET")
    assert "sk-test-value" not in str(e.value)
    monkeypatch.setenv("VINCI_TEST_SECRET", "sk-test-value")
    assert require_env("VINCI_TEST_SECRET") == "sk-test-value"


VALIDATOR = ROOT / ".github" / "scripts" / "validate_keys.py"
VALIDATE_WORKFLOW = ROOT / ".github" / "workflows" / "validate-keys.yml"


def _validator() -> Any:
    """The `validate-keys` script, loaded as a module (it is not a package)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("validate_keys", VALIDATOR)
    assert spec is not None and spec.loader is not None
    vk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vk)
    return vk


def test_the_key_validator_fails_a_padded_key_instead_of_calling_it_connectivity(
        monkeypatch: Any, capsys: Any) -> None:
    """`validate-keys` read the padded key's connection error as "runner connectivity, NOT a key
    problem" and passed green from 2026-06-26 until the 2026-10-20 run. It now FAILS the key
    before any request (no network here: the check precedes the call)."""
    vk = _validator()
    def no_request(url: str, **kw: Any) -> Any:
        raise AssertionError("a padded key sends no request")

    monkeypatch.setattr(vk.httpx, "get", no_request)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test\n")
    monkeypatch.setenv("POLYGON_API_KEY", " pk-test")
    monkeypatch.setenv("TIINGO_API_KEY", "tiingo-test ")
    assert vk.check_anthropic() is False and vk.check_polygon() is False
    assert vk.check_tiingo() is False
    out = capsys.readouterr().out
    assert "ANTHROPIC_API_KEY: FAIL — the secret has leading or trailing whitespace" in out
    assert "POLYGON_API_KEY: FAIL — the secret has leading or trailing whitespace" in out
    assert "TIINGO_API_KEY: FAIL — the secret has leading or trailing whitespace" in out
    assert "sk-ant-test" not in out and "pk-test" not in out and "tiingo-test" not in out


# --- the second Actions run: Tiingo refused the Actions key, and nothing checked it -------------

class _Response:
    """The two things `check_tiingo` reads from an httpx response."""

    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code, self._body = status_code, body

    def json(self) -> Any:
        return self._body


def test_the_key_validator_fails_a_refused_tiingo_key_with_tiingos_reason(
        monkeypatch: Any, capsys: Any) -> None:
    """2026-10-21: Tiingo refused all 43 of run 39565710165's requests (403) while the local key
    read the same URL, and `validate-keys` never asked Tiingo. It now does, with the request the
    weekly run makes, and FAILS a refused key with Tiingo's own reason — the body Tiingo returned
    for an invalid token that day — never the key."""
    vk = _validator()
    seen: dict[str, Any] = {}

    def get(url: str, **kw: Any) -> _Response:
        seen.update(url=url, **kw)
        return _Response(403, {"detail": "Invalid token."})

    monkeypatch.setattr(vk.httpx, "get", get)
    monkeypatch.setenv("TIINGO_API_KEY", "tiingo-test-key")
    assert vk.check_tiingo() is False
    out = capsys.readouterr().out
    assert "TIINGO_API_KEY: FAIL — HTTP 403: Invalid token." in out
    assert "tiingo-test-key" not in out
    assert seen["url"] == "https://api.tiingo.com/tiingo/daily/aapl/prices"
    assert seen["headers"] == {"Authorization": "Token tiingo-test-key"}
    # HYPOTHETICAL shape (Tiingo has not been seen to echo a key): a reason quoting the key is
    # printed with the key masked — the value is never printed, whatever the service returns
    monkeypatch.setattr(vk.httpx, "get", lambda url, **kw: _Response(
        403, {"detail": "Token tiingo-test-key is not valid."}))
    assert vk.check_tiingo() is False
    out = capsys.readouterr().out
    assert "HTTP 403: Token <key> is not valid." in out and "tiingo-test-key" not in out


def test_a_working_tiingo_key_passes_and_an_unset_one_only_warns(
        monkeypatch: Any, capsys: Any) -> None:
    """NEGATIVE: a key Tiingo answers 200 passes; no key at all is not a failure (the weekly run
    reads two years of P/E without one) and sends no request."""
    vk = _validator()
    monkeypatch.setattr(vk.httpx, "get", lambda url, **kw: _Response(200, [{"close": 1.0}]))
    monkeypatch.setenv("TIINGO_API_KEY", "tiingo-test-key")
    assert vk.check_tiingo() is True
    assert "TIINGO_API_KEY: PASS" in capsys.readouterr().out

    def no_request(url: str, **kw: Any) -> _Response:
        raise AssertionError("an unset key sends no request")

    monkeypatch.setattr(vk.httpx, "get", no_request)
    monkeypatch.delenv("TIINGO_API_KEY")
    assert vk.check_tiingo() is True
    assert "TIINGO_API_KEY: WARN — secret not set" in capsys.readouterr().out


def test_a_refused_tiingo_key_turns_the_validator_red(monkeypatch: Any) -> None:
    """The check is wired into the run's verdict: a refused Tiingo key fails `validate-keys`.
    NEGATIVE: every check passing exits 0."""
    vk = _validator()
    for name in ("check_anthropic", "check_polygon", "check_sec"):
        monkeypatch.setattr(vk, name, lambda: True)
    monkeypatch.setattr(vk, "check_tiingo", lambda: False)
    assert vk.main() == 1
    monkeypatch.setattr(vk, "check_tiingo", lambda: True)
    assert vk.main() == 0


def unvalidated_secrets(workflows: list[str], validate_workflow: str, script: str) -> set[str]:
    """The secrets a workflow reads that `validate-keys` does not check — a secret is checked when
    the validate workflow passes it AND the script reads it."""
    def read(text: str) -> set[str]:
        return set(re.findall(r"secrets\.([A-Z0-9_]+)", text))

    checked = {n for n in read(validate_workflow) if f'os.environ.get("{n}")' in script}
    return set().union(*(read(w) for w in workflows)) - checked


def test_every_secret_a_workflow_reads_is_checked_by_validate_keys() -> None:
    """Run on the repo's own workflows: before this change the sweep found exactly one —
    TIINGO_API_KEY, read by the weekly theme-intelligence run, checked by nothing."""
    workflows = [p.read_text() for p in sorted((ROOT / ".github" / "workflows").glob("*.yml"))]
    assert unvalidated_secrets(workflows, VALIDATE_WORKFLOW.read_text(),
                               VALIDATOR.read_text()) == set()


def test_a_secret_the_validator_skips_is_found() -> None:
    """NEGATIVE, both halves: the validate workflow without the Tiingo secret (as main carried
    it), and the script without the Tiingo read."""
    workflows = [WORKFLOW.read_text()]
    wf, script = VALIDATE_WORKFLOW.read_text(), VALIDATOR.read_text()
    line = "          TIINGO_API_KEY: ${{ secrets.TIINGO_API_KEY }}\n"
    assert wf.count(line) == 1
    assert unvalidated_secrets(workflows, wf.replace(line, ""), script) == {"TIINGO_API_KEY"}
    read = 'os.environ.get("TIINGO_API_KEY")'
    assert script.count(read) == 1
    assert unvalidated_secrets(workflows, wf, script.replace(read, "")) == {"TIINGO_API_KEY"}
