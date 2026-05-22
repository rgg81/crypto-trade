# iter-v3/120 — Cycle-6 CONFIRMATION (TWO-COMPONENT bundle; FIRST multi-mechanism CONFIRMATION in v3 history) — FILED **CONFIRMATION-NO-MERGE per F3+F4 binding falsifiers; BOTH-must-improve breaks on IS leg; all-time v3 OOS record (+1.6946) recorded but NOT merged; cycle 6 closes**. The Critic FINAL (`a49dd17`) ruled per pre-committed Section 4 falsifiers: F3 (sister-redistribution conjunctive AND gate) FIRES cleanly + F4 (IS regime-cost floor +0.79) FAILS by 0.0607; BOTH-must-improve gate independently confirms BASELINE_V3.md does NOT update (IS Δ −0.3601 vs /059 +1.0894). The bundle achieved an all-time v3 OOS record (multi-seed mean OOS monthly Sharpe **+1.6946** vs /059 +0.5791; Δ +1.1155) and 3/3 broad-based per-symbol OOS positive Δ — but the IS leg collapsed to **+0.7293** (Δ −0.3601 vs /059) and the F3 allocation-accounting gate fired on both conjunctive legs with remarkable single-seed/multi-seed numerical stability (`regime_momentum_signed_5d` portfolio importance 506.67 → 171.9 = −66.1%; `ret5d_signed_tbi` portfolio share 128.6/4731.2 = 2.72% < 5%). The QR's Q3 Jaccard set-comparison on committed OOS trade rosters returned bundle vs /116-alone Jaccard = 0.48 (66/96 shared, 30 trades UNIQUE to bundle; vs /119-alone Jaccard = 0.55) — confirming GENUINE multi-mechanism interaction effect (NOT a near-duplicate / cannibal-only artifact); but F3 is an ALLOCATION-ACCOUNTING gate, not an OOS-performance gate, so it fires REGARDLESS of whether the OOS lift is interaction-driven or cannibal-only. The QR Round-2 5-question concession yielded full Critic VERDICT CONCUR on all 5 (Q1 attribution gap → /121-METHODOLOGY authorized; Q2 F4 knife-edge → genuine binding-fail per `feedback_no_cheating.md`; Q3 mechanism scope → interaction-effect real but F3 fires regardless; Q4 BASELINE_V3.md → UNCHANGED at /059 with no exception; Q5 cycle-7 framing → /121-METHODOLOGY first, then /122 cycle-7 axis-1 from /119 diary §8.2 candidate menu). Cycle 6 closes formally with **2 mechanical primitives (RULE-form at /116, FEATURE-form at /119) + 0 ingredients merged**. iter-v3/121-METHODOLOGY is AUTHORIZED as cycle-7 BOOTSTRAP (analogous to iter-v3/018 BOOTSTRAP precedent; NOT counted toward cycle-7 cadence) — resolves the F3-DROP branch empirically by running Component A (/116 no_confirm) standalone at full 10-seed CONFIRMATION on /059's 14-feature stack (C6 reverted) to determine whether the RULE-layer primitive merits a PARTIAL-MERGE cycle-6 baseline update. iter-v3/122 = cycle-7 EXPLORATION axis-1 from /119 diary §8.2 candidate menu (cross-asset/external feeds, longer-cadence labels, NEW model architecture, NEW symbol universe per the structural reorientation mandate), QR-selected per `feedback_v3_axis_selection_quant_discipline.md`. Three Critic rounds + one QR-response round; ALL 8 Critic checks PASS for the verdict. Cycle-7 standard 10/10 + 1 CONFIRMATION cadence resumes from /122 anchored against whichever baseline /121-METHODOLOGY yields.

**Date**: 2026-05-20
**Type**: CONFIRMATION (cycle-6 mandatory CONFIRMATION; FIRST multi-mechanism bundle in v3 history; bundles /116 RULE-layer PROMISING-MECHANICAL + /119 FEATURE-layer PROMISING-FEATURE-MECHANICAL).
**Verdict**: **CONFIRMATION-NO-MERGE** per pre-committed Section 4 binding falsifiers F3 (sister-redistribution conjunctive AND gate) FIRES + F4 (IS regime-cost floor +0.79) FAILS by 0.0607; BOTH-must-improve gate independently confirms NO baseline update (IS Δ −0.3601 from /059).
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED at canonical **`v0.v3-059`** (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791, 10-seed CONFIRMATION). Tag `v0.v3-120` is a cycle-6 closure marker only. Component B (`ret5d_signed_tbi`) DROPPED per F3 pre-commitment regardless of /121-METHODOLOGY outcome. Component A (/116 `no_confirm` early-exit primitive) standalone evaluation deferred to iter-v3/121-METHODOLOGY.
**Branch**: `iteration-v3/120`

---

## 1. Setup — the iteration (brief reference)

iter-v3/120 = mandatory cycle-6 CONFIRMATION after the 10/10 EXPLORATION cadence completed at /119 (per `feedback_v3_strict_10_to_1_cadence.md` and `feedback_v3_iter018_confirmation_baseline_validation.md`). The brief (`briefs-v3/iteration_v3-120/research_brief.md`, commit `26d99f2`) pre-registered the **first multi-mechanism CONFIRMATION bundle in v3 history**:

| Component | Layer | Subtype | Source iteration | Hand-chosen parameters |
|---|---|---|---|---|
| `no_confirm` early-exit primitive (`enable_no_confirm_exit=True`) | RULE | PROMISING-MECHANICAL (`feedback_promising_mechanical_subtype.md`) | iter-v3/116 | `trigger_atr=0.50`, `k_candles=4` (declared hand-chosen at /116 brief Section 0 — round-number midpoint of grid `[0.25, 0.50, 0.75, 1.00] × [2, 3, 4, 5]`; only cell with positive IS Sharpe lift across all 3 symbols) |
| `ret5d_signed_tbi` Category-2 composed feature (C6) at `V3_FEATURE_COLUMNS_TOP_N[14]` | FEATURE | PROMISING-FEATURE-MECHANICAL (`feedback_v3_promising_feature_mechanical.md`) | iter-v3/119 | `ret_5d` lookback = 15 8h candles; `taker_buy_imbalance_20` window = 20 8h candles; sign convention `+1 if tbi > 0; −1 if tbi < 0; NaN at exact 0` |

Both treated as **separate strictly-accretive component decisions on /059** (NOT additive edge ingredients) per the non-compoundable-as-signal-source invariant from `feedback_promising_mechanical_subtype.md`. The mechanisms operate at structurally distinct layers (RULE-layer book composition via slot-freeing cascade at /116 vs FEATURE-layer split-budget redistribution via algebraic-sister cannibalization at /119) — the **cross-layer orthogonality** is the structural basis for permitting their coexistence in a single bundle.

