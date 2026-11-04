# A frozen slice of screen run 2026-10-16-01

Verbatim lines of the committed run (`data/snapshots/screen_runs/2026-10-16-01.jsonl` and its
manifest), and of `data/snapshots/universe_snapshot.jsonl` and `securities.jsonl` as committed
on main f419b845 (universe as of 2026-10-16), for three tickers: EEFT (a candidate stopped at
G1), FUBO (a candidate that reached G3) and NFLX (a universe row, out of band, never screened).
Frozen for the fact layer's screen scope and replay pins (`tests/test_facts_screen.py`); the
committed universe snapshot is rewritten by every weekly run, so a test cannot read it live.
