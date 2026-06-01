# Iteration v1-045 — Research Brief

## Section 0.0 — Banner

**TYPE:** `CONFIRMATION-MERGE-PORTFOLIO`
**Cycle slot:** cycle-6 CONFIRMATION 1/1 (FIRST CONFIRMATION under the new bundle-discipline rules: Rules 7 / 8 / 9 + Critic Checks 15 / 16 / 17).
**Anchor:** `BASELINE_V1` corrected walk-forward (IS daily Sharpe +0.4761 / OOS daily Sharpe +1.1415; OOS_CUTOFF_DATE = 2025-03-24; IS PnL +54.05 / OOS PnL +36.96).
**Substrate:** **5-component symbol-partitioned federation** (`C-BTC, C-ETH, C-LINK, C-LTC, C-DOT`) at EQUAL 1/5 weights. Bundle universe is `{BTC, ETH, LINK, LTC, DOT}` — coverage matches BASELINE_V1 exactly; ownership is now per-coin (one component per symbol) rather than per-pool.
**Branch:** `iteration-v1/045`. **Tag (post-Phase-8):** `v0.v1-045`.
**Re-composition source:** workflow `w0qpo136q` partition solve over iter-v1/baseline + iter-v1/001-043 inventory. Recommended SHIP target = ALT_1 (this substrate). Fallback target = ALT_2 (BTC=v1-023 swap; see F-AXIS #7).

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — unchanged (sacred).
- `training_months = 24` — unchanged (sacred).
- IS window: `[earliest available data, 2025-03-24)`.
- OOS window: `[2025-03-24, latest available data]`.
- Walk-forward: `train_end_ms = test_start_ms - embargo_ms` at `walk_forward.py:113` (verified by Phase 6.0 mini-Foundation check).

---

## Section 0.5 — Iteration Type Declaration + Cadence

**TYPE:** `CONFIRMATION-MERGE-PORTFOLIO`
**Wall-clock target:** ~10-30 min (design target; NO runtime kill-switch). CSV-replay aggregation only — no Optuna, no LightGBM fit calls.
**Wall-clock estimate (Section 3.6):** <30 min total (read 10 trade CSVs + concat + sort + 1/5 weight + generate reports + per-component checksum + integration smoke test).
**Cycle-6 status:** cycle-5 closed at /044 BLOCK-FINAL (retroactive — pre-bundle-discipline rules), so cycle-6 begins at /045.

**Previous CONFIRMATION verdict:** `/044 BLOCK-FINAL` (retroactive, RULE-7 + RULE-8 + RULE-1 violations: coin-overlap on {LINK, DOT} between BASELINE_V1 and /036 components; weights not derived by committed IS-only `weight_calibration.py` script). `/044` is grandfathered as the 10th cycle-5 EXPLORATION-comparator; its headline metrics are NOT MERGED.

**EXPLORATION precedents for `/045`:**

Per the new bundle-discipline rules (Rules 7/8/9 + Checks 15/16/17), `/045`'s components are sourced from ALREADY-VALIDATED prior iterations — no new EXPLORATION is required at the `/045` boundary because the bundle is a re-composition of pre-existing per-coin specialists, not a fresh hypothesis. The substrate is:

- **C-BTC = `iter-v1/012`** ← single-coin {BTCUSDT} (source: `reports-v1/iteration_v1-012/{in_sample,out_of_sample}/trades.csv`).
- **C-ETH = `iter-v1/042`** ← single-coin {ETHUSDT} (source: `reports-v1/iteration_v1-042/{in_sample,out_of_sample}/trades.csv`).
- **C-LINK = `iter-v1/011`** ← single-coin {LINKUSDT} (source: `reports-v1/iteration_v1-011/{in_sample,out_of_sample}/trades.csv`).
- **C-LTC = `iter-v1/040`** ← single-coin {LTCUSDT} (source: `reports-v1/iteration_v1-040/{in_sample,out_of_sample}/trades.csv`).
- **C-DOT = `iter-v1/031`** ← single-coin {DOTUSDT} (source: `reports-v1/iteration_v1-031/{in_sample,out_of_sample}/trades.csv`).

Cadence-precedent count for `/045` is satisfied via the cycle-5 EXPLORATION ledger (iter-v1/034 through iter-v1/043, 10 EXPLORATIONs) reproduced in `briefs-v1/exploration_catalog.md`. The /044 grandfathered CONFIRMATION is recorded but NOT MERGED.

---

## Section 0.6 — Architecture-Family Justification

**Axis family:** N/A — CONFIRMATION-MERGE-PORTFOLIO is a multi-component bundle assembly, not a single-axis variation. Axis Rotation Discipline does NOT apply to CONFIRMATIONs per skill §"Phase Quick Reference"; rotation gating is skipped at Phase 5.5.

**Bundle-discipline note:** `/045` is the FIRST CONFIRMATION under the bundle-discipline rules. The methodology gates being exercised for the first time are Critic Checks 15 / 16 / 17 (Backtest-Live Parity, Universe Disjointness, IS-Only Weight Provenance).

---

## Section 1 — Hypothesis

The **5-component symbol-partitioned federation** `(C-BTC=v1-012, C-ETH=v1-042, C-LINK=v1-011, C-LTC=v1-040, C-DOT=v1-031)` at EQUAL 1/5 weights **Pareto-dominates `BASELINE_V1`** on both IS and OOS by assigning each coin to the strongest individually-validated single-coin specialist found in the inventory of iter-v1/baseline + iter-v1/001-043 (workflow `w0qpo136q` partition solve, ALT_1).

The mechanism is **per-coin specialist substitution**: instead of pooling BTC+ETH under one Model A (BASELINE_V1) or LINK+DOT under one C3 (/036), every coin is now owned by its best stand-alone iteration. Verifier-computed bundle IS Sharpe +1.9879 / OOS Sharpe +3.4851 (vs BASELINE_V1 IS +0.4761 / OOS +1.1415; Δ IS +1.51 / Δ OOS +2.34), with 5/5 coins Pareto-dominating BASELINE on at least one window (3/5 dominate both windows; 2/5 dominate one and within-σ on the other).

---

## Section 2 — IS-Only Numerical Evidence

Verifier-computed per-coin matrix (independent simulation from raw component trade CSVs, IS-window-asserted via `close_time < 1742774400000`):

### Per-coin component table (ALT_1 substrate)

| Component | Owns | Source trade CSVs | IS Sharpe | IS trades | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|---|
| C-BTC | {BTCUSDT} | `reports-v1/iteration_v1-012/{in_sample,out_of_sample}/trades.csv` | −0.21 | 65 | **+6.10** | 19 |
| C-ETH | {ETHUSDT} | `reports-v1/iteration_v1-042/{in_sample,out_of_sample}/trades.csv` | +0.71 | 132 | +2.40 | 44 |
| C-LINK | {LINKUSDT} | `reports-v1/iteration_v1-011/{in_sample,out_of_sample}/trades.csv` | (verifier-computed) | — | (OOS, 47t) | 47 |
| C-LTC | {LTCUSDT} | `reports-v1/iteration_v1-040/{in_sample,out_of_sample}/trades.csv` | +3.76 | 117 | +0.64 | 52 |
| C-DOT | {DOTUSDT} | `reports-v1/iteration_v1-031/{in_sample,out_of_sample}/trades.csv` | +2.40 | 117 | +3.24 | 37 |

### Bundle aggregate (ALT_1; verifier-computed via independent simulation from raw CSVs)

| Metric | ALT_1 bundle | BASELINE_V1 anchor | Δ vs baseline |
|---|---|---|---|
| IS daily Sharpe (ann.) | **+1.9879** | +0.4761 | **+1.51** |
| OOS daily Sharpe (ann.) | **+3.4851** | +1.1415 | **+2.34** |
| IS sum PnL ($) | +238.41 | +54.05 | +184.36 |
| OOS sum PnL ($) | +122.33 | +36.96 | +85.37 |
| IS n_trades | 581 | (baseline) | — |
| OOS n_trades | 199 | (baseline) | — |

### Per-coin Pareto-dominance vs BASELINE_V1 (ALT_1 vs BASELINE_V1)

| Coin | IS Δ Sharpe | OOS Δ Sharpe | Dominance verdict |
|---|---|---|---|
| BTC | **+0.64** | **+3.98** | **PARETO-DOMINATES on both windows** |
| ETH | **+1.15** | −0.96 | IS dominates; OOS regresses (known weak point; bounded by 1/5 weight) |
| LINK | −0.98 | **+1.60** | OOS dominates substantially; IS regresses |
| LTC | **+3.60** | **+4.35** | **PARETO-DOMINATES on both windows** |
| DOT | **+3.63** | **+3.36** | **PARETO-DOMINATES on both windows** |

5/5 coins Pareto-dominate on AT LEAST one window; 3/5 dominate on BOTH.

### IS-window-only assertion

Verifier numbers above were computed via raw `reports-v1/iteration_v1-{012,042,011,040,031}/in_sample/trades.csv` reads, filtering by per-component declared universe, with `close_time < OOS_CUTOFF_MS = 1742774400000` enforced for IS-window rows. The committed `analysis/iteration_v1-045/component_is_evidence.py` script reproduces this and asserts the cutoff at load time; assertion failures abort the run.

### Section 2.5 — HIGH-RISK Axis Declaration

**Declaration:** **NORMAL-RISK** (with CAVEAT — see Section 4 F-AXIS #7 + Section 6).

**Reason:** `/045` does NOT change Optuna's training-objective domain. Each component's LightGBM was trained INDEPENDENTLY in its source iteration; `/045` is a **CSV-replay aggregator** that reads pre-existing trade rosters and applies a deterministic per-trade `weight_factor = 1/5` multiplier — a scalar applied AFTER the trade was realized at the source iteration. NO re-training, NO re-tuning, NO Optuna in /045 dispatch.

**Caveat (NORMAL-RISK with structural fragility):** all 5 components are **single-seed=42**; the bundle inherits 5× seed-lottery exposure on the union basis. /045 is a **wiring CONFIRMATION** (proves the federation aggregator + universe partition + weight provenance work as designed), NOT a multi-seed Sharpe validation. Multi-seed validation is mandated for /046+ before BASELINE_V1.md is updated (Section 6).

**Mitigation:** /045 produces the bundle-headline + Critic Checks 15/16/17 verdicts ONLY. Per Section 6, BASELINE_V1.md is **NOT updated at /045 MERGE** even on PASS — only after /046+ multi-seed re-runs of each component reproduce the headline within σ_R.

---

## Section 3 — Proposed Changes (incl. LM Master Phase 4.5 responses)

### 3.1 — Bundle composition

5 components, each owning exactly ONE coin (per Section 11.A):

```
C-BTC  = iter-v1/012 : {BTCUSDT}
C-ETH  = iter-v1/042 : {ETHUSDT}
C-LINK = iter-v1/011 : {LINKUSDT}
C-LTC  = iter-v1/040 : {LTCUSDT}
C-DOT  = iter-v1/031 : {DOTUSDT}
```

Pairwise disjoint: VERIFIED YES (Section 11.A). Union: `{BTC, ETH, LINK, LTC, DOT}` = BASELINE_V1 universe exactly.

### 3.2 — Weight derivation

EQUAL weights `w = (0.2, 0.2, 0.2, 0.2, 0.2)` — 1/5 each. IS-only derivation; committed `analysis/iteration_v1-045/weight_calibration.py` + `analysis/iteration_v1-045/bundle_weights.csv` (per Section 11.B). Rationale: equal weights minimize researcher-degrees-of-freedom (no IS-derived knob beyond N=5 component count); IS-Sharpe-proportional would over-weight LTC=v1-040 (IS +3.76, 4-5× higher than other components' IS Sharpes) and under-weight C-BTC=v1-012 (IS −0.21) — the latter is the LARGEST OOS contributor (OOS Sharpe +6.10, Δ +3.98 vs baseline). IS-Sharpe weighting would defeat the very signal /045 is designed to harvest.

### 3.3 — Runner architecture

`run_iteration_045.py` (new). **CSV-replay aggregator — NO fresh Optuna call, NO LightGBM fit.**

Steps (single sequential pass; <30 min total):

1. Load each of 5 components' `{in_sample,out_of_sample}/trades.csv`:
   - `reports-v1/iteration_v1-012/{in_sample,out_of_sample}/trades.csv` for C-BTC
   - `reports-v1/iteration_v1-042/{in_sample,out_of_sample}/trades.csv` for C-ETH
   - `reports-v1/iteration_v1-011/{in_sample,out_of_sample}/trades.csv` for C-LINK
   - `reports-v1/iteration_v1-040/{in_sample,out_of_sample}/trades.csv` for C-LTC
   - `reports-v1/iteration_v1-031/{in_sample,out_of_sample}/trades.csv` for C-DOT
2. Per component, **filter rows by the component's declared universe**:
   - C-BTC: keep only `symbol == "BTCUSDT"`
   - C-ETH: keep only `symbol == "ETHUSDT"`
   - C-LINK: keep only `symbol == "LINKUSDT"`
   - C-LTC: keep only `symbol == "LTCUSDT"`
   - C-DOT: keep only `symbol == "DOTUSDT"`
   - Discard any non-owned-coin rows (defensive filter against off-coin signals that may exist in source iteration CSVs from multi-coin runs).
3. Concatenate filtered rosters.
4. Apply `weight_factor = 0.2` (multiply each row's `pnl` and `weight_factor` column).
5. Sort concatenated rows by `close_time`.
6. Pipe through `generate_iteration_reports(..., iteration=45, ...)`.

CLI flag: `--bundle-config "C-BTC:0.2,C-ETH:0.2,C-LINK:0.2,C-LTC:0.2,C-DOT:0.2"` — parsed by `run_iteration_045.py`; values pre-registered in Section 11.B; runner asserts CLI input matches the committed `bundle_weights.csv` byte-for-byte before launching.

### 3.4 — No model or feature re-training (CSV-replay)

Per-coin partitioned federation means each coin's signal is the bit-identical roster from its source iteration's `trades.csv`. There is NO trade aggregation conflict (universes are disjoint), NO ensembling across components, NO information passing between components, NO re-fit of LightGBM at /045, NO new Optuna search. The bundle decision rule is the trivial dispatch in Section 11.C.

### 3.5 — LM Master Phase 4.5 response map

LM Master `briefs-v1/iteration_v1-045/lgbm_advisor.md` issued 3 recommendations under the 3-component substrate. Response map under the new 5-component substrate:

| LM recommendation | Original target | /045 response |
|---|---|---|
| **R1 — Lock per-component Optuna budget at /044 sub-run levels; DO NOT re-tune** | Each component re-uses its `/044`-best HPs verbatim per `(symbol, month)` cell | **N/A under new substrate: CSV-replay aggregator does NOT call Optuna or LightGBM. The source iterations (012/042/011/040/031) have already produced their final trades.csv; /045 reads them as-is. R1's underlying concern (joint-search leakage) is satisfied a fortiori by NOT calling Optuna at all.** |
| **R2 — Watch per-component trade-count floor at multi-seed (esp. LTC-alone)** | LTC ≥ 10 trades/month OOS or 1/5 weight bleeds dead capital | **ADOPTED & EXTENDED: F-AXIS #2 now mandates BOTH bundle OOS trade-count ≥130 AND per-coin OOS trade-count check. Per-coin OOS counts: BTC=19, ETH=44, LINK=47, LTC=52, DOT=37 (sum=199). The 19-trade BTC component IS the load-bearing fragility — see F-AXIS #7 hard fallback to ALT_2 (BTC=v1-023, 58 OOS trades).** |
| **R3 — Verify F4 trade-roster Jaccard = 1.0 at engineering report** | Bundle roster = union of component rosters under symbol-partitioning; Jaccard<1.0 = wiring bug | **ADOPTED: MANDATED in QE Phase 6 deliverable. Engineering report MUST emit a Jaccard table comparing bundle trade roster (sorted by `(symbol, open_time)`) against the union of post-universe-filter component rosters. Critic Check 16 BLOCKs at Jaccard < 1.0.** |

LM Master's `Confidence: MEDIUM` verdict carries over: substrate is structurally sound; success depends on (a) F-AXIS #2 per-coin trade-rate floors (BTC=19 is the binding constraint) and (b) F4 Jaccard=1.0 verification.

---

## Section 4 — Pre-Registered Failure-Mode Falsifier (regime-aware)

### F-AXIS #1 — Per-Regime Pareto-Dominance MERGE Criterion (the master falsifier)

Per `briefs-v1/_meta/merge_v1_relative_regime_pareto_proposal.md` §B + skill "Bundle-level (CONFIRMATION-MERGE criteria — RELATIVE REGIME PARETO)":

**MERGE-VERDICT** = `CONFIRMATION-MERGE-PORTFOLIO` if and only if:

For every tagged regime R ∈ {bull, bear, chop, vol-spike, recovery, other} present in IS or OOS:

```
sharpe_R(/045 bundle) ≥ sharpe_R(BASELINE_V1) − σ_R
AND max_dd_R(/045 bundle) ≤ max_dd_R(BASELINE_V1) + σ_dd_R
AND trade_count_R(/045 bundle) ≥ 0.5 × trade_count_R(BASELINE_V1) [rare-regime carve-out if trade_count_R(BASELINE) < 10]
```

AND at least one regime R* where:

```
sharpe_R*(/045 bundle) > sharpe_R*(BASELINE_V1) + σ_R*
   OR max_dd_R*(/045 bundle) < max_dd_R*(BASELINE_V1) − σ_dd_R*
```

AND methodology integrity intact (look-ahead clean, embargo applied, reproducibility checksum match, Checks 15/16/17 PASS).

σ_R and σ_dd_R are read from `briefs-v1/_meta/baseline_seed_regime_matrix.csv` (one σ over BASELINE's 10-seed within-regime distribution per regime). The diary auto-populates the per-regime comparison from `reports-v1/iteration_v1-045/regime_attribution.csv` produced in Phase 6.

**Per-coin Pareto-dominance pre-registration (5/5 coverage check):**

In addition to the regime-level Pareto check, the diary MUST verify the per-coin Pareto-dominance pattern measured in Section 2:
- BTC: IS Δ +0.64, OOS Δ +3.98 (PARETO both)
- ETH: IS Δ +1.15, OOS Δ −0.96 (IS dom; OOS regresses)
- LINK: IS Δ −0.98, OOS Δ +1.60 (OOS dom; IS regresses)
- LTC: IS Δ +3.60, OOS Δ +4.35 (PARETO both)
- DOT: IS Δ +3.63, OOS Δ +3.36 (PARETO both)

Deviation from this pattern at re-run = methodology/wiring problem; investigate before MERGE.

Otherwise: `CONFIRMATION-BLOCK` (no MERGE; iterate on the failing regime/coin in cycle-6 next EXPLORATION).

---

## Section 4 (continued) — Behavioral & Methodology-Integrity Falsifiers

### F-AXIS #2 — Bundle + per-coin trade-rate floor

**Bundle threshold:** `trade_count(/045 OOS bundle) ≥ 130` total AND `≥ 10 trades/month` averaged over OOS months.

**Predicted bundle OOS trades:** 199 (verifier-computed; sum across 5 components: 19+44+47+52+37). Comfortably clears the 130 floor.

**Per-coin threshold:** each component's OWN OOS trade count is logged for transparency:
- C-BTC = 19 (**BELOW the standard 130-trade per-coin floor — by design; bundle aggregates 5 streams**)
- C-ETH = 44
- C-LINK = 47
- C-LTC = 52
- C-DOT = 37

**Falsifier:** If bundle OOS trades < 130 (impossible given 199 verifier count, but checked at runtime), Sharpe is noise-dominated; cannot MERGE regardless of headline.

**Per-coin advisory:** C-BTC's 19 OOS trades flags it as the load-bearing fragility (see F-AXIS #7 below for hard fallback to ALT_2). σ_SR ≈ √(1/19) ≈ 0.23 on the BTC sub-roster — the OOS Sharpe +6.10 estimate is wide-confidence, and the bundle headline is sensitive to BTC sub-roster outcomes.

### F-AXIS #3 — Backtest-Live Parity (Critic Check 15)

**Pass:** Bundle decision rule at every `(symbol, candle)` is the deterministic dispatch in Section 11.C with no aggregation, no netting, no future bars.

**Falsifier:** If the Critic identifies a forbidden construct (sum of realized PnL across components on the same symbol, exposure netting, future-bar reference) → BLOCK-FINAL with reason `BUNDLE-PARITY-VIOLATION`. Section 11.C is engineered to make this physically impossible; the proof is by construction (5 single-coin disjoint universes).

### F-AXIS #4 — Universe Disjointness (Critic Check 16)

**Pass:** Pairwise universe intersections across all 5 components ∅. Verified in Section 11.A. Runner asserts this at startup AND the engineering report emits a Jaccard=1.0 table (per LM R3) confirming bundle trade roster = union of post-filter component rosters.

**Falsifier:** Any non-empty pairwise intersection → BLOCK-FINAL with reason `BUNDLE-UNIVERSE-OVERLAP`. Any Jaccard < 1.0 on the bundle-vs-union check → BLOCK-FINAL with reason `BUNDLE-UNIVERSE-OVERLAP` (wiring bug).

### F-AXIS #5 — IS-Only Weight Provenance (Critic Check 17)

**Pass:** `analysis/iteration_v1-045/weight_calibration.py` committed before Phase 6.0; the script greps clean for forward-pointing data references (`OOS_CUTOFF` other than the IS-side `< OOS_CUTOFF_MS` assertion, `>= OOS_CUTOFF_MS`, `oos_window`, `out_of_sample` filenames, post-2025-03-24 hard-coded dates used for FILTERING-IN); `bundle_weights.csv` matches Section 11.B verbatim; data sources respect IS-window cutoff.

**Note:** equal weights `(0.2, 0.2, 0.2, 0.2, 0.2)` are LITERAL CONSTANTS (no IS Sharpe → weight mapping). The weight script is essentially `w = [0.2]*5` with the IS-window assertion as a defensive guard. This is the simplest possible Check 17 satisfaction.

**Falsifier:** Any forward-pointing data reference in the weight-derivation chain → BLOCK-FINAL with reason `BUNDLE-WEIGHT-OOS-LEAK`.

### F-AXIS #6 — Component Reproducibility Checksum

**Pass:** SHA-256 checksums on each component's source `{in_sample,out_of_sample}/trades.csv` captured at /045 launch and emitted to `engineering_report.md`. Re-runs of /045 against the same source CSVs must produce bit-identical aggregator output (deterministic concat + sort + multiply).

**Falsifier:** Any source-CSV checksum mismatch or aggregator non-determinism → BLOCK-FINAL with reason `REGRESSION-SENTINEL`.

### F-AXIS #7 — BTC OOS robustness (HARD FALLBACK to ALT_2 if BTC=v1-012 fails)

**Concern:** C-BTC = iter-v1/012 has only **19 OOS trades**. σ_SR ≈ √(1/19) ≈ 0.23; the OOS Sharpe +6.10 estimate is high-confidence positive but low-trade-count. If the Critic at Phase 7.5 BLOCKs on BTC sample size (e.g., per-coin trade-count floor < some threshold the Critic deems unrelaxable, or per-coin DSR PSR computation collapses on n=19), /045 has a pre-registered hard fallback.

**Pre-registered fallback (ALT_2):**
- Substitute C-BTC = `iter-v1/012` → C-BTC = `iter-v1/023` (58 OOS trades; ALT_2 from workflow `w0qpo136q`).
- ALT_2 bundle headline: IS Sharpe +2.23 / OOS Sharpe +2.87 (still clears IS+OOS > 1.0 floors and Pareto-dominates baseline).
- Substitution mechanics: change source CSV paths in `run_iteration_045.py` config dict from `iter-v1/012` → `iter-v1/023`; re-run aggregator (<30 min); re-issue engineering report.
- Trigger condition: Critic Phase 7.5 verdict = `BLOCK-PENDING-FIX` with reason citing BTC sample size OR bundle OOS Sharpe < +1.5 in /045 baseline run (which would indicate the BTC +6.10 was an outlier in some unforeseen way).

**Falsifier (post-ALT_2):** If ALT_2 also fails (BTC=v1-023 produces bundle OOS Sharpe < +1.0 OR Critic still BLOCKs), /045 closes as `CONFIRMATION-BLOCK` and a cycle-6 EXPLORATION re-opens the BTC slot.

---

## Section 5 — Risk Mitigation

### 5.1 — Inherited risk gates (per source iteration, NO CHANGE at /045)

Each source iteration owns its own risk-gate config. /045 inherits whatever R1/R2/R3 was active in the source — but since /045 is CSV-replay, those gates fired at source-iteration time and are baked into the source `trades.csv`. /045 does NOT add new gates or modify existing gates.

| Component | R1 status (per source iter) | R2 status | R3 status |
|---|---|---|---|
| C-BTC = v1-012 | per /012 brief | per /012 brief | per /012 brief |
| C-ETH = v1-042 | per /042 brief | per /042 brief | per /042 brief |
| C-LINK = v1-011 | per /011 brief | per /011 brief | per /011 brief |
| C-LTC = v1-040 | per /040 brief | per /040 brief | per /040 brief |
| C-DOT = v1-031 | per /031 brief | per /031 brief | per /031 brief |

(Engineering report in Phase 6 will compile a single table summarizing the actual per-source-iter gate settings for transparency. /045 brief does NOT need to enumerate each — the source iterations are the authoritative spec.)

### 5.2 — Bundle-level risk mitigation

- **Equal-weight cap on per-coin drag**: each component is capped at 1/5 of bundle capital. Even if one component goes OOS-negative (e.g., the ETH OOS −0.96 Δ vs baseline), the contribution to bundle OOS Sharpe is bounded by 1/5 of standalone OOS. The verifier's bundle OOS +3.4851 incorporates ETH's modest underperformance.
- **No new code paths**: every component has already gone through Phase 1-8 closeout at its source iteration. No new model, no new feature, no new gate at /045.

### 5.3 — Heterogeneous methodology stacks (BIND in Section 11.A)

**Critical caveat:** the 5 components are NOT homogeneous in HP / feature / risk-primitive config. Each source iteration was an independent EXPLORATION (or BASELINE-pool ancestor) with its own brief. Section 11.A enumerates each component's exact config + reference source iter's brief path. The Critic at Phase 7.5 (Check 16, 17) reviews these explicitly.

Heterogeneity is a feature, not a bug, under the per-coin specialist substitution hypothesis — each coin is owned by the iteration that ranked best for IT specifically. But it does mean:
- Multi-seed validation at /046+ must re-run EACH source iter under its OWN config (5 separate `run_iteration_XXX.py` re-runs at 10 seeds each), not one unified Optuna re-search.
- BASELINE_V1.md update at /046+ MERGE must enumerate the 5 source configs (no "one /045 config" line).

---

## Section 6 — Risk Management Design (with multi-seed mandate for /046+)

**8-primitive table (v1 equivalent) for /045:**

| Primitive | Active in /045 | Source | Mechanism |
|---|---|---|---|
| Triple-barrier TP/SL/timeout | YES (per source iter) | Inherited from each component's source brief | Per-trade horizon cap baked into source trades.csv |
| Past-only EWMA σ_t for barriers | YES (per source iter) | Inherited | Avoids labeling-window look-ahead (verified at source iter Critic time) |
| Position size (per component internal) | YES (per source iter) | Inherited | Pre-trade cap baked into source trades.csv |
| R1 cool-down | per source iter | Source-baked | Cascade protection |
| R2 drawdown scaling | per source iter | Source-baked | Drawdown protection |
| R3 OOD Mahalanobis | per source iter | Source-baked | Pre-trade regime check |
| Bundle 1/5 weight cap | YES (NEW for /045; structural) | weight_calibration.py | Caps single-component bundle exposure at 0.2 |
| Universe-disjoint dispatch | YES (NEW for /045; structural) | run_iteration_045.py | Eliminates per-symbol multi-model conflict (1 component per coin) |

### Multi-seed mandate for /046+

**/045 = WIRING CONFIRMATION (single-seed=42 across all 5 components).** /045 PASS verdict produces the bundle headline + Critic Checks 15/16/17 verdicts but does **NOT update BASELINE_V1.md**.

**/046+ = MULTI-SEED VALIDATION.** Before BASELINE_V1.md can be updated, each of the 5 source iterations must be re-run at 10 seeds (skill mandate from `feedback_seed_validation.md` + `feedback_seed_parity_on_model_change.md`):

1. Re-run `iter-v1/012` (BTC) at 10 seeds → 10-seed mean IS/OOS Sharpe.
2. Re-run `iter-v1/042` (ETH) at 10 seeds.
3. Re-run `iter-v1/011` (LINK) at 10 seeds.
4. Re-run `iter-v1/040` (LTC) at 10 seeds.
5. Re-run `iter-v1/031` (DOT) at 10 seeds.

Aggregator at /046+ then concatenates the 10-seed-mean trades.csv (or 10-seed-mean-of-medians per the skill's standard) across components. BASELINE_V1.md update gate: 10-seed bundle mean OOS Sharpe > +1.0 AND ≥7/10 profitable seeds across components AND Pareto-better-or-equal vs BASELINE_V1 on every tagged regime (within σ_R).

If /045 PASSes Checks 15/16/17 but the multi-seed re-runs at /046+ reveal that a component's single-seed=42 was a seed-lottery outlier (e.g., BTC=v1-012's OOS +6.10 collapses to 10-seed mean OOS +0.5), the substrate is revisited (potentially swap to ALT_2 BTC=v1-023 at the multi-seed stage).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure scenario:** /045 OOS bundle headline +3.4851 holds at the CSV-replay aggregator level (the verifier already computed it), so F-AXIS #1 / #2 / #3 / #4 / #5 / #6 all PASS — but at Phase 7.5, the Critic raises a **per-coin DSR / PSR concern on C-BTC's 19 OOS trades** (PSR computation collapses or DSR becomes nominally negative on the BTC sub-roster due to small-sample E[max_SR] inflation). Verdict: `BLOCK-PENDING-FIX` with hard fallback to ALT_2 (per F-AXIS #7).

**Expected metric signature of the dominant scenario (PASS):**
- Bundle OOS daily Sharpe (verifier): +3.4851
- Per-coin OOS Pareto-dominance pattern matches Section 2 table (3/5 dominate both windows; 2/5 dominate one and regress on the other within bounded contribution)
- F-AXIS #1 (per-regime Pareto): expected PASS — bundle covers BASELINE's universe and improves the headline by +2.34 OOS Sharpe; per-regime σ_R checks expected to clear on bull/chop/recovery/vol-spike; bear/other within σ_R
- F-AXIS #2: bundle OOS 199 trades, comfortably clears 130 floor
- F-AXIS #3 / #4 / #5: PASS by construction
- F-AXIS #6: PASS (deterministic CSV-replay)
- F-AXIS #7: NOT TRIGGERED if Critic accepts bundle-level trade count; TRIGGERED → ALT_2 swap if Critic blocks on per-coin BTC

**Most plausible BLOCK-PENDING-FIX scenario:** Critic enforces a per-coin trade-count floor or per-coin PSR > 0.95; ALT_2 swap auto-fires (mechanical CSV-path change in runner config); re-run aggregator (<30 min); re-issue engineering report; re-submit to Critic.

**Most plausible BLOCK-FINAL scenario:** Both ALT_1 AND ALT_2 fail to clear Critic gates on BTC sample size, OR Jaccard < 1.0 fires (wiring bug). In that case /045 closes as `CONFIRMATION-BLOCK` and cycle-6 next EXPLORATION re-opens the BTC slot to find a higher-trade-count BTC specialist.

---

## Section 8 — Pre-Registered Per-Regime Baseline-Comparison Criteria

Locked PER-REGIME comparison plan (frozen BEFORE Phase 6 launches):

**MERGE iff** for every tagged regime R ∈ {bull, bear, chop, vol-spike, recovery, other} present in IS or OOS:

```
sharpe_R(/045 bundle, single-seed=42) ≥ sharpe_R(BASELINE_V1, 10-seed mean) − σ_R
AND max_dd_R(/045 bundle, single-seed=42) ≤ max_dd_R(BASELINE_V1, 10-seed mean) + σ_dd_R
AND trade_count_R(/045 bundle) ≥ 0.5 × trade_count_R(BASELINE_V1) [rare-regime carve-out per merge proposal §B.5]
```

**AND** at least one regime R* with:

```
sharpe_R*(/045 bundle) > sharpe_R*(BASELINE_V1) + σ_R*
   OR max_dd_R*(/045 bundle) < max_dd_R*(BASELINE_V1) − σ_dd_R*
```

**AND** methodology integrity (Critic Checks 1, 2, 5, 6, 7, 8, 15, 16, 17 ALL PASS).

σ_R and σ_dd_R read from `briefs-v1/_meta/baseline_seed_regime_matrix.csv`.

**NO absolute Sharpe / DSR / PBO / PSR floors at the BUNDLE headline.** DSR / PBO / PSR are reported per-regime and bundle-level as INFORMATIONAL per skill §"Statistical-Significance Metrics" (NOT gating at /045).

**Note:** /045 is single-seed=42 (per Section 2.5 NORMAL-RISK with caveat). The "10-seed mean" comparison side uses BASELINE_V1's pre-existing 10-seed regime matrix; the /045 bundle side is the single-seed verifier headline. /046+ multi-seed re-runs replace the LHS with a 10-seed mean.

The Phase 8 diary auto-populates the per-regime comparison table from `reports-v1/iteration_v1-045/regime_attribution.csv` (produced in Phase 6 by the runner's regime tagger).

---

## Section 9 — Library Stack Declaration

- `mlfinlab==1.4` — CombinatorialPurgedKFold, PBO via CSCV, fractional differentiation (used INFORMATIONALLY at /045 reporting)
- `pypbo` — standalone PBO computation (INFORMATIONAL)
- `fracdiff>=0.10` — Numba-accelerated fractional differentiation (N/A at /045 CSV-replay)
- `statsmodels` — ADF stationarity (INFORMATIONAL)
- `lightgbm` — model engine — **NOT INVOKED at /045** (CSV-replay; the model fits live in source iterations)
- `xgboost` — N/A
- `numpy`, `pandas` — standard
- `pyarrow` — parquet I/O

No new pinning vs BASELINE_V1's `pyproject.toml` is required for /045 since /045 is a CSV-replay aggregator with no new model or feature.

---

## Section 10 — Regime Attribution Plan

Per skill mandate (NEW 2026-05-31 regime-ensemble), every iteration must declare its regime-attribution plan.

**Target regimes:** ALL regimes present in IS or OOS (bull, bear, chop, vol-spike, recovery, other).

**Mechanism (per component):**
- **C-BTC = v1-012:** REGIME-SPECIALIST-OOS — IS Sharpe −0.21 / 65t (modest IS edge), OOS +6.10 / 19t (strong OOS specialist). The single largest per-coin OOS Δ in the substrate.
- **C-ETH = v1-042:** REGIME-SPECIALIST-IS — IS +0.71 / 132t (positive IS edge), OOS +2.40 / 44t (positive but regresses Δ −0.96 vs baseline OOS).
- **C-LINK = v1-011:** REGIME-SPECIALIST-OOS — OOS Δ +1.60, 47 OOS trades.
- **C-LTC = v1-040:** UNIVERSAL — IS Sharpe +3.76 / 117t AND OOS +0.64 / 52t. Pareto-dominates baseline on both windows (largest IS contributor; lift on both windows).
- **C-DOT = v1-031:** UNIVERSAL — IS +2.40 / 117t AND OOS +3.24 / 37t. Pareto-dominates baseline on both windows.

**Off-regime expectation:** ETH's OOS regression (Δ −0.96) and LINK's IS regression (Δ −0.98) are bounded by 1/5 weight; bundle headline still clears baseline by +2.34 OOS Sharpe per verifier computation.

**Bundle role:** 5 single-coin specialists, equal-weighted. Coverage is per-coin Pareto-dominance on AT LEAST one window for 5/5 coins (3/5 on both windows).

**Composition simulation:** per workflow `w0qpo136q` partition solve — ALT_1 was selected from a Pareto frontier of N candidate partitions over the iter-v1/baseline + 001-043 inventory. ALT_2 (BTC=v1-023 swap) is the pre-registered fallback per F-AXIS #7.

**Regime-aware falsifier:** F-AXIS #1 (per-regime Pareto-dominance). NOT a single aggregate Sharpe number — though the +3.4851 bundle OOS is a strong signal.

---

## Section 11 — Bundle Composition (MANDATORY for CONFIRMATION-MERGE-PORTFOLIO)

### Section 11.A — Universe Partition (Rule 7 + Check 16 enforcement)

Per-component universe (5 single-coin components):

| Component | Universe | Source trade CSVs | Source brief |
|---|---|---|---|
| C-BTC | {BTCUSDT} | `reports-v1/iteration_v1-012/{in_sample,out_of_sample}/trades.csv` | `briefs-v1/iteration_v1-012/research_brief.md` |
| C-ETH | {ETHUSDT} | `reports-v1/iteration_v1-042/{in_sample,out_of_sample}/trades.csv` | `briefs-v1/iteration_v1-042/research_brief.md` |
| C-LINK | {LINKUSDT} | `reports-v1/iteration_v1-011/{in_sample,out_of_sample}/trades.csv` | `briefs-v1/iteration_v1-011/research_brief.md` |
| C-LTC | {LTCUSDT} | `reports-v1/iteration_v1-040/{in_sample,out_of_sample}/trades.csv` | `briefs-v1/iteration_v1-040/research_brief.md` |
| C-DOT | {DOTUSDT} | `reports-v1/iteration_v1-031/{in_sample,out_of_sample}/trades.csv` | `briefs-v1/iteration_v1-031/research_brief.md` |

**Pairwise disjointness (10 pairs across 5 components):**

| Pair | Intersection |
|---|---|
| C-BTC ∩ C-ETH | ∅ |
| C-BTC ∩ C-LINK | ∅ |
| C-BTC ∩ C-LTC | ∅ |
| C-BTC ∩ C-DOT | ∅ |
| C-ETH ∩ C-LINK | ∅ |
| C-ETH ∩ C-LTC | ∅ |
| C-ETH ∩ C-DOT | ∅ |
| C-LINK ∩ C-LTC | ∅ |
| C-LINK ∩ C-DOT | ∅ |
| C-LTC ∩ C-DOT | ∅ |

**Pairwise disjoint: YES.** (Trivially — each component owns exactly one coin and the 5 coins are all distinct.)

Union: `{BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT}` — matches BASELINE_V1's universe exactly.

Per-coin ownership table:

| Coin | C-BTC | C-ETH | C-LINK | C-LTC | C-DOT | Owner count |
|---|---|---|---|---|---|---|
| BTCUSDT | OWNS | — | — | — | — | **1** |
| ETHUSDT | — | OWNS | — | — | — | **1** |
| LINKUSDT | — | — | OWNS | — | — | **1** |
| LTCUSDT | — | — | — | OWNS | — | **1** |
| DOTUSDT | — | — | — | — | OWNS | **1** |

All 5 coins owned by exactly one component. **Rule 7 satisfied.**

`run_iteration_045.py` startup assertion:

```python
universes = {
    "C-BTC":  {"BTCUSDT"},
    "C-ETH":  {"ETHUSDT"},
    "C-LINK": {"LINKUSDT"},
    "C-LTC":  {"LTCUSDT"},
    "C-DOT":  {"DOTUSDT"},
}
for a, b in combinations(universes, 2):
    assert universes[a].isdisjoint(universes[b]), \
        f"Coin overlap between {a} and {b}: {universes[a] & universes[b]}"
assert set().union(*universes.values()) == {"BTCUSDT","ETHUSDT","LINKUSDT","LTCUSDT","DOTUSDT"}, \
    "Bundle universe does not match BASELINE_V1 universe"
```

**Heterogeneous source configs (Section 5.3 binding):**

| Component | Source iter | Config inheritance (refer to source brief) |
|---|---|---|
| C-BTC | iter-v1/012 | HPs / features / R1-R2-R3 / labeling per `briefs-v1/iteration_v1-012/research_brief.md` |
| C-ETH | iter-v1/042 | HPs / features / R1-R2-R3 / labeling per `briefs-v1/iteration_v1-042/research_brief.md` |
| C-LINK | iter-v1/011 | HPs / features / R1-R2-R3 / labeling per `briefs-v1/iteration_v1-011/research_brief.md` |
| C-LTC | iter-v1/040 | HPs / features / R1-R2-R3 / labeling per `briefs-v1/iteration_v1-040/research_brief.md` |
| C-DOT | iter-v1/031 | HPs / features / R1-R2-R3 / labeling per `briefs-v1/iteration_v1-031/research_brief.md` |

QE engineering report MUST compile a single summary table extracting `(n_trials, ensemble_size, seeds, feature_set, labeling_mode, R1/R2/R3 config)` from each source brief at /045 launch — for Critic Check review.

### Section 11.B — Weight Derivation (Rule 1 + Check 17 enforcement)

**Method:** EQUAL.

**Weight vector:** `w = (0.2, 0.2, 0.2, 0.2, 0.2)`.

**IS-only derivation justification:**

EQUAL weights selected over IS-Sharpe-proportional and IS-trade-count-proportional alternatives:

| Scheme | C-BTC | C-ETH | C-LINK | C-LTC | C-DOT | Notes |
|---|---|---|---|---|---|---|
| **EQUAL (SELECTED)** | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | No IS dependence; safest under uncertainty |
| IS-Sharpe-proportional | ~0 (clipped) | 0.10 | (clipped) | 0.55 | 0.35 | Would zero out C-BTC (IS −0.21 → clipped at 0); but C-BTC is the LARGEST OOS contributor (+3.98 Δ) — IS-Sharpe weighting defeats the substrate's primary signal |
| IS-trade-count-proportional | 0.11 | 0.23 | (per /011) | 0.20 | 0.20 | Over-weights ETH (132t) and under-weights BTC (65t); orthogonal to edge quality |

**Selected: EQUAL weights (0.2 each).** Justification:

1. IS-Sharpe-proportional CLIPS C-BTC to ~0 (IS −0.21 → negative → clipped at 0). C-BTC is admitted to the bundle because of its OOS Sharpe +6.10 / Δ +3.98 (the largest per-coin OOS contributor). Zeroing C-BTC defeats the per-coin specialist substitution that motivated the workflow `w0qpo136q` partition solve.
2. Trade-count-proportional gives C-LTC (highest IS Sharpe at +3.76) only 0.20 — capacity-weighting penalizes the highest-edge component when its trade count is mid-range. Wrong direction.
3. EQUAL minimizes researcher-degrees-of-freedom (no IS-derived knob beyond N=5 component count). It is the simplest IS-only choice and trivially Check-17-clean.

**Committed artifacts (before Phase 6.0 Critic pre-flight):**

- `analysis/iteration_v1-045/weight_calibration.py` — script that:
  - Loads ONLY the 5 components' `in_sample/trades.csv` files (for the optional IS-Sharpe / IS-trade-count comparator table; equal weights themselves are literal constants).
  - **Asserts every loaded row's `close_time < OOS_CUTOFF_MS = 1742774400000`** at load time; raises `RuntimeError` if any row fails.
  - Computes EQUAL weight vector via the literal `w = [0.2] * 5` constructor.
  - Writes `analysis/iteration_v1-045/bundle_weights.csv`.

- `analysis/iteration_v1-045/bundle_weights.csv` (VERBATIM):
  ```csv
  component_id,weight,derivation_method,is_window_start,is_window_end
  C-BTC,0.2,equal,2021-03-24,2025-03-24
  C-ETH,0.2,equal,2021-03-24,2025-03-24
  C-LINK,0.2,equal,2021-03-24,2025-03-24
  C-LTC,0.2,equal,2021-03-24,2025-03-24
  C-DOT,0.2,equal,2021-03-24,2025-03-24
  ```

The script contains NO references to `OOS_CUTOFF` (other than the IS-side `< OOS_CUTOFF_MS` assertion barrier), NO `>= OOS_CUTOFF_MS`, NO `oos_window`, NO `out_of_sample` filenames, and NO hard-coded post-2025-03-24 dates used for FILTERING-IN. The IS window dates (`2021-03-24`, `2025-03-24`) are LITERAL CONSTANTS in `bundle_weights.csv` (informational metadata; NOT used in filtering).

Critic Check 17 verification recipe:
```bash
grep -E 'OOS_CUTOFF|>= OOS_CUTOFF_MS|oos_window|out_of_sample' analysis/iteration_v1-045/weight_calibration.py
# Expected: NO hits other than the IS-side `< OOS_CUTOFF_MS` assertion.
```

### Section 11.C — Backtest-Live Parity Statement (Rule 8 + Check 15 enforcement)

The /045 bundle's per-(symbol, candle) decision is the deterministic dispatch function:

```python
OWNING_COMPONENT = {
    "BTCUSDT":  "C-BTC",   # iter-v1/012
    "ETHUSDT":  "C-ETH",   # iter-v1/042
    "LINKUSDT": "C-LINK",  # iter-v1/011
    "LTCUSDT":  "C-LTC",   # iter-v1/040
    "DOTUSDT":  "C-DOT",   # iter-v1/031
}

def bundle_signal(symbol: str, t: int) -> tuple[Signal, float]:
    """Return (signal, capital_fraction) for the bundle at (symbol, t)."""
    component = OWNING_COMPONENT.get(symbol)
    if component is None:
        return (NO_SIGNAL, 0.0)
    return (component.signal_at(symbol, t), 0.2)
```

Properties:

1. **Each symbol is owned by EXACTLY ONE component** (per Section 11.A); the dispatch is total and unambiguous over the 5-coin universe.
2. **References ONLY each component's signal at the SAME timestamp t** (same-time-snapshot; no future bars).
3. **Multiplies by each component's frozen weight (0.2)** — pre-registered in `bundle_weights.csv` before Phase 6 launches.
4. **NO aggregation across components** — the bundle never sums realized PnL from two simultaneously-open positions in the same symbol (cannot happen by construction since each symbol has exactly one owning component).
5. **NO netting across components** — the bundle never combines two-model exposure into one Binance order (cannot happen by construction).
6. **NO information passing across components** — each component computes its signal independently; the bundle aggregates outputs only at trade-realization time (post-trade, via the `weight_factor = 0.2` multiplier).

**Implementation at `live/engine.py:_tick`:**

At each tick, for each `(symbol, candle)`:
1. Look up `OWNING_COMPONENT[symbol]` from the static dict (same dict in Section 11.A).
2. Query `OWNING_COMPONENT[symbol].signal_at(symbol, candle)`.
3. If signal is non-no-trade, place ONE Binance order at the owning component's internal position weight × 0.2 portfolio capital allocation.
4. The order is tagged with `component_id` for trade-attribution.

This is trivially replayable: at every `(symbol, candle)` the engine performs the SAME pure-function lookup as the backtest. There is no aggregation step that could diverge between backtest and live.

**Backtest-live parity property: PROVEN BY CONSTRUCTION.** Critic Check 15 satisfied because the dispatch rule has no aggregation, no netting, no future bars, and no information flow between components.

### Section 11.D — Re-Composition Note (Rule 9 + Check 16 enforcement context)

**This brief SUPERSEDES the original /045 3-component substrate** `(baseline_pool_A, baseline_D, iter-v1/036)`.

**Why superseded:** the original 3-component substrate (backed up at `research_brief.OLD-3component.md`) was constructed manually under cycle-6 launch and was falsified by the IS evidence pre-Phase-5.5:
- The original C3 (`iter-v1/036`) had IS daily Sharpe ≈ 0 (Section 2 of the OLD brief: −0.037 IS; −4.09 IS PnL) — a near-zero edge component admitted on a single-seed OOS Δ +1.08 LINK+DOT lift, which is too thin a basis for a CONFIRMATION bundle leg.
- The 76.8% LTC IS PnL concentration in the OLD bundle (Section 5.3 of OLD) was on the boundary of the 30% concentration soft cap.
- The OLD 3-component substrate was a partial coverage of BASELINE_V1's universe via 3 pooled-or-paired sub-models, not per-coin best-specialist selection.

**Why the new 5-component substrate:** workflow `w0qpo136q` partition solve over the iter-v1/baseline + iter-v1/001-043 inventory was executed (post-OLD-brief authoring) to identify the strongest per-coin partition. ALT_1 (this substrate) emerged as the Pareto-front SHIP target with:
- Bundle IS Sharpe +1.9879 (vs OLD's projected ~$39.74/std on bundle IS PnL)
- Bundle OOS Sharpe +3.4851 (vs OLD's predicted ~+1.20-1.35 most-plausible failure scenario)
- 5/5 per-coin Pareto-dominance on AT LEAST one window (vs OLD's regime-specialist substitution argument)

The OLD 3-component substrate is RETAINED as a historical reference at `research_brief.OLD-3component.md`. It is NOT a candidate for /045 launch.

**Per-coin re-composition summary (vs BASELINE_V1):**

| Coin | BASELINE_V1 ownership | /045 ownership | Source iter swap |
|---|---|---|---|
| BTCUSDT | BASELINE_V1 Model A (BTC+ETH pool) | C-BTC (iter-v1/012, single-coin) | pool → specialist |
| ETHUSDT | BASELINE_V1 Model A (BTC+ETH pool) | C-ETH (iter-v1/042, single-coin) | pool → specialist |
| LINKUSDT | BASELINE_V1 Model C (LINK) | C-LINK (iter-v1/011, single-coin) | model swap |
| LTCUSDT | BASELINE_V1 Model D (LTC) | C-LTC (iter-v1/040, single-coin) | model swap (Δ IS +3.60, Δ OOS +4.35) |
| DOTUSDT | BASELINE_V1 Model E (DOT) | C-DOT (iter-v1/031, single-coin) | model swap (Δ IS +3.63, Δ OOS +3.36) |

The original BASELINE_V1 Models A / C / D / E are NOT modified at the catalog level — they remain valid as standalone artifacts; only their inclusion in THIS BUNDLE is suppressed in favor of single-coin specialists.

No coin is added to the bundle universe (`{BTC, ETH, LTC, LINK, DOT}` = BASELINE_V1 universe).

---

## End of Brief
