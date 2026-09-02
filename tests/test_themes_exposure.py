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
    flag_intra_population_control,
    grade_driving_fact,
    is_real_exposure,
    mention_prefilter,
    parse_efts_ciks,
    provenance_tag_of,
)
from vinci.themes.schemas import (
    DriverSpec,
    DriverTie,
    ExposureAssessment,
    ExposureBasis,
    ExposureConcreteness,
    ExposureFact,
)

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
    """Theme #3 (truckload-supply-purge, T007) is in the registry and its analyst-ratified spec
    fields are all non-empty. The exposure classifier is driver-agnostic, so a new theme is a new
    DriverSpec and nothing else.

    THE COUNT ASSERTION WAS REMOVED, and the reason is the point of the test. It read
    `len(DRIVER_SPECS) == 3` — a pin on how many OTHER drivers exist, which is not the property
    this test names. Adding `glp1-demand-shift` reddened it while truckload remained perfectly
    registered, so the pin reported a regression that had not happened. The classifier being
    driver-agnostic is exactly the claim that the registry's SIZE is nobody's business: a test
    that must be edited to add a driver is asserting the opposite of the design it documents."""
    assert "truckload-supply-purge" in DRIVER_SPECS
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


def test_silicon_ecosystem_moat_tags_the_software_moat_never_unit_demand() -> None:
    """BOUNDARY PIN (operator ruling 2026-08-30): ai-value-migration's third model-agnostic
    beneficiary class — a silicon vendor whose SOFTWARE/developer-ecosystem bundle is the moat.
    The tag's keywords deliberately name only the software moat, never bare silicon terms
    ("gpu", "chip"): a unit-demand/build-out sentence must fall through to 'unspecified' under
    THIS driver's tags (the ai-datacenter sibling reads that fact), because a GPU-volumes fact
    mis-tagged as a moat would dissolve the boundary the ruling drew — the split is by ECONOMICS
    NAMED in the disclosure, not by company."""
    from vinci.themes.exposure import provenance_tags_of

    spec = DRIVER_SPECS["ai-value-migration"]
    assert spec.multi_tag is True  # one vendor can be moat AND platform — record all
    hits = provenance_tags_of(
        "our accelerated computing platform is supported by a broad developer ecosystem and a "
        "widely adopted programming model", spec.provenance_tags)
    assert "silicon-ecosystem-moat" in hits
    # the build-out chain's unit/capacity demand carries NO tag here — ai-datacenter's territory
    assert provenance_tags_of(
        "we supply HBM memory and advanced packaging for AI data center GPUs, with capacity "
        "commitments through 2027", spec.provenance_tags) == ("unspecified",)
    # REVIEW PIN (2026-08-31) — the REALISTIC mis-tag, not just the keyword-free one above: a
    # pure volumes sentence wearing the standard vendor label "accelerated computing". That
    # phrase was a tag keyword at birth and DID tag this sentence as a moat (executed during
    # review), dissolving the ruling's boundary; the keyword is gone and this pin holds the
    # door shut against re-widening (gpu/chip/accelerated — what the tag comment forbids).
    assert "silicon-ecosystem-moat" not in provenance_tags_of(
        "record demand for our accelerated computing platform drove data center revenue up 60% "
        "on GPU shipments", spec.provenance_tags)


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


