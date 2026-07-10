# DIAGNOSTIC-003 — Monthly regime dependence of the /005 book (IS-only)

**Date:** 2026-07-10  **Phase:** REGIME-ROBUST REDESIGN — descriptive diagnostic (no strategy change, no tuning)
**Script:** `analysis/portfolio/blind_diag_003_monthly.py` (committed, reproducible, IS hard-sliced at top)
**Reference book:** EXPLORATION-005 — `lowvol_signal(window=12)` × `pit_topn_universe(top_n=20, lookback=30)`
× `run_backtest(CostModel(5,2.5,funding ON), gross=1.0, rebal=21, weighting="midvol_short",
long_frac=0.5, short_frac=0.25)`.
**Blinding/quarantine:** imports only `blind_*` modules; panel sliced to `open_time < 2025-03-24`;
every metric computed on IS candles only. OOS never touched.

**Sign convention:** all P&L columns are **return contributions to the strategy** (+ helps equity,
− hurts). `net_fund > 0` = funding was net **income** (shorts earned > longs paid).

## Parity guard (reproduces /005 headline before any analysis)
| metric | value | target | status |
|--|--:|--:|--|
| Sharpe | **+0.9134** | +0.913 ±0.005 | PASS |
| maxDD | **−32.99%** | −33% ±1pp | PASS |
| turnover | **55.4x/yr** | 55.4 ±2 | PASS |

Per-candle leg attribution reconciles to `rets` at **1.4e-17** (`long_px + short_px + net_fund − tcost ≡ ret`),
so the decompositions below are exact, not approximate. 63 months post-warmup (warmup=63 candles).

---

## 1. Monthly SHAPE — a few big months carry everything
- **Total IS log-equity growth +1.168 → 3.22× final equity.** Monthly **win rate 66.7%** (42/63 by
  return; 42/63 by Sharpe). 21 negative months.
- **Brutal concentration: top-5 months = 58.8% of total log-growth; top-10 months = 98.8%.**
  The book is ≈ flat ex its 10 best months. This is the single most important robustness fact:
  the edge is a handful of concentrated winners on top of a lot of chop — **any control that clips
  the fat right tail (2020-12 +21%, 2024-02 +15%, 2020-10 +14%, 2024-06 +13%, 2021-02 +11%) will
  gut the Sharpe.**

| best 5 (loggrow) | ret | worst 5 (loggrow) | ret |
|--|--:|--|--:|
| 2020-12 | +21.4% | 2024-11 | −16.4% |
| 2024-02 | +14.8% | 2021-03 | −13.5% |
| 2020-10 | +14.1% | 2024-05 | −11.9% |
| 2024-06 | +12.6% | 2023-09 | −10.6% |
| 2021-02 | +11.0% | 2022-06 |  −8.8% |

Per-year Sharpe (from /005 headline): 2020 +1.51, 2021 +1.10, 2022 +1.07, 2023 +0.35, 2024 +0.46, 2025Q1 +2.15.

## 2. THE KEY RESULT — the book does NOT lose in BTC-crash months; the short leg is its friend there
Crash months **defined by the market** (BTC monthly ret < −15% **OR** BTC trailing 540-candle dd at
month-end > 25%) = **20 months**. In those months the book earns **+2.59% mean, 70% win rate**.
Aggregate leg P&L over the 20 crash months: **long_px −0.892, short_px +1.531, net_fund −0.035** —
i.e. **the SHORT leg (short high-vol) is the entire crash-month P&L**; the long leg is the loser.

| month | btc_ret | btc_dd1 | strat ret | shrp | long_px | short_px | net_fnd |
|--|--:|--:|--:|--:|--:|--:|--:|
| 2020-03 | −25.0% | 38.2% | +0.35% | +0.36 | −0.145 | +0.154 | −0.001 |
| 2021-05 | −35.5% | 42.2% | +10.39% | +3.64 | +0.000 | +0.109 | −0.001 |
| 2021-06 | −4.9% | 45.6% | **−0.43%** | −0.16 | −0.088 | +0.087 | +0.002 |
| 2021-08 | +13.1% | 26.8% | +8.68% | +4.49 | +0.230 | −0.142 | +0.001 |
| 2021-12 | −19.2% | 32.4% | **−4.96%** | −2.29 | −0.096 | +0.051 | +0.000 |
| 2022-01 | −18.5% | 43.8% | **−5.36%** | −2.46 | −0.158 | +0.110 | −0.001 |
| 2022-04 | −16.4% | 45.0% | +4.92% | +3.17 | −0.139 | +0.191 | +0.000 |
| 2022-05 | −16.2% | 44.0% | +8.95% | +3.78 | −0.193 | +0.290 | −0.005 |
| 2022-06 | −36.7% | 58.0% | **−8.83%** | −3.52 | −0.218 | +0.137 | −0.003 |
| 2022-07 | +19.0% | 50.9% | **−1.18%** | −0.66 | +0.139 | −0.146 | +0.001 |
| 2022-08 | −14.0% | 57.7% | **−1.64%** | −1.27 | −0.075 | +0.065 | −0.002 |
| 2022-11 | −16.7% | 45.6% | +9.71% | +3.62 | −0.053 | +0.158 | −0.004 |
| 2025-02 | −17.5% | 21.3% | +5.46% | +1.96 | −0.160 | +0.226 | −0.005 |

