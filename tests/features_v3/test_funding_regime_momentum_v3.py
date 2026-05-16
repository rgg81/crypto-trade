"""Adversarial tests for funding_regime_momentum_5d — iter-v3/085.

iter-v3/085 (cycle-3 EXPLORATION #4) appends ONE Category-2 composed feature to
V3_FEATURE_COLUMNS_TOP_N (14 -> 15):

    funding_regime_momentum_5d = regime_momentum_signed_5d * sign(funding_z_30)

where funding_z_30 is the 30-period z-score of the PAST-ONLY funding rate
(funding_rate.shift(1) before the rolling mean/std).  Funding enters ONLY as a
sign() switch inside the composed feature — it is never a direct model column.
This is NOT the closed v3 funding-as-direct-feature axis (/019/023/024/082).

Focuses on:
1. Import smoke — public API importable without error.
2. Composition correctness — the feature equals the element-wise product of
   regime_momentum_signed_5d and sign(funding_z_30).
3. Past-only discipline (THE MANDATED TEST) — perturbing a future funding rate
   must not change funding_regime_momentum_5d at any earlier bar.
4. funding_z_30 past-only — the .shift(1)-before-rolling discipline: bar t's own
   funding settlement never enters its own z-score window.
5. NaN warm-up — funding_z_30 needs 30 bars + a 1-bar shift; regime_momentum
   needs 99 bars (hurst_100). The longer warm-up dominates.
6. sign() exactness — sign(funding_z_30) is exactly +1 / -1 / NaN, never a
   continuous gradient; exactly-zero funding-z -> NaN (degenerate row).
7. Missing regime_momentum_signed_5d — graceful all-NaN fallback, no error.
8. GROUP_REGISTRY smoke + FileNotFoundError on missing cache + KeyError on
   missing symbol column.
9. funding_regime_momentum_v3 is registered in GROUP_REGISTRY, AFTER engineered_v3.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v3.engineered_v3 import (
    _FUNDING_REGIME_Z_WINDOW,
    add_funding_regime_momentum_v3_features,
    compute_funding_regime_momentum_5d,
    compute_regime_momentum_signed_5d,
)

_8H_MS = 8 * 3600 * 1000
_IS_START_MS = 1_679_616_000_000  # 2023-03-24 00:00 UTC


def _make_kline_df(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Kline-like DataFrame with open_time + close + a pre-computed hurst_100.

    regime_momentum_signed_5d (the composed feature's primitive) is materialized
    via compute_regime_momentum_signed_5d so the new feature has its dependency.
    """
    rng = np.random.default_rng(seed)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    close = 100.0 * np.cumprod(1.0 + rng.normal(0, 0.02, n))
    # hurst_100 in (0, 1) — two-sided around 0.5 so the regime sign flips.
    hurst = np.clip(0.5 + rng.normal(0, 0.15, n), 0.02, 0.98)
    df = pd.DataFrame(
        {
            "open_time": open_times,
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.uniform(1000, 10000, n),
            "hurst_100": hurst,
            "symbol": "BCHUSDT",
        }
    )
    # Materialize the primitive the composed feature depends on.
    return compute_regime_momentum_signed_5d(df)


def _make_funding_df(n: int = 300, seed: int = 7) -> pd.DataFrame:
    """Funding-rate history aligned to the kline open_times.

    Mildly persistent (AR-like) so funding_z_30's sign is genuinely two-sided.
    """
    rng = np.random.default_rng(seed)
    funding_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    rates = np.zeros(n)
    for i in range(1, n):
        rates[i] = 0.7 * rates[i - 1] + rng.normal(0, 0.0003)
    return pd.DataFrame({"funding_time": funding_times, "funding_rate": rates})


def test_import_smoke() -> None:
    """The public API is importable and callable."""
    out = compute_funding_regime_momentum_5d(_make_kline_df(), _make_funding_df())
    assert "funding_regime_momentum_5d" in out.columns


