"""`qa --run RUN_ID` — re-check a run's STORED records, deterministically, without any LLM.

Each check re-derives something from the registry and compares it with what the run recorded, so
a QA pass is evidence about the persisted state, not a restatement of the run's own log:

- spans: every verified claim's quote is re-found in its stored article-version block;
- numbers: every number-bearing verified claim's figure is re-found in its quote;
- look-ahead: no evidence dated after the run's as-of, no article published after it analysed;
- card facts: every source-labelled card line cites a verified claim and prints only its numbers;
- structure: every card has the nine sections in the fixed order;
- immutability: every version's content hash recomputes, and the version chain links up;
- append-only: the no-UPDATE / no-DELETE triggers exist on every history table;
- names: every source-explicit company is a mention whose name is in the article text;
- readiness: a RESEARCH NOW card keeps investment readiness NOT_ASSESSED;
- coverage: a scan reports every configured source, with internally consistent counts;
- renders: HTML / Markdown / JSON of each card carry the same section order and claim refs;
- completeness: every analysed article has a completeness ledger; every figure it states is
  captured or explicitly judged immaterial, and every argument block is accounted for — the open
  ones are listed in full;
- point in time: every listed exposure is common equity registered on a cover page filed on or
  before the run's as-of (no later-registered security, no preferred / debt line);
- labels: every source-labelled line carries the WEAKEST label of the claims it cites, and no
  share-price / valuation move sits in an earnings step;
- authors: every analysed article names its author(s).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

from vinci.theme_intelligence.cards import capped_label
from vinci.theme_intelligence.config import load_sources
from vinci.theme_intelligence.display import first_of
from vinci.theme_intelligence.schemas import (
    SECTION_IDS,
    SOURCE_LABELS,
    FieldStatus,
    InstrumentClass,
    InvestmentReadiness,
    PitStatus,
    Provenance,
    ResearchAction,
    utc_day,
)
from vinci.theme_intelligence.store import APPEND_ONLY_TABLES, Store
from vinci.theme_intelligence.verify import (
    EARNINGS_STEPS,
    card_sentences,
    deterministic_card_checks,
    is_market_reaction,
    label_for,
    locate,
    norm_text,
    stated_numbers,
)


@dataclass
class QaCheck:
    name: str
    ok: bool
    detail: str


@dataclass
class QaResult:
    run_id: str
    checks: list[QaCheck] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.ok)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)


def _fail_list(items: list[str], n: int = 5) -> str:
    shown = items[:n]
    return "; ".join(shown) + (f" … (showing {len(shown)} of {len(items)})" if len(items) > n
                               else "")


def _stored_sections(store: Store, thesis_id: str, version: int) -> list[str]:
    """The card sections of one stored version, in the order its payload holds them (the header
    left out). A parsed version always has the model's field order, so only the stored JSON can
    show a section out of place."""
    row = store.conn.execute("SELECT payload FROM thesis_versions WHERE thesis_id=? AND "
                             "version=?", (thesis_id, version)).fetchone()
    content = json.loads(row[0]).get("content", {}) if row else {}
    return [k for k in content if k != "header"]


def _stored_content_sha(store: Store, thesis_id: str, version: int) -> str | None:
    """sha256 of one version's content AS STORED — the bytes `card_sha` hashed when it was written.

    NOT `card_sha(v.content)`: that re-serialises the PARSED content through today's model, so a
    field the schema gained later (with its default) changes the hash of a version that is intact.
    Measured 2026-10-20 over every local registry: the stored content reproduces 1,011 of 1,011
    stored hashes, the re-serialisation 42 — the pilot's six failures were
    `s07_what_could_go_wrong.price_context`, added after they were written."""
    row = store.conn.execute("SELECT payload FROM thesis_versions WHERE thesis_id=? AND "
                             "version=?", (thesis_id, version)).fetchone()
    if row is None:
        return None
    content = json.loads(row[0]).get("content")
    return hashlib.sha256(json.dumps(content, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def run_qa(store: Store, run_id: str) -> QaResult:
    run = store.run(run_id)
    if run is None:
        raise KeyError(run_id)
    res = QaResult(run_id)
    add = res.checks.append

    add(QaCheck("run status recorded", run.status.value != "RUNNING",
                f"status {run.status.value}; counts {run.counts}"))

    # claims of the articles this run contributed -------------------------------------------------
    # every article this run ANALYSED — including those that yielded no thesis (zero is valid)
    contribs = [c for c in store.contributions() if c.run_id == run_id]
    article_ids = sorted({c.article_id for c in contribs}
                         | {str(c["ref"]) for c in store.llm_calls(run_id)
                            if c.get("purpose") == "extract"})
    span_bad: list[str] = []
    span_unheld: list[str] = []
    num_bad: list[str] = []
    look_bad: list[str] = []
    n_claims = 0
    for aid in article_ids:
        art = store.article(aid)
        if art and art.published_at and utc_day(art.published_at) > run.as_of:
            look_bad.append(f"{aid} published {utc_day(art.published_at)} (UTC) > as-of "
                            f"{run.as_of}")
        for c in store.claims_for_article(aid):
            if not c.span_verified:
                continue
            n_claims += 1
            av0 = store.article_version(c.article_version_id)
            if av0 is not None and av0.blocks and not any(b.text for b in av0.blocks):
                # the text was never brought here (state import / a document kept elsewhere):
                # NOT re-checked — said so, never counted as re-verified
                span_unheld.append(f"{c.claim_id} ({c.article_id})")
                continue
            block = next((b for b in (av0.blocks if av0 else ()) if b.block_id == c.block_id),
                         None)
            if block is None or locate(c.quote, block.text) is None:
                span_bad.append(f"{c.claim_id} ({c.block_id})")
            if c.value_text and c.number_verified:
                nums = [n.replace(",", "") for n in stated_numbers(c.value_text)]
                q = norm_text(c.quote).replace(",", "")
                if nums and not any(n in q for n in nums):
                    num_bad.append(f"{c.claim_id} {c.value_text!r}")
    linked: set[str] = set()
    for th0 in store.theses():
        linked |= {lk.claim_id for lk in store.links(th0.thesis_id)}
    unverified_linked: list[str] = []
    for cid in sorted(linked):
        lc = store.claim(cid)
        if lc and lc.measured_as_of and lc.measured_as_of > run.as_of and \
                lc.article_id in article_ids:
            look_bad.append(f"{cid} measured {lc.measured_as_of} > as-of {run.as_of}")
        if lc is None or not lc.span_verified or lc.number_verified is False:
            unverified_linked.append(cid)
    # unverified material can never raise a research action: it is never linked to a thesis
    add(QaCheck("no unverified claim is linked to a thesis", not unverified_linked,
                _fail_list(unverified_linked)
                or f"{len(linked)} linked claim(s) in the registry, all verified"))
    add(QaCheck("spans re-found in stored article text", not span_bad,
                f"{n_claims - len(span_unheld)} of {n_claims} verified claim(s) in "
                f"{len(article_ids)} article(s) re-checked"
                + (f"; {len(span_unheld)} NOT re-checkable here — the article text is not held "
                   f"on this machine (an imported registry keeps hashes and quotes, never full "
                   f"text); never counted as re-verified: {_fail_list(span_unheld)}"
                   if span_unheld else "")
                + (f"; FAILED: {_fail_list(span_bad)}" if span_bad else "")))
    add(QaCheck("figures re-found in their quotes", not num_bad,
                _fail_list(num_bad) if num_bad else "every number-bearing claim checked"))
    add(QaCheck("no look-ahead past the run's as-of", not look_bad,
                _fail_list(look_bad) if look_bad else f"as-of {run.as_of}"))

    # versions created by this run ----------------------------------------------------------------
    versions = [tv for th in store.theses() for tv in store.thesis_versions(th.thesis_id)
                if tv.run_id == run_id]
    order = [fid for fid, _ in SECTION_IDS]
    struct_bad: list[str] = []
    sha_bad: list[str] = []
    chain_bad: list[str] = []
    fact_bad: list[str] = []
    ready_bad: list[str] = []
    names_bad: list[str] = []
    names_unchecked: list[str] = []
    for v in versions:
        # the STORED version's sections, in the order its payload holds them — never the
        # class's fields, which are the same for every version and so always passed (U27)
        fields = _stored_sections(store, v.thesis_id, v.version)
        if fields != order:
            struct_bad.append(f"{v.thesis_id} v{v.version}: {fields}")
        if _stored_content_sha(store, v.thesis_id, v.version) != v.content_sha:
            sha_bad.append(f"{v.thesis_id} v{v.version}")
        if v.version > 1:
            prior = store.thesis_version(v.thesis_id, v.version - 1)
            if prior is None or prior.content_sha != v.prior_content_sha:
                chain_bad.append(f"{v.thesis_id} v{v.version}")
        claims = {}
        cited = {c for _t, _p, cids in card_sentences(v.content).values() for c in cids}
        for cid in {lk.claim_id for lk in store.links(v.thesis_id)} | cited:
            kc = store.claim(cid)
            if kc is not None:
                claims[cid] = kc
        recorded = {i.ref_id for i in store.issues(run_id=run_id) if i.severity.value == "BLOCK"}
        for i in deterministic_card_checks(v.content, claims, run_id):
            if i.ref_id not in recorded:
                fact_bad.append(f"{i.ref_id} {i.code}")
        if v.priority.research_action is ResearchAction.RESEARCH_NOW and \
                v.priority.investment_readiness is not InvestmentReadiness.NOT_ASSESSED:
            ready_bad.append(f"{v.thesis_id} v{v.version}")
        for co in v.content.s05_affected.companies:
            m = store.mention(co.mention_id)
            av = store.article_version(m.article_version_id) if m else None
            text = norm_text(" ".join(b.text for b in av.blocks)) if av else ""
            if m is not None and av is not None and av.blocks and not text:
                # an imported registry keeps hashes and quotes, never full text (export rule)
                names_unchecked.append(f"{v.thesis_id}: {co.name_as_written}")
            elif m is None or norm_text(m.name_as_written) not in text:
                names_bad.append(f"{v.thesis_id}: {co.name_as_written}")
    add(QaCheck("cards keep the nine sections in order", not struct_bad,
                f"{len(versions)} version(s) created by this run"
                + (f"; FAILED: {_fail_list(struct_bad)}" if struct_bad else "")))
    add(QaCheck("version content hashes recompute", not sha_bad, _fail_list(sha_bad) or "ok"))
    add(QaCheck("version chain links to the prior version", not chain_bad,
                _fail_list(chain_bad) or "ok"))
    add(QaCheck("source-labelled lines cite verified claims (or are withheld)", not fact_bad,
                _fail_list(fact_bad) or "every failing line was recorded and withheld"))
    add(QaCheck("RESEARCH NOW keeps readiness NOT_ASSESSED", not ready_bad,
                _fail_list(ready_bad) or "ok"))
    add(QaCheck("source-explicit companies are named in the article text", not names_bad,
                (_fail_list(names_bad) or "ok")
                + (f"; {len(names_unchecked)} not re-checkable here — their article's full text "
                   f"is not retained by an imported registry (verified when ingested): "
                   f"{_fail_list(names_unchecked)}" if names_unchecked else "")))

    # labels, transmission and point-in-time listings on this run's versions ----------------------
    label_bad: list[str] = []
    react_bad: list[str] = []
    pit_bad: list[str] = []
    for v in versions:
        cited_ids = {c for _t, _p, cids in card_sentences(v.content).values() for c in cids}
        linked_claims = {cid: kc2 for cid in {lk.claim_id for lk in store.links(v.thesis_id)}
                         | cited_ids if (kc2 := store.claim(cid)) is not None}
        unlinked = cited_ids - {lk.claim_id for lk in store.links(v.thesis_id)}
        if unlinked:
            label_bad.append(f"{v.thesis_id} v{v.version}: cites claim(s) the thesis does not "
                             f"link: {first_of(sorted(unlinked), 3, ', ')}")
        for sid, (text, prov, cids) in card_sentences(v.content).items():
            if prov in {p.value for p in SOURCE_LABELS} and prov != Provenance.ARTICLE_FACT.value:
                want = label_for(cids, linked_claims)
                if want is not None:  # a conditional line is at most SOURCE OPINION (cards)
                    want = capped_label(want, text)
                if want is not None and want.value != prov:
                    label_bad.append(f"{v.thesis_id} v{v.version} {sid}: {prov} but cites "
                                     f"{want.value}")
        for st in v.content.s03_transmission:
            if st.step in EARNINGS_STEPS and is_market_reaction(st.text):
                react_bad.append(f"{v.thesis_id} v{v.version} {st.step}: {st.text[:80]!r}")
        for co in v.content.s05_affected.companies:
            for ls in co.listings:
                filed = re.search(r"filed (\d{4}-\d{2}-\d{2})", ls.pit_source or "")
                if ls.pit_status is not PitStatus.VERIFIED or \
                        ls.instrument is not InstrumentClass.COMMON_EQUITY:
                    pit_bad.append(f"{v.thesis_id}: {co.name_as_written} {ls.ticker} "
                                   f"{ls.pit_status.value}/{ls.instrument.value}")
                elif filed is None or date.fromisoformat(filed.group(1)) > run.as_of:
                    pit_bad.append(f"{v.thesis_id}: {co.name_as_written} {ls.ticker} cover page "
                                   f"{ls.pit_source!r} not on or before {run.as_of}")
    add(QaCheck("source-labelled lines carry the weakest label of their claims", not label_bad,
                _fail_list(label_bad) or f"{len(versions)} version(s) checked"))
    add(QaCheck("no share-price / valuation move filed as an earnings step", not react_bad,
                _fail_list(react_bad) or "ok"))
    add(QaCheck("listed exposures are point-in-time-verified common equity", not pit_bad,
                _fail_list(pit_bad) or f"as of {run.as_of}"))

    # completeness ledgers and authors for every article this run analysed ------------------------
    no_ledger: list[str] = []
    open_figs: list[str] = []
    open_blocks: list[str] = []
    n_figs = 0
    no_author: list[str] = []
    for aid in article_ids:
        art = store.article(aid)
        if art is not None and art.authors_status is not FieldStatus.KNOWN:
            no_author.append(f"{aid} ({art.publisher})")
        for av in store.article_versions(aid):
            if av.retrieval_state.value == "BLOCKED" or not av.blocks:
                continue
            reps = [r for r in store.completeness(av.version_id) if r.run_id == run_id] or \
                store.completeness(av.version_id)
            if not reps:
                no_ledger.append(f"{aid} {av.version_id}")
                continue
            rep = reps[-1]
            n_figs += len(rep.figures)
            open_figs += [f"{aid} {f.block_id} {f.figure!r} [{f.open_cause or 'unclassified'}]"
                          for f in rep.uncaptured]
            open_blocks += [f"{aid} {b.block_id} [{b.open_cause or 'unclassified'}]"
                            for b in rep.unaccounted_blocks]
    add(QaCheck("completeness ledger recorded for every analysed article", not no_ledger,
                _fail_list(no_ledger) or f"{len(article_ids)} article(s)"))
    add(QaCheck("every reported figure captured or judged immaterial", not open_figs,
                (f"OPEN — {len(open_figs)} of {n_figs} figure(s): " + _fail_list(open_figs, 12))
                if open_figs else f"{n_figs} figure(s) accounted for"))
    add(QaCheck("every argument block accounted for", not open_blocks,
                (f"OPEN — {len(open_blocks)} block(s): " + _fail_list(open_blocks, 12))
                if open_blocks else "ok"))
    add(QaCheck("every analysed article names its author(s)", not no_author,
                _fail_list(no_author) or f"{len(article_ids)} article(s)"))

    # source health: a scan checks every channel it covers at its start (runs from schema v3) ---
    if run.mode == "scan" and run.db_schema_version >= 3:
        known = store.latest_health(until=run.finished_at or datetime.now(tz=UTC))
        unchecked = [sc.source_id for sc in run.sources if sc.source_id not in known]
        add(QaCheck("source health recorded for every scanned channel", not unchecked,
                    _fail_list(unchecked) or f"{len(run.sources)} channel(s)"))

    # append-only triggers ------------------------------------------------------------------------
    trig = {r[0] for r in store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'")}
    missing = [t for t in APPEND_ONLY_TABLES
               if f"{t}_no_update" not in trig or f"{t}_no_delete" not in trig]
    add(QaCheck("append-only triggers present", not missing,
                f"{len(APPEND_ONLY_TABLES)} history tables" + (f"; missing {missing}"
                                                                if missing else "")))

    # coverage (scan runs) ------------------------------------------------------------------------
    if run.mode == "scan":
        configured = {s.id for s in load_sources()}
        reported = {s.source_id for s in run.sources}
        cov_bad = [f"{sid}: not reported" for sid in sorted(configured - reported)]
        for sc in run.sources:
            if sc.in_window != sc.new + sc.already_known:
                cov_bad.append(f"{sc.source_id}: in_window {sc.in_window} != new {sc.new} + "
                               f"known {sc.already_known}")
            if sc.status in ("BLOCKED", "ERROR") and not sc.errors:
                cov_bad.append(f"{sc.source_id}: {sc.status} without a recorded reason")
        add(QaCheck("every configured source reported with consistent counts", not cov_bad,
                    _fail_list(cov_bad) or f"{len(reported)} sources"))

    # rendered outputs agree with the record ------------------------------------------------------
    out = Path(run.output_dir) if run.output_dir else None
    render_bad: list[str] = []
    titles = [t for _, t in SECTION_IDS]
    if out and (out / "cards").is_dir():
        for v in versions:
            cur = store.thesis(v.thesis_id)
            if cur is None or cur.current_version != v.version:
                continue  # superseded within the run — the files show the current version
            base = out / "cards" / v.thesis_id
            try:
                html_s = (base.with_suffix(".html")).read_text()
                md_s = (base.with_suffix(".md")).read_text()
                js = json.loads((base.with_suffix(".json")).read_text())
            except FileNotFoundError as exc:
                render_bad.append(f"{v.thesis_id}: missing {exc.filename}")
                continue
            if js.get("card") != json.loads(v.content.model_dump_json()):
                render_bad.append(f"{v.thesis_id}: JSON card differs from the stored version")
            if js.get("section_order") != [fid for fid, _ in SECTION_IDS]:
                render_bad.append(f"{v.thesis_id}: JSON section order")
            pos_h = [html_s.find(f'data-field="{fid}"') for fid, _ in SECTION_IDS]
            pos_m = [md_s.find(f"## {title}") for title in titles]
            if -1 in pos_h or pos_h != sorted(pos_h):
                render_bad.append(f"{v.thesis_id}: HTML section order {pos_h}")
            if -1 in pos_m or pos_m != sorted(pos_m):
                render_bad.append(f"{v.thesis_id}: Markdown section order")
            for r in v.content.s04_key_evidence:
                if r.claim_id not in html_s or r.claim_id not in md_s:
                    render_bad.append(f"{v.thesis_id}: {r.claim_id} missing from a render")
        add(QaCheck("HTML / Markdown / JSON agree with the stored card", not render_bad,
                    _fail_list(render_bad) or f"rendered cards in {out}"))
    else:
        add(QaCheck("HTML / Markdown / JSON agree with the stored card", False,
                    "no rendered cards found for this run — run `report --run` first"))
    return res

