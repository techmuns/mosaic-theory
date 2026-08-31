---
id:
status: shipped
date: 2026-08-29
prs: [516]
supersedes:
superseded-by:
---

# The data tree follows the code, not the shell

**THE BUG.** `Config.data_dir` defaulted to a bare relative `Path("data")`, so every derived path —
`cache_dir`, `snapshots_dir`, `db_path` — moved with whatever CWD the process started in. Running
any script from `scripts/` built a second, empty tree at `scripts/data/` and quietly refilled it:
4.6MB of SEC responses re-fetched into a cache nothing else would ever read again.

**THE CACHE WAS ONLY THE VISIBLE SYMPTOM, because a cache creates what it misses.** The dangerous
half is silent: `snapshots_dir` and `db_path` pointed at directories that do not exist, so a caller
writing through `cfg.snapshots_dir` from the wrong CWD files an artifact where nothing will read it
and reports success. Nothing in the repo does that today — which is exactly why it was worth closing
before something did.

**THE FIX.** `data_dir` anchors to `Path(__file__).resolve().parents[1]` — run this checkout's
`vinci`, get this checkout's `data/`. That is the right coupling, and it composes with the `sys.path`
pin added to `scripts/` in #514: under `scripts/`, a bare `import vinci` resolves through the venv's
`.pth` to a DIFFERENT worktree, and the data must follow whichever code actually loaded.

Still overridable — `Config(data_dir=...)` is how every test that writes points at a `tmp_path`, and
that is pinned separately so anchoring the default cannot weld the path down.

**HOW IT WAS FOUND.** Not by a test. `git status` showed an untracked `scripts/data/` after the
triage cost gate ran from that directory during #515.

**VERIFIED.** The same command from three CWDs (repo root, `scripts/`, `/tmp`) resolves one
absolute path, and `snapshots_dir`/`db_path` exist from all three. Re-running the gate from
`scripts/` creates no second tree and completes at 0.0s/name — a cache HIT, where before it missed
and re-fetched. 4 mutations caught: the relative default restored, the anchor off by one level, an
absolute path to the wrong tree, and the override ignored.
