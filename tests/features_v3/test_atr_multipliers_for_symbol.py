"""Adversarial tests for per-symbol ATR multipliers — iter-v3/043.

iter-v3/043 state (EXPLORATION — cycle 3 #4 — REVERT ATR + ADD efficiency_ratio_50):
  - DEFAULT_ATR_MULTIPLIERS REVERTED from (1.5, 0.75) → (2.0, 1.0) at iter-v3/043.
    iter-v3/042 IS collapse NEGATIVE mandate fires (IS Sharpe -0.5941; TRX OOS -33).
  - V3_ATR_MULTIPLIERS_PER_SYMBOL is EMPTY (unchanged from iter-v3/040).
  - ALL symbols (BCH/LDO/TRX/ALGO) fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
  - Architecture (dict + helper) KEPT; only DEFAULT reverted.
  - Single-axis change: efficiency_ratio_50 addition is the new variation.
    ATR revert (1.5, 0.75) → (2.0, 1.0) is the mandatory pre-commit per
    iter-v3/042 IS-collapse mandate.

iter-v3/032 EDA context (preserved for reference):
  LDOUSDT natr_21_raw median 5.01 vs peer median 3.70 (1.35× higher).
  At (2.0, 1.0) multipliers: LDO TP barrier = 10.01%, SL = 5.01%.
  iter-v3/042 EXPLORATION: (1.5, 0.75) universally caused IS collapse and TRX
  OOS -33 swing — universal barrier tightening FALSIFIED. Per-symbol LDO variant
  (iter-v3/032) remains a possible future axis but requires re-evaluation.

Validates:
  1. DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) (REVERTED from (1.5, 0.75) at iter-v3/043).
  2. All symbols fall back to (2.0, 1.0) (V3_ATR_MULTIPLIERS_PER_SYMBOL is empty).
  3. LDOUSDT returns (2.0, 1.0) — via DEFAULT (NOT via per-symbol entry).
  4. BCHUSDT returns (2.0, 1.0) — via DEFAULT (reverted from (1.5, 0.75)).
  5. V3_ATR_MULTIPLIERS_PER_SYMBOL is empty (0 entries).
  6. The runner's _build_v3_model dispatches (2.0, 1.0) for all symbols.
"""

from __future__ import annotations


def test_atr_multipliers_default():
    """DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0) at iter-v3/043.

    iter-v3/043: DEFAULT REVERTED from (1.5, 0.75) to (2.0, 1.0).
    iter-v3/042 IS collapse NEGATIVE mandate fires (IS Sharpe -0.5941; TRX OOS -33).
    V3_ATR_MULTIPLIERS_PER_SYMBOL is empty — all symbols use DEFAULT via fallback.
    """
    from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS, atr_multipliers_for_symbol

    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0), (
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/043: DEFAULT REVERTED from (1.5, 0.75) to (2.0, 1.0). "
        "Verify in features_v3/__init__.py."
    )
    assert atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.0)
    assert atr_multipliers_for_symbol("UNKNOWN_SYMBOL") == (2.0, 1.0)
    # LDO also returns (2.0, 1.0) via DEFAULT at iter-v3/043.
    # At iter-v3/032, LDO had (1.5, 0.75) via per-symbol entry.
    # At iter-v3/042, LDO returned (1.5, 0.75) via DEFAULT (old default).
    # At iter-v3/043, LDO returns (2.0, 1.0) via DEFAULT (REVERTED default).
    assert atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0), (
        "LDOUSDT must return (2.0, 1.0) at iter-v3/043 (DEFAULT_ATR_MULTIPLIERS reverted). "
        "iter-v3/043: DEFAULT REVERTED from (1.5, 0.75) to (2.0, 1.0). "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL is empty — LDO uses DEFAULT fallback."
    )


