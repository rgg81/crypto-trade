# LightGBM Master Advisor — iter-v1/055 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-6 EXP-10/10 FINAL — ETH-only specialist, mirroring /050 DOT cross-asset design
- Cohort: **ETHUSDT only** (ETH-only specialist head; BTC klines loaded for feature computation only)
- Baseline ETH IS Sharpe: **-0.61** (second-worst of 5 symbols; 145 IS trades / ~5675 IS rows)
- NEW feature: `eth_vs_btc_ret_ratio_30` (ETH 30d return / BTC 30d return, z-scored 90 bars, clipped ±10)
  — direct algebraic mirror of `dot_vs_btc_ret_ratio_30` from /050; same module class `cross_btc_v1.py`
- Optuna: n_trials=18, single seed=42, ENSEMBLE_SIZE=3 (EXPLORATION standard)
- Feature stack: V1_FEATURE_COLUMNS_PRUNED 47 → 48 cols (post-/054 impulse-drop finalized at 47)
- Preceding verdict chain: /050 PROMISING-PARTIAL (DOT; Δ +1.12 IS, feature-attributed, gate inert)
  → /051 PARTIAL-CONFIRMED (DOT multi-seed; mean IS Δ +0.99) → /052 PROMISING-SPECIALIST-CANDIDATE
  (BTC; Δ +1.01) → /053 PARTIAL-CONFIRMED (BTC multi-seed; mean IS Δ +0.81) → /054
  IMPULSE-DROP-CONFIRMED (BTC spread-only; Δ +1.11 single-seed; impulse permanently dropped)

---

## Phase 4.5 — LM Master Pre-Design Advisory

### ETH-Only Training — ML Perspective

ETH-only training has **145 IS trades / ~5675 IS rows** — materially larger than DOT's 93 IS
trades / ~3775 rows. This is favorable: more training rows per CV fold reduces n_eff starvation
at `min_data_in_leaf` upper bound, giving Optuna a more stable optimization surface at n_trials=18.
Per-seed Sharpe variance should therefore be **lower than DOT's spread 0.5690** (per /051
multi-seed); the single-seed=42 read at /055 carries less lottery risk than /050 did.

ETH and BTC are highly correlated at daily-to-weekly timescales (~0.85 correlation). This makes
`eth_vs_btc_ret_ratio_30` structurally meaningful: when the ratio is high (ETH outperforms BTC
over 30 bars), ETH is expressing **idiosyncratic momentum** — altcoin beta is positive independent
of BTC macro direction. When the ratio is flat, ETH moves in lockstep with BTC and ETH-specific
signal degrades toward BTC-inherited noise. The z-score over 90 bars captures the regime context
(is this ETH/BTC ratio expansion typical or abnormal for the recent quarter?).

The DOT analogue (`dot_vs_btc_ret_ratio_30`) achieved importance rank 8/45 at /050 single-seed
and rank 7-9 across all three /051 multi-seed outer seeds — a robustly learned, mid-table feature.
ETH/BTC correlation is higher than DOT/BTC (~0.85 vs ~0.70), so the ratio is noisier at short
windows. The 30-bar window corresponds to ~10 days at 8h cadence — long enough to capture
positioning momentum but short enough to respond to regime transitions. The 90-bar z-score
normalization is well-calibrated for this frequency.

---

## Top 3 Recommendations

### Rec 1 — ETH/BTC ratio captures idiosyncratic ETH alpha; clip ±10 is load-bearing

`eth_vs_btc_ret_ratio_30` is well-motivated at 8h cadence. When ETH moves independently of BTC
(high ratio or low ratio, not flat), the ETH-only LightGBM head has **informative conditioning
signal** for directional predictions. When ETH = BTC × constant (ratio near historic mean), the
feature adds noise.

The critical implementation constraint: **clip ±10 before z-scoring** (same as `dot_vs_btc_ret_ratio_30`
at /050). Raw ratio values blow up during extreme vol events when BTC 30d return approaches zero
(division by near-zero). Without the clip, a single outlier candle corrupts the 90-bar z-score
window. Verify in the EDA analysis script that clipped pct > 0 on ETH rows (ETH/BTC extreme
divergences occur 1-3× per year; clip should fire on a handful of rows).

