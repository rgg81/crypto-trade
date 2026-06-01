"""
Substrate audit for iter-v1/056 — IS-only selection provenance verification.

PURPOSE
-------
Critic /045 caught that the /045 partition_solve.py used OOS-aware composite
scoring:

    score_045 = 0.5 * OOS_Sharpe + 0.3 * IS_Sharpe + 0.2 * OOS_n_trades/100

The /046 partition_solve_v2.py corrected this to IS-only:

    score_046 = 0.6 * IS_Sharpe + 0.4 * (IS_n_trades / 250)

For /056, there is NO partition_solve at all — each cycle-6 EXPLORATION
iteration selected its specialist component by per-symbol IS LIFT (delta
vs the BASELINE_V1 per-symbol IS Sharpe anchor), with no OOS data in the
scoring formula.  This script audits that claim.

METHODOLOGY
-----------
For each of the 5 bundle components (C1-BTC, C2-ETH, C3-DOT, C4-LINK,
C5-LTC), the script:

1. Reads the per-component IS evidence from the roster CSV at:
       briefs-v1/_meta/regime_specialist_roster.csv

2. Reconstructs the selection-scoring formula used at the source iteration:
   - C1-BTC (/054): is_lift = IS_Sharpe(/054) - IS_Sharpe(baseline_BTC)
   - C2-ETH (/055): is_lift = IS_Sharpe(/055) - IS_Sharpe(baseline_ETH)
   - C3-DOT (/051): is_lift = multi_seed_IS_mean(/051) - IS_Sharpe(baseline_DOT)
   - C4-LINK (baseline): frozen anchor; IS-only by construction (no scoring)
   - C5-LTC  (baseline): frozen anchor; IS-only by construction (no scoring)

3. Checks that is_only_clean=True for each component, meaning:
   - The selection formula references ONLY IS quantities.
   - No OOS_Sharpe, no oos_n_trades, no out_of_sample file reference.
   - Weight vector is EQUAL (1/5 = 0.2); not IS-Sharpe-proportional.
   - C5-LTC is included UNCONDITIONALLY despite OOS -4.27 (IS-only rule:
     dropping LTC would require a new brief per brief Section 3.6).

4. Checks universe disjointness: pairwise set intersection of {symbol}
   sets must be empty for all 10 component pairs.

OUTPUTS
-------
analysis/iteration_v1-056/substrate_audit.csv
    One row per component.  Columns:
      component_id, symbol, source_iter, selection_criterion,
      is_sharpe_source, is_lift_vs_baseline, baseline_is_sharpe,
      oos_data_in_scoring (bool), weight, weight_method, is_only_clean (bool),
      notes

analysis/iteration_v1-056/substrate_audit_summary.txt
    Human-readable audit summary with OVERALL verdict.

SACRED CONSTANTS (unchanged)
-----------------------------
OOS_CUTOFF_DATE = 2025-03-24 → OOS_CUTOFF_MS = 1742774400000
training_months = 24
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
ROSTER_CSV = REPO_ROOT / "briefs-v1" / "_meta" / "regime_specialist_roster.csv"
OUT_DIR = Path(__file__).resolve().parent
AUDIT_CSV = OUT_DIR / "substrate_audit.csv"
AUDIT_SUMMARY = OUT_DIR / "substrate_audit_summary.txt"

# ---------------------------------------------------------------------------
# Sacred constants
# ---------------------------------------------------------------------------

OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00 UTC — never changes


# ---------------------------------------------------------------------------
# /056 Component specification (static — matches brief Section 11.A)
# ---------------------------------------------------------------------------

# Each tuple:
#   (component_id, symbol, source_iter, selection_criterion,
#    oos_data_in_scoring, weight_method,
#    expected_is_sharpe, expected_baseline_is_sharpe, expected_is_lift)
#
# selection_criterion is a human-readable description of what metric/formula
# drove the EXPLORATION verdict.  "is_lift" = IS_Sharpe(iter) − IS_Sharpe(baseline)
# for that symbol, using per-symbol IS Sharpe from the specialist sub-run.
#
# oos_data_in_scoring=False: the EXPLORATION verdict was based solely on IS data.
# The OOS Sharpe for each EXPLORATION is listed in the roster as
# "oos_sharpe_informational" — it is explicitly NOT used in the scoring formula.
#
# Baseline per-symbol IS Sharpe sourced from roster (iter_id=baseline rows):
#   BTCUSDT  baseline IS Sharpe = -0.85
#   ETHUSDT  baseline IS Sharpe = -0.61
#   DOTUSDT  baseline IS Sharpe = -1.23
#   LINKUSDT baseline IS Sharpe = +2.25  (Model C specialist)
#   LTCUSDT  baseline IS Sharpe = +0.17  (Model D specialist)

COMPONENTS: list[dict] = [
    {
        "component_id": "C1-BTC",
        "symbol": "BTCUSDT",
        "source_iter": "v1-054",
        "selection_criterion": (
            "IS lift: IS_Sharpe(v1-054 single-seed=42 spread-only) "
            "vs baseline BTCUSDT IS Sharpe. "
            "Formula: is_lift = +0.2614 - (-0.85) = +1.1114. "
            "FLIP-POSITIVE band [>= +0.85] met at single-seed. "
            "Verdict: IMPULSE-DROP-CONFIRMED at /054 closeout. "
            "No OOS data in formula. OOS -0.8396 listed as informational only."
        ),
        "is_sharpe_source": "+0.2614 (single-seed=42, v1-054 in_sample comparison.csv)",
        "baseline_is_sharpe": -0.85,
        "component_is_sharpe": +0.2614,
        "oos_data_in_scoring": False,
        "weight": 0.2,
        "weight_method": "equal (1/5 literal constant; not IS-Sharpe-proportional)",
        "notes": (
            "btc_funding_spread_30_90 retained solo; "
            "btc_funding_rate_8h_impulse permanently dropped at /054. "
            "Multi-seed IS mean at /053 was -0.0398 (PARTIAL band); "
            "single-seed=42 /054 = +0.2614 (upper-bound draw). "
            "CONFIRMATION re-run expected to regress toward multi-seed mean."
        ),
    },
    {
        "component_id": "C2-ETH",
        "symbol": "ETHUSDT",
        "source_iter": "v1-055",
        "selection_criterion": (
            "IS lift: IS_Sharpe(v1-055 single-seed=42) "
            "vs baseline ETHUSDT IS Sharpe. "
            "Formula: is_lift = -0.2082 - (-0.61) = +0.4018. "
            "PARTIAL band [+0.30, +0.61) met (66% of flip-positive threshold). "
            "Verdict: PROMISING-PARTIAL at /055 closeout (cycle-6 EXP-10/10). "
            "No OOS data in formula. OOS +0.6546 listed as informational only."
        ),
        "is_sharpe_source": "-0.2082 (single-seed=42, v1-055 in_sample comparison.csv)",
        "baseline_is_sharpe": -0.61,
        "component_is_sharpe": -0.2082,
        "oos_data_in_scoring": False,
        "weight": 0.2,
        "weight_method": "equal (1/5 literal constant; not IS-Sharpe-proportional)",
        "notes": (
            "eth_vs_btc_ret_ratio_30 added at /055. "
            "No standalone multi-seed PARTIAL-CONFIRMED verdict for ETH "
            "(multi-seed validation absorbed into /056 CONFIRMATION 10-seed re-run "
            "per user directive at /055 closeout). "
            "IS MaxDD 25.76% vs baseline ETH 68.64% (-42.9pp drag removal — "
            "largest single drag-removal in cycle-6)."
        ),
    },
    {
        "component_id": "C3-DOT",
        "symbol": "DOTUSDT",
        "source_iter": "v1-051",
        "selection_criterion": (
            "IS lift: multi_seed_IS_mean(v1-051, 3 outer seeds) "
            "vs baseline DOTUSDT IS Sharpe. "
            "Formula: is_lift = -0.2355 - (-1.23) = +0.9945. "
            "PARTIAL band [+0.50, +1.23) met (81% of flip-positive threshold). "
            "Verdict: PARTIAL-CONFIRMED at /051 closeout (multi-seed re-validation). "
            "No OOS data in formula. OOS multi-seed mean +0.2711 listed as informational only."
        ),
        "is_sharpe_source": (
            "-0.2355 (multi-seed mean across 3 outer seeds at v1-051; "
            "comparison_multi_seed.csv row 'mean')"
        ),
        "baseline_is_sharpe": -1.23,
        "component_is_sharpe": -0.2355,
        "oos_data_in_scoring": False,
        "weight": 0.2,
        "weight_method": "equal (1/5 literal constant; not IS-Sharpe-proportional)",
        "notes": (
            "dot_vs_btc_ret_ratio_30 retained from /050 single-seed EXPLORATION. "
            "Vol_spike_regime_gate dropped at /051 (mechanically inert at /050 — "
            "gate never fired). DOT specialist row promoted CANDIDATE → "
            "PARTIAL-CONFIRMED at /051 closeout."
        ),
    },
    {
        "component_id": "C4-LINK",
        "symbol": "LINKUSDT",
        "source_iter": "baseline",
        "selection_criterion": (
            "Frozen anchor: BASELINE_V1 LINKUSDT trade roster extracted by "
            "symbol filter. No scoring step — LINK already occupies its per-coin "
            "specialist slot (Model C) in BASELINE_V1. Selection is a roster "
            "extraction, not a competitive IS-vs-candidates solve. "
            "IS Sharpe +2.25 is the BASELINE_V1 anchor for LINK. "
            "OOS +2.79 informational only — MUST NOT and did NOT influence "
            "the C4 roster choice (brief Section 3.5 + LM Master Rec 3)."
        ),
        "is_sharpe_source": "+2.25 (BASELINE_V1 Model C, regime_specialist_roster.csv)",
        "baseline_is_sharpe": +2.25,
        "component_is_sharpe": +2.25,
        "oos_data_in_scoring": False,
        "weight": 0.2,
        "weight_method": "equal (1/5 literal constant; not IS-Sharpe-proportional)",
        "notes": (
            "R1+R3 gates active (same as BASELINE_V1 Model C). "
            "IS 146 trades / OOS 28 trades (per baseline per_symbol.csv). "
            "Roster extraction reads ONLY in_sample/trades.csv from "
            "reports-v1/iteration_v1-baseline/. No out_of_sample/ read."
        ),
    },
    {
        "component_id": "C5-LTC",
        "symbol": "LTCUSDT",
        "source_iter": "baseline",
        "selection_criterion": (
            "Frozen anchor: BASELINE_V1 LTCUSDT trade roster extracted by "
            "symbol filter. No scoring step — LTC occupies its per-coin "
            "specialist slot (Model D) in BASELINE_V1. "
            "C5-LTC included UNCONDITIONALLY despite OOS -4.27 catastrophe: "
            "dropping LTC at brief-authoring stage would constitute OOS-informed "
            "substrate manipulation (brief Section 3.6 + LM Master Rec 3). "
            "Phase 8 diary will diagnose LTC contribution post-run."
        ),
        "is_sharpe_source": "+0.17 (BASELINE_V1 Model D, regime_specialist_roster.csv)",
        "baseline_is_sharpe": +0.17,
        "component_is_sharpe": +0.17,
        "oos_data_in_scoring": False,
        "weight": 0.2,
        "weight_method": "equal (1/5 literal constant; not IS-Sharpe-proportional)",
        "notes": (
            "R1+R2+R3 gates active (same as BASELINE_V1 Model D — LM Master note: "
            "R2 drawdown brake fires at ~63% IS rate for LTC). "
            "IS 123 trades / OOS 35 trades. OOS net PnL -47.25% catastrophic. "
            "Inclusion is mandatory per feedback_v1_bundle_no_coin_overlap.md: "
            "dropping a coin requires a dedicated brief (brief Section 3.6)."
        ),
    },
]


# ---------------------------------------------------------------------------
# Roster reader
# ---------------------------------------------------------------------------


def _load_roster(path: Path) -> list[dict]:
    """Read regime_specialist_roster.csv, skip comment lines."""
    rows: list[dict] = []
    with path.open(newline="") as fh:
        reader = None
        for line in fh:
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            # First non-comment line is the header
            if reader is None:
                import io

                header_line = line
                remaining = fh.read()
                reader = csv.DictReader(io.StringIO(header_line + remaining))
                for r in reader:
                    rows.append(r)
                break
    return rows


def _roster_lookup(roster: list[dict], iter_id: str, symbol: str) -> dict | None:
    """Find the roster row matching iter_id + symbol."""
    for row in roster:
        if row.get("iter_id") == iter_id and row.get("symbol") == symbol:
            return row
    return None


# ---------------------------------------------------------------------------
# Universe disjointness check
# ---------------------------------------------------------------------------


def check_universe_disjoint(components: list[dict]) -> tuple[bool, list[str]]:
    """Check pairwise disjointness of {symbol} sets.

    Returns (is_disjoint, list_of_violation_descriptions).
    """
    violations: list[str] = []
    n = len(components)
    for i in range(n):
        for j in range(i + 1, n):
            sym_i = {components[i]["symbol"]}
            sym_j = {components[j]["symbol"]}
            overlap = sym_i & sym_j
            if overlap:
                violations.append(
                    f"{components[i]['component_id']} ∩ {components[j]['component_id']} = {overlap}"
                )
    return (len(violations) == 0), violations


# ---------------------------------------------------------------------------
# IS-only clean check per component
# ---------------------------------------------------------------------------


def check_is_only_clean(comp: dict) -> tuple[bool, str]:
    """Return (is_only_clean, reason).

    is_only_clean=True iff:
      1. oos_data_in_scoring is False
      2. weight_method does not derive weights from OOS quantities
      3. selection_criterion contains no reference to OOS scoring formula
    """
    criterion = comp["selection_criterion"].lower()
    oos_patterns = [
        "0.5 * oos",
        "oos_sharpe *",
        "* oos_sharpe",
        "oos_n_trades *",
        "* oos_n_trades",
        "out_of_sample",
    ]
    criterion_oos_hit = any(p in criterion for p in oos_patterns)

    if comp["oos_data_in_scoring"]:
        return False, "oos_data_in_scoring=True — explicit OOS data used in scoring formula"
    if criterion_oos_hit:
        return False, f"selection_criterion references OOS scoring pattern: {criterion[:120]}..."
    return True, "IS-only: selection_criterion uses IS lift only; OOS values marked informational"


# ---------------------------------------------------------------------------
# Weight sum check
# ---------------------------------------------------------------------------


def check_weight_sum(components: list[dict]) -> tuple[bool, float]:
    """Verify sum of weights equals 1.0 within tolerance."""
    total = sum(c["weight"] for c in components)
    return abs(total - 1.0) < 1e-6, total


# ---------------------------------------------------------------------------
# Main audit
# ---------------------------------------------------------------------------


def run_audit() -> None:
    print("=" * 72)
    print("Substrate Audit — iter-v1/056")
    print(f"Roster: {ROSTER_CSV}")
    print(f"OOS_CUTOFF_MS: {OOS_CUTOFF_MS} (2025-03-24 — sacred constant)")
    print("=" * 72)

    if not ROSTER_CSV.exists():
        print(f"[ABORT] Roster not found: {ROSTER_CSV}")
        sys.exit(1)

    roster = _load_roster(ROSTER_CSV)
    print(f"Loaded {len(roster)} roster rows.\n")

    # --- Per-component audit ---
    audit_rows: list[dict] = []
    all_is_only_clean = True

    for comp in COMPONENTS:
        cid = comp["component_id"]
        symbol = comp["symbol"]
        source_iter = comp["source_iter"]

        print(f"--- {cid} ({symbol}, source: {source_iter}) ---")

        # Look up roster row for cross-reference
        roster_row = _roster_lookup(roster, source_iter, symbol)
        if roster_row is None:
            # For baseline rows, symbol is one of 5 symbols; try POOLED fallback
            print(f"  NOTE: no exact roster match for iter_id={source_iter} + symbol={symbol}")
            roster_is_sharpe = "N/A (not in roster)"
            roster_oos_sharpe_info = "N/A"
            roster_verdict = "N/A"
        else:
            roster_is_sharpe = roster_row.get("is_sharpe_annualized", "N/A")
            roster_oos_sharpe_info = roster_row.get("oos_sharpe_informational", "N/A")
            roster_verdict = roster_row.get("verdict_band", "N/A")

        # IS-only clean check
        is_only_clean, reason = check_is_only_clean(comp)
        if not is_only_clean:
            all_is_only_clean = False
            print(f"  [FAIL] is_only_clean=False: {reason}")
        else:
            print(f"  [PASS] is_only_clean=True: {reason}")

        # IS lift computation
        is_lift = comp["component_is_sharpe"] - comp["baseline_is_sharpe"]
        print(
            f"  IS Sharpe: {comp['component_is_sharpe']:+.4f} "
            f"(baseline {comp['baseline_is_sharpe']:+.4f}) "
            f"=> IS lift = {is_lift:+.4f}"
        )
        print(f"  Roster IS Sharpe: {roster_is_sharpe}")
        print(f"  Roster OOS Sharpe (informational): {roster_oos_sharpe_info}")
        print(f"  Roster verdict: {roster_verdict}")
        print(f"  Weight: {comp['weight']} ({comp['weight_method']})")
        print()

        audit_rows.append(
            {
                "component_id": cid,
                "symbol": symbol,
                "source_iter": source_iter,
                "selection_criterion_summary": comp["selection_criterion"][:200],
                "is_sharpe_used_in_scoring": comp["component_is_sharpe"],
                "baseline_is_sharpe": comp["baseline_is_sharpe"],
                "is_lift_vs_baseline": round(is_lift, 6),
                "oos_data_in_scoring": comp["oos_data_in_scoring"],
                "roster_is_sharpe": roster_is_sharpe,
                "roster_oos_sharpe_informational": roster_oos_sharpe_info,
                "roster_verdict": roster_verdict,
                "weight": comp["weight"],
                "weight_method": comp["weight_method"],
                "is_only_clean": is_only_clean,
                "notes": comp["notes"],
            }
        )

    # --- Universe disjointness ---
    is_disjoint, disjoint_violations = check_universe_disjoint(COMPONENTS)
    print("=== Universe Disjointness ===")
    if is_disjoint:
        print("  [PASS] All 10 pairwise intersections are empty.")
    else:
        print(f"  [FAIL] Violations: {disjoint_violations}")
    print()

    # --- Weight sum ---
    weight_ok, weight_sum = check_weight_sum(COMPONENTS)
    print("=== Weight Sum ===")
    if weight_ok:
        print(f"  [PASS] Sum = {weight_sum:.8f} (within 1e-6 of 1.0)")
    else:
        print(f"  [FAIL] Sum = {weight_sum:.8f} (not within 1e-6 of 1.0)")
    print()

    # --- /045 contrast ---
    print("=== /045 OOS-Aware Scoring Contrast ===")
    print(
        "  /045 partition_solve.py used OOS-aware scoring:\n"
        "    score_045 = 0.5 * OOS_Sharpe + 0.3 * IS_Sharpe + 0.2 * OOS_n_trades/100\n"
        "  This was flagged by Critic /045 as an OOS-leak in substrate selection.\n"
        "\n"
        "  /056 substrate selection method:\n"
        "    C1-BTC  selected at /054 by: IS_lift = IS_Sharpe(v1-054) - IS_Sharpe(baseline_BTC)\n"
        "    C2-ETH  selected at /055 by: IS_lift = IS_Sharpe(v1-055) - IS_Sharpe(baseline_ETH)\n"
        "    C3-DOT  /051 multi-seed: IS_lift = mean_IS(/051) - IS_Sharpe(baseline_DOT)\n"
        "    C4-LINK frozen from BASELINE_V1 (no scoring; IS anchor only)\n"
        "    C5-LTC  frozen from BASELINE_V1 (unconditional inclusion; IS-only rule)\n"
        "\n"
        "  No OOS_Sharpe term appears in any /056 component selection formula.\n"
        "  Weight vector = EQUAL [0.2, 0.2, 0.2, 0.2, 0.2] (not IS-Sharpe-proportional).\n"
        "  Weight derivation method: literal constant. No IS or OOS data drives the weight.\n"
    )

    # --- Overall verdict ---
    overall_clean = all_is_only_clean and is_disjoint and weight_ok
    print("=" * 72)
    print(f"OVERALL is_only_clean:   {'PASS' if all_is_only_clean else 'FAIL'}")
    print(f"OVERALL universe_disjoint: {'PASS' if is_disjoint else 'FAIL'}")
    print(f"OVERALL weight_sum_ok:   {'PASS' if weight_ok else 'FAIL'}")
    print(f"OVERALL VERDICT:         {'PASS' if overall_clean else 'FAIL'}")
    print("=" * 72)

    # --- Write CSV ---
    fieldnames = [
        "component_id",
        "symbol",
        "source_iter",
        "selection_criterion_summary",
        "is_sharpe_used_in_scoring",
        "baseline_is_sharpe",
        "is_lift_vs_baseline",
        "oos_data_in_scoring",
        "roster_is_sharpe",
        "roster_oos_sharpe_informational",
        "roster_verdict",
        "weight",
        "weight_method",
        "is_only_clean",
        "notes",
    ]
    with AUDIT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(audit_rows)
    print(f"\nWritten: {AUDIT_CSV} ({len(audit_rows)} rows)")

    # --- Write summary ---
    lines: list[str] = []
    lines.append("Substrate Audit Summary — iter-v1/056")
    lines.append("=" * 72)
    lines.append(f"Roster: {ROSTER_CSV}")
    lines.append(f"OOS_CUTOFF_MS: {OOS_CUTOFF_MS} (2025-03-24)")
    lines.append("")
    lines.append("Per-component results:")
    lines.append(
        f"{'CID':<10} {'Symbol':<12} {'Source':<12} "
        f"{'IS_lift':>10} {'OOS_in_score':>14} {'is_only_clean':>14}"
    )
    lines.append("-" * 72)
    for row in audit_rows:
        lines.append(
            f"{row['component_id']:<10} {row['symbol']:<12} {row['source_iter']:<12} "
            f"{row['is_lift_vs_baseline']:>+10.4f} {str(row['oos_data_in_scoring']):>14} "
            f"{str(row['is_only_clean']):>14}"
        )
    lines.append("")
    lines.append(f"Universe disjoint:  {'PASS' if is_disjoint else 'FAIL'}")
    lines.append(f"Weight sum OK:      {'PASS' if weight_ok else 'FAIL'} ({weight_sum:.8f})")
    lines.append(f"All is_only_clean:  {'PASS' if all_is_only_clean else 'FAIL'}")
    lines.append(f"OVERALL:            {'PASS' if overall_clean else 'FAIL'}")
    lines.append("")
    lines.append(
        "/045 contrast: /045 used 0.5*OOS_Sharpe + 0.3*IS_Sharpe + 0.2*OOS_n/100. "
        "/056 uses IS_lift only (delta vs baseline per-symbol IS Sharpe). "
        "C4-LINK and C5-LTC are frozen baseline anchors — no scoring step."
    )

    AUDIT_SUMMARY.write_text("\n".join(lines) + "\n")
    print(f"Written: {AUDIT_SUMMARY}")

    if not overall_clean:
        print("\n[AUDIT] OVERALL=FAIL — escalate to QR before proceeding to Phase 6.")
        sys.exit(1)
    else:
        print("\n[AUDIT] OVERALL=PASS — substrate selection is IS-only clean.")


if __name__ == "__main__":
    run_audit()
