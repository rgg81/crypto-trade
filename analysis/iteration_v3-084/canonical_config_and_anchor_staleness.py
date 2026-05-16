"""iter-v3/084 — REFERENCE-iteration EDA: /059-canonical config audit + anchor-staleness.

iter-v3/084 is a STREAMLINED REFERENCE / METHODOLOGY iteration — NOT a bold research
axis. It has exactly two purposes:

  Purpose 1 — the PER_CELL_GAP methodology fix (/083 Critic FINAL `1116124` Rec #2).
  Purpose 2 — the clean /059-config 3-symbol anchor re-run on current data.

This script is OPTIONAL per the iter-v3/084 scope. It produces NO new research evidence.
It does exactly two reference jobs, both reading ONLY committed prior-iteration artifacts
and source-code constants (no backtest, no model fit, no OOS data — sacred-constant safe):

  1. CONFIG AUDIT — emit the /059-canonical 3-symbol configuration values that the
     iter-v3/084 setup must restore (V3_MODELS, REQUIRED_GAP, the 14-feature stack,
     the 11-knob config-accretion table), and the per-cell PBO gap correction.

  2. ANCHOR-STALENESS TABLE — reproduce the /083 closeout Section-3 incumbent-drift
     decomposition (Sharpe-framing vs net_pnl%-framing), the tension iter-v3/084's
     clean run must resolve.

NO CHEATING: this script touches no OOS data, fits no model, and does not read or
modify `OOS_CUTOFF_DATE` / `training_months`. It only prints reference numbers already
recorded in BASELINE_V3.md, diary-v3/iteration_v3-082.md, and diary-v3/iteration_v3-083.md.

Run:
  export PATH="$HOME/.local/bin:$PATH"
  uv run python analysis/iteration_v3-084/canonical_config_and_anchor_staleness.py
"""

from __future__ import annotations

import csv
from pathlib import Path

OUT_DIR = Path("analysis/iteration_v3-084")

# Sacred constants — printed for the record, never mutated.
OOS_CUTOFF_DATE = "2025-03-24"
TRAINING_MONTHS = 24
TIMEOUT_CANDLES = 21  # 10080 min / 480 min at 8h — the /069/070 revert value


# ---------------------------------------------------------------------------
# Purpose 1 — /059-canonical 3-symbol config the iter-v3/084 setup must restore
# ---------------------------------------------------------------------------

# The canonical /059 3-symbol universe (BASELINE_V3.md "Code Configuration").
V3_MODELS_V059 = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
)
N_SYMBOLS_V059 = len(V3_MODELS_V059)

# REQUIRED_GAP = (timeout_candles + 1) * n_symbols — the global CPCV purge gap.
REQUIRED_GAP_V059 = (TIMEOUT_CANDLES + 1) * N_SYMBOLS_V059  # (21+1)*3 = 66
REQUIRED_GAP_083 = (TIMEOUT_CANDLES + 1) * 4  # (21+1)*4 = 88 — the /083 4-symbol value

# PER_CELL_GAP = (timeout_candles + 1) — the per-(symbol, month) single-symbol CSCV
# purge gap. It is single-symbol, so n_symbols does NOT enter (unlike REQUIRED_GAP).
PER_CELL_GAP_CORRECT = TIMEOUT_CANDLES + 1  # (21+1) = 22
PER_CELL_GAP_STALE = 43  # the runner's stale value — (42+1), iter-v3/068 timeout=42 leftover

# The 14-feature /059 anchor stack (BASELINE_V3.md "Code Configuration").
# iter-v3/084 already inherits this from the /083 setup (the funding family was
# reverted 18->14 at /083) — it is recorded here for the config audit completeness.
V3_FEATURE_COLUMNS_V059 = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
)

# The 11-knob config-accretion table (the `_canonical_v059` pre-flight). At /083 the
# first 2 rows carried the 4-symbol universe-expansion delta; iter-v3/084 reverts ALL
# 11 rows to /059-canonical 3-symbol — the universe expansion is fully unwound.
CONFIG_ACCRETION_V059 = [
    ("V3_MODELS symbols", ("BCHUSDT", "LDOUSDT", "TRXUSDT")),
    ("REQUIRED_GAP", REQUIRED_GAP_V059),  # 66 — reverts the /083 88
    ("DEFAULT_ATR_MULTIPLIERS", (2.0, 1.0)),
    ("V3_ATR_MULTIPLIERS_PER_SYMBOL", {}),
    ("zscore_threshold", 2.0),
    ("adx_threshold", 20.0),
    ("adx_threshold_per_symbol", {}),
    ("vol_scale_floor_per_symbol", {}),
    ("block_long_for", ()),
    ("block_short_for", ()),
    ("enable_per_symbol_drawdown_brake", False),
]


