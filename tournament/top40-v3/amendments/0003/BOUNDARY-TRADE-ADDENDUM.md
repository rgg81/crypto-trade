# Amendment 0003 end-boundary trade-count addendum

Status: prospective until the unique boundary-trade freeze commit is verified.

The scored-stage addendum failed closed during trade reconciliation. The canonical validation
artifact includes forced-settlement trade rows exactly at `2023-07-01T00:00:00Z`, the public
window's end-exclusive timestamp. These rows are legitimate evaluator evidence but are not inside
the scored validation interval. Amendment 0002 already used the correct half-open interval and
excluded them from its released trade count.

This addendum applies the same fixed rule to stitched reconciliation: IS trades are counted in
`[2020-02-03, 2022-07-01)`, validation trades in `[2022-07-01, 2023-07-01)`, and settlement rows
exactly at `2023-07-01` are verified but excluded. Any row before the public start or after that
exact terminal boundary fails closed.

No returns, model, split, cost, metric, threshold, or released packet changes. The adapter is
committed and freeze-bound before the corrected aggregate assessment is attempted.
