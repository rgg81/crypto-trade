# DIAGNOSTIC-A — Funding-Carry Cross-Section Probe (MN track)

**Date:** 2026-07-10 · **Role:** QR · **Script:** `analysis/portfolio/mn_diag_a_funding.py`
(committed spec = PLAN.md §2 Sketch A, run exactly as frozen; trial ledger: 3 cadence cells)
**Data hygiene:** `mn_panel_health()` → OK (BTC grid T=7147 contiguous; live feeds current).
**Blinding/IS:** panel sliced via `mn_split.mn_slice_is` before any computation; `mn_guard_grid`
passed; IS = 2020-01-01 → 2025-12-31 (T=6,576 candles × 747 syms). Old-track `is_mask`/
`OOS_CUTOFF` never touched. Reproducibility: full re-run after lint edits is bit-identical.

## VERDICT — pre-registered kill criteria (PLAN §2 Sketch A, verbatim)

| # | Criterion (frozen) | Measured | Verdict |
|---|---|---|---|
| (a) | net-of-cost D1−D10 residual total-return spread ≤ 0 ann. at BOTH rebal=3 AND rebal=21 (phase-agnostic) | net₃ = **+163.8%**, net₂₁ = **+131.4%** | **SURVIVES** |
| (b) | price-leg giveback ≥ 100% of funding collected, full-IS aggregate | giveback = **−54.6%** (price leg ADDS +4.145 on funding +7.595 cum) | **SURVIVES** |
| (c) | CRASH-bucket mean spread < 0 with t < −2 | mean = **−9.43 bps**, t = **−0.58** | **SURVIVES** |

**SKETCH A SURVIVES DIAG-A. Recommendation: proceed to EXPLORATION-A** (engine backtest with
the §4.1 hedge overlay, full neutrality gate G1–G5). Design requirements from the findings below.

---

## 0. Pre-scoring gates

- **Regime occupancy sanity check (PLAN §1.2, run before scoring):** CRASH 11.5% (n=747),
  MANIA 15.7% (n=1,021), CHOP 72.7% (n=4,718); WARMUP 90. All buckets ≥5% → **PASSED**, no
  amendment needed; the frozen rules are now immutable for the track's lifetime.
- **Funding coverage:** complete for all 361 top-40 ever-members (745/747 panel syms resolve
  direct; the 2 missing are never universe members). No silent-zero funding.

## 1. Signal construction (as registered + implementation decisions on record)

- Universe: PIT top-40 by trailing 30-candle mean $-volume via `pit_topn_universe`, with the
  ≥90d-history requirement implemented by NaN-masking a name's first 270 candles of
  quote-volume before ranking (machinery reused verbatim). Mean 36.6 members/candle.
- Signal S_i[t] = trailing 9-candle mean of the funding z. **Implementation decision:** z is the
  **cross-sectional** z-score of the 8h bucket-sum funding over current universe members
  (min 5 of 9 finite). Rationale: the PLAN's mechanism text demands insensitivity to the
  aggregate funding level ("isolates RELATIVE crowding"), which cross-sectional normalization
  delivers; DIAG-D's spec names a per-name trailing window explicitly where that is meant —
  DIAG-A's does not.
- Sort: deciles by S ascending among members with finite S; D1 = lowest/most-negative funding
  (LONG, collects from crowded shorts), D10 = highest funding (SHORT, collects from crowded
  longs); equal-weight n//10 names per leg (median 38 names used → k=3; book gross = 2.0).
- Returns: next-candle TOTAL residual return = (r[t+1] − β[t]·r_BTC[t+1]) − fund[t+1] per unit
  long. β = `mn_beta.rolling_beta` frozen defaults (270/135/λ=0.33/clip[0,3]) at the standard
  [k−1] lag. fund[t] settles by open[t+1] = close[t], so S[t] is fully known at the decision.
- Regime conditioning: bucket = label at the DECISION candle t (live-computable convention).
- Capture measurement conditions membership on finite t+1 data (measurement necessity, ~1-candle
  scale); the cadence simulations do NOT (held names with NaN forward data contribute 0) — the
  kill-(a) numbers come from the simulations and carry no forward-conditioning.

## 2. Persistence (DIAG-A step 1) — does the sort outlive the decision lag?

- Pooled funding ACF (361 ever-member names): lag1 0.61, lag2 0.51, lag3 0.42, lag9 0.20,
  lag21 0.10, lag90 0.03. Per-name median: L1 0.48, L9 0.25, L90 0.07.
- Half-lives: raw funding pooled-ACF < 0.5 at lag 3 (~1 day); per-candle cross-sectional z
  AR(1) ρ=0.683 → HL 1.8 candles; **the 9-candle-mean sort signal AR(1) ρ=0.988 → HL 56
  candles ≈ 18.7 days.**
- Conclusion: raw funding is noisy but the registered 3d-mean sort is highly persistent — the
  sort survives the 1-candle decision lag by ~50 candles of margin. Weekly rebal is viable
  (consistent with measured turnover below).

## 3. Decile capture (DIAG-A step 2) — gross, top-40 primary view

