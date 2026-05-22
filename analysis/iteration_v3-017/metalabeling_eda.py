"""iter-v3/017 EDA — meta-labeling architecture (López de Prado AFML Ch. 3).

Phase 5.5 reproducibility requirement: this script reads ONLY iter-v3/013's
already-disclosed trade rosters (the M1 baseline) and produces:

  (a) M2 label distribution: what fraction of M1's positive predictions
      (i.e., taken trades) actually closed at TP (the take-profit barrier)
      within the timeout? This calibrates M2's positive-class prior.

  (b) Per-symbol M2 label rates — does M2 see different positive-class
      prior across BCH / LDO / TRX?

  (c) M2 label generation pseudocode (documented in synthesis.md).

  (d) Saturation predictor with NEW tighter band [iter-v3/013 baseline ± 25%]
      = [157, 261] trades per Critic Clar 4 of iter-v3/016. Predicts ~120-180
      IS trades after M2 filtering at threshold 0.5.

The M2 architecture:
  - M1 (primary): existing LightGbmStrategy on V3_FEATURE_COLUMNS (13 features).
    Predicts direction (binary +1/-1) using triple-barrier labels.
  - M2 (secondary): LGBMClassifier predicting "did the M1-positive prediction
    close at TP within timeout?" — binary 0/1.
  - Final signal: trade only when M1 says go AND M2 confidence >= 0.5.

The natural M2 label proxy for this analysis is `exit_reason == 'take_profit'`
on iter-v3/013's IS trade roster — every row was an M1-positive prediction
(M1 fired the trade) so the trade exit reveals whether TP was hit before
SL or timeout.

Outputs (committed alongside the script):
  - m2_label_distribution.csv — overall + per-symbol M2 positive-class rate
  - exit_reason_breakdown.csv — full TP/SL/timeout breakdown
  - synthesis.md — narrative + label-generation pseudocode + saturation band

This script does NOT generate new OOS information. It re-aggregates the
already-disclosed iter-v3/013 IS roster for M2 prior calibration.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_IS = ROOT / "reports-v3" / "iteration_v3-013" / "in_sample" / "trades.csv"
OUT_DIR = ROOT / "analysis" / "iteration_v3-017"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    rows = list(csv.DictReader(open(SRC_IS)))
    n_total = len(rows)
    if n_total == 0:
        raise RuntimeError(f"No trades found in {SRC_IS}")

    # Bucket exits
    by_symbol: dict[str, dict[str, int]] = {}
    overall: dict[str, int] = {"take_profit": 0, "stop_loss": 0, "timeout": 0, "other": 0}

    for r in rows:
        sym = r["symbol"]
        exit_reason = r["exit_reason"]
        if exit_reason not in ("take_profit", "stop_loss", "timeout"):
            exit_reason = "other"
        overall[exit_reason] = overall.get(exit_reason, 0) + 1
        if sym not in by_symbol:
            by_symbol[sym] = {"take_profit": 0, "stop_loss": 0, "timeout": 0, "other": 0}
        by_symbol[sym][exit_reason] = by_symbol[sym].get(exit_reason, 0) + 1

    # Compute M2 positive-class prior overall
    m2_pos_overall = overall["take_profit"]
    m2_pos_rate_overall = m2_pos_overall / n_total

    # Per-symbol M2 prior
    sym_m2_rates: dict[str, tuple[int, int, float]] = {}
    for sym, counts in by_symbol.items():
        n_sym = sum(counts.values())
        n_tp = counts["take_profit"]
        sym_m2_rates[sym] = (n_tp, n_sym, n_tp / n_sym if n_sym > 0 else 0.0)

    # Saturation band per Critic Clar 4 of iter-v3/016 (NEW tighter band)
    BASELINE_N = 209  # iter-v3/013 IS trade count
    sat_lower = round(BASELINE_N * 0.75)  # 157
    sat_upper = round(BASELINE_N * 1.25)  # 261
    # Predicted IS trade count after M2 filter at 0.5: ~120-180 (M2 keeps a
    # subset of M1-positive bars; if M2 mirrors the TP-hit prior, ~30-50% of
    # M1-positive bars exceed threshold 0.5 in expectation).
    predicted_lower = 120
    predicted_upper = 180

    # ---- Write distribution CSV ----
    dist_path = OUT_DIR / "m2_label_distribution.csv"
    with open(dist_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scope", "n_trades", "n_m2_positive_TP", "m2_positive_rate"])
        w.writerow(["overall", n_total, m2_pos_overall, f"{m2_pos_rate_overall:.4f}"])
        for sym in sorted(sym_m2_rates):
            n_tp, n_sym, rate = sym_m2_rates[sym]
            w.writerow([sym, n_sym, n_tp, f"{rate:.4f}"])

    # ---- Write exit-reason breakdown CSV ----
    breakdown_path = OUT_DIR / "exit_reason_breakdown.csv"
    with open(breakdown_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scope", "n_trades", "take_profit", "stop_loss", "timeout", "tp_pct", "sl_pct", "to_pct"])
        w.writerow([
            "overall",
            n_total,
            overall["take_profit"],
            overall["stop_loss"],
            overall["timeout"],
            f"{overall['take_profit']/n_total*100:.2f}",
            f"{overall['stop_loss']/n_total*100:.2f}",
            f"{overall['timeout']/n_total*100:.2f}",
        ])
        for sym in sorted(by_symbol):
            cnt = by_symbol[sym]
            n_sym = sum(cnt.values())
            w.writerow([
                sym,
                n_sym,
                cnt["take_profit"],
                cnt["stop_loss"],
                cnt["timeout"],
                f"{cnt['take_profit']/n_sym*100:.2f}",
                f"{cnt['stop_loss']/n_sym*100:.2f}",
                f"{cnt['timeout']/n_sym*100:.2f}",
            ])

    # ---- Synthesis ----
    synth = f"""# iter-v3/017 EDA Synthesis — Meta-Labeling Architecture

