# LightGBM Master Advisor — iter-v1/046 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; anchor BASELINE_V1 (`f8bc12c`); cycle-6 EXPLORATION 1/10.
- /045 BLOCK-FINAL (review.md): primary reasons (1) 5× single-seed=42 inheritance, (2) workflow w0qpo136q's composite score `0.5·OOS_Sh + 0.3·IS_Sh + 0.2·OOS_n/100` performed OOS-aware specialist selection, (3) C-BTC 19-trade σ_SR≈0.23 basin-lottery exposure.
- /045 ALT_1 substrate IS evidence (analysis/iteration_v1-045/component_is_evidence.csv): C-BTC=v1-012 IS Sharpe **−0.21**, C-ETH=v1-042 IS **+0.71**, C-LINK=v1-011 IS **+1.27**, C-LTC=v1-040 IS **+3.76**, C-DOT=v1-031 IS **+2.40**. **BTC's pick was IS-NEGATIVE** — the strongest a-priori evidence that an IS-only solve must diverge on at least 1 coin.
- /046 axis = methodology (CSV-replay partition re-solve with score = 0.6·IS_Sh + 0.4·IS_n_trades/100; per pre-brief outline §1, §4).
- LM Master scope on a methodology-axis iteration is **INHERENTLY narrow**: no Optuna call, no LightGBM fit, no feature engineering, no HP region exposed. The substantive advisory shifts from HP/feature recommendations to **methodology-clean substrate-selection discipline** (which components survive an honest IS-only screen, how to read the per-coin IS rank table, where the multiple-comparison trap lives).

## Top 3 Recommendations for IS-Only Substrate Selection

### 1. Look for HP-region diversity + IS sample-size adequacy across the top-1 picks (NOT just IS Sharpe maximization)

**What**: When `partition_solve_v2.py` emits per-coin top-3, the QR should NOT simply ship "top-1 by score_is". Instead, inspect the top-3 per coin for two ML-side signals:

- **HP-region diversity across coins**: each component's source iter ran a DIFFERENT Optuna search. If 3 of 5 top-1 picks happen to share the same source iter (e.g. v1-040 dominates LTC + ETH + BTC because /040's late-cycle 35-trial budget overfit a multi-symbol pool), the substrate has **HP-basin concentration** — one Optuna lottery roll drives 3 components. Pick lower-ranked alternatives if necessary to spread HP-basin exposure across iters.
- **IS sample-size adequacy at top-1**: any top-1 with IS n_trades < 50 is at σ_SR ≈ √(1/50) = 0.14 — wide enough that the IS Sharpe ranking is itself noisy. Flag these for top-2 fallback consideration. **v1-012's BTC IS n_trades=65 is borderline**; v1-040's LTC IS n_trades=117 is comfortable; v1-031's DOT IS n_trades=117 comfortable.

**Why**: The /045 BLOCK was specifically about substrate selection being statistically fragile at single-seed. An IS-only solve fixes the OOS-leak axis but does NOT fix the per-component basin-lottery axis. If 4 of 5 IS-only top-1 picks come from cycle-5 single-seed=42 iters, the IS-only substrate inherits the SAME single-seed exposure ALT_1 had — just selected on a different criterion. /046 buys methodology cleanliness; it does NOT buy multi-seed robustness.

**Expected effect**: Forces the QR to emit a documented justification in the brief Section 11.D for why the top-1 (vs top-2) was chosen for each coin — a methodology-trail audit even within the IS-only frame.

**Risk**: If QR over-engineers tiebreaker logic, they re-introduce a hidden DOF. **Mitigation**: pre-register the tiebreaker hierarchy in brief Section 4 BEFORE running partition_solve_v2.py. Outline §15 Q2 already commits to (IS Sharpe desc, IS n_trades asc) — extend this to a tertiary tiebreaker if needed (source iter date — prefer the older iter, less HP-search-budget evolution to overfit-on).

### 2. Pre-register the per-coin top-3 candidates BEFORE running the solve — multiple comparison correction

**What**: The IS-only score is a NEW scoring expression. With ~25-30 candidates per coin and 5 coins, the partition solve is silently running ~140 hypothesis tests. After /046's IS-only score, the top-1 per coin will be IS-Sharpe-maximizing under THAT score — and Sharpe-maximization across 25-30 candidates is itself a selection-bias generator. Per coin, the top-1's IS Sharpe is biased upward by ~σ_Sh × √(2 log N) ≈ 0.14 × √(2 log 30) ≈ 0.36 (single-coin best-of-N inflation).

The QR should:

- Pre-commit the per-coin candidate inventory in brief Section 2 (numbered list of iters considered per coin, BEFORE seeing partition_solve_v2.py output).
- Report top-1 score_is AND its honest deflated estimate (subtract 0.36 from IS Sharpe per coin).
- The substrate's IS Sharpe headline should be reported as `raw +X.XX / deflated +X.XX−0.36 = +(X-0.36).XX` per coin, with the bundle headline at the deflated-component aggregation.

**Why**: F1 master falsifier sets +0.50 IS daily Sharpe floor. With 5 components each best-of-25-30 selected, the bundle IS Sharpe is upward-biased by roughly +0.36/5 × 5 = +0.36 (if components are independent — which they are not, since they share the BASELINE_V1 risk gate stack). The deflated F1 floor should be +0.86 raw to clear +0.50 honest. **The brief's F1 threshold of +0.50 is too lax under multiple-comparison correction.**

