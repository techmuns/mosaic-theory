#!/usr/bin/env python3
"""On-demand validator that the API-key SECRETS are set + valid in this environment.

Pings each external service with a tiny request. Prints PASS/FAIL per key — NEVER the key
value. Exits non-zero if a REQUIRED key (Polygon, Anthropic) is missing or rejected, or an
OPTIONAL key that is set (Tiingo) is rejected, so the `validate-keys` workflow goes red. Run via
workflow_dispatch. Cheap: ~1 trivial call each.
"""
from __future__ import annotations

import os
import sys

import httpx

#: the model the pipelines call — `vinci.config.Config.graph_llm_model` and
#: `vinci.theme_intelligence.config.LLM_MODEL` (this script cannot import `vinci`: the workflow
#: installs only anthropic and httpx). A test fails when they differ. Pinged until 2026-10-21 was
#: Haiku, so a key that could use Haiku but not the pipelines' model passed.
PIPELINE_MODEL = "claude-opus-4-8"


def check_anthropic() -> bool:
    # Returns False ONLY on a real key problem (auth, permission, or no access to the pipelines'
    # model). A connectivity error from the runner to api.anthropic.com is a WARN (environment,
    # not the key) — it does NOT fail the run.
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("ANTHROPIC_API_KEY: FAIL — secret not set / empty")
        return False
    if padded("ANTHROPIC_API_KEY", key):
        return False
    import anthropic

    try:
        anthropic.Anthropic(api_key=key).messages.create(
            model=PIPELINE_MODEL,
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
        print(f"ANTHROPIC_API_KEY: FAIL — {type(e).__name__} (bad key or no model access)")
        return False
    except anthropic.NotFoundError as e:
        print(f"ANTHROPIC_API_KEY: FAIL — {type(e).__name__}: this key cannot use "
              f"{PIPELINE_MODEL}, the model the pipelines call")
        return False
    except Exception as e:
        print(
            f"ANTHROPIC_API_KEY: WARN — {type(e).__name__}: {str(e)[:110]} "
            "(runner→api.anthropic.com connectivity, NOT a key problem)"
        )
        return True
    print(f"ANTHROPIC_API_KEY: PASS — authenticated; {PIPELINE_MODEL} answered")
    return True


def padded(name: str, key: str) -> bool:
    """A key with leading or trailing whitespace is a key problem, reported as one: it cannot
    travel in an HTTP header, and the client then raises a CONNECTION error that this script read
    as "runner connectivity, NOT a key problem" and passed — ANTHROPIC_API_KEY from 2026-06-26 to
    2026-10-20. Checked before any request; the value is never printed."""
    if key != key.strip():
        print(f"{name}: FAIL — the secret has leading or trailing whitespace; re-save it without")
        return True
    return False


def check_polygon() -> bool:
    key = os.environ.get("POLYGON_API_KEY")
    if not key:
        print("POLYGON_API_KEY: FAIL — secret not set / empty")
        return False
    if padded("POLYGON_API_KEY", key):
        return False
    try:
        r = httpx.get(
            "https://api.polygon.io/v3/reference/tickers",
            params={"limit": 1},
            headers={"Authorization": f"Bearer {key}"},
            timeout=30,
        )
    except Exception as e:
        print(f"POLYGON_API_KEY: FAIL — {type(e).__name__}: {str(e)[:160]}")
        return False
    if r.status_code == 200:
        print("POLYGON_API_KEY: PASS — 200 from reference/tickers")
        return True
    print(f"POLYGON_API_KEY: FAIL — HTTP {r.status_code} (401 ⇒ bad key)")
    return False


def check_tiingo() -> bool:
    """TIINGO_API_KEY is OPTIONAL (the weekly theme-intelligence run reads P/E against the two
    years Polygon serves without it), but a key that is SET and refused fails the run: the weekly
    run's market step then degrades on every row. Unchecked here until 2026-10-21, when Tiingo
    refused all 43 of run 39565710165's requests (403) and nothing had said so. The request is the
    one that run makes — daily prices, five years back — and Tiingo's own reason is printed."""
    key = os.environ.get("TIINGO_API_KEY")
    if not key:
        print("TIINGO_API_KEY: WARN — secret not set (optional: P/E history reads two years)")
        return True
    if padded("TIINGO_API_KEY", key):
        return False
    try:
        r = httpx.get(
            "https://api.tiingo.com/tiingo/daily/aapl/prices",
            params={"startDate": "2021-10-01", "endDate": "2021-10-08", "format": "json"},
            headers={"Authorization": f"Token {key}"},
            timeout=30,
        )
    except Exception as e:
        print(f"TIINGO_API_KEY: FAIL — {type(e).__name__}: {str(e)[:160]}")
        return False
    if r.status_code == 200:
        print("TIINGO_API_KEY: PASS — 200 from tiingo/daily/aapl/prices")
        return True
    try:
        body = r.json()
        why = str(body.get("detail", "")) if isinstance(body, dict) else ""
    except ValueError:
        why = ""
    why = why.replace(key, "<key>")[:160] or "no reason given"
    print(f"TIINGO_API_KEY: FAIL — HTTP {r.status_code}: {why}")
    return False


def check_sec() -> bool:
    # SEC_USER_AGENT is OPTIONAL (EDGAR works with a default UA), so this never fails the run;
    # it just reports whether the secret is set and EDGAR is reachable.
    secret = os.environ.get("SEC_USER_AGENT")
    ua = secret or "vinci-research validate-keys"
    try:
        r = httpx.get(
            "https://data.sec.gov/submissions/CIK0000320193.json",  # Apple — a stable public doc
            headers={"User-Agent": ua},
            timeout=30,
        )
    except Exception as e:
        print(f"SEC_USER_AGENT: WARN — {type(e).__name__}: {str(e)[:160]}")
        return True
    tag = "secret set" if secret else "secret unset → default UA (fine; it's optional)"
    status = "PASS" if r.status_code == 200 else "WARN"
    print(f"SEC_USER_AGENT: {status} — EDGAR HTTP {r.status_code} ({tag})")
    return True


def main() -> int:
    print("=== validate-keys: pinging each service (key values never printed) ===")
    anthropic_ok = check_anthropic()
    polygon_ok = check_polygon()
    tiingo_ok = check_tiingo()  # optional — fails the run only when set and refused
    check_sec()  # optional — informational, never fails the run
    ok = anthropic_ok and polygon_ok and tiingo_ok
    print(f"\n=== {'ALL KEYS VALID' if ok else 'A KEY FAILED'} ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
