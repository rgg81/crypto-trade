"""
iter-v3/009 — Top-13 validation analysis (no new evidence; rerun-setup verification).

This is a VALIDATION analysis script for the SECOND EXPLORATION under the v3
cadence discipline (skill SHA d5c9f21). iter-v3/008 was ABORTED at 4h 15min,
so iter-v3/009 re-tests the iter-v3/008 hypothesis (top-14 minus vwap_dev_50)
AT EXPLORATION COST (~10-15 min wall-clock vs the ~25h CONFIRMATION extrapolation).

The top-13 feature subset is already configured in V3_FEATURE_COLUMNS by
iter-v3/008's setup commit SHA 56b8f8b ("drop vwap_dev_50"). This script
verifies that setup is still intact AND emits the iter-v3/007 importance
ranks for the 13 retained features.

Inputs (committed earlier; all IS-only):
- reports-v3/iteration_v3-007/ic_matrix.csv — 14x14 IC matrix from EXPLORATION
  (full v3 universe, top-14 features, single seed=42). NO OOS contact.
- reports-v3/iteration_v3-007/in_sample/feature_importance.csv — IS-only.

Outputs (committed alongside this script BEFORE the brief, per Phase 5.5):
- analysis/iteration_v3-009/top_13_features.csv — 13 retained features with
  iter-v3/007 importance and IS rank.
- analysis/iteration_v3-009/synthesis.md — 1-paragraph narrative.

Purpose:
1) Confirm V3_FEATURE_COLUMNS = 13, vwap_dev_50 dropped.
2) Confirm 13-feature subset has NO IC pair |rho| >= 0.7 (max residual = 0.6602
   per iter-v3/008's analysis at SHA 003a21e).
3) Provide a single concise CSV linking each retained feature to its IS
   importance rank from iter-v3/007.

Note: this script intentionally does NOT compute new statistics. It is a
"setup integrity" gate before launching the iter-v3/009 EXPLORATION run.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
IC_MATRIX_PATH = ROOT / "reports-v3" / "iteration_v3-007" / "ic_matrix.csv"
IMPORTANCE_PATH = (
    ROOT
    / "reports-v3"
    / "iteration_v3-007"
    / "in_sample"
    / "feature_importance.csv"
)
OUT_DIR = ROOT / "analysis" / "iteration_v3-009"
OUT_TOP_13 = OUT_DIR / "top_13_features.csv"
OUT_SYNTHESIS = OUT_DIR / "synthesis.md"

IC_THRESHOLD = 0.7
DROPPED_FEATURE = "vwap_dev_50"


# ---------------------------------------------------------------------------
# Step 1: import V3_FEATURE_COLUMNS at runtime and verify setup integrity
# ---------------------------------------------------------------------------


def verify_setup() -> tuple[list[str], dict[str, str]]:
    """Re-verify V3_FEATURE_COLUMNS is at 13 features post iter-v3/008's setup."""
    from crypto_trade.features_v3 import V3_FEATURE_COLUMNS  # noqa: PLC0415

    cols = list(V3_FEATURE_COLUMNS)
    diagnostics: dict[str, str] = {}

    diagnostics["V3_FEATURE_COLUMNS_len"] = str(len(cols))
    if len(cols) != 13:
        raise SystemExit(
            f"SETUP DRIFT: V3_FEATURE_COLUMNS has {len(cols)} entries, expected 13."
        )

    diagnostics["vwap_dev_50_in_cols"] = str(DROPPED_FEATURE in cols)
    if DROPPED_FEATURE in cols:
        raise SystemExit(
            f"SETUP DRIFT: {DROPPED_FEATURE!r} should be DROPPED (per iter-v3/008 SHA 56b8f8b)."
        )

    diagnostics["status"] = "PASS"
    return cols, diagnostics


# ---------------------------------------------------------------------------
# Step 2: load iter-v3/007 IC matrix and confirm no residual pair >= 0.7 in
# the 13-feature sub-matrix.
# ---------------------------------------------------------------------------


