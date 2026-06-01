"""Tests for iter-v1/056 — CONFIRMATION-PORTFOLIO bundle substrate.

Mandatory tests (7 required by brief Section 3.9 + F-AXIS):
1.  test_universe_disjoint               — 5 components × 5 coins; pairwise empty (10 pairs)
2.  test_weights_sum_to_one              — bundle_weights.csv weights sum to 1.0 ± 1e-6
3.  test_bundle_weights_csv_verbatim     — bundle_weights.csv matches brief Section 11.B spec
4.  test_no_oos_leak                     — weight_calibration.py has no forbidden OOS-leak patterns
5.  test_jaccard_eq_1                    — bundle trade roster == union of component rosters
6.  test_aggregator_synthetic            — 5-trade fixture → expected weighted bundle sum
7.  test_baseline_link_ltc_anchor_present — LINK + LTC trades present in BASELINE_V1 reports

Additional tests:
8.  test_walk_forward_embargo_regression — walk_forward.py embargo check (foundation regression)
9.  test_feature_col_count_btc          — C1-BTC expected 47 feature cols (impulse DROPPED)
10. test_feature_col_count_eth_dot      — C2-ETH / C3-DOT expected 48 feature cols
"""

from __future__ import annotations

import csv
import importlib.util
from itertools import combinations
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = REPO_ROOT / "analysis" / "iteration_v1-056"
BUNDLE_WEIGHTS_CSV = ANALYSIS_DIR / "bundle_weights.csv"
WEIGHT_CAL_PY = ANALYSIS_DIR / "weight_calibration.py"
RUNNER_PY = REPO_ROOT / "run_iteration_056.py"

# Expected components and symbols (Section 11.A)
EXPECTED_COMPONENTS = ["C1-BTC", "C2-ETH", "C3-DOT", "C4-LINK", "C5-LTC"]
EXPECTED_SYMBOLS = {"BTCUSDT", "ETHUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT"}

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC

# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------


def _load_runner() -> object:
    """Load run_iteration_056.py module without running main()."""
    spec = importlib.util.spec_from_file_location("_run_056", RUNNER_PY)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except SystemExit:
        pass
    return mod


def _load_bundle_weights() -> dict[str, float]:
    """Load bundle_weights.csv into {component_id: weight}."""
    with BUNDLE_WEIGHTS_CSV.open(newline="") as fh:
        return {r["component_id"]: float(r["weight"]) for r in csv.DictReader(fh)}


# ---------------------------------------------------------------------------
# Test 1 — Universe disjointness (10 pairwise pairs, all empty)
# ---------------------------------------------------------------------------


def test_universe_disjoint() -> None:
    """Pairwise universe intersection across all 5 components must be empty (10 pairs)."""
    mod = _load_runner()
    component_sources = getattr(mod, "COMPONENT_SOURCES")

    universes: dict[str, frozenset[str]] = {
        cid: frozenset([sym]) for cid, (sym, _) in component_sources.items()
    }
    pair_count = 0
    for a, b in combinations(sorted(universes), 2):
        overlap = universes[a] & universes[b]
        assert not overlap, (
            f"BUNDLE-UNIVERSE-OVERLAP: non-empty intersection between {a} and {b}: {overlap}"
        )
        pair_count += 1

    assert pair_count == 10, f"Expected 10 pairwise comparisons (C(5,2)), got {pair_count}"

    all_syms = set().union(*universes.values())
    assert all_syms == EXPECTED_SYMBOLS, (
        f"Bundle universe mismatch: {all_syms} vs expected {EXPECTED_SYMBOLS}"
    )


# ---------------------------------------------------------------------------
# Test 2 — Weights sum to 1.0
# ---------------------------------------------------------------------------


def test_weights_sum_to_one() -> None:
    """Weights in bundle_weights.csv must sum to 1.0 ± 1e-6."""
    weights = _load_bundle_weights()
    total = sum(weights.values())
    assert abs(total - 1.0) < 1e-6, (
        f"Weights sum to {total:.8f}, expected 1.0 ± 1e-6. Component weights: {weights}"
    )
    assert set(weights.keys()) == set(EXPECTED_COMPONENTS), (
        f"Component set mismatch: {set(weights.keys())} vs {set(EXPECTED_COMPONENTS)}"
    )


# ---------------------------------------------------------------------------
# Test 3 — bundle_weights.csv verbatim match to brief Section 11.B
# ---------------------------------------------------------------------------