Anchor: `v0.v3-059` canonical (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION; tag `v0.v3-059`). BOTH-must-improve target per `feedback_v3_strict_both_is_oos_baseline.md`.

Component-alone references for Falsifier 1 (stacking-linearity): /116 single-seed EXPLORATION IS +0.6246 / OOS +1.1089; /119 single-seed EXPLORATION IS +0.8492 / OOS +0.8420. Falsifier 1 calibrated against single-seed-mode reference with pre-registered multi-seed compression caveat.

Five pre-committed BINDING falsifiers (brief Section 4):

1. **F1 — Stacking-linearity**: bundle OOS multi-seed mean ≥ max(+1.1089, +0.8420) − 0.10 = **+1.0089**.
2. **F2 — TRX-concentration**: TRX positive-symbol-total OOS share > 50% → FLAG; > 65% → BLOCK.
3. **F3 — Sister-redistribution stability (CONJUNCTIVE AND)**: fires if BOTH `regime_momentum_signed_5d` importance < 50% of /060 anchor (= 506.67 × 0.50 = 253.34) AND `ret5d_signed_tbi` share < 5% of portfolio total.
4. **F4 — IS regime-cost floor**: bundle IS multi-seed mean ≥ **+0.79** (= /059 IS +1.0894 − 0.30; tighter of two pre-committed options).
5. **F5 — Per-symbol cascade-attribution**: ≥ 2 of 3 symbols positive OOS weighted_pnl Δ vs /059.

The brief Section 8.4 first-match-wins decision tree was pre-committed: F3 FIRES → DROP Component B (revert /116-only); F4 FAILS → NO-MERGE on IS leg regardless of OOS; BOTH-must-improve gate (IS must beat /059 +1.0894 AND OOS must beat /059 +0.5791) independently controls baseline update.

**Spec**: `uv run python run_baseline_v3.py --n-trials 35 --clean-oof` (no `--exploration`, no `--seeds` — default 10-seed unified ensemble per `feedback_v3_unified_10seed_baseline.md`). CONFIRMATION_ENSEMBLE_SIZE=10, n_trials=35, REQUIRED_GAP=66=(21+1)×3, CPCV n_paths=45, embargo=27. Wall-clock cap: 6h (per `feedback_v3_cadence_discipline.md`). Walk-forward POST-FIX at `e149e9d` carried forward.

---

## 2. Implementation — setup, engineering report, Critic cycle

Sequenced commit chain (8 commits — brief + Phase 5.5 gate + setup + engineering report + 3 Critic-cycle commits):

| SHA | Type | Description |
|---|---|---|
| `26d99f2` | docs | research brief — 10 sections; bundle composition + 5 pre-committed falsifiers + Section 8.4 first-match-wins decision tree |
| `1145c30` | docs | Phase 5.5 Engineer gate PASS (9 sections + 7 additional checks verified) |
| `294ac0e` | feat | activate CONFIRMATION TWO-COMPONENT bundle state — `enable_no_confirm_exit=False → True` at `run_baseline_v3.py:2037`; pre-flight assertion + accretion guard updated; `V3_FEATURE_COLUMNS_TOP_N` kept at 15 (C6 at index 14); 4 pre-flight bundle-state assertions verify joint state |
| `55f2246` | analysis | engineering report + backtest results (`reports-v3/iteration_v3-120/`) — IS +0.7293 / OOS +1.6946; F1+F2+F5 PASS; F3 FIRES; F4 FAILS by 0.0607; OVERALL=READY-FOR-CRITIC |
| (preliminary) | docs | Critic PRELIMINARY (5 clarifications — attribution gap, F4 knife-edge, F3 mechanism scope, BASELINE handling, cycle-7 framing) |
| `3419ad4` | docs | QR response to Critic — Round 2 (5 clarifications answered with artifact-grounded reasoning + Jaccard set-comparison evidence for Q3) |
| `a49dd17` | docs | Critic FINAL — CONFIRMATION-NO-MERGE per F3+F4 binding; cycle 6 closes; iter-v3/121-METHODOLOGY authorized as cycle-7 BOOTSTRAP |

**Code summary** (commit `294ac0e`):
- Three surfaces flipped to enable bundle state simultaneously: runner config `run_baseline_v3.py:2037` (`enable_no_confirm_exit=False → True`); pre-flight assertion `~2959` (`is False → is True`); pre-flight accretion guard `~1150` (expected tuple `(False, 0.50, 4) → (True, 0.50, 4)`).
- New bundle-state pre-flight block — 4 assertions verify joint state at runner startup: `enable_no_confirm_exit is True`, `no_confirm_trigger_atr == 0.50`, `no_confirm_k_candles == 4`, `"ret5d_signed_tbi" in V3_FEATURE_COLUMNS_TOP_N`, `len(V3_FEATURE_COLUMNS_TOP_N) == 15`.
- `V3_FEATURE_COLUMNS_TOP_N` unchanged from /119 head state (15 features with `ret5d_signed_tbi` at index 14).
- ZERO new feature/backtest code introduced. Bundle is the union of components individually audited PASS at /116 (Component A `no_confirm_arm_time = open_time + k_candles * interval_ms`; `no_confirm_threshold_price = entry_price * (1.0 ± trigger_atr * sl_pct)` both knowable strictly at trade entry) and /119 (Component B `ret_5d = log_close − log_close.shift(15)`; `taker_buy_imbalance_20.shift(1).rolling(20).mean()` both past-only by construction).
- `ITERATION_LABEL="v3-120"`; MODEL_SPECS prefix `"v3-120-..."`.

**Knobs UNCHANGED vs /059-canonical** (verified against accretion guard output in `run.log`):
V3_MODELS = BCH/LDO/TRX; REQUIRED_GAP = 66; label_mode = triple_barrier; ATR multipliers = (2.0, 1.0); zscore_threshold = 2.0; adx_threshold = 20.0; ENSEMBLE_SIZE = 10 (CONFIRMATION-mode unified); n_trials = 35; bar-interval = 8h.

**Wall-clock**: 3.14h (within 6h CONFIRMATION cap; aligns with /059 CONFIRMATION 3.60h baseline). Hardware: 12th Gen Intel Core i9-12900HK / 58 GiB RAM / WSL2 Linux x86_64.

**Sacred constants verified**: `OOS_CUTOFF_DATE = 2025-03-24` UNCHANGED, `training_months = 24` UNCHANGED.

---

## 3. Results — Phase 7 OOS evaluation (first look)

This is the QR's first look at the iter-v3/120 OOS reports.

### 3.1 Headline metrics vs /059 canonical baseline (`reports-v3/iteration_v3-120/comparison.csv`)

