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
