"""QuantStats tearsheets for the three winning desks and the ensemble, across three windows.

Books
    ``team-14``, ``team-08``, ``team-09`` -- the three individual desks -- and ``ensemble-eq3``.

    The ensemble is built by **combining target weights at one third each and evaluating the
    result as a single book**, not by averaging three return series. A desk running three
    strategies in one account nets their overlapping positions, so it trades less and pays less
    than the three run separately; averaging returns would charge costs three times over on
    positions that partly cancel. The return-level average is reported alongside so the size of
    that netting benefit is visible rather than assumed.

Windows
    ``is``    development, 2020-08-02 to 2024-02-01. In-sample for the organizer. Note that a
              lane only ever saw the 808 visible days of it; the 360 sealed days inside this
              window were held back from the teams and are included here.
    ``oos``   historical, 2024-02-01 to 2026-08-01. Out-of-sample for the lanes, and the window
              that ranked them. Contaminated for the organizer -- it is byte-identical to a prior
              edition's published leaderboard window -- so it authorizes nothing.
    ``full``  both, 2020-08-02 to 2026-08-01.

The benchmark is the equal-weight point-in-time member index: what the cross-section itself did,
without naming any single symbol. For a long/short book the useful question is not whether it beat
cash but whether it did something the index did not.

Usage::

    uv run python scripts/top40_v5_tearsheets.py
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.tournament.v5 import metrics
from crypto_trade.tournament.v5.engine import EvaluatorConfig, evaluate_targets, generate_targets
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

sys.path.insert(0, str(Path(__file__).resolve().parent))
from top40_v5_evaluate import INTERVAL_HOURS, REPO, SNAPSHOT, TOURNAMENT  # noqa: E402

WINNERS = ("team-14", "team-08", "team-09")
ENSEMBLE = "ensemble-eq3"

FULL_START = pd.Timestamp("2020-08-02", tz="UTC")
DEV_END = pd.Timestamp("2024-02-01", tz="UTC")
FULL_END = pd.Timestamp("2026-08-01", tz="UTC")

WINDOWS = {
    "is": (FULL_START, DEV_END),
    "oos": (DEV_END, FULL_END),
    "full": (FULL_START, FULL_END),
}

OUT = REPO / TOP40_V5_LAYOUT.reports_root / "tearsheets"


def _targets(team_id: str, data, decisions) -> pd.DataFrame:
    path = TOURNAMENT / "teams" / team_id / "outbox" / "candidate.py"
    spec = importlib.util.spec_from_file_location(f"ts_{team_id}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return generate_targets(
        module.build_strategy(),
        data["bars"],
        data["funding"],
        data["membership"],
        decisions,
        seed=42,
        interval_hours=INTERVAL_HOURS,
    )


def _combine(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """One third of each book's weights, summed. Overlapping positions net, as they would in one
    account."""

    reserved = [c for c in frames[0].columns if c.startswith("__")]
    numeric = [f.drop(columns=reserved, errors="ignore").astype(float) for f in frames]
    combined = sum(
        f.reindex(columns=sorted(set().union(*[set(f.columns) for f in numeric]))).fillna(0.0)
        for f in numeric
    ) / float(len(numeric))
    for column in reserved:
        # Rebalance where any constituent rebalanced; the desk acts when any of its books acts.
        combined[column] = np.logical_or.reduce([f[column].to_numpy() for f in frames])
    return combined


def _daily(targets: pd.DataFrame, data) -> pd.Series:
    result = evaluate_targets(
        data["bars"],
        data["funding"],
        data["membership"],
        targets,
        mark_prices=data["mark_prices"],
        config=EvaluatorConfig(),
        cost_multiplier=1.0,
    )
    return metrics.daily_returns(result.returns)


def _member_index(data) -> pd.Series:
    bars = data["bars"].copy()
    bars["open_time"] = pd.to_datetime(bars["open_time"], utc=True)
    members = set(data["membership"]["symbol"].astype(str).unique())
    frame = bars[bars["symbol"].astype(str).isin(members)]
    wide = frame.pivot_table(index="open_time", columns="symbol", values="close", aggfunc="last")
    returns = wide.sort_index().pct_change().replace([np.inf, -np.inf], np.nan)
    return ((1.0 + returns.mean(axis=1)).resample("1D").prod() - 1.0).dropna()


def main() -> int:
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-html", action="store_true", help="metrics only, no tearsheets")
    arguments = parser.parse_args()

    import quantstats as qs

    data = {
        name: pd.read_parquet(SNAPSHOT / f"{name}.parquet")
        for name in ("bars", "funding", "membership", "mark_prices")
    }
    decisions = list(
        pd.date_range(FULL_START, FULL_END, freq=f"{INTERVAL_HOURS}h", tz="UTC", inclusive="left")
    )
    print(f"full window {FULL_START.date()} -> {FULL_END.date()}, {len(decisions)} decisions\n")

    cache = OUT / "daily-returns.parquet"
    OUT.mkdir(parents=True, exist_ok=True)
    if cache.is_file():
        stored = pd.read_parquet(cache)
        series = {c: stored[c].dropna() for c in stored.columns}
        print(f"  reusing cached daily returns for {list(series)}", flush=True)
    else:
        frames, series = {}, {}
        for team_id in WINNERS:
            started = time.monotonic()
            frames[team_id] = _targets(team_id, data, decisions)
            series[team_id] = _daily(frames[team_id], data)
            print(
                f"  {team_id:12s} evaluated [{(time.monotonic() - started) / 60:.1f}m]", flush=True
            )
        started = time.monotonic()
        series[ENSEMBLE] = _daily(_combine([frames[t] for t in WINNERS]), data)
        print(f"  {ENSEMBLE:12s} evaluated [{(time.monotonic() - started) / 60:.1f}m]", flush=True)
        pd.DataFrame(series).to_parquet(cache)

    # The naive alternative, for comparison only: average the three return streams. This is what
    # running the books in three separate accounts would give, paying costs on positions that would
    # otherwise have netted.
    unnetted = sum(series[t] for t in WINNERS) / 3.0

    benchmark = _member_index(data)
    OUT.mkdir(parents=True, exist_ok=True)

    header = (
        f"\n{'book':18s} {'window':6s} {'days':>5} {'sharpe':>7}"
        f" {'cagr':>8} {'maxdd':>7} {'sortino':>8}"
    )
    print(header)
    for name, daily in list(series.items()) + [("ensemble-unnetted", unnetted)]:
        for window, (start, end) in WINDOWS.items():
            sliced = daily[(daily.index >= start) & (daily.index < end)]
            if len(sliced) < 30:
                continue
            sharpe = qs.stats.sharpe(sliced)
            print(
                f"{name:14s} {window:6s} {len(sliced):5d} {sharpe:>7.3f} "
                f"{qs.stats.cagr(sliced):>8.3f} {qs.stats.max_drawdown(sliced):>7.3f} "
                f"{qs.stats.sortino(sliced):>8.3f}"
            )
            if arguments.skip_html or name == "ensemble-unnetted":
                continue
            target = OUT / f"{name}-{window}.html"
            bench = benchmark[(benchmark.index >= start) & (benchmark.index < end)]
            # QuantStats compares the index against tz-naive timestamps internally, so a UTC-aware
            # index raises. Strip the zone for reporting only; the arithmetic is already done.
            naive = sliced.copy()
            naive.index = naive.index.tz_localize(None)
            bench_naive = bench.copy()
            bench_naive.index = bench_naive.index.tz_localize(None)
            try:
                qs.reports.html(
                    naive,
                    benchmark=bench_naive if len(bench_naive) == len(naive) else None,
                    output=str(target),
                    title=f"Top-40 V5 — {name} — {window.upper()}",
                    download_filename=str(target),
                )
            except Exception as error:  # noqa: BLE001
                print(f"    tearsheet failed for {name}-{window}: {type(error).__name__}: {error}")

    if not arguments.skip_html:
        print(f"\nwrote tearsheets to {OUT.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