# ---------------------------------------------------------------------------
# Purpose 2 — anchor-staleness numbers (the Sharpe-vs-net_pnl tension)
# ---------------------------------------------------------------------------

# Incumbent IS net_pnl% across three runs (diary-v3/iteration_v3-083.md Section 3).
# The /083 decomposition was framed in net_pnl% and concluded the incumbents drifted
# ~70pp. /082 (the same 3 incumbents on the same fresh data, FIL absent) proves the
# drift is data-extent drift, NOT FIL-perturbation.
INCUMBENT_IS_NET_PNL = {
    # symbol: (/059 IS 3-sym, /082 IS 3-sym fresh data, /083 IS 4-sym fresh data)
    "BCHUSDT": (109.23, 68.65, 79.45),
    "TRXUSDT": (3.95, -1.22, -23.04),
    "LDOUSDT": (0.89, -25.09, -11.44),
}

# Monthly Sharpe framing — the GATE-RELEVANT metric (diary-v3/iteration_v3-082.md
# Section 2 + BASELINE_V3.md Headline Metrics). This is the tension iter-v3/084 resolves.
SHARPE_FRAMING = {
    # label: (IS monthly Sharpe, OOS monthly Sharpe)
    "/059 CONFIRMATION baseline (10-seed, canonical)": (1.0894, 0.5791),
    "/081 CONFIRMATION re-validation (10-seed)": (1.0894, 0.5999),
    "/082 EXPLORATION 3-seed (3 incumbents, fresh data, 18-feat)": (1.0776, 1.7872),
}