# ─── provenance tags: multi-match, and the ordering three drivers depend on ──────────────────────
def test_multi_tag_is_opt_in_because_first_match_ordering_is_load_bearing() -> None:
    """MEASURED COLLISIONS (review of #488). `ai-datacenter` and `truckload-supply-purge` order
    their tags most-specific-first and rely on the first match winning. Under unconditional
    multi-match:

      "liquid cooling systems for data centers" -> ('thermal/cooling', 'colocation/operator')
      "less-than-truckload carrier"             -> ('ltl', 'asset-based-tl')

    The AI case makes nearly every name read as colocation, because its prefilter GUARANTEES
    "data center" appears. The truckload case is worse — its tags are DIRECTIONAL, so a HEADWIND
    name lands in the TAILWIND bucket, which is the collision `drivers.py` regression-pins.

    So the capability is a per-spec DECLARATION: a driver whose tags PARTITION keeps first-match;
    one whose tags are DIMENSIONS asks for all of them."""
    from vinci.themes.drivers import DRIVER_SPECS
    from vinci.themes.exposure import provenance_tag_of, provenance_tags_of

    partitioned = [k for k, s in DRIVER_SPECS.items() if not s.multi_tag]
    assert set(partitioned) >= {"ai-datacenter", "truckload-supply-purge", "defense-demand-shift"}
    assert DRIVER_SPECS["glp1-demand-shift"].multi_tag is True, (
        "the GLP-1 sides are genuinely non-exclusive — one name can be suppressed in one category "
        "and helped in another")

    tl = DRIVER_SPECS["truckload-supply-purge"].provenance_tags
    assert provenance_tag_of("less-than-truckload carrier", tl) == "ltl", (
        "first-match must still win for a partitioned driver — a headwind name tagged into the "
        "tailwind bucket is the defect this ordering exists to prevent")
    assert provenance_tags_of("less-than-truckload carrier", tl) == ("ltl", "asset-based-tl"), (
        "the multi-match function itself still returns every match — the GATE is the spec flag, "
        "not the resolver")


def test_the_single_tag_form_is_the_first_of_the_multi_form() -> None:
    """`provenance_tag_of` DELEGATES, so the two can never disagree — the property that lets the
    other three drivers stay untouched by the multi-tag work."""
    from vinci.themes.drivers import DRIVER_SPECS
    from vinci.themes.exposure import provenance_tag_of, provenance_tags_of

    for spec in DRIVER_SPECS.values():
        for text in ("data center liquid cooling", "less-than-truckload", "protein shake",
                     "nothing matches this string at all"):
            assert (provenance_tag_of(text, spec.provenance_tags)
                    == provenance_tags_of(text, spec.provenance_tags)[0])


def test_nothing_matching_yields_unspecified_rather_than_empty() -> None:
    """The return is never empty, so no caller needs a guard."""
    from vinci.themes.drivers import DRIVER_SPECS
    from vinci.themes.exposure import provenance_tags_of

    tags = DRIVER_SPECS["glp1-demand-shift"].provenance_tags
    assert provenance_tags_of("zzz no keyword here", tags) == ("unspecified",)


def test_no_cli_print_site_resolves_tags_outside_the_shared_helper() -> None:
    """THE SIBLING-CALL-SITE PIN (review of #488) — the defect that changed an answer.

    `cli.py` had TWO tag print sites. The multi-tag fix updated one; the committed-capacity block
    still called the single-tag helper, so 12 of 18 driver-specific names printed under-tagged and
    the reported conclusion — "no benefiting-side name competes with SMPL" — was FALSE, hiding
    SMPL's own second tag and BJRI's. The suite stayed green throughout, because nothing asserted
    that the print sites agree.

    A behavioural pin cannot reach a print site without running the whole scan, so this asserts the
    STRUCTURAL property instead: every tag resolution in the CLI goes through the ONE gated helper
    (`_tags`), and no call site reaches the raw resolvers directly. Same shape as the contamination
    caught in `assumptions` and invisible in its sibling `facts` — the sibling is the check that
    was missing."""
    import pathlib

    src = (pathlib.Path(__file__).resolve().parents[1] / "vinci" / "cli.py").read_text()
    # Counted rather than located: BOTH resolvers must be invoked exactly once in the whole file,
    # and both of those calls live in `_tags`. A second call anywhere is a second decision about
    # how tags resolve, which is precisely how the two print sites came to disagree.
    assert src.count("provenance_tags_of(") == 1, (
        "provenance_tags_of is called more than once in cli.py — every print site must share the "
        "ONE gated resolution, or a fix applied at one and not its sibling changes the answer")
    assert src.count("provenance_tag_of(") == 1, (
        "provenance_tag_of is called more than once in cli.py — the single-tag helper is the "
        "fallback INSIDE `_tags`, never a second path a print site can reach")
    # A generous window rather than a precise slice: `_tags` carries a docstring with blank lines,
    # so splitting on "\n\n" truncates before the body it is meant to check.
    tags_def = src[src.index("def _tags("):][:1200]
    assert "provenance_tags_of(" in tags_def and "provenance_tag_of(" in tags_def, (
        "both resolvers must sit inside `_tags` — if they moved, this pin is guarding nothing")


