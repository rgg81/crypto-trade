# Phase 7.5 Critic Review — iter-v1/030 (ETHUSDT)

OVERALL: EXPLORATION-NEGATIVE — IS Sharpe −0.0866 < 0 fails the both-positive PRIMARY gate; pre-registered
K2 fires (IS regressed −0.72 below iter-027 +0.6336). NOT a bug: the IS inversion is a genuine
entry-selection regularization effect, independently confirmed against the decision log.

## Bug-vs-Real Determination (load-bearing): REAL — not a wiring defect
The hypothesized pathology (per-month q=0.40 quantile collapsing to ~0 on the zero-inflated modulated
series, admitting near-zero-conviction trades) is EMPIRICALLY FALSIFIED:
- Threshold-build (lgbm.py L1986-1990): `np.isfinite` filter keeps agreement=0 rows as finite 0.0, so
  zero-inflation is structurally possible — the right place to look.
- BUT realized per-month `trend_strength_thr` ranges **~2.18-2.82** across all months (decision_log.jsonl)
  — healthy positive thresholds, never near 0. Full agreement=0 requires all 3 P3 members to disagree
  with the SMA200 anchor simultaneously (rare: family disagrees with anchor on only ~22.6% of rows at
  all; unanimous 3-way disagreement far rarer), so the zero-mass never exceeds 40% of any 24-month
  training window and q=0.40 stays in the positive part of the distribution.
- The gate SKIPS near-zero-conviction rows (OOS 2025-05 skips strength 0.28/0.37 vs thr 1.98) — the
  OPPOSITE of the hypothesized pathology.
- Look-ahead clean (9-test suite, append-future-candles 1e-12 on slowest binding member); byte-identity
  to iter-027 direction proven; crash-fix (L12388 universe guard) is post-report so headline metrics valid.
- Conclusion: AGREE_SCALE is mechanically sound. No fix-and-re-run warranted.

## Verdict Check — EXPLORATION-NEGATIVE confirmed
- Both-positive PRIMARY gate fails (IS −0.0866 < 0 is a hard fail under the generalization-first gate).
- K2 fires (pre-registered): IS regressed >0.05 below iter-027. K3 likely (recent-edge); F4/K4 PASS
  (79 IS / 29 OOS ≈ iter-027 82/32 → behaved as a modulator, not a hard veto).
- The strong OOS +0.2372 must NOT be chased (IS−/OOS+ is inverse-overfit, not a generalizing edge).
- iter-027 (IS +0.6336/OOS +0.0560) REMAINS BASELINE_V1_ETHUSDT.

## Forensic Assessment — QR explanation sound, sharpened
- The EDA-proxy-vs-backtest gap fully explains the −0.65 IS miss: the EDA (blend_agreement.csv) holds
  n=3291 CONSTANT (re-derives the gate threshold on the modulated series so 60% always clears,
  regardless of modulation) and measures "re-ranking ALL-gated candles by agreement." The backtest only
  trades LightGBM-SIGNALED candles with a per-MONTH (not per-period) threshold. AGREE_SCALE re-ranks
  which of the MODEL's entries clear the per-month gate; the model's IS-winning entries cluster in
  lower-agreement (chop) regimes → shrunk below the gate → dropped → IS inverts. The proxy could not
  see this (never modeled entry selection). Adequate; no residual unexplained gap.
- SHARPENING: this is the SECOND independent signal that the ETH model's ENTRY SELECTION is overfit
  (iter-028/029 M2 lottery-collapse + iter-030 de-correlating-from-entry-conviction helps OOS). This is
  the most actionable finding and should anchor the next axis. The de-concentration mechanism is partly
  vindicated (OOS top-2 438%→139%, MaxDD 19%→4.6%); the problem is purely the IS-sign cost.

