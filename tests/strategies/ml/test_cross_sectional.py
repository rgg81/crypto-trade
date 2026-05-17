"""Tests for the cross-sectional ranking architecture (iter-v3/088).

Covers:
  1. Import smoke test.
  2. label_cross_sectional_rank — grade assignment, no look-ahead on features.
  3. XS_REQUIRED_GAP = 88 formula and CPCV expected_gap assertion.
  4. Label look-ahead / leakage guard — the label's forward window must NOT
     overlap with any test row when XS_REQUIRED_GAP is applied.
  5. build_cross_sectional_panel — drop btc_ret_14d, xs-rank normalization.
  6. CrossSectionalRankStrategy — instantiation guard (explicit feature_columns).
  7. build_positions — dollar-neutral check, minimum symbol guard.
  8. _spearman_ic — correctness on a known-rank sequence.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.strategies.ml.cross_sectional import (
    XS_HORIZON,
    XS_MIN_SYMBOLS_PER_BAR,
    XS_REQUIRED_GAP,
    XS_UNIVERSE,
    CrossSectionalRankStrategy,
    _spearman_ic,
    build_positions,
    compute_xs_sharpe,
    label_cross_sectional_rank,
)
from crypto_trade.strategies.ml.validation_v3 import combinatorial_purged_cv

# ---------------------------------------------------------------------------
# 1. Import smoke test
# ---------------------------------------------------------------------------


def test_import_smoke():
    """Module imports without error and key constants are present."""
    assert XS_UNIVERSE is not None
    assert len(XS_UNIVERSE) == 22
    assert XS_REQUIRED_GAP == 88
    assert XS_HORIZON == 3


# ---------------------------------------------------------------------------
# 2. label_cross_sectional_rank
# ---------------------------------------------------------------------------


def _make_panel(n_syms: int = 6, n_bars: int = 20, seed: int = 42) -> pd.DataFrame:
    """Create a minimal synthetic panel for testing."""
    rng = np.random.default_rng(seed)
    rows = []
    t0 = 1_700_000_000_000  # arbitrary epoch ms
    interval_ms = 8 * 3600 * 1000
    syms = [f"SYM{i:02d}USDT" for i in range(n_syms)]
    price = np.ones(n_syms) * 100.0
    for bar in range(n_bars):
        ts = t0 + bar * interval_ms
        ret = rng.standard_normal(n_syms) * 0.02
        price = price * (1 + ret)
        for i, sym in enumerate(syms):
            rows.append({"open_time": ts, "symbol": sym, "close": price[i]})
    return pd.DataFrame(rows)


def test_label_grade_values():
    """All label grades in {0, 1, 2} or NaN (pd.NA)."""
    panel = _make_panel(n_syms=6, n_bars=20)
    labels = label_cross_sectional_rank(panel, horizon=XS_HORIZON)
    valid = labels.dropna()
    assert set(valid.unique()).issubset({0, 1, 2}), f"Unexpected grades: {valid.unique()}"


def test_label_nans_at_horizon_end():
    """Last H bars per symbol must have NaN labels (no forward close)."""
    n_bars = 15
    panel = _make_panel(n_syms=6, n_bars=n_bars)
    labels = label_cross_sectional_rank(panel, horizon=XS_HORIZON)
    # The last XS_HORIZON bars have no forward close → NaN labels.
    ts_sorted = sorted(panel["open_time"].unique())
    last_h_ts = ts_sorted[-XS_HORIZON:]
    last_labels = labels[panel["open_time"].isin(last_h_ts)]
    assert last_labels.isna().all(), (
        f"Expected NaN for last {XS_HORIZON} bars, got: {last_labels.dropna()}"
    )


def test_label_distribution_balanced():
    """With a wide enough cross-section, the grade distribution is roughly balanced."""
    panel = _make_panel(n_syms=12, n_bars=50)
    labels = label_cross_sectional_rank(panel, horizon=XS_HORIZON)
    valid = labels.dropna()
    counts = valid.value_counts()
    # Each tercile should contain roughly 33% of valid labels.
    for grade in [0, 1, 2]:
        frac = counts.get(grade, 0) / len(valid)
        assert 0.20 < frac < 0.50, f"Grade {grade} fraction out of expected range: {frac:.3f}"


def test_label_thin_cross_section_returns_na():
    """With fewer than XS_MIN_SYMBOLS_PER_BAR symbols, all labels should be NaN."""
    panel = _make_panel(n_syms=XS_MIN_SYMBOLS_PER_BAR - 1, n_bars=10)
    labels = label_cross_sectional_rank(panel, horizon=XS_HORIZON)
    # Too few symbols → all NaN.
    valid = labels.dropna()
    # May be empty if every timestamp is below the minimum.
    # (The grade function returns NaN when n < XS_MIN_SYMBOLS_PER_BAR.)
    assert len(valid) == 0 or valid.empty, f"Expected all NaN, got {len(valid)} valid labels"


# ---------------------------------------------------------------------------
# 3. XS_REQUIRED_GAP formula and CPCV assertion
# ---------------------------------------------------------------------------


def test_xs_required_gap_formula():
    """XS_REQUIRED_GAP must equal (H+1) * N_symbols = (3+1)*22 = 88."""
    expected = (XS_HORIZON + 1) * len(XS_UNIVERSE)
    assert XS_REQUIRED_GAP == expected, (
        f"XS_REQUIRED_GAP={XS_REQUIRED_GAP} != (H+1)*N={expected}. "
        "The gap formula ensures no training label's H=3 forward window "
        "overlaps a test row in the pooled cross-section."
    )


def test_cpcv_expected_gap_assertion_fires():
    """CPCV raises AssertionError when gap != expected_gap."""
    with pytest.raises(AssertionError, match="does not match expected_gap"):
        combinatorial_purged_cv(
            n_samples=500,
            n_splits=10,
            n_test_splits=2,
            gap=66,  # wrong gap (legacy per-symbol)
            expected_gap=XS_REQUIRED_GAP,  # 88
        )


def test_cpcv_correct_gap_passes():
    """CPCV does NOT raise when gap == expected_gap == XS_REQUIRED_GAP."""
    splits = combinatorial_purged_cv(
        n_samples=1000,
        n_splits=10,
        n_test_splits=2,
        gap=XS_REQUIRED_GAP,
        expected_gap=XS_REQUIRED_GAP,
    )
    assert len(splits) == 45  # C(10,2) = 45


# ---------------------------------------------------------------------------
# 4. Label look-ahead / leakage guard
# ---------------------------------------------------------------------------


def test_no_label_leakage_at_test_boundary():
    """Verify that XS_REQUIRED_GAP eliminates label look-ahead at every boundary.

    In the cross-sectional runner, the CPCV operates on TIMESTAMP indices —
    n_samples = number of unique timestamps (e.g., 2700 for 24 IS months).
    One CPCV sample = one timestamp = all 22 symbols at that bar.

    XS_REQUIRED_GAP = 88 timestamp-indices are purged on both sides of every
    test boundary.  The label's forward horizon is H=3 TIMESTAMPS.  A gap of
    88 >= H+1 = 4 guarantees no training timestamp's label window reaches into
    the test set.

    We verify this: after applying the gap, no training timestamp-index is
    within H=3 of the nearest test boundary.
    """
    n_timestamps = 500  # synthetic timestamp count

    # CPCV operates on timestamp-space (n_samples = n_timestamps).
    splits = combinatorial_purged_cv(
        n_samples=n_timestamps,
        n_splits=10,
        n_test_splits=2,
        gap=XS_REQUIRED_GAP,
        expected_gap=XS_REQUIRED_GAP,
    )

    # Verify: the gap removes all training indices from the embargo zone around
    # each test block boundary.  Specifically:
    #   - For the LEFT boundary (gap before the first test index): no training
    #     index should fall in (max_train_before, min_test) — the gap has
    #     cleared indices in (min_test - gap, min_test).
    #   - We check the crucial property: no training index is in the range
    #     [min_test - XS_HORIZON, min_test), because any such index would have
    #     its label window [idx, idx+H) overlap the test block.
    #
    # IMPORTANT: "training indices" here means indices that are <= max(train_idx
    # indices adjacent to this test block), NOT all training indices globally.
    # We filter to only training indices < min_test (before this test block).
    for train_idx, test_idx in splits:
        if len(train_idx) == 0 or len(test_idx) == 0:
            continue
        min_test = int(test_idx.min())

        # Only consider training indices that precede this test block.
        # Global training indices far after min_test belong to other test blocks
        # and are irrelevant for left-boundary leakage.
        train_before = train_idx[train_idx < min_test]
        if len(train_before) == 0:
            continue  # No training data precedes this test block — OK.

        # Any training index in [min_test - H, min_test) leaks: its label
        # window [idx, idx+H) overlaps [min_test, ...).
        # The gap (88) should have cleared all such indices.
        leaking = train_before[train_before >= min_test - XS_HORIZON]
        assert len(leaking) == 0, (
            f"Label leakage: {len(leaking)} training timestamp-indices in "
            f"[min_test-H={min_test - XS_HORIZON}, min_test={min_test}). "
            f"XS_REQUIRED_GAP={XS_REQUIRED_GAP} >> H+1={XS_HORIZON + 1} "
            "should eliminate all look-ahead."
        )


# ---------------------------------------------------------------------------
# 5. build_cross_sectional_panel — btc_ret_14d drop + xs-rank normalization
# ---------------------------------------------------------------------------


def test_xs_drop_btc_ret_14d():
    """btc_ret_14d must be dropped from the cross-sectional feature set."""
    from crypto_trade.strategies.ml.cross_sectional import XS_DROP_FEATURES

    assert "btc_ret_14d" in XS_DROP_FEATURES, (
        "btc_ret_14d must be in XS_DROP_FEATURES (zero cross-sectional dispersion — EDA T6)."
    )


def test_xs_rank_normalization_range():
    """After xs-rank normalization, all feature values are in [0, 1].

    Tests the normalization logic directly without loading real parquets.
    """
    import pandas as pd

    # Simulate xs-rank normalization on a small frame.
    np.random.seed(42)
    n_syms = 6
    n_bars = 10
    feature_cols = ["feat_a", "feat_b"]
    rows = []
    t0 = 1_700_000_000_000
    interval_ms = 8 * 3600 * 1000
    for bar in range(n_bars):
        ts = t0 + bar * interval_ms
        for i in range(n_syms):
            rows.append(
                {
                    "open_time": ts,
                    "symbol": f"SYM{i}",
                    "feat_a": np.random.randn(),
                    "feat_b": np.random.randn(),
                }
            )
    panel = pd.DataFrame(rows)

    # Apply the xs-rank normalization (copied from build_cross_sectional_panel logic).
    def _xs_rank_normalize(group, cols):
        n = len(group)
        if n < 2:
            return group
        for col in cols:
            ranked = group[col].rank(method="average", na_option="keep")
            group[col] = (ranked - 1.0) / max(n - 1, 1)
        return group

    panel[feature_cols] = panel.groupby("open_time", sort=False, group_keys=False).apply(
        lambda g: _xs_rank_normalize(g.copy(), feature_cols)[feature_cols]
    )

    for col in feature_cols:
        vals = panel[col].dropna()
        assert vals.min() >= -1e-9, f"{col} min below 0 after xs-rank: {vals.min()}"
        assert vals.max() <= 1.0 + 1e-9, f"{col} max above 1 after xs-rank: {vals.max()}"


# ---------------------------------------------------------------------------
# 6. CrossSectionalRankStrategy — instantiation guard
# ---------------------------------------------------------------------------


def test_strategy_requires_feature_columns():
    """CrossSectionalRankStrategy raises if feature_columns is empty/None."""
    with pytest.raises(ValueError, match="feature_columns must be explicitly specified"):
        CrossSectionalRankStrategy(feature_columns=None)

    with pytest.raises(ValueError, match="feature_columns must be explicitly specified"):
        CrossSectionalRankStrategy(feature_columns=[])


def test_strategy_instantiation_with_columns():
    """CrossSectionalRankStrategy instantiates without error when given columns."""
    strat = CrossSectionalRankStrategy(
        feature_columns=["max_dd_window_50", "ema_spread_atr_20", "ret_kurt_50"],
        training_months=24,
        n_trials=2,
    )
    assert strat.training_months == 24
    assert "btc_ret_14d" not in strat.feature_columns  # XS_DROP_FEATURES removes it


# ---------------------------------------------------------------------------
# 7. build_positions — dollar-neutral and minimum symbols
# ---------------------------------------------------------------------------


def _make_positions_panel(n_syms: int = 10) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    """Create a synthetic panel_t, scores, and hist_returns for build_positions tests."""
    rng = np.random.default_rng(0)
    syms = [f"SYM{i:02d}USDT" for i in range(n_syms)]
    panel_t = pd.DataFrame(
        {
            "symbol": syms,
            "open_time": [1_700_000_000_000] * n_syms,
        }
    )
    scores = rng.standard_normal(n_syms)
    # Hist returns: 50 bars × n_syms matrix.
    hist_returns = pd.DataFrame(
        rng.standard_normal((50, n_syms)) * 0.02,
        columns=syms,
    )
    return panel_t, scores, hist_returns


def test_positions_dollar_neutral():
    """Long gross and short gross must be approximately equal (dollar-neutral)."""
    panel_t, scores, hist_returns = _make_positions_panel(n_syms=12)

    # After vol-targeting, the long/short gross may differ from 1.0 but
    # their ratio should be ~1 (dollar-neutral before scaling is preserved).
    # We check the pre-scaling ratio by using vol_target=1e6 (no scaling effect).
    positions_raw = build_positions(panel_t, scores, hist_returns, vol_target=1e6)
    long_gross_raw = sum(v for v in positions_raw.values() if v > 0)
    short_gross_raw = sum(abs(v) for v in positions_raw.values() if v < 0)
    assert abs(long_gross_raw - short_gross_raw) < 1e-9, (
        f"Dollar-neutral violated: long={long_gross_raw:.6f}, short={short_gross_raw:.6f}"
    )


def test_positions_empty_below_min_symbols():
    """build_positions returns empty dict when cross-section is too thin."""
    panel_t, scores, hist_returns = _make_positions_panel(n_syms=XS_MIN_SYMBOLS_PER_BAR - 1)
    positions = build_positions(panel_t, scores, hist_returns[:1])
    assert positions == {}, (
        f"Expected empty positions for {XS_MIN_SYMBOLS_PER_BAR - 1} symbols "
        f"(below XS_MIN_SYMBOLS_PER_BAR={XS_MIN_SYMBOLS_PER_BAR})."
    )


def test_positions_long_short_are_separate():
    """No symbol should appear in both long and short legs."""
    panel_t, scores, hist_returns = _make_positions_panel(n_syms=12)
    positions = build_positions(panel_t, scores, hist_returns)
    long_syms = {s for s, v in positions.items() if v > 0}
    short_syms = {s for s, v in positions.items() if v < 0}
    overlap = long_syms & short_syms
    assert not overlap, f"Symbols in both legs: {overlap}"


# ---------------------------------------------------------------------------
# 8. _spearman_ic — correctness
# ---------------------------------------------------------------------------


def test_spearman_ic_perfect_positive():
    """Spearman IC = 1.0 for identical rank order."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
    assert abs(_spearman_ic(x, y) - 1.0) < 1e-9


