"""Pinned versions, paths and the two editable config files (sources, taxonomy).

PINNED, AND RECORDED ON EVERY OUTPUT. The model, the extraction / review prompt versions, the parser
version and the DB schema version are constants here and are written into every extraction, card
version and run manifest — a reader can always say which machinery produced a line.

WHY `claude-opus-4-8`. The brief requires the EXISTING configured LLM client
(`vinci.graph.llm.AnthropicLlmClient`). That client forces the tool call with
`tool_choice={"type": "tool"}`, which the newer Opus 5.5 / Fable 5.1 / Sonnet 5.5 models reject
with a 400; changing the shared client would touch every fund LLM phase (dossier synthesis, graph,
themes), which this package must not do. So the model is the repo's configured default, pinned here
explicitly so a change to `graph_llm_model` cannot silently re-point this package.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from vinci.config import sec_user_agent

PACKAGE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = PACKAGE_DIR / "config"

#: Working state — git-ignored (`data/*`). The DB, raw fetches, LLM caches and readouts live here.
DEFAULT_DATA_DIR = Path("data/theme_intelligence")

LLM_PROVIDER = "anthropic"
LLM_MODEL = "claude-opus-4-8"
#: Output-token cap per call. The shared client sends NON-streaming requests, and the Anthropic SDK
#: refuses a non-streaming request whose cap implies more than 10 minutes at its assumed 128k
#: tokens/hour — 21,333 tokens. The default 16,384 truncated the v6 extraction of a 3,000-word
#: SemiAnalysis post on 2026-10-10 (the run FAILED loudly, nothing partial kept). Billing is on
#: tokens actually produced, so the higher cap costs nothing on shorter outputs.
LLM_MAX_TOKENS = 21_333
EXTRACT_PROMPT_VERSION = "ti-extract-6"
COMPLETE_PROMPT_VERSION = "ti-complete-1"
REVIEW_PROMPT_VERSION = "ti-review-4"
PARSER_VERSION = "ti-parse-4"
ENGINE_VERSION = "ti-engine-2"

#: USD per million tokens (input, output) — Anthropic first-party list price as cached 2026-10-06.
#: Cache writes bill 1.25x input and cache reads 0.1x input. Used for the run manifest's cost line;
#: a model missing here makes the cost UNKNOWN, never zero.
PRICE_PER_MTOK: dict[str, tuple[float, float]] = {"claude-opus-4-8": (5.0, 25.0)}

#: Honest, identifying User-Agent. No browser spoofing: a site that refuses this is BLOCKED.
USER_AGENT = (f"mosaic-theory-theme-intelligence/0.1 (research scanner; "
              f"contact: {sec_user_agent().split()[-1]})")

#: The brief's default scan window and our own politeness floor between requests to one host.
DEFAULT_SCAN_DAYS = 10
DEFAULT_MIN_CRAWL_DELAY_S = 5.0

#: Budget caps. A cap is a TRUNCATION, and every truncation is printed with its population
#: ("processed X of Y in-window articles") — never a silent drop. Unprocessed candidates stay
#: QUEUED for the next run.
DEFAULT_MAX_ARTICLES_PER_RUN = 25
MAX_CLAIMS_PER_ARTICLE = 40

#: Archive rule (face validity, never outcome-tuned): a card's horizon is the next 2-4 quarters,
#: so a thesis with no material evidence for more than one quarter has lost its "why now" and
#: moves to the searchable archive (an ARCHIVED event the weekly report shows). New material
#: evidence re-activates it.
STALE_AFTER_DAYS = 91

#: THE RESEARCH HORIZON IN CALENDAR TERMS (face validity, never outcome-tuned). A card's horizon is
#: the next 2-4 quarters, so a forecast or dated event counts as near-term only when its window
#: STARTS within NEAR_TERM_START_DAYS of the as-of and ENDS within NEAR_TERM_END_DAYS — a calendar
#: year already under way qualifies, "2025-2031" never does merely because it is a forecast.
NEAR_TERM_START_DAYS = 366
NEAR_TERM_END_DAYS = 549
#: A MEASURED observation is current evidence when its data date (or, if the source states none,
#: the article's publication date) is at most one quarter before the as-of.
CURRENT_OBSERVATION_DAYS = 92

#: Weekly-dashboard display collapse per category. NOT a cut: the rest of the category sits one
#: click below, and the heading prints "showing X of Y".
DASHBOARD_ROWS_PER_CATEGORY = 12


@dataclass(frozen=True)
class SourceConfig:
    id: str
    publisher: str
    channel: str
    entry_url: str
    adapter: str
    reliability: str
    default_article_class: str
    min_crawl_delay_s: float
    sitemap_url: str | None = None
    listing_url: str | None = None
    link_pattern: str | None = None
    max_listing_pages: int = 1
    feed_url: str | None = None
    #: undated candidates whose page is fetched to read its own publication date, per run
    max_date_checks: int = 12
    #: a standing, documented access refusal: still attempted and reported BLOCKED every run, but
    #: it does not by itself turn the run PARTIAL (a NEW failure of any other channel does)
    expect_blocked: bool = False
    #: may a MANUALLY SUPPLIED document of this publisher be sent to the third-party LLM?
    #: permitted | not_permitted | unknown — anything but "permitted" HOLDS the document for
    #: review unless the operator states, for that document, that its licence allows it
    manual_llm_processing: str = "unknown"


@dataclass(frozen=True)
class TaxonomyItem:
    id: str
    label: str


@dataclass(frozen=True)
class Segment:
    """A segment within a node — identity read from the verbatim evidence (taxonomy.toml)."""

    node: str
    id: str
    label: str
    terms: tuple[str, ...]


@dataclass(frozen=True)
class Product:
    """A product within a node, for CLAIM-level comparison (taxonomy.toml `[[product]]`): a
    claim about HBM prices is not a claim about conventional DRAM prices. `covers` names the
    specific products a generic term spans ("DRAM" spans HBM and conventional DRAM) — a generic
    claim against one it covers is ambiguous, never assumed the same."""

    node: str
    id: str
    label: str
    terms: tuple[str, ...]
    covers: tuple[str, ...] = ()


@dataclass(frozen=True)
class Taxonomy:
    nodes: tuple[TaxonomyItem, ...]
    mechanisms: tuple[TaxonomyItem, ...]
    segments: tuple[Segment, ...] = ()
    products: tuple[Product, ...] = ()

    def products_of(self, node_id: str) -> tuple[Product, ...]:
        return tuple(p for p in self.products if p.node == node_id)

    def segments_of(self, node_id: str) -> tuple[Segment, ...]:
        return tuple(sg for sg in self.segments if sg.node == node_id)

    @property
    def node_ids(self) -> frozenset[str]:
        return frozenset(n.id for n in self.nodes)

    @property
    def mechanism_ids(self) -> frozenset[str]:
        return frozenset(m.id for m in self.mechanisms)

    def ancestry(self, node_id: str) -> tuple[str, ...]:
        """`ai_infrastructure.memory` → (`ai_infrastructure`, `ai_infrastructure.memory`)."""
        parts = node_id.split(".")
        return tuple(".".join(parts[: i + 1]) for i in range(len(parts)))


class ConfigError(ValueError):
    """An editable config file is malformed — refuse rather than guess."""


def load_sources(path: Path | None = None) -> tuple[SourceConfig, ...]:
    raw = tomllib.loads((path or CONFIG_DIR / "sources.toml").read_text())
    out: list[SourceConfig] = []
    for s in raw.get("source", []):
        try:
            out.append(SourceConfig(
                id=str(s["id"]), publisher=str(s["publisher"]), channel=str(s["channel"]),
                entry_url=str(s["entry_url"]), adapter=str(s["adapter"]),
                reliability=str(s["reliability"]),
                default_article_class=str(s["default_article_class"]),
                min_crawl_delay_s=float(s.get("min_crawl_delay_s", DEFAULT_MIN_CRAWL_DELAY_S)),
                sitemap_url=s.get("sitemap_url"), listing_url=s.get("listing_url"),
                link_pattern=s.get("link_pattern"),
                max_listing_pages=int(s.get("max_listing_pages", 1)),
                feed_url=s.get("feed_url"),
                max_date_checks=int(s.get("max_date_checks", 12)),
                expect_blocked=bool(s.get("expect_blocked", False)),
                manual_llm_processing=str(s.get("manual_llm_processing", "unknown")),
            ))
        except KeyError as exc:
            raise ConfigError(f"source entry missing {exc}: {s}") from exc
    for sc in out:
        if sc.manual_llm_processing not in ("permitted", "not_permitted", "unknown"):
            raise ConfigError(f"{sc.id}: manual_llm_processing must be permitted | "
                              f"not_permitted | unknown")
    ids = [s.id for s in out]
    if len(ids) != len(set(ids)):
        raise ConfigError(f"duplicate source ids: {ids}")
    for s in out:
        if s.reliability not in ("high", "medium", "low"):
            raise ConfigError(f"{s.id}: reliability {s.reliability!r} not in high|medium|low")
    return tuple(out)


def load_taxonomy(path: Path | None = None) -> Taxonomy:
    raw = tomllib.loads((path or CONFIG_DIR / "taxonomy.toml").read_text())
    nodes = tuple(TaxonomyItem(str(n["id"]), str(n["label"])) for n in raw.get("node", []))
    mechs = tuple(TaxonomyItem(str(m["id"]), str(m["label"])) for m in raw.get("mechanism", []))
    if "other" not in {n.id for n in nodes} or "other" not in {m.id for m in mechs}:
        raise ConfigError("taxonomy must define an `other` node and mechanism (the REVIEW route)")
    node_ids = {n.id for n in nodes}
    for n in nodes:
        parent = n.id.rsplit(".", 1)[0] if "." in n.id else None
        if parent and parent not in node_ids:
            raise ConfigError(f"node {n.id} has no parent node {parent}")
    segments = tuple(Segment(str(sg["node"]), str(sg["id"]), str(sg["label"]),
                             tuple(str(x) for x in sg["terms"]))
                     for sg in raw.get("segment", []))
    for sg in segments:
        if sg.node not in node_ids or not sg.terms or "+" in sg.id:
            raise ConfigError(f"segment {sg.id}: unknown node, no terms or a '+' in its id")
    products = tuple(Product(str(p["node"]), str(p["id"]), str(p["label"]),
                             tuple(str(x) for x in p["terms"]),
                             tuple(str(x) for x in p.get("covers", [])))
                     for p in raw.get("product", []))
    pids = {p.id for p in products}
    for p in products:
        if p.node not in node_ids or not p.terms or set(p.covers) - pids:
            raise ConfigError(f"product {p.id}: unknown node, no terms or an unknown covered id")
    return Taxonomy(nodes=nodes, mechanisms=mechs, segments=segments, products=products)


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def db(self) -> Path:
        return self.root / "registry.db"

    @property
    def raw(self) -> Path:
        return self.root / "raw"

    @property
    def llm_cache(self) -> Path:
        return self.root / "llm_cache"

    @property
    def http_cache(self) -> Path:
        return self.root / "http_cache"

    @property
    def runs(self) -> Path:
        return self.root / "runs"

    @property
    def backups(self) -> Path:
        return self.root / "backups"

    def ensure(self) -> None:
        for d in (self.root, self.raw, self.llm_cache, self.http_cache, self.runs, self.backups):
            d.mkdir(parents=True, exist_ok=True)
