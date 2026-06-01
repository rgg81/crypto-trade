# Iteration v1-046 — Research Brief

## Section 0.0 — Banner

**TYPE:** `EXPLORATION`
**Cycle slot:** cycle-6 EXPLORATION 1/10 (first EXPLORATION post-/045 BLOCK-FINAL; cycle-5 closed at /045 closeout).
**Axis family:** `methodology` (substrate re-composition methodology fix — IS-only partition-solve).
**Anchor:** `BASELINE_V1` corrected walk-forward (IS daily Sharpe +0.4761 / OOS daily Sharpe +1.1415; OOS_CUTOFF_DATE = 2025-03-24; IS PnL +54.05 / OOS PnL +36.96). Comparison reference: `/045 ALT_1` substrate `(C-BTC=v1-012, C-ETH=v1-042, C-LINK=v1-011, C-LTC=v1-040, C-DOT=v1-031)` at EQUAL 1/5 weights with verifier-computed bundle IS +1.9879 / OOS +3.4851.
**Branch:** `iteration-v1/046`. **Tag (post-Phase-8):** `v0.v1-046`.
**Methodology stance:** /045 BLOCK-FINAL on substrate-selection prudence (workflow `w0qpo136q` READ each candidate component's OOS Sharpe during partition optimization; per Critic, that constitutes post-hoc OOS-aware specialist selection; bundle headline +3.49 OOS is structurally inflated 30-50% by selection bias). /046 fixes the methodology by re-running the partition-solve with an **IS-only** scoring expression `score_is = 0.6·IS_Sharpe + 0.4·IS_n_trades_norm` (NO OOS data on either side of the score) and tests whether the substrate emerges identical to ALT_1 (substrate honest within the OOS-aware framework) or diverges (OOS-inflation empirically demonstrated).

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — unchanged (sacred).
- `training_months = 24` — unchanged (sacred).
- IS window: `[earliest available data, 2025-03-24)`.
- OOS window: `[2025-03-24, latest available data]`.
- Walk-forward: `train_end_ms = test_start_ms - embargo_ms` at `walk_forward.py:113` (verified by Phase 6.0 mini-Foundation check; lookahead-bug fix `e149e9d` in scope).
- **/046 SCORE INPUTS:** IS-window-only trade rosters (`reports-v1/iteration_v1-{iter}/in_sample/trades.csv` exclusively). OOS rosters are NOT loaded by `partition_solve_v2.py`; CSV-replay aggregator does load both windows for the **forensic** bundle headline emission (Section 9) but the score function itself NEVER touches OOS data.

---

## Section 0.5 — Iteration Type Declaration + Cadence

**TYPE:** `EXPLORATION`
**Wall-clock target:** <30 min total (CSV-replay class; same as /045). NO Optuna call, NO LightGBM fit, NO new training, NO src/ changes.
**Wall-clock estimate (Section 3.6):** <30 min — read up to ~120 (iter, coin) cells from inventory IS CSVs, compute per-cell IS Sharpe + IS n_trades + score_is, per-coin rank top-3, emit partition_solve_v2.csv, re-aggregate substrate via /045 CSV-replay aggregator, emit comparison.csv + comparison_vs_alt1.csv + source_checksums.csv + Spearman rank corr, run F5 grep + hide-test integration smoke.

**Cycle-6 cadence:** /046 = cycle-6 EXPLORATION 1/10. Cycle-5 closed at /045 BLOCK-FINAL closeout (cycle-5 had 10 EXPLORATIONs /034-/043 + 2 CONFIRMATIONs /044 + /045, zero BASELINE_V1.md updates). Per `briefs-v1/exploration_catalog.md` schema, /046 is the opening row of cycle-6's ledger.

**EXPLORATION precedents (cycle-5; cited in cadence ledger):** /034 NEG-CLEAN basis_zscore; /035 NEG-CAT bimodal; /036 PROMISING-CLEAN; /037 PROMISING-CLEAN-MECHANISM-DIVERGENT; /038 NEG-CAT EDA-VINDICATED; /039 NEG-CAT vs /036; /040 NEG-CLEAN-OVERFIT (reframe REGIME-SPECIALIST-IS); /041 NEG-CLEAN + TAIL-CONTROL; /042 REGIME-SPECIALIST-IS-CONDITIONAL; /043 REGIME-SPECIALIST-OOS.

Cadence requirement (10:1 ratio EXPLORATION:CONFIRMATION) **N/A at /046 EXPLORATION boundary**; /046 ADDS to cycle-6's ledger.

---

## Section 0.6 — Architecture-Family Justification (v1-only)

**Axis family:** `methodology` (substrate re-composition / partition-solve scoring fix).

**Prior 5 EXPLORATION families (from `briefs-v1/exploration_catalog.md`):**

| Iter | Date | Axis family |
|---|---|---|
| iter-v1/039 | 2026-05-31 | per-cohort × labeling COMBO (Sortino × LINK+DOT trend-scan hybrid) |
| iter-v1/040 | 2026-05-31 | feature-family (composed `regime_momentum_signed_5d` swap for `basis_zscore_30`) |
| iter-v1/041 | 2026-05-31 | labeling (atr_tp/sl width tighten 2.9→1.5 / 1.45→0.75) |
| iter-v1/042 | 2026-05-31 | model-arch (XGBoost head-to-head vs LightGBM) |
| iter-v1/043 | 2026-05-31 | per-cohort-specialization × labeling COMBO (LINK-only trend-scan) |

**Rotation status:** `VALID` — `methodology` is NOT in the prior 5. Prior 5 span 5 distinct families: per-cohort×labeling, feature-family, labeling, model-arch, per-cohort-specialization×labeling. `methodology` is a NEW family for this rotation window. **Axis Rotation Discipline SATISFIED.**

**One-sentence rationale:** /045 BLOCK-FINAL identified post-hoc OOS-aware selection as a structural defect in workflow `w0qpo136q`'s composite score `(0.5·OOS_Sh + 0.3·IS_Sh + 0.2·OOS_n_trades/100)`; the prior 5 EXPLORATIONs exhausted content axes (feature, label, model, cohort) under that contaminated selection framework; the right next axis is **methodology** — fix the selection by re-running the partition-solve with an IS-only scoring expression and test whether the substrate emerges identical (ALT_1 honest within its framework) or different (OOS-inflation confirmed). Methodology is structurally orthogonal to the content axes and answers a higher-order question that those axes cannot.

**What this is NOT:**
- NOT "re-run /045 ALT_1 components with multi-seed" — that is Critic Path Forward #1 in its original framing; multi-seed re-validation answers "is the headline replicable" but does NOT answer "was the substrate honestly selected." /046 answers the latter; multi-seed re-validation can follow at /047 conditional on /046's verdict.
- NOT "try another content axis" — the BLOCK at /045 was NOT a content defect (Checks 15/16/17 PASS by construction); cycling away from the methodology defect would leave the bundle pipeline contaminated for every future CONFIRMATION.

---

## Section 1 — Hypothesis

A symbol-partitioned 5-component substrate selected by an **IS-only** partition-solve `(score_is = 0.6·IS_Sharpe + 0.4·IS_n_trades_norm; IS-window cutoff `close_time < OOS_CUTOFF_MS = 1742774400000` enforced at load; OOS data not loaded by the score function)` either:

- **COINCIDES** with /045 ALT_1 (component-set equality across all 5 coins) — in which case ALT_1's OOS-aware selection was incidentally honest within its framework, and the headline +3.49 OOS Sharpe is supported by IS-side evidence alone; or
- **DIVERGES** in ≥3 of 5 coins — in which case OOS-inflation is empirically demonstrated and ALT_1's headline OOS Sharpe is, with high probability, a post-hoc selection artifact whose honest discount is 30-50% (per Critic /045 BLOCK-FINAL reasoning).

The /046 verdict (PROMISING-COINCIDENCE / PROMISING-DIVERGENCE / PROMISING-PARTIAL / NULL-METHODOLOGY-FIX / BLOCK-PENDING-FIX) routes /047 to the correct multi-seed re-validation target: ALT_1 if COINCIDENCE, the IS-only substrate if DIVERGENCE, both if PARTIAL.

---

## Section 2 — IS-Only Numerical Evidence

This section re-emits the 220-candidate IS-Sharpe distribution computed by `analysis/iteration_v1-045/partition_solve.py` (which is itself an IS-only solver; the OOS-leakage in /045 lived in workflow `w0qpo136q`'s SHIP-target composite score, not in the IS-substrate enumeration). At /046 Phase 6, `analysis/iteration_v1-046/partition_solve_v2.py` recomputes the IS-side from raw `reports-v1/iteration_v1-{iter}/in_sample/trades.csv` data with the explicit IS-window cutoff assertion and emits per-coin top-3 candidates by `score_is = 0.6·IS_Sharpe + 0.4·IS_n_trades_norm`.

### 2.1 Inventory survey (pre-EDA estimate)

Iterations available in `reports-v1/iteration_v1-{002..043}` excluding /001, /026, /027, /029 (absent) → 38 iterations. Each iteration's universe varies (some are BASELINE_V1 pool-A only, others are single-coin specialists, some are 2-3 coin combos). Per-coin cell coverage estimated:

| Coin | Iterations likely covering | Estimated cells with ≥1 IS trade |
|---|---|---|
| BTC | Pool-A baseline + multi-cohort variants | ~25-30 |
| ETH | Pool-A baseline + multi-cohort variants | ~25-30 |
| LINK | LINK-only + multi-cohort | ~20-25 |
| LTC | LTC-only + multi-cohort | ~20-25 |
| DOT | DOT-only + multi-cohort | ~15-20 |
| **TOTAL** | | **~100-130 cells** |

Total candidate (iter, coin) cells: ~100-130 (less than nominal 38×5=190 because not every iteration covers every coin). The 220-candidate figure cited in the brief instruction refers to the FULL inventory cell space (190 nominal + alternate weight schemes considered in /045 workflow); /046's `partition_solve_v2.py` operates on the realised ~100-130 cells with non-zero IS trade counts.

### 2.2 /045 ALT_1 — per-component IS evidence (anchor; from `analysis/iteration_v1-045/component_is_evidence.csv`)

| Component | Source iter | Universe | IS Sharpe | IS n_trades | IS_n_trades_norm (n/250) | score_is_alt1_components = 0.6·IS_Sh + 0.4·norm |
|---|---|---|---:|---:|---:|---:|
| C-BTC | v1-012 | {BTC} | **−0.21** | 65 | 0.65 | 0.140 |
| C-ETH | v1-042 | {ETH} | +0.71 | 132 | 1.32 | 0.954 |
| C-LINK | v1-011 | {LINK} | +1.27 | (per /011 brief) | (per /011 brief) | (computed at Phase 6) |
| C-LTC | v1-040 | {LTC} | +3.76 | 117 | 1.17 | 2.724 |
| C-DOT | v1-031 | {DOT} | +2.40 | 117 | 1.17 | 1.908 |

**Load-bearing observation:** C-BTC v1-012 has IS Sharpe **−0.21** — IS-NEGATIVE. Under the IS-only score formula, v1-012 will only top BTC's per-coin ranking if every other iteration covering BTC has an even worse score_is. Per inventory survey (§2.1), at least 5-10 iterations cover BTC (Pool-A baseline + multi-cohort variants like /022, /023, /038, /040). At least one of those almost certainly has score_is(BTC) > 0.140 (e.g., v1-023 had OOS 58 trades and the workflow `w0qpo136q` row recorded its IS Sharpe higher than v1-012's). **Therefore: IS-only solve almost certainly does NOT pick v1-012 for BTC. F2 (5/5 coincidence) is very unlikely; F3 (≥3 divergence) is the dominant prior.**

### 2.3 Per-coin top-3 IS-Sharpe-ranked candidates (pre-EDA estimate)

These pre-EDA estimates are placeholders; `partition_solve_v2.py` emits exact ranks in Phase 6. Estimate priors:

| Coin | Likely top-1 (by score_is) | Likely top-2 | Likely top-3 | /045 ALT_1 pick | Likely divergence? |
|---|---|---|---|---|---|
| BTC | v1-022 / v1-023 / v1-038 (pool-A variants with positive IS) | one of the above | one of the above | v1-012 (IS −0.21) | **HIGH-PROBABILITY DIVERGENCE** (v1-012 IS-negative cannot top a pool of positive-IS candidates unless all alternatives are also IS-negative — implausible) |
| ETH | v1-022 / v1-040 / v1-042 (pool-A or multi-cohort ETH-leg) | one of the above | one of the above | v1-042 (IS +0.71) | MEDIUM (v1-042's +0.71 is positive but not exceptional — could be edged out by a higher-IS-Sharpe pool-A variant) |
| LINK | v1-036 / v1-043 / v1-011 (single-coin and multi-cohort LINK) | one of the above | one of the above | v1-011 (IS +1.27) | MEDIUM (v1-011's +1.27 is strong but v1-036 had OOS Δ +1.08 LINK+DOT lift; v1-011 may or may not top score_is) |
| LTC | v1-040 (IS +3.76, strong dominant) / v1-013 / v1-016 | v1-013 / v1-016 | v1-013 / v1-016 | v1-040 (IS +3.76) | LOW (v1-040's IS +3.76 is exceptional — almost certainly tops score_is at +2.724) |
| DOT | v1-031 (IS +2.40) / v1-037 / v1-019 | v1-037 / v1-019 | v1-037 / v1-019 | v1-031 (IS +2.40) | LOW-MEDIUM (v1-031's IS +2.40 is strong; only edged out if a higher-IS-Sharpe DOT-covering iteration exists in inventory) |

**Expected /046 verdict modal (refined in Section 7):** **PROMISING-DIVERGENCE** (45% modal prior) driven by near-certain BTC divergence + medium-probability ETH/LINK divergence.

### 2.4 Verifier-source IS-window assertion

`partition_solve_v2.py` enforces at every CSV load:

```python
df = pd.read_csv(path)
assert (df["close_time"] < OOS_CUTOFF_MS).all(), \
    f"OOS rows leaked into {path}; close_time max = {df['close_time'].max()}"
```

This is the same assertion `analysis/iteration_v1-045/component_is_evidence.py` uses, verified clean at /045 Phase 7.5 (Critic Check 17 PASS).

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

**Declaration:** **NORMAL-RISK**

**Reason:** /046 does NOT change Optuna's training-objective domain. No risk-primitive constraint change, no universe substitution, no label-mode change, no feature-set replacement, no bar-interval change. The axis is methodology-only: a re-composition of the substrate via a new scoring expression applied to the SAME inventory of frozen trade CSVs. CSV-replay aggregator; no model fit; no Optuna call.

**Mitigation (NORMAL-RISK; no opt-in required):** none. The methodology-fix is the cheapest possible EXPLORATION (<30 min wall-clock) and the verdict resolves whether /045 ALT_1 was OOS-aware-selected or honestly-IS-selected — a substantive cycle-6 finding regardless of branch.

---

## Section 3 — Proposed Changes (methodology / IS-only solve algorithm)

### 3.1 — `analysis/iteration_v1-046/partition_solve_v2.py` (NEW; IS-only re-solve)

Committed BEFORE Phase 6.0 Critic pre-flight. Pure stdlib + pandas; no LightGBM, no Optuna, no MLflow.

**Algorithm:**

```
1. INPUT: inventory of (iter, coin) cells with valid IS trade CSVs.
   - Iterations in scope: /002..043 excluding /001, /026, /027, /029 (absent).
   - Per iteration: load reports-v1/iteration_v1-{iter}/in_sample/trades.csv.
   - Assert close_time < OOS_CUTOFF_MS = 1742774400000 (IS-window).
   - Per coin (symbol): filter rows by symbol == target_coin.
   - Drop (iter, coin) cells with 0 trades after filtering.
   - Drop cells with weight_factor = 0 (any zero-weighted trades).

2. SCORE: for each (iter, coin) cell:
   - IS_Sharpe = annualized daily Sharpe of cell's PnL series (sqrt(252) × mean/std).
   - IS_n_trades = count of cells' rows.
   - IS_n_trades_norm = IS_n_trades / 250. (Normalization factor 250, vs initial proposal 100, per LM Master Phase 4.5 Rec 2 — limits per-coin trade-count contribution to ~20% effective weight, reducing multiple-comparison inflation.)
   - score_is = 0.6 * IS_Sharpe + 0.4 * IS_n_trades_norm.

3. GATE: per-coin sample-size floor.
   - Drop cells with IS_n_trades < 20 (minimum reliability — σ_SR ≈ √(1/20) ≈ 0.22).
   - This is a sample-size FLOOR, not a TARGET; no tiebreaker uses trade count adversely.

4. RANK: per coin, sort cells by score_is descending. Tiebreaker hierarchy:
   - Primary: score_is descending.
   - Secondary: IS_Sharpe descending (largest signal wins).
   - Tertiary: IS_n_trades descending (largest sample wins — per LM Master Rec 3 Flag C; OUTLINE'S ORIGINAL ascending tiebreaker FLIPPED per LM Master advice).
   - Quaternary: source iter number ascending (older iter wins — less HP-search-budget evolution to overfit on; per LM Master Rec 1).

5. SELECT: per coin, take top-1 by score_is. Emit top-3 for diagnostic depth.

6. EMIT: analysis/iteration_v1-046/partition_solve_v2.csv with schema:
   coin,rank,iter,IS_Sharpe,IS_n_trades,IS_n_trades_norm,score_is,is_selected
```

**Tiebreaker change vs outline §15 Q2:** LM Master Recommendation 3 Flag C raised the concern that outline's "(IS Sharpe desc, IS n_trades asc)" picks the LOWEST-trade-count tied candidate, maximizing σ_SR exposure — the opposite of robustness. /046 brief adopts the LM-Master-preferred (IS Sharpe desc, IS n_trades **desc**) ordering. Per Section 3.5 below, this is an ADOPTED LM Master modification.

### 3.2 — `run_iteration_046.py` (NEW; CSV-replay aggregator dispatched on IS-only substrate)

Modifies /045's `run_iteration_045.py` to (a) source component IDs from `partition_solve_v2.csv` (not hardcoded) and (b) emit forensic comparison to ALT_1 substrate.

**Steps (sequential pass; <30 min total):**

1. Read `analysis/iteration_v1-046/partition_solve_v2.csv` → extract the 5 selected (coin, iter) pairs (the IS-only substrate).
2. For each of 5 components, load `reports-v1/iteration_v1-{iter}/{in_sample,out_of_sample}/trades.csv`.
3. Per component, filter rows by `symbol == target_coin` (defensive filter against multi-coin source iterations).
4. Concatenate filtered rosters; apply `weight_factor = 0.2` per row; sort by `close_time`.
5. Pipe through `generate_iteration_reports(..., iteration=46, ...)`.
6. **Forensic comparison emission:** ALSO re-aggregate the /045 ALT_1 substrate `(C-BTC=v1-012, C-ETH=v1-042, C-LINK=v1-011, C-LTC=v1-040, C-DOT=v1-031)` and emit `reports-v1/iteration_v1-046/comparison_vs_alt1.csv` with side-by-side headline metrics (IS Sharpe / OOS Sharpe / IS PnL / OOS PnL / IS trades / OOS trades) for both substrates. **This comparison is FORENSIC ONLY** — it is NOT used by any /046 falsifier (per F4 rationale).

### 3.3 — No `src/` changes

/046 is a methodology-axis iteration. No src/ touches; no LightGBM dispatch change; no feature engine change; no risk-gate change. The `partition_solve_v2.py` and `run_iteration_046.py` scripts live under `analysis/` and as a one-off runner respectively. Critic Check 14 (axis-family rotation match-to-actual-diff) verifies methodology axis match by inspecting that no src/ feature/risk/model paths are modified by this iteration's commits.

### 3.4 — Defaults / config inheritance

Each component's underlying trade CSV inherits its source iteration's full config (HPs, feature set, R1/R2/R3 settings, label mode). /046 does NOT modify any source iteration; the aggregator reads frozen artifacts.

### 3.5 — LM Master Phase 4.5 response map

LM Master `briefs-v1/iteration_v1-046/lgbm_advisor.md` issued 3 recommendations + 4 risk flags. Response map:

| LM recommendation | Response | Where addressed |
|---|---|---|
| **R1 — Look for HP-region diversity + IS sample-size adequacy across top-1 picks (NOT just IS Sharpe maximization)** | **ADOPTED (advisory; auditing trail).** `partition_solve_v2.csv` emits top-3 per coin with IS_Sharpe + IS_n_trades + source iter; engineering report in Phase 6 includes a "HP-basin concentration audit" subsection listing the source iter for each top-1 pick + flagging cases where 2+ top-1 picks share the same source iter (would indicate HP-basin concentration). Brief Section 11.D records the justification for top-1 (vs top-2) for each coin. NOT a falsifier — informational discipline. | §3.1 step 6 (top-3 emission); §11.D (Section to be filled in diary post-run) |
| **R2 — Pre-register per-coin candidate inventory + multiple-comparison correction (deflate IS Sharpe by ~0.36 per coin)** | **PARTIALLY ADOPTED.** Pre-registration: §2.3 lists pre-EDA top-3 estimates per coin (refined exact in Phase 6 output). Multiple-comparison correction: brief reports BOTH raw `score_is` AND deflated `score_is − 0.36·0.6` per coin in `partition_solve_v2.csv`'s diagnostic columns. **F1 threshold UPGRADED** from outline's "+0.50 raw IS Sharpe floor" to "+0.50 deflated bundle IS Sharpe floor" (equivalently, +0.86 raw — strictly more stringent). This addresses LM Master's load-bearing concern that /046's design removes OOS-aware bias but introduces best-of-25-30 IS-side inflation. | §2.3 (pre-EDA inventory); §3.1 step 2-5 (score formula); §4 F1 (deflated floor); §11.D (post-run audit) |
| **R3 — Verification recipe: data-loaded check, date-cutoff check, functional-invariance hide test** | **ADOPTED (3-part recipe).** Engineering report (Phase 6) MUST include: (a) Python `open()` log proving `partition_solve_v2.py` never touches `out_of_sample/` paths during execution; (b) grep-clean of `>= OOS_CUTOFF_MS` and `> OOS_CUTOFF_MS` patterns; (c) **functional-invariance hide test** — rename 5 source iters' `out_of_sample/` directories to `out_of_sample.HIDDEN/`, re-run `partition_solve_v2.py`, diff partition_solve_v2.csv before/after. Diff must be 0 bytes. Engineering report emits the diff verbatim. This is the F5 grep falsifier EXTENDED to functional-proof grade. | §4 F5 (extended); §9 smoke test |

LM Master risk flags — response map:

| LM Flag | Response |
|---|---|
| **Flag A — IS-overfit-on-a-different-axis (best-of-N inflation)** | Acknowledged in brief Section 4 F1 (deflated floor). The IS-only substrate is OOS-leak-free by construction but NOT IS-overfit-free; /047 multi-seed re-validation is still mandatory for MERGE-worthiness regardless of /046 verdict. |
| **Flag B — IS-only substrate may have WORSE OOS than ALT_1 (not a /046 failure)** | **EXPLICITLY DOCUMENTED in §4 F4.** OOS metrics are computed and reported in `comparison_vs_alt1.csv` for diagnostic interpretation but are NOT used as /046 success criteria. Brief Section 4 explicit language: "Critic CANNOT cite IS-only substrate OOS Sharpe < ALT_1 OOS Sharpe as evidence of /046 failure — that re-introduces the OOS-aware selection bias /046 is designed to detect." |
| **Flag C — Tiebreaker convention (IS n_trades desc, not asc)** | **ADOPTED (modification vs outline).** Tiebreaker hierarchy in §3.1 step 4 uses IS_n_trades DESCENDING (more trades = more reliable estimate). Outline's original ascending was flipped per LM Master advice. |
| **Flag D — Score formula effective-weight calculation** | **DOCUMENTED.** `IS_n_trades/250` ranges roughly [0.08, 0.60] for the inventory (20-150 IS trades after sample-size gate); IS_Sharpe ranges roughly [−0.5, +4]. Trade-count contributes ~[0.032, 0.24] to the score (effective ~8-15% weight, not the nominal 40%); IS_Sharpe dominates at effective ~85-92%. Trade-count acts as a soft tiebreaker more than a co-equal criterion. The /250 denominator (vs the initial /100 proposal) was adopted per LM Master Rec 2 to limit per-coin trade-count influence and reduce multiple-comparison inflation. This is the INTENDED behavior — /046 tests whether the score reproduces /045's substrate; the effective-weight distribution is documented for transparency, not adjusted. |

LM Master overall confidence MEDIUM-HIGH; modal prior PROMISING-DIVERGENCE 45%. QR concurs with the prior distribution (Section 7).

---

## Section 3.6 — Wall-Clock Estimate

| Step | Duration |
|---|---|
| Load IS-side trades.csv from inventory (~38 iters × 5 coins = up to 190 nominal cells, ~100-130 realised cells) | ~3 min |
| Per-cell IS Sharpe + IS n_trades + score_is computation | <1 min |
| Per-coin ranking + top-1 selection + tiebreaker resolution | <1 min |
| Emit partition_solve_v2.csv | <1 min |
| Re-aggregate IS-only substrate via /045 CSV-replay aggregator | ~5-10 min |
| Re-aggregate ALT_1 substrate for forensic comparison | ~5-10 min |
| Emit reports + checksums + Spearman rank corr | <2 min |
| F5 grep + functional-invariance hide test integration smoke | <5 min |
| **TOTAL** | **<30 min** |

**NO runtime kill-switch** (wall-clock is bounded mechanically by I/O on small CSVs; no compute-heavy step).

---

## Section 4 — Pre-Registered Failure-Mode Falsifiers (F-AXIS #1 through #5)

### F-AXIS #1 — Master IS-only substrate bundle quality floor (UPGRADED with LM Rec 2 deflation)

**Claim:** IS-only substrate's bundle IS daily Sharpe ≥ **+0.50 deflated** (equivalently, ≥ +0.86 raw under best-of-N correction). Deflation: per-coin score is adjusted by `−0.36·0.6 = −0.216` per LM Master Rec 2 (best-of-25-30 IS Sharpe inflation σ ≈ 0.14 × √(2 log 30) ≈ 0.36 per coin).

**Rationale:** ALT_1's IS Sharpe is +1.99 from 5 components selected partly on IS. If the IS-only substrate produces deflated IS Sharpe < +0.50, two scenarios:
- ALT_1's IS Sharpe was itself IS-overfit (selection on IS-side too); the IS-only substrate exposes this by selecting on PURE IS without OOS cushion.
- Both substrates have low IS Sharpe; the partition framework is signal-bounded by the inventory.

**Status:** Master falsifier. F1 FAIL → escalate to F-AXIS #2 diagnostic; verdict NULL-METHODOLOGY-FIX (signal-bounded). Do not propose substrate change.

**Threshold rationale:** +0.50 deflated bundle IS Sharpe is the same absolute floor as /045's `feedback_sharpe_floor.md` "Sharpe 1.0 floor" applied at deflated grade. Multi-seed validation in /047 may reveal additional discount; +0.50 here is a NECESSARY (not sufficient) condition for the substrate to be considered for /047.

### F-AXIS #2 — Coincidence (substrate matches ALT_1 exactly; 5-of-5)

**Claim:** IS-only top-1-per-coin equals ALT_1's substrate exactly:
- C-BTC: v1-012
- C-ETH: v1-042
- C-LINK: v1-011
- C-LTC: v1-040
- C-DOT: v1-031

**Interpretation if PASS (5/5 coincidence):** ALT_1 was honest within its OOS-aware framework — the IS signal in those 5 components was ALSO the strongest under IS-only scoring; the OOS-aware composite score did not divert from IS-only selection. ALT_1's headline +3.49 OOS Sharpe is supported by IS-side evidence and the 5-component partition is robust to scoring choice.
- **Action:** /047 escalates to multi-seed re-validation of ALT_1 (Critic Path Forward #1 in its original form) with HIGH confidence.

**Interpretation if FAIL:** see F-AXIS #3.

**Prior:** ~10% (LM Master estimate). v1-012's IS −0.21 makes BTC near-certain to diverge from ALT_1.

### F-AXIS #3 — Divergence (substrate components diverge ≥3 of 5 coins)

**Claim:** IS-only top-1-per-coin disagrees with ALT_1 on at least 3 of the 5 components.

**Interpretation if PASS (≥3 divergence):** OOS-inflation confirmed — the original score function's OOS terms (0.5·OOS_Sharpe + 0.2·OOS_n_trades) drove the substrate selection away from what IS evidence alone supports. ALT_1's headline +3.49 OOS Sharpe is, with high probability, a post-hoc selection artifact whose honest discount is 30-50% (per Critic /045 BLOCK-FINAL).
- **Action:** /047 becomes the IS-only substrate's multi-seed re-validation (NOT ALT_1's). ALT_1 is downgraded in the cycle-6 substrate-candidate ledger.

**Prior:** ~45% (LM Master modal). Driven by C-BTC near-certain divergence + medium-probability ETH/LINK divergence.

### F-AXIS #4 — Boundary case (1-2 divergences) + per-coin Pareto-dominance (relaxed; IS-only)

**Claim (1-2 divergences):** Most likely scenario where BTC diverges but ETH/LINK/LTC/DOT match — marginal evidence about OOS-inflation magnitude.

**Interpretation if PASS:** marginal substrate divergence. Both substrates are credible candidates; one is the IS-honest selection, the other is the OOS-honest selection.
- **Action:** /047 covers BOTH substrates in dual multi-seed validation. cycle-6 EXPLORATION 2/10.

**Per-coin Pareto-dominance (relaxed):** IS-only substrate's bundle Pareto-dominates BASELINE_V1 on every IS regime within σ_R. **NO OOS criterion in /046 falsifier** — OOS is observed but not used as a /046 success criterion to avoid the same OOS-aware selection bias.

**OOS treatment:** OOS metrics are COMPUTED and REPORTED in `reports-v1/iteration_v1-046/comparison.csv` and `reports-v1/iteration_v1-046/comparison_vs_alt1.csv` for diagnostic interpretation. The /046 verdict is determined SOLELY by F1+F2+F3+F4+F5. OOS divergence between the two substrates is FORENSIC EVIDENCE supporting F3's "OOS-inflation" interpretation but is NOT itself a falsifier — because using OOS to grade substrate-selection methodology would re-introduce the very leakage /046 is designed to detect (LM Master Flag B; expressly endorsed).

**Critic constraint (binding for Phase 7.5):** Critic CANNOT cite "IS-only substrate OOS Sharpe < ALT_1 OOS Sharpe" as evidence of /046 failure. The methodology axis is explicitly orthogonal to OOS magnitude comparisons.

**Prior:** ~20% (LM Master).

### F-AXIS #5 — Anti-pattern (partition_solve_v2.py is IS-clean)

**Claim:** the committed `analysis/iteration_v1-046/partition_solve_v2.py` script:
- **(a) Grep-clean** for OOS data references — no `oos`, no `out_of_sample`, no `OOS_CUTOFF` (other than the IS-side `< OOS_CUTOFF_MS` assertion), no post-`2025-03-24` date used for filtering IN (only as the IS-window UPPER bound).
- **(b) Data-loaded check** — Python `open()` log shows the script only touches `reports-v1/iteration_v1-{iter}/in_sample/trades.csv` paths; never `out_of_sample/`.
- **(c) Functional-invariance check (hide test)** — re-running `partition_solve_v2.py` with `out_of_sample/` directories renamed to `out_of_sample.HIDDEN/` for 5 randomly-chosen iters produces bit-identical output. Diff is 0 bytes.

**Mechanism:** the script must:
- Load `reports-v1/iteration_v1-{iter}/in_sample/trades.csv` ONLY.
- Assert `close_time < OOS_CUTOFF_MS` at load time; raise on violation.
- For each (iter, coin) cell: compute IS daily Sharpe (annualised) and IS n_trades.
- Compute `score_is = 0.6 · IS_Sharpe + 0.4 · IS_n_trades / 250`.
- Per coin, rank candidates by `score_is` descending; pick top-1 via tiebreaker hierarchy (§3.1 step 4).
- Emit `partition_solve_v2.csv` with per-coin top-3.

**Status:** Process integrity falsifier. F5 FAIL (any sub-check) → `BLOCK-PENDING-FIX` (one re-run cycle allowed per skill §v1 BLOCK-PENDING-FIX discipline; QR fixes script, re-grep, re-runs).

**Prior:** ~5% (LM Master) — script defect risk is low given clear F5 spec.

---

### Falsifier summary table

| F-AXIS | Falsifier | Trigger | /046 Verdict | /047 routing |
|---|---|---|---|---|
| F1 | Master deflated IS Sharpe floor | Bundle deflated IS Sharpe < +0.50 | NULL-METHODOLOGY-FIX (signal-bounded) | New content axis (axis-family rotation) |
| F2 | 5/5 substrate coincidence with ALT_1 | All 5 IS-only top-1 picks = ALT_1 picks | PROMISING-COINCIDENCE | ALT_1 multi-seed re-validation |
| F3 | ≥3 substrate divergence | ≥3 of 5 IS-only top-1 picks differ from ALT_1 | PROMISING-DIVERGENCE | IS-only substrate multi-seed re-validation |
| F4 | Boundary (1-2 divergence) + IS-regime Pareto | 1-2 IS-only top-1 picks differ from ALT_1, AND IS-regime Pareto holds | PROMISING-PARTIAL | Dual multi-seed validation |
| F5 | Anti-pattern (script OOS-leak) | Any of (grep / data-loaded / hide-test) fails | BLOCK-PENDING-FIX | One re-run cycle of /046 itself |

---

## Section 5 — Methodology Integrity

### 5.1 — Look-ahead audit

- `partition_solve_v2.py` loads ONLY IS-window trade rosters (`in_sample/trades.csv`), enforced by the `close_time < OOS_CUTOFF_MS` assertion at load.
- `run_iteration_046.py` CSV-replay aggregator inherits each source iteration's walk-forward embargo (no re-fit at /046; embargo applied at source iteration time).
- Each source iteration's `walk_forward.py:113` carries the lookahead-bug fix `train_end_ms = test_start_ms - embargo_ms` (commit `e149e9d`, verified at /045 Critic Phase 7.5).
- Each component CSV was produced by its source iteration runner under standard purge requirements; embargo is baked into the trade rosters /046 reads.

### 5.2 — Embargo

No new embargo computation at /046 bundle level. Inherited from source iterations. Validated at /045 Phase 7.5 Critic Check 2 PASS (review.md).

### 5.3 — DSR / PSR / PBO

INFORMATIONAL ONLY at /046 EXPLORATION budget. CSV-replay aggregator does not produce Optuna trial population; DSR / PBO / PSR at bundle level have no trial-count denominator. Per skill convention, these are reported as informational metrics in `comparison.csv` but do not enter any /046 falsifier.

### 5.4 — Regime attribution

`reports-v1/iteration_v1-046/regime_attribution.csv` emitted via canonical regime tagger (BTC 90-day return × rv30 quantiles; matches /045 emission). Per-regime IS Pareto-dominance check is part of F4's relaxed Pareto criterion (IS only). OOS regime attribution computed for forensic comparison; not used in /046 verdict.

### 5.5 — Reproducibility checksum

`reports-v1/iteration_v1-046/source_checksums.csv` emitted with SHA-256 of each component's source `{in_sample,out_of_sample}/trades.csv`. If the IS-only substrate matches ALT_1 (F2 PASS), the 10 SHA-256s match /045's row-for-row. If the substrate diverges, the new components' SHA-256s replace the divergent rows (still 10 total: 5 components × 2 windows). The `comparison_vs_alt1.csv` emission also writes ALT_1's 10 source SHA-256s for parallel verification.

### 5.6 — Hypothesis-implementation alignment (Critic Check 8 equivalent)

Brief Section 1 declares: "IS-only solve emerging substrate identical-or-different from ALT_1." Runner implementation: (a) `partition_solve_v2.py` computes IS-only per-coin top-1; (b) `run_iteration_046.py` aggregates the resulting 5-component substrate via the same CSV-replay path /045 used. The hypothesis-implementation match is direct.

### 5.7 — Critic Check 14 (axis-family match-to-diff)

QE Phase 6.0 / Critic Phase 7.5 verify that `git diff` shows NO src/ changes (no LightGBM dispatch / features / risk gates / runner core touched). Only:
- `analysis/iteration_v1-046/partition_solve_v2.py` (new).
- `analysis/iteration_v1-046/partition_solve_v2.csv` (output).
- `analysis/iteration_v1-046/bundle_weights.csv` (inherited from /045 methodology; EQUAL 1/5).
- `run_iteration_046.py` (new, top-level runner).
- `briefs-v1/iteration_v1-046/...` (this brief + supporting artifacts).
- `reports-v1/iteration_v1-046/...` (Phase 6 output artifacts).
- `diary-v1/iteration_v1-046.md` (Phase 8 output).

The axis is methodology; the diff scope MUST match.

---

## Section 6 — Risk Mitigation (Section 6 of v1 brief schema)

### 6.1 — Inherited risk gates

/046 inherits BASELINE_V1's risk stack unchanged. NO new R1/R2/R3 changes; the methodology axis is orthogonal to risk-primitive axes. Each component's source iteration owns its own R1/R2/R3 config baked into the source `trades.csv` (CSV-replay; no new dispatch).

### 6.2 — Substrate-selection robustness (R1-methodology)

**F1 floor at +0.50 deflated IS Sharpe.** If IS-only substrate deflated IS Sharpe < +0.50, the IS-side signal is itself weak across the inventory and the partition framework is signal-bounded. /046 closes as NULL-METHODOLOGY-FIX (signal-bounded); cycle-6 looks beyond cycle-5's inventory for substrate candidates (axis-family rotation: NEW feature family / on-chain / microstructure per Critic Path Forward #3).

### 6.3 — Coincidence-cherrypick guard (R2-methodology)

**F2's 5/5 coincidence is binary and pre-registered** — if the IS-only top-1 disagrees on even 1 coin, F2 FAILs. Score ties are broken with the deterministic tiebreaker hierarchy in §3.1 step 4 (Primary score_is desc; Secondary IS_Sharpe desc; Tertiary IS_n_trades desc per LM Master Flag C; Quaternary source iter ascending per LM Master Rec 1). Tiebreaker is deterministic given the IS data; documented in `partition_solve_v2.py` Section 4 (in-script header comment).

### 6.4 — Anti-pattern leakage (R3-methodology)

**F5's grep + data-loaded + hide-test is mandatory** — the script MUST be IS-clean across all three sub-checks. Critic Check 17 (IS-only weight provenance) extended at /046 to cover IS-only SUBSTRATE provenance via the same grep regime + functional-invariance proof. BLOCK-PENDING-FIX at Phase 7.5 if the script fails any of the 3 sub-checks.

### 6.5 — Per-coin partition coverage (R4-methodology)

IS-only substrate could in principle pick a multi-coin iteration's BTC trades (e.g., v1-013 if it has both BTC and ETH); the partition_solve MUST filter by `symbol == target_coin` BEFORE ranking, mirroring /045's per-component universe filter. This is documented as Step 1 in `partition_solve_v2.py` (`per coin (symbol): filter rows by symbol == target_coin`).

### 6.6 — Per-coin sample-size floor (R5-methodology)

Cells with IS_n_trades < 20 are dropped before ranking (§3.1 step 3). σ_SR ≈ √(1/20) ≈ 0.22; below this the IS Sharpe estimate is too noisy to rank reliably. This is a sample-size FLOOR (not a target); the deterministic tiebreaker handles ties at or above the floor.

### 6.7 — Informational OOS (R6-methodology)

OOS metrics are computed for diagnostic interpretation but NOT used in any falsifier (per F4 rationale; LM Master Flag B). Brief Section 4 is explicit that OOS is NOT a /046 success criterion. Critic at Phase 7.5 SHOULD NOT cite "OOS Sharpe < +0.50" as a /046 verdict input.

### 6.8 — Data integrity / regime breadth

`partition_solve_v2.py` enforces:
- `weight_factor != 0` filter (drops zero-weighted trades; matches /045 convention).
- `close_time < OOS_CUTOFF_MS` assertion (raises on violation).
- Per-coin `symbol == target_coin` filter before ranking.

Regime breadth: 5/5 coins covered (BTC, ETH, LINK, LTC, DOT) — matches BASELINE_V1 universe exactly. No coin is added or dropped from the partition.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

### 7.1 Verdict band priors (LM Master + QR convergence)

| Verdict | Prior | Reasoning |
|---|---:|---|
| **PROMISING-DIVERGENCE** (modal) | **45%** | C-BTC v1-012's IS Sharpe = −0.21 makes BTC divergence near-certain. Add likely 1-2 additional divergences (ETH/LINK with positive but non-exceptional IS Sharpes that may be edged out by higher-IS-Sharpe pool-A or single-coin candidates). 3+ divergence is more probable than exactly 1-2 once the BTC anomaly is conditional. |
| **PROMISING-PARTIAL (1-2 div)** | 20% | Boundary scenario where BTC diverges but ETH/LINK/LTC/DOT all match ALT_1. Routes /047 to dual multi-seed validation. |
| **NULL-METHODOLOGY-FIX (signal-bounded)** | 15% | F1 FAIL at +0.50 deflated IS Sharpe floor. v1-040 LTC IS +3.76 alone contributes +0.50 deflated × 1/5 ≈ +0.10 to bundle (per-coin best-of-N deflation reduces +3.76 → +3.40 deflated → contribution +0.68/5 = +0.14). Lower bound prior because LTC component nearly clears F1 alone. |
| **PROMISING-COINCIDENCE** | 10% | Would require 5 of 5 IS-only picks to match ALT_1 — requires C-BTC v1-012 to be IS-only top-1 for BTC despite IS Sharpe −0.21. Effectively impossible UNLESS no other iter covered BTC with positive IS Sharpe + IS n_trades ≥ 20. Inventory survey makes this implausible. |
| **BLOCK-PENDING-FIX (F5 grep fail)** | 5% | Script defect risk; competent execution makes this small. |
| **NULL-METHODOLOGY-FIX (other modes)** | 5% | E.g., tiebreaker collapse or score-formula edge case producing non-unique top-1 with no documented resolution. |
| **TOTAL** | 100% | |

### 7.2 Most plausible failure scenario

**Most plausible BLOCK-PENDING-FIX scenario:** `partition_solve_v2.py` accidentally constructs an OOS path via f-string (e.g., `f"reports-v1/iteration_v1-{iter}/{window}/trades.csv"` where `window` is parameterized). F5 hide test catches it (output changes when OOS dir hidden). One re-run fixes (hardcode `in_sample` literal).

**Most plausible NULL-METHODOLOGY-FIX scenario:** the inventory contains very few positive-IS-Sharpe candidates for BTC and ETH (pool-A baseline plus 2-3 weak BTC-positive iters), and the deflation correction reduces the best per-coin score_is enough that bundle deflated IS Sharpe lands at +0.30-0.45. Triggers F1 FAIL → cycle-6 next axis pivots to NEW feature family per Critic Path Forward #3.

**Most plausible PROMISING-DIVERGENCE scenario (modal expected outcome):**
- C-BTC: v1-022 or v1-023 wins (positive IS Sharpe; v1-012 NOT top-1).
- C-ETH: v1-022 or v1-040 wins (higher IS Sharpe than v1-042's +0.71); v1-042 NOT top-1.
- C-LINK: v1-036 or v1-043 wins; v1-011 NOT top-1.
- C-LTC: v1-040 wins (matches ALT_1).
- C-DOT: v1-031 wins (matches ALT_1).
- 3 divergences (BTC, ETH, LINK), 2 matches (LTC, DOT) → F3 PASS, F2 FAIL → PROMISING-DIVERGENCE.
- /047 axis = IS-only substrate multi-seed re-validation.

### 7.3 Expected metric signature

Under the modal PROMISING-DIVERGENCE scenario:
- IS-only substrate bundle IS Sharpe: likely +1.5 to +2.5 raw (deflated +1.0 to +2.0; above F1 +0.50 floor).
- IS-only substrate bundle OOS Sharpe: highly uncertain — could be lower than ALT_1's +3.49 (consistent with "ALT_1 inflated by OOS-aware selection") OR similar (consistent with "OOS-aware selection didn't actually inflate that much"). EITHER OUTCOME IS COMPATIBLE WITH PROMISING-DIVERGENCE; OOS is not used as the discriminator.
- Spearman rank corr between IS-only ranking and /045 composite ranking: expected per coin ~0.5-0.8 (rankings should be POSITIVELY correlated since both load on IS Sharpe heavily; perfect correlation would imply F2 PASS).
- F1 (deflated IS Sharpe ≥ +0.50): PASS expected with LTC component alone contributing strong IS lift.
- F2: FAIL expected.
- F3: PASS expected.
- F4: N/A under F3 PASS (boundary case dissolves into F3).
- F5: PASS expected (clean script execution).

---

## Section 8 — Pre-Registered Comparison Criteria (vs BASELINE_V1 + vs /045 ALT_1)

### 8.1 — Comparison vs BASELINE_V1 (per F-AXIS #4 relaxed IS-Pareto)

For every tagged regime R ∈ {bull, bear, chop, vol-spike, recovery, other} present in IS:

```
sharpe_R(IS-only bundle, IS) ≥ sharpe_R(BASELINE_V1, IS) − σ_R
AND max_dd_R(IS-only bundle, IS) ≤ max_dd_R(BASELINE_V1, IS) + σ_dd_R
AND trade_count_R(IS-only bundle, IS) ≥ 0.5 × trade_count_R(BASELINE_V1, IS) [rare-regime carve-out if baseline < 10]
```

AND at least one regime R* where:
```
sharpe_R*(IS-only bundle, IS) > sharpe_R*(BASELINE_V1, IS) + σ_R*
   OR max_dd_R*(IS-only bundle, IS) < max_dd_R*(BASELINE_V1, IS) − σ_dd_R*
```

σ_R and σ_dd_R read from `briefs-v1/_meta/baseline_seed_regime_matrix.csv`.

**NOTE: IS-regime-Pareto check is RELAXED (not load-bearing).** /046 is EXPLORATION; the master falsifier is F1 (deflated IS Sharpe floor). F-AXIS #4's IS-regime check is informational diagnostic.

### 8.2 — Forensic comparison vs /045 ALT_1 (NOT a falsifier; informational)

`reports-v1/iteration_v1-046/comparison_vs_alt1.csv` emits side-by-side:

| Metric | IS-only substrate | /045 ALT_1 substrate | Δ |
|---|---|---|---|
| IS daily Sharpe | (computed) | +1.9879 | (computed) |
| OOS daily Sharpe | (computed) | +3.4851 | (computed) |
| IS PnL ($) | (computed) | +238.41 | (computed) |
| OOS PnL ($) | (computed) | +122.33 | (computed) |
| IS n_trades | (computed) | 581 | (computed) |
| OOS n_trades | (computed) | 199 | (computed) |
| Substrate components | (5-tuple from partition_solve_v2.csv) | (C-BTC=v1-012, C-ETH=v1-042, C-LINK=v1-011, C-LTC=v1-040, C-DOT=v1-031) | (overlap count) |
| Substrate overlap with ALT_1 | (count 0-5) | 5 (by definition) | (5 − overlap) |

**Critic constraint:** OOS Δ between IS-only and ALT_1 is FORENSIC EVIDENCE supporting F3 (if IS-only OOS < ALT_1 OOS, that is consistent with "ALT_1 was OOS-aware-selected"; if IS-only OOS > ALT_1 OOS, that is consistent with "the OOS-aware selection in /045 was somehow suboptimal even on OOS"; both are informational). NOT used as /046 falsifier (LM Master Flag B; Section 4 F4 binding).

### 8.3 — Per-coin top-1-vs-ALT_1 comparison

`reports-v1/iteration_v1-046/per_coin_top1_vs_alt1.csv`:

| Coin | IS-only top-1 (from partition_solve_v2.csv) | ALT_1 pick | Match? | IS Sharpe delta | OOS Sharpe delta (forensic) |
|---|---|---|---|---:|---:|
| BTC | (iter) | v1-012 | (T/F) | (computed) | (computed; forensic) |
| ETH | (iter) | v1-042 | (T/F) | (computed) | (computed; forensic) |
| LINK | (iter) | v1-011 | (T/F) | (computed) | (computed; forensic) |
| LTC | (iter) | v1-040 | (T/F) | (computed) | (computed; forensic) |
| DOT | (iter) | v1-031 | (T/F) | (computed) | (computed; forensic) |

F2 evaluation: 5/5 Match = F2 PASS; <5/5 Match = F2 FAIL; routes to F3 (≥3 Match = F3 FAIL → F4 boundary; ≤2 Match = F3 PASS).

---

## Section 9 — Library Stack Declaration

**No fresh dependencies; stdlib + existing pinning only.**

- `pandas` (existing pinning) — CSV I/O and per-cell groupby.
- `numpy` (existing) — Sharpe computation.
- `pathlib`, `csv`, `hashlib` (stdlib) — file paths, source checksums.
- `itertools.combinations` (stdlib) — pairwise universe disjointness assertion (inherited from /045 runner).
- `scipy.stats.spearmanr` (existing) — Spearman rank correlation between IS-only ranking and /045 composite ranking.

**NOT INVOKED at /046:**
- `lightgbm` / `xgboost` — no model fit at CSV-replay stage.
- `optuna` — no HP search.
- `mlfinlab` / `pypbo` — no PBO / CSCV at EXPLORATION budget.
- `fracdiff` / `statsmodels` — no feature engineering or stationarity tests at /046 (inherited from source iterations).

No new pinning vs BASELINE_V1's `pyproject.toml` is required for /046.

---

## Section 10 — Regime Attribution Plan

Per skill mandate (NEW 2026-05-31 regime-ensemble), every iteration must declare its regime-attribution plan.

**Target regimes:** all regimes present in IS (bull, bear, chop, vol-spike, recovery, other) per canonical tagger.

**Mechanism (per /046 substrate; per component — substrate decided at Phase 6):**

The /046 verdict produces a 5-component substrate (selected by IS-only score). Each component's regime profile is INHERITED from its source iteration's diary. The per-coin regime profiles will be enumerated in Phase 8 diary after `partition_solve_v2.csv` resolves the 5 components.

**Per-coin specialist-mechanism classification (POST-Phase-6, in diary):**

For each of the 5 selected components, the diary records:
- IS-side regime profile: UNIVERSAL / REGIME-SPECIALIST-IS / TAIL-CONTROL / etc.
- OOS-side regime profile (forensic; not used in verdict): same classification space.
- Comparison vs ALT_1 component for same coin (if divergent).

**Bundle role:** 5 single-coin specialists, equal-weighted. Coverage is per-coin Pareto-dominance on the IS side (relaxed check; not load-bearing). OOS regime distribution is forensic (highly likely 95%+ trades land in "other" regime per /045 attribution — regime classifier limitation is inherited, not addressed at /046).

**Off-regime expectation:** any coin where the IS-only substrate's component has a weaker IS-side regime profile than ALT_1's component (e.g., if IS-only picks a PROMISING-IS over a UNIVERSAL pick from ALT_1, the IS-only bundle could show narrower IS regime coverage). This is documented in Phase 8 diary as forensic.

**Regime-aware falsifier:** F4 (relaxed IS-regime Pareto, not load-bearing). F1 (master deflated IS Sharpe) is the binding falsifier.

---

## Section 11 — Bundle Composition (CONFIRMATION-only; N/A for /046 EXPLORATION)

**N/A — /046 is EXPLORATION, not CONFIRMATION-MERGE-PORTFOLIO.**

The bundle-composition discipline (Sections 11.A universe disjointness, 11.B IS-only weight provenance, 11.C backtest-live parity, 11.D re-composition note) applies to CONFIRMATION-MERGE-PORTFOLIO iterations. /046 is a methodology-axis EXPLORATION; the bundle aggregation in `run_iteration_046.py` inherits /045's wiring (proven Check-15/16/17 PASS by construction) AND uses the SAME `bundle_weights.csv` (EQUAL 1/5 weights) as /045 — but /046 is NOT a MERGE attempt.

If /046 verdict is PROMISING-COINCIDENCE / PROMISING-DIVERGENCE / PROMISING-PARTIAL, /047 (CONFIRMATION or further EXPLORATION) will author Section 11 in full for the validated substrate.

**Diagnostic note for /046:** the IS-only substrate's bundle aggregation in `run_iteration_046.py` does verify (a) pairwise universe disjointness across the 5 selected components, (b) bundle universe = `{BTC, ETH, LINK, LTC, DOT}` exactly. This is identical wiring to /045 because each substrate variant is 5 single-coin specialists. The /046 Section 11 brief is N/A but the runtime assertion in the runner (`run_iteration_046.py`) inherits /045's `combinations(universes, 2)` disjointness check.

---

## End of Brief

**Summary:**

iter-v1/046 is a cycle-6 EXPLORATION methodology-axis iteration that re-solves /045's substrate selection under an IS-only scoring expression (`score_is = 0.6·IS_Sharpe + 0.4·IS_n_trades_norm`; gated at IS_n_trades ≥ 20; tiebreaker hierarchy hardened per LM Master Flag C) to test whether ALT_1 was OOS-aware-selected (F3 PROMISING-DIVERGENCE; modal 45%) or IS-honest (F2 PROMISING-COINCIDENCE; 10%) or signal-bounded (F1 NULL-METHODOLOGY-FIX; 15%). Master falsifier F1 is UPGRADED per LM Master Rec 2 from raw +0.50 IS Sharpe floor to **deflated** +0.50 (raw +0.86 under best-of-25-30 correction). Substrate-leakage is enforced by F5 (grep + data-loaded + functional-invariance hide test). OOS is computed for forensic comparison only; the /046 verdict is determined SOLELY by F1-F5, never by OOS magnitude (LM Master Flag B; Critic constraint binding at Phase 7.5). Wall-clock <30 min; no Optuna; no LightGBM fit; no src/ changes. Verdict resolves /047 routing: ALT_1 multi-seed (COINCIDENCE) / IS-only multi-seed (DIVERGENCE) / dual multi-seed (PARTIAL) / NEW feature family axis (NULL signal-bounded) / one-rerun script fix (BLOCK-PENDING-FIX).
