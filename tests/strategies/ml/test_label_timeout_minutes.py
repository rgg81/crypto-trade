"""Test label_timeout_minutes plumbing through LightGbmStrategy + embargo computation.

Per iter-v3/068 Path C: universal labeling timeout widening from 10080 to 20160 min.
Verifies that the labeling forward-scan window changes accordingly + the walk-forward
embargo gap is recomputed via compute_embargo_candles helper.

Five tests per brief Section 3 Sub-fix 7:
  1. test_label_timeout_minutes_default_preserved
       — verifies LightGbmStrategy stores label_timeout_minutes passed at init.
  2. test_label_timeout_minutes_iter068_value_20160
       — iter-v3/068 Path C value 20160 propagates correctly.
  3. test_compute_embargo_candles_iter068_value_43
       — embargo_candles=43 at label_timeout_minutes=20160 + 8h interval.
  4. test_compute_embargo_candles_iter060_anchor_value_22
       — baseline /060 anchor embargo_candles=22 at label_timeout_minutes=10080.
  5. test_compute_embargo_candles_doubles_on_timeout_doubling
       — additional 21 candles purged per cell when timeout doubles 10080→20160.
"""

from __future__ import annotations

from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
from crypto_trade.strategies.ml.walk_forward import compute_embargo_candles

# ---------------------------------------------------------------------------
# Minimal valid kwargs required by LightGbmStrategy.__init__ guards
# ---------------------------------------------------------------------------

_BASE_KWARGS = dict(
    features_dir="data/features_v3",
    ensemble_seeds=[42],
    feature_columns=["feat_a", "feat_b"],
)


# ---------------------------------------------------------------------------
# Test 1: label_timeout_minutes value is stored from constructor argument
# ---------------------------------------------------------------------------


def test_label_timeout_minutes_default_preserved():
    """LightGbmStrategy stores the label_timeout_minutes passed at init."""
    strat = LightGbmStrategy(
        **_BASE_KWARGS,
        label_timeout_minutes=10080,
    )
    assert strat.label_timeout_minutes == 10080, (
        f"Expected label_timeout_minutes=10080; got {strat.label_timeout_minutes}. "
        "LightGbmStrategy must store label_timeout_minutes from the constructor."
    )


# ---------------------------------------------------------------------------
# Test 2: iter-v3/068 Path C value 20160 propagates correctly
# ---------------------------------------------------------------------------


def test_label_timeout_minutes_iter068_value_20160():
    """iter-v3/068 Path C: label_timeout_minutes=20160 propagates correctly."""
    strat = LightGbmStrategy(
        **_BASE_KWARGS,
        label_timeout_minutes=20160,
    )
    assert strat.label_timeout_minutes == 20160, (
        f"Expected label_timeout_minutes=20160; got {strat.label_timeout_minutes}. "
        "iter-v3/068 Path C: universal labeling timeout widening to 42 candles at 8h."
    )


# ---------------------------------------------------------------------------
# Test 3: embargo_candles=43 at label_timeout_minutes=20160 + 8h interval
# ---------------------------------------------------------------------------


def test_compute_embargo_candles_iter068_value_43():
    """iter-v3/068 Path C: embargo_candles=43 at label_timeout_minutes=20160 + 8h."""
    embargo = compute_embargo_candles(20160, 480)
    assert embargo == 43, (
        f"Expected embargo_candles=43 (20160//480+1); got {embargo}. "
        "iter-v3/068 Path C: doubled timeout must produce 43-candle embargo per cell."
    )


# ---------------------------------------------------------------------------
# Test 4: baseline /060 anchor embargo_candles=22 at label_timeout_minutes=10080
# ---------------------------------------------------------------------------


def test_compute_embargo_candles_iter060_anchor_value_22():
    """Baseline /060 anchor: embargo_candles=22 at label_timeout_minutes=10080 + 8h."""
    embargo = compute_embargo_candles(10080, 480)
    assert embargo == 22, (
        f"Expected embargo_candles=22 (10080//480+1); got {embargo}. "
        "iter-v3/060 anchor value must remain 22 (regression guard)."
    )


# ---------------------------------------------------------------------------
# Test 5: embargo gap increases by 21 candles when timeout doubles
# ---------------------------------------------------------------------------


def test_compute_embargo_candles_doubles_on_timeout_doubling():
    """Embargo gap increases by 21 candles when timeout doubles 10080→20160."""
    e21 = compute_embargo_candles(10080, 480)
    e42 = compute_embargo_candles(20160, 480)
    assert e42 == 43, f"Expected 43 (20160→43); got {e42}"
    assert e21 == 22, f"Expected 22 (10080→22); got {e21}"
    assert e42 - e21 == 21, (
        f"Expected embargo gap delta=21 (doubled timeout); got {e42 - e21}. "
        "iter-v3/068: additional 21 candles purged per cell cross-cell gap 66→129."
    )
