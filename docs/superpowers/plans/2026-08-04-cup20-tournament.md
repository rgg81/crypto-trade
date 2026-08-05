# CUP-20 Tournament Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the CUP-20 organiser infrastructure — a stable top-20 pure-crypto universe, physically split IS/sealed snapshots, a common-risk-unit evaluator, neighbourhood-median scoring, hard floors, ranking, and a hash-chained trial journal — so that twelve blind teams can research on IS and exactly three can be advanced to a two-year sealed holdout.

**Architecture:** A new `src/crypto_trade/cup20/` package layers CUP-20 policy on top of the proven `crypto_trade.tournament` execution core. Teams implement the existing narrow `TargetStrategy` protocol; the organiser owns universe construction, fills, funding, costs, risk normalisation, scoring and disclosure. Every scored number is a per-metric median over a pre-declared parameter neighbourhood, never a single nominated point.

**Tech Stack:** Python 3.13, pandas, numpy, pytest, ruff, uv. Reused from `crypto_trade.tournament`: `protocol` (DecisionContext / TargetStrategy), `engine_v2` (`generate_targets`, `evaluate_targets`, `EvaluatorConfig`, `EvaluationResult`), `risk_policy` (`RiskPolicy`), `data` (`eligible_at`, `sha256_manifest`), `pure_crypto_universe_v6` (fail-closed asset audit).

## Global Constraints

- Source spec: `docs/superpowers/specs/2026-08-04-cup20-tournament-design.md`. Where this plan and the spec disagree, the spec wins and the plan is wrong.
- Python 3.13+. Run everything through `uv run` with `export PATH="$HOME/.local/bin:$PATH"`.
- Ruff: `select = ["E","F","I","N","W","UP"]`, `line-length = 100`. Run `uv run ruff check . --fix && uv run ruff format .` before every commit.
- Tests live under `tests/cup20/`. Run with `uv run pytest tests/cup20/ -q`.
- Frozen dataclasses for all value objects. Type hints on every public function.
- All timestamps are timezone-aware UTC `pd.Timestamp`. Naive timestamps are a bug, not a convenience.
- **Decision grid:** 8h boundaries at 00:00 / 08:00 / 16:00 UTC.
- **IS window:** `[IS_START, 2024-08-01T00:00:00Z)`. `IS_START` is computed at snapshot build, never hardcoded by hand.
- **Sealed window:** `[2024-08-01T00:00:00Z, 2026-08-01T00:00:00Z)`.
- **Universe:** weekly reconstitution, trailing 180-day quote volume, complete-window eligibility, hysteresis entry rank 20 / exit rank 25, target size 20.
- **Costs:** 5.0 bps taker fee + 2.5 bps slippage per side; every candidate scored at cost multipliers 1, 2 and 3.
- **Common risk unit:** 10% annualised volatility target, 90-day trailing lookback, scale clamped to `[0.20, 3.0]`.
- **Evaluator caps:** `max_gross_exposure = 1.0`, `max_abs_net_exposure = 1.0`, `max_symbol_exposure = 0.20`, `max_bar_participation = 0.001`, `initial_equity = 100_000.0`. The evaluator is unlevered by construction and rejects any gross above 1.0.
- **Minimum realised volatility floor `0.06`.** Human ruling 2026-08-04: because gross is capped at 1.0, the common risk unit can always scale a book down to the 10% target but cannot scale a very-low-volatility book up past unit gross. A candidate whose neighbourhood-median realised annualised volatility is below 0.06 fails a hard floor, so an under-risked book is disqualified rather than rewarded with an unearned drawdown advantage.
- **Trial budget:** 12 material trials per team, minimum 8 before nomination. The declared neighbourhood sweep is one trial; the falsification battery is one trial.
- No team code may read `data/cup20/sealed/`, another team's directory, or any prior-tournament directory.
- Verified environment in this worktree: pandas 3.0.0, numpy 2.2.6, pyarrow 23.0.1. All reused
  `crypto_trade.tournament` imports resolve. Note that `EvaluatorConfig` **defaults** to
  `max_abs_net_exposure=0.25` and `max_symbol_exposure=0.10`; CUP-20 must construct it explicitly
  from the `[execution]` table via `evaluator_config(...)` so directional mandates are not silently
  capped at quarter-net.

## File Structure

| File | Responsibility |
|---|---|
| `src/crypto_trade/cup20/__init__.py` | Public API re-exports |
| `src/crypto_trade/cup20/config.py` | Load + validate the frozen `config.toml` machine contract |
| `src/crypto_trade/cup20/universe.py` | Point-in-time top-20 membership with hysteresis |
| `src/crypto_trade/cup20/snapshot.py` | Build IS and sealed snapshots from raw bars/funding; manifests |
| `src/crypto_trade/cup20/risk_unit.py` | Causal common-risk-unit scalars |
| `src/crypto_trade/cup20/runner.py` | Two-pass candidate evaluation at 1×/2×/3× cost |
| `src/crypto_trade/cup20/metrics.py` | Window metrics, folds, quarters, concentration, roles |
| `src/crypto_trade/cup20/bootstrap.py` | Circular block bootstrap + trial-adjusted confidence |
| `src/crypto_trade/cup20/neighbourhood.py` | Neighbourhood declaration + per-metric median |
| `src/crypto_trade/cup20/qualification.py` | Conjunctive hard floors → gate vector |
| `src/crypto_trade/cup20/scoring.py` | `G` score, ranking, tie-breaks |
| `src/crypto_trade/cup20/journal.py` | Append-only hash-chained journal |
| `src/crypto_trade/cup20/archive.py` | Source archive + candidate identity hashes |
| `src/crypto_trade/cup20/report.py` | Result packets, manifest, atomic release |
| `tests/cup20/` | One test module per source module + leak battery + differential test |
| `TOURNAMENT-CHARTER-CUP20.md` | Charter (meaning) |
| `tournament/cup20/config.toml` | Machine contract (numbers) |
| `tournament/cup20/teams/team-NN/MANDATE.md` | Per-team assigned mechanism lane |
| `tournament/cup20/TEAM-PLAYBOOK.md` | Operating rules handed to every team |

---

### Task 1: Charter, machine contract, and package skeleton

**Files:**
- Create: `TOURNAMENT-CHARTER-CUP20.md`
- Create: `tournament/cup20/config.toml`
- Create: `src/crypto_trade/cup20/__init__.py`
- Create: `src/crypto_trade/cup20/config.py`
- Test: `tests/cup20/__init__.py`, `tests/cup20/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `load_config(path: str | Path) -> LoadedConfig` where `LoadedConfig` is a frozen dataclass with fields `path: Path`, `sha256: str`, `raw: Mapping[str, Any]`; `validate_config(raw: Mapping[str, Any]) -> None` raising `ValueError` on any drift; module constants `IS_END`, `SEALED_START`, `SEALED_END` as `pd.Timestamp`.

- [ ] **Step 1: Write the failing test**

```python
# tests/cup20/test_config.py
from pathlib import Path

import pytest

from crypto_trade.cup20.config import IS_END, SEALED_END, SEALED_START, load_config, validate_config

CONFIG_PATH = Path("tournament/cup20/config.toml")


def test_windows_are_frozen_utc_timestamps():
    assert str(IS_END) == "2024-08-01 00:00:00+00:00"
    assert str(SEALED_START) == "2024-08-01 00:00:00+00:00"
    assert str(SEALED_END) == "2026-08-01 00:00:00+00:00"


def test_load_config_returns_bytes_hash_and_policy():
    loaded = load_config(CONFIG_PATH)
    assert len(loaded.sha256) == 64
    assert loaded.raw["universe"]["target_size"] == 20
    assert loaded.raw["universe"]["entry_rank"] == 20
    assert loaded.raw["universe"]["exit_rank"] == 25
    assert loaded.raw["universe"]["lookback_days"] == 180
    assert loaded.raw["execution"]["taker_fee_bps_per_side"] == 5.0
    assert loaded.raw["execution"]["slippage_bps_per_side"] == 2.5
    assert loaded.raw["risk_unit"]["target_annualized_volatility"] == 0.10
    assert loaded.raw["research"]["trial_budget"] == 12
    assert loaded.raw["selection"]["advancing_slots"] == 3
    assert len(loaded.raw["mandates"]) == 12


def test_validate_config_rejects_drift():
    loaded = load_config(CONFIG_PATH)
    tampered = {key: dict(value) if isinstance(value, dict) else value
                for key, value in loaded.raw.items()}
    tampered["universe"]["target_size"] = 40
    with pytest.raises(ValueError):
        validate_config(tampered)


def test_validate_config_rejects_unknown_table():
    loaded = load_config(CONFIG_PATH)
    tampered = dict(loaded.raw)
    tampered["surprise"] = {}
    with pytest.raises(ValueError):
        validate_config(tampered)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/cup20/test_config.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20'`

- [ ] **Step 3: Write the charter**

Copy §1–§14 of `docs/superpowers/specs/2026-08-04-cup20-tournament-design.md` into `TOURNAMENT-CHARTER-CUP20.md`, adding this header verbatim:

```markdown
# CUP-20 Tournament Charter

Status: pre-activation authority
Tournament: `cup20`
Machine contract: `tournament/cup20/config.toml`

This charter controls meaning. The config controls numerical policy. Activation MUST fail on
disagreement. Before the first result an activation record hash-binds this charter, the config,
the implementation, the dependency lock, the data authority, the pure-crypto audit and the focused
test output. Later changes require a prospective, append-only amendment made before the affected
data are accessed. Historical evidence is never rewritten.
```

- [ ] **Step 4: Write the machine contract**

```toml
# tournament/cup20/config.toml
schema_version = 1
name = "cup20"
policy_status = "pre-activation"
charter_path = "TOURNAMENT-CHARTER-CUP20.md"
teams = [
  "team-01", "team-02", "team-03", "team-04", "team-05", "team-06",
  "team-07", "team-08", "team-09", "team-10", "team-11", "team-12",
]

[paths]
tournament_root = "tournament/cup20"
reports_root = "reports-cup20"
team_root = "tournament/cup20/teams"
research_journal = "tournament/cup20/research-journal.jsonl"
nomination_registry = "tournament/cup20/nomination-registry.json"
selection_freeze = "tournament/cup20/selection-freeze.json"
activation_freeze = "tournament/cup20/activation-freeze.json"
source_archive_root = "reports-cup20/source-archives/sha256"
is_reports_root = "reports-cup20/is"
private_holdout_root = "tournament/cup20/private/holdout"
holdout_release_root = "reports-cup20/holdout"

[data]
is_root = "data/cup20/is"
sealed_root = "data/cup20/sealed"

[splits]
is_end = "2024-08-01T00:00:00Z"
sealed_start = "2024-08-01T00:00:00Z"
sealed_end = "2026-08-01T00:00:00Z"

[universe]
target_size = 20
entry_rank = 20
exit_rank = 25
lookback_days = 180
reconstitution_weekday = 0
minimum_scored_members = 8

[execution]
interval_hours = 8
initial_equity = 100_000.0
taker_fee_bps_per_side = 5.0
slippage_bps_per_side = 2.5
max_gross_exposure = 1.0
max_abs_net_exposure = 1.0
max_symbol_exposure = 0.20
max_bar_participation = 0.001
cost_multipliers = [1, 2, 3]

[risk_unit]
target_annualized_volatility = 0.10
lookback_days = 90
minimum_scale = 0.20
maximum_scale = 3.0

[research]
trial_budget = 12
minimum_trials_for_nomination = 8
neighbourhood_minimum_points = 7
neighbourhood_positive_fraction = 0.70

[statistics]
bootstrap_samples = 2000
bootstrap_block_days = 10
bootstrap_seed = 20260804
minimum_trial_adjusted_confidence = 0.90

[floors]
net_sharpe = 0.80
double_cost_sharpe = 0.50
max_drawdown = 0.20
minimum_realized_volatility = 0.06
positive_quarter_fraction = 0.50
minimum_positive_folds = 3
worst_fold_sharpe = -0.25
max_annualized_turnover = 25.0
min_gross_edge_bps_per_turnover = 40.0
max_cost_share_of_positive_gross = 0.30
max_top5_day_share = 0.35
max_fold_share_of_positive_pnl = 0.60
minimum_trades = 500

[selection]
advancing_slots = 3

[holdout]
max_drawdown = 0.25
minimum_positive_quarters = 5

[mandates]
team-01 = "slow-per-coin-time-series-momentum"
team-02 = "breakout-channel-position"
team-03 = "trend-quality-gated-momentum"
team-04 = "market-residual-cross-sectional-momentum"
team-05 = "short-horizon-liquidity-shock-reversal"
team-06 = "downside-risk-low-volatility-selection"
team-07 = "funding-carry-crowding-crash-protection"
team-08 = "funding-basis-term-dynamics-reversion"
team-09 = "taker-flow-price-volume-pressure"
team-10 = "volatility-regime-risk-on-risk-off-timing"
team-11 = "calendar-settlement-clock-seasonality"
team-12 = "preregistered-multi-sleeve-ensemble"
```

- [ ] **Step 5: Write the config loader**

```python
# src/crypto_trade/cup20/config.py
"""Fail-closed machine contract for the CUP-20 tournament."""

from __future__ import annotations

import dataclasses
import hashlib
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

IS_END = pd.Timestamp("2024-08-01T00:00:00Z")
SEALED_START = pd.Timestamp("2024-08-01T00:00:00Z")
SEALED_END = pd.Timestamp("2026-08-01T00:00:00Z")

TEAM_IDS = tuple(f"team-{index:02d}" for index in range(1, 13))

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "name",
        "policy_status",
        "charter_path",
        "teams",
        "paths",
        "data",
        "splits",
        "universe",
        "execution",
        "risk_unit",
        "research",
        "statistics",
        "floors",
        "selection",
        "holdout",
        "mandates",
    }
)

_FROZEN_SCALARS: dict[tuple[str, ...], object] = {
    ("schema_version",): 1,
    ("name",): "cup20",
    ("splits", "is_end"): "2024-08-01T00:00:00Z",
    ("splits", "sealed_start"): "2024-08-01T00:00:00Z",
    ("splits", "sealed_end"): "2026-08-01T00:00:00Z",
    ("universe", "target_size"): 20,
    ("universe", "entry_rank"): 20,
    ("universe", "exit_rank"): 25,
    ("universe", "lookback_days"): 180,
    ("execution", "interval_hours"): 8,
    ("execution", "taker_fee_bps_per_side"): 5.0,
    ("execution", "slippage_bps_per_side"): 2.5,
    ("execution", "max_gross_exposure"): 1.0,
    ("execution", "max_symbol_exposure"): 0.20,
    ("risk_unit", "target_annualized_volatility"): 0.10,
    ("risk_unit", "lookback_days"): 90,
    ("risk_unit", "minimum_scale"): 0.20,
    ("risk_unit", "maximum_scale"): 3.0,
    ("research", "trial_budget"): 12,
    ("research", "minimum_trials_for_nomination"): 8,
    ("statistics", "minimum_trial_adjusted_confidence"): 0.90,
    ("floors", "max_drawdown"): 0.20,
    ("floors", "minimum_realized_volatility"): 0.06,
    ("selection", "advancing_slots"): 3,
    ("holdout", "max_drawdown"): 0.25,
}


@dataclasses.dataclass(frozen=True, slots=True)
class LoadedConfig:
    """Canonical config bytes and parsed policy."""

    path: Path
    sha256: str
    raw: Mapping[str, Any]


def _lookup(raw: Mapping[str, Any], path: tuple[str, ...]) -> object:
    current: object = raw
    for component in path:
        if not isinstance(current, Mapping):
            raise ValueError(f"CUP-20 config {'.'.join(path)} is not a table")
        current = current.get(component)
    return current


def validate_config(raw: Mapping[str, Any]) -> None:
    """Reject any semantic drift in the activated CUP-20 policy."""
    if set(raw) != _TOP_LEVEL_KEYS:
        raise ValueError("CUP-20 config has missing or unexpected top-level tables")
    for path, expected in _FROZEN_SCALARS.items():
        if _lookup(raw, path) != expected:
            raise ValueError(f"CUP-20 config {'.'.join(path)} differs from the frozen contract")
    if tuple(raw["teams"]) != TEAM_IDS:
        raise ValueError("CUP-20 config team roster differs from the frozen contract")
    if tuple(sorted(raw["mandates"])) != TEAM_IDS:
        raise ValueError("CUP-20 config mandates must cover exactly the twelve teams")
    if len(set(raw["mandates"].values())) != len(TEAM_IDS):
        raise ValueError("CUP-20 mandates must be distinct mechanism lanes")
    if tuple(raw["execution"]["cost_multipliers"]) != (1, 2, 3):
        raise ValueError("CUP-20 cost multipliers are frozen at 1, 2 and 3")


def load_config(path: str | Path) -> LoadedConfig:
    """Read, hash and validate the frozen machine contract."""
    config_path = Path(path)
    payload = config_path.read_bytes()
    raw = tomllib.loads(payload.decode("utf-8"))
    validate_config(raw)
    return LoadedConfig(
        path=config_path,
        sha256=hashlib.sha256(payload).hexdigest(),
        raw=raw,
    )
```

```python
# src/crypto_trade/cup20/__init__.py
"""CUP-20 tournament policy, evaluation and scoring."""

from crypto_trade.cup20.config import (
    IS_END,
    SEALED_END,
    SEALED_START,
    TEAM_IDS,
    LoadedConfig,
    load_config,
    validate_config,
)

__all__ = [
    "IS_END",
    "SEALED_END",
    "SEALED_START",
    "TEAM_IDS",
    "LoadedConfig",
    "load_config",
    "validate_config",
]
```

```python
# tests/cup20/__init__.py
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_config.py -q`
Expected: 4 passed

- [ ] **Step 7: Lint and commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add TOURNAMENT-CHARTER-CUP20.md tournament/cup20/config.toml src/crypto_trade/cup20 tests/cup20
git commit -m "Add CUP-20 charter and frozen machine contract"
```

---

### Task 2: Point-in-time top-20 universe

**Files:**
- Create: `src/crypto_trade/cup20/universe.py`
- Test: `tests/cup20/test_universe.py`

**Interfaces:**
- Consumes: `crypto_trade.cup20.config`.
- Produces: `build_membership(daily_quote_volume: pd.DataFrame, *, eligible: pd.DataFrame, reconstitution_times: Sequence[pd.Timestamp], lookback_days: int = 180, target_size: int = 20, entry_rank: int = 20, exit_rank: int = 25) -> pd.DataFrame` returning columns `reconstitution_time`, `symbol`, `liquidity_rank`, `trailing_quote_volume` (schema-compatible with `crypto_trade.tournament.data.eligible_at`); and `weekly_reconstitution_times(start: pd.Timestamp, end: pd.Timestamp, *, weekday: int = 0) -> tuple[pd.Timestamp, ...]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_universe.py
import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.universe import build_membership, weekly_reconstitution_times


def _frames(symbols, days, volumes):
    index = pd.date_range("2020-01-01", periods=days, freq="D", tz="UTC")
    volume = pd.DataFrame(
        {symbol: np.full(days, value, dtype=float) for symbol, value in zip(symbols, volumes)},
        index=index,
    )
    eligible = pd.DataFrame(True, index=index, columns=list(symbols))
    return volume, eligible


