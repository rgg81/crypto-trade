# v2 research notes — what generalizes OOS on crypto mid-cap perps (web lit review, 2026-06)

Motivation: rank-21–40 trend+carry is regime-faded (anchor OOS≈0); raw XS-mom marginal. Searched the
literature for cross-sectional factors that SURVIVE out-of-sample on crypto perps, to pick next axes.

## Findings (with the implication for THIS cohort)
1. **Residual / beta-neutralized momentum is the standout.** "Residual momentum removes exposure to
   common risk factors (market/size/value)… produces higher Sharpe and lower volatility… avoids the
   periodic crashes standard momentum suffers." Standard momentum is partly factor (beta) exposure.
   → **Directly fixes the anchor's failure**: mid-cap directional trend died because it is BTC-beta-
   coupled and that beta went dead in 2024–26. Residualize each coin's return vs BTC, momentum on the
   residual, cross-sectional rank, dollar-neutral. **Computable from on-disk klines (BTCUSDT present).**
   → **iter-v2-004 lead axis.**
2. **Crypto carry (funding) is REGIME-FADED.** Carry Sharpe ≈6.45 full-sample (2020–25), falls to 4.06
   in 2024, **turns NEGATIVE in 2025**. → A funding-rank book is risky NOW; consistent with the anchor's
   λ-leaning-to-carry not rescuing LATE. **De-prioritize standalone funding-rank.**
3. **Momentum is short-horizon (1–4 weeks, strongest ~2wk); RAW cross-sectional momentum is weak,
   beta-adjusted survives.** DS3 model = market + 2-week momentum (MOM2) + residual momentum (RMOM).
   → Matches iter-v2-002 (raw XS-mom L=84 marginal). The signal to revive is RESIDUAL + short horizon,
   not raw price-rank. Combine with #1.
4. **XS-mom works best on top-40 mcap; smaller tokens face liquidity limits.** → rank 21–40 is inside
   the viable band but at the thin edge — reinforces the cost-sensitivity (2×-taker kill) seen in /002.
5. **Basis (perp–spot) is the STRONGEST cross-sectional predictor** (basis, momentum, basis-momentum all
   significant). → Promising but needs SPOT prices (not on disk). v1 rejected basis on top-20 (/017);
   could differ on mid-caps. **Deferred (data gap)** — would need spot klines fetch.
6. **Size effect DISAPPEARED OOS; left-tail (downside) risk effect APPEARED; reversal alive.** → size is
   dead; a downside-risk or short-term-reversal overlay is a candidate.
7. **A "trend factor" (Han-style: combine multiple MAs via a forecasting regression into one
   cross-sectional trend signal)** beats simple sign-of-return trend cross-sectionally. → The ML model
   (iter-v2-003) approximates this; if ML underperforms, a explicit trend-factor is a fallback.
8. **Liquidation-cascade alpha is mostly BTC beta** (one study: Sharpe 3.58 but 54% BTC, alpha
   p=0.182). → consistent with v1 rejecting liquidation-fade (/011). **Skip.**

## Implied axis priority for v2 (post-ML)
- **iter-v2-004: RESIDUAL (BTC-beta-neutralized) momentum, cross-sectional, dollar-neutral.** Highest EV:
  literature-backed OOS survivor, mechanism-aligned with the anchor's exact failure, on-disk-computable.
  Test short + medium residual-momentum lookbacks (≈2wk/4wk). Era-split + 2×-taker gates as usual.
- **iter-v2-005: residual-momentum × regime gate** (lean in when trend-health low) — the regime-
  conditional idea, now on the residual signal instead of raw XS-mom.
- **Feature for ML:** ensure iter-v2-003's feature set includes BTC-beta-neutralized momentum
  (add if the base ML shows promise but misses it).
- **Deferred:** basis (needs spot fetch); funding-rank (regime-faded); reversal/downside (after the above).

## Sources
- Cross-Sectional Alpha Factors in Crypto (unravel.finance) — XS-mom ~30d top-40, enhanced carry,
  arithmetic-avg combine. https://blog.unravel.finance/p/cross-sectional-alpha-factors-in
- Crypto carry regime fade (Sharpe 6.45→neg 2025) — arXiv 2510.14435 "Cryptocurrency as an Investable
  Asset Class"; BIS WP 1087 "Crypto carry".
- Factor OOS survival / DS3 (MKT+MOM2+RMOM), size-effect death, left-tail — ScienceDirect "Taming crypto
  anomalies: a Lasso-type factor model"; "Cryptocurrency anomalies and economic constraints".
- Residual momentum (higher Sharpe, fewer crashes) — general factor lit; crypto trend factor:
  Cambridge JFQA "A Trend Factor for the Cross Section of Cryptocurrency Returns".
- Basis strongest XS predictor — cross-sectional crypto futures factor studies (2017–21 sample).
- Liquidation alpha ≈ BTC beta — Medium "Chasing Liquidation Cascade Alpha" (54% BTC, alpha p=0.182).
