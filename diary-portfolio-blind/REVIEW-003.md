# REVIEW-003 — Critic Integrity Audit of EXPLORATION-003 (multi-factor rev_3 z-blend)

**Reviewer:** Quant Critic (read-only). **Date:** 2026-07-09.
**Scope:** Result INTEGRITY — specifically: **are rev_3-only's −0.65 and the blend's −0.36 REAL
(turnover/partition cost) or ARTIFACT (z-scoring/sign bug)?** (Persisted by orchestrator.)

## OVERALL INTEGRITY VERDICT: CONDITIONAL-PASS
Numbers trustworthy in direction and magnitude. No sign bug, no look-ahead leak, no double-count,
no tuning-on-result. **The −0.65 and −0.36 are REAL.** ~6–9σ gaps (not noise).

**HOWEVER — the strategic interpretation is PARTLY OVER-ATTRIBUTED.** "OHLCV cross-section too weak"
undersates the dominant cause of rev_3's −0.65: **partition/signal mismatch**. `midvol_short` was
designed for vol_low (skip extreme-vol mooners); applied to rev_3 it skips exactly the names rev_3
wants to short (biggest recent winners = the mean-reversion alpha source). rev_3's IC was never
harvestable through this partition regardless of cost/OHLCV strength. See [F1].

## THE CRITICAL FINDING — Are −0.65 / −0.36 REAL or ARTIFACT? **REAL.**
Decomposed: ~1/3 turnover cost + ~1/2 partition mismatch + ~1/6 long-leg adverse selection.
**(1) Z-scoring CLEAN.** `_cs_zscore_2d` (blind_signals.py:49–71) = per-timestamp cross-sectional
mean/std over `univ & finite` only — no time-series/cross-sectional future. Mirrors `row_ic` scope.
`test_cs_zscore_past_only` is meaningful (corrupts arr AND univ; vacuous-test guard). End-to-end
`test_blended_signal_no_future_leak` corrupts panel → past weights/turnover/equity bit-identical. ✓
**(2) rev_3-only's −0.65: NOT a sign bug.** Both signals are "high=want-long" (lowvol=-rv;
rev3=-pct_change(3) → recent loser → positive → long). ONE builder applies ONE rule → sign
inconsistency mechanically impossible; locked by partition + tail-skip tests. rev3 formula
byte-identical to IC-probe (`blind_signal_ic_probe.py:116`). Decomposition:
  - (a) **Partition/signal mismatch (DOMINANT, ~−0.4 to −0.5):** midvol_short skips bottom-5; for
    rev_3 that = biggest recent WINNERS = exactly where IC says LOW forward return (the short alpha).
    Partition refuses to short them.
  - (b) **Turnover cost (~−0.2 to −0.3):** 230x×7.5bps≈17.25%/yr vs vol_low 10.35%/yr.
  - (c) **Long-leg adverse selection (~−0.0 to −0.1):** longs biggest losers = post-crash still-falling.
Per-leg P&L confirms: blended long +1.40 (pos 4/6 yrs), short −1.10 (neg 4/6 yrs, only 2022 +0.90) —
short leg is the drag, assigned to mid-band NEUTRAL rev_3 names with no IC edge. Consistent with
partition mismatch, not a sign bug. **2x-cost stress confirms (b) without contradicting (a):** rev_3
@2x −1.29 (Δ−0.636) vs vol_low @2x −0.29 (Δ−0.376); incremental cost sensitivity ~−0.26 ≈ one-third
of the −0.74 base gap; remaining ~0.48 is STRUCTURAL (partition + adverse selection).
**(3) Blend −0.36:** ≈ midpoint of +0.09 and −0.65 weighted by net-of-cost realizations; rev_3's drag
~3× vol_low's contribution → lands closer to rev_3. Mathematically consistent; no extra artifact.
**(4) Orthogonality −0.036:** correctly computed (per-timestamp Spearman over univ&finite, min_n=10);
within tolerance of probe's −0.006 (Δ0.030<0.05; sub-sampling effect). **Orthogonality HOLDS → failure
is downstream (partition conversion), NOT correlation breakdown.**

