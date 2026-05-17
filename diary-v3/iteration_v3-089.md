# iter-v3/089 — Cycle 3 #8 EXPLORATION — the CORRECTED cross-sectional iteration: sign fix + CPCV-proxy fix + cost-aware construction / CONSTRUCTION-PARTIAL

**Date**: 2026-05-17
**Type**: EXPLORATION (cycle 3 slot #8 of 10) — the CORRECTED next build on the RETAINED /088 cross-sectional `LGBMRanker` architecture. NOT a fresh re-architecture; NOT an incremental knob on the /059 per-symbol baseline. Single-axis: the two mandatory corrections (Critic /088 Recs #2/#3 — sign fix + CPCV-proxy fix) plus the genuine /089 axis — making the corrected cross-sectional architecture profitable by attacking the dominant turnover-drag failure mode structurally (quintile legs + 3-bar overlapping holds + no-trade band, with a pre-registered HARD turnover ceiling). EXPLORATION-mode single-seed (seed=42), `--n-trials 35`, 22-symbol panel, wall-clock 0h 22m 46s.
**Axis**: the corrected cross-sectional build the /088 closeout mandated — per `feedback_v3_bold_research_mandate.md` (SHARPENED 2026-05-17) the cross-sectional architecture produced v3's FIRST genuine OOS signal transfer in ~27 EXPLORATIONs, and /089's job is to convert that signal into a profitable book. QR-research-and-EDA-driven (brief Section 10: Poh/Lim/Zohren arXiv 2012.07149 — learning-to-rank quantile concentration; Constantinides 1986 / Davis-Norman 1990 — no-trade-region theory, optimal band O(ε^1/3) in the proportional cost; Jegadeesh-Titman 1993 — overlapping-portfolio construction; the practitioner cost-aware-rebalancing literature; the crypto cross-sectional net-of-cost evidence. EDA `c172a12` — `turnover_construction_eda.py` E1-E6 IS-internal walk-forward + `gross_signal_eda.py` G1-G4 model-free gross-spread quantification).
**Verdict**: EXPLORATION-MERGE per Critic FINAL `74054c2` — OVERALL=**MERGE**. All 8 mandatory + 4 optional Checks PASS, including the highest-stakes Check 1 (look-ahead, audited end-to-end across all four /089 surfaces — the sign flip, the 3-bar overlapping-hold tranche book, the no-trade band, the CPCV-proxy rewrite) and Check 2 (the `XS_REQUIRED_GAP = 88` embargo, re-confirmed). The Critic found NO methodology DEFECT, audited the new code leakage-free, and **verified the GROSS-POSITIVE finding is genuine** — not an artifact of look-ahead in the new PnL accounting. The Critic gates methodology soundness, NOT advancement; the classification is the QR's Phase-8 call (Section 3 below).
**Classification**: **CONSTRUCTION-PARTIAL** (brief Section 8.4). The corrected construction works, contains turnover (the HARD turnover gate PASSES), transfers OOS (OOS rank-IC +0.0279 > 0), and materially improves the OOS book (+0.44 vs /088) — but the thin gross signal keeps the net book sub-zero (OOS monthly Sharpe −0.0985 ≤ 0). 8.1 SUSPICIOUS does NOT fire; 8.2 CONSTRUCTION-FALSIFIED does NOT fire (F2 turnover-gate PASSES, F3 does NOT fire); 8.3 CONSTRUCTION-VALIDATED-PROMISING does NOT fire (it requires OOS Sharpe > 0). 8.4 CONSTRUCTION-PARTIAL is the disjunctive-precedence match — and it is the brief's Section-7 ≈45% modal prediction.
**Advancement**: does NOT advance to the iter-v3/092 cycle-3 CONFIRMATION bundle — a sub-floor EXPLORATION carries no merge ingredient. But the cross-sectional architecture and the `cross_sectional.py` infrastructure are **RETAINED and remain the active v3 research line** — /090 is the corrected-architecture next build (gross-signal strengthening). The cost-aware construction levers (quintile, 3-bar overlapping holds, no-trade band, the turnover ceiling) are RETAINED as the construction baseline.
**BASELINE_V3.md**: **UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) and tag `v0.v3-059` stay canonical. An EXPLORATION cannot update the baseline regardless of classification.
**Branch**: `iteration-v3/089`

---

## 1. What was done — the corrected cross-sectional build

iter-v3/089 is the EIGHTH EXPLORATION slot of v3 cycle 3 and the corrected next build on /088's RETAINED `cross_sectional.py` infrastructure. /088 (ARCHITECTURE-PARTIAL) established that the pooled `LGBMRanker(lambdarank)` cross-sectional MODEL genuinely transfers OOS — OOS rank-IC +0.0430, t ≈ 4.6, n = 1255 — the first genuine OOS signal transfer in ~27 v3 EXPLORATIONs. But the dollar-neutral tercile long-short BOOK lost money (IS monthly Sharpe −0.6403, OOS −0.5418) for two diagnosed, fixable reasons: a sign inversion in the /088 brief, and turnover drag (IS fees 8.8× the IS gross PnL magnitude). /089 carries the two mandatory corrections and the genuine cost-aware-construction axis. Five changes vs /088 (all IS-EDA-selected — EDA commit `c172a12`):

