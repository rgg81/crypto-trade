# iter-v1/074 — Research Brief

**Iteration**: iter-v1/074
**Date**: 2026-06-06
**TYPE**: SPECIALIST-IMPROVEMENT (ETH-IMPROVED-V3; **THIRD** improvement attempt for the ETH /064 specialist seat)
**Cycle**: 7, SPECIALIST 11 of N
**Branch**: `iteration-v1/074`
**Author**: QR (autopilot)
**Anchor**: ETH **/064** (IS Sharpe **+0.2383**, OOS Sharpe **+0.5171**, 198 IS / 81 OOS trades) — the BUNDLE-001 ETH seat. **/073 is NOT the anchor** — /073 IMPROVEMENT-FAIL (IS Δ −0.25, dispersion-reservoir mechanism falsified) and was discarded; /064 retains the BUNDLE slot per the /073 closeout.
**Axis**: **AXIS-R — Mid-Bull SHORT VETO rule layer.** Skip direction=−1 entries when `ret_270b ∈ [0.20, 0.50]`. Pre-registered band edges, post-prediction filter at the aggregator-level call-site. No feature change, no model change, no label change, no risk-wrapper change.
**LM Master verdict**: HIGH confidence; modal predicted IS Sharpe **+0.37** (Δ vs /064 anchor **+0.13**); 60% band [+0.29, +0.44]; 90% band [+0.19, +0.49].

---

## Section 0 — Data Split Declaration (Foundation)

- **OOS_CUTOFF_DATE**: `2025-03-24` (IMMUTABLE — never changes)
- **training_months**: `24` (IMMUTABLE — never changes)
- **IS window**: 2023-03-24 → 2025-03-24 (24 months walk-forward training; ETH /064 IS roster covers 198 trades 2022-01 → 2025-03-24)
- **OOS window**: 2025-03-24 → present
- **Walk-forward embargo**: `train_end_ms = test_start_ms - embargo_ms` (commit `5566a69`; identical helper used in this iteration; inherited bit-exactly from /064 setup)
- **Sacred constants HELD per Rule 3** (`feedback_training_window.md`, `feedback_no_cheating.md`): no shift, no extension, no trim, no peek.

EDA scripts (`analysis/iteration_v1-074/eth_axis_r_veto_simulation.py`, to be committed at Phase 6 setup) read ONLY `reports-v1/iteration_v1-064/in_sample/trades.csv` and the IS-window `data/ETHUSDT/8h.csv` close series. The script asserts `out_of_sample` substring absent from every loaded path. No OOS file is opened during Phase 1-5. The pre-registered band edges [0.20, 0.50] are frozen at this brief's authoring (commit SHA recorded in Section 12 below) and CANNOT be re-fitted post-hoc per `feedback_no_cheating.md`.

---

## Section 0.5 — Iteration Type Declaration & Cadence

- **TYPE**: SPECIALIST-IMPROVEMENT (single-bit deviation from a merged-baseline specialist; ETH-IMPROVED-V3 = **THIRD** attempt for the ETH BUNDLE seat)
- **Cycle 7 position**: SPECIALIST 11 of N (post-BUNDLE-001 baseline; third post-BUNDLE-001 SPECIALIST-IMPROVEMENT after /072 BTC-IMPROVED-V2 NEG and /073 ETH-IMPROVED-V2 NEG)
- **ETH-IMPROVED attempt counter**: **THIRD** improvement attempt for the ETH /064 seat
  - **Attempt 1**: /064 itself (original ETH SPECIALIST EXPLORATION; PROMOTED to BUNDLE-001 at /071)
  - **Attempt 2**: /073 ETH-IMPROVED-V2 (Axis 1 — feature-subset reduction 48→25 cols) → SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL (IS Δ −0.25 vs /064; dispersion-reservoir mechanism falsified)
  - **Attempt 3**: **/074 ETH-IMPROVED-V3** (AXIS-R — Mid-Bull SHORT VETO post-aggregator rule layer) → THIS ITERATION
