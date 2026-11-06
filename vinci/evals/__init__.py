"""The synthesis-prompt evaluation harness — MEASUREMENT ONLY.

Operator ruling, 2026-11-06: "Build it first".

Every change to how the synthesis prompt is built is measured here before it ships: a frozen gold
set of 644 graded claims (`tests/fixtures/synthesis_gold/`), a panel of pages chosen by rule
(`vinci/evals/synthesis_panel.json`), a $0 replay of each panel page's request through production
code, deterministic fidelity metrics, and a pre-registered decision rule
(`docs/records/2026-11-06-synthesis-eval-harness-design.md`, RUNBOOKS "Changing the synthesis
prompt").

NOTHING ON THE DECISION PATH IMPORTS THIS PACKAGE. It reads pages and prompts; it writes no page,
sets no parameter and never reads a forward return. Fidelity to the page's own facts is the only
target it measures.
"""