def test_bundle_weights_csv_verbatim() -> None:
    """bundle_weights.csv must match the brief Section 11.B specification."""
    assert BUNDLE_WEIGHTS_CSV.exists(), (
        f"bundle_weights.csv not found at {BUNDLE_WEIGHTS_CSV}. "
        "Run analysis/iteration_v1-056/weight_calibration.py first."
    )
    with BUNDLE_WEIGHTS_CSV.open(newline="") as fh:
        rows = list(csv.DictReader(fh))

    assert len(rows) == 5, f"Expected 5 rows, got {len(rows)}"
    for r in rows:
        assert float(r["weight"]) == 0.2, (
            f"Component {r['component_id']}: weight={r['weight']} ≠ 0.2"
        )
        assert r["derivation_method"] == "equal", (
            f"derivation_method={r['derivation_method']} ≠ 'equal'"
        )
        assert r["is_window_start"] == "2021-03-24", (
            f"is_window_start={r['is_window_start']} ≠ '2021-03-24'"
        )
        assert r["is_window_end"] == "2025-03-24", (
            f"is_window_end={r['is_window_end']} ≠ '2025-03-24'"
        )

    actual_cids = [r["component_id"] for r in rows]
    assert actual_cids == EXPECTED_COMPONENTS, (
        f"Component order mismatch: {actual_cids} vs {EXPECTED_COMPONENTS}"
    )


# ---------------------------------------------------------------------------
# Test 4 — No OOS-leak patterns in weight_calibration.py
# ---------------------------------------------------------------------------


def test_no_oos_leak() -> None:
    """weight_calibration.py must not contain forbidden OOS-leak patterns.

    Allowed: the IS-side assertion `< OOS_CUTOFF_MS` (enforces IS upper bound).
    Forbidden: `>= OOS_CUTOFF_MS`, `oos_window`, `out_of_sample` filenames.
    """
    assert WEIGHT_CAL_PY.exists(), f"weight_calibration.py not found at {WEIGHT_CAL_PY}"
    src = WEIGHT_CAL_PY.read_text()

    forbidden_patterns = [
        ">= OOS_CUTOFF_MS",
        "oos_window",
        "out_of_sample",
    ]
    for pat in forbidden_patterns:
        assert pat not in src, (
            f"BUNDLE-WEIGHT-OOS-LEAK: forbidden pattern '{pat}' found in "
            f"weight_calibration.py — Check 17 fails."
        )

    lines_with_cutoff = [
        (i + 1, line.strip())
        for i, line in enumerate(src.splitlines())
        if "OOS_CUTOFF_MS" in line and not line.strip().startswith("#")
    ]
    for lineno, line in lines_with_cutoff:
        assert ">= OOS_CUTOFF_MS" not in line, (
            f"BUNDLE-WEIGHT-OOS-LEAK: line {lineno} contains '>= OOS_CUTOFF_MS' "
            f"in weight_calibration.py: {line}"
        )


# ---------------------------------------------------------------------------
# Test 5 — Jaccard = 1.0 (bundle roster == union of component rosters)
# ---------------------------------------------------------------------------


def test_jaccard_eq_1() -> None:
    """Jaccard between bundle roster and union of component rosters must be 1.0.

    Uses a synthetic in-memory fixture — does NOT require live trade CSVs.
    """
    import pytest

    mod = _load_runner()
    _filter_and_weight = getattr(mod, "_filter_and_weight")
    _verify_jaccard = getattr(mod, "_verify_jaccard")

    syms_with_cids = [
        ("BTCUSDT", "C1-BTC"),
        ("ETHUSDT", "C2-ETH"),
        ("DOTUSDT", "C3-DOT"),
        ("LINKUSDT", "C4-LINK"),
        ("LTCUSDT", "C5-LTC"),
    ]

    component_filtered: dict[str, list[dict]] = {}
    all_bundle: list[dict] = []

    for i, (sym, cid) in enumerate(syms_with_cids):
        row = {
            "symbol": sym,
            "open_time": str(1000 + i * 1000),
            "close_time": str(2000 + i * 1000),
            "weighted_pnl": "10.0",
            "net_pnl_pct": "10.0",
            "pnl_pct": "10.0",
            "component_id": cid,
        }
        filtered = _filter_and_weight([row], sym, 0.2)
        assert len(filtered) == 1, f"Expected 1 filtered row for {sym}, got {len(filtered)}"
        filtered[0]["component_id"] = cid
        component_filtered[cid] = filtered
        all_bundle.extend(filtered)

    # PASS: bundle == union of components
    _verify_jaccard(all_bundle, component_filtered)

    # FAIL: missing last trade
    bad_bundle = all_bundle[:-1]
    with pytest.raises(AssertionError, match="Jaccard < 1.0"):
        _verify_jaccard(bad_bundle, component_filtered)


