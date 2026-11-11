"""Main against a branch — the harness's first comparison (design record §6, RUNBOOKS §n).

THREE STEPS, the first two at $0:

1. ``compare_requests`` — every panel page's request captured at BASE's code and at CAND's
   (`replay.capture_at`), with the same frozen inputs and the same named transforms. It reports per
   page whether the two requests differ, where, and each section's size. **When no page's request
   differs, the comparison is REFUSED**: the change does not reach the synthesis request by replay
   (a `mechanical.py` label change without its transform is exactly this), and drawing it would buy
   two samples of one prompt.
2. ``run_compare`` — PAID: the captured requests are drawn page by page, BASE then CAND, five
   draws each, every draw behind the guard and one cap (`replay.run_request`). Requests and raw
   draws are written OUTSIDE the repository (they carry licensed transcript text).
3. ``score_run`` — $0: every draw's prose units scored by the deterministic metrics, and the
   pre-registered rule applied: the declared target improves at ``p_lower <= 0.05``; no other
   metric worsens at ``p_upper <= 0.05``; lean tallies, modal leans and proposals per page;
   instruction echo and prompt size reported; the held-out pages read on their own. A
   NO-WORSENING-ONLY registration (``no_worsening``, no target) applies the second half alone —
   for a page set where the change's target cannot fire (#921's on the panel).

ONE REGISTRATION, ONE RUN. A registration pins every page's request bytes (``requests``: the
sha256 of each request as sent) and is drawn once: ``run_compare`` refuses a sha the approval's
ledger already records, or a capture whose bytes differ from the pinned ones; ``score_run``, given
the ledger, reports every run recorded under the sha and refuses when more than one holds draws.
"""
from __future__ import annotations

import dataclasses
import difflib
import hashlib
import json
import re
import subprocess
import time
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vinci.dossier.schemas import MechanicalLayer
from vinci.dossier.synthesis import SYNTHESIS_TOOL, _decode_escapes
from vinci.dossier.verdict import derive_proposal, split_lean
from vinci.evals import gold as gd
from vinci.evals import metrics as mt
from vinci.evals import replay as rp
from vinci.evals import stats as sx
from vinci.evals.capture_child import pre_synthesis_mech
from vinci.evals.units import draw_units

CONDITIONS = ("BASE", "CAND")
ALPHA = 0.05
REPLICATION_REQUIRED = "replication required"
DOES_NOT_SHIP = "does not ship"


@dataclass(frozen=True)
class PageDiff:
    ticker: str
    identical: bool
    user_diff_lines: int
    system_equal: bool
    base_sizes: dict[str, int]
    cand_sizes: dict[str, int]


@dataclass
class Captured:
    base_ref: str
    cand_ref: str
    transforms: tuple[str, ...]
    requests: dict[tuple[str, str], rp.Request] = field(default_factory=dict)
    diffs: list[PageDiff] = field(default_factory=list)
    #: What the requests were built from beyond the code: the CIQ root, and per page the comps
    #: export handed to the transforms and the transcripts, each by sha256.
    inputs: dict[str, Any] = field(default_factory=dict)

    @property
    def reaches(self) -> bool:
        return any(not d.identical for d in self.diffs)


def compare_requests(base_ref: str, cand_ref: str, *, tickers: Sequence[str] | None = None,
                     transforms: Sequence[str] = (), panel: dict[str, Any] | None = None,
                     ciq_root: Path = rp.DEFAULT_CIQ_ROOT) -> Captured:
    """Step 1, $0. Inputs are the frozen panel's (blob and transcript sha256s checked); with
    transforms, each page's comps export in ``ciq_root`` is handed to them (proved the page's own
    where it is read, `variants.own_comps`)."""
    p = panel or rp.load_panel_file()
    out = Captured(base_ref, cand_ref, tuple(transforms))
    out.inputs = {"ciq_root": str(Path(ciq_root).resolve()), "pages": {}}
    for t in tickers or p["panel"]:
        page, tx = rp.panel_inputs(t, panel=p, ciq_root=ciq_root)
        comps, ciq, recorded = _transform_inputs(t, Path(ciq_root), transforms)
        base = rp.capture_at(base_ref, page, tx, transforms=transforms, comps=comps, ciq=ciq)
        cand = rp.capture_at(cand_ref, page, tx, transforms=transforms, comps=comps, ciq=ciq)
        out.requests[(t, "BASE")], out.requests[(t, "CAND")] = base, cand
        out.diffs.append(page_diff(t, base, cand))
        out.inputs["pages"][t] = {**recorded, "transcripts": p["pages"][t]["transcripts"]}
    return out


def _transform_inputs(ticker: str, ciq_root: Path, transforms: Sequence[str]
                      ) -> tuple[Path | None, Path | None, dict[str, Any]]:
    """The CIQ inputs a page's transforms read — its comps export and its own CIQ folder (for a
    transform re-reading its exports, `variants.Context.ciq`) — and their sha256 record, as a
    registration records them (`compare_requests`) and a score checks them (`arm_layer`)."""
    comps = rp.comps_export(ticker, ciq_root=ciq_root) if transforms else None
    ciq = (ciq_root / ticker) if transforms and (ciq_root / ticker).is_dir() else None
    return comps, ciq, {
        "comps": ({"file": comps.name, "sha256": hashlib.sha256(comps.read_bytes()).hexdigest()}
                  if comps is not None else None),
        "ciq": ({f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                 for f in sorted(ciq.iterdir()) if f.is_file() and not f.name.startswith(".")}
                if ciq is not None else None)}


def page_diff(ticker: str, base: rp.Request, cand: rp.Request) -> PageDiff:
    """Two requests compared WHOLE and in order (`Request.wire`: every kwarg — SYSTEM, USER,
    tools, tool_choice, cache — key order included) — a change to the system prompt alone, or to
    the order of the tool schema's fields, reaches the comparison as surely as one to the
    facts."""
    diff = list(difflib.unified_diff(base.user.splitlines(), cand.user.splitlines(),
                                     lineterm="", n=0))
    return PageDiff(ticker, base.wire() == cand.wire(), len(diff), base.system == cand.system,
                    mt.prompt_size(base), mt.prompt_size(cand))


#: An impact run's export (`vinci.impact`; `impact-captures-format.md`): the side folders.
IMPACT_SIDES = {"BASE": "base", "CAND": "head"}


#: What the manifest records per page and arm: each file's sha256, and the export's proof that
#: re-capturing from `layer.json` at the arm's code gives its request byte for byte.
IMPACT_ARM_KEYS = ("built_sha256", "layer_sha256", "request_wire_sha256", "recapture_equal")


