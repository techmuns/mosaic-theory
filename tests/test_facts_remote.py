"""The fact layer's R2 location (vinci/facts/remote.py, vinci/facts/sigv4.py): signed, immutable,
read back, and never printing the endpoint.

The signer is pinned to AWS's own four worked S3 examples. Everything else runs the REAL committed
pages snapshot (``data/facts/manifests/edgar-4f3207f4da9fb71a.json`` and its 379 committed objects)
through :class:`FakeBucket`, an ``httpx.MockTransport`` that keeps S3's rules the client relies on:
``If-None-Match: *`` refuses an existing key (412), a body that does not match its ``Content-MD5``
is refused (400 BadDigest), ``x-amz-content-sha256`` must hash the body, and ListObjectsV2 pages
with a continuation token. No test reaches the network.
"""
from __future__ import annotations

import ast
import base64
import hashlib
import importlib.util
import json
import logging
import shutil
import sys
from datetime import date
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import parse_qsl, unquote

import httpx
import pytest

from vinci.facts import open_store
from vinci.facts.edgar_ingest import (
    EXTRACTOR,
    EXTRACTOR_VERSION,
    SOURCE,
    rows_from_companyfacts,
)
from vinci.facts.reader import FactStore
from vinci.facts.remote import (
    R2Client,
    R2Config,
    R2NotConfiguredError,
    R2Objects,
    R2RequestError,
    RemoteBytesDifferError,
    RemoteObjectMissingError,
    bucket_against_manifests,
    manifest_objects,
    upload_snapshot,
)
from vinci.facts.sigv4 import canonical_uri, sign
from vinci.facts.store import (
    FactsStoreError,
    RemoteStoreNotConfiguredError,
    build_manifest,
    is_r2,
    load_manifest,
    store_root,
    write_entity,
)

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "facts"
PAGES = "edgar-4f3207f4da9fb71a"
OBJECTS = ROOT / "data" / "facts" / "objects"
ACCOUNT = "0123456789abcdef0123456789abcdef"
CONFIG = R2Config(ACCOUNT, "AKFAKEACCESSKEY", "fake/secret+access=key", "fake-facts-bucket")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _err(status: int, code: str) -> httpx.Response:
    return httpx.Response(status, content=f"<Error><Code>{code}</Code></Error>".encode())


def _resigned(request: httpx.Request) -> str:
    """The Authorization the RECEIVED request should carry: its method, its raw path and query as
    sent, the headers it says it signed, and its body's own hash (round 2: the client signing one
    path or query and sending another passed every test)."""
    auth = request.headers["authorization"]
    names = auth.split("SignedHeaders=", 1)[1].split(",", 1)[0].split(";")
    path, _, qs = request.url.raw_path.decode().partition("?")
    return sign(request.method, request.url.host, unquote(path),
                query=parse_qsl(qs, keep_blank_values=True),
                headers={n: request.headers[n] for n in names
                         if n not in ("host", "x-amz-content-sha256")},
                payload_sha256=_sha(request.content), access_key=CONFIG.access_key_id,
                secret_key=CONFIG.secret_access_key, region="auto")["authorization"]


def _flip(data: bytes) -> bytes:
    """The same bytes with the last bit flipped: a corruption no size check can see."""
    return data[:-1] + bytes([data[-1] ^ 1])


class FakeBucket:
    """One R2 bucket in memory, keeping the S3 rules the client depends on."""

    def __init__(self, *, writable: bool = True, page: int = 1000) -> None:
        self.objects: dict[str, bytes] = {}
        self.requests: list[httpx.Request] = []
        self.writable = writable
        self.page = page

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        assert request.url.host == f"{ACCOUNT}.r2.cloudflarestorage.com"
        assert request.headers["authorization"].startswith(
            "AWS4-HMAC-SHA256 Credential=AKFAKEACCESSKEY/")
        if request.headers["authorization"] != _resigned(request):
            return _err(403, "SignatureDoesNotMatch")
        body = request.content
        assert request.headers["x-amz-content-sha256"] == _sha(body)
        bucket, _, key = request.url.path.lstrip("/").partition("/")
        assert bucket == CONFIG.bucket
        if not key:
            if request.method == "HEAD":
                return httpx.Response(200)
            if request.method == "GET" and request.url.params.get("list-type") == "2":
                return self._list(request)
            return _err(400, "Unsupported")
        if request.method == "PUT":
            if not self.writable:
                return _err(403, "AccessDenied")
            want = base64.b64encode(hashlib.md5(body, usedforsecurity=False).digest()).decode()
            if request.headers.get("content-md5") != want:
                return _err(400, "BadDigest")
            if request.headers.get("if-none-match") == "*" and key in self.objects:
                return _err(412, "PreconditionFailed")
            self.objects[key] = body
            return httpx.Response(200)
        if request.method == "GET":
            if key not in self.objects:
                return _err(404, "NoSuchKey")
            return httpx.Response(200, content=self.objects[key])
        return _err(400, "Unsupported")

    def _list(self, request: httpx.Request) -> httpx.Response:
        params = request.url.params
        prefix = params.get("prefix", "")
        token = params.get("continuation-token")
        after = base64.b64decode(token).decode() if token else ""
        keys = [k for k in sorted(self.objects) if k.startswith(prefix) and k > after]
        size = min(int(params.get("max-keys", "1000")), self.page)
        page, more = keys[:size], len(keys) > size
        ns = "http://s3.amazonaws.com/doc/2006-03-01/"
        items = "".join(f"<Contents><Key>{k}</Key><Size>{len(self.objects[k])}</Size></Contents>"
                        for k in page)
        nxt = (f"<NextContinuationToken>{base64.b64encode(page[-1].encode()).decode()}"
               "</NextContinuationToken>") if more else ""
        xml = (f'<ListBucketResult xmlns="{ns}"><IsTruncated>{"true" if more else "false"}'
               f"</IsTruncated>{items}{nxt}</ListBucketResult>")
        return httpx.Response(200, content=xml.encode())


