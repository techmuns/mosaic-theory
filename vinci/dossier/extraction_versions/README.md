# `extraction_versions/` — one file per extraction vintage

A PR that changes what a dossier carries declares a new vintage here, as ONE new file. It edits no
line another PR edits, so two such PRs merge in either order with no conflict.

```
python -m vinci.dossier.extraction_version new <slug> --names "<what this vintage names>"
python -m tests.test_extraction_version_drift --repin --entry <the id it printed>
```

The first writes `<YYYY-MM-DD>.<slug>.json`:

```json
{
  "id": "2026-11-12.example-slug",
  "follows": ["2026-11-11.guides-as-stated"],
  "names": "what changed in the output, for a reader of the page"
}
```

The second re-pins only the watched modules this PR moved, naming the new id. The web reads this
folder through `frontend/build.py`, which writes `frontend/snapshots/extraction_versions.json` on
every deploy (git-ignored), so nothing in `frontend/` is edited by hand.

## The rules

- **`id`** is the day the entry is written and a lowercase kebab slug holding a letter. A counter
  slug (`.1`, `.2`) is refused, because two PRs pick the same next number. Two PRs that pick the
  same id write the same file, and git refuses to merge them.
- **`follows`** names the vintage(s) current on the main the PR was cut from, which is what
  `new` fills in. Leave it as written when the PR later merges main. A vintage includes every
  vintage it follows, transitively.
- **Current is the HEADS**, the vintages nothing follows, and never the last line or the latest
  date. One head is the stamp. Two or more heads appear when PRs are cut from the same main and
  merged without either following the other. They stamp as their ids joined by `+` in id order,
  and that stamp is declared. The next entry follows every head, and the join closes.
- **An entry is never edited or deleted once merged**: a committed page may carry its id. The rows
  of `LEGACY_VERSIONS` in `../extraction_version.py` are frozen under the same rule, and no row is
  added there again.
- `note` is optional text for a reader of the file. Nothing renders it.

Moving a row from an open PR: take main's `extraction_version.py` and `dossier.js`, write your row
as a file with `new` (or by hand, keeping its id and names byte for byte), and re-pin as above. A
counter id (`2026-11-10.2`) is refused as a file id: give it a slug instead. No committed page
carries it, because the row never merged — but re-stamp any page the PR itself built with it.