def test_weekly_reconstitution_times_are_mondays_at_utc_midnight():
    times = weekly_reconstitution_times(
        pd.Timestamp("2020-01-01T00:00:00Z"), pd.Timestamp("2020-02-01T00:00:00Z")
    )
    assert times[0] == pd.Timestamp("2020-01-06T00:00:00Z")
    assert all(time.weekday() == 0 and time.hour == 0 for time in times)
    assert all(time.tzinfo is not None for time in times)


def test_incomplete_history_is_ineligible():
    volume, eligible = _frames(["AUSDT", "BUSDT"], 200, [100.0, 90.0])
    volume.loc[volume.index < "2020-03-01", "BUSDT"] = np.nan
    members = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
        lookback_days=180,
        target_size=20,
    )
    assert set(members["symbol"]) == {"AUSDT"}


def test_ranking_is_by_trailing_volume_descending():
    volume, eligible = _frames(["AUSDT", "BUSDT", "CUSDT"], 200, [10.0, 30.0, 20.0])
    members = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
        lookback_days=180,
        target_size=20,
    )
    ordered = members.sort_values("liquidity_rank")["symbol"].tolist()
    assert ordered == ["BUSDT", "CUSDT", "AUSDT"]
    assert members.sort_values("liquidity_rank")["liquidity_rank"].tolist() == [1, 2, 3]


def _ranked_frames(count=30, days=40):
    """Thirty symbols with strictly decreasing constant volume: S00 is rank 1, S29 is rank 30."""
    index = pd.date_range("2020-01-01", periods=days, freq="D", tz="UTC")
    symbols = [f"S{position:02d}USDT" for position in range(count)]
    volume = pd.DataFrame(
        {symbol: np.full(days, 1000.0 - position) for position, symbol in enumerate(symbols)},
        index=index,
    )
    eligible = pd.DataFrame(True, index=index, columns=symbols)
    return volume, eligible, index


def test_hysteresis_keeps_incumbent_between_entry_and_exit_rank():
    volume, eligible, index = _ranked_frames()
    first, second = index[7], index[14]
    # From the second window onward S00 sits between S22 (978) and S23 (977), i.e. rank 23:
    # worse than entry rank 20, better than exit rank 25, so an incumbent must survive.
    volume.loc[index[7] :, "S00USDT"] = 977.5
    members = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=[first, second],
        lookback_days=7,
        target_size=20,
        entry_rank=20,
        exit_rank=25,
    )
    first_members = set(members.loc[members["reconstitution_time"] == first, "symbol"])
    second_members = set(members.loc[members["reconstitution_time"] == second, "symbol"])
    assert "S00USDT" in first_members
    assert "S00USDT" in second_members
    assert len(second_members) == 20


def test_symbol_beyond_exit_rank_is_dropped_and_slot_refilled():
    volume, eligible, index = _ranked_frames()
    first, second = index[7], index[14]
    volume.loc[index[7] :, "S00USDT"] = 1.0
    members = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=[first, second],
        lookback_days=7,
        target_size=20,
        entry_rank=20,
        exit_rank=25,
    )
    second_members = set(members.loc[members["reconstitution_time"] == second, "symbol"])
    assert "S00USDT" not in second_members
    assert "S20USDT" in second_members
    assert len(second_members) == 20


def test_ineligible_symbol_is_excluded_even_with_complete_history():
    volume, eligible = _frames(["AUSDT", "BUSDT"], 200, [100.0, 90.0])
    eligible.loc[eligible.index >= "2020-06-01", "AUSDT"] = False
    members = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=[pd.Timestamp("2020-06-29T00:00:00Z")],
        lookback_days=180,
        target_size=20,
    )
    assert set(members["symbol"]) == {"BUSDT"}


def test_lookback_window_excludes_the_reconstitution_day_itself():
    volume, eligible = _frames(["AUSDT"], 400, [10.0])
    boundary = pd.Timestamp("2020-06-29T00:00:00Z")
    volume.loc[boundary:, "AUSDT"] = 1_000_000.0
    members = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=[boundary],
        lookback_days=180,
        target_size=20,
    )
    assert members["trailing_quote_volume"].iloc[0] == pytest.approx(10.0)


def test_naive_timestamps_are_rejected():
    volume, eligible = _frames(["AUSDT"], 200, [10.0])
    with pytest.raises(ValueError):
        build_membership(
            volume,
            eligible=eligible,
            reconstitution_times=[pd.Timestamp("2020-06-29")],
            lookback_days=180,
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_universe.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.universe'`

- [ ] **Step 3: Implement the universe builder**

```python
# src/crypto_trade/cup20/universe.py
"""Point-in-time, hysteresis-stabilised top-20 membership."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

MEMBERSHIP_COLUMNS = ("reconstitution_time", "symbol", "liquidity_rank", "trailing_quote_volume")


def weekly_reconstitution_times(
    start: pd.Timestamp, end: pd.Timestamp, *, weekday: int = 0
) -> tuple[pd.Timestamp, ...]:
    """Every UTC-midnight ``weekday`` boundary in ``[start, end)``."""
    start = _require_utc(start, "start")
    end = _require_utc(end, "end")
    days = pd.date_range(start.normalize(), end.normalize(), freq="D", tz="UTC", inclusive="left")
    return tuple(day for day in days if day.weekday() == weekday and day >= start)


def build_membership(
    daily_quote_volume: pd.DataFrame,
    *,
    eligible: pd.DataFrame,
    reconstitution_times: Sequence[pd.Timestamp],
    lookback_days: int = 180,
    target_size: int = 20,
    entry_rank: int = 20,
    exit_rank: int = 25,
) -> pd.DataFrame:
    """Build point-in-time membership from daily quote volume.

    A symbol is a candidate only when it has a *complete* ``lookback_days`` window of daily quote
    volume strictly before the boundary and is eligible on the boundary itself. The completeness
    requirement doubles as the minimum listing age. Incumbents survive to ``exit_rank``; new
    entrants require ``entry_rank``.
    """
    if lookback_days < 1 or target_size < 1:
        raise ValueError("lookback_days and target_size must be positive")
    if entry_rank < 1 or exit_rank < entry_rank:
        raise ValueError("exit_rank must be at least entry_rank")
    volume = _require_utc_index(daily_quote_volume, "daily_quote_volume")
    eligibility = _require_utc_index(eligible, "eligible").astype(bool)
    window = pd.Timedelta(days=lookback_days)

    rows: list[dict[str, object]] = []
    previous: tuple[str, ...] = ()
    for raw_time in reconstitution_times:
        boundary = _require_utc(raw_time, "reconstitution_time")
        history = volume.loc[(volume.index >= boundary - window) & (volume.index < boundary)]
        complete = history.notna().sum() == lookback_days
        eligible_now = _eligibility_at(eligibility, boundary)
        averages = history.mean()
        candidates = averages[complete & eligible_now].dropna()
        ordered = candidates.sort_values(ascending=False, kind="mergesort")
        ranks = {symbol: index + 1 for index, symbol in enumerate(ordered.index)}

        kept = [s for s in ordered.index if s in previous and ranks[s] <= exit_rank][:target_size]
        entrants = [s for s in ordered.index if s not in previous and ranks[s] <= entry_rank]
        members = kept + [s for s in entrants if s not in kept]
        members = members[:target_size]

        for symbol in members:
            rows.append(
                {
                    "reconstitution_time": boundary,
                    "symbol": symbol,
                    "liquidity_rank": ranks[symbol],
                    "trailing_quote_volume": float(ordered[symbol]),
                }
            )
        previous = tuple(members)

    if not rows:
        return pd.DataFrame(columns=list(MEMBERSHIP_COLUMNS))
    frame = pd.DataFrame(rows, columns=list(MEMBERSHIP_COLUMNS))
    return frame.sort_values(["reconstitution_time", "liquidity_rank"]).reset_index(drop=True)


def _eligibility_at(eligibility: pd.DataFrame, boundary: pd.Timestamp) -> pd.Series:
    past = eligibility.loc[eligibility.index <= boundary]
    if past.empty:
        return pd.Series(False, index=eligibility.columns)
    return past.iloc[-1]


def _require_utc(value: pd.Timestamp, label: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware UTC")
    return timestamp.tz_convert("UTC")


def _require_utc_index(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    index = pd.DatetimeIndex(frame.index)
    if index.tz is None:
        raise ValueError(f"{label} index must be timezone-aware UTC")
    result = frame.copy(deep=False)
    result.index = index.tz_convert("UTC")
    return result.sort_index()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_universe.py -q`
Expected: 8 passed

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/universe.py tests/cup20/test_universe.py
git commit -m "Add CUP-20 point-in-time top-20 universe with hysteresis"
```

---

### Task 3: Physically split IS and sealed snapshots

**Files:**
- Create: `src/crypto_trade/cup20/snapshot.py`
- Test: `tests/cup20/test_snapshot.py`

**Interfaces:**
- Consumes: `build_membership`, `weekly_reconstitution_times` from Task 2; `crypto_trade.tournament.data.sha256_manifest`.
- Produces: `SnapshotPaths` (frozen dataclass, fields `root: Path`, `bars: Path`, `funding: Path`, `mark_prices: Path`, `membership: Path`, `contract_metadata: Path`, `manifest: Path`); `write_split_snapshots(bars, funding, mark_prices, membership, contract_metadata, *, is_root, sealed_root, is_end, sealed_end) -> tuple[SnapshotPaths, SnapshotPaths]`; `resolve_is_start(membership: pd.DataFrame, *, target_size: int = 20) -> pd.Timestamp`; `load_snapshot(root: str | Path) -> Snapshot` where `Snapshot` is a frozen dataclass with fields `bars`, `funding`, `mark_prices`, `membership`, `contract_metadata` (all `pd.DataFrame`) and `manifest_sha256: str`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_snapshot.py
import pandas as pd
import pytest

from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start, write_split_snapshots


def _fixture_frames():
    times = pd.date_range("2024-07-25T00:00:00Z", periods=30, freq="8h")
    bars = pd.DataFrame(
        {
            "open_time": list(times) * 2,
            "symbol": ["AUSDT"] * 30 + ["BUSDT"] * 30,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 10.0,
            "quote_volume": 1000.0,
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": list(times) * 2,
            "symbol": ["AUSDT"] * 30 + ["BUSDT"] * 30,
            "funding_rate": 0.0001,
        }
    )
    marks = pd.DataFrame(
        {
            "mark_time": list(times) * 2,
            "symbol": ["AUSDT"] * 30 + ["BUSDT"] * 30,
            "mark_price": 100.0,
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [
                pd.Timestamp("2024-07-29T00:00:00Z"),
                pd.Timestamp("2024-07-29T00:00:00Z"),
                pd.Timestamp("2024-08-05T00:00:00Z"),
            ],
            "symbol": ["AUSDT", "BUSDT", "AUSDT"],
            "liquidity_rank": [1, 2, 1],
            "trailing_quote_volume": [1000.0, 900.0, 1000.0],
        }
    )
    metadata = pd.DataFrame({"symbol": ["AUSDT", "BUSDT"], "contract_type": ["PERPETUAL"] * 2})
    return bars, funding, marks, membership, metadata


def test_sealed_rows_are_absent_from_the_is_snapshot(tmp_path):
    bars, funding, marks, membership, metadata = _fixture_frames()
    is_paths, sealed_paths = write_split_snapshots(
        bars,
        funding,
        marks,
        membership,
        metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_end=pd.Timestamp("2024-08-01T00:00:00Z"),
        sealed_end=pd.Timestamp("2026-08-01T00:00:00Z"),
    )
    is_snapshot = load_snapshot(is_paths.root)
    assert is_snapshot.bars["open_time"].max() < pd.Timestamp("2024-08-01T00:00:00Z")
    assert is_snapshot.funding["funding_time"].max() < pd.Timestamp("2024-08-01T00:00:00Z")
    assert is_snapshot.membership["reconstitution_time"].max() < pd.Timestamp(
        "2024-08-01T00:00:00Z"
    )
    sealed_snapshot = load_snapshot(sealed_paths.root)
    assert sealed_snapshot.bars["open_time"].min() >= pd.Timestamp("2024-08-01T00:00:00Z")


def test_snapshots_have_distinct_manifest_hashes(tmp_path):
    bars, funding, marks, membership, metadata = _fixture_frames()
    is_paths, sealed_paths = write_split_snapshots(
        bars,
        funding,
        marks,
        membership,
        metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_end=pd.Timestamp("2024-08-01T00:00:00Z"),
        sealed_end=pd.Timestamp("2026-08-01T00:00:00Z"),
    )
    assert load_snapshot(is_paths.root).manifest_sha256 != load_snapshot(
        sealed_paths.root
    ).manifest_sha256


def test_snapshot_write_is_deterministic(tmp_path):
    bars, funding, marks, membership, metadata = _fixture_frames()
    digests = []
    for name in ("first", "second"):
        is_paths, _ = write_split_snapshots(
            bars,
            funding,
            marks,
            membership,
            metadata,
            is_root=tmp_path / name / "is",
            sealed_root=tmp_path / name / "sealed",
            is_end=pd.Timestamp("2024-08-01T00:00:00Z"),
            sealed_end=pd.Timestamp("2026-08-01T00:00:00Z"),
        )
        digests.append(load_snapshot(is_paths.root).manifest_sha256)
    assert digests[0] == digests[1]


def test_resolve_is_start_is_first_boundary_reaching_target_size():
    membership = pd.DataFrame(
        {
            "reconstitution_time": (
                [pd.Timestamp("2020-07-06T00:00:00Z")] * 19
                + [pd.Timestamp("2020-07-13T00:00:00Z")] * 20
            ),
            "symbol": [f"S{index}" for index in range(19)] + [f"S{index}" for index in range(20)],
            "liquidity_rank": list(range(1, 20)) + list(range(1, 21)),
            "trailing_quote_volume": [1.0] * 39,
        }
    )
    assert resolve_is_start(membership, target_size=20) == pd.Timestamp("2020-07-13T00:00:00Z")


def test_resolve_is_start_raises_when_target_never_reached():
    membership = pd.DataFrame(
        {
            "reconstitution_time": [pd.Timestamp("2020-07-06T00:00:00Z")] * 5,
            "symbol": [f"S{index}" for index in range(5)],
            "liquidity_rank": list(range(1, 6)),
            "trailing_quote_volume": [1.0] * 5,
        }
    )
    with pytest.raises(ValueError):
        resolve_is_start(membership, target_size=20)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_snapshot.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.snapshot'`

- [ ] **Step 3: Implement the split snapshot writer**

```python
# src/crypto_trade/cup20/snapshot.py
"""Physically separated IS and sealed snapshots.

Blindness is enforced by absence: the IS snapshot on disk contains no row at or after the IS
cutoff, so no team code path can read a sealed row even if it tries.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pandas as pd

from crypto_trade.tournament.data import sha256_manifest

# Canonical snapshot schemas, matching the acquisition pipeline:
#   bars              open_time, symbol, open, high, low, close, volume, close_time,
#                     quote_volume, trade_count, taker_buy_volume, taker_buy_quote_volume
#   funding           funding_time, symbol, funding_rate, mark_price, mark_time,
#                     settlement_time, funding_interval_hours
#   mark_prices       mark_time, symbol, mark_price
#   membership        reconstitution_time, symbol, liquidity_rank, trailing_quote_volume
#   contract_metadata symbol, contract_type, quote_asset, margin_asset, is_crypto,
#                     onboard_date, delivery_date, underlying_type, metadata_source
_TIME_COLUMN = {
    "bars": "open_time",
    "funding": "funding_time",
    "mark_prices": "mark_time",
    "membership": "reconstitution_time",
}
_DATASETS = ("bars", "funding", "mark_prices", "membership", "contract_metadata")


@dataclasses.dataclass(frozen=True, slots=True)
class SnapshotPaths:
    root: Path
    bars: Path
    funding: Path
    mark_prices: Path
    membership: Path
    contract_metadata: Path
    manifest: Path


@dataclasses.dataclass(frozen=True, slots=True)
class Snapshot:
    bars: pd.DataFrame
    funding: pd.DataFrame
    mark_prices: pd.DataFrame
    membership: pd.DataFrame
    contract_metadata: pd.DataFrame
    manifest_sha256: str


def resolve_is_start(membership: pd.DataFrame, *, target_size: int = 20) -> pd.Timestamp:
    """First reconstitution boundary whose membership reaches ``target_size``."""
    counts = membership.groupby("reconstitution_time").size().sort_index()
    reached = counts[counts >= target_size]
    if reached.empty:
        raise ValueError(f"membership never reaches {target_size} constituents")
    return pd.Timestamp(reached.index[0]).tz_convert("UTC")


def write_split_snapshots(
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    mark_prices: pd.DataFrame,
    membership: pd.DataFrame,
    contract_metadata: pd.DataFrame,
    *,
    is_root: str | Path,
    sealed_root: str | Path,
    is_end: pd.Timestamp,
    sealed_end: pd.Timestamp,
) -> tuple[SnapshotPaths, SnapshotPaths]:
    """Write the IS snapshot (strictly before ``is_end``) and the sealed snapshot."""
    frames = {
        "bars": bars,
        "funding": funding,
        "mark_prices": mark_prices,
        "membership": membership,
        "contract_metadata": contract_metadata,
    }
    is_frames = {name: _slice(name, frame, None, is_end) for name, frame in frames.items()}
    sealed_frames = {
        name: _slice(name, frame, is_end, sealed_end) for name, frame in frames.items()
    }
    return (
        _write(is_frames, Path(is_root), window=("", is_end)),
        _write(sealed_frames, Path(sealed_root), window=(is_end, sealed_end)),
    )


def load_snapshot(root: str | Path) -> Snapshot:
    """Load a snapshot and verify its manifest digest."""
    root_path = Path(root)
    manifest = json.loads((root_path / "manifest.json").read_text())
    files = [root_path / f"{name}.parquet" for name in _DATASETS]
    digest, _ = sha256_manifest(files, root=root_path)
    if digest != manifest["manifest_sha256"]:
        raise ValueError(f"snapshot at {root_path} does not match its manifest digest")
    loaded = {name: pd.read_parquet(root_path / f"{name}.parquet") for name in _DATASETS}
    return Snapshot(manifest_sha256=digest, **loaded)


def _slice(
    name: str, frame: pd.DataFrame, start: pd.Timestamp | None, end: pd.Timestamp
) -> pd.DataFrame:
    column = _TIME_COLUMN.get(name)
    if column is None:
        # Timeless datasets (contract metadata) are sorted for byte-stable manifests.
        return frame.sort_values("symbol").reset_index(drop=True)
    times = pd.to_datetime(frame[column], utc=True)
    mask = times < end
    if start is not None:
        mask &= times >= start
    result = frame.loc[mask].copy()
    result[column] = times.loc[mask]
    return result.sort_values([column, "symbol"]).reset_index(drop=True)


def _write(
    frames: dict[str, pd.DataFrame], root: Path, *, window: tuple[object, pd.Timestamp]
) -> SnapshotPaths:
    root.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_parquet(root / f"{name}.parquet", index=False)
    files = [root / f"{name}.parquet" for name in _DATASETS]
    digest, entries = sha256_manifest(files, root=root)
    manifest = {
        "schema_version": 1,
        "manifest_sha256": digest,
        "window_start": str(window[0]),
        "window_end": str(window[1]),
        "files": entries,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return SnapshotPaths(
        root=root,
        bars=root / "bars.parquet",
        funding=root / "funding.parquet",
        mark_prices=root / "mark_prices.parquet",
        membership=root / "membership.parquet",
        contract_metadata=root / "contract_metadata.parquet",
        manifest=root / "manifest.json",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_snapshot.py -q`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/snapshot.py tests/cup20/test_snapshot.py
git commit -m "Add CUP-20 physically split IS and sealed snapshots"
```

---

### Task 4: Common risk unit

**Files:**
- Create: `src/crypto_trade/cup20/risk_unit.py`
- Test: `tests/cup20/test_risk_unit.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `common_risk_scalars(gross_returns: pd.Series, decision_times: Sequence[pd.Timestamp], *, target_annualized_volatility: float = 0.10, lookback_days: int = 90, interval_hours: int = 8, minimum_scale: float = 0.20, maximum_scale: float = 3.0) -> pd.Series` indexed by `decision_times`; `apply_risk_scalars(targets: pd.DataFrame, scalars: pd.Series) -> pd.DataFrame`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_risk_unit.py
import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.cup20.risk_unit import apply_risk_scalars, common_risk_scalars

BARS_PER_YEAR = 365 * 24 / 8


def _returns(count, sigma_per_bar, seed=0):
    index = pd.date_range("2020-01-01T00:00:00Z", periods=count, freq="8h")
    values = np.random.default_rng(seed).normal(0.0, sigma_per_bar, count)
    return pd.Series(values, index=index)


def test_scale_is_one_before_the_lookback_is_full():
    series = _returns(100, 0.01)
    decisions = [series.index[50]]
    scalars = common_risk_scalars(series, decisions, lookback_days=90)
    assert scalars.iloc[0] == 1.0


def test_scale_targets_ten_percent_annualised_volatility():
    sigma_per_bar = 0.30 / math.sqrt(BARS_PER_YEAR)
    series = _returns(600, sigma_per_bar, seed=7)
    decision = series.index[-1] + pd.Timedelta(hours=8)
    scalars = common_risk_scalars(series, [decision], lookback_days=90)
    realized = series.iloc[-270:].std(ddof=1) * math.sqrt(BARS_PER_YEAR)
    assert scalars.iloc[0] == pytest.approx(0.10 / realized)


def test_scale_is_clamped_to_the_declared_band():
    calm = pd.Series(
        np.full(400, 1e-9), index=pd.date_range("2020-01-01T00:00:00Z", periods=400, freq="8h")
    )
    decision = calm.index[-1] + pd.Timedelta(hours=8)
    assert common_risk_scalars(calm, [decision]).iloc[0] == 3.0

    wild = _returns(400, 0.5, seed=3)
    decision = wild.index[-1] + pd.Timedelta(hours=8)
    assert common_risk_scalars(wild, [decision]).iloc[0] == 0.20


def test_scalar_uses_only_returns_strictly_before_the_decision():
    series = _returns(400, 0.01, seed=11)
    decision = series.index[350]
    baseline = common_risk_scalars(series, [decision]).iloc[0]
    corrupted = series.copy()
    corrupted.iloc[350:] = 10.0
    assert common_risk_scalars(corrupted, [decision]).iloc[0] == baseline


def test_apply_risk_scalars_leaves_the_instruction_column_untouched():
    index = pd.date_range("2020-01-01T00:00:00Z", periods=2, freq="8h")
    targets = pd.DataFrame(
        {"AUSDT": [0.5, -0.5], "BUSDT": [-0.5, 0.5], REBALANCE_INSTRUCTION_COLUMN: [True, False]},
        index=index,
    )
    scaled = apply_risk_scalars(targets, pd.Series([0.5, 2.0], index=index))
    assert scaled["AUSDT"].tolist() == [0.25, -1.0]
    assert scaled[REBALANCE_INSTRUCTION_COLUMN].tolist() == [True, False]


def test_apply_risk_scalars_requires_matching_index():
    index = pd.date_range("2020-01-01T00:00:00Z", periods=2, freq="8h")
    targets = pd.DataFrame({"AUSDT": [0.5, -0.5]}, index=index)
    with pytest.raises(ValueError):
        apply_risk_scalars(targets, pd.Series([0.5], index=index[:1]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_risk_unit.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.risk_unit'`

- [ ] **Step 3: Implement the common risk unit**

```python
# src/crypto_trade/cup20/risk_unit.py
"""Causal common risk unit.

Every submission is scaled toward one ex-ante volatility target so that drawdown comparisons
measure tail behaviour and regime timing rather than who chose to trade smallest. The scalar is
derived from the *unscaled* book's gross returns, which removes any circularity between the scalar
and the costs it induces.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN


def common_risk_scalars(
    gross_returns: pd.Series,
    decision_times: Sequence[pd.Timestamp],
    *,
    target_annualized_volatility: float = 0.10,
    lookback_days: int = 90,
    interval_hours: int = 8,
    minimum_scale: float = 0.20,
    maximum_scale: float = 3.0,
) -> pd.Series:
    """Gross-return volatility scalars, using only rows strictly before each decision."""
    if target_annualized_volatility <= 0:
        raise ValueError("target_annualized_volatility must be positive")
    if not 0 < minimum_scale <= maximum_scale:
        raise ValueError("scale band must satisfy 0 < minimum_scale <= maximum_scale")
    bars_per_year = 365 * 24 / interval_hours
    required = max(2, math.ceil(lookback_days * 24 / interval_hours))

    history = gross_returns.sort_index()
    times = pd.DatetimeIndex(history.index)
    if times.tz is None:
        raise ValueError("gross_returns index must be timezone-aware UTC")
    values = history.to_numpy(dtype=float)

    scalars: list[float] = []
    index: list[pd.Timestamp] = []
    for raw_time in decision_times:
        decision = pd.Timestamp(raw_time)
        if decision.tzinfo is None:
            raise ValueError("decision_times must be timezone-aware UTC")
        # Strictly earlier rows only. Conservative under either return-stamping convention.
        stop = int(times.searchsorted(decision, side="left"))
        index.append(decision)
        if stop < required:
            scalars.append(1.0)
            continue
        window = values[stop - required : stop]
        if not np.isfinite(window).all():
            raise ValueError("gross returns contain non-finite values")
        realized = float(np.std(window, ddof=1)) * math.sqrt(bars_per_year)
        if realized <= 0.0:
            scalars.append(maximum_scale)
            continue
        scalars.append(
            min(maximum_scale, max(minimum_scale, target_annualized_volatility / realized))
        )
    return pd.Series(scalars, index=pd.DatetimeIndex(index), dtype=float)


def apply_risk_scalars(targets: pd.DataFrame, scalars: pd.Series) -> pd.DataFrame:
    """Multiply every weight column by its boundary scalar, preserving the instruction column."""
    if not targets.index.equals(scalars.index):
        raise ValueError("risk scalars must be indexed by exactly the target decision times")
    scaled = targets.copy()
    weight_columns = [column for column in scaled.columns if column != REBALANCE_INSTRUCTION_COLUMN]
    scaled[weight_columns] = scaled[weight_columns].mul(scalars.astype(float), axis=0)
    return scaled
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_risk_unit.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/risk_unit.py tests/cup20/test_risk_unit.py
git commit -m "Add CUP-20 causal common risk unit"
```

---

### Task 5: Two-pass candidate runner

**Files:**
- Create: `src/crypto_trade/cup20/runner.py`
- Test: `tests/cup20/test_runner.py`

**Interfaces:**
- Consumes: `Snapshot` (Task 3), `common_risk_scalars` / `apply_risk_scalars` (Task 4), `crypto_trade.tournament.engine_v2.{generate_targets, evaluate_targets, EvaluatorConfig, EvaluationResult}`, `crypto_trade.tournament.risk_policy.RiskPolicy`, `crypto_trade.tournament.protocol.{TargetStrategy, REBALANCE_INSTRUCTION_COLUMN}`.
- Produces: `CandidateRun` (frozen dataclass, fields `targets: pd.DataFrame`, `scaled_targets: pd.DataFrame`, `risk_scalars: pd.Series`, `unscaled: EvaluationResult`, `results: dict[int, EvaluationResult]`); `decision_grid(start: pd.Timestamp, end: pd.Timestamp, *, interval_hours: int = 8) -> tuple[pd.Timestamp, ...]`; `normalise_unit_gross(targets: pd.DataFrame) -> pd.DataFrame`; `evaluator_config(raw: Mapping[str, Any]) -> EvaluatorConfig`; `run_candidate(strategy: TargetStrategy, snapshot: Snapshot, *, decision_times, seed: int, config: EvaluatorConfig, risk_unit: Mapping[str, float], cost_multipliers: Sequence[int] = (1, 2, 3), risk_policy: RiskPolicy | None = None) -> CandidateRun`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_runner.py
import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.runner import (
    CandidateRun,
    decision_grid,
    normalise_unit_gross,
    run_candidate,
)
from crypto_trade.cup20.snapshot import Snapshot
from crypto_trade.tournament.engine_v2 import EvaluatorConfig
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN


class ConstantLong:
    """Hold an equal-weight long book in every eligible symbol."""

    def target_weights(self, context, *, seed):
        if not context.eligible_symbols:
            return {}
        weight = 1.0 / len(context.eligible_symbols)
        return {symbol: weight for symbol in context.eligible_symbols}


class PeekingStrategy:
    """Records how many bar rows it can see at each decision."""

    def __init__(self):
        self.max_close_times = []

    def target_weights(self, context, *, seed):
        latest = max(
            (frame["open_time"].max() for frame in context.bars.values() if len(frame)),
            default=None,
        )
        self.max_close_times.append(latest)
        return None


def _snapshot(days=120, symbols=("AUSDT", "BUSDT", "CUSDT")):
    times = pd.date_range("2021-01-01T00:00:00Z", periods=days * 3, freq="8h")
    rng = np.random.default_rng(5)
    rows = []
    for symbol in symbols:
        price = 100.0 * np.cumprod(1.0 + rng.normal(0.0, 0.01, len(times)))
        rows.append(
            pd.DataFrame(
                {
                    "open_time": times,
                    "symbol": symbol,
                    "open": price,
                    "high": price * 1.01,
                    "low": price * 0.99,
                    "close": price,
                    "volume": 1e6,
                    "quote_volume": 1e8,
                }
            )
        )
    bars = pd.concat(rows, ignore_index=True)
    funding = pd.DataFrame(
        {
            "funding_time": np.tile(times, len(symbols)),
            "symbol": np.repeat(list(symbols), len(times)),
            "funding_rate": 0.0001,
        }
    )
    marks = bars[["open_time", "symbol", "open"]].rename(
        columns={"open_time": "mark_time", "open": "mark_price"}
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]] * len(symbols),
            "symbol": list(symbols),
            "liquidity_rank": list(range(1, len(symbols) + 1)),
            "trailing_quote_volume": [1e8] * len(symbols),
        }
    )
    metadata = pd.DataFrame({"symbol": list(symbols), "contract_type": "PERPETUAL"})
    return Snapshot(bars, funding, marks, membership, metadata, manifest_sha256="test")


