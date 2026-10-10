"""Living equity-theme intelligence — a RESEARCH DISCOVERY and PRIORITISATION tool.

It discovers permitted public research articles from eight publisher channels, extracts their
source-anchored evidence, named companies and risks, keeps a persistent, versioned registry of
investment theses, and issues a decision-first weekly briefing of identical nine-section Living
Thesis Cards. "RESEARCH NOW" means *allocate analyst attention* — never buy.

BOUNDARY (non-negotiable). This package is not on the fund's decision path:
- nothing in the screen / ranker / dossier / verdict / scoring / freeze / ledger / portfolio code
  imports it, and it imports none of them (pinned by an AST test);
- it keeps its OWN database (`data/theme_intelligence/registry.db`) and never opens the fund's;
- it has no buy / sell / target / weight field and no broker or trading path;
- its priority rules are face-validity constants, never tuned on forward returns or on the
  third-party audit's outcomes.

Pipeline (`pipeline.py`): discover → fetch (polite, honest UA, robots) → parse → extract (LLM
pass 1, cached by content) → verify (deterministic) → resolve securities (SEC) → match / version
(`engine.py`) → prioritise (`priority.py`, deterministic) → review (LLM pass 2) → render cards and
the weekly report (`cards.py`, `report.py`).
"""