(13 of 20 shown; full 20 in script output.) **HELD 14 / HURT 6.** The 6 crash months that hurt split
into two mechanisms:
- **True capitulation where everything falls together (2022-06 −8.8%, 2022-01 −5.4%, 2021-12 −5.0%):**
  the LONG leg loses hard (−0.22 / −0.16 / −0.10) and the short leg only partially offsets — cross-sectional
  dispersion collapses, so short-high-vol can't out-earn long-low-vol's beta loss.
- **Bear-market RALLIES inside a deep-dd flag (2022-07 +19% BTC, 2022-08):** the **short leg gets
  squeezed** (short_px −0.146 in 2022-07). These are the same short-squeeze mechanism as §3, not crashes.

**→ BTC-crash de-risking would be solving a non-problem, and would remove the short leg's crash alpha.**

## 3. The REAL drawdown driver — short-squeeze in alt-mania UP-months
Worst-10 strategy months by return. **7 of 10 are BTC-UP months.** The long leg is net **positive**
across all ten (+0.579); **the entire worst-10 loss is the short leg (−1.467)** — 165% of combined
price P&L. High cross-sectional dispersion (`x_disp`) is the tell.

| month | strat ret | long_px | short_px | net_fnd | btc_ret | x_disp | fnd8h |
|--|--:|--:|--:|--:|--:|--:|--:|
| 2024-11 | −16.35% | +0.230 | **−0.391** | +0.002 | **+39.2%** | +95.0% | +2.1bp |
| 2021-03 | −13.48% | +0.122 | **−0.262** | +0.003 | **+27.0%** | +189.0% | +5.8bp |
| 2024-05 | −11.86% | +0.129 | **−0.246** | −0.000 | **+17.6%** | +56.3% | +0.4bp |
| 2023-09 | −10.58% | +0.028 | −0.085 | **−0.047** | +3.8% | +47.8% | −10.7bp |
| 2022-06 |  −8.83% | −0.218 | +0.137 | −0.003 | −36.7% | +25.3% | −2.7bp |
| 2020-11 |  −8.61% | +0.212 | **−0.282** | −0.004 | **+43.1%** | +55.8% | +1.8bp |
| 2023-12 |  −8.44% | +0.152 | **−0.245** | +0.020 | **+10.7%** | +70.3% | +1.5bp |
| 2024-09 |  −6.73% | +0.055 | −0.120 | +0.001 | +8.3% | +98.8% | −0.5bp |
| 2020-05 |  −5.66% | +0.027 | −0.083 | +0.003 | +7.7% | +17.1% | +1.3bp |
| 2022-01 |  −5.36% | −0.158 | +0.110 | −0.001 | −18.5% | +11.7% | −0.2bp |

**The pattern:** BTC ripping + huge cross-sectional dispersion (lottery/high-vol alts mooning 3–10×) →
the short-high-vol leg is run over. `midvol_short` (skip the extreme-vol tail) mitigates but does NOT
eliminate it. Two outliers: **2023-09** is funding-driven (net_fund −0.047, fnd8h −10.7bp: short leg
*paid* funding in a low-BTC-vol grind), and **2022-06 / 2022-01** are the genuine-crash-capitulation
exceptions (long-leg beta loss).

## 4. Correlations — monthly crash beta ≈ 0; regime signal is weak at monthly resolution
Spearman ρ of monthly Sharpe / return vs regime feature (all weak):

| feature | ρ(sharpe) | ρ(return) |
|--|--:|--:|
| btc_ret | −0.01 | −0.06 |
| btc_vol | −0.02 | −0.00 |
| btc_dd_end | +0.10 | +0.09 |
| x_vol | +0.11 | +0.13 |
| x_disp | +0.03 | −0.00 |
| fund8h | +0.00 | +0.04 |