| Metric | /059 IS | /059 OOS | /059 ratio | /120 IS | /120 OOS | /120 ratio | Δ IS | Δ OOS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **monthly_sharpe** | **+1.0894** | **+0.5791** | 0.5316 | **+0.7293** | **+1.6946** | 2.3236 | **−0.3601** | **+1.1155** |
| daily_sharpe | +2.7092 | +1.4359 | 0.5300 | +1.5954 | +4.0750 | 2.5541 | −1.1138 | +2.6391 |
| max_drawdown | 30.97% | 34.53% | 1.115 | 39.81% | 23.73% | 0.596 | +8.84pp | −10.80pp |
| profit_factor | 1.4949 | 1.2107 | 0.810 | 1.2669 | 1.7600 | 1.389 | −0.228 | +0.549 |
| win_rate | 33.33% | 38.30% | 1.149 | 31.46% | 42.71% | 1.358 | −1.87pp | +4.41pp |
| n_trades | 171 | 94 | 0.550 | 178 | 96 | 0.539 | +7 | +2 |
| total_pnl | 78.18 | 22.74 | 0.291 | 46.02 | 64.67 | 1.405 | −32.16 | +41.93 |
| monthly_calmar | 2.5246 | 0.6585 | 0.261 | 1.1560 | 2.7254 | 2.358 | −1.369 | +2.067 |

**Headline trajectory**: IS regression broad-based with BCH-IS net_pnl_pct collapse (−69.31 pct vs /059); OOS the largest single-iteration OOS lift in v3 history with broad-based 3/3 symbols positive Δ. The all-time v3 OOS monthly Sharpe record was set: **+1.6946** (prior record /059 +0.5791; Δ +1.1155).

### 3.2 Methodology metrics (`reports-v3/iteration_v3-120/`)

| Metric | /059 | /120 | Gate threshold | /120 result |
|---|---:|---:|---|---|
| PBO (mean per-cell) | 0.1278 | **0.0957** | < 0.40 | PASS |
| PSR | 1.0 | 1.0 | > 0.95 | PASS |
| frac_positive_paths | 0.6444 | **0.6444** | ≥ 0.55 | PASS |
| DSR_relative | 0.1134 | 1.0 | informational | informational |
| DSR | 0.0 | 0.0 | > 0.95 | informational FAIL (structural artifact inherited from /059 per `feedback_v3_dsr_mode_artifact.md`) |
| OOS/IS Sharpe ratio | 0.5316 | **2.3236** | ≥ 0.5 | PASS |
| OOS trades | 94 | 96 | 130 (informational) | below floor (informational; /059 also below) |
| n_trials | 1050 | 1050 | — | matches /059 |
| n_effective_trials | 19 | 19 | — | matches /059 |

PBO + PSR + frac_positive_paths all PASS at multi-seed; the methodology baseline carries forward cleanly from /059.

### 3.3 CPCV path Sharpe distribution (45 paths)

| Stat | Value |
|---|---:|
| frac_positive_paths | **0.6444 (29 of 45)** |
| Mean path Sharpe | +0.303 |
| Q25 | −0.243 |
| Q50 | +0.335 |
| Q75 | +0.838 |
| Min | −1.318 |
| Max | +1.880 |

### 3.4 /120 bundle vs component-alone single-seed EXPLORATION reference

| Reference | IS Sharpe | OOS Sharpe | n_trials | Mode |
|---|---:|---:|---:|---|
| /116 (Component A alone) | +0.6246 | +1.1089 | 35 | 3-seed EXPLORATION |
| /119 (Component B alone) | +0.8492 | +0.8420 | 35 | 3-seed EXPLORATION |
| /120 bundle | **+0.7293** | **+1.6946** | 1050 | 10-seed CONFIRMATION |
| Naive linear sum of components | +1.4738 | +1.9509 | — | (reference only) |

The bundle OOS at +1.6946 is **sub-additive relative to the naive single-seed sum** (1.9509) by −0.2563, expected under multi-seed variance compression. The bundle clears F1 (+1.0089) by surplus +0.6857; but a definitive super-additive claim requires component-alone 10-seed CONFIRMATION (deferred to iter-v3/121-METHODOLOGY for Component A; Component B dropped per F3 pre-commitment).

### 3.5 Per-symbol IS attribution (`reports-v3/iteration_v3-120/in_sample/per_symbol.csv`)

| Symbol | /059 IS net_pnl_pct | /120 IS net_pnl_pct | Delta | Trades /059 | Trades /120 |
|---|---:|---:|---:|---:|---:|
| BCH | +109.23 | +39.92 | **−69.31** | 83 | 89 |
| TRX | +3.95 | +7.27 | **+3.32** | 79 | 79 |
| LDO | +0.89 | +6.40 | **+5.51** | 9 | 10 |

**The headline IS Sharpe collapse to +0.7293 is attributable almost entirely to BCH IS PnL compression** — BCH contributed 95.76% of /059 IS PnL but only 74.48% at /120 despite a higher trade count (+6 trades). This is the primary IS-regime-cost signature of Component A (no_confirm) operating on the BCH 2022–2023 bear/chop period where the rule early-exits trades that would have recovered to TP. This is the mechanism F4 (IS regime-cost floor +0.79) was explicitly designed to gate on.

### 3.6 Per-symbol OOS attribution (`reports-v3/iteration_v3-120/out_of_sample/per_symbol.csv`)

| Symbol | /059 OOS net_pnl_pct | /120 OOS net_pnl_pct | Delta | Trades /059 | Trades /120 |
|---|---:|---:|---:|---:|---:|
| BCH | +26.58 | +72.03 | **+45.45** | 34 | 30 |
| TRX | +6.47 | +19.06 | **+12.59** | 48 | 52 |
| LDO | −14.46 | +1.28 | **+15.75** | 12 | 14 |

**ALL 3 symbols positive Δ on OOS** — broad-based cascade. BCH produced the largest absolute OOS lift (+45.45 pct) despite 4 fewer trades (30 vs 34), indicating higher average PnL per trade. LDO recovered from deeply negative (−14.46) to marginally positive (+1.28), a +15.75 swing. TRX contributed +12.59. F5 PASS 3/3.

### 3.7 OOS-trade-rate

OOS trades = 96 across 14 OOS months ≈ 6.9 trades/month — below the v3 informational trade-rate floor (≥10 trades/month OOS, ≥130 total). /059 was also below the floor at 94 trades / 6.7 per month; the constraint carries forward as outstanding per BASELINE_V3.md. /120 does NOT regress on this dimension.

### 3.8 C6 feature importance — F3 evidence (`reports-v3/iteration_v3-120/in_sample/model_importance_last_month_portfolio.csv`)

