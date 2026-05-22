# QR Response to Critic — iter-v3/119 Round-1 PRELIMINARY

**Date**: 2026-05-20
**Branch**: iteration-v3/119
**Critic PRELIMINARY**: `briefs-v3/iteration_v3-119/review_preliminary.md` — leaning EXPLORATION-PROMISING with 5 substantive clarifications.

The Critic's central concern is structural: importance-rank-15/15 + OOS-Δ-+0.70 produces an inversion against /118 (rank 6/15 + IS −0.45 catastrophic). The Critic asks whether C6 is feature-SIGNAL (direct edge ingredient) or feature-MECHANICAL (loss-surface reorganizer of the kind /116 represents at the rule-layer). The QR's full read of the /060 vs /119 anchor importance files settles this question.

This response references ONLY committed artifacts: `reports-v3/iteration_v3-060/in_sample/model_importance_last_month_portfolio.csv`, `reports-v3/iteration_v3-119/in_sample/model_importance_last_month_portfolio.csv`, `reports-v3/iteration_v3-118/in_sample/model_importance_last_month_portfolio.csv`, `reports-v3/iteration_v3-119/comparison.csv`, the iter-v3/119 engineering report Section 6 + 11, and the iter-v3/116 diary. No new EDA, no new backtest.

---

## Clarification 1 — Importance-15/15 vs Sharpe-+0.70 paradox: feature-SIGNAL or feature-MECHANICAL?

**Row-by-row comparison of /060 (14 features) vs /119 (14 anchor features + C6 as 15th), last IS training month, portfolio aggregate:**

| Feature | /060 rank | /060 imp | /119 rank | /119 imp | Δ rank | Δ imp % |
|---|---:|---:|---:|---:|---:|---:|
| ret_skew_200 | 1 | 816.33 | 2 | 524.00 | +1 | -35.8% |
| vwap_dev_20 | 2 | 759.67 | 5 | 487.67 | +3 | -35.8% |
| range_realized_vol_50 | 3 | 706.33 | 4 | 503.00 | +1 | -28.8% |
| ema_spread_atr_20 | 4 | 698.67 | 7 | 402.00 | +3 | -42.5% |
| max_dd_window_50 | 5 | 646.33 | 1 | 551.00 | **-4** | -14.7% |
| ret_autocorr_lag1_50 | 6 | 607.00 | 11 | 352.00 | **+5** | -42.0% |
| ret_kurt_50 | 7 | 598.00 | 3 | 509.33 | **-4** | -14.8% |
| hurst_diff_100_50 | 8 | 593.33 | 6 | 422.33 | -2 | -28.8% |
| ret_kurt_200 | 9 | 582.00 | 10 | 360.67 | +1 | -38.0% |
| btc_ret_14d | 10 | 582.00 | 12 | 328.33 | +2 | -43.6% |
| hurst_100 | 11 | 569.33 | 8 | 389.67 | -3 | -31.6% |
| ret_skew_50 | 12 | 520.33 | 9 | 369.33 | -3 | -29.0% |
| sym_vs_btc_ret_7d | 13 | 511.67 | 13 | 319.67 | **0** | -37.5% |
| **regime_momentum_signed_5d** | **14** | **506.67** | **14** | **175.67** | **0** | **-65.3%** |
| ret5d_signed_tbi (NEW) | — | — | 15 | 153.00 | — | — |

**Diagnostic statistics:**

- **Spearman rank correlation /060 ↔ /119 (14 anchor features)**: ρ = **0.7714** — moderate-high preservation. NOT a chaotic shuffle.
- **Mean absolute rank shift per anchor feature**: 2.29 / 14 ranks.
- **Top-5 set preservation**: 4/5 (ret_skew_200, vwap_dev_20, range_realized_vol_50, max_dd_window_50 preserved; ret_kurt_50 enters top-5, ema_spread_atr_20 drops out).
- **Total importance allocation /060 → /119**: 8697.67 → 5847.67 (anchor-only 5694.67); the model receives ~35% less total split-count budget despite having one more feature. This is the LightGBM split-count budget at fixed `n_estimators` × `colsample_bytree` × `max_depth`. The total reduction is structurally expected when a new highly-correlated feature competes for the same splits — it dilutes per-feature split count without changing decision-boundary capacity.
- **C6's share of /119 total**: 153.0 / 5847.67 = **2.6%**.

### The smoking gun — regime_momentum_signed_5d cratered −65.3%

