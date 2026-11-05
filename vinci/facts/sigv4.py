"""AWS Signature Version 4 for S3-compatible requests (Cloudflare R2): the header-based form.

STANDARD LIBRARY ONLY, AND IMPORTS NOTHING FROM ``vinci``. ``.github/scripts/validate_keys.py``
loads this file by path to sign its R2 ping, and that workflow installs only ``anthropic`` and
``httpx``; a test fails if this module imports anything else. One signer, used by the fact layer's
R2 client (:mod:`vinci.facts.remote`) and by the key check, so the two cannot drift.

PINNED TO AWS'S OWN WORKED EXAMPLES. AWS publishes four signed S3 requests (GET Object, PUT
Object, GET Bucket Lifecycle, GET Bucket with a query) with their exact signatures, in "Signature
Calculations for the Authorization Header" (S3 API reference); ``tests/test_facts_remote.py``
reproduces all four byte for byte (``tests/fixtures/facts/sigv4_aws_s3_examples.json``).

THE S3 RULES, which differ from other AWS services: the canonical URI is each path segment
percent-encoded ONCE (RFC 3986 unreserved characters kept, ``/`` kept between segments, never
normalised); the canonical query sorts parameters by encoded name and keeps an empty value as
``name=``; every header sent is signed, its name lower-cased and its value trimmed.
"""
from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from urllib.parse import quote

ALGORITHM = "AWS4-HMAC-SHA256"
#: The sha256 of an empty body: what a GET, HEAD or DELETE signs as its payload.
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def _encode(text: str) -> str:
    """RFC 3986: every byte but ``A-Z a-z 0-9 - _ . ~`` as ``%XX``, upper-case hex."""
    return quote(text, safe="-_.~")


def canonical_uri(path: str) -> str:
    """``/bucket/key`` with each segment encoded once; ``""`` is ``/``."""
    if not path:
        return "/"
    return "/".join(_encode(seg) for seg in path.split("/"))


def canonical_query(params: Sequence[tuple[str, str]]) -> str:
    return "&".join(f"{k}={v}" for k, v in sorted((_encode(k), _encode(v)) for k, v in params))


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def signing_key(secret_key: str, day: str, region: str, service: str) -> bytes:
    k = _hmac(("AWS4" + secret_key).encode("utf-8"), day)
    return _hmac(_hmac(_hmac(k, region), service), "aws4_request")


def amz_date(now: datetime | None = None) -> str:
    """``YYYYMMDDTHHMMSSZ`` in UTC."""
    return (now or datetime.now(UTC)).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def sign(method: str, host: str, path: str, *, query: Sequence[tuple[str, str]] = (),
         headers: Mapping[str, str] | None = None, payload_sha256: str = EMPTY_SHA256,
         access_key: str, secret_key: str, region: str, service: str = "s3",
         now: datetime | None = None) -> dict[str, str]:
    """The headers to send: ``headers`` plus ``host``, ``x-amz-date``, ``x-amz-content-sha256``
    and ``Authorization``, every one of them signed.

    ``payload_sha256`` is the hex sha256 of the body as sent (S3 then refuses a body that does
    not hash to it). ``x-amz-date`` is taken from ``headers`` when given there, else from
    ``now``."""
    out = {k.lower(): " ".join(str(v).split()) for k, v in (headers or {}).items()}
    out["host"] = host
    out.setdefault("x-amz-date", amz_date(now))
    out["x-amz-content-sha256"] = payload_sha256
    stamp = out["x-amz-date"]
    day = stamp[:8]
    names = sorted(out)
    signed = ";".join(names)
    canonical = "\n".join([
        method.upper(),
        canonical_uri(path),
        canonical_query(query),
        "".join(f"{n}:{out[n]}\n" for n in names),
        signed,
        payload_sha256,
    ])
    scope = f"{day}/{region}/{service}/aws4_request"
    to_sign = "\n".join([ALGORITHM, stamp, scope,
                         hashlib.sha256(canonical.encode("utf-8")).hexdigest()])
    signature = hmac.new(signing_key(secret_key, day, region, service), to_sign.encode("utf-8"),
                         hashlib.sha256).hexdigest()
    out["authorization"] = (f"{ALGORITHM} Credential={access_key}/{scope},"
                            f"SignedHeaders={signed},Signature={signature}")
    return out