def _write_csv(name: str, header: list[str], rows: list[list]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {path}")


def main() -> None:
    print("=" * 78)
    print("iter-v3/084 REFERENCE EDA — /059-canonical config audit + anchor staleness")
    print("=" * 78)
    print(f"Sacred constants (IMMUTABLE): OOS_CUTOFF_DATE={OOS_CUTOFF_DATE}, "
          f"training_months={TRAINING_MONTHS}, timeout_candles={TIMEOUT_CANDLES}")
    print()

    # ---- Purpose 1: config audit -----------------------------------------
    print("-" * 78)
    print("PURPOSE 1 — the /059-canonical 3-symbol config the /084 setup restores")
    print("-" * 78)
    print(f"V3_MODELS (3 symbols, FILUSDT dropped): "
          f"{[s for _, s in V3_MODELS_V059]}")
    print(f"REQUIRED_GAP: {REQUIRED_GAP_083} (4-sym /083)  ->  "
          f"{REQUIRED_GAP_V059} (3-sym /059 = (21+1)*3)   [iter-v3/084 REVERTS]")
    print(f"V3_FEATURE_COLUMNS: {len(V3_FEATURE_COLUMNS_V059)} features "
          f"(/059 anchor stack — already in place since /083 funding revert)")
    print()
    print("PER_CELL_GAP methodology fix (the /084 SINGLE declared change):")
    print(f"  stale runner value     : PER_CELL_GAP = {PER_CELL_GAP_STALE}  "
          f"(= 42+1; iter-v3/068 timeout=42 leftover — REVERTED at /069/070)")
    print(f"  correct value          : PER_CELL_GAP = {PER_CELL_GAP_CORRECT}  "
          f"(= (timeout_candles+1) = (21+1); single-symbol cell, n_symbols does NOT enter)")
    print(f"  test already correct   : tests/strategies/ml/test_per_cell_pbo_synthetic.py:38 "
          f"has PER_CELL_GAP = {PER_CELL_GAP_CORRECT}  -> runner is OUT OF SYNC")
    print(f"  direction of the error : {PER_CELL_GAP_STALE} OVER-purges vs "
          f"{PER_CELL_GAP_CORRECT} -> biases per-cell PBO PESSIMISTICALLY -> "
          f"did NOT invalidate /083 (conservative)")
    print()

    _write_csv(
        "config_audit_v059_canonical.csv",
        ["knob", "v059_canonical_value", "note"],
        [
            [k, repr(v), "iter-v3/084 setup restores this 3-symbol /059 value"]
            for k, v in CONFIG_ACCRETION_V059
        ]
        + [
            ["PER_CELL_GAP", PER_CELL_GAP_CORRECT,
             f"FIX: stale {PER_CELL_GAP_STALE}->22; /084 single declared methodology change"],
            ["V3_FEATURE_COLUMNS count", len(V3_FEATURE_COLUMNS_V059),
             "14-feature /059 anchor — already in place since /083 funding revert"],
        ],
    )

    # ---- Purpose 2: anchor-staleness table -------------------------------
    print("-" * 78)
    print("PURPOSE 2 — the Sharpe-vs-net_pnl tension iter-v3/084's clean run resolves")
    print("-" * 78)
    print()
    print("(a) net_pnl% framing — the /083 decomposition (Section 3): '~70pp drift'")
    print(f"  {'symbol':<10} {'/059 IS':>10} {'/082 IS':>10} {'/083 IS':>10} "
          f"{'/082-/059 Δ':>13}")
    incumbent_059 = 0.0
    incumbent_082 = 0.0
    incumbent_083 = 0.0
    for sym, (v059, v082, v083) in INCUMBENT_IS_NET_PNL.items():
        incumbent_059 += v059
        incumbent_082 += v082
        incumbent_083 += v083
        print(f"  {sym:<10} {v059:>10.2f} {v082:>10.2f} {v083:>10.2f} "
              f"{v082 - v059:>+13.2f}")
    drift_082 = incumbent_082 - incumbent_059
    drift_083 = incumbent_083 - incumbent_059
    print(f"  {'AGGREGATE':<10} {incumbent_059:>10.2f} {incumbent_082:>10.2f} "
          f"{incumbent_083:>10.2f} {drift_082:>+13.2f}")
    print(f"  -> /082 incumbent aggregate Δ vs /059 = {drift_082:+.2f} pp "
          f"(FIL ABSENT — pure data-extent drift)")
    print(f"  -> /083 incumbent aggregate Δ vs /059 = {drift_083:+.2f} pp")
    print(f"  -> /082-vs-/083 incumbent Δ = {incumbent_083 - incumbent_082:+.2f} pp "
          f"(near-identical: FIL did NOT perturb incumbents)")
    print()
    print("(b) monthly-Sharpe framing — the GATE-RELEVANT metric: 'anchor reproduces'")
    print(f"  {'run':<52} {'IS Sh':>8} {'OOS Sh':>8}")
    for label, (is_sh, oos_sh) in SHARPE_FRAMING.items():
        print(f"  {label:<52} {is_sh:>8.4f} {oos_sh:>8.4f}")
    is_059 = SHARPE_FRAMING["/059 CONFIRMATION baseline (10-seed, canonical)"][0]
    is_082 = SHARPE_FRAMING[
        "/082 EXPLORATION 3-seed (3 incumbents, fresh data, 18-feat)"][0]
    print(f"  -> /082 IS monthly Sharpe {is_082:.4f} vs /059 {is_059:.4f}: "
          f"Δ = {is_082 - is_059:+.4f} (within ±0.10 — anchor REPRODUCES on Sharpe)")
    print()
    print("THE TENSION: net_pnl% says '~70pp incumbent drift'; monthly Sharpe says")
    print("'/082 reproduced /059 within ~0.01'. Monthly Sharpe is the gate-relevant")
    print("metric. /084's clean 3-symbol /059-config run on current data definitively")
    print("resolves it — see brief Section 4 for the pre-registered prediction + the")
    print("re-anchor decision rule.")
    print()

    _write_csv(
        "anchor_staleness_incumbent_drift.csv",
        ["symbol", "is_059", "is_082", "is_083", "drift_082_vs_059", "drift_083_vs_059"],
        [
            [sym, v059, v082, v083, round(v082 - v059, 2), round(v083 - v059, 2)]
            for sym, (v059, v082, v083) in INCUMBENT_IS_NET_PNL.items()
        ]
        + [[
            "AGGREGATE", round(incumbent_059, 2), round(incumbent_082, 2),
            round(incumbent_083, 2), round(drift_082, 2), round(drift_083, 2),
        ]],
    )
    _write_csv(
        "anchor_staleness_sharpe_framing.csv",
        ["run", "is_monthly_sharpe", "oos_monthly_sharpe"],
        [[label, is_sh, oos_sh] for label, (is_sh, oos_sh) in SHARPE_FRAMING.items()],
    )

    print("=" * 78)
    print("DONE — iter-v3/084 reference EDA. No backtest, no model fit, no OOS data.")
    print("=" * 78)


if __name__ == "__main__":
    main()
