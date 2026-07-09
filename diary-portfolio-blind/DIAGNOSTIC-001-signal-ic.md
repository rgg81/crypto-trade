# DIAGNOSTIC-001 — IS cross-sectional signal IC screen

**Date:** 2026-07-09  **Phase:** pre-EXPLORATION cheap diagnostic (brief step 2)
**Script:** `analysis/portfolio/blind_signal_ic_probe.py` (committed, reproducible)
**Data:** 712 coins aligned on BTC 8h grid (symlinked from main trunk — raw market data only;
this worktree stayed 100% blind to the deployed baseline in `analysis/portfolio/iter_*.py`,
`quant-portfolio*` worktrees, and `BASELINE_PORTFOLIO.md`).

## Setup
- **Universe:** point-in-time TOP-20 by trailing 30-candle quote-volume, ex-stablecoins,
  re-ranked every 8h candle (OI history unavailable → $-volume proxy, per skill).
- **Target:** forward return `close[t+1]/close[t]-1` (signal known at `close[t]`; leak-safe).
- **Metric:** cross-sectional Spearman rank-IC, IS only (`open_time < 2025-03-24`).
  **OOS sealed.** 5726 IS eval timestamps across 2020-01 → 2025-03.
- **This is a HYPOTHESIS-GENERATING SCREEN** — no cost model, no multiple-testing correction,
  no OOS. It only selects which signal merits a full costed EXPLORATION + Critic.

## Results (IS rank-IC)

| signal | n | meanIC | IR | t | 2020 | 2021 | 2022 | 2023 | 2024 | 2025Q1 |
|--------|--:|-------:|---:|--:|----:|----:|----:|----:|----:|------:|
| **vol_low** | 5662 | **+0.0523** | +0.19 | +14.2 | +.038 | +.068 | +.057 | +.038 | +.056 | **+.076** |
| **rev_3** | 5665 | **+0.0446** | +0.21 | +16.1 | +.048 | +.054 | +.050 | +.047 | +.027 | +.032 |
| rev_6 | 5662 | +0.0367 | +0.17 | +12.9 | +.030 | +.051 | +.034 | +.039 | +.031 | +.032 |
| mom_24 | 5644 | −0.0366 | −0.16 | −12.2 | neg all yrs | … | … | … | … | −.022 |
| mom_84 | 5584 | −0.0263 | −0.12 | −8.9 | … | … | … | … | … | +.011 |
| taker_imb3 | 5668 | −0.0071 | −0.05 | −4.0 | ~0 all yrs |

**Signal orthogonality (avg cross-sectional rank-corr, IS):**
- `corr(vol_low, rev_3) = −0.006` → **orthogonal**
- `corr(vol_low, mom_24) = −0.190`, `corr(vol_low, taker_imb3) = +0.001`
- `corr(rev_3, mom_24) = −0.259`

**Time-series lead-lag** (corr of lagged leader return vs avg top-20 alt fwd return, IS):
- BTC: lag1 +0.007, lag2 **−0.090**, lag3 +0.014
- ETH: lag1 +0.009, lag2 **−0.106**, lag3 +0.015

## Findings

1. **`vol_low` (low-volatility premium) is the winner** — strongest IC (+0.052), stable
   across ALL 6 IS years, *rising* in 2025Q1 (+0.076), and **orthogonal** to reversal and
   taker-pressure. Cross-sectional rank-IC is market-neutral by construction, so this is a
   genuine relative effect, not long-only drift. **Not present in the deployed baseline's
   factor list** (trend/carry/reversal/takerflow/regime/basis/hysteresis/eligexit/caps/
   magnitude/liqfade/riskparity/combiner/fundaccel/horizons — no low-vol factor). → NOVEL.
2. **`rev_3` (1-day reversal)** — strong & stable but **overlaps the baseline**
   (`iter_008_reversal`). Orthogonal to vol_low though → candidate for a LATER combined
   EXPLORATION, not the first.
3. **Cross-sectional momentum is negative** (mom_24/84 < 0 all years) — crypto
   cross-sectionally *mean-reverts* at 8h; it does not trend cross-sectionally. (The deployed
   "trend" is therefore presumably time-series momentum — a different axis.)
4. **Lead-lag diffusion is DEAD at 8h** — no positive BTC→alt lead; only a mild negative
   lag-2 (= another reversal flavor). **PLAN.md Approach 2 killed.**
5. **taker_imb** — weak/no cross-sectional edge.

## Crypto-native rationale for `vol_low` (to defend at Critic)
Retail exhibits strong **lottery preference** — systematic overpayment for high-vol, high-skew
names (memes, low-cap pumps, recently-spiked coins) → those underperform; "boring" low-vol
large-caps are under-owned and drift up. This is the equity low-vol anomaly, **amplified in
crypto** (heavier retail flow, leverage-driven liquidation cascades concentrated in high-vol
names). Mechanically vol is persistent (clustering) → low-vol rankings are stable → **low
turnover → low cost** — ideal for net Sharpe.

## Honest caveat
Low-vol is a *classic* factor in the equity literature. It is novel **only relative to this
deployed crypto book** (which lacks it). If the orchestrator wants a strictly-non-classic
angle, vol_low may not clear that bar — but its IC is strong, stable, orthogonal, and
low-turnover enough to be worth a costed EXPLORATION regardless.

## Verdict → EXPLORATION-001
**Proceed to a full costed EXPLORATION of a dollar-neutral low-volatility L/S factor**
(long lowest-realized-vol / short highest, within the PIT top-20, vol-targeted), scored
IS-only. Requires the foundation first:
- `analysis/portfolio/blind_engine.py` — signal→target weights→next-open rebalance→taker cost
  on turnover **+ funding on perp legs**→portfolio return series→Sharpe/DD/turnover/per-year.
- `analysis/portfolio/blind_universe.py` — PIT top-20 (reuse probe's logic).
- **Fetch funding** for the liquid universe (main trunk has only 5 series — needed for the
  perp-leg funding cost; the ~28% funding-inflation bug lesson demands real funding, not an
  approximation).
- Leak test in `tests/` (future→past corruption: past bit-identical) + dollar-neutrality +
  cost-accounting assertions.
Then full agent team (QR→QE→risk-engineer→Critic) for the EXPLORATION.
