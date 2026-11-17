# Frozen underwrite cards

A render pin that passes a page WITH its underwrite record reads that record's card:
`frontend/scenarios/<key>.json`, the mirror `frontend/build.py` emits from `scenarios/<key>.json`
(or from `scenarios/archive/<key>.json` for an archived record). The card is a living artifact, as
the page is: a verdict recorded, a record reissued or a name retired moves it under the pin. A pin
whose claim depends on the card's STATE (an undecided record, say) reads a frozen card, so the
claim cannot fall out from under it when the record moves.

A `cut-<sha8>/` folder holds cards exactly as committed at main `<sha8>`: the same git blobs, so
0 new objects. `tests/test_frozen_cards_are_cuts.py` holds every file here to
`git show <sha>:frontend/scenarios/<file>`, and this table to the files. A card is never
regenerated or edited. A pin re-pinned to a newer card reads a NEW cut; the old copy stays.

A card is paired with a frozen PAGE (`tests/fixtures/frozen_pages/`) of the same name, never a
living one, so a pin never renders a frozen card beside a page that keeps moving.

| copy | source | commit | blob | what is pinned on it |
|---|---|---|---|---|
| `cut-4889ddba/EPAM-2026-07-21.json` | `frontend/scenarios/EPAM-2026-07-21.json` | `4889ddba632f34b0479fdb4e6e6e1b32c095cb10` | `eae3502c505a04e7d339f5d7812e85fedda7aee3` | an UNDECIDED record: EPAM's 2026-07-21 R1 record, `pending_analyst` with no rationale and no void, superseded on the 2026-08-07 reconciliation (#402) before any verdict was recorded on it. Two committed records are still `pending_analyst` at this commit, both archived. The other, GOOGL's 2026-08-17, carries a `voided` block (the 2026-11-11 void of GOOGL's BUY), a second state a pending exemplar must not bring with it. EPAM is also the name the opener pin was written against, hardcoded until #407 decided EPAM's live record. Paired with EPAM's page in `frozen_pages/cut-4889ddba/`, cut at the same commit: a pending name renders the machine Assessment once and no thesis block (`test_dossier`'s `test_opener_narrative_slot_rationale_once_and_conditional_warning_node`) |
| `cut-f2c6e7aa/SMPL.json` | `frontend/scenarios/SMPL.json` | `f2c6e7aa763bf3b5cb32da7759551d502c212aef` | `6ed6d2be0af8dfaca405c7d340f99cf245ad2e9d` | SMPL's card as committed beside its page at `f2c6e7aa`, the commit `frozen_pages/2026-08-18/SMPL/` was frozen from (that page copy was rewritten twice since: its store stamp at `eac82b7f` and its transcript words at `91817458`): the card the shared-8-K render pin passes beside the page whose 2026-04-09 and 2026-04-10 gap-downs share one 8-K (`test_dossier`'s `test_one_8k_explaining_two_gap_downs_renders_once_e2e`) |
