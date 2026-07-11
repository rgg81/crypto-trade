# MN3 REVEAL LEDGER — append-only; single-use FAMILY tokens (PLAN §5.1/§6.1)

One holdout reveal per family, EVER. Every sanctioned holdout access appends a
`SPENT token=...` line below; `mn3_split.mn3_guard` reads this file and
hard-refuses any token already recorded. An `MN3-ENSEMBLE` spend atomically
records the ensemble token plus every member family's token. NEVER edit or
delete existing lines — this file is the audit record.

## Spends
- SPENT token=MN3-G at=2026-07-11T19:35:24Z window=[2020-01-01T00:00:00Z,2026-07-01T00:00:00Z) note=family-reveal