def test_hyperscaler_platform_tags_the_provider_not_every_filer_that_says_cloud() -> None:
    """MEASURED CALIBRATION (2026-08-31), from the FIRST real scan of ai-value-migration.

    The prior keywords ("cloud", "hyperscaler", "inference", "platform", "distribution") tagged
    12 of 12 scanned names. A tag that fires on everything carries no information, and the by-tag
    volume read is the entire purpose of this layer. The sentences below are VERBATIM from that
    scan's committed assessments, frozen here as fixtures — a value-level pin belongs on a frozen
    fixture, never on a re-drawn artifact, and freezing them is also what makes this a corpus
    check rather than text invented to fit the keywords.

    THE RESIDUAL IS PINNED TOO, because it is the honest limit: a filer that NAMES a hyperscaler
    reads identically to one that IS one. That is semantic, not lexical, and the tag stays
    provenance — the discrimination that matters is the LLM's driver_tie grade."""
    from vinci.themes.exposure import provenance_tags_of

    tags = DRIVER_SPECS["ai-value-migration"].provenance_tags

    def hp(text: str) -> bool:
        return "hyperscaler-platform" in provenance_tags_of(text, tags)

    # THE PROVIDERS — the three names that genuinely sell the below-the-model compute layer, on
    # their own reported segment vocabulary. All three must keep the tag.
    assert hp("Alphabet reports Google in two segments, Google Services and Google Cloud, and "
              "discloses that Google Cloud helps customers build for the AI era")
    assert hp("Segment disclosure: Intelligent Cloud is one of three reportable segments; "
              "Microsoft 365 Commercial cloud revenue grew")
    assert hp("AWS is disclosed as one of three reportable segments, serving developers and "
              "enterprises of all sizes")

    # THE APP LAYER — real sentences that the old keyword set swept in on bare "cloud" alone.
    assert not hp("Veeva describes itself as the leading provider of industry cloud solutions "
                  "for the global life sciences industry, spanning cloud software")
    assert not hp("The 10-K describes ServiceNow as delivering solutions that help organizations "
                  "govern, secure and manage artificial intelligence")
    # ...and an AI-feature sentence, which "inference" used to catch on any app-layer filer
    assert not hp("customers use the platform to run inference on their own enterprise data")

    # THE RESIDUAL, stated rather than papered over: naming a hyperscaler still tags.
    assert hp("our software is deployed on AWS and other public cloud providers")


def test_ai_value_migration_prefilter_excludes_the_two_generic_ai_phrases() -> None:
    """MEASURED on the first full sweep (2026-08-31): the prefilter passed 2,666 of 2,907 names —
    92% — to the expensive semantic layer, and per-term measurement named the cause exactly.
    "artificial intelligence" matched 2,579 on its own and "generative AI" 985; every modern 10-K
    says them. Dropping BOTH takes the candidate set to 1,266 (-53%) with all 12 operator-named
    beneficiaries still clearing on their LAYER vocabulary.

    The prefilter exists to buy RECALL cheaply so the semantic layer can discriminate — but recall
    bought with a phrase that matches everything is not recall, it is cost: each waved-through name
    costs filing fetches plus one LLM assessment.

    THE SIBLING IS DELIBERATELY UNTOUCHED: `ai-datacenter` keeps "artificial intelligence",
    because its OTHER terms are hardware-chain vocabulary (HBM, liquid cooling, switchgear) that a
    software filer never uses — the generic phrase is that driver's only bridge to an AI-cloud
    name. Same word, different job; measure per driver rather than sweeping the term out globally.
    """
    avm = DRIVER_SPECS["ai-value-migration"].prefilter_terms
    assert "artificial intelligence" not in avm
    assert "generative AI" not in avm
    # the layer vocabulary that carries recall in its place is still there
    for kept in ("inference", "hyperscaler", "system of record", "proprietary data", "copilot",
                 "agentic", "large language model", "workflow automation"):
        assert kept in avm, kept
    # and the sibling driver's own use of the generic phrase is untouched
    assert "artificial intelligence" in DRIVER_SPECS["ai-datacenter"].prefilter_terms


