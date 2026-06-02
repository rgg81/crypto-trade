"""Tests for iter-v1/064 — ETHUSDT SPECIALIST (second SPECIALIST under SPECIALIST+BUNDLE).

Covers:
- test_v1_064_cohort_is_eth_only: V1_ITER064_UNIVERSE == ("ETHUSDT",)
- test_v1_064_dispatch_branch_sets_specialist_mode_true: run_baseline_v1 dispatch branch
  for "v1-064" wires specialist_mode=True to LightGbmStrategy.
- test_v1_064_inherits_specialist_constants: V1_SPECIALIST_SEED_COUNT=50,
  V1_SPECIALIST_OPTUNA_TRIALS=30 (UNCHANGED from /063).
- test_v1_064_risk_config_matches_baseline_eth: atr_tp=2.9, atr_sl=1.45 (Model A ETH cell);
  R1=OFF, R2=OFF (no risk_consecutive_sl_limit, no risk_drawdown_scale_enabled).

Brief reference: iter-v1/064 — ETH SPECIALIST, second under SPECIALIST+BUNDLE methodology.
Commit tag: bef9dba (dispersion diagnostic), 913000c (specialist_mode), ca2a079 (/063 template).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# test_v1_064_cohort_is_eth_only
# ---------------------------------------------------------------------------


def test_v1_064_cohort_is_eth_only() -> None:
    """V1_ITER064_UNIVERSE must be ('ETHUSDT',) — ETH-only single-coin SPECIALIST."""
    from crypto_trade.features_v1 import V1_ITER064_UNIVERSE

    assert V1_ITER064_UNIVERSE == ("ETHUSDT",), (
        f"V1_ITER064_UNIVERSE={V1_ITER064_UNIVERSE!r}; expected ('ETHUSDT',). "
        "iter-v1/064 is ETHUSDT-only per brief Section 3.1."
    )
    assert len(V1_ITER064_UNIVERSE) == 1, (
        f"V1_ITER064_UNIVERSE should have exactly 1 symbol, got {len(V1_ITER064_UNIVERSE)}."
    )
    assert "ETHUSDT" in V1_ITER064_UNIVERSE, "ETHUSDT must be in V1_ITER064_UNIVERSE."
    # Isolation: ETH universe must NOT overlap with DOT (/063) universe.
    from crypto_trade.features_v1 import V1_ITER063_UNIVERSE

    assert set(V1_ITER064_UNIVERSE).isdisjoint(set(V1_ITER063_UNIVERSE)), (
        f"V1_ITER064_UNIVERSE {V1_ITER064_UNIVERSE} must be disjoint from "
        f"V1_ITER063_UNIVERSE {V1_ITER063_UNIVERSE} (per-cohort isolation)."
    )


# ---------------------------------------------------------------------------
# test_v1_064_dispatch_branch_sets_specialist_mode_true
# ---------------------------------------------------------------------------


def test_v1_064_dispatch_branch_sets_specialist_mode_true() -> None:
    """run_baseline_v1 dispatch branch for 'v1-064' wires specialist_mode=True.

    The branch condition is: `iteration_label == "v1-064" and set(symbols) == {"ETHUSDT"}`.
    We verify by inspecting the source code that the branch block contains
    `specialist_mode=True` — this is a structural code-path test, not a full execution.
    """
    import inspect

    import run_baseline_v1

    source = inspect.getsource(run_baseline_v1)

    # The dispatch branch key must be present.
    assert '"v1-064"' in source, 'run_baseline_v1 does not contain dispatch branch for "v1-064".'

    # Locate the v1-064 block and verify it contains specialist_mode=True.
    # We find the block between "v1-064" and the next "elif iteration_label".
    start_idx = source.find('"v1-064"')
    assert start_idx != -1, 'Could not find "v1-064" in run_baseline_v1 source.'

    # The next elif / else after the v1-064 block.
    end_idx = source.find("elif iteration_label", start_idx + 1)
    if end_idx == -1:
        end_idx = len(source)

    block_064 = source[start_idx:end_idx]

    # Strip comment lines (start with optional whitespace then '#') for structural checks.
    # This prevents false-positive matches on documentation comments that describe
    # parameters that are intentionally absent (e.g. "# R1=OFF: no risk_consecutive_sl_limit").
    code_lines_064 = "\n".join(
        line for line in block_064.splitlines() if not line.lstrip().startswith("#")
    )

    assert "specialist_mode=True" in code_lines_064, (
        "Dispatch branch for 'v1-064' must contain `specialist_mode=True`. "
        f"Code-only block excerpt (first 500 chars):\n{code_lines_064[:500]}"
    )

    # R1=OFF: the block must NOT contain risk_consecutive_sl_limit in code (R1 parameter).
    assert "risk_consecutive_sl_limit" not in code_lines_064, (
        "Dispatch branch for 'v1-064' must NOT contain `risk_consecutive_sl_limit` in code "
        "(R1 is OFF for Model A ETH baseline; only DOT /063 block has R1=ON). "
        f"Code-only block excerpt (first 800 chars):\n{code_lines_064[:800]}"
    )

    # R2=OFF: the block must NOT contain risk_drawdown_scale_enabled in code.
    assert "risk_drawdown_scale_enabled" not in code_lines_064, (
        "Dispatch branch for 'v1-064' must NOT contain `risk_drawdown_scale_enabled` in code "
        "(R2 is OFF for Model A ETH baseline). "
        f"Code-only block excerpt (first 800 chars):\n{code_lines_064[:800]}"
    )

    # R3=ON: the block must contain ood_enabled=True.
    assert "ood_enabled=True" in code_lines_064, (
        "Dispatch branch for 'v1-064' must contain `ood_enabled=True` (R3 ON-SHARED). "
        f"Code-only block excerpt (first 800 chars):\n{code_lines_064[:800]}"
    )

    # Cohort guard present in block (full block including comments is fine here).
    assert '"ETHUSDT"' in block_064 or "'ETHUSDT'" in block_064, (
        "Dispatch branch for 'v1-064' must reference ETHUSDT (cohort guard). "
        f"Block excerpt (first 500 chars):\n{block_064[:500]}"
    )


# ---------------------------------------------------------------------------
# test_v1_064_inherits_specialist_constants
# ---------------------------------------------------------------------------


def test_v1_064_inherits_specialist_constants() -> None:
    """V1_SPECIALIST_SEED_COUNT=50 and V1_SPECIALIST_OPTUNA_TRIALS=30 — UNCHANGED from /063."""
    from crypto_trade.strategies.ml.lgbm import (
        V1_SPECIALIST_OPTUNA_TRIALS,
        V1_SPECIALIST_SEED_COUNT,
        V1_SPECIALIST_SEEDS,
    )

    assert V1_SPECIALIST_SEED_COUNT == 50, (
        f"V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}; expected 50. "
        "Specialist constants must be UNCHANGED at iter-v1/064 (brief Section 3.2)."
    )
    assert V1_SPECIALIST_OPTUNA_TRIALS == 30, (
        f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}; expected 30. "
        "Specialist constants must be UNCHANGED at iter-v1/064 (brief Section 3.2)."
    )
    assert len(V1_SPECIALIST_SEEDS) == 50, (
        f"V1_SPECIALIST_SEEDS length={len(V1_SPECIALIST_SEEDS)}; expected 50."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"V1_SPECIALIST_SEEDS[0]={V1_SPECIALIST_SEEDS[0]}; expected 42."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"V1_SPECIALIST_SEEDS[-1]={V1_SPECIALIST_SEEDS[-1]}; expected 91."
    )
    # Seed roster is IDENTICAL to /063 (methodology generalization; same sampler config).
    expected_seeds = tuple(range(42, 92))
    assert V1_SPECIALIST_SEEDS == expected_seeds, (
        f"V1_SPECIALIST_SEEDS must be tuple(range(42, 92)); "
        f"got {V1_SPECIALIST_SEEDS[:3]}...{V1_SPECIALIST_SEEDS[-3:]}."
    )


# ---------------------------------------------------------------------------
# test_v1_064_risk_config_matches_baseline_eth
# ---------------------------------------------------------------------------


def test_v1_064_risk_config_matches_baseline_eth() -> None:
    """Dispatch branch for 'v1-064' uses Model A ETH risk config: atr_tp=2.9, atr_sl=1.45.

    Key differences from /063 DOT (Model E):
        /063: atr_tp=3.5, atr_sl=1.75, R1=ON K=3/C=27, R2=ON trigger=7%/anchor=15%/floor=0.33
        /064: atr_tp=2.9, atr_sl=1.45, R1=OFF, R2=OFF

    Both match their respective BASELINE_V1 cells (the "match-to-baseline" mandate).
    """
    import inspect

    import run_baseline_v1

    source = inspect.getsource(run_baseline_v1)

    start_idx = source.find('"v1-064"')
    assert start_idx != -1, 'Could not find "v1-064" in run_baseline_v1 source.'

    end_idx = source.find("elif iteration_label", start_idx + 1)
    if end_idx == -1:
        end_idx = len(source)

    block_064 = source[start_idx:end_idx]

    # atr_tp=2.9 (Model A ETH cell)
    assert "atr_tp_multiplier=2.9" in block_064, (
        "Dispatch branch for 'v1-064' must use `atr_tp_multiplier=2.9` (Model A ETH cell). "
        "This differs from /063's 3.5 (Model E DOT cell). "
        f"Block excerpt (first 1000 chars):\n{block_064[:1000]}"
    )

    # atr_sl=1.45 (Model A ETH cell)
    assert "atr_sl_multiplier=1.45" in block_064, (
        "Dispatch branch for 'v1-064' must use `atr_sl_multiplier=1.45` (Model A ETH cell). "
        "This differs from /063's 1.75 (Model E DOT cell). "
        f"Block excerpt (first 1000 chars):\n{block_064[:1000]}"
    )

    # R3 ON: ood_cutoff_pct=0.70 (inherited from Model A baseline)
    assert "ood_cutoff_pct=0.70" in block_064, (
        "Dispatch branch for 'v1-064' must have `ood_cutoff_pct=0.70` (R3 ON-SHARED). "
        f"Block excerpt (first 1000 chars):\n{block_064[:1000]}"
    )

    # R5 ON: vol-targeting enabled (same as /063)
    assert "vol_targeting=True" in block_064, (
        "Dispatch branch for 'v1-064' must have `vol_targeting=True` (R5 ON). "
        f"Block excerpt (first 1000 chars):\n{block_064[:1000]}"
    )

    # Verify specialist_n_startup_trials=10 and specialist_n_estimators_max=500
    assert "specialist_n_startup_trials=10" in block_064, (
        "Dispatch branch for 'v1-064' must have `specialist_n_startup_trials=10`. "
        f"Block excerpt (first 1000 chars):\n{block_064[:1000]}"
    )
    assert "specialist_n_estimators_max=500" in block_064, (
        "Dispatch branch for 'v1-064' must have `specialist_n_estimators_max=500`. "
        f"Block excerpt (first 1000 chars):\n{block_064[:1000]}"
    )
