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


def all_registries() -> PanelRegistry:
    """Every registered panel, across every tier.

    `followed.json` is ONE file describing a name's whole grid, so validating it against a single
    tier's registry rejects legitimate declarations from the others. That is not hypothetical: the
    moment GOOGL declared `multiple_and_price` (universal) the emitter — which passed the COHORT
    registry — refused the whole file and took the grid down with it. The declaration reader has to
    know about every tier, because the file does.
    """
    from vinci.panels import default_registry
    from vinci.panels_theme import theme_registry
    from vinci.panels_universal import universal_registry

    merged = PanelRegistry()
    for reg in (universal_registry(), default_registry(), theme_registry()):
        for key in reg:
            spec = reg.get(key)
            assert spec is not None
            merged.register(spec)
    return merged


def read_declarations(
    *, root: Path | None = None, registry: PanelRegistry | None = None,
) -> dict[str, dict[str, dict[str, str]]]:
    """`{ticker: {panel_key: {config_key: value}}}`, validated against the registry.

    VALIDATED AT READ, NOT AT RENDER. A typo'd panel key would otherwise surface as a missing tile
    on a page nobody was watching — the blank-tile failure one layer up from the gating rule. An
    unknown key raises here, naming the registered set, before anything renders.
    """
    registry = registry or all_registries()
    p = followed_path(root)
    if not p.exists():
        # NOT `{}`. An absent file and a file in which nobody declared anything are the same value
        # downstream — every cohort panel `not_in_set`, a grid of silent tiles — and the first of
        # those is a wiring bug (a wrong root, a run from the wrong cwd). Absent-vs-broken, at the
        # edge this module exists to guard.
        raise PanelDeclarationError(
            f"no follow list at {p} — panel declarations live in it, and returning 'nobody "
            f"declared anything' for a missing file would render every cohort panel as silence")
    raw: dict[str, Any] = json.loads(p.read_text())
    out: dict[str, dict[str, dict[str, str]]] = {}
    seen: set[str] = set()
    for raw_ticker, entry in sorted(raw.items()):
        # UPPERCASED, as `vinci/followed.py` does at the same edge. A lowercase key would otherwise
        # declare nothing at all — `declared_for("GOOGL", …)` misses `"googl"` — and the panel would
        # render as `not_in_set`, which is indistinguishable from "this name has no such question".
        ticker = str(raw_ticker).upper()
        if ticker in seen:
            raise PanelDeclarationError(
                f"{ticker} appears more than once in the follow list (keys differing only by "
                f"case); one set of panel declarations would be silently discarded")
        seen.add(ticker)
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
            # BOTH KINDS OF CONFIG ARE ACCEPTED HERE and each is checked against its own schema:
            # `config_schema` keys parameterise what the panel PROBES, `render_config` keys what it
            # SAYS. A name declares them in one object because that is how an operator thinks about
            # it; the two are only separate in the spec, where the no-op guard differs.
            known = set(spec.config_schema) | set(spec.render_config)
            unknown = sorted(set(cfg) - known)
            if unknown:
                raise PanelDeclarationError(
                    f"{ticker}/{key} supplies config {unknown} that the panel does not read — it "
                    f"declares {sorted(known)}. A config key nothing consumes is a silent no-op, "
                    f"which is how a name appears configured and is not.")
            for ck, opt in spec.render_config.items():
                if ck not in cfg or not opt.allowed:
                    continue
                if str(cfg[ck]) not in opt.allowed:
                    # THE FALSIFIER, AS A MACHINE CHECK. The record attaches one to
                    # `load_bearing_axis`: "a third R3 record matching neither archetype, at which
                    # point the field must be a statement rather than an enum." A name that fits
                    # none of the listed values raises HERE, at declare time, naming that ruling —
                    # rather than being quietly mis-filed under whichever value was closest.
                    raise PanelDeclarationError(
                        f"{ticker}/{key} sets {ck}={cfg[ck]!r}, which is not one of "
                        f"{sorted(opt.allowed)}. If this name genuinely fits none of them, that is "
                        f"the falsifier on this field: it must become a free statement rather than "
                        f"a closed set, and that is an operator ruling — not a value to force.")
            per_name[key] = {k: str(v) for k, v in cfg.items()}
        out[ticker] = per_name
    return out


def declared_for(
    ticker: str, declarations: dict[str, dict[str, dict[str, str]]],
) -> frozenset[str]:
    """The panel keys this name declares — SUBSTANCE. Absent name ⇒ declares nothing.

    The lookup is UPPERCASED to match `read_declarations`, so a caller holding a ticker in the
    store's own casing cannot silently miss a declaration and render `not_in_set`.
    """
    return frozenset(declarations.get(ticker.upper(), {}))


def config_for(
    ticker: str, panel_key: str, declarations: dict[str, dict[str, dict[str, str]]],
) -> dict[str, str]:
    """This name's config for one panel — FORM. Empty when undeclared or unconfigured."""
    return dict(declarations.get(ticker.upper(), {}).get(panel_key, {}))