Expect **partial-to-strong IS lift** via the same mechanism as DOT: ETH-only head learns that
high (or low) ratio regimes have edge; flat-ratio candles have reduced confidence → gated or
lower-weight predictions. The mechanism is feature-mediated (not gate-mediated — /050 proved the
vol-spike gate was inert for DOT; do NOT introduce a regime gate for ETH unless brief Section 2
has IS-only numerical evidence of gate utility).

### Rec 2 — Compare /055 ETH Δ against /050 DOT Δ +1.12; divergence is diagnostic

The /050 DOT benchmark provides a cross-symbol calibration reference. DOT IS baseline was -1.23;
ETH IS baseline is -0.61. DOT achieved Δ +1.12 (single-seed) → ETH has **less absolute headroom**
(only +0.61 to reach flip-positive). However, ETH has MORE training rows (145 vs 93 trades),
which should produce a cleaner Optuna optimization basin.

Two plausible comparative outcomes:
- **ETH Δ ≥ DOT Δ** (+1.12+): ETH flip-positive easily. More training data + same feature quality.
  Strong SPECIALIST-CANDIDATE verdict.
- **ETH Δ < DOT Δ** (+0.61 to +1.12): ETH reaches flip-positive but with smaller margin. Indicates
  DOT had more per-symbol IS variance to compress via idiosyncratic conditioning; ETH's pooled-head
  was less destructive (pooled -0.61 vs DOT -1.23 suggests DOT was more harmed by BTC co-training).

If ETH Δ < +0.30 (WEAK/NEG band), this is a **per-symbol baseline signal**: DOT benefited from
the cross-asset ratio more than ETH. Possible cause — ETH/BTC ratio is noisier (higher correlation)
and the 30-bar window does not resolve idiosyncratic ETH momentum cleanly from BTC macro at 8h.

### Rec 3 — Multi-seed conditional: /055 SPECIALIST-CANDIDATE → /057 ETH multi-seed

Following the /050→/051 (DOT) and /052→/053 (BTC) precedents:
- If /055 verdict ∈ {SPECIALIST-CANDIDATE, PARTIAL} → **ETH multi-seed re-validation is MANDATORY
  BEFORE CONFIRMATION**. Pre-register this in brief Section 8 as a binding conditional.
- If /055 verdict ∈ {WEAK, NEG-INERT, NEG-CLEAN} → /056 CONFIRMATION proceeds with only 2
  PARTIAL-CONFIRMED specialists (DOT + BTC). ETH multi-seed is NOT triggered.
- The /056 CONFIRMATION (cycle-6 EXP-10/10 cadence complete) assembles the portfolio. If /055
  SPECIALIST-CANDIDATE fires, /056 must sequence: /055 multi-seed first THEN /056 CONFIRMATION
  (cannot bundle unvalidated single-seed). Alternatively, if /057 slot is used for ETH multi-seed,
  /058 is the CONFIRMATION. QR should pre-register the branching path in brief Section 8.

---

## Prior Distribution

| Verdict Band | Probability | Rationale |
|---|---|---|
| SPECIALIST-CANDIDATE (Δ ≥ +0.61, flip-positive) | **35%** | Modal; 145 IS trades gives cleaner Optuna signal; ETH has clear idiosyncratic cycles |
| PARTIAL (Δ ∈ [+0.30, +0.61)) | **30%** | ETH/BTC correlation ~0.85 makes ratio noisier than DOT/BTC ~0.70; shorter headroom to flip |
| WEAK (Δ ∈ [+0.05, +0.30)) | **15%** | Noisy ratio at 30-bar window + n_trials=18 single-seed fails to isolate idiosyncratic ETH regimes |
| NEGATIVE-INERT (Δ ∈ (−0.05, +0.05)) | **12%** | LightGBM at single-seed=42 fails to learn ratio; feature ranks 35+ of 48 |
| NEGATIVE-CLEAN (Δ ≤ −0.05) | **8%** | Ratio anti-informative at n_trials=18; IS Sharpe degrades below -0.61 |

