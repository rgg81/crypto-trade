"""iter-v3/096 Phase-1 GO/NO-GO — significance adjudication of the LOSO
transfer ICs.

The headline EDA (pooled_transfer_go_nogo_eda.py) returned a BORDERLINE
result: T5 headline +0.0699 (90% of the within-symbol benchmark), 2/3
symbols transfer positively, but TRX transfer IC = -0.006 tripped the
pre-registered sign-consistency gate.

Fail-fast targets KNOWN failures, not genuinely-uncertain tests — so before
accepting a NO-GO this script adjudicates honestly:

  Q1. Is TRX's -0.006 transfer IC genuinely NEGATIVE, or noise around zero?
      -> block-bootstrap 95% CI on each held-out symbol's transfer IC.
  Q2. Is the +0.0699 headline an artifact of LDO's tiny 581-row IS sample?
      -> recompute the headline excluding LDO; report BCH+TRX-only.
  Q3. Does the within-symbol benchmark itself have a sign problem on TRX?
      -> already have within ICs; compare.

Block bootstrap (contiguous 21-bar blocks = the label horizon) preserves
the serial dependence of overlapping triple-barrier labels, so the CI is
not anti-conservative.

IS-only.  OOS_CUTOFF_MS untouched.  Reuses the labeling + load logic from
pooled_transfer_go_nogo_eda.py — imported, not duplicated.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pooled_transfer_go_nogo_eda import (
    LGB_PARAMS,
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    load_symbol_is,
    rank_ic,
)

import lightgbm as lgb

OUT = Path("analysis/iteration_v3-096")
BLOCK = 21  # contiguous-block length = the 21-bar label horizon
N_BOOT = 2000
RNG = np.random.default_rng(42)


def block_bootstrap_ic_ci(pred: np.ndarray, target: np.ndarray) -> tuple[float, float, float]:
    """Block-bootstrap 95% CI for the rank-IC of (pred, target).

    Resamples contiguous 21-bar blocks (the label horizon) to preserve the
    serial dependence of overlapping triple-barrier labels.
    """
    n = len(pred)
    if n < 60:
        return float("nan"), float("nan"), float("nan")
    n_blocks = int(np.ceil(n / BLOCK))
    starts = np.arange(0, n - BLOCK + 1)
    ics = []
    for _ in range(N_BOOT):
        chosen = RNG.choice(starts, size=n_blocks, replace=True)
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in chosen])[:n]
        ic = rank_ic(pred[idx], target[idx])
        if np.isfinite(ic):
            ics.append(ic)
    ics = np.array(ics)
    return (
        float(np.percentile(ics, 2.5)),
        float(np.median(ics)),
        float(np.percentile(ics, 97.5)),
    )


def main() -> None:
    print("=" * 78)
    print("iter-v3/096 Phase-1 — LOSO transfer-IC significance adjudication")
    print("=" * 78)

    panels: dict[str, pd.DataFrame] = {}
    for sym in SYMBOLS:
        d = load_symbol_is(sym)
        d["y"] = (d["tb_label"] == 1).astype(int)
        d = d.dropna(subset=list(V3_FEATURE_COLUMNS) + ["tb_pnl"]).reset_index(drop=True)
        panels[sym] = d

    # ---- Q1 + Q2: LOSO transfer IC with block-bootstrap CI ----
    print("\nQ1/Q2 — LOSO transfer IC + block-bootstrap 95% CI:")
    rows = []
    transfer = {}
    for held in SYMBOLS:
        train_syms = [s for s in SYMBOLS if s != held]
        train_df = pd.concat([panels[s] for s in train_syms], ignore_index=True)
        Xtr = train_df[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
        ytr = train_df["y"].to_numpy(dtype=int)
        d_held = panels[held]
        Xte = d_held[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
        tgt = d_held["tb_label"].to_numpy(dtype=np.float64)
        model = lgb.LGBMClassifier(**LGB_PARAMS)
        model.fit(Xtr, ytr)
        p = model.predict_proba(Xte)[:, 1]
        point = rank_ic(p, tgt)
        lo, med, hi = block_bootstrap_ic_ci(p, tgt)
        transfer[held] = (point, lo, hi)
        ci_excludes_zero = (lo > 0) or (hi < 0)
        rows.append(
            {
                "held_out_symbol": held,
                "transfer_ic_point": round(point, 5),
                "boot_ci_lo": round(lo, 5),
                "boot_ci_hi": round(hi, 5),
                "ci_excludes_zero": ci_excludes_zero,
                "n_held_rows": len(d_held),
            }
        )
        verdict = (
            "POSITIVE (CI > 0)"
            if lo > 0
            else "NEGATIVE (CI < 0)"
            if hi < 0
            else "INDISTINGUISHABLE FROM ZERO"
        )
        print(
            f"  hold {held:8s}: IC {point:+.5f}  95% CI [{lo:+.5f}, {hi:+.5f}]  "
            f"n={len(d_held):4d}  -> {verdict}"
        )
    sig = pd.DataFrame(rows)
    sig.to_csv(OUT / "T6_transfer_ic_significance.csv", index=False)

    # ---- Q2: headline excluding LDO's tiny sample ----
    bch_trx = [transfer["BCHUSDT"][0], transfer["TRXUSDT"][0]]
    headline_all = float(np.nanmean([transfer[s][0] for s in SYMBOLS]))
    headline_no_ldo = float(np.nanmean(bch_trx))
    print("\nQ2 — headline robustness to LDO's 581-row sample:")
    print(f"  T5 headline, all 3 symbols      : {headline_all:+.5f}")
    print(f"  headline, BCH+TRX only (no LDO)  : {headline_no_ldo:+.5f}")

    # ---- Adjudication ----
    print("\n" + "=" * 78)
    print("ADJUDICATION")
    print("=" * 78)
    trx_lo, trx_hi = transfer["TRXUSDT"][1], transfer["TRXUSDT"][2]
    trx_genuinely_neg = trx_hi < 0
    trx_zero = (trx_lo <= 0) and (trx_hi >= 0)
    bch_lo = transfer["BCHUSDT"][1]
    ldo_lo = transfer["LDOUSDT"][1]
    print(
        f"  TRX transfer IC 95% CI [{trx_lo:+.5f}, {trx_hi:+.5f}] -> "
        + (
            "genuinely NEGATIVE"
            if trx_genuinely_neg
            else "INDISTINGUISHABLE FROM ZERO"
            if trx_zero
            else "positive"
        )
    )
    print(f"  BCH transfer IC CI lower bound = {bch_lo:+.5f}")
    print(f"  LDO transfer IC CI lower bound = {ldo_lo:+.5f}")
    print(
        "  Headline excl. LDO = "
        f"{headline_no_ldo:+.5f} -> "
        + ("survives LDO removal" if headline_no_ldo >= 0.030 else "DROPS below the 0.030 GO floor")
    )
    rows2 = [
        {"q": "TRX_transfer_genuinely_negative", "answer": bool(trx_genuinely_neg)},
        {"q": "TRX_transfer_indistinguishable_from_zero", "answer": bool(trx_zero)},
        {"q": "headline_no_LDO", "answer": round(headline_no_ldo, 5)},
        {"q": "headline_no_LDO_clears_0.030", "answer": bool(headline_no_ldo >= 0.030)},
        {"q": "BCH_transfer_CI_excludes_zero", "answer": bool(transfer["BCHUSDT"][1] > 0)},
        {"q": "LDO_transfer_CI_excludes_zero", "answer": bool(transfer["LDOUSDT"][1] > 0)},
    ]
    pd.DataFrame(rows2).to_csv(OUT / "T7_adjudication.csv", index=False)
    print("=" * 78)


if __name__ == "__main__":
    main()
