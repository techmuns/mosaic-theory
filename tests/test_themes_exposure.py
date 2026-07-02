"""Regression tests for the SEMANTIC-PRIMARY exposure classifier (now theme-parameterized).

Offline / synthetic (a mock LLM). Pins the load-bearing behaviour: the exposure_basis is DERIVED
from CITED + GROUNDED facts (an uncited or fact-text-ungrounded 'binding' fact cannot credit it —
fail-closed); the DRIVER-TIE gate caps a terms-binding-but-indirect fact to committed and a
not-driver fact to aspirational (neither REAL), while an ANONYMIZED-but-driver-specific fact stays
REAL (anonymity is never penalized); a mention/intent is NOT real exposure; an empty stream fails
loud; directional language is flagged; the efts parser fails loud; and the assessment schema cannot
conclude. Plus the multi-theme refactor: the classifier runs on ANY DriverSpec with NO AI-datacenter
strings leaking in; AI-datacenter's prompt reproduces its old load-bearing content minus the dropped
"~50%"; and the fact-text cite-check fails loud on ungrounded facts.
"""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from vinci.graph.llm import LlmClient
from vinci.netcache import CachedHttp, HttpError
from vinci.themes.drivers import AI_DATACENTER
from vinci.themes.exposure import (
    assess_exposure,
    grade_driving_fact,
    is_real_exposure,
    mention_prefilter,
    parse_efts_ciks,
    provenance_tag_of,
)
from vinci.themes.schemas import DriverSpec, ExposureAssessment, ExposureBasis, ExposureFact

_STREAM = [
    ("8-K 2026-01-15 (acc A1)", "On January 10, 2026 ..."),
    ("10-K 2025-11-01 (acc A2)", "Our business ..."),
]

# a DEMAND-shaped toy theme — deliberately NOT a value chain: no layers, non-chain prefilter terms.
# Used to prove the classifier is driver-AGNOSTIC (no AI-datacenter leakage).
TOY_SPEC = DriverSpec(
    key="toy-obesity-demand",
    description="the GLP-1 obesity-drug DEMAND wave — makers/suppliers of GLP-1 therapies.",
    tie_taxonomy="driver-specific = a named GLP-1 asset (a molecule, a fill-finish contract). "
    "indirect = generic pharma capacity. not-driver = a non-obesity indication.",
    prefilter_terms=("GLP-1", "obesity", "semaglutide", "incretin"),
    provenance_tags=(),  # a demand-shaped theme has no value-chain layers
)


class _MockLlm(LlmClient):
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.last_system = ""
        self.last_user = ""
        self.last_tool: dict[str, Any] = {}

    @property
    def model(self) -> str:
        return "mock-model"

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        self.last_system, self.last_user, self.last_tool = system, user, tool
        return self._payload