6,150 capture candles, effective start 2020-05-17 (universe formability), median 38 names.

Per-decile mean next-candle TOTAL residual return (bps/candle):

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 |
|---|---|---|---|---|---|---|---|---|---|
| +7.42 | +1.98 | +2.08 | −3.85 | −2.09 | −3.04 | −2.68 | −4.82 | −6.04 | **−9.19** |

- Spearman IC (S vs next total residual return): mean **−0.0194, t = −7.59** — negative as the
  mechanism predicts (high funding → lower forward total return), and monotone-ish across deciles.
- **D1−D10 gross spread: +19.09 bps/candle, t = +3.66, annualized +209.0%** on the 2×-gross
  probe book (per-candle σ = 409 bps → ann vol ≈ 135%, gross ann Sharpe ≈ 1.54 — probe-level,
  unsized).
- Distribution honesty: median +11.65 bps; 52.0% of candles positive; symmetric 1%-trim mean
  +17.88 bps (the edge is not a handful of candles); one-sided removal of the top-1% best
  candles alone drops the mean to +2.55 bps — both tails are fat and roughly offsetting;
  the single best candle is +149% (ALPACA-class squeeze; see §8).

## 4. Funding-capture vs price-giveback decomposition (the (b) falsifier)

Full-IS aggregate (rebal=1 capture): funding collected **+7.595** cum, price leg **+4.145** cum
→ **giveback ratio = −54.6%** — the price leg does not give back the carry; it ADDS 55% on top
(positioning mean-reversion is real in-sample). Per-candle means: funding +12.35 bps,
price +6.74 bps.

Structural note (disclosed, not a registered criterion): the price leg decays across eras —
per-year price leg +28.1, +36.0, +4.5, +6.1, **−9.3, −16.7** bps (2020→2025) while the funding
leg is positive every year (+7.8, +7.7, +10.7, +15.1, +5.9, +25.2). At year granularity 2024's
price giveback exceeded its funding (158%) and 2025's ran at 66%. The registered criterion is
full-IS aggregate and SURVIVES; but the durable component in the recent era is the funding leg,
not the price pop. EXPLORATION-A should be sized to survive on the funding leg alone.

## 5. Regime-bucket breakdown — THE all-conditions question

Decision-candle label, top-40, gross capture (bps/candle):

| bucket | n | total | t | price | funding | ann |
|---|---|---|---|---|---|---|
| CRASH | 658 | **−9.43** | −0.58 | −22.70 | +13.27 | −103% |
| MANIA | 919 | +37.57 | +3.36 | +30.43 | +7.14 | +411% |
| CHOP | 4,573 | +19.48 | +3.14 | +6.22 | +13.26 | +213% |

- The mechanism's mania story is confirmed (short the crowded longs; both legs pay). The chop
  story is confirmed (funding does the work). **The crash story is NOT confirmed directionally:**
  funding still collects (+13.3) but the price leg bleeds −22.7 — in crashes, deeply-negative
  funding often marks a crowd that is RIGHT about a collapsing name (LUNA May-2022 cost the
  probe −10,600 bps cum by longing a death spiral against its shorts). Kill (c) requires
  significance (t < −2) and does not fire at t = −0.58 — but a book from this sketch must
  budget for crash-bucket drag, and G4 (worst-bucket t > −1.0) currently passes with little room.
- G5 flavor: no bucket exceeds 60% of P&L (CHOP ≈ 74% of candles produces ~76% of cum P&L —
  borderline; report to Critic at EXPLORATION).

## 6. Probe beta before/after neutralization

OLS of the spread stream on 8h factor returns, full capture window (n=6,150):

| stream | β_BTC | (se) | β_ETH | (se) |
|---|---|---|---|---|
| RAW (before residualization) | −0.0548 | 0.0302 | −0.0472 | 0.0229 |
| RESIDUAL (after) | **+0.0056** | 0.0301 | **−0.0080** | 0.0228 |

Bucket-conditional β_BTC of the residual stream: **CRASH +0.172 (se 0.071)** — above the G2
bound (|β| ≤ 0.15); MANIA −0.028 (se 0.056). Measurement-level residualization achieves
full-sample neutrality but NOT crash-conditional neutrality — exactly the predecessor's failure
axis. This is the single most important number for EXPLORATION-A: the engine-level hedge
overlay (PLAN §4.1) must be tested against G2 in the CRASH bucket specifically, and passing is
not a foregone conclusion.

## 7. Cost coverage (DIAG-A step 3) — pre-registered cadences, phase-agnostic

7.5 bps/side on Σ|Δw|; 2×-twin = 15 bps/side. Turnover in book-notional multiples per year
(book gross = 2.0). Ex-window = excluding 2025-03→2025-12 (contamination map, §9).

| rebal | gross ann | NET ann (1×) | NET ann (2×) | turnover/yr | phase dist (NET) | ex-window NET |
|---|---|---|---|---|---|---|
| 1 | +209.6% | +154.6% | +99.7% | 733× | single phase | +179.2% |
| 3 | +199.7% | **+163.8%** | +128.0% | 478× | +150.5/+162.6/+178.4 · 3/3 pos | +192.5% |
| 21 | +142.3% | **+131.4%** | +120.5% | 145× | min +16.9 / med +149.5 / max +206.7 · **21/21 pos** | +137.3% |