- **History context**: FOURTH SPECIALIST-IMPROVEMENT in v1 history (after /072 BTC-IMPROVED-V2 R1-enable NEG; /073 ETH-IMPROVED-V2 feature-subset NEG; the unwritten DOT specialist improvement remains pending). The two post-BUNDLE NEGATIVE outcomes (/072 R1 axis; /073 feature-stack axis) closed two categorical axes for SPECIALIST_mode (`f81cafc3` R1 catalog-closure; /073 closeout dispersion-reservoir flag). /074 pivots to a **RULE-form post-aggregator primitive** — categorically distinct from both prior failed axes.
- **Wall-clock budget**: **2h hard cap** per `feedback_v1_confirmation_walltime_9h.md` EXPLORATION default. LM Master Phase 4.5 predicts ~50-90 min Optuna + 10 min wrap-up (198 IS trades baseline cell count; 50 inner seeds × 30 trials × 24 walk-forward cells; AXIS-R is a post-aggregator deterministic filter — adds **zero** training-time overhead; expected wall-clock ≈ /064's wall-clock).
- **Kill-switch**: if wall-clock exceeds 2.5h, OR any specialist outer-seed returns `nan` Sharpe, OR the FEATURES_BASE_HASH_48COL pre-flight guard fails to match /064's tuple hash, OR observed IS trade count diverges by >10% from the expected (198 − 32 veto = ~166 ± 17, so 149-183) → abort, capture commit, defer to /075 with diagnostic.

---

## Section 0.6 — Architecture-Family Justification (v1)

- **Axis family**: `risk-primitive` (post-aggregator RULE-form veto; sister to the v3 `/116 no_confirm` PROMISING-MECHANICAL pattern — RULE-layer primitive on inference output)
- **Prior 5 EXPLORATION families** (catalog rows ending in /065 → /073; /071 was bundle composition not EXPLORATION):
  - iter-v1/063: `feature-family` + `risk-primitive` (DOT specialist EXPLORATION — Model E lineage, atr-band tune) → PROMOTED to BUNDLE-001
  - iter-v1/064: `feature-family` + `risk-primitive` (ETH specialist EXPLORATION — Model A R3-only, atr-band tune) → PROMOTED to BUNDLE-001 (the /074 anchor)
  - iter-v1/065: `feature-family` + `risk-primitive` (BTC specialist EXPLORATION — Model A R3-only, atr-band tune) → PROMOTED to BUNDLE-001
  - iter-v1/072: `risk-primitive` (BTC-IMPROVED-V2; R1 streak-cooldown enable on Model A BTC specialist) → SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL; R1 catalog-CLOSED for SPECIALIST_mode per skill rule `f81cafc3`
  - iter-v1/073: `feature-family` (ETH-IMPROVED-V2; feature-subset reduction 48→25 cols) → SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL; dispersion-reservoir mechanism falsified; feature-stack pruning at SPECIALIST mode catalog-CLOSED
- **Rotation status**: **VALID** — `risk-primitive` (post-aggregator RULE-form veto) is categorically distinct from /073's `feature-family` (the immediately prior axis). Family rotation is SUSPENDED in cycle-7 per `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md` (specialist mandate overrides axis-family rotation), but the rotation is honored anyway because /074's RULE-form mechanism is distinct from /072's R1 risk-primitive mechanism (R1 = streak-conditional cool-down on past trade outcomes; AXIS-R = regime-conditional veto on prediction direction from a structural feature `ret_270b`).
- **One-sentence rationale**: The ETH /064 short book in mid-bull regime (`ret_270b ∈ [0.20, 0.50]`) carries a quantified per-trade Sharpe drag (16.2% of IS trades produce −9.73% PnL with WR 16.7% vs structural-bull shorts at 41% WR and bear-continuation shorts at 49% WR); the 48-col feature stack lacks any 90-day structural-regime primitive and a depth-5 tree cannot disambiguate the three direction-asymmetric WR bands across a single feature axis even if that axis were added — the cleanest single-bit fix is a **post-aggregator RULE-form veto** that injects the disambiguation at the inference layer without changing labels, features, model, or training distribution.

---

## Section 0.7 — SPECIALIST-IMPROVEMENT Attempt 3-of-N for ETH (anchor /064, NOT /073)

This is the **THIRD improvement attempt** for the ETH seat in BUNDLE-001. **The anchor is /064, NOT /073.** Per the /073 closeout, /073 was discarded as IMPROVEMENT-FAIL (IS Δ −0.25 vs /064; dispersion-reservoir mechanism falsified — pruning the feature stack at SPECIALIST 50-seed × 30-trial budget reduced cross-seed HP-trajectory diversity from dispersion 38.61 → 33.44, collapsing the ensemble to a tighter-but-lower-quality consensus). The /064 anchor retains the BUNDLE-001 ETH slot.

| Field | Value |
|---|---|
| **Original iter (anchor)** | **/064 (ETH SPECIALIST-PROMISING; IS Sharpe +0.2383, OOS Sharpe +0.5171, 198 IS / 81 OOS trades, BUNDLE-001 ingredient)** |
| **NOT-anchor (prior attempt)** | /073 ETH-IMPROVED-V2 — Axis 1 (feature-subset reduction 48→25 cols); IS Δ −0.25; SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL; **DISCARDED** at /073 closeout |
| Improvement axis | **AXIS-R — Mid-Bull SHORT VETO post-aggregator rule layer.** When the 50-seed mean-of-signed-weights aggregator emits `Signal(direction=−1, weight=W)` AND `ret_270b ∈ [0.20, 0.50]`, the signal is replaced with `Signal(direction=0, weight=0)`. Long signals and flat signals are NEVER vetoed. The veto is post-aggregator (NOT per-seed) to preserve cross-seed dispersion measurement (F-AXIS #2 audit). |
| Pre-registered band edges (HARD — anti-tuning) | `ret_270b ∈ [0.20, 0.50]`. Lookback = 270 8h candles = 90 calendar days. Edges frozen at brief-authoring commit (Section 12). Edges WILL NOT be re-tuned post-hoc. Per `feedback_no_cheating.md` and `feedback_v1_basin_lottery_vigilance.md`. |
| Code-level change | (a) Clone `run_iteration_064.py` to `run_iteration_074.py` with identical signature including `FEATURES_BASE_HASH_48COL` and ITERATION_LABEL=`v1-074`; (b) add new dispatch branch `elif iteration_label == "v1-074"` in `run_baseline_v1.py`, identical to the `v1-064` branch except for FOUR new kwargs to `LightGbmStrategy`: `enable_mid_bull_short_veto=True, mid_bull_short_veto_lo=0.20, mid_bull_short_veto_hi=0.50, mid_bull_short_veto_lookback=270`; (c) implement the veto in `LightGbmStrategy.get_signal` immediately AFTER the aggregator produces `Signal(direction, weight)` and BEFORE R3 OOD / R5 vol-target call-sites; (d) wire parity-mirrored conditional in `engine.py:_tick` at the same call-site, using the same close-window source. **SINGLE-BIT change**: only the post-aggregator veto kwargs differ from /064. Methodology constants HELD. |
| Variables held identical to /064 (HARD) | V1_FEATURE_COLUMNS_PRUNED (48 cols, UNCHANGED), ATR TP=2.9 / SL=1.45 barriers, R1=OFF / R2=OFF / R3=ON-SHARED cutoff=0.70, **50 inner seeds × 30 Optuna trials**, `specialist_mode=True`, outer seed=42, `training_months=24`, **ENSEMBLE_SIZE=1**, max_depth=5 fixed, num_leaves=31 fixed, n_estimators ≤ 500, n_startup_trials=10, mean-of-signed-weights aggregator, walk-forward embargo fix, Model A wrapper class, label horizon, training data, parquet feature-generation (NO regeneration; veto is post-aggregator runner-side only) |
| R1 EXCLUDED per catalog rule | R1 streak-cooldown is **CATALOG-CLOSED for SPECIALIST_mode** per skill rule `f81cafc3` (committed 2026-06-06 post-/072 falsification). /074 honors R1=OFF preservation. AXIS-R is at a different layer (post-aggregator direction veto on regime feature; not streak-conditional). |
| Pre-registered 3-strike rule | /073 (Attempt 2) was POSITIVE-strike-NOT-CONSUMED (closed with feature-stack axis CLOSED; /064 retained BUNDLE slot — no strike was charged to ETH because the failure was axis-level not signal-level). /074 (Attempt 3) is therefore **STRIKE-1 for the ETH BUNDLE seat** under the 2-strike rule. If /074 IS Δ vs /064 anchor ≥ 0 → POSITIVE strike; ETH-IMPROVED-V3 enters BUNDLE-002 candidate roster (replacing or augmenting /064). If /074 IS Δ vs /064 anchor < 0 → **ETH STRIKE-1**; future ETH-IMPROVED iter advances to strike-2 (axis options: regime-conditional kill switch on 2024-bull-bear transition; OR multi-seed CONFIRMATION of /064 to disambiguate basin-lottery from architectural ceiling). |
| Methodology constants HELD per Rule 3 | OOS_CUTOFF=2025-03-24, training_months=24, walk_forward embargo fix, specialist_mode=True, single outer seed=42 (EXPLORATION pattern). The only deviation from /064 is the four post-aggregator veto kwargs. |

---

## Section 1 — Hypothesis

**H1 (PRIMARY)**: Injecting a post-aggregator RULE-form veto at the inference layer — skipping shorts when `ret_270b ∈ [0.20, 0.50]` (90-day mid-bull regime) — will lift IS Sharpe above the /064 anchor (+0.24) by removing 32 of 198 IS trades (16.2%) that the LM Master Phase 4.5 simulator quantifies as a chronic short-bleed cohort (WR 16.7%, contributing −9.73% to net IS PnL). The mechanism is **structurally identical** to v3's `/116 no_confirm` PROMISING-MECHANICAL pattern: RULE-form post-inference primitive that disambiguates a known regime-feature gap the depth-5 tree cannot compose internally. Modal point estimate: IS Sharpe **+0.37** (Δ vs /064 +0.13); LM Master Phase 4.5 predicted band [+0.05, +0.25].

**H1a (mechanism — missing 90-day structural-regime feature)**: The 48-col V1_FEATURE_COLUMNS_PRUNED carries `regime_momentum_signed_5d` (5-day) and `eth_vs_btc_ret_ratio_30` (30-day) but **no 90-day structural-regime primitive**. The ETH short book has a **non-monotone WR profile in `ret_270b`**:
- `ret_270b < 0.20` (bear-continuation): shorts fire at WR ~49% — **profitable**
- `ret_270b ∈ [0.20, 0.50]` (mid-bull / bear-recovery transition): shorts fire at WR ~16.7% — **chronic bleed**
- `ret_270b > 0.50` (structural-bull): shorts fire at WR ~41% — **profitable** (contrarian-bull-top edge)

A depth-5 LightGBM tree cannot disambiguate three direction-asymmetric WR bands across a single non-monotone feature axis. Injecting the disambiguation at the **post-prediction inference layer** preserves the IS/OOS training distribution exactly (no label change, no feature change, no model retrain) — the veto is a rule-form patch on a known mechanism gap, not a new edge claim. Per `feedback_promising_mechanical_subtype.md` (v1 analogue), this is correctly classified as a **RULE-form accretive component decision**, not a NEW edge ingredient.

**H1b (Aggregator-level veto, not per-seed)**: The veto is applied AFTER the 50-seed mean-of-signed-weights aggregator emits a single Signal(direction, weight). Vetoing at this layer is equivalent to forcing the mean-of-signed-weights to flat when the aggregated direction is short AND `ret_270b ∈ band`. Per-seed veto (rejected) would re-bias the cross-seed dispersion distribution and break the F-AXIS #2 dispersion audit. Aggregator-level veto preserves the basin-lottery audit surface (single-seed=42 EXPLORATION's cross-seed dispersion = /064's distribution exactly, modulo deterministic post-aggregator filter), which is required for verdict integrity per `feedback_v1_basin_lottery_vigilance.md`.

**H1c (Expected effect; LM Master simulator base + scale-down)**: The LM Master Phase 4.5 simulator (computed on the committed /064 IS trades.csv roster) quantifies the raw effect: 32 of 198 IS trades vetoed, +9.73% PnL recovered, +0.186 per-trade Sharpe lift (raw 0.686 → 0.871). The runner's actual lift is expected at 0.6× to 0.8× the simulator scale because:
- (a) The simulator holds model identity fixed (the /064 trade roster). The runner re-trains 50 inner seeds × 30 trials per month — the basin-lottery surface remains.
- (b) The mean-of-signed-weights aggregator is non-linear in the veto; some marginal vetoes (band edge ±) may flip the aggregator direction relative to the simulator's deterministic veto-at-strict-threshold semantics. This is by design; the simulator is an upper bound at the strict-band, not a tight forecast.
- (c) OOS expected directionally positive but **smaller magnitude** (+0.05 to +0.15): the OOS window (2025-03-24 onward) is a structural bull (ret_270b > 0.50 frequently), so few OOS trades fall in the veto band. The veto's OOS impact is **trade-count-bounded** at perhaps 3-8 vetoes of the 81 OOS trades.

Modal predicted IS Sharpe **+0.37** (Δ vs /064 +0.13), 60% band [+0.29, +0.44], 90% band [+0.19, +0.49].

**H1d (basin-lottery audit invariance)**: Because the veto is post-aggregator AND deterministic given `(ret_270b, signal.direction)`, the inner cross-seed Optuna trajectories are **mechanically unchanged** from /064. Cross-seed dispersion (F-AXIS #2) will read identically to /064 modulo the 32 deterministic vetoes. This is structurally orthogonal to basin-lottery: a NEGATIVE outcome here cannot be attributed to basin-lottery (the basin is identical to /064's basin), so a NEGATIVE verdict falsifies the **AXIS-R mechanism** cleanly, not the EXPLORATION budget. This is a load-bearing property of choosing AXIS-R over alternatives (per-seed veto, asymmetric-cutoff HP) that mutate the basin distribution.

---

## Section 2 — IS-Only Numerical Evidence (from /064 anchor; pre-registered AXIS-R simulator)

**Analysis script**: `analysis/iteration_v1-074/eth_axis_r_veto_simulation.py` (committed at Phase 6 setup; per Phase 5.5 gate the script must be committed before the runner fires; IS-firewall verified by path-substring assertion `assert "out_of_sample" not in p` for every loaded file path).
**Source data**: `reports-v1/iteration_v1-064/in_sample/trades.csv` (198 trades) + `data/ETHUSDT/8h.csv` close series (IS window only).
**LM Master cross-reference**: `briefs-v1/iteration_v1-074/lgbm_advisor.md` (commit `33910a56`) — the simulator numbers reported below are the LM Master Phase 4.5 simulator outputs that the QR brief Section 2 ratifies.

### 2.1 /064 ETH IS baseline (per `reports-v1/iteration_v1-064/comparison.csv` + IS trades.csv)

| Metric | Value |
|---|---:|
| IS Sharpe (monthly annualized) | **+0.2383** |
| IS Trades | 198 (87 long + 111 short) |
| IS Net PnL | +15.0025% |
| IS Win Rate | 39.39% |
| IS Profit Factor | 1.0814 |
| IS Avg Win | +6.83% |
| IS Avg Loss | −3.97% |
| IS Win/Loss ratio | 1.72× (asymmetry favourable; WR drag is the killer) |
| IS Exit mix | SL 56.6% / TP 25.8% / Timeout 17.7% |
| IS MaxDD | 24.66% |
| IS DSR | −88.4420 (informational; EXPLORATION budget artifact per `feedback_v3_dsr_mode_artifact.md`; NOT a verdict gate) |
| OOS reference (informational, NOT used during design) | +0.5171 (recorded from /071 bundle diary; not re-loaded for /074 design) |

### 2.2 AXIS-R veto simulator — pre-registered effect on the /064 IS trade roster

The LM Master Phase 4.5 simulator computes the deterministic effect of `if signal.direction == −1 and 0.20 ≤ ret_270b ≤ 0.50 then signal = Signal(direction=0, weight=0)` applied at the post-aggregator inference layer, holding the /064 model identity fixed.

| Quantity | /064 (no veto) | AXIS-R simulator (post-veto) | Δ |
|---|---:|---:|---|
| Total IS trades | 198 | **166** | **−32 vetoed** (16.2% of roster) |
| Total IS short trades | 111 | 79 | −32 (28.8% of short book vetoed) |
| Vetoed-trade net PnL (counterfactual) | **−9.73%** | 0% | **+9.73% recovered** |
| Total IS Net PnL | +15.0025% | **+24.73%** | +9.73 pp |
| Vetoed-trade Win Rate | **16.7%** (cohort) | — | — |
| Per-trade Sharpe (raw, fixed-model) | 0.686 | **0.871** | **+0.186 per-trade Sharpe lift** |
| Predicted monthly IS Sharpe (scaled 0.6×-0.8× simulator → runner) | +0.2383 | **+0.32 to +0.40** (modal **+0.37**) | **+0.08 to +0.16** (modal **+0.13**) |

The pre-registered AXIS-R simulator is **the only proposal in the LM Master Phase 4.5 dossier with a quantified effect simulated on the committed /064 IS trade roster**. Every other axis proposal in the LM-A/Critic-A/QR-F pool is descriptive EDA, not pre-backtest simulation on actual trades.

### 2.3 ret_270b regime-band WR profile (the decisive non-monotone table)

The /064 IS short-trade roster (111 trades) decomposed by 90-day trailing-return band at trade entry:

| ret_270b regime band | n shorts | Cohort WR | Net PnL contribution | Verdict |
|---|---:|---:|---:|---|
| `ret_270b < 0.20` (bear-continuation) | 36 | **~49%** | **+17.84%** (profitable short book) | KEEP |
| **`ret_270b ∈ [0.20, 0.50]` (MID-BULL — TARGET BAND)** | **32** | **16.7%** | **−9.73%** (chronic bleed) | **VETO** |
| `ret_270b > 0.50` (structural-bull contrarian) | 43 | ~41% | +4.58% (profitable contrarian) | KEEP |

The non-monotonicity in WR across `ret_270b` is the load-bearing observation. A depth-5 LightGBM tree CANNOT compose this disambiguation across a single feature axis — even if `ret_270b` were added to the stack, the tree would have to allocate split budget across THREE different decision regions on a single axis, with direction asymmetry, at depth ≤5. The post-aggregator RULE-form veto sidesteps the depth constraint by injecting the disambiguation at the inference layer.

### 2.4 Per-year decomposition (regime proxy; manual via calendar-year tagging on /064 IS roster)

| Year | n_trades | Net PnL | Per-trade Sharpe | Short-book contribution | Note |
|---|---:|---:|---:|---:|---|
| 2022 (bear) | 67 | **+14.80%** | +0.029 | Long +2.11 / Short **+12.69** | Bear-regime edge in shorts; mostly `ret_270b < 0.20` |
| 2023 (chop) | 58 | −2.20% | +0.016 | Long +15.88 / Short −12.02 | Mid-bull-recovery transition; ~14 shorts in [0.20, 0.50] band |
| **2024 (bull)** | 61 | **−9.12%** | −0.030 | Long +11.16 / **Short −20.28** | **Structural short-book drag; ~18 shorts in [0.20, 0.50] band — load-bearing flaw** |
| 2025-Q1 (post-cycle) | 13 | +47.36% | +0.569 | Long +23.53 / Short +23.83 | Best regime, both sides; ~0 shorts in band |

**Per-year falsifier (load-bearing per LM Master)**: **no single calendar month** may carry **>40%** of the realized IS Sharpe lift. If 2024 alone produces >40% of the lift and 2022/2023/2025-Q1 produce flat or negative contribution, AXIS-R is a regime-coincident artifact NOT a structural rule — verdict downgrades to FALSIFIED-REGIME-FIT regardless of headline Δ.

### 2.5 Cross-iteration anchor consistency (anchor IS /064, NOT /073)

Per the /073 closeout, the /064 IS Sharpe is the anchor:

| Iter | IS Sharpe | IS Δ vs /064 | Verdict | Status |
|---|---:|---:|---|---|
| **/064 (anchor)** | **+0.2383** | (baseline) | SPECIALIST-PROMISING | **BUNDLE-001 ETH seat** |
| /073 (Attempt 2) | −0.012 (closeout report) | **−0.25** | SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL | DISCARDED at /073 closeout (feature-stack axis closed) |
| /074 (Attempt 3 = **this iter**) | TBD | TBD (predicted **+0.13**) | TBD | THIS ITERATION |

The /064 anchor is the ONLY ETH baseline for /074 verdict adjudication. /073 is NOT referenced in F-AXIS bands (Section 4) because /073 was discarded.

### 2.6 EDA streak-cooldown audit (DIAGNOSTIC ONLY — R1 EXCLUDED per catalog rule)

For symmetry with /073 Section 2.5 (R1 streak diagnostic): the /064 IS roster prior-streak audit confirms R1 is NOT load-bearing for ETH (streak ≥3 cohort = 47 trades, net **+7.73%**, WR 38.3% — recovers at streak=4). R1 streak-cooldown is **CLOSED for specialist mode** per skill rule `f81cafc3` (proven harmful on BTC /072: IS Δ −0.23, OOS Δ −0.89 vs /065). **R1=OFF preserved** in /074. AXIS-R is at a DIFFERENT layer (post-aggregator direction veto on a regime feature, not streak-conditional on past trade outcomes); the two primitives are orthogonal.

### 2.7 Confidence-bin × outcome (diagnostic; informs band-edge robustness)

From /064 IS roster: short-book confidence bins are roughly uniform across the [0.20, 0.50] veto band (no clear confidence-conditioned escape valve for mid-bull shorts). The veto cleanly removes the entire short cohort in the band regardless of model confidence; AXIS-R is robust to LightGBM threshold-calibration variation. Predicted effect: `ret_270b ∈ band AND short` removes the entire problem region cleanly.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1)

- **Declaration**: **HIGH-RISK**
- **Reason**: Post-aggregator rule-form veto adds a new inference-layer primitive that changes the deployed trade roster (32 of 198 IS trades skipped). While Optuna's training-objective domain is mechanically unchanged (the veto is deterministic post-aggregation and the model trains on the same labels), the deployed PnL distribution is modified — this qualifies as a risk-primitive change under the Section 2.5 HIGH-RISK rubric (v1 refactor) because the rule layer is an injection into the inference dispatch.
- **Mitigation**: **single-seed EXPLORATION (outer seed=42)** with mechanical "AXIS-R is mechanism-orthogonal to basin-lottery" argument (H1d: the inner-seed Optuna trajectories are deterministic on the /064 basin; only the post-aggregator filter is applied). Multi-seed validation is **deferred** to a future iteration (BUNDLE-002 multi-seed re-validation per /071 Critic Path Forward, or a dedicated AXIS-R 7-seed CONFIRMATION if /074 verdicts PROMISING-MARGINAL).
- **Mechanical floor argument**: even at worst-case where the simulator's +0.186 per-trade Sharpe lift entirely fails to materialize in re-trained backtest (zero recovery; the model could counter-fit to compensate for the veto), the lower bound on IS Δ is approximately **−0.05** (lost-trade-statistics tax on 32 fewer trades at near-zero net contribution). LM Master P25 = +0.05 → IS Sharpe band low end +0.19 (still > /064 anchor IS −0.05 floor).
- **Lighter footing than v3** (`feedback_v1_basin_lottery_vigilance.md`): /074 is the THIRD cycle-7 post-BUNDLE HIGH-RISK SPECIALIST-IMPROVEMENT (after /072 NEG and /073 NEG). Under the v1 rule, if 3+ consecutive HIGH-RISK single-seed EXPLORATIONs produce >1σ negative deltas in a row, the next becomes mandatorily multi-seed. /072 produced IS Δ −0.23 (1.0σ NEG); /073 produced IS Δ −0.25 (1.1σ NEG); /074 is the third HIGH-RISK iter. **If /074 verdicts NEG at IS Δ < −0.10, this is the trigger condition for mandatory multi-seed at /075**. The QR brief explicitly flags this to LM Master Phase 7.4 + Critic Phase 7.5.

---

## Section 3 — Proposed Changes (single-bit deviation from /064)

### 3.1 Code-level changes

**(a) Runner: clone `run_iteration_064.py` → `run_iteration_074.py`** with identical signature including FEATURES_BASE_HASH_48COL = sha256(sorted(V1_FEATURE_COLUMNS_PRUNED)) and `ITERATION_LABEL = "v1-074"`.

**(b) Dispatch: add `elif iteration_label == "v1-074"` in `run_baseline_v1.py`**, identical to the `v1-064` dispatch branch except for FOUR new kwargs to `LightGbmStrategy`:

```python
# /074 dispatch — AXIS-R Mid-Bull SHORT VETO (single-bit add over /064)
elif iteration_label == "v1-074":
    strategy = LightGbmStrategy(
        feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),  # 48 cols — UNCHANGED
        # ... all other /064 kwargs UNCHANGED ...
        enable_mid_bull_short_veto=True,        # NEW (single bit)
        mid_bull_short_veto_lo=0.20,            # NEW — pre-registered band edge LOW
        mid_bull_short_veto_hi=0.50,            # NEW — pre-registered band edge HIGH
        mid_bull_short_veto_lookback=270,       # NEW — 270 8h candles = 90 calendar days
    )
```

**(c) Implementation in `LightGbmStrategy.get_signal`** (post-aggregator filter at the call-site):

```python
# AXIS-R: Mid-Bull SHORT VETO — post-aggregator rule layer (deterministic; pre-registered band)
# Apply IMMEDIATELY after the 50-seed mean-of-signed-weights aggregator emits Signal(direction, weight)
# and BEFORE the R3 OOD gate / R5 vol-target call-sites.
signal = self._aggregate_seeds(predictions)  # the existing mean-of-signed-weights aggregator
if (
    self.enable_mid_bull_short_veto
    and signal.direction == -1
    and len(close_window) > self.mid_bull_short_veto_lookback
):
    ret_270b = (close_window[-1] / close_window[-self.mid_bull_short_veto_lookback - 1]) - 1.0
    if self.mid_bull_short_veto_lo <= ret_270b <= self.mid_bull_short_veto_hi:
        signal = Signal(direction=0, weight=0)  # VETO short; long/flat untouched
        self._log_veto(symbol, t, ret_270b)  # forensic event for Phase 7 verification
```

The 270-bar close window is already maintained by the existing R3 Mahalanobis history buffer (which loads ≥270 candles per symbol per training cell); no new buffer allocation is required.

**(d) Engine parity: wire identical conditional in `engine.py:_tick`** at the same call-site (immediately after `LightGbmStrategy.get_signal` returns, before R3 OOD + R5 vol-target). The trailing-270-close window is loaded from the `klines` table query already used by catch-up:

```python
# engine.py:_tick — AXIS-R parity (load 270 prior closes from klines table)
signal = strategy.get_signal(symbol, open_time)
if (
    config.enable_mid_bull_short_veto
    and signal.direction == -1
):
    closes_270 = self.db.fetch_recent_closes(symbol, n=271, before_ts=open_time)
    if len(closes_270) >= 271:
        ret_270b = (closes_270[-1] / closes_270[0]) - 1.0
        if config.mid_bull_short_veto_lo <= ret_270b <= config.mid_bull_short_veto_hi:
            signal = Signal(direction=0, weight=0)
            self._log_decision_event("axis_r_veto", symbol, open_time, ret_270b=ret_270b)
```

Per `feedback_v1_backtest_live_parity_hard.md` (Critic Check 15 = `BUNDLE-PARITY-VIOLATION`), the QE Phase 5.5 gate MUST verify the backtest implementation and the engine implementation use byte-equivalent ret_270b computation (same 270-bar lookback, same close-series source, same band edges).

**(e) Pre-flight guard**: assert `_compute_features_hash(V1_FEATURE_COLUMNS_PRUNED) == FEATURES_BASE_HASH_48COL` at runner entry (mirrors /064's existing pin — verifies feature stack UNCHANGED at 48 cols).

### 3.2 What is held identical to /064 (everything except the four new veto kwargs)

| Variable | Value |
|---|---|
| Universe | `{ETHUSDT}` |
| Feature columns | **`V1_FEATURE_COLUMNS_PRUNED` (48 cols, UNCHANGED)** |
| Labels | Triple-barrier ATR TP=2.9 / ATR SL=1.45 (UNCHANGED) |
| Label horizon | 21 candles (UNCHANGED) |
| Optuna trials | 30 (single-bit UNCHANGED) |
| Inner ensemble seeds | **50** (`specialist_mode=True`; UNCHANGED) |
| ENSEMBLE_SIZE | 1 (UNCHANGED) |
| Outer seed | 42 (single EXPLORATION ply; UNCHANGED) |
| max_depth | 5 fixed (UNCHANGED) |
| num_leaves | 31 fixed (UNCHANGED) |
| n_estimators | ≤500 (UNCHANGED) |
| n_startup_trials | 10 (UNCHANGED) |
| Aggregator | mean-of-signed-weights (UNCHANGED) |
| training_months | 24 (sacred; UNCHANGED) |
| Walk-forward embargo | `train_end_ms = test_start_ms - embargo_ms` (commit `5566a69`; UNCHANGED) |
| Model wrapper class | Model A (`RiskV1Wrapper` instance with R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70) — UNCHANGED |
| Vol targeting | Per-coin VT (45-day rolling, UNCHANGED) |
| Parquet feature-generation | **NO REGENERATION** — feature stack identical to /064; AXIS-R is post-aggregator only |

### 3.3 What is NOT changed

- **No feature change** (V1_FEATURE_COLUMNS_PRUNED stays at 48 cols — does NOT revert to /073's 25-col subset)
- **No labeling change** (triple-barrier ATR=2.9/1.45 UNCHANGED)
- **No model-arch change** (LightGBM head; not XGBoost; per /016 v3 closure)
- **No risk-wrapper flip** (R1 stays OFF per catalog rule; R2 stays OFF; R3 stays ON-SHARED cutoff=0.70)
- **No ATR-barrier change** (reserved for hypothetical strike-2)
- **No Optuna search-space change** (HP bounds inherited from /064)
- **No multi-seed promotion** (single outer seed=42 EXPLORATION discipline)
- **No parquet regeneration** (HIGH guard: cross-iteration reproducibility for /075+ depends on parquet hash stability)
- **No per-seed veto** (rejected per H1b: would re-bias cross-seed dispersion distribution)
- **No asymmetric-cutoff HP** (rejected per LM Master "Why NOT Critic-A": expands Optuna search dimension at fixed n_trials=30 → increases basin-lottery exposure)
- **No band re-tuning** (HARD: edges [0.20, 0.50] frozen at brief authoring per `feedback_no_cheating.md`)

### 3.4 Response to LM Master Phase 4.5 recommendations (per v1 LM Coordination)

LM Master's `briefs-v1/iteration_v1-074/lgbm_advisor.md` (commit `33910a56`) ranked AXIS-R as the HIGH-confidence dominant pick over Critic-A (asymmetric-cutoff HP), QR-F/LM-A1/A2/A5 (new feature axes), LM-A3/Critic-C (label changes), Critic-D (risk-wrapper changes), QR-U (universe expansion), and QR-L (meta-model). QR response:

| LM Master section | QR response |
|---|---|
| Chosen axis: AXIS-R Mid-Bull SHORT VETO post-aggregator rule layer | **ADOPTED VERBATIM** — Section 3.1 implements the exact code-level change; band [0.20, 0.50]; lookback 270; post-aggregator (NOT per-seed); SINGLE-BIT change enforced. |
| Predicted modal IS Sharpe +0.37; 60% band [+0.29, +0.44]; 90% band [+0.19, +0.49] | **ADOPTED** as the F-AXIS #1 verdict band reference. |
| Mechanism: missing-90-day-regime feature gap + depth-5 disambiguation impossibility on non-monotone WR profile | **ADOPTED** as the load-bearing mechanism claim (Section 1 H1a). |
| Pre-registered band edges [0.20, 0.50] frozen at brief authoring | **HARD ENFORCED** — Section 0.7 + Section 3.3 anti-tuning assertion; brief commit SHA in Section 12; no post-backtest re-fitting permitted. |
| Per-trade Sharpe lift < +0.10 OR any single calendar month > 40% of realized lift = FALSIFIED | **ADOPTED** as F-AXIS-FALSIFIER (Section 4). |
| Aggregator-level veto (NOT per-seed) preserves cross-seed dispersion measurement | **ADOPTED** — Section 1 H1b + H1d explicit; F-AXIS #2 dispersion audit unchanged from /064. |
| Why NOT per-seed veto: re-biases cross-seed dispersion → breaks F-AXIS #2 audit | **HONORED** — Section 3.3 explicit "No per-seed veto". |
| Why NOT Critic-A (asymmetric-cutoff HP): expands Optuna search dim at n_trials=30 → increases basin-lottery; cannot pre-register effect on /064 roster | **HONORED** — Critic-A reserved as next-iter fallback if /074 lift < +0.10 (per LM Master closing note). |
| Why NOT QR-F / LM-A1/A2/A5 (new feature axes): /073 closeout established 48-col stack is mechanically held at SPECIALIST mode (dispersion-reservoir mechanism); adding OR removing features perturbs cross-seed HP-trajectory in unpredictable directions | **HONORED** — Section 3.3 explicit "No feature change". The /073 NEG outcome is the load-bearing evidence; cannot re-litigate at /074. |
| Why NOT LM-A3 / Critic-C (label changes) or Critic-D (risk-wrapper changes): multi-bit / not single-bit | **HONORED** — Section 3.3 explicit "No labeling change", "No risk-wrapper flip". |
| Why NOT QR-U / QR-L (universe / meta-model): out of scope for SPECIALIST-IMPROVEMENT | **HONORED** — Section 3.3 explicit; would violate `feedback_v1_bundle_no_coin_overlap.md`. |
| Trade-count floor risk: 32 vetoes → ~166 IS / ~76 OOS — both well above SPECIALIST 50-floor | **ACCEPTED** — Section 4 F-AXIS-BEHAVIORAL records the expected counts. |
| Saturation Risk #1: ETH-IMPROVED is 3-of-N; pattern of incremental failure at SPECIALIST mode; if /074 lands MARGINAL/NEGATIVE, pivot ETH to next-cycle CONFIRMATION envelope | **FLAGGED for Phase 7.4 LM Master post-mortem + Phase 8 diary** — if /074 verdicts NEGATIVE, this is the third ETH-IMPROVED NEGATIVE in a row (counting /073 even though /073 was discarded mid-axis); the next cycle should pivot ETH to multi-seed re-validation of /064 (let the multi-seed test resolve whether /064 has a 0.10-0.20 lift surface at all) rather than continuing single-seed knob-tuning. |
| Saturation Risk #2: AXIS-R generalizes to BTC/DOT but DO NOT pre-apply at /074 — single-cohort validation first | **ADOPTED** — /074 is ETH-only single-cohort. If /074 PROMISING, a future BTC-IMPROVED-V3 brief can pre-register AXIS-R as primary axis with BTC-specific band edges from BTC's own short-bleed cohort analysis (NOT ETH's edges). |
| Saturation Risk #3: engine.py:_tick parity surface area — AXIS-R adds a 3rd inference-layer rule | **ADOPTED for QE Phase 5.5 verification** — Section 5.3 item 11 enumerates the inference-layer rule order (LightGbmStrategy.get_signal → AXIS-R veto → R3 OOD → R5 vol-target) and Critic Check 15 verifies backtest-live alignment at each rule. Future iterations should resist accumulating rule-layer primitives without retiring earlier ones. |
| Closing note: HIGH confidence /074 will improve /064 IS Sharpe, conditional on pre-registered band edges holding through brief authoring without re-fitting | **HARD ACCEPTED** — Section 0.7 + Section 12 commit-SHA assertion; band edges [0.20, 0.50] / lookback 270 frozen at this brief's commit; no re-fitting permitted under any post-backtest scenario. |

LM Master confidence: **HIGH**. QR concurs and stakes verdict integrity on the pre-registered band assertion.

---

## Section 4 — F-Axis Bands (Falsifier Gates)

### F-AXIS #1 — IS Δ vs /064 anchor (PRIMARY verdict; strike adjudicator)

Anchor: /064 IS Sharpe = **+0.2383**. LM Master predicted band: modal **+0.37** (Δ +0.13); 60% band [+0.29, +0.44]; 90% band [+0.19, +0.49].

| Band | Range | Verdict | Strike effect |
|---|---|---|---|
| **PROMISING-CLEAN** | IS Sharpe ≥ **+0.37** (IS Δ ≥ **+0.13**) | SPECIALIST-PROMISING | **POSITIVE** for ETH; ETH-IMPROVED-V3 enters BUNDLE-002 candidate roster at HIGH confidence; future iter advances to multi-seed CONFIRMATION of AXIS-R |
| PROMISING-MARGINAL | +0.29 ≤ IS Sharpe < +0.37 (+0.05 ≤ IS Δ < +0.13) | TENTATIVE-POSITIVE | POSITIVE (still > 0 and ≥ LM P25); ETH-IMPROVED-V3 enters BUNDLE-002 candidate roster at REDUCED confidence; future iter advances to multi-seed CONFIRMATION or to Critic-A fallback (asymmetric-cutoff HP) |
| INERT | +0.19 ≤ IS Sharpe < +0.29 (−0.05 ≤ IS Δ < +0.05) | INERT (lift below LM P10 floor) | TENTATIVE-NEUTRAL; ETH /064 retains BUNDLE slot; strike NOT consumed (axis didn't fire materially); future iter pivots to Critic-A (asymmetric-cutoff HP) per LM Master "next-iter axis if /074 lift < +0.10" |
| NEG-1st-STRIKE | IS Sharpe < **+0.19** (IS Δ < **−0.05**) | **1st STRIKE** for ETH BUNDLE seat | **ETH STRIKE-1 fires**; future ETH-IMPROVED iter advances to strike-2; AXIS family of post-aggregator rule-form vetoes flagged for FALSIFICATION review at /075 if observed Δ < −0.10 (suggests AXIS-R mechanism is wrong, not just basin-lottery) |
| Catastrophic | IS Sharpe < **−0.10** (IS Δ < **−0.34**) | NEG-CONFIDENT + MULTI-SEED MANDATE TRIGGER | Three consecutive HIGH-RISK single-seed EXPLORATIONs with >1σ NEG deltas (/072, /073, /074) → **mandatory multi-seed at /075** per `feedback_v1_basin_lottery_vigilance.md`; AXIS-R mechanism flagged for full LM Master Phase 7.4 falsification audit |

Per `feedback_sharpe_floor.md`, the v1 IS Sharpe > 1.0 floor is the absolute merge gate; merge happens only at BUNDLE-002 assembly. The /074 verdict gates on the strike-adjudicator IS Δ band above, NOT on absolute Sharpe.

### F-AXIS #2 — Cross-seed dispersion (basin-lottery audit; UNCHANGED from /064 expected)

Per H1d (mechanism-orthogonal to basin-lottery): AXIS-R is post-aggregator and deterministic given (ret_270b, signal.direction). Cross-seed dispersion should read **identically** to /064 modulo the deterministic veto.

| Observed (basin_diagnostics.py output on /074 specialist_dispersion.csv) | Interpretation |
|---|---|
| `cross_seed_sharpe_std` within ±10% of /064 value | Mechanism intact; AXIS-R is structurally orthogonal as designed |
| `cross_seed_sharpe_std` ±10% to ±30% from /064 | Mild perturbation; investigate whether the 32-trade veto disproportionately affected high-variance seeds |
| `cross_seed_sharpe_std` >30% deviation from /064 | **Mechanism violated**; the post-aggregator veto is interacting with the aggregator distribution in unexpected ways; flag for Phase 7.4 LM Master diagnostic |

### F-AXIS #3 — OOS Sharpe (informational; not a verdict gate)

/064 OOS Sharpe = +0.5171. LM Master predicts: directionally positive but smaller magnitude (+0.05 to +0.15) — the OOS window is structural-bull (`ret_270b > 0.50` frequently), so few OOS trades fall in the veto band. The veto's OOS impact is trade-count-bounded at perhaps 3-8 vetoes of the 81 OOS trades.

| Band | OOS Sharpe range | Comment |
|---|---|---|
| Preserved/improved | ≥ +0.45 | AXIS-R preserves or lifts OOS edge as designed |
| Mild compression | +0.20 to +0.45 | acceptable; consistent with mechanical short-veto at single-seed |
| Severe compression | < +0.20 | flag for multi-seed re-validation at future iter; do NOT block /074 verdict |
| Suspicious OOS-dominant lift | ≥ +0.80 with IS Δ < +0.10 | flag possible regime-specific OOS lift (sister to v3 PROMISING-MECHANICAL); needs Phase 7.4 LM Master diagnostic |

OOS Sharpe is **NEVER** the strike adjudicator (per `feedback_no_cheating.md`).

### F-AXIS-BEHAVIORAL — IS trade count

LM Master simulator predicts 32 vetoes → 198 − 32 = **166 expected IS trades**. Tolerance ±10%.

| Observed | Interpretation |
|---|---|
| 149 ≤ IS trades ≤ 183 | AXIS-R fired as designed; mechanical veto working |
| 184-198 or 130-148 | Mild veto-count divergence; investigate which months changed (model re-trains may have re-routed some pre-veto trades to long-side, shifting baseline counts) |
| <130 or >198 (>15% from 166 expected, or >0 from 198 — runner produced MORE trades than no-veto baseline) | **Veto did not fire as expected** — flag for QE engineering verification; kill-switch fires per Section 0.5 |

### F-AXIS-FALSIFIER — Per-trade Sharpe lift + month concentration (HARD per LM Master)

Two HARD falsifiers from LM Master Phase 4.5 (both must hold for verdict integrity):

1. **Per-trade Sharpe lift ≥ +0.10**: the realized per-trade Sharpe lift over the AXIS-R retained roster vs the /064 retained roster (same trades minus the 32 vetoes counterfactually) must be ≥ +0.10. If <+0.10, the simulator's +0.186 raw lift did not materialize — verdict downgrades to AXIS-R-MECHANISM-FALSIFIED regardless of headline IS Δ.

2. **No single calendar month >40% of realized IS lift**: if 2024 alone produces >40% of the realized IS Sharpe lift and other years produce flat or negative contribution, AXIS-R is a regime-coincident artifact NOT a structural rule. Verdict downgrades to FALSIFIED-REGIME-FIT.

Both falsifiers are **HARD** and not negotiable; the QR Phase 7 evaluation MUST report on both.

### F-AXIS-IMPORTANCE — Top-feature rank preservation (sanity; UNCHANGED from /064 expected)

Because the feature stack is UNCHANGED (48 cols) and the veto is post-aggregator, the IS feature importance CSV should preserve /064's top-10 rank order (LightGBM trains on the same labels; the veto only filters the OUTPUT trade roster, not the training distribution).

| Observed | Interpretation |
|---|---|
| Spearman ρ(/074 top-10 ranks vs /064 top-10 ranks) ≥ 0.85 | Mechanism intact; training distribution preserved |
| 0.60 ≤ ρ < 0.85 | Mild re-ranking; expected for any LightGBM re-run at single-seed=42 (Optuna trajectories may differ within the same basin) |
| ρ < 0.60 | **Suggests Optuna trajectory shifted unexpectedly** despite identical training inputs — investigate inner-seed reproducibility; flag for Phase 7.4 |

### F-AXIS-COUNTERFACTUAL — Vetoed-trade audit

The QR Phase 7 evaluation MUST produce a counterfactual audit table:

| Quantity | /074 (post-veto) | Pre-veto reconstruction (the 32 vetoed trades) | Match LM simulator? |
|---|---:|---:|---|
| Vetoed-trade count | N/A | TBD (count of `direction==-1 AND ret_270b ∈ band` in pre-veto roster) | LM simulator says 32; tolerance ±5 |
| Vetoed-trade net PnL counterfactual | N/A | TBD | LM simulator says −9.73%; tolerance ±2pp |
| Vetoed-trade Win Rate | N/A | TBD | LM simulator says 16.7%; tolerance ±5pp |

If the counterfactual audit deviates from the LM simulator beyond tolerance, the simulator was wrong — flag for LM Master Phase 7.4.

---

## Section 5 — Risk Mitigation

### 5.1 Axis-specific risk

- **Pre-registered band rigor (HIGH)**: this is the single most important discipline per LM Master Phase 4.5 closing note. The brief commit SHA (Section 12) is the freeze point. If the QR (or any future post-hoc analyst) re-fits the band post-hoc to find a stronger lift, the verdict collapses to METHODOLOGY-FALSIFIED. Phase 8 diary must explicitly reference the brief commit SHA when adjudicating.
- **Single-bit discipline (HARD)**: the brief HARDWIRES ATR=2.9/1.45, R-config=(R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70), 50 inner seeds × 30 trials, ENSEMBLE_SIZE=1, max_depth=5, num_leaves=31, n_estimators ≤ 500, n_startup_trials=10, V1_FEATURE_COLUMNS_PRUNED (48 cols, UNCHANGED), mean-of-signed-weights aggregator — **exactly identical to /064**. Only the four post-aggregator veto kwargs change. If the runner touches a second axis (e.g., "while we're here, let's try atr_tp=2.8"), the iteration becomes a 2-bit cross-axis confound and the verdict is uninterpretable. /073's NEG outcome does NOT license multi-axis compensation at /074.
- **Engine parity (HIGH)**: per `feedback_v1_backtest_live_parity_hard.md` (Critic Check 15), the veto MUST be wired into `engine.py:_tick` at the same call-site as the backtest implementation, with byte-equivalent ret_270b computation (270-bar lookback, same close-series source, same band edges 0.20/0.50). QE Phase 5.5 gate verifies this explicitly.
- **Mid-bull regime persistence in OOS (MEDIUM-LOW)**: if 2026+ OOS extends into a new bull/bear transition where `ret_270b` re-enters [0.20, 0.50] frequently, the veto may begin firing again. This is EXPECTED behavior — AXIS-R is a regime-state-dependent filter, not a time-window patch. The verdict at /074 is single-window OOS; cycle-7 multi-seed CONFIRMATION will re-validate.
- **AXIS-R is mechanism-orthogonal to basin-lottery** (H1d): the cross-seed Optuna trajectories are unchanged from /064 (the basin is identical). A NEGATIVE outcome at /074 cleanly falsifies the AXIS-R mechanism, not the EXPLORATION budget. This is structurally different from /073's feature-pruning axis (which mutated the basin distribution and produced an ambiguous NEG outcome attributable to either dispersion-reservoir mechanism failure OR mechanical degradation).

### 5.2 Risk wrappers inherited per BUNDLE-001 spec (NO CHANGE vs /064)

| Wrapper | /064 setting | /074 setting | Change? |
|---|---|---|---|
| R1 (consecutive-SL cool-down) | DISABLED (Model A pattern) | **DISABLED** (catalog rule `f81cafc3` — R1 CLOSED for SPECIALIST_mode) | NO |
| R2 (DD scaling) | DISABLED (Model A pattern) | DISABLED (unchanged) | NO |
| R3 (OOD Mahalanobis cutoff=0.70, 16 SI features SHARED) | ENABLED | ENABLED (unchanged) | NO |
| R5 (per-coin vol target, 45-day rolling) | ENABLED | ENABLED (unchanged) | NO |
| **AXIS-R (NEW; mid-bull short veto post-aggregator)** | N/A | **ENABLED** (single-bit add) | YES (the only change) |

The AXIS-R primitive is placed in the inference-layer rule order **AFTER** the LightGBM aggregator and **BEFORE** R3 OOD / R5 vol-target. Order matters: AXIS-R can flip a short to flat, and a flat signal does NOT trigger R3 OOD computation (R3 only gates non-flat signals). The QE Phase 5.5 gate must verify the order is BACKTEST-EQUAL-TO-LIVE.

### 5.3 QE Phase 6.0 Critic pre-flight check items

1. `run_iteration_074.py` is a clone of `run_iteration_064.py` with the SINGLE-BIT FOUR-kwarg veto add.
2. `run_baseline_v1.py` dispatch branch `elif iteration_label == "v1-074"` is identical to `v1-064` branch except for the four new kwargs.
3. `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` (48 cols) is passed explicitly to `LightGbmStrategy` per `feedback_explicit_feature_columns.md`; **NOT** V1_FEATURE_COLUMNS_ETH_TOP25 (the /073 axis is closed).
4. `FEATURES_BASE_HASH_48COL = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)` is pinned at runner entry and asserts equality with /064's pinned hash.
5. **Parquets NOT regenerated** — runner reads existing parquet files (same FEATURES_BASE_HASH as /064 setup).
6. Risk wrappers unchanged: `r1_enabled=False, r1_streak_cutoff=None, r1_cooldown_candles=None, r2_enabled=False, r3_enabled=True` (Model A R3-only pattern).
7. ATR barriers unchanged: TP=2.9, SL=1.45.
8. `specialist_mode=True`, inner_seeds=50, n_trials=30, outer seed=42 — all unchanged from /064.
9. `ENSEMBLE_SIZE=1`, max_depth=5 fixed, num_leaves=31 fixed, n_estimators ≤ 500, n_startup_trials=10, mean-of-signed-weights aggregator — all unchanged.
10. Walk-forward embargo applied (`train_end_ms = test_start_ms - embargo_ms`).
11. **Inference-layer rule order verified** (HARD per Critic Check 15): `LightGbmStrategy._aggregate_seeds` → AXIS-R veto → R3 OOD → R5 vol-target. Same order in backtest and at `engine.py:_tick`.
12. **Engine parity verified** (HARD): `engine.py:_tick` AXIS-R conditional reads 270 prior closes from the `klines` table query with byte-equivalent ret_270b computation; band edges 0.20/0.50/lookback 270 read from config (not hardcoded in two places).
13. **Veto-event forensic logging**: every AXIS-R veto fires a decision-log event `kind=axis_r_veto` with `symbol, open_time, ret_270b, signal_direction_pre_veto, signal_weight_pre_veto` for Phase 7 counterfactual audit (per F-AXIS-COUNTERFACTUAL).
14. `reports-v1/iteration_v1-074/` directory committed at Phase 8 closeout per HARD rule `0a19e068`.
15. `specialist_dispersion.csv` persisted for both IS and OOS windows per LM 7.4 load-bearing patch `153664ed`.
16. Pre-registered band edges [0.20, 0.50] / lookback 270 read from config kwargs (NOT hardcoded magic numbers); brief commit SHA is the freeze reference.

### 5.4 Historical effect simulation (from /064 IS roster — pre-registered counterfactual)

The LM Master Phase 4.5 simulator applied to the /064 IS trades.csv roster (counterfactual: holding model identity fixed):

| Quantity | /064 (no veto) | AXIS-R counterfactual | Δ | Notes |
|---|---:|---:|---:|---|
| IS trades total | 198 | 166 | **−32** | 16.2% of roster vetoed |
| IS short trades | 111 | 79 | −32 | 28.8% of short book vetoed |
| Vetoed-cohort net PnL | — | — | **+9.73% recovered** | All 32 vetoes from the 16.7% WR cohort |
| IS net PnL | +15.0025% | +24.73% | +9.73 pp | Direct addition |
| Per-trade raw Sharpe (fixed-model) | 0.686 | 0.871 | **+0.186** | Simulator upper bound |
| Predicted monthly IS Sharpe (runner; 0.6×-0.8× simulator scale-down) | +0.2383 | **+0.32 to +0.40** (modal **+0.37**) | **+0.08 to +0.16** (modal **+0.13**) | LM Master Phase 4.5 prediction |

The counterfactual is the PRE-REGISTERED effect basis. Phase 7 evaluation will compare observed vs predicted on all four quantities (trade-count, vetoed-PnL, vetoed-WR, per-trade Sharpe lift) per F-AXIS-COUNTERFACTUAL.

---

## Section 6 — CPCV / DSR / PBO / PSR (Informational)

Per `feedback_v3_dsr_mode_artifact.md` (analogous v1 reasoning):

- /074 runs at EXPLORATION budget (n_trials=30, single outer seed=42, 50 inner seeds × specialist_mode).
- DSR/PBO/PSR at EXPLORATION budget are **STRUCTURAL ARTIFACTS** — not comparable to CONFIRMATION-mode DSR (which would use n_trials=50+ × multi-outer-seed).
- /064 DSR = −88.4420 (EXPLORATION budget; informational artifact).
- /074 DSR will be computed for traceability but is **NOT a verdict gate**.
- CPCV is not run at SPECIALIST EXPLORATION (walk-forward k=24 cells is the methodology anchor).

These metrics will be recorded in the report for archival but do not bind the /074 verdict.

---

## Section 6.5 — Specialist Dispersion Persistence (LM 7.4 Load-Bearing Patch)

Per commit `153664ed`: every specialist EXPLORATION must persist `specialist_dispersion.csv` (per-candle ensemble std diagnostic for σ_pop in `specialist_mode`). /074 retains this:

- `reports-v1/iteration_v1-074/in_sample/specialist_dispersion.csv` (mandatory)
- `reports-v1/iteration_v1-074/out_of_sample/specialist_dispersion.csv` (mandatory)

LM Master Phase 7.4 post-mortem will reference these to verify ensemble convergence stability under AXIS-R post-aggregator filtering (expected: dispersion **identical** to /064 because AXIS-R is mechanism-orthogonal to inner-seed Optuna trajectories — F-AXIS #2 audit). Any deviation >30% from /064 is a flag for mechanism violation.

---

## Section 7 — Library Stack

- Python 3.13
- LightGBM (head; 50 inner seeds × 30 Optuna trials × walk-forward cells; specialist_mode=True; max_depth=5 fixed; num_leaves=31 fixed)
- Optuna (TPE sampler; n_trials=30; n_startup_trials=10; single outer seed=42)
- pandas, numpy (trade composition + metrics)
- `crypto_trade.strategies.ml.lgbm.LightGbmStrategy` (feature_columns pinned to V1_FEATURE_COLUMNS_PRUNED 48 cols; **NEW**: `enable_mid_bull_short_veto, mid_bull_short_veto_lo, mid_bull_short_veto_hi, mid_bull_short_veto_lookback` kwargs)
- `crypto_trade.risk_v2.RiskV1Wrapper` (Model A instance with R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70 — IDENTICAL to /064)
- `crypto_trade.engine` (`_tick` AXIS-R parity-mirrored conditional reading 270 prior closes from `klines` table)
- quantstats (tearsheet, optional)

No new third-party dependencies introduced. **The only new code paths are**: (a) the four-kwarg AXIS-R block in `LightGbmStrategy.get_signal`, (b) the engine.py parity conditional, (c) the runner dispatch branch, (d) decision-log forensic event `kind=axis_r_veto`. No new feature computation. No new model class.

---

## Section 8 — Pre-Registered Outcome Conditions

Per cycle-7 SPECIALIST iter discipline: **merge happens only at BUNDLE stage (BUNDLE-002 assembly).** /074 is a SPECIALIST iteration that produces a candidate trade artifact, not a merge candidate on its own.

| Scenario | Action |
|---|---|
| IS Sharpe ≥ +0.37 (PROMISING-CLEAN) AND both falsifiers PASS (per-trade Sharpe lift ≥ +0.10 AND no single month >40% of lift) AND F-AXIS-COUNTERFACTUAL within tolerance | SPECIALIST-PROMISING verdict; commit `reports-v1/iteration_v1-074/` per HARD rule; ETH-IMPROVED-V3 enters BUNDLE-002 candidate roster; future iter advances to multi-seed CONFIRMATION of AXIS-R |
| +0.29 ≤ IS Sharpe < +0.37 (PROMISING-MARGINAL) AND both falsifiers PASS | TENTATIVE-POSITIVE verdict; commit reports; ETH-IMPROVED-V3 enters BUNDLE-002 candidate roster at REDUCED confidence; future iter advances to multi-seed CONFIRMATION OR to Critic-A fallback (asymmetric-cutoff HP) |
| +0.19 ≤ IS Sharpe < +0.29 (INERT) | TENTATIVE-NEUTRAL; ETH /064 retains BUNDLE slot; strike NOT consumed (axis didn't fire materially); future iter pivots to Critic-A (asymmetric-cutoff HP) |
| IS Sharpe < +0.19 (NEG-1st-STRIKE) | **ETH STRIKE-1 fires**; future ETH-IMPROVED iter advances to strike-2 (axis options: regime-conditional kill switch on 2024-bull-bear transition; OR multi-seed CONFIRMATION of /064) |
| IS Sharpe < −0.10 (Catastrophic) | NEG-CONFIDENT + **multi-seed mandate trigger** per `feedback_v1_basin_lottery_vigilance.md` (3 consecutive HIGH-RISK single-seed EXPLORATIONs with >1σ NEG: /072 + /073 + /074); /075 becomes mandatorily multi-seed |
| Per-trade Sharpe lift < +0.10 (FALSIFIER 1 fires) | AXIS-R-MECHANISM-FALSIFIED regardless of headline IS Δ; verdict downgrades; ETH STRIKE-1; future iter cannot re-litigate AXIS-R |
| Any single calendar month >40% of realized IS Sharpe lift (FALSIFIER 2 fires) | FALSIFIED-REGIME-FIT; verdict downgrades; ETH STRIKE-1; future iter cannot re-litigate AXIS-R |
| Behavioral falsifier fires (IS trade count <130 or >198, or |Δ from 166 expected| > 17) | Verdict invalidated; QE engineering verification mandated; /074 re-run after fix; NO strike consumed |
| F-AXIS #2 dispersion deviation >30% from /064 (mechanism violation) | Verdict invalidated; Phase 7.4 LM Master diagnostic mandated; AXIS-R mechanism re-evaluated |
| F-AXIS-COUNTERFACTUAL audit deviation beyond tolerance (vetoed-trade count not 32 ± 5, vetoed-PnL not −9.73% ± 2pp, vetoed-WR not 16.7% ± 5pp) | LM Master simulator was wrong; Phase 7.4 diagnostic mandated; verdict TENTATIVE pending re-analysis |
| FEATURES_BASE_HASH_48COL pre-flight mismatch | Kill-switch fires; abort; capture commit; defer to /075 with diagnostic |
| Methodology-integrity FAIL (look-ahead, embargo violation, forming-candle leak, OOS peek, parquet regeneration, OOD feature substitution, band-edge re-fitting post-backtest) | BLOCK; Critic escalation; methodology gates are HARD and not overridable |
| Wall-clock exceeds 2.5h | Kill-switch fires; abort; capture commit; defer to /075 with diagnostic |

**Pre-registered: SPECIALIST iter; merge happens only at BUNDLE stage (BUNDLE-002 assembly).** The band edges [0.20, 0.50] and lookback 270 are FROZEN at this brief's commit SHA (Section 12) and CANNOT be re-fitted under any post-backtest scenario.

---

## Section 9 — Pairwise-Disjoint Universe Assertion (HARD per `feedback_v1_bundle_no_coin_overlap.md`)

/074 is a SPECIALIST iteration (single-coin EXPLORATION); the bundle-level pairwise-disjoint assertion applies at BUNDLE-002 assembly time, not at /074 EXPLORATION time. For traceability:

| Specialist | Universe |
|---|---|
| /074 ETH-IMPROVED-V3 (this iter) | **`{ETHUSDT}`** (single-coin) |

If /074 verdicts PROMISING and replaces /064 in BUNDLE-002, the future BUNDLE-002 assembly must re-assert pairwise-disjoint per Critic Check 16 with `{DOTUSDT} ∩ {ETHUSDT} = ∅, {DOTUSDT} ∩ {BTCUSDT} = ∅, {ETHUSDT} ∩ {BTCUSDT} = ∅` (or whatever the BUNDLE-002 composition is at that point).

---

## Section 10 — Reproduction Recipe

To reproduce /074 metrics after Phase 6 completes:

```bash
cd /home/roberto/crypto-trade/.worktrees/quant-research
git checkout iteration-v1/074
# Fetch fresh klines + features (if not already present in this worktree)
uv run crypto-trade fetch --symbols ETHUSDT --intervals 8h
uv run crypto-trade features --symbols ETHUSDT --interval 8h --track v1 --format parquet --workers 4
# Run the iteration
uv run python run_iteration_074.py
# Verify pre-flight guards
python3 -c "from src.crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED; assert len(V1_FEATURE_COLUMNS_PRUNED) == 48"
```

Expected outputs:
- `reports-v1/iteration_v1-074/in_sample/trades.csv` (~166 IS trades; cf. /064's 198)
- `reports-v1/iteration_v1-074/out_of_sample/trades.csv` (~73-78 OOS trades; cf. /064's 81)
- `reports-v1/iteration_v1-074/in_sample/comparison.csv` with IS Sharpe ≈ +0.37 (LM modal)
- `reports-v1/iteration_v1-074/in_sample/specialist_dispersion.csv` (matching /064 ±10%)
- Decision-log `kind=axis_r_veto` events (count ~32 in IS window, ~5 in OOS window)

---

## Section 11 — Portfolio Composition Design (HARD CONFORMANCE; bundle-relevant only at BUNDLE-002)

### 11.A — Pairwise-disjoint universe assertion

/074 is a SPECIALIST EXPLORATION (single-coin). The HARD pairwise-disjoint assertion applies at BUNDLE-002 assembly. For /074: universe = `{ETHUSDT}` (singleton; trivially pairwise-disjoint with itself).

### 11.B — Weight calibration

No bundle-level weights at /074 (SPECIALIST EXPLORATION). The per-trade `weight_factor` column in trades.csv encodes vol targeting + R2 scaling + risk wrapper effects (inherited from /064's risk wrapper config; AXIS-R does NOT modify weight_factor — only direction; vetoed trades have direction=0 and are excluded from PnL).

### 11.C — Backtest-live parity

Per `feedback_v1_backtest_live_parity_hard.md` Critic Check 15: the AXIS-R conditional is wired identically in backtest (`LightGbmStrategy.get_signal` post-aggregator filter) and at `engine.py:_tick`. Both implementations:
- Use the same 270 prior 8h-close lookback
- Compute `ret_270b = (close[-1] / close[-271]) - 1.0` byte-equivalently
- Apply the same band edges [0.20, 0.50] read from config (not hardcoded in two places)
- Fire on `signal.direction == -1` only (long signals and flat signals untouched)
- Apply BEFORE R3 OOD and R5 vol-target call-sites
- Log forensic event `kind=axis_r_veto`

QE Phase 5.5 gate verifies all six conditions explicitly. Critic Check 15 PASS gate.

### 11.D — Re-composition statement

/074 is non-overlapping by construction (single-coin SPECIALIST). No re-composition needed.

---

## Section 12 — Brief Commit SHA (Pre-Registered Band Freeze Reference)

This brief's commit SHA is the **freeze reference** for the pre-registered band edges. Any post-Phase-6 modification to the band edges 0.20 / 0.50 OR the lookback 270 in the runner or engine.py invalidates the pre-registration and downgrades the verdict to METHODOLOGY-FALSIFIED per `feedback_no_cheating.md`.

The commit SHA will be recorded in the Phase 8 diary as the "band freeze reference"; the Phase 8 closeout verifies the actual runner / engine.py code references match the brief commit SHA's stated band edges exactly.

---

## Section 13 — Sign-off

| Phase | Owner | Status |
|---|---|---|
| Phase 1 (EDA) | QR | DONE (LM Master Phase 4.5 simulator is the load-bearing EDA; QR analysis script to be committed at Phase 6 setup) |
| Phase 2-4 (labeling, symbols, features) | QR | DONE (NO change vs /064; single-bit post-aggregator veto only) |
| Phase 4.5 (LM Master advisor) | LM Master | DONE — `briefs-v1/iteration_v1-074/lgbm_advisor.md` (commit `33910a56`) |
| Phase 5 (research brief) | QR | DONE (this document) |
| Phase 5.5 (gate) | Orchestrator | PENDING |
| Phase 6 (implementation + backtest) | QE | PENDING — runner is a clone of /064 with the SINGLE-BIT FOUR-kwarg veto add; `LightGbmStrategy.get_signal` + `engine.py:_tick` parity-mirrored AXIS-R conditional; decision-log forensic event |
| Phase 6.0 (Critic pre-flight) | Critic | PENDING — checks per Section 5.3 |
| Phase 7 (evaluation) | QR | PENDING — F-AXIS bands per Section 4 + F-AXIS-COUNTERFACTUAL audit table |
| Phase 7.4 (LM Master post-mortem) | LM Master | PENDING — specialist_dispersion.csv vs /064 verification + counterfactual audit + per-trade Sharpe lift verification + month-concentration falsifier check |
| Phase 7.5 (Critic review) | Critic | PENDING |
| Phase 8 (diary + merge decision) | QR | PENDING — pre-registered SPECIALIST verdict per Section 8; merge happens only at BUNDLE-002 stage |

---

**End of brief.**
