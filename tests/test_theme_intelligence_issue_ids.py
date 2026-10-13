"""A verification issue's id includes its DETAIL (engine fix, 2026-10-13, PR #703).

Found by the SYNTHETIC stress registry (tests/theme_intelligence_stress.py): two articles of one
run that split one identity key into different products each raised PRODUCT_SPLIT on the same key.
`Engine._issue` hashed run, scope, ref and code but not the detail, so both issues had one id and
the append-only store refused the second (StoreIntegrityError) — that article failed. The id now
hashes the detail, as `verify._issue` always has. No network, no model call.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

from tests.theme_intelligence_stress import END, _article, _doc
from tests.theme_intelligence_support import fetched, make_pipeline
from vinci.theme_intelligence.schemas import RunStatus


def test_two_articles_of_one_run_splitting_one_key_by_product_are_both_recorded(
        tmp_path: Path) -> None:
    """A thesis exists on a key (NAND); one run then reads two articles on the same key naming
    other products (enterprise SSD, client SSD) with no shared evidence — each a PRODUCT_SPLIT.
    The engine's issue id left out the detail, so both issues shared one id and the append-only
    store refused the second (StoreIntegrityError): that article failed. Both are processed, with
    two issues of two ids."""
    pipe = make_pipeline(tmp_path)
    rng = random.Random(1)
    node, mech = "ai_infrastructure.memory", "pricing_cycle"

    def read(subject: str, slug: str, as_of: date) -> str:
        blocks, x, title = _article((node, mech, subject, "Global"), "straddle", as_of, rng,
                                    uncaptured=False, tag=slug)
        doc = _doc(slug, title, as_of, blocks)
        res = pipe.process_document(doc, fetched(doc), url=doc.canonical_url,
                                    source_id="trendforce", as_of=as_of, fixture=x,
                                    completeness_fixture={"figure_reviews": [],
                                                          "block_reviews": []})
        return res.status

    first = END - timedelta(days=7)
    pipe.start_run("scan", as_of=first, window_from=first - timedelta(days=6), window_to=first)
    assert read("NAND", "split-0", first) == "PROCESSED"
    pipe.finish_run(RunStatus.SUCCEEDED)
    run = pipe.start_run("scan", as_of=END, window_from=END - timedelta(days=6), window_to=END)
    assert [read("enterprise SSD", "split-1", END), read("client SSD", "split-2", END)] == [
        "PROCESSED", "PROCESSED"]
    pipe.finish_run(RunStatus.SUCCEEDED)
    splits = [i for i in pipe.store.issues(run_id=run.run_id) if i.code == "PRODUCT_SPLIT"]
    assert len(splits) == 2 and len({i.issue_id for i in splits}) == 2
    assert len({i.ref_id for i in splits}) == 1  # one key, two products — the colliding case