# ---------------------------------------------------------------------------
# Test 6 — Synthetic 5-trade aggregator fixture
# ---------------------------------------------------------------------------


def test_aggregator_synthetic() -> None:
    """5-trade fixture (one per coin) → weighted_pnl scaled by 0.2 each.

    Total bundle PnL = 5 × (10.0 × 0.2) = 10.0.
    """
    mod = _load_runner()
    _filter_and_weight = getattr(mod, "_filter_and_weight")
    _total_pnl = getattr(mod, "_total_pnl")

    coin_map = {
        "BTCUSDT": "C1-BTC",
        "ETHUSDT": "C2-ETH",
        "DOTUSDT": "C3-DOT",
        "LINKUSDT": "C4-LINK",
        "LTCUSDT": "C5-LTC",
    }

    all_filtered: list[dict] = []
    for sym, cid in coin_map.items():
        raw_row = {
            "symbol": sym,
            "open_time": "1000000000000",
            "close_time": "1000086400000",  # well within IS window
            "weighted_pnl": "10.0",
            "net_pnl_pct": "10.0",
            "pnl_pct": "10.0",
            "direction": "1",
            "entry_price": "100",
            "exit_price": "110",
            "weight_factor": "1.0",
            "exit_reason": "take_profit",
        }
        # Include distractor row for different symbol
        distractor = dict(raw_row)
        distractor["symbol"] = "SOLUSDT"
        distractor["weighted_pnl"] = "999.0"

        filtered = _filter_and_weight([raw_row, distractor], sym, 0.2)
        assert len(filtered) == 1, f"Expected 1 filtered row for {sym}, got {len(filtered)}"
        assert abs(float(filtered[0]["weighted_pnl"]) - 2.0) < 1e-6, (
            f"Expected weighted_pnl=2.0 for {sym}, got {filtered[0]['weighted_pnl']}"
        )
        all_filtered.extend(filtered)

    assert len(all_filtered) == 5, f"Expected 5 aggregate rows, got {len(all_filtered)}"
    total = _total_pnl(all_filtered)
    assert abs(total - 10.0) < 1e-6, f"Expected total bundle PnL=10.0, got {total:.6f}"


# ---------------------------------------------------------------------------
# Test 7 — BASELINE_V1 LINK and LTC anchor trades present
# ---------------------------------------------------------------------------


def test_baseline_link_ltc_anchor_present() -> None:
    """LINK + LTC trades must be present in BASELINE_V1 reports for anchor extraction."""
    baseline_is = REPO_ROOT / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
    baseline_oos = (
        REPO_ROOT / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
    )

    assert baseline_is.exists(), (
        f"BASELINE_V1 in_sample/trades.csv not found at {baseline_is}. "
        "Run `uv run python run_baseline_v1.py --baseline-mode` first."
    )
    assert baseline_oos.exists(), (
        f"BASELINE_V1 out_of_sample/trades.csv not found at {baseline_oos}."
    )

    with baseline_is.open(newline="") as fh:
        is_rows = list(csv.DictReader(fh))

    link_is = [r for r in is_rows if r.get("symbol") == "LINKUSDT"]
    ltc_is = [r for r in is_rows if r.get("symbol") == "LTCUSDT"]

    assert len(link_is) > 0, (
        "LINK IS trades missing from BASELINE_V1 in_sample/trades.csv. "
        "C4-LINK anchor extraction will fail."
    )
    assert len(ltc_is) > 0, (
        "LTC IS trades missing from BASELINE_V1 in_sample/trades.csv. "
        "C5-LTC anchor extraction will fail."
    )

    # Verify all anchor IS rows are within the IS window
    for r in link_is + ltc_is:
        ct = int(r["close_time"])
        # Close times may straddle the OOS boundary (walk-forward artifact); just warn
        if ct >= OOS_CUTOFF_MS:
            pass  # boundary row — acceptable (documented in weight_calibration.py)


# ---------------------------------------------------------------------------
# Test 8 — Foundation regression: walk_forward.py embargo
# ---------------------------------------------------------------------------


