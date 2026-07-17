"""team-07 strategy tests — leak-proofing self-checks for build_raw_weights.

Imports are restricted to numpy / pandas + the local strategy module so the file
passes the harness static-import scan (no ``import pytest``: pytest discovers the
``test_*`` functions by name and the plain ``assert`` statements need no framework).

The panels here are SYNTHETIC (a seeded geometric random walk) — the tests never
read the frozen snapshot, so they exercise no data-boundary path. Positive prices
keep ``open/close`` ratios well defined and match the harness's positivity-
preserving corruption (prices ×7+5, volume ×3+1).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy

_N_ROWS = 420  # > 252 + slack so the trailing window yields live signals
_N_TICKERS = 9  # enough breadth for a meaningful cross-sectional rank
_SEED = 20260717


def _make_panels(seed: int = _SEED) -> tuple[dict[str, pd.DataFrame], dict]:
    """Deterministic synthetic OHLCV panel dict + aux, mirroring engine.team_view."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-01", periods=_N_ROWS)
    tickers = [f"SYM{i:02d}USDT" for i in range(_N_TICKERS)]
    # geometric random walk close, positive by construction
    steps = rng.normal(0.0, 0.02, size=(_N_ROWS, _N_TICKERS))
    close = 100.0 * np.exp(np.cumsum(steps, axis=0))
    on_gap = rng.normal(0.0, 0.01, size=(_N_ROWS, _N_TICKERS))
    open_ = close * (1.0 + on_gap)  # open near close; strictly positive
    high = np.maximum(open_, close) * (1.0 + rng.uniform(0.0, 0.01, size=close.shape))
    low = np.minimum(open_, close) * (1.0 - rng.uniform(0.0, 0.01, size=close.shape))
    volume = rng.uniform(1e3, 1e6, size=close.shape)

    def _df(arr: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame(arr, index=dates, columns=tickers)

    pn = {
        "open": _df(open_),
        "high": _df(high),
        "low": _df(low),
        "close": _df(close),
        "volume": _df(volume),
    }
    aux = {"vix": None, "sector_map": {t: "Tech" for t in tickers}, "seed": seed}
    return pn, aux


def _corrupt_after(pn: dict[str, pd.DataFrame], cut: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """Mangle every bar STRICTLY AFTER cut, exactly like the harness corruption."""
    out = {}
    for k, df in pn.items():
        d = df.copy()
        mask = d.index > cut
        if k == "volume":
            d.loc[mask] = d.loc[mask] * 3.0 + 1.0
        else:
            d.loc[mask] = d.loc[mask] * 7.0 + 5.0
        out[k] = d
    return out


# ---------------------------------------------------------------- tests -------------------------
def test_determinism() -> None:
    """Two calls on identical inputs emit bit-identical weights (pure, seed-free)."""
    pn, aux = _make_panels()
    w1 = strategy.build_raw_weights(pn, aux)
    w2 = strategy.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)


def test_seed_independence() -> None:
    """aux['seed'] is unused: changing it must not move a single weight."""
    pn, aux = _make_panels()
    aux_other = dict(aux, seed=aux["seed"] + 12345)
    pd.testing.assert_frame_equal(
        strategy.build_raw_weights(pn, aux),
        strategy.build_raw_weights(pn, aux_other),
        check_exact=True,
    )


def test_future_corruption() -> None:
    """Mangling bars strictly AFTER a cut leaves weights at/before the cut unchanged."""
    pn, aux = _make_panels()
    cut = pn["close"].index[300]
    w_full = strategy.build_raw_weights(pn, aux)
    w_corr = strategy.build_raw_weights(_corrupt_after(pn, cut), aux)
    a = w_full[w_full.index <= cut]
    b = w_corr[w_corr.index <= cut]
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_uses_only_open_and_close() -> None:
    """high/low/volume are irrelevant: mangling them anywhere leaves ALL weights unchanged."""
    pn, aux = _make_panels()
    w_full = strategy.build_raw_weights(pn, aux)
    pn2 = dict(pn)
    pn2["high"] = pn["high"] * 3.0 + 2.0
    pn2["low"] = pn["low"] * 0.5 + 1.0
    pn2["volume"] = pn["volume"] * 11.0 + 7.0
    w2 = strategy.build_raw_weights(pn2, aux)
    pd.testing.assert_frame_equal(w_full, w2, check_exact=True)


def test_same_bar_close_perturbation() -> None:
    """Perturbing close[t*] cannot change weights STRICTLY BEFORE t* (close[t*] is past-only
    for on[t*+1] = open[t*+1]/close[t*] - 1; on[t*] does not use close[t*])."""
    pn, aux = _make_panels()
    t_star = pn["close"].index[330]
    w_full = strategy.build_raw_weights(pn, aux)
    pn2 = dict(pn)
    c2 = pn["close"].copy()
    c2.loc[t_star] = c2.loc[t_star] * 1.001
    pn2["close"] = c2
    w2 = strategy.build_raw_weights(pn2, aux)
    a = w_full[w_full.index < t_star]
    b = w2[w2.index < t_star]
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_dollar_neutral_rows() -> None:
    """Once the window fills, each active row is centered: weights sum to ~0 across names."""
    pn, aux = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    live = w.dropna(how="all")
    assert len(live) > 0, "expected live signal rows after the 252-bar warmup"
    row_sums = w.sum(axis=1, min_count=1).dropna()
    assert np.allclose(row_sums.to_numpy(), 0.0, atol=1e-9), "active rows must be dollar-neutral"


def test_warmup_is_flat() -> None:
    """Strict min_periods=252: the first 251 rows carry no signal (all-NaN weights)."""
    pn, aux = _make_panels()
    w = strategy.build_raw_weights(pn, aux)
    # on[t] itself is NaN at row 0 (needs close[t-1]); the 252-window mean needs 252 valid
    # on-observations, so the earliest possible live signal is row index 252.
    assert w.iloc[:252].isna().all().all(), "no name may have a weight before the window fills"
    assert w.iloc[252:].notna().any().any(), "signals must appear once the window fills"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"{name}: ok")
    print("all tests passed")