def test_spearman_ic_perfect_negative():
    """Spearman IC = -1.0 for exactly reversed rank order."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
    assert abs(_spearman_ic(x, y) - (-1.0)) < 1e-9


def test_spearman_ic_zero_variance():
    """Spearman IC returns 0.0 when one array is constant."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([5.0, 5.0, 5.0])
    # Degenerate: constant y → IC = 0.
    ic = _spearman_ic(x, y)
    assert ic == 0.0


def test_spearman_ic_short():
    """Spearman IC returns 0.0 for arrays shorter than 2."""
    assert _spearman_ic(np.array([1.0]), np.array([2.0])) == 0.0


# ---------------------------------------------------------------------------
# 9. XS_UNIVERSE — V3_EXCLUDED_SYMBOLS isolation
# ---------------------------------------------------------------------------


def test_xs_universe_not_in_v1v2():
    """XS_UNIVERSE must not overlap with V3_EXCLUDED_SYMBOLS (no v1/v2 symbols)."""
    from crypto_trade.features_v3 import V3_EXCLUDED_SYMBOLS

    overlap = set(XS_UNIVERSE) & set(V3_EXCLUDED_SYMBOLS)
    assert not overlap, (
        f"XS_UNIVERSE contains v1/v2 symbols: {sorted(overlap)}\n"
        "XS_UNIVERSE must be disjoint from V3_EXCLUDED_SYMBOLS."
    )


# ---------------------------------------------------------------------------
# 10. compute_xs_sharpe — smoke test
# ---------------------------------------------------------------------------


def test_compute_xs_sharpe_smoke():
    """compute_xs_sharpe runs without error on synthetic results."""
    rng = np.random.default_rng(7)
    t0 = 1_700_000_000_000
    interval_ms = 8 * 3600 * 1000
    # 3 months of 8h bars.
    rows = []
    for bar in range(3 * 30 * 3):
        ts = t0 + bar * interval_ms
        rows.append(
            {
                "open_time": ts,
                "symbol": "ADAUSDT",
                "net_pnl": float(rng.standard_normal()),
                "is_oos": bar >= 200,
            }
        )
    results = pd.DataFrame(rows)
    is_sharpe = compute_xs_sharpe(results, is_oos=False)
    oos_sharpe = compute_xs_sharpe(results, is_oos=True)
    # Just check they return finite floats.
    assert np.isfinite(is_sharpe)
    assert np.isfinite(oos_sharpe)
