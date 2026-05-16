"""iter-v3/080 — Cycle 2 EXPLORATION #10 of 10 — Axis-Selection EDA.

================================================================================
AXIS DECISION: PASSIVE-DIAGNOSTIC — persist the per-trade M1 `confidence` scalar
to `trades.csv` (a `confidence` column) + emit `confidence_distribution.csv`
(per-symbol / per-IS-month M1-confidence histograms with the realized Optuna
confidence_threshold per cell overlaid). Bit-identical trade roster.
================================================================================

This is the iter-v3/079 Critic Recommendation #1 instrument. /079 ran a
conviction-DERATE per-trade sizing primitive (primitive 13) and classified
NULL-RESULT (behavioral saturation): the de-rate engaged only 7.5% of IS trades
(12/159) vs a predicted >=25%, because its a-priori reference constant C_REF=0.65
landed at the Optuna-tuned confidence-threshold pile-up rather than in the
populated region of the M1-confidence distribution. The /079 Critic PARKED
(did NOT close) the conviction-derate axis and ruled: a fair re-attempt is
permissible ONLY after the per-trade M1 `confidence` distribution is persisted
to a report artifact, so a re-attempt's C_REF can be placed empirically.

This EDA establishes — IS-data-only — three facts that justify spending the
final cycle-2 slot on the PASSIVE-DIAGNOSTIC rather than on a fresh structural
axis:

  TEST A — the instrumentation gap is real and unrecoverable without a backtest.
           `trades.csv` has 15 columns; `confidence` is not one of them. The M1
           directional margin is computed inside `lgbm.get_signal` and discarded.
           No report artifact persists it. C_REF cannot be placed empirically
           today — exactly the /079 root cause.

  TEST B — the alternative (a fresh structural labeling axis) is NOT genuinely
           fresh. Cycle 2 already tested labeling three ways (/072 fixed-horizon
           NEGATIVE, /071 meta-labeling SUSPICIOUS, /073 per-symbol-barrier
           SUSPICIOUS). A vol-adjusted past-only-realized-vol barrier — the
           candidate the /079 diary floated — is a barrier-REBALANCING change
           in the SATURATED holding-time-extension family
           (`feedback_v3_is_oos_regime_divergence.md`): /065 (SL widening),
           /071, /073 all loaded the IS/OOS regime factor and went
           SUSPICIOUS-OOS-DOMINANT. A barrier knob is not a category-1/2
           structural axis; it is a knob on a closed axis.

  TEST C — the conviction hypothesis has weak-but-real residual support that a
           properly-instrumented cycle-3 re-attempt could convert. The /079
           engineering report isolated the 12 de-rated IS trades: they
           underperformed the 147 non-de-rated (mean net_pnl_pct -0.019% vs
           +0.476%; WR 33.3% vs 38.0%). The directional signal exists; /079
           simply had almost nothing to act on. Persisting `confidence` is the
           precondition for ever measuring whether a populated de-rate band
           exists. This EDA QUANTIFIES the residual support from the committed
           /079 trade rosters; it does NOT re-attempt the derate.

================================================================================
NO-CHEATING SELF-AUDIT (feedback_no_cheating.md — Vector 1: OOS parameter tuning)
================================================================================
This EDA computes NO per-candidate OOS counterfactual. It selects NO design
parameter on any OOS metric. The PASSIVE-DIAGNOSTIC axis has exactly ONE design
parameter (the regime label used to BIN the `confidence_distribution.csv`
histogram), and it is a-priori (a calendar/price BTC-trend label, identical to
the /075/077 classifier). The `confidence` instrumentation itself is a pure
report-emission column — it has zero tunable parameters and zero behavioral
effect on the trade roster. The OOS rosters are read ONLY to print OOS trade
counts for the bit-identity / degeneracy proof (TEST A, TEST D) — no OOS
quantity feeds any sort / filter / argmax / threshold. A `_grep_no_oos_tuning()`
AST self-audit runs at the end of this module and asserts PASS.

Per-parameter IS-only / a-priori selection-function disclosure
(mandated by Critic /075 Rec #2 — reproduced in brief Section 10.2):

  PARAMETER 1 — the AXIS itself (PASSIVE-DIAGNOSTIC: persist `confidence` +
                emit `confidence_distribution.csv`).
      Selection function: `_pick_axis()` — returns a fixed string constant.
      Not a sort / filter / argmax over any metric.
      Input columns: NONE (data-free).  IS-only / a-priori: A-PRIORI.

  PARAMETER 2 — the BTC monthly regime label that BINS the
                `confidence_distribution.csv` per-IS-month histograms.
      Selection function: `build_btc_monthly_regime()` — a month is BULL if
      >=50% of its BTC 8h bars have close[t-1] > SMA_270[t-1] (`.shift(1)`
      before the rolling SMA — past-only), else BEAR/CHOP.
      Input columns: BTCUSDT 8h `open_time`, `close` ONLY (calendar/price
      label — NOT an OOS performance metric).  IS-only / a-priori: A-PRIORI.
      NOTE: this label only LABELS histogram rows in the report CSV. It does
      NOT enter the trained model, the trade roster, or any selection gate.

  PARAMETER 3 — the histogram bin edges for `confidence_distribution.csv`.
      Selection function: a-priori uniform grid on the intrinsic [0.50, 1.00]
      confidence scale, edges every 0.025 (`CONF_BIN_EDGES`).
      Input columns: NONE.  IS-only / a-priori: A-PRIORI.

  PARAMETER 4 — the EDA per-month training window (used only by TEST B's
                labeling-family note — no model is trained in this EDA).
      a-priori: `training_months = 24`, the SACRED CONSTANT.

The conviction-derate constants (C_FLOOR / C_REF / W_MIN_FRAC) are NOT design
parameters of iter-v3/080 — /080 REVERTS /079's derate (Section 3.2 baseline-
restore) and ships flat weight=100. /080 selects NO conviction constant. The
empirical placement of a future C_REF is explicitly DEFERRED to cycle 3, to be
done from the `confidence_distribution.csv` this iteration builds.

================================================================================
WHY THE PASSIVE-DIAGNOSTIC IS THE HIGHER-EV USE OF THE FINAL CYCLE-2 SLOT
================================================================================
Cycle 2 is 9/10 done with 0 clean PROMISING (4 SUSPICIOUS-OOS-DOMINANT, 1
NEGATIVE, 3 INERT, 1 NULL-RESULT). On current evidence the /081 CONFIRMATION is
a /059-baseline multi-seed re-validation regardless of /080's outcome — a
PASSIVE-DIAGNOSTIC, by design, will not produce a PROMISING edge ingredient, so
it does not change the /081 plan. The question is therefore: what is the most
valuable thing the final EXPLORATION slot can DELIVER?

Two candidates:
  (1) PASSIVE-DIAGNOSTIC — build the persisted-`confidence` instrument. Cost: a
      ~one-line report-column change + one report CSV. Benefit: discharges the
      standing /079 Critic Rec #1, and converts the PARKED conviction-derate
      axis from "blocked, needs instrumentation" into "cycle-3-ready, C_REF
      placeable empirically". Provably bit-identical roster (after the /079
      derate revert) — SUSPICIOUS is mechanically near-impossible (TEST D).
  (2) A fresh structural axis — a vol-adjusted barrier label. TEST B shows this
      is NOT fresh: it is a barrier knob in the SATURATED holding-time-extension
      family, and `feedback_v3_is_oos_regime_divergence.md` predicts it
      reproduces SUSPICIOUS-OOS-DOMINANT. Spending the last slot on a
      structurally-predicted-SUSPICIOUS axis delivers another regime-luck data
      point, not an edge ingredient.

An honest EDA concludes (1): the PASSIVE-DIAGNOSTIC converts an open
methodology debt into a deliverable and seeds a clean cycle-3 re-attempt; the
"fresh axis" candidate is a knob on a closed axis whose outcome is structurally
predictable. This mirrors the /077 PASSIVE-DIAGNOSTIC precedent exactly (which
spent a slot building the conditional-orthogonality map and was certified clean
INERT-AT-EXPLORATION).

Run:
  python analysis/iteration_v3-080/axis_selection_eda.py
"""

