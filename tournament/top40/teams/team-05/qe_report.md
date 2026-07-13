# Team-05 QE report

## Outcome

The frozen `T05-AER12-H80-R72-v1` specification is implemented behind the target-weight
protocol. The independent synthetic QE suite passes all 23 tests, the strategy and evaluator
reject explicit NaN/Inf targets, two clean processes reproduce target/position/return/manifest
hashes byte-for-byte, and the team dependency lock is byte-identical to the repository root lock.

This QE run did not read or evaluate public OOS and did not run a canonical snapshot backtest.
Consequently, the QR's numerical OOF performance, turnover, realized-sleeve, and 95% QP-level-1
acceptance gates remain for the organizer's authorized IS-only gate. No performance conclusion is
claimed here.

## Frozen bindings

- Common freeze commit: `48df09341f02eba7a3469abd1ccda6649a4ef0ba`
- Phase-0 record commit: `012727865acecad6ea0c3327745359820b8e45c6`
- Data manifest SHA-256: `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`
- Common config SHA-256: `030a065f75f9c4adb7484065908f4379435929609d446be0de0a831d9e28ee0a`
- Strategy SHA-256: `30e8159fddf388d42750def7f32c9a122c1a589611b820765c4e0aaaf441cd37`
- Frozen config SHA-256: `8b7b74a3d304b0036d1a4a7becc5fcf536c3daf0c97687f4dfede20bced939ae`
- Test source SHA-256: `0407ee59d77a9de6c2b76eac6f7b189fa7306994d5e70515fefcf5837a53846d`
- Compliance SHA-256: `9f15ae9d9c4ad1bd4ffd65af07c293b7c1f63682dc214d9c156f02e7b6c6990d`
- Team/root dependency-lock SHA-256: `869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5`

The Phase-0 field uses the organizer-supplied final replacement record. No discarded or guessed
Phase-0 hash is retained in QE-created config/report files.

## Environment

- OS: `Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.35`
- Python: `3.13.12`
- NumPy: `2.2.6`
- pandas: `3.0.0`
- SciPy: `1.17.0`
- pytest: `9.0.2`
- Deterministic strategy seed: `20260713`
- Trial namespace seed: `2026071305`
- Test setting: `PYTHONDONTWRITEBYTECODE=1`; pytest cache provider disabled

## Implementation evidence

The strategy implements scheduled-slot, exact-8h adjacency throughout. It calculates the frozen
true-range auction score without assigning wick/body credit to gaps; uses adjacent log close
returns, exact contiguous 3/21-return horizons, 21-slot volatility/quote volume, demeaned 63-slot
BTC beta, and strictly lagged actual funding; applies contemporaneous median/MAD transforms and
the fixed nuisance projection; and fails flat on unavailable BTC, fewer than ten fully valid
names, or zero alpha MAD.

Requested tail sets use the frozen 0.80/0.20 entry and 0.55/0.45 retention thresholds. BTC
Parkinson-range stress state uses 90 scheduled slots, 75 minimum, strict 0.80/0.65 hysteresis, and
stress-on-unavailability. The deterministic sorted-symbol SLSQP uses the exact objective, bounds,
equalities, tolerances, and ordered funding/beta fallbacks. Each mapping records fallback level in
the strategy's in-memory `fallback_history`; level 4 denotes an explicit flat request. Mappings are
emitted only for selection, PIT membership, stress-state, or 72h-refresh changes; otherwise the
strategy returns `None`.

## Test commands and results

Primary command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -p no:cacheprovider \
  tournament/top40/teams/team-05/test_team_05_strategy.py -q
```

Result: `23 passed in 5.32s`. Measured process wall time was `5.77s`, user CPU `16.58s`, system CPU
`0.35s`, and peak RSS `169228 KiB`.

Static formatting/scanner command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run ruff check \
  tournament/top40/teams/team-05/strategy.py \
  tournament/top40/teams/team-05/test_team_05_strategy.py
```

Result: `All checks passed!`. The test suite also performs an AST allowlist scan of strategy
imports/calls and rejects network/process/filesystem and historical-portfolio capability tokens.

Compile/JSON/lock checks:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python - <<'PY'
import json
from pathlib import Path
for path in (
    Path('tournament/top40/teams/team-05/strategy.py'),
    Path('tournament/top40/teams/team-05/test_team_05_strategy.py'),
):
    compile(path.read_text(encoding='utf-8'), str(path), 'exec')
for path in (
    Path('tournament/top40/teams/team-05/frozen_config.json'),
    Path('tournament/top40/teams/team-05/compliance.json'),
):
    json.loads(path.read_text(encoding='utf-8'))
PY
cmp -s /home/roberto/crypto-trade/uv.lock \
  tournament/top40/teams/team-05/uv.lock
```

The following behaviors have direct passing tests:

- exact auction/body/gap math, log-return windows, demeaned beta, funding lag/age, robust z, and
  zero-alpha-MAD flat behavior;
- tail and stress hysteresis, 72h refresh, immediate membership-loss mapping, QP equalities/caps,
  deterministic level-1/2/3 fallback behavior, finite signed two-sided outputs, and fresh factory;
- truncation, corrupt-future, and append invariance with exact target-frame equality;
- closed-bar and strictly-prior-funding context, point-in-time membership, next-open fills, actual
  funding sign/timestamp, entry/rebalance/exit costs, long/short exposure and PnL signs;
- independent 2x-cost evaluation, participation-limited fills, charged forced-delist execution,
  common adverse residual settlement, caps, missing prices, duplicate timestamps, flat/hold
  distinction, and NaN/Inf rejection at both mapping and raw-target ingestion;
- two independent Python processes reproducing synthetic targets, positions, base returns,
  2x-cost returns, and their aggregate manifest hash exactly.

These passing tests back every `true` value in `compliance.json`.

## Reproduction

Exact QE reproduction command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --locked pytest -p no:cacheprovider \
  tournament/top40/teams/team-05/test_team_05_strategy.py -q
```

Stable post-freeze organizer command, after source manifest, review binding, champion freeze, and
canonical artifacts exist:

```bash
uv run python scripts/top40_tournament.py validate \
  tournament/top40/teams/team-05/submission.json
```

## Canonical report locations and tolerance

- Base report location: `PENDING_ORGANIZER_CANONICAL_RUN`
- 2x-cost report location: `PENDING_ORGANIZER_CANONICAL_RUN`

Those reports were intentionally not created: canonical base/2x evaluation is organizer-owned,
and this scoped QE task prohibited public-OOS access and writes outside team-05. The synthetic
base/2x evidence is generated ephemerally by the test suite and leaves no claimed performance
artifact.

Rerun discrepancy tolerance for targets, positions, returns, and manifest hashes is zero bytes.
QP acceptance separately uses the frozen equality-residual threshold `1e-8` and SLSQP
`ftol=1e-12`; those numeric solver thresholds are not a relaxation of the byte-identical clean
rerun requirement.

## Known limitations and required organizer follow-up

- Run the authorized IS-only seven-fold gate before acceptance. This QE run does not establish the
  required QP-level-1 share, target turnover, OOF base/2x Sharpe, drawdown, positive-quarter rate,
  realized sleeve/execution floors, median-fold return, or fold IC signs.
- No public OOS rows or results were accessed. Public-OOS views remain zero.
- Historical quantity steps/minimum notionals are unavailable under the common data contract;
  canonical history remains continuous-quantity, while forward paper must apply current filters.
- Determinism is pinned to the frozen dependency lock and x86-64 official runtime; the organizer's
  two clean canonical reruns remain authoritative.
