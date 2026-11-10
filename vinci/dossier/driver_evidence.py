"""(RG-D19, PR 2) The PRIVATE evidence behind a transcript driver row.

This is the row's quote and the paragraph after it. It is kept out of
git, because this repo is public and the public page carries the fact and its locator, never the
licensed words (`docs/records/2026-11-10-driver-facts-not-quotes.md`).

THE WRITER IS THE OPERATOR'S RULING (2026-11-10, option 1):
- The assembling machine writes each record into a SPOOL folder on the shared Drive, beside
  `manual/ciq`.
- The ingest machine, the one holding the read/write R2 token, uploads the spool to the private R2
  bucket (`upload_spool`). That keeps the fact store's rule: one writer, read-only readers.

THE SPOOL IS THE OPERATOR'S FOLDER, AND THIS CODE NEVER CREATES IT. It is named by
``$VINCI_EVIDENCE_SPOOL``. A folder that does not exist fails loud and names the variable: the
operator creates it by hand, and this code only writes FILES inside it, flat, never a sub-folder.

Two places are refused outright:
- a spool inside this repository, whose files would be committed;
- a spool under a `manual/ciq` folder, the licensed exports, which nothing here writes to, moves
  or deletes.

ONE RECORD PER PASSAGE, IMMUTABLE AND CONTENT-ADDRESSED. A record is the quote and the
paragraph after it, and nothing that varies by row or by build:
- **The model's stated value is NOT evidence.** It is a claim the fact check read against the
  quote, and its words are the quote's own. One quote backs several rows: on the 28 committed
  pages, 881 transcript rows give 810 (call, quote) keys. Of the 63 keys shared by more than one
  row, all hold the same quote and context, and 62 differ only in the stated value.
- **Nor is the extraction version,** so a rebuild meets its own record and writes nothing.
- **Nor is the ticker.** A call file is the passage's identity, and two listings citing one file
  (a second share class) would otherwise collide on it.
- **The key** is `driver-evidence/v1/<transcript_sha256>/<paragraph>/<quote_sha256>.json`. A
  call-only locator (the call was not on hand to count in) keys under
  `driver-evidence/v1/unlocated/<sha256 of the call's file name>/`.
- **The bytes** are canonical JSON. The same record twice is a no-op; different bytes under one
  key are refused in the spool and in the bucket (`R2Client.put_new`, ``If-None-Match: *``).
- **Every read and every upload re-checks** that the quote hashes to its locator's
  ``quote_sha256``, so a record cannot claim a passage it does not hold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

from vinci.dossier.driver_extract import quote_key
from vinci.dossier.schemas import Dossier, OperatingDriver, TranscriptLocator

if TYPE_CHECKING:
    from vinci.facts.remote import R2Client

SPOOL_ENV = "VINCI_EVIDENCE_SPOOL"
PREFIX = "driver-evidence/v1"
_HEX = r"[0-9a-f]{64}"
KEY = re.compile(rf"^{PREFIX}/(?:{_HEX}/\d+|unlocated/{_HEX}|claims/{_HEX})/{_HEX}\.json$")
#: The spool is FLAT, so the code never makes a folder: a key's "/" is "__" in its file name.
_SEP = "__"
_REPO = Path(__file__).resolve().parents[2]


class EvidenceError(RuntimeError):
    """The private evidence could not be written, read or uploaded as asked."""


class SpoolNotConfiguredError(EvidenceError):
    """``$VINCI_EVIDENCE_SPOOL`` is not set."""


class SpoolMissingError(EvidenceError):
    """The configured spool folder does not exist. This code never creates it."""


class SpoolRefusedError(EvidenceError):
    """The configured spool is a place evidence is never written: in the repo, or under
    `manual/ciq`."""


class EvidenceBytesDifferError(EvidenceError):
    """A key already holds a different record: evidence is never overwritten."""


class EvidenceIntegrityError(EvidenceError):
    """A record's quote does not hash to its locator, or its file name is not its key."""


class EvidenceRecord(BaseModel):
    """One quoted passage of a transcript: what a driver row's locator points at."""

    schema_version: int = 1
    locator: TranscriptLocator
    verbatim: str
    following_context: str | None = None

    model_config = {"frozen": True}


class ClaimRecord(BaseModel):
    """(RG-D19 PR 3) One row's CLAIM: the model's stated value, read off a passage. Kept beside the
    passage, not in it, because one passage backs several rows — on the 28 committed pages, 63
    passages back more than one row, and in 62 of them the stated values differ. The public row
    names it by ``locator.quote_sha256`` and ``locator.value_sha256``, never by its words."""

    schema_version: int = 1
    quote_sha256: str
    value_sha256: str
    stated_value: str

    model_config = {"frozen": True}