C6's IC-0.72 algebraic sister `regime_momentum_signed_5d` (which shares the `ret_5d` value primitive) lost **65.3% of its importance** — the largest single-feature decline by an order of magnitude. C6 absorbed `regime_momentum_signed_5d`'s allocation almost exactly: 506.67 (/060 sister importance) → 175.67 (/119 sister) + 153.00 (C6) = **328.67 combined**, compared to /060's 506.67 alone. **Net combined allocation to the "ret_5d × regime-sign" sister family DROPPED 35.1%** (from 506.67 to 328.67), and that 35.1% lost-allocation is redistributed to the OTHER 13 anchor features (every one of which sees a -14% to -44% importance drop — but their RANK ordering moves only modestly: Spearman ρ = 0.77 vs the "if every anchor were identically scaled" null of ρ=1.0).

### Interpretation — Mixed: NEITHER pure feature-SIGNAL NOR pure feature-MECHANICAL

The Critic's framing (feature-SIGNAL = anchors unchanged + C6 adds new allocation; feature-MECHANICAL = anchors shuffle + C6 enables existing features to fit) is the right axis but the data falls **between** the two endpoints:

**Evidence FOR feature-SIGNAL (direct edge contribution):**
1. Spearman ρ = 0.77 — anchor RANKS are mostly preserved (not the chaotic shuffle a loss-surface reorganizer would produce). A pure mechanical reorganizer would produce ρ closer to 0.3–0.5.
2. Top-5 set 4/5 preserved — the model is still finding the same dominant signals.
3. All three symbols produce positive IS PnL Δ (BCH +4.57, LDO +18.75, TRX +37.63) — the broad-based-cascade signature the engineering report's Section 11 documents. Pure mechanical reorganizers tend to produce single-symbol carrier outcomes (like /118).
4. The /116 PROMISING-MECHANICAL signature is at the RULE layer (book-composition via slot-freeing cascade — observable bar-by-bar in October 2025 attribution). C6 has no rule-layer mechanism; it's only a column added to the feature matrix.

