"""Reusable continuous replay for the frozen Top-12 V2 Team 12 winner."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from crypto_trade.team12.authority import (
    CANDIDATE_ID,
    DATA_MANIFEST_SHA256,
    GOLDEN_BAR_RETURNS_SHA256,
    GOLDEN_POSITIONS_SHA256,
    GOLDEN_TARGETS_SHA256,
    build_frozen_strategy,
    load_frozen_risk_policy,
    release_team_root,
    repository_root,
    sha256_file,
    snapshot_root,
    verify_frozen_authority,
)
from crypto_trade.tournament.engine_v2 import (
    EvaluationResult,
    EvaluatorConfig,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.metrics_v3 import (
    aggregate_daily_returns,
    compute_window_metrics,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

REPLAY_START = pd.Timestamp("2020-08-03T00:00:00Z")
HISTORICAL_END_EXCLUSIVE = pd.Timestamp("2026-07-01T00:00:00Z")
IS_END_EXCLUSIVE = pd.Timestamp("2023-07-01T00:00:00Z")
IS_CONFIRMATION_END_EXCLUSIVE = pd.Timestamp("2024-07-01T00:00:00Z")
LIVE_FORWARD_START = pd.Timestamp("2026-08-03T00:00:00Z")
LIVE_REPLAY_ACTIVATION_BOUNDARY = pd.Timestamp("2026-08-03T16:00:00Z")
LIVE_REPLAY_BASELINE_SYMBOL_COUNT = 670
LIVE_REPLAY_BASELINE_SYMBOLS_SHA256 = (
    "417eac3bf18d8801f3d3f9ebce9f3ffd66287e0d42ddfc272808216c0ad4bbb5"
)
INTERVAL_HOURS = 8
STRATEGY_SEED = 20_260_731

EVALUATOR_CONFIG = EvaluatorConfig(
    interval_hours=INTERVAL_HOURS,
    initial_equity=100_000.0,
    taker_fee_bps_per_side=5.0,
    slippage_bps_per_side=2.5,
    max_gross_exposure=1.0,
    max_abs_net_exposure=0.25,
    max_symbol_exposure=0.10,
    max_bar_participation=0.001,
)


@dataclasses.dataclass(frozen=True)
class Team12MarketData:
    bars: pd.DataFrame
    funding: pd.DataFrame
    membership: pd.DataFrame
    mark_prices: pd.DataFrame
    contract_metadata: pd.DataFrame


@dataclasses.dataclass(frozen=True)
class Team12Replay:
    decision_times: pd.DatetimeIndex
    targets: pd.DataFrame
    evaluations: dict[float, EvaluationResult]

    def evaluation(self, cost_multiplier: float = 1.0) -> EvaluationResult:
        try:
            return self.evaluations[float(cost_multiplier)]
        except KeyError as exc:
            raise KeyError(f"cost multiplier {cost_multiplier:g} was not replayed") from exc

    def daily_returns(self, cost_multiplier: float = 1.0) -> pd.Series:
        result = self.evaluation(cost_multiplier)
        return aggregate_daily_returns(result.returns["net_return"])


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return (
        timestamp.tz_localize("UTC")
        if timestamp.tzinfo is None
        else timestamp.tz_convert("UTC")
    )


def decision_grid(
    *,
    start: object = REPLAY_START,
    end_exclusive: object = HISTORICAL_END_EXCLUSIVE,
) -> pd.DatetimeIndex:
    first = _utc(start)
    end = _utc(end_exclusive)
    interval = pd.Timedelta(hours=INTERVAL_HOURS)
    if first != first.floor(f"{INTERVAL_HOURS}h"):
        raise ValueError("Team 12 replay start must be an exact 8-hour UTC boundary")
    if end != end.floor(f"{INTERVAL_HOURS}h") or end <= first + interval:
        raise ValueError("Team 12 replay end must be a later exact 8-hour UTC boundary")
    return pd.date_range(first, end - interval, freq=interval, tz="UTC").as_unit(
        "ns"
    )


def load_frozen_snapshot(root: str | Path | None = None) -> Team12MarketData:
    """Load the organizer-verified historical snapshot without modifying it."""

    verify_frozen_authority(root)
    base = Path(root).resolve() if root is not None else repository_root()
    data_root = snapshot_root(base)
    required = {
        "bars": data_root / "bars.parquet",
        "funding": data_root / "funding.parquet",
        "membership": data_root / "membership.parquet",
        "mark_prices": data_root / "mark_prices.parquet",
        "contract_metadata": data_root / "contract_metadata.parquet",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Team 12 snapshot is incomplete: {missing}")

    manifest_path = base / "tournament" / "top12" / "data_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing tournament data manifest: {manifest_path}")
    manifest_sha = _sha256_file(manifest_path)
    if manifest_sha != DATA_MANIFEST_SHA256:
        raise RuntimeError(
            f"Team 12 data-manifest drift: {manifest_sha} != {DATA_MANIFEST_SHA256}"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Team 12 data manifest is not valid JSON") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise ValueError("Team 12 data manifest has an invalid schema")
    entries = {
        str(entry.get("name")): entry
        for entry in manifest["files"]
        if isinstance(entry, dict)
    }
    frames: dict[str, pd.DataFrame] = {}
    for name, path in required.items():
        entry = entries.get(name)
        expected_relative = path.relative_to(base).as_posix()
        if (
            entry is None
            or entry.get("path") != expected_relative
            or type(entry.get("size")) is not int
            or type(entry.get("rows")) is not int
            or not isinstance(entry.get("sha256"), str)
        ):
            raise ValueError(f"Team 12 manifest binding is invalid for {name}")
        actual_size = path.stat().st_size
        if actual_size != entry["size"]:
            raise RuntimeError(
                f"Team 12 snapshot size drift for {name}: "
                f"{actual_size} != {entry['size']}"
            )
        actual_sha256 = sha256_file(path)
        if actual_sha256 != entry["sha256"]:
            raise RuntimeError(
                f"Team 12 snapshot hash drift for {name}: "
                f"{actual_sha256} != {entry['sha256']}"
            )
        frame = pd.read_parquet(path)
        if len(frame) != entry["rows"]:
            raise RuntimeError(
                f"Team 12 snapshot row-count drift for {name}: "
                f"{len(frame)} != {entry['rows']}"
            )
        frames[name] = frame

    return Team12MarketData(
        bars=frames["bars"],
        funding=frames["funding"],
        membership=frames["membership"],
        mark_prices=frames["mark_prices"],
        contract_metadata=frames["contract_metadata"],
    )


def historical_terminal_held_symbols(
    root: str | Path | None = None,
) -> tuple[str, ...]:
    """Return the exact held book entering the first live bridge boundary."""

    verify_frozen_authority(root)
    path = release_team_root(root) / "positions.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"missing Team 12 golden positions: {path}")
    actual_sha256 = sha256_file(path)
    if actual_sha256 != GOLDEN_POSITIONS_SHA256:
        raise RuntimeError(
            "Team 12 golden position drift: "
            f"{actual_sha256} != {GOLDEN_POSITIONS_SHA256}"
        )
    positions = _parquet_time_index(path)
    expected_terminal = HISTORICAL_END_EXCLUSIVE - pd.Timedelta(
        hours=INTERVAL_HOURS
    )
    if positions.index.max() != expected_terminal:
        raise RuntimeError("Team 12 golden positions end at the wrong boundary")
    terminal = positions.loc[expected_terminal].astype(float)
    if terminal.isna().any() or not terminal.map(math.isfinite).all():
        raise ValueError("Team 12 terminal golden positions are non-finite")
    return tuple(sorted(terminal.index[terminal.abs() > 1e-12].astype(str)))


def validate_market_data(
    data: Team12MarketData,
    *,
    end_exclusive: object,
) -> None:
    """Reject schema, rank, and terminal-coverage drift before a replay."""

    end = _utc(end_exclusive)
    required_bars = {
        "open_time",
        "symbol",
        "open",
        "close",
        "quote_volume",
        "trade_count",
        "taker_buy_quote_volume",
    }
    required_funding = {"funding_time", "symbol", "funding_rate", "mark_price"}
    required_membership = {
        "reconstitution_time",
        "symbol",
        "liquidity_rank",
        "trailing_quote_volume",
    }
    required_marks = {"mark_time", "symbol", "mark_price"}
    required_metadata = {
        "symbol",
        "contract_type",
        "quote_asset",
        "margin_asset",
        "is_crypto",
        "onboard_date",
        "delivery_date",
    }
    for label, frame, columns in (
        ("bars", data.bars, required_bars),
        ("funding", data.funding, required_funding),
        ("membership", data.membership, required_membership),
        ("mark prices", data.mark_prices, required_marks),
        ("contract metadata", data.contract_metadata, required_metadata),
    ):
        missing = columns - set(frame)
        if missing:
            raise ValueError(f"Team 12 {label} missing columns: {sorted(missing)}")
        if frame.empty:
            raise ValueError(f"Team 12 {label} is empty")
    if data.bars.duplicated(["open_time", "symbol"]).any():
        raise ValueError("Team 12 bars contain duplicate boundaries")
    if data.funding.duplicated(["funding_time", "symbol"]).any():
        raise ValueError("Team 12 funding contains duplicate settlements")
    if data.mark_prices.duplicated(["mark_time", "symbol"]).any():
        raise ValueError("Team 12 mark prices contain duplicate boundaries")
    if data.membership.duplicated(["reconstitution_time", "symbol"]).any():
        raise ValueError("Team 12 membership contains duplicate constituents")
    if data.contract_metadata["symbol"].duplicated().any():
        raise ValueError("Team 12 contract metadata contains duplicate symbols")

    bar_times = pd.to_datetime(data.bars["open_time"], utc=True, errors="raise")
    terminal = end - pd.Timedelta(hours=INTERVAL_HOURS)
    if terminal not in set(bar_times):
        raise ValueError(
            f"Team 12 bars do not contain the terminal decision boundary {terminal}"
        )
    membership_times = pd.to_datetime(
        data.membership["reconstitution_time"], utc=True, errors="raise"
    )
    for timestamp, group in data.membership.groupby(membership_times, observed=True):
        ranks = sorted(int(value) for value in group["liquidity_rank"])
        if len(group) != 12 or ranks != list(range(1, 13)):
            raise ValueError(
                f"Team 12 membership ranks are invalid at {timestamp}"
            )
    latest_membership = pd.to_datetime(
        data.membership["reconstitution_time"], utc=True, errors="raise"
    ).max()
    required_monday = (end - pd.Timedelta(nanoseconds=1)).normalize()
    required_monday -= pd.Timedelta(days=required_monday.weekday())
    if latest_membership < required_monday:
        raise ValueError(
            "Team 12 membership is stale: "
            f"{latest_membership.isoformat()} < {required_monday.isoformat()}"
        )


def run_replay(
    data: Team12MarketData,
    *,
    start: object = REPLAY_START,
    end_exclusive: object = HISTORICAL_END_EXCLUSIVE,
    cost_multipliers: Iterable[float] = (1.0, 2.0, 3.0),
) -> Team12Replay:
    """Run one uninterrupted causal replay through the frozen strategy and evaluator."""

    first = _utc(start)
    end = _utc(end_exclusive)
    if first != REPLAY_START:
        raise ValueError(
            "Team 12 is path-dependent; every replay must start at "
            f"{REPLAY_START.isoformat()}"
        )
    validate_market_data(data, end_exclusive=end)
    times = decision_grid(start=first, end_exclusive=end)
    strategy = build_frozen_strategy()
    policy = load_frozen_risk_policy()
    targets = generate_targets(
        strategy,
        data.bars,
        data.funding,
        data.membership,
        times,
        seed=STRATEGY_SEED,
        interval_hours=INTERVAL_HOURS,
    )
    # The tournament runner publishes the complete sorted contract universe,
    # including symbols whose target remains zero throughout the replay. Preserve
    # that schema here so reusable/live artifacts are structurally identical.
    target_symbols = sorted(set(data.bars["symbol"].astype(str)))
    targets = targets.reindex(
        columns=[REBALANCE_INSTRUCTION_COLUMN, *target_symbols],
        fill_value=0.0,
    )
    targets.index.name = "timestamp"
    targets.index = pd.DatetimeIndex(targets.index).as_unit("ns")
    targets[REBALANCE_INSTRUCTION_COLUMN] = targets[
        REBALANCE_INSTRUCTION_COLUMN
    ].astype(bool)

    unique_multipliers = tuple(dict.fromkeys(float(value) for value in cost_multipliers))
    if not unique_multipliers or any(
        not math.isfinite(value) or value <= 0.0 for value in unique_multipliers
    ):
        raise ValueError("cost multipliers must be finite and positive")
    evaluations: dict[float, EvaluationResult] = {}
    deferred_symbol_admissions = _live_deferred_symbol_admissions(
        data.bars,
        end_exclusive=end,
    )
    for multiplier in unique_multipliers:
        evaluation = evaluate_targets(
            data.bars,
            data.funding,
            data.membership,
            targets,
            mark_prices=data.mark_prices,
            config=EVALUATOR_CONFIG,
            cost_multiplier=multiplier,
            risk_policy=policy,
            deferred_symbol_admissions=deferred_symbol_admissions,
        )
        evaluation.returns.index.name = "timestamp"
        evaluation.returns.index = pd.DatetimeIndex(
            evaluation.returns.index
        ).as_unit("ns")
        evaluation.positions.index.name = "timestamp"
        evaluation.positions.index = pd.DatetimeIndex(
            evaluation.positions.index
        ).as_unit("ns")
        evaluations[multiplier] = evaluation
    return Team12Replay(
        decision_times=times,
        targets=targets,
        evaluations=evaluations,
    )


def _live_deferred_symbol_admissions(
    bars: pd.DataFrame,
    *,
    end_exclusive: pd.Timestamp,
) -> dict[str, pd.Timestamp]:
    """Freeze the activation universe and causally admit later listings.

    Historical tournament replays end before paper activation and retain their
    original global symbol schema.  Live replays bind the exact activation
    schema by count and hash; symbols first seen later enter only at their first
    bar, preventing a future listing from changing already-sealed reductions.
    """

    if end_exclusive <= LIVE_REPLAY_ACTIVATION_BOUNDARY:
        return {}
    first_seen = (
        bars.assign(open_time=pd.to_datetime(bars["open_time"], utc=True))
        .groupby(bars["symbol"].astype(str), observed=True)["open_time"]
        .min()
        .sort_index()
    )
    baseline_symbols = sorted(
        str(symbol)
        for symbol, timestamp in first_seen.items()
        if timestamp <= LIVE_REPLAY_ACTIVATION_BOUNDARY
    )
    baseline_payload = json.dumps(
        baseline_symbols,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    baseline_hash = hashlib.sha256(baseline_payload).hexdigest()
    if (
        len(baseline_symbols) != LIVE_REPLAY_BASELINE_SYMBOL_COUNT
        or baseline_hash != LIVE_REPLAY_BASELINE_SYMBOLS_SHA256
    ):
        raise RuntimeError(
            "Team 12 live replay baseline-symbol authority drift: "
            f"count={len(baseline_symbols)} sha256={baseline_hash}"
        )
    return {
        str(symbol): pd.Timestamp(timestamp)
        for symbol, timestamp in first_seen.items()
        if timestamp > LIVE_REPLAY_ACTIVATION_BOUNDARY
    }


def replay_summary(replay: Team12Replay) -> dict[str, object]:
    scenarios: dict[str, object] = {}
    for multiplier, result in sorted(replay.evaluations.items()):
        daily = aggregate_daily_returns(result.returns["net_return"])
        metrics = compute_window_metrics(daily)
        scenarios[f"{multiplier:g}x"] = {
            "start": daily.index.min().isoformat(),
            "end": daily.index.max().isoformat(),
            "observations": int(len(daily)),
            "cumulative_return": float((1.0 + daily).prod() - 1.0),
            "annualized_return": metrics.annualized_return,
            "net_sharpe": metrics.net_sharpe,
            "net_sortino": metrics.net_sortino,
            "max_drawdown": metrics.max_drawdown,
            "calmar": metrics.calmar,
            "positive_quarter_fraction": metrics.positive_quarter_fraction,
        }
    return {
        "schema_version": "team12-continuous-replay-v1",
        "candidate_id": CANDIDATE_ID,
        "decision_count": int(len(replay.decision_times)),
        "replay_start": replay.decision_times.min().isoformat(),
        "replay_end": replay.decision_times.max().isoformat(),
        "scenarios": scenarios,
    }


def verify_historical_parity(
    replay: Team12Replay,
    root: str | Path | None = None,
) -> dict[str, object]:
    """Prove exact logical equality to the one-shot continuous golden replay."""

    expected_grid = decision_grid()
    if not replay.decision_times.equals(expected_grid):
        raise ValueError("golden parity requires the complete historical decision grid")
    release = release_team_root(root)
    paths = {
        "targets": release / "targets.parquet",
        "positions": release / "positions.parquet",
        "bar_returns": release / "bar_returns.csv",
    }
    expected_hashes = {
        "targets": GOLDEN_TARGETS_SHA256,
        "positions": GOLDEN_POSITIONS_SHA256,
        "bar_returns": GOLDEN_BAR_RETURNS_SHA256,
    }
    for label, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"missing Team 12 golden {label}: {path}")
        actual = sha256_file(path)
        if actual != expected_hashes[label]:
            raise RuntimeError(
                f"Team 12 golden {label} drift: {actual} != {expected_hashes[label]}"
            )

    expected_targets = _parquet_time_index(paths["targets"])
    expected_positions = _parquet_time_index(paths["positions"])
    # The release uses 17-significant-digit CSV values. Pandas' default fast
    # parser can round those one ULP away from the original evaluator floats;
    # round_trip reconstructs the exact binary values that produced the file.
    expected_returns = pd.read_csv(
        paths["bar_returns"],
        float_precision="round_trip",
    )
    expected_returns["timestamp"] = pd.to_datetime(
        expected_returns["timestamp"], utc=True, errors="raise"
    )
    # The evaluator emits an empty string when no risk-policy reason applies.
    # CSV has no distinct representation for that value, so restore the
    # evaluator's exact string semantics after parsing the golden artifact.
    expected_returns["risk_policy_reasons"] = expected_returns[
        "risk_policy_reasons"
    ].fillna("")
    expected_returns = expected_returns.set_index("timestamp")
    expected_returns.index = expected_returns.index.as_unit("ns")
    result = replay.evaluation()
    pd.testing.assert_frame_equal(
        replay.targets,
        expected_targets,
        check_dtype=False,
        check_exact=True,
        check_names=True,
    )
    pd.testing.assert_frame_equal(
        result.positions,
        expected_positions,
        check_dtype=False,
        check_exact=True,
        check_names=True,
    )
    pd.testing.assert_frame_equal(
        result.returns,
        expected_returns,
        check_dtype=False,
        check_exact=True,
        check_names=True,
    )
    return {
        "status": "PASS",
        "decision_count": int(len(replay.decision_times)),
        "targets_sha256": expected_hashes["targets"],
        "positions_sha256": expected_hashes["positions"],
        "bar_returns_sha256": expected_hashes["bar_returns"],
    }


def write_replay_artifacts(replay: Team12Replay, output_dir: str | Path) -> Path:
    """Write a reusable, non-tournament replay bundle."""

    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    _indexed_frame(replay.targets).to_parquet(
        destination / "targets.parquet", engine="pyarrow", compression="zstd", index=False
    )
    for multiplier, result in sorted(replay.evaluations.items()):
        label = _cost_label(multiplier)
        _indexed_frame(result.positions).to_parquet(
            destination / f"{label}positions.parquet",
            engine="pyarrow",
            compression="zstd",
            index=False,
        )
        events = result.events.copy()
        if not events.empty and "timestamp" in events:
            events["timestamp"] = pd.to_datetime(events["timestamp"], utc=True)
        events.to_parquet(
            destination / f"{label}events.parquet",
            engine="pyarrow",
            compression="zstd",
            index=False,
        )
        _write_csv(_indexed_frame(result.returns), destination / f"{label}bar_returns.csv")
        daily = aggregate_daily_returns(result.returns["net_return"])
        _write_csv(
            pd.DataFrame({"date": daily.index, "net_return": daily.to_numpy()}),
            destination / f"{label}daily_returns.csv",
        )
    (destination / "summary.json").write_text(
        json.dumps(replay_summary(replay), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def _cost_label(multiplier: float) -> str:
    if multiplier == 1.0:
        return ""
    if multiplier == 2.0:
        return "double_cost_"
    if multiplier == 3.0:
        return "triple_cost_"
    return f"cost_{multiplier:g}x_"


def _indexed_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output.index = pd.to_datetime(output.index, utc=True)
    output = output.sort_index()
    output.index.name = "timestamp"
    return output.reset_index()


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    output = frame.copy()
    for column in output:
        if isinstance(output[column].dtype, pd.DatetimeTZDtype) or pd.api.types.is_datetime64_dtype(
            output[column].dtype
        ):
            timestamps = pd.to_datetime(output[column], utc=True)
            output[column] = (
                timestamps.dt.strftime("%Y-%m-%d")
                if column == "date"
                else timestamps.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            )
    output.to_csv(path, index=False, lineterminator="\n", float_format="%.17g")


def _sha256_file(path: Path) -> str:
    return sha256_file(path)


def _parquet_time_index(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    result = frame.set_index("timestamp")
    result.index = result.index.as_unit("ns")
    return result
