#!/usr/bin/env python3
"""Observational digest for the CUP-20 winner's paper desk. A test result, not an alert.

This script reports what the forward window did. It states no verdict, applies no threshold and
compares nothing to a floor: the desk exists to find out how the holdout winner behaves on data
nobody has seen, and a number that arrives pre-judged is a number that has stopped being evidence.
Anything that *is* an alert -- a drifted artifact, a moved pin, a dead engine -- belongs to
``scripts/cup20_paper_healthcheck.py`` and is deliberately absent here.

**Only the ``official`` phase is summarised.** Boundaries between the sealed window's end and the
first Monday after the desk's first tick are an UNSCORED BRIDGE: they exist so the book is already
formed when observation opens, and folding them into a statistic would report the desk's warm-up as
its result. They are excluded from every number below and reported as a count of their own.

**Nothing here recomputes an execution number.** Every input is a row the tournament's own
evaluator produced and the tick recorded; this script groups, compounds and averages them. The
compounding and the risk statistics are the tournament's own ``crypto_trade.cup20.metrics``
functions, applied to the official rows -- reused rather than restated, so the forward Sharpe is
computed by the same lines that computed the holdout Sharpe.

**Below ninety official bars the whole result is labelled INSUFFICIENT**, and the label says what
it is insufficient FOR: ninety 8h bars is thirty days, which is roughly the point at which a Sharpe
estimate stops being dominated by its own standard error. Shorter windows are printed, because
watching them is the job, but they do not support an inference about forward performance.
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
import types
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crypto_trade.cup20.metrics import daily_returns, window_metrics  # noqa: E402
from crypto_trade.cup20_desk.live_data import conform_frame  # noqa: E402
from crypto_trade.cup20_desk.tick import (  # noqa: E402
    BRIDGE,
    FILL_SCHEMA,
    FORWARD_RETURN_SCHEMA,
    LEDGER_DIRNAME,
    OFFICIAL,
)

DEFAULT_DESK_DIR = ROOT / "paper-cup20"

MINIMUM_OFFICIAL_BARS = 90
"""Thirty days on the 8h grid. Below it the digest is labelled INSUFFICIENT."""

BARS_PER_DAY = 3


@dataclasses.dataclass(frozen=True, slots=True)
class Digest:
    """Summary statistics over the recorded official rows. Every field is a description."""

    official_bars: int
    official_days: int
    bridge_bars: int
    official_fills: int
    bridge_fills: int
    first_official: str
    last_official: str
    cumulative_return: float
    annualized_return: float
    net_sharpe: float
    max_drawdown: float
    total_turnover: float
    annualized_turnover: float
    mean_gross_exposure: float
    mean_net_exposure: float
    mean_long_exposure: float
    mean_short_exposure: float
    positive_bars: int
    positive_days: int
    recorded_fees: float
    recorded_slippage: float

    @property
    def sufficient(self) -> bool:
        return self.official_bars >= MINIMUM_OFFICIAL_BARS

    def render(self) -> str:
        lines = ["=== CUP-20 winner (team-02 channel-position-ls) - forward observation ==="]
        if not self.sufficient:
            lines.append(
                f"INSUFFICIENT: {self.official_bars} official 8h bars, below the "
                f"{MINIMUM_OFFICIAL_BARS} ({MINIMUM_OFFICIAL_BARS // BARS_PER_DAY} days) this "
                "desk treats as the shortest window that supports an inference about forward "
                "performance. The numbers below are insufficient for a Sharpe, a drawdown or a "
                "turnover estimate; they are printed to be watched, not read as a result."
            )
        lines.append(
            f"official window: {self.official_bars} bars / {self.official_days} days"
            + (f"  {self.first_official} -> {self.last_official}" if self.official_bars else "")
        )
        lines.append(
            f"unscored bridge rows excluded from every statistic: {self.bridge_bars} bars, "
            f"{self.bridge_fills} fills"
        )
        lines.append(
            f"return: cumulative {self.cumulative_return:+.4%}  "
            f"annualized {self.annualized_return:+.4%}"
        )
        lines.append(
            f"daily-annualized Sharpe {self.net_sharpe:+.3f}  max drawdown {self.max_drawdown:.4%}"
        )
        lines.append(
            f"turnover: {self.total_turnover:.4f} total, {self.annualized_turnover:.3f} annualized"
        )
        lines.append(
            f"exposure means: gross {self.mean_gross_exposure:.4f}  "
            f"net {self.mean_net_exposure:+.4f}  long {self.mean_long_exposure:.4f}  "
            f"short {self.mean_short_exposure:+.4f}"
        )
        lines.append(
            f"positive periods: {self.positive_bars}/{self.official_bars} bars, "
            f"{self.positive_days}/{self.official_days} days"
        )
        lines.append(
            f"recorded costs over the window: fees {self.recorded_fees:.2f}, "
            f"slippage {self.recorded_slippage:.2f} (as the evaluator wrote them)"
        )
        lines.append(f"official fills recorded: {self.official_fills}")
        return "\n".join(lines)


def _read(path: Path, schema) -> pd.DataFrame:
    if not path.is_file():
        return conform_frame(schema, pd.DataFrame(columns=list(schema.columns)))
    return conform_frame(schema, pd.read_parquet(path))


def summarise(desk_root: str | Path) -> Digest:
    """Summarise the official phase of the desk's append-invariant forward record."""
    root = Path(desk_root)
    forward = _read(root / LEDGER_DIRNAME / "forward_returns.parquet", FORWARD_RETURN_SCHEMA)
    fills = _read(root / LEDGER_DIRNAME / "paper_fills.parquet", FILL_SCHEMA)

    official = forward.loc[forward["phase"] == OFFICIAL].reset_index(drop=True)
    bridge_bars = int((forward["phase"] == BRIDGE).sum())
    official_fills = int((fills["phase"] == OFFICIAL).sum())
    bridge_fills = int((fills["phase"] == BRIDGE).sum())

    # The tournament's own metric implementations, applied to the official rows. `window_metrics`
    # and `daily_returns` read exactly two attributes of an evaluation, so a namespace carrying
    # those two is enough -- and reusing them means the forward Sharpe and the holdout Sharpe are
    # computed by the same lines rather than by two implementations that can disagree.
    evaluation = types.SimpleNamespace(
        returns=official.set_index("timestamp"),
        events=fills.loc[fills["phase"] == OFFICIAL],
    )
    # Before the first official bar there is nothing to summarise, and the tournament's
    # `window_metrics` cannot be asked: on an empty window `daily_returns` returns a Series whose
    # index is a bare RangeIndex, and the quarterly grouping inside `window_metrics` calls
    # `tz_convert` on it and raises. That happens twice in a desk's life -- before the first tick,
    # and throughout the unscored bridge -- and both are ordinary states, not failures. The fix
    # belongs here rather than in `crypto_trade.cup20.metrics`, which is hash-bound by the
    # activation freeze: the digest simply declines to ask a question the official window cannot
    # answer yet, and reports zeros with `official_bars == 0` saying why.
    if official.empty:
        daily = pd.Series(dtype=float)
        metrics = types.SimpleNamespace(
            annualized_return=0.0,
            net_sharpe=0.0,
            max_drawdown=0.0,
            annualized_turnover=0.0,
        )
    else:
        daily = daily_returns(evaluation)
        metrics = window_metrics(evaluation)
    net = official["net_return"].astype(float)
    growth = float((1.0 + net).prod()) if len(net) else 1.0

    return Digest(
        official_bars=int(len(official)),
        official_days=int(len(daily)),
        bridge_bars=bridge_bars,
        official_fills=official_fills,
        bridge_fills=bridge_fills,
        first_official=official["timestamp"].min().isoformat() if len(official) else "-",
        last_official=official["timestamp"].max().isoformat() if len(official) else "-",
        cumulative_return=growth - 1.0,
        annualized_return=metrics.annualized_return,
        net_sharpe=metrics.net_sharpe,
        max_drawdown=metrics.max_drawdown,
        total_turnover=float(official["turnover"].astype(float).sum()),
        annualized_turnover=metrics.annualized_turnover,
        mean_gross_exposure=_mean(official, "gross_exposure"),
        mean_net_exposure=_mean(official, "net_exposure"),
        mean_long_exposure=_mean(official, "long_exposure"),
        mean_short_exposure=_mean(official, "short_exposure"),
        positive_bars=int((net > 0.0).sum()),
        positive_days=int((daily > 0.0).sum()),
        recorded_fees=float(official["fees"].astype(float).sum()),
        recorded_slippage=float(official["slippage"].astype(float).sum()),
    )


def _mean(frame: pd.DataFrame, column: str) -> float:
    values = frame[column].astype(float)
    return float(values.mean()) if len(values) else 0.0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CUP-20 winner paper-desk observational digest (official phase only)"
    )
    parser.add_argument("--desk-dir", type=Path, default=DEFAULT_DESK_DIR)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.desk_dir.resolve()
    print(f"desk {root}", flush=True)
    print(summarise(root).render(), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
