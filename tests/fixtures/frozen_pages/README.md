# Frozen pages

A test that pins a VALUE read off a committed page — a guide range, a calendar date, a TEV, a
ratio — rots the next time that page is re-assembled, because the page is a living artifact. The
TEST-LAYER RULE (CLAUDE.md) puts such a pin on a frozen fixture and leaves the living page to
phrasing-independent invariants. Each directory here is laid out like `data/dossiers/`
(`<date>/<TICKER>/dossier.json`), so a reader that takes a dossiers root can be pointed at it.

These track NO page and are never regenerated. Refreeze one only with the pins that read it.

| directory | page | frozen from | what is pinned on it |
|---|---|---|---|
| `2026-08-18/SMPL/` | SMPL, assembled 2026-08-18, reference date 2026-08-14 | `data/dossiers/SMPL/dossier.json` and `dossier.md` at main `f2c6e7aa`, byte-identical (frozen 2026-10-29, ahead of the page moving to its FY2026 10-K) | the 2026-07-09 release's FY2026 net-sales guide $1,345–1,355M beside CIQ's quarter (`test_net_sales_is_revenue`); the calendar's 2026-10-08 print (`test_record_legibility`); TEV 1,324.6 on a $1,000M cap, from its $324.6M net debt (`test_refresh_path`); net debt / EBITDA 1.5x (`test_trigger_state_surface`); the LTM $391.9M writedown (`test_material_figure_presence`); the $60.9M Atkins impairment in the digest, and `drawdown_cause.revised_guidance` holding April's outlook (`test_guidance_vintage`); the gross-margin guide printed in bps on the card (`test_release_amount_scale`); the LTM column's −2.08 read before FY2025's +1.02 (`test_pe_basis_cause_claim`) |
