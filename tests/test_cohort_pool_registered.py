"""THE COHORT POOL READS A LINE AS ITS ISSUER REGISTERS IT (2026-10-27).

The pool's type gate admits whatever the feed types `CS`, and the feed types notes and preferred
depositaries `CS`. Measured on the committed pool (18,827 rows across seven runs): 318 rows, 57
lines, were registered on their issuers' own cover pages as debt (178 rows — T-Mobile's TMUSI /
TMUSL / TMUSZ, Xcel's XELLL, Adamas's ADAMG …) or as preferred beside a common traded under
another symbol (140 rows — MCHPP, ACGLN, the bank depositaries …), and each one sat in its
industry's median as if it were a company. 86 of the 1,245 (run, industry) medians moved when they
were removed.

The committed rows were pruned once, by the measurement in
`docs/records/2026-10-27-rename-alias-and-registered-pool.md`; from then on the builder applies the
universe's own rule (`EntityResolver.registered_line` → `RegisteredLine.excluded_class`).
"""

from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
POOL = ROOT / "data" / "snapshots" / "cohort_pool.jsonl"


def test_the_pool_builder_applies_the_universes_registered_line_rule() -> None:
    """PIN THE CALL SITE: the same reader and the same rule as `universe.build_universe` Axis 3,
    read for CS lines only, counted on its own line of the summary."""
    src = (ROOT / "scripts" / "build_cohort_pool.py").read_text()
    assert "resolver.registered_line(ident.cik, ident.ticker, end)" in src
    assert "reg.excluded_class is not None" in src
    assert 'sec_types.get(ticker) == "CS"' in src
    assert "skipped_registered += 1" in src


def test_the_foreign_private_issuer_stage_is_poolable() -> None:
    """The 2026-08-26 ruling (an industry's move is the industry's, wherever the issuer files)
    survives the 2026-10-27 one that took foreign private issuers out of the screened population."""
    src = (ROOT / "scripts" / "build_cohort_pool.py").read_text()
    m = re.search(r"POOLABLE = \(([^)]*)\)", src)
    assert m and "foreign_private_issuer" in m.group(1)


def test_no_committed_pool_row_is_a_line_its_issuer_registers_as_debt_or_preferred() -> None:
    """END TO END on the committed artifact, against the lines the measurement found — the
    observed failure shapes, each named. A re-run of the old builder would put them back."""
    pooled = {json.loads(x)["ticker"] for x in POOL.read_text().splitlines() if x.strip()}
    registered = {"MCHPP", "ACGLN", "TMUSI", "TMUSL", "TMUSZ", "XELLL", "ADAMG", "ADAMH", "ADAMI",
                  "ADAMO", "ADAML", "ADAMZ", "GOOGM", "GOOGN"}
    assert pooled & registered == set()
    # and the negative: a common stock the feed NAMES like a bond ("Our Bond, Inc. Common
    # Stock") is a company, and stays a peer
    assert "OBAI" in pooled