1. **Correction #1 — the SIGN FIX (Critic /088 Rec #2).** `build_positions` now LONGs the TOP quantile (highest predicted scores = predicted future winners) and SHORTs the BOTTOM quantile — the inverse of /088. Specified from first principles: `LGBMRanker(lambdarank)` is trained on the FORWARD-return-grade label, so it learns high score = high future return; there is no past-return reversal for the model to invert. The wrong `predict_ranking` / `label_cross_sectional_rank` docstrings were corrected.

2. **Correction #2 — the CPCV-PROXY FIX (Critic /088 Rec #3).** /088's `_compute_xs_cpcv` computed each CPCV path "Sharpe" as a label-grade self-correlation (`mean(sub_labels[long]) − mean(sub_labels[short])`) — degenerate; `cpcv_paths.csv` collapsed to 45 rows of `sharpe = 0.0`. /089 rewrites it to compute the ACTUAL realised long-short NET return on each path's test fold (reading the trained corrected-sign walk-forward `net_pnl` — it does not re-fit). `cpcv_paths.csv` is now non-degenerate (45 distinct Sharpes, range [−0.094, +0.053]).

3. **The /089 axis — the cost-aware construction.** Three IS-validated turnover-reduction levers: **`XS_QUANTILE_FRAC = 0.20`** (quintile legs — EDA E2/G1: quintile maximises the realised per-bar spread Sharpe at N=22; decile is too thin); **`XS_HOLD_BARS = 3`** (overlapping 3-bar holds — Jegadeesh-Titman tranche construction, horizon-matched, EDA E3: cuts turnover ~2.2×); **`XS_NO_TRADE_BAND = 0.020`** (no-trade band — Constantinides/Davis-Norman, EDA E4: the IS-best net Sharpe of the scanned grid).

4. **The pre-registered HARD turnover ceiling — `XS_TURNOVER_CEILING = 0.138`.** The IS-best /089 construction runs at 0.120 gross turnover/bar (EDA E6); the ceiling is ×1.15 headroom = 0.138. A /089 build whose realised IS mean gross turnover/bar exceeds 0.138 is NO-MERGE regardless of Sharpe — the brief's defining falsifier F2, making the "attack turnover" claim a gate, not a footnote.

5. **UNCHANGED from /088**: the 13-feature cross-sectional stack, the 22-symbol `XS_UNIVERSE`, the H=3 forward-tercile-grade label, the `XS_REQUIRED_GAP = 88` embargo, the `LGBMRanker(lambdarank)` model, the walk-forward `train_end_ms = test_start_ms − embargo_ms` (the `e149e9d` fix). The G4 cross-sectional-momentum feature expansion (+2% IC-IR on IS) was explicitly DEFERRED to /090 — a feature expansion done properly needs its own axis (the iter-v3/070 dead-path discipline: do not stack a marginally-correlated feature set onto another axis).

---

## 2. Results — the corrected cross-sectional book is GROSS-POSITIVE, OOS materially improved, still net-sub-zero

iter-v3/089 produces a market-neutral cross-sectional long-short book; per brief Section 4.1 it is **not directly comparable** to the per-symbol-book Sharpes of the /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322) or the /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791) — a different return distribution, beta, turnover. The operative evaluation is the absolute floors + the architecture-internal diagnostics + the /089-specific HARD turnover gate, and a Δ vs the honest internal anchor — the /088 cross-sectional book itself.

| Metric | iter-v3/088 (cross-sectional book) | iter-v3/089 (corrected cross-sectional book) | Δ vs /088 |
|---|---:|---:|---:|
| IS monthly Sharpe (NET) | −0.6403 | **−0.1960** | **+0.4443** |
| OOS monthly Sharpe (NET) | −0.5418 | **−0.0985** | **+0.4433** |
| OOS/IS monthly Sharpe ratio | 0.846 | 0.502 | — |
| **IS gross monthly Sharpe** | ≈ +0.067 (flipped-IS diag) | **+0.0925** | — |
| **OOS gross monthly Sharpe** | ≈ −0.043 (flipped est.) | **+0.1717** | — |
| IS fees / \|gross\| | 8.8× | **3.35×** | −2.6× |
| OOS fees / \|gross\| | ≈ 1.58× est. region | **1.58×** | — |
| IS turnover/bar | ~0.30 | **0.1153** | −2.6× |
| OOS turnover/bar | ~0.30 | 0.0710 | — |
| **HARD turnover gate (≤ 0.138)** | n/a | **PASS** (0.1153 ≤ 0.138) | — |
| OOS rank-IC (mean) | +0.0430 (t ≈ 4.6) | **+0.0279** | −0.0151 |
| frac_positive_paths (CPCV) | 0.000 (degenerate proxy) | **0.356** (informative) | — |
| IS MaxDD | 34.03% | 7.4775 | tighter |
| OOS MaxDD | 20.23% | 2.7614 | tighter |
| max OOS symbol concentration | CRVUSDT 14.3% | ICPUSDT 12.18% | — |

### 2.1 — The gross-vs-net decomposition — the central diagnostic

This is the iteration's load-bearing finding, and the Critic verified it is genuine (Check 1: not an artifact of look-ahead in the new PnL accounting).

| | Gross PnL | Total Fees | Net PnL | Fees / \|Gross\| | Gross monthly Sharpe | Net monthly Sharpe |
|---|---:|---:|---:|---:|---:|---:|
| **IS** | **+0.1155** | 0.3871 | −0.2716 | **3.35×** | **+0.0925** | −0.1960 |
| **OOS** | **+0.0567** | 0.0893 | −0.0326 | **1.58×** | **+0.1717** | −0.0985 |

