# Covenant selector fixtures (STATE row 63)

Frozen copies of committed page data for `tests/test_covenant_selector.py`. A pin that asserts a
VALUE reads it from here, never from the living `data/dossiers/` page, which a paid build rewrites
(CLAUDE.md, TEST-LAYER RULE).

- `WLK.json`: WLK's `mechanical.capital_structure`, unmodified, from `data/dossiers/WLK/dossier.json`
  at main `71f9d9bb` (2026-11-17). Its term rows include the GO Zone bond loan agreement's
  (`0001193125-10-276447 · dex101.htm`) principal of $89,000,000, model-extracted at WLK's last paid
  build. The tests host it in WLK's committed page to render, and add ONE derived row: that
  principal row re-cited to the IKE Zone agreement beside it (`dex102.htm`), quoting that
  exhibit's own clause ($65,000,000) read from the EDGAR cache.
- `EPAM.json`: EPAM's `covenant_pointer_rows`, unmodified, from the same commit. Its 2026 10-K row
  (`0001352010-26-000015`) lists six page images (`.jpg`) beside the exhibit it targets.

Public SEC filings and the page's own extracted values. No workbook, no transcript text.
