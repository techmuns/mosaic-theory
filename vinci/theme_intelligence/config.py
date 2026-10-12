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
PARSER_VERSION = "ti-parse-6"  # 6: undecodable PDF glyphs quarantined
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

#: A supplied or linked DOCUMENT's model cost, estimated BEFORE any call from what the
#: completeness pass will have to review: at most ceil((stated figures + argument paragraphs) /
#: GAPS_PER_CALL) parts, each re-sending the whole text. Range per part (USD, list price) and
#: the fixed part (extraction + card reviews) — CALIBRATED on three real reports (2026-10-11,
#: claude-opus-4-8): Citi Gridlock 23 parts estimated / 22 run, $46.67; LatAm 11 / 10, $9.47;
#: ETF 8 / 7, $3.80. A face-validity cost constant, never tuned on research outcomes.
DOC_COST_PER_PART_USD = (0.4, 2.1)
DOC_COST_FIXED_USD = 2.0
#: a document whose HIGH estimate exceeds this is HELD (COST) until `--max-cost` raises it —
#: also for a linked report the scan would fetch automatically
DOC_COST_LIMIT_USD = 30.0
#: ACTUAL-spend limits checked before every paid call (budget.py): a weekly scan, a manual batch
#: (ingest-file / ingest-inbox / article), and — within a document's limit — the share its
#: retries and completeness passes may take. Face-validity constants; the CLI raises them.
SCAN_BUDGET_USD = 40.0
BATCH_BUDGET_USD = 100.0
DOC_RETRY_COMPLETENESS_SHARE = 0.85
#: a call's input is bounded at (characters / this) tokens — conservative for English prose and
#: tables (~3.5-4 characters per token measured); a bound from size, never a billing cap
CHARS_PER_TOKEN_BOUND = 2.5
#: the parts of a split completeness review send the article as a cached first block (llm.py) —
#: the same text, billed at a tenth after the first part. OFF until its evidence quality is shown
#: equivalent (brief, 2026-10-11). Measured on Citi's ETF report, one run each over the same
#: first-pass extraction: completeness cost $2.586 / $2.481 uncached (original / control) vs
#: $1.418 cached; open figures 1 / 0 vs 2 of 252, open paragraphs 0 in all; claims the pass added
#: 46 / 31 vs 26 — the cached run lowest, inside a spread the two uncached runs already show (15),
#: so neither equivalence nor harm is shown. An operator decision; see the 2026-10-11 record.
PROMPT_CACHE_PARTS = False


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
    #: a page that summarises a fuller report it LINKS to: "fetch" = read that report through
    #: the polite fetcher (robots obeyed; never an authenticated, paid or client-portal route)
    #: as a fuller VERSION of the same article, processed like the public page that links it;
    #: "request" = list it for an authorised upload (the default)
    linked_reports: str = "request"
    #: linked reports fetched per run for this channel — each is a long document (cost bound)
    max_linked_reports: int = 2
    #: "automatic" — discovered and read by every scan; "manual_first" — a lightweight health
    #: check only (no discovery, no retrieval attempt): its research arrives as authorised uploads
    mode: str = "automatic"


@dataclass(frozen=True)
class RetiredSource:
    """A channel removed from the active list: its history stays attributable; nothing new is
    discovered, checked, queued or imported from it."""

    id: str
    publisher: str
    retired: str
    reason: str
    hosts: tuple[str, ...] = ()


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


def load_retired_sources(path: Path | None = None) -> tuple[RetiredSource, ...]:
    raw = tomllib.loads((path or CONFIG_DIR / "sources.toml").read_text())
    try:
        return tuple(RetiredSource(id=str(r["id"]), publisher=str(r["publisher"]),
                                   retired=str(r["retired"]), reason=str(r["reason"]),
                                   hosts=tuple(str(h) for h in r.get("hosts", ())))
                     for r in raw.get("retired", []))
    except KeyError as exc:
        raise ConfigError(f"retired entry missing {exc}") from exc


def retired_for(source_id: str | None = None, url: str | None = None,
                path: Path | None = None) -> RetiredSource | None:
    """The retired channel a source id or a URL's host belongs to, if any."""
    from urllib.parse import urlparse

    host = (urlparse(url).hostname or "").lower() if url else ""
    for r in load_retired_sources(path):
        if source_id == r.id or (host and any(host == h or host.endswith("." + h)
                                              for h in r.hosts)):
            return r
    return None


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
                linked_reports=str(s.get("linked_reports", "request")),
                max_linked_reports=int(s.get("max_linked_reports", 2)),
                mode=str(s.get("mode", "automatic")),
            ))
        except KeyError as exc:
            raise ConfigError(f"source entry missing {exc}: {s}") from exc
    retired = {r.id for r in load_retired_sources(path)}
    for sc in out:
        if sc.id in retired:
            raise ConfigError(f"{sc.id} is both active and retired")
        if sc.mode not in ("automatic", "manual_first"):
            raise ConfigError(f"{sc.id}: mode must be automatic | manual_first")
        if sc.linked_reports not in ("fetch", "request"):
            raise ConfigError(f"{sc.id}: linked_reports must be fetch | request")
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
