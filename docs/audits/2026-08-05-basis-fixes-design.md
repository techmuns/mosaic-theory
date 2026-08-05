# The two basis fixes — consumer map and design

**2026-08-05. Report, not a build.** The claim under test: *"they're the same shape — a value
carrying the basis it's on"*. **They are the same family and NOT the same fix.** Separable, and
`revenue_fy` should go first.

---

## 1 · `revenue_fy` — consumer map

`ev_gap.anchor_fy` has **one writer, one computation, one decision consumer, and two render twins**.

| # | site | what it does with the anchor |
|---|---|---|
| W | `ev_gap.py:486` → `anchor_year(levels)` | **picks it** — nearest forward FY where BOTH Revenue and EBITDA resolve. Never consults the record. |
| C | `ev_gap.py:112` | `revenue_ratio = i.revenue / i.consensus_revenue` — `revenue` is the record's base leg, `consensus_revenue` the median **at the anchor**. **This is where the mismatch bites.** |
| D | `propose.py:129` | reads `anchor_fy` to pick the consensus median it proposes as the base revenue anchor |
| R | `render.py:3118,3123` · `dossier.js` ×8 | display only ("Anchor FY2026 · consensus as-of …") |

**The proposer is why this stayed invisible for so long.** `propose_anchors` anchors the base
revenue *at* `anchor_fy`, so a record built from the template is self-consistent by construction.
The mismatch can only arise when the analyst **overrides** to a different fiscal year — which is
exactly what SMPL's 2026-08-05 underwrite did (base 1,340 = FY2028 median, read at an 18-month
horizon, against an FY2026 anchor).

**Blast radius: small.** `revenue_fy` is a **coordinate** — it says *which period* a value
describes. It does not change what `revenue=1340.0` means; it is still $M of revenue. Every
consumer that reads the float keeps working unchanged. Only the writer and the computation need to
know it exists; the render twins gain a line.

---

## 2 · `GuidanceItem` change-vs-level — consumer map

`low`/`high` are read as a **level in the metric's unit** in five places:

| # | site | what it does |
|---|---|---|
| 1 | `mechanical.py:515` | `_fmt_guide_range(g.low, g.high, unit)` → the release summary line |
| 2 | `mechanical.py:2456` `current_guide` | takes the newest **revenue** guide as `(low, high, qualitative)` |
| 3 | `mechanical.py:2493` `guide_verification` | **compares CIQ's guide against the release's `low`/`high`** |
| 4 | `synthesis.py:998` `_primary_source_digest` | the brief's `guidance (metric period): low–high` line |
| 5 | `propose.py:379` `evidence_for` | the analyst template's revenue evidence block |

**Blast radius: every one of them.** A change basis is a **different dimension**, not a different
coordinate. `low=375, unit="bps", basis="change"` is not the same *kind* of quantity as
`low=1345, unit="$M", basis="level"`, and **no consumer can ignore the difference safely**:

- #3 is the sharpest. `guide_verification` compares a CIQ level guide to the release's guide. Given
  a change guide it has nothing to compare — it must derive the level from a base (which base? the
  prior-year actual, and on which accounting basis?) or **refuse and say so**. Silently comparing
  375 against 32.5 would be a new instance of the very defect.
- #4 and #5 print `low–high` with a unit; a change guide printed that way reads as a level. That is
  the 300–350% gross margin, in the brief and in the analyst's own template.
- #2 feeds a `(low, high)` tuple onward; a change value there propagates untyped.

---

## 3 · Same family, different fix — so: separable

Both are the basis class, and the operator is right that the shape is *a value carrying the basis
it is on*. But the two differ on the thing that decides how you build them:

| | `revenue_fy` | guidance change-vs-level |
|---|---|---|
| what is added | a **coordinate** (which period) | a **dimension** (level or change) |
| can a consumer ignore it? | **yes** — the float keeps its meaning | **no** — the quantity changes kind |
| consumers needing change | 1 writer + 1 computation (+2 render) | **all 5**, one of which (`guide_verification`) may have to refuse |
| overlap | `propose.py` — but a *different function* (`propose_anchors`) | `propose.py` — `evidence_for` |
| blocked on | nothing | a ruling on how a change guide verifies against a level guide |

**The only shared file is `propose.py`, and they touch different functions in it.** There is no
surface either fix would map twice. Doing them together buys nothing and couples a small guard to a
design question that is genuinely open.

**Recommendation: `revenue_fy` first, alone.** It converts a live accepted risk on the only open
position into a guard and lets the STATE entry be deleted. The guidance fix follows and needs its
own ruling first (below).

---

## 4 · The live-record decision, made here rather than when it fires

**`revenue_fy` will fire on SMPL on day one.** Its base leg is an FY2028 figure against an FY2026
anchor — that is the accepted risk becoming a guard, and it is the point.

**Proposed rule, consistent with the horizon precedent already shipped in #346:**

1. **Refuse at the WRITE boundary.** `scenario-create` and `scenario-supersede` refuse a record
   whose `revenue_fy` disagrees with the gap's `anchor_fy` **unless the record states why** — the
   `{axis}_adjustment` idiom, since deviating from the anchor year is exactly a stated deviation.
   Nothing new lands mismatched and unexplained.
2. **FLAG on recompute, never refuse.** `build_ev_gap` gains a status/mismatch field naming both
   years, rendered on the page beside "Anchor FY2026". Recomputation keeps working.
   **This matters:** refusing inside the recompute path would blind
   `test_every_committed_record_result_matches_its_own_facts` on the only open position — the same
   argument that moved the horizon refusal to the write boundary, and the reason that call was
   right.
3. **SMPL specifically:** its record predates the field, so `revenue_fy` is **UNSTATED**, not
   disagreeing. Unstated ⇒ flag as unverifiable, never refuse — a record cannot be punished for
   lacking a field that did not exist when it was written. The operator supplies it at the next
   supersede, at which point the disagreement becomes explicit and must state its reason.

**The distinction that makes this safe:** *unstated* and *disagreeing* are different states and
must render differently — the same rule that separates "we looked and found none" from "this
predates the question" in the version-scoping mechanism.

---

## 5 · Scope note — capture is still open

Marking is done; **capture is not**. Seventeen guided clauses still drop across four names —
**SMPL 8, MVST 6, VITL 2, IT 1** — and the cause is sentence SHAPE, not the metric allowlist
(`gross margin` is already in it). **This gates IT's re-assembly**, which is next in the queue.
Full measurement: `docs/audits/2026-08-05-guidance-extractor-drops.md`.
