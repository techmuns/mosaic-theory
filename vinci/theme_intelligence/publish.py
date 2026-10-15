"""PUBLISH the research desk into the main app (operator decision 2026-10-13, PR #703, option C).

`python -m vinci.theme_intelligence publish` renders one run of the registry — the desk's six
screens, the reading pages, the nine-section cards and the weekly report — and writes it to
`frontend/theme-intelligence/`, which the main app (Nostra Vinci, `frontend/`) shows as its
**Theme intelligence** section and Cloudflare Pages deploys with the site:

  site/        the standalone pages, exactly as a run writes them (the Full record and the weekly
               report open from here; the app frames the desk screens)
  desk.js      the desk's behaviour (tabs, filters, sorts) — the SAME script the standalone pages
               carry inline, so the app's copy can never drift from it
  intel.css    the desk's component styles SCOPED under `.intel` and re-pointed at the app's own
               design tokens (light and dark follow the app's toggle)
  index.json   what was published: the run, its week, when, and every file

ONE RENDERER: the app does not re-implement any screen — it fetches a published page, keeps its
content, maps its links onto the app's routes and styles it with the app's tokens
(`frontend/views/intel/desk.js`).

WHAT IS PUBLISHED: derived analysis — titles, figures, short verbatim claim quotes and business-
group excerpts, the review's words — never an article's text (the registry's export never carries
it either), never a local file path, never the per-card JSON/Markdown exports or the run's
manifest. The deploy is the private, authenticated internal site (CLAUDE.md §Security); if it is
ever made public, `frontend/theme-intelligence/` must be withdrawn and git-ignored.

A registry holding articles from a reserved TEST domain (the synthetic stress registries) is
refused unless `allow_test_data` — synthetic data never reaches the app by accident.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from vinci.theme_intelligence.cards import THEME_CSS
from vinci.theme_intelligence.desk import CSS as DESK_CSS
from vinci.theme_intelligence.desk import JS as DESK_JS
from vinci.theme_intelligence.desk import _test_domain, desk_weeks
from vinci.theme_intelligence.display import first_of
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.store import Store

KIND = "theme-intelligence-publish"
#: the run's outputs the app may show — every other output (the card JSON / Markdown exports, the
#: weekly report's JSON / CSV / Markdown, the validation log, the manifest with its local paths)
#: stays where the run wrote it
_PAGES = re.compile(r"^(index|themes|review|uploads|sources|articles(-[\w.-]+)?|dashboard|"
                    r"report_print)\.html$|^theses/TH-[0-9A-F]+\.html$|"
                    r"^cards/TH-[0-9A-F]+(\.print)?\.html$")

#: the desk's design tokens re-pointed at the main app's (frontend/assets/styles.css), so the
#: section reads in the app's own design language — light and dark follow the app's toggle
#: (--bg, --ink, --line, --accent and --accent-bg are the same names in both and are simply
#: inherited — a self-reference such as `--bg: var(--bg)` would be a cycle, i.e. invalid)
APP_TOKENS = {
    "--panel": "var(--surface)", "--ink2": "var(--ink-2)", "--muted": "var(--ink-3)",
    "--soft": "var(--surface-2)",
    "--now": "var(--danger-text)", "--now-bg": "var(--danger-bg)",
    "--watch": "var(--warn-text)", "--watch-bg": "var(--conditional-bg)",
    "--skip": "var(--ink-3)", "--skip-bg": "var(--surface-2)",
    "--warn": "var(--warn-text)", "--warn-bg": "var(--conditional-bg)",
    "--ok": "var(--pos-text)", "--ok-bg": "var(--live-bg)",
    "--bad": "var(--danger-text)", "--bad-bg": "var(--danger-bg)",
    "--info": "var(--accent-text)", "--info-bg": "var(--accent-bg)",
    "--obs": "var(--pos-text)", "--fc": "var(--teal-text)", "--op": "var(--synth)",
    "--inf": "var(--warn-text)", "--ext": "var(--accent-strong)", "--unk": "var(--ink-3)",
    "--block": "var(--danger-text)",
}

#: in the app the frame supplies the page title, breadcrumb and audit switch
_IN_APP = """
.intel{font-variant-numeric:tabular-nums}
.intel .hero h1{font-size:20px;margin-top:0}
.intel .hero h1.tabtitle{display:none}
.intel .th h1{display:none}
.intel .crumb{display:none}
.intel .aud{display:none}#intel-audit:checked~.intel .aud{display:revert}
.intel-bar{display:flex;justify-content:flex-end;margin:-4px 0 10px}
.intel-auditbar{font-size:12.5px;color:var(--ink-3);cursor:pointer;border:1px solid var(--line);
border-radius:6px;padding:3px 9px}
#intel-audit:checked~.intel-bar .intel-auditbar{background:var(--accent-bg);color:var(--accent)}
.intel .pill{display:inline-block;font-size:12px;font-weight:650;letter-spacing:.02em;
padding:3px 10px;border-radius:999px;white-space:nowrap;vertical-align:1px}
.intel .pill.now{background:var(--now-bg);color:var(--now)}
.intel .pill.watch{background:var(--watch-bg);color:var(--watch)}
.intel .pill.skip{background:var(--skip-bg);color:var(--skip)}
.intel .main{padding:0;max-width:none;min-width:0;zoom:1}
.intel .tabs{display:block;gap:0;flex-wrap:nowrap}
.intel .flag{display:inline-block;gap:0;align-items:normal;margin:0;line-height:inherit;
padding:2px 9px;border-radius:6px;font-size:13px}
.intel .num{font-family:inherit;text-align:left}
"""
#: the app's own class names the desk's markup shares (frontend/assets/styles.css) — each reset
#: above so the app's rule for it never leaks into the section (pinned by a test)
APP_COLLISIONS = ("main", "tabs", "flag", "num", "pill")


class PublishError(ValueError):
    """Refused: nothing was written."""


def scope_css(css: str, scope: str = ".intel") -> str:
    """Every rule of `css` confined to `scope`: `h1{…}` → `.intel h1{…}`, `body` / `:root` → the
    scope itself, `@media` blocks scoped inside. For the desk's own stylesheet (flat rules and
    @media blocks — no nested at-rules, no commas inside selectors' parentheses)."""
    out: list[str] = []
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        head = css[i:j].strip()
        if head.startswith("@media"):
            depth, k = 1, j + 1
            while depth:
                depth += {"{": 1, "}": -1}.get(css[k], 0)
                k += 1
            out.append(f"{head}{{{scope_css(css[j + 1:k - 1], scope)}}}")
            i = k
            continue
        k = css.index("}", j)
        sels = [x.strip() for x in head.split(",") if x.strip()]
        scoped = [scope if x in ("body", "html", ":root", "*") else
                  f"{scope} {x}" for x in sels]
        out.append(",".join(scoped) + css[j:k + 1])
        i = k + 1
    return "\n".join(out)