def _impact_arm_files(export: Path, ticker: str, cond: str,
                      want: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """One arm of one page of an impact export — its $0 page, its layer's JSON and its request's
    kwargs — each checked against the sha256 the export's manifest records, or refused. An arm
    whose layer the export did not prove is the one its request carried (`recapture_equal`) is
    refused: it would be scored against a layer the request may not have sent."""
    d = export / IMPACT_SIDES[cond] / ticker
    if missing := [k for k in IMPACT_ARM_KEYS if k not in want]:
        raise rp.ReplayError(f"{export / 'manifest.json'}: {ticker}:{cond} records no {missing} "
                             "— the arm cannot be checked, so nothing is registered, drawn or "
                             "scored from it")
    if want["recapture_equal"] is not True:
        raise rp.ReplayError(f"{ticker}:{cond}: the export does not prove its layer.json is the "
                             "layer its request carried (recapture_equal is "
                             f"{want['recapture_equal']!r}) — it is not scored against it")
    raw: dict[str, bytes] = {}
    for name, key in (("built.json", "built_sha256"), ("layer.json", "layer_sha256")):
        raw[name] = (d / name).read_bytes()
        if (got := hashlib.sha256(raw[name]).hexdigest()) != want[key]:
            raise rp.ReplayError(f"{d / name}: sha256 {got[:12]} is not the manifest's "
                                 f"{want[key][:12]} — the export moved after its run, so nothing "
                                 "is registered, drawn or scored from it")
    kwargs: dict[str, Any] = json.loads((d / "request.json").read_text(encoding="utf-8"))
    if (got := hashlib.sha256(rp.wire(kwargs).encode()).hexdigest()) != want[
            "request_wire_sha256"]:
        raise rp.ReplayError(f"{d / 'request.json'}: wire sha256 {got[:12]} is not the "
                             f"manifest's {want['request_wire_sha256'][:12]} — the export moved")
    built: dict[str, Any] = json.loads(raw["built.json"])
    return built, raw["layer.json"].decode("utf-8"), kwargs


def captured_from_impact(export: Path, *, panel: dict[str, Any] | None = None) -> Captured:
    """THE COMPARISON AN IMPACT RUN CAPTURED (`register --from-impact`; the #953 retrospective,
    coordinator 2026-11-11). Every request in the export was built FRESH, by each arm's own code
    from a $0 build on the same inputs — never a replay of the frozen page — so it is read as it
    was captured: the two commits, each page's two requests (in the panel's order), each file
    checked against the manifest's sha256. Its identity — the folder, the manifest's sha256 and
    every page's hashes — is recorded as the registration's `inputs["impact"]`."""
    export = Path(export).resolve()
    raw = (export / "manifest.json").read_bytes()
    m = json.loads(raw)
    p = panel or rp.load_panel_file()
    pages = list(m["pages"])
    order = [t for t in p["panel"] if t in pages] + [t for t in pages if t not in p["panel"]]
    out = Captured(str(m["base"]["sha"]), str(m["cand"]["sha"]), ())
    for t in order:
        reqs = {cond: rp.Request(_impact_arm_files(export, t, cond,
                                                      m["pages"][t].get(cond) or {})[2])
                for cond in CONDITIONS}
        out.requests[(t, "BASE")], out.requests[(t, "CAND")] = reqs["BASE"], reqs["CAND"]
        out.diffs.append(page_diff(t, reqs["BASE"], reqs["CAND"]))
    out.inputs = {"impact": {"dir": str(export), "manifest_sha256": hashlib.sha256(
        raw).hexdigest(), "pages": m["pages"], "inputs": m.get("inputs", {})}}
    return out


def impact_arm(reg: Registration, ticker: str, cond: str) -> tuple[dict[str, Any],
                                                                   MechanicalLayer, str | None]:
    """An impact registration's arm, as its own request carried it: its $0 page, its layer and
    the transcripts its request sent (the USER's transcripts section), each file checked against
    the hashes the registration recorded (STATE row 53 item 6, for fresh builds)."""
    imp = reg.inputs["impact"]
    built, layer, kwargs = _impact_arm_files(Path(imp["dir"]), ticker, cond,
                                             imp["pages"][ticker][cond])
    sec = mt.user_sections(rp.Request(kwargs).user).get("transcripts")
    # the transcripts AS SENT, without the section's header: the header is instruction text, and
    # M-ABSENT would read a quote of it as "transcript-only" (the frozen path's is the raw text)
    head = mt._HEADER.match(sec) if sec is not None else None
    tx = sec[head.end():] if sec is not None and head is not None else sec
    return built, MechanicalLayer.model_validate_json(layer), tx


def refuse_if_unreached(c: Captured) -> None:
    if not c.reaches:
        raise rp.ReplayError(
            f"{c.cand_ref} sends the request {c.base_ref} sends on every page "
            f"({', '.join(d.ticker for d in c.diffs)}): the change does not reach the synthesis "
            "request by replay. A change to the mechanical layer's words needs its transform "
            "(variants.py; RUNBOOKS §n step 2) — drawing this would compare one prompt with itself")


# ------------------------------------------------------------------------- the registration

#: The files whose definitions decide a score: the harness's scorer, the production modules it
#: reads its definitions from (`TRAILING_ONLY_NOTE`, `material_direction_flags`, `SYNTHESIS_TOOL`,
#: `split_lean`/`derive_proposal`), and what builds the layer and the inputs a draw is scored
#: against. A score is refused unless they are byte-identical to the registered ones. (Fix 3a's
#: run, `cceba9d9`, was registered and scored by the files at fc79a7be, before this list grew.)
SCORER_FILES = ("vinci/evals/metrics.py", "vinci/evals/units.py", "vinci/evals/compare.py",
                "vinci/evals/stats.py", "vinci/evals/panel.py", "vinci/dossier/synthesis.py",
                "vinci/dossier/mechanical.py", "vinci/dossier/verdict.py",
                # #926 review F7: what the score also runs — the layer a draw is scored against
                # (`capture_child.pre_synthesis_mech`), the frozen inputs (`replay.panel_inputs`
                # and the panel file) and the schemas the layer is validated by
                "vinci/evals/capture_child.py", "vinci/evals/replay.py",
                "vinci/evals/synthesis_panel.json", "vinci/dossier/schemas.py",
                # M-GAP reads each frozen page's gap types (fix 4a's gap test, frozen 2026-11-09)
                "vinci/evals/synthesis_gap_types.json")


def _fingerprint(files: dict[str, bytes]) -> str:
    h = hashlib.sha256()
    for f in SCORER_FILES:
        h.update(f.encode() + b"\0" + files[f] + b"\0")
    return h.hexdigest()


def scorer_fingerprint(root: Path = rp.ROOT) -> str:
    return _fingerprint({f: (root / f).read_bytes() for f in SCORER_FILES})


#: The PRODUCTION files the metrics borrow their definitions from (B's check of order 8, gap 1):
#: what a candidate edits, so they are BASE's bytes, always — prospective or retrospective.
PRODUCTION_SCORER_FILES = ("vinci/dossier/synthesis.py", "vinci/dossier/mechanical.py",
                           "vinci/dossier/verdict.py", "vinci/dossier/schemas.py")
#: The harness's OWN scorer files: a reviewed harness, origin/main's at registration
#: (`scorer_ref`), re-checked at the draw and the score.
HARNESS_SCORER_FILES = tuple(f for f in SCORER_FILES if f not in PRODUCTION_SCORER_FILES)


def _scorer_files_at(ref: str, root: Path,
                     files: Sequence[str] = SCORER_FILES) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for f in files:
        done = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{f}"], capture_output=True)
        if done.returncode != 0:
            raise rp.ReplayError(f"{f} cannot be read at {ref} (git show exited "
                                 f"{done.returncode}): BASE's scorer is not known, so nothing is "
                                 "registered, drawn or scored")
        out[f] = done.stdout
    return out


def _is_ancestor(ref: str, of: str, root: Path) -> bool:
    rc = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", ref, of],
                        capture_output=True).returncode
    if rc not in (0, 1):
        raise rp.ReplayError(f"cannot place {ref} against {of} (git exited {rc}): fetch {of}; "
                             "the fixed scorer is not guessed")
    return rc == 0