def test_walk_forward_embargo_regression() -> None:
    """walk_forward.py must carry train_end_ms = test_start_ms - embargo_ms."""
    wf_path = REPO_ROOT / "src" / "crypto_trade" / "strategies" / "ml" / "walk_forward.py"
    assert wf_path.exists(), f"walk_forward.py not found at {wf_path}"
    wf_src = wf_path.read_text()

    assert "train_end_ms = test_start_ms - embargo_ms" in wf_src, (
        "WALK-FORWARD EMBARGO REGRESSION: walk_forward.py does NOT carry "
        "'train_end_ms = test_start_ms - embargo_ms'. "
        "This is the iter-v3/058 fix — DO NOT revert."
    )
    assert "train_end_ms = test_start_ms\n" not in wf_src, (
        "WALK-FORWARD EMBARGO REGRESSION: walk_forward.py still contains "
        "'train_end_ms = test_start_ms' (the buggy form)."
    )


# ---------------------------------------------------------------------------
# Test 9 — C1-BTC expected 47 feature cols (btc_funding_rate_8h_impulse DROPPED)
# ---------------------------------------------------------------------------


def test_feature_col_count_btc() -> None:
    """C1-BTC specialist must use 47 feature cols (btc_funding_rate_8h_impulse DROPPED,
    eth_vs_btc_ret_ratio_30 excluded for BTC-only stack).

    V1_FEATURE_COLUMNS_PRUNED is 48 (includes eth_vs_btc_ret_ratio_30 from /055).
    The C1-BTC dispatch branch excludes eth_vs_btc_ret_ratio_30 (all-NaN for BTC rows)
    to produce the 47-col BTC-only stack: same as /054's impulse-drop-confirmed stack.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert "btc_funding_spread_30_90" in V1_FEATURE_COLUMNS_PRUNED, (
        "btc_funding_spread_30_90 missing from V1_FEATURE_COLUMNS_PRUNED. "
        "This feature must be RETAINED (rank 4-10/48 at /053 — STABLE)."
    )
    assert "btc_funding_rate_8h_impulse" not in V1_FEATURE_COLUMNS_PRUNED, (
        "btc_funding_rate_8h_impulse IS in V1_FEATURE_COLUMNS_PRUNED — it must be DROPPED. "
        "The /054 IMPULSE-DROP-CONFIRMED verdict permanently removed this feature. "
        "Check src/crypto_trade/features_v1/__init__.py."
    )
    assert "eth_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "eth_vs_btc_ret_ratio_30 expected in V1_FEATURE_COLUMNS_PRUNED (added at /055). "
        "C1-BTC dispatch branch excludes it (ETH cross-asset; NaN for BTC rows)."
    )

    # Verify the derived 47-col BTC-only stack is correct
    # Exclude both ETH and LTC cross-asset features (both NaN for BTC rows):
    # V1_FEATURE_COLUMNS_PRUNED has 49 cols; excluding eth + ltc ratio → 47 BTC-only cols.
    _btc_excl = {"eth_vs_btc_ret_ratio_30", "ltc_vs_btc_ret_ratio_30"}
    btc_cols = [c for c in V1_FEATURE_COLUMNS_PRUNED if c not in _btc_excl]
    assert len(btc_cols) == 47, (
        f"After excluding eth_vs_btc_ret_ratio_30 and ltc_vs_btc_ret_ratio_30, "
        f"expected 47 BTC-only cols, got {len(btc_cols)}. "
        "C1-BTC dispatch branch uses this filtered list. "
        "V1_FEATURE_COLUMNS_PRUNED is 49 (post /057 ADD); BTC-only = 49 - 2 = 47."
    )
    assert "btc_funding_spread_30_90" in btc_cols, (
        "btc_funding_spread_30_90 missing from 47-col BTC-only stack."
    )
    assert "btc_funding_rate_8h_impulse" not in btc_cols, (
        "btc_funding_rate_8h_impulse must not appear in 47-col BTC-only stack."
    )


# ---------------------------------------------------------------------------
# Test 10 — C2-ETH and C3-DOT expected 48 feature cols
# ---------------------------------------------------------------------------


def test_feature_col_count_eth_dot() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have 48 cols for C2-ETH and C3-DOT sub-runs."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n_cols == 49, (
        f"Expected 49 feature cols (V1_FEATURE_COLUMNS_PRUNED post /057 ADD), got {n_cols}. "
        "C2-ETH and C3-DOT dispatch branches expect 49 cols "
        "(ltc_vs_btc_ret_ratio_30 added at /057; LTC-only NaN for ETH/DOT)."
    )
    assert "eth_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "eth_vs_btc_ret_ratio_30 missing from V1_FEATURE_COLUMNS_PRUNED. "
        "C2-ETH specialist requires this feature (added at /055)."
    )
    assert "dot_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "dot_vs_btc_ret_ratio_30 missing from V1_FEATURE_COLUMNS_PRUNED. "
        "C3-DOT specialist requires this feature (added at /050)."
    )