**Effective monthly crash beta (strat ret on BTC ret): −0.003 (pearson −0.008)** — genuinely
dollar-neutral. Split: **BTC-down months (27): mean strat ret +2.76%, Sharpe +1.17.** BTC-up months
(36): +1.65%, Sharpe +1.24. The book is, if anything, **mildly anti-crash** — it likes down months on
average. The monthly-linear correlations are weak because the killer is a **non-linear interaction**
(BTC-up **AND** extreme dispersion **AND** a specific set of names mooning) that a single monthly
scalar dilutes.

---

## Ranked control hypotheses (QR read, crypto-native)

The evidence overturns the naive framing. The enemy is **alt-mania short-squeeze**, not BTC crashes.
Ranked by expected Sharpe impact:

**1. Regime filter — HIGHEST, but must gate the RIGHT regime (mania, not crash).**
Mechanism: cut / remove / cap the **SHORT leg** when the cross-section enters mania — rising BTC
momentum **+** blown-out cross-sectional dispersion **+** positive-funding blow-off (the 2021Q1,
2024Q4 signatures: fnd8h +2–6bp, x_disp 55–189%). This attacks the exact −1.47 short-leg loss in the
worst-10 directly. Caveat: mania is diagnosable with a lag; a month-scale gate catches the
*persistent* mania regimes (helps 2021Q1, 2024Q4 broadly) but misses a one-week blow-off. Pair it
with a short-side selection/stop (below) for the fast spikes.

**2. Vol-targeted sizing — MEDIUM-HIGH, the most mechanically-honest lever.**
The engine already supports `vol_target_ann` (past-only trailing realized-vol scalar). Portfolio
realized vol spikes precisely in the loser months; scaling gross down on trailing vol would auto-shrink
into the persistent high-vol regimes. Honest costs: it is **symmetric** — it also shrinks in
crash months where the book WINS (+2.76% down-month mean) and, worse, it clips the **concentrated
winners** (2020-12, 2024-02 are high-vol too, and §1 says top-10 months = 98.8% of growth). Must be
validated that it doesn't decapitate the right tail. Best as a smooth continuous scaler, not a hard cut.

**3. Drawdown circuit breaker — MEDIUM, tail-insurance not alpha.**
A per-book DD breaker (de-gross after equity DD > X%) caps the depth of 2024-11 (−19.9% intra-month),
2020-11 (−23.4%), 2023-12 (−21.9%) — good for the "succeed in the worst months" mandate — but the
losses are **fast** (intra-week), so it mostly fires AFTER the squeeze and risks locking out the
rebound. Adds little to Sharpe; keep as a maxDD-tail layer on top of #1/#2, not a primary lever.

**4. BTC-crash de-risking — LOWEST / likely NEGATIVE. De-prioritize.**
Unambiguous: the book **makes** +2.59% mean (70% win) across 20 market-crash months, carried by the
short leg (+1.53 aggregate short_px). A generic BTC-drawdown gross cut would **remove the short leg's
crash alpha** — the very thing that makes the book defensive. (`blind_regime.btc_drawdown_scalar`
de-grosses only the LONG leg, which *is* the crash-month loser at −0.89 aggregate, so a long-leg-only
trim is mildly defensible — but its upside is small and it is NOT "crash de-risking of the book".)

### Months NO gross-scaling control could rescue
The **alt-mania short-squeeze blow-offs where the damage is intra-week between weekly rebalances**:
**2024-11, 2021-03, 2020-11, 2024-05, 2023-12.** A gross scalar set at the weekly rebalance from
past-only data cannot see a coin that 3–10×'s in 3 days; by the next rebalance the loss is realized.
Only a **selection change** (don't short names with mania characteristics — accelerating price /
parabolic vol expansion / funding blow-off) or a **per-name short stop-loss / short-side tail cap**
can address those. **2023-09** is a separate, funding-driven loss (negative funding + short price
grind at low BTC vol) that none of the four gross-scaling families would flag.

### One-line redesign thesis
The /005 book is already crash-robust; its fragility is a **short-side alt-mania tail**. The highest-value
redesign is a **mania-aware short leg** (regime-gated short gross + a per-name short tail cap), with a
continuous vol-target as the honest second-moment governor and a DD breaker only as tail insurance —
**BTC-crash de-risking should be dropped from the menu.**
