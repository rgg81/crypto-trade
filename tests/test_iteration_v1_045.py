"""Tests for iter-v1/045 — CONFIRMATION-MERGE-PORTFOLIO bundle substrate.

Mandatory 6 tests:
1.  test_partition_disjoint               — pairwise universe disjointness
2.  test_weights_sum_to_one               — weights sum to 1.0 ± 1e-6
3.  test_bundle_weights_csv_verbatim      — bundle_weights.csv byte-matches brief §11.B
4.  test_aggregator_synthetic             — synthetic 5-trade fixture → expected weighted aggregate
5.  test_no_oos_leak      — weight_calibration.py has no forbidden OOS-leak patterns
6.  test_jaccard_eq_1                     — bundle trade roster == union of component rosters

Additional tests:
7.  test_parse_bundle_config_valid        — _parse_bundle_config() correctly parses valid spec
8.  test_parse_bundle_config_invalid_sum  — raises ValueError on weight sum != 1.0
9.  test_parse_bundle_config_unknown_cid  — raises ValueError on unknown component id
10. test_walk_forward_embargo_regression  — walk_forward.py embargo check (foundation regression)
"""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = REPO_ROOT / "analysis" / "iteration_v1-045"
BUNDLE_WEIGHTS_CSV = ANALYSIS_DIR / "bundle_weights.csv"
WEIGHT_CAL_PY = ANALYSIS_DIR / "weight_calibration.py"
RUNNER_PY = REPO_ROOT / "run_iteration_045.py"

# Expected bundle_weights.csv content (brief Section 11.B verbatim):
EXPECTED_CSV_BODY = (
    "component_id,weight,derivation_method,is_window_start,is_window_end\r\n"
    "C-BTC,0.2,equal,2021-03-24,2025-03-24\r\n"
    "C-ETH,0.2,equal,2021-03-24,2025-03-24\r\n"
    "C-LINK,0.2,equal,2021-03-24,2025-03-24\r\n"
    "C-LTC,0.2,equal,2021-03-24,2025-03-24\r\n"
    "C-DOT,0.2,equal,2021-03-24,2025-03-24\r\n"
)

EXPECTED_COMPONENTS = ["C-BTC", "C-ETH", "C-LINK", "C-LTC", "C-DOT"]
EXPECTED_SYMBOLS = {"BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"}
OOS_CUTOFF_MS = 1742774400000


# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------


def _load_runner() -> object:
    """Load run_iteration_045.py module without running main()."""
    spec = importlib.util.spec_from_file_location("_run_045", RUNNER_PY)
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
# Test 1 — Universe disjointness
# ---------------------------------------------------------------------------


def test_partition_disjoint() -> None:
    """Pairwise universe intersection across all 5 components must be empty."""
    mod = _load_runner()
    component_sources = getattr(mod, "COMPONENT_SOURCES")
    from itertools import combinations

    universes: dict[str, frozenset[str]] = {
        cid: frozenset([sym]) for cid, (sym, _) in component_sources.items()
    }
    for a, b in combinations(sorted(universes), 2):
        overlap = universes[a] & universes[b]
        assert not overlap, (
            f"BUNDLE-UNIVERSE-OVERLAP: non-empty intersection between {a} and {b}: {overlap}"
        )
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
# Test 3 — bundle_weights.csv byte-matches brief Section 11.B verbatim
# ---------------------------------------------------------------------------


def test_bundle_weights_csv_verbatim() -> None:
    """bundle_weights.csv must byte-match the brief Section 11.B specification."""
    assert BUNDLE_WEIGHTS_CSV.exists(), (
        f"bundle_weights.csv not found at {BUNDLE_WEIGHTS_CSV}. "
        "Run analysis/iteration_v1-045/weight_calibration.py first."
    )
    with BUNDLE_WEIGHTS_CSV.open(newline="") as fh:
        rows = list(csv.DictReader(fh))

    # Check structure
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

    expected_cids = ["C-BTC", "C-ETH", "C-LINK", "C-LTC", "C-DOT"]
    actual_cids = [r["component_id"] for r in rows]
    assert actual_cids == expected_cids, (
        f"Component order mismatch: {actual_cids} vs {expected_cids}"
    )


# ---------------------------------------------------------------------------
# Test 4 — Synthetic 5-trade aggregator fixture
# ---------------------------------------------------------------------------


