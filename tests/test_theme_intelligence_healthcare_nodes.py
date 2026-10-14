"""Healthcare's sub-categories (operator, 2026-10-14).

With healthcare as ONE taxonomy node, every article arguing rising US healthcare demand shared one
thesis key (node · mechanism · direction · geography): the pilot's Alzheimer drug-market thesis
absorbed a direct-to-consumer cash-pay piece and a conference piece on GLP-1 access. Four children
now separate the economics; the theses already keyed at `healthcare` keep their keys.

Offline: HYPOTHETICAL articles (invented text on the reserved `.test` domain), extractions in the
REAL type. The real run is in the build record.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.config import load_taxonomy
from vinci.theme_intelligence.extract import system_prompt
from vinci.theme_intelligence.schemas import RunStatus, ThesisStatus

AS_OF = date(2026, 10, 14)
CHILDREN = ("healthcare.pharma_biotech", "healthcare.life_science_tools",
            "healthcare.medtech_diagnostics", "healthcare.services_payers")


def test_healthcare_has_four_children_and_the_extractor_is_offered_them() -> None:
    tx = load_taxonomy()
    assert set(CHILDREN) <= set(tx.node_ids) and "healthcare" in tx.node_ids
    for c in CHILDREN:
        assert tx.ancestry(c) == ("healthcare", c), c
    prompt = system_prompt(tx)
    assert "healthcare.pharma_biotech: Pharmaceuticals and biotechnology" in prompt
    assert "healthcare.services_payers: Healthcare services and payers" in prompt


def _article(pipe: object, slug: str, line: str, node: str, title: str) -> None:
    art = Hypo(slug, "Test Publisher", date(2026, 9, 14), [("paragraph", line)])
    x = extraction([claim("c1", "b001", line.rstrip("."), title, metric=f"{slug} measure",
                          value=26, value_text="26%", unit="%", period="2026")],
                   [hyp("h1", title, node=node, mechanism="demand_volume_shift",
                        supporting=["c1"])])
    ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)  # type: ignore[arg-type]


def test_a_drug_market_and_a_care_payment_shift_are_two_theses_never_one(tmp_path: Path) -> None:
    """The pilot's shape: an Alzheimer drug-market thesis, then a cash-pay care-delivery article
    arguing rising US demand too. At child nodes they are two theses, linked as siblings in the
    same area — never merged. NEGATIVE pin: a second drug-market article at the same node,
    mechanism, direction and geography still UPDATES the first thesis (identity is unchanged)."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    _article(pipe, "alz", "Alzheimer's drug sales could grow 26% in 2026.",
             "healthcare.pharma_biotech", "Alzheimer's drugs open a large market")
    _article(pipe, "cash", "Cash-pay healthcare visits rose 26% in 2026.",
             "healthcare.services_payers", "Patients pay cash for more care")
    pipe.finish_run(RunStatus.SUCCEEDED)
    theses = {t.key_node: t for t in pipe.store.theses()}
    assert set(theses) == {"healthcare.pharma_biotech", "healthcare.services_payers"}
    alz, cash = theses["healthcare.pharma_biotech"], theses["healthcare.services_payers"]
    # known nodes: active, labelled by their child (an unknown node is held REVIEW_NEEDED)
    assert alz.status is ThesisStatus.ACTIVE and cash.status is ThesisStatus.ACTIVE
    assert alz.sector.startswith("Pharmaceuticals and biotechnology")
    assert cash.sector.startswith("Healthcare services and payers")
    rel = {r.relation.value for r in pipe.store.relations(alz.thesis_id)
           if cash.thesis_id in (r.from_thesis, r.to_thesis)}
    assert rel == {"SIBLING"}  # same parent sector, different child: linked, never merged
    pipe.start_run("ingest", as_of=AS_OF)
    _article(pipe, "alz2", "Alzheimer's drug sales could rise 26% in 2026, a second source says.",
             "healthcare.pharma_biotech", "Alzheimer's drugs open a large market")
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert len(pipe.store.theses()) == 2
    t = pipe.store.thesis(alz.thesis_id)
    assert t is not None and t.current_version == 2