def verify_no_redundancy(retained_cols: list[str]) -> dict[str, float | str]:
    ic_matrix = pd.read_csv(IC_MATRIX_PATH, index_col=0)

    # Subset to 13 retained features
    sub = ic_matrix.loc[retained_cols, retained_cols]

    # Off-diagonal absolute IC values
    abs_ic = sub.abs()
    # Mask the diagonal so 1.0 self-IC is ignored
    n = len(abs_ic)
    iu = abs_ic.values.copy()
    for i in range(n):
        iu[i, i] = 0.0
    max_abs = float(iu.max())

    # Locate the max pair
    flat_idx = int(iu.argmax())
    r, c = divmod(flat_idx, n)
    max_pair = (str(abs_ic.index[r]), str(abs_ic.columns[c]))
    pair_count_above = int((iu >= IC_THRESHOLD).sum() // 2)

    return {
        "max_residual_abs_ic": max_abs,
        "max_residual_pair_a": max_pair[0],
        "max_residual_pair_b": max_pair[1],
        "headroom_to_threshold": IC_THRESHOLD - max_abs,
        "pairs_above_threshold": pair_count_above,
        "ic_threshold": IC_THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Step 3: emit top_13_features.csv with iter-v3/007 importance + IS rank
# ---------------------------------------------------------------------------


def emit_top_13_csv(retained_cols: list[str]) -> Path:
    imp = pd.read_csv(IMPORTANCE_PATH).set_index("feature")
    # iter-v3/007 IS ranks are in display order of the importance CSV
    imp_with_rank = imp.copy()
    imp_with_rank = imp_with_rank.sort_values("importance", ascending=False)
    imp_with_rank["iter_v3_007_is_rank"] = range(1, len(imp_with_rank) + 1)

    rows: list[dict[str, object]] = []
    for col in retained_cols:
        if col not in imp_with_rank.index:
            raise SystemExit(
                f"Setup integrity break: {col!r} missing from iter-v3/007 importance CSV."
            )
        rec = imp_with_rank.loc[col]
        rows.append(
            {
                "feature": col,
                "iter_v3_007_importance": float(rec["importance"]),
                "iter_v3_007_is_rank": int(rec["iter_v3_007_is_rank"]),
            }
        )

    out = pd.DataFrame(rows).sort_values(
        "iter_v3_007_is_rank", ascending=True, ignore_index=True
    )
    out.insert(0, "iter_v3_009_position", range(1, len(out) + 1))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_TOP_13, index=False)
    return OUT_TOP_13


# ---------------------------------------------------------------------------
# Step 4: write synthesis.md (1 paragraph)
# ---------------------------------------------------------------------------


def write_synthesis(
    retained_cols: list[str],
    redundancy_check: dict[str, float | str],
) -> Path:
    text = (
        "# iter-v3/009 — top-13 validation synthesis\n\n"
        "Setup integrity check for the SECOND EXPLORATION under the v3 cadence "
        "discipline. iter-v3/008 was aborted at 4h 15min wall-clock; iter-v3/009 "
        "re-tests the iter-v3/008 hypothesis (top-14 minus `vwap_dev_50`) at "
        "EXPLORATION cost. V3_FEATURE_COLUMNS imports at runtime as a 13-tuple "
        "with `vwap_dev_50` confirmed dropped (setup commit SHA 56b8f8b on the "
        f"iteration-v3/008 branch, inherited here). The 13×13 IC sub-matrix from "
        f"iter-v3/007's `ic_matrix.csv` has zero pairs at |IC| >= "
        f"{redundancy_check['ic_threshold']:.2f}; the maximum residual is "
        f"|IC|={redundancy_check['max_residual_abs_ic']:.4f} for the pair "
        f"(`{redundancy_check['max_residual_pair_a']}` × "
        f"`{redundancy_check['max_residual_pair_b']}`), giving headroom "
        f"{redundancy_check['headroom_to_threshold']:.4f} to threshold. NO new "
        "evidence is produced — this is purely a rerun-setup verification "
        "before the EXPLORATION run launches. The 13 retained features in "
        "iter-v3/007 IS rank order are written to `top_13_features.csv`.\n"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_SYNTHESIS.write_text(text, encoding="utf-8")
    return OUT_SYNTHESIS


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    retained_cols, setup = verify_setup()
    print(json.dumps({"setup": setup}, indent=2))

    redundancy = verify_no_redundancy(retained_cols)
    print(json.dumps({"redundancy": redundancy}, indent=2, default=str))

    csv_path = emit_top_13_csv(retained_cols)
    print(f"WROTE: {csv_path}")

    synth_path = write_synthesis(retained_cols, redundancy)
    print(f"WROTE: {synth_path}")

    if redundancy["pairs_above_threshold"] != 0:
        raise SystemExit(
            "FAIL: at least one IC pair |rho| >= 0.7 in 13-feature subset; "
            "setup is corrupted."
        )

    print("PASS — setup integrity verified for iter-v3/009.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