def _refuse_unless_files_at(files: Sequence[str], ref: str, root: Path, what: str) -> None:
    here = {f: (root / f).read_bytes() for f in files}
    there = _scorer_files_at(ref, root, files)
    if differ := [f for f in files if here[f] != there[f]]:
        raise rp.ReplayError(f"the scorer here is not {what} at {ref}: {differ} differ — a "
                             "candidate never scores itself (RG-D12)")


def refuse_unless_scored_by_base(base_ref: str, *, root: Path = rp.ROOT) -> str:
    """THE PRODUCTION FILES THE METRICS BORROW ARE BASE'S (fix request 2, RG-D12; B's scope,
    operator 2026-11-11). The metrics read production's own parsers and definitions
    (`PRODUCTION_SCORER_FILES`), so a candidate that edited them edited the scorer of its own
    measurement: fix 4a was registered by its own files (`755044b4…`), not its parent's
    (`03e384a3…`). This checkout must hold BASE's bytes for those four, naming any that differ.
    The harness's own files are NOT compared with BASE's — a BASE older than the harness (any
    retrospective) would be refused from every checkout that has the harness's rules — they are
    pinned to the registered fingerprint instead. This checkout's fingerprint is returned."""
    _refuse_unless_files_at(PRODUCTION_SCORER_FILES, base_ref, root, "BASE's production files")
    return scorer_fingerprint(root)


def fixed_scorer(base_ref: str, *, root: Path = rp.ROOT,
                 main_ref: str = "origin/main") -> tuple[str, str]:
    """THE FIXED SCORER, and the commit its harness is (RG-D12, merged with B's scope): BASE's
    production files (`refuse_unless_scored_by_base`) and ``main_ref``'s harness at registration,
    recorded as the registration's `scorer_ref` — a reviewed harness, never one a candidate
    brings. One rule for a prospective change and a retrospective (#953) alike; a retrospective
    whose production files moved on main since BASE is registered from a checkout holding BASE's
    production files under main's harness. The fingerprint and the harness commit return."""
    fp = refuse_unless_scored_by_base(base_ref, root=root)
    from vinci.evals.builds import _resolve
    main = _resolve(main_ref, repo=root)
    _refuse_unless_files_at(HARNESS_SCORER_FILES, main, root, f"{main_ref}'s harness")
    return fp, main


def refuse_unless_registered_scorer(reg: Registration, *, root: Path = rp.ROOT,
                                    main_ref: str = "origin/main") -> None:
    """At a draw or a score (RG-D12): the scorer here is the registered one; its production files
    are BASE's; its harness is the one at `scorer_ref`, a commit on ``main_ref``. A registration
    written before `scorer_ref` existed must be BASE's scorer whole."""
    if (here := scorer_fingerprint(root)) != reg.scorer:
        raise rp.ReplayError(f"the scorer here ({here[:12]}) is not the registered scorer "
                             f"({reg.scorer[:12]}): draw and score from the checkout it was "
                             "registered from")
    _refuse_unless_files_at(PRODUCTION_SCORER_FILES, reg.base_ref, root, "BASE's production files")
    if reg.scorer_ref is None:
        if _fingerprint(_scorer_files_at(reg.base_ref, root)) != reg.scorer:
            raise rp.ReplayError(f"registration {reg.sha[:12]} records the scorer "
                                 f"{reg.scorer[:12]}, which is not BASE's: a candidate never "
                                 "scores itself")
        return
    if not _is_ancestor(reg.scorer_ref, main_ref, root):
        raise rp.ReplayError(f"registration {reg.sha[:12]} records its harness at "
                             f"{reg.scorer_ref[:12]}, which is not on {main_ref}: a harness is a "
                             "reviewed one, never a candidate's")
    _refuse_unless_files_at(HARNESS_SCORER_FILES, reg.scorer_ref, root, "the registered harness")


#: Fields added after PR 2's first registrations were written: serialised only when set, so a
#: registration written before them keeps the sha256 its ledger records.
_LATER_FIELDS: dict[str, Any] = {"no_worsening": False, "requests": {}, "ship_alpha": None,
                                 "replicates": None, "inputs": {}, "note": None,
                                 "no_worsening_families": {}, "scorer_ref": None}

#: The fields that make two registrations THE SAME COMPARISON: what is drawn, how often, what must
#: improve and by what rule and scorer. Everything else — the words (`note`), the record of what
#: was read (`inputs`, a path's spelling included), the derived `held_out` and the replication link
#: (`replicates`) — can differ between two registrations of one design (#926 review: two shas over
#: one design were each drawable once).
DESIGN_FIELDS = ("base_ref", "cand_ref", "transforms", "pages", "draws", "targets", "alpha",
                 "ship_alpha", "scorer", "requests", "no_worsening", "rule",
                 "no_worsening_families")


def gated(metric: str, families: Sequence[str]) -> str:
    """The name a metric's GATED series is scored and reported under."""
    return f"{metric}[{'+'.join(families)}]"


def ungated(metric: str, families: Sequence[str]) -> str:
    """The name of the rest of its families, reported, never gated."""
    rest = [f for f in mt.METRIC_FAMILIES.get(metric, ()) if f not in families]
    return f"{metric}[reported: {'+'.join(rest)}]"


def design_differs(a: Any, b: Any) -> list[str]:
    """The design fields on which ``a`` and ``b`` differ — [] when they are one design."""
    return [k for k in DESIGN_FIELDS if getattr(a, k) != getattr(b, k)]


def run_registration(out_dir: str | Path) -> Registration:
    """The registration a run folder was drawn under (its own ``registration.json``). A run the
    ledger records must be checkable: a missing file is refused, never skipped."""
    rec = Path(out_dir) / "registration.json"
    if not rec.exists():
        raise rp.ReplayError(f"the ledger records a run at {out_dir} with no registration.json: "
                             "every recorded run must be checkable")
    return Registration.from_json(rec.read_text(encoding="utf-8"))


REPLICATION_RULE = ("design record §6 under the replication rule (coordinator, 2026-11-07): each "
                    "target p_lower <= ship_alpha after Holm across the targets ships; ship_alpha "
                    "< p_lower <= alpha counts only if a FRESH, separately registered replication "
                    "of the same design (`replicates`) reaches p_lower <= alpha; above alpha it "
                    "does not ship; no other class metric p_upper <= alpha; every lean, proposal "
                    "and the panel's committed-lean count explained if moved")

NO_WORSENING_RULE = ("design record §6.1, no-worsening only (registered where no target can "
                     "fire): no class metric p_upper <= alpha; every lean, proposal and the "
                     "panel's committed-lean count explained if moved")


def request_pins(c: Captured) -> dict[str, str]:
    """``TICKER:CONDITION`` → the sha256 of that request serialised in order (`Request.wire`)."""
    return {f"{t}:{cond}": hashlib.sha256(req.wire().encode()).hexdigest()
            for (t, cond), req in c.requests.items()}