def app_css() -> str:
    """intel.css — the desk's components (the theme's chrome left to the app) scoped to `.intel`,
    its tokens mapped onto the app's."""
    components = DESK_CSS[len(THEME_CSS):]
    tokens = ".intel{" + ";".join(f"{k}:{v}" for k, v in APP_TOKENS.items()) + "}"
    return ("/* GENERATED by `python -m vinci.theme_intelligence publish` — do not edit; the source"
            " is vinci/theme_intelligence/desk.py */\n" + tokens + "\n" + scope_css(components)
            + _IN_APP)


def _marker(out: Path) -> dict[str, Any] | None:
    f = out / "index.json"
    if not f.exists():
        return None
    data = json.loads(f.read_text())
    return data if isinstance(data, dict) else None


def publish(store: Store, run_id: str, out: Path, *, allow_test_data: bool = False
            ) -> dict[str, Any]:
    """Render `run_id` and replace the publication in `out` with it. Refused — nothing written —
    for a registry holding test-domain articles (unless `allow_test_data`), for a folder that holds
    anything but an earlier publication, or when a page would carry a local path."""
    run = store.run(run_id)
    if run is None:
        raise PublishError(f"no run {run_id}")
    test = [a.canonical_url for a in store.articles() if _test_domain(a.canonical_url)]
    if test and not allow_test_data:
        raise PublishError(f"the registry holds {len(test)} article(s) from a reserved test "
                           f"domain (e.g. {test[0]}) — synthetic data is never published to the "
                           f"app; pass allow_test_data only for a local preview")
    marker = _marker(out) if out.exists() else None
    if out.exists() and any(out.iterdir()) and (marker or {}).get("kind") != KIND:
        raise PublishError(f"{out} holds files that are not a theme-intelligence publication — "
                           f"refusing to replace them")
    if marker is not None:  # a file the last publication did not write is never deleted (U32e)
        stray = sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()
                       and not p.name.startswith(".")  # OS metadata (Finder's .DS_Store)
                       and str(p.relative_to(out)) not in {"index.json", *marker.get("files", [])})
        if stray:
            raise PublishError(f"{out} holds {len(stray)} file(s) the last publication did not "
                               f"write ({first_of(stray, 5, ', ')}) — refusing to delete them; "
                               f"move them out first")
    with tempfile.TemporaryDirectory() as tmp:
        rendered = Path(write_run_outputs(store, run_id, Path(tmp) / "run")["dir"])
        pages = sorted(str(p.relative_to(rendered)) for p in rendered.rglob("*.html")
                       if _PAGES.match(str(p.relative_to(rendered))))
        local = {str(store.path.parent.resolve()), str(Path(tmp).resolve()), str(Path.home())}
        for rel in pages:
            text = (rendered / rel).read_text()
            leak = next((x for x in local if x in text), None)
            if leak:
                raise PublishError(f"{rel} carries a local path ({leak}) — not published")
        staging = Path(tmp) / "publish"
        for rel in pages:
            (staging / "site" / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(rendered / rel, staging / "site" / rel)
        (staging / "desk.js").write_text(
            "/* GENERATED by `python -m vinci.theme_intelligence publish` — the research desk's "
            "behaviour, the same script its standalone pages carry inline. */\n" + DESK_JS)
        (staging / "intel.css").write_text(app_css())
        weeks = desk_weeks(store, run)
        week = weeks[-1] if weeks else None
        manifest = {
            "kind": KIND, "run_id": run.run_id, "run_mode": run.mode,
            "run_as_of": run.as_of.isoformat(),
            "week": week.label if week else None,
            "published_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
            "test_data": bool(test),
            "theses": len(list((staging / "site" / "theses").glob("TH-*.html"))),
            "files": sorted(["desk.js", "intel.css", *(f"site/{p}" for p in pages)]),
        }
        (staging / "index.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
        if out.exists():
            shutil.rmtree(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staging, out)
    return manifest
