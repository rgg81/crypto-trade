# iter-v3/075 — Axis-Selection EDA Synthesis

## QR axis decision

**Primitive 12 — BTC-trend-regime position-SIZE de-rate scalar, SCOPED to the genuine-drag symbols ('LDOUSDT', 'TRXUSDT').** A NEW risk primitive: a past-only BTC bull/bear-chop classifier (close[t-1] < SMA_270(close)[t-1]). When the classifier says BTC bear/chop, the position WEIGHT of a trade is multiplied by **0.5** — but ONLY for symbols in the scope set ('LDOUSDT', 'TRXUSDT'). BCH trades and all bull-regime trades are unchanged (weight 1.0). The scalar slots in at primitive 5 (vol-scaling) as an extra multiplicative factor — WEIGHT only, never SL/TP/timeout.

## Why this axis — and the EDA-driven correction to the SCOPE

Critic /074 FINAL `2371324` Rec #3 mandates iter-v3/075 target the IS bear/chop drag directly with a HOLDING-TIME-ORTHOGONAL, FULL-ROSTER mechanism. T1 re-derives the drag: IS bear/chop monthly Sharpe **-0.2193** (26.3% positive months, 77 trades, total wpnl -6.8733).

The EDA first tested a BLANKET (all-3-symbol) bear/chop SIZE de-rate (T3). It is IS-NEGATIVE at every scalar (IS Δ -0.0274 at derate 0.5; the full T3 grid is monotone-negative). T7 explains why: the drag is SYMBOL-ASYMMETRIC. BCH's bear/chop-entry IS trades carry **+35.6641 wpnl** — BCH WINS in BTC-bear/chop months. TRX's bear/chop-entry IS wpnl is **-10.4875** and LDO's is **-3.641** — TRX and LDO are the genuine drag. A blanket de-rate down-scales BCH's IS edge and collapses IS Sharpe.

The corrected axis SCOPES the de-rate to ('LDOUSDT', 'TRXUSDT') — the symbols whose bear/chop-entry IS wpnl is negative (T7 `bearchop_is_genuine_drag`). T8 is the scoped counterfactual: IS Δ **+0.1413**, OOS Δ **-0.1426**, OOS/IS ratio -0.0024. The scope is the IS-improving axis, not a customisation that breaks IS — BCH (the IS-edge carrier) is deliberately OUTSIDE the scope and is bit-identical to /060.

## Holding-time-orthogonality (T4)

A position-SIZE scalar removes NO trade and shifts NO barrier. The kept-roster mean/median duration delta is **EXACTLY 0** (T4) — the post-scalar roster is bit-identical in membership and timing; only `weighted_pnl` differs. Per `feedback_v3_is_oos_regime_divergence.md`, a ~0 duration change does NOT load the IS/OOS regime factor. This axis is structurally incapable of reproducing the SUSPICIOUS-OOS-DOMINANT holding-time-extension pattern of /065/071/073.

## Behavioral-effect prediction (T5, scoped to the de-rate set)

Within the scope ('LDOUSDT', 'TRXUSDT'), the scalar changes the WEIGHT of **24 IS trades** and **32 OOS trades** (bear/chop-entry trades of the scope symbols — see T5 per-symbol rows). This is MATERIALLY LARGER than /074's 3-IS/5-OOS suppression — the full-roster mandate is satisfied. The IS effect (>20 trades) clears the Critic threshold by a wide margin.

## Simulated historical effect (T8)

At the chosen de-rate 0.5, scope ('LDOUSDT', 'TRXUSDT'), on the /060 roster: IS monthly Sharpe 0.9738 (Δ +0.1413), OOS monthly Sharpe -0.0023 (Δ -0.1426), OOS/IS ratio -0.0024. CRUCIAL: a position-SIZE scalar at primitive 5 fires AFTER the model and AFTER labeling — it changes only the realised weighted_pnl of trades that still happen; it does NOT change trade SELECTION, labels, or Optuna's optimization landscape (unlike the /074 KILL switch). The T8 counterfactual is therefore ESSENTIALLY EXACT — a size scalar scales realised PnL linearly. The backtest should reproduce the T8 numbers up to a tiny integer-rounding interaction with the existing vol-scale. This is the honest read: T8 shows a genuine IS<->OOS tension (the SAME classifier de-rates OOS-bull-window trades the uptrend rewards), and at derate 0.50 OOS Δ -0.14 lands inside the [-0.20,+0.20] noise band — the most-likely backtest outcome is INERT-AT-EXPLORATION on the OOS axis. The de-rate grid is in T8_scoped_derate_counterfactual.csv.

## Per-symbol IS-axis discipline (T6)

The de-rate fires only for the scope symbols; BCH is outside the scope and is BIT-IDENTICAL to /060 (IS wpnl delta exactly 0). T6 verifies every symbol's IS weighted_pnl is preserved or lifted — see T6_per_symbol_is_discipline.csv `is_wpnl_delta` and `is_axis_preserves_or_lifts`. This satisfies `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: the per-symbol SCOPE is itself the IS-improving design (de-rate the drag symbols, leave the edge carrier alone).

## No look-ahead

Every IS table uses IS-window data only (open_time < OOS_CUTOFF_MS). The BTC classifier applies close.shift(1) BEFORE the rolling SMA — past-only, identical to risk_v3._build_btc_regime_lookup. Trade-regime tagging uses searchsorted 'left' minus 1 (the BTC bar strictly older than the trade entry). The axis decision (T2 window, T7 scope, T8 de-rate) is made on IS columns only; OOS columns are descriptive.

## Axes rejected at EDA stage

- **A BLANKET (all-3-symbol) bear/chop SIZE de-rate** — IS-NEGATIVE at every scalar (T3). REJECTED; replaced by the scoped variant.
- **A NEW regime-discriminating composed FEATURE** (the Critic's first suggested direction) — NOT selected. A feature changes model predictions, but (a) its trade-population effect is fuzzy to bound — the behavioral-effect predictor cannot give a clean number; (b) the engineered-feature graveyard is deep (vol_adj_autocorr, efficiency_ratio_50, hurst_drift_50_200, regime_momentum_signed_3d all NEGATIVE/PARKED); (c) single-seed engineered-feature behaviour is lottery-prone. A SCOPED SIZE scalar gives a precisely-bounded, materially-large, holding-time-orthogonal effect that PRESERVES the BCH IS edge — a strictly better fit for the Critic mandate.
