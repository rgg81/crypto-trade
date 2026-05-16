# iter-v3/076 — Axis-Selection EDA Synthesis

## QR axis decision

**Add a NEW SIGN-INVARIANT trend-efficiency feature `C2_range_efficiency_50` to V3_FEATURE_COLUMNS (15th slot) — a feature-internal IS-regime discriminator the LightGBM model learns.** The feature measures HOW price is moving (efficient directional move vs choppy grind), NOT WHICH WAY — so its value is not a monotone proxy for the bull/bear (IS/OOS) regime axis. The model can learn from it WITHIN the IS bear/chop drag without that learning systematically suppressing OOS-uptrend trades.

## How the design parameters are chosen (all IS-only or a-priori)

- **WHICH feature (PARAMETER 1)** — chosen by `_pick_feature(t2, t3)`: among candidates whose T3 `regime_sign_abs_corr` is below the a-priori 0.35 ceiling, the one with the highest T2 IS-only `is_bearchop_discrimination_auc`. Both inputs are IS-only / calendar-label-only — no OOS PnL/Sharpe/counterfactual. Chosen: `C2_range_efficiency_50`.
- **Feature window (PARAMETER 2)** — a-priori: the window of the parquet primitive the feature reuses; no SWEEP, no fit. (Reusing an existing primitive's window also means zero parquet-regen.)

NO OOS-tuning: this EDA computes no per-candidate OOS counterfactual; T3's regime indicator is the IS/OOS CALENDAR label fixed by OOS_CUTOFF_DATE, not an OOS performance metric. A repo grep of this EDA source for `oos_delta` / `oos_monthly_sharpe` / `oos_is_ratio` returns zero matches.

## Why this axis BREAKS the /075 IS-up/OOS-down tension (the Critic gate)

T1 re-derives the drag: the IS bear/chop sub-period has monthly Sharpe **-0.2193** (26.3% positive months, 77 trades, 26.0% win rate, total wpnl -6.8733).

/075 demonstrated that a post-gate BTC-trend classifier — whose value is +1 bull / -1 bear, exactly the IS/OOS regime axis — de-rates IS and OOS together (the discriminator's SIGN flips between the two windows). T3 is the EDA's pre-registered test of whether the chosen feature repeats that trap. The chosen feature `C2_range_efficiency_50` has T3 `regime_sign_abs_corr` = **0.01** (below the 0.35 ceiling: True) — its value distribution is statistically SIMILAR across the IS bear/chop window and the OOS uptrend window (standardized mean gap -0.0202). The feature is therefore NOT a directional-regime proxy: a model that learns 'this is a dangerous choppy moment' from it in IS bear/chop is not learning 'suppress the OOS uptrend', because the OOS uptrend is not uniformly tagged by the feature. This is the structural difference from the /075 macro classifier — and it is the Critic /075 Rec #3 mandate, satisfied by a committed IS-only (plus calendar-label) analysis.

## Within-IS discrimination strength (T2)

The chosen feature separates winning from losing IS-bear/chop trades with AUC **0.657** (IS-bull AUC 0.5487 — the feature is informative in the bull sub-period too, so it is not a bear-only artifact). This is the IS-only evidence the feature carries signal the model can use inside the drag regime.

## Per-symbol IS discipline (T6)

The feature is UNIVERSAL (added to V3_FEATURE_COLUMNS — all 3 symbols' models receive it). Per-symbol within-IS-bear/chop discrimination: **2 of 2** symbols-with-IS-bear/chop-trades carry signal (AUC >= 0.55). LDO has 0 IS bear/chop trades on the /060 roster (a later-listed symbol) so its per-symbol AUC is undefined — recorded n/a, NOT a FAIL; LDO's model still receives the universal feature. A universal feature that discriminates for the symbols that DO trade the drag regime preserves the IS aggregate by construction (per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — universal changes are preferred precisely because all symbols see the same logic).

## Holding-time orthogonality (T4)

A FEATURE has NO duration-extension mechanism — unlike a wider SL, a meta-label veto, or a barrier rebalance, a feature cannot widen a barrier or veto an early stop-out. The trade roster changes ONLY via the model re-learning its split structure. Predicted kept-roster mean/median duration delta ~0; falsifier at > +1.0 candle (T4).

## Behavioral-effect estimate (T5)

Informative-tail population PROXY: ~106 IS + ~68 OOS trades sit in the chosen feature's lower/upper IS-bear/chop tercile (the regions where T2 shows the feature discriminates). This is a PROXY for the roster-change scale, not an exact count — a feature is not a post-gate scalar. The brief Section 4.4 pre-registers this band; the Phase 6 backtest's actual roster delta vs /060 is the measured quantity.

## IC structure (T7 — INFORMATIONAL, Category-2 carve-out)

Max |IC| of `C2_range_efficiency_50` vs the 14 BASELINE_V3 features = **0.2061** (top: sym_vs_btc_ret_7d). Per `feedback_v3_engineered_feature_pivot.md`, IC is INFORMATIONAL for a derived feature; the binding gate is importance >= 30 in >=1 symbol's LightGBM output (Critic Check at Phase 7.5).

## Single-axis discipline

The /076 brief declares exactly TWO changes: (1) the NEW feature `C2_range_efficiency_50` added to V3_FEATURE_COLUMNS (15th slot — the single primary axis); (2) the mandatory revert of /075's Primitive 12 (`enable_regime_size_scalar` True->False, `regime_size_scalar_symbols` ->()) — a baseline-restore to the /060 state, NOT a second varied axis. Tested ALONE — no same-family stacking (`feedback_v3_engineered_features_dont_stack.md`).
