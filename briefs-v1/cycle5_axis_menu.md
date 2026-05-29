# Cycle-5 EXPLORATION Axis Menu — drafted 2026-05-29

## Discipline reminders

- **Skill v1 (reverted)**: EXPLORATION default n_trials=18, ENSEMBLE_SIZE=3, 2h wall-clock cap
- **Anchor**: BASELINE_V1.md +0.6637 OOS Sharpe (193-feature; valid as stable reference regardless of iteration feature count)
- **Single-axis discipline**: each EXPLORATION varies ONE element only
- **Comparison**: F1 OOS Sharpe Δ vs baseline; Critic checks anti-cheating + anti-look-ahead + methodology
- **70/30 rule**: 70% NEW signal sources (features/symbols), 30% architecture/risk

## Strategic framing for cycle-5

Cycles 1-4 explored most STRUCTURAL axes within current symbol set / OHLCV features / triple-barrier labels. Cycle-5 should pivot toward:
1. **Crypto-native signals NOT derivable from OHLCV** — liquidations, funding velocity, basis, on-chain proxies. Highest-prior axes since v3 cycle-7 closed cross-asset OHLCV; v1 has NOT systematically explored crypto microstructure.
2. **Universe expansion** — 5 symbols (BTC/ETH/LINK/LTC/DOT) is small. Adding 1-2 new cohorts at a time tests denominator expansion.
3. **Labeling architecture** — triple-barrier σ_t has been the only labeling primitive since /014. Trend-scanning (AFML Ch.5) is the natural NEXT.

## Proposed 10 EXPLORATIONs

### Wave 1 — NEW signal sources (4 iterations; 70% rule)

**/034 — Liquidations volume z-score (NEW feature family)**
- Data: Binance forced-liquidation feed (`fapi/v1/forceOrders` historical / sourceable via aggregated daily CSV)
- Feature: per-symbol 24h liquidation USD volume z-score over 30-day window
- Hypothesis: liquidation cascades precede mean-reversion (squeeze) or trend acceleration; sign-conditional alpha
- Wall-clock: 1.5h (5 syms × n_trials=18 × pruned + data fetch ~15 min)
- Risk: data fetch cost (per /025 lesson — count as inside budget); fall back to publicly available daily-aggregate if API rate-limited

**/035 — Open-interest velocity (NEW feature; orthogonal to /025 OI level)**
- Feature: OI 24h rate-of-change normalized by 90d std (OI velocity z-score)
- /025 tested OI LEVEL z-score and got LEARNED-NEG-CAT
- VELOCITY captures regime change (OI building up before move); structurally different from level
- Wall-clock: 1.2h (data already cached from /025)

**/036 — Volume imbalance feature (taker_buy / quote ratio)**
- Feature: `taker_buy_volume / quote_volume` z-score over 14-day window (already partial in `vol_taker_buy_ratio`; this is the z-scored version)
- Hypothesis: high taker-buy ratio = aggressive buying → trend continuation prior; low ratio = mean-reversion setup
- Wall-clock: 1.0h (no new data; feature computed in-place)

**/037 — Volatility-of-volatility (VVIX-equivalent)**
- Feature: std of `vol_natr_21` over rolling 60-day window
- Captures regime instability; high VVIX → uncertain market, lower signal quality expected
- Could be USED as feature OR as REGIME GATE (Wave 3 candidate); EXPLORATION tests it as feature first
- Wall-clock: 0.8h

### Wave 2 — Universe expansion (2 iterations)

**/038 — Add AAVE (single new symbol, pure isolation)**
- Add AAVEUSDT to V1_EXCLUDED_SYMBOLS removal list
- Train Model F (AAVE specialist): single-cohort like /018 LINK approach
- 4+ years Binance Futures history; mid-cap; idiosyncratic alpha potential
- Wall-clock: 1.0h (single-cohort fast)

**/039 — Add ATOM (single new symbol, pure isolation)**
- Add ATOMUSDT specialist
- Cosmos ecosystem; different correlation profile than EVM tokens
- Wall-clock: 1.0h

### Wave 3 — Structural architecture (4 iterations; 30% rule)

