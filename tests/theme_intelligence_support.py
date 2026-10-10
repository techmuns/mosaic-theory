"""Shared helpers for the theme-intelligence tests (not collected: no `test_` prefix).

Two kinds of fixture, never mixed up:
- AUTHENTIC — `tests/fixtures/theme_intelligence/jpm_software_shock/`: an excerpt of the real J.P.
  Morgan page (only the sentences the frozen extraction cites), the frozen pass-1 model output, and
  the real SEC rows for the registrants it names. Replayed, never regenerated.
- HYPOTHETICAL — built here for the overlap / change-management tests. Every hypothetical article
  says so in its title and URL (`example.test/hypothetical/...`), and is built from the REAL
  extraction types (`Extraction` and friends), so a schema change breaks these fixtures loudly.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.netcache import HttpError
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
JPM_URL = ("https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt/"
           "software-shock-ais-broken-logic")
JPM_AS_OF = date(2026, 2, 9)


# --- authentic JPM fixture -----------------------------------------------------------------------

def jpm_document() -> ParsedDocument:
    d = json.loads((JPM_DIR / "excerpt.json").read_text())
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
        article_class_basis=d["article_class_basis"])


def jpm_extraction() -> dict[str, Any]:
    out: dict[str, Any] = json.loads((JPM_DIR / "extraction.json").read_text())["output"]
    return out


class FrozenSecHttp:
    """Serves the AUTHENTIC SEC subset in place of the network (same shapes as the live files)."""

    def __init__(self) -> None:
        self.sec = json.loads((JPM_DIR / "sec_subset.json").read_text())

    def get_json(self, url: str, ttl_seconds: float | None = None) -> Any:
        if url == TICKERS_EXCHANGE:
            return self.sec["exchange"]
        if url == TICKERS_MF:
            return self.sec["mf"]
        for cik, forms in self.sec["submission_forms"].items():
            if url == SUBMISSIONS.format(cik=cik):
                return {"filings": {"recent": {"form": forms}}}
        # not in the frozen subset: fail like the network would — the resolver then records
        # "foreign-issuer check unavailable" rather than this stub inventing a filer type
        raise HttpError(f"not in the frozen SEC subset: {url}")


# --- pipelines -----------------------------------------------------------------------------------

def make_pipeline(tmp_path: Path, *, sources: tuple[Any, ...] | None = None) -> Pipeline:
    """An offline pipeline: no LLM client (extractions come from fixtures), no pass-2 LLM review,
    SEC resolution from the authentic frozen subset."""
    resolver = SecResolver(tmp_path / "sec", http=FrozenSecHttp())
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
           source_id: str = "manual", publisher: str | None = None) -> ArticleResult:
    Extraction.model_validate(extraction)  # fixtures are the REAL type — fail loud on drift
    return pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id=source_id,
                                 as_of=as_of, fixture=extraction, publisher_override=publisher)


def ingest_jpm(pipe: Pipeline) -> ArticleResult:
    return ingest(pipe, jpm_document(), jpm_extraction(), as_of=JPM_AS_OF, source_id="jpm_tmt")


# --- hypothetical articles -----------------------------------------------------------------------

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
        steps: bool = True) -> dict[str, Any]:
    sup = supporting or []
    return {
        "local_id": local_id, "title": title, "value_chain_node": node, "mechanism": mechanism,
        "direction": direction, "geography": geography, "sectors": ["Test sector"],
        "horizon": horizon, "stance_in_source": stance, "premise_condition": premise,
        "bottom_line_fact": {"text": f"{title} (fact line)", "provenance": "article_fact",
                             "claim_ids": sup[:1]},
        "bottom_line_inference": {"text": f"{title} (inference line)",
                                  "provenance": "model_inference"},
        "transmission_chain": ([{"step": "industry_shift", "text": "industry shift",
                                 "provenance": "model_inference"},
                                {"step": "pricing", "text": "pricing moves",
                                 "provenance": "model_inference"}] if steps else []),
        "supporting_claim_ids": sup, "dislocation_claim_ids": dislocation or [],
        "counter_claim_ids": counter or [],
        "catalyst": {"window_text": "test window", "provenance": "model_inference",
                     "claim_ids": catalyst or []},
        "affected_mentions": [{"name_as_written": n, "role": r} for n, r in (affected or [])],
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
