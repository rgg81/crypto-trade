# iter-v3/082 — Cycle 3 #1 EXPLORATION / NEW crypto-native FUNDING-RATE FEATURE FAMILY (Direction 1) / SUSPICIOUS-OOS-DOMINANT

**Date**: 2026-05-16
**Type**: EXPLORATION (cycle 3 #1 of 10 — the FIRST cycle-3 EXPLORATION; single-axis — a NEW crypto-native funding-rate FEATURE FAMILY: 4 features added to `V3_FEATURE_COLUMNS`, count 14→18)
**Axis**: Direction 1 of `briefs-v3/cycle3_plan.md` — a 4-member funding-rate feature family — `funding_sign_persist_9`, `funding_momentum_3`, `funding_accel_3`, `funding_price_divergence_6` — added to `V3_FEATURE_COLUMNS_TOP_N` (14→18). The 14 anchor features, ATR labeling `(2.0, 1.0)`, the 7-primitive risk-gate stack, `V3_MODELS` (BCH/LDO/TRX), `ENSEMBLE_SEEDS`, and the Optuna search are all UNCHANGED. EXPLORATION-mode 3-seed. Anchor: BASELINE_V3.md `v0.v3-059` (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791), freshly re-validated at the iter-v3/081 CONFIRMATION.
**Verdict**: EXPLORATION-MERGE per Critic FINAL `d5670aa` — OVERALL=MERGE; **SUSPICIOUS-OOS-DOMINANT classification adopted (the Critic's recommended result-read)**. A closeout-integrity / methodology certification, NOT an advancement: a SUSPICIOUS-OOS-DOMINANT axis never advances to the CONFIRMATION bundle.
**Classification**: **SUSPICIOUS-OOS-DOMINANT** per the LOCKED brief Section 8.3 — the OOS/IS ratio gate did NOT fire (1.6585 < 3.0), but the **OOS-DOMINANT sub-mode FIRED**: IS Δ -0.0118 < 0 AND OOS Δ +1.2081 ≥ +0.20. Section 8's disjunctive precedence (SUSPICIOUS → NEGATIVE → PROMISING → INERT) places SUSPICIOUS before INERT — and the feature-level INERT signature (the 4 funding features rank 15/16/17/18 of 18) is ALSO present, so the disjunctive order is load-bearing here. PROMISING (8.1) is mechanically foreclosed independently — it requires a family member at rank ≤ 9/18 with importance ≥ 30; the best funding feature ranks 15/18.
**Advancement**: does NOT advance to the iter-v3/092 cycle-3 CONFIRMATION bundle. A SUSPICIOUS-OOS-DOMINANT axis produces no edge ingredient — the +1.21 OOS lift is uncorroborated by IS and not attributable to the funding axis. The v3 funding axis is now a **4-data-point structural verdict** (/019/023/024/082, all INERT-by-importance) — CLOSED for the remainder of cycle 3 absent a fundamentally different construction.
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791; tag `v0.v3-059`). **No new tag issued.** The only BASELINE_V3.md edits at this closeout are documentation: the v3 funding axis added to Dead Ideas as a 4-data-point closed verdict, and a one-line note that the OOF parquet append is now atomic.
**Branch**: `iteration-v3/082`

---

## 1. What was done

iter-v3/082 is the FIRST EXPLORATION of v3 cycle 3 — the bold structural pivot mandated by `feedback_v3_bold_research_mandate.md` + `feedback_v3_mass_feature_expansion.md` and governed by `briefs-v3/cycle3_plan.md`. Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 3 runs 10 SEPARATE EXPLORATIONs (/082-/091) followed by 1 SEPARATE CONFIRMATION (/092) — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The axis is a **single-axis NEW crypto-native feature family** — Direction 1 of the cycle-3 plan (NEW crypto-native feature families researched from literature). `V3_FEATURE_COLUMNS_TOP_N` goes 14→18 by appending 4 funding-rate features after the 14 anchor features:

| Feature | Construction (all past-only) | What it encodes |
|---|---|---|
| `funding_sign_persist_9` | `np.sign(rate).shift(1).rolling(9).mean()` | crowding DIRECTION + PERSISTENCE — a mean-zero z-score structurally cannot carry this |
| `funding_momentum_3` | `rate[t] − rate[t−3]` | funding momentum — leverage building / unwinding |
| `funding_accel_3` | `momentum[t] − momentum[t−3]` (second difference) | funding ACCELERATION / carry SHOCK (BIS WP 1087: carry shocks predict liquidation jumps) |
| `funding_price_divergence_6` | `z(6-bar cum funding) − z(6-bar price return)`, clipped ±10 | the "crowded at the high" reversal setup |

Nothing else is touched — no labeling change, no symbol change, no risk-gate change, no model-architecture change, no seed change. `REQUIRED_GAP = 66 = (21+1)×3` unchanged (universe count unchanged). The funding-rate data pipeline (`data/funding_rates/<SYMBOL>.csv`, fed by `crypto-trade fetch-funding`) was already built at iter-v3/019; the /082 engineering build is a contained new feature-family function (`compute_funding_family` in `features_v3/funding_v3.py`) + a `GROUP_REGISTRY` entry, not a new fetcher.

The axis is QR-research-and-EDA-driven per `feedback_v3_axis_selection_quant_discipline.md` and the cycle-3 research mandate: brief Section 10 documents the genuine WebSearch/WebFetch literature path (BIS WP 1087 "Crypto carry" 2025; MDPI Mathematics 14(2):346 2025; CFB Benchmarks / the funding-crowding-reversal literature) — research motivated the four-channel family construction; the committed EDA `analysis/iteration_v3-082/funding_family_eda.py` (SHA `37d4da8`) validated it on v3's own IS data.

Run mode: EXPLORATION (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, `ENSEMBLE_SEEDS` outer-42 lineage subset `[191664963, 1662057957, 1405681631]`), `--n-trials 35`, 3-symbol universe (BCH/LDO/TRX), `REQUIRED_GAP = 66`, embargo 22. Total 315 Optuna trials (35 × 3 sym × 3 seeds). Wall-clock 0.74h, within the 2h EXPLORATION cap.

Commit chain: EDA `37d4da8` → research brief `275d24a` → brief SHA-backfill `222308e` → Phase 5.5 gate initial BLOCK `3cd8012` → setup `87195d1` → Phase 5.5 re-gate PASS `034d7e6` → OOF atomic-write infra fix `a7abba4` → engineering report `8913d9c` → Critic review `d5670aa`.

## 2. Results — vs the BASELINE_V3.md /059 anchor (IS +1.0894 / OOS +0.5791)

| Metric | /059 anchor | /082 actual | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+1.0894** | **+1.0776** | **-0.0118** |
| OOS monthly Sharpe | **+0.5791** | **+1.7872** | **+1.2081** |
| OOS/IS monthly Sharpe ratio | 0.5316 | **1.6585** | — |
| IS n_trades | 171 | 176 | +5 |
| OOS n_trades | 94 | 89 | -5 |
| IS daily Sharpe | 2.7092 | 1.8908 | — |
| OOS daily Sharpe | 1.4359 | 3.5478 | — |
| IS MaxDD | 30.97% | 18.92% | — |
| OOS MaxDD | 34.53% | 31.48% | — |
| PBO mean | 0.1278 | **0.1284** | PASS (< 0.40) |
| PSR | 1.0 | **1.0000** | PASS (> 0.95) |
| DSR (legacy) | 0.0 | **0.0000** | EXPLORATION-mode artifact (informational) |
| DSR_relative_B4 | — | **1.0000** | EXPLORATION-mode artifact (informational) |
| frac_positive_paths (CPCV) | 0.6444 | **0.6444** | PASS (> 0.55) |
| n_trials (Optuna total) | 1050 | 315 | EXPLORATION-mode (3 seeds) |
| n_eff | 19 | 19 | architecture-independent |

**Per-symbol OOS attribution** (from `comparison.csv` `per_symbol` block):

| Symbol | OOS weighted_pnl | OOS n_trades | OOS WR | OOS concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | **+55.6021** | 40 | 55.0% | **103.69%** |
| LDOUSDT | **-7.0037** | 13 | 30.8% | -13.06% |
| TRXUSDT | **+5.0236** | 36 | 38.9% | 9.37% |

OOS `weighted_pnl_total` = 53.6220; the three per-symbol values sum to it exactly (55.6021 − 7.0037 + 5.0236 = 53.6220).

**The headline.** IS slipped trivially (-0.0118, inside the ±0.10 noise band). OOS jumped sharply (+1.2081, from +0.5791 to +1.7872). The OOS/IS ratio is 1.6585 — below the 3.0 ratio gate. **But the 4 funding features rank 15/16/17/18 of 18 by importance — bottom-4, combined share 9.90%.** A +1.21 OOS Sharpe move from a feature family the model barely uses is NOT a funding-signal discovery; it is the documented INERT-feature Optuna-perturbation / 3-seed-lottery artifact (`feedback_v3_inert_features_at_higher_budget.md`). DSR=0.0000 / DSR_relative_B4=1.0000 are **informational at EXPLORATION** per `feedback_v3_dsr_mode_artifact.md` (EXPLORATION-mode `n_trials=315` is not comparable to CONFIRMATION-mode `n_trials=1050`); only CONFIRMATION-mode DSR triggers a MERGE gate. PBO=0.1284 — the one Check-3 axis meaningful at any mode — PASSES.

## 3. The funding family is INERT-by-importance — the OOS jump is NOT attributable to the axis

This is the central finding of the iteration.

**The 4 funding features are bottom-4 of 18 by importance.** From `conditional_orthogonality.csv` `last_month_importance_share_portfolio` (last walk-forward month, portfolio-pooled):

| Rank | Feature | Importance share |
|---|---|---:|
| 15 | funding_price_divergence_6 | 0.0376 |
| 16 | funding_sign_persist_9 | 0.0240 |
| 17 | funding_momentum_3 | 0.0189 |
| 18 | funding_accel_3 | 0.0185 |

Combined: **9.90%** of total importance across 18 features. A uniform 18-way split would assign each feature 5.56%; the 4 funding features average 2.475% each — **below-parity allocation**. The brief Section 4.2 supplemental feature-level falsifier fired exactly: "all 4 family members rank ≥ 14/18 (bottom quartile) across ≥ 2 of 3 symbols → the family is INERT." On the portfolio-pooled rank all 4 are 15-18/18. The PROMISING criterion (Section 8.1 — at least one family member rank ≤ 9/18 with absolute importance ≥ 30) is mechanically foreclosed: the best funding feature ranks 15/18.

**The OOS +1.21 lift is therefore NOT a funding-signal verdict.** A model that splits on the funding family for only 9.90% of its total importance is not learning a load-bearing funding rule. The +1.21 OOS Sharpe move with IS flat is the exact mechanism `feedback_v3_inert_features_at_higher_budget.md` documents: adding a feature family the model does not load expands Optuna's hyperparameter search space along uninformative dimensions; at `n_trials=35` the larger 18-column search lets Optuna land on a different IS-overfit hyperparameter region whose OOS realization happens, on the 3-seed draw, to be favorable. The IS Δ is flat (-0.0118) because the funding family did not give the model genuine IS edge; the OOS Δ is large and positive (+1.2081) because the perturbed hyperparameters' OOS realization caught the v3 OOS uptrend. This is lottery, not discovery.

**This is now the 4th EXPLORATION data point on the v3 funding axis** — after /019 (`funding_rate_zscore_30`, n_trials=10, PROMISING-INERT rank 14/14), /023 (same feature, n_trials=35, OOS collapsed), and /024 (BTC `funding_rate_zscore_30` cross-asset variant, n_trials=35, OOS collapsed). The /082 family construction was the explicit, literature-grounded, genuinely-distinct attempt to break the /019 INERT pattern — a 4-member family encoding crowding/momentum/shock/divergence vs the single mean-zero z-score. **It did not break it.** All four funding-axis data points are INERT-by-importance: LightGBM, at v3's per-symbol scale and EXPLORATION budget, does not learn the funding signal regardless of whether it is presented as a single z-score or a 4-channel family.

## 4. Concentration corroborates the fragility — and a reporting reconciliation

BCH carries **103.69%** of OOS weighted PnL (BCH +55.6021, TRX +5.0236, LDO −7.0037 on a 53.6220 total). The aspirational ≤30% top-symbol gate is missed by ~74 percentage points. The entire OOS "lift" is a single-symbol bet — one symbol's OOS-uptrend realization is doing all the work, the textbook regime-luck-via-concentration pattern, not a portfolio edge. LDO is a net OOS detractor (-13.06%).

**Reporting reconciliation (per Critic Rec #2).** The engineering report's per-symbol OOS table reported BCH at **110.2%** of OOS PnL, while `comparison.csv`'s `per_symbol` block reports BCH `concentration_pct` = **103.69%**. The two figures use different denominators: the 103.69% is BCH OOS `weighted_pnl` (55.6021) / total OOS `weighted_pnl_total` (53.6220); the 110.2% appears to use BCH gross unweighted `net_pnl_pct` (84.11) over a different base. **This diary adopts the `comparison.csv` total-OOS-weighted-PnL definition: BCH = 103.69% of OOS weighted PnL.** It is the cleaner definition — it is the same denominator the per-symbol `concentration_pct` field uses, it is internally consistent (the three shares sum to 100%), and it is the figure carried in all v3 prior diaries. Future engineering reports should align the per-symbol table to the `comparison.csv` `concentration_pct` definition so the artifact pair does not present two numbers that invite post-hoc cherry-picking. Both numbers say the same thing qualitatively — BCH carries the entire OOS book; LDO is negative.

## 5. PATH classification — SUSPICIOUS-OOS-DOMINANT

The gate evaluation order per the LOCKED brief Section 8 disjunctive taxonomy is SUSPICIOUS → NEGATIVE → PROMISING → INERT; first match is canonical. Anchor = BASELINE_V3.md /059 (IS +1.0894 / OOS +0.5791). Observed: IS +1.0776 (Δ -0.0118), OOS +1.7872 (Δ +1.2081), OOS/IS ratio 1.6585, funding family rank 15-18/18.

1. **SUSPICIOUS — FIRES.** Two grounds evaluated:
   - **Ratio gate (8.3)**: OOS/IS monthly Sharpe ratio = +1.7872 / +1.0776 = **1.6585** < 3.0 — does NOT fire.
   - **OOS-DOMINANT sub-mode (8.3)**: requires IS Δ < 0 AND OOS Δ ≥ +0.20. IS Δ = **-0.0118** < 0 is TRUE; OOS Δ = **+1.2081** ≥ +0.20 is TRUE — **FIRES**. The sub-mode is an independent SUSPICIOUS ground with no magnitude qualifier; it is the /078 signature exactly. SUSPICIOUS FIRES.
   - **Conditional-orthogonality test (8.3)**: not the firing trigger (the funding family is not relied on at importance ≥ 30 — it is bottom-4 — so there is no "relied-on member" whose split-allocation could be regime-loaded), but it does not rescue the axis: a feature family the model does not use carries no conditional signal at all.
2. **NEGATIVE — ruled out.** NEGATIVE (8.2) requires IS Δ < −0.10 OR OOS Δ < −0.20. IS Δ -0.0118 > −0.10; OOS Δ +1.2081 > −0.20. Neither floor breached.
3. **PROMISING — ruled out, and fails independently.** PROMISING (8.1) requires IS Δ ≥ +0.10 AND OOS Δ ≥ −0.10 AND `frac_positive_paths` ≥ 0.50 AND NOT SUSPICIOUS AND at least one family member rank ≤ 9/18 with importance ≥ 30. It fails on THREE independent terms: (a) IS Δ -0.0118 < +0.10; (b) SUSPICIOUS fires (precedence); (c) the best funding feature ranks 15/18, never reaching the ≤ 9/18 + importance-≥-30 bar. PROMISING is mechanically foreclosed.
4. **INERT — present at the feature level, but blocked by precedence.** INERT (8.4) has two clauses: both Δ in-band, OR all 4 family members rank ≥ 14/18 across ≥ 2 of 3 symbols. The **feature-level INERT signature IS met** — the 4 funding features rank 15/16/17/18 of 18 portfolio-pooled. But INERT is fourth in the disjunctive order; SUSPICIOUS fires first (the OOS-DOMINANT sub-mode), so SUSPICIOUS is canonical. The INERT signature is recorded as a corroborating feature-level fact (Section 3) — it is precisely what tells us the OOS +1.21 is the INERT-feature Optuna-perturbation artifact, not funding signal.
5. **NULL-RESULT — ruled out.** A 4-feature addition that the model uses at all (even at 9.90%) is not a bit-identical roster; the /082 roster differs from /081 (IS 176 vs 171, OOS 89 vs 94). Listed in the brief for taxonomy completeness only.

**→ SUSPICIOUS-OOS-DOMINANT.** The Critic's review (focus points #4/#5) independently reached this read and recommended it: Section 8's disjunctive precedence places SUSPICIOUS before INERT, both the OOS-DOMINANT sub-mode and the feature-level INERT signature are present, and under the brief's own LOCKED taxonomy SUSPICIOUS wins. The QR FINAL CALL adopts it. The disjunctive precedence is load-bearing here — and it is the *correct* call: classifying /082 as INERT would understate the fact that a +1.21 OOS headline was produced; classifying it SUSPICIOUS-OOS-DOMINANT records, accurately, that an eye-catching OOS number with a flat/negative IS and a barely-used feature family is the regime-luck pattern, not edge. Either reading is non-advancing — SUSPICIOUS produces no edge ingredient, INERT does not advance — so the verdict for the iter-v3/092 CONFIRMATION bundle is identical. **NO-MERGE. BASELINE_V3.md UNCHANGED (/059 canonical, tag `v0.v3-059`). No new tag.**

## 6. Section 7 prediction check — the outcome landed inside the pre-registered prediction set

The brief Section 7 pre-registered three failure paths plus a residual PROMISING tail, with explicit probabilities:

| Path | Pre-registered probability | Outcome |
|---|---:|---|
| INERT | ≈ 40% | feature-level signature MET (rank 15-18/18) — present |
| **SUSPICIOUS-OOS-DOMINANT** | **≈ 25%** | **FIRED — the canonical classification** |
| NEGATIVE | ≈ 15% | did not fire |
| PROMISING (residual) | ≈ 20% | did not fire |

**The realized outcome — SUSPICIOUS-OOS-DOMINANT — was a pre-registered path, weighted ≈25%.** Section 7's text for that path is verbatim accurate: *"`funding_sign_persist_9` has moderate marginal regime correlation (T6: 0.10–0.21). If the model leans on the sign-persistence feature and that feature is regime-loaded, the family could lift OOS while IS stays flat or slips — the /078 signature (IS Δ < 0, OOS Δ ≥ +0.20)."* The observed signature — IS Δ -0.0118 < 0, OOS Δ +1.2081 ≥ +0.20, OOS/IS ratio elevated — matches the predicted signature exactly. Section 7 also predicted the INERT feature-level signature as the most-likely path (≈40%); that signature is ALSO present (rank 15-18/18) — the two are not mutually exclusive at the feature level, and Section 8's disjunctive precedence resolves the classification to SUSPICIOUS. The honest reckoning in Section 7 — *"the funding axis has a 3-data-point INERT track record and the family construction is the explicit attempt to break it"* — is borne out: the family did not break the pattern; /082 is the 4th INERT-by-importance funding data point.

**Calibration assessment: sound.** The realized classification was inside the pre-registered prediction set, at a ≈25% weight that correctly sat below the cycle-wide SUSPICIOUS base rate (cycle 2 ran 4/10 ≈ 40%) on the explicit, defensible ground that a feature-only holding-time-orthogonal axis touches no barrier. The brief did not float SUSPICIOUS below a level it could justify, and the predicted sub-mode signature ("IS Δ < 0, OOS Δ ≥ +0.20") matched the observed outcome term-for-term. This is the same calibration discipline the /078 closeout endorsed — pre-register the failure mode honestly, do not let the central forecast (which leaned INERT/PROMISING) launder the failure-mode weight.

## 7. The OOF parquet atomic-write infra fix (`a7abba4`) — a permanent runner robustness improvement

The /082 backtest had a documented two-failed-launch detour before the clean run. Launch #2 corrupted `trial_oof_returns.parquet`: `pandas.DataFrame.to_parquet` truncates and rewrites the file non-atomically, and a concurrent reader between truncation and final flush read a partial/empty file ("magic bytes" / "end of stream" errors). The fix `a7abba4` replaced the in-place write with an atomic temp-file + `os.replace` pattern (`df.to_parquet(tmp_path); os.replace(tmp_path, final_path)`) at `src/crypto_trade/strategies/ml/optimization.py`. `os.replace` is an atomic POSIX rename — a concurrent reader sees either the fully-written old file or the fully-written new file, never a partial-write window. The failure-cleanup branch (`os.unlink` on exception then `raise`) removes only a partial temp file.

**This is recorded as a permanent runner robustness improvement.** The Critic's focus-point-#1 scrutiny (review Check 7) verified the fix is genuinely **metric-neutral**: the `combined` DataFrame that feeds the OOF parquet consumed by per-cell PBO/DSR/PSR is built identically pre/post-fix (same `oof_buffer`, same 6-column schema, same `pd.concat`); the only change is the write *mechanism*. `os.replace` does not touch DataFrame contents. No OOF row reaching the PBO/DSR/PSR computation is altered. The clean launch #3 confirmed `grep -c "magic bytes|end of stream|Traceback" run.log = 0`. The fix is a pure file-integrity safety change; it could NOT alter any /082 metric, and it removes a real concurrency hazard for **every future v3 iteration** — any runner that writes the OOF parquet while another process may read it. It is carried forward as standing infrastructure.

## 8. Critic verdict summary

**OVERALL=MERGE** per Critic FINAL `d5670aa` (`briefs-v3/iteration_v3-082/review.md`). A single-round full review; the verdict is FINAL. The MERGE verdict CERTIFIES the SUSPICIOUS-OOS-DOMINANT result-read and the methodology clean — it is a closeout-integrity certification, NOT an advancement. A SUSPICIOUS-OOS-DOMINANT (or INERT) *result* with *sound methodology* is OVERALL=MERGE; the Critic gates methodology, not outcome.

- **All 8 mandatory Checks PASS or PASS-equivalent.** Check 1 (look-ahead) PASS — the Critic hand-traced all 4 funding features in `funding_v3.py:395-492` (`compute_funding_family`); each construction carries an explicit `.shift(1)` before any rolling window (`funding_sign_persist_9` window `[t−9,t−1]`; `funding_price_divergence_6` both legs `.shift(1)`-lagged before the 6-bar window and 60-bar z-norm); the funding-record left-merge joins observation `t` to bar `t` and every downstream stat shifts; the QE's `test_past_only_no_lookahead` spike-perturbation test is consistent with the hand-trace. Check 2 (embargo) PASS — `timeout_candles = 21`, `REQUIRED_GAP = (21+1)×3 = 66` asserted at runtime, `compute_embargo_candles(10080,480) = 22`, the post-`e149e9d` walk-forward carried unchanged. Check 3 (multiple-testing) — FAIL on the DSR axis but INFORMATIONAL for EXPLORATION and NOT BLOCK-eligible (the documented EXPLORATION-mode DSR artifact per `feedback_v3_dsr_mode_artifact.md`); the BLOCK-eligible PBO axis PASSES at 0.1284 < 0.40; PSR 1.0 > 0.95. Check 4 (IC) PASS — cross-family max |IC| vs the 14 anchors = 0.220 (`funding_price_divergence_6` vs `vwap_dev_20`), far below the 0.70 hard gate and 0.50 strict target; the intra-family `funding_momentum_3` ~ `funding_accel_3` |IC| = 0.816 was substantively adjudicated as the established Category-2 momentum/second-difference carve-out (`funding_accel_3` is the exact algebraic second difference of `funding_momentum_3`, unit-tested) — a known, pre-registered, mechanically-forced correlation, not an undisclosed redundancy. Check 5 (ADF) PASS — all 4 features stationary in 89.8–96.8% of IS month-cells (combined 94.1%), `funding_sign_persist_9` lowest at 89.8% but above the 80% v3 threshold and economically expected to be the least stationary. Check 6 (Pareto) PASS — Gate-10-Pareto retired under the unified architecture; Gate-10-CPCV `frac_positive_paths = 0.6444` clears the 0.55 threshold. Check 7 (reproducibility) PASS — commit chain stamped and verified, explicit 18-element `feature_columns` list with all 4 funding names asserted by literal name, `ENSEMBLE_SEEDS` literal 3-tuple, OOS trade-PnL spot-checks reconcile exactly; the focus-point-#1 OOF atomic-write fix verified metric-neutral. Check 8 (hypothesis-implementation alignment) PASS — the code change maps exactly to the brief (4 named columns via `compute_funding_family`, `funding_family_v3` registered in `GROUP_REGISTRY`, 14→18 count asserted); the config-accretion pre-flight (the Critic-/081-Rec-#3-mandated `_canonical_v059` check, 11 behavior-affecting knobs) confirms single-axis discipline — no scope creep; the closed `funding_rate_zscore_30` / `btc_funding_rate_zscore_30` literal-name bans are retained; the /019 differentiation (brief Section 3.4) is adjudicated substantive, not a re-tread.
- **Result classification (focus points #4/#5)** — the Critic explicitly stated the result reads **SUSPICIOUS-OOS-DOMINANT** (the feature-level INERT signature is also present; Section 8's disjunctive precedence resolves to SUSPICIOUS; PROMISING is mechanically foreclosed because the best funding feature ranks 15/18). The QR adopts this as the FINAL classification.
- **Three Critic Recommendations** — carried to Section 11 below: (#1) classify SUSPICIOUS-OOS-DOMINANT and record the v3 funding axis as a 4-data-point closed verdict; (#2) reconcile the 110.2% vs 103.69% concentration-reporting discrepancy (done — Section 4); (#3) the remaining cycle-3 EXPLORATIONs should weight Direction 2 (universe expansion) up the priority list (recorded — Section 11 + `cycle3_plan.md` annotation).

## 9. Look-ahead audit + the OOS +1.21 mechanism

**Look-ahead — clean (Critic Check 1).** The funding rate at bar `t` settled at candle `open_time` and is broadcast ~5 min before the 8h boundary, so `funding_rate[t]` is knowable at bar `t` open — the identical convention the existing `funding_v3.py` uses and `test_funding_v3.py` enforces. Every family member carries an explicit `.shift(1)` before any rolling window. The Critic hand-traced all four constructions and confirmed the QE's adversarial spike-perturbation test (`test_funding_family_v3.py::test_past_only_no_lookahead` — perturb `funding_rate[250]` by +5.0, assert all 4 columns unchanged at bars `< 245`) is genuine and consistent. The walk-forward embargo fix (`walk_forward.py:113`, `train_end_ms = test_start_ms − embargo_ms`) is intact in this worktree. No look-ahead.

**The OOS +1.21 is the INERT-feature Optuna-perturbation artifact, not a funding-signal effect.** Because the funding family is bottom-4 by importance (9.90% combined, below-parity), it is not a load-bearing model input — the model is not splitting on it in any way that could produce a +1.21 OOS Sharpe of genuine funding edge. Per `feedback_v3_inert_features_at_higher_budget.md`, adding a feature family the model does not load expands Optuna's `n_trials=35` search space along uninformative dimensions; the larger 18-column surface lets Optuna land on a different IS-overfit hyperparameter region. The IS Δ is flat (the funding family gave no genuine IS edge) and the OOS Δ is large and positive (the perturbed hyperparameters' OOS realization, on the 3-seed draw, caught the v3 OOS uptrend). The OOS/IS ratio of 1.66 sits below the 3.0 ratio gate, so the ratio gate does not fire — but the IS-Δ<0 / OOS-Δ≥+0.20 OOS-DOMINANT sub-mode fires independently and is sufficient. The 103.69% BCH concentration is the corroborating evidence: the OOS lift is a single-symbol regime-luck realization, not portfolio edge.

## 10. BASELINE_V3.md status — UNCHANGED

**BASELINE_V3.md is UNCHANGED. /059 stays canonical (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791; tag `v0.v3-059`).**

A SUSPICIOUS-OOS-DOMINANT EXPLORATION produces no edge ingredient, does not advance to the CONFIRMATION, and an EXPLORATION cannot update the baseline regardless. **No new git tag for a baseline update.** Two documentation edits are made to BASELINE_V3.md at this closeout:

1. **Dead Ideas** — the existing `iter-v3/019/023/024 funding rate family` entry is updated: the v3 funding axis is now a **4-data-point structural verdict** (/019/023/024/082), all INERT-by-importance. The post-walk-forward-fix re-evaluation eligibility that motivated /082 is **DISCHARGED** — /082 was the rule-sanctioned re-evaluation under a genuinely distinct family construction and it reproduced the INERT verdict. The funding axis is CLOSED for the remainder of cycle 3 absent a fundamentally different construction (e.g. a multi-symbol-pooled model that gives the funding family more training data per fit, or open-interest data which has no current feed).
2. A one-line note in the Code Configuration section that the OOF parquet append is now atomic (commit `a7abba4`) — a metric-neutral runner robustness improvement.

`V3_MODELS` stays BCH/LDO/TRX. The 14-feature `V3_FEATURE_COLUMNS_TOP_N` is restored — at /083's setup the 4 funding features are reverted (`V3_FEATURE_COLUMNS_TOP_N` 18→14, the /059 anchor stack); per `feedback_v3_inert_features_at_higher_budget.md`, an INERT feature family must not be carried forward, and it must not be retested at a higher Optuna budget (an INERT feature at higher budget actively HARMS OOS). The `funding_v3.py` `compute_funding_family` function and the `funding_family_v3` `GROUP_REGISTRY` entry are left as harmless unreferenced infrastructure at zero revert cost. The closed `funding_rate_zscore_30` / `btc_funding_rate_zscore_30` literal-name bans stay intact.

## 11. Critic Recommendations carried forward + Next Iteration Ideas

Three recommendations from Critic FINAL `d5670aa`, plus the cycle-3 forward agenda. This iteration's verdict is final; a SUSPICIOUS-OOS-DOMINANT axis does not advance.

1. **The v3 funding axis is CLOSED at 4 data points.** /019/023/024/082 are all INERT-by-importance — three single-z-score attempts and one literature-grounded 4-channel family, none learned by LightGBM at v3's per-symbol scale + EXPLORATION budget. A 5th funding attempt must NOT re-use either the single-z-score or the per-symbol-family construction. The only constructions that could plausibly change the verdict: (a) a **multi-symbol-pooled model** — pooling the BCH/LDO/TRX (or a larger universe's) cross-section gives a single fit far more training data, and a funding family may be learnable with more rows per fit where it is not learnable per-thin-symbol-model; (b) **open-interest data** — a genuinely different crypto-native feed (OI delta as a leverage-stretch signal), which v3 does not currently fetch and which would require a new fetcher. Neither is a funding-axis retread; both are different axes. Absent one of those, the funding axis is closed for cycle 3.

2. **Concentration-percentage reporting is reconciled to the `comparison.csv` definition** (Section 4) — BCH = 103.69% of OOS weighted PnL, using BCH OOS `weighted_pnl` over total OOS `weighted_pnl_total`. The Engineer should align the per-symbol engineering-report table to the `comparison.csv` `concentration_pct` field in future iterations so the artifact pair does not present two divergent numbers.

3. **The remaining cycle-3 EXPLORATIONs (/083-091) should weight Direction 2 (universe expansion) higher.** /082's OOS result is 103.69%-concentrated in BCH on a 3-symbol universe — the OOS Sharpe is structurally a single-symbol bet, and **no feature-family axis can fix that denominator problem.** A funding family (or any feature) added to a still-3-symbol universe was always going to produce a concentration-dominated result regardless of whether the feature carried signal. The cycle-3 plan's Direction 2 (universe expansion = denominator expansion, distinct from the CLOSED swap-by-replacement family) and Direction 3 (multi-symbol-pooled model) directly attack the BCH-concentration fragility that makes every v3 OOS number fragile. This is recorded as a Section-11 annotation to `briefs-v3/cycle3_plan.md`. The Fundamental Law (IR = IC × √breadth) names breadth as the lever v3 has never pulled.

### Cycle 3 progress — 1/10 EXPLORATIONs done, 0 clean PROMISING

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /082 | NEW crypto-native FEATURE FAMILY (funding-rate, 4 features, Direction 1) | **SUSPICIOUS-OOS-DOMINANT** |
| #2-#10 | /083-/091 | TBD per QR research + EDA — Direction 2 (universe expansion) strongly preferred | — |

**iter-v3/083 (cycle 3 #2) — what it should prioritize.** Per Critic Rec #3 and the cycle-3 plan, **iter-v3/083 should pursue Direction 2 — symbol-universe EXPANSION** (growing the denominator from 3 symbols, distinct from the CLOSED swap-by-replacement family). The /082 result makes the case structurally: the OOS Sharpe is 103.69%-concentrated in BCH and no feature axis can fix that. The /083 QR must, per `feedback_v3_axis_selection_quant_discipline.md` and the cycle-3 research mandate: (a) research the candidate-symbol set with genuine WebSearch/WebFetch — liquidity, listing date (drop the first 30-60 days of any newly-listed symbol), data depth; (b) screen candidates on a genuine IS-edge screen AND a portfolio-aggregate IS-Sharpe-contribution screen under BCH dominance (the /078 lesson: a per-symbol Sharpe screen does not transfer to portfolio-aggregate lift); (c) pre-register the holding-time / roster-composition predictor including the added-symbol mean-duration sub-channel under production Optuna-tuned barriers (the /078 lesson: a screen-grade proxy under-predicts the timeout-trade tail by 6×). A larger universe (5-8 symbols) directly dilutes BCH concentration — the structural fix the cycle-3 plan identifies as HIGH priority. The /083 axis is QR-EDA-driven and selected fresh in /083 Phase 1-2; Direction 2 is the strongly-preferred direction per this closeout's Critic Rec #3.

**Hard constraints on /083** (carried from prior closeouts + the /082 Critic):
- Anchor against BASELINE_V3.md /059 (IS +1.0894 / OOS +0.5791) — the canonical anchor, re-validated at /081.
- `V3_FEATURE_COLUMNS_TOP_N` reverts to the 14-feature /059 anchor stack at /083's setup (the 4 funding features dropped; INERT features are not carried forward and not retested at higher budget per `feedback_v3_inert_features_at_higher_budget.md`).
- `V3_MODELS` is BCH/LDO/TRX at the /083 starting point; a universe-EXPANSION axis ADDS symbols (it does not swap — the swap-by-replacement family is CLOSED).
- Pre-register the OOS/IS Sharpe ratio bound (> 3.0 → SUSPICIOUS) AND the OOS-DOMINANT sub-mode (IS Δ < 0 AND OOS Δ ≥ +0.20) in Section 4/8 per `feedback_v3_oos_is_ratio_gate.md`.
- Pre-register the holding-time / roster-composition predictor per `feedback_v3_is_oos_regime_divergence.md` — for a universe axis, the added-symbol mean-duration sub-channel computed under production Optuna-tuned barriers.
- Genuine WebSearch/WebFetch literature research in Phases 1-4, documented in brief Section 10 (the cycle-3 research mandate).
- Config-accretion pre-flight retained — the `_canonical_v059` 11-knob check stays in `run_baseline_v3.py`.
- The v3 funding axis (`funding_rate_zscore_30` / `btc_funding_rate_zscore_30` / the /082 funding family), the Kaufman path-efficiency axis (`efficiency_ratio_50` / `range_efficiency_50`), the regime-conditional kill switch (primitive 9), and the LDO→ADA universe swap are all CLOSED — do not re-propose any of them.

---

**Diary commit SHA**: `afdf4d3` (this closeout — diary + catalog + BASELINE_V3.md + cycle3_plan.md)
**Critic FINAL SHA**: `d5670aa`
**Engineering report SHA**: `8913d9c`
**Brief LOCKED SHA**: `275d24a` (backfill `222308e`)
**Setup SHA**: `87195d1`
**Phase 5.5 gate SHA**: `034d7e6` (re-gate PASS; initial BLOCK `3cd8012`)
**EDA SHA**: `37d4da8`
**OOF atomic-write infra fix SHA**: `a7abba4`
**Reports**: `reports-v3/iteration_v3-082/`
**Tag**: `v0.v3-082` (EXPLORATION closeout marker; NOT a baseline update — BASELINE_V3.md UNCHANGED at `v0.v3-059`)