@dataclass(frozen=True)
class Registration:
    """Written BEFORE any paid draw (record §6): what is compared, how often, which metric(s)
    must improve — or, ``no_worsening``, that none may worsen — with what scorer, and the bytes
    of every request to be drawn. Its sha256 is recorded in the budget ledger; ``score`` reads
    it, never a target given at score time."""

    base_ref: str
    cand_ref: str
    transforms: tuple[str, ...]
    pages: tuple[str, ...]
    draws: int
    targets: tuple[str, ...]
    held_out: tuple[str, ...]
    scorer: str
    alpha: float = ALPHA
    rule: str = ("design record §6: each target p_lower <= alpha after Holm across the targets; "
                 "no other class metric p_upper <= alpha; every lean, proposal and the panel's "
                 "committed-lean count explained if moved")
    no_worsening: bool = False
    requests: dict[str, str] = field(default_factory=dict)
    #: The replication rule: a first run ships at p_lower <= ship_alpha, needs a replication in
    #: (ship_alpha, alpha], and fails above alpha.
    ship_alpha: float | None = None
    #: A replication's: the sha256 of the registration it replicates (the same design, drawn
    #: fresh); its target needs p_lower <= alpha.
    replicates: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    #: What the registration states in words before the draw — what the target covers and what
    #: it does not. Part of the sha, so it cannot be written after the result.
    note: str | None = None
    #: A metric whose no-worsening check counts only these families (#929, the coordinator's
    #: ruling for #927: M-LABEL gated on bleed, trailing-only and pe-percentile-blocked; its
    #: gap-statement families reported, not gated). The whole metric is still reported.
    no_worsening_families: dict[str, list[str]] = field(default_factory=dict)
    #: The commit whose scorer files are the registration's fixed scorer (`fixed_scorer`): BASE
    #: for a prospective comparison, origin/main at registration for a retrospective one.
    scorer_ref: str | None = None

    def __post_init__(self) -> None:
        if self.ship_alpha is not None and not 0 < self.ship_alpha < self.alpha:
            raise ValueError(f"ship_alpha {self.ship_alpha} must lie in (0, alpha {self.alpha})")
        if self.ship_alpha is not None and self.no_worsening:
            raise ValueError("the replication rule decides a target; a no-worsening-only "
                             "registration has none")
        if self.replicates is not None and self.ship_alpha is None:
            raise ValueError("a replication is of a registration under the replication rule")
        if self.no_worsening:
            if self.targets:
                raise ValueError("a no-worsening-only registration declares no target")
        else:
            bad = [t for t in self.targets if t not in mt.UNIT_METRICS]
            if bad or not self.targets:
                raise ValueError(f"target(s) {bad or '(none)'} not a deterministic metric "
                                 f"({sorted(mt.UNIT_METRICS)}) — or register no-worsening only")
        if self.draws < 2 or not self.pages:
            raise ValueError("a registration needs pages and at least two draws per condition")
        for m, fams in self.no_worsening_families.items():
            known = mt.METRIC_FAMILIES.get(m)
            if known is None or m not in mt.GOLD_CLASS:
                raise ValueError(f"{m}: only a no-worsening metric with named families can be "
                                 f"gated on some of them ({sorted(mt.METRIC_FAMILIES)})")
            if m in self.targets:
                raise ValueError(f"{m} is a target; its no-worsening families do not apply")
            if not fams or len(set(fams)) != len(fams) or [f for f in fams if f not in known]:
                raise ValueError(f"{m}: families {fams} must be distinct names from {known}")

    def to_json(self) -> str:
        return json.dumps({k: v for k, v in self.__dict__.items()
                           if not (k in _LATER_FIELDS and v == _LATER_FIELDS[k])},
                          sort_keys=True, default=list)

    @property
    def sha(self) -> str:
        return hashlib.sha256(self.to_json().encode()).hexdigest()

    @classmethod
    def from_json(cls, text: str) -> Registration:
        d: dict[str, Any] = {k: tuple(v) if isinstance(v, list) else v
                             for k, v in json.loads(text).items()}
        return cls(**d)


def change_names(base_ref: str, cand_ref: str, tickers: Sequence[str],
                 repo: Path = rp.ROOT) -> set[str]:
    """Every ticker the CHANGE itself names: the subjects and bodies of the commits base..cand and
    the full text of every record they add — the pages a change may have been designed on."""
    def git(*a: str) -> str:
        return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True,
                              check=True).stdout
    text = git("log", "--format=%B", f"{base_ref}..{cand_ref}")
    for rec in git("diff", "--name-only", "--diff-filter=A", f"{base_ref}...{cand_ref}",
                   "--", "docs/records").split():
        text += git("show", f"{cand_ref}:{rec}")
    return {t for t in tickers
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(t)}(?![A-Za-z0-9])", text)}


def registered_pages(pages: Sequence[str] | None,
                     panel: dict[str, Any] | None = None) -> tuple[str, ...]:
    """The pages a registration may name: the frozen panel WHOLE, or TARGET pages outside it
    (record §6.1: a change whose target never fires on the panel is measured where it does, as
    #921 on NFLX). A panel page is never chosen — so no panel page can be dropped — and every
    page must be one the frozen file carries inputs for."""
    p = panel or rp.load_panel_file()
    if not pages:
        return tuple(p["panel"])
    chosen = tuple(pages)
    if len(set(chosen)) != len(chosen):
        raise rp.ReplayError(f"{list(chosen)}: a page is registered more than once")
    inside = [t for t in chosen if t in p["panel"]]
    if inside:
        raise rp.ReplayError(f"{inside}: a panel page is never chosen — the panel is registered "
                             "whole (no pages given), so none can be dropped; pages given are "
                             "target pages OUTSIDE it")
    unknown = [t for t in chosen if t not in p["pages"]]
    if unknown:
        raise rp.ReplayError(f"{unknown}: no frozen inputs in the panel file for these pages")
    return chosen


#: Metrics that may not be a registration's target: they are scored and printed, and no decision
#: reads them. M-GAP: its truth is the candidate's own classifier output — the gap types #927's
#: code wrote — so "M-GAP 37 → 4" measured compliance with the new rule-8 wording, not fidelity
#: to the page (fix request 2, RG-D13; operator 2026-11-11, "Bar it now"), until an independent
#: coding of the gap types exists.
BARRED_TARGETS: dict[str, str] = {
    "M-GAP": "RG-D13: its truth is the candidate's own classifier output, so it measures "
             "compliance, not fidelity; barred until an independent coding of the gap types "
             "exists"}


