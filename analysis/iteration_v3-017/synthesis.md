# iter-v3/017 EDA Synthesis — Meta-Labeling Architecture

## Source data
- iter-v3/013 IS trade roster: `reports-v3/iteration_v3-013/in_sample/trades.csv`
- N = 209 trades (M1-positive predictions from iter-v3/013 baseline)
- Exit reasons: TP=71 / SL=124 / Timeout=14

## M2 label distribution (positive-class prior)

The M2 secondary classifier predicts "did the M1-positive prediction reach TP
before SL or timeout?" — binary label = 1 if `exit_reason == 'take_profit'`,
0 otherwise.

| Scope | N M1-positive bars | N M2=1 (TP hit) | M2 positive-class rate |
|---|---:|---:|---:|
| **Overall** | **209** | **71** | **33.97%** |
| BCHUSDT | 100 | 35 | 35.00% |
| LDOUSDT | 21 | 9 | 42.86% |
| TRXUSDT | 88 | 27 | 30.68% |


**Calibration**: M2 positive-class prior = **33.97%** overall
(consistent with iter-v3/013's IS WR ~36% — TP rate is slightly below WR
because WR includes timeouts that closed positive while TP rate counts only
TP-barrier hits). Per-symbol prior ranges from 30.7%
(TRXUSDT) to
42.9%
(LDOUSDT) — moderate per-symbol
heterogeneity but not extreme; M2 should learn a useful generalizing signal.

## M2 label generation pseudocode

At training time, after M1 is trained for a calendar month:

```
def generate_m2_labels(m1_model, train_features, train_labels, train_weights,
                       long_pnls, short_pnls, master_df, candidate_indices,
                       atr_values, timeout_minutes, fee_pct):
    """Generate M2 labels for the training window.

    For each M1-positive prediction (M1 says trade), walk forward on price
    path to determine TP/SL/timeout outcome, label M2 = 1 if TP-first else 0.
    """
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
- Baseline IS trade count (iter-v3/013): **209**
- Saturation band: **[157, 261]** (lower bound = floor(0.75 × 209); upper bound = ceil(1.25 × 209))

**Predicted iter-v3/017 IS trade count: ~120-180**
(M2 filters at threshold 0.5 → keeps ~30-50% of M1-positive bars in
expectation, but the precise count depends on M2's confidence distribution).
This prediction is BELOW the saturation lower bound 157, which is
EXPECTED behavior for meta-labeling (it filters trades, by design).

**Saturation falsifier per `feedback_axis_saturation_predictor.md`**:
- Lower-bound NULL-RESULT trigger: IS trades >= 157 → meta-labeling
  did NOT propagate (M2 filter too lenient or M2 inactive). Verdict: BLOCK.
- Upper-bound saturation cap: IS trades > 261 → architecture failure
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
  (predicted [120, 180] IS trades). Per-trade
  economics improve enough to compensate for trade-count drop.
- **PATH B (NEGATIVE-no-effect)**: M2 trusts every M1 signal → trade count
  ≈ iter-v3/013 baseline (>= 157) → BLOCK or NEGATIVE-no-effect
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
diverge from this analysis's 71 because of the three sources
of variance above.