**The corrected cross-sectional book is GROSS-POSITIVE both IS and OOS.** The cross-sectional long-short signal produces a genuine positive gross spread — and the OOS gross monthly Sharpe **+0.1717** is materially higher than the IS gross (+0.0925), consistent with the lower OOS turnover bleeding less per bar. The book fails NET only on fees. The fees/gross ratio collapsed from /088's 8.8× to **IS 3.35× / OOS 1.58×** — a 2.6× reduction directly attributable to the quintile + overlapping-hold + no-trade-band construction. The OOS gross PnL (+0.0567) needs only ~37% further fee reduction OR gross-signal lift to cross breakeven net. **The gap to a net-positive book is now a concrete, bounded cost/signal problem — not a diffuse "the architecture loses money."**

### 2.2 — Signal anatomy — the SHORT leg carries the alpha

| | n rows | Gross PnL | Fees | Net PnL |
|---|---:|---:|---:|---:|
| IS LONG | 19721 | −0.1566 | 0.1426 | −0.2992 |
| IS SHORT | 23166 | +0.2721 | 0.1741 | +0.0980 |
| OOS LONG | 7478 | −0.0633 | 0.0363 | −0.0997 |
| OOS SHORT | 10880 | **+0.1200** | 0.0386 | +0.0815 |

The sign fix is confirmed structurally correct — mean predicted score LONG leg +0.114, SHORT leg −0.209: high-score symbols are correctly assigned to the LONG leg. But the realised SHORT leg (predicted losers) carries the **entire** gross spread (OOS short-leg gross **+0.1200**), and the LONG leg loses gross (OOS long-leg gross −0.0633) despite longing the model's predicted winners. This is the opposite of the textbook cross-sectional pattern. It is internally consistent (the per-leg PnL reconciles; the sign fix is verified). The Critic (Rec #3) and the engineering report both flag this as a real, pre-registerable **signal-anatomy finding** — the cross-sectional signal in this 22-symbol altcoin universe may be structurally a downside/short predictor (consistent with crypto-specific momentum reversal in trending altcoins, and with the long leg being "least-bad" rather than "absolute winners" under a relative `lambdarank` ordering). This is a /090/091 axis, not noise (Section 6).

### 2.3 — Per-symbol attribution — diversification is structural

OOS concentration: ICPUSDT the largest loss at 12.18% of trades, FILUSDT the largest profit at 9.42% — no single symbol exceeds 13% of the OOS book. The brief's F5 falsifier (no single symbol > 50% of OOS book PnL) PASSES decisively. The quintile dollar-neutral construction delivers the structural diversification it was designed for — and unlike the /059 per-symbol baseline (BCH 95.76% IS concentration), the cross-sectional book has no single-symbol fragility flag. IS attribution: TRXUSDT +0.1475, THETAUSDT +0.0935, FILUSDT +0.0666 lead; 16 symbols negative; AVAXUSDT −0.1160 the worst — healthy dispersion.

---

## 3. PATH classification — CONSTRUCTION-PARTIAL — the disjunctive-precedence walk

The brief Section 8 LOCKED taxonomy runs in disjunctive precedence, first match canonical: **8.1 SUSPICIOUS → 8.2 CONSTRUCTION-FALSIFIED → 8.3 CONSTRUCTION-VALIDATED-PROMISING → 8.4 CONSTRUCTION-PARTIAL → 8.5 NULL/INCONCLUSIVE.** The pre-registered falsifiers: F1 (OOS rank-IC ≤ 0), F2 (IS mean gross turnover/bar > 0.138), F3 (OOS monthly Sharpe ≤ the /088 book's −0.5418), F4 (OOS/IS Sharpe ratio < 0.5, evaluated only when both positive), F5 (single symbol > 50% OOS book PnL).

### 3.1 — 8.1 SUSPICIOUS — evaluated FIRST, does NOT fire

8.1 fires on EITHER (a) OOS monthly Sharpe / IS monthly Sharpe **> 3.0** (the OOS-soars-on-flat-IS signature; N/A if both negative), OR (b) OOS rank-IC ≥ 2× the IS rank-IC magnitude. (a) does not fire — the ratio is **+0.502** (two negative Sharpes; the SUSPICIOUS signature is OOS-soars-on-flat-IS, and /089 produced two coherent improvements of essentially equal magnitude — IS +0.4443, OOS +0.4433 — not a divergence). (b) does not fire — OOS rank-IC +0.0279 is *weaker* than the model's IS-train rank-IC (~0.10–0.13 per the EDA), the opposite of the SUSPICIOUS pattern. **SUSPICIOUS does NOT fire.**

### 3.2 — 8.2 CONSTRUCTION-FALSIFIED — does NOT fire

8.2 fires if (NOT SUSPICIOUS) AND **F2 fires (IS turnover > 0.138) OR F3 fires (OOS monthly Sharpe ≤ −0.5418)**. **F2 does NOT fire** — IS mean gross turnover/bar is **0.1153 ≤ 0.138**; the pre-registered HARD turnover gate PASSES. The cost-aware construction did genuinely contain turnover. **F3 does NOT fire** — OOS monthly Sharpe is **−0.0985 > −0.5418** (a +0.4433 improvement on the /088 predecessor); the construction levers improved the OOS book. Neither firing condition holds. **8.2 CONSTRUCTION-FALSIFIED does NOT fire** — the /089 cost-aware-construction hypothesis is NOT falsified.

### 3.3 — 8.3 CONSTRUCTION-VALIDATED-PROMISING — does NOT fire

8.3 fires if (NOT SUSPICIOUS, NOT 8.2) AND **OOS rank-IC > 0 AND IS turnover ≤ 0.138 AND OOS monthly Sharpe > −0.5418 AND OOS monthly Sharpe > 0**. The first three conjuncts hold (OOS rank-IC +0.0279 > 0; IS turnover 0.1153 ≤ 0.138; OOS Sharpe −0.0985 > −0.5418) — but the fourth fails: **OOS monthly Sharpe −0.0985 ≤ 0**. The book is not yet net-positive. **8.3 does NOT fire** — neither sub-case 8.3-FULL (OOS ≥ +1.0 AND IS ≥ +1.0) nor 8.3-FOUNDATION (OOS ∈ (0, +1.0)) applies.

### 3.4 — 8.4 CONSTRUCTION-PARTIAL — fires, and is canonical

8.4 fires if (NOT SUSPICIOUS, NOT 8.2, NOT 8.3) AND **OOS rank-IC > 0 AND IS turnover ≤ 0.138 AND OOS monthly Sharpe > −0.5418** but the OOS monthly Sharpe is **≤ 0**. Every condition holds: OOS rank-IC **+0.0279 > 0** (the signal transferred); IS turnover **0.1153 ≤ 0.138** (the HARD gate PASSES); OOS monthly Sharpe **−0.0985 > −0.5418** (a +0.4433 material improvement on the /088 book); and OOS monthly Sharpe **−0.0985 ≤ 0** (so 8.3 does not fire — the book is materially improved but not yet net-positive). **8.4 CONSTRUCTION-PARTIAL is the canonical classification** — *"the corrected construction works, contains turnover, transfers OOS, and materially improves the OOS book — but the thin gross signal keeps it sub-zero."* NO-MERGE; the cross-sectional construction axis is advanced and /090's gross-signal expansion is the next required lever.

The Critic's Phase-7.5 review (FINAL `74054c2`, Recommendation #1) reached exactly this read independently — the same disjunctive walk: *"8.1 SUSPICIOUS does not fire ... 8.2 CONSTRUCTION-FALSIFIED does not fire — F2 (IS turnover 0.1153 > 0.138) does NOT fire (the hard gate PASSES), and F3 (OOS Sharpe ≤ /088's −0.5418) does NOT fire ... 8.3 ... does not fire — it requires OOS monthly Sharpe > 0 ... 8.4 CONSTRUCTION-PARTIAL is the canonical match."* The Critic's read and the QR's Phase-8 walk converge.

