---
id:
status: shipped
date: 2026-11-13
prs: [1059]
supersedes:
superseded-by:
---

# The impact check sees a synthesis request that differs only in key order: the child writes `request.json` in the captured order, never key-sorted, and a key-order-only difference is named

**WHAT.**
- **`vinci.impact`'s child** (`child.write_request`) writes each page side's `request.json` in the
  captured key order. Reads, clock and timing stay key-sorted (`_side_file`).
- **`run.request_diff`** names `key_order_only` when the two sides' values are all equal and only
  some keys' order differs, and `order_moved`: each argument whose order moved, and the arguments'
  own order.
- **A run folder names the check's own code.** `run.json` records the sha256 of the impact child and
  of the capture child, so `--resume` of a folder written by other check code (before this change,
  key-sorted requests) is refused as "one run, one folder".
- **The report's section 3** says the comparison is byte for byte "key order included", and names
  a KEY ORDER ONLY page and where its order moved.

**WHY.** Found preparing #953's retrospective panel check, 2026-11-13. The child wrote
`request.json` with `json.dumps(…, sort_keys=True)`, so `request_diff`'s byte comparison
(`replay.wire`) compared two alphabetised copies. That had two effects:
- A change that only reorders the tool schema's fields, or the top-level arguments, read
  "identical". That is the class PR 2 drew: production's tool schema sent alphabetised in all 70
  draws, which `capture_child.jsonable` was written to prevent.
- A run's `request.json` was not the request production sends. #953's export, and E2's for #1027,
  had to re-capture each arm to get the captured order.

**HOW VERIFIED.**
- **Pins** (`tests/test_impact_request_key_order.py`), on production's own offline capture
  (`capture_child.capture_calls`) of the frozen page `tests/fixtures/frozen_pages/2026-09-28/TECX`:
  - **The blind spot, as a pin:** the tool schema's fields alphabetised, and `tools` moved before
    `system`, read identical when written the old way. This passes at both refs.
  - **The fix:** written as captured, both read as differing and `key_order_only`. A changed value
    is never `key_order_only`, the same request is identical, the rendered section names the
    reordered page and not the changed one, and the file reads back `wire`-equal to the capture.
  - **Fail first** (`vinci.impact run`, part 1): 6 of 8 nodes fail on base's `vinci/` (at the
    missing `child.write_request`) and pass on head; 2 pass at both (the blind-spot pins).
  - **Review round 1** (the coordinator's independent review of `03ec2237`), four more nodes:
    - **The call site:** `child.page` itself runs on the frozen TECX page, with only the build and
      the CIQ reads stubbed. Its `request.json` keeps the captured order, and a planted reorder on
      one side reaches `compare_page` as KEY ORDER ONLY. With the old line put back at the call site
      (the reviewer's mutant M4), it fails; every earlier pin called `write_request` directly and
      stayed green under M4.
    - **`--resume`:** a folder whose `run.json` predates this change is refused; one written by
      the same check code continues. Both failed on `03ec2237`.
    - **`order_moved`:** a reorder inside `messages` names `messages`; the alphabetised schema names
      `tools`; the swapped arguments name the arguments' own order; the report row names it. This
      failed on `03ec2237`.
- **A real pair, nothing else changes:** #953's six panel pages (base `586fdcfd`, head `7ec84833`,
  the sweep's pinned store and CIQ root) run with this tool, against the same run made before it
  that morning.
  - Identical-or-not, sections (`facts` on 5; LLY identical), USER diff lines and page field moves
    are unchanged on all six. `key_order_only` is false on the 5 that differ.
  - Each side's request sha256 now equals the #953 export's captured-order `request_wire_sha256`:
    12 of 12, against 0 of 12 before.
- **The gate** (`bin/commit`) was green. `vinci.impact run` on this branch builds no page: no
  changed path reaches the page builder, and no consumer is reached.

**BOUNDARY.**
- **"8 nodes"** are the new file's 8 test nodes at its first commit, `eea52b24` (one test is
  parametrised over the 2 planted reorders). Review round 1 adds 4, so there are 12 in all.
- **"12 of 12"** counts the 6 pages × 2 arms of #953's panel run: this tool's run stamped
  2026-11-13T10:32:03Z, the export `manifest.json` `0fb65dad…`, and the morning run 09:58:21Z.
- **Main:** `01ab6923`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A report from before this change** carries key-sorted request hashes. Exports from older
  runs must re-capture each arm, as #953's and E2's did.
- **`--resume` of a run folder written by other check code is refused** (review round 1). A run
  folder from before this change cannot be continued; start a fresh one. The build cache keys on
  the child's sha256, as before.
- **A reorder of the top-level arguments alone** is reported, although the SDK builds its own
  top-level order and may send both sides alike. `replay.wire` fails safe there, and the report says
  so.