Record = EvidenceRecord | ClaimRecord


def value_key(value: str) -> str:
    """sha256 of a stated value's exact bytes: the claim's half of its key."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def claim_key(quote_sha256: str, value_sha256: str) -> str:
    return f"{PREFIX}/claims/{quote_sha256}/{value_sha256}.json"


def key_of(rec: Record) -> str:
    """A record's key, from what it holds."""
    if isinstance(rec, ClaimRecord):
        return claim_key(rec.quote_sha256, rec.value_sha256)
    return evidence_key(rec.locator)


def evidence_key(loc: TranscriptLocator) -> str:
    """The record's key: by file, paragraph and quote when the call was counted in; by the call's
    name and the quote when it was not."""
    if loc.transcript_sha256 is not None and loc.paragraph is not None:
        return f"{PREFIX}/{loc.transcript_sha256}/{loc.paragraph}/{loc.quote_sha256}.json"
    call = hashlib.sha256(loc.call.encode("utf-8")).hexdigest()
    return f"{PREFIX}/unlocated/{call}/{loc.quote_sha256}.json"


def record_bytes(rec: Record) -> bytes:
    """The record's one serialisation: sorted keys, no spacing, a final newline."""
    body = json.dumps(rec.model_dump(mode="json"), sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))
    return (body + "\n").encode("utf-8")


def verify(rec: Record) -> Record:
    """``rec`` when its words hash to its key, else raise: a passage's quote to its locator's
    ``quote_sha256``, a claim's stated value to its ``value_sha256``."""
    if isinstance(rec, ClaimRecord):
        if value_key(rec.stated_value) != rec.value_sha256:
            raise EvidenceIntegrityError(
                f"the stated value in {key_of(rec)} does not hash to its value_sha256")
        return rec
    if quote_key(rec.verbatim) != rec.locator.quote_sha256:
        raise EvidenceIntegrityError(
            f"the quote in {evidence_key(rec.locator)} does not hash to its "
            "locator's quote_sha256")
    return rec


def _parse(data: bytes, key: str) -> Record:
    kind: type[EvidenceRecord] | type[ClaimRecord] = (
        ClaimRecord if key.startswith(f"{PREFIX}/claims/") else EvidenceRecord)
    try:
        rec: Record = kind.model_validate_json(data)
    except ValueError as exc:
        raise EvidenceIntegrityError(f"{key}: not an evidence record ({exc})") from exc
    verify(rec)
    if key_of(rec) != key:
        raise EvidenceIntegrityError(f"{key}: the record's locator keys it elsewhere")
    if record_bytes(rec) != data:
        raise EvidenceIntegrityError(f"{key}: not in the record's one serialisation")
    return rec


def record_for(row: OperatingDriver) -> EvidenceRecord | None:
    """The evidence of one row. None for a row this store does not hold: an anchored row (its text
    is a filing's or CIQ's, not a transcript's), or a transcript row with no locator or no quote."""
    if row.tier != "llm-fenced" or row.locator is None or not row.verbatim:
        return None
    return EvidenceRecord(locator=row.locator, verbatim=row.verbatim,
                          following_context=row.following_context)


def records_for(dossier: Dossier) -> tuple[list[EvidenceRecord], int]:
    """Every transcript row's evidence on a page, and how many transcript rows had none to give
    (no locator, or no quote)."""
    od = dossier.mechanical.operating_drivers
    out: list[EvidenceRecord] = []
    missed = 0
    for r in od.rows if od is not None else []:
        if r.tier != "llm-fenced":
            continue
        rec = record_for(r)
        if rec is not None:
            verify(rec)
        if rec is None:
            missed += 1
        else:
            out.append(rec)
    return out, missed


def _checkouts(repo: Path) -> list[Path]:
    """Every working tree of this repository: ``repo`` and, through its git common dir, the main
    checkout and each linked worktree. Agents build in worktrees, so ``repo`` alone would let a
    spool sit in the main checkout (or a sibling worktree) unrefused."""
    dotgit = repo / ".git"
    common = dotgit
    if dotgit.is_file():   # a linked worktree: "gitdir: <common>/worktrees/<name>"
        line = dotgit.read_text(encoding="utf-8").strip()
        if not line.startswith("gitdir:"):
            return [repo]
        gitdir = Path(line.removeprefix("gitdir:").strip())
        common = (gitdir if gitdir.is_absolute() else repo / gitdir).resolve().parent.parent
    roots = [repo, common.parent]
    for entry in (common / "worktrees").glob("*/gitdir"):
        roots.append(Path(entry.read_text(encoding="utf-8").strip()).parent)
    return roots


