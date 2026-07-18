"""Organizer-owned synthetic canary for the Top-40 V3 strategy sandbox.

The canary deliberately stops at target generation.  It does not load the market snapshot, call
an evaluator, publish result artifacts, or consume a team journal entry.  Its only purpose is to
prove that the production worker boundary can complete one deterministic protocol round trip.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pandas as pd

from crypto_trade.tournament import runner_v3
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

CANARY_ENTRYPOINT = (
    "tournament/top40-v3/teams/team-01/fixtures/sandbox-canary/strategy.py"
)
CANARY_TEAM_LABEL = "team-01"
CANARY_SYMBOL = "BTCUSDT"
CANARY_SEED = 20260718
CANARY_WEIGHT = 0.03125
CANARY_DECISION_TIME = pd.Timestamp("2026-07-18T08:00:00Z")


@dataclasses.dataclass(frozen=True)
class SandboxCanaryResult:
    """Minimal proof returned only after a clean worker shutdown."""

    decision_time: str
    symbol: str
    weight: float
    source_bundle_sha256: str


def _synthetic_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return a tiny, wholly synthetic past/current-open boundary."""

    bars = pd.DataFrame(
        {
            "open_time": pd.to_datetime(
                ["2026-07-18T00:00:00Z", "2026-07-18T08:00:00Z"],
                utc=True,
            ),
            "symbol": [CANARY_SYMBOL, CANARY_SYMBOL],
            "open": [100.0, 101.0],
            "close": [101.0, 102.0],
            "quote_volume": [1_000_000.0, 1_000_000.0],
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": pd.to_datetime(["2026-07-18T00:00:00Z"], utc=True),
            "symbol": [CANARY_SYMBOL],
            "funding_rate": [0.0001],
            "mark_price": [100.5],
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": pd.to_datetime(["2026-07-13T00:00:00Z"], utc=True),
            "symbol": [CANARY_SYMBOL],
            "liquidity_rank": [1],
            "trailing_quote_volume": [1_000_000.0],
        }
    )
    return bars, funding, membership


def _scoped_entrypoint(root: Path) -> Path:
    raw_entrypoint = root / CANARY_ENTRYPOINT
    if raw_entrypoint.is_symlink():
        raise runner_v3.StrategySandboxError(
            "the Phase-0 sandbox-canary strategy is missing or unsafe"
        )
    entrypoint = raw_entrypoint.resolve()
    if (
        not entrypoint.is_relative_to(root)
        or not entrypoint.is_file()
    ):
        raise runner_v3.StrategySandboxError(
            "the Phase-0 sandbox-canary strategy is missing or unsafe"
        )
    return entrypoint


def run_sandbox_canary(root: str | Path) -> SandboxCanaryResult:
    """Run exactly init, one synthetic decision, and clean shutdown in the real V3 sandbox.

    No exception is softened or converted into a skip.  In particular, unavailable Linux user,
    mount, network, or PID namespaces; mount-helper failures; an external venv; insufficient
    Landlock support; and seccomp installation failures all propagate and fail Phase 0 closed.
    """

    raw_root = Path(root)
    if raw_root.is_symlink():
        raise runner_v3.StrategySandboxError("sandbox-canary root is missing or unsafe")
    root_path = raw_root.resolve(strict=True)
    if not root_path.is_dir():
        raise runner_v3.StrategySandboxError("sandbox-canary root is missing or unsafe")
    entrypoint = _scoped_entrypoint(root_path)
    source_files = runner_v3._team_tree_files(entrypoint.parent)
    source_bundle_sha256 = runner_v3._team_tree_fingerprint(source_files)
    bars, funding, membership = _synthetic_inputs()

    targets = runner_v3._generate_targets_in_worker(
        root_path,
        CANARY_TEAM_LABEL,
        CANARY_ENTRYPOINT,
        bars,
        funding,
        membership,
        [CANARY_DECISION_TIME],
        seed=CANARY_SEED,
        interval_hours=8,
        expected_source_bundle_sha256=source_bundle_sha256,
    )

    expected_columns = {CANARY_SYMBOL, REBALANCE_INSTRUCTION_COLUMN}
    if (
        len(targets) != 1
        or not targets.index.equals(pd.DatetimeIndex([CANARY_DECISION_TIME]))
        or set(targets.columns) != expected_columns
        or not bool(targets.iloc[0][REBALANCE_INSTRUCTION_COLUMN])
        or float(targets.iloc[0][CANARY_SYMBOL]) != CANARY_WEIGHT
    ):
        raise runner_v3.StrategySandboxError(
            "sandbox canary returned a non-canonical synthetic target"
        )

    return SandboxCanaryResult(
        decision_time=CANARY_DECISION_TIME.isoformat(),
        symbol=CANARY_SYMBOL,
        weight=CANARY_WEIGHT,
        source_bundle_sha256=source_bundle_sha256,
    )


__all__ = [
    "CANARY_DECISION_TIME",
    "CANARY_ENTRYPOINT",
    "CANARY_SEED",
    "CANARY_SYMBOL",
    "CANARY_WEIGHT",
    "SandboxCanaryResult",
    "run_sandbox_canary",
]