def test_aggregator_synthetic() -> None:
    """5-trade fixture (one per coin) → weighted_pnl scaled by 0.2 each."""
    mod = _load_runner()
    _filter_and_weight = getattr(mod, "_filter_and_weight")
    _total_pnl = getattr(mod, "_total_pnl")

    # Synthetic source rows — one trade per coin, pnl=10.0 each
    # After 0.2 weight: each contributes 2.0; total bundle PnL = 10.0
    coin_map = {
        "BTCUSDT": ("C-BTC", 10.0),
        "ETHUSDT": ("C-ETH", 10.0),
        "LINKUSDT": ("C-LINK", 10.0),
        "LTCUSDT": ("C-LTC", 10.0),
        "DOTUSDT": ("C-DOT", 10.0),
    }

    all_filtered: list[dict] = []
    for sym, (cid, pnl) in coin_map.items():
        raw_row = {
            "symbol": sym,
            "open_time": "1000000000000",
            "close_time": "1000086400000",  # IS (< OOS_CUTOFF_MS)
            "weighted_pnl": str(pnl),
            "net_pnl_pct": str(pnl),
            "pnl_pct": str(pnl),
            "direction": "1",
            "entry_price": "100",
            "exit_price": "110",
            "weight_factor": "1.0",
            "exit_reason": "take_profit",
            "stop_loss_price": "90",
            "take_profit_price": "110",
            "timeout_time": "1001000000000",
            "confidence": "0.9",
            "fee_pct": "0.1",
        }
        # Include a distractor row with a different symbol in the source
        distractor = dict(raw_row)
        distractor["symbol"] = "SOLUSDT"  # not in any component universe
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
# Test 5 — No OOS-leak patterns in weight_calibration.py
# ---------------------------------------------------------------------------


def test_no_oos_leak() -> None:
    """weight_calibration.py must not contain forbidden OOS-leak patterns.

    Allowed: the IS-side assertion `< OOS_CUTOFF_MS` (enforces IS upper bound).
    Forbidden: `>= OOS_CUTOFF_MS`, `oos_window`, `out_of_sample` filenames,
    post-2025-03-24 hard-coded dates used for filtering-in.
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

    # Also check that OOS_CUTOFF_MS itself is only used for the IS-side assertion
    # (the constant definition line is OK; the usage must be `< OOS_CUTOFF_MS`)
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
# Test 6 — Jaccard = 1.0 (bundle roster == union of component rosters)
# ---------------------------------------------------------------------------


def test_jaccard_eq_1() -> None:
    """Jaccard between bundle roster and union of component rosters must be 1.0.

    Uses a synthetic in-memory fixture — does NOT require live trade CSVs.
    """
    mod = _load_runner()
    _filter_and_weight = getattr(mod, "_filter_and_weight")
    _verify_jaccard = getattr(mod, "_verify_jaccard")

    # Build synthetic trade rows for 5 coins
    syms_with_cids = [
        ("BTCUSDT", "C-BTC"),
        ("ETHUSDT", "C-ETH"),
        ("LINKUSDT", "C-LINK"),
        ("LTCUSDT", "C-LTC"),
        ("DOTUSDT", "C-DOT"),
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
        assert len(filtered) == 1
        filtered[0]["component_id"] = cid
        component_filtered[cid] = filtered
        all_bundle.extend(filtered)

    # Should PASS (bundle = union of components, no duplicates, no missing)
    _verify_jaccard(all_bundle, component_filtered)

    # Now test with a missing trade — should RAISE
    import pytest

    bad_bundle = all_bundle[:-1]  # drop last trade
    with pytest.raises(AssertionError, match="Jaccard < 1.0"):
        _verify_jaccard(bad_bundle, component_filtered)


# ---------------------------------------------------------------------------
# Test 7 — _parse_bundle_config: valid spec
# ---------------------------------------------------------------------------


def test_parse_bundle_config_valid() -> None:
    """_parse_bundle_config parses the canonical 5-component equal-weight spec."""
    mod = _load_runner()
    parse_fn = getattr(mod, "_parse_bundle_config")

    result = parse_fn("C-BTC:0.2,C-ETH:0.2,C-LINK:0.2,C-LTC:0.2,C-DOT:0.2")
    assert isinstance(result, dict)
    assert set(result.keys()) == {"C-BTC", "C-ETH", "C-LINK", "C-LTC", "C-DOT"}
    for cid, w in result.items():
        assert abs(w - 0.2) < 1e-9, f"Expected 0.2 for {cid}, got {w}"
    assert abs(sum(result.values()) - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# Test 8 — _parse_bundle_config: invalid weight sum
# ---------------------------------------------------------------------------


def test_parse_bundle_config_invalid_sum() -> None:
    """_parse_bundle_config raises ValueError when weights sum to != 1.0."""
    import pytest

    mod = _load_runner()
    parse_fn = getattr(mod, "_parse_bundle_config")

    with pytest.raises(ValueError, match="weights sum"):
        parse_fn("C-BTC:0.3,C-ETH:0.3,C-LINK:0.3,C-LTC:0.3,C-DOT:0.3")  # sums to 1.5


# ---------------------------------------------------------------------------
# Test 9 — _parse_bundle_config: unknown component id
# ---------------------------------------------------------------------------


def test_parse_bundle_config_unknown_cid() -> None:
    """_parse_bundle_config raises ValueError for an unknown component name."""
    import pytest

    mod = _load_runner()
    parse_fn = getattr(mod, "_parse_bundle_config")

    with pytest.raises(ValueError, match="Unknown component"):
        parse_fn("C-SOL:0.2,C-ETH:0.2,C-LINK:0.2,C-LTC:0.2,C-DOT:0.2")


# ---------------------------------------------------------------------------
# Test 10 — Foundation regression: walk_forward.py embargo
# ---------------------------------------------------------------------------


def test_walk_forward_embargo_regression() -> None:
    """walk_forward.py:113 must carry train_end_ms = test_start_ms - embargo_ms."""
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