def register(base_ref: str, cand_ref: str, *, targets: Sequence[str] = (), draws: int = 5,
             transforms: Sequence[str] = (), panel: dict[str, Any] | None = None,
             pages: Sequence[str] | None = None, captured: Captured | None = None,
             no_worsening: bool = False, ship_alpha: float | None = None,
             replicates: Registration | None = None,
             ledger: Path | None = None, note: str | None = None,
             no_worsening_families: dict[str, list[str]] | None = None) -> Registration:
    """The registration for a comparison of the frozen panel, or of target pages outside it
    (`registered_pages`). ``captured`` — the $0 capture of exactly this comparison — pins every
    request's bytes and records its inputs; ``run_compare`` refuses a registration without the
    pins. HELD OUT is per change: the pages the change's own commits and records do not name
    (the corpus holds no page that no fix ever named — record R8).

    ``ship_alpha`` registers the replication rule. ``replicates`` registers a REPLICATION of a
    registration under it: the same design in every field — refs, transforms, pages, draws,
    targets, both alphas, scorer and the request bytes (`DESIGN_FIELDS`) — and only for a first
    run the approval's ``ledger`` records, complete, whose own ledger-backed score decided
    "replication required" (`first_run_verdict`); a replication of any other outcome is
    result-shopping and is refused."""
    if barred := [t for t in targets if t in BARRED_TARGETS]:
        raise rp.ReplayError(f"{barred} cannot be a target — {BARRED_TARGETS[barred[0]]}; it is "
                             "still scored and reported beside the targets")
    scorer = refuse_unless_scored_by_base(base_ref)   # RG-D12, in the library (B's check, gap 1)
    p = panel or rp.load_panel_file()
    chosen = registered_pages(pages, p)
    for t in targets:
        blobs = {x: (p["pages"].get(x) or {}).get("dossier_blob") for x in chosen}
        if t in mt.PAGE_LIMITED and (off := [x for x in chosen
                                             if mt.gap_entries(x, blobs[x]) is None]):
            raise rp.ReplayError(f"{t} is defined only on the pages whose gap types are frozen "
                                 f"(`{mt.GAP_TYPES_FILE.name}`); not on {off} — never scored as "
                                 "zero there")
    pins: dict[str, str] = {}
    inputs: dict[str, Any] = {}
    if captured is not None:
        got = (captured.base_ref, captured.cand_ref, captured.transforms,
               tuple(dict.fromkeys(t for t, _ in captured.requests)))
        if got != (base_ref, cand_ref, tuple(transforms), chosen):
            raise rp.ReplayError("the capture is not of the comparison being registered (refs, "
                                 "transforms or pages differ)")
        pins, inputs = request_pins(captured), dict(captured.inputs)
    named = change_names(base_ref, cand_ref, sorted(p["pages"]))
    rule = (NO_WORSENING_RULE if no_worsening else
            REPLICATION_RULE if ship_alpha is not None else Registration.rule)
    nwf = {m: list(f) for m, f in (no_worsening_families or {}).items()}
    for m, fams in nwf.items():
        rule += (f"; {m}'s no-worsening check counts only its families {fams}, the rest "
                 "reported, never gated")
    reg = Registration(base_ref=base_ref, cand_ref=cand_ref, transforms=tuple(transforms),
                       pages=chosen, draws=draws, targets=tuple(targets),
                       held_out=tuple(t for t in chosen if t not in named),
                       scorer=scorer, no_worsening=no_worsening,
                       requests=pins, rule=rule, ship_alpha=ship_alpha, inputs=inputs,
                       note=note, no_worsening_families=nwf)
    if replicates is None:
        return reg
    if replicates.replicates is not None:
        raise rp.ReplayError("a replication is of a FIRST run's registration; that registration "
                             "is itself a replication")
    if ledger is None:
        raise rp.ReplayError("a replication is registered against the approval's ledger, which "
                             "records the first run")
    first, _ = first_run_verdict(replicates.sha, ledger)
    differ = design_differs(reg, first)
    if differ:
        raise rp.ReplayError(f"a replication is of the same design; these differ: {differ}")
    return dataclasses.replace(reg, replicates=first.sha)


def first_run_verdict(first_sha: str, ledger: Path) -> tuple[Registration, Path]:
    """The FIRST run a replication replicates, as the approval's ledger records it — or a refusal.
    Exactly one run under ``first_sha`` holds draws; its own ``registration.json`` is that sha and
    is not itself a replication; it holds every registered draw (pages × conditions × draws); and
    its LAST score under that registration, scored WITH a ledger, decided "replication required".
    A folder's word alone, another registration's rows, or a score with no ledger never count."""
    runs = [(d, n) for d, n in runs_under(ledger, first_sha) if n]
    if len(runs) != 1:
        raise rp.ReplayError(f"the ledger records {len(runs)} run(s) of {first_sha[:12]} holding "
                             "draws; a replication replicates exactly one")
    folder, n = Path(runs[0][0]), runs[0][1]
    first = run_registration(folder)
    if first.sha != first_sha or first.replicates is not None:
        raise rp.ReplayError(f"{folder} holds registration {first.sha[:12]}, not the first run "
                             f"{first_sha[:12]} the ledger records there")
    want = len(first.pages) * len(CONDITIONS) * first.draws
    if n != want:
        raise rp.ReplayError(f"{folder} holds {n} draws; {first_sha[:12]} registered {want}")
    log = folder / "score_log.jsonl"
    rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()
            if x.strip()] if log.exists() else []
    mine = [r for r in rows if r.get("registration") == first_sha and r.get("ledger")]
    if not mine or mine[-1].get("decision") != REPLICATION_REQUIRED:
        got = mine[-1].get("decision") if mine else "never scored with a ledger"
        raise rp.ReplayError(f"the first run decided {got!r}, not {REPLICATION_REQUIRED!r}: only "
                             "a result in the replication band is replicated")
    return first, folder


def write_registration(reg: Registration, path: Path) -> None:
    rp.refuse_inside_repo(path, "the registration")
    if path.exists():
        raise rp.ReplayError(f"{path} exists: a registration is written once, before any draw")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(reg.to_json(), encoding="utf-8")