def _client(bucket: FakeBucket) -> R2Client:
    return R2Client(CONFIG, transport=httpx.MockTransport(bucket), sleep=lambda s: None)


@pytest.fixture(scope="module")
def pages() -> dict[str, Any]:
    return load_manifest(PAGES)


# --- the signer ------------------------------------------------------------------------------

def _examples() -> dict[str, Any]:
    fx: dict[str, Any] = json.loads((FIXTURES / "sigv4_aws_s3_examples.json").read_text())
    return fx


def _sign_example(fx: dict[str, Any], e: dict[str, Any], **override: str) -> str:
    args = {"access_key": fx["access_key"], "secret_key": fx["secret_key"],
            "region": fx["region"], **override}
    return sign(e["method"], fx["host"], override.get("path", e["path"]),
                query=[(k, v) for k, v in e["query"]],
                headers={**e["headers"], "x-amz-date": override.get("date", fx["x_amz_date"])},
                payload_sha256=e["payload_sha256"], access_key=args["access_key"],
                secret_key=args["secret_key"], region=args["region"])["authorization"]


def test_the_signer_reproduces_aws_s_four_worked_s3_examples() -> None:
    """POSITIVE: AWS's published signatures, byte for byte (GET and PUT Object, a query with an
    empty value, a sorted two-parameter query, a ``$`` encoded once in the key)."""
    fx = _examples()
    assert len(fx["examples"]) == 4
    for e in fx["examples"]:
        if "body" in e:
            assert _sha(e["body"].encode()) == e["payload_sha256"]
        assert _sign_example(fx, e) == e["authorization"], e["name"]


def test_every_input_of_the_signature_is_signed() -> None:
    """NEGATIVE: the secret, the day, the region and the path each change the signature."""
    fx = _examples()
    e = fx["examples"][0]
    for change in ({"secret_key": fx["secret_key"] + "x"}, {"date": "20130525T000000Z"},
                   {"region": "auto"}, {"path": "/test.txT"}):
        assert _sign_example(fx, e, **change) != e["authorization"], change
    assert canonical_uri("/b/test$file.text") == "/b/test%24file.text"
    assert canonical_uri("") == "/"


def test_the_signer_imports_the_standard_library_only() -> None:
    """validate_keys.py loads it by path in a job that installs only anthropic and httpx."""
    tree = ast.parse((ROOT / "vinci" / "facts" / "sigv4.py").read_text())
    names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)
             for a in n.names}
    names |= {str(n.module).split(".")[0] for n in ast.walk(tree)
              if isinstance(n, ast.ImportFrom) and n.module}
    assert names <= set(sys.stdlib_module_names) | {"__future__"}, names


# --- the upload ------------------------------------------------------------------------------