## Per-Area Findings (ranked)
### [F1 — HIGH] Interpretation over-reaches: "OHLCV too weak" understates partition mismatch
rev_3's IC +0.045 IS REAL & STABLE (formula reproduces byte-identically). Its conversion failure is
dominated by partition/signal mismatch, not OHLCV weakness. **Failure scenario:** if QR accepts
"OHLCV too weak" and pivots to OI-universe or different mechanism, the SAME mismatch recurs for any
signal whose alpha sits in names midvol_short skips. **Fix (informational):** Phase-7 framing should
read "rev_3's IC real but unconvertible through midvol_short's skip-tail," not "OHLCV weak."
### [F2 — MEDIUM] rev_3's IC conversion UNTESTED in a compatible partition — the decisive gap
No run of rev_3 through `rank_neutral` (shorts bottom-5 instead of skipping) or `longonly_tophalf`
(long-side bounce only). Cannot distinguish:
  - **H1:** IC real & harvestable; midvol_short cripples it via skip-band misalignment → partition-specific.
  - **H2:** IC real but unharvestable at 8h on this universe regardless of partition → signal-specific.
These point to OPPOSITE next iterations (partition change vs scope break). Data = one ~5-min run not done.
### [F3 — MEDIUM/LOW] Blend introduces a NEW failure mode (crashed-coin-into-short) not fully decomposed
Blend assigns short-band positions NEITHER parent makes (crashed coins: low vol_low, high rev_3 →
blended z≈0 → SHORT). Short-leg −1.10 loss not split into "neutral-mid-band shorts" vs "crashed-coin
shorts." Next iteration should classify short-band names by (z_vol,z_rev) quadrant.
### [F4 — LOW] Funding-by-leg not split (only net). Would sharpen rev_3's diagnosis.
### [F5 — LOW] Realized corr −0.036 is 5× more negative than probe's −0.006 (within tolerance); mildly substitutive in bear → may amplify disagreement-case risk.
### [F6 — LOW] Warmup-edge max|w|≈0.50 at k<63 (same artifact as /001,/002; masked).

## Leak-Safety: 5 new tests MEANINGFUL (not tautologies)
1. `test_rev3_signal_past_only` ✓ 2. `test_cs_zscore_past_only` (vacuous-guard) ✓
3. **`test_blended_signal_no_future_leak` — LOAD-BEARING end-to-end** (corrupt panel → past bit-identical through full run_backtest) ✓
4. `test_blended_skips_agreement_outlier` ✓ 5. `test_blended_crashed_coin_lands_short` (disagreement case; cross-checks vol_low-only) ✓
No new engine path (signal-only); 18 pre-existing byte-identical. 23/23 green.

## Cost / Apples-to-Apples / Pre-Reg / Stats
5+2.5bps fair. 2x-cost = strongest evidence for F1 (cost is only ~1/3 of rev_3's gap). Apples-to-apples:
vol_low +0.088≈+0.09, ew +0.45, long-only +0.51 all reproduce. Brief FROZEN; 0.5/0.5 parameter-free;
no scan. Predictions wrong but pre-registered → informative. Gaps ~6–9σ (not noise). 2021 prediction
correct in direction (rev_3 helped mania +0.48 vs vol_low −0.38); disagreement-case fired in 2023/2024
not 2021.

## Path Forward — DO NOT commit to scope break before resolving H1 vs H2
1. **[HIGHEST — resolves F2] Re-test rev_3 through `rank_neutral` (no skip-tail)** [partition-axis, NOT
   a new feature]. ~5 min. If rev_3 turns positive (~+0.2–0.4) → H1: IC harvestable, failure was
   midvol_short-specific → next = partition redesign, NOT scope break. If stays negative → H2: "OHLCV
   too weak" validated → scope break justified. **Single highest-information next step.**
2. [HIGH] Turnover-reduction/hysteresis (REVIEW-002 S1) — lifts vol_low +0.09 by ~+0.1–0.2; won't
   rescue rev_3 (its problem is partition, not cost).
3. [MEDIUM, IF H2] OI-ranked universe (fetch-oi available; less adverse-selected).
4. [MEDIUM, IF H2] Different MECHANISM family (non-OHLCV: funding carry, on-chain, taker-flow) —
   IC-probe first.
5. [LOWER, IF H1] Composite partition (skip-tail for vol_low, no-skip for rev_3, signal-aware).
**"OHLCV 8h cross-section too weak" should be the conclusion ONLY if #1 returns negative.**
