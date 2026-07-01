"""Regression tests for Stage 3 build 1 — the semantic-primary exposure detector.

Offline / synthetic (a mock LLM). Pins the load-bearing behaviour: the exposure_basis is DERIVED
from CITED facts (an uncited 'binding' fact cannot credit it — fail-closed); the DRIVER-TIE gate
caps a terms-binding-but-indirect fact to committed and a not-driver fact to aspirational (neither
REAL), while an ANONYMIZED-but-binding chain-specific fact stays REAL (anonymity is never
penalized); a mention/intent is NOT real exposure; an empty stream fails loud; directional language
is flagged; the efts parser fails loud; and the assessment schema cannot conclude.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from vinci.graph.llm import LlmClient
from vinci.netcache import CachedHttp, HttpError
from vinci.themes.exposure import (
    AI_DATACENTER_DRIVER,
    DRIVER_PHRASES,
    assess_exposure,
    chain_layer_of,
    grade_driving_fact,
    is_real_exposure,
    mention_prefilter,
    parse_efts_ciks,
)
from vinci.themes.schemas import ExposureAssessment, ExposureBasis, ExposureFact

_STREAM = [
    ("8-K 2026-01-15 (acc A1)", "On January 10, 2026 ..."),
    ("10-K 2025-11-01 (acc A2)", "Our business ..."),
]


class _MockLlm(LlmClient):
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    @property
    def model(self) -> str:
        return "mock-model"

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        return self._payload


def test_basis_derived_from_cited_binding_fact() -> None:
    payload = {
        "disclosed_facts": [
            {"fact": "15-year lease with AWS for ~300 MW of data center capacity",
             "concreteness": "binding-contract", "driver_tie": "chain-layer-specific",
             "source_ref": "8-K 2026-01-15 (acc A1)"},
            {"fact": "exploring further AI strategy", "concreteness": "stated-intent",
             "driver_tie": "chain-layer-specific", "source_ref": "10-K 2025-11-01 (acc A2)"},
        ],
        "primary_business": "datacenter HPC host transitioning from bitcoin mining",
        "key_unknowns": ["contract dollar revenue not disclosed"],
    }
    a = assess_exposure("CIFR", "1819989", "AI-datacenter", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.BINDING_CONTRACTS  # derived from the max cited fact
    assert is_real_exposure(a)
    assert a.flags == []  # all cited, no directional language


def test_uncited_binding_fact_cannot_credit_basis() -> None:
    """An uncited 'binding' fact is fail-closed to NONE — the detector never credits a fabricated
    exposure (the source-binding discipline; mirrors synthesis.py's cite-check)."""
    payload = {
        "disclosed_facts": [
            {"fact": "binding AWS hyperscaler deal", "concreteness": "binding-contract",
             "driver_tie": "chain-layer-specific",
             "source_ref": "8-K 2099-01-01 (accession FABRICATED)"},
        ],
        "primary_business": "miner", "key_unknowns": [],
    }
    a = assess_exposure("X", "1", "AI-datacenter", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.NONE_DISCLOSED
    assert not is_real_exposure(a)
    assert any("UNCITED" in f for f in a.flags)


def test_mention_only_is_aspirational_not_real() -> None:
    """The Part-6 discriminator: a tenant-less 'SVP of AI Data Centers' / 'exploring' is intent, NOT
    exposure — basis ASPIRATIONAL, is_real False (so it is NOT a false positive in the count)."""
    payload = {
        "disclosed_facts": [
            {"fact": "appointed an SVP of AI Data Centers; exploring opportunities",
             "concreteness": "stated-intent", "driver_tie": "chain-layer-specific",
             "source_ref": "10-K 2025-11-01 (acc A2)"},
        ],
        "primary_business": "bitcoin mining data center operator",
        "key_unknowns": ["no named AI tenant or contracted capacity disclosed"],
    }
    a = assess_exposure("CLSK", "827876", "AI-datacenter", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.ASPIRATIONAL
    assert not is_real_exposure(a)


def test_empty_stream_fails_loud() -> None:
    a = assess_exposure("X", "1", "AI-datacenter", [], llm=_MockLlm({}))
    assert a.exposure_basis is ExposureBasis.NONE_DISCLOSED
    assert a.disclosed_facts == []
    assert any("no recent filings" in f for f in a.flags)


def test_directional_language_flagged_but_still_assembled() -> None:
    payload = {
        "disclosed_facts": [
            {"fact": "well-positioned to win; ~50% of revenue from HBM/advanced packaging",
             "concreteness": "quantified-revenue", "driver_tie": "chain-layer-specific",
             "source_ref": "10-K 2025-11-01 (acc A2)"},
        ],
        "primary_business": "an undervalued metrology leader", "key_unknowns": [],
    }
    a = assess_exposure("CAMT", "1109138", "AI-datacenter", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.QUANTIFIED_REVENUE  # cited quantified fact credits
    assert any("DIRECTIONAL" in f for f in a.flags)  # 'well-positioned to win' + 'undervalued'


def test_driver_tie_indirect_caps_binding_to_committed() -> None:
    """FCEL error-mode: a terms-BINDING contract with only an INDIRECT datacenter tie is NOT real —
    the driver-tie gate caps it at committed-capacity — independent of the binding terms."""
    payload = {"disclosed_facts": [
        {"fact": "binding CEPA: up to 380 MW carbonate fuel cells for data center applications",
         "concreteness": "binding-contract", "driver_tie": "indirect",
         "source_ref": "8-K 2026-01-15 (acc A1)"}],
        "primary_business": "fuel-cell maker", "key_unknowns": []}
    a = assess_exposure("FCEL", "886128", "AI-datacenter chain", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.COMMITTED_CAPACITY  # capped by the indirect tie
    assert not is_real_exposure(a)


def test_driver_tie_not_driver_caps_to_aspirational() -> None:
    """HIMX error-mode: even a strong fact tied to EDGE/on-device AI (the opposite of a datacenter)
    is capped to stated-intent — not-driver is not exposure to THIS driver."""
    payload = {"disclosed_facts": [
        {"fact": "image-sensor ICs for edge/on-device AI and the broad AI market",
         "concreteness": "quantified-revenue", "driver_tie": "not-driver",
         "source_ref": "10-K 2025-11-01 (acc A2)"}],
        "primary_business": "display-driver IC maker", "key_unknowns": []}
    a = assess_exposure("HIMX", "1342338", "AI-datacenter chain", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.ASPIRATIONAL  # capped by the not-driver tie
    assert not is_real_exposure(a)


def test_anonymized_but_binding_chain_specific_stays_real() -> None:
    """TSSI/WYFI: an ANONYMIZED counterparty with BINDING terms + a chain-specific tie stays REAL —
    the grader penalizes deferred TERMS, never customer anonymity (no named-customer rule)."""
    payload = {"disclosed_facts": [
        {"fact": "long-term agreement with its largest (unnamed) OEM customer: systems integration "
                 "for AI-enabled GPU racks at a minimum monthly volume with make-whole terms",
         "concreteness": "binding-contract", "driver_tie": "chain-layer-specific",
         "source_ref": "8-K 2026-01-15 (acc A1)"}],
        "primary_business": "AI-rack integration services", "key_unknowns": []}
    a = assess_exposure("TSSI", "1320760", "AI-datacenter chain", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.BINDING_CONTRACTS  # anonymity is not penalized
    assert is_real_exposure(a)


def test_missing_driver_tie_defaults_conservative() -> None:
    """Fail-closed: a fact with NO driver_tie defaults to INDIRECT — a binding fact without an
    explicit chain-specific tie is capped at committed-capacity, never silently REAL."""
    payload = {"disclosed_facts": [
        {"fact": "binding data-center power supply agreement", "concreteness": "binding-contract",
         "source_ref": "8-K 2026-01-15 (acc A1)"}],  # no driver_tie key
        "primary_business": "x", "key_unknowns": []}
    a = assess_exposure("X", "1", "AI-datacenter chain", _STREAM, llm=_MockLlm(payload))
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
# Build 2 — the value-chain UNIVERSE-SCAN path (pre-filter resilience, layer/provenance, driver)
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


def test_chain_layer_of_tags_disclosed_layer() -> None:
    """The provenance tag: which value-chain layer a fact names (most-specific first; a keyword read
    for by-layer volume, not a grade)."""
    assert chain_layer_of("~50% of revenue from HBM and advanced packaging") == "HBM/memory"
    assert chain_layer_of("liquid cooling systems for data centers") == "thermal/cooling"
    assert chain_layer_of("switchgear and power delivered to data centers") == "power/electrical"
    assert chain_layer_of("silicon photonics optical interconnect") == "optical/interconnect"
    assert chain_layer_of("colocation data-center campus operator") == "colocation/operator"
    assert chain_layer_of("we design GPUs and accelerators") == "chips/GPU"
    assert chain_layer_of("GPU-as-a-service neocloud platform") == "AI-cloud"
    assert chain_layer_of("we sell industrial floor paint") == "unspecified"


def test_grade_driving_fact_returns_basis_setter() -> None:
    """The human's first-read provenance is the fact that SET the basis (max effective rank) — the
    binding lease, not the co-listed 'exploring' intent."""
    payload = {"disclosed_facts": [
        {"fact": "exploring AI opportunities", "concreteness": "stated-intent",
         "driver_tie": "chain-layer-specific", "source_ref": "10-K 2025-11-01 (acc A2)"},
        {"fact": "15-year 300 MW lease with a hyperscaler", "concreteness": "binding-contract",
         "driver_tie": "chain-layer-specific", "source_ref": "8-K 2026-01-15 (acc A1)"}],
        "primary_business": "x", "key_unknowns": []}
    a = assess_exposure("X", "1", "AI-datacenter chain", _STREAM, llm=_MockLlm(payload))
    f = grade_driving_fact(a)
    assert f is not None and f.concreteness.value == "binding-contract"


def test_grade_driving_fact_none_when_no_exposure() -> None:
    a = assess_exposure("X", "1", "AI-datacenter chain", [], llm=_MockLlm({}))
    assert grade_driving_fact(a) is None


def test_value_chain_driver_and_prefilter_cover_the_chain() -> None:
    """The build-2 driver is the whole VALUE CHAIN (upstream enablers in scope), and the pre-filter
    was broadened to the chain's vocabulary — not just 'AI' (the wide-funnel requirement)."""
    d = AI_DATACENTER_DRIVER.lower()
    for layer in ("hbm", "packaging", "cooling", "power", "optical", "colocation", "cloud"):
        assert layer in d, f"driver text missing chain layer: {layer}"
    assert "upstream enablers" in d  # the CAMT scope decision
    joined = " ".join(DRIVER_PHRASES).lower()
    for term in ("data center", "liquid cooling", "optical interconnect", "high bandwidth memory"):
        assert term in joined, f"pre-filter missing chain vocabulary: {term}"