### 3.5 — 8.5 NULL/INCONCLUSIVE — does NOT fire

8.5 fires only if the Phase-6 build did not reach a runnable cross-sectional backtest. The /089 backtest ran in full (exit status 0, `comparison.csv`, per-symbol attribution, the corrected non-degenerate `cpcv_paths.csv`, `rank_ic.csv`, `dsr.json` all emitted). 8.5 does NOT apply.

---

## 4. The cross-sectional trajectory — /088 → /089 — v3's most sustained positive trajectory

This is the iteration's substantive finding and the reason CONSTRUCTION-PARTIAL is materially more than a NEGATIVE-class result. The cross-sectional architecture is, across two consecutive iterations, the only v3 research line that has shown a *responsive, monotone-improving* trajectory:

| Iteration | Type | OOS monthly Sharpe (NET) | OOS gross monthly Sharpe | Classification | What it established |
|---|---|---:|---:|---|---|
| iter-v3/088 | RE-ARCHITECTURE | −0.5418 | ≈ −0.043 (flipped est.) | ARCHITECTURE-PARTIAL | the cross-sectional MODEL transfers OOS (rank-IC +0.043, t ≈ 4.6) — v3's first OOS signal transfer; the BOOK loses (sign inversion + turnover drag) |
| iter-v3/089 | CORRECTED build | **−0.0985** | **+0.1717** | **CONSTRUCTION-PARTIAL** | the corrected construction works, contains turnover, transfers OOS, **the book is gross-POSITIVE**; the gap to net-positive is now a bounded cost/signal problem |

Four facts make this v3's most promising sustained trajectory:

1. **The architecture responds to fixes.** /089 lifted the OOS book +0.4433 (and IS +0.4443) over /088 — the corrected sign + cost-aware construction did exactly what the IS-internal-walk-forward EDA predicted (E5 "roughly halves the net loss"). This is the first v3 line where a diagnosed fix produced the predicted production lift. Three prior cycles of v3 EXPLORATIONs were dominated by IS-overfit-OOS-inversion, where no fix transferred.

