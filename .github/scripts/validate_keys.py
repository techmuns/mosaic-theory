#!/usr/bin/env python3
"""On-demand validator that the API-key SECRETS are set + valid in this environment.

Pings each external service with a tiny request. Prints PASS/FAIL per key — NEVER the key
value. Exits non-zero if a REQUIRED key (Polygon, Anthropic) is missing or rejected, so the
`validate-keys` workflow goes red. Run via workflow_dispatch. Cheap: ~1 trivial call each.
"""
from __future__ import annotations

import os
import sys

import httpx


def check_anthropic() -> bool:
    # Returns False ONLY on a real key problem (auth/permission). A connectivity error from the
    # runner to api.anthropic.com is a WARN (environment, not the key) — it does NOT fail the run.
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("ANTHROPIC_API_KEY: FAIL — secret not set / empty")
        return False
    if padded("ANTHROPIC_API_KEY", key):
        return False
    import anthropic

    try:
        anthropic.Anthropic(api_key=key).messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
        print(f"ANTHROPIC_API_KEY: FAIL — {type(e).__name__} (bad key or no model access)")
        return False
    except Exception as e:
        print(
            f"ANTHROPIC_API_KEY: WARN — {type(e).__name__}: {str(e)[:110]} "
            "(runner→api.anthropic.com connectivity, NOT a key problem)"
        )
        return True
    print("ANTHROPIC_API_KEY: PASS — authenticated")
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
    check_sec()  # optional — informational, never fails the run
    required_ok = anthropic_ok and polygon_ok
    print(f"\n=== {'ALL REQUIRED KEYS VALID' if required_ok else 'A REQUIRED KEY FAILED'} ===")
    return 0 if required_ok else 1


if __name__ == "__main__":
    sys.exit(main())
