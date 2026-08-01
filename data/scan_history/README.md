Immutable archive behind data/snapshots/candidate_themes.jsonl.

TRACKED ON PURPOSE. While this directory was git-ignored, the 'a monthly sweep must never
clobber the prior harvest' guarantee in cli.py protected nothing: the pointer was the only
committed copy and it was overwritten BEFORE the snapshot was written. Detection now refuses
to overwrite the pointer without archiving, and the archive is kept here.
