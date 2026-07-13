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
from pathlib import Path
from typing import Any, cast

import pytest

from vinci.graph.llm import LlmClient
from vinci.netcache import CachedHttp, HttpError
from vinci.themes.drivers import (
    AI_DATACENTER,
    DEFENSE_DEMAND_SHIFT,
    DRIVER_SPECS,
    TRUCKLOAD_SUPPLY_PURGE,
)
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


def test_defense_spec_runs_with_no_ai_datacenter_leak() -> None:
    """Theme #2 (the refactor's proof-of-generalization): the analyst-approved DEFENSE spec runs
    through the SAME driver-agnostic classifier — its DEFENSE / demand-shift taxonomy reaches the
    LLM, with ZERO AI-datacenter leakage into the prompt."""
    mock = _MockLlm({"disclosed_facts": [], "primary_business": "x", "key_unknowns": []})
    assess_exposure(DEFENSE_DEMAND_SHIFT, "AVAV", "1", _STREAM, llm=mock)
    prompt = mock.last_system + "\n" + mock.last_user + "\n" + json.dumps(mock.last_tool)
    low = prompt.lower()
    for leak in ("ai-datacenter", "value chain", "hbm", "advanced packaging", "hyperscaler",
                 "colocation", "chain-layer"):
        assert leak not in low, f"AI-datacenter leaked into the defense prompt: {leak!r}"
    for term in ("attritable", "loitering", "counter-uas", "legacy", "tailwind"):
        assert term in low, f"defense taxonomy missing from the prompt: {term!r}"


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


def test_grounding_accepts_scale_and_comma_number_drift() -> None:
    """(a) FALSE-FAIL fix — number-format drift: a fact's '$47,829K' grounds against a filing's
    '47,829' (reported in thousands) via scale-word + comma NORMALIZATION, instead of failing on
    the surface-format mismatch (the FEIM case from the defense scan)."""
    ref = "10-Q 2026-03-01 (accession 0001185185-26-000893)"
    stream = [(ref, "Consolidated revenues were 47,829 for the nine months ended "
                    "January 31, 2026.")]
    payload = {"disclosed_facts": [
        {"fact": "Consolidated revenues were $47,829K for the nine months ended January 31, 2026",
         "concreteness": "committed-capacity", "driver_tie": "indirect", "source_ref": ref}],
        "primary_business": "precision timing", "key_unknowns": []}
    a = assess_exposure(DEFENSE_DEMAND_SHIFT, "FEIM", "1", stream, llm=_MockLlm(payload))
    assert not any("UNGROUNDED" in f for f in a.flags)      # $47,829K ↔ 47,829 now grounds
    assert a.exposure_basis is ExposureBasis.COMMITTED_CAPACITY


def test_grounding_ignores_driver_vocabulary_in_negative_reasoning() -> None:
    """(b) FALSE-FAIL fix — the LLM's NEGATIVE reasoning names the driver's OWN taxonomy ('… no tie
    to attritable UAVs, counter-UAS, loitering munitions …'); those theme-generic tokens are
    excluded so the fact grounds on its COMPANY-specific token (Wolfspeed), which IS in the filing
    (the WOLF dual-use case — its 33-flag-dominant mode)."""
    ref = "10-K 2025-08-01 (accession 0000895419-25-000110)"
    stream = [(ref, "Wolfspeed's silicon carbide materials are used in military communications, "
                    "radar and satellite applications.")]
    payload = {"disclosed_facts": [
        {"fact": "Wolfspeed materials are used in military communications, radar and satellite — a "
                 "generic dual-use listing with no tie to attritable UAVs, counter-UAS, loitering "
                 "munitions, defense autonomy/AI, or scaled munitions.",
         "concreteness": "stated-intent", "driver_tie": "indirect", "source_ref": ref}],
        "primary_business": "silicon carbide maker", "key_unknowns": []}
    a = assess_exposure(DEFENSE_DEMAND_SHIFT, "WOLF", "1", stream, llm=_MockLlm(payload))
    assert not any("UNGROUNDED" in f for f in a.flags)   # Wolfspeed grounds; UAV terms excluded


