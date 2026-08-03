"""All-period reporting for the frozen Team 12 continuous replay."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.backtest_report import generate_html_report
from crypto_trade.team12.authority import (
    CANDIDATE_ID,
    GOLDEN_DAILY_RETURNS_SHA256,
    release_team_root,
    sha256_file,
    verify_frozen_authority,
)
from crypto_trade.team12.backtest import (
    HISTORICAL_END_EXCLUSIVE,
    IS_CONFIRMATION_END_EXCLUSIVE,
    IS_END_EXCLUSIVE,
    REPLAY_START,
)
from crypto_trade.tournament.metrics_v3 import compute_window_metrics

REPORT_TITLE = (
    "Team 12 — Continuous IS + Confirmation + Historical OOS "
    "(2020-08-03 through 2026-06-30)"
)


def load_released_daily_returns(root: str | Path | None = None) -> pd.Series:
    """Load the immutable all-period return stream from the atomic release."""

    verify_frozen_authority(root)
    path = release_team_root(root) / "daily_returns.csv"
    if not path.is_file():
        raise FileNotFoundError(f"missing Team 12 released daily returns: {path}")
    actual_sha256 = sha256_file(path)
    if actual_sha256 != GOLDEN_DAILY_RETURNS_SHA256:
        raise RuntimeError(
            "Team 12 released daily-return drift: "
            f"{actual_sha256} != {GOLDEN_DAILY_RETURNS_SHA256}"
        )
    frame = pd.read_csv(path)
    if set(frame) != {"date", "net_return"}:
        raise ValueError(f"unexpected Team 12 daily-return schema: {list(frame)}")
    series = pd.Series(
        pd.to_numeric(frame["net_return"], errors="raise").to_numpy(),
        index=pd.to_datetime(frame["date"], utc=True, errors="raise"),
        name="net_return",
        dtype=float,
    )
    validate_all_period_returns(series)
    return series


def validate_all_period_returns(returns: pd.Series) -> None:
    """Require the exact gap-free IS + OOS calendar without a path reset."""

    if not isinstance(returns.index, pd.DatetimeIndex):
        raise TypeError("Team 12 daily returns require a DatetimeIndex")
    series = pd.Series(returns, dtype=float).copy()
    series.index = pd.to_datetime(series.index, utc=True)
    expected = pd.date_range(
        REPLAY_START.normalize(),
        HISTORICAL_END_EXCLUSIVE - pd.Timedelta(days=1),
        freq="1D",
        tz="UTC",
    )
    if not series.index.is_unique:
        raise ValueError("Team 12 daily returns contain duplicate dates")
    if not series.index.equals(expected):
        raise ValueError(
            "Team 12 daily returns must be one gap-free continuous stream from "
            f"{expected[0].date()} through {expected[-1].date()}"
        )
    values = series.to_numpy()
    if not np.isfinite(values).all() or (values <= -1.0).any():
        raise ValueError("Team 12 daily returns contain invalid values")


def _normalized_all_period_returns(returns: pd.Series) -> pd.Series:
    validate_all_period_returns(returns)
    series = pd.Series(returns, dtype=float, name="net_return").copy()
    series.index = pd.to_datetime(series.index, utc=True)
    return series


def period_statistics(returns: pd.Series) -> dict[str, object]:
    """Return exact compounded statistics for full, IS, and historical OOS."""

    returns = _normalized_all_period_returns(returns)
    windows = {
        "all_periods": returns,
        "is": returns.loc[returns.index < IS_END_EXCLUSIVE],
        "is_confirmation": returns.loc[
            (returns.index >= IS_END_EXCLUSIVE)
            & (returns.index < IS_CONFIRMATION_END_EXCLUSIVE)
        ],
        "historical_oos": returns.loc[
            returns.index >= IS_CONFIRMATION_END_EXCLUSIVE
        ],
    }
    result: dict[str, object] = {}
    for label, window in windows.items():
        metrics = compute_window_metrics(window)
        result[label] = {
            "start": window.index.min().date().isoformat(),
            "end": window.index.max().date().isoformat(),
            "observations": int(len(window)),
            "cumulative_return": float((1.0 + window).prod() - 1.0),
            **dataclasses.asdict(metrics),
        }
    return result


def generate_all_period_report(
    returns: pd.Series,
    output_dir: str | Path,
    *,
    source: str,
) -> dict[str, Path]:
    """Write the daily stream, split statistics, and compounded QuantStats HTML."""

    returns = _normalized_all_period_returns(returns)
    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    daily_path = destination / "team12-all-periods-daily-returns.csv"
    metrics_path = destination / "team12-all-periods-statistics.json"
    html_path = destination / "team12-all-periods-quantstats.html"

    daily = pd.DataFrame(
        {
            "date": returns.index.strftime("%Y-%m-%d"),
            "net_return": returns.to_numpy(),
            "period": np.select(
                [
                    returns.index < IS_END_EXCLUSIVE,
                    returns.index < IS_CONFIRMATION_END_EXCLUSIVE,
                ],
                ["IS", "IS confirmation"],
                default="historical OOS",
            ),
        }
    )
    daily.to_csv(daily_path, index=False, lineterminator="\n", float_format="%.17g")

    authority = verify_frozen_authority()
    input_payload = json.dumps(
        [
            [timestamp.strftime("%Y-%m-%d"), float(value)]
            for timestamp, value in returns.items()
        ],
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    payload = {
        "schema_version": "team12-all-periods-report-v1",
        "candidate_id": CANDIDATE_ID,
        "source": source,
        "continuous_replay": True,
        "compounded": True,
        "is_end_exclusive": IS_END_EXCLUSIVE.isoformat(),
        "is_confirmation_end_exclusive": IS_CONFIRMATION_END_EXCLUSIVE.isoformat(),
        "strategy_sha256": authority.strategy_sha256,
        "risk_policy_sha256": authority.risk_policy_sha256,
        "source_bundle_sha256": authority.source_bundle_sha256,
        "source_archive_sha256": authority.source_archive_sha256,
        "dependency_lock_sha256": authority.dependency_lock_sha256,
        "data_manifest_sha256": authority.data_manifest_sha256,
        "evaluator_authority_sha256": authority.evaluator_authority_sha256,
        "pure_crypto_policy_sha256": authority.pure_crypto_policy_sha256,
        "deployment_bundle_sha256": authority.deployment_bundle_sha256,
        "deployment_manifest_sha256": authority.deployment_manifest_sha256,
        "deployment_git_commit": authority.deployment_git_commit,
        "input_daily_returns_sha256": hashlib.sha256(input_payload).hexdigest(),
        "report_daily_csv_sha256": sha256_file(daily_path),
        "statistics": period_statistics(returns),
    }
    metrics_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # QuantStats is most reliable with a timezone-naive daily index. Removing
    # the UTC annotation does not change any date or return.
    quantstats_returns = returns.copy()
    quantstats_returns.index = quantstats_returns.index.tz_convert(None)
    generate_html_report(
        quantstats_returns,
        html_path,
        title=REPORT_TITLE,
        compounded=True,
    )
    return {
        "daily_returns": daily_path,
        "statistics": metrics_path,
        "quantstats": html_path,
    }