def _within(path: Path, root: Path) -> bool:
    """``path`` is ``root`` or under it — by the file system's identity, so a case variant of the
    path on a case-insensitive volume is still inside."""
    for p in (path, *path.parents):
        try:
            if os.path.samefile(p, root):
                return True
        except OSError:
            continue
    return False


def _refusal(root: Path) -> str | None:
    """Why ``root`` is a place evidence is never written, or None."""
    real = root.resolve()
    if any(_within(real, r) for r in _checkouts(_REPO)):
        return "it is inside this repository, whose files are committed and public"
    parts = [p.lower() for p in real.parts]
    if any(a == "manual" and b == "ciq" for a, b in zip(parts, parts[1:], strict=False)):
        return ("it is under manual/ciq, the licensed exports, which nothing here writes to, "
                "moves or deletes")
    return None


class EvidenceSpool:
    """The operator's spool folder: written to, never created."""

    def __init__(self, root: Path) -> None:
        if not root.is_dir():
            raise SpoolMissingError(
                f"${SPOOL_ENV} names a folder that does not exist. This code never creates it: "
                "the operator creates it by hand, then the evidence is written inside it")
        if (why := _refusal(root)) is not None:
            raise SpoolRefusedError(f"${SPOOL_ENV} is refused: {why}")
        self.root = root

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> EvidenceSpool:
        spool = cls.configured(env)
        if spool is None:
            raise SpoolNotConfiguredError(
                f"${SPOOL_ENV} is not set: name the evidence folder the operator created on the "
                "shared Drive")
        return spool

    @classmethod
    def configured(cls, env: Mapping[str, str] | None = None) -> EvidenceSpool | None:
        """The spool when ``$VINCI_EVIDENCE_SPOOL`` is set, else None. Set but wrong still
        raises: a spool named and unusable is an error, never a skip."""
        value = ((os.environ if env is None else env).get(SPOOL_ENV) or "").strip()
        return cls(Path(value).expanduser()) if value else None

    def path(self, key: str) -> Path:
        if not KEY.match(key):
            raise EvidenceIntegrityError(f"{key!r} is not an evidence key")
        return self.root / key.replace("/", _SEP)

    def put(self, rec: Record) -> bool:
        """Write ``rec``. True when written; False when the same bytes were already there.
        Different bytes under its key raise: a record is never overwritten."""
        verify(rec)
        key = key_of(rec)
        path, data = self.path(key), record_bytes(rec)
        if path.exists():
            if path.read_bytes() == data:
                return False
            raise EvidenceBytesDifferError(f"{key}: the spool holds another record under it")
        part = path.with_name(path.name + ".part")
        try:
            # exclusive: two writers never share a partial file
            fd = os.open(part, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as exc:   # never removed here: it may be another writer's
            raise EvidenceError(
                f"{key}: a partial write ({part.name}) is already in the spool — another build "
                "is writing this record, or one died mid-write; delete it once none is running"
            ) from exc
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            if path.exists():   # written meanwhile: it must be the same record
                if path.read_bytes() != data:
                    raise EvidenceBytesDifferError(f"{key}: written meanwhile with another record")
                return False
            os.replace(part, path)
        finally:
            part.unlink(missing_ok=True)
        return True

    def get(self, key: str) -> Record:
        return _parse(self.path(key).read_bytes(), key)

    def keys(self) -> tuple[list[str], list[str]]:
        """(the evidence keys the spool holds, the names of every other file in it). Another
        file is never read as evidence: a Drive conflict copy ("… 2.json"), a partial write or
        anything the operator keeps there."""
        held: list[str] = []
        other: list[str] = []
        for p in sorted(self.root.iterdir()):
            key = p.name.replace(_SEP, "/")
            if p.is_file() and KEY.match(key):
                held.append(key)
            else:
                other.append(p.name)
        return held, other


@dataclass
class SpoolReport:
    written: int = 0
    already: int = 0
    no_evidence: int = 0  # transcript rows with text but no locator: their words are dropped
    stripped: int = 0  # transcript rows already without text: spooled by an earlier write


def spool_dossier(dossier: Dossier, spool: EvidenceSpool) -> tuple[Dossier, SpoolReport]:
    """Write every transcript row's passage and claim on ``dossier`` into ``spool``, and return the
    page as it may now be written: each spooled row's locator carries its ``value_sha256``.

    THE ONE SERIALIZER THEN DROPS THE TEXT (`schemas.PRIVATE_TRANSCRIPT_FIELDS`), so this runs
    FIRST, every time a page with transcript text is written. A row with text but no locator (a
    quote said on two calls whose period named neither) has nowhere to be filed: it is counted, and
    its words survive only in the licensed call."""
    od = dossier.mechanical.operating_drivers
    rep = SpoolReport()
    if od is None:
        return dossier, rep
    rows: list[OperatingDriver] = []
    for r in od.rows:
        if r.tier != "llm-fenced":
            rows.append(r)
            continue
        if not r.verbatim:
            rep.stripped += 1
            rows.append(r)
            continue
        rec = record_for(r)
        if rec is None or r.locator is None:
            rep.no_evidence += 1
            rows.append(r)
            continue
        recs: list[Record] = [rec]
        loc = r.locator
        if r.value is not None:
            loc = loc.model_copy(update={"value_sha256": value_key(r.value)})
            recs.append(ClaimRecord(quote_sha256=loc.quote_sha256,
                                    value_sha256=value_key(r.value), stated_value=r.value))
        for x in recs:
            if spool.put(x):
                rep.written += 1
            else:
                rep.already += 1
        rows.append(r.model_copy(update={"locator": loc}))
    mech = dossier.mechanical.model_copy(update={
        "operating_drivers": od.model_copy(update={"rows": rows})})
    return dossier.model_copy(update={"mechanical": mech}), rep


def rehydrate(rows: Sequence[OperatingDriver], get: Callable[[str], Record]
              ) -> list[OperatingDriver]:
    """The rows with each stripped transcript row's quote, context and stated value read back
    from the private store through ``get`` (a spool's or a bucket client's read) — for a reader
    that needs the words, such as a replay of a committed page. A stripped row whose records
    are missing raises, from ``get``: the words are never guessed."""
    out = []
    for r in rows:
        if r.tier != "llm-fenced" or r.verbatim or r.locator is None:
            out.append(r)
            continue
        passage = get(evidence_key(r.locator))
        assert isinstance(passage, EvidenceRecord)
        update: dict[str, object] = {"verbatim": passage.verbatim,
                                     "following_context": passage.following_context}
        if r.locator.value_sha256 is not None:
            claim = get(claim_key(r.locator.quote_sha256, r.locator.value_sha256))
            assert isinstance(claim, ClaimRecord)
            update["value"] = claim.stated_value
        out.append(r.model_copy(update=update))
    return out


@dataclass
class UploadReport:
    written: list[str] = field(default_factory=list)
    already: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # spool files that are not evidence


def upload_spool(spool: EvidenceSpool, client: R2Client) -> UploadReport:
    """Upload every record in ``spool`` to the bucket ``client`` writes. Run on the ingest machine
    only, the one holding the read/write token.

    Each record is re-read and re-checked first (`_parse`: quote hash, key, serialisation), and
    read back from the bucket after its PUT (a key already held was read back and compared by
    `put_new` itself). A record is never deleted from the spool here: the operator keeps or
    clears the folder."""
    held, other = spool.keys()
    rep = UploadReport(skipped=other)
    for key in held:
        data = record_bytes(spool.get(key))
        if not client.put_new(key, data):
            rep.already.append(key)
            continue
        rep.written.append(key)
        if client.get(key) != data:
            raise EvidenceIntegrityError(f"{key}: the bucket returned other bytes after the PUT")
    return rep


def fetch(client: R2Client, key: str) -> Record:
    """One record from the bucket, checked like a spool read."""
    if not KEY.match(key):
        raise EvidenceIntegrityError(f"{key!r} is not an evidence key")
    return _parse(client.get(key), key)


def _shown(items: Sequence[str], k: int = 5) -> str:
    head = ", ".join(items[:k])
    return f"{head} (showing {min(k, len(items))} of {len(items)})" if items else "none"


def main(argv: Iterable[str] | None = None) -> int:
    """``python -m vinci.dossier.driver_evidence upload [--spool PATH]``: the ingest machine's
    upload. It prints counts and keys, never the bucket, the endpoint or a credential."""
    ap = argparse.ArgumentParser(prog="python -m vinci.dossier.driver_evidence")
    sub = ap.add_subparsers(dest="cmd", required=True)
    up = sub.add_parser("upload", help="upload the spool to the private R2 bucket")
    up.add_argument("--spool", type=Path, default=None,
                    help=f"the spool folder (default ${SPOOL_ENV})")
    a = ap.parse_args(list(argv) if argv is not None else None)
    from vinci.config import load_local_env
    from vinci.facts.remote import R2Client

    load_local_env()
    spool = EvidenceSpool(a.spool) if a.spool is not None else EvidenceSpool.from_env()
    with R2Client.from_env() as client:
        rep = upload_spool(spool, client)
    print(f"uploaded {len(rep.written)} record(s), {len(rep.already)} already in the bucket; "
          f"{len(rep.skipped)} other file(s) in the spool left alone: {_shown(rep.skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

