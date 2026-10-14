"""Shared helpers for the theme-intelligence tests (not collected: no `test_` prefix).

Two kinds of fixture, never mixed up:
- AUTHENTIC — `tests/fixtures/theme_intelligence/jpm_software_shock/` and `jpm_calm_index/`: an
  excerpt of the real J.P. Morgan page (only the sentences the frozen outputs cite), the frozen
  pass-1 and pass-1b (completeness) model outputs, the full-article completeness ledger the real
  run persisted, and the real SEC data for the registrants it names — ticker-map rows, trimmed
  submissions and the inline-XBRL cover-page facts the point-in-time check reads. Replayed, never
  regenerated.
- HYPOTHETICAL — built here for the overlap / change-management tests. Every hypothetical article
  says so in its title and URL (`example.test/hypothetical/...`), and is built from the REAL
  extraction types (`Extraction` and friends), so a schema change breaks these fixtures loudly.
"""

from __future__ import annotations

import hashlib
import html
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.netcache import HttpError
from vinci.theme_intelligence.completeness import CompletenessOutput
from vinci.theme_intelligence.config import load_sources, load_taxonomy
from vinci.theme_intelligence.extract import Extraction
from vinci.theme_intelligence.fetch import FetchResult
from vinci.theme_intelligence.parse import ParsedDocument
from vinci.theme_intelligence.pipeline import ArticleResult, Pipeline
from vinci.theme_intelligence.schemas import (
    ArticleClass,
    Author,
    Block,
    FieldStatus,
    RetrievalState,
)
from vinci.theme_intelligence.securities import (
    SUBMISSIONS,
    TICKERS_EXCHANGE,
    TICKERS_MF,
    SecResolver,
)

FIXTURES = Path(__file__).parent / "fixtures" / "theme_intelligence"
JPM_DIR = FIXTURES / "jpm_software_shock"
CALM_DIR = FIXTURES / "jpm_calm_index"
JPM_URL = ("https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt/"
           "software-shock-ais-broken-logic")
CALM_URL = ("https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt/"
            "a-calm-index-a-restless-market")
JPM_AS_OF = date(2026, 2, 9)
CALM_AS_OF = date(2026, 10, 10)


# --- authentic fixtures ---

def load_document(fixture_dir: Path) -> ParsedDocument:
    d = json.loads((fixture_dir / "excerpt.json").read_text())
    return ParsedDocument(
        canonical_url=d["canonical_url"], title=d["title"], title_source=d["title_source"],
        authors=tuple(Author.model_validate(a) for a in d["authors"]),
        authors_status=FieldStatus.KNOWN if d["authors"] else FieldStatus.UNKNOWN,
        published_at=datetime.fromisoformat(d["published_at"]) if d["published_at"] else None,
        published_raw=d["published_raw"], published_source=d["published_source"],
        published_status=FieldStatus.KNOWN if d["published_at"] else FieldStatus.UNKNOWN,
        modified_at=None, modified_source=None,
        blocks=tuple(Block.model_validate(b) for b in d["blocks"]),
        retrieval_state=RetrievalState(d["provenance"]["retrieval_state"]),
        notes=["authentic excerpt fixture"],
        article_class_hint=(ArticleClass(d["article_class_hint"]) if d["article_class_hint"]
                            else None),
        article_class_basis=d["article_class_basis"],
        author_discrepancy=d.get("author_discrepancy"))


def frozen_output(fixture_dir: Path, name: str) -> dict[str, Any]:
    out: dict[str, Any] = json.loads((fixture_dir / name).read_text())["output"]
    return out


def jpm_document() -> ParsedDocument:
    return load_document(JPM_DIR)


def jpm_extraction() -> dict[str, Any]:
    return frozen_output(JPM_DIR, "extraction.json")


def jpm_completeness() -> dict[str, Any]:
    return frozen_output(JPM_DIR, "completeness.json")


def cover_html(lines: list[dict[str, Any]]) -> str:
    """An inline-XBRL cover page carrying exactly the frozen AUTHENTIC cover facts (one XBRL
    context per registered line, as the filings tag them)."""
    out = ["<html><body>"]
    for i, ln in enumerate(lines):
        for tag, key in (("dei:Security12bTitle", "title"), ("dei:TradingSymbol", "symbol"),
                         ("dei:SecurityExchangeName", "exchange")):
            if ln.get(key):
                out.append(f'<ix:nonNumeric contextRef="c-{i}" name="{tag}">'
                           f"{html.escape(str(ln[key]))}</ix:nonNumeric>")
    out.append("</body></html>")
    return "".join(out)