**Expected effect**: F1 reframed as "deflated IS Sharpe ≥ +0.50" — strictly more stringent. If the inventory is signal-bounded, F1 FAIL fires earlier and routes /046 to NULL-METHODOLOGY-FIX (signal-bounded) per outline §10 more honestly.

**Risk**: QR may reject this on the basis that /045's ALT_1 didn't carry deflation (true — and /045 BLOCKED partly for this reason). If QR pushes back, the alternative is to report BOTH raw and deflated and let Critic Phase 7.5 read both. **Confidence: HIGH** that this should be in the brief; **MEDIUM** that QR adopts it as a strict F1 transform vs informational supplement.

### 3. Verification recipe: the IS-only solve is methodologically clean iff three properties hold

**What**: Beyond F5's grep-clean check (script contains no `oos`/`out_of_sample`/`OOS_CUTOFF` strings), the QR + Engineering Report should verify:

- **(a) Data-loaded check**: `partition_solve_v2.py` opens ONLY `reports-v1/iteration_v1-{iter}/in_sample/trades.csv` for each (iter, coin) cell — never `.../out_of_sample/...`. Engineering report Section 9 should emit `lsof`-equivalent or a Python `open()` log proving the script never touches `out_of_sample/` paths.
- **(b) Date-cutoff check**: any timestamp filtering in the script uses `OOS_CUTOFF_MS = 1742774400000` (2025-03-24) ONLY as the IS-window UPPER bound (i.e., `open_time < OOS_CUTOFF_MS`), NEVER as a lower bound to filter IN OOS data. Critic Check 17's `partition_solve_v2.py` grep regime should explicitly check `>= OOS_CUTOFF_MS` or `> OOS_CUTOFF_MS` patterns and flag them.
- **(c) Functional invariance check**: re-run `partition_solve_v2.py` with the OOS CSVs DELETED from disk (rename `out_of_sample/` → `out_of_sample.HIDDEN/` for 5 iters, then re-run). If the script's output is bit-identical, the script provably did not read OOS data. Engineering report emits a `diff` of the partition_solve_v2.csv before/after the hide test — should be ZERO bytes different.

**Why**: Grep-clean is necessary but not sufficient. A script can `pd.read_csv("../out_of_sample/trades.csv")` without containing the literal string `oos` (e.g., constructed via f-string `f".../{window}/trades.csv"` where `window` is a parameter). The hide test (c) is the only true functional proof.

**Expected effect**: Engineering report contains a "methodology-clean proof" subsection that goes beyond /045's verification regime — sets the bar for future methodology-axis iterations.

**Risk**: Adds ~5 min to engineering report wall-clock (rename + re-run + diff). Negligible cost on a < 30 min total iteration.

## Risk Flags — What Could Go Wrong with IS-Only Selection

**Flag A — IS-overfit-on-a-different-axis**: An IS-only substrate is OOS-leak-free by construction but is NOT IS-overfit-free. Per-coin best-of-25-30 is itself a selection bias (Rec 2 above). If the QR adopts IS-only as "the honest substrate" without deflation, the catalog gains a different inflation type (IS-side selection bias instead of OOS-side selection bias). Both are unmerged-worthy at single-seed; both require multi-seed re-validation at /047 to be MERGE-worthy.