def test_the_committed_pages_snapshot_uploads_once_and_reads_back(
        pages: dict[str, Any]) -> None:
    """POSITIVE, on the real committed snapshot: every object written and read back against the
    manifest; a second upload writes nothing and finds every object already there."""
    bucket = FakeBucket()
    with _client(bucket) as client:
        first = upload_snapshot(pages, OBJECTS, client, workers=4)
        again = upload_snapshot(pages, OBJECTS, client, workers=4)
        audit = bucket_against_manifests(client, [pages])
    n = pages["totals"]["files"] + pages["totals"]["order_files"]
    size = pages["totals"]["bytes"] + pages["totals"]["order_bytes"]
    assert (first.objects, first.bytes) == (n, size) == (379, 6_584_136)
    assert (first.written, first.written_bytes, first.present) == (n, size, 0)
    assert (first.read_back, first.read_back_bytes, first.problems) == (n, size, [])
    assert (again.written, again.present, again.read_back, again.problems) == (0, n, n, [])
    assert {k: _sha(v) for k, v in bucket.objects.items()} == {
        e["path"]: e["sha256"] for e in manifest_objects(pages)}
    assert audit == {"bucket_keys": n, "bucket_bytes": size, "named_by_a_manifest": n,
                     "named_by_none": 0, "named_and_absent": 0, "size_differs": 0,
                     "manifest_objects": n, "manifest_bytes": size}


def test_other_bytes_under_an_existing_key_are_refused_never_overwritten(
        pages: dict[str, Any]) -> None:
    """NEGATIVE: the key exists with other bytes; the upload reports it, and the bucket still
    holds what it held."""
    bucket = FakeBucket()
    victim = manifest_objects(pages)[7]["path"]
    bucket.objects[victim] = b"not the sealed bytes"
    with _client(bucket) as client:
        rep = upload_snapshot(pages, OBJECTS, client, workers=4)
        with pytest.raises(RemoteBytesDifferError, match="never overwritten"):
            client.put_new(victim, (OBJECTS / victim).read_bytes())
    assert bucket.objects[victim] == b"not the sealed bytes"
    assert len(rep.problems) == 1 and victim in rep.problems[0]
    assert (rep.written, rep.present, rep.read_back) == (378, 0, 0)


def test_a_put_carries_if_none_match_and_the_body_s_own_digest() -> None:
    """What the bucket's two refusals key on: ``If-None-Match: *`` and the body's Content-MD5."""
    bucket = FakeBucket()
    with _client(bucket) as client:
        assert client.put_new("k/1.parquet", b"abc") is True
    put = bucket.requests[-1]
    assert put.headers["if-none-match"] == "*"
    assert put.headers["content-md5"] == base64.b64encode(
        hashlib.md5(b"abc", usedforsecurity=False).digest()).decode()


def test_an_unsealed_local_copy_uploads_nothing(pages: dict[str, Any], tmp_path: Path) -> None:
    """NEGATIVE: one local object's bytes changed; refused before any request."""
    local = tmp_path / "objects"
    shutil.copytree(OBJECTS, local)
    target = local / pages["files"][3]["path"]
    target.write_bytes(target.read_bytes()[:-1] + b"\0")
    bucket = FakeBucket()
    with _client(bucket) as client, pytest.raises(FactsStoreError, match="nothing was uploaded"):
        upload_snapshot(pages, local, client, workers=4)
    assert bucket.requests == []


def test_a_token_that_may_not_write_stops_the_upload(pages: dict[str, Any]) -> None:
    """A read-only token (the one CI may hold): the first refused PUT stops the rest."""
    bucket = FakeBucket(writable=False)
    with _client(bucket) as client:
        rep = upload_snapshot(pages, OBJECTS, client, workers=1)
    assert rep.written == 0 and rep.problems and "HTTP 403 AccessDenied" in rep.problems[0]
    assert rep.not_attempted == 378 and rep.read_back == 0
    assert bucket.objects == {}