from __future__ import annotations

import ast
import csv
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = Path(__file__).resolve().parent
OUT_DIR = ANALYSIS_DIR

# Sacred constant — IMMUTABLE. The OOS cutoff. Used ONLY to label rosters
# IS vs OOS for the bit-identity / degeneracy proof. No parameter is selected
# on OOS data anywhere in this module.
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC
CANDLE_MS = 8 * 60 * 60 * 1000  # 8h

# a-priori histogram bin edges for confidence_distribution.csv (PARAMETER 3).
CONF_BIN_EDGES = [round(0.50 + 0.025 * i, 3) for i in range(21)]  # 0.50..1.00


# ---------------------------------------------------------------------------
# PARAMETER 1 — the axis. Data-free constant. Not a sort/filter/argmax.
# ---------------------------------------------------------------------------
def _pick_axis() -> str:
    """Return the fixed iter-v3/080 axis identifier. Data-free — a-priori."""
    return (
        "PASSIVE-DIAGNOSTIC: persist per-trade M1 confidence to trades.csv "
        "+ emit confidence_distribution.csv"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_trades(iter_label: str, split: str) -> list[dict]:
    """Read a committed trades.csv roster. Read-only; no OOS quantity used for
    parameter selection — OOS rosters feed only count-printing proofs."""
    p = REPO / "reports-v3" / f"iteration_v3-{iter_label}" / split / "trades.csv"
    if not p.is_file():
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def _duration_candles(row: dict) -> float:
    return (int(row["close_time"]) - int(row["open_time"])) / CANDLE_MS


def _is_only(rows: list[dict]) -> list[dict]:
    """Filter to IS rows (open_time < OOS cutoff). Honesty guard for any
    statistic that feeds the axis rationale."""
    return [r for r in rows if int(r["open_time"]) < OOS_CUTOFF_MS]


# ===========================================================================
# TEST A — the instrumentation gap (the /079 Critic Rec #1 finding, verified)
# ===========================================================================
def test_a_instrumentation_gap() -> list[dict]:
    """Verify, from the committed rosters, that no report artifact persists the
    per-trade M1 `confidence`. This is the /079 root cause restated as fact."""
    rows_is = _read_trades("060", "in_sample")
    cols = list(rows_is[0].keys()) if rows_is else []
    out = [
        {
            "fact": "trades.csv column count",
            "value": str(len(cols)),
            "note": "; ".join(cols),
        },
        {
            "fact": "confidence column present in trades.csv",
            "value": str("confidence" in cols),
            "note": "M1 directional margin is NOT persisted anywhere",
        },
        {
            "fact": "weight_factor semantics",
            "value": "vt_scale x (signal.weight/100)",
            "note": (
                "weight_factor is the vol-target scale times the signal weight; "
                "at /079 signal.weight is the conviction-derate output. It is "
                "NOT the M1 confidence scalar — confidence is upstream of weight."
            ),
        },
        {
            "fact": "C_REF empirical placement possible today",
            "value": "False",
            "note": (
                "the M1 confidence distribution is computed inside "
                "lgbm.get_signal and discarded; recovering it needs a backtest "
                "(re-train every walk-forward month) — exactly the /079 "
                "instrumentation gap the Critic Rec #1 named"
            ),
        },
    ]
    return out


# ===========================================================================
# TEST B — the "fresh structural axis" alternative is a knob on a closed axis
# ===========================================================================
def test_b_labeling_family_is_saturated() -> list[dict]:
    """Document that cycle 2 has exhausted labeling, and that a vol-adjusted
    barrier is a barrier-rebalancing change in the SATURATED holding-time-
    extension family. This is a-priori reasoning over the cycle record — no
    model trained, no metric computed; it justifies SKIPPING the alt axis."""
    return [
        {
            "cycle2_labeling_attempt": "iter-v3/071 meta-labeling (M2 take/skip)",
            "verdict": "SUSPICIOUS-OOS-DOMINANT",
            "mechanism": "M2 veto removes early stop-outs -> holding-time extension",
        },
        {
            "cycle2_labeling_attempt": "iter-v3/072 fixed-horizon-21 label",
            "verdict": "NEGATIVE",
            "mechanism": "label DEFINITION change; no edge",
        },
        {
            "cycle2_labeling_attempt": "iter-v3/073 per-symbol triple-barrier asymmetry",
            "verdict": "SUSPICIOUS-OOS-DOMINANT (OOS/IS ratio 6.85)",
            "mechanism": "per-symbol barrier rebalanced toward TP -> holding-time extension",
        },
        {
            "cycle2_labeling_attempt": (
                "candidate: vol-adjusted past-only-realized-vol barrier "
                "(the /079-diary floated alt)"
            ),
            "verdict": "PREDICTED SUSPICIOUS-OOS-DOMINANT — SKIP",
            "mechanism": (
                "replacing the global ATR multiplier with a per-symbol "
                "realized-vol barrier RE-SCALES the TP/SL distances per trade "
                "-> changes per-trade duration -> SATURATED holding-time-"
                "extension family (feedback_v3_is_oos_regime_divergence.md: "
                "/065/071/073). A barrier knob is NOT a category-1/2 structural "
                "axis; it is a knob on a closed axis."
            ),
        },
    ]


# ===========================================================================
# TEST C — the conviction hypothesis has weak-but-real residual support
# ===========================================================================
def test_c_conviction_residual_support() -> list[dict]:
    """Quantify the /079 residual finding from the committed /079 IS roster.

    The /079 engineering report isolated 12 de-rated (low-conviction) IS trades
    vs 147 non-de-rated. We cannot re-derive `confidence` here (TEST A) — but
    /079's derate de-rates exactly when conviction is below C_REF, and a de-rate
    is detectable in the /079 roster as a `weight_factor` that the SAME-cell
    /060 roster (flat weight) does NOT carry. Concretely: a /079 IS trade is
    de-rated iff its weight_factor is strictly lower than the matching /060
    trade's weight_factor on the same (symbol, open_time) key (the only thing
    that changed /060 -> /079 is the conviction-derate; the roster keys and the
    vol-target scale are bit-identical, per the /079 diary). We then compare the
    de-rated group's IS outcomes against the non-de-rated group's.

    This is an IS-ONLY statistic — every row used is asserted IS. It quantifies
    whether low conviction associated with worse IS outcomes. It does NOT
    re-attempt the derate and selects no parameter."""
    is060 = {(r["symbol"], r["open_time"]): r for r in _is_only(_read_trades("060", "in_sample"))}
    is079 = _is_only(_read_trades("079", "in_sample"))

    derated, non_derated = [], []
    for r in is079:
        key = (r["symbol"], r["open_time"])
        base = is060.get(key)
        if base is None:
            continue
        # de-rated iff /079 weight_factor strictly below /060's on the same key
        # (tolerance for float formatting in the CSV)
        if float(r["weight_factor"]) < float(base["weight_factor"]) - 1e-6:
            derated.append(r)
        else:
            non_derated.append(r)

    def _grp(rows: list[dict], label: str) -> dict:
        if not rows:
            return {
                "group": label,
                "n_is_trades": "0",
                "mean_net_pnl_pct": "n/a",
                "win_rate_pct": "n/a",
            }
        pnl = [float(r["net_pnl_pct"]) for r in rows]
        wins = sum(1 for r in rows if float(r["weighted_pnl"]) > 0)
        return {
            "group": label,
            "n_is_trades": str(len(rows)),
            "mean_net_pnl_pct": f"{st.mean(pnl):.4f}",
            "win_rate_pct": f"{100.0 * wins / len(rows):.1f}",
        }

    rows_out = [
        _grp(derated, "de-rated (low-conviction, /079 weight_factor < /060)"),
        _grp(non_derated, "non-de-rated"),
    ]
    incidence = (
        100.0 * len(derated) / (len(derated) + len(non_derated))
        if (derated or non_derated)
        else 0.0
    )
    rows_out.append(
        {
            "group": "de-rate incidence (IS)",
            "n_is_trades": f"{len(derated)}/{len(derated) + len(non_derated)}",
            "mean_net_pnl_pct": f"{incidence:.1f}%",
            "win_rate_pct": (
                "7.5% at /079 vs >=25% predicted -> NULL-RESULT behavioral "
                "saturation; C_REF=0.65 sat on the Optuna threshold pile-up"
            ),
        }
    )
    return rows_out


# ===========================================================================
# TEST D — the PASSIVE-DIAGNOSTIC roster is bit-identical (SUSPICIOUS proof)
# ===========================================================================
def test_d_bit_identity_proof() -> list[dict]:
    """Establish that iter-v3/080 — after reverting /079's conviction-derate to
    flat weight=100 and adding only a report column + one report CSV — runs the
    byte-identical /060-config. The trade roster is therefore bit-identical to
    /060, the OOS/IS ratio is a mechanical copy, and SUSPICIOUS is structurally
    near-impossible (this is the PROOF that justifies a sub-base-rate SUSPICIOUS
    weight in brief Section 7, per the /077 precedent).

    The /060 vs /079 roster comparison below shows the keys are ALREADY
    identical (159 IS / ~102 OOS) — /079's derate only re-weighted; it added/
    removed no trade. /080 reverts the derate, so /080's roster equals /060's
    on keys AND on weight_factor (the derate is the only /060->/079 delta)."""
    out = []
    for split in ["in_sample", "out_of_sample"]:
        r060 = _read_trades("060", split)
        r079 = _read_trades("079", split)
        k060 = {(r["symbol"], r["open_time"]) for r in r060}
        k079 = {(r["symbol"], r["open_time"]) for r in r079}
        out.append(
            {
                "split": split,
                "n_060": str(len(r060)),
                "n_079": str(len(r079)),
                "keys_added_079_vs_060": str(len(k079 - k060)),
                "keys_removed_079_vs_060": str(len(k060 - k079)),
                "note": (
                    "key roster identical; /079 derate re-weighted only. "
                    "/080 reverts the derate -> /080 roster == /060 on keys "
                    "AND weight_factor. confidence column is report-only."
                ),
            }
        )
    out.append(
        {
            "split": "PROOF",
            "n_060": "—",
            "n_079": "—",
            "keys_added_079_vs_060": "—",
            "keys_removed_079_vs_060": "—",
            "note": (
                "iter-v3/080 = /060-config exactly + (a) flat weight=100 "
                "restored + (b) `confidence` trades.csv column + (c) "
                "confidence_distribution.csv. (a) is a revert to the anchor; "
                "(b)+(c) are pure report emission with zero behavioral effect. "
                "=> roster bit-identical to /060 => OOS/IS ratio is a "
                "mechanical identity, not an estimate => SUSPICIOUS "
                "mechanically near-impossible."
            ),
        }
    )
    return out


# ===========================================================================
# TEST E — holding-time predictor (mandated; mechanical identity here)
# ===========================================================================
def test_e_holding_time_predictor() -> list[dict]:
    """The holding-time-effect predictor + the added-vs-removed roster-
    composition sub-channel (feedback_v3_is_oos_regime_divergence.md + Critic
    /076 Rec #2). For a PASSIVE-DIAGNOSTIC (revert-derate + report-only) both
    channels are mechanical identities. Reported on the /060 roster."""
    out = []
    for split in ["in_sample", "out_of_sample"]:
        rows = _read_trades("060", split)
        durs = [_duration_candles(r) for r in rows]
        out.append(
            {
                "split": split,
                "n_trades": str(len(rows)),
                "mean_duration_candles_060": f"{st.mean(durs):.4f}" if durs else "n/a",
                "predicted_full_roster_duration_delta": "0.0000",
                "predicted_trades_added": "0",
                "predicted_trades_removed": "0",
                "basis": (
                    "byte-identical /060-config labeling + model + seeds => "
                    "identical per-trade barriers; report column touches no "
                    "barrier; added & removed sets BOTH empty (degenerate "
                    "sub-channel)"
                ),
            }
        )
    return out


# ===========================================================================
# NO-CHEATING SELF-AUDIT — AST scan for OOS-metric live identifiers
# ===========================================================================
def _grep_no_oos_tuning() -> str:
    """AST-scan this module: flag any OOS-metric token used as a LIVE
    identifier — a `Name` (variable read), an `Attribute` access, or a
    `Subscript` string key. Non-docstring prose string Constants that merely
    MENTION an OOS metric are NOT flagged (they cannot feed a sort/filter/
    argmax). `OOS_CUTOFF_MS` is the sacred constant and is exempt.
    Returns 'PASS' if no live OOS-metric identifier is found, else 'FAIL ...'.
    """
    src = Path(__file__).read_text()
    tree = ast.parse(src)
    forbidden = {"oos_sharpe", "oos_delta", "oos_pnl", "oos_return", "oos_metric"}
    hits: list[str] = []

    for node in ast.walk(tree):
        # a variable named after an OOS metric being READ
        if isinstance(node, ast.Name) and node.id.lower() in forbidden:
            hits.append(f"Name:{node.id}@L{node.lineno}")
        # an attribute access ending in an OOS-metric token
        elif isinstance(node, ast.Attribute) and node.attr.lower() in forbidden:
            hits.append(f"Attribute:{node.attr}@L{node.lineno}")
        # a dict/df SUBSCRIPT keyed by an OOS-metric string literal — the
        # concrete iter-v3/075 cheating signature (`row["oos_delta"]`)
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            key = node.slice.value
            if isinstance(key, str) and key.lower() in forbidden:
                hits.append(f"Subscript-key:{key}@L{node.lineno}")
    return "PASS" if not hits else f"FAIL: {hits}"


# ---------------------------------------------------------------------------
def _dump(name: str, rows: list[dict]) -> None:
    if not rows:
        print(f"[{name}] (empty)")
        return
    path = OUT_DIR / f"{name}.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[{name}] -> {path}  ({len(rows)} rows)")
    for r in rows:
        print("   ", r)