class FrozenSecHttp:
    """Serves AUTHENTIC SEC data in place of the network (same shapes as the live files): the
    ticker maps, each registrant's submissions (trimmed to periodic filings and 8-A12B
    registrations) and the cover-page facts of the filings the as-of dates select."""

    def __init__(self, *dirs: Path) -> None:
        self.ex: dict[str, Any] = {"fields": [], "data": []}
        self.mf: dict[str, Any] = {"fields": [], "data": []}
        self.subs: dict[str, Any] = {}
        self.covers: dict[str, Any] = {}
        for d in dirs or (JPM_DIR,):
            sec = json.loads((d / "sec_subset.json").read_text())
            self.ex["fields"] = sec["exchange"]["fields"]
            self.ex["data"] += [r for r in sec["exchange"]["data"] if r not in self.ex["data"]]
            self.mf["fields"] = sec["mf"]["fields"]
            self.mf["data"] += [r for r in sec["mf"]["data"] if r not in self.mf["data"]]
            self.subs.update(sec["submissions"])
            self.covers.update(sec["covers"])

    def get_json(self, url: str, ttl_seconds: float | None = None) -> Any:
        if url == TICKERS_EXCHANGE:
            return self.ex
        if url == TICKERS_MF:
            return self.mf
        for cik, sub in self.subs.items():
            if url == SUBMISSIONS.format(cik=cik):
                return {"filings": {"recent": sub, "files": []}}
        # not in the frozen subset: fail like the network would — the resolver then records
        # "point-in-time registration not verifiable" rather than this stub inventing one
        raise HttpError(f"not in the frozen SEC subset: {url}")

    def get_text(self, url: str, ttl_seconds: float | None = None) -> str:
        if url in self.covers:
            return cover_html(self.covers[url])
        raise HttpError(f"not in the frozen SEC subset: {url}")


# --- pipelines ---

def make_pipeline(tmp_path: Path, *, sources: tuple[Any, ...] | None = None,
                  sec_dirs: tuple[Path, ...] = (JPM_DIR,)) -> Pipeline:
    """An offline pipeline: no LLM client (extractions come from fixtures), no pass-2 LLM review,
    SEC resolution from the authentic frozen subset(s)."""
    http = FrozenSecHttp(*sec_dirs)
    resolver = SecResolver(tmp_path / "sec", http=http)  # type: ignore[arg-type]
    return Pipeline(tmp_path / "ti", sources=sources or load_sources(),
                    taxonomy=load_taxonomy(), client=None, resolver=resolver, review=False)


def fetched(doc: ParsedDocument, *, state: RetrievalState = RetrievalState.FULL) -> FetchResult:
    body = "\n".join(b.text for b in doc.blocks).encode()
    return FetchResult(url=doc.canonical_url, final_url=doc.canonical_url, status=200,
                       state=state, note="test fixture", content=body,
                       content_type="text/html", fetched_at=datetime.now(tz=UTC),
                       sha256=hashlib.sha256(body).hexdigest(), cache_path=None,
                       from_cache=False, seconds=0.0)


def ingest(pipe: Pipeline, doc: ParsedDocument, extraction: dict[str, Any], *, as_of: date,
           source_id: str = "manual", publisher: str | None = None,
           completeness: dict[str, Any] | None = None) -> ArticleResult:
    Extraction.model_validate(extraction)  # fixtures are the REAL type — fail loud on drift
    if completeness is not None:
        CompletenessOutput.model_validate(completeness)
    return pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id=source_id,
                                 as_of=as_of, fixture=extraction, publisher_override=publisher,
                                 completeness_fixture=completeness)


def ingest_jpm(pipe: Pipeline) -> ArticleResult:
    return ingest(pipe, jpm_document(), jpm_extraction(), as_of=JPM_AS_OF, source_id="jpm_tmt",
                  completeness=jpm_completeness())


def ingest_calm(pipe: Pipeline) -> ArticleResult:
    return ingest(pipe, load_document(CALM_DIR), frozen_output(CALM_DIR, "extraction.json"),
                  as_of=CALM_AS_OF, source_id="jpm_tmt",
                  completeness=frozen_output(CALM_DIR, "completeness.json"))


# --- hypothetical articles ---

