"""SYNTHETIC multi-week registry for the research-desk stress test (2026-10-13) — NEVER the real
registry and never production state (not collected: no `test_` prefix).

Built through the REAL engine — verification, identity, priority, cards, archive pass — with
offline extraction fixtures (no model client, no network): weekly scans that read articles in
full or only as previews, fail or are blocked; manual uploads that are analysed or held; queued
candidates; weekly source-health checks; card-review findings. Every article says what it is in
its title ("[SYNTHETIC STRESS TEST] …") and URL (`https://example.test/synthetic-stress/…`).
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from tests.theme_intelligence_support import claim, extraction, fetched, hyp, make_pipeline
from vinci.theme_intelligence.config import load_sources
from vinci.theme_intelligence.documents import Declared
from vinci.theme_intelligence.ingest import ingest_file
from vinci.theme_intelligence.parse import ParsedDocument
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import (
    Author,
    Block,
    FieldStatus,
    Freshness,
    HealthStatus,
    IssueSeverity,
    RetrievalState,
    RunStatus,
    SourceHealthCheck,
    VerificationIssue,
)
from vinci.theme_intelligence.verify import card_sentences

SYNTH = "[SYNTHETIC STRESS TEST]"
_CONTEXT = ("The note reviews {subject} supply discipline in {geo}, {a}, and discusses how {b} "
            "could shape the coming quarters for buyers and suppliers of {subject} across the "
            "chain.")
_A = ("customer qualification cycles", "the pace of capacity additions", "channel inventory",
      "the order book of the largest buyers", "regional policy incentives", "logistics constraints")
_B = ("contract negotiations", "inventory positions", "allocation decisions", "pricing discipline",
      "capacity expansions", "procurement timing")
END = date(2026, 10, 12)

#: (taxonomy node, mechanism, subject) — one research key per row; the subject keeps a key's
#: articles on one product, so the engine updates ONE thesis instead of splitting it
KEYS: list[tuple[str, str, str]] = [
    (n, m, s)
    for n, subjects in (
        ("ai_infrastructure.memory", ("HBM", "DRAM contract", "NAND", "enterprise SSD")),
        ("ai_infrastructure.compute_semis", ("accelerator", "custom ASIC", "GPU server")),
        ("ai_infrastructure.optical_networking", ("800G transceiver", "co-packaged optics",
                                                  "switch silicon")),
        ("ai_infrastructure.power_grid", ("grid transformer", "gas turbine", "interconnection")),
        ("ai_infrastructure.datacenter_physical", ("liquid cooling", "rack power",
                                                   "datacenter lease")),
        ("ai_infrastructure.materials_commodities", ("copper", "specialty gas", "substrate")),
        ("ai_infrastructure.semicap_foundry", ("advanced packaging", "lithography tool",
                                               "foundry wafer")),
        ("ai_infrastructure.hyperscaler_capex", ("cloud capex", "AI capex")),
        ("software.application_saas", ("seat-based SaaS", "vertical SaaS")),
        ("software.infrastructure", ("observability software", "data platform")),
        ("electronic_components", ("MLCC", "connector")),
        ("consumer_electronics", ("AI PC", "smartphone")),
    )
    for s in subjects
    for m in ("pricing_cycle", "demand_volume_shift", "supply_constraint")
]
GEOS = ("Global", "US", "China", "Korea", "Taiwan", "Europe", "Japan")


@dataclass
class StressStats:
    weeks: int
    scans: list[str]
    articles: int
    uploads: int
    held: int
    queued: int


def _doc(slug: str, title: str, published: date, blocks: list[str],
         state: RetrievalState = RetrievalState.FULL) -> ParsedDocument:
    bl = tuple(Block(block_id=f"b{i + 1:03d}", kind="paragraph", text=t,
                     sha256=hashlib.sha256(t.encode()).hexdigest(), section=None, order=i)
               for i, t in enumerate(blocks))
    pub = datetime(published.year, published.month, published.day, 9, 0, tzinfo=UTC)
    return ParsedDocument(
        canonical_url=f"https://example.test/synthetic-stress/{slug}", title=f"{SYNTH} {title}",
        title_source="synthetic stress test",
        authors=(Author(name="Synthetic Author", title=None, source_field="synthetic"),),
        authors_status=FieldStatus.KNOWN, published_at=pub, published_raw=published.isoformat(),
        published_source="synthetic", published_status=FieldStatus.KNOWN, modified_at=None,
        modified_source=None, blocks=bl, retrieval_state=state, notes=["SYNTHETIC stress test"])


def _quarter_after(d: date, n: int) -> str:
    q = (d.month - 1) // 3 + n
    return f"{q % 4 + 1}Q{str(d.year + q // 4)[2:]}"


def _article(key: tuple[str, str, str, str], horizon: str, as_of: date, rng: random.Random,
             uncaptured: bool, tag: str) -> tuple[list[str], dict[str, Any], str]:
    """A data-report-shaped article (the pilot's TrendForce shape the tests pin): a dated price or
    volume forecast, the pricing / volumes step stated by the source, the subject named as the
    exposure. `horizon`: near (inside the next 4 quarters), straddle (next year's full year),
    long (beyond the horizon) or opinion (no material evidence)."""
    node, mech, subject, geo = key
    verb = "prices" if mech == "pricing_cycle" else "shipments" if mech == "demand_volume_shift" \
        else "capacity"
    if horizon == "opinion":
        text = f"Our analysts believe {subject} {verb} could improve as conditions normalise."
        x = extraction(
            [claim("c1", "b001", text.rstrip("."), f"{subject} {verb} may improve",
                   kind="assertion", epistemic="opinion", scope=subject)],
            [hyp("h1", f"{subject} {verb} may improve", node=node, mechanism=mech,
                 geography=geo, supporting=["c1"], sectors=[(subject, "b001", subject)])])
        title = f"{subject} ({geo}): {verb} commentary — {tag}"
    else:
        pct = rng.choice([8, 12, 15, 18, 22, 27, 31, 40, 55, 121])
        period = {"near": _quarter_after(as_of, 2), "straddle": str(as_of.year + 1),
                  "long": str(as_of.year + 4)}[horizon]
        text = (f"Our {subject} tracker projects blended {subject} {verb} to rise {pct}% YoY in "
                f"{period} as supply stays tight.")
        step = "pricing" if mech == "pricing_cycle" else "volumes"
        verb_s = {"prices": "rise", "shipments": "rise", "capacity": "stay constrained"}[verb]
        x = extraction(
            [claim("c1", "b001", text.split(" as ")[0], f"{subject} {verb} +{pct}% {period}",
                   kind="forecast", epistemic="forecast", metric=f"{subject} {verb} change",
                   value=pct, value_text=f"{pct}%", unit="% YoY", period=period, scope=subject)],
            [hyp("h1", f"{subject} {verb} {verb_s} in {geo}", node=node, mechanism=mech,
                 geography=geo, supporting=["c1"],
                 step_list=[{"step": step, "text": f"{subject} {verb} {verb_s}",
                             "provenance": "source_stated", "claim_ids": ["c1"]}],
                 sectors=[(subject, "b001", subject)])])
        title = f"{subject} ({geo}): {verb} outlook to {period} — {tag}"
    blocks = [text]
    if uncaptured:  # a figure the extraction did not capture — an open completeness item
        blocks.append(f"Inventory at {subject} suppliers stands at {rng.randint(3, 19)} weeks.")
    return blocks, x, title


def _shift_blocks(x: dict[str, Any]) -> dict[str, Any]:
    """The fixture's citations moved one block down (a heading line now comes first)."""
    def nxt(b: str) -> str:
        return f"b{int(b[1:]) + 1:03d}"

    for c in x["claims"]:
        c["block_id"] = nxt(c["block_id"])
    for h in x["hypotheses"]:
        for se in h.get("sector_exposures", []):
            se["block_id"] = nxt(se["block_id"])
    return x


def _new_key(rng: random.Random) -> tuple[str, str, str, str]:
    node, mech, subject = rng.choice(KEYS)
    return node, mech, subject, rng.choice(GEOS)


def _reviewer(run_id: str) -> Callable[..., list[VerificationIssue]]:
    """A deterministic card review: about a third of cards get one PARTIAL finding."""
    def review(card: Any, claims: Any) -> list[VerificationIssue]:
        tid = card.header.thesis_id
        if int(hashlib.sha256(f"{tid}{card.header.title}".encode()).hexdigest(), 16) % 3:
            return []
        text = card_sentences(card)["s01.0"][0]
        return [VerificationIssue(
            issue_id=f"VI-stress-{hashlib.sha256((run_id + tid + text).encode()).hexdigest()[:12]}",
            run_id=run_id, scope="card_sentence", ref_id=f"{tid}:s01.0",
            severity=IssueSeverity.WARN, code="REVIEW_PARTIAL",
            detail=f"s01.0: the cited span does not state the supply cause (synthetic) | "
                   f"{text[:100]!r}",
            created_at=datetime.now(tz=UTC))]
    return review


def build_stress_registry(root: Path, *, weeks: int, seed: int = 7, end: date = END,
                          per_week: tuple[int, int] = (14, 26)) -> tuple[Pipeline, StressStats]:
    """`weeks` SYNTHETIC weeks ending on `end`, built into a fresh registry under `root`."""
    if (root / "ti" / "registry.db").exists():
        raise FileExistsError(f"{root} already holds a registry — build into an empty directory")
    rng = random.Random(seed)
    pipe = make_pipeline(root)
    sources = {s.id: s for s in load_sources()}
    auto = [s for s in sources.values() if s.mode != "manual_first"]
    manual = [s for s in sources.values() if s.mode == "manual_first"]
    used: list[tuple[str, str, str, str]] = []
    scans: list[str] = []
    n_art = n_up = n_held = n_q = 0
    files = root / "uploads"
    files.mkdir(parents=True, exist_ok=True)
    empty: dict[str, Any] = {"figure_reviews": [], "block_reviews": []}
    for wi in range(weeks):
        as_of = end - timedelta(days=7 * (weeks - 1 - wi))
        w_from = as_of - timedelta(days=6)
        # 1. manual uploads before the scan: analysed reports, sometimes one held for licence;
        # every new card version is reviewed, as production reviews it
        up = pipe.start_run("ingest", as_of=as_of)
        pipe.engine.reviewer = _reviewer(up.run_id)
        for j in range(rng.choice([1, 2, 2, 3])):
            src = rng.choice(manual)
            key = rng.choice(used) if used and rng.random() < 0.5 else _new_key(rng)
            blocks, x, title = _article(key, rng.choice(["near", "straddle", "straddle"]),
                                        as_of, rng, uncaptured=False,
                                        tag=f"report W{wi + 1}.{j + 1}")
            held = rng.random() < 0.25
            path = files / f"synthetic-stress-w{wi:02d}-u{j}.txt"
            # the claim paragraph first (the fixture cites block b001), then context: a document
            # needs 40 words of body text to be read at all
            ctx = _CONTEXT.format(subject=key[2], geo=key[3], a=rng.choice(_A), b=rng.choice(_B))
            # a document's title is read from its first line: give each its own, and point the
            # fixture's citations at the paragraph below it
            head = f"[SYNTHETIC] {key[2]} {key[3]} {as_of:%d %B} {('alpha', 'beta', 'gamma')[j]}"
            path.write_text(head + "\n\n" + "\n\n".join(blocks) + "\n\n" + ctx + "\n")
            x = _shift_blocks(x)
            # one marker word, so a title's own words decide a match (the engine reviews a title
            # overlap from 50%)
            name = f"[SYNTHETIC] {key[2]} {key[3]} {as_of:%d %B} {('alpha', 'beta', 'gamma')[j]}"
            ingest_file(pipe, path, Declared(source_id=src.id, title=name,
                                             published=as_of - timedelta(days=rng.randint(0, 5)),
                                             llm_permitted=None if held else True),
                        as_of=as_of, fixture=x, completeness_fixture=empty)
            n_held += held
            n_up += not held
            if key not in used:
                used.append(key)
        pipe.finish_run(RunStatus.SUCCEEDED)
        # 2. the weekly scan: full reads, previews, a failure or a blocked page, the archive pass
        run = pipe.start_run("scan", as_of=as_of, window_from=w_from, window_to=as_of)
        scans.append(run.run_id)
        pipe.engine.reviewer = _reviewer(run.run_id)
        for k in range(rng.randint(*per_week)):
            src = rng.choice(auto)
            key = rng.choice(used) if used and rng.random() < 0.45 else _new_key(rng)
            horizon = rng.choices(["near", "straddle", "long", "opinion"],
                                  [0.07, 0.66, 0.12, 0.15])[0]
            if horizon == "near":
                src = sources["trendforce"]  # the inflection route needs a data report
            blocks, x, title = _article(key, horizon, as_of, rng, uncaptured=rng.random() < 0.2,
                                        tag=f"week {wi + 1} item {k + 1}")
            pub = as_of - timedelta(days=rng.randint(0, 6))
            state = RetrievalState.PARTIAL if rng.random() < 0.14 else RetrievalState.FULL
            doc = _doc(f"w{wi:02d}-a{k:02d}", title, pub, blocks, state)
            res = pipe.process_document(doc, fetched(doc, state=state), url=doc.canonical_url,
                                        source_id=src.id, as_of=as_of, fixture=x,
                                        publisher_override=src.publisher,
                                        completeness_fixture=empty)
            assert pipe.run is not None
            pipe.run.checkpoint[doc.canonical_url] = res.status
            n_art += 1
            if key not in used:
                used.append(key)
        assert pipe.run is not None
        for k in range(rng.choice([0, 1, 1, 2])):  # a fetch that failed or was blocked
            pipe.run.checkpoint[f"https://example.test/synthetic-stress/w{wi:02d}-f{k}"] = \
                rng.choice(["FAILED", "BLOCKED", "NO_BODY"])
        if wi == weeks - 1:  # discovered in the window, left for the next run by the budget cap
            for k in range(rng.randint(3, 7)):
                src = rng.choice(auto)
                pipe.store.upsert_candidate(
                    f"https://example.test/synthetic-stress/w{wi:02d}-q{k}", src.id, "QUEUED",
                    {"source_id": src.id, "title": f"{SYNTH} queued article {k + 1}",
                     "published": as_of.isoformat()})
                n_q += 1
            pipe.run.counts["articles_queued"] = n_q
        for s in sources.values():  # the week's source-health check, as a stored record
            st = (HealthStatus.BLOCKED if s.mode == "manual_first" else
                  rng.choices([HealthStatus.HEALTHY, HealthStatus.DEGRADED], [0.8, 0.2])[0])
            pipe.store.add_health_check(SourceHealthCheck(
                check_id=f"HC-stress-{s.id}-{wi}", source_id=s.id, publisher=s.publisher,
                checked_at=datetime(as_of.year, as_of.month, as_of.day, 3, 0, tzinfo=UTC),
                trigger="scan", run_id=run.run_id, status=st,
                reason=f"synthetic weekly check ({st.value.lower()})",
                next_action="upload manually" if st is not HealthStatus.HEALTHY else "none",
                freshness=Freshness.FRESH if st is HealthStatus.HEALTHY else Freshness.UNKNOWN,
                newest_article_date=as_of if st is HealthStatus.HEALTHY else None,
                window_from=w_from, window_to=as_of, expect_blocked=s.mode == "manual_first"))
        pipe.engine.reviewer = None
        pipe.engine.archive_pass(run_id=run.run_id, as_of=as_of)
        pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe, StressStats(weeks=weeks, scans=scans, articles=n_art, uploads=n_up,
                             held=n_held, queued=n_q)
