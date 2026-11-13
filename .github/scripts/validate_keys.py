#!/usr/bin/env python3
"""On-demand validator that the API-key SECRETS are set + valid in this environment.

Pings each external service with a tiny request. Prints PASS/FAIL per key — NEVER the key
value. Exits non-zero if a REQUIRED key (Polygon, Anthropic, the four R2 values) is missing or
rejected, or an OPTIONAL value that is set (Tiingo, SEC_USER_AGENT) is rejected, so the
`validate-keys` workflow goes red. Run via workflow_dispatch. Cheap: ~1 trivial call each, and
none to SEC (`check_sec`).
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path
from types import ModuleType

import httpx

#: the model the pipelines call — `vinci.config.Config.graph_llm_model` and
#: `vinci.theme_intelligence.config.LLM_MODEL` (this script cannot import `vinci`: the workflow
#: installs the lock's packages, never `vinci` itself). A test fails when they differ. Pinged
#: until 2026-10-21 was Haiku, so a key that could use Haiku but not the pipelines' model passed.
PIPELINE_MODEL = "claude-opus-4-8"


def check_anthropic() -> bool:
    # Returns False on a real key or account problem: auth, permission, no access to the
    # pipelines' model, or any other 4xx answer (a 400 "credit balance too low" is the account,
    # and the weekly run would hit it). A WARN that does NOT fail the run is kept for what is
    # transient or the runner's environment: no connection, a timeout, 408, 429 and 5xx.
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
    except anthropic.APIStatusError as e:
        error = e.body.get("error", {}) if isinstance(e.body, dict) else {}
        why = f"{error.get('type', type(e).__name__)}: {error.get('message', '')}"
        why = why.replace(key, "<key>")[:160]
        if e.status_code in (408, 429) or e.status_code >= 500:
            print(f"ANTHROPIC_API_KEY: WARN — HTTP {e.status_code} {why} (transient: a rate "
                  "limit or the service, NOT a key problem)")
            return True
        print(f"ANTHROPIC_API_KEY: FAIL — HTTP {e.status_code} {why}")
        return False
    except anthropic.APIConnectionError as e:  # its timeout is one too
        print(
            f"ANTHROPIC_API_KEY: WARN — {type(e).__name__}: {str(e)[:110]} "
            "(runner→api.anthropic.com connectivity, NOT a key problem)"
        )
        return True
    except Exception as e:
        # ANYTHING ELSE IS NOT CONNECTIVITY (fix request 2, RH-D8). This branch printed
        # "connectivity, NOT a key problem" and passed for every exception, so an SDK change (a
        # TypeError on a renamed argument) or a bug here read as a valid key. The check did not
        # run: that fails.
        print(f"ANTHROPIC_API_KEY: FAIL — {type(e).__name__}: "
              f"{str(e).replace(key, '<key>')[:110]} (an unexpected error: the check did not run, "
              "so the key is not shown valid)")
        return False
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


def _load_sigv4() -> ModuleType:
    """The fact layer's own SigV4 signer, loaded BY PATH: this script cannot import `vinci` (the
    workflow installs the lock's packages, never `vinci` itself), and `vinci/facts/sigv4.py`
    imports the standard library only (tests/test_facts_remote.py holds it to that). One signer
    for the key check and the uploads, so a check that passes signs the way the uploads sign."""
    path = Path(__file__).resolve().parents[2] / "vinci" / "facts" / "sigv4.py"
    spec = importlib.util.spec_from_file_location("vinci_facts_sigv4", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load the signer at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_r2() -> bool:
    """The fact layer's R2 bucket (vinci/facts/remote.py). All four values are REQUIRED: one
    signed HeadBucket, which a read-only token should pass (CI may hold one; only this repo's
    ingest machine writes; untested with a read-only pair, 2026-11-05). Prints PASS/FAIL and the
    HTTP status only — never the account id, the endpoint (which contains it) or the bucket
    name."""
    values = {
        "R2_ACCOUNT_ID": os.environ.get("R2_ACCOUNT_ID") or "",
        "R2_ACCESS_KEY_ID": os.environ.get("R2_ACCESS_KEY_ID") or "",
        "R2_SECRET_ACCESS_KEY": os.environ.get("R2_SECRET_ACCESS_KEY") or "",
        "R2_BUCKET": os.environ.get("R2_BUCKET") or "",
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        print(f"R2: FAIL — secret not set / empty: {', '.join(missing)}")
        return False
    if [name for name, value in values.items() if padded(name, value)]:
        return False
    sigv4 = _load_sigv4()
    host = f"{values['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    path = f"/{values['R2_BUCKET']}"
    headers = sigv4.sign("HEAD", host, path, access_key=values["R2_ACCESS_KEY_ID"],
                         secret_key=values["R2_SECRET_ACCESS_KEY"], region="auto")
    try:
        r = httpx.request("HEAD", f"https://{host}{sigv4.canonical_uri(path)}", headers=headers,
                          timeout=30)
    except Exception as e:
        # the exception's text carries the URL, and the URL the account id: its type only
        print(f"R2: FAIL — {type(e).__name__} (no answer from the bucket's endpoint)")
        return False
    if r.status_code == 200:
        print("R2: PASS — HeadBucket HTTP 200")
        return True
    print(f"R2: FAIL — HeadBucket HTTP {r.status_code} (403 ⇒ the token may not read this "
          "bucket; 404 ⇒ no such bucket in this account)")
    return False


#: `vinci.config.sec_user_agent`'s rule, which this script cannot import (the workflow installs the
#: lock's packages, never `vinci` itself). A test pins the two equal.
SEC_UA_PLACEHOLDER_EMAIL = "your@email.com"
SEC_UA_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}")


def check_sec() -> bool:
    """SEC_USER_AGENT is a declared identity, not a key — EDGAR authenticates nothing — so this
    checks it as `vinci.config.sec_user_agent` does before every SEC request, and SENDS NOTHING.

    It used to GET a submissions document with "vinci-research validate-keys" as the agent when the
    secret was unset: a request with no declared contact, outside the machine's one shared SEC
    budget (`vinci.netcache.sec_pace`), proving only that EDGAR was up (fix request 2, RE1-D17).
    Unset is fine — the pipelines then send vinci's own default, which declares a contact. Set and
    refused by that rule fails the run: the pipelines would refuse it at their first SEC call."""
    ua = (os.environ.get("SEC_USER_AGENT") or "").strip()
    if not ua:
        print("SEC_USER_AGENT: PASS — not set; the pipelines send vinci's default, which declares "
              "a contact (no request sent)")
        return True
    if SEC_UA_PLACEHOLDER_EMAIL in ua.lower():
        print("SEC_USER_AGENT: FAIL — still the .env.example placeholder; set a name and an email "
              "SEC can reach")
        return False
    if not SEC_UA_EMAIL.search(ua):
        print("SEC_USER_AGENT: FAIL — carries no contact email; SEC fair-access requires one")
        return False
    print("SEC_USER_AGENT: PASS — declares a contact (no request sent)")
    return True


def main() -> int:
    print("=== validate-keys: pinging each service (key values never printed) ===")
    anthropic_ok = check_anthropic()
    polygon_ok = check_polygon()
    tiingo_ok = check_tiingo()  # optional — fails the run only when set and refused
    r2_ok = check_r2()
    sec_ok = check_sec()  # optional — fails the run only when set and refused
    ok = anthropic_ok and polygon_ok and tiingo_ok and r2_ok and sec_ok
    print(f"\n=== {'ALL KEYS VALID' if ok else 'A KEY FAILED'} ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