def test_grounding_still_catches_fabricated_counterparty() -> None:
    """(c) GENUINE-CATCH preserved: excluding driver vocabulary must NOT rescue a fabricated
    counterparty — a made-up name is never driver vocab, so a 'binding loitering-munition contract
    with Vortex Dynamics' whose counterparty is absent from the filing still fails closed (even
    though the filing DOES carry the driver's vocabulary)."""
    ref = "8-K 2026-02-01 (accession 0001628280-26-013305)"
    stream = [(ref, "The Company manufactures loitering munitions and unmanned aerial systems.")]
    payload = {"disclosed_facts": [
        {"fact": "binding loitering-munition supply contract with Vortex Dynamics",
         "concreteness": "binding-contract", "driver_tie": "driver-specific", "source_ref": ref}],
        "primary_business": "x", "key_unknowns": []}
    a = assess_exposure(DEFENSE_DEMAND_SHIFT, "X", "1", stream, llm=_MockLlm(payload))
    assert any("UNGROUNDED" in f for f in a.flags)
    assert a.exposure_basis is ExposureBasis.NONE_DISCLOSED  # fabricated counterparty → fail-closed


def test_grounding_still_catches_fabricated_figure() -> None:
    """(c) GENUINE-CATCH preserved: a quantitative claim whose EVERY figure is absent fails closed
    even when a real company name grounds — a fabricated '$250 million order' is not rescued by the
    real 'Kratos' (closes the figure-side fabrication hole a pooled proper-noun match would leave
    open)."""
    ref = "8-K 2026-02-01 (accession 0001628280-26-013305)"
    stream = [(ref, "Kratos announced a new production order during the quarter.")]
    payload = {"disclosed_facts": [
        {"fact": "Kratos received a $250 million binding production order",
         "concreteness": "binding-contract", "driver_tie": "driver-specific", "source_ref": ref}],
        "primary_business": "x", "key_unknowns": []}
    a = assess_exposure(DEFENSE_DEMAND_SHIFT, "X", "1", stream, llm=_MockLlm(payload))
    assert any("UNGROUNDED" in f for f in a.flags)   # figure absent → fail-closed despite 'Kratos'
    assert a.exposure_basis is ExposureBasis.NONE_DISCLOSED


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


