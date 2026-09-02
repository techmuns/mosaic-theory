# Draft thesis cards — NOT declared

A card here is **not declared** and nothing loads it. `load_all_theses` reads only
`data/themes/thesis/`; a file in this directory is a working draft held for the operator, kept in
the repo rather than a scratch path so the STATE.md row that cites it still resolves next week.

Declaring is the operator's act: `vinci theme-thesis declare <driver> --file <card.json>`. When a
draft is declared, the declared copy lands under `data/themes/thesis/` and the draft here is deleted
— the record of what changed between draft and declaration lives in `docs/records/`, not here.
