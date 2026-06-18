# Diary — iter-v1/044-046 (ZECUSDT) — establish ZEC baseline (low-corr portfolio coin) — NEGATIVE: ZEC's trend edge is IS-negative; the low-corr⟂trend tension

**Context:** user steered the portfolio path to a LOW-CORRELATION coin (for genuine diversification /
independent edge). Data-driven pick = ZEC (Zcash): 0.59 corr to BTC/ETH (lowest among liquid coins),
$285M liquidity, privacy-coin idiosyncratic, full history. Data fully prepped (perp+spot+funding+OI,
19/19 v1 features, 2020-02→2026-06). Tested the proven v1 trend stack in 3 configs.

## Result — ZEC fails the v1 trend approach across ALL 3 configs (every config IS-negative)
| config | IS Sharpe | OOS Sharpe | both-positive? |
|---|---|---|---|
| iter-044 deterministic-core, R2-OFF | −0.1841 | +0.8463 | ✗ (IS<0) |
| iter-045 deterministic-core, R2-ON (ZEC-cal 7.57/30.27/0.20) | −0.6629 | +0.4688 | ✗ (R2 over-braked, worse) |
| iter-046 model-gated (LightGBM selects entries), R2-OFF | −0.2673 | +0.8527 | ✗ (IS<0) |

- **ZEC's trend-direction edge is fundamentally NEGATIVE on its 2020-2025 IS history.** Neither the
  deterministic-all-entries core NOR the model-gated entry-selection can produce a positive IS — the
  underlying 200-SMA trend-state direction LOSES on ZEC (it whipsaws; ZEC is choppy/idiosyncratic).
- **The consistently-strong OOS (+0.85) is REGIME-LUCK, not a generalizing edge** — it's the 2025 ZEC
  rally (a single big trend the core caught). The negative IS proves it does NOT generalize backward.
  Classic inverse-overfit signature (IS−/OOS+); the cardinal rule forbids chasing it.
- R2 (DD brake) made it WORSE (iter-045), same over-brake as DOT — R2 calibration is coin-specific and
  cut ZEC's productive periods.

## ROOT FINDING — the low-correlation ⟂ trend-tradability TENSION (strategic)
**Low-correlation coins are low-correlation BECAUSE they're idiosyncratic and don't follow the market
trend** (ZEC's privacy-coin demand is independent of BTC → its price action is choppy/uncorrelated →
no clean trend). But the v1 method is TREND-FOLLOWING (it works on ETH precisely because ETH trends
strongly with the market). So the user's diversification goal (low-corr) is in direct tension with the
v1 method (trend). The correlated majors (LINK/LTC/DOT, 0.72-0.76) trend WITH BTC but duplicate its beta
(no diversification) — and even they failed the deterministic core. The genuinely-diversifying low-corr
coins (ZEC) don't trend → the trend method fails on them.

## The decision (surfaced to user) — the low-corr-portfolio-via-trend path hit a fundamental wall
Options: (1) try ANOTHER low-corr coin — but the tension likely recurs (low-corr ⟹ choppy ⟹ trend-hard);
worth checking if SOME low-corr coin has a positive trend-IS (each needs the full data-prep saga).
(2) ACCEPT the tension: the v1 trend portfolio is limited to trend-tradable coins (ETH strong, BTC modest);
genuine low-corr diversification isn't achievable via trend-following. (3) Develop a NON-trend edge
(mean-reversion / stat-arb) suited to choppy low-corr coins — a different method (bigger effort;
mean-reversion already failed on ETH at 8h, iter-032). (4) Consolidate the ETH win + revisit.

ZEC is NOT a v1 baseline. The ETH iter-034 breakthrough (OOS +0.41) remains the session's headline win;
BTC iter-020 the modest second. (Note: ZEC data is now fully prepped + cached, so a future non-trend
ZEC edge could be tested without re-fetching.)