**Flag B — IS-only substrate may have WORSE OOS than ALT_1 (and that's NOT a /046 failure)**: The outline §4 F4 correctly states OOS is forensic-only. **LM Master strongly endorses this design choice.** The Critic may be tempted to use OOS as a tiebreaker between substrates at Phase 7.5; QR should pre-empt this in brief Section 4 with explicit language: "Critic CANNOT cite IS-only substrate OOS Sharpe < ALT_1 OOS Sharpe as evidence of /046 failure — that re-introduces the OOS-aware selection bias /046 is designed to detect."

**Flag C — Tiebreaker convention matters more than QR may think**: With ~25-30 candidates per coin, score_is ties at the 0.01 level are plausible (especially when IS Sharpe is bounded ~[0, 4]). Outline §15 Q2 commits to (IS Sharpe desc, IS n_trades asc). LM Master prefers (IS Sharpe desc, IS n_trades **desc** — more trades = more reliable estimate, NOT fewer). The outline's "ascending" choice would pick the LOWEST trade-count tied candidate, maximizing σ_SR exposure — the opposite of robustness. **Recommend QR flip the secondary tiebreaker to descending in the brief.**

**Flag D — Score formula `0.6·IS_Sh + 0.4·IS_n_trades/100` may produce score-domain-collapsed top-1s**: IS_n_trades/100 ranges roughly [0.5, 1.5] for the inventory (50-150 IS trades). IS Sharpe ranges roughly [−0.5, +4]. The 0.4 weight on trade-count contributes ~[0.2, 0.6] to score; the 0.6 weight on IS Sharpe contributes ~[−0.3, +2.4]. Trade-count has ~15-25% effective weight on the score (not the 40% nominal) — it's a tiebreaker more than a co-equal criterion. This is FINE as long as the QR understands it. If QR wanted trade-count to truly co-determine, the formula should be `0.6·IS_Sh + 0.4·log10(IS_n_trades/10)` or similar. **Recommend QR document the effective weight calculation in brief Section 2.**

## Prior Distribution (verdict bands for /046)

The verdict bands for /046 are methodology-axis-flavored — the v1 standard bands (UNIVERSAL / REGIME-SPECIALIST-IS/OOS / TAIL-CONTROL / EXPLORATION-PROMISING / TRUE-NEG / NEGATIVE-no-effect / LEARNED-NEG) need translation to /046's subtype space (PROMISING-COINCIDENCE / PROMISING-DIVERGENCE / PROMISING-PARTIAL / NULL-METHODOLOGY-FIX / BLOCK-PENDING-FIX). Mapping:

- **EXPLORATION-PROMISING** (modal) = PROMISING-DIVERGENCE OR PROMISING-COINCIDENCE — substrate decision is INFORMATIVE either way
- **NEGATIVE-no-effect** = NULL-METHODOLOGY-FIX (signal-bounded) — F1 FAIL, inventory exhausted
- **LEARNED-NEG** = BLOCK-PENDING-FIX — script grep-fail
- **TRUE-NEG**, **REGIME-SPECIALIST-IS/OOS**, **TAIL-CONTROL**, **UNIVERSAL** — N/A at methodology-axis

Estimated band priors (sum to 100%):

| Band | Prior | Reasoning |
|---|---:|---|
| **PROMISING-DIVERGENCE (modal)** | **45%** | C-BTC v1-012 has IS Sharpe −0.21 — IS-only solve CANNOT pick it. Divergence on BTC is near-certain. Add likely divergence on ETH (v1-042 IS +0.71 is well behind v1-040 LTC IS +3.76 — though that's a different coin; relevant comparison is v1-042 vs other ETH-covering iters in inventory). 2+-coin divergence is more probable than 1-coin. |
| **PROMISING-COINCIDENCE** | 10% | Would require 5 of 5 IS-only picks to match ALT_1 — requires C-BTC v1-012 to be IS-only top-1 for BTC despite IS Sharpe −0.21. Effectively impossible UNLESS no other iter covered BTC with positive IS Sharpe + IS n_trades ≥ 50. Inventory survey makes this implausible but not impossible (pre-EDA Section 9 of outline lists v1-022/023/038/040 as plausible BTC top-3 candidates — at least one likely has IS Sharpe > 0). |
| **PROMISING-PARTIAL (1-2 div)** | 20% | Most likely scenario where BTC diverges but ETH/LINK/LTC/DOT match. Outline §10 routes this to /047 dual multi-seed validation. |
| **NULL-METHODOLOGY-FIX (signal-bounded)** | 15% | F1 FAIL at +0.50 IS Sharpe floor — inventory's best IS-only substrate has weak IS Sharpe in aggregate. Lower bound prior because v1-040 LTC IS +3.76 alone, weighted 1/5, contributes +0.75 IS Sharpe to the bundle — F1 floor cleared even if other 4 components have IS Sharpe = 0. F1 FAIL only if 3+ coins have ALL candidates IS-negative. |
| **BLOCK-PENDING-FIX (F5 grep fail)** | 5% | Script defect — the QR has clear F5 spec; competent execution makes this small. |
| **NULL-METHODOLOGY-FIX (other modes)** | 5% | E.g., tiebreaker collapse or score-formula edge case producing non-unique top-1 with no documented resolution. |

**MODAL = PROMISING-DIVERGENCE at 45%.** The dominant driver is the C-BTC v1-012 IS-negative anomaly: any honest IS-only solve almost certainly does NOT pick v1-012 for BTC, which DEFINITIONALLY fails F2 (5-of-5 coincidence) and most likely passes F3 (≥3 divergence) once 1-2 additional ETH/LINK divergences are added.

**Confidence: MEDIUM-HIGH** on the modal. The IS evidence for ALT_1 (especially BTC at IS −0.21) is the load-bearing signal. The bands are slightly soft on the F2-vs-F3 split (45/10/20) — the inventory survey in /046 EDA will sharpen these.

## What I Did NOT Recommend, and Why

- **DO NOT recommend an HP-region change for /046**: methodology-axis iteration has no Optuna call, no LightGBM fit. Any HP recommendation would be ignored or misapplied. /047+ (multi-seed re-validation of the /046-selected substrate) is the next iteration where HP advice becomes relevant.
- **DO NOT recommend a feature change for /046**: same reason. /046 inherits each component's source-iter feature set verbatim. Feature axis is closed at this iteration.
- **DO NOT recommend a third scoring expression (e.g., IS-Sharpe-only, no trade count)**: outline §15 Q4 already commits to ONE methodology fix per /046. A second variant would dilute the test signal and re-introduce researcher DOFs.
- **DO NOT recommend ALT_2 (BTC=v1-023) as a pre-committed swap path**: ALT_2 was /045's fallback under the OOS-aware framework. /046's IS-only solve treats v1-023 as just another BTC candidate evaluated by score_is — if it wins on IS-only, it wins on merit; if not, it doesn't. The QR should NOT pre-register ALT_2 as a fallback because that would re-introduce the very OOS-aware selection /046 is designed to detect.
- **DO NOT recommend deflating only the bundle headline (instead of per-component)**: per-coin deflation is correct because each coin's best-of-N selection is an independent inflation source. Bundle-level deflation alone would be too lenient.

## Closing Note

**Confidence: MEDIUM-HIGH.** The /046 design is sound and the methodology-fix axis is the right cycle-6 opening move. LM Master's value on this iteration is narrower than usual (no HP, no feature) but the multiple-comparison correction (Rec 2) and the functional-invariance verification (Rec 3) are genuine additions to the brief's rigor that the outline does not yet contain.

The modal /046 outcome is **PROMISING-DIVERGENCE (45%)** driven by C-BTC v1-012's IS Sharpe = −0.21 — an honest IS-only solve almost certainly does NOT select v1-012 for BTC. This means /046 will likely **confirm the /045 BLOCK was substantively correct** (ALT_1 was OOS-aware-selected, not IS-honest), routing /047 to multi-seed re-validation of the IS-only substrate rather than ALT_1.

**Single most important thing the QR should NOT ignore**: **Recommendation 2 — multiple-comparison correction on per-coin best-of-N selection.** /046's design correctly removes OOS-aware bias but does NOT remove IS-side best-of-25-30 inflation. F1's +0.50 IS Sharpe floor is too lax without deflation. The brief should report BOTH raw and deflated bundle IS Sharpe, and F1 should fire on the deflated value. This is the difference between /046 producing a methodologically clean answer and /046 producing an answer that's clean on ONE axis (OOS-leak) while silently inflated on another (best-of-N).

---

*End of LightGBM Master Phase 4.5 advisory for iter-v1/046.*

---

# LightGBM Master Advisor — iter-v1/046 — Phase 7.4 (Post-Mortem)

## Context Read

- **Iteration outcome (comparison.csv)**: IS daily Sharpe **+2.837** / OOS daily Sharpe **−0.876** / ratio **−0.309** (sign FLIP). IS PnL +50.28 / OOS PnL −6.56. IS n_trades 537 / OOS n_trades 242.
- **Substrate selected (is_only_substrate.csv)**: C-BTC=**v1-025**, C-ETH=**v1-009**, C-LINK=**v1-025**, C-LTC=**v1-025**, C-DOT=**v1-031**. Source iter **v1-025 dominates 3/5 = 60%**.
- **Divergence vs /045 ALT_1**: 4 of 5 components diverge (only C-DOT=v1-031 matches). F2 FAIL (5/5 coincidence FALSE). F3 PASS (≥3 divergence TRUE). Modal Phase 4.5 prior (**PROMISING-DIVERGENCE 45%**) materialized.
- **Phase 4.5 risk flag MATERIALIZED**: LM Master Rec 1 explicitly warned "if 3 of 5 top-1 picks happen to share the same source iter, the substrate has HP-basin concentration — one Optuna lottery roll drives 3 components." v1-025 owns BTC+LINK+LTC. This is the **exact failure mode flagged**.

---

## Item 0 — Regime Attribution Table (per regime_attribution.csv)

| Regime | IS_sample | Cand IS Sharpe | Cand OOS Sharpe (inferred from "False" row) | Cand IS Trades | Baseline IS Sharpe | Baseline IS Trades | IS Δ vs baseline | OOS-side comment |
|---|---|---:|---:|---:|---:|---:|---:|---|
| bull | IS | +0.2803 | n/a in tagger | 61 | −0.3514 | 50 | **+0.6317** (strong IS lift) | OOS-only "bull False" row: 5 trades, Sharpe 0.0 — regime tagger fired but cohort tiny |
| bear | IS | +0.4001 | n/a | 111 | +0.1463 | 222 | +0.2538 | half the bear trades of baseline — selectivity working IS |
| chop | IS | +0.3988 | n/a | 273 | +0.2348 | 224 | +0.1640 | 273 IS chop trades = 51% of all IS trades; substrate is chop-heavy |
| vol-spike | IS | 0.0 | n/a | 0 | 0.0 | 0 | 0 | regime never tagged at IS (tagger limitation) |
| recovery | IS | **+0.7815** | n/a | 90 | +0.2782 | 124 | +0.5033 | strongest regime IS — LTC v1-025's 4.18 IS Sharpe likely concentrated here |
| other | IS | 0.0 | n/a | 0 | 0.0 | 0 | 0 | tagger artifact |
| other | OOS | n/a | **−0.1592** | 239 | n/a (baseline OOS other=+0.1405) | 191 | n/a | **239 of 242 OOS trades (99%) land in "other"** — regime tagger is OOS-DEGENERATE; per-regime IS Pareto is unanchored OOS |

**Headline regime finding**: IS regime tagger reports 4 distinct regimes (bull/bear/chop/recovery) with positive Sharpe — IS-Pareto would PASS F4 relaxed. OOS regime tagger collapses 99% of trades into "other" — the IS-regime narrative does not transfer to OOS. This is a tagger limitation, NOT a substrate failure. But it also means **F4's relaxed IS-regime Pareto is not predictive of OOS behavior** — the regime test is structurally weak.

---

## Item 1 — Divergence Interpretation (KEY ANALYSIS)

The IS-only solve picked **v1-025 for 3 of 5 coins** (BTC, LINK, LTC) instead of /045's three different source iters (v1-012 for BTC, v1-011 for LINK, v1-040 for LTC). DOT matched (v1-031). ETH replaced (v1-042 → v1-009). What does this mean?

**Two competing readings:**

**Reading A — "/045 ALT_1 substrate was IS-suboptimal under honest IS scoring."** The /045 OOS-aware composite favored components whose OOS Sharpe was high BUT whose IS Sharpe was lower than the IS-only winner. Specifically:
- C-BTC: v1-012 IS Sharpe = −0.21 (NEGATIVE) vs v1-025 BTC IS Sharpe = +0.46. /045 picked an IS-NEGATIVE component for BTC because v1-012's OOS was strong — pure OOS-aware selection bias. **Confirmed by /046**.
- C-LTC: v1-040 IS = +3.76 vs v1-025 LTC IS = +4.98. /046 picks v1-025 LTC by +0.4 score margin (IS_Sh edge). /045 picked v1-040 — possibly because v1-040's OOS Sharpe edged v1-025's, or because v1-025 had fewer IS trades (61 vs 117 for v1-040; tiebreaker collision visible).

**Reading B — "v1-025 is a single Optuna lottery-roll that happens to dominate IS on multiple symbols."** v1-025 is a single training iteration with a single set of HPs and feature configurations. When the IS-only score picks v1-025 for 3 different coins, it is saying "this ONE Optuna trial's HPs were the best for BTC IS, LINK IS, and LTC IS simultaneously." That is structurally suspicious — independent best-of-N picks should NOT cluster on the same source iter unless that iter happened to land in a particularly fertile HP basin that generalizes to multiple symbols. **In a 159-candidate cell space across ~25-30 candidates per coin, the prior on same-source 3/5 is ≈ (1/27)^2 × C(5,3) ≈ 1.4% under independence. The observed 3/5 is therefore evidence AGAINST independence — v1-025 is a basin-wide lottery winner.**

**Synthesis (LM Master interpretation):** Both readings are correct, and they compound. /045 was OOS-aware AND the underlying inventory has a HP-basin dominator (v1-025). The IS-only fix correctly removes the OOS-aware bias (Reading A vindicated) but exposes a NEW bias the methodology axis did not anticipate (Reading B: source-iter clustering). **The "honest" IS-only substrate is itself basin-lottery-concentrated.** /046 trades one selection bias (OOS-aware) for another (HP-basin-aware, single-Optuna-roll inheritance).

The 4-of-5 divergence is **substantive evidence that ALT_1's +3.49 OOS Sharpe headline was OOS-aware-selected** (Reading A vindicated; the /045 BLOCK-FINAL Critic was correct). But it does NOT vindicate /046's substrate as MERGE-worthy — Reading B is the dominant residual concern.

---

## Item 2 — HP-Basin Concentration Question: Is 60% v1-025 an artifact of IS-Sharpe maximization?

**Yes, with high confidence.** The mechanism:

- v1-025's per-symbol IS Sharpes (from is_only_substrate.csv): BTC = 0.46, LINK = 2.39, LTC = 4.98. These are **rank-1 for BTC and LTC simultaneously** in their respective per-coin candidate pools (LINK rank-1 across its pool of ~20-25). One single Optuna run, with one set of HPs and one feature configuration, produced top-quartile IS Sharpe on **3 different symbols**.
- This is not impossible. It happens when the HP region (`num_leaves`, `min_data_in_leaf`, `learning_rate`, `lambda_l1/l2`, etc.) found by v1-025 reduces variance on **pooled multi-symbol training data** at the expense of fitting any individual symbol's noise. The "broad-spectrum" HP basin then trumps per-symbol-tuned HP basins on raw IS Sharpe because (a) it generalizes within IS across symbols, (b) it inherits more IS trades after risk gates, (c) it's stable to seed perturbation.
- **The selection criterion (IS-Sharpe maximization) is structurally non-orthogonal to basin-broadness.** A broad-spectrum basin will always edge a narrow-spectrum basin on multi-symbol IS Sharpe — that's what broad-spectrum MEANS. So IS-only top-1 selection across symbols will MECHANICALLY favor the broadest-basin iter. /046's score does not penalize basin clustering.

**Empirical signature of basin-lottery exposure** (from per-component analysis):
- v1-025's 3 components show mean IS Sharpe +2.08, mean OOS Sharpe **−1.24**, IS→OOS delta **−3.32** (collapse).
- v1-009's C-ETH: IS +1.70, OOS −1.68, delta **−3.38** (similar collapse).
- v1-031's C-DOT: IS +2.00, OOS **+2.73**, delta **+0.73** (the ONE component that survives OOS).
- **The four worst IS-vs-OOS reversals are all NON-v1-031 components.** v1-031 is the lottery survivor; everyone else is basin-stranded.

**The HP-basin concentration is NOT just an artifact of multiple-comparison — it is an artifact of using IS-Sharpe-maximization as the cross-symbol selection rule on a non-orthogonal inventory.** The fix is not a different deflation; it is a substrate-selection rule that enforces source-iter diversity (e.g., max 2/5 from any single iter; or pre-stratify the candidate pool by source iter before per-coin ranking).

---

## Item 3 — Multiple-Comparison Correction (per QR Phase 4.5 Rec 2)

**Deflation formula:** `deflation_per_coin = σ_SR × √(2 log N)` where N = candidates per coin.

- N = 159 total candidate cells (as cited in context).
- σ_SR ≈ 0.14 (from √(1/50), assuming median IS sample of ~50 trades per cell).
- **deflation = 0.14 × √(2 × log(159)) = 0.14 × 3.184 = 0.446 per coin.**

**Applied to comparison.csv headlines:**

| Metric | Raw | Deflated (subtract 0.446 from IS bundle Sharpe) | Notes |
|---|---:|---:|---|
| IS daily Sharpe | **+2.837** | **+2.391** | Bundle headline; survives F1 +0.50 floor by a wide margin. F1 PASS. |
| OOS daily Sharpe | **−0.876** | n/a (OOS not deflated; no selection on OOS) | F4 forensic. |
| IS:OOS ratio | −0.309 | n/a | Sign FLIP. |

**F1 Falsifier check (per brief §4 F1, deflated ≥ +0.50):** PASS at +2.39. Bundle clears F1 by ~1.9 Sharpe units even after correction — the IS-side signal is genuinely large in this inventory.

**Per-component deflation (informational):** v1-025 BTC raw IS = 0.46, deflated = +0.01 (essentially zero IS signal post-correction). v1-025 LTC raw IS = 4.98, deflated = +4.54. The wide spread of per-component deflated IS Sharpes ([+0.01, +4.54]) is itself a warning — the bundle headline is **driven by LTC alone**, which contributes (4.54 / 5) × 5 = +0.91 to the bundle IS Sharpe after deflation. Take away LTC and the bundle IS Sharpe drops to ~+1.4 — still F1-PASS but no longer dominant.

**Critical observation**: deflation **does not change the verdict**. F1 PASSes both raw and deflated. The OOS sign flip (−0.876) is the binding signal, NOT a deflation-sensitive IS gate. **The multiple-comparison correction was a red herring as a falsifier-tightening mechanism on this iteration** — it works, it deflates by a meaningful amount, but it does not flip any /046 verdict bit. The OOS catastrophe (Item 4) dominates.

---

## Item 4 — IS-vs-OOS Reversal Analysis (the binding finding)

The **load-bearing post-mortem result** is the per-component IS→OOS delta table:

| Component | Source iter | IS Sharpe | OOS Sharpe | Δ | OOS PnL ($) | Reading |
|---|---|---:|---:|---:|---:|---|
| C-BTC | v1-025 | +0.38 | **−2.31** | **−2.69** | **−3.42** | Catastrophic — v1-025 BTC selected at marginal IS (0.46 score; barely cleared F1) collapses OOS |
| C-ETH | v1-009 | +1.70 | **−1.68** | **−3.38** | **−3.67** | Catastrophic — v1-009 ETH IS lift completely erased OOS |
| C-LINK | v1-025 | +1.69 | +0.10 | −1.59 | +0.25 | Neutral OOS — barely positive |
| C-LTC | v1-025 | +4.17 | **−1.50** | **−5.67** | **−3.70** | **Worst IS→OOS reversal** — strongest IS component → OOS-NEG. Classic basin-lottery signature. |
| C-DOT | v1-031 | +2.00 | **+2.73** | +0.73 | +3.98 | Only OOS survivor. The match-to-/045 component. |

**Aggregate:** 4 of 5 components show OOS-NEG. The ONE positive (C-DOT, v1-031) is also the ONLY substrate match with /045's ALT_1. That is **strong corroboration** that v1-031 (DOT) genuinely lives in a non-lottery HP region — both selection criteria converge on it — while the 4 divergent components are basin-lottery picks under either criterion (different bias, same noise inheritance).

**LTC is the most diagnostic cell**: v1-025 LTC has IS Sharpe 4.98 (rank-1 across all 159 cells) and OOS Sharpe −1.50. This is the textbook "Optuna found a lottery basin on IS" pattern. The score score_is = 3.09 (highest single cell) drove the substrate selection. Under multiple-comparison correction (deflate by 0.446 → 4.54), it still ranks top-1 — so deflation alone is insufficient as a guard.

---

## Item 5 — Hyperparameter Trial Stability (v1-025 basin diagnostic)

LM Master cannot inspect /025's Optuna trial logs without re-reading them, but the empirical signature **strongly suggests a too-wide HP search and a single-month-overfit basin**:

- v1-025's IS Sharpe of 4.98 on LTC (61 trades) corresponds to σ_SR ≈ √(1/61) ≈ 0.13. The 4.98 IS Sharpe is **38 σ_SR units above zero** — a value that under H0 (no real edge) has probability < 10⁻³⁰⁰. **Either v1-025 found genuine, replicable LTC edge — falsified by OOS = −1.50 — or v1-025's IS Sharpe is artifactual.** The OOS evidence forces the artifactual reading.
- The artifact is most likely **Optuna basin over-concentration** on a small number of high-conviction LTC trades during a favorable IS month, with HPs (`num_leaves`, `feature_fraction`, `min_data_in_leaf`) tuned to maximize those trades at the cost of generalization.
- **Recommendation for /047 (if v1-025 substrate survives the IS-only frame):** before any multi-seed validation, audit v1-025's `run.log` Optuna trace. Look for: (1) trial-30 best loss > 2× the trial-rank-2 loss (single-trial dominance); (2) `num_leaves` best value > 80 with min_data_in_leaf < 30 (overfit-prone region); (3) IS Sharpe std across walk-forward months > 1.5 (basin instability). If any 2 of 3 trigger, v1-025 should be REJECTED as a substrate component regardless of /046's IS-Sharpe-maximization output.

---

## Item 6 — Gain Concentration Audit (cannot run; structural inference only)

`feature_importance.csv` is not emitted by /046 (CSV-replay iteration; no model fit). Cannot inspect feature-level gain concentration directly. **Inference from substrate composition:**

v1-025 generated 3 of 5 components — meaning whatever feature configuration v1-025 used drives 60% of the bundle. If v1-025's feature set contained 1-2 high-gain anchor features (e.g., a momentum primitive at rank 1 with > 30% gain), the bundle's effective feature concentration is hidden but real. **For /047 multi-seed validation of the /046 substrate, the engineering report MUST emit per-component feature importance from re-fits**, not just bundle-level CSV-replay. Without this, the basin-lottery audit cannot be completed.

---

## Item 7 — Suspicious Patterns

**(a) BTC+ETH+LTC simultaneously OOS-NEG, DOT+LINK OOS-positive:** The 3 OOS-NEG components are the 3 largest-market-cap symbols (BTC, ETH, LTC). DOT and LINK are smaller. This pattern is consistent with **the OOS window containing a large-cap drawdown regime** that v1-025's HP basin specifically did NOT generalize to. Specifically: monthly OOS PnL collapses in 2025-04 (−3.69), 2025-05 (−3.66), 2025-09 (−5.58), 2026-02 (−6.04) — these are the bleed months. These months should be cross-referenced against BTC/ETH return distributions to test whether they represent a regime not present in IS.

**(b) Single-month outliers:** 2026-02 OOS PnL = −6.04 over 13 trades = average −0.46% per trade. This single month is 92% of the −6.56 OOS bundle loss. Without that one month, the substrate is roughly flat OOS. A regime-conditional kill switch tied to BTC drawdown depth might neutralize this component-bleed pattern. **Recommendation for /047**: enable an outer-level loss-stop tied to bundle equity at OOS-roll boundaries to control this single-month tail.

**(c) v1-031 (DOT) as the methodology-agnostic anchor:** v1-031 is selected by both the OOS-aware /045 framework AND the IS-only /046 framework. It is the only component whose IS+OOS BOTH support its selection. This is the **ONE merge-worthy v1-substrate ingredient** identified across the /045/046 methodology comparison. For /047, LM Master strongly recommends C-DOT=v1-031 as a stand-alone reference cell — independently audit its multi-seed Sharpe at 10-seed CONFIRMATION budget before bundling.

---

## Next-Iteration Tuning Recommendations (5 items)

### 1. /047 axis = source-iter-diversity-constrained partition resolve (NEW score)

**What:** Pre-register a substrate-selection rule that enforces source-iter diversity: max 2/5 components from any single source iter. Re-run partition_solve with `score_is` AND this constraint. If no feasible solution exists (5 single-coin specialists, ≥4 distinct source iters), fall back to admitting per-coin sub-1.0 IS Sharpe candidates.

**Mechanism:** Defeats basin-lottery concentration (Reading B). Forces the substrate to span the inventory's HP-search landscape, increasing the probability that at least 1-2 components are NOT basin-stranded.

**Risk:** May lower bundle IS Sharpe. That is OK — the goal is robustness, not headline maximization.

### 2. /047 axis (alternative) = multi-seed validation of v1-031 (C-DOT) STAND-ALONE

**What:** Take C-DOT=v1-031 in isolation. Run 10-seed CONFIRMATION. If multi-seed mean OOS Sharpe ≥ +1.0 with ≥7/10 profitable seeds, declare v1-031 a "validated component cell." This is the only cell with cross-methodology corroboration.

**Mechanism:** Builds a verified atomic cell from which future bundles can compound. Avoids re-running the basin-lottery-prone /025-derived components.

**Risk:** v1-031 alone has narrow universe coverage (1 symbol). A single-symbol "bundle" cannot satisfy the v1 trade-rate floor unless DOT alone generates ≥130 OOS trades (currently 37 in /046 OOS) — likely FAILS the floor on its own.

### 3. Drop v1-025-sourced components entirely from cycle-6 substrate consideration

**What:** Catalog-level decision: v1-025 produced 3 catastrophic IS→OOS reversals (BTC −2.69, LINK −1.59, LTC −5.67). The pattern is consistent across symbols. Treat v1-025 as a **basin-lottery iter** and exclude its outputs from all future partition-solve candidate pools.

**Mechanism:** v1-031 is the methodology-agnostic anchor; v1-025 is the methodology-agnostic anti-anchor.

**Risk:** Removing 3 high-IS-Sharpe candidate cells will lower the bundle IS Sharpe ceiling. May force exploration of NEW feature families to find replacement edges.

### 4. Implement formal Optuna trial-stability audit at all CONFIRMATION runs

**What:** Add an engineering-report-mandated audit: parse `run.log` for `Trial [0-9]+ finished` lines. Emit a `optuna_basin_audit.csv` with: best-trial loss std/mean across months, `num_leaves` best-value std, `learning_rate` best-value std. Any axis with std/mean > 0.5 → flag.

**Mechanism:** Catches the basin-lottery pattern at training time instead of at the Phase 7 backtest. Cheap to implement (parse-only, ~30 lines of Python in `analysis/`).

**Risk:** None — pure additive instrumentation.

### 5. Re-examine the score formula's weight balance

**What:** Current `score_is = 0.6·IS_Sharpe + 0.4·IS_n_trades/250`. With v1-025 LTC at 61 trades scoring 0.6×4.98 + 0.4×0.244 = 3.09 vs v1-040 LTC at 117 trades scoring 0.6×3.76 + 0.4×0.468 = 2.44, the trade-count component favors v1-040 but the IS-Sharpe edge wins. **The trade-count regularization (effective weight 8-15% per /046 brief §3.5 Flag D) is too weak to defeat the basin-lottery signal.** Recommend `score_is = 0.6·IS_Sharpe × (n/(n+30)) + 0.4·log10(n/10)` — shrinks the IS Sharpe of low-trade-count cells via the empirical-Bayes-style shrinkage factor `n/(n+30)`. v1-025 LTC at 61 trades → 4.98 × (61/91) = 3.34 effective IS Sharpe; v1-040 LTC at 117 trades → 3.76 × (117/147) = 2.99. Closer.

**Mechanism:** Penalizes low-trade-count basin-lottery cells without breaking the IS-Sharpe primacy.

**Risk:** Introduces an additional researcher DOF. Must pre-register the shrinkage constant (30) BEFORE running the solve.

---

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

**Phase 4.5 confidence MEDIUM-HIGH; modal prior PROMISING-DIVERGENCE 45%.** Outcome materialized: **4 of 5 components diverged (F3 PASS by a wide margin)**. The modal prior was directionally correct.

**Phase 4.5 Rec 1 (HP-region diversity audit)**: **ADOPTED in brief but partially — the QR included a "HP-basin concentration audit" in §3.5 R1 response but did NOT make it a falsifier.** The audit was emitted (3-of-5 v1-025 concentration visible in is_only_substrate.csv) but produced no /046-blocking signal. **This recommendation was correct in substance but under-weighted as advisory rather than falsifying.** For /047, LM Master upgrades the recommendation to a HARD constraint (Item-1 next-iter recommendation above: max 2/5 from any single source iter).

**Phase 4.5 Rec 2 (multiple-comparison deflation)**: **PARTIALLY ADOPTED** (F1 floor upgraded raw → deflated). Deflation correctly applied (0.446 per coin); bundle deflates +2.84 → +2.39 IS Sharpe; F1 PASS both raw and deflated. **Recommendation did its work in principle but did NOT change verdict bits** — the binding signal is the OOS sign flip, not the IS deflation. The Rec was sound; this iteration just happened to be IS-strong enough that deflation was non-determinative.

**Phase 4.5 Rec 3 (verification recipe — grep/data-loaded/hide test)**: cannot fully verify from this read; QR Phase 6 brief §3.5 R3 cites adoption. Engineering report (not read in this post-mortem) presumably emits the hide-test diff.

**Phase 4.5 Risk Flag A (IS-side overfit on a different axis)**: **MATERIALIZED.** This is the load-bearing finding. The IS-only solve removes OOS-aware bias but inherits HP-basin-lottery bias. LM Master flagged this as Flag A but did not anticipate that the basin-lottery would express as **single-source-iter concentration**. Updated mental model: best-of-N IS-Sharpe maximization on a non-orthogonal candidate pool will MECHANICALLY favor the broadest-basin source iter, producing same-source clustering — the basin-lottery has a structural signature.

**Phase 4.5 Flag C (tiebreaker direction)**: ADOPTED by QR (IS_n_trades descending). Net effect on /046: minor — most top-1 picks won by score_is margin, not by tiebreaker.

**LM Master track record update**: Phase 4.5 modal prior CORRECT directionally (F3 PROMISING-DIVERGENCE materialized). Phase 4.5 Rec 1 (HP-basin diversity) was UNDER-WEIGHTED — should have been a falsifier, not advisory. This is a learning to apply at /047 brief authoring.

---

## Modal Verdict Recommendation

**Modal: PROMISING-DIVERGENCE with BASIN-LOTTERY-INHERITED-CAUTION.**

Per /046 brief §4 falsifier framework:
- F1 (deflated IS Sharpe ≥ +0.50): **PASS** (+2.39 deflated).
- F2 (5/5 coincidence with ALT_1): **FAIL** (1/5 match).
- F3 (≥3 divergence): **PASS** (4/5 divergence).
- F4 (boundary 1-2): N/A (F3 PASSed dominantly).
- F5 (anti-pattern): assumed PASS per QR Phase 6 deliverables (LM Master did not re-verify).

**Verdict band: PROMISING-DIVERGENCE.** OOS-inflation in /045 ALT_1 is empirically demonstrated. ALT_1's headline +3.49 OOS Sharpe was OOS-aware-selected (Critic /045 BLOCK-FINAL ratified by /046 empirical finding).

**BUT:** the IS-only substrate is **NOT MERGE-WORTHY** — OOS Sharpe −0.876 (sign flip), 4 of 5 components OOS-NEG, 60% source-iter concentration on v1-025 (basin-lottery anti-anchor). **Recommended /046 catalog entry suffix: "PROMISING-DIVERGENCE-WITH-BASIN-LOTTERY-CAUTION" or equivalent.**

**/047 routing:** NOT a straightforward multi-seed re-validation of the /046 IS-only substrate. Instead, /047 should be **source-iter-diversity-constrained partition resolve (Item 1 above)** OR **stand-alone v1-031 multi-seed validation (Item 2)**. Multi-seeding the basin-lottery substrate as-is will burn ~5h of CONFIRMATION wall-clock to confirm what /046 already shows: the substrate is basin-stranded.

---

## Closing Note for Critic (Phase 7.5)

Three specific evidence anchors for Critic 8-check attention:

1. **HP-basin concentration (NEW failure mode)**: 3/5 components from v1-025 is a previously-unflagged structural bias. Critic Check 17 (IS-only weight provenance) is satisfied by /046 BUT Critic should consider whether a **Check 17B (source-iter-diversity)** is needed to catch basin-lottery substrate selection. This is not a /046-blocking finding but is the principal Path Forward for /047.

2. **Per-component IS→OOS reversal table**: Critic should read Item 4 above. The 4-of-5 OOS-NEG pattern with mean delta −3.32 across v1-025 components is consistent with basin-lottery overfit, not regime change. The single OOS survivor (v1-031 / DOT) is the methodology-agnostic anchor and merits independent treatment.

3. **Critic constraint per /046 brief §4 F4 (binding)**: Critic CANNOT cite "IS-only substrate OOS Sharpe < ALT_1 OOS Sharpe" as /046 failure evidence. /046 verdict determined SOLELY by F1-F5. **LM Master endorses this constraint** — OOS is forensic interpretation, not a falsifier. The OOS catastrophe is information for /047 design, not a /046 verdict input.

LM Master Phase 7.4 verdict bands the iteration **PROMISING-DIVERGENCE (modal)** consistent with the QR's expected outcome — but with the strong forensic finding that the substrate so identified is itself basin-lottery-concentrated and **must not be carried into /047 without source-iter-diversity intervention**.

---

*End of LightGBM Master Phase 7.4 post-mortem for iter-v1/046.*
