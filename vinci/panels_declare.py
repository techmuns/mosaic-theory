"""(phase 4) WHICH PANELS A NAME RUNS, AND WITH WHAT CONFIG — read from `data/followed.json`.

The approved design says *"a NAME declares which panels it runs and with what config, beside its
sleeve"*, and this is that declaration. It is the missing link that made the cohort tier real: until
a name could name its own note, `commissioning` carried Alphabet's heading on the SHARED spec and
every other filer's panel would have probed the wrong accounts.

DECLARATION IS SUBSTANCE, CONFIG IS FORM, and they are separate fields for the reason phase 2
separated them: `panels` lists the economic questions this name has, `config` says where this filer
happens to disclose the answer. A name that drops a panel from `panels` gets silence; a name that
declares one without the config it needs gets a LOUD refusal naming the key.

WHY THE NOTE NAME CANNOT BE A REPO-WIDE CONSTANT — measured on real filings, 2026-09-10:

  * GOOGL discloses fixed assets under *"Supplemental Financial Statement Information - Property and
    Equipment"*; NFLX under *"Balance Sheet Components - Schedule of Property and Equipment and
    Accumulated Depreciation"*. Same economic question, two headings, neither derivable from the
    other.
  * Segment economics is worse. For UBER, IT and VRRM the FIRST report matching /segment/ AND
    /(details)/ is a GOODWILL-BY-SEGMENT table — the right name on the wrong numbers. GOOGL's 10-Q
    carries two economics-matching reports and `_pick_report` rightly refuses as ambiguous; naming
    the report here is what resolves it.
  * WERN publishes NO property-named details report at all. It is a REFUSAL, not a rename — worth
    recording because the design used a trucking name as its rename exemplar and that is not what
    WERN's filing actually does.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vinci.panels import PanelRegistry

#: Per-name panel declarations live beside the sleeve, under this key.
PANELS_KEY = "panels"


class PanelDeclarationError(RuntimeError):
    """A name declares a panel that does not exist, or config no panel reads."""


def followed_path(root: Path | None = None) -> Path:
    return (root or Path.cwd()) / "data" / "followed.json"


def read_declarations(
    *, root: Path | None = None, registry: PanelRegistry,
) -> dict[str, dict[str, dict[str, str]]]:
    """`{ticker: {panel_key: {config_key: value}}}`, validated against the registry.

    VALIDATED AT READ, NOT AT RENDER. A typo'd panel key would otherwise surface as a missing tile
    on a page nobody was watching — the blank-tile failure one layer up from the gating rule. An
    unknown key raises here, naming the registered set, before anything renders.
    """
    p = followed_path(root)
    if not p.exists():
        return {}
    raw: dict[str, Any] = json.loads(p.read_text())
    out: dict[str, dict[str, dict[str, str]]] = {}
    for ticker, entry in sorted(raw.items()):
        decl = (entry or {}).get(PANELS_KEY)
        if decl is None:
            continue
        if not isinstance(decl, dict):
            raise PanelDeclarationError(
                f"{ticker}: '{PANELS_KEY}' must map panel keys to their config, got "
                f"{type(decl).__name__}")
        per_name: dict[str, dict[str, str]] = {}
        for key, cfg in decl.items():
            spec = registry.get(key)
            if spec is None:
                raise PanelDeclarationError(
                    f"{ticker} declares panel {key!r}, which is not registered — registered: "
                    f"{sorted(registry.keys())}")
            cfg = cfg or {}
            if not isinstance(cfg, dict):
                raise PanelDeclarationError(
                    f"{ticker}/{key}: config must be an object, got {type(cfg).__name__}")
            unknown = sorted(set(cfg) - set(spec.config_schema))
            if unknown:
                raise PanelDeclarationError(
                    f"{ticker}/{key} supplies config {unknown} that the panel does not read — it "
                    f"declares {sorted(spec.config_schema)}. A config key nothing consumes is a "
                    f"silent no-op, which is how a name appears configured and is not.")
            per_name[key] = {k: str(v) for k, v in cfg.items()}
        out[ticker] = per_name
    return out


def declared_for(
    ticker: str, declarations: dict[str, dict[str, dict[str, str]]],
) -> frozenset[str]:
    """The panel keys this name declares — SUBSTANCE. Absent name ⇒ declares nothing."""
    return frozenset(declarations.get(ticker, {}))


def config_for(
    ticker: str, panel_key: str, declarations: dict[str, dict[str, dict[str, str]]],
) -> dict[str, str]:
    """This name's config for one panel — FORM. Empty when undeclared or unconfigured."""
    return dict(declarations.get(ticker, {}).get(panel_key, {}))
