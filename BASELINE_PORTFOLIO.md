# BASELINE_PORTFOLIO — systematic top-20 L/S crypto perp portfolio

Living baseline for the `portfolio-iteration` track. Updated only by a confirmed accretive change.

## Current baseline: TREND + CARRY-TILT (walk-forward λ) + HYSTERESIS-BANDING  [iter-005 + iter-020]
- **Config:** point-in-time top-20 by trailing $-volume (ex-stablecoins, ≥2y-history pool, 206 coins).
  Per coin, blended directional signal `(1-λ)·trend + λ·carry`, inverse-vol sized:
    - trend = mean sign of trailing returns over {7d,14d,28d,56d} (8h candles)
    - carry = −sign(trailing-9 funding) (short high-funding / long low-funding)
    - **λ selected WALK-FORWARD** each month on the past 24mo (best past Sharpe); converges ~0.25.
  Gross-normalized long/short, portfolio vol-targeted (1%/candle, max 3x). Real funding P&L booked.
  **HYSTERESIS-BANDING (SNAP δ=0.010, iter-020, critic-PROMOTED 2026-06-20):** rebalance a coin only
  when |target_w − held_w| > 0.010 (no-trade band), gross renormalized each candle (cadence change, not
  sizing). Realistic: decide close[t] → fill open[t+1] → hold; taker 0.05%/side. Leak-safe.
- **Performance:** net **IS +1.30 / OOS +1.37+ / maxDD −23%**, positive every year. The hysteresis band
  cuts rebalancing TICKETS −63% (−7% notional turnover) at NO Sharpe cost (OOS within-noise +1.50 point
  est; the deterministic ticket/cost reduction is the promotion case), and is MORE cost-robust (OOS@2×
  taker +0.89 → +1.05). The carry tilt is walk-forward-VALIDATED (λ≈0.25 picked 14/18 OOS months).
  Beats buy-and-hold BTC (IS +0.98 / OOS −0.36 / −77% DD) on every axis.
- **Code:** `analysis/portfolio/iter_002_top20.py` (trend) + `iter_004_funding.py` (carry tilt) +
  `iter_005_wf_lambda.py` (walk-forward λ) + `iter_020_hysteresis.py` (SNAP δ=0.010 band — deploy this).

## Progression
- iter-001 BTC trend anchor: OOS +0.64. → iter-002 diversified top-20 trend: OOS +0.50, −28% DD.
- iter-003 trend-agreement gate: REJECTED (no help). → iter-004/005 carry tilt: OOS +0.48→**+1.08**, confirmed (funding-fixed).

## Rejected
- Cross-sectional momentum (rank L/S): OOS −1.81. Trend-agreement gate: no effect / over-concentrates.

## Open improvement axes (one per EXPLORATION; keep only if net Sharpe rises, walk-forward-validated)
1. Walk-forward the trend horizon mix {7,14,28,56d} (currently equal-weight).
2. Short-term reversal overlay (1–3d). 3. Regime/vol scaling of gross exposure. 4. Per-coin caps /
   correlation-aware weights to trim the −29% DD.

## Sacred constants
OOS_CUTOFF=2025-03-24 · 8h candles · signals past-only, fill open[t+1] · never tune on OOS ·
walk-forward any param · universe PIT top-20 ex-stables · report net (cost+funding) · NO capacity gate.

## CORRECTION LOG (critic review, 2026-06-19)
- **Funding-alignment bug fixed** (`iter_004_funding.load_funding`): Binance funding_time has ms jitter;
  exact-match reindex silently zeroed ~65% of funding cells, inflating the carry edge ~28%. Fixed via
  nearest-match within 4h. HONEST numbers: walk-forward λ → **IS +1.30 / OOS +1.08 / DD −24%** (was the
  inflated +1.22). The carry tilt is still real + walk-forward-confirmed, just smaller.
