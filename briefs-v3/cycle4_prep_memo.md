# Cycle-4 Preparatory Research Memo — Derivatives-Microstructure Re-Architecture

**Status**: PREPARATORY research memo — NOT a formal iteration brief. Untracked (do NOT commit; a backtest is running concurrently on `iteration-v3/092`). The iter-v3/093 QR picks this up and formalizes the /093 brief.
**Author role**: Quant Researcher (QR), v3
**Date**: 2026-05-17
**Branch context**: `iteration-v3/092` worktree (iter-v3/092 CONFIRMATION backtest in flight)
**Scope**: De-risk cycle 4 (opening at iter-v3/093) BEFORE the formal /093 design. The single most important open question is **data availability** for the /091-recommended derivatives-microstructure direction.

---

## 0. Executive summary

**The derivatives-microstructure direction is FEASIBLE and is the recommended cycle-4 axis.** All three data legs exist or are straightforwardly fetchable with infrastructure already in the worktree:

| Data leg | Status | Source |
|---|---|---|
| Funding rate | **ALREADY FETCHED** — 25 symbols, 2019/2020→2026 | `data/funding_rates/*.csv`; `crypto-trade fetch-funding` CLI |
| Perp-spot basis (spot klines) | **ALREADY FETCHED** — 23 symbols, full v3 window | `data/spot/<SYM>/8h.csv`; `crypto-trade fetch-spot` CLI |
| Open interest + long/short ratios | **NOT FETCHED — but straightforwardly fetchable** | data.binance.vision `metrics` archive, daily ZIPs from 2020-09 |
| Liquidation flow | **NOT directly available** at usable history depth — use OI-delta + funding extremes as the deleveraging proxy | (see §1.4) |

The "funding features are ABSENT-banned" report is **a policy choice, not a data gap** — closed-axis discipline from iter-v3/082, with the data and fetch code deliberately retained. The one genuine prerequisite for cycle 4 is a **dedicated open-interest fetch step** (`fetch-oi` subcommand) at iter-v3/093 setup — small, ~1-2h of engineering, parallel to the existing `fetch-spot`. **Recommendation: cycle 4 proceeds with Candidate A (derivatives-microstructure state-conditioning), with the OI fetcher as /093's setup work.**

---

## TASK 1 — Data Availability (the critical de-risking finding)

### 1.1 — What is in `data/`

`data/` is 2.8 GB, ~769 symbol directories of perp 8h klines (`<SYM>/8h.csv`). Two derivatives-relevant sub-trees already exist:

- **`data/funding_rates/`** — 25 CSVs, schema `funding_time,funding_rate`. Coverage (rows / first settlement):
  - BTCUSDT 7295 rows, 2019-09-10 → 2026-05-07
  - BCHUSDT 7020, 2019-12-19 → 2026-05-16
  - LDOUSDT 3997, 2022-09-22 → 2026-05-16
  - TRXUSDT 6940, 2020-01-15 → 2026-05-16
  - Plus AAVE, ADA, ALGO, ATOM, AVAX, AXS, CHZ, CRV, EOS, GALA, GRT, HBAR, ICP, MANA, MKR, RUNE, SAND, THETA, VET — i.e. essentially the 22-symbol cross-sectional `XS_UNIVERSE`.
  - **DATA-QUALITY FLAG**: `FILUSDT.csv` is empty (header only, 0 rows). FTM/MKR funding stops mid-2025 (FTM 2025-06-19, MKR 2025-09-08) — likely delistings/rebrands. The /093 QR must re-run `fetch-funding` and screen per-symbol completeness before relying on any symbol.
- **`data/spot/`** — 23 symbol directories of spot 8h klines (11-col kline schema), e.g. `data/spot/BCHUSDT/8h.csv` 7087 rows 2019-11-28→2026-05-17. Built at iter-v3/086 for the perp-spot basis. Full v3-window coverage.

### 1.2 — The "funding ABSENT-banned" report: policy, not data gap

`run_baseline_v3.py` has a pre-flight block (lines ~344-466) that **raises** if any of these are in `V3_FEATURE_COLUMNS`: `funding_rate_zscore_30`, `btc_funding_rate_zscore_30`, the 4 `/082` funding-family columns (`funding_sign_persist_9`, `funding_momentum_3`, `funding_accel_3`, `funding_price_divergence_6`), `funding_regime_momentum_5d`, the 3 `/086` basis columns.