def test_decision_grid_is_eight_hourly_and_half_open():
    grid = decision_grid(
        pd.Timestamp("2021-01-01T00:00:00Z"), pd.Timestamp("2021-01-02T00:00:00Z")
    )
    assert grid[0] == pd.Timestamp("2021-01-01T00:00:00Z")
    assert grid[-1] == pd.Timestamp("2021-01-01T16:00:00Z")
    assert len(grid) == 3


def test_normalise_unit_gross_scales_rows_to_unit_absolute_sum():
    index = pd.date_range("2021-01-01T00:00:00Z", periods=3, freq="8h")
    targets = pd.DataFrame(
        {
            "AUSDT": [2.0, 0.0, -1.0],
            "BUSDT": [-2.0, 0.0, 3.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True, True],
        },
        index=index,
    )
    result = normalise_unit_gross(targets)
    assert result.loc[index[0], "AUSDT"] == pytest.approx(0.5)
    assert result.loc[index[1]].drop(REBALANCE_INSTRUCTION_COLUMN).abs().sum() == 0.0
    assert result.loc[index[2]].drop(REBALANCE_INSTRUCTION_COLUMN).abs().sum() == pytest.approx(1.0)


def test_run_candidate_produces_all_three_cost_levels():
    snapshot = _snapshot()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    run = run_candidate(
        ConstantLong(),
        snapshot,
        decision_times=grid,
        seed=42,
        config=EvaluatorConfig(max_gross_exposure=1.0, max_abs_net_exposure=1.0),
        risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
    )
    assert isinstance(run, CandidateRun)
    assert sorted(run.results) == [1, 2, 3]
    for multiplier in (1, 2, 3):
        assert not run.results[multiplier].returns.empty


def test_higher_cost_multiplier_never_improves_net_return():
    snapshot = _snapshot()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    run = run_candidate(
        ConstantLong(),
        snapshot,
        decision_times=grid,
        seed=42,
        config=EvaluatorConfig(max_gross_exposure=1.0, max_abs_net_exposure=1.0),
        risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
    )
    totals = {
        multiplier: (1.0 + result.returns["net_return"]).prod()
        for multiplier, result in run.results.items()
    }
    assert totals[1] >= totals[2] >= totals[3]


def test_strategy_never_sees_a_bar_at_or_after_its_decision_time():
    snapshot = _snapshot()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    strategy = PeekingStrategy()
    run_candidate(
        strategy,
        snapshot,
        decision_times=grid,
        seed=1,
        config=EvaluatorConfig(max_gross_exposure=1.0, max_abs_net_exposure=1.0),
        risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
    )
    for decision, latest in zip(grid, strategy.max_close_times):
        if latest is not None:
            # A bar opening at ``latest`` closes at ``latest + 8h`` and may equal the decision.
            assert latest + pd.Timedelta(hours=8) <= decision
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_runner.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.runner'`

- [ ] **Step 3: Implement the runner**

```python
# src/crypto_trade/cup20/runner.py
"""Two-pass candidate evaluation: unscaled book, then common risk unit at 1x/2x/3x cost."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from crypto_trade.cup20.risk_unit import apply_risk_scalars, common_risk_scalars
from crypto_trade.cup20.snapshot import Snapshot
from crypto_trade.tournament.engine_v2 import (
    EvaluationResult,
    EvaluatorConfig,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN, TargetStrategy
from crypto_trade.tournament.risk_policy import RiskPolicy


@dataclasses.dataclass(frozen=True, slots=True)
class CandidateRun:
    targets: pd.DataFrame
    scaled_targets: pd.DataFrame
    risk_scalars: pd.Series
    unscaled: EvaluationResult
    results: dict[int, EvaluationResult]


def decision_grid(
    start: pd.Timestamp, end: pd.Timestamp, *, interval_hours: int = 8
) -> tuple[pd.Timestamp, ...]:
    """Half-open ``[start, end)`` grid of UTC decision boundaries."""
    times = pd.date_range(
        pd.Timestamp(start).tz_convert("UTC"),
        pd.Timestamp(end).tz_convert("UTC"),
        freq=f"{interval_hours}h",
        inclusive="left",
    )
    return tuple(times)


def normalise_unit_gross(targets: pd.DataFrame) -> pd.DataFrame:
    """Rescale every explicit rebalance row to unit gross, preserving net exposure and signs."""
    result = targets.copy()
    weight_columns = [c for c in result.columns if c != REBALANCE_INSTRUCTION_COLUMN]
    if not weight_columns:
        return result
    gross = result[weight_columns].abs().sum(axis=1)
    divisor = gross.where(gross > 0.0, 1.0)
    result[weight_columns] = result[weight_columns].div(divisor, axis=0)
    return result


def evaluator_config(raw: Mapping[str, Any]) -> EvaluatorConfig:
    """Build the evaluator configuration from the frozen ``[execution]`` table."""
    return EvaluatorConfig(
        interval_hours=int(raw["interval_hours"]),
        initial_equity=float(raw["initial_equity"]),
        taker_fee_bps_per_side=float(raw["taker_fee_bps_per_side"]),
        slippage_bps_per_side=float(raw["slippage_bps_per_side"]),
        max_gross_exposure=float(raw["max_gross_exposure"]),
        max_abs_net_exposure=float(raw["max_abs_net_exposure"]),
        max_symbol_exposure=float(raw["max_symbol_exposure"]),
        max_bar_participation=float(raw["max_bar_participation"]),
    )


def run_candidate(
    strategy: TargetStrategy,
    snapshot: Snapshot,
    *,
    decision_times: Sequence[pd.Timestamp],
    seed: int,
    config: EvaluatorConfig,
    risk_unit: Mapping[str, float],
    cost_multipliers: Sequence[int] = (1, 2, 3),
    risk_policy: RiskPolicy | None = None,
) -> CandidateRun:
    """Generate targets, derive the common risk unit, then score at every cost multiplier."""
    raw_targets = generate_targets(
        strategy,
        snapshot.bars,
        snapshot.funding,
        snapshot.membership,
        decision_times,
        seed=seed,
        interval_hours=config.interval_hours,
    )
    targets = normalise_unit_gross(raw_targets)

    unscaled = evaluate_targets(
        snapshot.bars,
        snapshot.funding,
        snapshot.membership,
        targets,
        mark_prices=snapshot.mark_prices,
        config=config,
        cost_multiplier=1.0,
        risk_policy=risk_policy,
    )
    gross_returns = unscaled.returns["price_pnl"] + unscaled.returns["funding_pnl"]
    scalars = common_risk_scalars(
        gross_returns,
        list(targets.index),
        target_annualized_volatility=float(risk_unit["target_annualized_volatility"]),
        lookback_days=int(risk_unit["lookback_days"]),
        interval_hours=config.interval_hours,
        minimum_scale=float(risk_unit.get("minimum_scale", 0.20)),
        maximum_scale=float(risk_unit.get("maximum_scale", 3.0)),
    )
    scaled_targets = apply_risk_scalars(targets, scalars)

    results = {
        int(multiplier): evaluate_targets(
            snapshot.bars,
            snapshot.funding,
            snapshot.membership,
            scaled_targets,
            mark_prices=snapshot.mark_prices,
            config=config,
            cost_multiplier=float(multiplier),
            risk_policy=risk_policy,
        )
        for multiplier in cost_multipliers
    }
    return CandidateRun(
        targets=targets,
        scaled_targets=scaled_targets,
        risk_scalars=scalars,
        unscaled=unscaled,
        results=results,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_runner.py -q`
Expected: 5 passed

If `evaluate_targets` rejects the mark-price column name, inspect
`crypto_trade.tournament.engine_v2._normalise_mark_prices` and rename the fixture column to match
the schema it requires; do not change the evaluator.

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/runner.py tests/cup20/test_runner.py
git commit -m "Add CUP-20 two-pass candidate runner"
```

---

### Task 6: Window metrics, folds and concentration

**Files:**
- Create: `src/crypto_trade/cup20/metrics.py`
- Test: `tests/cup20/test_metrics.py`

**Interfaces:**
- Consumes: `EvaluationResult` from Task 5.
- Produces: `daily_returns(result: EvaluationResult) -> pd.Series`; `WindowMetrics` (frozen dataclass with float fields `net_sharpe`, `annualized_return`, `annualized_volatility`, `max_drawdown`, `calmar`, `positive_quarter_fraction`, `annualized_turnover`, `gross_edge_bps_per_turnover`, `cost_share_of_positive_gross`, `top5_day_share`, `long_gross_pnl`, `short_gross_pnl`, and int field `trade_count`, plus `as_dict() -> dict[str, float]`); `window_metrics(result: EvaluationResult) -> WindowMetrics`; `fold_sharpes(result: EvaluationResult, folds: Sequence[tuple[str, pd.Timestamp, pd.Timestamp]]) -> dict[str, float]`; `fold_positive_pnl_shares(result, folds) -> dict[str, float]`; `is_folds(is_start: pd.Timestamp, is_end: pd.Timestamp) -> tuple[tuple[str, pd.Timestamp, pd.Timestamp], ...]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_metrics.py
import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.metrics import (
    daily_returns,
    fold_positive_pnl_shares,
    fold_sharpes,
    is_folds,
    window_metrics,
)
from crypto_trade.tournament.engine_v2 import EvaluationResult