def run_compare(c: Captured, *, budget: rp.Budget, out_dir: Path, registration: Registration,
                sdk: Any | None = None, claim: Callable[[], object] | None = None) -> None:
    """Step 2, PAID. Page by page, BASE then CAND, so the hours between conditions are bounded by
    one page's ten draws (#920 could not bound them). Draws exactly what ``registration`` says —
    once, and only the request bytes it pins — and records its sha256 in the budget ledger
    before the first draw. ``claim`` (the index's `registry.claim_draw`) is called after every
    $0 refusal and before the first write, so a refused run never consumes its registration."""
    gd.verify_committed_gold()   # RG-D11: the gold's hashes, before any paid draw (gap 4)
    refuse_if_unreached(c)
    if (here := scorer_fingerprint()) != registration.scorer:   # RG-D12, in the library (gap 1)
        raise rp.ReplayError(f"the scorer here ({here[:12]}) is not the registered scorer "
                             f"({registration.scorer[:12]}): nothing is drawn")
    reg = registration
    pages = tuple(dict.fromkeys(t for t, _ in c.requests))
    if (c.base_ref, c.cand_ref, c.transforms, pages) != (reg.base_ref, reg.cand_ref,
                                                         reg.transforms, reg.pages):
        raise rp.ReplayError("the captured comparison is not the registered one (refs, "
                             "transforms or pages differ) — register it first")
    recorded = [r for r in budget.rows() if "registration" in r and "out_dir" in r]
    prior = [r["out_dir"] for r in recorded if r["registration"] == reg.sha]
    if prior:
        raise rp.ReplayError(f"registration {reg.sha[:12]} was already drawn under this "
                             f"approval (into {prior}): a registration is drawn ONCE — "
                             "re-drawing a completed run is result-shopping; a new run needs a "
                             "new registration")
    for r in recorded:   # ... and so is a DESIGN, whatever its note or inputs say
        other = run_registration(r["out_dir"])
        if other.sha != r["registration"]:
            raise rp.ReplayError(f"{r['out_dir']} holds registration {other.sha[:12]}, not the "
                                 f"{r['registration'][:12]} the ledger records there")
        if not design_differs(reg, other) and other.replicates == reg.replicates:
            raise rp.ReplayError(
                f"this design was already drawn under this approval, as {other.sha[:12]} into "
                f"{r['out_dir']}: a design is drawn ONCE whatever its note or inputs (a "
                "replication of a first run is the one other draw, and it too is drawn once)")
    if not reg.requests:
        raise rp.ReplayError(f"registration {reg.sha[:12]} pins no request bytes: register it "
                             "with its $0 capture, so what is drawn is what was registered")
    pins = request_pins(c)
    if pins != reg.requests:
        differ = sorted(k for k in set(pins) | set(reg.requests)
                        if pins.get(k) != reg.requests.get(k))
        raise rp.ReplayError(f"the captured requests are not the registered bytes ({differ} "
                             "differ): the code or inputs moved since registration — a new "
                             "registration, never a re-draw under this one")
    draws = reg.draws
    rp.refuse_inside_repo(out_dir, "the run folder (requests and draws carry licensed text)")
    if (out_dir / "draws.jsonl").exists():
        raise rp.ReplayError(f"{out_dir} already holds draws: draws append, so a second run here "
                             "would be scored with the first — use a fresh folder")
    if claim is not None:
        claim()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    budget.record({"registration": reg.sha, "out_dir": str(out_dir), "usd": 0.0})
    with (out_dir / "requests.jsonl").open("w", encoding="utf-8") as f:
        for (t, cond), req in c.requests.items():
            f.write(json.dumps({"ticker": t, "condition": cond,
                                "ref": c.base_ref if cond == "BASE" else c.cand_ref,
                                "transforms": list(c.transforms), "kwargs": req.kwargs}) + "\n")
    for t in dict.fromkeys(t for t, _ in c.requests):
        for cond in CONDITIONS:
            rp.run_request(c.requests[(t, cond)], draws=draws, budget=budget,
                           label=f"{t}:{cond}", draws_out=out_dir / "draws.jsonl", sdk=sdk,
                           registration=reg.sha)


# ------------------------------------------------------------------------------------- scoring

@dataclass(frozen=True)
class MetricResult:
    metric: str
    base_total: int
    cand_total: int
    p_lower: float
    p_upper: float
    held_out_base: int
    held_out_cand: int


@dataclass(frozen=True)
class Score:
    targets: tuple[str, ...]
    metrics: dict[str, MetricResult]
    leans: dict[str, dict[str, dict[str, int]]]
    proposals: dict[str, dict[str, str | None]]
    failed_draws: dict[str, int]
    echo_new: dict[str, list[str]]
    ships: bool
    reasons: tuple[str, ...]
    runs: tuple[tuple[str, int], ...] = ()   # every run the ledger records under the sha: draws
    #: The registered rule's outcome: "ships", "ships once the moves listed are explained",
    #: "replication required", "replicated: ships" or "does not ship".
    decision: str = ""
    #: Targets the registration named that may not decide (`BARRED_TARGETS`): reported, never read
    #: by the decision.
    barred: tuple[str, ...] = ()


def runs_under(ledger: Path, sha: str) -> tuple[tuple[str, int], ...]:
    """Every run an approval's ledger records under registration ``sha``, with the draws its
    folder holds — so a score reports them all, never one chosen."""
    out: list[tuple[str, int]] = []
    for r in rp.Budget.load(ledger).rows():
        if r.get("registration") == sha:
            d = Path(str(r.get("out_dir")))
            f = d / "draws.jsonl"
            n = (sum(1 for x in f.read_text(encoding="utf-8").splitlines() if x.strip())
                 if f.exists() else 0)
            out.append((str(d), n))
    return tuple(out)


def target_family(targets: Sequence[str], p_lower: dict[str, float]) -> dict[str, float]:
    """The registered targets' family for Holm's correction. A BARRED target (`BARRED_TARGETS`)
    keeps its place at p = 1, its worst case: its value is never read, and the correction is never
    looser than the one the registration was made under (review round 0)."""
    return {t: 1.0 if t in BARRED_TARGETS else p_lower[t] for t in targets if t in p_lower
            or t in BARRED_TARGETS}