This is **closed-axis discipline**, the documented `feedback_v3_inert_features_at_higher_budget.md` pattern: an INERT feature must not be carried forward OR retested at higher Optuna budget. It is **not** an absent-data assertion. The diaries are explicit:

- iter-v3/082 §10: *"The `funding_v3.py` `compute_funding_family` function and the `funding_family_v3` GROUP_REGISTRY entry are left as harmless unreferenced infrastructure at zero revert cost."*
- iter-v3/086 §1 / runner line ~428: *"The fetch-spot subcommand, basis_v3.py, and data/spot/ cache are RETAINED as reusable infrastructure."*

What iter-v3/019/082/086 actually used as their data source:
- **iter-v3/019** (`funding_rate_zscore_30`) and **iter-v3/082** (4-channel funding family) both read `data/funding_rates/<SYM>.csv`, fed by the `crypto-trade fetch-funding` CLI (`main.py:_cmd_fetch_funding`, hits `/fapi/v1/fundingRate`). **That data and fetch code are still in the worktree.**
- **iter-v3/086** (perp-spot basis) read `data/spot/<SYM>/8h.csv`, fed by `crypto-trade fetch-spot` (`main.py:_cmd_fetch_spot`, data.binance.vision monthly spot archives + `/api/v3/klines` fallback). **Still in the worktree.**

**Bottom line**: the funding and basis data feeds are LIVE and current (through 2026-05-16/17). Cycle 4 is not starting from zero on the derivatives-data front — it is starting with two of three legs already built and a closed-axis ban that the /093 brief simply does not trip (Candidate A is a new *architecture*, not the banned single-z-score *feature* bolted onto the price model).

### 1.3 — Why iter-v3/082 closing the funding axis does NOT close Candidate A

iter-v3/082's verdict was SUSPICIOUS-OOS-DOMINANT / INERT-by-importance: funding *features* ranked 15-18/18 because they were bolted onto a **price-barrier-labelled per-symbol LightGBM**. The model's label was a price move; funding was a weak side-input the tree barely split on. Candidate A is the opposite construction — **the label itself is a derivatives-microstructure object** (forward realized-vol regime, or forward deleveraging-event probability). When the prediction target IS the derivatives state, funding/OI/basis are the primary signal, not a 4%-importance afterthought. The /082 closeout (§11 Rec 1) names exactly this: a 5th funding attempt is allowed if it is *(a) a multi-symbol-pooled model* or *(b) open-interest data* — "Neither is a funding-axis retread; both are different axes." Candidate A is both.

### 1.4 — Open interest and liquidations: the fetch-feasibility question

**Funding fetch** — exists (`fetch-funding`). `/fapi/v1/fundingRate` paginates full history; the cache is incremental. No work needed beyond a refresh.

**Open-interest fetch** — does NOT exist in the codebase (`grep` of `client.py`/`fetcher.py`/`bulk.py`/`discovery.py`/`main.py` finds zero OI references). The naive REST route is a dead end: `GET /futures/data/openInterestHist` **serves only the latest 1 month** ([Binance OI Statistics docs](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics)) — useless for a 2022→2026 walk-forward.

**But the historical OI feed exists on data.binance.vision** — I verified the S3 bucket directly:
- Path: `data/futures/um/daily/metrics/<SYMBOL>/<SYMBOL>-metrics-YYYY-MM-DD.zip` — one daily ZIP, ~12 KB each.
- Coverage verified: BTCUSDT from **2020-09-01**; TRXUSDT / GALAUSDT / HBARUSDT from **2021-12-01**; LDOUSDT from **2022-09-22** (its listing date). **This covers the entire v3 walk-forward window** (training from 2020-04, OOS 2025-03→2026-05; LDO simply has no pre-listing history, same as its kline/funding data).
- Schema verified (probed `BTCUSDT-metrics-2024-01-01.zip`, 11 KB): `create_time, symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio` at **5-minute granularity** — trivially resampled to the v3 8h bar.

This is a genuine bonus: the `metrics` archive carries **OI + OI-value + three long/short positioning ratios** in one file. The taker long/short volume ratio is a partial liquidation/aggression proxy.