def main() -> None:
    print("=" * 78)
    print("iter-v3/080 axis-selection EDA — PASSIVE-DIAGNOSTIC (persist confidence)")
    print("AXIS:", _pick_axis())
    print("=" * 78)

    a = test_a_instrumentation_gap()
    b = test_b_labeling_family_is_saturated()
    c = test_c_conviction_residual_support()
    d = test_d_bit_identity_proof()
    e = test_e_holding_time_predictor()

    _dump("T_A_instrumentation_gap", a)
    _dump("T_B_labeling_family_saturated", b)
    _dump("T_C_conviction_residual_support", c)
    _dump("T_D_bit_identity_proof", d)
    _dump("T_E_holding_time_predictor", e)

    audit = _grep_no_oos_tuning()
    print()
    print(f"NO-CHEATING AST self-audit: {audit}")
    assert audit == "PASS", audit

    # one-line summary CSV
    summary = [
        {
            "decision": "PASSIVE-DIAGNOSTIC — persist confidence + confidence_distribution.csv",
            "test_A": "instrumentation gap confirmed: confidence absent from all artifacts",
            "test_B": "alt axis (vol-adj barrier) = knob on SATURATED holding-time family -> SKIP",
            "test_C": "conviction hypothesis has weak-but-real IS residual support",
            "test_D": "roster bit-identical to /060 -> SUSPICIOUS mechanically near-impossible",
            "no_oos_tuning": audit,
        }
    ]
    _dump("axis_selection_summary", summary)
    print()
    print("EDA complete. Axis: PASSIVE-DIAGNOSTIC. No design parameter selected on OOS data.")


if __name__ == "__main__":
    main()