def test_glp1_prefilter_replaces_generic_words_with_the_terms_of_art() -> None:
    """MEASURED on the first full sweep (2026-08-31): this filter passed 1,772 of 2,907 names, and
    four generic ENGLISH words carried nearly all of it — "compounded" 993 matches / 578 unique,
    "generic" 663/152, "contract manufacturing" 471/78, "capacity expansion" 308/144 — while every
    specific molecule term matched 5-30 and contributed ZERO unique names.

    THE POINT OF THIS PIN is the trap the fix avoids. Two of those words are ALSO terms of art in
    the operator's thesis: compounded semaglutide IS the access-channel leg, generic entry IS the
    price-compression leg. Deleting them outright would have cut real signal along with the noise,
    so each bare word is REPLACED by the phrase that carries its meaning. A future editor tempted
    to re-add the short form should read the numbers above first."""
    glp1 = DRIVER_SPECS["glp1-drug-value-chain"].prefilter_terms
    # the ambiguous single words are gone...
    for banned in ("compounded", "generic", "contract manufacturing", "capacity expansion"):
        assert banned not in glp1, banned
    # ...and their MEANING is retained by precise phrases that have NO parent term in the list,
    # so each can actually contribute (review 2026-08-31 removed three that could not)
    for phrase in ("compounding pharmacy", "generic entry", "generic competition",
                   "loss of exclusivity"):
        assert phrase in glp1, phrase
    # the manufacturing leg is carried by specific vocabulary, not by the bare word that matched
    # every manufacturer in the universe
    for kept in ("CDMO", "fill-finish", "sterile injectable", "peptide"):
        assert kept in glp1, kept
    # and the molecules that make the filter MEAN this theme are untouched
    for mol in ("semaglutide", "tirzepatide", "incretin", "amylin", "GLP-1"):
        assert mol in glp1, mol


def test_no_prefilter_term_is_contained_by_another_term_of_the_same_driver() -> None:
    """INVARIANT (2026-08-31): a prefilter phrase that CONTAINS another phrase in the same list is
    dead configuration. EFTS matches the shorter string wherever the longer one appears, so the
    longer phrase can never contribute a candidate the shorter one did not — it only costs one
    paced batch-query per CIK batch, every scan, forever.

    Found by review of the glp1 narrowing, which had added three such phrases ("compounded
    semaglutide" ⊂ "semaglutide", "compounded GLP-1" ⊂ "GLP-1", "peptide manufacturing" ⊂
    "peptide" — all verified SUBSET=True against the live universe), and which then surfaced a
    PRE-EXISTING one ("peptide synthesis" ⊂ "peptide"). Checked across EVERY driver, because the
    mistake is a property of how the filter works, not of one taxonomy.

    NOTE the direction: this forbids REDUNDANCY, not specificity. Replacing a bare word with a
    precise phrase stays correct as long as the bare word LEAVES the list — which is exactly what
    the glp1 change does with compounded/generic."""
    #: TWO pre-existing pairs, recorded rather than silently fixed. `ai-datacenter` and
    #: `glp1-demand-shift` are LIVE themes with committed scans, frozen baskets and pages;
    #: editing their analyst-ratified vocabulary changes what future scans surface, which is an
    #: operator decision belonging in its own change — not smuggled into a glp1-drug-value-chain
    #: PR. The allowlist keeps the rule enforced for every NEW term while naming the debt.
    #:
    #: HYPHENATED pairs (counter-drone/drone, high-protein/protein) are deliberately NOT flagged:
    #: whether EFTS treats a hyphen as a token boundary was not measured, so the check declines to
    #: claim they are redundant. Measure before extending the rule to them.
    known_pre_existing = {("data center power", "data center"), ("protein shake", "protein")}
    # WORD-BOUNDARY containment, not plain substring — the distinction is the whole correctness of
    # this check. EFTS searches TOKENS: "semaglutide" matches a filing saying "compounded
    # semaglutide" (whole token present), but "snack" does NOT match one saying only "snacking"
    # (different token). A naive `short in long` flags snack/snacking and salty snacks/snack as
    # redundant when they are genuinely distinct terms — the first draft of this test did exactly
    # that across three drivers.
    import re as _re

    for key, spec in DRIVER_SPECS.items():
        terms = [t.lower() for t in spec.prefilter_terms]
        contained = [
            (long, short) for long in terms for short in terms
            if long != short
            and _re.search(rf"(?<![\w-]){_re.escape(short)}(?![\w-])", long)
            and (long, short) not in known_pre_existing
        ]
        assert not contained, (
            f"{key}: these prefilter phrases contain another term in the same list, so they can "
            f"never match anything the shorter term misses: {contained}")