def _result(net, *, turnover=0.0, fees=0.0, slippage=0.0, price=None, funding=0.0, events=None):
    index = pd.date_range("2021-01-01T00:00:00Z", periods=len(net), freq="8h", name="timestamp")
    price_series = np.asarray(net, dtype=float) if price is None else np.asarray(price, dtype=float)
    returns = pd.DataFrame(
        {
            "net_return": np.asarray(net, dtype=float),
            "price_pnl": price_series,
            "long_price_pnl": price_series,
            "short_price_pnl": np.zeros(len(net)),
            "funding_pnl": np.full(len(net), funding, dtype=float),
            "long_funding_pnl": np.full(len(net), funding, dtype=float),
            "short_funding_pnl": np.zeros(len(net)),
            "fees": np.full(len(net), fees, dtype=float),
            "slippage": np.full(len(net), slippage, dtype=float),
            "turnover": np.full(len(net), turnover, dtype=float),
        },
        index=index,
    )
    event_frame = (
        pd.DataFrame(events)
        if events is not None
        else pd.DataFrame({"event_type": [], "notional": []})
    )
    return EvaluationResult(returns=returns, positions=pd.DataFrame(), events=event_frame)


def test_daily_returns_compound_within_each_utc_day():
    result = _result([0.01, 0.01, 0.01, -0.02, 0.0, 0.0])
    daily = daily_returns(result)
    assert len(daily) == 2
    assert daily.iloc[0] == pytest.approx(1.01**3 - 1.0)


def test_zero_variance_returns_give_zero_sharpe_not_nan():
    metrics = window_metrics(_result([0.0] * 90))
    assert metrics.net_sharpe == 0.0
    assert math.isfinite(metrics.net_sharpe)


def test_max_drawdown_is_a_positive_magnitude():
    # One move per UTC day: +10%, -20%, +5%. Drawdown is measured on the daily curve.
    bars = [0.10, 0.0, 0.0, -0.20, 0.0, 0.0, 0.05] + [0.0] * 83
    metrics = window_metrics(_result(bars))
    assert metrics.max_drawdown == pytest.approx(0.20)
    assert metrics.max_drawdown > 0.0


def test_calmar_is_zero_when_drawdown_is_zero_and_return_is_not_positive():
    assert window_metrics(_result([0.0] * 90)).calmar == 0.0


def test_gross_edge_per_turnover_is_in_basis_points():
    result = _result([0.001] * 90, turnover=0.01, price=[0.001] * 90)
    metrics = window_metrics(result)
    expected = (0.001 * 90) / (0.01 * 90) * 10_000
    assert metrics.gross_edge_bps_per_turnover == pytest.approx(expected)


def test_cost_share_uses_only_positive_gross_bars():
    result = _result([0.001, -0.002] * 45, fees=0.0001, slippage=0.0, price=[0.001, -0.002] * 45)
    metrics = window_metrics(result)
    positive_gross = 0.001 * 45
    assert metrics.cost_share_of_positive_gross == pytest.approx(0.0001 * 90 / positive_gross)


def test_trade_count_ignores_funding_and_zero_notional_rows():
    events = {
        "event_type": ["trade", "trade", "funding", "risk_reduction"],
        "notional": [100.0, -50.0, 0.0, 25.0],
    }
    metrics = window_metrics(_result([0.0] * 90, events=events))
    assert metrics.trade_count == 3


def test_top5_day_share_is_bounded_and_correct():
    values = [0.0] * 300
    for position in range(5):
        values[position * 3] = 1.0
    metrics = window_metrics(_result(values))
    assert metrics.top5_day_share == pytest.approx(1.0)