**LM Master modal: SPECIALIST-CANDIDATE (35%) + PARTIAL (30%) = 65% positive prior.** Driven by
larger ETH training corpus vs DOT and proven mechanism from /050 cross-asset ratio family.

---

## Risk Flags

1. **ETH/BTC high correlation noise floor**: daily correlation ~0.85 means many 30-bar windows
   have ratio near 1.0 (noise-dominated). The 90-bar z-score must reveal VARIATION in the ratio
   across IS regimes — verify in EDA that z-score std > 0.5 across IS rows (if std < 0.3, the
   ratio is too flat to condition on). Brief Section 2 must include this check.

2. **Clip ±10 critical — verify clip fires**: BTC 30d return approaches zero at cycle bottoms
   (2022-Q4, any crash trough). If not clipped, division by near-zero blows ETH/BTC ratio to
   ±100+, corrupting the 90-bar z-score rollowing window for multiple bars after. EDA script
   must confirm: `(df['eth_vs_btc_ret_ratio_30_raw'].abs() > 10).sum() > 0` on IS rows.

3. **ETH OOS is near-flat (+0.07) — avoid OOS-fishing**: ETH OOS Sharpe +0.07 at baseline is
   already near-flat. A specialist lift of +0.61 IS Δ produces an ETH IS Sharpe ~0.00 — the OOS
   will remain informational only at EXPLORATION budget. Do NOT gate the verdict on OOS Sharpe.
   The /050 precedent (DOT OOS -0.14 with PARTIAL verdict) is the correct methodology.

4. **Single-axis discipline**: `eth_vs_btc_ret_ratio_30` alone, no companion gate. /050 showed
   the regime gate was INERT (0% fire rate IS+OOS). Do not add a vol-spike gate to the ETH
   specialist unless brief Section 2 provides IS-only numerical evidence of gate utility.

---

## What I Did NOT Recommend

- No regime gate (per /050 INERT gate precedent — gate contributed 0% of the IS Δ)
- No companion feature (single-feature-at-a-time discipline; brief Section 3 must enforce)
- No HP search-space change (frozen vs /054 at n_trials=18 + colsample_bytree [0.5, 1.0])
- No ENSEMBLE_SIZE bump (stays at 3 for EXPLORATION budget)
- No multi-seed at /055 (single-seed=42 diagnostic; multi-seed deferred to /057 if SPECIALIST-CANDIDATE)

---

## Closing

This is the FINAL EXPLORATION of cycle-6. /055 outcome determines the /056 CONFIRMATION
composition:

- **If SPECIALIST-CANDIDATE or PARTIAL**: /056 sequences ETH multi-seed first (/057), THEN
  CONFIRMATION with 3 specialists (DOT + BTC + ETH) + 2 anchors (LINK + LTC). This is the
  maximal-specialist bundle outcome.
- **If WEAK or NEG-INERT**: /056 CONFIRMATION launches directly with 2 specialists
  (DOT PARTIAL-CONFIRMED + BTC PARTIAL-CONFIRMED-CLEAN) + 3 anchors (LINK + LTC + ETH pooled).
  ETH stays in Model A pooled head.
- **If NEGATIVE-CLEAN**: same as WEAK/NEG-INERT path.

ETH has the structural advantage of larger training data (145 IS trades vs DOT's 93). The
cross-asset ratio mechanism is proven at DOT. The primary remaining question is whether ETH/BTC
correlation noise at 30-bar window is low enough for LightGBM at n_trials=18 to extract regime
signal. The prior is positive (65% SPECIALIST-or-PARTIAL); the single-seed=42 result at /055
will resolve it.

**Single most important metric**: ETH IS Sharpe Δ vs baseline -0.61. If Δ ≥ +0.61 (flip-positive),
pre-register /057 ETH multi-seed in brief Section 8 immediately.

— Phase 4.5 advisor authored 2026-06-01