def test_basis_derived_from_cited_binding_fact() -> None:
    payload = {
        "disclosed_facts": [
            {"fact": "15-year lease with AWS for ~300 MW of data center capacity",
             "concreteness": "binding-contract", "driver_tie": "driver-specific",
             "source_ref": "8-K 2026-01-15 (acc A1)"},
            {"fact": "exploring further AI strategy", "concreteness": "stated-intent",
             "driver_tie": "driver-specific", "source_ref": "10-K 2025-11-01 (acc A2)"},
        ],
        "primary_business": "datacenter HPC host transitioning from bitcoin mining",
        "key_unknowns": ["contract dollar revenue not disclosed"],
    }
    a = assess_exposure(AI_DATACENTER, "CIFR", "1819989", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.BINDING_CONTRACTS  # derived from the max cited fact
    assert is_real_exposure(a)
    assert a.flags == []  # all cited, no directional language


def test_uncited_binding_fact_cannot_credit_basis() -> None:
    """An uncited 'binding' fact is fail-closed to NONE — the detector never credits a fabricated
    exposure (the source-binding discipline; mirrors synthesis.py's cite-check)."""
    payload = {
        "disclosed_facts": [
            {"fact": "binding AWS hyperscaler deal", "concreteness": "binding-contract",
             "driver_tie": "driver-specific",
             "source_ref": "8-K 2099-01-01 (accession FABRICATED)"},
        ],
        "primary_business": "miner", "key_unknowns": [],
    }
    a = assess_exposure(AI_DATACENTER, "X", "1", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.NONE_DISCLOSED
    assert not is_real_exposure(a)
    assert any("UNCITED" in f for f in a.flags)


def test_mention_only_is_aspirational_not_real() -> None:
    """The Part-6 discriminator: a tenant-less 'SVP of AI Data Centers' / 'exploring' is intent, NOT
    exposure — basis ASPIRATIONAL, is_real False (so it is NOT a false positive in the count)."""
    payload = {
        "disclosed_facts": [
            {"fact": "appointed an SVP of AI Data Centers; exploring opportunities",
             "concreteness": "stated-intent", "driver_tie": "driver-specific",
             "source_ref": "10-K 2025-11-01 (acc A2)"},
        ],
        "primary_business": "bitcoin mining data center operator",
        "key_unknowns": ["no named AI tenant or contracted capacity disclosed"],
    }
    a = assess_exposure(AI_DATACENTER, "CLSK", "827876", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.ASPIRATIONAL
    assert not is_real_exposure(a)


def test_empty_stream_fails_loud() -> None:
    a = assess_exposure(AI_DATACENTER, "X", "1", [], llm=_MockLlm({}))
    assert a.exposure_basis is ExposureBasis.NONE_DISCLOSED
    assert a.disclosed_facts == []
    assert any("no recent filings" in f for f in a.flags)


def test_directional_language_flagged_but_still_assembled() -> None:
    payload = {
        "disclosed_facts": [
            {"fact": "well-positioned to win; a quantified share of revenue from HBM/advanced "
                     "packaging", "concreteness": "quantified-revenue",
             "driver_tie": "driver-specific", "source_ref": "10-K 2025-11-01 (acc A2)"},
        ],
        "primary_business": "an undervalued metrology leader", "key_unknowns": [],
    }
    a = assess_exposure(AI_DATACENTER, "CAMT", "1109138", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.QUANTIFIED_REVENUE  # cited quantified fact credits
    assert any("DIRECTIONAL" in f for f in a.flags)  # 'well-positioned to win' + 'undervalued'


def test_driver_tie_indirect_caps_binding_to_committed() -> None:
    """FCEL error-mode: a terms-BINDING contract with only an INDIRECT tie is NOT real — the
    driver-tie gate caps it at committed-capacity — independent of the binding terms."""
    payload = {"disclosed_facts": [
        {"fact": "binding CEPA: up to 380 MW carbonate fuel cells for data center applications",
         "concreteness": "binding-contract", "driver_tie": "indirect",
         "source_ref": "8-K 2026-01-15 (acc A1)"}],
        "primary_business": "fuel-cell maker", "key_unknowns": []}
    a = assess_exposure(AI_DATACENTER, "FCEL", "886128", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.COMMITTED_CAPACITY  # capped by the indirect tie
    assert not is_real_exposure(a)


def test_driver_tie_not_driver_caps_to_aspirational() -> None:
    """HIMX error-mode: even a strong fact tied to an adjacent-but-distinct market (edge/on-device
    AI) is capped to stated-intent — not-driver is not exposure to THIS driver."""
    payload = {"disclosed_facts": [
        {"fact": "image-sensor ICs for edge/on-device AI and the broad AI market",
         "concreteness": "quantified-revenue", "driver_tie": "not-driver",
         "source_ref": "10-K 2025-11-01 (acc A2)"}],
        "primary_business": "display-driver IC maker", "key_unknowns": []}
    a = assess_exposure(AI_DATACENTER, "HIMX", "1342338", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.ASPIRATIONAL  # capped by the not-driver tie
    assert not is_real_exposure(a)


def test_anonymized_but_binding_driver_specific_stays_real() -> None:
    """TSSI/WYFI: an ANONYMIZED counterparty with BINDING terms + a driver-specific tie stays REAL —
    the grader penalizes deferred TERMS, never customer anonymity (no named-customer rule)."""
    payload = {"disclosed_facts": [
        {"fact": "long-term agreement with its largest (unnamed) OEM customer: systems integration "
                 "for AI-enabled GPU racks at a minimum monthly volume with make-whole terms",
         "concreteness": "binding-contract", "driver_tie": "driver-specific",
         "source_ref": "8-K 2026-01-15 (acc A1)"}],
        "primary_business": "AI-rack integration services", "key_unknowns": []}
    a = assess_exposure(AI_DATACENTER, "TSSI", "1320760", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.BINDING_CONTRACTS  # anonymity is not penalized
    assert is_real_exposure(a)


def test_missing_driver_tie_defaults_conservative() -> None:
    """Fail-closed: a fact with NO driver_tie defaults to INDIRECT — a binding fact without an
    explicit driver-specific tie is capped at committed-capacity, never silently REAL."""
    payload = {"disclosed_facts": [
        {"fact": "binding data-center power supply agreement", "concreteness": "binding-contract",
         "source_ref": "8-K 2026-01-15 (acc A1)"}],  # no driver_tie key
        "primary_business": "x", "key_unknowns": []}
    a = assess_exposure(AI_DATACENTER, "X", "1", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.COMMITTED_CAPACITY
    assert not is_real_exposure(a)


def test_parse_efts_ciks_fails_loud_on_throttle_body() -> None:
    with pytest.raises(HttpError):
        parse_efts_ciks({"message": "throttled"})


def test_parse_efts_ciks_pads_and_counts() -> None:
    data = {"hits": {"total": {"value": 3},
                     "hits": [{"_source": {"ciks": ["1819989"]}},
                              {"_source": {"ciks": ["827876"]}}]}}
    ciks, total = parse_efts_ciks(data)
    assert ciks == ["0001819989", "0000827876"]
    assert total == 3


def test_exposure_schema_cannot_conclude() -> None:
    forbidden = ("verdict", "recommendation", "buy", "sell", "avoid", "score", "rank", "priority",
                 "decision", "conclude", "target")
    fields = set(ExposureAssessment.model_fields) | set(ExposureFact.model_fields)
    assert fields
    for n in fields:
        for tok in forbidden:
            assert tok not in n.lower(), f"field {n!r} smuggles a conclusion ({tok})"


# ------------------------------------------------------------------------------------------------
# The UNIVERSE-SCAN path (pre-filter resilience + provenance)
# ------------------------------------------------------------------------------------------------
class _FakeEfts:
    """A minimal efts double: raises on any URL containing ``fail_substr`` (a chosen phrase), else
    returns one in-batch hit for CIK 1. Duck-typed to CachedHttp (only ``get_json`` is used)."""

    def __init__(self, fail_substr: str | None = None) -> None:
        self.fail_substr = fail_substr
        self.calls = 0

    def get_json(self, url: str, *, ttl_seconds: int = 0) -> dict[str, Any]:
        self.calls += 1
        if self.fail_substr and self.fail_substr in url:
            raise HttpError("simulated transient efts error")
        return {"hits": {"total": {"value": 1}, "hits": [{"_source": {"ciks": ["1"]}}]}}


def test_mention_prefilter_skip_errors_continues() -> None:
    """A universe-scale scan WILL hit transient efts errors; skip_errors=True skips the erroring
    batch×phrase and keeps scanning (a conservative recall gap, never a fabricated mention)."""
    efts = cast(CachedHttp, _FakeEfts(fail_substr="thermal"))  # 'thermal management' phrase errors
    matched = mention_prefilter(efts, ["0000000001"], ("data center", "thermal management"),
                                startdt="2025-09-01", enddt="2026-06-30", skip_errors=True)
    assert matched == {"0000000001": {"data center"}}  # good phrase kept, erroring one skipped


def test_mention_prefilter_fail_loud_by_default() -> None:
    """Default is fail-loud: a bad efts body/throttle raises, not a false 'no mentions'."""
    efts = cast(CachedHttp, _FakeEfts(fail_substr="thermal"))
    with pytest.raises(HttpError):
        mention_prefilter(efts, ["0000000001"], ("thermal management",),
                          startdt="2025-09-01", enddt="2026-06-30")


def test_provenance_tag_of_tags_by_spec() -> None:
    """The provenance tag: which of the SPEC's tags a fact names (most-specific first; a keyword
    read for by-tag volume, not a grade). AI-datacenter supplies value-chain layers; a theme with no
    tags yields 'unspecified'."""
    lyr = AI_DATACENTER.provenance_tags
    assert provenance_tag_of("~50% of revenue from HBM and advanced packaging", lyr) == "HBM/memory"
    assert provenance_tag_of("liquid cooling systems for data centers", lyr) == "thermal/cooling"
    assert provenance_tag_of("switchgear and data center power", lyr) == "power/electrical"
    assert provenance_tag_of("silicon photonics modules", lyr) == "optical/interconnect"
    assert provenance_tag_of("colocation data-center campus operator", lyr) == "colocation/operator"
    assert provenance_tag_of("we design GPUs and accelerators", lyr) == "chips/GPU"
    assert provenance_tag_of("GPU-as-a-service neocloud platform", lyr) == "AI-cloud"
    assert provenance_tag_of("we sell industrial floor paint", lyr) == "unspecified"
    assert provenance_tag_of("GLP-1 semaglutide demand", ()) == "unspecified"  # no tags


def test_grade_driving_fact_returns_basis_setter() -> None:
    """The human's first-read provenance is the fact that SET the basis (max effective rank) — the
    binding lease, not the co-listed 'exploring' intent."""
    payload = {"disclosed_facts": [
        {"fact": "exploring AI opportunities", "concreteness": "stated-intent",
         "driver_tie": "driver-specific", "source_ref": "10-K 2025-11-01 (acc A2)"},
        {"fact": "15-year 300 MW lease with a hyperscaler", "concreteness": "binding-contract",
         "driver_tie": "driver-specific", "source_ref": "8-K 2026-01-15 (acc A1)"}],
        "primary_business": "x", "key_unknowns": []}
    a = assess_exposure(AI_DATACENTER, "X", "1", _STREAM, llm=_MockLlm(payload))
    f = grade_driving_fact(a)
    assert f is not None and f.concreteness.value == "binding-contract"


def test_grade_driving_fact_none_when_no_exposure() -> None:
    a = assess_exposure(AI_DATACENTER, "X", "1", [], llm=_MockLlm({}))
    assert grade_driving_fact(a) is None


# ------------------------------------------------------------------------------------------------
# Multi-theme refactor — parameterization, prompt-equivalence regression, fact-text cite-check
# ------------------------------------------------------------------------------------------------
def test_classifier_is_driver_agnostic_no_ai_datacenter_leak() -> None:
    """A NON-chain theme (TOY_SPEC) runs through the SAME classifier with NO AI-datacenter strings
    leaking into the prompt — the driver-specific content comes only from the spec. The generic
    system prompt + tool carry no theme; the user message carries only TOY_SPEC's driver."""
    mock = _MockLlm({"disclosed_facts": [], "primary_business": "x", "key_unknowns": []})
    assess_exposure(TOY_SPEC, "TOY", "1", _STREAM, llm=mock)
    prompt = mock.last_system + "\n" + mock.last_user + "\n" + json.dumps(mock.last_tool)
    low = prompt.lower()
    for leak in ("ai-datacenter", "value chain", "hbm", "advanced packaging", "hyperscaler",
                 "colocation", "chain-layer"):
        assert leak not in low, f"AI-datacenter leaked into a non-AI-datacenter prompt: {leak!r}"
    assert "glp-1" in low and "obesity" in low  # the toy driver IS present
    assert "driver-specific" in json.dumps(mock.last_tool)  # generic tie value, not chain-specific


def test_ai_datacenter_prompt_reproduces_load_bearing_content_minus_50pct() -> None:
    """Behavior-preservation regression: the AI-datacenter path (generic system + spec-in-user +
    tool) still carries EVERY load-bearing instruction the old hardcoded prompt had — the type-
    appropriate concreteness rules AND each value-chain layer + the not-driver / upstream scope —
    the ONLY deliberate change being that the CAMT-specific '~50%' example is GONE."""
    mock = _MockLlm({"disclosed_facts": [], "primary_business": "x", "key_unknowns": []})
    assess_exposure(AI_DATACENTER, "X", "1", _STREAM, llm=mock)
    prompt = mock.last_system + "\n" + mock.last_user + "\n" + json.dumps(mock.last_tool)
    low = prompt.lower()
    # the general type-appropriate concreteness rules (unchanged)
    for phrase in ("binding-contract", "make-whole", "take-or-pay", "subject to further agreement",
                   "backstop", "quantified", "blended", "committed-capacity", "anonymized"):
        assert phrase in low, f"lost a concreteness rule: {phrase!r}"
    # the AI-datacenter driver-tie taxonomy (relocated to the spec, still present)
    for phrase in ("hbm", "advanced packaging", "thermal", "optical", "colocation", "ai-cloud",
                   "gpu", "upstream enablers", "edge/on-device", "broad ai market", "indirect"):
        assert phrase in low, f"lost an AI-datacenter tie element: {phrase!r}"
    assert "~50%" not in prompt  # the deliberate drop (a CAMT-specific number, must not generalize)


def test_fact_text_grounding_fails_loud_on_ungrounded() -> None:
    """The fact-text cite-check (multi-theme scale can't hand-check): a fact citing a REAL accession
    whose load-bearing claim is NOT in that filing is UNGROUNDED → fail-closed to NONE, flagged —
    catching the audit's fact/accession-mismatch mode (a fabricated fact + a real accession)."""
    ref = "8-K 2026-01-15 (accession 0001628280-26-013305)"
    stream = [(ref, "The Company explores general opportunities across various end markets.")]
    payload = {"disclosed_facts": [
        {"fact": "binding $500 million contract with Zephyr Corporation for 400 MW of capacity",
         "concreteness": "binding-contract", "driver_tie": "driver-specific", "source_ref": ref}],
        "primary_business": "x", "key_unknowns": []}
    a = assess_exposure(AI_DATACENTER, "X", "1", stream, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.NONE_DISCLOSED  # ungrounded → cannot credit
    assert any("UNGROUNDED" in f for f in a.flags)


def test_fact_text_grounding_passes_when_grounded() -> None:
    """The counterpart: a fact whose claim IS in the cited filing credits the basis normally."""
    ref = "8-K 2026-01-15 (accession 0001628280-26-013305)"
    stream = [(ref, "The Company signed a binding agreement with Zephyr Corporation for 400 MW.")]
    payload = {"disclosed_facts": [
        {"fact": "binding agreement with Zephyr Corporation for 400 MW",
         "concreteness": "binding-contract", "driver_tie": "driver-specific", "source_ref": ref}],
        "primary_business": "x", "key_unknowns": []}
    a = assess_exposure(AI_DATACENTER, "X", "1", stream, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.BINDING_CONTRACTS  # grounded → credits
    assert not any("UNGROUNDED" in f for f in a.flags)


def test_ai_datacenter_spec_covers_the_chain() -> None:
    """AI-datacenter is one DriverSpec instance: its description spans the value chain (upstream
    enablers in scope) and its prefilter carries the chain vocabulary — not just 'AI'."""
    d = AI_DATACENTER.description.lower() + " " + AI_DATACENTER.tie_taxonomy.lower()
    for layer in ("hbm", "packaging", "cooling", "power", "optical", "colocation", "cloud"):
        assert layer in d, f"driver spec missing chain layer: {layer}"
    assert "upstream enablers" in d
    joined = " ".join(AI_DATACENTER.prefilter_terms).lower()
    for term in ("data center", "liquid cooling", "optical interconnect", "high bandwidth memory"):
        assert term in joined, f"pre-filter missing chain vocabulary: {term}"
