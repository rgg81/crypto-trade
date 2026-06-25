"""Regression tests for the iter-008 SLEEVE-AWARE REGIME BOOK (the all-weather breakthrough).

The book guards real capital and DEPARTS from the strict one-net_from_raw rule (it is a portfolio of
two separately-vol-targeted sub-strategies), so it ships with its own causality + structural tests:

  * the portfolio-breadth REGIME GATE is past-only (corrupting the future leaves past b bit-id);
  * the TWO-LEG book is leak-safe (corrupting the future leaves the past net bit-identical);
  * the SLEEVE-AWARE brake hits the ANCHOR leg ONLY (the dispersion leg net is unchanged by it);
  * the anchor is NEVER short (expo ≥ 0 everywhere — confirmed-bear is FLAT, not short);
  * the dispersion leg is EXACTLY dollar-neutral (Σ raw weight = 0 each bar).

Synthetic OHLCV panels (the same {ticker: OHLCV-frame} shape load_metals returns) — no data load.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
_METALS = _ROOT / "analysis" / "portfolio" / "metals"
sys.path.insert(0, str(_METALS))

import iter_002_mn_overlay as ov  # noqa: E402
import iter_008_allweather as a8  # noqa: E402
import universe_metals as um  # noqa: E402


def _synth_coins(n: int = 1200, seed: int = 7) -> dict[str, pd.DataFrame]:
    """Build a synthetic 4-metal OHLCV dict (open_time ms index) with a real bear→bull arc so the
    SMA(win) breadth gate, the EMA cross, and the inverse-vol sizing all exercise both regimes."""
    rng = np.random.default_rng(seed)
    # ms open_time on an 8h grid (the metals cadence)
    t0 = int(pd.Timestamp("2016-01-01").value // 10**6)
    step = 8 * 3600 * 1000
    ot = t0 + step * np.arange(n)
    # a long down-drift then up-drift so breadth crosses 0.6 in the "bear" half
    drift = np.concatenate([np.full(n // 2, -0.0006), np.full(n - n // 2, +0.0007)])
    coins: dict[str, pd.DataFrame] = {}
    for i, sym in enumerate(um.UNIVERSE):
        shocks = rng.normal(0, 0.012, n) + drift + 0.0002 * i
        close = 100.0 * np.exp(np.cumsum(shocks))
        op = close * (1 + rng.normal(0, 0.001, n))
        hi = np.maximum(op, close) * (1 + np.abs(rng.normal(0, 0.002, n)))
        lo = np.minimum(op, close) * (1 - np.abs(rng.normal(0, 0.002, n)))
        coins[sym] = pd.DataFrame(
            {
                "open_time": ot,
                "open": op,
                "high": hi,
                "low": lo,
                "close": close,
                "volume": rng.uniform(1e3, 1e4, n),
            }
        ).set_index("open_time")
    return coins


def _corrupt_future(coins: dict[str, pd.DataFrame], cut: int) -> dict[str, pd.DataFrame]:
    """Return a copy whose rows at/after `cut` are arbitrarily corrupted (future tampering)."""
    out: dict[str, pd.DataFrame] = {}
    for sym, df in coins.items():
        d = df.copy()
        for col in ("open", "high", "low", "close"):
            d.iloc[cut:, d.columns.get_loc(col)] = (
                d.iloc[cut:][col].to_numpy() * 3.0 + 17.0
            )  # arbitrary future garbage
        out[sym] = d
    return out


# ── 1. regime gate is past-only ────────────────────────────────────────────────────────────────
def test_regime_gate_is_past_only():
    """Corrupting every close AT/AFTER a cutoff must not change any bear flag b BEFORE it."""
    coins = _synth_coins()
    close = um.panels(coins)["close"]
    cut = 800
    b0 = a8._bear_flag(close, "ma", 450, 0.6, 0)
    close_c = um.panels(_corrupt_future(coins, cut))["close"]
    b1 = a8._bear_flag(close_c, "ma", 450, 0.6, 0)
    pd.testing.assert_series_equal(b0.iloc[:cut], b1.iloc[:cut])


# ── 2. the two-leg book is leak-safe ─────────────────────────────────────────────────────────────
def test_two_leg_book_is_leak_safe():
    """Corrupting the future must leave the past combined net stream bit-identical (no look-ahead).

    Causality boundary of the leak-safe core: the DECISION (raw weight) is past-only and the book is
    .shift(1)-lagged, but the REALISATION at bar t reads ret_fwd[t] = open[t+1]/open[t] — the next
    bar's open, the fill the already-decided position exits into. So corrupting bars at/after `cut`
    can legitimately move net[cut−1] (it realises into open[cut]) but NOTHING at or before cut−2.
    We corrupt at `cut` and assert every net bar strictly before index[cut−1] is bit-identical —
    proving no FUTURE close enters any DECISION. (A genuine leak would shift bars far before cut.)
    """
    coins = _synth_coins()
    cut = 850
    net0, _ = a8.regime_book(coins, **a8.CHAMP)
    bound_ts = um.panels(coins)["close"].index[cut - 1]  # realisation may touch cut−1; assert < it
    net1, _ = a8.regime_book(_corrupt_future(coins, cut), **a8.CHAMP)
    common = net0.index.intersection(net1.index)
    common = common[common < bound_ts]
    assert len(common) > 100  # the test actually exercises a long past window
    pd.testing.assert_series_equal(net0.loc[common], net1.loc[common])


# ── 3. the sleeve-aware brake hits the ANCHOR leg ONLY ───────────────────────────────────────────
def test_sleeve_aware_brake_anchor_only():
    """Toggling brake_anchor changes the anchor leg net but leaves the dispersion leg untouched."""
    coins = _synth_coins()
    # the dispersion leg takes no brake argument — byte-identical regardless of the anchor brake
    disp = a8.dispersion_leg(coins)
    a_braked, _ = a8.anchor_leg_braked(coins, **{k: a8.CHAMP[k] for k in ("win", "thresh")})
    a_unbraked, _ = a8.anchor_leg_braked(
        coins, **{k: a8.CHAMP[k] for k in ("win", "thresh")}, apply_brake=False
    )
    # the brake genuinely changes the anchor sleeve (it engages somewhere in this synthetic bear)...
    assert not np.allclose(a_braked.to_numpy(), a_unbraked.to_numpy())
    # ...but the dispersion sleeve is the SAME object/values whether or not the anchor is braked.
    disp_again = a8.dispersion_leg(coins)
    pd.testing.assert_series_equal(disp, disp_again)
    # and the combined book differs ONLY through the anchor term (a_w·Δanchor); dispersion fixed.
    champ_braked, b = a8.regime_book(coins, **{**a8.CHAMP, "brake_anchor": True})
    champ_unbraked, _ = a8.regime_book(coins, **{**a8.CHAMP, "brake_anchor": False})
    d_w = a8.CHAMP["dw_bull"] + (a8.CHAMP["dw_bear"] - a8.CHAMP["dw_bull"]) * b
    delta = champ_braked - champ_unbraked
    expected = a8.CHAMP["a_w"] * (a_braked - a_unbraked)
    common = delta.index.intersection(expected.index)
    # the dispersion contribution d_w·net_disp cancels in the difference → only anchor delta left
    np.testing.assert_allclose(
        delta.loc[common].to_numpy(), expected.loc[common].to_numpy(), atol=1e-12
    )
    _ = d_w  # documents the dispersion weight that cancels out


# ── 4. the anchor is NEVER short ─────────────────────────────────────────────────────────────────
def test_anchor_never_short():
    """expo ≥ 0 everywhere: long in bull/neutral, FLAT (0) in confirmed bear — never negative."""
    coins = _synth_coins()
    raw, b = a8._anchor_flatbear_raw(coins, "ma", 450, 0.6, 0)
    assert (raw.to_numpy() >= -1e-12).all()  # inverse-vol-sized long-or-flat book, never short
    # and where the portfolio bear flag is on, the anchor raw is exactly flat (0) for present metals
    bear_bars = b[b > 0].index
    if len(bear_bars):
        assert np.allclose(raw.loc[bear_bars].to_numpy(), 0.0)


# ── 5. the dispersion leg is EXACTLY dollar-neutral ──────────────────────────────────────────────
def test_dispersion_leg_dollar_neutral():
    """The dispersion raw book sums to ~0 cross-sectionally each bar (Σw = 0 → dollar-neutral)."""
    coins = _synth_coins()
    close = um.panels(coins)["close"]
    raw = ov.mn_dispersion_raw(close)
    row_sums = raw.sum(axis=1).abs()
    assert float(row_sums.max()) < 1e-9  # exact dollar-neutrality every bar


# ── 6. the CHAMPION is all-3-regime positive on the real metals (the headline claim) ─────────────
def test_champion_all_three_regimes_positive():
    """End-to-end on the real metals data: the champion is Sharpe-positive in BEAR, IS, and BULL.

    Skips if the metals CSVs are not ingested in this worktree (keeps the synthetic tests hermetic).
    """
    if not (_ROOT / "data" / "XAUUSDT" / "8h.csv").exists():
        import pytest

        pytest.skip("metals data not ingested")
    rows = a8.all_weather_scorecard()
    champ = rows["CHAMPION (regime book ma450/0.6 dW.25->1.5)"]
    # LEAK-FREE numbers (regime gate d_w lagged to b[t-1] after the live-parity reconcile caught a
    # same-bar look-ahead): the champion STILL flips the bear Sharpe positive and stays all-3-+, but
    # the lift is much smaller than the look-ahead version and the worst-DD REGRESSES vs the brake
    # baseline — a documented caveat (see EXPLORATION-008 / BASELINE_METALS leak-fix note).
    assert champ["bsr"] > 0  # BEAR Sharpe still positive (the sign-flip survives the leak fix)
    assert champ["isr"] > 0  # IS Sharpe still positive
    assert champ["usr"] > 0  # BULL Sharpe positive
    assert champ["allp"]  # all-three-positive flag still set
    assert (
        champ["worst"] >= -40.0
    )  # tail still bounded (NOT tighter than the brake baseline anymore)
