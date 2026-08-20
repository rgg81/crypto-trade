"""The risk unit has to reach the scored path, not merely exist.

Every replay fixture in the suite is two or three boundaries long, which is inside the unit's
warm-up, so a scalar that never fired would leave them all green.  This runs a long synthetic
snapshot end to end and measures the volatility the book actually delivers.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup50v2.common_risk import BARS_PER_YEAR
from crypto_trade.cup50v2.replay import ExecutionConfig, run_candidate
from crypto_trade.cup50v2.snapshot import Snapshot

SYMBOLS = ("AUSDT", "BUSDT", "CUSDT", "DUSDT")


def _snapshot(sigma: float, periods: int = 900, seed: int = 11) -> Snapshot:
    generator = np.random.default_rng(seed)
    start = pd.Timestamp("2023-01-02T00:00:00Z")
    open_times = pd.date_range(start, periods=periods, freq="8h", tz="UTC")
    bars, funding, marks, membership = [], [], [], []
    for symbol in SYMBOLS:
        close = 100.0 * np.exp(np.cumsum(generator.normal(0.0, sigma, size=periods)))
        opens = np.concatenate(([100.0], close[:-1]))
        bars.append(
            pd.DataFrame(
                {
                    "open_time": open_times,
                    "close_time": open_times + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
                    "symbol": symbol,
                    "open": opens,
                    "close": close,
                    "quote_volume": 1e12,
                }
            )
        )
        funding.append(
            pd.DataFrame(
                {
                    "funding_time": open_times,
                    "symbol": symbol,
                    "funding_rate": 0.0,
                    "mark_price": close,
                }
            )
        )
        marks.append(pd.DataFrame({"mark_time": open_times, "symbol": symbol, "mark_price": close}))
    for boundary in pd.date_range(start, open_times[-1], freq="7D", tz="UTC"):
        for rank, symbol in enumerate(SYMBOLS, start=1):
            membership.append([boundary, symbol, rank, 1e11])
    return Snapshot(
        pd.concat(bars, ignore_index=True),
        pd.concat(funding, ignore_index=True),
        pd.concat(marks, ignore_index=True),
        pd.DataFrame(
            membership,
            columns=[
                "reconstitution_time",
                "symbol",
                "liquidity_rank",
                "median_daily_quote_volume",
            ],
        ),
        pd.DataFrame({"symbol": list(SYMBOLS)}),
        "x" * 64,
        open_times[0],
        open_times[-1],
        True,
    )


class EqualWeightLong:
    """A fully invested book, so its size is the risk unit's decision alone."""

    def target_weights(self, context, *, seed):
        eligible = [symbol for symbol in context.eligible_symbols if symbol in context.bars]
        if not eligible:
            return {}
        return {symbol: 1.0 / len(eligible) for symbol in eligible}


def _annualized_volatility(replay) -> float:
    gross = replay.costs[1].returns["gross_return"].to_numpy(dtype=float)
    warm = gross[300:]
    return float(np.std(warm, ddof=1)) * math.sqrt(BARS_PER_YEAR)


def test_a_volatile_book_is_scaled_down_onto_the_common_target() -> None:
    snapshot = _snapshot(0.02)
    replay = run_candidate(
        EqualWeightLong(),
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
        seed=1,
    )
    config = ExecutionConfig()
    assert _annualized_volatility(replay) == pytest.approx(config.risk_target, rel=0.35)

    scalars = replay.risk_scalars
    warm = config.risk_minimum_symbol_bars
    # Neutral until a book symbol has enough observations to estimate, then live: the unit
    # estimates from whatever part of the window has closed rather than waiting for all of it.
    assert (scalars.iloc[:warm] == 1.0).all(), "warm-up must be neutral"
    assert (scalars.iloc[warm + 5 :] < 1.0).all(), "a wild panel must be sized down"
    assert scalars.iloc[400:].nunique() > 1, "the unit must respond to the panel"


def test_a_calm_book_is_held_at_the_gross_ceiling_rather_than_grown_onto_the_target() -> None:
    """The unit asks for more size than the caps allow, and the caps win.

    This is a real limit of the design, not a defect: a book calm enough to want more than full
    gross cannot reach the common target, so its drawdowns are smaller than a like-for-like
    comparison would suggest. Recording it here keeps it from being rediscovered as a surprise.
    """
    snapshot = _snapshot(0.005)
    replay = run_candidate(
        EqualWeightLong(),
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
        seed=1,
    )
    config = ExecutionConfig()
    achieved = _annualized_volatility(replay)
    scalars = replay.risk_scalars
    warm = config.risk_minimum_symbol_bars

    assert (scalars.iloc[warm + 5 :] > 1.0).all(), "the unit wants to grow this book"
    assert achieved < config.risk_target
    gross = replay.costs[1].returns["gross_exposure"].iloc[400:]
    # With four names the per-symbol ceiling binds before the gross one, so the book tops out at
    # 0.80 rather than 1.00. A concentrated book is therefore capped harder than a diversified one.
    ceiling = min(config.max_gross_exposure, len(SYMBOLS) * config.max_symbol_exposure)
    assert gross.max() <= ceiling + 1e-9
    assert gross.iloc[-1] == pytest.approx(ceiling, rel=1e-6)


def test_a_calmer_panel_is_sized_larger_than_a_wilder_one() -> None:
    calm = run_candidate(
        EqualWeightLong(),
        snapshot=_snapshot(0.005),
        start=_snapshot(0.005).window_start,
        end=_snapshot(0.005).window_end,
        seed=1,
    )
    wild = run_candidate(
        EqualWeightLong(),
        snapshot=_snapshot(0.02),
        start=_snapshot(0.02).window_start,
        end=_snapshot(0.02).window_end,
        seed=1,
    )
    assert float(calm.risk_scalars.iloc[-1]) > float(wild.risk_scalars.iloc[-1])


def test_the_replay_no_longer_carries_a_calibration_pass() -> None:
    """The zero-cost pass existed only to feed the realised-volatility unit."""
    snapshot = _snapshot(0.01, periods=320)
    replay = run_candidate(
        EqualWeightLong(),
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
        seed=1,
    )
    assert not hasattr(replay, "calibration")
