# Team-07 Quantitative Engineering Report

## Disposition

Implemented the unchanged organizer nominee `T07-SRMB-118`, Slow Residual Momentum with Breadth
Brake. This candidate is **not QR-accepted**: its QR full-IS fill fraction was `0.669`, below the
predeclared `0.90` falsifier. The tournament's performance anti-veto rule permits the organizer to
advance the mechanically valid candidate despite that research failure. QE made no rescue,
parameter change, alternate selection, or public-OOS request.

The implementation reproduces `W=189`, `F=63`, `S=21`, OLS with intercept, residual-RMS
standardization, six names per sleeve, `+/-0.05` weights, gross `0.60`, breadth bounds
`[0.20,0.80]`, and outside multiplier `0`. It explicitly rebalances only Monday 00:00 UTC and
holds at every other boundary. BTC is factor-only. Funding is not an alpha input; the central
evaluator owns actual funding, fills, costs, participation, exposure controls, and PnL.

## Environment and bindings

- Host: Linux `6.18.33.2-microsoft-standard-WSL2`, x86-64.
- Python: `3.13.12`; NumPy `2.2.6`; pandas `3.0.0`; pytest `9.0.2`; Ruff `0.15.1`.
- Engineering checkout while this report was produced: `458acb9bbe4eb2f8a93a257304141ea7c0519fbd`.
- Strategy seed: `20260713`; QR search seed retained for provenance: `2026071307`.
- Canonical data-manifest SHA-256: `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`.
- Common config SHA-256: `030a065f75f9c4adb7484065908f4379435929609d446be0de0a831d9e28ee0a`.
- Evaluator source SHA-256 (`engine.py`): `44c1fb93f2d434c845cfea367a3a9760997d947ecdf8b3be25c86a9112d40835`.
- Final handoff bindings: common freeze
  `48df09341f02eba7a3469abd1ccda6649a4ef0ba`, Phase-0 record
  `012727865acecad6ea0c3327745359820b8e45c6`. The organizer completed this administrative
  rebinding before registration and before any public-OOS access.

The canonical snapshot was not opened by QE. All engineering tests use generated, local data with
decision boundaries inside the research interval. No timestamp at or after the public-OOS boundary
was read, and no full evaluator/OOS run was requested.

## Frozen engineering artifacts

| Artifact | SHA-256 |
|---|---|
| `strategy.py` | `d1161852adc9fbf525686705f30b9353eddaf072edf490a7a3270450751eeb73` |
| `frozen_config.json` | `09fd205786ba51935ef6585d579f6ad8f52c1cc2bd19bab0f0efacd4b6964849` |
| `test_team_07_strategy.py` | `6dbc1e7976a0e22b182e168d516c2ff233af3a6f6068bade51b4e3852e6dbd75` |
| `compliance.json` | `9f15ae9d9c4ad1bd4ffd65af07c293b7c1f63682dc214d9c156f02e7b6c6990d` |
| team `uv.lock` | `869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5` |

The team lock is byte-identical to the root lock. The organizer's final source-bundle fingerprint
must be derived after this report and the Phase-0 path/reference rebinding; recording an earlier
bundle digest here would be stale by construction.

## Verification

Commands:

```bash
.venv/bin/ruff check \
  tournament/top40/teams/team-07/strategy.py \
  tournament/top40/teams/team-07/test_team_07_strategy.py
.venv/bin/pytest -q tournament/top40/teams/team-07/test_team_07_strategy.py
PYTHONPATH=src .venv/bin/python -c \
  "from crypto_trade.tournament.runner import source_bundle_fingerprint; print(source_bundle_fingerprint('.', 'team-07', 'tournament/top40/teams/team-07/strategy.py')[0])"
cmp -s uv.lock tournament/top40/teams/team-07/uv.lock
```

Results:

- Ruff: all checks passed.
- Pytest: `10 passed in 2.39s`; measured command wall time `2.82s`.
- Team-tree/source scanner: passed after generated Python caches were removed.
- Dependency lock comparison: byte-identical.
- Clean-process reproducibility: two independent Python processes produced identical target,
  position, return, and synthetic manifest SHA-256 values. Required discrepancy tolerance is zero
  bytes for these hashes.

The tests cover the exact QR formula and tie ordering; explicit Monday rebalance versus hold;
truncation, corrupt-future, and append invariance; input immutability; strict adjacent-bar gaps;
missing/zero/negative/NaN/Inf closes; missing or degenerate BTC; residual-RMS degeneracy; seed and
duplicate-membership faults; completed-history PIT membership; ineligible targets; next-open
execution; actual funding sign and boundary order; entry/rebalance/exit fees and slippage; a fresh
2x-cost run; independent long/short price and funding reconciliation; realized two-sided exposure
and buy/sell notional on synthetic data; participation limits; costed risk reduction; costed forced
delisting and adverse unfilled residual settlement; non-finite target rejection; duplicate rows;
missing marks; risk caps; empty output; and clean-process hashes.

## Reproduction and report destinations

Engineering reproduction is the pytest command above. The stable post-freeze canonical reproduce
command is:

```bash
uv run python scripts/top40_tournament.py validate \
  tournament/top40/teams/team-07/submission.json
```

Canonical base and stress outputs are intentionally absent until organizer execution. Their fixed
destinations are `reports-top40/team-07/bar_returns.csv`,
`reports-top40/team-07/double_cost_bar_returns.csv`,
`reports-top40/team-07/daily_returns.csv`, and
`reports-top40/team-07/double_cost_daily_returns.csv`.

## Known limitations and required organizer actions

- The QR's `0.90` full-IS fill falsifier failed (`0.669`). This remains a prominent research-risk
  warning, never a QR acceptance and never a performance DQ.
- No canonical full-snapshot result, public-OOS metric, window-wide sleeve-floor result, or report
  artifact was generated by QE. Synthetic tests prove mechanics, not tournament performance.
- The candidate requires BTC plus at least twelve scorable non-BTC PIT members. A required gap,
  invalid close, degenerate regression, absent BTC, or failed breadth gate makes Monday explicitly
  flat; other boundaries hold.
- Continuous historical quantities inherit the common limitation that Binance does not publish a
  complete point-in-time archive of quantity steps and minimum-notional filters.
- The organizer must rebind the temporary common/Phase-0 references, rerun Ruff/pytest/source
  scanning, recompute the changed strategy/config/test/compliance hashes if any file is patched,
  build and commit the team source manifest, and perform the QR/QE review and canonical runs.