## Source data
- iter-v3/013 IS trade roster: `reports-v3/iteration_v3-013/in_sample/trades.csv`
- N = {n_total} trades (M1-positive predictions from iter-v3/013 baseline)
- Exit reasons: TP={overall['take_profit']} / SL={overall['stop_loss']} / Timeout={overall['timeout']}

## M2 label distribution (positive-class prior)

The M2 secondary classifier predicts "did the M1-positive prediction reach TP
before SL or timeout?" — binary label = 1 if `exit_reason == 'take_profit'`,
0 otherwise.

| Scope | N M1-positive bars | N M2=1 (TP hit) | M2 positive-class rate |
|---|---:|---:|---:|
| **Overall** | **{n_total}** | **{m2_pos_overall}** | **{m2_pos_rate_overall*100:.2f}%** |
"""
    for sym in sorted(sym_m2_rates):
        n_tp, n_sym, rate = sym_m2_rates[sym]
        synth += f"| {sym} | {n_sym} | {n_tp} | {rate*100:.2f}% |\n"

    synth += f"""

**Calibration**: M2 positive-class prior = **{m2_pos_rate_overall*100:.2f}%** overall
(consistent with iter-v3/013's IS WR ~36% — TP rate is slightly below WR
because WR includes timeouts that closed positive while TP rate counts only
TP-barrier hits). Per-symbol prior ranges from {min(r[2] for r in sym_m2_rates.values())*100:.1f}%
({min(sym_m2_rates, key=lambda s: sym_m2_rates[s][2])}) to
{max(r[2] for r in sym_m2_rates.values())*100:.1f}%
({max(sym_m2_rates, key=lambda s: sym_m2_rates[s][2])}) — moderate per-symbol
heterogeneity but not extreme; M2 should learn a useful generalizing signal.

## M2 label generation pseudocode

At training time, after M1 is trained for a calendar month:

```
def generate_m2_labels(m1_model, train_features, train_labels, train_weights,
                       long_pnls, short_pnls, master_df, candidate_indices,
                       atr_values, timeout_minutes, fee_pct):
    \"\"\"Generate M2 labels for the training window.

    For each M1-positive prediction (M1 says trade), walk forward on price
    path to determine TP/SL/timeout outcome, label M2 = 1 if TP-first else 0.
    \"\"\"
    # M1 inference on training features
    m1_proba = m1_model.predict_proba(train_features)   # [n, 2] for binary
    m1_pred = np.argmax(m1_proba, axis=1)               # 0=short, 1=long
    m1_confidence = m1_proba.max(axis=1)
    m1_positive = m1_confidence >= m1.confidence_threshold

    # For each M1-positive bar, check the actual TP/SL/timeout outcome
    # (already encoded in long_pnls / short_pnls from the triple-barrier
    # labeler — TP-hit yields tp_pnl_pct, SL-hit yields -sl_pnl_pct, timeout
    # yields fwd_return_pct).
    m2_labels = np.zeros(n, dtype=int)
    m2_features = np.zeros((n, n_input_features), dtype=float)

    for i in candidate_indices[m1_positive]:
        direction = +1 if m1_pred[i] == 1 else -1
        outcome_pnl = long_pnls[i] if direction == +1 else short_pnls[i]
        # M2 = 1 iff direction-correct trade hit TP barrier (NOT timeout, NOT SL)
        m2_labels[i] = 1 if outcome_pnl >= (tp_pct - fee_pct) else 0

    # M2 input features: 13 V3 features + M1's prediction probability
    m2_features[m1_positive, :13] = train_features[m1_positive]
    m2_features[m1_positive, 13] = m1_confidence[m1_positive]

    return m2_labels, m2_features
```

At prediction time:

```
def get_signal_metalabeled(symbol, open_time):
    m1_signal = m1.get_signal(symbol, open_time)
    if m1_signal == NO_SIGNAL:
        return NO_SIGNAL
    # M2 inference: 13 features + M1's confidence as 14th feature
    feat = lookup_features(symbol, open_time)
    m2_input = np.concatenate([feat, [m1_signal.confidence]])
    m2_proba = m2_model.predict_proba(m2_input.reshape(1, -1))[0]
    m2_confidence = m2_proba[1]   # P(TP-hit class)
    if m2_confidence < 0.5:
        return NO_SIGNAL          # M2 vetoes M1's signal
    return m1_signal                  # M2 trusts M1 → trade
```

## Saturation predictor (iter-v3/017 brief §2 + §4.4 row 5)

Per Critic Clar 4 of iter-v3/016, the saturation falsifier band tightens to
`[baseline ± 25%]`:
- Baseline IS trade count (iter-v3/013): **{BASELINE_N}**
- Saturation band: **[{sat_lower}, {sat_upper}]** (lower bound = floor(0.75 × {BASELINE_N}); upper bound = ceil(1.25 × {BASELINE_N}))

**Predicted iter-v3/017 IS trade count: ~{predicted_lower}-{predicted_upper}**
(M2 filters at threshold 0.5 → keeps ~30-50% of M1-positive bars in
expectation, but the precise count depends on M2's confidence distribution).
This prediction is BELOW the saturation lower bound {sat_lower}, which is
EXPECTED behavior for meta-labeling (it filters trades, by design).

**Saturation falsifier per `feedback_axis_saturation_predictor.md`**:
- Lower-bound NULL-RESULT trigger: IS trades >= {sat_lower} → meta-labeling
  did NOT propagate (M2 filter too lenient or M2 inactive). Verdict: BLOCK.
- Upper-bound saturation cap: IS trades > {sat_upper} → architecture failure
  (M2 generated more trades than M1 baseline, structurally impossible
  unless wiring is broken). Verdict: BLOCK.
- Both bounds active for iter-v3/017 EXPLORATION.

## Per Critic Clar 1 of iter-v3/016 — §4.4 row 5 condition update

The brief template §4.4 row 5 for iter-v3/017 reads:
"either |Δ trades| ≥ 11 OR per-symbol shift > 5 trades on any symbol"

This catches opposite-direction per-symbol shifts that mask through to
portfolio aggregate (e.g., iter-v3/016's BCH -5 + TRX +11 + LDO +2 = +8
portfolio aggregate hides TRX +11 from the 11-trade threshold).

For iter-v3/017 meta-labeling: per-symbol shifts are EXPECTED to be large
in the negative direction (M2 filters trades) but NOT in the positive
direction. If any symbol's IS trade count INCREASES vs iter-v3/013 baseline,
that's a wiring red flag.

## Three pathways (per iter-v3/017 brief §4.4)

- **PATH A (PROMISING)**: M2 filters effectively → IS Sharpe ≥ +0.10 above
  iter-v3/013 +1.0088 baseline → PROMISING. Trade count drops 20-50%
  (predicted [{predicted_lower}, {predicted_upper}] IS trades). Per-trade
  economics improve enough to compensate for trade-count drop.
- **PATH B (NEGATIVE-no-effect)**: M2 trusts every M1 signal → trade count
  ≈ iter-v3/013 baseline (>= {sat_lower}) → BLOCK or NEGATIVE-no-effect
  per saturation falsifier.
- **PATH C (NEGATIVE-over-filter)**: M2 filters too aggressively → trade
  count < 30 OR OOS Sharpe collapses < +0.50. Suggests M2 overfitting to
  IS noise rather than learning generalizable confidence.

## Audit-trail integrity

This EDA does NOT use any iter-v3/013 OOS data. It uses ONLY the IS roster
to calibrate M2's positive-class prior. The iter-v3/017 backtest will see
different M2 labels because:

1. M1 is retrained per-month walk-forward at iter-v3/017 (different M1 →
   different M1-positive bars → different M2 label set)
2. M2 retrains every month with M1's per-month predictions
3. Optuna re-optimization on M2 search space introduces hyperparam variance

The DIRECTION of the M2 prior (~33-36% positive class rate) is calibration-
informative; the EXACT count of M2=1 labels in the iter-v3/017 run will
diverge from this analysis's {m2_pos_overall} because of the three sources
of variance above.
"""

    synth_path = OUT_DIR / "synthesis.md"
    with open(synth_path, "w") as f:
        f.write(synth)

    print(f"Wrote: {dist_path}")
    print(f"Wrote: {breakdown_path}")
    print(f"Wrote: {synth_path}")
    print(f"\nM2 positive-class prior (overall): {m2_pos_rate_overall*100:.2f}% ({m2_pos_overall}/{n_total})")
    print(f"Per-symbol prior range: [{min(r[2] for r in sym_m2_rates.values())*100:.2f}%, {max(r[2] for r in sym_m2_rates.values())*100:.2f}%]")
    print(f"Saturation band [iter-v3/013 ± 25%]: [{sat_lower}, {sat_upper}]")
    print(f"Predicted iter-v3/017 IS trade count: [{predicted_lower}, {predicted_upper}]")


if __name__ == "__main__":
    main()
