"""iter-v3/074 — regression tests for the regime-gate axis + /073 ATR revert.

CYCLE 2 EXPLORATION #4. Two surfaces change at /074 setup:

  1. V3_ATR_MULTIPLIERS_PER_SYMBOL is REVERTED to {} — the /073 per-symbol
     triple-barrier asymmetry axis (BCH (2.0,1.25), LDO (1.5,1.25)) was
     SUSPICIOUS-OOS-DOMINANT (OOS/IS ratio 6.85; a holding-time-extension axis)
     and was CLOSED at catalog level. Per `feedback_no_cheating.md` anti-drift
     discipline /074 reverts it; all symbols use DEFAULT_ATR_MULTIPLIERS (2.0, 1.0).

  2. enable_regime_gate is flipped True — the regime-conditional kill switch
     (primitive 9) is the /074 cycle-2 EXPLORATION #4 axis. It is holding-time-
     ORTHOGONAL (a binary kill switch removing whole TRX trades on BTC-regime-
     stress bars; surviving trades unchanged).

The deep past-only / fire-condition coverage of the regime gate lives in
tests/strategies/ml/test_regime_gate.py (the /022 lineage). This file pins the
/074 SETUP state: the ATR revert holds and the regime gate is the active axis.
"""

from __future__ import annotations

from crypto_trade.features_v3 import (
    DEFAULT_ATR_MULTIPLIERS,
    V3_ATR_MULTIPLIERS_PER_SYMBOL,
    atr_multipliers_for_symbol,
)
from crypto_trade.strategies.ml.risk_v2 import RiskV2Config


# ---------------------------------------------------------------------------
# Surface 1 — V3_ATR_MULTIPLIERS_PER_SYMBOL revert (/073 axis closed)
# ---------------------------------------------------------------------------
def test_per_symbol_atr_dict_is_empty() -> None:
    """iter-v3/074 REVERT: V3_ATR_MULTIPLIERS_PER_SYMBOL must be empty {}.

    The /073 per-symbol axis was SUSPICIOUS-OOS-DOMINANT and closed; /074 reverts
    the dict so no symbol carries a per-symbol multiplier override.
    """
    assert V3_ATR_MULTIPLIERS_PER_SYMBOL == {}


def test_default_atr_multipliers_unchanged() -> None:
    """DEFAULT_ATR_MULTIPLIERS must be the canonical /059 baseline pair (2.0, 1.0)."""
    assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)


def test_all_v3_symbols_use_one_global_pair() -> None:
    """All three v3 symbols (BCH/LDO/TRX) resolve to the SAME global pair (2.0, 1.0).

    With V3_ATR_MULTIPLIERS_PER_SYMBOL empty, the labeling layer is symbol-
    homogeneous — no per-symbol barrier customization. The /074 axis (regime gate)
    is the only varied surface.
    """
    pairs = {atr_multipliers_for_symbol(s) for s in ("BCHUSDT", "LDOUSDT", "TRXUSDT")}
    assert pairs == {(2.0, 1.0)}


def test_unknown_symbol_falls_back_to_default() -> None:
    """Any symbol not in the dict resolves to DEFAULT_ATR_MULTIPLIERS."""
    assert atr_multipliers_for_symbol("NOTASYMBOLUSDT") == DEFAULT_ATR_MULTIPLIERS


# ---------------------------------------------------------------------------
# Surface 2 — regime-conditional kill switch is the /074 axis
# ---------------------------------------------------------------------------
def test_regime_gate_default_is_off() -> None:
    """A bare RiskV2Config must keep the regime gate OFF — /074 enables it
    explicitly in _build_v3_model, NOT via a changed default. This guards the
    v1/v2/v3-prior backward-compat contract."""
    cfg = RiskV2Config()
    assert cfg.enable_regime_gate is False


def test_regime_gate_thresholds_are_is_calibrated() -> None:
    """The regime-gate thresholds must be the IS-calibrated values. /074 does NOT
    re-tune them (re-tuning would be a second axis)."""
    cfg = RiskV2Config()
    # IS-90th percentile of BTC drawdown_30d; IS-95th percentile of vol_zscore_30d.
    assert cfg.regime_dd_threshold_pct == 20.0
    assert cfg.regime_vol_zscore_threshold == 1.5


def test_regime_gate_can_be_enabled_for_trx_only() -> None:
    """The /074 axis configuration: enable_regime_gate=True, regime_gate_symbols
    targeting TRX only. BCH/LDO must NOT be in the gate's symbol list (they are
    the positive controls — their rosters must stay /060-byte-identical)."""
    cfg = RiskV2Config(
        enable_regime_gate=True,
        regime_gate_symbols=("TRXUSDT",),
    )
    assert cfg.enable_regime_gate is True
    assert cfg.regime_gate_symbols == ("TRXUSDT",)
    assert "BCHUSDT" not in cfg.regime_gate_symbols
    assert "LDOUSDT" not in cfg.regime_gate_symbols