@dataclass
class Hypo:
    """One HYPOTHETICAL article: blocks of authentic-looking but invented text, labelled as such."""

    slug: str
    publisher: str
    published: date | None
    blocks: list[tuple[str, str]]  # (kind, text)
    author: str | None = "Test Author"
    state: RetrievalState = RetrievalState.FULL

    @property
    def url(self) -> str:
        return f"https://example.test/hypothetical/{self.slug}"

    def doc(self) -> ParsedDocument:
        blocks = tuple(Block(block_id=f"b{i + 1:03d}", kind=k, text=t,
                             sha256=hashlib.sha256(t.encode()).hexdigest(), section=None,
                             order=i)
                       for i, (k, t) in enumerate(self.blocks))
        pub = (datetime(self.published.year, self.published.month, self.published.day, 9, 0,
                        tzinfo=UTC) if self.published else None)
        return ParsedDocument(
            canonical_url=self.url, title=f"[HYPOTHETICAL TEST FIXTURE] {self.slug}",
            title_source="test fixture",
            authors=(Author(name=self.author, title=None, source_field="test fixture"),)
            if self.author else (),
            authors_status=FieldStatus.KNOWN if self.author else FieldStatus.UNKNOWN,
            published_at=pub, published_raw=self.published.isoformat() if self.published else None,
            published_source="test fixture" if self.published else None,
            published_status=FieldStatus.KNOWN if self.published else FieldStatus.UNKNOWN,
            modified_at=None, modified_source=None, blocks=blocks, retrieval_state=self.state,
            notes=["HYPOTHETICAL test fixture"])


def claim(local_id: str, block: str, quote: str, statement: str, *, kind: str = "metric",
          epistemic: str = "actual", metric: str | None = None, value: float | None = None,
          value_text: str | None = None, unit: str | None = None, period: str | None = None,
          scope: str | None = None, source: str | None = None,
          measured_as_of: str | None = None, as_of_block: str | None = None) -> dict[str, Any]:
    return {"local_id": local_id, "block_id": block, "quote": quote, "statement": statement,
            "kind": kind, "epistemic": epistemic, "metric": metric, "value": value,
            "value_text": value_text, "unit": unit, "period": period, "scope": scope,
            "attributed_source": source, "measured_as_of": measured_as_of,
            "as_of_block_id": as_of_block, "confidence": "high"}


def mention(name: str, block: str, quote: str, *, entity_type: str = "company",
            role: str = "potential_beneficiary", direction: str = "positive",
            reco: str = "not_a_recommendation", ticker: str | None = None,
            issuer: str | None = None) -> dict[str, Any]:
    return {"name_as_written": name, "block_id": block, "quote": quote,
            "entity_type": entity_type, "role": role, "role_detail": f"{role} (test)",
            "direction": direction, "recommendation_status": reco, "ticker_hint": ticker,
            "issuer_name_hint": issuer}


def hyp(local_id: str, title: str, *, node: str, mechanism: str, direction: str = "positive",
        geography: str = "US", horizon: str = "next_2_4_quarters", stance: str = "asserted",
        supporting: list[str] | None = None, dislocation: list[str] | None = None,
        counter: list[str] | None = None, catalyst: list[str] | None = None,
        affected: list[tuple[str, str]] | None = None, premise: str | None = None,
        steps: bool = True, kind: str = "investment_thesis",
        sectors: list[tuple[str, str, str]] | None = None,
        step_list: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """`sectors`: (name, block id, verbatim quote) spans the source names as exposed."""
    sup = supporting or []
    chain = step_list if step_list is not None else (
        [{"step": "industry_shift", "text": "industry shift", "provenance": "model_inference"},
         {"step": "pricing", "text": "pricing moves", "provenance": "model_inference"}]
        if steps else [])
    return {
        "local_id": local_id, "title": title, "kind": kind, "value_chain_node": node,
        "mechanism": mechanism, "direction": direction, "geography": geography,
        "sectors": ["Test sector"],
        "horizon": horizon, "stance_in_source": stance, "premise_condition": premise,
        "bottom_line_fact": {"text": f"{title} (fact line)", "provenance": "source_stated",
                             "claim_ids": sup[:1]},
        "bottom_line_inference": {"text": f"{title} (inference line)",
                                  "provenance": "model_inference"},
        "transmission_chain": chain,
        "supporting_claim_ids": sup, "dislocation_claim_ids": dislocation or [],
        "counter_claim_ids": counter or [],
        "catalyst": {"window_text": "test window", "provenance": "model_inference",
                     "claim_ids": catalyst or []},
        "affected_mentions": [{"name_as_written": n, "role": r} for n, r in (affected or [])],
        "sector_exposures": [{"name": n, "direction": direction, "block_id": b, "quote": q,
                              "claim_ids": []} for n, b, q in (sectors or [])],
        "next_research_step": "check the next data point (test)",
        "unknowns": ["what the test does not establish"],
    }


def extraction(claims: list[dict[str, Any]], hyps: list[dict[str, Any]],
               mentions: list[dict[str, Any]] | None = None,
               risks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"article_classification": {"article_class": "publisher_commentary",
                                       "basis": "hypothetical test fixture"},
            "claims": claims, "mentions": mentions or [], "hypotheses": hyps,
            "market_risks": risks or []}


def table_counts(pipe: Pipeline) -> dict[str, int]:
    tables = [r[0] for r in pipe.store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('meta', 'runs', "
        "'llm_calls', 'candidates', 'verification_issues', 'snapshots')")]
    return {t: int(pipe.store.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
            for t in tables}