def test_a_transient_failure_is_retried_then_reported_without_the_endpoint() -> None:
    calls: list[httpx.Request] = []

    def down(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        raise httpx.ConnectError(f"cannot reach {request.url}")

    client = R2Client(CONFIG, transport=httpx.MockTransport(down), retries=2,
                      sleep=lambda s: None)
    with client, pytest.raises(R2RequestError) as got:
        client.get("edgar/x/2020/y.parquet")
    assert len(calls) == 3
    assert "ConnectError after 3 attempts" in str(got.value)
    for secret in CONFIG.secrets():
        assert secret not in str(got.value)


# --- no list of names: mosaic-theory holds back no name (operator ruling 2026-11-05) ---------

def test_the_committed_snapshot_uploads_with_no_exclusion_list(monkeypatch: pytest.MonkeyPatch,
                                                               pages: dict[str, Any]) -> None:
    """On main this command was REFUSED before any request: the snapshot was written excluding 1
    name of a list of 6 under the lifted hold, and no `--exclude` was passed. It now uploads, and
    every object reads back against the manifest."""
    from vinci.facts import remote
    from vinci.facts.__main__ import main
    assert (pages["scope"]["excluded_by_operator_instruction"],
            pages["scope"]["exclusions_listed"]) == (1, 6)
    bucket = FakeBucket()
    monkeypatch.setattr(remote.R2Client, "from_env", classmethod(lambda cls: _client(bucket)))
    assert main(["upload", "--no-audit", "--workers", "2"]) == 0
    assert {k: _sha(v) for k, v in bucket.objects.items()} == {
        e["path"]: e["sha256"] for e in manifest_objects(pages)}


def test_an_upload_given_exclude_fails_loud_before_any_request(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """An upload has no names to skip: a snapshot goes up whole. On main `--exclude` was the
    held-name list, refused here for naming 1 where the snapshot was written with 6. The flag is
    gone, so a copied command line is refused by argparse, and nothing is requested."""
    from vinci.facts import remote
    from vinci.facts.__main__ import main
    bucket = FakeBucket()
    monkeypatch.setattr(remote.R2Client, "from_env", classmethod(lambda cls: _client(bucket)))
    with pytest.raises(SystemExit) as refused:
        main(["upload", "--no-audit", "--workers", "2", "--exclude", "ZZQA"])
    assert refused.value.code == 2
    assert "unrecognized arguments: --exclude ZZQA" in capsys.readouterr().err
    assert bucket.requests == []


# --- reading from R2 -------------------------------------------------------------------------

def _uploaded(pages: dict[str, Any]) -> FakeBucket:
    bucket = FakeBucket()
    for e in manifest_objects(pages):
        bucket.objects[e["path"]] = (OBJECTS / e["path"]).read_bytes()
    return bucket


def test_a_reader_with_an_empty_cache_reads_the_snapshot_from_r2(
        pages: dict[str, Any], tmp_path: Path) -> None:
    """POSITIVE: the same facts through R2 as from the committed objects, for every company."""
    bucket = _uploaded(pages)
    remote = R2Objects(_client(bucket), tmp_path / "cache")
    entities = [e["entity"] for e in pages["entities"]]
    with FactStore(PAGES, root="r2://", remote=remote) as far, open_store(PAGES) as near:
        for ent in entities:
            assert far.companyfacts_as_of(ent, date(2026, 6, 30)) == \
                near.companyfacts_as_of(ent, date(2026, 6, 30))
    fetched = sorted(p.relative_to(tmp_path / "cache").as_posix()
                     for p in (tmp_path / "cache").rglob("*.parquet"))
    assert fetched == [e["path"] for e in manifest_objects(pages)]


def test_a_missing_or_altered_object_raises_and_nothing_falls_back(
        pages: dict[str, Any], tmp_path: Path) -> None:
    """NEGATIVE: the committed objects are on disk here, and r2:// still never reads them."""
    ent = pages["files"][0]["entity"]
    gone = _uploaded(pages)
    del gone.objects[pages["files"][0]["path"]]
    with FactStore(PAGES, root="r2://", remote=R2Objects(_client(gone), tmp_path / "a")) as s, \
            pytest.raises(RemoteObjectMissingError, match="not in the R2 bucket"):
        s.companyfacts_as_of(ent, date(2026, 6, 30))
    altered = _uploaded(pages)
    altered.objects[pages["files"][0]["path"]] += b"\0"
    with FactStore(PAGES, root="r2://", remote=R2Objects(_client(altered), tmp_path / "b")) as s, \
            pytest.raises(FactsStoreError, match="are not the manifest's"):
        s.companyfacts_as_of(ent, date(2026, 6, 30))
    assert not (tmp_path / "b" / pages["files"][0]["path"]).exists()


def test_a_corrupted_cache_copy_is_fetched_again(pages: dict[str, Any], tmp_path: Path) -> None:
    bucket = _uploaded(pages)
    remote = R2Objects(_client(bucket), tmp_path / "cache")
    entry = pages["files"][0]
    path, fresh = remote.fetch(entry)
    assert fresh and _sha(path.read_bytes()) == entry["sha256"]
    path.write_bytes(b"corrupted")
    path, fresh = remote.fetch(entry)
    assert fresh and _sha(path.read_bytes()) == entry["sha256"]
    assert remote.fetch(entry)[1] is False                  # now cached and checked


def test_fetch_all_counts_every_failure(pages: dict[str, Any], tmp_path: Path) -> None:
    bucket = _uploaded(pages)
    entries = manifest_objects(pages)
    for e in entries[:3]:
        del bucket.objects[e["path"]]
    rep = R2Objects(_client(bucket), tmp_path / "c").fetch_all(entries, workers=4)
    assert (rep.objects, rep.fetched, rep.cached, len(rep.problems)) == (379, 376, 0, 3)


def test_the_bucket_is_listed_across_pages_and_a_stray_key_is_counted(
        pages: dict[str, Any]) -> None:
    bucket = _uploaded(pages)
    bucket.page = 50
    bucket.objects["edgar/stray/2020/x.parquet"] = b"x"
    with _client(bucket) as client:
        keys = dict(client.list_objects())
        audit = bucket_against_manifests(client, [pages])
    assert len(keys) == 380
    assert sum(1 for r in bucket.requests if r.url.params.get("list-type")) == 2 * 8
    assert (audit["named_by_none"], audit["named_and_absent"]) == (1, 0)


# --- the location ----------------------------------------------------------------------------

def test_r2_is_a_reader_s_location_and_never_a_writer_s(monkeypatch: pytest.MonkeyPatch) -> None:
    assert is_r2("r2://") and is_r2("R2://") and not is_r2("data/facts/local")
    for raw in ("r2://facts", "r2://bucket/prefix"):
        with pytest.raises(RemoteStoreNotConfiguredError, match="alone"):
            is_r2(raw)
    with pytest.raises(RemoteStoreNotConfiguredError, match="local directory"):
        store_root("r2://", storage="local")
    monkeypatch.setenv("VINCI_FACTS_STORE", "r2://")
    with pytest.raises(RemoteStoreNotConfiguredError, match="local directory"):
        store_root(storage="local")
    with pytest.raises(RemoteStoreNotConfiguredError, match="only one configured is R2"):
        store_root("s3://facts")


def test_r2_without_its_variables_names_them_never_a_value(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("R2_BUCKET", "some-bucket")
    with pytest.raises(R2NotConfiguredError) as got:
        FactStore(PAGES, root="r2://")
    msg = str(got.value)
    assert "R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY" in msg
    assert "some-bucket" not in msg
    monkeypatch.setenv("R2_ACCOUNT_ID", "abc")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "k ")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "s")
    with pytest.raises(R2NotConfiguredError, match="R2_ACCESS_KEY_ID has leading or trailing"):
        R2Config.from_env()


def test_the_config_and_the_client_never_print_their_values() -> None:
    for text in (repr(CONFIG), repr(_client(FakeBucket()))):
        for secret in CONFIG.secrets():
            assert secret not in text


def test_the_request_log_never_carries_the_account_or_the_bucket(
        caplog: pytest.LogCaptureFixture, pages: dict[str, Any]) -> None:
    """httpx logs every request's URL at INFO; the client's filter replaces the four values."""
    caplog.set_level(logging.DEBUG)
    bucket = _uploaded(pages)
    with _client(bucket) as client:
        client.head_bucket()
        client.get(pages["files"][0]["path"])
    lines = [r.getMessage() for r in caplog.records if r.name == "httpx"]
    assert len(lines) == 2 and all("<r2>" in line for line in lines)
    for secret in CONFIG.secrets():
        assert secret not in caplog.text


# --- validate-keys ---------------------------------------------------------------------------

def _validator() -> ModuleType:
    path = ROOT / ".github" / "scripts" / "validate_keys.py"
    spec = importlib.util.spec_from_file_location("validate_keys_under_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def r2_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in zip(("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY",
                            "R2_BUCKET"), CONFIG.secrets(), strict=True):
        monkeypatch.setenv(name, value)