**Evidence FOR feature-MECHANICAL (loss-surface reorganization):**
1. Total importance budget collapsed ~35% — the tree ensemble re-allocates split count widely, not just at the C6 slot.
2. `regime_momentum_signed_5d` (C6's IC=−0.72 algebraic sister) drops 65% of its importance. The C6+sister combined allocation NET DECREASES by 35% (506→328). C6 is not ADDING signal capacity to the ret_5d×regime-sign family — it is REPLACING regime_momentum_signed_5d at a lower combined budget.
3. The combined "saved" allocation of 178 split-counts (506−328) is distributed to OTHER anchor features (notice `max_dd_window_50`, `ret_kurt_50`, `hurst_100`, `ret_skew_50` all RISE in rank — those are the four features that rank-rise in /119 vs /060). The model is using C6+regime_momentum LESS and using these four other features RELATIVELY MORE.
4. The 13.7% importance lift the Critic cited for `vwap_dev_20` actually shows the opposite direction in absolute terms: vwap_dev_20 DROPS 35.8% in absolute importance (759→487) but only +3 in rank — its relative weight increases vs the lower-ranked features but its absolute split count falls. The reorganization is real, not just nominal.

### Verdict

**C6 is BOTH feature-SIGNAL (low-but-nonzero direct contribution) AND feature-MECHANICAL (loss-surface reorganizer that redistributes split budget away from regime_momentum_signed_5d and toward the four other anchor features that rank-rise).**

The DOMINANT effect, however, is feature-MECHANICAL: C6's NEW allocation (153) is smaller than the allocation it cannibalizes from its sister regime_momentum_signed_5d (506→175, a −331 drop). The "new signal" channel cannot account for the +0.70 OOS Sharpe lift — 153 / 5847 = 2.6% of the model's split budget cannot mechanistically produce a 5.0× lift in OOS monthly Sharpe (0.14 → 0.84) as a direct-edge effect. The lift is more parsimoniously attributed to the loss-surface reorganization elevating max_dd_window_50, ret_kurt_50, hurst_100, ret_skew_50 (the four rank-rising anchors), with C6 acting as the catalyst.

This is structurally NEW in the v3 catalog and warrants a sister-subtype designation: **PROMISING-FEATURE-MECHANICAL** (FEATURE-form sister to /116's RULE-form PROMISING-MECHANICAL). The mechanism — loss-surface reorganization via algebraic-sister redistribution — is mechanistically distinct from /116's slot-freeing cascade but shares the load-bearing property: **the new primitive is non-compoundable as a SIGNAL source because its mechanism is allocation redistribution rather than new edge information**.

**One-line answer: feature-MECHANICAL dominant (with low-but-nonzero direct signal component); classify as PROMISING-FEATURE-MECHANICAL (sister-subtype to /116).**

---

## Clarification 2 — Mode 6 knife-edge: daily-Sharpe vs monthly-Sharpe reconciliation

The Mode 6 falsifier was pre-registered in the brief at **monthly Sharpe** scale (OOS Δ > +0.30 AND IS Δ < +0.05). Observed: OOS Δ = +0.7017, IS Δ = +0.1167 — Mode 6 IS-leg misses by 0.067 Sharpe units.

**Daily Sharpe view**: IS 1.7386 → OOS 2.3234 = 1.34× ratio (healthy).
**Monthly Sharpe view**: IS 0.8492 → OOS 0.8420 = 0.99× ratio (essentially equal IS/OOS).

These two views measure the SAME dataset but at different aggregation cadences. The daily view treats each daily PnL as a sample; the monthly view aggregates within-month before computing the Sharpe ratio. For a strategy with autocorrelated daily returns (which crypto strategies typically are at 8h cadence — trade-rate ~5/month implies many daily PnL = 0 days), the monthly Sharpe is the noise-floor-adjusted view. Monthly aggregation smooths out the daily-Sharpe's denominator noise from sparse-trade days.

**Canonical for /119 classification**: **monthly Sharpe** — both because (a) the brief Section 7 Mode 6 falsifier was pre-registered at monthly scale, and (b) the cycle-1 axis-PASS criteria (`feedback_v3_cycle1_axis_pass_criteria.md`) and BASELINE_V3.md use monthly Sharpe as canonical. Daily Sharpe is INFORMATIONAL; cannot be used to reclassify Mode 6 post-hoc.

That said, the OOS Δ = +0.7017 in monthly Sharpe represents a 5.0× lift in OOS monthly Sharpe (0.14 → 0.84) — this is far above the modal upper bound (+0.25). Mode 6 misses by 0.067 IS Sharpe units because IS Sharpe LIFTED +0.1167 (above the +0.05 threshold) — Mode 6's IS-leg is calibrated to detect the catastrophic case where IS doesn't move but OOS spikes (lottery-style). /119's IS-leg shows REAL IS movement (broad-based +PnL on all 3 symbols documented in engineering report Section 4) — this is the SUSPICIOUS-OOS-DOMINANT exclusion criterion as designed. **Mode 6 correctly does not fire.**

**However**, the OOS Δ being 2.8× the modal upper bound is a structural anomaly that warrants pre-committed multi-seed validation gates at /120 CONFIRMATION. The /118 Critic-protocol established that when the EXPLORATION-mode result substantially exceeds modal predictions, multi-seed validation should pre-register tighter falsifier bands. I will commit those at /120.

**One-line answer**: Monthly Sharpe is canonical (matches brief pre-registration). Mode 6 correctly does NOT fire because IS Δ = +0.1167 (above the +0.05 threshold) — IS-side shows real broad-based movement, not a no-IS-movement lottery signature.

---

## Clarification 3 — /116 PROMISING-MECHANICAL precedent: feature-form analog?

Per `feedback_promising_mechanical_subtype.md` and the iter-v3/116 diary, PROMISING-MECHANICAL is defined by: (a) mechanism is mechanical rearrangement (book-composition, slot-freeing, allocation redistribution) rather than new edge information; (b) Sharpe lift is real and broad-based per-symbol; (c) **non-compoundable as a SIGNAL source** — only ONE mechanical primitive of a given mechanism class can be active at a time.

iter-v3/116 represents the RULE-form: an exit rule that frees symbol slots, triggering a cascade of new entries. The mechanism is at the trade-construction layer (book composition).

iter-v3/119 represents what the QR analysis above identifies as the FEATURE-form: a new feature column that redistributes the LightGBM ensemble's split budget away from an algebraic sister and toward four other anchor features. The mechanism is at the feature-importance layer (loss-surface reorganization).

**These mechanisms are STRUCTURALLY DIFFERENT** — /116 modifies what trades are kept; /119 modifies what features the model weights — and in principle they ARE orthogonal (one is rule-layer, one is feature-layer; they can coexist mechanically without overlapping mechanism class).

**However**, both are mechanistic-rearrangement mechanisms, NOT new edge ingredients. The PROMISING-MECHANICAL subtype's core invariant is that such primitives are **strictly-accretive component decisions on /059, NOT new edge ingredients**. By that invariant:

- A two-component bundle of (/116 no_confirm) + (C6) at /120 would be a bundle of TWO mechanical primitives, both of which are individually strictly-accretive on /059.
- Per `feedback_promising_mechanical_subtype.md` invariant: "non-compoundable as a SIGNAL source" — this refers to the property that mechanical primitives cannot be expected to STACK as if they were independent edge ingredients. Two mechanical primitives that each contribute +0.7 OOS individually do NOT contribute +1.4 OOS combined; the cascade-attribution falsifier the iter-v3/116 diary documented (the 11 new OOS entries traceable to slot-freeing) is the diagnostic.
- The two mechanisms (slot-freeing rule + algebraic-sister-redistribution feature) are at different layers and could in principle be NEAR-orthogonal — but the EDA evidence does NOT bound the interaction at single-seed EXPLORATION mode.

**Classification recommendation**: /119 → **PROMISING-FEATURE-MECHANICAL** (NEW sister-subtype to /116's RULE-form PROMISING-MECHANICAL). Both are non-compoundable as signal sources but ARE potentially orthogonal at the mechanism-layer level (rule-vs-feature). Pre-registration for /120 should treat them as separate accretion decisions, NOT as additive edge ingredients.

**One-line answer**: /119 IS the feature-form analog of /116 — classify as PROMISING-FEATURE-MECHANICAL (sister-subtype to /116). Non-compoundable as signal source. Mechanisms differ enough (rule-layer vs feature-layer) that they can in principle coexist as separate accretion decisions in a two-component bundle.

---

## Clarification 4 — TRX OOS concentration 80% (or 52% of positive PnL even after sign-divergence correction): pre-committed falsifier?

**Re-stating the data:**
- Raw `concentration_pct` in `comparison.csv`: BCH 43.89%, LDO −24.03%, TRX 80.14% (numerator is per-symbol weighted_pnl; denominator is portfolio weighted_pnl total = 55.08).
- Sign-divergence corrected (TRX + BCH share of positive PnL total 65.11): TRX 52.05%, BCH 47.95%. The two positive carriers are nearly equally weighted.

**Comparison to /116 OOS** (BCH +31.55, TRX +16.04, LDO +12.00, all positive): BCH 52.9%, TRX 26.9%, LDO 20.1% of positive total. **/116 had three positive carriers; /119 has two positive carriers** (LDO is −10.03 = drag). /119 is materially more concentrated than /116 even after sign-correction.

**Pre-committed falsifier for /120 CONFIRMATION 10-seed (committed here as the QR-binding pre-registration):**

> **Falsifier Gate for /120 — TRX-concentration**: at /120 CONFIRMATION (10-seed unified ensemble), if **TRX multi-seed mean OOS weighted PnL share > 50% of the positive-symbol total**, the /119 C6 component is BLOCKED from bundle inclusion. Threshold rationale: the /116 PROMISING-MECHANICAL bar was a single positive carrier ≤53% of positive total — /119 at single-seed already shows TRX 52% of positive total, exactly at the threshold. The /120 10-seed multi-seed mean must NOT exceed this baseline. If the multi-seed mean shows TRX 50-65% of positive total, the SUBORDINATE falsifier triggers (concentration-watch flag, but not auto-BLOCK); if TRX > 65% of positive total, full BLOCK fires.

Additionally:
- **Single-symbol carrier signature**: at multi-seed, if ANY ONE symbol is > 65% of positive total, BLOCK. This generalizes the /118-style single-carrier failure mode.
- **Net-PnL-positive minimum**: all three symbols must show non-catastrophic OOS PnL at multi-seed mean (no single symbol > −15% portfolio share OOS PnL). The /119 LDO at −18.22% portfolio share is borderline; at /120 multi-seed if LDO worsens beyond −25% portfolio share, the bundle is flagged.

**One-line answer**: Pre-committed falsifier: at /120 multi-seed, if TRX OOS weighted PnL share > 50% of positive-symbol total → BLOCK C6 inclusion. If 50-65% → concentration-watch flag. > 65% → full BLOCK.

---

## Clarification 5 — /120 bundling adjudication: (a) TWO-COMPONENT /116+C6, (b) SINGLE-COMPONENT, (c) deferred /119

Given the Clarification-1 verdict (C6 = PROMISING-FEATURE-MECHANICAL, feature-form analog of /116, dominant mechanism is allocation redistribution rather than new edge):

**Recommendation: (a) TWO-COMPONENT /116+C6 bundle at /120 CONFIRMATION, with both treated as mechanical accretion decisions (NOT additive edge ingredients), and with multi-seed validation falsifiers pre-committed.**

**Rationale:**

1. The mechanisms are at DIFFERENT layers: /116 no_confirm is rule-layer (book composition); /119 C6 is feature-layer (split-budget redistribution). They are not the SAME mechanism class — the "non-compoundable as SIGNAL source" invariant of PROMISING-MECHANICAL applies WITHIN a mechanism class. Two mechanical primitives at different mechanism layers CAN coexist as separate strictly-accretive component decisions.

2. Both /116 and /119 individually show broad-based OOS lift on multiple symbols at single-seed EXPLORATION. The /120 CONFIRMATION 10-seed validation is the ONLY way to determine whether they STACK linearly or interact (positively or negatively). Deferring /119 to a separate post-/120 validation would (i) require an additional 6h CONFIRMATION run that the cycle-6 cadence doesn't budget for, and (ii) miss the opportunity to test stacking under the only multi-seed run available.

3. The single-component options (b) leave evidence on the table. Picking /116 alone leaves C6 untested at multi-seed; picking C6 alone leaves /116 untested at multi-seed. Either way the cycle-6 closes without resolving the multi-seed status of the iteration that produced the lift.

4. The 10-seed CONFIRMATION already pre-registers multi-seed Pareto + DSR + PSR + PBO gates that would catch a non-stacking interaction (Mode 6 SUSPICIOUS-OOS-DOMINANT, single-symbol carrier inflation, etc.).

**Pre-committed falsifiers for /120 TWO-COMPONENT bundle:**

> **Falsifier 1 — Stacking-linearity check**: at /120 multi-seed, if the /116+C6 bundle OOS monthly Sharpe is LOWER than the LARGER of (/116-only multi-seed OOS Sharpe, C6-only multi-seed OOS Sharpe) by more than 0.10 Sharpe units, the bundle is NEGATIVE-no-stacking and one component must be DROPPED for /120 MERGE. Determining which component is dropped: revert to /116-only (the RULE-layer mechanism with bar-by-bar attributable mechanism documentation from cycle-6 diary).
> **Falsifier 2 — TRX-concentration**: per Clarification 4, TRX OOS PnL share > 50% of positive total → BLOCK C6 inclusion (keep /116 alone).
> **Falsifier 3 — Sister-redistribution stability**: at /120 multi-seed, if `regime_momentum_signed_5d` importance falls by > 50% in mean (vs /060 anchor) AND `ret5d_signed_tbi` importance fails to exceed 5% of portfolio total importance, the C6 mechanism is "allocation cannibal without contribution" — BLOCK C6 inclusion.

**Does Clarification 1's feature-MECHANICAL ruling change the answer?**
- It SHARPENS the answer: C6 is NOT a new edge ingredient — it is a mechanical accretion primitive at the feature layer. This makes the /120 bundle a TWO-MECHANICAL bundle (not a mechanical + signal bundle). The bundle is still valid because the mechanisms are at different layers (rule vs feature), but the cycle-6 closes with **ZERO new EDGE ingredients added to v3** since /058 — only mechanical primitives that are strictly-accretive on /059. This is a cycle-6 cumulative finding worth recording in the diary: **cycle 6 produced 2 mechanical primitives and 8 NEGATIVE/NULL; no new signal-edge ingredient was found in 10 EXPLORATIONs.**

**One-line answer**: (a) TWO-COMPONENT /116+C6 at /120 CONFIRMATION, with both treated as mechanical accretion decisions; three falsifiers pre-committed (stacking-linearity, TRX-concentration, sister-redistribution stability). The Clarification-1 feature-MECHANICAL ruling does NOT change the answer (mechanisms are at different layers), but it RECLASSIFIES the cycle-6 closure as "zero new edge ingredients found; two strictly-accretive mechanical primitives."

---

## Position

**STAND BY VERDICT** with sub-classification refinement: I accept the Critic's PROMISING direction and request the verdict be filed as **EXPLORATION-PROMISING — PROMISING-FEATURE-MECHANICAL subclass** (new sister-subtype to /116's PROMISING-MECHANICAL, feature-layer analog of /116's rule-layer mechanism). The strict-PROMISING classification (direct edge ingredient) is NOT supported by the importance evidence: C6 cannibalizes 65% of regime_momentum_signed_5d's allocation, net combined sister-family allocation drops 35%, and 153 / 5847 = 2.6% of split budget cannot mechanistically produce a 5.0× OOS monthly Sharpe lift as direct edge — the lift is more parsimoniously attributed to loss-surface reorganization elevating four other anchor features (max_dd_window_50, ret_kurt_50, hurst_100, ret_skew_50).

The bundle decision and TRX-concentration falsifier are pre-committed above. Cycle 6 closes with 2 PROMISING-MECHANICAL primitives (/116 RULE-form + /119 FEATURE-form) advancing to /120 CONFIRMATION; ZERO new edge ingredients found in 10 EXPLORATIONs.
