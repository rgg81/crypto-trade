# Team-02 QE report — Directed Lagged Diffusion Network

## Frozen implementation

- Candidate: `t02-dldn-c01`
- Entrypoint: `tournament/top40/teams/team-02/strategy.py:build_strategy`
- Seed: `20260713`
- Parameters: `L=540`, `lambda=20`, `K=3`, `kappa=0.5`, `tau=0.015`, `H=0.30`
- Phase-0 record commit supplied to the team: `012727865acecad6ea0c3327745359820b8e45c6`
- Public OOS accessed by the QE: no

The implementation learns all regression, graph, clustering, scale, and projection state from the
past-only `DecisionContext` inside the chronological worker. It has no filesystem, network,
process, environment-variable, prefit-model, or timestamp-to-target dependency. The exact
eligible tuple is part of refit state; every Monday or tuple addition, removal, or order change
forces a refit and explicit mapping. Invalid fits/scores return `{}` and reset hysteresis state;
sub-threshold valid changes return `None`.

## Environment

- Linux `6.18.33.2-microsoft-standard-WSL2`, x86-64
- Python `3.13.12`
- NumPy `2.2.6`
- pandas `3.0.0`
- Team `uv.lock` is a byte-identical copy of the root lock.

## Frozen hashes

- Strategy SHA-256: `22bb19d7e20d9a1c07a9c00af1436914e3239c9ed9e98d521a9f4605d4671e4e`
- Frozen-config SHA-256: `eb107387695398746f7f58de1a50f31c914259783af2e88899c25d41d246bb4d`
- Team/root lock SHA-256: `869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5`
- Data-manifest SHA-256: `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`
- Common-config SHA-256: `030a065f75f9c4adb7484065908f4379435929609d446be0de0a831d9e28ee0a`

The complete team-tree/source-bundle fingerprint is intentionally recomputed after this report is
final because the report and compliance evidence are part of that fingerprint.

## Verification performed

Commands were run from the tournament worktree with bytecode writes disabled for final checks:

```text
PYTHONDONTWRITEBYTECODE=1 uv run ruff check tournament/top40/teams/team-02/strategy.py tournament/top40/teams/team-02/test_team_02_strategy.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tournament/top40/teams/team-02/test_team_02_strategy.py
```

Result: ruff passed and `7 passed in 0.80s`. The tests cover truncation, corrupt-future, append,
and clean-instance bit invariance; fixed seed; exact eligible-only finite two-sided caps; a missing
current return; forced refit, hold, and flat state semantics; next-open fills; entry/exit fees and
slippage; actual-timestamp funding signs; a fresh 2x-cost evaluation; past-only Top-40 membership;
participation-shared delisting exits; and the adverse residual settlement.

A separate causal 40-asset single-refit smoke completed in `0.409s`, returning gross `0.80`, net
`-5.519e-17`, and maximum symbol weight `0.048464`. A representative 1,000-decision, 40-asset,
single-thread duration smoke completed in `20.222s`; its linear 7,020-decision projection is
`141.959s`, comfortably below the 900-second worker cap. These smokes read no tournament market
rows.

Ledger/config validation confirmed exactly one newline-terminated `registered` event, exact schema
keys, candidate/seed/parameter agreement, `public_oos_requested=true`, and no result event. Bundle
validation uses `crypto_trade.tournament.runner.source_bundle_fingerprint` and rejects generated
bytecode or any disallowed team-tree content.

## Canonical reproduction and artifacts

The organizer-authorized research command, not executed by the QE, is:

```text
uv run python scripts/top40_tournament.py run-team team-02 --candidate-id t02-dldn-c01
```

The stable post-freeze reproduction command is:

```text
uv run python scripts/top40_tournament.py validate tournament/top40/teams/team-02/submission.json
```

Canonical base and 2x-cost return locations are respectively
`reports-top40/team-02/daily_returns.csv` and
`reports-top40/team-02/double_cost_daily_returns.csv`; bar-level locations are
`reports-top40/team-02/bar_returns.csv` and
`reports-top40/team-02/double_cost_bar_returns.csv`. These files do not exist until the authorized
organizer run. Clean canonical reruns require byte-identical artifacts and exact scalar equality;
the accepted discrepancy tolerance is zero bytes and zero scalar difference.

## Known limitations

- No public-OOS result or canonical base/2x report was read or produced by the QE. The pending
  registration requests the QR-authorized single organizer-gated view.
- Synthetic engineering tests cannot establish realized sleeve floors, fillability, or performance
  on the frozen market snapshot; those remain canonical evaluator outputs.
- The QR disclosed a negative naive IS prototype and forbids performance claims. This
  implementation freezes the requested mechanism without optimizing it.
- Graph eigensystems and pseudoinverses depend on the pinned x86-64 NumPy numerical stack; the
  canonical worker and lock fix that stack and require byte-identical reruns.
- Binance lacks historical point-in-time order-filter history. The common evaluator uses continuous
  quantities; live paper execution must apply then-current filters and rounding.