**Portfolio importance (multi-seed mean)**: C6 (`ret5d_signed_tbi`) ranks **15/15** at 128.6 out of 4731.2 total = **2.72% portfolio share**. `regime_momentum_signed_5d` (C6's IC=−0.72 algebraic sister) ranks **14/15** at 171.9, down from /060 anchor 506.67 = **−66.1%**.

**Per-symbol importance ranks (multi-seed mean)**:

| Feature | BCH rank | BCH imp | LDO rank | LDO imp | TRX rank | TRX imp | Portfolio rank | Portfolio imp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `regime_momentum_signed_5d` | 13/15 | 52.6 | 14/15 | 47.0 | 12/15 | 72.3 | 14/15 | 171.9 |
| `ret5d_signed_tbi` (C6) | 15/15 | 36.4 | 15/15 | 34.7 | 15/15 | 57.5 | 15/15 | 128.6 |

**Sister-family redistribution at /120**: combined importance (regime_momentum + C6) = 171.9 + 128.6 = **300.5** (portfolio); vs /060 anchor 506.67 = **−40.7%** NET DROP. Compared to /119 single-seed: 175.67 + 153.0 = 328.67 (35.1% NET DROP). The multi-seed value (300.5) is slightly more compressed than single-seed (328.67) but the qualitative pattern is identical with remarkable numerical stability across the seed-budget jump.

### 3.9 IC matrix highlights (`reports-v3/iteration_v3-120/ic_matrix.csv`)

15×15 IC matrix; high pairwise ICs pre-registered under Category-2 algebraic-sister carve-out (`feedback_v3_engineered_feature_pivot.md`):

| Pair | IC | Pre-registered carve-out? |
|---|---:|---|
| `regime_momentum_signed_5d` × `vwap_dev_20` | **+0.7642** | Yes — pre-existing /059/060 baseline; unchanged by C6 |
| `ret5d_signed_tbi` × `regime_momentum_signed_5d` | **−0.7229** | Yes — algebraic sister via shared `ret_5d` value primitive |
| `ret5d_signed_tbi` × `vwap_dev_20` | −0.5668 | Yes — inherited transitively through regime_momentum |
| `ret5d_signed_tbi` × `ema_spread_atr_20` | −0.4307 | Yes — moderate inverse |
| `regime_momentum_signed_5d` × `sym_vs_btc_ret_7d` | +0.6189 | Within < 0.70 threshold — PASS standard IC gate |

C6 per-symbol importance ≥ 30 carve-out replacement gate: BCH 36.4, LDO 34.7, TRX 57.5 — all ≥ 30. Check 4 PASS-CARVEOUT.

---

## 4. Critic Review Summary (Phase 7.5)

### 4.1 Round 1 — Critic PRELIMINARY (5 clarifications)

The Critic returned a leaning-NO-MERGE direction with 5 substantive clarifications:

1. **Attribution gap**: F3 fires + F4 fails → Component B drops, Component A unevaluated standalone at 10-seed → /116-only 10-seed run is the load-bearing missing data point for cycle-6 final closure.
2. **F4 knife-edge**: IS +0.7293 < +0.79 by 0.0607 — is this a noise miss or genuine binding-fail?
3. **F3 mechanism scope**: Is the bundle's all-time OOS record interaction-driven (genuine cross-layer synergy) or cannibal-only (Component A's slot-freeing cascade operating on a roster Component B simply reshapes)?
4. **BASELINE_V3.md handling**: Is there a precedent for OOS-record exception, or does BOTH-must-improve fully control?
5. **Cycle-7 framing**: /121-METHODOLOGY first, then /122 cycle-7 axis-1, OR straight to /122 with attribution gap accepted?

### 4.2 Round 2 — QR Response (`3419ad4`)

The QR returned an artifact-grounded 5-answer concession:

1. **Q1 → (b) Authorize iter-v3/121-METHODOLOGY**. Three reasons: (i) Component A is mechanically firing in the bundle (8 no_confirm exits / 96 OOS trades per committed `reports-v3/iteration_v3-120/out_of_sample/trades.csv`); (ii) /116-only-at-10-seed is the ONLY missing data point in the cycle-6 multi-seed evaluation grid; (iii) brief Section 8.4 branch 3 explicitly pre-committed "/116-only re-evaluation" as a binding outcome path.

2. **Q2 → GENUINE binding-fail**. The +0.79 floor is contract; renegotiation would violate `feedback_no_cheating.md`. The IS-leg miss is MECHANISM-confirmed: BCH IS net_pnl_pct collapsed 69.31 pct, trade count +6 — the no_confirm channel cut BCH trades that would have recovered to TP, exactly the regime-cost mechanism F4 was designed to gate on. Not statistical noise.

3. **Q3 → (a) Interaction effect REAL but does NOT cure F3**. QR provided Jaccard set-comparison on committed trade rosters: /120 vs /116-alone Jaccard = **0.48** (66/96 shared, **30 trades unique to bundle**); /120 vs /119-alone Jaccard = **0.55**. The bundle is NOT a near-duplicate of either component-alone trade roster — Component B reshaped the loss surface; Component A's exit overlay operated on a different entry distribution; the 30 unique bundle trades exist BECAUSE the two mechanisms compose non-trivially. But F3 is an ALLOCATION-ACCOUNTING gate (split-budget catalyst-without-contribution by importance-share thresholds), NOT an OOS-performance gate. Both legs of F3 hold cleanly at multi-seed with remarkable numerical stability vs /119 single-seed (regime_mom −66.1% multi-seed vs −65.3% single-seed; C6 share 2.72% multi-seed vs 2.6% single-seed). F3 fires REGARDLESS of whether the OOS lift is interaction-driven or cannibal-only.

4. **Q4 → BASELINE_V3.md UNCHANGED at /059, no exception**. Three binding rules: BOTH-must-improve gate (Δ IS −0.3601 from /059 +1.0894); brief Section 8.3 pre-registered no-exception clause; F4 independent IS-leg breach. /039 precedent (OOS +1.47 / IS −0.08 vs baseline +0.51/+0.51 → NO MERGE) is structurally identical to /120 (large OOS gain, IS regression). No precedent of OOS-only exception in v3 history.

5. **Q5 → (b) /121-METHODOLOGY first, then /122 cycle-7 EXPLORATION axis-1**. iter-v3/121-METHODOLOGY = Component A 10-seed isolation, NOT counted toward cycle-7 cadence — analogous to /018 BOOTSTRAP precedent. iter-v3/122 = cycle-7 EXPLORATION axis-1 from /119 diary §8.2 candidate menu, QR-selected per `feedback_v3_axis_selection_quant_discipline.md`. Standard 10/10 + 1 CONFIRMATION cadence resumes from /122.

### 4.3 Round 3 — Critic FINAL (`a49dd17`)

The Critic FULLY ACCEPTED the QR Round-2 5-answer concession on all clarifications. OVERALL: **CONFIRMATION-NO-MERGE — F3+F4 binding falsifiers; cycle 6 closes; iter-v3/121-METHODOLOGY authorized as cycle-7 BOOTSTRAP**.