def test_is_folds_are_four_blocks_anchored_backward_from_the_cutoff():
    folds = is_folds(pd.Timestamp("2020-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))
    assert [name for name, _, _ in folds] == ["F1", "F2", "F3", "F4"]
    assert folds[0][1] == pd.Timestamp("2020-08-01T00:00:00Z")
    assert folds[0][2] == pd.Timestamp("2021-08-01T00:00:00Z")
    assert folds[-1][2] == pd.Timestamp("2024-08-01T00:00:00Z")


def test_fold_sharpes_and_shares_cover_every_named_fold():
    # Exactly the IS window, so every scored day belongs to exactly one fold and shares sum to 1.
    index = pd.date_range(
        "2020-08-01T00:00:00Z",
        "2024-08-01T00:00:00Z",
        freq="8h",
        inclusive="left",
        name="timestamp",
    )
    rng = np.random.default_rng(2)
    values = rng.normal(0.0002, 0.004, len(index))
    returns = pd.DataFrame(
        {
            "net_return": values,
            "price_pnl": values,
            "long_price_pnl": values,
            "short_price_pnl": np.zeros(len(index)),
            "funding_pnl": np.zeros(len(index)),
            "long_funding_pnl": np.zeros(len(index)),
            "short_funding_pnl": np.zeros(len(index)),
            "fees": np.zeros(len(index)),
            "slippage": np.zeros(len(index)),
            "turnover": np.zeros(len(index)),
        },
        index=index,
    )
    result = EvaluationResult(returns, pd.DataFrame(), pd.DataFrame({"event_type": [],
                                                                     "notional": []}))
    folds = is_folds(pd.Timestamp("2020-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))
    sharpes = fold_sharpes(result, folds)
    shares = fold_positive_pnl_shares(result, folds)
    assert set(sharpes) == {"F1", "F2", "F3", "F4"}
    assert all(math.isfinite(value) for value in sharpes.values())
    assert sum(shares.values()) == pytest.approx(1.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_metrics.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.metrics'`

- [ ] **Step 3: Implement metrics**

```python
# src/crypto_trade/cup20/metrics.py
"""Deterministic window metrics, chronological folds and concentration diagnostics."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.engine_v2 import EvaluationResult

DAYS_PER_YEAR = 365.0
Fold = tuple[str, pd.Timestamp, pd.Timestamp]

# Every metric this module reports MUST be finite. These values are ranked, compared against hard
# floors, and serialised into a hash-chained release artifact, and none of those three consumers
# handles an infinity correctly: the ranking clamp would score a perfect drawdown profile at zero,
# and json.dumps would emit the non-standard "Infinity" token into a published, hashed packet.
UNDEFINED_CALMAR = 1_000.0  # drawdown is zero and return positive: unbounded, reported as capped
UNDEFINED_COST_SHARE = 1.0  # no positive gross PnL at all: reported as costs consuming everything


@dataclasses.dataclass(frozen=True, slots=True)
class WindowMetrics:
    net_sharpe: float
    annualized_return: float
    annualized_volatility: float
    max_drawdown: float
    calmar: float
    positive_quarter_fraction: float
    annualized_turnover: float
    gross_edge_bps_per_turnover: float
    cost_share_of_positive_gross: float
    top5_day_share: float
    long_gross_pnl: float
    short_gross_pnl: float
    trade_count: int

    def as_dict(self) -> dict[str, float]:
        return {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}


def daily_returns(result: EvaluationResult) -> pd.Series:
    """Compound bar net returns within each UTC calendar day."""
    if result.returns.empty:
        return pd.Series(dtype=float)
    net = result.returns["net_return"].astype(float)
    index = pd.DatetimeIndex(net.index).tz_convert("UTC")
    grouped = (1.0 + net).groupby(index.normalize()).prod() - 1.0
    grouped.index = pd.DatetimeIndex(grouped.index)
    return grouped.sort_index()


def is_folds(is_start: pd.Timestamp, is_end: pd.Timestamp) -> tuple[Fold, ...]:
    """Four 12-month blocks anchored backward from the IS cutoff; F1 absorbs any shortfall."""
    start = pd.Timestamp(is_start).tz_convert("UTC")
    end = pd.Timestamp(is_end).tz_convert("UTC")
    interior = [end - pd.DateOffset(years=years) for years in (3, 2, 1)]
    bounds = [start, *(max(edge, start) for edge in interior), end]
    return tuple(
        (f"F{index + 1}", bounds[index], bounds[index + 1]) for index in range(len(bounds) - 1)
    )


def holdout_folds(start: pd.Timestamp, end: pd.Timestamp) -> tuple[Fold, ...]:
    """Four 6-month blocks across the sealed window."""
    start = pd.Timestamp(start).tz_convert("UTC")
    edges = [start + pd.DateOffset(months=6 * step) for step in range(5)]
    edges[-1] = pd.Timestamp(end).tz_convert("UTC")
    return tuple((f"H{index + 1}", edges[index], edges[index + 1]) for index in range(4))


def sharpe(series: pd.Series) -> float:
    """Annualised Sharpe of a daily return series; zero variance yields zero, never NaN."""
    values = series.dropna().to_numpy(dtype=float)
    if values.size < 2:
        return 0.0
    deviation = float(np.std(values, ddof=1))
    if deviation <= 0.0:
        return 0.0
    return float(np.mean(values)) / deviation * math.sqrt(DAYS_PER_YEAR)


def max_drawdown(series: pd.Series) -> float:
    """Maximum peak-to-trough decline of the compounded curve, as a non-negative magnitude."""
    values = series.dropna().to_numpy(dtype=float)
    if values.size == 0:
        return 0.0
    equity = np.cumprod(1.0 + values)
    peaks = np.maximum.accumulate(equity)
    return float(np.max(1.0 - equity / peaks))


def window_metrics(result: EvaluationResult) -> WindowMetrics:
    """Every scalar the floors and the ranking score consume."""
    daily = daily_returns(result)
    frame = result.returns
    days = max(len(daily), 1)
    years = days / DAYS_PER_YEAR

    total_growth = float(np.prod(1.0 + daily.to_numpy(dtype=float))) if len(daily) else 1.0
    annualized_return = total_growth ** (1.0 / years) - 1.0 if total_growth > 0 else -1.0
    drawdown = max_drawdown(daily)
    if drawdown <= 0.0:
        calmar = math.inf if annualized_return > 0.0 else 0.0
    else:
        calmar = annualized_return / drawdown

    naive_index = pd.DatetimeIndex(daily.index).tz_convert("UTC").tz_localize(None)
    quarters = (1.0 + daily).groupby(naive_index.to_period("Q")).prod() - 1.0
    positive_quarter_fraction = (
        float((quarters > 0.0).sum()) / len(quarters) if len(quarters) else 0.0
    )

    gross_bar = frame["price_pnl"].astype(float) + frame["funding_pnl"].astype(float)
    total_turnover = float(frame["turnover"].astype(float).sum())
    gross_total = float(gross_bar.sum())
    positive_gross = float(gross_bar.clip(lower=0.0).sum())
    costs = float(frame["fees"].astype(float).sum() + frame["slippage"].astype(float).sum())

    absolute_daily = daily.abs()
    top5 = float(absolute_daily.nlargest(5).sum())
    absolute_total = float(absolute_daily.sum())

    if result.events.empty or "notional" not in result.events.columns:
        trade_count = 0
    else:
        notional = result.events["notional"].fillna(0.0).astype(float)
        types = result.events.get("event_type", pd.Series("trade", index=result.events.index))
        trade_count = int(((notional.abs() > 0.0) & (types != "funding")).sum())

    return WindowMetrics(
        net_sharpe=sharpe(daily),
        annualized_return=annualized_return,
        annualized_volatility=(
            float(np.std(daily.to_numpy(dtype=float), ddof=1)) * math.sqrt(DAYS_PER_YEAR)
            if len(daily) > 1
            else 0.0
        ),
        max_drawdown=drawdown,
        calmar=calmar,
        positive_quarter_fraction=positive_quarter_fraction,
        annualized_turnover=total_turnover / years if years > 0 else 0.0,
        gross_edge_bps_per_turnover=(
            gross_total / total_turnover * 10_000.0 if total_turnover > 0 else 0.0
        ),
        cost_share_of_positive_gross=(costs / positive_gross if positive_gross > 0 else math.inf),
        top5_day_share=(top5 / absolute_total if absolute_total > 0 else 0.0),
        long_gross_pnl=float(
            frame["long_price_pnl"].astype(float).sum()
            + frame["long_funding_pnl"].astype(float).sum()
        ),
        short_gross_pnl=float(
            frame["short_price_pnl"].astype(float).sum()
            + frame["short_funding_pnl"].astype(float).sum()
        ),
        trade_count=trade_count,
    )


def fold_sharpes(result: EvaluationResult, folds: Sequence[Fold]) -> dict[str, float]:
    """Annualised Sharpe within every named fold."""
    daily = daily_returns(result)
    return {
        name: sharpe(daily[(daily.index >= start) & (daily.index < end)])
        for name, start, end in folds
    }


def fold_positive_pnl_shares(result: EvaluationResult, folds: Sequence[Fold]) -> dict[str, float]:
    """Share of total positive arithmetic daily PnL contributed by each fold."""
    daily = daily_returns(result)
    positive = daily.clip(lower=0.0)
    total = float(positive.sum())
    if total <= 0.0:
        return {name: 0.0 for name, _, _ in folds}
    return {
        name: float(positive[(positive.index >= start) & (positive.index < end)].sum()) / total
        for name, start, end in folds
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_metrics.py -q`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/metrics.py tests/cup20/test_metrics.py
git commit -m "Add CUP-20 window metrics, folds and concentration diagnostics"
```

---

### Task 7: Block bootstrap and trial-adjusted confidence

**Files:**
- Create: `src/crypto_trade/cup20/bootstrap.py`
- Test: `tests/cup20/test_bootstrap.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `circular_block_bootstrap_positive_fraction(daily: pd.Series, *, samples: int = 2000, block_days: int = 10, seed: int = 20260804) -> float`; `trial_adjusted_confidence(positive_fraction: float, trial_count: int) -> float`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_bootstrap.py
import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.bootstrap import (
    circular_block_bootstrap_positive_fraction,
    trial_adjusted_confidence,
)


def _daily(values):
    index = pd.date_range("2021-01-01", periods=len(values), freq="D", tz="UTC")
    return pd.Series(np.asarray(values, dtype=float), index=index)


def test_strongly_positive_series_gives_fraction_one():
    assert circular_block_bootstrap_positive_fraction(_daily([0.01] * 400)) == 1.0


def test_strongly_negative_series_gives_fraction_zero():
    assert circular_block_bootstrap_positive_fraction(_daily([-0.01] * 400)) == 0.0


def test_bootstrap_is_deterministic_for_a_fixed_seed():
    rng = np.random.default_rng(9)
    series = _daily(rng.normal(0.0005, 0.01, 500))
    first = circular_block_bootstrap_positive_fraction(series, seed=123)
    second = circular_block_bootstrap_positive_fraction(series, seed=123)
    assert first == second


def test_different_seeds_are_permitted_to_differ():
    rng = np.random.default_rng(4)
    series = _daily(rng.normal(0.0002, 0.02, 500))
    values = {
        circular_block_bootstrap_positive_fraction(series, seed=seed) for seed in (1, 2, 3, 4, 5)
    }
    assert len(values) >= 1


def test_short_series_is_rejected():
    with pytest.raises(ValueError):
        circular_block_bootstrap_positive_fraction(_daily([0.01] * 5), block_days=10)


def test_trial_adjustment_penalises_multiplicity():
    assert trial_adjusted_confidence(1.0, 12) == 1.0
    assert trial_adjusted_confidence(0.99, 12) == pytest.approx(0.88)
    assert trial_adjusted_confidence(0.95, 12) == pytest.approx(0.40)
    assert trial_adjusted_confidence(0.90, 12) == 0.0
    assert trial_adjusted_confidence(0.99, 1) == pytest.approx(0.99)


def test_trial_adjustment_rejects_bad_inputs():
    with pytest.raises(ValueError):
        trial_adjusted_confidence(1.2, 3)
    with pytest.raises(ValueError):
        trial_adjusted_confidence(0.9, 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_bootstrap.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.bootstrap'`

- [ ] **Step 3: Implement bootstrap and trial adjustment**

```python
# src/crypto_trade/cup20/bootstrap.py
"""Circular block bootstrap and multiplicity-adjusted confidence."""

from __future__ import annotations

import numpy as np
import pandas as pd


def circular_block_bootstrap_positive_fraction(
    daily: pd.Series,
    *,
    samples: int = 2000,
    block_days: int = 10,
    seed: int = 20260804,
) -> float:
    """Fraction of circular block bootstrap resample means that are strictly positive."""
    if samples < 1 or block_days < 1:
        raise ValueError("samples and block_days must be positive")
    values = daily.dropna().to_numpy(dtype=float)
    if values.size < block_days * 2:
        raise ValueError("daily series is too short for the requested block length")
    if not np.isfinite(values).all():
        raise ValueError("daily series contains non-finite values")

    length = values.size
    blocks = int(np.ceil(length / block_days))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, length, size=(samples, blocks))
    offsets = np.arange(block_days)
    indices = (starts[:, :, None] + offsets[None, None, :]) % length
    resampled = values[indices.reshape(samples, blocks * block_days)[:, :length]]
    return float(np.mean(resampled.mean(axis=1) > 0.0))


def trial_adjusted_confidence(positive_fraction: float, trial_count: int) -> float:
    """Penalise the bootstrap confidence by the team's complete accepted-trial count."""
    if not 0.0 <= positive_fraction <= 1.0:
        raise ValueError("positive_fraction must lie in [0, 1]")
    if trial_count < 1:
        raise ValueError("trial_count must be at least 1")
    return max(0.0, min(1.0, 1.0 - trial_count * (1.0 - positive_fraction)))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_bootstrap.py -q`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/bootstrap.py tests/cup20/test_bootstrap.py
git commit -m "Add CUP-20 block bootstrap and trial-adjusted confidence"
```

---

### Task 8: Neighbourhood declaration and per-metric median

**Files:**
- Create: `src/crypto_trade/cup20/neighbourhood.py`
- Test: `tests/cup20/test_neighbourhood.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `NeighbourhoodDeclaration` (frozen dataclass, fields `nominee: Mapping[str, float]`, `points: tuple[Mapping[str, float], ...]`, `coordinates: tuple[str, ...]`, method `validate(minimum_points: int = 7) -> None`, method `all_points() -> tuple[Mapping[str, float], ...]`); `median_metrics(per_point: Sequence[Mapping[str, float]]) -> dict[str, float]`; `positive_point_fraction(per_point: Sequence[Mapping[str, float]]) -> float`; `load_declaration(path: str | Path) -> NeighbourhoodDeclaration`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_neighbourhood.py
import json

import pytest

from crypto_trade.cup20.neighbourhood import (
    NeighbourhoodDeclaration,
    load_declaration,
    median_metrics,
    positive_point_fraction,
)


def _declaration(nominee=None, points=None, coordinates=("lookback", "threshold")):
    nominee = nominee or {"lookback": 60.0, "threshold": 1.0}
    if points is None:
        points = [
            {"lookback": 40.0, "threshold": 1.0},
            {"lookback": 80.0, "threshold": 1.0},
            {"lookback": 60.0, "threshold": 0.8},
            {"lookback": 60.0, "threshold": 1.2},
            {"lookback": 40.0, "threshold": 0.8},
            {"lookback": 80.0, "threshold": 1.2},
        ]
    return NeighbourhoodDeclaration(
        nominee=nominee, points=tuple(points), coordinates=tuple(coordinates)
    )


def test_valid_declaration_passes():
    _declaration().validate()


def test_all_points_includes_the_nominee_exactly_once():
    declaration = _declaration()
    assert len(declaration.all_points()) == 7
    assert declaration.all_points()[0] == declaration.nominee


def test_too_few_points_is_rejected():
    with pytest.raises(ValueError, match="at least"):
        _declaration(points=[{"lookback": 40.0, "threshold": 1.0}]).validate()


def test_coordinate_without_an_upward_variation_is_rejected():
    points = [
        {"lookback": 40.0, "threshold": 1.0},
        {"lookback": 30.0, "threshold": 1.0},
        {"lookback": 60.0, "threshold": 0.8},
        {"lookback": 60.0, "threshold": 1.2},
        {"lookback": 50.0, "threshold": 0.9},
        {"lookback": 20.0, "threshold": 1.1},
    ]
    with pytest.raises(ValueError, match="lookback"):
        _declaration(points=points).validate()


def test_unknown_coordinate_in_a_point_is_rejected():
    points = [
        {"lookback": 40.0, "threshold": 1.0, "sneaky": 1.0},
        {"lookback": 80.0, "threshold": 1.0},
        {"lookback": 60.0, "threshold": 0.8},
        {"lookback": 60.0, "threshold": 1.2},
        {"lookback": 40.0, "threshold": 0.8},
        {"lookback": 80.0, "threshold": 1.2},
    ]
    with pytest.raises(ValueError, match="sneaky"):
        _declaration(points=points).validate()


def test_median_is_computed_per_metric_independently():
    per_point = [
        {"net_sharpe": 1.0, "max_drawdown": 0.30},
        {"net_sharpe": 2.0, "max_drawdown": 0.20},
        {"net_sharpe": 3.0, "max_drawdown": 0.10},
    ]
    assert median_metrics(per_point) == {"net_sharpe": 2.0, "max_drawdown": 0.20}


def test_median_requires_every_point_to_report_the_same_metrics():
    with pytest.raises(ValueError):
        median_metrics([{"a": 1.0}, {"b": 2.0}])


def test_positive_point_fraction_requires_both_return_and_double_cost_sharpe():
    per_point = [
        {"annualized_return": 0.1, "double_cost_sharpe": 0.6},
        {"annualized_return": 0.1, "double_cost_sharpe": -0.1},
        {"annualized_return": -0.1, "double_cost_sharpe": 0.6},
        {"annualized_return": 0.2, "double_cost_sharpe": 0.9},
    ]
    assert positive_point_fraction(per_point) == 0.5


def test_load_declaration_round_trips(tmp_path):
    declaration = _declaration()
    path = tmp_path / "neighbourhood.json"
    path.write_text(
        json.dumps(
            {
                "nominee": dict(declaration.nominee),
                "points": [dict(point) for point in declaration.points],
                "coordinates": list(declaration.coordinates),
            }
        )
    )
    assert load_declaration(path).nominee == declaration.nominee
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_neighbourhood.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.neighbourhood'`

- [ ] **Step 3: Implement neighbourhood scoring**

```python
# src/crypto_trade/cup20/neighbourhood.py
"""Pre-declared parameter neighbourhoods and per-metric median scoring.

A nominated point is the maximum of a noisy surface and is upward-biased by construction. The
median of a neighbourhood declared before evaluation is not.
"""

from __future__ import annotations

import dataclasses
import json
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path


@dataclasses.dataclass(frozen=True, slots=True)
class NeighbourhoodDeclaration:
    nominee: Mapping[str, float]
    points: tuple[Mapping[str, float], ...]
    coordinates: tuple[str, ...]

    def all_points(self) -> tuple[Mapping[str, float], ...]:
        """The nominee first, then every declared neighbourhood point."""
        return (self.nominee, *self.points)

    def validate(self, minimum_points: int = 7) -> None:
        """Reject a neighbourhood that cannot support a robustness claim."""
        if not self.coordinates:
            raise ValueError("a neighbourhood must declare at least one coordinate")
        required = max(minimum_points, 2 * len(self.coordinates) + 1)
        points = self.all_points()
        if len(points) < required:
            raise ValueError(
                f"neighbourhood needs at least {required} points, got {len(points)}"
            )
        for point in points:
            unknown = set(point) - set(self.coordinates)
            if unknown:
                raise ValueError(f"neighbourhood point declares unknown coordinates: {sorted(unknown)}")
            missing = set(self.coordinates) - set(point)
            if missing:
                raise ValueError(f"neighbourhood point omits coordinates: {sorted(missing)}")
        for coordinate in self.coordinates:
            centre = float(self.nominee[coordinate])
            values = [float(point[coordinate]) for point in self.points]
            if not any(value > centre for value in values):
                raise ValueError(f"coordinate {coordinate} has no upward variation")
            if not any(value < centre for value in values):
                raise ValueError(f"coordinate {coordinate} has no downward variation")


def median_metrics(per_point: Sequence[Mapping[str, float]]) -> dict[str, float]:
    """Median of every metric taken independently across the neighbourhood."""
    if not per_point:
        raise ValueError("median_metrics requires at least one point")
    keys = set(per_point[0])
    for point in per_point[1:]:
        if set(point) != keys:
            raise ValueError("every neighbourhood point must report the same metric keys")
    return {key: float(statistics.median(float(point[key]) for point in per_point)) for key in sorted(keys)}


def positive_point_fraction(per_point: Sequence[Mapping[str, float]]) -> float:
    """Fraction of points with positive annualised return AND positive 2x-cost Sharpe."""
    if not per_point:
        raise ValueError("positive_point_fraction requires at least one point")
    passing = sum(
        1
        for point in per_point
        if float(point["annualized_return"]) > 0.0 and float(point["double_cost_sharpe"]) > 0.0
    )
    return passing / len(per_point)


def load_declaration(path: str | Path) -> NeighbourhoodDeclaration:
    """Read a frozen neighbourhood declaration from JSON."""
    payload = json.loads(Path(path).read_text())
    declaration = NeighbourhoodDeclaration(
        nominee={str(k): float(v) for k, v in payload["nominee"].items()},
        points=tuple(
            {str(k): float(v) for k, v in point.items()} for point in payload["points"]
        ),
        coordinates=tuple(str(name) for name in payload["coordinates"]),
    )
    declaration.validate()
    return declaration
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_neighbourhood.py -q`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/neighbourhood.py tests/cup20/test_neighbourhood.py
git commit -m "Add CUP-20 neighbourhood declaration and per-metric median scoring"
```

---

### Task 9: Conjunctive hard floors

**Files:**
- Create: `src/crypto_trade/cup20/qualification.py`
- Test: `tests/cup20/test_qualification.py`

**Interfaces:**
- Consumes: `config.load_config` (Task 1).
- Produces: `GateVector` (frozen dataclass, fields `checks: Mapping[str, bool]`, property `passed: bool`, property `failures: tuple[str, ...]`); `evaluate_floors(scored: Mapping[str, float], *, floors: Mapping[str, Any], declared_roles: Sequence[str], sign_inversion_passes_core: bool, neighbourhood_positive_fraction: float, trial_adjusted_confidence: float, statistics_config: Mapping[str, Any], research_config: Mapping[str, Any]) -> GateVector`. `scored` must contain the keys `net_sharpe`, `double_cost_sharpe`, `triple_cost_sharpe`, `annualized_return`, `double_cost_annualized_return`, `max_drawdown`, `annualized_volatility`, `positive_quarter_fraction`, `positive_fold_count`, `worst_fold_sharpe`, `annualized_turnover`, `gross_edge_bps_per_turnover`, `cost_share_of_positive_gross`, `top5_day_share`, `max_fold_positive_pnl_share`, `trade_count`, `long_gross_pnl`, `short_gross_pnl`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_qualification.py
import pytest

from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.qualification import evaluate_floors

CONFIG = load_config("tournament/cup20/config.toml").raw

PASSING = {
    "net_sharpe": 1.20,
    "double_cost_sharpe": 0.95,
    "triple_cost_sharpe": 0.60,
    "annualized_return": 0.18,
    "double_cost_annualized_return": 0.14,
    "max_drawdown": 0.12,
    "annualized_volatility": 0.10,
    "positive_quarter_fraction": 0.69,
    "positive_fold_count": 4,
    "worst_fold_sharpe": 0.35,
    "annualized_turnover": 14.0,
    "gross_edge_bps_per_turnover": 95.0,
    "cost_share_of_positive_gross": 0.11,
    "top5_day_share": 0.22,
    "max_fold_positive_pnl_share": 0.38,
    "trade_count": 3100,
    "long_gross_pnl": 0.22,
    "short_gross_pnl": 0.15,
}


def _evaluate(**overrides):
    scored = dict(PASSING)
    kwargs = {
        "declared_roles": ("long", "short"),
        "sign_inversion_passes_core": False,
        "neighbourhood_positive_fraction": 0.86,
        "trial_adjusted_confidence": 0.97,
    }
    for key, value in overrides.items():
        if key in kwargs:
            kwargs[key] = value
        else:
            scored[key] = value
    return evaluate_floors(
        scored,
        floors=CONFIG["floors"],
        statistics_config=CONFIG["statistics"],
        research_config=CONFIG["research"],
        **kwargs,
    )


def test_passing_candidate_passes_every_gate():
    gate = _evaluate()
    assert gate.passed
    assert gate.failures == ()


@pytest.mark.parametrize(
    ("override", "expected_failure"),
    [
        ({"net_sharpe": 0.79}, "net_sharpe"),
        ({"double_cost_sharpe": 0.49}, "double_cost_sharpe"),
        ({"triple_cost_sharpe": 0.0}, "triple_cost_sharpe"),
        ({"annualized_return": 0.0}, "annualized_return"),
        ({"max_drawdown": 0.2001}, "max_drawdown"),
        ({"annualized_volatility": 0.0599}, "annualized_volatility"),
        ({"positive_quarter_fraction": 0.49}, "positive_quarter_fraction"),
        ({"positive_fold_count": 2}, "positive_fold_count"),
        ({"worst_fold_sharpe": -0.26}, "worst_fold_sharpe"),
        ({"annualized_turnover": 25.1}, "annualized_turnover"),
        ({"gross_edge_bps_per_turnover": 39.9}, "gross_edge_bps_per_turnover"),
        ({"cost_share_of_positive_gross": 0.31}, "cost_share_of_positive_gross"),
        ({"top5_day_share": 0.36}, "top5_day_share"),
        ({"max_fold_positive_pnl_share": 0.61}, "max_fold_positive_pnl_share"),
        ({"trade_count": 499}, "trade_count"),
        ({"short_gross_pnl": -0.01}, "role_short_gross_pnl"),
        ({"neighbourhood_positive_fraction": 0.69}, "neighbourhood_positive_fraction"),
        ({"trial_adjusted_confidence": 0.89}, "trial_adjusted_confidence"),
        ({"sign_inversion_passes_core": True}, "sign_inversion_not_profitable"),
    ],
)
def test_each_floor_is_individually_binding(override, expected_failure):
    gate = _evaluate(**override)
    assert not gate.passed
    assert expected_failure in gate.failures


def test_undeclared_role_is_not_checked():
    gate = _evaluate(declared_roles=("long",), short_gross_pnl=-5.0)
    assert gate.passed


def test_zero_is_not_positive():
    assert not _evaluate(short_gross_pnl=0.0).passed


def test_missing_metric_fails_closed():
    scored = dict(PASSING)
    del scored["worst_fold_sharpe"]
    with pytest.raises(KeyError):
        evaluate_floors(
            scored,
            floors=CONFIG["floors"],
            statistics_config=CONFIG["statistics"],
            research_config=CONFIG["research"],
            declared_roles=("long", "short"),
            sign_inversion_passes_core=False,
            neighbourhood_positive_fraction=0.86,
            trial_adjusted_confidence=0.97,
        )


def test_non_finite_metric_fails_closed():
    assert not _evaluate(net_sharpe=float("nan")).passed
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_qualification.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.qualification'`

- [ ] **Step 3: Implement the floors**

```python
# src/crypto_trade/cup20/qualification.py
"""Conjunctive hard floors. Aggregate performance never compensates for a failed floor."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any


@dataclasses.dataclass(frozen=True, slots=True)
class GateVector:
    checks: Mapping[str, bool]

    @property
    def passed(self) -> bool:
        return all(self.checks.values())

    @property
    def failures(self) -> tuple[str, ...]:
        return tuple(name for name, ok in self.checks.items() if not ok)


def _finite(value: object) -> float:
    number = float(value)  # type: ignore[arg-type]
    return number if math.isfinite(number) else math.nan


def _at_least(value: object, floor: float) -> bool:
    number = _finite(value)
    return math.isfinite(number) and number >= floor


def _at_most(value: object, ceiling: float) -> bool:
    number = _finite(value)
    return math.isfinite(number) and number <= ceiling


def _positive(value: object) -> bool:
    number = _finite(value)
    return math.isfinite(number) and number > 0.0


def evaluate_floors(
    scored: Mapping[str, float],
    *,
    floors: Mapping[str, Any],
    statistics_config: Mapping[str, Any],
    research_config: Mapping[str, Any],
    declared_roles: Sequence[str],
    sign_inversion_passes_core: bool,
    neighbourhood_positive_fraction: float,
    trial_adjusted_confidence: float,
) -> GateVector:
    """Evaluate every hard floor. A missing key raises; a non-finite value fails."""
    checks: dict[str, bool] = {
        "net_sharpe": _at_least(scored["net_sharpe"], float(floors["net_sharpe"])),
        "double_cost_sharpe": _at_least(
            scored["double_cost_sharpe"], float(floors["double_cost_sharpe"])
        ),
        "triple_cost_sharpe": _positive(scored["triple_cost_sharpe"]),
        "annualized_return": _positive(scored["annualized_return"]),
        "double_cost_annualized_return": _positive(scored["double_cost_annualized_return"]),
        "max_drawdown": _at_most(scored["max_drawdown"], float(floors["max_drawdown"])),
        # The evaluator is unlevered, so the common risk unit cannot scale a very-low-volatility
        # book up to the 10% target. This floor disqualifies an under-risked book instead of
        # rewarding it with an unearned drawdown advantage.
        "annualized_volatility": _at_least(
            scored["annualized_volatility"], float(floors["minimum_realized_volatility"])
        ),
        "positive_quarter_fraction": _at_least(
            scored["positive_quarter_fraction"], float(floors["positive_quarter_fraction"])
        ),
        "positive_fold_count": _at_least(
            scored["positive_fold_count"], float(floors["minimum_positive_folds"])
        ),
        "worst_fold_sharpe": _at_least(
            scored["worst_fold_sharpe"], float(floors["worst_fold_sharpe"])
        ),
        "annualized_turnover": _at_most(
            scored["annualized_turnover"], float(floors["max_annualized_turnover"])
        ),
        "gross_edge_bps_per_turnover": _at_least(
            scored["gross_edge_bps_per_turnover"],
            float(floors["min_gross_edge_bps_per_turnover"]),
        ),
        "cost_share_of_positive_gross": _at_most(
            scored["cost_share_of_positive_gross"],
            float(floors["max_cost_share_of_positive_gross"]),
        ),
        "top5_day_share": _at_most(scored["top5_day_share"], float(floors["max_top5_day_share"])),
        "max_fold_positive_pnl_share": _at_most(
            scored["max_fold_positive_pnl_share"],
            float(floors["max_fold_share_of_positive_pnl"]),
        ),
        "trade_count": _at_least(scored["trade_count"], float(floors["minimum_trades"])),
        "neighbourhood_positive_fraction": _at_least(
            neighbourhood_positive_fraction,
            float(research_config["neighbourhood_positive_fraction"]),
        ),
        "trial_adjusted_confidence": _at_least(
            trial_adjusted_confidence,
            float(statistics_config["minimum_trial_adjusted_confidence"]),
        ),
        "sign_inversion_not_profitable": not sign_inversion_passes_core,
    }
    # Touch every role metric so a missing key still raises, then gate only declared roles.
    role_values = {
        "long": scored["long_gross_pnl"],
        "short": scored["short_gross_pnl"],
    }
    for role in declared_roles:
        checks[f"role_{role}_gross_pnl"] = _positive(role_values[role])
    return GateVector(checks=checks)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_qualification.py -q`
Expected: 22 passed

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/qualification.py tests/cup20/test_qualification.py
git commit -m "Add CUP-20 conjunctive hard floors"
```

---

### Task 10: Ranking score and selection

**Files:**
- Create: `src/crypto_trade/cup20/scoring.py`
- Test: `tests/cup20/test_scoring.py`

**Interfaces:**
- Consumes: `GateVector` (Task 9).
- Produces: `robustness_score(scored: Mapping[str, float], *, drawdown_floor: float) -> float`; `RankedEntry` (frozen dataclass, fields `team_id: str`, `candidate_id: str`, `score: float`, `scored: Mapping[str, float]`); `rank_entries(entries: Sequence[RankedEntry]) -> tuple[RankedEntry, ...]`; `select_advancing(entries: Sequence[RankedEntry], *, slots: int) -> tuple[RankedEntry, ...]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_scoring.py
import pytest

from crypto_trade.cup20.scoring import RankedEntry, rank_entries, robustness_score, select_advancing

BASE = {
    "worst_fold_sharpe": 0.75,
    "median_fold_sharpe": 1.00,
    "max_drawdown": 0.05,
    "calmar": 1.50,
    "positive_quarter_fraction": 0.875,
    "trial_adjusted_confidence": 1.00,
}


def test_perfect_candidate_scores_one_hundred():
    assert robustness_score(BASE, drawdown_floor=0.20) == pytest.approx(100.0)


def test_floor_candidate_scores_zero():
    worst = {
        "worst_fold_sharpe": -0.25,
        "median_fold_sharpe": 0.25,
        "max_drawdown": 0.20,
        "calmar": 0.0,
        "positive_quarter_fraction": 0.50,
        "trial_adjusted_confidence": 0.90,
    }
    assert robustness_score(worst, drawdown_floor=0.20) == pytest.approx(0.0)


def test_components_are_clamped_and_cannot_exceed_their_weight():
    generous = dict(BASE)
    generous.update({"worst_fold_sharpe": 99.0, "calmar": 99.0, "max_drawdown": 0.0})
    assert robustness_score(generous, drawdown_floor=0.20) == pytest.approx(100.0)


def test_generalisation_outweighs_drawdown():
    consistent = dict(BASE, worst_fold_sharpe=0.75, max_drawdown=0.19, calmar=0.1)
    shallow = dict(BASE, worst_fold_sharpe=-0.25, median_fold_sharpe=0.25, max_drawdown=0.0)
    assert robustness_score(consistent, drawdown_floor=0.20) > robustness_score(
        shallow, drawdown_floor=0.20
    )


def test_holdout_drawdown_floor_rebases_the_component():
    scored = dict(BASE, max_drawdown=0.20)
    assert robustness_score(scored, drawdown_floor=0.25) > robustness_score(
        scored, drawdown_floor=0.20
    )


def test_ranking_is_by_descending_score_then_tie_breaks():
    entries = [
        RankedEntry("team-03", "c3", 50.0, dict(BASE, max_drawdown=0.10, worst_fold_sharpe=0.5,
                                                annualized_turnover=10.0)),
        RankedEntry("team-01", "c1", 50.0, dict(BASE, max_drawdown=0.08, worst_fold_sharpe=0.5,
                                                annualized_turnover=10.0)),
        RankedEntry("team-02", "c2", 70.0, dict(BASE, max_drawdown=0.15, worst_fold_sharpe=0.5,
                                                annualized_turnover=10.0)),
    ]
    ordered = [entry.team_id for entry in rank_entries(entries)]
    assert ordered == ["team-02", "team-01", "team-03"]


def test_tie_break_falls_through_to_team_id():
    scored = dict(BASE, annualized_turnover=10.0)
    entries = [
        RankedEntry("team-05", "c5", 50.0, dict(scored)),
        RankedEntry("team-02", "c2", 50.0, dict(scored)),
    ]
    assert [entry.team_id for entry in rank_entries(entries)] == ["team-02", "team-05"]


def test_select_advancing_never_backfills_beyond_the_qualifier_pool():
    scored = dict(BASE, annualized_turnover=10.0)
    entries = [RankedEntry("team-01", "c1", 60.0, dict(scored))]
    assert len(select_advancing(entries, slots=3)) == 1


def test_select_advancing_truncates_to_the_declared_slots():
    scored = dict(BASE, annualized_turnover=10.0)
    entries = [
        RankedEntry(f"team-{index:02d}", f"c{index}", float(90 - index), dict(scored))
        for index in range(1, 8)
    ]
    advancing = select_advancing(entries, slots=3)
    assert [entry.team_id for entry in advancing] == ["team-01", "team-02", "team-03"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_scoring.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.scoring'`

- [ ] **Step 3: Implement scoring**

```python
# src/crypto_trade/cup20/scoring.py
"""Generalisation-shaped ranking score.

Fifty-eight of one hundred points reward consistency across chronological folds, thirty-five
reward drawdown control, and seven reward multiplicity honesty. The score ranks; it never vetoes.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence


def _clamp(value: float) -> float:
    """Clamp a normalised score component to ``[0, 1]``.

    Every component is oriented so that larger is better, so a positive infinity means "as good
    as this term can be" and must earn full credit, not zero. NaN and negative infinity earn
    nothing. Metrics are expected to be finite by the time they arrive here — this is
    defence in depth, not a licence for upstream to emit infinities.
    """
    if math.isnan(value):
        return 0.0
    if value == math.inf:
        return 1.0
    if value == -math.inf:
        return 0.0
    return min(1.0, max(0.0, value))


@dataclasses.dataclass(frozen=True, slots=True)
class RankedEntry:
    team_id: str
    candidate_id: str
    score: float
    scored: Mapping[str, float]


def robustness_score(scored: Mapping[str, float], *, drawdown_floor: float) -> float:
    """Compute ``G`` in ``[0, 100]`` from the neighbourhood-median metric vector."""
    if drawdown_floor <= 0:
        raise ValueError("drawdown_floor must be positive")
    drawdown_span = drawdown_floor - 0.05
    if drawdown_span <= 0:
        raise ValueError("drawdown_floor must exceed the 0.05 full-credit level")
    return (
        30.0 * _clamp((float(scored["worst_fold_sharpe"]) + 0.25) / 1.00)
        + 20.0 * _clamp((float(scored["median_fold_sharpe"]) - 0.25) / 0.75)
        + 20.0 * _clamp((drawdown_floor - float(scored["max_drawdown"])) / drawdown_span)
        + 15.0 * _clamp(float(scored["calmar"]) / 1.50)
        + 8.0 * _clamp((float(scored["positive_quarter_fraction"]) - 0.50) / 0.375)
        + 7.0 * _clamp((float(scored["trial_adjusted_confidence"]) - 0.90) / 0.10)
    )


def rank_entries(entries: Sequence[RankedEntry]) -> tuple[RankedEntry, ...]:
    """Descending score, then lower drawdown, higher worst fold, lower turnover, team id."""
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                -entry.score,
                float(entry.scored["max_drawdown"]),
                -float(entry.scored["worst_fold_sharpe"]),
                float(entry.scored["annualized_turnover"]),
                entry.team_id,
            ),
        )
    )


def select_advancing(entries: Sequence[RankedEntry], *, slots: int) -> tuple[RankedEntry, ...]:
    """Advance at most ``slots`` qualifiers. An empty slot is never backfilled."""
    if slots < 1:
        raise ValueError("slots must be positive")
    return rank_entries(entries)[:slots]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_scoring.py -q`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/scoring.py tests/cup20/test_scoring.py
git commit -m "Add CUP-20 generalisation-shaped ranking score"
```

---

### Task 11: Append-only hash-chained journal

**Files:**
- Create: `src/crypto_trade/cup20/journal.py`
- Test: `tests/cup20/test_journal.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `append_record(path: str | Path, event_type: str, payload: Mapping[str, Any]) -> str` returning the new record digest; `read_records(path: str | Path) -> tuple[dict[str, Any], ...]`; `verify_chain(path: str | Path) -> int` returning the record count and raising `ValueError` on any break; `accepted_trial_count(path: str | Path, team_id: str) -> int`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_journal.py
import json

import pytest

from crypto_trade.cup20.journal import (
    accepted_trial_count,
    append_record,
    read_records,
    verify_chain,
)


def test_first_record_has_a_null_parent(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01", "candidate_id": "c1"})
    records = read_records(path)
    assert records[0]["previous_sha256"] is None
    assert records[0]["sequence"] == 1


def test_each_record_chains_to_its_predecessor(tmp_path):
    path = tmp_path / "journal.jsonl"
    first = append_record(path, "trial_accepted", {"team_id": "team-01"})
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    records = read_records(path)
    assert records[1]["previous_sha256"] == first
    assert verify_chain(path) == 2


def test_tampering_with_a_payload_breaks_the_chain(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01", "note": "original"})
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    lines = path.read_text().splitlines()
    record = json.loads(lines[0])
    record["payload"]["note"] = "tampered"
    lines[0] = json.dumps(record, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="record digest"):
        verify_chain(path)


def test_deleting_a_record_breaks_the_chain(tmp_path):
    path = tmp_path / "journal.jsonl"
    for _ in range(3):
        append_record(path, "trial_accepted", {"team_id": "team-01"})
    lines = path.read_text().splitlines()
    path.write_text("\n".join([lines[0], lines[2]]) + "\n")
    with pytest.raises(ValueError):
        verify_chain(path)


def test_accepted_trial_count_is_per_team(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    append_record(path, "trial_accepted", {"team_id": "team-02"})
    append_record(path, "nomination", {"team_id": "team-01"})
    assert accepted_trial_count(path, "team-01") == 2
    assert accepted_trial_count(path, "team-02") == 1
    assert accepted_trial_count(path, "team-09") == 0


def test_records_are_byte_stable_for_identical_payloads(tmp_path):
    digests = []
    for name in ("a", "b"):
        path = tmp_path / f"{name}.jsonl"
        digests.append(append_record(path, "trial_accepted", {"z": 1, "a": 2}))
    assert digests[0] == digests[1]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_journal.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.journal'`

- [ ] **Step 3: Implement the journal**

```python
# src/crypto_trade/cup20/journal.py
"""Append-only, hash-chained research journal.

A trial is consumed when it is accepted, before market data are opened, even if the run later
crashes or is abandoned. Records are never deleted, renumbered, replaced or squashed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "cup20-research-journal-v1"


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _record_digest(record: Mapping[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "record_sha256"}
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


def read_records(path: str | Path) -> tuple[dict[str, Any], ...]:
    """Every record in file order."""
    journal = Path(path)
    if not journal.exists():
        return ()
    return tuple(json.loads(line) for line in journal.read_text().splitlines() if line.strip())


def append_record(path: str | Path, event_type: str, payload: Mapping[str, Any]) -> str:
    """Append one chained record and return its digest."""
    journal = Path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    existing = read_records(journal)
    record = {
        "schema_version": SCHEMA_VERSION,
        "sequence": len(existing) + 1,
        "event_type": event_type,
        "payload": dict(payload),
        "previous_sha256": existing[-1]["record_sha256"] if existing else None,
    }
    record["record_sha256"] = _record_digest(record)
    with journal.open("a", encoding="utf-8") as handle:
        handle.write(_canonical(record) + "\n")
    return str(record["record_sha256"])


def verify_chain(path: str | Path) -> int:
    """Verify sequence numbers, parent links and digests. Return the record count."""
    records = read_records(path)
    previous: str | None = None
    for index, record in enumerate(records, start=1):
        if record.get("sequence") != index:
            raise ValueError(f"journal sequence break at position {index}")
        if record.get("previous_sha256") != previous:
            raise ValueError(f"journal parent link break at sequence {index}")
        if _record_digest(record) != record.get("record_sha256"):
            raise ValueError(f"journal record digest mismatch at sequence {index}")
        previous = str(record["record_sha256"])
    return len(records)


def accepted_trial_count(path: str | Path, team_id: str) -> int:
    """Count accepted material trials for one team."""
    return sum(
        1
        for record in read_records(path)
        if record.get("event_type") == "trial_accepted"
        and record.get("payload", {}).get("team_id") == team_id
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_journal.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/journal.py tests/cup20/test_journal.py
git commit -m "Add CUP-20 append-only hash-chained research journal"
```

---

### Task 12: Source archive and blindness pre-flight scan

**Files:**
- Create: `src/crypto_trade/cup20/archive.py`
- Test: `tests/cup20/test_archive.py`

**Interfaces:**
- Consumes: `NeighbourhoodDeclaration` from Task 8.
- Produces: `archive_directory(source_root: str | Path, destination_root: str | Path) -> str` returning the bundle digest and writing `<destination_root>/<digest>.tar` plus `<digest>.json`; `bundle_digest(source_root: str | Path) -> str`; `FORBIDDEN_PATTERNS: tuple[str, ...]`; `scan_for_blindness_violations(source_root: str | Path, *, team_id: str | None = None) -> tuple[str, ...]` returning `"<relative_path>:<line_number>:<pattern>"` strings; and `verify_neighbourhood_coordinates(source_root, declaration, *, entrypoint: str = "strategy.py") -> tuple[str, ...]` returning violation strings.

**Why `verify_neighbourhood_coordinates` is here.** Design spec §7.2 requires that "every coordinate
maps to an identically named numeric material parameter in the frozen source." Task 8's
`NeighbourhoodDeclaration.validate()` can only check internal self-consistency — that the declared
coordinate list matches the points' keys. It cannot know whether `lookback` is a real parameter of
the team's strategy or a name invented to satisfy the count. Without this check a team can declare
fictional coordinates, pass every internal gate, and claim a plateau it never explored. This module
already owns "what is in the frozen source", so the check belongs here.

The check parses the frozen entrypoint with `ast` — never imports or executes it — collects every
module-level numeric assignment, numeric keyword default and dataclass field default, then requires
for each declared coordinate that (1) a parameter of exactly that name exists, and (2) the nominee's
declared value equals the value in the frozen source. Requirement (2) is what forces the nominated
point to actually be what the frozen code does, rather than a favourable point the team labelled as
its nominee.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_archive.py
from pathlib import Path

from crypto_trade.cup20.archive import (
    archive_directory,
    bundle_digest,
    scan_for_blindness_violations,
)


def _team(tmp_path: Path, body: str) -> Path:
    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    (root / "strategy.py").write_text(body)
    return root


def test_bundle_digest_is_stable_and_content_sensitive(tmp_path):
    first = _team(tmp_path / "a", "x = 1\n")
    second = _team(tmp_path / "b", "x = 1\n")
    third = _team(tmp_path / "c", "x = 2\n")
    assert bundle_digest(first) == bundle_digest(second)
    assert bundle_digest(first) != bundle_digest(third)


def test_archive_directory_writes_tar_and_sidecar(tmp_path):
    root = _team(tmp_path / "src", "x = 1\n")
    digest = archive_directory(root, tmp_path / "archives")
    assert (tmp_path / "archives" / f"{digest}.tar").exists()
    assert (tmp_path / "archives" / f"{digest}.json").exists()


def test_sealed_data_path_is_a_violation(tmp_path):
    root = _team(tmp_path, "PATH = 'data/cup20/sealed/bars.parquet'\n")
    violations = scan_for_blindness_violations(root)
    assert any("data/cup20/sealed" in violation for violation in violations)


def test_post_cutoff_date_literal_is_a_violation(tmp_path):
    root = _team(tmp_path, "CUTOFF = '2025-03-01'\n")
    assert scan_for_blindness_violations(root)


def test_prior_tournament_directory_is_a_violation(tmp_path):
    root = _team(tmp_path, "import crypto_trade.tournament.top40_v4\n")
    assert scan_for_blindness_violations(root)


def test_another_team_directory_is_a_violation(tmp_path):
    root = _team(tmp_path, "OTHER = 'tournament/cup20/teams/team-07/candidates'\n")
    assert scan_for_blindness_violations(root, team_id="team-01")


def test_own_team_directory_is_allowed(tmp_path):
    root = _team(tmp_path, "SELF = 'tournament/cup20/teams/team-01/candidates'\n")
    assert scan_for_blindness_violations(root, team_id="team-01") == ()


def test_declared_coordinate_absent_from_frozen_source_is_a_violation(tmp_path):
    from crypto_trade.cup20.archive import verify_neighbourhood_coordinates
    from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

    root = _team(tmp_path, "LOOKBACK = 60\nTHRESHOLD = 1.0\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0, "INVENTED": 3.0},
        points=({"LOOKBACK": 40.0, "INVENTED": 2.0},),
        coordinates=("LOOKBACK", "INVENTED"),
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("INVENTED" in violation for violation in violations)
    assert not any("LOOKBACK" in violation for violation in violations)


def test_nominee_value_must_match_the_frozen_source(tmp_path):
    from crypto_trade.cup20.archive import verify_neighbourhood_coordinates
    from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

    root = _team(tmp_path, "LOOKBACK = 60\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 90.0},
        points=({"LOOKBACK": 40.0},),
        coordinates=("LOOKBACK",),
    )
    assert verify_neighbourhood_coordinates(root, declaration)


def test_matching_coordinates_and_values_have_no_violations(tmp_path):
    from crypto_trade.cup20.archive import verify_neighbourhood_coordinates
    from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

    root = _team(tmp_path, "LOOKBACK = 60\nTHRESHOLD = 1.5\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0, "THRESHOLD": 1.5},
        points=({"LOOKBACK": 40.0, "THRESHOLD": 1.2},),
        coordinates=("LOOKBACK", "THRESHOLD"),
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_verify_never_imports_the_frozen_source(tmp_path):
    from crypto_trade.cup20.archive import verify_neighbourhood_coordinates
    from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

    # Importing this module would raise; parsing it must not.
    root = _team(tmp_path, "LOOKBACK = 60\nraise RuntimeError('team code must never execute')\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_clean_source_has_no_violations(tmp_path):
    root = _team(
        tmp_path,
        "from crypto_trade.tournament.protocol import DecisionContext\n"
        "LOOKBACK = 60\n"
        "IS_ERA_NOTE = '2023-01-01 was a chop regime, 2024-07-31 is the last IS day'\n",
    )
    assert scan_for_blindness_violations(root, team_id="team-01") == ()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_archive.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.archive'`

- [ ] **Step 3: Implement archive and scan**

```python
# src/crypto_trade/cup20/archive.py
"""Reproducible source archives and the blindness pre-flight scan."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import tarfile
from pathlib import Path

from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

FORBIDDEN_PATTERNS: tuple[str, ...] = (
    # Sealed and organiser-only surfaces.
    r"data/cup20/sealed",
    r"tournament/cup20/private",
    r"reports-cup20/holdout",
    # Prior-tournament evidence of any kind.
    r"crypto_trade\.tournament\.top40",
    r"tournament/top40",
    r"reports-top40",
    r"tournament/crypto/results",
    r"diary-portfolio-mn",
    # Any calendar date on or after the IS cutoff of 2024-08-01.
    r"(?<!\d)2024-(?:0[89]|1[0-2])-\d{2}",
    r"(?<!\d)20(?:2[5-9]|[3-9]\d)-\d{2}-\d{2}",
)
_COMPILED = tuple((pattern, re.compile(pattern)) for pattern in FORBIDDEN_PATTERNS)
_SCANNED_SUFFIXES = frozenset({".py", ".toml", ".json", ".md", ".cfg", ".txt", ".yaml", ".yml"})
_TEAM_DIRECTORY = re.compile(r"tournament/cup20/teams/(team-\d{2})")


def _files(source_root: Path) -> list[Path]:
    return sorted(
        path
        for path in source_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )


def bundle_digest(source_root: str | Path) -> str:
    """Digest file names and bytes into one reproducible bundle identity."""
    root = Path(source_root).resolve()
    digest = hashlib.sha256()
    for path in _files(root):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\x00")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\x00")
    return digest.hexdigest()


def archive_directory(source_root: str | Path, destination_root: str | Path) -> str:
    """Write a deterministic tar of the source tree, named by its bundle digest."""
    root = Path(source_root).resolve()
    destination = Path(destination_root)
    destination.mkdir(parents=True, exist_ok=True)
    digest = bundle_digest(root)
    archive_path = destination / f"{digest}.tar"
    with tarfile.open(archive_path, "w", format=tarfile.PAX_FORMAT) as archive:
        for path in _files(root):
            info = archive.gettarinfo(str(path), arcname=path.relative_to(root).as_posix())
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with path.open("rb") as handle:
                archive.addfile(info, handle)
    sidecar = {
        "bundle_sha256": digest,
        "files": [path.relative_to(root).as_posix() for path in _files(root)],
    }
    (destination / f"{digest}.json").write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n")
    return digest


def _frozen_numeric_parameters(path: Path) -> dict[str, float]:
    """Collect module-level numeric parameters from a frozen entrypoint by parsing, never importing.

    Team code is untrusted and must never execute during verification, so this uses ``ast`` and
    reads module-level assignments, annotated assignments, dataclass field defaults and numeric
    keyword defaults on function signatures.
    """
    tree = ast.parse(path.read_text())
    found: dict[str, float] = {}

    def _numeric(node: ast.AST) -> float | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if isinstance(node.value, bool):
                return None
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            inner = _numeric(node.operand)
            return None if inner is None else -inner
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = _numeric(node.value)
            if value is not None:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        found.setdefault(target.id, value)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            value = _numeric(node.value)
            if value is not None and isinstance(node.target, ast.Name):
                found.setdefault(node.target.id, value)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            names = [arg.arg for arg in args.args + args.kwonlyargs]
            defaults = list(args.defaults) + list(args.kw_defaults)
            for name, default in zip(names[-len(defaults) :] if defaults else [], defaults):
                if default is None:
                    continue
                value = _numeric(default)
                if value is not None:
                    found.setdefault(name, value)
    return found


def verify_neighbourhood_coordinates(
    source_root: str | Path,
    declaration: NeighbourhoodDeclaration,
    *,
    entrypoint: str = "strategy.py",
) -> tuple[str, ...]:
    """Check every declared coordinate is a real numeric parameter of the frozen source.

    Design spec section 7.2 requires that every coordinate map to an identically named numeric
    material parameter in the frozen source. Internal self-consistency is not enough: without this,
    a team can declare a fictional coordinate, satisfy every other gate, and claim a plateau across
    a surface it never explored. Requiring the nominee's value to match the frozen source also
    forces the nominated point to be what the frozen code actually does.
    """
    entry = Path(source_root) / entrypoint
    if not entry.exists():
        return (f"{entrypoint}:missing-entrypoint",)
    parameters = _frozen_numeric_parameters(entry)
    violations: list[str] = []
    for coordinate in declaration.coordinates:
        if coordinate not in parameters:
            violations.append(f"{entrypoint}:{coordinate}:absent-from-frozen-source")
            continue
        declared = float(declaration.nominee[coordinate])
        frozen = parameters[coordinate]
        if not math.isclose(declared, frozen, rel_tol=1e-9, abs_tol=1e-12):
            violations.append(
                f"{entrypoint}:{coordinate}:nominee-{declared}-differs-from-frozen-{frozen}"
            )
    return tuple(violations)


def scan_for_blindness_violations(
    source_root: str | Path, *, team_id: str | None = None
) -> tuple[str, ...]:
    """Report every forbidden reference in a team's frozen source tree.

    A team may name its own directory; naming any other team's directory is a violation.
    """
    root = Path(source_root).resolve()
    violations: list[str] = []
    for path in _files(root):
        if path.suffix not in _SCANNED_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
            for pattern, compiled in _COMPILED:
                if compiled.search(line):
                    violations.append(f"{relative}:{number}:{pattern}")
            for match in _TEAM_DIRECTORY.finditer(line):
                if match.group(1) != team_id:
                    violations.append(f"{relative}:{number}:foreign-team-directory")
    return tuple(violations)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_archive.py -q`
Expected: 7 passed

If the date-literal patterns over-match a legitimate IS-era date, tighten them so that any date on
or after `2024-08-01` matches and every earlier date does not; add the failing example as a
regression test rather than loosening the scan.

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/archive.py tests/cup20/test_archive.py
git commit -m "Add CUP-20 source archive and blindness pre-flight scan"
```

---

### Task 13: Result packets and atomic release

**Files:**
- Create: `src/crypto_trade/cup20/report.py`
- Test: `tests/cup20/test_report.py`

**Interfaces:**
- Consumes: `CandidateRun` (Task 5); `Fold`, `daily_returns`, `window_metrics`, `fold_sharpes` (Task 6).
- Produces: `build_packet(run: CandidateRun, *, team_id: str, candidate_id: str, folds, identity: Mapping[str, str], output_dir: str | Path) -> dict[str, Any]`; `write_manifest(packets: Sequence[Mapping[str, Any]], *, path: str | Path) -> str`; `atomic_release(staging_root: str | Path, release_root: str | Path) -> None`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cup20/test_report.py
import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.metrics import is_folds
from crypto_trade.cup20.report import atomic_release, build_packet, write_manifest
from crypto_trade.cup20.runner import CandidateRun
from crypto_trade.tournament.engine_v2 import EvaluationResult


def _run():
    index = pd.date_range("2020-08-01T00:00:00Z", periods=4400, freq="8h", name="timestamp")
    rng = np.random.default_rng(1)
    values = rng.normal(0.0002, 0.003, len(index))
    frame = pd.DataFrame(
        {
            "net_return": values,
            "price_pnl": values,
            "long_price_pnl": values,
            "short_price_pnl": np.zeros(len(index)),
            "funding_pnl": np.zeros(len(index)),
            "long_funding_pnl": np.zeros(len(index)),
            "short_funding_pnl": np.zeros(len(index)),
            "fees": np.zeros(len(index)),
            "slippage": np.zeros(len(index)),
            "turnover": np.full(len(index), 0.01),
        },
        index=index,
    )
    events = pd.DataFrame({"event_type": ["trade"] * 600, "notional": [10.0] * 600})
    result = EvaluationResult(frame, pd.DataFrame(), events)
    return CandidateRun(
        targets=pd.DataFrame(),
        scaled_targets=pd.DataFrame(),
        risk_scalars=pd.Series(dtype=float),
        unscaled=result,
        results={1: result, 2: result, 3: result},
    )


def test_packet_contains_every_cost_level_and_fold(tmp_path):
    folds = is_folds(pd.Timestamp("2020-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))
    packet = build_packet(
        _run(),
        team_id="team-01",
        candidate_id="c1",
        folds=folds,
        identity={"strategy_sha256": "a" * 64},
        output_dir=tmp_path,
    )
    assert set(packet["cost_levels"]) == {"1", "2", "3"}
    assert set(packet["fold_sharpes"]) == {"F1", "F2", "F3", "F4"}
    assert packet["identity"]["strategy_sha256"] == "a" * 64
    assert (tmp_path / "daily_returns.csv").exists()


def test_packet_records_artifact_digests(tmp_path):
    folds = is_folds(pd.Timestamp("2020-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))
    packet = build_packet(
        _run(),
        team_id="team-01",
        candidate_id="c1",
        folds=folds,
        identity={},
        output_dir=tmp_path,
    )
    assert len(packet["artifact_sha256"]["daily_returns"]) == 64


def test_manifest_digest_changes_with_packet_content(tmp_path):
    first = write_manifest([{"team_id": "team-01", "score": 1.0}], path=tmp_path / "a.json")
    second = write_manifest([{"team_id": "team-01", "score": 2.0}], path=tmp_path / "b.json")
    assert first != second


def test_atomic_release_moves_the_whole_bundle(tmp_path):
    staging = tmp_path / "staging"
    (staging / "team-01").mkdir(parents=True)
    (staging / "team-01" / "summary.json").write_text("{}")
    release = tmp_path / "release"
    atomic_release(staging, release)
    assert (release / "team-01" / "summary.json").exists()
    assert not staging.exists()


def test_atomic_release_refuses_to_overwrite_an_existing_release(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    release = tmp_path / "release"
    release.mkdir()
    with pytest.raises(FileExistsError):
        atomic_release(staging, release)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_report.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.report'`

- [ ] **Step 3: Implement reporting**

```python
# src/crypto_trade/cup20/report.py
"""Result packets, manifests and the single atomic release."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from crypto_trade.cup20.metrics import Fold, daily_returns, fold_sharpes, window_metrics
from crypto_trade.cup20.runner import CandidateRun


def build_packet(
    run: CandidateRun,
    *,
    team_id: str,
    candidate_id: str,
    folds: Sequence[Fold],
    identity: Mapping[str, str],
    output_dir: str | Path,
) -> dict[str, Any]:
    """Write per-cost artifacts and return the summary packet."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, str] = {}
    cost_levels: dict[str, dict[str, float]] = {}
    for multiplier, result in sorted(run.results.items()):
        metrics = window_metrics(result)
        cost_levels[str(multiplier)] = metrics.as_dict()
        name = "daily_returns" if multiplier == 1 else f"daily_returns_{multiplier}x"
        path = directory / f"{name}.csv"
        daily_returns(result).to_csv(path, header=["daily_return"])
        artifacts[name] = hashlib.sha256(path.read_bytes()).hexdigest()

    base = run.results[min(run.results)]
    packet = {
        "team_id": team_id,
        "candidate_id": candidate_id,
        "identity": dict(identity),
        "cost_levels": cost_levels,
        "fold_sharpes": fold_sharpes(run.results[2] if 2 in run.results else base, folds),
        "risk_scalar_summary": {
            "count": int(run.risk_scalars.size),
            "median": float(run.risk_scalars.median()) if run.risk_scalars.size else 0.0,
            "minimum": float(run.risk_scalars.min()) if run.risk_scalars.size else 0.0,
            "maximum": float(run.risk_scalars.max()) if run.risk_scalars.size else 0.0,
        },
        "artifact_sha256": artifacts,
    }
    # allow_nan=False: a non-finite metric must fail loudly here rather than silently emitting
    # the non-standard "Infinity" token into a hash-chained, publicly released artifact.
    (directory / "summary.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return packet


def write_manifest(packets: Sequence[Mapping[str, Any]], *, path: str | Path) -> str:
    """Write the release manifest and return its digest."""
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(list(packets), indent=2, sort_keys=True, allow_nan=False) + "\n"
    manifest_path.write_text(body)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def atomic_release(staging_root: str | Path, release_root: str | Path) -> None:
    """Publish a fully built bundle in one rename. There is no partial publication."""
    staging = Path(staging_root)
    release = Path(release_root)
    if release.exists():
        raise FileExistsError(f"release path already exists: {release}")
    if not staging.exists():
        raise FileNotFoundError(f"staging path does not exist: {staging}")
    release.parent.mkdir(parents=True, exist_ok=True)
    staging.rename(release)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/cup20/test_report.py -q`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/report.py tests/cup20/test_report.py
git commit -m "Add CUP-20 result packets and atomic release"
```

---

### Task 14: Leak battery and differential validation

**Files:**
- Create: `tests/cup20/test_leak_battery.py`
- Modify: `src/crypto_trade/cup20/__init__.py` (export the public surface built in Tasks 2–13)

**Interfaces:**
- Consumes: every module from Tasks 2–13.
- Produces: no new runtime API. Exports `build_membership`, `write_split_snapshots`, `load_snapshot`, `resolve_is_start`, `common_risk_scalars`, `run_candidate`, `decision_grid`, `window_metrics`, `is_folds`, `holdout_folds`, `robustness_score`, `rank_entries`, `select_advancing`, `evaluate_floors`, `append_record`, `verify_chain`, `scan_for_blindness_violations`, `build_packet`, `atomic_release` from `crypto_trade.cup20`.

- [ ] **Step 1: Write the failing leak battery**

```python
# tests/cup20/test_leak_battery.py
"""Every check that must pass before a single team is allowed to start."""

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.runner import decision_grid, run_candidate
from crypto_trade.cup20.snapshot import Snapshot, load_snapshot, write_split_snapshots
from crypto_trade.tournament.engine_v2 import EvaluatorConfig

CONFIG = EvaluatorConfig(max_gross_exposure=1.0, max_abs_net_exposure=1.0, max_symbol_exposure=0.20)
RISK_UNIT = {"target_annualized_volatility": 0.10, "lookback_days": 90}


class MomentumProbe:
    """A realistic causal strategy: sign of the trailing 30-bar return, equal weight."""

    def target_weights(self, context, *, seed):
        weights = {}
        for symbol, frame in context.bars.items():
            if len(frame) < 31:
                continue
            closes = frame["close"].to_numpy(dtype=float)
            weights[symbol] = 1.0 if closes[-1] > closes[-31] else -1.0
        if not weights:
            return {}
        scale = 1.0 / len(weights)
        return {symbol: value * scale for symbol, value in weights.items()}


def _synthetic(seed=3, symbols=("AUSDT", "BUSDT", "CUSDT", "DUSDT")):
    times = pd.date_range("2021-01-01T00:00:00Z", periods=900, freq="8h")
    rng = np.random.default_rng(seed)
    frames = []
    for symbol in symbols:
        price = 100.0 * np.cumprod(1.0 + rng.normal(0.0002, 0.012, len(times)))
        frames.append(
            pd.DataFrame(
                {
                    "open_time": times,
                    "symbol": symbol,
                    "open": price,
                    "high": price * 1.01,
                    "low": price * 0.99,
                    "close": price,
                    "volume": 1e6,
                    "quote_volume": 1e9,
                }
            )
        )
    bars = pd.concat(frames, ignore_index=True)
    funding = pd.DataFrame(
        {
            "funding_time": np.tile(times, len(symbols)),
            "symbol": np.repeat(list(symbols), len(times)),
            "funding_rate": 0.0001,
        }
    )
    marks = bars[["open_time", "symbol", "open"]].rename(
        columns={"open_time": "mark_time", "open": "mark_price"}
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]] * len(symbols),
            "symbol": list(symbols),
            "liquidity_rank": list(range(1, len(symbols) + 1)),
            "trailing_quote_volume": [1e9] * len(symbols),
        }
    )
    metadata = pd.DataFrame({"symbol": list(symbols), "contract_type": "PERPETUAL"})
    return Snapshot(bars, funding, marks, membership, metadata, manifest_sha256="synthetic")


def _run(snapshot, grid, seed=42):
    return run_candidate(
        MomentumProbe(),
        snapshot,
        decision_times=grid,
        seed=seed,
        config=CONFIG,
        risk_unit=RISK_UNIT,
    )


def test_future_corruption_does_not_change_any_target():
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    cutoff = grid[len(grid) // 2]
    baseline = _run(snapshot, grid[: len(grid) // 2])

    corrupted_bars = snapshot.bars.copy()
    mask = corrupted_bars["open_time"] >= cutoff
    for column in ("open", "high", "low", "close"):
        corrupted_bars.loc[mask, column] *= 1000.0
    corrupted = Snapshot(
        corrupted_bars,
        snapshot.funding,
        snapshot.mark_prices,
        snapshot.membership,
        snapshot.contract_metadata,
        manifest_sha256="corrupted",
    )
    after = _run(corrupted, grid[: len(grid) // 2])
    pd.testing.assert_frame_equal(baseline.targets, after.targets)


def test_evaluation_is_bit_reproducible():
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    first = _run(snapshot, grid)
    second = _run(snapshot, grid)
    pd.testing.assert_frame_equal(first.results[1].returns, second.results[1].returns)
    pd.testing.assert_series_equal(first.risk_scalars, second.risk_scalars)


def test_risk_unit_moves_realised_volatility_toward_the_common_target():
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    run = _run(snapshot, grid)
    scaled = run.results[1].returns["net_return"]
    unscaled = run.unscaled.returns["net_return"]
    tail = slice(300, None)
    assert abs(scaled.iloc[tail].std() - 0.10 / np.sqrt(1095)) < abs(
        unscaled.iloc[tail].std() - 0.10 / np.sqrt(1095)
    )


def test_costs_are_strictly_monotone_in_the_multiplier():
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    run = _run(snapshot, grid)
    costs = {
        multiplier: float(result.returns["fees"].sum() + result.returns["slippage"].sum())
        for multiplier, result in run.results.items()
    }
    assert costs[1] < costs[2] < costs[3]


def test_a_flat_strategy_earns_no_funding_and_no_costs():
    class Flat:
        def target_weights(self, context, *, seed):
            return {}

    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    run = run_candidate(
        Flat(), snapshot, decision_times=grid, seed=1, config=CONFIG, risk_unit=RISK_UNIT
    )
    frame = run.results[1].returns
    assert float(frame["funding_pnl"].abs().sum()) == pytest.approx(0.0, abs=1e-12)
    assert float(frame["fees"].sum() + frame["slippage"].sum()) == pytest.approx(0.0, abs=1e-12)


def test_is_snapshot_written_to_disk_contains_no_sealed_row(tmp_path):
    snapshot = _synthetic()
    cutoff = pd.Timestamp("2021-06-01T00:00:00Z")
    is_paths, sealed_paths = write_split_snapshots(
        snapshot.bars,
        snapshot.funding,
        snapshot.mark_prices,
        snapshot.membership,
        snapshot.contract_metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_end=cutoff,
        sealed_end=pd.Timestamp("2022-01-01T00:00:00Z"),
    )
    reloaded = load_snapshot(is_paths.root)
    assert (reloaded.bars["open_time"] < cutoff).all()
    assert (reloaded.funding["funding_time"] < cutoff).all()
    assert load_snapshot(sealed_paths.root).bars["open_time"].min() >= cutoff
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cup20/test_leak_battery.py -q`
Expected: FAIL — the module imports resolve but at least the future-corruption and volatility tests
fail until the exports in Step 3 are in place. If any leak test fails for a substantive reason, stop
and fix the implementation; a leak test is never adjusted to match behaviour.

- [ ] **Step 3: Export the public surface**

```python
# src/crypto_trade/cup20/__init__.py
"""CUP-20 tournament policy, evaluation and scoring."""

from crypto_trade.cup20.archive import (
    archive_directory,
    bundle_digest,
    scan_for_blindness_violations,
)
from crypto_trade.cup20.bootstrap import (
    circular_block_bootstrap_positive_fraction,
    trial_adjusted_confidence,
)
from crypto_trade.cup20.config import (
    IS_END,
    SEALED_END,
    SEALED_START,
    TEAM_IDS,
    LoadedConfig,
    load_config,
    validate_config,
)
from crypto_trade.cup20.journal import (
    accepted_trial_count,
    append_record,
    read_records,
    verify_chain,
)
from crypto_trade.cup20.metrics import (
    WindowMetrics,
    daily_returns,
    fold_positive_pnl_shares,
    fold_sharpes,
    holdout_folds,
    is_folds,
    window_metrics,
)
from crypto_trade.cup20.neighbourhood import (
    NeighbourhoodDeclaration,
    load_declaration,
    median_metrics,
    positive_point_fraction,
)
from crypto_trade.cup20.qualification import GateVector, evaluate_floors
from crypto_trade.cup20.report import atomic_release, build_packet, write_manifest
from crypto_trade.cup20.risk_unit import apply_risk_scalars, common_risk_scalars
from crypto_trade.cup20.runner import (
    CandidateRun,
    decision_grid,
    evaluator_config,
    normalise_unit_gross,
    run_candidate,
)
from crypto_trade.cup20.scoring import (
    RankedEntry,
    rank_entries,
    robustness_score,
    select_advancing,
)
from crypto_trade.cup20.snapshot import (
    Snapshot,
    SnapshotPaths,
    load_snapshot,
    resolve_is_start,
    write_split_snapshots,
)
from crypto_trade.cup20.universe import build_membership, weekly_reconstitution_times

__all__ = [
    "IS_END",
    "SEALED_END",
    "SEALED_START",
    "TEAM_IDS",
    "CandidateRun",
    "GateVector",
    "LoadedConfig",
    "NeighbourhoodDeclaration",
    "RankedEntry",
    "Snapshot",
    "SnapshotPaths",
    "WindowMetrics",
    "accepted_trial_count",
    "append_record",
    "apply_risk_scalars",
    "archive_directory",
    "atomic_release",
    "build_membership",
    "build_packet",
    "bundle_digest",
    "circular_block_bootstrap_positive_fraction",
    "common_risk_scalars",
    "daily_returns",
    "decision_grid",
    "evaluate_floors",
    "evaluator_config",
    "fold_positive_pnl_shares",
    "fold_sharpes",
    "holdout_folds",
    "is_folds",
    "load_config",
    "load_declaration",
    "load_snapshot",
    "median_metrics",
    "normalise_unit_gross",
    "positive_point_fraction",
    "rank_entries",
    "read_records",
    "resolve_is_start",
    "robustness_score",
    "run_candidate",
    "scan_for_blindness_violations",
    "select_advancing",
    "trial_adjusted_confidence",
    "validate_config",
    "verify_chain",
    "weekly_reconstitution_times",
    "window_metrics",
    "write_manifest",
    "write_split_snapshots",
]
```

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest tests/cup20/ -q`
Expected: all tests pass. Then run `uv run pytest -q` to confirm nothing in the existing suite
regressed.

- [ ] **Step 5: Commit**

```bash
uv run ruff check src/crypto_trade/cup20 tests/cup20 --fix
uv run ruff format src/crypto_trade/cup20 tests/cup20
git add src/crypto_trade/cup20/__init__.py tests/cup20/test_leak_battery.py
git commit -m "Add CUP-20 leak battery and public surface"
```

---

### Task 15: Build the real snapshot, freeze activation, scaffold the twelve teams

**Files:**
- Create: `scripts/cup20_build_snapshot.py`
- Create: `scripts/cup20_activate.py`
- Create: `tournament/cup20/TEAM-PLAYBOOK.md`
- Create: `tournament/cup20/teams/team-NN/MANDATE.md` (twelve files)
- Create: `tournament/cup20/activation-freeze.json` (generated)
- Create: `data/cup20/is/`, `data/cup20/sealed/` (generated)
- Test: `tests/cup20/test_activation.py`

**Interfaces:**
- Consumes: everything from Tasks 1–14.
- Produces: `scripts/cup20_build_snapshot.py` CLI writing both snapshots and printing the resolved `IS_START`; `scripts/cup20_activate.py` CLI writing `activation-freeze.json`; `crypto_trade.cup20.activation.build_activation_record(config_path, charter_path, is_root, sealed_root, test_output) -> dict[str, str]` and `verify_activation(path) -> dict[str, str]`.

- [ ] **Step 1: Write the failing activation test**

```python
# tests/cup20/test_activation.py
import json

import pytest

from crypto_trade.cup20.activation import build_activation_record, verify_activation


def _fixture(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('schema_version = 1\n')
    charter = tmp_path / "CHARTER.md"
    charter.write_text("# charter\n")
    is_root = tmp_path / "is"
    sealed_root = tmp_path / "sealed"
    for root in (is_root, sealed_root):
        root.mkdir()
        (root / "manifest.json").write_text(
            json.dumps({"manifest_sha256": "f" * 64 if root is is_root else "e" * 64})
        )
    tests = tmp_path / "tests.out"
    tests.write_text("42 passed\n")
    return config, charter, is_root, sealed_root, tests


def test_activation_record_binds_every_authority(tmp_path):
    record = build_activation_record(*_fixture(tmp_path))
    for key in (
        "config_sha256",
        "charter_sha256",
        "is_manifest_sha256",
        "sealed_manifest_sha256",
        "dependency_lock_sha256",
        "test_output_sha256",
    ):
        assert len(record[key]) == 64


def test_is_and_sealed_manifests_must_differ(tmp_path):
    config, charter, is_root, sealed_root, tests = _fixture(tmp_path)
    (sealed_root / "manifest.json").write_text(json.dumps({"manifest_sha256": "f" * 64}))
    with pytest.raises(ValueError, match="distinct"):
        build_activation_record(config, charter, is_root, sealed_root, tests)


def test_verify_activation_detects_a_changed_authority(tmp_path):
    config, charter, is_root, sealed_root, tests = _fixture(tmp_path)
    record = build_activation_record(config, charter, is_root, sealed_root, tests)
    path = tmp_path / "activation-freeze.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True))
    assert verify_activation(path) == record
    charter.write_text("# charter changed\n")
    with pytest.raises(ValueError, match="charter"):
        verify_activation(path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/cup20/test_activation.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'crypto_trade.cup20.activation'`

- [ ] **Step 3: Implement activation**

```python
# src/crypto_trade/cup20/activation.py
"""Activation freeze: one record binding every authority before the first result."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_AUTHORITIES = (
    ("config_sha256", "config"),
    ("charter_sha256", "charter"),
    ("dependency_lock_sha256", "dependency lock"),
    ("test_output_sha256", "test output"),
)


def _digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _manifest_digest(root: Path) -> str:
    return str(json.loads((Path(root) / "manifest.json").read_text())["manifest_sha256"])


def build_activation_record(
    config_path: str | Path,
    charter_path: str | Path,
    is_root: str | Path,
    sealed_root: str | Path,
    test_output: str | Path,
    dependency_lock: str | Path = "uv.lock",
) -> dict[str, str]:
    """Hash-bind charter, config, data authorities, dependency lock and test output."""
    is_manifest = _manifest_digest(Path(is_root))
    sealed_manifest = _manifest_digest(Path(sealed_root))
    if is_manifest == sealed_manifest:
        raise ValueError("IS and sealed snapshots must have distinct manifest digests")
    return {
        "config_sha256": _digest(Path(config_path)),
        "charter_sha256": _digest(Path(charter_path)),
        "is_manifest_sha256": is_manifest,
        "sealed_manifest_sha256": sealed_manifest,
        "dependency_lock_sha256": _digest(Path(dependency_lock)),
        "test_output_sha256": _digest(Path(test_output)),
        "config_path": str(config_path),
        "charter_path": str(charter_path),
        "is_root": str(is_root),
        "sealed_root": str(sealed_root),
        "dependency_lock_path": str(dependency_lock),
        "test_output_path": str(test_output),
    }


def verify_activation(path: str | Path) -> dict[str, str]:
    """Recompute every bound authority and fail on any drift."""
    record = json.loads(Path(path).read_text())
    current = build_activation_record(
        record["config_path"],
        record["charter_path"],
        record["is_root"],
        record["sealed_root"],
        record["test_output_path"],
        record["dependency_lock_path"],
    )
    for key, label in _AUTHORITIES:
        if current[key] != record[key]:
            raise ValueError(f"activation authority changed: {label}")
    for key, label in (
        ("is_manifest_sha256", "IS snapshot"),
        ("sealed_manifest_sha256", "sealed snapshot"),
    ):
        if current[key] != record[key]:
            raise ValueError(f"activation authority changed: {label}")
    return record
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/cup20/test_activation.py -q`
Expected: 3 passed

- [ ] **Step 5: Write the acquisition config**

Data acquisition reuses the proven pipeline. The acquisition universe is deliberately **wider**
than CUP-20's: ranking by the same trailing 180-day volume at size 60 makes the CUP-20 top-20 a
provable subset (anything ranked ≤25 by that measure is certainly ranked ≤60), which the build
script then asserts.

```toml
# tournament/cup20/snapshot-config.toml
schema_version = 1
name = "cup20-acquisition"

[data]
source = "binance-public-usdm"
archive_base_url = "https://data.binance.vision"
archive_s3_url = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
exchange_info_url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
funding_rate_url = "https://fapi.binance.com/fapi/v1/fundingRate"
mark_price_klines_url = "https://fapi.binance.com/fapi/v1/markPriceKlines"
warmup_start = "2019-09-01"
hard_end_exclusive = "2026-08-01"
transaction_interval = "8h"
mark_price_interval = "1h"
snapshot_dir = "data/cup20/acquisition"
manifest_path = "tournament/cup20/data_manifest.json"
common_report_dir = "reports-cup20/common"
checksum_policy = "require-binance-sha256-sidecar"
parser_version = "cup20-snapshot-v1"

[splits]
in_sample_start = "2020-02-03"
in_sample_end_inclusive = "2024-07-31"
public_oos_start = "2024-08-01"
public_oos_end_inclusive = "2026-07-31"
public_oos_visible_to_teams = false
quarantined_gap_start = "2026-08-01"
forward_paper_start = "winner-freeze-next-8h-boundary"

[universe]
venue = "binance-usdm"
instrument = "linear-usdt-perpetual"
size = 60
reconstitution = "weekly-monday-00:00-utc"
liquidity_measure = "median-daily-quote-volume"
trailing_days = 180
minimum_history_days = 180
```

Before running, seed the archive cache so only recent months are downloaded:

```bash
mkdir -p data/cup20/acquisition
cp -rn /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top40-v3/data/top40/snapshot-v1/raw \
       data/cup20/acquisition/raw 2>/dev/null || true
```

If `build_snapshot` rejects a key in this config, read `_load_config` in
`src/crypto_trade/tournament/snapshot.py` and add the missing key with the value that file
requires. Do not weaken a validation to make the config load.

- [ ] **Step 6: Write the snapshot build script**

```python
# scripts/cup20_build_snapshot.py
"""Acquire raw Binance USD-M data, derive the CUP-20 top-20 universe, write both snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from crypto_trade.cup20.config import IS_END, SEALED_END, load_config
from crypto_trade.cup20.snapshot import resolve_is_start, write_split_snapshots
from crypto_trade.cup20.universe import build_membership, weekly_reconstitution_times
from crypto_trade.tournament.pure_crypto_universe_v6 import audit_pure_crypto_universe
from crypto_trade.tournament.snapshot import build_snapshot

ACQUISITION_CONFIG = Path("tournament/cup20/snapshot-config.toml")
ACQUISITION_DIR = Path("data/cup20/acquisition")


def acquire() -> None:
    """Download, checksum-verify and publish the wide acquisition snapshot."""
    build_snapshot(
        ACQUISITION_CONFIG,
        ACQUISITION_DIR,
        Path("tournament/cup20/data_manifest.json"),
        Path("reports-cup20/common"),
        resume=True,
    )


def daily_quote_volume(bars: pd.DataFrame) -> pd.DataFrame:
    """Sum 8h quote volume into UTC days: index=day, columns=symbol."""
    frame = bars[["open_time", "symbol", "quote_volume"]].copy()
    frame["day"] = pd.to_datetime(frame["open_time"], utc=True).dt.normalize()
    pivot = frame.pivot_table(
        index="day", columns="symbol", values="quote_volume", aggfunc="sum"
    )
    full_days = pd.date_range(pivot.index.min(), pivot.index.max(), freq="D", tz="UTC")
    return pivot.reindex(full_days)


def eligibility(volume: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    """A symbol is eligible on a day when it traded and its contract passes the crypto policy."""
    allowed = set(
        metadata.loc[
            metadata["is_crypto"].astype(bool)
            & metadata["contract_type"].astype(str).eq("PERPETUAL")
            & metadata["quote_asset"].astype(str).eq("USDT")
            & metadata["margin_asset"].astype(str).eq("USDT"),
            "symbol",
        ].astype(str)
    )
    frame = volume.notna()
    for column in frame.columns:
        if column not in allowed:
            frame[column] = False
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the CUP-20 IS and sealed snapshots")
    parser.add_argument("--skip-acquire", action="store_true", help="reuse the acquisition dir")
    arguments = parser.parse_args()

    if not arguments.skip_acquire:
        acquire()

    audit = audit_pure_crypto_universe(ACQUISITION_DIR)
    print(f"pure-crypto audit: {audit.get('status', audit)}")

    bars = pd.read_parquet(ACQUISITION_DIR / "bars.parquet")
    funding = pd.read_parquet(ACQUISITION_DIR / "funding.parquet")
    marks = pd.read_parquet(ACQUISITION_DIR / "mark_prices.parquet")
    metadata = pd.read_parquet(ACQUISITION_DIR / "contract_metadata.parquet")
    acquired = pd.read_parquet(ACQUISITION_DIR / "membership.parquet")

    config = load_config("tournament/cup20/config.toml").raw["universe"]
    volume = daily_quote_volume(bars)
    eligible = eligibility(volume, metadata)
    boundaries = weekly_reconstitution_times(
        pd.Timestamp(volume.index.min()) + pd.Timedelta(days=int(config["lookback_days"])),
        SEALED_END,
        weekday=int(config["reconstitution_weekday"]),
    )
    membership = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=boundaries,
        lookback_days=int(config["lookback_days"]),
        target_size=int(config["target_size"]),
        entry_rank=int(config["entry_rank"]),
        exit_rank=int(config["exit_rank"]),
    )

    # Containment: every CUP-20 member must exist in the audited acquisition universe.
    missing = set(membership["symbol"]) - set(acquired["symbol"].astype(str))
    if missing:
        raise SystemExit(f"CUP-20 members absent from the acquisition universe: {sorted(missing)}")

    is_start = resolve_is_start(membership, target_size=int(config["target_size"]))
    membership = membership.loc[membership["reconstitution_time"] >= is_start].reset_index(
        drop=True
    )
    members = sorted(set(membership["symbol"]))
    warmup_start = is_start - pd.Timedelta(days=int(config["lookback_days"]))

    def restrict(frame: pd.DataFrame, column: str) -> pd.DataFrame:
        times = pd.to_datetime(frame[column], utc=True)
        return frame.loc[frame["symbol"].astype(str).isin(members) & (times >= warmup_start)]

    is_paths, sealed_paths = write_split_snapshots(
        restrict(bars, "open_time"),
        restrict(funding, "funding_time"),
        restrict(marks, "mark_time"),
        membership,
        metadata.loc[metadata["symbol"].astype(str).isin(members)],
        is_root="data/cup20/is",
        sealed_root="data/cup20/sealed",
        is_end=IS_END,
        sealed_end=SEALED_END,
    )
    summary = {
        "is_start": str(is_start),
        "is_end": str(IS_END),
        "sealed_end": str(SEALED_END),
        "distinct_members": len(members),
        "reconstitutions": int(membership["reconstitution_time"].nunique()),
        "is_manifest_sha256": json.loads(is_paths.manifest.read_text())["manifest_sha256"],
        "sealed_manifest_sha256": json.loads(sealed_paths.manifest.read_text())[
            "manifest_sha256"
        ],
    }
    Path("tournament/cup20/universe-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```

Run it:

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run python scripts/cup20_build_snapshot.py
```

Acquisition downloads several years of monthly archives and is the long pole; run it detached with
`PYTHONUNBUFFERED=1` and a log file if it exceeds a few minutes. Then verify the split by hand:

```bash
uv run python -c "
import pandas as pd
i = pd.read_parquet('data/cup20/is/bars.parquet')
s = pd.read_parquet('data/cup20/sealed/bars.parquet')
print('IS  max open_time:', i.open_time.max())
print('SEALED min open_time:', s.open_time.min())
assert i.open_time.max() < pd.Timestamp('2024-08-01T00:00:00Z')
assert s.open_time.min() >= pd.Timestamp('2024-08-01T00:00:00Z')
m = pd.read_parquet('data/cup20/is/membership.parquet')
print('members per boundary:', m.groupby('reconstitution_time').size().describe())
print('distinct symbols:', m.symbol.nunique())
"
```

Record `IS_START`, the distinct member count and both manifest digests in the commit message.
Expected shape from the design-time measurement: roughly 70 distinct symbols across the full
period and a universe that reaches 20 members around 2020-08.

- [ ] **Step 7: Write the team playbook and twelve mandates**

`tournament/cup20/TEAM-PLAYBOOK.md` states, in the team's own words:

- your data root is `data/cup20/is/`, and nothing else — the sealed rows are not on this machine's
  team-visible path and attempting to reach them is a disqualification;
- your workspace is `tournament/cup20/teams/team-NN/`, and nothing else;
- you implement `build_strategy() -> TargetStrategy` in
  `candidates/<candidate-id>/strategy.py` against
  `crypto_trade.tournament.protocol.TargetStrategy`; you return signed target weights and nothing
  else; the organiser owns fills, costs, funding, delistings and risk normalisation;
- every material trial is journaled before you look at any number; you have twelve, you need at
  least eight to nominate, the declared neighbourhood sweep is one trial and the falsification
  battery is one trial;
- you fix your nominee **before** declaring the neighbourhood; moving it afterwards voids the sweep;
- every neighbourhood coordinate must be a **module-level numeric constant** in your frozen
  `strategy.py`, named identically to the coordinate, and the nominee's declared value must equal
  that constant. Module-level means the top level of the module, including inside a module-level
  `if`/`try`; a value defined inside a function body or a class body does not count and will be
  reported as absent. This rule exists so the nominated point is provably what the frozen code
  actually does, and it is stated here so an honest submission is never surprised by it. The
  constant must have exactly **one** value: if a coordinate name is assigned two different numeric
  values anywhere at module scope — by reassignment or across branches of an `if`/`try` — the
  submission is rejected as ambiguous. Verification parses your code and never runs it, so it
  cannot know which branch would execute, and a name whose value depends on a branch is therefore
  not a frozen parameter;
- your research certificate must cover: baseline, exact sign inversion, ≥3 formation horizons, ≥2
  rebalance/holding horizons with the phase offset swept for any cadence longer than one bar,
  controls-off and individual-control and combined-control ablations, long/short/chop role checks,
  the declared neighbourhood, and every failure and abandoned attempt with its journal sequence;
- a negative candidate is evidence, not a submission — do not nominate because your budget ran out;
- you may pivot mechanism once, and only after your original thesis is falsified across the full
  matrix.

Each `tournament/cup20/teams/team-NN/MANDATE.md` states the lane from `[mandates]`, two or three
sentences of mechanism intent, and the explicit note that shared causal transforms and shared risk
controls are not a collision but copying another team's alpha is.

- [ ] **Step 7b: Re-derive the charter from the amended spec**

`docs/superpowers/specs/2026-08-04-cup20-tournament-design.md` was amended after Task 1 generated
`TOURNAMENT-CHARTER-CUP20.md` (§4 caps, §6 risk-unit interaction, §7.2 neighbourhood validity,
§7.3 floors). Re-derive the charter body so it is byte-identical to spec §1-§14 again, keeping
Task 1's header block, and verify with a `diff`. The activation record hash-binds both, so a stale
charter would freeze a contradiction.

- [ ] **Step 8: Freeze activation**

```bash
uv run pytest tests/cup20/ -q | tee tournament/cup20/activation-tests.out
uv run python scripts/cup20_activate.py
uv run python -c "
from crypto_trade.cup20.activation import verify_activation
print(verify_activation('tournament/cup20/activation-freeze.json'))
"
```

- [ ] **Step 9: Commit**

```bash
uv run ruff check src scripts tests --fix
uv run ruff format src scripts tests
git add src/crypto_trade/cup20/activation.py scripts/cup20_build_snapshot.py \
        scripts/cup20_activate.py tournament/cup20 tests/cup20/test_activation.py
# data/cup20/ is large and .gitignored; the manifests inside tournament/cup20 pin its identity
git commit -m "Build CUP-20 snapshots, freeze activation, scaffold twelve teams"
```

---

## Self-review notes

- Spec §3 universe → Task 2. §5 blindness → Tasks 3, 12, 14. §4 execution → Task 5. §6 risk unit → Task 4. §7.1 journal → Task 11. §7.2 neighbourhood → Task 8. §7.3 floors → Tasks 6, 7, 9. §7.4 ranking → Task 10. §7.5 freeze → Tasks 12, 15. §8 holdout → Tasks 10, 13 (`holdout_folds`, `drawdown_floor=0.25`). §9 mandates → Tasks 1, 15. §11 surface → all. §13 authority → Task 15.
- Spec §10 (forward paper desk) is intentionally **not** in this plan. It is a separate sub-project that only becomes real if the holdout produces an eligible winner, and it depends on artifacts that do not exist yet. Write that plan after the reveal.
- Ensemble reporting (spec §7.5) is a thin composition over `build_packet` and is folded into the Phase-2 operating procedure rather than a code task; it needs the actual finalist return streams to be meaningful.

## Phases 1–4 operating procedure (not code)

Once Task 15 is committed and activation verifies:

1. **Phase 1.** Dispatch twelve independent QR+QE pairs, one per mandate, each restricted to its
   own team directory and the IS snapshot. Each pair journals every material trial, produces a
   research certificate, freezes one candidate plus its neighbourhood declaration, and stops.
2. **Phase 2.** For every nomination: run `scan_for_blindness_violations`, `archive_directory`,
   the neighbourhood sweep and the falsification battery; compute per-metric medians; evaluate
   floors; compute `G`; rank; write `selection-freeze.json` with the top three and the frozen
   equal-risk ensemble weights. Close the journal at one head.
3. **Phase 3.** Only after the selection freeze exists, run each finalist's neighbourhood against
   `data/cup20/sealed/`. Build every packet privately, verify hashes, then one `atomic_release`.
4. **Phase 4.** Comparative Critic review, final leaderboard, and the noise-floor disclosure
   (±0.7 Sharpe over two years). If no finalist is eligible, publish the null result.