@pytest.mark.parametrize(("status", "verdict"), [(200, "R2: PASS"), (403, "R2: FAIL"),
                                                 (404, "R2: FAIL")])
def test_validate_keys_heads_the_bucket_and_prints_only_a_verdict(
        r2_env: None, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        status: int, verdict: str) -> None:
    """POSITIVE (200) and NEGATIVE (403, 404): one signed HeadBucket, the status printed, no
    value."""
    v = _validator()
    seen: list[tuple[str, str, dict[str, str]]] = []

    def request(method: str, url: str, **kw: Any) -> httpx.Response:
        seen.append((method, url, kw["headers"]))
        return httpx.Response(status)

    monkeypatch.setattr(v.httpx, "request", request)
    assert v.check_r2() is (status == 200)
    out = capsys.readouterr().out
    assert out.startswith(verdict) and f"HTTP {status}" in out
    for secret in CONFIG.secrets():
        assert secret not in out
    ((method, url, headers),) = seen
    assert method == "HEAD"
    assert url == f"https://{ACCOUNT}.r2.cloudflarestorage.com/{CONFIG.bucket}"
    assert headers["authorization"].startswith("AWS4-HMAC-SHA256 Credential=AKFAKEACCESSKEY/")
    assert "/auto/s3/aws4_request" in headers["authorization"]


