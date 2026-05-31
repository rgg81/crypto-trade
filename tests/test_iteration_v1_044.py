"""Tests for iter-v1/044 — CONFIRMATION-MERGE-PORTFOLIO bundle dispatch.

Covers 12 mandatory test items:

1.  test_v1_044_bundle_config_flag_parsing_valid — _parse_bundle_config() correctly
    parses a valid spec with 3 components summing to 1.0.
2.  test_v1_044_bundle_config_invalid_weight_sum — _parse_bundle_config() raises
    ValueError when weights sum to != 1.0.
3.  test_v1_044_bundle_config_invalid_component_name — _parse_bundle_config() raises
    ValueError for unknown component name.
4.  test_v1_044_bundle_config_malformed_token — _parse_bundle_config() raises
    ValueError for a token missing the colon separator.
5.  test_v1_044_in_baseline_catchall_exclusion — "v1-044" is in the catch-all
    exclusion tuple in run_baseline_v1.py source.
6.  test_v1_044_dispatch_banner_present — runner source contains expected banner
    "[iter-v1/044] CONFIRMATION-MERGE-PORTFOLIO ACTIVE".
7.  test_v1_044_bundle_aggregator_active_weight_renorm — bundle_aggregator()
    correctly renormalizes weights when only a subset of components are active
    in a cell (P0+P1 active, P2 silent → P0 gets w0/(w0+w1), P1 gets w1/(w0+w1)).
8.  test_v1_044_bundle_aggregator_all_active — bundle_aggregator() computes
    correct weighted PnL when all 3 components emit trades in a cell.
9.  test_v1_044_bundle_aggregator_comparison_csv_schema — bundle_aggregator()
    writes comparison.csv with required columns: metric, in_sample, out_of_sample, ratio.
10. test_v1_044_bundle_aggregator_regime_attribution_schema — bundle_aggregator()
    calls build_regime_attribution_csv and produces regime_attribution.csv with
    the required schema columns.
11. test_v1_044_pairwise_correlation_schema — bundle_aggregator() writes
    per_component_correlation.csv with columns: pair, daily_pnl_corr, trade_jaccard.
12. test_v1_044_component_substitution_schema — bundle_aggregator() writes
    component_substitution.csv with columns: dropped_component, oos_sharpe_delta.

Foundation regression:
- test_v1_044_walk_forward_embargo_regression — walk_forward.py:113 carries
  train_end_ms = test_start_ms - embargo_ms (not = test_start_ms).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Test 1 — _parse_bundle_config: valid spec
# ---------------------------------------------------------------------------


def test_v1_044_bundle_config_flag_parsing_valid() -> None:
    """_parse_bundle_config() must parse 'baseline:0.50,v1-036:0.30,v1-043:0.20'."""
    # Import via source to avoid running main()
    import importlib.util

    _runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    spec = importlib.util.spec_from_file_location("_runner_v1", _runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Don't execute top-level code (argparse sets up in main()); only load the module.
    # Use exec_module but protect against the argparse parse_args() call in main().
    # The functions we need (_parse_bundle_config, bundle_aggregator) are module-level
    # and will be available after exec_module.
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except SystemExit:
        pass  # argparse calls sys.exit if no args passed; catch it

    parse_fn = getattr(mod, "_parse_bundle_config", None)
    assert parse_fn is not None, "_parse_bundle_config not found in runner module"

    result = parse_fn("baseline:0.50,v1-036:0.30,v1-043:0.20")
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert set(result.keys()) == {"baseline", "v1-036", "v1-043"}, (
        f"Keys mismatch: {set(result.keys())}"
    )
    assert abs(result["baseline"] - 0.50) < 1e-9
    assert abs(result["v1-036"] - 0.30) < 1e-9
    assert abs(result["v1-043"] - 0.20) < 1e-9
    assert abs(sum(result.values()) - 1.0) < 1e-6, (
        f"Weights sum to {sum(result.values())}, expected 1.0"
    )


# ---------------------------------------------------------------------------
# Test 2 — _parse_bundle_config: invalid weight sum
# ---------------------------------------------------------------------------


def test_v1_044_bundle_config_invalid_weight_sum() -> None:
    """_parse_bundle_config() must raise ValueError when weights sum to != 1.0."""
    import importlib.util

    _runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    spec = importlib.util.spec_from_file_location("_runner_v1_t2", _runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except SystemExit:
        pass

    parse_fn = getattr(mod, "_parse_bundle_config")

    import pytest

    with pytest.raises(ValueError, match="weights sum"):
        parse_fn("baseline:0.50,v1-036:0.30,v1-043:0.30")  # sums to 1.10


# ---------------------------------------------------------------------------
# Test 3 — _parse_bundle_config: invalid component name
# ---------------------------------------------------------------------------


def test_v1_044_bundle_config_invalid_component_name() -> None:
    """_parse_bundle_config() must raise ValueError for unknown component."""
    import importlib.util

    _runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    spec = importlib.util.spec_from_file_location("_runner_v1_t3", _runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except SystemExit:
        pass

    parse_fn = getattr(mod, "_parse_bundle_config")

    import pytest

    with pytest.raises(ValueError, match="Unknown component"):
        parse_fn("baseline:0.50,v1-099:0.30,v1-043:0.20")


# ---------------------------------------------------------------------------
# Test 4 — _parse_bundle_config: malformed token (no colon)
# ---------------------------------------------------------------------------


def test_v1_044_bundle_config_malformed_token() -> None:
    """_parse_bundle_config() must raise ValueError for a token missing ':'."""
    import importlib.util

    _runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    spec = importlib.util.spec_from_file_location("_runner_v1_t4", _runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except SystemExit:
        pass

    parse_fn = getattr(mod, "_parse_bundle_config")

    import pytest

    with pytest.raises(ValueError, match="Invalid token"):
        parse_fn("baseline0.50,v1-036:0.30,v1-043:0.20")  # missing colon on first token


# ---------------------------------------------------------------------------
# Test 5 — "v1-044" in catch-all exclusion tuple
# ---------------------------------------------------------------------------


def test_v1_044_in_baseline_catchall_exclusion() -> None:
    """'v1-044' must appear in the baseline catch-all exclusion tuple."""
    runner_src = (Path(__file__).parent.parent / "run_baseline_v1.py").read_text()
    assert '"v1-044"' in runner_src, (
        "'v1-044' not found in run_baseline_v1.py source. Add it to the catch-all exclusion tuple."
    )


# ---------------------------------------------------------------------------
# Test 6 — dispatch banner present in source
# ---------------------------------------------------------------------------


def test_v1_044_dispatch_banner_present() -> None:
    """Runner source must contain the /044 CONFIRMATION-MERGE-PORTFOLIO banner."""
    runner_src = (Path(__file__).parent.parent / "run_baseline_v1.py").read_text()
    assert "[iter-v1/044] CONFIRMATION-MERGE-PORTFOLIO ACTIVE" in runner_src, (
        "Expected bundle dispatch banner '[iter-v1/044] CONFIRMATION-MERGE-PORTFOLIO ACTIVE' "
        "not found in run_baseline_v1.py."
    )


# ---------------------------------------------------------------------------
# Helpers for bundle_aggregator unit tests
# ---------------------------------------------------------------------------


def _make_mock_trades_csv(
    tmp_dir: Path,
    split: str,
    rows: list[dict],
) -> None:
    """Write a minimal trades.csv to tmp_dir/split/trades.csv."""
    import csv

    split_dir = tmp_dir / split
    split_dir.mkdir(parents=True, exist_ok=True)
    path = split_dir / "trades.csv"
    if not rows:
        path.write_text("symbol,open_time,close_time,pnl_pct\n")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_runner_module(tag: str):
    """Load run_baseline_v1 module without running main()."""
    import importlib.util

    _runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    spec = importlib.util.spec_from_file_location(f"_runner_v1_{tag}", _runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except SystemExit:
        pass
    return mod


# IS cutoff (2025-03-24 00:00 UTC in ms)
_IS_CUTOFF_MS = 1742774400000


# ---------------------------------------------------------------------------
# Test 7 — bundle_aggregator: active-weight renormalization
# ---------------------------------------------------------------------------


def test_v1_044_bundle_aggregator_active_weight_renorm() -> None:
    """Active-weight renormalization: P2 silent → P0 and P1 weights renormalize.

    Cell key (LINKUSDT, open_time=1000):
      P0 active: pnl_pct = +0.10
      P1 active: pnl_pct = +0.20
      P2 silent (no trade)
    Weights: P0=0.50, P1=0.30, P2=0.20
    Active sum = 0.80
    Expected bundle pnl = (0.50/0.80)*0.10 + (0.30/0.80)*0.20
                        = 0.625*0.10 + 0.375*0.20
                        = 0.0625 + 0.0750 = 0.1375
    """
    mod = _load_runner_module("t7")
    bundle_aggregator = getattr(mod, "bundle_aggregator")

    # All trades in OOS (close_time >= _IS_CUTOFF_MS)
    _ot = 1000
    _ct = _IS_CUTOFF_MS + 1000  # OOS

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # Component dirs
        p0_dir = tmp_path / "baseline"
        p1_dir = tmp_path / "v1-036"
        p2_dir = tmp_path / "v1-043"
        bundle_out = tmp_path / "bundle"

        _make_mock_trades_csv(
            p0_dir,
            "out_of_sample",
            [{"symbol": "LINKUSDT", "open_time": _ot, "close_time": _ct, "pnl_pct": 0.10}],
        )
        _make_mock_trades_csv(
            p1_dir,
            "out_of_sample",
            [{"symbol": "LINKUSDT", "open_time": _ot, "close_time": _ct, "pnl_pct": 0.20}],
        )
        _make_mock_trades_csv(p2_dir, "out_of_sample", [])  # P2 silent

        bundle_aggregator(
            component_dirs={"baseline": p0_dir, "v1-036": p1_dir, "v1-043": p2_dir},
            weights={"baseline": 0.50, "v1-036": 0.30, "v1-043": 0.20},
            is_cutoff_ms=_IS_CUTOFF_MS,
            btc_klines_path=None,
            bundle_out_dir=bundle_out,
        )

        import pandas as pd

        agg_df = pd.read_csv(bundle_out / "out_of_sample" / "aggregated_trades.csv")
        assert len(agg_df) == 1, f"Expected 1 bundle trade, got {len(agg_df)}"
        wpnl = float(agg_df.iloc[0]["weighted_pnl"])
        expected = (0.50 / 0.80) * 0.10 + (0.30 / 0.80) * 0.20
        assert abs(wpnl - expected) < 1e-9, (
            f"Active-weight renormalization mismatch: got {wpnl:.8f}, expected {expected:.8f}"
        )


# ---------------------------------------------------------------------------
# Test 8 — bundle_aggregator: all 3 components active in cell
# ---------------------------------------------------------------------------


def test_v1_044_bundle_aggregator_all_active() -> None:
    """When all 3 components emit a trade in the same cell, use full weights.

    Cell (LINKUSDT, open_time=1000):
      P0 pnl_pct = +0.10, w0 = 0.50
      P1 pnl_pct = +0.20, w1 = 0.30
      P2 pnl_pct = -0.05, w2 = 0.20
    Expected bundle pnl = 0.50*0.10 + 0.30*0.20 + 0.20*(-0.05)
                        = 0.05 + 0.06 - 0.01 = 0.10
    """
    mod = _load_runner_module("t8")
    bundle_aggregator = getattr(mod, "bundle_aggregator")

    _ot = 1000
    _ct = _IS_CUTOFF_MS + 1000  # OOS

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        p0_dir, p1_dir, p2_dir = (
            tmp_path / "baseline",
            tmp_path / "v1-036",
            tmp_path / "v1-043",
        )
        bundle_out = tmp_path / "bundle"

        for comp_dir, pnl in ((p0_dir, 0.10), (p1_dir, 0.20), (p2_dir, -0.05)):
            _make_mock_trades_csv(
                comp_dir,
                "out_of_sample",
                [{"symbol": "LINKUSDT", "open_time": _ot, "close_time": _ct, "pnl_pct": pnl}],
            )

        bundle_aggregator(
            component_dirs={"baseline": p0_dir, "v1-036": p1_dir, "v1-043": p2_dir},
            weights={"baseline": 0.50, "v1-036": 0.30, "v1-043": 0.20},
            is_cutoff_ms=_IS_CUTOFF_MS,
            btc_klines_path=None,
            bundle_out_dir=bundle_out,
        )

        import pandas as pd

        agg_df = pd.read_csv(bundle_out / "out_of_sample" / "aggregated_trades.csv")
        assert len(agg_df) == 1
        wpnl = float(agg_df.iloc[0]["weighted_pnl"])
        expected = 0.50 * 0.10 + 0.30 * 0.20 + 0.20 * (-0.05)
        assert abs(wpnl - expected) < 1e-9, (
            f"All-active bundle PnL mismatch: got {wpnl:.8f}, expected {expected:.8f}"
        )


# ---------------------------------------------------------------------------
# Test 9 — bundle_aggregator: comparison.csv schema
# ---------------------------------------------------------------------------


def test_v1_044_bundle_aggregator_comparison_csv_schema() -> None:
    """comparison.csv must have columns: metric, in_sample, out_of_sample, ratio."""
    mod = _load_runner_module("t9")
    bundle_aggregator = getattr(mod, "bundle_aggregator")

    _ot = 1000
    _ct = _IS_CUTOFF_MS + 1000

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        p0_dir = tmp_path / "baseline"
        p1_dir = tmp_path / "v1-036"
        p2_dir = tmp_path / "v1-043"
        bundle_out = tmp_path / "bundle"

        for comp_dir, pnl in ((p0_dir, 0.10), (p1_dir, 0.20), (p2_dir, 0.05)):
            _make_mock_trades_csv(
                comp_dir,
                "out_of_sample",
                [{"symbol": "LINKUSDT", "open_time": _ot, "close_time": _ct, "pnl_pct": pnl}],
            )

        bundle_aggregator(
            component_dirs={"baseline": p0_dir, "v1-036": p1_dir, "v1-043": p2_dir},
            weights={"baseline": 0.50, "v1-036": 0.30, "v1-043": 0.20},
            is_cutoff_ms=_IS_CUTOFF_MS,
            btc_klines_path=None,
            bundle_out_dir=bundle_out,
        )

        import pandas as pd

        comp_df = pd.read_csv(bundle_out / "comparison.csv")
        required_cols = {"metric", "in_sample", "out_of_sample", "ratio"}
        assert required_cols.issubset(set(comp_df.columns)), (
            f"comparison.csv missing required columns. "
            f"Expected {required_cols}, got {set(comp_df.columns)}"
        )
        required_metrics = {
            "monthly_sharpe",
            "max_drawdown",
            "n_trades",
            "win_rate",
            "profit_factor",
        }
        present_metrics = set(comp_df["metric"].tolist())
        assert required_metrics.issubset(present_metrics), (
            f"comparison.csv missing required metric rows. "
            f"Expected {required_metrics}, got {present_metrics}"
        )


# ---------------------------------------------------------------------------
# Test 10 — bundle_aggregator: regime_attribution.csv schema
# ---------------------------------------------------------------------------


def test_v1_044_bundle_aggregator_regime_attribution_schema() -> None:
    """regime_attribution.csv must have the required schema columns."""
    mod = _load_runner_module("t10")
    bundle_aggregator = getattr(mod, "bundle_aggregator")

    _ot = 1000
    _ct = _IS_CUTOFF_MS + 1000

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        p0_dir = tmp_path / "baseline"
        p1_dir = tmp_path / "v1-036"
        p2_dir = tmp_path / "v1-043"
        bundle_out = tmp_path / "bundle"

        for comp_dir, pnl in ((p0_dir, 0.10), (p1_dir, 0.20), (p2_dir, 0.05)):
            _make_mock_trades_csv(
                comp_dir,
                "out_of_sample",
                [{"symbol": "LINKUSDT", "open_time": _ot, "close_time": _ct, "pnl_pct": pnl}],
            )

        bundle_aggregator(
            component_dirs={"baseline": p0_dir, "v1-036": p1_dir, "v1-043": p2_dir},
            weights={"baseline": 0.50, "v1-036": 0.30, "v1-043": 0.20},
            is_cutoff_ms=_IS_CUTOFF_MS,
            btc_klines_path=None,
            bundle_out_dir=bundle_out,
        )

        import pandas as pd

        ra_path = bundle_out / "regime_attribution.csv"
        assert ra_path.exists(), f"regime_attribution.csv not found at {ra_path}"
        ra_df = pd.read_csv(ra_path)
        required_cols = {
            "regime_tag",
            "in_sample",
            "candidate_sharpe",
            "candidate_max_dd",
            "candidate_trade_count",
            "baseline_sharpe",
            "baseline_max_dd",
            "baseline_trade_count",
        }
        assert required_cols.issubset(set(ra_df.columns)), (
            f"regime_attribution.csv missing columns. "
            f"Expected {required_cols}, got {set(ra_df.columns)}"
        )
        assert len(ra_df) >= 5, (
            f"regime_attribution.csv has < 5 rows (expected ≥5 regimes): {len(ra_df)}"
        )


# ---------------------------------------------------------------------------
# Test 11 — bundle_aggregator: per_component_correlation.csv schema
# ---------------------------------------------------------------------------


def test_v1_044_pairwise_correlation_schema() -> None:
    """per_component_correlation.csv must have: pair, daily_pnl_corr, trade_jaccard."""
    mod = _load_runner_module("t11")
    bundle_aggregator = getattr(mod, "bundle_aggregator")

    _ct = _IS_CUTOFF_MS + 1000

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        p0_dir = tmp_path / "baseline"
        p1_dir = tmp_path / "v1-036"
        p2_dir = tmp_path / "v1-043"
        bundle_out = tmp_path / "bundle"

        # Multiple trades across different open_times to get real correlations
        for comp_dir, pnl_base in ((p0_dir, 0.10), (p1_dir, 0.20), (p2_dir, 0.05)):
            _make_mock_trades_csv(
                comp_dir,
                "out_of_sample",
                [
                    {
                        "symbol": "LINKUSDT",
                        "open_time": 1000 + i * 1000,
                        "close_time": _ct + i * 1000,
                        "pnl_pct": pnl_base * (1 + 0.1 * i),
                    }
                    for i in range(5)
                ],
            )

        bundle_aggregator(
            component_dirs={"baseline": p0_dir, "v1-036": p1_dir, "v1-043": p2_dir},
            weights={"baseline": 0.50, "v1-036": 0.30, "v1-043": 0.20},
            is_cutoff_ms=_IS_CUTOFF_MS,
            btc_klines_path=None,
            bundle_out_dir=bundle_out,
        )

        import pandas as pd

        corr_path = bundle_out / "per_component_correlation.csv"
        assert corr_path.exists(), f"per_component_correlation.csv not found at {corr_path}"
        corr_df = pd.read_csv(corr_path)
        required_cols = {"pair", "daily_pnl_corr", "trade_jaccard"}
        assert required_cols.issubset(set(corr_df.columns)), (
            f"per_component_correlation.csv missing columns. "
            f"Expected {required_cols}, got {set(corr_df.columns)}"
        )
        # Expect 3 pairwise entries for 3 components: (P0,P1), (P0,P2), (P1,P2)
        assert len(corr_df) == 3, f"Expected 3 pairwise rows for 3 components, got {len(corr_df)}"


# ---------------------------------------------------------------------------
# Test 12 — bundle_aggregator: component_substitution.csv schema
# ---------------------------------------------------------------------------


def test_v1_044_component_substitution_schema() -> None:
    """component_substitution.csv must have: dropped_component, oos_sharpe_delta."""
    mod = _load_runner_module("t12")
    bundle_aggregator = getattr(mod, "bundle_aggregator")

    _ct = _IS_CUTOFF_MS + 1000

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        p0_dir = tmp_path / "baseline"
        p1_dir = tmp_path / "v1-036"
        p2_dir = tmp_path / "v1-043"
        bundle_out = tmp_path / "bundle"

        for comp_dir, pnl in ((p0_dir, 0.10), (p1_dir, 0.20), (p2_dir, 0.05)):
            _make_mock_trades_csv(
                comp_dir,
                "out_of_sample",
                [
                    {
                        "symbol": "LINKUSDT",
                        "open_time": 1000 + i * 1000,
                        "close_time": _ct + i * 1000,
                        "pnl_pct": pnl,
                    }
                    for i in range(3)
                ],
            )

        bundle_aggregator(
            component_dirs={"baseline": p0_dir, "v1-036": p1_dir, "v1-043": p2_dir},
            weights={"baseline": 0.50, "v1-036": 0.30, "v1-043": 0.20},
            is_cutoff_ms=_IS_CUTOFF_MS,
            btc_klines_path=None,
            bundle_out_dir=bundle_out,
        )

        import pandas as pd

        sub_path = bundle_out / "component_substitution.csv"
        assert sub_path.exists(), f"component_substitution.csv not found at {sub_path}"
        sub_df = pd.read_csv(sub_path)
        required_cols = {
            "dropped_component",
            "oos_sharpe_delta",
            "bundle_oos_sharpe",
            "oos_monthly_sharpe_without",
        }
        assert required_cols.issubset(set(sub_df.columns)), (
            f"component_substitution.csv missing columns. "
            f"Expected {required_cols}, got {set(sub_df.columns)}"
        )
        # One row per component dropped
        assert len(sub_df) == 3, f"Expected 3 rows (one per dropped component), got {len(sub_df)}"
        assert set(sub_df["dropped_component"].tolist()) == {"baseline", "v1-036", "v1-043"}


# ---------------------------------------------------------------------------
# Foundation regression — walk_forward embargo
# ---------------------------------------------------------------------------


def test_v1_044_walk_forward_embargo_regression() -> None:
    """walk_forward.py:113 must carry train_end_ms = test_start_ms - embargo_ms."""
    wf_path = (
        Path(__file__).parent.parent
        / "src"
        / "crypto_trade"
        / "strategies"
        / "ml"
        / "walk_forward.py"
    )
    assert wf_path.exists(), f"walk_forward.py not found at {wf_path}"
    wf_src = wf_path.read_text()

    assert "train_end_ms = test_start_ms - embargo_ms" in wf_src, (
        "WALK-FORWARD EMBARGO REGRESSION: walk_forward.py does NOT carry "
        "'train_end_ms = test_start_ms - embargo_ms'. "
        "This is the iter-v3/058 fix — DO NOT revert. "
        "The embargo prevents label-horizon leakage across train/test boundaries."
    )
    # Explicitly assert the old buggy form is NOT present
    assert "train_end_ms = test_start_ms\n" not in wf_src, (
        "WALK-FORWARD EMBARGO REGRESSION: walk_forward.py still contains "
        "'train_end_ms = test_start_ms' (the buggy form). "
        "Must be 'train_end_ms = test_start_ms - embargo_ms'."
    )