## Per-Check Status
Check 1 Look-Ahead: PASS. Check 2 Embargo: PASS (inherited). Check 3 Multiple-testing: INFORMATIONAL
(EXPLORATION; DSR −68 is mode artifact). Check 6 Single-Axis/Pareto: PASS (only
_spec_enable_agreement_scale differs from /027). Check 7 Reproducibility: PASS (committed; headline
metrics valid pre-crash). Check 8 Hypothesis-Implementation: PASS (AGREE_SCALE modulator, panel math
matches committed primitives). Check 14 Axis Family: PASS (labeling/conviction; rotation VALID).

## Recommendations to QR (process)
1. EDA proxies that hold n constant are blind to the model's entry-selection layer; for entry-conviction
   axes, the IS proxy must trade only model-signaled candles + per-month threshold or it mis-predicts the
   sign. Pre-register this proxy-fidelity caveat.
2. Two iterations now point at overfit ENTRY SELECTION as the ETH root cause. Next axis should either
   de-concentrate WITHOUT touching entry selection (exit-side) or regularize the entry layer in an
   IS-preserving way. Stop attacking entry conviction from the chop-regime angle — it inverts IS.
3. The de-concentration primitive (multi-speed agreement) is validated; carry it forward as a composable
   component for a future config that de-concentrates without the IS hit. Do not discard it.

## Path Forward (mandatory — 3 de-concentration axes from different families, IS-inversion-safe)
Closed/tried: meta-labeling M2 veto (iter-028/029, model-arch, K=20 lottery-collapse); entry-side
conviction modulation by multi-speed agreement (iter-030, labeling/conviction, IS-inverting). Both
attack ENTRY supply.

1. **[TOP] EXIT-side scale-out / partial-profit ladder — family: execution/exit-primitive.** Keep
   iter-027 entries/direction/conviction gate BYTE-IDENTICAL. Convert each 14d let-winners-run capture
   into 2-3 realized sub-trades (e.g. realize ⅓ at +1.5 ATR, ⅓ at +3 ATR, rest to 14d timeout). Avoids
   the IS-inversion trap: does NOT change which candles enter or the direction → IS-winning entries fully
   preserved → IS sign cannot flip. De-concentration comes from splitting the few big trades' realized
   PnL across more rows (directly attacks the 438% top-2). IS-only test: simulate the ladder on iter-027's
   realized IS trade roster (entry/exit known + intra-trade OHLCV), measure top-1/top-2 share + per-trade
   Sharpe vs single-exit baseline; pre-register net Σ stays within −0.05 Sharpe of iter-027 IS.
2. **Entry-layer regularization via ensemble-disagreement abstention — family: model-arch
   (entry-confidence, NOT veto).** Require K-of-N bagging seeds to agree on direction before firing;
   abstain only where the ensemble is internally split (model uncertainty), NOT a chop-regime agreement
   score. Removes genuinely-uncertain entries (poor in BOTH IS and OOS) rather than IS-profitable chop
   entries → should de-concentrate while preserving/improving IS. IS-only test: bucket iter-027 IS trades
   by ensemble_std (already logged), measure IS per-trade Sharpe + top-2 vs an abstention threshold;
   pre-register the threshold must lift IS Sharpe (not just OOS) and lower top-2.
3. **Per-trade vol-target exposure CEILING — family: risk-primitive (exposure ceiling, NOT proportional
   scaling).** Cap any single trade's weight at the IS-calibrated p80 of historical trade weights.
   Modulates SIZE never WHICH candles enter → IS sign preserved; trims the tail-weight producing the
   438% concentration. (NB v3 lesson feedback_v3_concentration_is_signal: proportional per-symbol
   scaling failed there; this is a single-symbol exposure CEILING, which that finding explicitly permits.)
   IS-only test: apply the p80 cap to iter-027's realized IS roster, measure top-2 + IS Sharpe;
   pre-register IS Sharpe must not regress >0.05 and top-2 must drop below iter-027 IS.

All three are from families NOT used in the prior 5 ETH iterations and are testable IS-only on iter-027's
already-realized roster — which structurally cannot invert IS the way the chop-regime AGREE_SCALE did.