def holm(p_values: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    """Holm's step-down across the declared targets: the i-th smallest p (0-based) is rejected
    only if every smaller one was and it is <= alpha / (k - i)."""
    k = len(p_values)
    out = dict.fromkeys(p_values, False)
    for i, (m, p) in enumerate(sorted(p_values.items(), key=lambda kv: kv[1])):
        if p > alpha / (k - i):
            break
        out[m] = True
    return out


def usable(row: dict[str, Any]) -> bool:
    """A draw `synthesize` would have kept: the call stopped on its tool (a ``max_tokens`` stop
    is a truncated, partial tool input — production's client raises on it) and the output carries
    every required field but ``evidence_balance`` (production's INCOMPLETE rule)."""
    raw = row.get("raw")
    if not raw or row.get("stop_reason") != "tool_use":
        return False
    required = SYNTHESIS_TOOL["input_schema"]["required"]
    return all(k in raw for k in required if k != "evidence_balance")


def _lean(raw: dict[str, Any]) -> str:
    parts = split_lean(str(_decode_escapes(raw).get("evidence_balance") or ""))
    return parts[0].strip().lower() if parts else ""


_COMMITTED = ("strongly-bullish", "strongly-bearish")


def _modal_set(tally: Counter[str]) -> frozenset[str]:
    """Every lean at the top count — a tie is a set, so draw ORDER never reads as a lean move."""
    if not tally:
        return frozenset()
    top = max(tally.values())
    return frozenset(k for k, v in tally.items() if v == top)


def _proposal(tally: Counter[str], sleeve: str) -> str | None:
    """Production's proposal for a build with this tally: the modal lean, withheld unless the
    draws are unanimous (`verdict.derive_proposal`)."""
    if not tally:
        return None
    modal = max(tally.items(), key=lambda kv: kv[1])[0]
    p = derive_proposal(f"{modal} — x", sleeve=sleeve, draws_unanimous=len(tally) == 1)
    return p.action.value if p.action is not None else None


def _check_run(out_dir: Path, reg: Registration, rows: list[dict[str, Any]]) -> None:
    """The run IS the registered one, scored by the registered scorer, on the registered pages
    and draw counts — anything else is refused, never scored."""
    rec = out_dir / "registration.json"
    if not rec.exists() or Registration.from_json(rec.read_text(encoding="utf-8")).sha != reg.sha:
        raise rp.ReplayError(f"{reg.sha[:12]} is not the registration this run was drawn under "
                             f"({rec}); re-scoring under another needs a new registration and run")
    if (fp := scorer_fingerprint()) != reg.scorer:
        raise rp.ReplayError(f"the scorer here ({fp[:12]}) is not the registered scorer "
                             f"({reg.scorer[:12]}): score from the registered code")
    seen = Counter(r["label"] for r in rows)
    pages = {lab.split(":")[0] for lab in seen}
    if pages != set(reg.pages):
        raise rp.ReplayError(f"the draws cover {sorted(pages)}, not the registered pages "
                             f"{sorted(reg.pages)}")
    for t in reg.pages:
        for cond in CONDITIONS:
            if seen[f"{t}:{cond}"] != reg.draws:
                raise rp.ReplayError(f"{t}:{cond} has {seen[f'{t}:{cond}']} draws; the run "
                                     f"registered {reg.draws} draws per page per condition")


def arm_layer(reg: Registration, ticker: str, cond: str, page: dict[str, Any]) -> MechanicalLayer:
    """THE LAYER THIS ARM'S REQUEST CARRIED (STATE row 53 item 6, handed over on issue #1004).
    Both arms were captured with the registered transforms run by their OWN code
    (`compare_requests`), but every draw was scored against the committed layer, untransformed,
    BASE's for both — which tilted M-ABSENT's "quote: nowhere" and M-ECHO against CAND, whose
    request carried words its own transform wrote. With transforms, the arm's layer is rebuilt by
    its own ref (`replay.layer_at`) from the inputs the registration recorded, each checked by
    sha256; without, both arms carried the committed layer, as before."""
    if not reg.transforms:
        return pre_synthesis_mech(page)
    root = reg.inputs.get("ciq_root")
    rec = (reg.inputs.get("pages") or {}).get(ticker)
    if root is None or rec is None:
        raise rp.ReplayError(f"registration {reg.sha[:12]} records no inputs for {ticker}: the "
                             "layer its transforms wrote cannot be rebuilt, so it is not scored")
    comps, ciq, got = _transform_inputs(ticker, Path(root), reg.transforms)
    if got["comps"] != rec.get("comps") or got["ciq"] != rec.get("ciq"):
        raise rp.ReplayError(f"{ticker}: the CIQ inputs at {root} are not the ones the "
                             "registration recorded: the layer its transforms wrote cannot be "
                             "rebuilt as drawn, so it is not scored")
    ref = reg.base_ref if cond == "BASE" else reg.cand_ref
    return MechanicalLayer.model_validate(
        rp.layer_at(ref, page, transforms=reg.transforms, comps=comps, ciq=ciq))


def score_run(out_dir: Path, registration: Registration, *, panel: dict[str, Any] | None = None,
              pages: dict[str, dict[str, Any]] | None = None,
              transcripts: dict[str, str | None] | None = None,
              ledger: Path | None = None,
              layer_for: Callable[[Registration, str, str, dict[str, Any]],
                                  MechanicalLayer] | None = None) -> Score:
    """Step 3, $0 — the registered rule, on the registered run, appended to its score log.
    ``pages``/``transcripts`` override the frozen panel inputs (tests); otherwise they are read
    and checked as the capture read them. With the approval's ``ledger`` (the CLI requires it),
    every run recorded under the registration is reported, and the score is refused when this
    folder is not one of them or another also holds draws."""
    reg = registration
    p = panel or rp.load_panel_file()
    runs: tuple[tuple[str, int], ...] = ()
    if reg.replicates is not None:   # a replication counts only as one of a real first run
        if ledger is None:
            raise rp.ReplayError("a replication is scored against the approval's ledger, which "
                                 "records the first run it replicates")
        first, _ = first_run_verdict(reg.replicates, ledger)
        if differ := design_differs(reg, first):
            raise rp.ReplayError(f"a replication is of the same design; these differ: {differ}")
    if ledger is not None:
        runs = runs_under(ledger, reg.sha)
        here = out_dir.resolve()
        if not any(Path(d).resolve() == here for d, _ in runs):
            raise rp.ReplayError(f"{out_dir} is not a run the ledger records under registration "
                                 f"{reg.sha[:12]} (it records {list(runs)})")
        others = [(d, n) for d, n in runs if Path(d).resolve() != here and n]
        if others:
            raise rp.ReplayError(f"registration {reg.sha[:12]} was drawn more than once: "
                                 f"{list(runs)} — every run under one sha is reported, never "
                                 "one chosen; none of them is scored")
    for m in reg.targets:
        if m in mt.PAGE_LIMITED and (off := [
                t for t in reg.pages
                if mt.gap_entries(t, (p["pages"].get(t) or {}).get("dossier_blob")) is None]):
            raise rp.ReplayError(f"{m} is a target, but {off} are not the pages its gap types "
                                 "were frozen on (ticker and blob): it cannot be scored there")
    rows = [json.loads(x) for x in (out_dir / "draws.jsonl").read_text(encoding="utf-8")
            .splitlines() if x.strip()]
    _check_run(out_dir, reg, rows)
    reqs: dict[tuple[str, str], rp.Request] = {}
    if (out_dir / "requests.jsonl").exists():
        for x in (out_dir / "requests.jsonl").read_text(encoding="utf-8").splitlines():
            if x.strip():
                r = json.loads(x)
                reqs[(r["ticker"], r["condition"])] = rp.Request(r["kwargs"])
    counts: dict[str, dict[str, dict[str, list[int]]]] = {}
    leans: dict[str, dict[str, Counter[str]]] = {}
    failed: Counter[str] = Counter()
    echo: dict[str, dict[str, set[str]]] = {}
    ctxs: dict[tuple[str, str], mt.PageContext] = {}   # one per page AND arm (row 53 item 6)
    loaded: dict[str, tuple[dict[str, Any], str | None]] = {}
    indexes: dict[tuple[str, str], mt.EchoIndex] = {}
    for row in rows:
        t, cond = row["label"].split(":")
        if reg.inputs.get("impact") and (t, cond) not in ctxs:
            # A FRESH BUILD'S ARM: its own page, layer and transcripts, never the frozen page
            page, mech, tx = impact_arm(reg, t, cond)
            loaded.setdefault(t, (page, tx))
            ctxs[(t, cond)] = mt.PageContext(page=page, mech=mech, transcript=tx, blob=None)
        if t not in loaded:
            if pages is not None:
                loaded[t] = pages[t], (transcripts or {}).get(t)
            else:
                loaded[t] = rp.panel_inputs(t, panel=p)   # read BY the panel's blob, checked
        if (t, cond) not in ctxs:
            page, tx = loaded[t]
            ctxs[(t, cond)] = mt.PageContext(
                page=page, mech=(layer_for or arm_layer)(reg, t, cond, page), transcript=tx,
                blob=(p["pages"].get(t) or {}).get("dossier_blob"))
        ctx = ctxs[(t, cond)]
        if not usable(row):
            failed[row["label"]] += 1
            continue
        req = reqs.get((t, cond))
        if req is not None and (t, cond) not in indexes:
            indexes[(t, cond)] = mt.EchoIndex.of(req, ctx)
        sc = mt.score_units(draw_units(row["raw"]), ctx, echo=indexes.get((t, cond)))
        series = dict(sc)
        for m, fams in reg.no_worsening_families.items():   # the gated families, and the rest
            if m in sc:
                series[gated(m, fams)] = [h for h in sc[m] if h.family in fams]
                series[ungated(m, fams)] = [h for h in sc[m] if h.family not in fams]
        for m, hits in series.items():
            counts.setdefault(m, {}).setdefault(t, {c: [] for c in CONDITIONS})[cond].append(
                len({h.unit for h in hits}))
        leans.setdefault(t, {c: Counter() for c in CONDITIONS})[cond][_lean(row["raw"])] += 1
        for h in sc.get("M-ECHO", []):
            echo.setdefault(cond, {}).setdefault(h.phrase, set()).add(t)
    reasons: list[str] = []
    for t in reg.pages:
        for cond in CONDITIONS:
            if not sum(leans.get(t, {}).get(cond, Counter()).values()):
                reasons.append(f"{t}: {cond} has no usable draw — the page cannot be compared, "
                               "and a panel is never shrunk silently")
    held = set(reg.held_out)
    results: dict[str, MetricResult] = {}
    for m, by_page in counts.items():
        pd = [sx.PageDraws(t, tuple(v["BASE"]), tuple(v["CAND"]))
              for t, v in sorted(by_page.items()) if v["BASE"] and v["CAND"]]
        if not pd:
            continue
        r = sx.stratified_exact(pd)
        ho = [x for x in pd if x.page in held]
        results[m] = MetricResult(m, r.base_total, r.cand_total, float(r.p_lower),
                                  float(r.p_upper), sum(sum(x.base) for x in ho),
                                  sum(sum(x.cand) for x in ho))
    hard = list(reasons)   # a page that cannot be compared, a class that worsens: never ships
    # A BARRED TARGET (RG-D13) is scored and printed, never read by the decision: a registration
    # written before the bar (#927's) decides on its other targets alone
    barred = tuple(t for t in reg.targets if t in BARRED_TARGETS)
    deciding = tuple(t for t in reg.targets if t not in BARRED_TARGETS)
    if barred and not deciding and not reg.no_worsening:
        reasons.append(f"no target decides: {list(barred)} reported only (RG-D13)")
    target_p = target_family(reg.targets, {t: results[t].p_lower for t in deciding
                                           if t in results})
    at_alpha = holm(target_p, reg.alpha)
    first_run_rule = reg.ship_alpha is not None and reg.replicates is None
    at_ship = holm(target_p, reg.ship_alpha) if first_run_rule and reg.ship_alpha else at_alpha
    band = ("fail" if barred and not deciding and not reg.no_worsening else
            "ship" if all(at_ship.get(t) for t in deciding) else
            "replicate" if first_run_rule and all(at_alpha.get(t) for t in deciding) else
            "fail")
    for t in deciding:
        got = f"p_lower {results[t].p_lower:.3g}" if t in results else "not scored"
        if not at_alpha.get(t):
            reasons.append(f"target {t} does not improve beyond noise ({got}; Holm across "
                           f"{len(reg.targets)} target(s))"
                           + (" — the replication does not replicate" if reg.replicates else ""))
        elif not at_ship.get(t):
            reasons.append(f"target {t}: {got} is in the replication band ({reg.ship_alpha}, "
                           f"{reg.alpha}] — it counts only if a fresh, separately registered "
                           f"replication of the same design reaches p_lower <= {reg.alpha}")
    checked = {m: (gated(m, reg.no_worsening_families[m]) if m in reg.no_worsening_families
                   else m) for m in mt.GOLD_CLASS if m not in reg.targets}
    for name in checked.values():
        if (r := results.get(name)) is not None and r.p_upper <= reg.alpha:
            hard.append(f"{name} worsens beyond noise: {r.base_total} → {r.cand_total} "
                        f"(p_upper {r.p_upper:.3g})")
            reasons.append(hard[-1])
    explain_from = len(reasons)
    proposals: dict[str, dict[str, str | None]] = {}
    for t, by in leans.items():
        sleeve = str(loaded[t][0].get("sleeve"))
        proposals[t] = {c: _proposal(by[c], sleeve) for c in CONDITIONS}
        modal = {c: _modal_set(by[c]) for c in CONDITIONS}
        if modal["BASE"] != modal["CAND"] or proposals[t]["BASE"] != proposals[t]["CAND"]:
            reasons.append(f"{t}: the lean moved ({dict(by['BASE'])} → {dict(by['CAND'])}; "
                           f"proposal {proposals[t]['BASE']} → {proposals[t]['CAND']}) — explain "
                           "it in writing before review")
    committed = [sx.PageDraws(t, *(tuple(int(k in _COMMITTED) for k, v in by[c].items()
                                         for _ in range(v)) for c in CONDITIONS))
                 for t, by in sorted(leans.items()) if by["BASE"] and by["CAND"]]
    if committed:
        cr = sx.stratified_exact(committed)
        two_sided = min(1.0, 2 * float(min(cr.p_lower, cr.p_upper)))
        if two_sided <= reg.alpha:
            reasons.append(f"the panel's committed-lean draws moved {cr.base_total} → "
                           f"{cr.cand_total} (two-sided p {two_sided:.3g}) — explain it in "
                           "writing before review (record §6.3)")
    new_echo = {ph: sorted(ts) for ph, ts in echo.get("CAND", {}).items()
                if ph not in echo.get("BASE", {})}
    explain = reasons[explain_from:]
    decision = (DOES_NOT_SHIP if band == "fail" or hard else
                REPLICATION_REQUIRED if band == "replicate" else
                ("replicated: ships" if reg.replicates else "ships")
                + (" once the moves listed are explained in writing" if explain else ""))
    score = Score(targets=reg.targets, metrics=results,
                  leans={t: {c: dict(v) for c, v in by.items()} for t, by in leans.items()},
                  proposals=proposals, failed_draws=dict(failed),
                  echo_new={"CAND only": [f"{ph} ({', '.join(ts)})"
                                          for ph, ts in new_echo.items()]},
                  ships=not reasons, reasons=tuple(reasons), runs=runs, decision=decision,
                  barred=barred)
    with (out_dir / "score_log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            "registration": reg.sha, "scorer": reg.scorer,
                            "runs_under_sha": [list(r) for r in runs],
                            "ledger": str(ledger.resolve()) if ledger is not None else None,
                            "ships": score.ships, "decision": score.decision,
                            "ship_alpha": reg.ship_alpha, "replicates": reg.replicates,
                            "reasons": list(score.reasons),
                            "metrics": {m: r.__dict__ for m, r in results.items()}}) + "\n")
    return score


def score_text(s: Score) -> str:
    lines = [f"TARGETS {', '.join(s.targets) or 'none (no-worsening only)'}; ships: {s.ships}; "
             f"decision: {s.decision}"]
    lines += [f"  run under this registration: {d} ({n} draws)" for d, n in s.runs]
    for m, r in sorted(s.metrics.items()):
        lines.append(f"  {m:8} BASE {r.base_total:3} → CAND {r.cand_total:3} | p_lower "
                     f"{r.p_lower:.3g} p_upper {r.p_upper:.3g} | held-out {r.held_out_base} → "
                     f"{r.held_out_cand}")
    for t, by in sorted(s.leans.items()):
        lines.append(f"  {t:5} leans BASE {by['BASE']} CAND {by['CAND']} | proposal "
                     f"{s.proposals[t]['BASE']} → {s.proposals[t]['CAND']}")
    if s.failed_draws:
        lines.append(f"  draws with no usable output: {s.failed_draws}")
    lines += [f"  echo, CAND only: {x}" for x in s.echo_new["CAND only"]]
    lines += [f"  {t}: reported, never decides — {BARRED_TARGETS[t]}" for t in s.barred]
    lines += [f"  BLOCKS: {r}" for r in s.reasons]
    return "\n".join(lines)