**/040 — Trend-scanning labels (López de Prado AFML Ch.5)**
- Replace triple-barrier σ_t with Wald-test trend-direction labels
- Labels = sign of statistically-significant trend over forward 21-bar window (Bailey + López de Prado §5.5)
- HIGH-RISK declared (changes labeling = Optuna training objective domain)
- Wall-clock: 1.8h (labeling rebuild + retrain)

**/041 — Sortino objective in Optuna (downside-only deviation)**
- Optuna objective = mean / downside_std (Sortino) instead of mean / std (Sharpe)
- Trains model to maximize downside-protected return; should improve Calmar at modest Sharpe cost
- Wall-clock: 1.0h (just objective function change)

**/042 — Per-symbol vol-target ceiling (NEW risk primitive)**
- Pre-trade: if symbol's 14-day realized vol > 80th percentile of trailing 90-day, scale down position by 0.5×
- Stateless gate; orthogonal to /010 R5 (which was vol-target floor)
- Wall-clock: 0.8h (post-Optuna gate)

**/043 — Cross-symbol correlation gate**
- Pre-trade: if BTC ↔ ETH 30-day correlation > 0.90, kill non-BTC/ETH trades
- Forces diversification when major coins co-move (no diversification benefit available)
- Stateless gate; addresses /027/032 concentration concern at architectural level
- Wall-clock: 0.8h

## Cadence + Routing

- /034–/043 are 10 EXPLORATIONs at v1 standard config (n_trials=18, ENSEMBLE_SIZE=3, 2h cap)
- Estimated cycle-5 total wall-clock: ~11-12h aggregate (1-2h per iteration)
- After /043 → **/044 CONFIRMATION** = bundle of PROMISING ingredients from /034-/043
- /044 substrate determined by which axes fire PROMISING (≥ +0.20 OOS Sharpe Δ at single-seed)

## Critic scope reminder (per skill v1 reverted)

Critic checks anti-cheating, anti-look-ahead, anti-methodology-mistake, anti-seed-fragility. **NOT** trade-roster overlap. **NOT** basin-lottery framing. Each EXPLORATION measured against BASELINE_V1.md +0.6637 OOS Sharpe stable anchor — different configs producing different trades is expected and correct.

## Open questions for QR to decide at each iteration

1. Data fetch for liquidations (/034) — is the historical feed accessible? If not, fall back to Coinglass aggregated daily.
2. Trend-scanning (/040) HIGH-RISK declaration — should we run it at CONFIRMATION-spec wall-clock instead?
3. Order of execution — Wave 1 (signal sources) first vs Wave 2 (universe) first?

## Order recommendation

Run in this order to maximize info:
1. /034 Liquidations (highest novelty)
2. /035 OI velocity (low data risk, fast)
3. /037 VVIX feature (no data fetch)
4. /036 Volume imbalance (no data fetch)
5. /038 AAVE specialist (test universe expansion fast)
6. /040 Trend-scanning labels (NEW labeling architecture)
7. /039 ATOM specialist
8. /041 Sortino objective
9. /042 Per-symbol vol-target ceiling
10. /043 Cross-symbol correlation gate

Sequenced to front-load high-novelty axes; structural changes after fast feature-additions.

## What I'd defend if pushed

**Most novel + highest expected lift**: /034 Liquidations + /040 Trend-scanning labels
**Lowest-risk fastest wins**: /037 VVIX + /042 per-symbol vol ceiling
**Boldest bet**: /038-/039 AAVE+ATOM universe expansion (if both PROMISING → cycle-6 could bundle 7-symbol universe)

If you want to TRIM the list, the 2 I'd cut first: /039 ATOM (redundant with /038 AAVE in spirit) and /036 volume imbalance (incremental on existing volume features).

If you want to BOLD the list further: replace /041 Sortino with **on-chain feature family** (Glassnode-style proxies: SOPR, MVRV, exchange inflow/outflow) — this is the BIG untouched signal category. Same wall-clock; higher upside; higher data-fetch risk.

Your call on edits before /033 finishes. Otherwise this menu is what I'll execute starting once /033's verdict lands.