def test_composition_correctness() -> None:
    """funding_regime_momentum_5d == regime_momentum_signed_5d * sign(funding_z_30).

    Recompute funding_z_30 independently from the merged funding rate and assert
    the composed feature is the exact element-wise product.
    """
    kline = _make_kline_df(n=300)
    funding = _make_funding_df(n=300)
    out = compute_funding_regime_momentum_5d(kline, funding)

    # Independent recomputation of funding_z_30 (same .shift(1) discipline).
    f = funding.copy()
    f["open_time_aligned"] = (f["funding_time"] // 60_000) * 60_000
    k = kline.copy()
    k["open_time_aligned"] = (k["open_time"] // 60_000) * 60_000
    merged = k.merge(
        f[["open_time_aligned", "funding_rate"]], on="open_time_aligned", how="left"
    )
    merged.index = kline.index
    r = merged["funding_rate"].astype(float)
    fr_lag = r.shift(1)
    w = _FUNDING_REGIME_Z_WINDOW
    fz = (r - fr_lag.rolling(w, min_periods=w).mean()) / (
        fr_lag.rolling(w, min_periods=w).std(ddof=1) + 1e-9
    )
    expected = kline["regime_momentum_signed_5d"].astype(float) * np.sign(fz).replace(
        0.0, np.nan
    )

    m = out["funding_regime_momentum_5d"].notna() & expected.notna()
    assert m.sum() > 100, "too few comparable (non-NaN) bars"
    np.testing.assert_allclose(
        out["funding_regime_momentum_5d"][m].to_numpy(),
        expected[m].to_numpy(),
        rtol=1e-9,
        atol=1e-12,
    )


def test_past_only_no_lookahead() -> None:
    """MANDATED past-only test — perturbing a FUTURE funding rate must not change
    funding_regime_momentum_5d at any EARLIER bar.

    This is the look-ahead invariant: funding_z_30 uses funding_rate.shift(1)
    before the 30-bar rolling window, so a spike at bar k can only affect bars
    >= k (k enters its own numerator; the .shift(1)-lagged rolling window first
    sees k at bar k+1).
    """
    kline = _make_kline_df(n=300)
    funding = _make_funding_df(n=300)
    base = compute_funding_regime_momentum_5d(kline, funding)

    perturb_idx = 250  # perturb a late bar
    funding_perturbed = funding.copy()
    funding_perturbed.loc[perturb_idx, "funding_rate"] += 5.0  # huge spike

    perturbed = compute_funding_regime_momentum_5d(kline, funding_perturbed)

    # Every value at bars STRICTLY BEFORE perturb_idx must be unchanged.
    b = base["funding_regime_momentum_5d"].iloc[:perturb_idx]
    p = perturbed["funding_regime_momentum_5d"].iloc[:perturb_idx]
    pd.testing.assert_series_equal(
        b,
        p,
        check_names=False,
        obj="funding_regime_momentum_5d changed at a bar BEFORE the perturbed future rate",
    )

    # Sanity: the perturbation DID propagate at/after perturb_idx (the feature is
    # not trivially constant w.r.t. funding) — funding_z_30's rolling window sees
    # the spike from perturb_idx+1 onward.
    after = (
        base["funding_regime_momentum_5d"].iloc[perturb_idx:]
        != perturbed["funding_regime_momentum_5d"].iloc[perturb_idx:]
    )
    assert after.any(), "perturbation never propagated — feature ignores funding"


def test_funding_z_window_shift_is_past_only() -> None:
    """funding_z_30 must use ONLY bars [t-30, t-1] in its rolling denominator.

    Perturbing the funding rate exactly AT bar k changes the feature at k (k is
    in its own numerator) but a perturbation at k must NOT alter bars < k.
    """
    kline = _make_kline_df(n=200)
    funding = _make_funding_df(n=200)
    base = compute_funding_regime_momentum_5d(kline, funding)

    k = 150
    fp = funding.copy()
    fp.loc[k, "funding_rate"] += 3.0
    perturbed = compute_funding_regime_momentum_5d(kline, fp)

    b = base["funding_regime_momentum_5d"].iloc[:k]
    p = perturbed["funding_regime_momentum_5d"].iloc[:k]
    pd.testing.assert_series_equal(b, p, check_names=False)


def test_nan_warmup() -> None:
    """The composed feature's warm-up is the max of its two legs' warm-ups.

    In this fixture hurst_100 is supplied pre-filled, so regime_momentum_signed_5d
    is valid from bar 15 (ret_5d's shift(15) warm-up). funding_z_30 applies a
    1-bar shift then a 30-bar rolling window, so its first valid bar is 30. The
    funding-z leg therefore dominates: funding_regime_momentum_5d is NaN for
    bars [0, 29] and valid from bar 30. (In the real pipeline hurst_100 itself
    has a 99-bar warm-up which would dominate instead — see
    compute_regime_momentum_signed_5d; this test isolates the funding-z leg.)
    """
    out = compute_funding_regime_momentum_5d(_make_kline_df(n=300), _make_funding_df(n=300))
    frm = out["funding_regime_momentum_5d"]
    w = _FUNDING_REGIME_Z_WINDOW  # 30
    # funding_z_30 needs w bars after a 1-bar shift -> NaN for bars [0, w-1].
    assert frm.iloc[:w].isna().all(), (
        f"feature has non-NaN inside the funding_z_30 warm-up (first {w} bars)"
    )
    assert frm.iloc[w + 20 :].notna().mean() > 0.8, "feature too sparse post-warmup"


def test_sign_is_exact_not_gradient() -> None:
    """sign(funding_z_30) must yield only the discrete factors {+1, -1, NaN}.

    funding_regime_momentum_5d / regime_momentum_signed_5d must therefore equal
    exactly +1 or -1 wherever both are finite and non-zero.
    """
    out = compute_funding_regime_momentum_5d(_make_kline_df(n=400), _make_funding_df(n=400))
    prim = out["regime_momentum_signed_5d"].astype(float)
    comp = out["funding_regime_momentum_5d"].astype(float)
    m = prim.notna() & comp.notna() & (prim.abs() > 1e-12)
    ratio = (comp[m] / prim[m]).to_numpy()
    assert m.sum() > 100
    # ratio is sign(funding_z_30) -> within float tolerance of exactly +/-1.
    assert np.all(np.isclose(np.abs(ratio), 1.0, atol=1e-9)), (
        "sign(funding_z_30) produced a non-{+1,-1} factor — composition is not a sign-switch"
    )


def test_missing_regime_momentum_primitive_all_nan() -> None:
    """If regime_momentum_signed_5d is absent, the feature is all-NaN (no error).

    The pipeline then fails loudly at the downstream feature-column assertion.
    """
    kline = _make_kline_df(n=200).drop(columns=["regime_momentum_signed_5d"])
    out = compute_funding_regime_momentum_5d(kline, _make_funding_df(n=200))
    assert "funding_regime_momentum_5d" in out.columns
    assert out["funding_regime_momentum_5d"].isna().all()


def test_idempotency() -> None:
    """Calling compute_funding_regime_momentum_5d twice produces identical output."""
    kline = _make_kline_df(n=250)
    funding = _make_funding_df(n=250)
    a = compute_funding_regime_momentum_5d(kline, funding)
    b = compute_funding_regime_momentum_5d(kline, funding)
    pd.testing.assert_series_equal(
        a["funding_regime_momentum_5d"], b["funding_regime_momentum_5d"]
    )


def test_add_funding_regime_momentum_registry_entry() -> None:
    """add_funding_regime_momentum_v3_features reads the per-symbol cache and
    appends funding_regime_momentum_5d."""
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        (data_dir / "funding_rates").mkdir()
        _make_funding_df().to_csv(data_dir / "funding_rates" / "BCHUSDT.csv", index=False)
        out = add_funding_regime_momentum_v3_features(_make_kline_df(), data_dir=data_dir)
        assert "funding_regime_momentum_5d" in out.columns


def test_add_funding_regime_momentum_missing_cache_raises() -> None:
    """add_funding_regime_momentum_v3_features raises FileNotFoundError on missing cache."""
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(FileNotFoundError, match="Funding-rate cache not found"):
            add_funding_regime_momentum_v3_features(_make_kline_df(), data_dir=Path(tmp))


def test_add_funding_regime_momentum_missing_symbol_raises() -> None:
    """add_funding_regime_momentum_v3_features raises KeyError without a symbol column."""
    df = _make_kline_df().drop(columns=["symbol"])
    with pytest.raises(KeyError, match="symbol"):
        add_funding_regime_momentum_v3_features(df)


def test_group_registry_contains_funding_regime_momentum() -> None:
    """funding_regime_momentum_v3 is registered in GROUP_REGISTRY, AFTER engineered_v3.

    Ordering matters: funding_regime_momentum_5d depends on
    regime_momentum_signed_5d, which add_engineered_v3_features computes.
    """
    from crypto_trade.features_v3 import GROUP_REGISTRY

    keys = list(GROUP_REGISTRY.keys())
    assert "funding_regime_momentum_v3" in keys
    assert "engineered_v3" in keys
    assert keys.index("funding_regime_momentum_v3") > keys.index("engineered_v3"), (
        "funding_regime_momentum_v3 must be registered AFTER engineered_v3 — it "
        "depends on regime_momentum_signed_5d computed by add_engineered_v3_features."
    )