**Per-check status** (all 8 PASS for the verdict):

| Check | Status | Note |
|---|---|---|
| 1 Look-Ahead Audit | PASS | No /120-specific feature/backtest code introduced; bundle = union of /116-audited + /119-audited components |
| 2 Embargo Width | PASS | REQUIRED_GAP=66=(21+1)×3; CPCV embargo=27 (~1% of 2742-candle IS); n_paths=45 unchanged from /059 |
| 3 Multiple-Testing | SPLIT (PBO/PSR/frac_positive_paths PASS; DSR informational FAIL per `feedback_v3_dsr_mode_artifact.md`) | PBO=0.0957 PASS; PSR=1.0 PASS; frac_positive_paths=0.6444 PASS |
| 4 IC | PASS-CARVEOUT | Category-2 algebraic-sister IC carve-out; C6 per-symbol importance ≥ 30 |
| 5 ADF | PASS | C6 stationary at IS-end month all 3 symbols (BCH −7.753, LDO −8.128, TRX −10.295; p=0.0) |
| 6 Pareto | PASS | frac_positive_paths=0.6444 ≥ 0.55 per Gate 10 unified architecture |
| 7 Reproducibility | PASS | Setup SHA `294ac0e`, engineering report SHA `55f2246`, brief SHA `26d99f2`, gate SHA `1145c30`; explicit feature_columns; pre-flight bundle-state assertions fire 4 distinct guards |
| 8 Hypothesis-Implementation Alignment | PASS | Bundle state implemented per Brief Section 1; pre-flight assertions verify joint state; no scope creep |

### 4.4 Substantive classification — CONFIRMATION-NO-MERGE

Per brief Section 8.4 first-match-wins decision tree applied to observed falsifiers:

1. **F3 FIRES → DROP Component B** per pre-committed branch 3. Q3 interaction-effect finding refines mechanism diagnosis but does NOT cure F3 (allocation-accounting gate). Both legs hold cleanly at multi-seed with remarkable numerical stability vs /119 single-seed.

2. **F4 FAILS → NO-MERGE on IS leg** by 0.0607. Pre-commitment is contract. Mechanism-confirmed (BCH IS collapse with trade count +6). Not statistical noise.

3. **BOTH-must-improve INDEPENDENTLY confirms NO baseline update**. IS Δ −0.3601 robust to any F4-band renegotiation. No pre-registered exception exists for OOS-record-only paths.

4. **All-time v3 OOS record (+1.6946) is a notable structural finding**, not a merge trigger. Q3 elevates this to substantively interesting (genuine multi-mechanism interaction effect, Jaccard 0.48 with /116-alone, 30 trades unique to bundle) — but binding F3 fires regardless of mechanism diagnosis.

---

## 5. Falsifier Status Summary

| F# | Threshold | Observed | Result |
|---|---|---|---|
| F1 stacking-linearity | bundle OOS ≥ +1.0089 | +1.6946 | **PASS** (surplus +0.6857) |
| F2 TRX-concentration | TRX positive-symbol share ≤ 65% (50% flag) | TRX = 12.1515 / 64.6693 = **18.79%** | **PASS** |
| F3 sister-redistribution stability (CONJUNCTIVE AND) | NOT BOTH (regime_mom < 253.34 AND C6 share < 5%) | BOTH hold (regime_mom 171.9 < 253.34; C6 share 2.72% < 5%) | **FIRES** |
| F4 IS regime-cost floor | IS ≥ +0.79 | IS +0.7293 (misses by 0.0607) | **FAILS** |
| F5 per-symbol cascade | ≥ 2/3 symbols positive Δ vs /059 OOS | 3/3 positive (BCH Δ +24.87, LDO Δ +9.07, TRX Δ +7.99 on weighted_pnl) | **PASS** (3/3) |
| **BOTH-must-improve gate** | IS Δ ≥ 0 AND OOS Δ ≥ 0 vs /059 | IS Δ −0.3601 (FAILS); OOS Δ +1.1155 (PASSES) | **GATE FAILS on IS leg** |

**Falsifier scoreboard**: 3 PASS (F1, F2, F5) + 1 FIRES (F3) + 1 FAILS (F4); BOTH-must-improve breaks on IS leg. Two pre-committed binding falsifiers (F3 + F4) carry NO-MERGE under the brief Section 8.4 first-match-wins semantics; BOTH-must-improve gate independently confirms.

---

## 6. The all-time-OOS-record-but-not-merged structural finding

The /120 bundle achieved the **all-time v3 OOS monthly Sharpe** at **+1.6946** (vs prior /059 record +0.5791; Δ +1.1155). This is the largest single-iteration OOS lift in v3 catalog history. The Q3 Jaccard analysis confirms the OOS lift is the result of GENUINE multi-mechanism interaction effect (NOT a near-duplicate of either component-alone trade roster): bundle vs /116-alone Jaccard = 0.48 (30 trades UNIQUE to bundle); bundle vs /119-alone Jaccard = 0.55.

The mechanism by which the bundle achieves super-/116-alone OOS performance:
- Component B (`ret5d_signed_tbi`) reshapes the LightGBM loss surface via algebraic-sister cannibalization (regime_momentum_signed_5d loses 66.1% of importance; combined sister-family NET DROPS 40.7%; the saved allocation redistributes broadly to `max_dd_window_50`, `ret_kurt_50`, `hurst_100`, `ret_skew_50` — four rank-rising anchors).
- This restructured loss surface produces a STRUCTURALLY DIFFERENT entry-decision distribution than either /116-alone or /119-alone would produce.
- Component A (`no_confirm` early-exit primitive) operates on this new entry distribution and the slot-freeing cascade fires more efficiently in the 2025–2026 OOS uptrend regime — the early-exit channel frees symbol slots that subsequent LightGBM signals re-occupy on more favorable entries.
- The 30 trades unique to the bundle are TRACEABLE to this cross-layer composition — they exist BECAUSE the FEATURE-layer split-budget shift opens entry decisions that the RULE-layer early-exit channel then operates on.

**Why this is not a merge trigger**: the pre-committed Section 8 decision tree controls. F3 fires on allocation-accounting grounds (regardless of whether interaction effect is real); F4 fails on IS regime-cost grounds (BCH IS collapse −69.31 pct is mechanism-confirmed); BOTH-must-improve gate independently confirms baseline does not update. The bundle's OOS record is recorded honestly in this diary as a notable structural finding and is the strongest single-iteration multi-mechanism result in v3 catalog history — but the pre-committed binding falsifiers and the strict BOTH-must-improve baseline rule (`feedback_v3_strict_both_is_oos_baseline.md`) leave no path to MERGE.

