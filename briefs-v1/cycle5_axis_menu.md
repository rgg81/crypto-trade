# Cycle-5 EXPLORATION Axis Menu — drafted 2026-05-29

## Discipline reminders (locked 2026-05-29)

- **Wall-clock**: EXPLORATION 2h cap, kill at 2.4h (20% margin). CONFIRMATION 8h cap, kill at 9.6h. NO exceptions — Phase 6.0 Critic BLOCKS if estimated modal > cap.
- **No Optuna parallelization, no caching attempts** — user-confirmed tried-and-failed; sequential single-cell is production reality.
- **Single-cohort preference** — fast wall-clock, clean attribution.
- **Diversification is multiplier, not source** — Sharpe lift comes from NEW SIGNAL (features/labels) first; diversification then bundles. AAVE/ATOM dropped because adding symbols without new signal adds noise.
- **Anchor**: BASELINE_V1.md +0.6637 OOS Sharpe (193-feature; valid as stable reference regardless of iteration feature count).
- **Single-axis discipline**: each EXPLORATION varies ONE element only.
- **Comparison**: F1 OOS Sharpe Δ vs baseline; Critic checks anti-cheating + anti-look-ahead + methodology + wall-clock.
- **NO side scripts** — verdict from `comparison.csv` only; no `analysis/iteration_v1-NNN/*.py` diagnostic generation.

## Strategic framing for cycle-5

User-aligned priors (2026-05-29): Sharpe lift comes from signal sources first, diversification multiplies. AAVE/ATOM universe-expansion dropped from initial menu — replaced with stronger signal-source candidates.

Cycle-5 pivots toward:
1. **Crypto-native signals NOT derivable from OHLCV** — liquidations, funding velocity, basis, on-chain proxies. Highest-prior axes since v3 cycle-7 closed cross-asset OHLCV; v1 has NOT systematically explored crypto microstructure. → /034-/038
2. **Labeling architecture** — triple-barrier σ_t has been the only labeling primitive since /014. Trend-scanning (AFML Ch.5) is the natural NEXT. → /039
3. **Risk primitives + architecture** — protect existing alpha, build runtime safeguards. → /040-/043

## Proposed 10 EXPLORATIONs (revised 2026-05-29)

### Wave 1 — NEW signal sources (5 iterations; signal-first priority)

**/034 — Liquidations volume z-score (NEW feature family)**
- Data: Binance forced-liquidation feed (Coinglass / Binance public force-order CSV)
- Feature: per-symbol 24h liquidation USD volume z-score over 30d window
- Hypothesis: liquidation cascades → mean-reversion (squeeze) OR trend acceleration; sign-conditional alpha
- Wall-clock: 1.5h modal / 2.4h cap

**/035 — Open-interest velocity (orthogonal to /025 OI level)**
- Feature: OI 24h rate-of-change / 90d std (velocity z-score)
- /025 tested OI LEVEL → LEARNED-NEG-CAT. Velocity captures REGIME CHANGE; structurally different
- Wall-clock: 1.2h modal / 2.4h cap

**/036 — Funding-rate velocity (sign-conditional, NEW)**
- Feature: 24h funding rate change normalized by 30d std
- /023 tested funding LEVEL z-score → LEARNED-NEG. VELOCITY signal independent
- Hypothesis: positive funding velocity → leverage building → squeeze setup. Negative funding velocity → short stress → potential bounce
- Wall-clock: 1.0h modal / 2.4h cap

**/037 — Volume imbalance z-score**
- Feature: `taker_buy_volume / quote_volume` z-score over 14d window (z-scored version of existing `vol_taker_buy_ratio`)
- Hypothesis: high taker-buy = aggressive buying → trend continuation prior
- Wall-clock: 1.0h modal / 2.4h cap

**/038 — On-chain proxy: exchange net flow (BOLD)**
- Feature: estimated Binance net exchange flow (deposits − withdrawals) z-score over 14d (from publicly aggregated data feeds — Glassnode-style proxies or CryptoQuant if available; fallback to derived-from-OI as a coarse proxy)
- Untouched signal category in v1; structurally orthogonal to OHLCV + funding + OI
- Wall-clock: 1.8h modal / 2.4h cap (data fetch cost factored)
- Risk: data availability fallback — if no clean source, replace with **basis (perp − spot) z-score** as alternative signal-source NEW family

### Wave 2 — Labels (1 iteration)

**/039 — Trend-scanning labels (López de Prado AFML Ch.5)**
- Replace triple-barrier σ_t with Wald-test trend-direction labels over forward 21-bar window
- HIGH-RISK declared (changes Optuna training-objective domain)
- Wall-clock: 1.8h modal / 2.4h cap

