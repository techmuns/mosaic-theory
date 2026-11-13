"""The impact check's per-ref worker: build, render and capture pages with ONE ref's code, at $0.

RUN BY PATH, NEVER IMPORTED FROM ``vinci.impact``. The parent (`vinci.impact.pages`) extracts a
ref's ``vinci/`` and runs this file in a child process whose ``PYTHONPATH`` is that extraction
(``-P``: this file's own folder is never on the path), with the run's inputs tree as its cwd. So it
imports only production entry points that exist at every ref since the pre-spend check (#893) —
``prespend.mechanical_build``, ``render.render_markdown``, ``synthesis.synthesize`` — and refuses
to run against any other ``vinci`` (``--expect-root``). The request capture is
``vinci/evals/capture_child.py`` of the CHECKOUT RUNNING THE CHECK, loaded by path: it imports only
production modules, which bind to the ref's code.

PER PAGE, each step on its own, a failure written down and never fatal to the next step or page:

1. ``built.json`` / ``built.md`` — the page as a paid build would write it minus every LLM phase
   (`prespend.mechanical_build`), rendered as ``assemble._write`` renders it;
2. ``request.json`` — the synthesis request that build's layer would send, captured with a client
   that sends nothing (`capture_child.capture_calls`), the layer marked material first as
   ``assemble_one`` marks it, and kept in the captured key order (`write_request`);
3. ``committed.md`` — the COMMITTED ``dossier.json`` rendered by this ref's code;
4. ``reads.json`` — every HTTP response the page read (URL → sha256), and which were fetched live.

THE FROZEN CACHE (``--frozen-cache``). Every cached response is served whatever its age, so two
refs read one copy; a response the cache does not hold is fetched once, through the normal paced
client, and named in ``reads.json`` — never a silent difference between the two runs.

NOTHING SENT TO A MODEL: the parent strips every Anthropic credential from this environment, and
the capture's client records each request and raises.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

_READS: dict[str, dict[str, Any]] = {}

#: Set by the parent unless ``--allow-vendor-pulls``: a price vendor's response the cache lacks is
#: refused, never fetched — "no Polygon or Tiingo bulk pulls without asking" (coordinator,
#: 2026-11-11). SEC misses are still fetched, through the paced client.
NO_VENDOR_PULLS = "IMPACT_NO_VENDOR_PULLS"
VENDOR_HOSTS = frozenset({"api.polygon.io", "api.tiingo.com"})


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def freeze_cache() -> None:
    """Serve every cached response whatever its age, and record every response read."""
    from vinci import netcache

    cls = netcache.CachedHttp
    read, fetch = getattr(cls, "_read_cache", None), getattr(cls, "_fetch_with_retries", None)
    if read is None or fetch is None:
        raise SystemExit("impact child: this ref's netcache has no _read_cache/_fetch_with_retries "
                         "to freeze — the frozen-cache run cannot be made at this ref")

    def where(self: Any, url: str) -> str:
        p = self._cache_path(url)
        return f"{p.parent.name}/{p.name}"

    def frozen_read(self: Any, url: str, ttl_seconds: float | None) -> str | None:
        text: str | None = read(self, url, None)
        if text is not None:
            _READS.setdefault(url, {"sha256": _sha(text), "live": False, "file": where(self, url)})
        return text

    def logged_fetch(self: Any, url: str, **kw: Any) -> str:
        host = urlsplit(url).hostname or ""
        if os.environ.get(NO_VENDOR_PULLS) and host in VENDOR_HOSTS:
            raise RuntimeError(f"not in the cache, and a {host} pull is the operator's call "
                               f"(coordinator, 2026-11-11): {url}")
        text: str = fetch(self, url, **kw)
        _READS[url] = {"sha256": _sha(text), "live": True, "file": where(self, url)}
        return text

    cls._read_cache = frozen_read  # type: ignore[method-assign]
    cls._fetch_with_retries = logged_fetch  # type: ignore[method-assign]


def own_soffice_profile(profile: Path) -> None:
    """Every LibreOffice conversion in this process runs under its OWN user profile.

    LibreOffice refuses a second conversion while one runs under the same profile
    (`ciq.extract_text`, RA-D11), so parallel builds sharing the default one lose a transcript on
    whichever side collides — a move no code made. A profile of its own per process cannot
    collide; the conversion itself is unchanged."""
    import subprocess

    real = subprocess.run
    flag = f"-env:UserInstallation={profile.resolve().as_uri()}"

    def run(args: Any, *a: Any, **k: Any) -> Any:
        if (isinstance(args, (list, tuple)) and args
                and Path(str(args[0])).name in ("soffice", "libreoffice")
                and not any(str(x).startswith("-env:UserInstallation") for x in args)):
            args = [args[0], flag, *args[1:]]
        return real(args, *a, **k)

    subprocess.run = run


def block_sockets() -> None:
    """No socket from this process can connect: a store filled "from the cache only" must fail
    loud on a response the cache does not hold, never fetch it (`vinci.impact.store`)."""
    import socket

    def refuse(*_a: Any, **_k: Any) -> Any:
        raise RuntimeError("network is blocked in this impact child (cache only)")
    socket.socket.connect = refuse  # type: ignore[method-assign]
    socket.socket.connect_ex = refuse  # type: ignore[method-assign]
    socket.create_connection = refuse


def _capture_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("_impact_capture_child", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _step(out: Path, name: str, timings: dict[str, float], fn: Any) -> Any:
    t0 = time.monotonic()
    try:
        return fn()
    except BaseException as exc:  # noqa: BLE001 — every failure is written down, none is fatal
        if isinstance(exc, KeyboardInterrupt):
            raise
        (out / f"{name}.error.json").write_text(json.dumps({
            "error": type(exc).__name__, "message": str(exc)[:4000],
            "where": traceback.format_exc()[-4000:]}), encoding="utf-8")
        return None
    finally:
        timings[name] = round(time.monotonic() - t0, 2)


def utc_day() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _side_file(path: Path, obj: Any) -> None:
    """A page side's own record (reads, clock, timing) — never the page, which is saved through
    `dossier_json` (``built.json``), and never its request (`write_request`)."""
    path.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")


def write_request(path: Path, calls: list[dict[str, Any]]) -> None:
    """A page side's synthesis request, ``{"calls": [kwargs, …]}``, in the CAPTURED KEY ORDER.

    Never sorted (2026-11-13). The paid path sends this order (`capture_child.jsonable`: a sorted
    copy would send production's tool schema with its fields reordered, the defect PR 2 drew), and
    the run compares the two sides byte for byte (`replay.wire`). Written key-sorted, as every side
    file was, the record erased exactly the change that reorders the tool schema's fields or the
    top-level arguments: the two sides read identical, and a request exported from the run was
    not the one production sends."""
    path.write_text(json.dumps({"calls": calls}, ensure_ascii=False), encoding="utf-8")


def page(ticker: str, out: Path, *, capture: Any, requests: bool, committed: bool) -> None:
    from vinci.config import Config
    from vinci.dossier import assemble, prespend
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier, dossier_json

    out.mkdir(parents=True, exist_ok=True)
    _READS.clear()
    first_day = utc_day()
    cfg = Config()
    timings: dict[str, float] = {}
    root = cfg.data_dir / "dossiers"

    def build() -> Any:
        built = prespend.mechanical_build(ticker, cfg)
        (out / "built.json").write_text(dossier_json(built), encoding="utf-8")
        return built

    built = _step(out, "build", timings, build)
    if built is not None:
        _step(out, "render", timings, lambda: (out / "built.md").write_text(
            render_markdown(built, card=assemble._read_scenario_card(built.ticker),
                            dossiers_root=root), encoding="utf-8"))
    if built is not None and requests:
        def request() -> None:
            from vinci.dossier.ciq import CiqBundle
            from vinci.dossier.ciq_sheets import transcript_for_synthesis
            from vinci.dossier.manual_store import LocalFolderStore

            bundle = CiqBundle.from_files(ticker, LocalFolderStore.from_config(cfg).files(ticker))
            doc = json.loads(dossier_json(built))
            doc["mechanical"] = json.loads(
                assemble._mark_material(built.mechanical).model_dump_json())
            model = getattr(cfg, "graph_llm_model", None) or capture.production_model()
            from vinci.dossier.synthesis import SYNTHESIS_DRAWS

            calls = capture.capture_calls(doc, transcript_for_synthesis(bundle), model=model,
                                          draws=SYNTHESIS_DRAWS)
            write_request(out / "request.json", [capture.jsonable(c) for c in calls])
        _step(out, "request", timings, request)
    page_json = root / ticker / "dossier.json"
    if committed and page_json.exists():
        _step(out, "committed_render", timings, lambda: (out / "committed.md").write_text(
            render_markdown(Dossier.model_validate_json(page_json.read_text()),
                            card=assemble._read_scenario_card(ticker), dossiers_root=root),
            encoding="utf-8"))
    _side_file(out / "reads.json", _READS)
    # every UTC day the steps ran across: the build stamps today's date on the page
    # (`run.build_days`), so two sides compare only when built within one and the same day
    _side_file(out / "clock.json", {"utc_days": sorted({first_day, utc_day()})})
    _side_file(out / "timing.json", timings)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tickers", default="", help="comma-separated")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--expect-root", required=True, type=Path)
    ap.add_argument("--capture-child", type=Path)
    ap.add_argument("--run-module", nargs=argparse.REMAINDER,
                    help="instead of pages: run `python -m MODULE ARGS…` with this ref's code "
                         "(a downstream consumer), the cache frozen when asked")
    ap.add_argument("--frozen-cache", action="store_true")
    ap.add_argument("--no-network", action="store_true",
                    help="refuse every socket: a response the cache lacks fails loud")
    ap.add_argument("--seed", action="append", default=[],
                    help="a committed snapshot table to load into the store first")
    ap.add_argument("--soffice-profile", type=Path,
                    help="a LibreOffice user profile folder of this process's own")
    ap.add_argument("--no-requests", action="store_true")
    ap.add_argument("--no-committed", action="store_true")
    a = ap.parse_args(argv)
    import vinci
    where = Path(vinci.__file__).resolve()
    if a.expect_root.resolve() not in where.parents:
        print(f"impact child: imported vinci from {where}, not under {a.expect_root}",
              file=sys.stderr)
        return 2
    if a.frozen_cache:
        freeze_cache()
    if a.no_network:
        block_sockets()
    if a.soffice_profile is not None:
        own_soffice_profile(a.soffice_profile)
    if a.seed:
        from vinci.config import Config
        from vinci.store import Store

        cfg = Config()
        with Store(cfg.db_path) as store:
            store.rebuild_from_snapshots(cfg.snapshots_dir, tables=a.seed)
    if a.run_module:
        import runpy
        sys.argv = list(a.run_module)
        code = 0
        try:
            runpy.run_module(a.run_module[0], run_name="__main__", alter_sys=True)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        if a.out is not None:
            a.out.write_text(json.dumps(_READS, sort_keys=True), encoding="utf-8")
        return code
    if a.out is None or a.capture_child is None:
        print("impact child: pages need --out and --capture-child", file=sys.stderr)
        return 2
    capture = _capture_module(a.capture_child)
    for t in [x for x in a.tickers.split(",") if x]:
        page(t, a.out / t, capture=capture, requests=not a.no_requests,
             committed=not a.no_committed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