# --------------------------------------------------------------------------------------------------
# Same asset, two tickers — the intra-population control-pair flag (2026-09-02)
# --------------------------------------------------------------------------------------------------
def _assessment(ticker: str, facts: list[str]) -> ExposureAssessment:
    """Build from the REAL type (CLAUDE.md: fixtures are never hand-rolled to the test's shape)."""
    return ExposureAssessment(
        ticker=ticker, cik=f"000{abs(hash(ticker)) % 10**7:07d}", driver="d",
        exposure_basis=ExposureBasis.BINDING_CONTRACTS,
        disclosed_facts=[
            ExposureFact(fact=f, concreteness=ExposureConcreteness.BINDING_CONTRACT,
                         driver_tie=DriverTie.DRIVER_SPECIFIC, source_ref="0001-25-000001")
            for f in facts
        ],
        primary_business="", key_unknowns=[], stream_refs=["0001-25-000001"],
    )


def test_control_pair_is_flagged_on_both_sides() -> None:
    """POSITIVE PIN — the real observed pair: BTBT disclosed ~70.5% of WYFI and both graded
    binding-contract in the live ai-compute-platform scan, one asset counted twice in a nine-name
    tier. The flag must reach BOTH rows, since either is the one a reader opens."""
    rows = flag_intra_population_control([
        _assessment("BTBT", ["The Company holds an approximately 70.5% majority equity stake in "
                             "WhiteFiber Inc. (Nasdaq: WYFI) following the July 2025 IPO."]),
        _assessment("WYFI", ["Data center hosting revenue under a binding 5-year agreement."]),
        _assessment("CRWV", ["Remaining performance obligations of $60.7 billion."]),
    ])
    by_ticker = {r.ticker: r for r in rows}
    assert any("CONTROL PAIR" in f and "WYFI" in f for f in by_ticker["BTBT"].flags)
    assert any("CONTROL PAIR" in f and "BTBT" in f for f in by_ticker["WYFI"].flags)
    assert by_ticker["CRWV"].flags == []          # an unrelated name is untouched


def test_bare_ticker_words_do_not_create_control_pairs() -> None:
    """NEGATIVE PIN — the real observed failure shape. An unqualified \\b[A-Z]{2,5}\\b scan of the
    745-name corpus matched the English words 'AI' (C3.ai's symbol) and 'IT' (Gartner's), inventing
    8 false pairs against 1 true one. Only an EXCHANGE-QUALIFIED cite may form a pair."""
    rows = flag_intra_population_control([
        _assessment("NEE", ["NextEra Energy Resources, a wholly owned subsidiary, develops AI "
                            "data center capacity and IT infrastructure for the segment."]),
        _assessment("MARA", ["Majority ownership of the AI hosting joint venture is retained."]),
        _assessment("AI", ["Enterprise AI application revenue."]),
        _assessment("IT", ["Research and advisory revenue."]),
    ])
    assert all(r.flags == [] for r in rows), [r.flags for r in rows if r.flags]


def test_control_of_a_name_outside_the_scan_is_not_flagged() -> None:
    """NEGATIVE PIN — the flag exists to stop DOUBLE-COUNTING WITHIN a tier. A subsidiary that is
    not in the population cannot be counted twice, so it is not this guard's business."""
    rows = flag_intra_population_control([
        _assessment("WULF", ["The Company holds a 50.1% majority equity interest in Nautilus "
                             "Cryptomine LLC (Nasdaq: XXXX), an unconsolidated affiliate."]),
    ])
    assert rows[0].flags == []