def test_validate_keys_fails_an_unset_or_padded_r2_secret(
        r2_env: None, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    v = _validator()
    monkeypatch.setattr(v.httpx, "request", lambda *a, **k: pytest.fail("no request expected"))
    monkeypatch.delenv("R2_BUCKET")
    assert v.check_r2() is False
    assert "R2_BUCKET" in capsys.readouterr().out
    monkeypatch.setenv("R2_BUCKET", CONFIG.bucket + "\n")
    assert v.check_r2() is False
    out = capsys.readouterr().out
    assert "R2_BUCKET: FAIL" in out and CONFIG.bucket not in out


def test_validate_keys_signs_with_the_fact_layer_s_own_signer() -> None:
    v = _validator()
    assert Path(v._load_sigv4().__file__).resolve() == ROOT / "vinci" / "facts" / "sigv4.py"


def test_a_refused_r2_check_turns_the_validator_red(monkeypatch: pytest.MonkeyPatch) -> None:
    """The R2 check is wired into the verdict. NEGATIVE: every check passing exits 0."""
    v = _validator()
    for name in ("check_anthropic", "check_polygon", "check_tiingo", "check_sec"):
        monkeypatch.setattr(v, name, lambda: True)
    monkeypatch.setattr(v, "check_r2", lambda: False)
    assert v.main() == 1
    monkeypatch.setattr(v, "check_r2", lambda: True)
    assert v.main() == 0


class _RottingBucket(FakeBucket):
    """Accepts a PUT (its digest checked) and stores other bytes OF THE SAME SIZE: what the
    read-back's hash is for (round 2: an appended byte let a size compare pass the suite)."""

    def __call__(self, request: httpx.Request) -> httpx.Response:
        r = super().__call__(request)
        _, _, key = request.url.path.lstrip("/").partition("/")
        if request.method == "PUT" and r.status_code == 200 and "/order/" in key:
            self.objects[key] = _flip(self.objects[key])
        return r


def test_the_read_back_catches_bytes_the_bucket_changed(pages: dict[str, Any]) -> None:
    """NEGATIVE: every order object is stored with one bit flipped; each is reported, and every
    data object reads back clean."""
    bucket = _RottingBucket()
    with _client(bucket) as client:
        rep = upload_snapshot(pages, OBJECTS, client, workers=4)
    assert rep.written == 379
    assert len(rep.problems) == 26 and all("/order/" in p and "read back as" in p
                                           for p in rep.problems)
    assert rep.read_back == 353


def test_a_manifest_path_that_is_not_a_content_addressed_key_is_never_used(
        pages: dict[str, Any], tmp_path: Path) -> None:
    """NEGATIVE: a path that would leave the cache, or name anything but an object, refuses
    before any request or write. POSITIVE: every real committed path passes."""
    bucket = _uploaded(pages)
    remote = R2Objects(_client(bucket), tmp_path / "cache")
    entry = pages["files"][0]
    for bad in ("../../escape.parquet", f"edgar/../{entry['path']}", "/etc/passwd",
                entry["path"].replace(".parquet", ".json")):
        with pytest.raises(FactsStoreError, match="not a content-addressed object key"):
            remote.fetch({**entry, "path": bad})
    with pytest.raises(FactsStoreError, match="not a content-addressed object key"):
        manifest_objects({**pages, "files": [{**entry, "path": "../x.parquet"}]})
    assert bucket.requests == [] and not (tmp_path / "cache").exists()
    assert len(manifest_objects(pages)) == 379


def test_a_manifest_the_audit_cannot_read_is_counted_not_fatal(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round 1: a manifest `load_manifest` refuses (an older version kept in the tree) made the
    audit raise AFTER a finished upload. It is now counted, and the upload's verdict stands."""
    from vinci.facts import remote
    from vinci.facts.__main__ import main
    shutil.copytree(ROOT / "data" / "facts", tmp_path / "data" / "facts")
    (tmp_path / "data" / "facts" / "manifests" / "edgar-00000000000000v1.json").write_text(
        json.dumps({"manifest_version": 1, "snapshot_id": "edgar-00000000000000v1"}))
    monkeypatch.chdir(tmp_path)
    bucket = FakeBucket()
    monkeypatch.setattr(remote.R2Client, "from_env", classmethod(lambda cls: _client(bucket)))
    assert main(["upload", "--workers", "2"]) == 0
    out = capsys.readouterr().out
    assert "against the 2 committed manifests it reads" in out
    assert "1 manifest not read" in out


class _HtmlBucket(FakeBucket):
    def _list(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"<html><body>sign in to the network</body>")


def test_a_listing_that_is_not_xml_is_an_r2_error() -> None:
    """Round 1: a 200 that is not S3's XML (a proxy's page) raised ParseError from the parser."""
    with _client(_HtmlBucket()) as client, pytest.raises(R2RequestError,
                                                          match="ListObjectsV2: not S3's XML"):
        list(client.list_objects())



# --- round 2 (the coordinator's review of #913) ----------------------------------------------

def test_same_size_corruption_is_caught_at_every_hash(pages: dict[str, Any],
                                                     tmp_path: Path) -> None:
    """Item 1: each corruption here keeps the object's size, so only the sha256 can see it: the
    fetch, the 412 compare and the cached copy (the read-back: the rotting bucket above)."""
    entry = pages["files"][0]
    sealed = (OBJECTS / entry["path"]).read_bytes()
    flipped = _uploaded(pages)
    flipped.objects[entry["path"]] = _flip(sealed)
    with pytest.raises(FactsStoreError, match="are not the manifest's"):
        R2Objects(_client(flipped), tmp_path / "a").fetch(entry)
    assert not (tmp_path / "a" / entry["path"]).exists()
    with _client(flipped) as client, pytest.raises(RemoteBytesDifferError):
        client.put_new(entry["path"], sealed)
    assert flipped.objects[entry["path"]] == _flip(sealed)
    good = R2Objects(_client(_uploaded(pages)), tmp_path / "b")
    path, _ = good.fetch(entry)
    path.write_bytes(_flip(sealed))
    assert good.fetch(entry)[1] is True and path.read_bytes() == sealed


@pytest.mark.parametrize("scope", [
    {"rule": "test", "names_selected": 1, "excluded_by_operator_instruction": 0,
     "exclusions_listed": 0, "names_ingested": 1, "unread": []},       # as every ingest writes
    {"rule": "test"}])                                                 # no count at all
def test_a_snapshot_naming_no_exclusion_uploads_beside_the_committed_ones(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, scope: dict[str, Any],
        capsys: pytest.CaptureFixture[str]) -> None:
    """A snapshot that names no exclusion, uploaded while the two committed snapshots (each
    written excluding 1 of a list of 6) are current. On main both were REFUSED before any
    request: the guard held an upload to every current snapshot's list (0 < 6), and refused a
    snapshot stating no count. Now it uploads, and the bucket audit over every manifest in the
    tree still runs and passes."""
    from vinci.facts import remote
    from vinci.facts.__main__ import main
    facts = tmp_path / "data" / "facts"
    shutil.copytree(ROOT / "data" / "facts" / "manifests", facts / "manifests")
    shutil.copy(ROOT / "data" / "facts" / "current.json", facts / "current.json")
    got = rows_from_companyfacts(json.loads(
        (FIXTURES / "FUBO-companyfacts-slice.json").read_text()))
    files, order = write_entity(got.rows, facts / "objects")
    manifest = build_manifest(
        source=SOURCE, extractor=EXTRACTOR, extractor_version=EXTRACTOR_VERSION, scope=scope,
        entities=[{"entity": got.entity, "tickers": ["FUBO"], "rows_kept": len(got.rows)}],
        files=files, orders={got.entity: order})
    sid = manifest["snapshot_id"]
    (facts / "manifests" / f"{sid}.json").write_text(json.dumps(manifest, indent=2,
                                                                sort_keys=True) + "\n")
    monkeypatch.chdir(tmp_path)
    bucket = FakeBucket()
    monkeypatch.setattr(remote.R2Client, "from_env", classmethod(lambda cls: _client(bucket)))
    assert main(["upload", "--snapshot", sid, "--workers", "2"]) == 0
    assert {k: _sha(v) for k, v in bucket.objects.items()} == {
        e["path"]: e["sha256"] for e in manifest_objects(manifest)}
    assert "a manifest, 0 named by none;" in capsys.readouterr().out


def test_the_upload_fails_when_the_bucket_holds_what_no_manifest_names(
        monkeypatch: pytest.MonkeyPatch, pages: dict[str, Any],
        capsys: pytest.CaptureFixture[str]) -> None:
    """Item 4: the audit is the evidence that nothing but the manifests' objects is in the bucket,
    so a key no manifest names, or a named key of another size, fails the run."""
    from vinci.facts import remote
    from vinci.facts.__main__ import main
    argv = ["upload", "--workers", "2"]
    for extra in ({"edgar/stray/2020/" + "0" * 64 + ".parquet": b"x"},
                  {load_manifest(name="screen")["files"][0]["path"]: b"x"}):
        bucket = FakeBucket()
        bucket.objects.update(extra)
        monkeypatch.setattr(remote.R2Client, "from_env",
                            classmethod(lambda cls, b=bucket: _client(b)))
        assert main(argv) == 1
        assert "FAIL: the bucket holds" in capsys.readouterr().out


def test_bytes_changed_after_the_local_verify_are_not_uploaded(
        monkeypatch: pytest.MonkeyPatch, pages: dict[str, Any], tmp_path: Path) -> None:
    """Item 5: the re-hash inside each PUT, for a file that changed after the pre-verify."""
    from vinci.facts import remote
    local = tmp_path / "objects"
    shutil.copytree(OBJECTS, local)
    target = local / pages["files"][3]["path"]
    target.write_bytes(_flip(target.read_bytes()))
    monkeypatch.setattr(remote, "verify_manifest", lambda *a, **k: [])
    bucket = FakeBucket()
    with _client(bucket) as client:
        rep = upload_snapshot(pages, local, client, workers=2)
    assert rep.written == 378 and len(rep.problems) == 1
    assert "changed on disk since it was verified" in rep.problems[0]
    assert pages["files"][3]["path"] not in bucket.objects


def test_a_transient_status_is_retried_and_a_lasting_one_reported() -> None:
    """Item 5: 503 is retried with backoff; three in a row are reported with S3's code."""
    bucket = FakeBucket()
    bucket.objects["k/2020/x.parquet"] = b"abc"
    answers = [503, 503]

    def flaky(request: httpx.Request) -> httpx.Response:
        if answers:
            return _err(answers.pop(), "ServiceUnavailable")
        return bucket(request)

    waits: list[float] = []
    client = R2Client(CONFIG, transport=httpx.MockTransport(flaky), retries=2,
                      sleep=waits.append)
    assert client.get("k/2020/x.parquet") == b"abc" and waits == [0.5, 1.0]
    answers.extend([503, 503, 503])
    with pytest.raises(R2RequestError, match="HTTP 503 ServiceUnavailable after 3 attempts"):
        client.get("k/2020/x.parquet")


class _EndlessBucket(FakeBucket):
    def _list(self, request: httpx.Request) -> httpx.Response:
        ns = "http://s3.amazonaws.com/doc/2006-03-01/"
        return httpx.Response(200, content=(f'<ListBucketResult xmlns="{ns}"><IsTruncated>true'
                                            "</IsTruncated></ListBucketResult>").encode())


def test_a_truncated_listing_without_a_token_is_an_error() -> None:
    """Item 5: never loop forever on page one, never stop short and call it the whole bucket."""
    with _client(_EndlessBucket()) as client, pytest.raises(
            R2RequestError, match="truncated with no continuation token"):
        list(client.list_objects())


def test_the_account_id_and_a_placeholder_are_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """Item 5: an account id that is not one never reaches a host name. Item 9: a value copied
    from .env.example unedited is refused by its NAME, as config.sec_user_agent refuses its own."""
    env = dict(zip(("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"),
                   CONFIG.secrets(), strict=True))
    assert R2Config.from_env(env) == CONFIG
    with pytest.raises(R2NotConfiguredError, match="R2_ACCOUNT_ID is not an account id"):
        R2Config.from_env({**env, "R2_ACCOUNT_ID": "evil.example/x"})
    example = (ROOT / ".env.example").read_text()
    copied = {n: line.split("=", 1)[1] for line in example.splitlines()
              for n in env if line.startswith(f"{n}=")}
    assert set(copied) == set(env)
    with pytest.raises(R2NotConfiguredError) as got:
        R2Config.from_env(copied)
    assert "still .env.example's placeholder" in str(got.value)
    for n in env:
        assert n in str(got.value) and copied[n] not in str(got.value)


def test_a_cache_write_that_fails_is_counted_and_leaves_nothing(
        monkeypatch: pytest.MonkeyPatch, pages: dict[str, Any], tmp_path: Path) -> None:
    """Items 5 and 6: the write goes to a temporary file renamed into place, so a failure leaves
    no object at its name and no temporary file; and fetch_all counts it rather than dying."""
    def full(*a: Any, **k: Any) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("vinci.facts.remote.os.replace", full)
    cache = tmp_path / "cache"
    rep = R2Objects(_client(_uploaded(pages)), cache).fetch_all(manifest_objects(pages)[:3],
                                                                workers=1)
    assert (rep.fetched, len(rep.problems)) == (0, 3)
    assert all("could not be written to the cache (OSError)" in p for p in rep.problems)
    assert [p for p in cache.rglob("*") if p.is_file()] == []


def test_an_http_error_that_is_not_a_transport_error_is_an_r2_error() -> None:
    """Item 6: any httpx error, not only a transport one, is retried and reported by type only."""
    def broken(request: httpx.Request) -> httpx.Response:
        raise httpx.DecodingError(f"bad body from {request.url}")

    client = R2Client(CONFIG, transport=httpx.MockTransport(broken), retries=1,
                      sleep=lambda s: None)
    with client, pytest.raises(R2RequestError, match="DecodingError after 2 attempts") as got:
        client.get("k/2020/x.parquet")
    assert ACCOUNT not in str(got.value)