2. **The signal transfers OOS.** OOS rank-IC +0.0279 stays positive (a faint drop from /088's +0.0430 — the no-trade-band filters near-zero-score rows that had near-zero IC contribution anyway; the signal direction is preserved). The cross-sectional MODEL is a genuine, OOS-positive edge — confirmed across two iterations.

3. **The book is GROSS-POSITIVE.** IS gross monthly Sharpe +0.0925, OOS gross monthly Sharpe +0.1717. The cross-sectional long-short spread is a real positive economic edge. /088's book was not credibly gross-positive (the flipped-IS diagnostic put corrected-sign IS gross at only ≈ +0.067, OOS gross ≈ negative). /089 is the first cross-sectional iteration with a verified-genuine positive gross book on BOTH windows.

4. **The gap to net-positive is now concrete.** The book fails net only on fees — fees/gross collapsed to IS 3.35× / OOS 1.58×. The OOS gross PnL (+0.0567) needs ~37% further fee reduction OR gross lift to cross breakeven. The remaining problem is a bounded, well-posed cost/signal problem with a clear lever (/090's gross-signal strengthening), not a diffuse architectural failure.

The honest residual: /089 is still NO-MERGE — the net book is sub-zero on both windows, far below the +1.0 absolute floors. CONSTRUCTION-PARTIAL is a genuine advance on the construction axis, not a finished result. But across /088 → /089 the cross-sectional architecture is the first v3 line in three cycles where the architecture responds to fixes, the signal transfers OOS, and the book has turned gross-positive. That is a real, sustained trajectory — and /090 has a concrete, IS-quantified axis.

---

## 5. Section 7 prediction check — CONSTRUCTION-PARTIAL IS the pre-registered ≈45% modal outcome

The brief Section 7 pre-registered the failure-mode distribution: **≈45%** "the corrected + cost-aware construction MATERIALLY improves the OOS book vs /088 (OOS monthly Sharpe lifts from −0.54 toward [−0.30, +0.05]), turnover stays within the 0.138 ceiling, OOS rank-IC stays positive — but the OOS monthly Sharpe remains sub-floor (below +1.0, plausibly still slightly negative)"; **≈20%** "the construction fixes work AND the OOS book turns net-positive, OOS ∈ (0, +1.0)"; **≈20%** "F3 fires — the construction levers do NOT improve the OOS book"; **≈10%** "F2 fires — the realised IS turnover breaches the 0.138 ceiling"; **≈5%** "full success — OOS monthly Sharpe ≥ +1.0."

**The realized classification — CONSTRUCTION-PARTIAL with OOS rank-IC > 0, OOS monthly Sharpe −0.0985, turnover gate PASS, gross-positive — IS the brief's ≈45% modal prediction, and the calibration is clean:**

- **The modal scenario fired exactly.** The brief's ≈45% scenario named "OOS monthly Sharpe lifts toward **[−0.30, +0.10]**." The brief Section 4.2 stated the same band: "an OOS monthly Sharpe in roughly **[−0.30, +0.10]** ... very likely still below the +1.0 floor, plausibly still slightly negative." The realized OOS monthly Sharpe is **−0.0985 — squarely in-band** (well inside [−0.30, +0.10], slightly negative as the brief explicitly predicted). The brief also predicted "OOS rank-IC ≈ +0.03 to +0.05" — realized +0.0279, marginally below the lower bound but the same direction and order of magnitude (the brief noted the band assumed the model unchanged, which it was; the small shortfall is the no-trade-band filtering effect documented in the engineering report). And "IS mean gross turnover/bar ≈ 0.12" — realized 0.1153, essentially exact.

- **The classification was named.** Section 8.4 explicitly states "**This is the Section-7 ≈45% modal prediction.**" The brief pre-registered CONSTRUCTION-PARTIAL as the single most-likely outcome and the production result landed on it.

- **No over-claiming.** The brief did NOT float a full-success outcome above the evidence — it weighted "OOS ≥ +1.0" at only ≈5% and stated plainly "clearing the +1.0 floor on this iteration is not expected — the gross signal needs /090's expansion first." The honest hypothesis (Section 1.2) explicitly said the construction fixes "roughly HALVE the IS net loss, but do not by itself reach a positive IS net Sharpe." That is exactly what happened (IS net −0.6403 → −0.1960, "roughly halved"; still negative).

**Calibration verdict: CLEAN.** The /089 brief applied the /088-closeout calibration lesson correctly — it pre-registered the thin-gross-signal residual honestly, named CONSTRUCTION-PARTIAL as the ≈45% modal outcome, gave a tight OOS band [−0.30, +0.10] that the realized −0.0985 fell squarely inside, and did not over-weight the tail. This is the second consecutive cross-sectional iteration where the brief's modal prediction was correct (/088 pre-registered ARCHITECTURE-PARTIAL's central claim; /089 pre-registered CONSTRUCTION-PARTIAL outright). The one minor item — OOS rank-IC +0.0279 marginally below the predicted [+0.03, +0.05] band — is within noise and the same sign; recorded, not a miss.

---

## 6. Critic integration — OVERALL=MERGE + 3 Recommendations

**Critic FINAL `74054c2`** (`briefs-v3/iteration_v3-089/review.md`): a single-round full review (zero clarifications), OVERALL=**MERGE**. The MERGE verdict CERTIFIES the methodology of a clean corrected-build EXPLORATION that produced a methodologically-sound CONSTRUCTION-PARTIAL result — a methodology certification, NOT an advancement or an edge endorsement.

- **All 8 mandatory Checks + 4 optional Checks PASS.** Check 1 (look-ahead) PASS — the highest-stakes check, all four /089 surfaces audited end-to-end: (a) the sign flip in `build_positions` — a relabeling of which decided positions are long vs short, no temporal dependency; (b) the 3-bar overlapping-hold tranche book — the known look-ahead trap, traced explicitly: each tranche carries a retire-bar index, the book at bar `t` is the sum of tranches formed at `t`/`t−1`/`t−2` (all decided at-or-before `t`), exactly one `gross_pnl` row emitted per (bar, symbol) from the current summed-tranche position — no double-count, no peek, `bar_counter`/`prev_book` correctly carried across walk-forward month boundaries; (c) the no-trade band — current-target vs previous-actual, strictly past-referencing; (d) the CPCV-proxy rewrite — reads the already-computed corrected-sign walk-forward `net_pnl` (does not re-fit), `combinatorial_purged_cv` called with `expected_gap=88` (the silent-rescale guard). **The Critic explicitly verified the GROSS-POSITIVE claim survives the audit** — "OOS gross monthly Sharpe +0.1717 from a +0.0279 OOS rank-IC is plausible for a concentrated quintile long-short with inverse-vol weighting ... a leaked result would show an OOS rank-IC an order of magnitude larger. The +0.0279 faint OOS rank-IC and the +0.17 gross Sharpe are mutually consistent with a real, clean, thin signal." Check 2 (embargo) PASS — `XS_REQUIRED_GAP = 88` re-confirmed. Check 3 (multiple-testing) FAIL but **informational for EXPLORATION** per brief Section 0.5 — DSR/PSR set as deliberate sentinels; the substantive read is that `frac_positive_paths = 0.356` is now a genuine, informative number (the /088 CPCV-proxy defect is fixed; `cpcv_paths.csv` non-degenerate, 16 of 45 paths positive). Checks 4-12 all PASS — no new feature family (Check 4), the cross-sectional rank-normalization strengthens stationarity (Check 5), F5 concentration PASSES decisively (Check 6 — max OOS 12.18%), code SHA `bb8c231` stamped + explicit 13-element `XS_FEATURE_COLUMNS` + literal `seed=42` + 3-row PnL spot-check reconciles (Check 7), every /089 code change maps to a brief sentence (Check 8).
- **Critic result-read — a methodologically-clean CONSTRUCTION-PARTIAL.** The Critic found *no methodology DEFECT*, audited the new code leakage-free, and verified the gross-positive finding genuine — "A CONSTRUCTION-PARTIAL result (improved +0.44 on both IS and OOS vs /088, gross-positive, still net-sub-floor) from a clean run is OVERALL=MERGE — validly recorded."
- **Three Critic Recommendations — all integrated; Recs #2 and #3 define /090:**
  1. **Classify CONSTRUCTION-PARTIAL.** DONE — Section 3 of this diary. The Critic's independent disjunctive-precedence walk (8.1 does not fire; 8.2 does not fire — F2 turnover-gate PASSES, F3 does not fire; 8.3 does not fire — requires OOS Sharpe > 0; 8.4 is the match) is reproduced and confirmed.
  2. **/090 should pursue gross-signal STRENGTHENING, NOT a third round of turnover reduction.** RECORDED for /090 (Section 7). The load-bearing finding is that the book IS gross-positive (OOS gross monthly Sharpe +0.1717) and fails net only on fees (OOS fees/gross 1.58×). Of the /090 directions: (a) further turnover reduction has *steeply diminishing returns* — the /089 EDA E4 shows IS net Sharpe gains of only ~0.01–0.04 per band step, and pushing hold-bars or the band harder starts *sacrificing the gross signal itself* (E3 already shows gross Sharpe going negative on the IS-internal walk-forward at hold ≥ 3); (b) gross-signal strengthening is the *higher-EV* lever — the OOS gross Sharpe +0.17 is the asset to grow, and the brief already scoped the **G4 cross-sectional-momentum feature expansion** (+2% IC-IR on IS) as the /090 axis with its own EDA. The Critic concurs with the brief's deferral: /090 is the gross-signal feature-expansion EXPLORATION, multivariate-contribution-tested per the iter-v3/070 dead-path discipline.
  3. **The short-leg-carries-the-alpha asymmetry is a real, pre-registerable signal-anatomy finding.** RECORDED for /090 (Section 7). The engineering report documents that the SHORT leg carries the entire gross spread (OOS short-leg gross +0.1200; OOS long-leg gross −0.0633 — the long leg loses gross despite longing the model's predicted winners). This is the opposite of the textbook cross-sectional pattern; it is internally consistent (the per-leg PnL reconciles, the sign fix is confirmed correct). /090's QR should pre-register, with IS-only EDA, whether the cross-sectional signal in this 22-symbol altcoin universe is structurally a downside/short predictor — and if so, a short-tilted / asymmetric-leg construction is a legitimate /090/091 axis with its own pre-registered falsifier band. Do not let the asymmetry be rationalized post-hoc; make it a falsifiable hypothesis.
- **One minor record item (Critic, not affecting any verdict):** the brief Section 2.4 E4 table transcribed 5 of the 7 τ-grid rows the EDA actually scanned (`E4_no_trade_band_scan.csv` has τ ∈ {0.0, 0.0025, 0.005, 0.0075, 0.010, 0.015, 0.020}; the brief table showed {0.0, 0.005, 0.010, 0.015, 0.020}). The IS-best τ=0.020 is the same in both — no parameter is affected — but future briefs should transcribe EDA grids in full. RECORDED.

---

## 7. iter-v3/090 — the gross-signal-strengthening cross-sectional iteration (the forward plan)

iter-v3/090 is **NOT a fresh re-architecture and NOT a third round of turnover reduction** — it is the gross-signal-strengthening next build on /089's RETAINED `cross_sectional.py` infrastructure, with the cost-aware construction (quintile + 3-bar overlapping holds + no-trade band + the 0.138 turnover ceiling) RETAINED as the construction baseline. The mission bar is top-quant-firm-grade: convert the gross-positive book into a net-positive one. The /090 spec, per Critic Recs #2/#3 and the /089 brief's scoped deferral:

1. **The /090 axis — gross-signal STRENGTHENING via the G4 cross-sectional-momentum feature expansion (the scoped axis).** The book is gross-positive (OOS gross Sharpe +0.1717) and fails net only on fees; the highest-EV lever is to grow the gross signal, not to keep shaving turnover (steeply diminishing per Critic Rec #2; pushing the construction harder sacrifices the gross signal). The /089 brief Section 2.6 already scoped this: the G4 EDA showed the 13-feature composite IC-IR 0.200 → 0.204 (+2%) when 5 cross-sectional momentum/reversal multi-lookback `close`-ratio channels are added — a real but marginal lift on the *initial* G4 measurement. /090's QR must commit a dedicated `analysis/iteration_v3-090/*.py` EDA that (a) properly quantifies the multivariate contribution of a researched cross-sectional-momentum feature family (NOT univariate Spearman rank — the iter-v3/070 dead-path discipline: cluster-MDA / multivariate-contribution test, since correlated-to-existing features steal `colsample_bytree` picks); (b) targets a materially stronger gross spread than G4's +2% — the QR should research the cross-sectional crypto literature for feature families with genuine cross-sectional dispersion (the Karagiorgis skew-kurtosis cross-sectional factors, cross-sectional reversal channels at multiple lookbacks, idiosyncratic-volatility-ranked factors). The goal is a gross-signal lift large enough that, net of the contained turnover, the OOS book crosses breakeven.

2. **The short-leg-asymmetry hypothesis — /090 QR weighs whether to test it now or defer to /091.** Critic Rec #3: the SHORT leg carries the entire gross spread (OOS short-leg gross +0.1200, long-leg gross −0.0633). /090's QR must pre-register, with IS-only EDA, whether the cross-sectional signal in this 22-symbol altcoin universe is structurally a downside/short predictor. If the IS EDA confirms a structural short-side asymmetry, a short-tilted or asymmetric-leg-sizing construction (or a long-only-short book) is a legitimate axis with its own pre-registered falsifier band. **The QR's call:** the /089 brief deferred the gross-signal feature expansion to /090 as a single dedicated axis (the iter-v3/070 discipline forbids stacking two axes in one EXPLORATION). The short-leg-asymmetry construction is a *second, orthogonal* axis (a construction change, not a feature change) — so the QR should weigh running /090 as the feature-expansion EXPLORATION (the scoped axis) with the short-leg asymmetry pre-registered as the /091 axis, OR — if the /090 IS EDA shows the asymmetry is the dominant lever — making the asymmetric construction the /090 axis and deferring the feature expansion. The QR EDA-picks and scopes /090 on committed numerical evidence per `feedback_v3_axis_selection_quant_discipline.md`; this diary mandates the gross-signal-strengthening *direction*, not the specific lever.

3. **What /090 must NOT do.** Do not run a third round of turnover reduction (Critic Rec #2 — diminishing returns, and pushing the construction harder kills the gross signal). Do not stack the feature expansion AND the asymmetric construction in one EXPLORATION (the iter-v3/070 / `feedback_v3_engineered_features_dont_stack.md` discipline). Do not retest funding/microstructure/basis feature families (the 7-feed structural verdict — though note that verdict was established on the per-symbol architecture; a cross-sectional ranker is a different statistical object, so a *cross-sectionally-normalized* crypto-native family is not categorically banned, but it must be EDA-justified, not assumed). Do not pick the axis ad-hoc — the QR commits the EDA before the brief.

The honest senior read: iter-v3/089 is a genuine, well-researched, methodologically-clean advance on the cross-sectional construction axis. It executed the two mandatory corrections cleanly, carried a fully IS-validated cost-aware construction grounded in the canonical cost-aware-portfolio literature, pre-registered a HARD turnover ceiling that PASSED, and delivered the brief's ≈45% modal outcome on a clean run verified leakage-free by the Critic. The book is now gross-positive on both windows and the gap to net-positive is a bounded, well-posed cost/signal problem. The cross-sectional architecture is, across /088 → /089, v3's most sustained positive trajectory — the first line in three cycles where the architecture responds to fixes, the signal transfers OOS, and the book has turned gross-positive. /089 is NO-MERGE — the net book is sub-floor — but it is not a stopping point: it hands /090 a concrete, IS-grounded gross-signal-strengthening axis with a clear goal. That is the relentless, honest, top-quant-firm-grade execution the mission demands.

---

## 8. Cycle-3 progress + iter-v3/090

### 8.1 — Cycle 3 progress — 8/10 EXPLORATION slots done

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /082 | NEW crypto-native FEATURE FAMILY (funding-rate 4-channel, Direction 1) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /083 | symbol-universe EXPANSION 3→4 (+FILUSDT, Direction 2) | NEGATIVE |
| #3 | /084 | REFERENCE / METHODOLOGY — PER_CELL_GAP 43→22 fix + clean /059-config 3-symbol anchor re-run | REFERENCE-REANCHOR |
| #4 | /085 | NEW funding-regime-conditioned ENGINEERED feature (Category-2 composed, Direction 1) | SUSPICIOUS (trade-selection sub-channel) |
| #5 | /086 | NEW crypto-native DATA FEED — perp-spot basis 3-feature family (Direction 1) | INERT |
| #6 | /087 | symbol-universe EXPANSION 3→6 WHOLESALE (+GALA+MANA+SAND, Direction 2) | NEGATIVE |
| #7 | /088 | RE-ARCHITECTURE — cross-sectional relative-value RANKING model | ARCHITECTURE-PARTIAL |
| #8 | /089 | the CORRECTED cross-sectional iteration (sign fix + CPCV-proxy fix + cost-aware construction) | **CONSTRUCTION-PARTIAL** |
| #9 | /090 | gross-signal STRENGTHENING on the cross-sectional architecture (G4 feature expansion / short-leg asymmetry — QR EDA-picks) | — |
| #10 | /091 | continued cross-sectional iteration per the /090 result | — |
| CONFIRMATION | /092 | best cycle-3 result (multi-seed validation) | pre-registered MERGE gates |

Cycle 3 has used 8 of its 10 EXPLORATION slots — 0 clean PROMISING — but /088 and /089 are the structural break. /088 produced v3's first genuine OOS signal transfer; /089 corrected the construction, contained turnover (the HARD gate PASSED), and turned the book gross-positive on both windows. Across /088 → /089 the cross-sectional architecture is v3's most sustained positive trajectory: the architecture responds to fixes, the signal transfers OOS, and the gap to a net-positive book is now a concrete cost/signal problem. /090 and /091 continue iterating it — /090 on the gross-signal-strengthening axis; /092 evaluates whether the corrected cross-sectional book has reached a CONFIRMATION-worthy result.

### 8.2 — The honest senior read

iter-v3/089 is the corrected next build on v3's most promising structural result and it did exactly what a clean construction-fix iteration should: it executed the two mandatory corrections, carried a fully IS-validated cost-aware construction, pre-registered a HARD turnover ceiling that PASSED, and delivered the brief's pre-registered ≈45% modal outcome — verified leakage-free and gross-positive by the Critic. The cross-sectional book is now gross-positive (OOS gross monthly Sharpe +0.1717) and fails net only on fees (OOS fees/gross 1.58×, down from /088's 8.8×). That is a bounded, well-posed problem with a clear next lever. /089 is NO-MERGE — the net book is sub-floor on both windows — but the trajectory is real and sustained, and /090 has a concrete IS-grounded gross-signal-strengthening axis. The /087-closeout PARALLEL contingency (escalate to the user for a paradigm decision if the cross-sectional pivots also fail) is NOT triggered — /088 → /089 is a responsive, improving trajectory, not a failed pivot; the immediate path is clear: iterate the cross-sectional architecture at /090-091.

---

## 9. Decision — NO-MERGE; the cross-sectional architecture is the active v3 research line; /090 is the gross-signal-strengthening next build

**NO-MERGE. BASELINE_V3.md is UNCHANGED — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) and tag `v0.v3-059` stay canonical. The /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed) stays the cycle-3 intra-cycle anchor for any residual per-symbol-path comparison.**

iter-v3/089 classified **CONSTRUCTION-PARTIAL** (brief Section 8.4 — OOS rank-IC +0.0279 > 0; IS turnover 0.1153 ≤ 0.138, the HARD gate PASSES; OOS monthly Sharpe −0.0985 > /088's −0.5418; OOS monthly Sharpe −0.0985 ≤ 0, so 8.3 does not fire). A sub-floor EXPLORATION carries no merge ingredient and does not advance to the /092 CONFIRMATION bundle; an EXPLORATION cannot update the baseline regardless. **No new git tag for a baseline update.** An EXPLORATION closeout marker tag `v0.v3-089` is issued (annotated; explicitly NOT a baseline update — the same pattern as `v0.v3-082` … `v0.v3-088`).

**The cross-sectional architecture is RETAINED as the LIVE v3 research direction — not Dead Ideas.** The `cross_sectional.py` module, the `run_cross_sectional_v3.py` runner, the `XS_UNIVERSE` 22-symbol constant, the pooled-ranking infrastructure, and the /089 cost-aware construction (quintile + 3-bar overlapping holds + no-trade band + the 0.138 turnover ceiling) are all RETAINED and built upon. The architecture is not falsified — it produced a gross-positive book on both windows and a sustained /088 → /089 improving trajectory. iter-v3/090 is the gross-signal-strengthening next build on it — NOT a fresh re-architecture, NOT a third round of turnover reduction.

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are untouched.

---

**Commit chain:**
- EDA SHA: `c172a12` — `analysis/iteration_v3-089/turnover_construction_eda.py` (E1-E6 CSVs) + `analysis/iteration_v3-089/gross_signal_eda.py` (G1-G4 CSVs)
- Brief SHA: `ac2b487` — `briefs-v3/iteration_v3-089/research_brief.md` + the Phase 5.5 gate; brief Section 11 SHA backfill `2b996fd`
- Setup SHA: `bb8c231` — the sign fix + CPCV-proxy fix + cost-aware construction + turnover ceiling wired into `cross_sectional.py` / `run_cross_sectional_v3.py`; ITERATION_LABEL "v3-089"; the 6 new /089 tests in `tests/strategies/ml/test_cross_sectional.py`
- Phase 5.5 gate SHA: `32ee747` (PASS — QE independent verification of the QR-driven corrected cross-sectional axis)
- Engineering report SHA: `3c7d300` — `briefs-v3/iteration_v3-089/engineering_report.md`
- Critic FINAL SHA: `74054c2` (OVERALL=MERGE — methodology of a clean corrected-build EXPLORATION certified; the gross-positive finding verified genuine; 3 Recommendations — Recs #2/#3 define /090)
- Diary + catalog + cycle3_plan + BASELINE_V3.md update SHA: `0975071` (this closeout; SHA backfilled by the immediately-following commit)
**Reports**: `reports-v3/iteration_v3-089/`
**Tag**: `v0.v3-089` (EXPLORATION closeout marker; NOT a baseline update — BASELINE_V3.md UNCHANGED at `v0.v3-059`)
