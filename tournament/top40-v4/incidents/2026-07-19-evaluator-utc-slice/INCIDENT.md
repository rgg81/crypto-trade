# Top-40 V4 activation incident — 2026-07-19

Status: activation abandoned before any successful IS observation

The first V4 activation at implementation commit
`b283c1c45c4353dcbff56e2949b92873a3c0592d` passed its 25 focused tests and bound activation
record `75f7ee5b20cb6426c97adc0973fbb3b7cac487e9bcce2908f046c9a99bf82342`.

Team 01 trial 1 was durably accepted and opened the authorized IS data. After target generation
and evaluation, Pandas 3 rejected a metric slice whose start was UTC-aware while its inclusive end
was date-only. The terminal journal record is an infrastructure failure:

`ValueError: Both dates must have the same UTC offset`

A minimal synthetic call to `runner_v4._compute_metrics` reproduced the same exception without
team code or market data. No candidate produced an IS summary, no team advanced, and historical
OOS was never opened. V4 receives no further result-bearing commands. A clean R1 tournament fixes
the UTC normalization prospectively, adds a regression that exercises the metric path, and starts
with a new activation and empty journal. It inherits no trial or performance evidence.

Preserved evidence:

- `activation-freeze.json`: 11,964 bytes, SHA-256
  `8058b098ed01679ed286188c9aab8f7332abed5833deacb74abca2956538ffe3`
- `activation-tests.out`: 99 bytes, SHA-256
  `53ae54068f4726a32be641a180dc29a907314e388e63e0b8105712110af50f63`
- `research-journal.jsonl`: 3,415 bytes, SHA-256
  `b2f2bdefe0b1933cefe772dccdcdfa201f407cf166b406d5c6b7188cfcf63718`
- final journal head:
  `ed6466e01f41b965720878bbbd5497f7ebd36b8d143cba1bd8f217f07b9059c3`

This archive is append-only incident evidence. The failed trial remains recorded exactly as it
occurred; it is not reclassified or deleted.