- **OUTSTANDING (blockers from review):** (2) data is stale — 183/206 coins stop ~Feb-2026, so the last
  ~4 OOS months run a degenerate (<TOP_N) universe; the ~11 clean OOS months are +2.10, the full OOS
  (incl. stale tail) is the conservative +1.08. FIX = refresh full-universe data + min-eligible guard.
  (3) only λ is walk-forward; honest path per risk-engineer = walk-forward λ + PROVE robustness of the
  structural params (NOT per-month-tune all 12, which overfits the 24mo window = a hidden cheat).

## UPDATE — iter-007 (agent-driven: risk-engineer built, quant-critic reviewed), 2026-06-19
- **Data refresh (blocker #2 FIXED):** the stale-universe degenerate OOS tail is gone (critic-verified:
  0 OOS candles guarded, no new leak — legitimate de-biasing). Honest baseline OOS **+1.08 → +1.37**.
- **min-eligible guard:** KEPT as a free, leak-safe safety net (neutral on current data — only guards
  the early-2020 warmup; insurance against future universe degeneracy).
- **vol-spike de-lever: REJECTED by critic.** Its apparent +0.16 OOS lift was a STITCH-ORDER ARTIFACT
  (iter_007 vol-targets once vs iter_005's per-λ); under canonical accounting it adds +0.01 OOS (noise).
  NOT promoted. (The agent review caught a measurement artifact before it entered the baseline.)
- **Current honest baseline = canonical iter_005 walk-forward λ: IS +1.30 / OOS +1.37 / DD −23%**,
  positive every year, funding-fixed, fresh PIT universe, taker fees, no HFT/MM/VIP.

## PROMOTION LOG
- **2026-06-20 — HYSTERESIS-BANDING promoted (iter-020, critic PASS).** First promotion since the data
  refresh. SNAP δ=0.010 no-trade band: rebalancing tickets −63% at no Sharpe cost, more cost-robust
  (advantage widens under 2× taker), leak-free, gross-preserved (true cadence change, not a de-lever),
  robust δ=0.005→0.020. maxDD unchanged (the whipsaw-DD hypothesis did NOT confirm; the win is cost/
  cadence). Deploy SNAP δ=0.010 (NOT EDGE mode — degrades IS + worsens DD). Tag portfolio-baseline-v2.
- HELD (NOT promoted): trend+carry+flow risk-parity combiner (iter-014/015) — OOS +2.40 point est but
  DSR-NOT-significant at N=14 (iter-018); strong CANDIDATE, run in SHADOW for forward OOS.

## PROMOTION — baseline-v3: ELIGIBILITY-EXIT (iter-021, K=2, critic PASS 2026-06-21)
User-found flaw: the δ=0.010 band held ~18 ZOMBIE positions (exited coins never closed, incl. delisted
TOMO/BLZ) -> book = 38 for a "top-20" strategy. FIX (iter_021_eligexit.py): force-close any coin
ineligible (liquidity rank > 20) for >= K=2 consecutive candles, overriding the band; renorm + vol-target
as before. RESULT (current data): book 38 -> 20 (true top-20, all zombies + delisted GONE), IS +1.22 /
OOS +1.63 (baseline K=inf +1.25/+1.66 same data), maxDD -23%. NOT alpha — book-hygiene + deployment
robustness: order-TICKETS/candle FALL 23.8 -> 18.3 (zombies generated a phantom renorm ticket every bar)
-> lower live cost/slippage; OOS RETURN actually HIGHER (+53.9% vs +51.7%), the -0.03 Sharpe is just
slightly higher vol from a less-diluted book. Critic PASS: leak-free (corruption bit-identical; K=inf
reproduces iter_020 bit-exact), K robust on mechanism (not OOS-tuned), concentration healthy (ETH 18.9%).
DEPLOYABLE BASELINE = trend+carry (wf λ) + hysteresis (δ=0.010) + eligibility-exit (K=2). Tag
portfolio-baseline-v3. Critic suggestion (future): add a liquidity-floor exit for coins that stay rank<=20
but go untradeable (TOMO-style pre-delist decay), IS-calibrated, as standing insurance.