**True liquidation data** — Binance does NOT publish a deep historical liquidation archive (the `forceOrder` websocket is real-time only; data.binance.vision has no liquidation tree). This is the one genuinely-missing leg. Mitigation: the deleveraging signal is *reconstructable* from OI + price + funding — a sharp OI **drop** concurrent with an adverse price move IS a deleveraging cascade fingerprint (the literature's "20% OI drop ≈ deleveraging regime"). Candidate A should treat `liquidation flow` as a **derived feature** (`oi_delta` × adverse-return interaction), not a fetched feed. Third-party vendors (Coinglass, Amberdata, CryptoQuant) sell liquidation history, but introducing a paid external feed is out of scope for a v3 iteration.

### 1.5 — TASK 1 verdict

**A derivatives-microstructure architecture CAN be built with data that already exists or is straightforwardly fetchable.**

- Funding: already fetched, current, 25 symbols. Zero prerequisite.
- Basis (spot klines): already fetched, current, 23 symbols. Zero prerequisite.
- Open interest + L/S ratios: **NOT fetched, but the data exists** on data.binance.vision (`metrics` archive, daily ZIPs, 2020-09→present, all v3 symbols covered). Prerequisite = a `fetch-oi` CLI subcommand. **Size estimate: small.** It is a near-clone of the existing `fetch-spot` (`_cmd_fetch_spot` already downloads, unzips, dedups, and caches data.binance.vision monthly/daily archives). Estimated ~1-2h engineering at /093 setup; ~12 KB × ~1700 days × ~22 symbols ≈ **<500 MB** raw download, far smaller than the 2.8 GB kline tree.
- Liquidations: no deep history feed. Reconstruct as a derived OI-delta-×-return feature. No prerequisite, but a documented modeling compromise.

**No hard blocker.** The single prerequisite (the OI fetcher) is small, parallels existing infrastructure, and is properly /093's setup work — exactly the split the /091 closeout anticipated ("fetch per-symbol Binance funding + OI history" as the /093 QR's pre-brief task).

---

## TASK 2 — Architecture Research

### 2.1 — How funding / OI / liquidation signals are used as regime/state indicators (2024-2025)

The 2025 derivatives-signal literature converges on a consistent set of findings:

- **Integrated frameworks beat single indicators.** The recurring 2025 result: a model combining OI + funding + liquidation/positioning data "achieved substantially higher accuracy than relying on single indicators alone"; tree ensembles (Random Forest, XGBoost) "process multiple derivatives signals... capturing non-linear relationships that traditional analysis misses" ([gate.com derivatives signals 2025](https://web3.gate.com/crypto-wiki/article/how-do-derivatives-market-signals-predict-crypto-price-movements-in-2025-futures-open-interest-funding-rates-and-liquidation-data-explained-20260206)). One source reports 87% directional accuracy for an integrated derivatives model — treat the headline number with the usual skepticism (no DSR, no PBO), but the *direction* (integration > single signal) is consistent across sources.
- **OI rising faster than price = fragility.** "Rising open interest indicates intensified market leverage and potential for volatility"; declining OI plus sustained extreme funding "frequently precedes significant price movements" ([gate.com, 2025](https://web3.gate.com/en/crypto-wiki/article/how-do-derivatives-market-signals-predict-crypto-market-trends-funding-rates-open-interest-and-liquidation-data-in-2025-20251222)). Stealth-leverage build (rising OI + flat price) and deleveraging (OI drop + adverse price) are the two canonical regime fingerprints.
- **Liquidation cascades are mechanically deterministic, not noise.** Before the Oct 10 2025 cascade, annualized funding had climbed toward ~30% and leveraged positioning left the market vulnerable; the cascade liquidated $3.21 B in a single minute, $19 B in 24h ([coinchange](https://www.coinchange.io/blog/bitcoins-2-billion-reckoning-how-novembers-liquidations-cascade-exposed-cryptos-structural-fragilities)). The lesson stated bluntly: *"If an AI is not designed to be regime-aware, a sudden change from a quiet maturation phase to a volatile, deleveraging environment will break its underlying logic."* This is the core argument for Candidate A as a **regime classifier**, not a return predictor.
- **Funding thresholds.** Practitioner consensus: funding > ~0.01% per 8h (≈11% APR) signals leveraged-long crowding; sustained > ~15-30% APR is the danger zone. Funding < ~0.005% signals bearish/accumulation. These are coarse but usable regime cut-points (and IS-calibratable on v3's own data).

### 2.2 — The carry-decay caveat (and why it argues FOR a regime-conditional framing)

This is the single most important nuance for cycle 4. **The crypto carry trade has decayed hard:**

- The crypto carry trade had a 2020-2025 annualized Sharpe of 6.45; this fell to **4.06 in 2024 and turned NEGATIVE in 2025** ([The Crypto Carry Trade, Christin et al.](https://www.andrew.cmu.edu/user/azj/files/CarryTrade.v1.0.pdf); corroborated by [arXiv 2510.14435 investable-asset survey](https://arxiv.org/html/2510.14435v2)).
- Funding-rate arbitrage returns have compressed with market maturity: through Nov 2025, only ~17% of observations show economically significant arbitrage spreads (≥20 bps) and **only 40% of top opportunities are positive after costs** ([ScienceDirect S2096720925000818](https://www.sciencedirect.com/science/article/pii/S2096720925000818)).

**The v3 OOS window is 2025-03→2026-05 — precisely the window where naive carry stopped working.** A long-carry book would be backtested on its own graveyard. This is a real hazard and the /093 brief must state it explicitly.

But the decay is the *argument for* the regime-conditional framing, not against the whole direction:
- The 170-predictor study found 63 statistically significant total-return strategies sorted on basis/momentum/liquidity/size/volatility, with a two-factor log-basis + price-volume model spanning all 63 ([ScienceDirect S2096720925000818](https://www.sciencedirect.com/science/article/pii/S2096720925000818)) — the derivatives state remains a *rich predictor space* even as naive carry dies.
- The edge in 2025 is **regime avoidance**, not yield collection: "be flat into the deleveraging regime the funding+OI state predicts." Regime avoidance is structurally robust to carry decay — it does not depend on funding being a *paid* signal, only on funding+OI extremes being a *leading* signal of forced deleveraging.

### 2.3 — Sketch of a top-quant-firm-grade derivatives-microstructure architecture

A genuine re-architecture (not a feature add). The label and signal are both derivatives-state objects:

**Layer 1 — derivatives-state feature panel (per symbol, 8h bar, all past-only):**
- *Funding*: rate level, sign-persistence (9-bar), 8/24/72h momentum, second-difference (carry-shock, BIS WP 1087), 30-bar z-score, premium-vs-own-history.
- *OI* (the new leg): OI 8h log-delta, OI/market-cap (leverage-stretch), OI z-score, the "OI-up + price-flat" stealth-build interaction, the "OI-down + adverse-return" deleveraging interaction.
- *Basis*: perp-spot basis level, z-score, momentum (already built in `basis_v3.py`).
- *Positioning*: top-trader long/short ratio, taker long/short volume ratio (from the same `metrics` archive — free with the OI fetch).
- *Cross-asset*: BTC funding/OI z-scores broadcast as a market-wide stress regime input.

**Layer 2 — the regime model (the PRIMARY object).** A state classifier whose target is a derivatives-microstructure outcome, NOT a price barrier:
- *Option A (recommended)*: predict the **forward realized-vol regime** — bucket the next-H-bar realized vol into {calm, normal, stressed} and classify. This is a well-posed, balanced multi-class problem and directly actionable.
- *Option B*: predict **forward deleveraging-event probability** — a binary label, event = OI drop > k·σ concurrent with adverse return over the next H bars (the reconstructed-cascade label from §1.4). Rarer-class; needs sample weighting.
- The classifier itself can be LightGBM (multi-class / binary) — the *re-architecture* is in the label and feature class, not necforcedessarily a new model family. (An HMM is the Candidate-C route; for Candidate A a tree classifier on a derivatives-state label is the cleaner first cut.)

**Layer 3 — the regime-conditional book.** Position sizing gated by the predicted regime:
- Calm/stable-funding regime → normal directional or mild-carry exposure.
- Stressed / OI-stretch + extreme-funding regime → **flat or net-short**; this is the edge — harvesting *regime avoidance*.
- Size by predicted-regime confidence, not by a raw return forecast.

This respects every v3 discipline: walk-forward with embargo (the `e149e9d` fix is intact), purged CV, DSR/PBO/PSR gating, the 10:1 cadence. It is genuinely orthogonal — it is the **first v3 architecture to predict a non-price target from a non-price information layer**.

---

## TASK 3 — Feasibility Verdict and Cycle-4 Recommendation

### 3.1 — Is derivatives-microstructure viable for iter-v3/093?

**Yes.** Data is not a hard blocker. Two of three legs (funding, basis) are already fetched and current. The third (OI + L/S ratios) is hosted on data.binance.vision with verified full-window coverage for the v3 universe, and the fetcher is a near-clone of the existing `fetch-spot`. The prerequisite is a **dedicated data-fetch step** — a `fetch-oi` subcommand — and it is properly /093 setup work (small, ~1-2h, <500 MB download), exactly as the /091 closeout scoped it. The closed-axis funding ban does not block Candidate A, because Candidate A is a new architecture (derivatives-state *label* + regime classifier), not the banned single-z-score feature on the price model.

### 3.2 — Candidates B and C: do their data needs change the calculus?

- **Candidate B (cointegration stat-arb)**: zero new data — it runs on perp 8h klines already in `data/`. Lowest data risk of the three. But the /091 closeout's caveat stands: the v3 universe **excludes BTC/ETH** (v1/v2 symbols), and the literature's strong cointegration results are concentrated in BTC-ETH and major caps. A 22-symbol altcoin universe's cointegration structure is thinner and more regime-fragile, and stat-arb is turnover-sensitive — the exact fee drag that sank the /088-091 cross-sectional book. Recorded as the fallback.
- **Candidate C (regime-switching TSMOM)**: zero new data — runs on klines. But the /091 closeout's honest worry stands: v3 already uses Hurst + ADX as regime *features* and has a 7-gate stack — Candidate C risks collapsing into "another gate on a momentum book," which `feedback_v3_structural_over_knob_exploration.md` warns against. It is a genuine re-architecture only if the regime model (HMM/k-means state) is the *primary* sizing object. Lowest ambition of the three.

Neither B nor C is data-blocked. But the /091 closeout's central argument is decisive: **Candidate A is the only candidate that attacks the structural fact uniting every v3 failure — every prior v3 architecture has been price-myopic.** B and C still predict from price (a price spread; a price trend). A introduces a genuinely orthogonal information layer. With the data question now resolved in A's favor, A's one disadvantage (a data prerequisite) is shown to be small.

### 3.3 — Recommendation

**Cycle 4 (iter-v3/093) proceeds with Candidate A — the derivatives-microstructure state-conditioning architecture — with a `fetch-oi` data-fetch step as /093's setup work.** Concretely, the iter-v3/093 QR should:

1. **Setup (engineering)**: build a `fetch-oi` CLI subcommand cloning `_cmd_fetch_spot`'s data.binance.vision download/unzip/dedup/cache pattern; target `data/futures/um/daily/metrics/<SYM>/`; cache to `data/open_interest/<SYM>/8h.csv` resampled from the 5-min `metrics` rows. Refresh `fetch-funding` for the full universe and screen per-symbol completeness (fix the empty `FILUSDT.csv`; flag FTM/MKR mid-2025 gaps).
2. **EDA (mandatory, committed before brief, per `feedback_v3_axis_selection_quant_discipline.md`)**: on the v3 walk-forward window, IS-screen the funding/OI/basis/positioning feature space for genuine forward predictive content on the forward-vol-regime (or deleveraging-event) label. Pre-register the regime-conditional book construction and the holding-time / roster-composition predictor.
3. **Frame the brief around regime AVOIDANCE, not carry collection** — the carry-decay literature (§2.2) means a naive long-carry book would be tested on its graveyard; the brief must state the 2025 carry-negative finding explicitly and justify the regime-conditional framing as the carry-decay-robust alternative.
4. **Keep the cross-sectional infrastructure as a recorded alternative** — if /092's CONFIRMATION (in flight) and the /093 derivatives-state EDA both come back weak, Candidate B (cointegration, zero data risk) is the fallback; Candidate C is the third option.

The honest expectation: this is a hard, genuinely-novel architecture and a first cut may not clear the merge floors. But it is the correct bold direction — it is the first v3 architecture to see the information layer that price-only models structurally cannot — and the critical de-risking question (data) is now answered: **the data is there.**

---

## Appendix — files / artifacts inspected

- `data/funding_rates/` (25 CSVs), `data/spot/` (23 dirs) — coverage quantified §1.1
- `src/crypto_trade/features_v3/funding_v3.py`, `basis_v3.py` — feature modules (retained infra)
- `src/crypto_trade/main.py` — `_cmd_fetch_funding` (~L1050), `_cmd_fetch_spot` (~L1144) CLI subcommands
- `run_baseline_v3.py` — funding/basis ABSENT-ban pre-flight (~L344-466), `V3_MODELS` (~L190)
- `diary-v3/iteration_v3-082.md` (funding family — INERT, axis closed), `iteration_v3-086.md` (perp-spot basis — INERT), `iteration_v3-091.md` §9 (cycle-4 re-architecture direction, Candidates A/B/C)
- data.binance.vision S3 bucket — verified `data/futures/um/daily/metrics/` archive exists; BTCUSDT 2020-09→present, LDO/TRX/GALA/HBAR full v3-window coverage; schema probed (OI + OI-value + 3 L/S ratios, 5-min granularity)
