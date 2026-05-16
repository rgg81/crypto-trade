# iter-v3/083 — Cycle 3 #2 EXPLORATION / symbol-universe EXPANSION 3→4 (add FILUSDT, Direction 2) / NEGATIVE

**Date**: 2026-05-16
**Type**: EXPLORATION (cycle 3 #2 of 10 — single-axis: `V3_MODELS` 3→4 by adding FILUSDT; the 14-feature anchor stack, ATR labeling `(2.0, 1.0)`, the 7-primitive risk-gate stack, `ENSEMBLE_SEEDS`, the Optuna search all UNCHANGED)
**Axis**: Direction 2 of `briefs-v3/cycle3_plan.md` — symbol-universe EXPANSION (denominator expansion, distinct from the CLOSED swap-by-replacement family). `V3_MODELS` grows BCH/LDO/TRX → BCH/LDO/TRX/**FIL**. FILUSDT was selected by the committed EDA `analysis/iteration_v3-083/universe_expansion_edge_screen.py` (SHA `e538d5f`) — rank #1 of 4 survivors (best standalone IS edge, least-harmful aggregate-IS-Sharpe delta, duration-clean, deepest liquidity). Mandatory secondary edit: `V3_FEATURE_COLUMNS_TOP_N` reverted 18→14 (drop the /082 INERT funding family per `feedback_v3_inert_features_at_higher_budget.md`). `REQUIRED_GAP` recomputed 66→88 = (21+1)×4. EXPLORATION-mode 3-seed, `--n-trials 35`. Anchor: BASELINE_V3.md `v0.v3-059` (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791), re-validated at the iter-v3/081 CONFIRMATION.
**Verdict**: EXPLORATION-MERGE per Critic FINAL `1116124` — OVERALL=MERGE = methodology certified clean; result-read **NEGATIVE** (the Critic's recommended result-read, adopted here as FINAL). A closeout-integrity / methodology certification, NOT an advancement: a NEGATIVE axis never advances to the CONFIRMATION bundle.
**Classification**: **NEGATIVE** per the LOCKED brief Section 8.2 — IS monthly Sharpe Δ = **−0.9156** vs /059 (IS +0.1738 vs anchor +1.0894), far below the −0.10 NEGATIVE floor; brief Section 4.2 Falsifier #1 ("IS monthly Sharpe Δ < −0.20 → the /021 HBAR/AVAX failure mode reproduced") FIRED decisively. SUSPICIOUS does not fire (see Section 5). The disjunctive precedence SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL-RESULT lands on NEGATIVE.
**Advancement**: does NOT advance to the iter-v3/092 cycle-3 CONFIRMATION bundle. FILUSDT is NOT carried forward — universe expansion with FIL produced an aggregate IS collapse, not the denominator-expansion structural fix the brief hypothesized.
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791; tag `v0.v3-059`). An EXPLORATION cannot update the baseline, and a NEGATIVE EXPLORATION produces no edge ingredient regardless. The only BASELINE_V3.md edit at this closeout is documentation: the universe-expansion-with-FILUSDT outcome added to Dead Ideas.
**Branch**: `iteration-v3/083`

---

## 1. What was done

iter-v3/083 is the SECOND EXPLORATION of v3 cycle 3 — the bold structural pivot mandated by `feedback_v3_bold_research_mandate.md` + `feedback_v3_mass_feature_expansion.md` and governed by `briefs-v3/cycle3_plan.md`. Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 3 runs 10 SEPARATE EXPLORATIONs (/082-/091) followed by 1 SEPARATE CONFIRMATION (/092) — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The axis is a **single-axis symbol-universe EXPANSION** — Direction 2 of the cycle-3 plan, strongly preferred per the /082 closeout (Critic Rec #3: "no feature-family axis can fix the 3-symbol denominator problem"). `V3_MODELS` grows from 3 symbols (BCHUSDT, LDOUSDT, TRXUSDT) to 4 by adding FILUSDT:

```python
V3_MODELS = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
    ("F (FILUSDT)", "FILUSDT"),   # <- /083 single axis
)
```

This is **denominator expansion** — the Fundamental Law (IR = IC·√breadth, Grinold & Kahn 1999) names breadth as the lever v3 has never pulled. It is structurally distinct from the CLOSED swap-by-replacement family (/078 swapped LDO→ADA at constant count and loaded the regime factor via the added symbol's roster) — every incumbent is kept; FIL is added. FIL gets one independent per-symbol LightGBM model with the same 14-feature stack, the same `(2.0,1.0)` ATR triple-barrier labeling, and the same 7-gate risk stack as every incumbent (a **universal** addition; `feedback_v3_per_symbol_lifts_oos_breaks_is.md` is satisfied — no per-symbol features, no per-symbol ATR, no per-symbol gates).

Two mandatory secondary edits, both established baseline-restore patterns (cf. /077 reverting /076's `range_efficiency_50`, /079 reverting /078's ADA swap):
- **`V3_FEATURE_COLUMNS_TOP_N` 18→14** — drop the /082 funding family. /082 closed SUSPICIOUS-OOS-DOMINANT with the funding family ranked bottom-4/18 by importance; per `feedback_v3_inert_features_at_higher_budget.md` an INERT feature family must NOT be carried forward and must NOT be retested at higher budget. Restores the /059 canonical 14-feature anchor stack, so /083's sole declared delta vs /059 is the universe expansion.
- **`REQUIRED_GAP` 66→88** — the pooled-CPCV purge gap = `(timeout_candles+1)×n_symbols = (21+1)×4 = 88`. The runtime `_verify_label_leakage_gap()` assertion confirmed it; the `expected_gap` self-assertion at `_compute_cpcv_paths` makes a stale 66 impossible.

Nothing else is touched — no labeling change, no risk-gate change, no model-architecture change, no seed change, no Optuna-search change.

The axis is QR-research-and-EDA-driven per `feedback_v3_axis_selection_quant_discipline.md` and the cycle-3 research mandate: brief Section 10 documents the genuine literature path (Grinold & Kahn *Active Portfolio Management* 1999 — the Fundamental Law; Cakici et al. *International Review of Financial Analysis* 94 (2024) / SSRN 4295427 — crypto-ML cross-section, simple-models-beat-complex; XBTO 2025 institutional diversified-crypto practice). The committed EDA `analysis/iteration_v3-083/universe_expansion_edge_screen.py` (SHA `e538d5f`) screened 8 deep-history liquid large-cap candidates and selected FILUSDT — rank #1 of 4 survivors.

Run mode: EXPLORATION (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, `ENSEMBLE_SEEDS` outer-42 lineage subset `[191664963, 1662057957, 1405681631]`), `--n-trials 35`, 4-symbol universe, `REQUIRED_GAP = 88`, embargo 22. Total 420 Optuna trials (35 × 4 sym × 3 seeds). Wall-clock 1.00h, within the 2h EXPLORATION cap.

Commit chain: EDA `e538d5f` → research brief `36c7630` → setup `c5f6456` → brief SHA-backfill `8eafb4d` → Phase 5.5 gate PASS `21defda` → Phase-6 setup (fetch+regen 4-symbol parquets + stale-test fixes) `17ef604` → engineering report `6479e88` → Critic review `1116124`.

## 2. Results — vs the BASELINE_V3.md /059 anchor (IS +1.0894 / OOS +0.5791)

| Metric | /059 anchor | /083 actual | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+1.0894** | **+0.1738** | **−0.9156** |
| OOS monthly Sharpe | **+0.5791** | **+0.4394** | **−0.1397** |
| OOS/IS monthly Sharpe ratio | 0.5316 | **2.5276** | — |
| IS daily Sharpe | 2.7092 | 0.3996 | — |
| OOS daily Sharpe | 1.4359 | 1.0029 | — |
| IS MaxDD | 30.97% | **73.18%** | **+42.21pp** |
| OOS MaxDD | 34.53% | 33.58% | −0.95pp |
| IS n_trades | 171 | 219 | +48 |
| OOS n_trades | 94 | 131 | +37 |
| IS profit_factor | 1.4949 | 1.0585 | −0.436 |
| OOS profit_factor | 1.2107 | 1.1289 | −0.082 |
| PBO mean | 0.1278 | 0.1392 | +0.011 (PASS < 0.40) |
| PSR | 1.0 | 1.0000 | PASS (> 0.95) |
| DSR (legacy) | 0.0 | 0.0000 | EXPLORATION-mode artifact (informational) |
| DSR_relative_B4 | — | 1.0000 | EXPLORATION-mode artifact (informational) |
| frac_positive_paths (CPCV) | 0.6444 | **0.4667** | **FAIL** (< 0.55) |
| n_trials (Optuna total) | 1050 | 420 | EXPLORATION-mode (3 seeds) |
| n_eff | 19 | 19 | architecture-independent |

CPCV path Sharpe distribution: q25 = −0.706, q50 = **−0.079** (median path negative), q75 = +0.440. 21 of 45 CPCV paths positive. The CPCV gate FAIL (`frac_positive_paths` 0.4667 < 0.55) and the median negative path corroborate the NEGATIVE classification — they are a result signal, not a methodology defect (the CPCV computation is sound: 45 paths from C(10,2), pooled 4-symbol candle sequence, `gap=88` correctly purged and symmetrically applied).

**Per-symbol IS attribution** (report-layer `in_sample/per_symbol.csv`, `net_pnl_pct`):

| Symbol | IS trades | IS WR | IS net_pnl% | IS avg_pnl% |
|---|---:|---:|---:|---:|
| BCHUSDT | 73 | 45.2% | **+79.45** | +1.09 |
| FILUSDT | 60 | 36.7% | **−32.45** | −0.54 |
| LDOUSDT | 11 | 27.3% | **−11.44** | −1.04 |
| TRXUSDT | 75 | 29.3% | **−23.04** | −0.31 |

**Per-symbol OOS attribution** (`comparison.csv` per_symbol block, `weighted_pnl`):

| Symbol | OOS weighted_pnl | OOS n_trades | OOS WR | OOS concentration_pct |
|---|---:|---:|---:|---:|
| TRXUSDT | +24.0798 | 55 | 47.3% | 121.92% |
| FILUSDT | +6.3410 | 27 | 40.7% | 32.11% |
| BCHUSDT | +1.9078 | 37 | 32.4% | 9.66% |
| LDOUSDT | −12.5778 | 12 | 25.0% | −63.68% |

**The headline.** IS collapsed −0.9156 (from +1.0894 to +0.1738). OOS slipped −0.1397 (from +0.5791 to +0.4394). The IS collapse is the dispositive signal: an IS monthly Sharpe of +0.17 is economically broken; the 73.18% IS MaxDD (vs /059's 30.97%) is the second corroborator. Only BCH carries a positive IS contribution — FIL, LDO and TRX are all net-negative IS, producing a near-zero +12.52 net IS PnL (the 4-symbol report-layer sum). The structural target — BCH OOS concentration dilution — is moot under a collapsed-aggregate result.

## 3. The decomposition — how much of −0.9156 is FIL-own vs incumbent-drift (Critic Rec #1, the core analytical task)

The engineering report's "Core Diagnostic" attributed the incumbent damage to FIL "reshaping the Optuna landscape for all 3 incumbents." **The Critic traced the runner code and found this is mechanistically false** — see Section 9 for the corrected mechanism. The correct decomposition is below.

**The unit.** The brief Section 4.3 falsifier band is specified in "combined IS weighted_pnl Δ." The report-layer `in_sample/per_symbol.csv` `net_pnl_pct` field is the per-symbol IS PnL figure carried in all v3 prior diaries and is the figure the brief's T3 screen used as the IS contribution proxy; the decomposition is in that unit. (`comparison.csv`'s per_symbol `weighted_pnl` block is the OOS-side block; the IS-side per-symbol figures come from the report layer.)

**Incumbent IS net_pnl% across three runs:**

| Symbol | /059 IS (3-sym anchor, 14 feat) | /082 IS (3-sym, fresh data, 18 feat) | /083 IS (4-sym, fresh data, 14 feat) |
|---|---:|---:|---:|
| BCHUSDT | +109.23 | +68.65 | +79.45 |
| TRXUSDT | +3.95 | −1.22 | −23.04 |
| LDOUSDT | +0.89 | −25.09 | −11.44 |
| **Incumbent aggregate (BCH+TRX+LDO)** | **+114.07** | **+42.33** | **+44.97** |
| FILUSDT | — | — | −32.45 |
| **4-symbol total** | 114.07 | 42.33 | **+12.52** |

**The incumbent-aggregate IS weighted_pnl Δ and the Section 4.3 band.** Incumbent aggregate /083 = +44.97 vs /059 = +114.07 → **Δ = −69.11 pp**. The brief Section 4.3 pre-registered the band [−20, +20] combined IS weighted_pnl Δ. **The band was BREACHED — decisively (−69.11 vs a −20 floor, ~3.5× outside).** The brief's *prediction* (incumbents "CAN shift") was correct in direction; the magnitude was far beyond the pre-registered band.

**The decomposition of the IS PnL collapse −101.56 pp (/059 +114.07 → /083 +12.52):**
- **Component A — FIL's own negative edge: −32.45 pp** = FIL's standalone IS net_pnl%. This is **32% of the collapse**. FIL's IS model is a genuine net detractor at the 14-feature anchor — 60 trades, 36.7% WR, −0.54% avg PnL. The worst FIL months (2023-03 −21.88%, 2023-11 −28.74%, 2024-03 −13.90%) cluster in 2023-Q1 / 2023-Q4 / 2024-Q1; FIL's per-cell CPCV mean_path_sharpe is positive 2022-Q4→2024-Q1 then predominantly negative — FIL's IS edge was period-specific, not durable.
- **Component B — incumbent drift: −69.11 pp** = the incumbent-aggregate Δ vs /059. This is **68% of the collapse** — the *larger* share. Decomposed by symbol: TRX −27.00 pp (+3.95→−23.04, the largest single incumbent swing), BCH −29.79 pp (+109.23→+79.45, attenuated but still the sole positive anchor), LDO −12.32 pp (+0.89→−11.44).

**The cleanest available test — /082 vs /083 incumbents on the same fresh data.** /082 ran the SAME three incumbents (BCH/LDO/TRX) on the SAME freshly-fetched data as /083; the only differences are (i) /082 had 4 funding features (18-feature stack), /083 has the 14-feature anchor, and (ii) /083 has FIL in the book. If FIL were "reshaping the incumbents' Optuna landscape," the /082 incumbents (FIL absent) and the /083 incumbents (FIL present) would differ materially. **They do not.** Incumbent aggregate /082 = +42.33 vs /083 = +44.97 → **Δ = +2.63 pp** — essentially identical, and the small +2.63 difference is itself plausibly the 18→14 feature revert, not FIL. **The incumbents had ALREADY collapsed ~70 pp from /059 at /082 (Δ −71.74 pp), with FIL entirely absent from the book.** This is the decisive evidence: the incumbent drift is NOT caused by FIL's addition. It is data-extent drift — the incumbents drift on fresh data whether or not FIL is in the universe.

**Decomposition verdict.** Of the −0.9156 IS Sharpe collapse (−101.56 pp of IS PnL): ~32% is FIL's own genuine negative IS edge (a real, FIL-specific finding — FIL does not transfer); ~68% is incumbent drift, and that incumbent drift is **almost entirely data-extent drift, not FIL-perturbation** — proven by /082 (FIL absent) showing the incumbents already ~70 pp below /059 on the same fresh data. FIL is *not* a free-rider on incumbent edge and is *not* an Optuna-landscape disruptor; FIL added a genuinely negative −32 pp own edge, and the rest of the collapse was already baked in by the anchor staleness before FIL was ever added.

## 4. The corrected mechanism — data-extent drift, not Optuna-landscape reshaping (Critic Rec #1)

**The engineering report's stated mechanism is mechanistically false and is corrected here.** The report claimed adding FIL "reshaped the Optuna landscape for all 3 incumbents" and that "TRX's Optuna-selected hyperparameters at the 4-symbol landscape differ from those at 3-symbol." The Critic traced the runner end-to-end and found:

- **Per-symbol model isolation is total.** `_run_single_seed` (`run_baseline_v3.py:2349-2381`) iterates `for name, symbol in models_to_run` and calls `_build_v3_model(symbol=symbol, seed=seed, n_trials=n_trials, ensemble_seeds=ensemble_seeds_run, ...)`. Every argument to `_build_v3_model` for BCH/LDO/TRX is **byte-identical whether `V3_MODELS` has 3 or 4 entries** — `seed` constant, `n_trials=35` constant, `ensemble_seeds_run` the constant 3-tuple. `_build_v3_model` builds each model with `symbols=(symbol,)` and `feature_columns=list(features_for_symbol(symbol))`. **There is no `len(V3_MODELS)` dependency anywhere in `_build_v3_model` or in the per-symbol Optuna study.** Each symbol gets its own independent Optuna study with its own TPE sampler — TRX's study sees only TRX's training samples; it is identical to the 3-symbol run's TRX study. **There is no per-incumbent "4-symbol Optuna landscape."**
- The post-model risk filters are stateless (`apply_btc_trend_filter` is a pure per-trade filter; `apply_hit_rate_gate` is config-disabled). The only genuinely pooled computation is `_compute_cpcv_paths` — and that is a downstream *reporting artifact* computed after the trade roster is fixed; it cannot retroactively change which trades TRX takes. (The brief Section 4.3's attribution of the incumbent shift to "`REQUIRED_GAP` rises 66→88 changing the embargo" is also imprecise — `REQUIRED_GAP` enters only the pooled CPCV path computation; it does not touch the per-cell walk-forward embargo, fixed at 22.)

**The correct mechanism: data-extent drift from the mandatory Phase-6 re-fetch against a stale /059 anchor.** Brief Section 3.6, per `feedback_data_staleness_per_worktree.md`, mandates re-fetching all four symbols' 8h klines and regenerating all features in this worktree. The /059 baseline numbers were produced at commit `bea0987` on a different data extent. BASELINE_V3.md's own "EXPLORATION-Mode Anchor Staleness" section (the /077 finding) establishes that the /059 config no longer reproduces bit-identically on current code+data — there is a documented IS code-drift + OOS data-extent drift. Re-fetching the incumbents' klines revises and extends their series; feature recomputation shifts their marginal feature values; TRX is a structurally low-edge symbol (29-34% WR) where small feature shifts flip many marginal trades. This is the legitimate, expected consequence of running a fresh backtest on freshly-fetched data — and the /082-vs-/083 incumbent comparison (Section 3) proves it empirically: /082 saw the identical ~70 pp incumbent collapse with FIL entirely absent. **The diary records the correct mechanism: data-extent drift, NOT Optuna-landscape reshaping.**

## 5. PATH classification — NEGATIVE

The gate evaluation order per the LOCKED brief Section 8 disjunctive taxonomy is SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL-RESULT; first match is canonical. Anchor = BASELINE_V3.md /059 (IS +1.0894 / OOS +0.5791). Observed: IS +0.1738 (Δ −0.9156), OOS +0.4394 (Δ −0.1397), OOS/IS ratio 2.5276.

1. **SUSPICIOUS — does NOT fire.** Three grounds evaluated:
   - **Ratio gate (8.3)**: OOS/IS monthly Sharpe ratio = +0.4394 / +0.1738 = **2.5276** < 3.0 — does NOT fire.
   - **OOS-DOMINANT sub-mode (8.3)**: requires IS Δ < 0 AND OOS Δ ≥ +0.20. IS Δ = −0.9156 < 0 is TRUE; but OOS Δ = **−0.1397** < +0.20 is FALSE — does NOT fire. (The /078 OOS-DOMINANT signature is a universe change that *lifts* OOS while IS stays flat/negative; /083's OOS also *fell* − the opposite of OOS-DOMINANT.)
   - **Duration-loading (8.3)**: requires the FIL roster mean-duration gap > +1.0 candle AND OOS Δ ≥ +0.20 — OOS Δ is negative, so this cannot fire regardless of the duration gap.
   - **SUSPICIOUS does NOT fire** on any of the three grounds.
2. **NEGATIVE — FIRES.** NEGATIVE (8.2) requires IS monthly Sharpe Δ < −0.10 OR OOS monthly Sharpe Δ < −0.20 (and NOT SUSPICIOUS). IS Δ = **−0.9156** ≪ −0.10 — FIRES, unambiguously and by a large margin. (OOS Δ = −0.1397 is inside the −0.20 OOS floor, so the IS-collapse term is the firing term.) Brief Section 4.2 Falsifier #1 ("IS monthly Sharpe Δ < −0.20 → the /021 HBAR/AVAX failure mode reproduced") fired decisively. With SUSPICIOUS not firing, NEGATIVE is canonical.
3. **PROMISING — ruled out.** PROMISING (8.1) requires IS Δ ≥ +0.10 AND OOS Δ ≥ +0.10 AND `frac_positive_paths` ≥ 0.50 AND FIL IS weighted_pnl ≥ +5.0. It fails on all four: IS Δ −0.9156 < +0.10; OOS Δ −0.1397 < +0.10; `frac_positive_paths` 0.4667 < 0.50; FIL IS net_pnl% −32.45 ≪ +5.0.
4. **INERT — ruled out.** INERT (8.4) requires IS Δ ∈ [−0.10, +0.10]. IS Δ −0.9156 is far outside that band.
5. **NULL-RESULT — ruled out.** Adding a 4th symbol changes the pooled book and `REQUIRED_GAP`; the /083 roster is not bit-identical to the 3-symbol /059 roster (IS 219 vs 171, OOS 131 vs 94). Listed in the brief for taxonomy completeness only.

**→ NEGATIVE.** The Critic's Phase-7.5 review independently reached this read and recommended it: the IS-collapse term is unambiguous and large, SUSPICIOUS does not fire (the OOS Δ is negative, foreclosing the OOS-DOMINANT sub-mode), and the disjunctive precedence lands on NEGATIVE. The Gate-10-CPCV FAIL (`frac_positive_paths` 0.4667 < 0.55) and the 73.18% IS MaxDD (vs /059's 30.97%) corroborate. **NO-MERGE. BASELINE_V3.md UNCHANGED (/059 canonical, tag `v0.v3-059`). No new baseline-update tag** (an EXPLORATION closeout marker tag `v0.v3-083` is issued — explicitly NOT a baseline update, the same pattern as `v0.v3-082`).

## 6. Anchor-staleness assessment + recommendation for iter-v3/084 (Critic Rec #1 follow-through)

The Section 3 decomposition is dispositive on this question. **The /059 anchor is stale for cycle-3 EXPLORATION delta comparisons, and the staleness is large — a ~70 pp incumbent IS PnL drift, ~68% of the headline −0.9156 collapse.** /082 (a 3-symbol run on the same fresh data, FIL absent) already showed the incumbent aggregate ~70 pp below /059. Every cycle-3 Δ-vs-/059 is therefore confounded: an EXPLORATION can show an apparent IS regression that is mostly anchor staleness, not the axis. /082's own −0.0118 IS Δ "vs /059" was almost certainly masking a large negative incumbent drift offset by the funding-family Optuna perturbation — the catalog already classified /082 SUSPICIOUS partly on this reasoning, but the magnitude of the underlying incumbent drift was not isolated until /083's /082-vs-/083 comparison made it measurable.

This is exactly the situation cycle 1 faced and handled: cycle 1's /060 EXPLORATION-MODE-REFERENCE went stale and the /077 closeout established a fresh current-code /060-config baseline (IS +0.8236 / OOS +0.2078), against which cycle-2 EXPLORATIONs /078+ re-anchored. The same correction is needed now.

**Recommendation (clear, for the orchestrator to act on): iter-v3/084 should be a fresh /059-config anchor re-run on current data — a no-axis run of the canonical 3-symbol BCH/LDO/TRX, 14-feature, `(2.0,1.0)`-ATR, 7-gate /059 configuration at EXPLORATION-mode 3-seed, on the freshly-fetched current data.** This establishes a current-code/current-data EXPLORATION-MODE-REFERENCE for cycle 3 (the analogue of /077's current-code /060-config baseline). Cycle-3 EXPLORATIONs /085-091 then re-anchor their Δ against that fresh reference instead of the stale /059 numbers; the /092 CONFIRMATION continues to anchor against the canonical /059 CONFIRMATION baseline (a CONFIRMATION-mode number, separate from the EXPLORATION-mode reference, exactly as BASELINE_V3.md's anchor-staleness note specifies). /084 is not a "wasted" slot — it converts the cycle-3 measurement axis from confounded to clean, and it is the disciplined response to a decomposition that proved the anchor is stale. This recommendation is recorded in `cycle3_plan.md` Section 7. The canonical /059 CONFIRMATION baseline and tag `v0.v3-059` are UNCHANGED — this is an EXPLORATION-mode-reference correction, not a baseline change, and `OOS_CUTOFF_DATE` / `training_months` are untouched.

## 7. Section 7 prediction check — the outcome landed inside the pre-registered prediction set

The brief Section 7 pre-registered three failure paths plus a residual PROMISING tail, with explicit probabilities:

| Path | Pre-registered probability | Outcome |
|---|---:|---|
| SUSPICIOUS-OOS-DOMINANT via the added symbol's roster | ≈ 30% | did not fire (OOS Δ negative — the opposite of OOS-DOMINANT) |
| **INERT / NEGATIVE-aggregate** (the /021 HBAR+AVAX pattern) | **≈ 40%** (the central forecast) | **NEGATIVE FIRED — the canonical classification** |
| NEGATIVE via incumbent perturbation | ≈ 10% | partially borne out as a mechanism (incumbent drift was real) but mis-attributed in the brief to CPCV-path/Optuna reshaping; the realized mechanism is data-extent drift |
| PROMISING (residual) | ≈ 20% | did not fire |

**The realized outcome — NEGATIVE — was a pre-registered path, inside the ≈40% central-forecast bucket** ("INERT / NEGATIVE-aggregate — the /021 HBAR+AVAX pattern"). Section 7's text for that bucket is verbatim accurate: *"#1 of 4 negative-Sharpe candidates is still a negative standalone screen Sharpe (−0.137). FIL may simply add un-fittable noise: the per-symbol FIL model contributes near-zero or negative IS weighted_pnl, the aggregate IS Sharpe regresses... universe expansion at the EXPLORATION budget (35 trials × 1 ensemble per symbol) is over-stretched."* FIL's realized IS net_pnl% of −32.45 and the aggregate IS Sharpe collapse match the predicted FIL-adds-un-fittable-noise mechanism. The brief's honest reckoning — *"v3 has 0 clean PROMISING across 21 prior EXPLORATIONs, and the two prior count-expansions both failed... a single un-tuned screen cannot guarantee the production multi-symbol model fits FIL"* — is borne out. **Calibration: sound** — the realized classification was the central pre-registered forecast, and the brief did not float PROMISING above a level the evidence (a screen showing all 4 candidates at negative standalone Sharpe) could justify. (One precision: the brief's bucket merged INERT and NEGATIVE-aggregate; the realized result was the NEGATIVE end of that bucket — the IS collapse was far larger than the [−0.20, 0] "NEGATIVE-aggregate" magnitude Section 7's text sketched, which is the screen-under-prediction finding of Section 8 below.)

## 8. The IS-edge screen under-predicted the aggregate IS damage by ~24× (Critic Rec #3)

The Section-2 screen (`universe_expansion_edge_screen.py`, SHA `e538d5f`) predicted adding FIL would cost **−0.0382** aggregate IS Sharpe (T3 — "FIL is the LEAST harmful to the aggregate IS Sharpe"). The realized IS monthly Sharpe Δ was **−0.9156** — a **~24× magnitude miss** (0.9156 / 0.0382 ≈ 24).

**The screen is a defensible relative-ranking tool, NOT an absolute-magnitude predictor — and this is now documented as a process finding.** The screen's *ranking* was honest and useful: it correctly ranked FIL #1 of 4 survivors on standalone IS edge, and the brief's "Screen-scope disclosure (LOAD-BEARING)" section was explicit upfront that the screen is relative-ranking — it runs an un-tuned fixed-LightGBM-param pipeline with NO Optuna and NO 7-gate risk stack, so its absolute Sharpe numbers are not comparable to the production +1.09 baseline. But two factors the screen structurally cannot capture drove the 24× miss:
1. **FIL's own production-Optuna IS edge is more negative than the un-tuned screen's relative ranking implied.** The screen ranked FIL least-bad of a bad pool (standalone screen Sharpe −0.137); the production Optuna-tuned 4-symbol FIL model landed at −32.45 pp net IS PnL. A least-bad ranking among negative-Sharpe candidates does not imply a small absolute production contribution.
2. **The screen's "incumbent aggregate" baseline was itself measured on data that has since drifted.** Per Section 3, ~68% of the realized −0.9156 is incumbent data-extent drift — drift the screen, run before the Phase-6 re-fetch, could not have foreseen. The screen's −0.0382 figure isolates only FIL's *marginal* contribution against a *then-current* incumbent baseline; it never claimed to forecast the incumbents' own drift.

**The process lesson, recorded for future universe-expansion EXPLORATIONs:** the screen's aggregate-Δ figure must be treated as a **direction-only signal, not a magnitude estimate.** A universe-expansion brief must (a) pre-register the screen's aggregate-Δ as direction-only, and (b) set the falsifier bands wide enough that a ~24× magnitude miss is anticipated — brief Section 4.2 partly did this (the falsifier was a sign/floor test — "IS Δ < −0.20" — not a magnitude band, and it fired correctly), but the Section 4.3 incumbent-aggregate band [−20, +20] was a magnitude band and it breached at −69 pp. Future universe screens should either widen the incumbent-aggregate band substantially or, better, decompose the predicted Δ into the FIL-marginal term (direction-only) and an explicit anchor-staleness term (which a fresh-anchor re-run — see Section 6 — would make measurable). This closes the loop on the `feedback_v3_axis_selection_quant_discipline.md` mandate honestly: the screen did its job as a relative-ranking instrument; it was never built as a quantitative magnitude forecast and must not be cited as one.

## 9. The stale `PER_CELL_GAP` constant — a MANDATORY iter-v3/084-setup fix (Critic Rec #2)

The Critic Check-2 review found a pre-existing staleness defect (NOT /083-introduced — it predates /083 in `validation_v3.py`/runner history):

**`PER_CELL_GAP = 43` (`run_baseline_v3.py:1497`) is stale.** It is the value `(42+1)` left over from the reverted iter-v3/068 42-candle timeout-widening; that timeout was reverted to 21 candles at /069/070. With `timeout_candles = 21` the per-cell single-symbol CSCV purge gap should be `(21+1) = 22`. The brief Section 3.4's claim that `PER_CELL_GAP = 43` "= `(timeout_candles+1)`" is arithmetically false (`(21+1) = 22 ≠ 43`). The runner docstrings at `run_baseline_v3.py:1349` and `:1512` even contradict the constant by saying "gap=22 within-cell."

**It is NOT a leakage hazard and did not invalidate /083.** `43` over-purges relative to `22` — it removes *more* training data near each per-cell test boundary (43-of-~1805 candles ≈ 2.4% per side), which is the conservative direction. PBO is the headline per-cell overfitting metric and an over-purge biases it *pessimistically*, not optimistically — it cannot inflate PBO. The /083 run is methodologically sound; the constant is simply wrong.

**Recorded as a MANDATORY iter-v3/084-setup fix** (iter-v3/084 is the next runner-touching iteration — the fresh-anchor re-run of Section 6):
1. Correct `PER_CELL_GAP` from `43` to `(timeout_candles + 1) = 22` at `run_baseline_v3.py:1497`.
2. Add an `expected_gap` guard to the per-cell `combinatorial_purged_cv` call (`run_baseline_v3.py:1586-1592`) — currently called with **no `expected_gap` guard**, so the constant can silently drift again. The guard makes a future stale value raise `AssertionError` at runtime (the same protection the global `_compute_cpcv_paths` call already has via its `expected_gap=REQUIRED_GAP` self-assertion).
3. Fix the stale runner string literals at `run_baseline_v3.py:2539` (comment "asserts REQUIRED_GAP == 66") and `:2593` (print "Gap: 88 (= (21+1)*3=66; ... 3-sym universe BCH+LDO+TRX)") — these are cosmetic-only (the runtime assertion is correct) but the Phase 5.5 gate flagged them and they were not fixed before the /083 run. They must be updated to the correct text. (Note: if /084 is the fresh /059-config 3-symbol re-run, `REQUIRED_GAP` returns to 66 and `V3_MODELS` returns to BCH/LDO/TRX — the /084 setup must set the literals consistent with whatever universe /084 actually runs.)

This is recorded in `cycle3_plan.md` Section 7.

## 10. Critic verdict summary

**OVERALL=MERGE** per Critic FINAL `1116124` (`briefs-v3/iteration_v3-083/review.md`). A single-round full review; the verdict is FINAL. The MERGE verdict CERTIFIES the NEGATIVE result-read and the methodology clean — it is a closeout-integrity certification, NOT an advancement. A NEGATIVE *result* with *sound methodology* is OVERALL=MERGE; the Critic gates methodology, not outcome.

- **All 8 mandatory Checks + 4 optional Checks PASS or PASS-equivalent.** Check 1 (look-ahead) PASS — /083 adds no features; the new symbol FIL is fed through the identical per-symbol pipeline (`_build_v3_model` with `symbols=(symbol,)`, `feature_columns=list(features_for_symbol("FILUSDT"))`); the post-`e149e9d` walk-forward embargo is intact. Check 2 (embargo) PASS — `REQUIRED_GAP = (21+1)×4 = 88` proven correct, asserted at runtime, applied symmetrically (one sub-finding on the stale `PER_CELL_GAP` — Section 9 — does not change the verdict; the over-purge biases PBO conservatively). Check 3 (multiple-testing) — PBO axis PASS at 0.1392 < 0.40 (the one BLOCK-eligible axis at EXPLORATION mode); DSR/PSR informational per `feedback_v3_dsr_mode_artifact.md`. Check 4 (IC) PASS — no new feature family; max |IC| = 0.773 is the pre-existing Category-2 `regime_momentum_signed_5d`/`vwap_dev_20` carve-out. Check 5 (ADF) PASS — FIL 82.6% stationary, comparable to incumbents; one benign skipped cell (FIL/2020-11 sparse-data). Check 6 (Gate-10-CPCV) PASS on methodology — the `frac_positive_paths` 0.4667 < 0.55 FAIL is a result signal corroborating NEGATIVE, not a computation defect. Check 7 (reproducibility) PASS — commit `17ef604` stamped, explicit `feature_columns` list, `ENSEMBLE_SEEDS` literal 3-tuple, 10 IS trade-row spot-checks reconcile, `n_trials = 420 = 35×4×3`. Check 8 (hypothesis-implementation alignment) PASS — the `V3_MODELS` 4-symbol edit + the two sanctioned secondary edits map exactly to the brief; the `_canonical_v059` 11-knob config-accretion pre-flight confirms no scope creep. Checks 9-12 (symbol-exclusion, feature-isolation, forming-candle/freshness, library-pinning) all PASS.
- **The Central Adjudication — the incumbent-perturbation question.** The Critic traced the runner's per-symbol seed/CV/gap handling end-to-end and concluded **the incumbent perturbation is NOT a bug** — per-symbol model isolation is total, the post-model filters are stateless, the only pooled computation (`_compute_cpcv_paths`) is a downstream reporting artifact. The engineering report's stated mechanism ("FIL reshaped the Optuna landscape for the incumbents") is mechanistically false; the correct mechanism is data-extent drift from the Phase-6 re-fetch (Section 4 / Section 9 of this review). The run is methodologically sound; the result is a valid NEGATIVE.
- **Result classification.** The Critic explicitly read the result as **NEGATIVE** (IS Δ −0.9156 far below the −0.10 floor; SUSPICIOUS does not fire — OOS/IS ratio 2.5276 < 3.0, OOS-DOMINANT needs OOS Δ ≥ +0.20 but OOS Δ = −0.14). The QR adopts this as the FINAL Section-8 classification.
- **Three Critic Recommendations** — all integrated into this diary: (#1) correct the false incumbent-perturbation mechanism at the diary stage and decompose the IS Δ — done, Sections 3-4; (#2) fix the stale `PER_CELL_GAP` constant + the stale runner string literals, with an `expected_gap` guard — recorded as a MANDATORY /084-setup fix, Section 9; (#3) the IS-edge screen under-predicted by ~24×; treat the screen's aggregate-Δ as direction-only — recorded, Section 8.

## 11. BASELINE_V3.md status — UNCHANGED

**BASELINE_V3.md is UNCHANGED. /059 stays canonical (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791; tag `v0.v3-059`).**

A NEGATIVE EXPLORATION produces no edge ingredient, does not advance to the CONFIRMATION, and an EXPLORATION cannot update the baseline regardless. **No new git tag for a baseline update.** One documentation edit is made to BASELINE_V3.md at this closeout: the universe-expansion-with-FILUSDT outcome added to Dead Ideas (NEGATIVE: −0.92 IS, FIL's own −32% IS edge, and the IS-edge screen's ~24× magnitude under-prediction). An EXPLORATION closeout marker tag `v0.v3-083` is issued (annotated; explicitly NOT a baseline update — the same pattern as `v0.v3-082`).

`V3_MODELS` returns to BCH/LDO/TRX at the /084 starting point — FILUSDT is dropped (a NEGATIVE-axis symbol is not carried forward). The 14-feature `V3_FEATURE_COLUMNS_TOP_N` /059 anchor stack stays in place (the /083 funding-revert is retained — /082's funding family was already CLOSED).

## 12. Critic Recommendations carried forward + Next Iteration Ideas

Three recommendations from Critic FINAL `1116124`, plus the cycle-3 forward agenda. This iteration's verdict is final; a NEGATIVE axis does not advance.

1. **The engineering report's incumbent-perturbation mechanism is corrected** (Sections 3-4). The decomposition: of the −0.9156 IS Sharpe collapse, ~32% is FIL's own genuine negative IS edge (FIL does not transfer — a real FIL-specific finding) and ~68% is incumbent drift that is **data-extent drift, not FIL-perturbation** (proven by /082, FIL absent, already showing the incumbent aggregate ~70 pp below /059 on the same fresh data). The correct mechanism is recorded; the engineering report's "Optuna-landscape reshaping" claim is NOT repeated.

2. **MANDATORY iter-v3/084-setup fix: `PER_CELL_GAP` 43→22** (Section 9). Correct the stale constant at `run_baseline_v3.py:1497`, add an `expected_gap` guard to the per-cell `combinatorial_purged_cv` call (1586-1592), and fix the stale runner string literals at `:2539`/`:2593`. Recorded in `cycle3_plan.md` Section 7. The over-purge biased per-cell PBO conservatively, so no /083 result is invalidated — but the constant is wrong and must be corrected in the next runner-touching iteration.

3. **The IS-edge screen is a relative-ranking tool, NOT an absolute-magnitude predictor** (Section 8). It under-predicted the aggregate IS damage by ~24× (predicted −0.038, realized −0.9156). Future universe-expansion screens must treat the aggregate-Δ as direction-only; the falsifier bands must anticipate a large magnitude miss (a sign/floor falsifier — as Section 4.2's "IS Δ < −0.20" — works; a tight magnitude band — as Section 4.3's [−20, +20] — breached).

4. **iter-v3/084 should be a fresh /059-config anchor re-run on current data** (Section 6 — the anchor-staleness recommendation, the QR's clear call for the orchestrator). The /082-vs-/083 decomposition proved the /059 anchor is stale by ~70 pp of incumbent IS PnL — every cycle-3 Δ-vs-/059 is confounded. /084 = a no-axis EXPLORATION-mode 3-seed run of the canonical 3-symbol BCH/LDO/TRX, 14-feature, `(2.0,1.0)`-ATR, 7-gate /059 configuration on the freshly-fetched current data, establishing a current-code EXPLORATION-MODE-REFERENCE for cycle 3 — the exact analogue of cycle 1's /077 current-code /060-config baseline. Cycle-3 EXPLORATIONs /085-091 re-anchor against that fresh reference. The /084 setup also carries the MANDATORY `PER_CELL_GAP` fix of recommendation #2. This is recorded in `cycle3_plan.md` Section 7.

### Cycle 3 progress — 2/10 EXPLORATIONs done, 0 clean PROMISING

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /082 | NEW crypto-native FEATURE FAMILY (funding-rate, 4 features, Direction 1) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /083 | symbol-universe EXPANSION 3→4 (+FILUSDT, Direction 2) | **NEGATIVE** |
| #3 | /084 | fresh /059-config anchor re-run on current data (per Section 6) — strongly recommended | TBD |
| #4-#10 | /085-/091 | TBD per QR research + EDA, Directions 1-3 | — |

**iter-v3/084 — what it should be.** Per Section 6 (the QR's anchor-staleness recommendation) and Section 9 (the MANDATORY `PER_CELL_GAP` fix): **iter-v3/084 should be a fresh /059-config anchor re-run** — a no-axis EXPLORATION-mode 3-seed run of the canonical BCH/LDO/TRX / 14-feature / `(2.0,1.0)`-ATR / 7-gate /059 configuration on current freshly-fetched data. It establishes a current-code/current-data EXPLORATION-MODE-REFERENCE so cycle-3 Δ comparisons stop being confounded by the ~70 pp anchor staleness the /083 decomposition exposed. The /084 setup carries the `PER_CELL_GAP` 43→22 fix + the `expected_gap` guard + the stale-literal fixes. /084 is not a wasted slot — it converts cycle 3's measurement axis from confounded to clean, and the orchestrator should sequence it as the next iteration before any further structural EXPLORATION.

**Hard constraints on /084** (carried from prior closeouts + the /083 Critic):
- Anchor against BASELINE_V3.md /059 (IS +1.0894 / OOS +0.5791) — the canonical CONFIRMATION anchor, re-validated at /081 — for the CONFIRMATION-mode comparison; /084 itself *produces* the new EXPLORATION-MODE-REFERENCE.
- `V3_MODELS` returns to BCH/LDO/TRX (FILUSDT dropped — a NEGATIVE-axis symbol is not carried forward; the swap-by-replacement family stays CLOSED).
- `V3_FEATURE_COLUMNS_TOP_N` stays at the 14-feature /059 anchor stack.
- `PER_CELL_GAP` corrected 43→22; `expected_gap` guard added; stale runner string literals fixed (the MANDATORY /084-setup fix).
- `REQUIRED_GAP` returns to 66 = (21+1)×3 if /084 runs the 3-symbol universe.
- Pre-register the OOS/IS Sharpe ratio bound (> 3.0 → SUSPICIOUS) AND the OOS-DOMINANT sub-mode in Section 4/8 per `feedback_v3_oos_is_ratio_gate.md`.
- Config-accretion pre-flight retained — the `_canonical_v059` 11-knob check stays in `run_baseline_v3.py`.
- The v3 funding axis, the Kaufman path-efficiency axis (`efficiency_ratio_50` / `range_efficiency_50`), the regime-conditional kill switch (primitive 9), the LDO→ADA universe swap, the per-symbol PnL-share cap, and now **universe expansion with FILUSDT** are all CLOSED — do not re-propose any of them.
- HBAR/AVAX (CLOSED at /021), ADA (CLOSED at /078), and FILUSDT (CLOSED here at /083) are all closed universe-expansion candidates.

---

**Diary commit SHA**: (this closeout — diary + catalog + BASELINE_V3.md + cycle3_plan.md)
**Critic FINAL SHA**: `1116124`
**Engineering report SHA**: `6479e88`
**Phase-6 setup SHA**: `17ef604`
**Phase 5.5 gate SHA**: `21defda`
**Brief LOCKED SHA**: `36c7630` (SHA-backfill `8eafb4d`)
**Setup SHA**: `c5f6456`
**EDA SHA**: `e538d5f`
**Reports**: `reports-v3/iteration_v3-083/`
**Tag**: `v0.v3-083` (EXPLORATION closeout marker; NOT a baseline update — BASELINE_V3.md UNCHANGED at `v0.v3-059`)