### Wave 3 — Risk + architecture (4 iterations)

**/040 — Sortino objective in Optuna**
- Optuna objective = mean / downside_std instead of mean / std
- Trains model to maximize downside-protected return
- Wall-clock: 1.0h modal / 2.4h cap

**/041 — Per-symbol vol-target ceiling**
- Pre-trade: if symbol's 14d RV > 80th percentile trailing 90d, scale down position by 0.5×
- Stateless gate orthogonal to /010 R5 (which was floor)
- Wall-clock: 0.8h modal / 2.4h cap

**/042 — Cross-symbol correlation gate**
- Pre-trade: if BTC ↔ ETH 30d correlation > 0.90, kill non-BTC/ETH trades
- Forces diversification only when correlation actually provides it
- Stateless gate
- Wall-clock: 0.8h modal / 2.4h cap

**/043 — Per-trade Kelly sizing**
- Replace uniform position sizing with `f* = (μ × (b+1) − 1) / b` where μ = predicted edge (LightGBM proba × magnitude), b = TP/SL ratio
- Sizing scales with model confidence × edge magnitude — more informative trades get larger positions
- Wall-clock: 1.0h modal / 2.4h cap

## Cadence + Routing

- /034-/043 are 10 EXPLORATIONs at v1 standard (n_trials=18, ENSEMBLE_SIZE=3, 2h cap / 2.4h kill)
- Estimated cycle-5 aggregate wall-clock: ~12-14h across all 10 (1-2h each)
- After /043 → **/044 CONFIRMATION** = bundle of PROMISING ingredients from /034-/043
- /044 substrate determined by which axes fire PROMISING (F1 OOS Sharpe Δ ≥ +0.20)

## Execution order (run in this sequence)

1. /034 Liquidations (highest novelty, may have data fetch overhead)
2. /035 OI velocity (low data risk, cached from /025)
3. /036 Funding velocity (cached from /023)
4. /037 Volume imbalance (no data fetch)
5. /038 On-chain exchange flow (BOLD; falls back to basis if data unavailable)
6. /039 Trend-scanning labels (structural label change)
7. /040 Sortino objective (loss function change)
8. /041 Per-symbol vol-target ceiling (stateless gate)
9. /042 Cross-symbol correlation gate (stateless gate)
10. /043 Per-trade Kelly sizing (sizing change)

Front-load high-novelty signal axes; risk + sizing changes at end.

## Critic scope (locked 2026-05-29)

Critic checks:
1. Anti-cheating (no OOS tuning, no IS window trimming)
2. Anti-look-ahead (walk_forward.py:113, embargo, past-only labels/features)
3. Anti-methodology-mistake (CV gap, training_months, dispatch defects)
4. Anti-seed-fragility (reproducible with same seed)
5. **Wall-clock validation (Mini-Check L) is BLOCKING** — if modal > cap, BLOCK + brief must reduce scope

Critic does NOT:
- Compare trade-roster overlap (V3 metric retired)
- Demand frozen-HP ablations
- Generate side scripts or supplementary diagnostics
- Authorize wall-clock exceptions

## Backtest improvements to build into runner (anti-issue prevention at source)

These are CODE changes to backtest itself, not side scripts:
1. **Runtime wiring assert**: `assert lightgbm_model._actual_sample_weight is not None when sample_weight_mode != "uniform"` — fail fast at trial 0
2. **Reproducibility smoke test**: 60-second test runs single cell baseline seed=42, asserts bit-identical across 2 invocations. Pre-Phase-6 gate.
3. **Live-engine parity test**: same model loaded by backtest + live produces bit-identical predictions on same bar
4. **Wall-clock projection**: runner emits `[wall_clock] model=X month=Y elapsed=Zs projected_total=Wh` per month. Kill BEFORE cap, not after.
5. **Foundation regression expansion**: more tests in tests/test_lookahead_embargo.py covering edge cases

These build during cycle-5 execution (1 per 2-3 iterations) — not a separate framework project.

## What I'd defend if pushed

**Highest expected lift**: /034 Liquidations + /039 Trend-scanning labels (true new signal sources)
**Lowest-risk fast wins**: /037 Volume imbalance + /041 Per-symbol vol ceiling
**Boldest bet**: /038 On-chain exchange flow — UNTOUCHED signal category; success unlocks cycle-6+ on-chain feature family

If data fetch for /034 or /038 takes > 30 min in budget, swap to next-priority axis and revisit data fetch separately.
