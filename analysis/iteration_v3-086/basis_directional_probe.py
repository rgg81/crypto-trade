"""iter-v3/086 EDA PART 2 — basis directional / interaction probe (IS-only).

PART 1 (basis_feed_eda.py) found the 3-feature basis family has WEAK univariate
IC (all |IC| <= 0.051) and a NEGATIVE incremental-information delta on all 3
symbols.  The basis feed is technically viable (full IS history, clean past-only
construction, 100% spot-merge coverage) but the off-the-shelf direct basis
features do not carry edge.

The crypto-native literature (AEA 2026 "Perpetual Futures and Basis Risk";
the funding-crowding-reversal literature) says the basis predicts MEAN REVERSION
AT EXTREMES, not trend — a crowded positive basis is a fade setup.  PART 2 tests
whether a basis-conditioned construction recovers structure the direct features
miss.  Per `feedback_v3_engineered_feature_pivot.md`, the one PROVEN-PROMISING v3
axis is Category-2 composed features (regime_momentum_signed_5d, iter-v3/025).
PART 2 probes the analogous basis construction:

    basis_regime_momentum  =  regime_momentum_signed_5d  ×  -sign(basis_z[t-1])

— momentum FADED when the basis is in a crowded-positive regime.  The hypothesis:
momentum into a crowded (positive-basis) long is exhaustion; the sign-flip encodes
the fade.  This is the basis analogue of /085's funding-regime feature (which was
INERT/SUSPICIOUS — but funding settles on an 8h lag while the basis reprices
continuously, so the basis carries a DIFFERENT, faster crowding signal).

It ALSO probes:
  - extreme-bucket conditional WR: does the label WR differ at |basis_z| > 1.5?
  - basis_z reversal IC: Spearman of basis_z[t-1] vs the FORWARD raw return (not
    the triple-barrier label) — does a high basis predict a negative next return?

NO CHEATING: IS data only; OOS never loaded; no parameter swept on any metric.
The fade construction (-sign) is fixed a-priori by the crowding-reversal
hypothesis, NOT chosen by comparing +sign vs -sign on a metric.

Run:  uv run python analysis/iteration_v3-086/basis_directional_probe.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OOS_CUTOFF_MS = int(pd.Timestamp("2025-03-24", tz="UTC").timestamp() * 1000)
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
OUT_DIR = Path("analysis/iteration_v3-086")

# reuse the verified PART-1 builders
import sys

sys.path.insert(0, str(OUT_DIR))
from basis_feed_eda import (  # noqa: E402
    _anchor_features,
    compute_basis_features,
    triple_barrier_label,
)


def main() -> None:
    print("=" * 72)
    print("iter-v3/086 EDA PART 2 — basis directional / interaction probe (IS)")
    print("=" * 72)

    # --- P1: basis_z[t-1] vs FORWARD 1-bar / 3-bar raw return ----------------
    p1_rows = []
    for sym in SYMBOLS:
        perp = pd.read_csv(f"data/{sym}/8h.csv").sort_values("open_time").reset_index(drop=True)
        spot = pd.read_csv(f"data/spot/{sym}/8h.csv").sort_values("open_time").reset_index(drop=True)
        bf = compute_basis_features(perp, spot)
        close = perp["close"].to_numpy(float)
        logc = np.log(close)
        fwd1 = np.concatenate([np.diff(logc), [np.nan]])           # ret t -> t+1
        fwd3 = np.concatenate([logc[3:] - logc[:-3], [np.nan] * 3])  # ret t -> t+3
        z = bf["basis_zscore_30"].to_numpy(float)
        is_mask = (bf["open_time"] < OOS_CUTOFF_MS).to_numpy()
        for horizon, fwd in (("fwd_ret_1bar", fwd1), ("fwd_ret_3bar", fwd3)):
            m = is_mask & np.isfinite(z) & np.isfinite(fwd)
            ic, _ = spearmanr(z[m], fwd[m])
            p1_rows.append({"symbol": sym, "horizon": horizon, "n": int(m.sum()),
                            "basis_z_vs_fwdret_ic": round(float(ic), 4)})
    p1 = pd.DataFrame(p1_rows)
    print("\n--- P1: basis_z[t-1] -> forward raw return Spearman IC ---")
    print("(reversal hypothesis: a crowded-high basis -> negative fwd ret -> IC < 0)")
    print(p1.to_string(index=False))
    p1.to_csv(OUT_DIR / "p1_basis_reversal_ic.csv", index=False)

    # --- P2: extreme-bucket conditional label WR -----------------------------
    p2_rows = []
    for sym in SYMBOLS:
        perp = pd.read_csv(f"data/{sym}/8h.csv").sort_values("open_time").reset_index(drop=True)
        spot = pd.read_csv(f"data/spot/{sym}/8h.csv").sort_values("open_time").reset_index(drop=True)
        bf = compute_basis_features(perp, spot)
        label = triple_barrier_label(perp)
        z = bf["basis_zscore_30"].to_numpy(float)
        is_mask = (bf["open_time"] < OOS_CUTOFF_MS).to_numpy()
        base = is_mask & np.isfinite(z) & np.isfinite(label)
        # label is +1 (long-favoured) / -1; "long-rate" = share of +1
        for tag, sel in (
            ("all_IS", base),
            ("basis_z > +1.5 (crowded long)", base & (z > 1.5)),
            ("basis_z < -1.5 (crowded short)", base & (z < -1.5)),
            ("|basis_z| <= 0.5 (neutral)", base & (np.abs(z) <= 0.5)),
        ):
            n = int(sel.sum())
            long_rate = float((label[sel] == 1).mean()) if n else np.nan
            p2_rows.append({"symbol": sym, "bucket": tag, "n": n,
                            "long_label_rate": round(long_rate, 4) if n else np.nan})
    p2 = pd.DataFrame(p2_rows)
    print("\n--- P2: triple-barrier long-label rate by basis-z extreme bucket ---")
    print(p2.to_string(index=False))
    p2.to_csv(OUT_DIR / "p2_extreme_bucket_wr.csv", index=False)

    # --- P3: basis_regime_momentum composed feature --------------------------
    # = regime_momentum_signed_5d × -sign(basis_z[t-1])  (momentum FADED in
    #   a crowded-positive-basis regime).  IC vs label + orthogonality vs the
    #   raw primitive + incremental info.
    p3_rows = []
    for sym in SYMBOLS:
        perp = pd.read_csv(f"data/{sym}/8h.csv").sort_values("open_time").reset_index(drop=True)
        spot = pd.read_csv(f"data/spot/{sym}/8h.csv").sort_values("open_time").reset_index(drop=True)
        bf = compute_basis_features(perp, spot)
        adf = _anchor_features(sym)
        label = triple_barrier_label(perp)
        merged = bf.merge(adf, on="open_time", how="inner").assign(_label=label)
        rm = merged["regime_momentum_signed_5d"].to_numpy(float)
        bz = merged["basis_zscore_30"].to_numpy(float)
        composed = rm * (-np.sign(bz))
        lab = merged["_label"].to_numpy(float)
        is_mask = (merged["open_time"] < OOS_CUTOFF_MS).to_numpy()
        m = is_mask & np.isfinite(composed) & np.isfinite(lab)
        ic_lab, _ = spearmanr(composed[m], lab[m]) if m.sum() > 50 else (np.nan, 0)
        mr = is_mask & np.isfinite(composed) & np.isfinite(rm)
        ic_prim = np.corrcoef(composed[mr], rm[mr])[0, 1] if mr.sum() > 50 else np.nan
        rm_ic, _ = spearmanr(rm[m], lab[m]) if m.sum() > 50 else (np.nan, 0)
        p3_rows.append({
            "symbol": sym, "n": int(m.sum()),
            "composed_vs_label_ic": round(float(ic_lab), 4),
            "raw_regime_mom_vs_label_ic": round(float(rm_ic), 4),
            "composed_vs_primitive_ic": round(float(ic_prim), 4),
        })
    p3 = pd.DataFrame(p3_rows)
    print("\n--- P3: basis_regime_momentum = regime_momentum_signed_5d × -sign(basis_z) ---")
    print(p3.to_string(index=False))
    p3.to_csv(OUT_DIR / "p3_basis_regime_momentum.csv", index=False)

    print("\n" + "=" * 72)
    print("PART-2 CSVs written to analysis/iteration_v3-086/")
    print("=" * 72)


if __name__ == "__main__":
    main()
