"""ITEM 1 — the freshness contract's two guards.

THE DEFECT WAS LIVE ON ALL ELEVEN, and the audited name was the least of them: every committed
dossier renders a market cap that cannot be reconciled to the price beside it, SMPL smallest at
−2.4% and FUBO worst at −91%. A fix built and tested on SMPL alone would have closed the mildest
instance in the fleet.

WHAT IS PINNED HERE. The two guards fire on the right names and stay quiet on the right names; the
ratio DIAGNOSES rather than merely flags; and — the pin that would have caught the mistake made
twice while measuring this — a value-borne date is not a panel arrival.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re

import pytest

from vinci.dossier import freshness as fr

ROOT = pathlib.Path(__file__).resolve().parents[1]
#: The gate began measuring against the BUILD date on this day. Artifacts assembled
#: BEFORE it were guarded by the old rule and report its staleness honestly.
GATE_FIXED_ON = "2026-07-30"


def _num(x: object) -> float | None:
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    m = re.search(r"-?[\d,]+\.?\d*", str(x or ""))
    return float(m.group(0).replace(",", "")) if m else None


def _stock(mech: dict, key: str) -> float | None:
    v = (mech.get("stock_info") or {}).get(key)
    return _num(v.get("value") if isinstance(v, dict) else v)


def _fleet() -> dict[str, dict]:
    out = {}
    for d in sorted((ROOT / "data" / "dossiers").iterdir()):
        j = d / "dossier.json"
        if j.exists():
            out[d.name] = json.loads(j.read_text()).get("mechanical") or {}
    return out


def _assembled(ticker: str) -> str:
    """A dossier's own assembly stamp — what panel age is measured against, so a committed artifact
    reports the age it had WHEN BUILT rather than ageing every time it is re-read."""
    return str(json.loads(((ROOT / "data" / "dossiers" / ticker / "dossier.json")).read_text())
               ["assembled_at"])


def test_a_value_borne_date_is_not_a_panel_arrival() -> None:
    """THE MEASUREMENT BUG, pinned — it was made twice and inverted the fleet's ranking both times.

    An own-history band's `as_of` travels WITH ITS VALUE (item 20's fix: a band's current reading
    carries the date of the close it came from). A panel's `as_of` is an ARRIVAL — when an export
    was taken. Counting the first as the second makes SMPL read 115 days stale when its true panel
    oldest panel is 8 days old, the TIGHTEST in the fleet, and puts it top of a list it should be
    bottom of.
    """
    mech = _fleet()["SMPL"]
    keys = {k for k, _ in fr.panel_dates(mech)}
    assert keys, "no panel dates found on SMPL — the harvester is looking in the wrong place"
    assert not [k for k in keys if "own_history" in k or "stock_performance" in k], (
        f"value-borne dates leaked into the panel set: {sorted(keys)}")

    age = fr.panel_age(mech, _assembled("SMPL"), kind="export")
    assert age is not None and age.days <= 15, (
        f"SMPL's oldest PANEL is {age.days if age else '?'}d old — a much larger number here means "
        "value-borne dates are being counted as arrivals again")


def test_the_ratio_separates_a_corporate_action_from_price_drift() -> None:
    """The diagnosis, not just the flag (operator 2026-07-29). A near-whole-number ratio is a
    SHARE-BASIS mismatch — a split straddling the panel dates — and a fractional one is drift.
    The remediations differ completely: fix a share basis vs re-export a panel. A gate reporting
    only pass/fail would flag FUBO without saying which."""
    # FUBO's real numbers: EDGAR's pre-split 342.4M shares against CIQ's post-split $256.4M cap
    split = fr.reconcile_cap(cap_musd=256.4, shares=342_433_118, spot=8.33)
    assert split is not None and split.corporate_action
    assert 11.0 < split.ratio < 11.3, split.ratio
    assert "SHARE-BASIS mismatch" in split.note() and "not price drift" in split.note()

    # ordinary drift — a June cap against a July close — must NOT be called a corporate action
    drift = fr.reconcile_cap(cap_musd=1069.4, shares=48_543_350, spot=25.28)
    assert drift is not None and not drift.corporate_action
    assert -0.15 < drift.gap < -0.10
    assert "own as-of" in drift.note()

    # and a clean reconciliation is neither
    ok = fr.reconcile_cap(cap_musd=100.0, shares=10_000_000, spot=10.0)
    assert ok is not None and not ok.corporate_action and abs(ok.gap) < 1e-9


def test_a_share_basis_mismatch_is_caught_in_both_directions() -> None:
    """REVIEW FINDING on #253. The first cut tested `ratio >= 2`, which catches a PRE-split share
    count against a POST-split cap (FUBO, ~11x) and SILENTLY REPORTS THE REVERSE AS DRIFT.

    Nothing guarantees which side of the pair is the stale one: if the CAP were the pre-split
    figure and the shares post-split, the ratio is ~1/11 and the old test returned
    corporate_action=False — so the build would pass, the cap would render merely 'labelled with
    its own as-of', and a page whose every per-share figure is wrong by 11x would look like
    ordinary June-vs-July drift. The remediation is identical in both directions, so the detection
    must be too."""
    forward = fr.reconcile_cap(cap_musd=256.4, shares=342_433_118, spot=8.33)
    inverse = fr.reconcile_cap(cap_musd=2853.0, shares=342_433_118, spot=0.749)
    assert forward is not None and inverse is not None
    assert forward.corporate_action and inverse.corporate_action, (
        f"forward={forward.ratio:.4g} inverse={inverse.ratio:.4g} — a share-basis mismatch was "
        "missed in one direction")
    assert forward.ratio > 2 and inverse.ratio < 0.5, "the fixture no longer spans both directions"
    assert "either way" in inverse.note(), (
        "the note prints a bare 0.09x with no explanation — a reader cannot tell that from a "
        "90%-off drift, which is the distinction the ratio exists to draw")

    # the fold must NOT drag ordinary drift over the line: 1.17x is EPAM's real June-vs-July gap
    for r in (1.148, 1.169, 0.850, 0.918):
        drift = fr.reconcile_cap(cap_musd=100.0, shares=1e7, spot=10.0 * r)
        assert drift is not None and not drift.corporate_action, f"{r} misread as a split"


def test_a_build_with_no_price_bars_fails_rather_than_passing_silently() -> None:
    """THE DEFECT, and it happened: a SMPL re-assembly in a worktree whose EOD store had no SMPL
    bars produced a dossier with **no spot, no 52-week range and no as-of** — and reported
    "1 done · 0 error(s)", raised no caveat, and PASSED this very gate.

    The gate catches *cap ÷ shares disagrees with spot*. It did not catch *there is no spot*,
    because `reconcile_cap` returns None on an absent input and `check_freshness` read None as
    nothing-to-report. Completeness and reconciliation are different checks and it conflated them
    — the guard-that-cannot-fire class, inside a guard built to close that class.

    The field layer was honest throughout (`status=unknown, note="no price bars"`). Nothing at
    BUILD level noticed, which is what made it shippable."""
    # exactly the shape the failed re-assembly produced
    absent = fr.absent_cap_inputs(cap_musd=909.4, shares=88_460_545, spot=None)
    assert absent == ("spot price",), absent
    with pytest.raises(fr.FreshnessError, match="not underwritable"):
        fr.check_freshness(None, None, ticker="SMPL", absent=absent)

    # every combination of absence is named, not just the first
    assert fr.absent_cap_inputs(cap_musd=None, shares=None, spot=None) == (
        "market cap", "shares outstanding", "spot price")
    assert fr.absent_cap_inputs(cap_musd=None, shares=1e7, spot=10.0) == ("market cap",)

    # ...and a complete build still passes: the check must not fire on the fleet
    assert fr.absent_cap_inputs(cap_musd=909.4, shares=88_460_545, spot=10.53) == ()
    fr.check_freshness(None, None, ticker="SMPL", absent=())      # must not raise


def test_every_committed_name_has_the_inputs_the_gate_requires() -> None:
    """PER-NAME TABLE for the completeness half: requiring all three costs nothing on the fleet
    today (11 of 11 carry price, shares and cap), so the gate fires ONLY on a genuinely incomplete
    build — a fresh worktree, or a name whose price refresh has not run."""
    incomplete = {}
    for name, mech in _fleet().items():
        absent = fr.absent_cap_inputs(cap_musd=_stock(mech, "market_cap"),
                                      shares=_stock(mech, "shares_out"),
                                      spot=_stock(mech, "price"))
        if absent:
            incomplete[name] = absent
    assert not incomplete, (
        f"committed dossiers missing gate inputs: {incomplete}. Either a name shipped without a "
        "price — which the gate now refuses — or the fleet changed and the requirement needs "
        "re-deciding rather than relaxing")
    assert len(_fleet()) >= 10, "the corpus shrank; this table proves less than it says"


def test_absent_inputs_reconcile_to_nothing_rather_than_to_a_guess() -> None:
    """A missing cap/shares/spot is its own fail-loud elsewhere. Inventing one here to keep the
    check running would be the fabrication the repo refuses."""
    for kw in ({"cap_musd": None}, {"shares": None}, {"spot": None}, {"spot": 0.0}):
        args = {"cap_musd": 100.0, "shares": 1e7, "spot": 10.0, **kw}
        assert fr.reconcile_cap(**args) is None            # type: ignore[arg-type]


def test_the_guards_fail_the_four_names_they_should_and_no_others_e2e() -> None:
    """THE PER-NAME GATE across the whole committed fleet (operator's standing rule: no fix ships
    without a per-name table showing where it fires, where it does not, and that not-firing is
    correct on each).

    FIRES — the AGE leg currently refuses NOBODY. It once held BRBR 74d, MVST 56d, CNXC 53d and
    VRRM 48d; every one cleared when the comps re-exports landed, which is the gate reporting a WIN.
    The docstring said otherwise long after it stopped being true, so it is now written as what the
    assertions actually check rather than as a name list that ages out of correctness: the ceiling
    is 45 (CNXC is why it is not 60 — cleared under 16c on comps 49 days old), and `age_fail` must
    equal the computed over-ceiling set whatever that set happens to be.
    FIRES — the BASIS leg refuses FUBO, on the share basis rather than the age; its 45d lands
    exactly ON the ceiling and passes it (`> 45`, not `>=`).
    QUIET — everyone else: ordinary drift, which is a RENDERING obligation (clause (e)), not a
    build stop. Failing on drift would fail the whole fleet, which is a freeze wearing a guard's
    name.

    NO SET IN HERE IS PINNED BY NAME any more — see the comments at each assertion. The fleet is
    meant to GROW (out-of-band names the fund FOLLOWS assemble into the same directory), and a
    roster pin reds on an arriving name exactly as loudly as on a broken guard.
    """
    age_fail, basis_fail, quiet = set(), set(), set()
    over_ceiling, basis_break = set(), set()
    for name, mech in _fleet().items():
        recon = fr.reconcile_cap(cap_musd=_stock(mech, "market_cap"),
                                 shares=_stock(mech, "shares_out"), spot=_stock(mech, "price"))
        age = fr.panel_age(mech, _assembled(name), kind="export")
        if age is not None and age.days > fr.MAX_PANEL_AGE_DAYS:
            over_ceiling.add(name)
        if recon is not None and recon.corporate_action:
            basis_break.add(name)
        try:
            fr.check_freshness(age, recon, ticker=name)
            quiet.add(name)
        except fr.FreshnessError as exc:
            (basis_fail if "share basis" in str(exc) else age_fail).add(name)

    # SELF-CONSISTENT, not hardcoded: the gate must refuse exactly the names whose computed age is
    # over the ceiling. Written this way deliberately — comps re-exports move names off the list,
    # and a hardcoded set would red on a WIN and read as a regression. (It was hardcoded to
    # {BRBR, MVST, CNXC} before the 2026-07-29 re-measure; VRRM joined at 48d.)
    assert age_fail == over_ceiling, (age_fail, over_ceiling)
    # THE SAME TREATMENT, FINALLY APPLIED TO THE BASIS LEG. This read `basis_fail == {"FUBO"}` —
    # a hardcoded set sitting one line under the comment explaining why hardcoded sets are wrong.
    # It reds on a name ARRIVING exactly as loudly as on the share-basis check breaking, and the
    # fleet is meant to grow (out-of-band names the fund FOLLOWS assemble into the same directory).
    # `corporate_action` is the computable predicate, so the relation can be stated instead:
    # refuse exactly the names whose shares ratio sits on a whole number...
    #
    # ...MINUS the ones age already refused, because `check_freshness` tests the ceiling BEFORE the
    # share basis, so a name failing BOTH lands in `age_fail`.
    #
    # THAT SUBTRACTION IS CORRECT BUT VACUOUS TODAY, and saying so is the point: `over_ceiling` is
    # currently EMPTY (every comps re-export landed), so `basis_break & over_ceiling` is empty and
    # no corpus state can exercise the precedence. A first draft of this claimed "flip the two
    # blocks and this equality breaks" — MEASURED, and it does not; the mutation passes. The order
    # is pinned on constructed inputs instead, in `test_age_is_refused_before_the_share_basis`,
    # which is where a rule the live corpus cannot reach belongs.
    assert basis_fail == basis_break - over_ceiling, (basis_fail, basis_break, over_ceiling)
    # THE LIVE INSTANCE IS GONE, AND THAT IS THE GOAL (2026-08-13). This asserted `basis_fail`
    # non-empty so the corporate-action refusal had a name proving it fires. FUBO was that name;
    # its 2026-08-12 re-assembly put cap and count on one basis (30.2M shares against a $293M cap,
    # 0.03% apart), so EVERY committed name now reconciles and the set is legitimately empty.
    #
    # The refusal is NOT unpinned by this: the prior wording asked for it to be "moved to a
    # constructed fixture before deleting this", and two already exist —
    # `test_a_share_basis_mismatch_is_caught_in_both_directions` (both directions, constructed) and
    # `test_age_is_refused_before_the_share_basis` (precedence, constructed). What is dropped is the
    # requirement that some real name stay BROKEN to keep a guard honest.
    assert not basis_fail or basis_fail == basis_break - over_ceiling, (basis_fail, basis_break)
    assert quiet, "no name passes both guards — a gate that stops every build is a freeze"
    # The quiet SET is no longer pinned by name. It is exactly `fleet − age_fail − basis_fail` by
    # construction, so with both refusal sets now derived, a literal membership list adds nothing
    # but a roster pin — and reds on every arriving name. What the list was reaching for is proved
    # below instead: each quiet name is quiet for a STATED reason (it RECONCILES or it DRIFTS), and
    # both buckets must stay populated. That is the invariant, and it survives the fleet growing.
    # ...and each quiet name is quiet for a STATED reason — it either RECONCILES (the end state we
    # want) or merely DRIFTS (labelled, per clause (e)). The first cut asserted every quiet name
    # drifts, carrying the note "if a name now reconciles this is a WIN, but the assertion must
    # move with it rather than silently weaken". SMPL's 2026-07-29 re-assembly made it so: it
    # picked up the 2026-07-24 close, matching the 2026-07-24 comps vintage, and now implies
    # $10.28 against a $10.22 spot — +0.6%. **$10.28 is exactly the figure the audit's own P4
    # cross-check computed**, so C16 is resolved on the first name re-assembled since it was found.
    #
    # **SMPL LEFT `reconciled` ON 2026-08-04, AND THE PIN THAT FORBADE IT RESTED ON A FALSE
    # PREMISE.** That pin read "losing this is a regression in price SELECTION, not a data change
    # to absorb" — so it was checked against the selection code rather than absorbed. There is no
    # vintage alignment to regress: `_stock_info` sets `price = feats.last`, the store's last
    # close, and nothing anywhere aligns it to the comps export. The 2026-07-29 agreement was the
    # store frontier happening to sit five days from the 2026-07-24 panel, not a property the code
    # maintains. The store then advanced to 2026-08-03 and SMPL closed 11.32 against a FROZEN
    # 909.4 cap → −9.2%, outside the 2% tolerance. Cap didn't move; the market did.
    #
    # So the assertion below is now the invariant that is actually TRUE and worth guarding: the
    # reconcile path must keep a live instance (BRBR/CNXC/EPAM/VRRM do), exactly mirroring the
    # `assert drifting` guard beneath it. Both buckets stay populated, so neither path can quietly
    # stop being exercised — which is what the SMPL pin was reaching for and what it could not
    # deliver by naming ONE name whose membership no code controls. Every name's spot drifts from
    # its cap as the frontier advances past the CIQ export; a per-name pin re-reds on every price
    # refresh and teaches the reader to absorb it, which is the failure mode it warned against.
    reconciled, drifting = set(), set()
    for name in quiet:
        mech = _fleet()[name]
        r = fr.reconcile_cap(cap_musd=_stock(mech, "market_cap"),
                             shares=_stock(mech, "shares_out"), spot=_stock(mech, "price"))
        assert r is not None, f"{name} passed the gate with an input absent — impossible now"
        (reconciled if abs(r.gap) <= fr.RECONCILE_TOLERANCE else drifting).add(name)

    assert reconciled | drifting == quiet, "a quiet name fell into neither bucket"
    assert reconciled, (
        "NO name reconciles cap against spot — every dossier now carries a cap and a spot that "
        "disagree by more than the tolerance, so the reconcile path has no live instance and this "
        "test stops proving it works. That is not ordinary drift: check whether the CIQ comps "
        "panel is stale fleet-wide, or whether shares/cap extraction broke.")
    assert drifting, (
        "EVERY name now reconciles — genuinely the goal, but then clause (e)'s vintage labelling "
        "has no live instance and this test stops proving the drift path works. Move the drift "
        "assertions to a constructed fixture before deleting this one")


def test_the_ceiling_is_a_boundary_not_a_range() -> None:
    """`> 45`, not `>= 45`. Pinned because a silent flip to `>=` would fail an extra name and read
    as a data change rather than a code change.

    Driven off a CONSTRUCTED PanelAge, not off a fleet name. It used to key on VRRM sitting at
    exactly 45d — but the 2026-07-29 re-measure moved VRRM to 48d and put FUBO on the boundary
    instead, so a fleet-keyed boundary test silently stops testing the boundary whenever the
    fleet moves. The boundary is a property of the guard, so it is tested as one."""
    at = fr.PanelAge(oldest="2026-01-01", oldest_key="a", as_of="2026-02-15",
                     days=fr.MAX_PANEL_AGE_DAYS)
    fr.check_freshness(at, None, ticker="X")               # exactly at the ceiling: must not raise

    over = fr.PanelAge(oldest="2026-01-01", oldest_key="a", as_of="2026-02-16",
                       days=fr.MAX_PANEL_AGE_DAYS + 1)
    with pytest.raises(fr.FreshnessError, match="ceiling"):
        fr.check_freshness(over, None, ticker="X")


def test_age_is_refused_before_the_share_basis() -> None:
    """WHICH refusal a doubly-broken build reports — pinned on CONSTRUCTED inputs, because the live
    corpus cannot reach this state.

    The e2e gate asserts `basis_fail == basis_break - over_ceiling`; that subtraction encodes this
    precedence, but `over_ceiling` is empty today, so the corpus proves nothing about the order and
    a mutation flipping the two blocks passes it. MEASURED, not assumed — the first draft of that
    comment claimed the flip would break the equality and it does not.

    The order is load-bearing for the reader: age is REMEDIABLE by a re-export, a share-basis break
    is NOT ("a panel re-export will NOT resolve it"). A doubly-broken build reporting the basis
    error first would send the operator to fix the thing that cannot be fixed that way.
    """
    over = fr.PanelAge(oldest="2026-01-01", oldest_key="a", as_of="2026-02-16",
                       days=fr.MAX_PANEL_AGE_DAYS + 1)
    # ratio spot/implied ≈ 3 → reads as a split straddling the panels, exactly FUBO's shape
    split = fr.reconcile_cap(cap_musd=100.0, shares=3e6, spot=100.0)
    assert split is not None and split.corporate_action, "the fixture is not a basis break"

    with pytest.raises(fr.FreshnessError, match="ceiling"):
        fr.check_freshness(over, split, ticker="X")
    # and each still fires alone, so the precedence is an ORDER, not one check masking the other
    with pytest.raises(fr.FreshnessError, match="share basis"):
        fr.check_freshness(None, split, ticker="X")


def test_the_panel_age_note_renders_on_a_passing_build_too() -> None:
    """Rendered ALWAYS, not only on failure (operator): panel age is context a reader needs to
    read a multiple. A guard that speaks only when it fails leaves the other seven names looking
    clean when their fundamentals are weeks behind their price."""
    age = fr.panel_age(_fleet()["AORT"], _assembled("AORT"), kind="export")
    assert age is not None
    note = age.note()
    assert "oldest panel" in note and str(age.days) in note
    assert age.oldest in note and age.as_of in note


def test_the_gate_measures_against_the_build_date_not_the_screens_reference_date() -> None:
    """THE 2026-07-30 DEFECT, and it defeated the guard it was part of.

    `_freshness_check` was handed `fin.reference_date` — the SCREEN's as-of, which runs weeks
    behind the build (2026-07-06 against a 07-29 run). So the gate measured a 23-day-shorter age
    than the page it was guarding: CNXC PASSED at 31d and rendered "oldest panel 54d old", and
    NCNO's gate age came out at **-6 days** because its panel postdates the screen.

    A guard that can return a negative age is not measuring anything, and a page stating a number
    its own guard never applied is the stamp-names-a-different-object defect this contract exists
    to remove. The render measures against `assembled_at`; the gate now takes the same instant, so
    the two agree BY CONSTRUCTION rather than by coincidence."""
    from vinci.dossier.assemble import _freshness_check

    class _V:
        def __init__(self, v: float) -> None:
            self.value = v

    class _SI:
        # the completeness guard runs FIRST and refuses a build with no cap inputs, so the stub
        # carries three that RECONCILE — otherwise this test would pass on the wrong refusal.
        market_cap, shares_out, price = _V(1000.0), _V(100_000_000.0), _V(10.0)

    class _M:
        stock_info = _SI()

        def model_dump(self, mode: str = "python") -> dict[str, object]:
            return {"valuation": {"multiples_as_of": "2026-06-01"}}

    mech = _M()
    # one day inside the ceiling: passes
    _freshness_check(mech, ticker="X", built_at=dt.date(2026, 6, 1) + dt.timedelta(days=45))
    # one day past it: refuses
    with pytest.raises(fr.FreshnessError, match="ceiling"):
        _freshness_check(mech, ticker="X", built_at=dt.date(2026, 6, 1) + dt.timedelta(days=46))


def test_the_gate_is_wired_to_the_build_instant_not_the_screen_date() -> None:
    """THE CALL-SITE PIN, and it is the one that matters — the defect WAS the call site.

    `test_the_gate_measures_against_the_build_date...` calls `_freshness_check` WITH a date, so it
    passes no matter what the caller hands over: reverting `built_at=built_at.date()` to
    `built_at=fin.reference_date` reds nothing there. The e2e invariant below cannot cover it yet
    either (see its docstring).

    So this asserts the wiring directly: the gate must receive the SAME instant the artifact is
    stamped with. Source-level by necessity — the coupling is between two call sites inside one
    function, and driving `assemble_one` end-to-end needs a live store, EDGAR and an LLM."""
    import inspect

    from vinci.dossier import assemble as asm

    src = inspect.getsource(asm.assemble_one)
    assert "built_at = datetime.now(UTC)" in src, "the build instant must be taken ONCE"
    assert "built_at=built_at.date()" in src, (
        "the freshness gate must be handed the BUILD instant, not the screen's reference_date")
    assert "assembled_at=built_at" in src, (
        "the artifact must be stamped with the SAME instant the gate used, not a second now()")
    assert "reference_date=fin.reference_date" not in src.split("_freshness_check")[1][:120]


def test_a_date_before_the_panel_yields_a_negative_age_which_is_the_tell() -> None:
    """Kept as the diagnostic, not as accepted behaviour. `panel_age` does not clamp, deliberately:
    a negative age is the unmistakable signature of measuring against the wrong date, and clamping
    it to zero would have hidden the defect above instead of exposing it. NCNO produced -6d in the
    live batch and that number is what made the cause obvious."""
    mech = {"valuation": {"multiples_as_of": "2026-07-12"}}
    age = fr.panel_age(mech, dt.date(2026, 7, 6), kind="export")
    assert age is not None and age.days < 0, "a negative age must stay visible, not be clamped"


@pytest.mark.skipif(not (ROOT / "data" / "dossiers").is_dir(), reason="no committed dossiers")
def test_no_committed_dossier_renders_an_age_its_own_gate_never_applied() -> None:
    """THE WIRING PIN, and the one that would have caught the defect where the unit tests did not.

    Everything above tests `_freshness_check` by CALLING it with a date. That leaves the call SITE
    unpinned — and the call site was the bug: it passed `fin.reference_date` where the render uses
    `assembled_at`. Reverting it reds nothing above.

    This asserts the property a reader depends on: **a committed dossier's rendered panel age is
    within the ceiling.** CNXC shipped at a rendered 54d having passed its gate at 31d; under this
    pin that artifact cannot be committed at all. It is an e2e invariant on a living corpus, so it
    asserts a THRESHOLD rather than any particular value — re-assembly moves the numbers and must
    not red it."""
    # GRANDFATHERED BY ASSEMBLY DATE, not exempted by name. An artifact built under the old gate
    # honestly reports a staleness the old rule allowed; re-assembling it is what fixes it, and
    # names that CANNOT re-assemble (FUBO's corporate action, MVST/WERN outside the screen cohort)
    # would otherwise red this forever for a reason that is not a wiring defect. The scope clears
    # itself as names rebuild — no exemption list to go stale.
    over, checked = [], 0
    for d in sorted((ROOT / "data" / "dossiers").iterdir()):
        j = d / "dossier.json"
        if not j.exists():
            continue
        doc = json.loads(j.read_text())
        if str(doc["assembled_at"])[:10] < GATE_FIXED_ON:
            continue
        checked += 1
        age = fr.panel_age(doc.get("mechanical") or {}, doc["assembled_at"], kind="export")
        if age is not None and age.days > fr.MAX_PANEL_AGE_DAYS:
            over.append(f"{d.name}: renders {age.days}d, ceiling {fr.MAX_PANEL_AGE_DAYS}d")
    assert not over, (
        "committed dossiers render a panel age their own gate would refuse — the gate and the page "
        f"are measuring against different dates: {over}")
    # DECLARE VACUITY. Every committed artifact predates GATE_FIXED_ON today, so this pin currently
    # covers ZERO names and passes for that reason — not because the property holds. A guard that
    # cannot fire must say so rather than read as evidence; it starts covering names as the fleet
    # re-assembles. (This was claimed as "stronger than a batch run" before it was measured; it is
    # stronger ONLY once names are built under the new gate.)
    if not checked:
        pytest.skip(
            f"vacuous: no committed dossier is assembled on/after {GATE_FIXED_ON}, so this "
            "invariant covers nothing yet — it begins covering names as the fleet re-assembles")


def test_a_lease_basis_date_is_not_a_panel_arrival() -> None:
    """(+/-) #750's pages: the ex-lease band's `as_of` is the date its current reading was struck
    at (TJX's 2026-08-28 filing) — value-borne, like `own_history`'s. On TJX's real page with its
    real lease basis it must not enter the panel set or move the panel age; a panel date beside it
    still does."""
    mech = json.loads(json.dumps(_fleet()["TJX"]))
    before = fr.panel_age(mech, _assembled("TJX"), kind="export")
    lb = json.loads((ROOT / "tests" / "fixtures" / "lease_basis" / "TJX.json").read_text())
    assert lb["ex_lease_band"]["as_of"], "the fixture must carry the dated band this pins"
    mech["valuation"]["lease_basis"] = lb
    keys = {k for k, _ in fr.panel_dates(mech)}
    assert not [k for k in keys if "lease_basis" in k], sorted(keys)
    assert fr.panel_age(mech, _assembled("TJX"), kind="export") == before
    assert keys, "the panel dates beside it are still harvested"


#: Every dated panel key the committed fleet actually carries, each consciously classified.
#: EXPORT = ours to re-pull, so it GATES. CONSENSUS = the street's to revise, so it prints.
_CLASSIFIED_PANEL_KEYS = {
    "catalyst_path.as_of": "consensus",
    "financial_summary.as_of": "consensus",
    "valuation.implied_expectations.multiples_as_of": "consensus",
    "ev_gap.vintages.consensus_as_of": "consensus",
    "ev_gap.vintages.tev_as_of": "export",
    # FOUND BY THIS GUARD ON ITS FIRST RUN — both pre-existing, and the silent default was CORRECT
    # for both, which is the useful result: the gating default is safe, it simply was not asserted.
    # `stock_info.as_of` is the price/cap stamp and `…implied_expectations.tev_as_of` the comps
    # TEV; both are OURS to re-pull, so both gate.
    "stock_info.as_of": "export",
    "valuation.implied_expectations.tev_as_of": "export",
    # FOUND BY THIS GUARD ON EPAM's 2026-08-05 re-assembly — the FIRST committed dossier to carry
    # it, so the guard fired the moment O3's structured cap as-of reached an artifact rather than
    # after a fleet had quietly adopted the gating default.
    #
    # CLASSIFIED BY THE source_ref ITS OWN NODE CARRIES, per CONSENSUS_PANELS' own rule that
    # membership is MEASURED, not assumed. It shares a NAMESPACE with `stock_info.as_of` and
    # nothing else: that key stamps the EOD store, while EPAM's `market_cap` reads
    # "CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of
    # 2026-07-29" — the SAME panel `ev_gap.vintages.tev_as_of` parses, which is its real sibling
    # and is already "export". A CIQ export is ours to re-pull on our own schedule, never the
    # street's to revise, so it GATES. Not added to CONSENSUS_PANELS.
    "stock_info.market_cap_as_of": "export",
    # (2026-10-21) FOUND BY THIS GUARD on the valuation-bases pass: the date of the comps TEV that
    # `ev_ebitda_basis` divides — a copy of `valuation.implied_expectations.tev_as_of` above, the
    # same CIQ export, so it gates exactly as that one does and moves no page's oldest export age.
    "valuation.ev_ebitda_basis.tev_as_of": "export",
}


def test_every_dated_panel_key_is_consciously_classified() -> None:
    """THE TRAP THIS CLOSES, and it caught me rather than being imagined. `CONSENSUS_PANELS` is an
    ALLOWLIST: anything not in it falls into the GATING class by default. Persisting A2b's
    `ev_gap.vintages.consensus_as_of` therefore put MVST's `≥2026-05-15` back in front of the
    export gate — 56d against a 45d ceiling — and refused the build for "no analyst has revised
    it", which is exactly the condition the 2026-07-30 staleness split had just stopped refusing
    for, and which no operator action clears.

    Default-to-gating is the SAFE direction and is not being changed. What was missing is that the
    default was silent: a new dated field joined the gating class with nobody deciding it should.
    This asserts the inventory, so the next one argues with a test.
    """
    seen: set[str] = set()
    for mech in _fleet().values():
        seen |= {k for k, _ in fr.panel_dates(mech)}
    unclassified = seen - set(_CLASSIFIED_PANEL_KEYS)
    assert not unclassified, (
        f"dated panel key(s) {sorted(unclassified)} default to the GATING class with nobody "
        f"deciding they should. Classify each: add to freshness.CONSENSUS_PANELS if it is the "
        f"street's to revise, and to _CLASSIFIED_PANEL_KEYS either way.")
    # …and the classification here must AGREE with the module's, or this inventory is decoration.
    for key, kind in _CLASSIFIED_PANEL_KEYS.items():
        assert ((key in fr.CONSENSUS_PANELS) is (kind == "consensus")), (
            f"{key}: this file calls it {kind}, freshness.CONSENSUS_PANELS disagrees")