def test_atr_multipliers_ldo_universal_tighter():
    """LDO must return (2.0, 1.0) — via REVERTED DEFAULT — at iter-v3/043.

    iter-v3/042: LDO returned (1.5, 0.75) via DEFAULT (tighter).
    iter-v3/043: DEFAULT REVERTED to (2.0, 1.0); LDO still uses DEFAULT fallback.
    V3_ATR_MULTIPLIERS_PER_SYMBOL is empty — LDO has no per-symbol entry.
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL, atr_multipliers_for_symbol

    assert "LDOUSDT" not in V3_ATR_MULTIPLIERS_PER_SYMBOL, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has 'LDOUSDT' key — must be ABSENT at iter-v3/043. "
        f"LDO must use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) fallback (no per-symbol entry). "
        f"Current keys: {list(V3_ATR_MULTIPLIERS_PER_SYMBOL.keys())}."
    )
    ldo_result = atr_multipliers_for_symbol("LDOUSDT")
    assert ldo_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('LDOUSDT') returned {ldo_result} — expected (2.0, 1.0). "
        f"iter-v3/043: DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0); LDO uses DEFAULT fallback."
    )


def test_atr_multipliers_bch_universal_tighter():
    """BCH must return (2.0, 1.0) via REVERTED DEFAULT at iter-v3/043.

    BCH has no per-symbol ATR entry (V3_ATR_MULTIPLIERS_PER_SYMBOL is empty).
    DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) at iter-v3/043 (REVERTED from (1.5, 0.75)).
    """
    from crypto_trade.features_v3 import atr_multipliers_for_symbol

    bch_result = atr_multipliers_for_symbol("BCHUSDT")
    assert bch_result == (2.0, 1.0), (
        f"atr_multipliers_for_symbol('BCHUSDT') returned {bch_result} — expected (2.0, 1.0). "
        f"iter-v3/043: DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0); BCH uses DEFAULT fallback."
    )


def test_v3_atr_multipliers_per_symbol_is_empty():
    """V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty (0 entries) at iter-v3/043.

    iter-v3/040: cycle 3 EXPLORATION #1 — REVERT all per-symbol ATR customizations.
    iter-v3/041/042/043: dict remains empty. DEFAULT reverted at iter-v3/043 only.
    All symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    """
    from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL

    assert len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0, (
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty at iter-v3/043. "
        f"Got {len(V3_ATR_MULTIPLIERS_PER_SYMBOL)} entries: {dict(V3_ATR_MULTIPLIERS_PER_SYMBOL)}. "
        f"Clear V3_ATR_MULTIPLIERS_PER_SYMBOL to {{}} in features_v3/__init__.py."
    )


def test_atr_multipliers_runner_dispatch():
    """The runner's _build_v3_model uses atr_multipliers_for_symbol() and
    applies (2.0, 1.0) for ALL symbols at iter-v3/043 (REVERTED DEFAULT)."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from run_baseline_v3 import _build_v3_model

    _cfg_bch, strat_bch = _build_v3_model(
        symbol="BCHUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    _cfg_ldo, strat_ldo = _build_v3_model(
        symbol="LDOUSDT", seed=42, n_trials=1, ensemble_seeds=[42]
    )
    # iter-v3/043: ALL symbols use REVERTED DEFAULT (2.0, 1.0).
    # The strategy is RiskV3Wrapper(LightGbmStrategy); inner strategy is
    # accessible via .inner (RiskV2Wrapper stores it as self.inner).
    assert strat_bch.inner.atr_tp_multiplier == 2.0, (
        f"BCH atr_tp_multiplier: expected 2.0, got {strat_bch.inner.atr_tp_multiplier}. "
        "iter-v3/043: BCH uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)."
    )
    assert strat_bch.inner.atr_sl_multiplier == 1.0, (
        f"BCH atr_sl_multiplier: expected 1.0, got {strat_bch.inner.atr_sl_multiplier}. "
        "iter-v3/043: BCH uses DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)."
    )
    assert strat_ldo.inner.atr_tp_multiplier == 2.0, (
        f"LDO atr_tp_multiplier: expected 2.0, got {strat_ldo.inner.atr_tp_multiplier}. "
        "iter-v3/043: LDO uses DEFAULT (2.0, 1.0) via empty per-symbol dict."
    )
    assert strat_ldo.inner.atr_sl_multiplier == 1.0, (
        f"LDO atr_sl_multiplier: expected 1.0, got {strat_ldo.inner.atr_sl_multiplier}. "
        "iter-v3/043: LDO uses DEFAULT (2.0, 1.0) via empty per-symbol dict."
    )
