# REVIEW-004 — Critic Integrity Audit of EXPLORATION-004 (long-bias multi-factor + leg-decoupled defense)

**Reviewer:** Quant Critic (read-only). **Date:** 2026-07-09.
**Scope:** Are the R1–R5 numbers (R1 +0.511, R2 +0.263, R3 +0.362, R4 +0.235, R5 +0.336) REAL, and is
"defensive engineering works but alpha too weak" SOUND? (Persisted by orchestrator.) OOS sealed.

## OVERALL INTEGRITY VERDICT: CONDITIONAL-PASS
Numbers trustworthy in direction/magnitude. No sign bug, no look-ahead leak (9 new + 23 regression = 32/32
green), no tuning-on-result (defaults 0.7/0.3, 180d/0.20/0.30 frozen; risk-engineer calibration DEFERRED
per §7). Parity holds (R1 Δ+0.001, R2 Δ+0.003, P-RN Δ−0.001). End-to-end leak assertions on BOTH new paths
(regime scalar + leg-decoupled builder) meaningful.

**Three qualifications to the strategic interpretation:**
1. **"Multi-factor synergy failed" is partly MIS-ATTRIBUTED.** R3<R1 is real but the mechanism is averaged-IC
   + turnover cost (R3 turnover 144x vs R1 73x), NOT "no synergy exists." The brief's √2-IC lift assumed
   optimal LINEAR weighting; long-only equal-weight top-N CANNOT realize that bound. Fairer test: weighted-z
   blend (e.g. 0.7/0.3 favoring vol_low) or turnover-controlled rev_3 (hysteresis).
2. **Overlap 89.8% is structural & under-acknowledged.** Short leg effective count ~3.27 names (not 5),
   per-short weight 0.092 (53% higher than 0.06 brief table). Late-IS short-side max|w|=37%. The "diversified
   5-short band" framing is overstated — closer to "3-short concentrated band."
3. **2021 regime-gate 51% firing is REAL (not a bug).** BTC 2021 (Apr ~$64k → May–Jul ~$30k −53% → Nov ~$69k → chop)
   genuinely spent a majority of candles ≥20% off trailing-180d-peak. Loose but legitimate; 0.25–0.30 threshold
   would reduce false-positives while preserving 2022 catch.

## THE NUMBERS ARE REAL — decomposition
- **Regime scalar CLEAN:** `btc_drawdown_scalar` rolling-max over trailing window (strictly past-only);
  `test_btc_drawdown_scalar_past_only` (vacuous-guard) + `monotone_in_bear`; engine consumes `long_scalar[k-1]`
  (1-candle lag); `test_longbias_scalar_scales_longs_not_shorts` proves long-leg-only (long gross halves at
  scalar=0.5, short unchanged, per-short weights bit-identical). ✓
- **Leg-decoupled builder works, F3 eliminated:** `target_weights_longbias_ls` ranks each leg by its own signal;
  long-precedence overlap resolution. **F3 elimination lock** (`test_longbias_ls_crashed_coin_skipped_on_both_legs`):
  crashed coin (z_vol=−3,z_rev=+3,blend=0) → weight 0 on both legs; cross-checked it WOULD be shorted under /003's
  midvol_short. End-to-end no-leak load-bearing. ✓
- **R3<R1 REAL (~6–9σ):** (a) IC averaging (equal-weight blend → ~arithmetic-mean IC, not √2 synergy; rank-averaging
  loses info) ~−0.07–0.10; (b) turnover cost R3 144x×7.5bps≈10.8%/yr vs R1 73x×5.5%/yr ~−0.05–0.08; (c) selection
  shift ~−0.01–0.03. R3 maxDD −89.8% (slightly worse than R1 −87%) consistent (blend holds crash-exposed bounce names, no defense).
- **R5 +0.336/−47.8% REAL:** regime gate clipped 2022 long-loss −0.93→−0.43 (+0.50 equity rescue), short leg
  bit-identical R4→R5 (+0.5746 vs +0.5730, gate never touches shorts); net-long→net-short flip +0.403→−0.052 in 2022
  (long gross mean 0.244, short held 0.30). Sharpe recovery +0.102 (R4→R5) genuine.

## Leak-Safety: 9 new tests MEANINGFUL
gross/sign discipline; long-precedence overlap; decoupled selection; extreme-tail skip; **F3 elimination lock**;
regime-scalar past-only; monotone-in-bear; **end-to-end no-leak (load-bearing)**; long-leg-only scaling. 23 pre-existing byte-identical.
[Minor gap F4: end-to-end test pre-computes scalar then corrupts the array (not recomputed from corrupted panel inside engine);
mitigated by the direct `btc_drawdown_scalar_past_only` test. Recommend a `test_longbias_full_composition_no_leak` to close fully.]

## Findings ranked: [F1 HIGH] synergy mis-attribution | [F2 HIGH] overlap→3.27-name short concentration |
[F3 MED] 2021 over-firing (real, calibratable) | [F4 MED] end-to-end leak test composition gap | [F5 LOW] max|w|37% overlap-driven | [F6 LOW] 2024 −0.56 (gate didn't fire; still ≥−1.0).

## READ ON THE STRATEGIC CONCLUSION — **SOUND (with F1/F2 reframings)**
- **Defense WORKS:** empirically validated (maxDD −87%→−48%; 2022 −1.53→+0.32; net-long→net-short; short leg untouched by gate).
- **Alpha too WEAK:** R3<R1 (blend dilutes); R5 +0.34 < G-DEPLOY +0.60; R5×2 −0.057 (cost-fragile); R5 < EW-top-20 +0.451.
- **Calmar lens:** R1 Calmar 0.113 vs R5 0.119 — marginal; defense trades return for DD at ~1:1, no Calmar uplift.
- **Calibration ceiling ~+0.50–0.55, NOT +0.60:** regime params +0.05–0.10; gross_short +0.03–0.05; blend 0.7/0.3 → ~R1's +0.51; hysteresis +0.10–0.15. Combined ceiling ~+0.50–0.55. **The +0.60 gap is STRUCTURAL** — OHLCV-8h-cross-section long-side alpha has a hard ~+0.51 ceiling on the $-volume-ranked top-20 at 8h.

## PATH FORWARD (honest)
- **(a) Deploy R5 as baseline — NOT RECOMMENDED.** +0.336 < EW +0.451 and < R1 +0.511 (undefended). On Sharpe (track's objective) R5 is worse than R1; cost-fragile. Keep EW or vol_low-long-only as baseline.
- **(b) Pivot to SUBSTRATE — RECOMMENDED if track continues.** (1) **Weekly rebalance** (rebal 6→21): cuts 73–244x turnover ~3–4x, saves +0.10–0.15 Sharpe on every rung — cheapest, highest-ROI. (2) **OI-ranked universe** (fetch-oi available): less adverse-selected than $-volume. (3) Non-OHLCV mechanism (funding carry — but brief excludes; on-chain/taker — IC-probe first).
- **(c) Conclude — DEFENSIBLE after 4 NO-MERGE.** Coherent finding: OHLCV-8h-cross-section long-side alpha is real (~+0.26–+0.51), orthogonal, net-of-cost positive — but structurally too weak to overcome funding tax + crash DD on this universe/frequency. No blend/defense clears +0.60. Legitimate scope-break signal.
- **Recommendation: ONE substrate test (weekly rebalance first — attacks 5–18%/yr turnover drag), then OI universe if it fails, then conclude. Do NOT do more OHLCV factor engineering — the +0.51 ceiling is mapped.**