def test_themes_exposure_driver_required_and_resolves(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--driver is REQUIRED + choices-gated (fail-loud, no default); each valid key round-trips
    through the parser to its DRIVER_SPECS entry; an unknown key errors naming both keys."""
    from vinci.cli import build_parser

    parser = build_parser()

    with pytest.raises(SystemExit):  # unknown driver → argparse exit
        parser.parse_args(["themes-exposure", "--driver", "not-a-theme"])
    err = capsys.readouterr().err
    assert all(k in err for k in DRIVER_SPECS)  # error names every registry key (derived)

    with pytest.raises(SystemExit):  # missing --driver → required, no silent default
        parser.parse_args(["themes-exposure"])

    for key in DRIVER_SPECS:  # each valid key round-trips to the right spec
        args = parser.parse_args(["themes-exposure", "--driver", key])
        assert args.driver == key
        assert DRIVER_SPECS[args.driver].key == key
    assert "truckload-supply-purge" in DRIVER_SPECS  # registry drives --driver choices (derived)


def test_truckload_driver_registered_and_fields_nonempty() -> None:
    """Theme #3 (truckload-supply-purge, T007) is in the registry — now 3 keys — and its
    analyst-ratified spec fields are all non-empty. The exposure classifier is driver-agnostic, so a
    new theme is a new DriverSpec and nothing else."""
    assert "truckload-supply-purge" in DRIVER_SPECS and len(DRIVER_SPECS) == 3
    t = TRUCKLOAD_SUPPLY_PURGE
    assert t.key == "truckload-supply-purge"
    assert all([t.description, t.tie_taxonomy, t.prefilter_terms, t.provenance_tags])


def test_truckload_provenance_ltl_ordered_before_asset_based_tl() -> None:
    """Provenance ORDERING pin: 'less-than-truckload' → ltl, NOT asset-based-tl. Because
    provenance_tag_of is first-match and ltl is listed FIRST, the 'truckload' substring in
    asset-based-tl's keywords must not win — a regression would mis-tag LTL names as asset TL."""
    lyr = TRUCKLOAD_SUPPLY_PURGE.provenance_tags
    assert provenance_tag_of("less-than-truckload carrier, tonnage per day", lyr) == "ltl"
    assert provenance_tag_of("asset-based truckload linehaul", lyr) == "asset-based-tl"
    assert provenance_tag_of("we run a freight brokerage / 3pl", lyr) == "brokerage-3pl"


def test_truckload_asset_tl_precedes_equipment() -> None:
    """Provenance ORDERING pin #2: a real asset-based TL carrier's fact names its OWN tractors and
    trailers (equipment keywords), yet must tag `asset-based-tl` — the tailwind bucket — not
    `equipment`. asset-based-tl precedes equipment, so its `truckload`/`linehaul` match wins;
    a regression (equipment first) would mis-file every tractor/trailer-mentioning TL carrier under
    equipment. `equipment` still catches a pure OEM/dealer fact with NO truckload signal."""
    lyr = TRUCKLOAD_SUPPLY_PURGE.provenance_tags
    # carrier fact naming its own tractors AND its truckload capacity → the tailwind bucket
    assert provenance_tag_of(
        "grew the company tractor fleet, expanding truckload capacity", lyr) == "asset-based-tl"
    # a pure equipment fact (used-truck / dealer, NO truckload signal) still reaches `equipment`
    assert provenance_tag_of("used truck sales through the dealer network", lyr) == "equipment"


def test_only_tickers_partition_subset_and_missing() -> None:
    """--only-tickers restricts to the intersection with the universe; unknown names come back as
    `missing` (the caller prints + skips them) while the rest proceed — the delta-scan primitive."""
    from vinci.cli import _partition_only

    kept, missing = _partition_only({"AAA", "BBB"}, {"AAA", "BBB", "CCC"})
    assert kept == {"AAA", "BBB"} and missing == []  # pure subset — all kept, none missing
    kept, missing = _partition_only({"AAA", "ZZZ"}, {"AAA", "BBB"})
    assert kept == {"AAA"} and missing == ["ZZZ"]  # unknown ZZZ surfaced; AAA still scanned


def test_only_tickers_empty_intersection_errors() -> None:
    """An empty intersection must ERROR (SystemExit), never silently scan nothing — a typo'd or
    stale delta list would otherwise read as 'no exposure'."""
    from vinci.cli import _partition_only

    with pytest.raises(SystemExit):
        _partition_only({"ZZZ", "YYY"}, {"AAA", "BBB"})


def test_resolve_only_tickers_sources_and_guards(tmp_path: Path) -> None:
    """--only-tickers parses a comma list (uppercased); --only-file reads the same from disk;
    neither → None; both sources → error; a supplied-but-empty source → error."""
    import argparse

    from vinci.cli import _resolve_only_tickers

    def ns(t: str | None = None, f: Path | None = None) -> argparse.Namespace:
        return argparse.Namespace(only_tickers=t, only_file=f)

    assert _resolve_only_tickers(ns()) is None  # neither given → not a delta scan
    assert _resolve_only_tickers(ns(t="wern, rxo,arcb")) == {"WERN", "RXO", "ARCB"}  # comma+upper
    names = tmp_path / "names.txt"
    names.write_text("wern\nrxo\n")
    assert _resolve_only_tickers(ns(f=names)) == {"WERN", "RXO"}  # file source
    with pytest.raises(SystemExit):
        _resolve_only_tickers(ns(t="A", f=names))  # both sources → error
    empty = tmp_path / "empty.txt"
    empty.write_text("  \n , \n")
    with pytest.raises(SystemExit):
        _resolve_only_tickers(ns(f=empty))  # supplied but parses to nothing → error


def test_themes_exposure_only_tickers_argparse() -> None:
    """themes-exposure exposes --only-tickers / --only-file (the monitor's future delta-scan)."""
    from vinci.cli import build_parser

    a = build_parser().parse_args(
        ["themes-exposure", "--driver", "truckload-supply-purge", "--only-tickers", "WERN,RXO"])
    assert a.only_tickers == "WERN,RXO" and a.only_file is None


# --- scan-error grading (the 2026-07-13 quota incident) ---------------------------------------
def test_llm_error_is_unassessed_not_none() -> None:
    """An LLM error yields the UNASSESSED_ERROR bucket + a flag — NEVER a false NONE. A failure must
    not read as 'no exposure' (the 2026-07-13 quota incident, 22 error records → false none=22)."""
    from vinci.graph.llm import LlmError

    class _Boom(LlmClient):
        @property
        def model(self) -> str:
            return "mock"

        def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
            raise LlmError("truncated")

    a = assess_exposure(AI_DATACENTER, "X", "1", _STREAM, llm=_Boom())
    assert a.exposure_basis is ExposureBasis.UNASSESSED_ERROR  # NOT NONE_DISCLOSED
    assert any("LLM error" in f for f in a.flags)


def test_scan_error_unassessed_and_non_4xx_no_abort(monkeypatch: pytest.MonkeyPatch) -> None:
    """A raw scan error → UNASSESSED_ERROR record (never NONE); a NON-4xx error does NOT
    trip the abort — the run COMPLETES with every failed name bucketed unassessed."""
    import vinci.themes.exposure as ex_mod
    from vinci.themes.exposure import scan_driver_exposure

    class _NetBoom(LlmClient):
        @property
        def model(self) -> str:
            return "mock"

        def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("connection reset")  # no status_code → transient, not systemic

    names = [(f"T{i}", str(2000 + i)) for i in range(5)]
    monkeypatch.setattr(ex_mod, "mention_prefilter", lambda *a, **k: {c for _, c in names})
    monkeypatch.setattr(ex_mod, "recent_disclosure_stream", lambda *a, **k: [("8-K (acc A1)", "x")])
    _matched, results = scan_driver_exposure(
        AI_DATACENTER, names, edgar=cast(Any, None), sec_http=cast(Any, None),
        efts_http=cast(Any, None), llm=_NetBoom(), startdt="2026-01-01", enddt="2026-06-01",
        max_workers=1)
    assert len(results) == 5  # completed — a non-4xx transient never aborts
    assert all(r.exposure_basis is ExposureBasis.UNASSESSED_ERROR for r in results)  # never NONE


def test_scan_aborts_fast_on_repeated_quota_4xx(monkeypatch: pytest.MonkeyPatch) -> None:
    """3 consecutive same-4xx (quota/auth) LLM failures ABORT the scan (ScanAbortedError) BEFORE it
    poisons the whole queue — the 2026-07-13 incident. Aborts EARLY (not all names scanned)."""
    import vinci.themes.exposure as ex_mod
    from vinci.themes.exposure import ScanAbortedError, scan_driver_exposure

    class _Api400Error(Exception):
        status_code = 400

    class _Quota(LlmClient):
        @property
        def model(self) -> str:
            return "mock"

        def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
            raise _Api400Error("You have reached your specified API usage limits")

    names = [(f"T{i}", str(1000 + i)) for i in range(10)]
    monkeypatch.setattr(ex_mod, "mention_prefilter", lambda *a, **k: {c for _, c in names})
    monkeypatch.setattr(ex_mod, "recent_disclosure_stream", lambda *a, **k: [("8-K (acc A1)", "x")])
    with pytest.raises(ScanAbortedError) as ei:
        scan_driver_exposure(
            AI_DATACENTER, names, edgar=cast(Any, None), sec_http=cast(Any, None),
            efts_http=cast(Any, None), llm=_Quota(), startdt="2026-01-01", enddt="2026-06-01",
            max_workers=1)
    assert ei.value.status == 400
    assert len(ei.value.assessed) == 3  # aborted at the 3rd consecutive 4xx, not all 10
    assert ei.value.remaining  # names left un-scanned (queue not poisoned)


def test_valid_assessment_grade_unaffected_by_error_bucket() -> None:
    """Regression pin: the UNASSESSED_ERROR bucket is isolated to error paths — a VALID (successful
    LLM) assessment still derives its basis from the cited facts, unchanged."""
    payload = {
        "disclosed_facts": [
            {"fact": "15-year lease with AWS for ~300 MW of data center capacity",
             "concreteness": "binding-contract", "driver_tie": "driver-specific",
             "source_ref": "8-K 2026-01-15 (acc A1)"}],
        "primary_business": "datacenter HPC host", "key_unknowns": [],
    }
    a = assess_exposure(AI_DATACENTER, "CIFR", "1819989", _STREAM, llm=_MockLlm(payload))
    assert a.exposure_basis is ExposureBasis.BINDING_CONTRACTS  # derived, NOT unassessed-error
    assert a.flags == []