- Costs are not the binding constraint at any registered cadence; even the 2×-twin nets >99%
  everywhere. Weekly costs ≈ 10.9%/yr at 1×.
- Phase variance at rebal=21 is wide (+16.9% worst phase vs +206.7% best) though all 21 are
  positive — an EXPLORATION book at weekly cadence should be a tranche ensemble, per §5.5.

## 8. Integrity checks (data due diligence, not re-gating)

- **Funding tails are real market events, not corrupt rows:** extremes are settlement-cadence-
  exact bucket sums from documented squeezes — ALPACA Apr-2025 delisting squeeze (−1,146 to
  −1,461 bps/candle), LPT May-2025 (−1,713), OMG Nov-2021 (−1,200), PIPPIN Dec-2025 (−1,067).
  Universe-member funding quantiles: q0.1% −220 bps, q1% −25.5, median +0.9, q99% +19.7 bps.
- **Single-name P&L concentration:** ALPACA +15.3% of cum P&L, LUNA −9.0%, TRB +6.5%,
  PIPPIN +6.0%/−4.8% (two episodes). No name >16%; both signs present (the squeeze exposure
  cuts both ways). Live capacity/borrow on ALPACA-class names is not credible at size —
  the PLAN's own construction-stage mandate (liquidity floor + per-name cap) is confirmed
  necessary, and its P&L cost must be measured at EXPLORATION, not assumed away.
- **Leg concentration:** D1 (long) is dominated by structurally-negative-funding majors
  (BNB 22.9% of candles, AXS 19.3%, BCH 11.9%); D10 (short) by meme perps (FARTCOIN 9.6%,
  1000SHIB 6.2%, 1000PEPE 5.5%, DOGE 5.4%) — precisely the PLAN-flagged meme-perp
  concentration. Short-side borrow/liquidity realism is an EXPLORATION question.

## 9. Contamination disclosure (PLAN §5.4)

Excluding the 2025-03→2025-12 revealed-regime sub-window: gross capture +21.40 bps/candle
(t = +4.86, ann +234.4%), IC −0.0238, giveback −120.2%, net ann at all three cadences HIGHER
than the full-IS headline (table above). **The result does not depend on the burned window** —
it is stronger without it (2025 was the weakest price-leg year).

## 10. Per-year stability (return-candle year, gross capture)

| year | n | total bps | t | price | funding | ann |
|---|---|---|---|---|---|---|
| 2020 | 678 | +35.87 | +4.14 | +28.08 | +7.79 | +393% |
| 2021 | 1,090 | +43.61 | +4.36 | +35.95 | +7.66 | +478% |
| 2022 | 1,094 | +15.19 | +1.39 | +4.54 | +10.66 | +166% |
| 2023 | 1,095 | +21.27 | +2.55 | +6.13 | +15.14 | +233% |
| 2024 | 1,098 | **−3.41** | −0.34 | −9.31 | +5.89 | −37% |
| 2025 | 1,095 | +8.56 | +0.41 | −16.65 | +25.21 | +94% |

Five of six years positive; 2024 (funding-compression year) flat-negative and insignificant.
The funding leg is positive in ALL six years — the carry component has no losing year in-sample.

## 11. Top-20 robustness column (pre-registered secondary view)

Capture gross +22.45 bps/candle (t = +2.26, ann +245.9%); IC −0.0222; giveback −66.6%;
CRASH bucket −24.22 bps (t = −0.78); NET ann rebal=3 +218.1%, rebal=21 +201.6% (phase-agnostic).
Same sign, same structure, larger point estimates with wider error bars (2 names/leg) —
the finding is not a top-40 artifact.

## 12. What EXPLORATION-A must carry forward

1. **Engine backtest with the §4.1 BTC/ETH hedge-leg overlay**; neutrality gate G1–G5 measured,
   with G2 in the CRASH bucket as the expected point of failure (probe: +0.172 vs bound 0.15).
   If static residual-hedging cannot pass G2-CRASH, that is the research problem — not a reason
   to relax the gate.
2. **Liquidity floor + per-name cap** (PLAN-mandated): measure the P&L cost of removing
   ALPACA-class squeeze names; the sketch must remain alive on the funding leg after capping.
3. **Cadence:** rebal=3 and rebal=21 both clear costs with 2× margin; weekly + tranche ensemble
   is the deployment-shaped choice given the 18.7-day signal half-life and the phase spread.
4. **Sizing prior:** budget for crash-bucket drag (−9.4 bps/candle mean gross in CRASH) and a
   funding-leg-only base case (~+12 bps/candle gross before costs); the 2020-21 price pop is
   not to be extrapolated.
5. n_eff ledger for family A after this diagnostic: 3 registered cadence cells, no other knobs
   tried, no amendments.

*— QR, MN track, 2026-07-10. Probe run exactly as pre-registered; verdict SURVIVES on all three
kill criteria; no post-hoc re-gating performed.*