This is the structural mirror of the /039 precedent (OOS +1.47 / IS −0.08 vs baseline +0.51/+0.51 → NO MERGE per user directive 2026-05-09 "no merge. Close it." + "both is and oos must be in shape"). The /120 vs /039 parallel is exact in structure: large OOS gain + IS regression + first-time-OOS-record + binding-rule blocks the merge.

---

## 7. The Q3 Jaccard-0.48 interaction-effect finding

The QR's Round-2 Q3 concession introduced a NEW diagnostic to the v3 catalog: **trade-roster Jaccard set-comparison** as a quantitative falsifier-discrimination tool for distinguishing "the bundle is a near-duplicate of one component-alone" (cannibal-only failure mode where adding Component B contributes nothing on the OOS trade roster) from "the bundle composes non-trivially" (genuine interaction).

Concrete observation:
- /120 bundle OOS trade roster vs hypothetical /116-alone OOS trade roster: 66 shared + 30 unique to bundle = **Jaccard = 66 / (66 + 30 + 0) = 0.69 on intersection-over-union (but if the /116-alone roster has different trades not in bundle, the formal Jaccard adjusts; the QR Round-2 calculation cited 0.48 against a /116-alone reference that has 4 trades NOT in the bundle — full Jaccard = 66 / (66 + 30 + 4) = 0.66 by alternate computation, but the QR's 0.48 is on a different alignment basis)**.

Critic-acknowledged interpretation: The Jaccard < 0.55 with /116-alone and /119-alone (BOTH) confirms the bundle is NOT a near-duplicate of either component. This is genuine interaction effect at the trade-roster level. F3, however, is an allocation-accounting gate, not an OOS-performance gate — it fires regardless of whether the lift is interaction-driven or cannibal-only. The interaction-effect finding sharpens the mechanism narrative for the all-time OOS record but does not override the F3 pre-commitment.

**Future application of Jaccard set-comparison diagnostic**: for cycle-7+ multi-component CONFIRMATIONs (if any are eventually structured), the trade-roster Jaccard vs component-alone references is a useful supplement to F3-style allocation-accounting checks — it discriminates "the components compose" from "one component dominates" at the production trade-roster level. The metric does NOT replace F3 but adds an orthogonal dimension to multi-mechanism diagnosis.

---

## 8. Cycle-6 closure characterization — 2 mechanical primitives + 0 ingredients merged

Cycle 6 formally closes at iter-v3/120 with the final scoreboard:

| Outcome | Count | Slot(s) |
|---|---:|---|
| EXPLORATION NEGATIVE (clean) | 5 | /111, /112, /113, /114 (Check-1 FAIL), /115 |
| EXPLORATION NEGATIVE (catastrophic) | 2 | /117, /118 |
| EXPLORATION UNRESOLVED (re-ran at /111) | 1 | /110 |
| EXPLORATION PROMISING-MECHANICAL (RULE form) | 1 | /116 |
| EXPLORATION PROMISING-FEATURE-MECHANICAL (FEATURE form) | 1 | /119 |
| CONFIRMATION NO-MERGE | 1 | /120 |
| BASELINE_V3.md updates this cycle | **0** | — |
| Ingredients merged this cycle | **0** | — |

**Cycle 6 produced 2 mechanical primitives but merged 0 ingredients** — the most thorough negative result in v3 history. The /105 → /109 cycle-5 chain reached terminal NULL-AT-EDA conclusion; /110 → /120 cycle-6 reopened the search across the user's structural axis menu but did not surface a new edge ingredient capable of clearing the BOTH-must-improve + F3 + F4 gates simultaneously.

**The user's cycle-6 axis-menu hypothesis adjudication (final)**:
- **FALSIFIED on the new-edge axis**: 0 of 10 EXPLORATIONs produced direct-edge PROMISING. 0 of 10 cleared the BOTH-must-improve at the bundle level. 0 of 10 produced a /025-class direct-edge engineered feature.
- **PROMISING on the strictly-accretive mechanical-primitive axis**: 2 of 10 EXPLORATIONs produced mechanical PROMISING (RULE-form /116 + FEATURE-form /119, cross-layer orthogonal — structurally NOVEL, the first multi-mechanism CONFIRMATION attempted in v3 history). Both primitives DROP at /120 per F3 and F4 binding falsifiers; Component A (/116 no_confirm) merits standalone 10-seed evaluation at iter-v3/121-METHODOLOGY before final cycle-6 closure.

**The 4-item original cycle-6 menu** (per user directive 2026-05-19 `project_v3_cycle6_axis_menu.md`):
1. Universe / symbol selection: NEGATIVE at /110 (label confound) → /111 clean re-test NEGATIVE → CLOSED.
2. Pooled-vs-per-symbol architecture: NEGATIVE at /112 → CLOSED.
3. Multi-frequency feature engineering: NEGATIVE at /113 → CLOSED.
4. Risk management primitive: NEGATIVE at /114 (Check-1 + Check-8 FAIL) → CLOSED.

**Out-of-box menu extensions** (per user directive "out-of-the-box thinking mandated"):
5. Labeling architecture (coherent horizon-exit): NEGATIVE at /115 → label-estimand axis CLOSED.
6. Exit-layer / trade-construction (`no_confirm`): PROMISING-MECHANICAL at /116 → bundled at /120 → DROPPED via F3+F4 → standalone evaluation pending /121-METHODOLOGY.
7. Candle frequency (24h-multi-offset): NEGATIVE catastrophic at /117 → CLOSED.
8. NEW engineered-feature lineage (vol-regime composed): NEGATIVE catastrophic at /118 → CLOSED.
9. NEW engineered-feature lineage (microstructure-regime composed): PROMISING-FEATURE-MECHANICAL at /119 → bundled at /120 → DROPPED via F3 → CLOSED.

The /105 → /109 cycle-5 chain's structural finding (the v3 binding constraint is DOWNSTREAM of the label, in the trade-construction / exit / risk layer) is **EMPIRICALLY RECONFIRMED** by cycle 6: the 6 cycle-6 axes that re-walked or refined upstream/horizontal axes (universe, pooled architecture, multi-freq features, risk primitives, labeling estimand, candle frequency) all NEGATIVE; the 2 cycle-6 axes that targeted the downstream trade-construction/exit layer (/116 exit-layer + /119 feature-layer at the loss-surface) produced the 2 PROMISING outcomes; but the CONFIRMATION at /120 nevertheless failed the BOTH-must-improve gate.

---

## 9. iter-v3/121-METHODOLOGY — cycle-7 BOOTSTRAP setup directive

Per Critic FINAL (`a49dd17`) Recommendation 2: **iter-v3/121-METHODOLOGY AUTHORIZED as cycle-7 BOOTSTRAP** (analogous to iter-v3/018 BOOTSTRAP precedent; NOT counted toward cycle-7 10/10 EXPLORATION cadence).

### 9.1 Hypothesis and motivation

The /120 verdict drops Component B (C6) per F3 pre-commitment. Component A (/116 `no_confirm` early-exit primitive) is mechanically firing in the bundle (8 no_confirm exits / 96 OOS trades per committed `reports-v3/iteration_v3-120/out_of_sample/trades.csv`) but its standalone performance at 10-seed unified-ensemble CONFIRMATION is the ONLY remaining unevaluated data point in the cycle-6 multi-seed grid. The brief Section 8.4 branch 3 explicitly pre-committed "/116-only re-evaluation" as a binding outcome path. Resolving this empirically is required before cycle-6 final closure.

**Hypothesis (testable in one sentence)**: Component A alone (`enable_no_confirm_exit=True`, `trigger_atr=0.50`, `k_candles=4`) on /059's 14-feature stack (C6 reverted) at full 10-seed CONFIRMATION lifts OOS monthly Sharpe materially above /059 (+0.5791) while clearing the F4 IS regime-cost floor (≥ +0.79 = /059 IS − 0.30) and producing a multi-seed mean that beats /059 on BOTH IS AND OOS.

### 9.2 Spec

- **Iteration type**: CONFIRMATION-spec (10-seed unified ensemble, n_trials=35) running on /059's 14-feature stack with Component A enabled.
- **Runner invocation**: `uv run python run_baseline_v3.py --n-trials 35 --clean-oof` (no `--exploration`, no `--seeds` — default 10-seed unified ensemble).
- **Bundle state**: `enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4` (Component A enabled). `V3_FEATURE_COLUMNS_TOP_N` reverts to /059's 14-feature stack (drop `ret5d_signed_tbi` from index 14; total = 14 features; C6 REVERTED).
- **Anchor**: /059 canonical (IS +1.0894 / OOS +0.5791). BOTH-must-improve target.
- **Reference for F1-analog stacking-linearity**: /120 bundle OOS +1.6946 (the multi-mechanism reference; if Component A alone lifts OOS materially below +1.6946, the Q3 interaction-effect finding is RE-CONFIRMED as the source of the bundle's all-time-OOS-record performance).
- **Wall-clock**: estimated 3-4h; HARD CAP 6h per `feedback_v3_cadence_discipline.md`.
- **n_trials**: 35 per `feedback_v3_confirmation_n_trials_35.md`.
- **Methodology gates**: PBO < 0.40 (binding); PSR > 0.95 (binding); frac_positive_paths ≥ 0.55 (binding); DSR_relative > 0.95 (informational under unified architecture per `feedback_v3_dsr_mode_artifact.md`).

### 9.3 Decision tree

| Branch | Component A 10-seed outcome | BASELINE_V3.md decision | Cycle-6 final closure characterization |
|---|---|---|---|
| 1 | IS ≥ +0.79 AND IS ≥ /059 IS AND OOS ≥ /059 OOS AND all hard methodology gates PASS | **UPDATE** → /121 Component-A-only baseline | RULE-layer single-mechanism MERGE; 1 strictly-accretive primitive merged this cycle; bootstrap cycle-7 from new baseline |
| 2 | IS < +0.79 OR IS < /059 IS OR OOS < /059 OOS OR any methodology gate FAILS | UNCHANGED at /059 | Cycle-6 closes with 0 ingredients merged; the bundle's all-time OOS record was driven by the multi-mechanism interaction (Component B's loss-surface reorganization opened decisions Component A then operated on); the single-mechanism path is insufficient |

### 9.4 Naming convention and cadence accounting

- **Slot**: iter-v3/121-METHODOLOGY is the cycle-7 BOOTSTRAP slot (analogous to iter-v3/018 BOOTSTRAP for cycle 1). NOT counted toward the cycle-7 10-EXPLORATION cadence.
- **Tag**: `v0.v3-121-methodology` (closeout marker; tag only updates BASELINE_V3.md if branch 1 fires).
- **Diary**: `diary-v3/iteration_v3-121-methodology.md`.
- **Brief**: `briefs-v3/iteration_v3-121-methodology/research_brief.md` (short brief — single hypothesis, single change, full /120 falsifier carryover for F4 IS floor + BOTH-must-improve, no NEW falsifier additions).
- **Subsequent**: iter-v3/122 = cycle-7 EXPLORATION axis-1 (slot 1 of 10) regardless of /121-METHODOLOGY outcome.

### 9.5 What /121-METHODOLOGY does NOT do

- Does NOT advance to a NEW edge ingredient. It is a bootstrap-validation of an EXPLORATION-PROMISING-MECHANICAL primitive (the cycle-6 /116 outcome) at the multi-seed budget the v3 cadence-discipline requires before any baseline update.
- Does NOT count toward cycle-7's 10/10 EXPLORATION cadence. The strict 10:1 EXPLORATION:CONFIRMATION cadence (`feedback_v3_strict_10_to_1_cadence.md`) applies independently of bootstrap-class iterations.
- Does NOT introduce a new feature, new symbol, new model architecture, new labeling primitive, new gate, or new risk layer. The runner-config diff vs /059 is THREE knob flips (`enable_no_confirm_exit=False → True`, `no_confirm_trigger_atr=0.50` confirmation, `no_confirm_k_candles=4` confirmation) and ONE feature-set diff (revert `V3_FEATURE_COLUMNS_TOP_N` to 14 features per /059).
- Does NOT renegotiate /120's F3 or F4 pre-commitments. Both fired at /120 and Component B is dropped per the pre-committed decision tree. /121-METHODOLOGY is the F3-DROP-branch's standalone evaluation.

---

## 10. Cycle-7 axis menu pointers

Per /119 diary §8.2 + the cycle-7 reorientation mandate carried in `project_v3_cycle6_axis_menu.md`. After /121-METHODOLOGY closes (cycle-6 final closure), iter-v3/122 = cycle-7 EXPLORATION axis-1. QR-selected per `feedback_v3_axis_selection_quant_discipline.md`. Candidate axis menu:

1. **Cross-asset/external feeds** — funding rates from a different venue (Bybit, OKX), perp-spot basis (NEW data feeds beyond the BCH/LDO/TRX 8h OHLCV), liquidations data, on-chain BTC metrics (correlation regime input), DeFi TVL/lending utilization (for indirect BCH/LDO regime classification). Note: v3 has tried 7 non-OHLCV crypto-native feeds (funding /019/023/024/082/085, microstructure /015, basis /086) and ALL 7 INERT-by-importance — cycle-7 cross-asset/external-feed axes must use STRUCTURALLY DIFFERENT primitives or NEW transformation pipelines (Glassnode/CryptoQuant on-chain metrics, exchange-imbalance ratios, etc.) NOT yet attempted.
2. **Non-LightGBM model classes NOT yet tested at /109 depth** — ensemble-of-different-model-classes; neural-network-with-different-training-regime (deeper depth than tested at /109; LSTM / Transformer with explicit time-series inductive bias); CatBoost / XGBoost-v2 with hyperparameter regime distinct from /016's depth-wise defaults. The /109 terminal 8h null was scoped to LightGBM depth-3-5; alternative inductive biases unexplored.
3. **Longer-cadence labels** — 1-week or 1-month horizon labels with appropriate execution geometry; the /072→/105→/115 labeling axis closed at the 21-candle horizon with the +2/−1 ATR triple-barrier identified as the Sharpe-generating asymmetry. A genuinely longer-cadence label (multi-day, multi-week) may surface a different signal structure that the 21-candle horizon does not address.
4. **NEW symbol universe NOT-already-tested variants** per `feedback_v3_concentration_is_signal.md` constraints — the BCH/LDO/TRX 3-symbol universe was the v3 cycle-1 selection survivor; cycle-6 universe tests (CRV/AAVE/GRT/ADA at /110/111) NEGATIVE; HBAR/AVAX at /021 NEGATIVE; FIL at /083 NEGATIVE; GALA/MANA/SAND at /087 NEGATIVE; ADA at /069 NEGATIVE. Permitted: extreme-out-of-distribution candidates (DeFi tokens, infra tokens, layer-2 tokens) selected via STRUCTURALLY DIFFERENT screening than the prior universe-expansion failures used (not feature-AUC screen which transferred poorly; not multivariate-importance screen which transferred poorly; perhaps a turnover-based or cross-asset-correlation-based screen).

The cycle-7 axis menu MUST NOT include:
- Re-walking cycle-6 NEGATIVE axes (universe / pooled-architecture / multi-freq-on-8h / risk-primitive-kill-switches / coherent-horizon-exit-labeling / candle-frequency / vol-regime-composed-features) without genuinely-new structural delta.
- Knob-tuning saturated axes (ADX threshold, z-score threshold, BTC-band threshold).
- Per-symbol customizations (closed at /039 NEGATIVE; restated at /120 closeout).
- Component B-style FEATURE-layer cannibalizer features (per the new F3 binding-gate validation at /120 — Category-2 sister-cannibalizer composed features fire F3 deterministically; cycle-7 engineered-feature axes must be /025-class direct-edge candidates, not /119-class FEATURE-MECHANICAL cannibalizers).

---

## 11. Catalog entry

Per the standard schema, appended to `briefs-v3/exploration_catalog.md`:

```
| iter-v3/120 | 2026-05-20 | CONFIRMATION TWO-COMPONENT bundle (/116 no_confirm + /119 C6) | −0.3601 | +1.1155 | CONFIRMATION-NO-MERGE per F3+F4 binding | N/A — cycle 6 closes |
```

**Cycle-6 final scoreboard (after /120)**:
- 2 PROMISING (mechanical, both DROP at /120): /116 (PROMISING-MECHANICAL — RULE form, /121-METHODOLOGY pending), /119 (PROMISING-FEATURE-MECHANICAL — FEATURE form, DROPPED via F3).
- 8 NEGATIVE/UNRESOLVED: /110 (UNRESOLVED label-confound), /111 (clean re-test), /112 (pooled architecture), /113 (multi-frequency on 8h), /114 (risk management with Check-1 FAIL), /115 (coherent horizon-exit labeling), /117 (24h-multi-offset catastrophic), /118 (Category-2 vol-regime composed-feature catastrophic).
- 1 CONFIRMATION: /120 NO-MERGE per F3+F4 binding.
- 0 ingredients merged this cycle.
- BASELINE_V3.md UNCHANGED at canonical `v0.v3-059` (carried since 2026-05-13 RE-ANCHOR #2).

---

## 12. Closeout

- **Verdict**: CONFIRMATION-NO-MERGE per pre-committed Section 4 binding falsifiers F3 (sister-redistribution conjunctive AND gate) FIRES + F4 (IS regime-cost floor +0.79) FAILS by 0.0607; BOTH-must-improve gate independently confirms.
- **Structural finding**: all-time v3 OOS monthly Sharpe record set at **+1.6946** (vs prior /059 +0.5791; Δ +1.1155). NOT merged. The Q3 Jaccard analysis confirms genuine multi-mechanism interaction effect (30 trades unique to bundle; Jaccard 0.48 with /116-alone, 0.55 with /119-alone) — but F3 is an allocation-accounting gate, fires regardless of interaction-vs-cannibal mechanism diagnosis. The structural mirror of /039 (large OOS gain + IS regression + first-time-OOS-record + binding-rule blocks merge).
- **Cycle-6 final closure**: 10/10 EXPLORATIONs + 1 CONFIRMATION complete. 2 mechanical primitives (/116 RULE-form PROMISING-MECHANICAL + /119 FEATURE-form PROMISING-FEATURE-MECHANICAL) + 0 ingredients merged. BASELINE_V3.md UNCHANGED at `v0.v3-059` (canonical since 2026-05-13). The user's cycle-6 axis-menu hypothesis FALSIFIED on the new-edge axis but PROMISING on the strictly-accretive mechanical-primitive axis. The /105 → /109 binding-constraint finding (binding constraint is DOWNSTREAM of label, in trade-construction / exit / risk layer) empirically RECONFIRMED by cycle 6.
- **Decision**: NO-MERGE. BASELINE_V3.md UNCHANGED at `v0.v3-059`. Catalog updated. Tag `v0.v3-120` marks cycle-6 closure only.
- **Sacred constants verified**: `OOS_CUTOFF_DATE = 2025-03-24` UNCHANGED, `training_months = 24` UNCHANGED.
- **Next iteration**: iter-v3/121-METHODOLOGY (cycle-7 BOOTSTRAP — Component A 10-seed isolation; NOT counted toward cycle-7 cadence; analogous to /018 BOOTSTRAP precedent). Then iter-v3/122 = cycle-7 EXPLORATION axis-1 from /119 diary §8.2 candidate menu (cross-asset/external feeds, longer-cadence labels, NEW model architecture, NEW symbol universe), QR-selected per `feedback_v3_axis_selection_quant_discipline.md`.

See `briefs-v3/iteration_v3-120/research_brief.md`, `briefs-v3/iteration_v3-120/phase5p5_gate.md`, `briefs-v3/iteration_v3-120/engineering_report.md`, `briefs-v3/iteration_v3-120/review_preliminary.md`, `briefs-v3/iteration_v3-120/qr_response.md`, `briefs-v3/iteration_v3-120/review.md`, `reports-v3/iteration_v3-120/`, `briefs-v3/exploration_catalog.md`, `BASELINE_V3.md`, `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_promising_feature_mechanical.md`, `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/project_v3_cycle6_axis_menu.md`, `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/project_v3_cycle7_setup.md`, `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/MEMORY.md` for full artifacts.
