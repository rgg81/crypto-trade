"""team-02 — strategy self-tests for `t02-breakout-channel-v2`.

Self-contained (synthetic panels only; NO data reads) checks required by research_brief.md
section II.8: determinism, future-corruption (rows <= cut bit-identical after mangling rows >
cut in close AND aux copies), widening (extra columns don't crash / don't perturb originals),
flat-warmup (first N-1 rows of a fresh column are 0), and NaN-close decay-to-0. Plus interface
and aux-independence guards. The mechanical harness (`cli.py audit`) re-checks all six leak
properties against the frozen snapshot; these tests exercise the same properties on synthetic
data so failures surface locally.

Imports are limited to the tournament static-scan whitelist (numpy/pandas + the team-local
`strategy` module); pytest's default prepend import mode puts this directory on sys.path so
`import strategy` resolves to strategy.py in the same folder.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import strategy as strat

N = strat.N  # 60


# ------------------------------------------------------------------ synthetic panels ------------
def _grid(n: int) -> pd.DatetimeIndex:
    return pd.date_range(pd.Timestamp("2021-01-01"), periods=n, freq="8h")


def _synth_close(n: int = 320, n_sym: int = 6, seed: int = 7) -> pd.DataFrame:
    """Per-symbol geometric random walk with alternating drift -> real channel breakouts."""
    rng = np.random.default_rng(seed)
    idx = _grid(n)
    cols = [f"C{i:02d}USDT" for i in range(n_sym)]
    data = {}
    for j, c in enumerate(cols):
        steps = rng.normal(0.0, 0.03, size=n) + (0.004 if j % 2 == 0 else -0.004)
        data[c] = 100.0 * np.exp(np.cumsum(steps))
    return pd.DataFrame(data, index=idx)


def _make_pn(close: pd.DataFrame) -> dict:
    idx, cols = close.index, close.columns
    ones = pd.DataFrame(1.0, index=idx, columns=cols)
    return {
        "open": close.shift(1).fillna(close),
        "high": close * 1.001,
        "low": close * 0.999,
        "close": close,
        "volume": ones * 1000.0,
        "quote_volume": ones * 1e5,
        "trades": ones * 100.0,
        "taker_buy_volume": ones * 500.0,
        "taker_buy_quote_volume": ones * 5e4,
    }


def _make_aux(close: pd.DataFrame, seed: int = 12345) -> dict:
    idx, cols = close.index, close.columns

    def _df(v):
        return pd.DataFrame(v, index=idx, columns=cols)

    return {
        "funding": _df(1e-4),
        "oi": _df(1e6),
        "oi_value": _df(1e8),
        "tt_ls_accounts": _df(1.0),
        "tt_ls_positions": _df(1.0),
        "ls_accounts": _df(1.0),
        "taker_ls_vol": _df(1.0),
        "eligibility": _df(True),
        "seed": seed,
    }


# ------------------------------------------------------------------ tests -----------------------
def test_interface_and_shape():
    close = _synth_close()
    out = strat.build_raw_weights(_make_pn(close), _make_aux(close))
    assert isinstance(out, pd.DataFrame)
    assert list(out.columns) == list(close.columns)
    assert out.index.equals(close.index)
    assert not out.isna().any().any()  # NaN is never emitted (0 = flat)
    assert (out.abs() <= 1.0 + 1e-12).all().all()  # raw signed weights in [-1, 1]
    assert out.abs().to_numpy().sum() > 0.0  # signal is non-trivial post-warmup


def test_determinism():
    close = _synth_close()
    pn, aux = _make_pn(close), _make_aux(close)
    w1 = strat.build_raw_weights(pn, aux)
    w2 = strat.build_raw_weights(pn, aux)
    pd.testing.assert_frame_equal(w1, w2, check_exact=True)
    # rebuilt inputs (fresh frames, same values) must also be bit-identical
    w3 = strat.build_raw_weights(_make_pn(_synth_close()), _make_aux(_synth_close()))
    pd.testing.assert_frame_equal(w1, w3, check_exact=True)


def test_aux_independence():
    """Signal is price-only: different aux (funding/oi/eligibility/seed) -> identical output."""
    close = _synth_close()
    pn = _make_pn(close)
    base = strat.build_raw_weights(pn, _make_aux(close, seed=1))
    other = _make_aux(close, seed=999)
    other["funding"] = other["funding"] * 50.0 + 0.01
    other["oi"] = other["oi"] * 3.0 + 1.0
    other["eligibility"] = ~other["eligibility"]  # invert the mask entirely
    alt = strat.build_raw_weights(pn, other)
    pd.testing.assert_frame_equal(base, alt, check_exact=True)


def test_future_corruption():
    """Mangle rows STRICTLY AFTER a cut in close AND aux copies; rows <= cut are unchanged."""
    close = _synth_close()
    pn, aux = _make_pn(close), _make_aux(close)
    full = strat.build_raw_weights(pn, aux)

    cut_pos = int(len(close) * 0.7)
    cut_ts = close.index[cut_pos]
    after = close.index > cut_ts

    close_c = close.copy()
    close_c.loc[after] = close_c.loc[after] * 7.0 + 5.0  # harness kline mangle
    pn_c = _make_pn(close_c)

    aux_c = _make_aux(close)
    aux_c["funding"].loc[after] = aux_c["funding"].loc[after] * 3.0 + 1e-4
    aux_c["oi"].loc[after] = aux_c["oi"].loc[after] * 3.0 + 1.0
    aux_c["oi_value"].loc[after] = aux_c["oi_value"].loc[after] * 3.0 + 1.0
    aux_c["eligibility"].loc[after] = ~aux_c["eligibility"].loc[after]

    corrupted = strat.build_raw_weights(pn_c, aux_c)
    pd.testing.assert_frame_equal(
        full.loc[full.index <= cut_ts],
        corrupted.loc[corrupted.index <= cut_ts],
        check_exact=True,
    )


def test_truncated_replay():
    """Re-running on data truncated at the cut reproduces rows <= cut bit-identically."""
    close = _synth_close()
    full = strat.build_raw_weights(_make_pn(close), _make_aux(close))
    cut_pos = int(len(close) * 0.6)
    cut_ts = close.index[cut_pos]
    close_t = close.loc[close.index <= cut_ts]
    trunc = strat.build_raw_weights(_make_pn(close_t), _make_aux(close_t))
    pd.testing.assert_frame_equal(full.loc[full.index <= cut_ts], trunc, check_exact=True)


def test_widening_no_crash_and_originals_unchanged():
    """Extra never-seen columns must not crash and must not perturb the original columns."""
    close = _synth_close()
    base = strat.build_raw_weights(_make_pn(close), _make_aux(close))

    rng = np.random.default_rng(123)
    wide = close.copy()
    # synthetic columns that list only mid-panel (NaN-before behaviour included)
    for i in range(3):
        col = np.full(len(close), np.nan)
        half = len(close) // 2
        col[half:] = 20.0 * np.exp(np.cumsum(rng.normal(0, 0.02, size=len(close) - half)))
        wide[f"ZZWIDE{i:02d}USDT"] = col

    out = strat.build_raw_weights(_make_pn(wide), _make_aux(wide))
    assert isinstance(out, pd.DataFrame)
    assert set(close.columns).issubset(out.columns)
    pd.testing.assert_frame_equal(out[close.columns], base, check_exact=True)


def test_flat_warmup():
    """First N-1 rows of every (fresh) column are exactly 0.0 (min_periods=N unwarmed)."""
    close = _synth_close()
    out = strat.build_raw_weights(_make_pn(close), _make_aux(close))
    warmup = out.iloc[: N - 1]
    assert (warmup.to_numpy() == 0.0).all()


def test_nan_close_decays_to_zero():
    """A column that goes NaN mid-panel decays monotonically toward 0 via the EMA."""
    n = 200
    idx = _grid(n)
    # strongly monotone uptrend -> post-warmup channel position saturates to s = +1
    px = 100.0 * np.power(1.01, np.arange(n))
    close = pd.DataFrame({"UPUSDT": px}, index=idx)
    onset = 150
    close.iloc[onset:, 0] = np.nan  # column dies from `onset` onward

    out = strat.build_raw_weights(_make_pn(close), _make_aux(close))
    series = out["UPUSDT"]

    assert series.iloc[onset - 1] > 0.5  # saturated signal active pre-onset
    tail = series.iloc[onset:].to_numpy()
    assert np.all(np.diff(tail) < 0.0)  # strictly decreasing from the NaN onset
    assert np.all(tail >= 0.0)
    assert tail[-1] < 1e-3  # essentially flat by the end of the panel
    assert not np.isnan(tail).any()  # NaN close never emits NaN weight
