# LightGBM Master Advisory — iter-v1/091 (R-CONV)

Seat ETH/064 (IS +0.2383/OOS +0.5171, 198 IS/81 OOS trades). Axis: post-aggregator conviction skip gate `_sp_confidence<τ→NO_SIGNAL`, τ=0.06 (net seed agreement ≤2/50), opt-in default OFF, same RULE-layer band as /074 AXIS-R + /084 R-FADE (lgbm.py:2179-2229). LOCK confirmed (50×30×depth-5×leaves-31×24mo, single outer seed, fail-fast=2.0). No HP recs (post-aggregator, Optuna domain untouched). OOS read for advisory diagnostics ONLY — τ was set IS-only (correct, unchanged).

## 1. Conviction-as-gate mechanics — abstention/disagreement conflation REAL but addressable
`_sp_confidence=|n_long−n_short|/50` conflates (a) abstention (seeds vote 0, below own threshold) with (b) directional disagreement (+100 cancel −100). The gate can't distinguish from net alone, but `_ensemble_std` (logged per candle) CAN. The IS dropped set = 46 trades at |net|=1 + 21 at |net|=2 (thin 1-2-seed-tie tail). Abstention-tail = genuine low-SNR (defensible skip); disagreement-tail = coin-flips (NOT reliably noise). **REQUIRED 7.4: persist specialist_dispersion.csv + split the dropped set by ensemble_std — else a VALIDATED verdict can't tell a real SNR filter from a lucky IS coin-flip partition.**

## 2. τ=0.06 magnitude — modal F1 ≈ +0.10 to +0.14 (TENTATIVE, below +0.20)
Removing 67 net-losing trades (−5.43%/37.3% WR) from a 198-trade/+15%/+0.24-Sharpe seat = ~36% PnL-density improvement on the kept set. BUT the genuinely-toxic [0.12,0.20) block (−31.27%) is KEPT at τ=0.06, and Optuna re-fits nothing (post-hoc gate). +0.20 reachable only if the dropped tail disproportionately clears clustered losing-DAYS (Sharpe is day-level) — ~30% prob. **Modal F1 ≈ +0.10-0.14 = TENTATIVE/FLAT, sub-threshold.**

## 3. R-CONV × R5 vol-targeting — mild CONFLICT not compounding
Orthogonal (no double-count), but R-CONV thins the trade count ~34% IS → R5's rolling realized-vol estimate runs on a smaller sample → slightly NOISIER vol-target scaling. Net small (R5 is 45-day daily-PnL window). Don't credit R-CONV with exposure-shaping; it slightly degrades R5's sample.

## 4. Selection-bias — ρ(conf,hold)=+0.046 guard NECESSARY but NOT SUFFICIENT
Hold-duration is a coarse vol proxy. The subtler confound: **conviction-as-TREND-regime** — net agreement spikes when the trend is clean (all momentum-feature seeds align), collapses to coin-flips in choppy/range regimes, INDEPENDENT of vol level. So ρ(conf,NATR) can be ~0 while conviction proxies trend-vs-range. **REQUIRED F4 addition: ρ(conf, |ret_5d| or trend-strength feature) on kept-vs-dropped, OOS. The NATR guard alone could PASS while the gate is silently a trend-regime filter.**

## 5. Trade-rate floor — F3 HOLDS (ruled low)
OOS conviction p10=0.040, p25=0.160; at τ=0.06 OOS keeps 72/81 (89%, drops 9) — 44% headroom over the 50 floor. OOS conviction distribution is shifted HIGHER than IS (OOS median 0.300 vs IS 0.120) → OOS filter rate (11%) LOWER than IS (34%). NEGATIVE-OVERFILTER ~2-3%, not the QR's 8%.

## 6. Modal verdict (advisory)
**DECISIVE FINDING: the IS dropped-tail-net-losing does NOT replicate OOS.** At τ=0.06 the OOS dropped set is **+6.25% / 44.4% WR** — mirror-opposite of IS (−5.43%/37.3%). The monotone IS conviction→edge gradient is ABSENT/inverted in ETH's OOS window. R-CONV will skip 9 OOS candles that were aggregate-PROFITABLE. Mechanically engages (F2 ✓), floor holds (F3 ✓), but it removes OOS-profitable candles.
- NEGATIVE-NO-EFFECT (F2 engaged, F1 flat/slightly-neg OOS): **~45%**
- TENTATIVE/FLAT (IS Δ [0,0.20)): **~30%**
- VALIDATED (IS Δ ≥+0.20): **~15%** (needs day-clustering luck)
- NEGATIVE-REGIME-PROXY (F4): **~8%** (trend-regime confound, §4)
- NEGATIVE-OVERFILTER/INERT: **~2%/~0%**

## Closing (confidence MEDIUM)
Single most important: **the IS low-conviction→net-losing gradient does not replicate in ETH OOS (dropped set +6.25% not −5.43%).** NOT a reason to change τ pre-Phase-6 (that's the uncertainty the backtest resolves; τ stays pre-registered IS-only). But Phase 7.4/7.5 MUST read any IS-positive F1 against this OOS sign-flip — an IS-only +0.20 with flat/negative OOS Δ is the IS-overfit-threshold signature, NOT a bundle-wide primitive. Split the dropped set by ensemble_std (§1); add the trend-strength F4 proxy (§4). No multi-seed.
