"""iter-v3/090 — B2 downside-risk per-feature selection EDA (IS-ONLY).

The companion to gross_signal_expansion_eda.py.  That EDA established (IS-only):
  - the cross-sectional signal is short-leg-asymmetric (A3: bottom-half
    within-IC 0.0576 vs top-half 0.0141 — 4.1x sharper at the loser end);
  - of the candidate families, B2 DOWNSIDE-RISK gives the largest incremental
    multivariate contribution (d composite IC-IR +0.0306, d quintile L-S
    spread Sharpe +0.0215 vs the 13-feature anchor) — and it targets exactly
    the short leg the asymmetry shows carries the alpha.

But B2 added FOUR features at once.  The iter-v3/070 dead-path discipline and
`feedback_v3_engineered_features_dont_stack.md` warn that stacking many
marginally-correlated features dilutes `colsample_bytree` picks.  This EDA
isolates WHICH B2 features carry the incremental contribution, so /090 adds the
MINIMAL effective subset (1-2 features), not all four.  Two IS-only tests:

  C1  GREEDY FORWARD SELECTION inside B2 — start from the 13-feature anchor;
      at each step add the single B2 feature that most raises the composite
      IC-IR; stop when the next addition's marginal d(IC-IR) <= +0.005 (a
      meaningful-contribution floor).  This yields the minimal B2 subset.

  C2  LEAVE-ONE-OUT REDUNDANCY CHECK — for each B2 feature SELECTED by C1,
      drop it from the {anchor + selected} composite and measure the IC-IR
      loss.  A feature whose removal barely changes the composite (loss <
      +0.005) is redundant with the rest of the stack — the iter-v3/070
      colsample-dilution risk — and is dropped.  This is the multivariate
      (not univariate) confirmation each kept feature earns its slot.

  C3  PAIRWISE REDUNDANCY of the C1-selected features against the existing
      anchor volatility/tail features (range_realized_vol_50, ret_skew_50,
      ret_skew_200, ret_kurt_50, ret_kurt_200, max_dd_window_50) — the
      cross-sectional rank correlation; reported so the brief can show the
      kept features are not near-duplicates of an incumbent.

NO-CHEATING: every table is computed on IS rows ONLY (open_time <
OOS_CUTOFF_MS = 2025-03-24, 180-bar burn-in).  The forward-return target is the
H=3 cross-sectional forward return.  The selection is made on the IS composite
IC-IR; OOS is never read.  Outputs are CSVs.

Run: uv run python analysis/iteration_v3-090/b2_feature_selection_eda.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "src"))

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE

from crypto_trade.strategies.ml.cross_sectional import XS_UNIVERSE  # noqa: E402

# reuse the candidate-engineering + composite helpers from the main /090 EDA.
sys.path.insert(0, str(OUT))
from gross_signal_expansion_eda import (  # noqa: E402
    ANCHOR_13,
    BURNIN_BARS,
    CANDIDATE_FAMILIES,
    MIN_XS,
    H,
    _composite_ic_series,
    _engineer_candidates,
    _load_is,
    _per_feature_is_ic,
)

B2_FEATS = CANDIDATE_FAMILIES["B2_downside_risk"]
# the anchor volatility / tail features the C3 redundancy check compares against.
ANCHOR_VOLTAIL = [
    "range_realized_vol_50",
    "ret_skew_50",
    "ret_skew_200",
    "ret_kurt_50",
    "ret_kurt_200",
    "max_dd_window_50",
]
MARGINAL_FLOOR = 0.005  # d(IC-IR) below this = not a meaningful contribution


def _ic_ir(panels: dict, all_ts: list, feats: list[str], sign: dict[str, float]) -> float:
    arr, _ = _composite_ic_series(panels, all_ts, feats, sign)
    if len(arr) < 2 or arr.std(ddof=1) <= 0:
        return 0.0
    return float(arr.mean() / arr.std(ddof=1))


def main() -> None:
    print("=" * 78)
    print("iter-v3/090 — B2 downside-risk per-feature selection EDA — IS-ONLY")
    print(f"IS cutoff: open_time < {OOS_CUTOFF_MS}; burn-in {BURNIN_BARS} bars; H={H}")
    print("=" * 78)

    panels: dict[str, pd.DataFrame] = {}
    for sym in XS_UNIVERSE:
        df = _load_is(sym)
        if df is None or len(df) < 250:
            continue
        df = _engineer_candidates(df)
        df["fwd_H"] = df["close"].astype(float).shift(-H) / df["close"].astype(float) - 1.0
        panels[sym] = df.set_index("open_time")
    all_ts = sorted(set().union(*[set(p.index) for p in panels.values()]))
    print(f"\nLoaded {len(panels)} IS panels, {len(all_ts)} timestamps.\n")

    # sign alignment (IS rank-IC) for the anchor + B2 features.
    feats_for_sign = ANCHOR_13 + B2_FEATS + ANCHOR_VOLTAIL
    feats_for_sign = list(dict.fromkeys(feats_for_sign))  # dedup, keep order
    feat_ic = _per_feature_is_ic(panels, all_ts, feats_for_sign)
    sign = {f: (1.0 if feat_ic[f] >= 0 else -1.0) for f in feats_for_sign}

    anchor_ir = _ic_ir(panels, all_ts, ANCHOR_13, sign)
    print(f"ANCHOR-13 composite IC-IR: {anchor_ir:+.4f}\n")

    # =====================================================================
    # C1 — greedy forward selection inside B2
    # =====================================================================
    print("=" * 78)
    print("C1 — GREEDY FORWARD SELECTION inside B2 (stop when marginal d IC-IR <= "
          f"{MARGINAL_FLOOR})")
    print("=" * 78)
    selected: list[str] = []
    remaining = list(B2_FEATS)
    current_ir = anchor_ir
    c1_rows = []
    step = 0
    while remaining:
        step += 1
        best_feat, best_ir = None, current_ir
        for f in remaining:
            ir = _ic_ir(panels, all_ts, ANCHOR_13 + selected + [f], sign)
            if ir > best_ir:
                best_ir, best_feat = ir, f
        if best_feat is None:
            print(f"  step {step}: no candidate raises IC-IR — STOP.")
            break
        marginal = best_ir - current_ir
        c1_rows.append(
            {
                "step": step,
                "feature_added": best_feat,
                "composite_ic_ir": round(best_ir, 4),
                "marginal_delta_ic_ir": round(marginal, 4),
                "accepted": marginal > MARGINAL_FLOOR,
            }
        )
        print(
            f"  step {step}: best = {best_feat:24s} IC-IR {best_ir:+.4f} "
            f"(marginal {marginal:+.4f}) -> "
            f"{'ACCEPT' if marginal > MARGINAL_FLOOR else 'REJECT (below floor) STOP'}"
        )
        if marginal <= MARGINAL_FLOOR:
            break
        selected.append(best_feat)
        remaining.remove(best_feat)
        current_ir = best_ir
    pd.DataFrame(c1_rows).to_csv(OUT / "C1_greedy_forward_selection.csv", index=False)
    print(f"\n  C1 SELECTED B2 subset: {selected or '(none)'}")
    print(f"  composite IC-IR with selected subset: {current_ir:+.4f} "
          f"(anchor {anchor_ir:+.4f}, lift {current_ir - anchor_ir:+.4f})\n")

    # =====================================================================
    # C2 — leave-one-out redundancy check on the C1-selected features
    # =====================================================================
    print("=" * 78)
    print("C2 — LEAVE-ONE-OUT redundancy check on the C1-selected features")
    print("=" * 78)
    full = ANCHOR_13 + selected
    full_ir = _ic_ir(panels, all_ts, full, sign)
    c2_rows = []
    for f in selected:
        loo = [x for x in full if x != f]
        loo_ir = _ic_ir(panels, all_ts, loo, sign)
        loss = full_ir - loo_ir
        c2_rows.append(
            {
                "feature_dropped": f,
                "ic_ir_with": round(full_ir, 4),
                "ic_ir_without": round(loo_ir, 4),
                "ic_ir_loss_on_removal": round(loss, 4),
                "earns_its_slot": loss > MARGINAL_FLOOR,
            }
        )
        print(
            f"  drop {f:24s}: IC-IR {full_ir:+.4f} -> {loo_ir:+.4f} "
            f"(loss {loss:+.4f}) -> "
            f"{'KEEP' if loss > MARGINAL_FLOOR else 'REDUNDANT — drop'}"
        )
    pd.DataFrame(c2_rows).to_csv(OUT / "C2_leave_one_out.csv", index=False)
    final = [r["feature_dropped"] for r in c2_rows if r["earns_its_slot"]]
    print(f"\n  C2 FINAL /090 feature additions: {final or '(none)'}")
    final_ir = _ic_ir(panels, all_ts, ANCHOR_13 + final, sign)
    print(
        f"  composite IC-IR with the final {len(final)}-feature addition: "
        f"{final_ir:+.4f} (anchor {anchor_ir:+.4f}, lift {final_ir - anchor_ir:+.4f})\n"
    )

    # =====================================================================
    # C3 — pairwise redundancy of the kept features vs anchor vol/tail feats
    # =====================================================================
    print("=" * 78)
    print("C3 — PAIRWISE cross-sectional rank correlation: kept B2 features vs")
    print("     the anchor volatility/tail features")
    print("=" * 78)
    # build a long table of (timestamp, symbol, feature) cross-sectional ranks,
    # then correlate the per-timestamp rank vectors.
    keep = final if final else selected
    c3_rows = []
    for kf in keep:
        for af in ANCHOR_VOLTAIL:
            corrs = []
            for ts in all_ts:
                kv, av = [], []
                for _sym, p in panels.items():
                    if ts not in p.index:
                        continue
                    r = p.loc[ts]
                    if kf in p.columns and af in p.columns and pd.notna(r[kf]) and pd.notna(r[af]):
                        kv.append(float(r[kf]))
                        av.append(float(r[af]))
                if len(kv) < MIN_XS:
                    continue
                c = pd.Series(kv).rank().corr(pd.Series(av).rank())
                if pd.notna(c):
                    corrs.append(c)
            c3_rows.append(
                {
                    "kept_feature": kf,
                    "anchor_feature": af,
                    "mean_xs_rank_corr": round(float(np.mean(corrs)), 4) if corrs else 0.0,
                }
            )
    c3 = pd.DataFrame(c3_rows)
    c3.to_csv(OUT / "C3_pairwise_redundancy.csv", index=False)
    print(c3.to_string(index=False))
    if not c3.empty:
        mx = c3.loc[c3["mean_xs_rank_corr"].abs().idxmax()]
        print(
            f"\n  max |cross-sectional rank corr| of any kept-vs-anchor pair: "
            f"{mx['mean_xs_rank_corr']} ({mx['kept_feature']} vs {mx['anchor_feature']})"
        )

    print("\n" + "=" * 78)
    print("EDA SUMMARY — /090 B2 feature selection, IS data only")
    print("=" * 78)
    print(f"  C1 greedy-selected B2 subset: {selected or '(none)'}")
    print(f"  C2 final additions after leave-one-out: {final or '(none)'}")
    print(
        f"  composite IC-IR: anchor {anchor_ir:+.4f} -> final {final_ir:+.4f} "
        f"(lift {final_ir - anchor_ir:+.4f})"
    )
    if not c3.empty:
        print(
            f"  C3 max kept-vs-anchor |xs rank corr|: "
            f"{c3['mean_xs_rank_corr'].abs().max():.4f}"
        )
    print("  ALL tables IS-only. Selection on IS composite IC-IR; OOS unread.")
    print("=" * 78)


if __name__ == "__main__":
    sys.exit(main())
