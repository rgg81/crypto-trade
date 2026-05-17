# iter-v3/087 — Cycle 3 #6 EXPLORATION — WHOLESALE universe-breadth expansion 3→6 / NEGATIVE

**Date**: 2026-05-17
**Type**: EXPLORATION (cycle 3 slot #6 of 10). Single-axis: a WHOLESALE symbol-universe EXPANSION — `V3_MODELS` grew 3→6, adding GALAUSDT/MANAUSDT/SANDUSDT to the BCH/LDO/TRX incumbents. EXPLORATION-mode 3-seed, `--n-trials 35`, 630 Optuna trials, wall-clock 1.55h.
**Axis**: Direction 2 — symbol-universe EXPANSION (breadth / the Grinold-Kahn `IR = IC·√breadth` lever), done WHOLESALE rather than /083's single-weak-symbol add. QR-research-and-EDA-driven (brief Section 10: Grinold & Kahn *Active Portfolio Management* 1999; Bailey/López de Prado/del Pozo "Strategy Approval — Sharpe Ratio Indifference Curve" SSRN 2003638; crypto portfolio-size literature arXiv 2505.24831; multi-task GBM ScienceDirect S0957417425043118; EDA `1a117b2`).
**Verdict**: EXPLORATION-MERGE per Critic FINAL `24a9dcc` — OVERALL=MERGE certifies the methodology of a clean EXPLORATION (all 8 mandatory + 4 optional Checks PASS, including the NO-CHEATING-critical Check 2 embargo at `REQUIRED_GAP = (21+1)×6 = 132`). The Critic gates methodology soundness, NOT advancement; the Critic's result-read is **NEGATIVE**; the Section 8 classification is the QR's Phase-8 call.
**Classification**: **NEGATIVE** (brief Section 8.2 — the general `OOS Δ < −0.20` clause). OOS monthly Sharpe Δ vs the /084 EXPLORATION-MODE-REFERENCE = **−0.8349** (OOS monthly Sharpe collapsed to −0.5027); the −0.20 NEGATIVE leg is breached by a wide margin. SUSPICIOUS (evaluated first) does NOT fire; NEGATIVE precedes PROMISING/INERT in the disjunctive precedence.
**Advancement**: does NOT advance to the iter-v3/092 cycle-3 CONFIRMATION bundle — a NEGATIVE axis carries no edge ingredient. The 6-symbol universe is falsified; `V3_MODELS` reverts to the 3-symbol /059 universe at the /088 setup.
**BASELINE_V3.md**: **UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) and tag `v0.v3-059` stay canonical. An EXPLORATION cannot update the baseline regardless. The /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed) stays the cycle-3 intra-cycle anchor.
**Branch**: `iteration-v3/087`

---

## 1. What was done — the single axis

iter-v3/087 is the SIXTH EXPLORATION slot of v3 cycle 3. Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 3 runs 10 SEPARATE EXPLORATIONs (/082-/091) followed by 1 SEPARATE CONFIRMATION (/092); the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The single axis: a **WHOLESALE symbol-universe EXPANSION** — `V3_MODELS` grew from 3 symbols (BCH/LDO/TRX) to **6** by adding **GALAUSDT, MANAUSDT, SANDUSDT** in one step. Every incumbent was kept; 3 symbols were added; each added symbol got one independent per-symbol LightGBM with the identical 14-feature stack, the identical `(2.0,1.0)`-ATR triple-barrier labeling, and the identical 7-gate risk stack — a fully **universal** addition (no per-symbol features, no per-symbol ATR, no per-symbol gates). The axis is **denominator expansion** — the Grinold-Kahn breadth lever — structurally distinct from the CLOSED swap-by-replacement family (/078 swapped LDO→ADA at constant count). The 7-feed structural verdict (/086 closeout) had explicitly ruled out an 8th crypto-native feature family; /087 is the Direction-2 structural pivot.

Two MANDATORY non-axis baseline-restore actions accompanied the setup (Critic /086 Rec #3): (a) the 3 perp-spot basis features (`basis_zscore_30`, `basis_momentum_3`, `basis_extreme_flag`) were dropped — `V3_FEATURE_COLUMNS_TOP_N` reverted from the 17-feature /086 stack to the **14-feature /059 anchor**; (b) the 3 basis names joined the runner's pre-flight ABSENT-assertion list (the `funding_regime_momentum_5d` pattern). The `fetch-spot` subcommand, `basis_v3.py`, and `data/spot/` cache were RETAINED as reusable infrastructure. `REQUIRED_GAP` recomputed 66→132 = (21+1)×6; `PER_CELL_GAP` correctly stayed 22 (single-symbol cell — no `×n_symbols` factor). The 11-knob `_canonical_v059` config-accretion check confirmed all 9 risk/labeling knobs /059-canonical — the only declared deltas the 2 axis deltas (`V3_MODELS` 3→6, `REQUIRED_GAP` 66→132).

## 2. Results — vs the cycle-3 EXPLORATION-MODE-REFERENCE (/084)

Per the MANDATORY two-anchor structure (Critic /084 Rec #2): the intra-cycle Δ is classified against **ANCHOR 1 — the /084 EXPLORATION-MODE-REFERENCE, IS +0.8325 / OOS +0.3322 (3-seed EXPLORATION-mode, current data)** — architecturally matched to /087's own 3-seed EXPLORATION run. **ANCHOR 2 — the /059 CONFIRMATION baseline, IS +1.0894 / OOS +0.5791 (10-seed)** — is RESERVED for the iter-v3/092 CONFIRMATION and is NOT the comparison point here.

| Metric | /084 EXPLORATION-MODE-REFERENCE | /087 (this run) | Δ /087 − /084 |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.8325** | **+0.9208** | **+0.0883** |
| OOS monthly Sharpe | **+0.3322** | **−0.5027** | **−0.8349** |
| OOS/IS monthly Sharpe ratio | +0.3990 | **−0.5460** | — |
| IS daily Sharpe | 1.7115 | +2.1267 | — |
| OOS daily Sharpe | 0.8745 | −0.9112 | — |
| IS MaxDD | 31.87% | 61.78% | — |
| OOS MaxDD | 35.78% | 76.42% | — |
| IS n_trades | 159 | 283 | +124 |
| OOS n_trades | 104 | 180 | +76 |
| PBO (per-cell mean) | 0.1278 | **0.1230** | — |
| frac_positive_paths (CPCV) | 0.644 | **0.556** | −0.088 |
| PSR | 1.0000 | 0.0000 | EXPLORATION-mode artifact |
| DSR (legacy) | 0.0000 | 0.0000 | EXPLORATION-mode artifact |
| n_trials (Optuna total) | 315 | 630 | (6 syms × 3 seeds × 35) |
| n_eff | 19 | 19 | — |

CPCV path Sharpe distribution: q25 = −0.964, q50 = +0.169, q75 = +0.942; worst path −3.47 Sharpe / 968 MaxDD. `frac_positive_paths = 0.5556` (25/45 paths) clears the 0.55 Gate-10-CPCV threshold by the thinnest possible margin, and PBO 0.1230 clears the 0.40 gate — the run is a methodologically valid measurement of a genuinely NEGATIVE result.

**Per-symbol IS vs OOS attribution** (`in_sample`/`out_of_sample` `per_symbol.csv`, `net_pnl%`):

| Symbol | Status | IS net_pnl% | OOS net_pnl% | IS WR | OOS WR | Sign flip? |
|---|---|---:|---:|---:|---:|---|
| GALAUSDT | NEW | **+67.20** | **−18.98** | 46.4% | 29.2% | YES — IS-positive, OOS-negative |
| MANAUSDT | NEW | **+101.56** | **−27.16** | 49.1% | 25.8% | YES — IS-positive, OOS-negative |
| SANDUSDT | NEW | **−18.10** | **−28.07** | 36.6% | 28.6% | consistent negative (IS also negative) |
| BCHUSDT | incumbent | +79.45 | −8.69 | 45.2% | 32.4% | YES — IS-positive, OOS-negative |
| TRXUSDT | incumbent | −23.04 | +33.33 | 29.3% | 50.9% | YES — IS-negative, OOS-positive |
| LDOUSDT | incumbent | −11.44 | −15.80 | 27.3% | 25.0% | consistent negative |

**All 3 new symbols lost in OOS.** GALA (+67.2% IS → −19.0% OOS) and MANA (+101.6% IS → −27.2% OOS) are textbook positive-IS/negative-OOS overfit; MANA's swing is the largest single-symbol IS→OOS reversal in v3 history at this iteration. SAND was IS-negative in the full 24-month backtest (−18.1%) — the EDA's restricted-window screen predicted IS-positive edge for SAND and the full IS window did not replicate it (the screen mis-signed SAND; see Section 6, Critic Rec #3). The lone OOS-profitable symbol is the incumbent TRX (+33.33%); BCH/LDO/GALA/MANA/SAND all OOS-negative.

## 3. The roster-diff — F4 / sub-channels (c)/(d) formally adjudicated

The brief Section 8.3 LOCKED SUSPICIOUS taxonomy has four sub-channels; sub-channels (c) and (d) — the trade-selection sub-channels — require the Phase-8 OOS roster-diff (`analysis/iteration_v3-087/roster_diff_oos.py`, the /085/086 method precedent). The Critic's Phase-7.5 review flagged this for Phase 8 ("the QR must run the roster-diff to formally close (c)/(d)"). This Phase 8 ran it.

**The roster-diff exposed a structural fact: the /087 OOS roster is a near-strict SUPERSET of /084's.** All 104 /084 OOS trades survive into /087 (`/087 ADDS 76, REMOVES 0`); /087 adds exactly 76 new OOS trades, and those 76 are precisely the GALA+MANA+SAND OOS trades (76 = 24+31+21). The 3-symbol incumbent OOS roster is essentially frozen: BCH and LDO are **bit-identical** between /087 and /084 (same wpnl +1.9077 / −12.5778, same trade counts 37 / 12), and TRX differs by exactly **1 trade** with a +0.28 wpnl delta (+24.5433 vs +24.2639) — the established `feedback_v3_single_seed_frozen_baseline.md` pattern: at single-seed=42 the non-target symbols' Optuna trajectories are deterministic and the incumbent rosters reproduce.

**Sub-channel (c) — F4, added-vs-removed gap.** With the removed set EMPTY (`REMOVES = 0`), the script's mechanical reading is `added mean 6.1974 − removed mean 0.0000 = +6.1974`, which trips the `> +1.0` threshold. **This "firing" is a degenerate empty-set artifact, NOT a regime-loading signal.** The /085/086 precedent had genuine roster swaps (40/36 trades removed) where the added-minus-removed gap is a real holding-time-shift diagnostic. /087 has a pure-superset roster — there is no removed set to compare against, so `removed mean = 0` is an arithmetic placeholder, not an empirical 0-candle-duration roster. A LOCKED falsifier is honored exactly as written — but the F4 sub-channel was DESIGNED for the /076 swap signature (the model dropping short-held trades and picking up longer-held OOS-uptrend trades), and a wholesale universe expansion that REMOVES NOTHING and ADDS a new symbol's entire roster does not exercise that mechanism. The economically meaningful adjudication of the regime-loading question for a universe axis is sub-channel (d).

**Sub-channel (d) — added-symbol target-axis (the brief Section 4.4 pre-registered target-axis falsifier).** The GALA+MANA+SAND OOS-roster mean duration is **6.1974 candles** (76 trades); the incumbent BCH/LDO/TRX OOS pooled roster is **6.4519 candles** (104 trades):

```
added-symbol-minus-incumbent OOS mean-duration gap  =  6.1974 − 6.4519  =  −0.2546 candles
```

**−0.2546 ≤ +1.0 — the LOCKED Section 8.3(d) target-axis falsifier does NOT fire.** The 3 added symbols hold trades for essentially the same duration as the incumbents (per-symbol: GALA 6.375, MANA 5.839, SAND 6.524) — the brief's EDA T5 prediction (IS added-symbol duration gaps +0.149/+0.181/−0.171, all inside ±0.2) transferred faithfully to OOS. **The expansion did NOT load the v3 IS/OOS regime factor via roster duration.** This is the substantively correct read: /087's failure is NOT a holding-time / regime-selection failure — it is a straight IS-overfit of the 3 new symbols' per-symbol models (positive-IS / negative-OOS), with the incumbents frozen.

**F4 adjudication: sub-channel (d) does NOT fire (gap −0.2546). Sub-channel (c)'s mechanical "fire" is an empty-removed-set artifact of a pure-superset roster and carries no regime-loading content.** The economically valid trade-selection adjudication — sub-channel (d), the only one a wholesale-expansion roster meaningfully exercises — clears the gate. SUSPICIOUS does not fire on the trade-selection sub-channels (see Section 4).

## 4. PATH classification — NEGATIVE — disjunctive-precedence walk

The brief Section 8 LOCKED taxonomy runs disjunctive precedence, first match canonical: **SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL-RESULT.** Anchor for all Δ: ANCHOR 1 (/084, IS +0.8325 / OOS +0.3322).

### 4.1 SUSPICIOUS (8.3) — evaluated FIRST, and it does NOT fire

Section 8.3 fires on ANY of four sub-channels:

- **(a) OOS/IS monthly Sharpe ratio > 3.0** — /087 ratio = −0.5027 / +0.9208 = **−0.5460** → NEGATIVE, not `> 3.0`; does NOT fire. (A SUSPICIOUS ratio is the *OOS soars on flat IS* signature; /087's OOS went hard negative.)
- **(b) OOS-DOMINANT sub-mode — IS Δ < 0 AND OOS Δ ≥ +0.20** — /087 IS Δ = **+0.0883 (positive)** AND OOS Δ = **−0.8349** — neither leg holds; mechanically foreclosed. The OOS-DOMINANT sub-mode is the /082/078 *IS flat-or-down / OOS up* signature; /087 is the opposite signature.
- **(c) F4 — the /076 trade-selection sub-channel** — adjudicated in Section 3: the mechanical "fire" is an **empty-removed-set artifact** of a pure-superset roster (REMOVES = 0); it carries no regime-loading content. The /076 mechanism (the model swapping short-held trades for longer-held OOS-uptrend trades) is not exercised by an expansion that removes nothing.
- **(d) added-symbol target-axis sub-channel** — adjudicated in Section 3: the GALA+MANA+SAND-minus-incumbent OOS mean-duration gap is **−0.2546 ≤ +1.0** → does NOT fire. This is the economically meaningful trade-selection test for a universe axis, and it clears.

**SUSPICIOUS does NOT fire.** The headline metrics rule it out structurally — SUSPICIOUS in every one of its forms is an *OOS-up-on-flat-IS* divergence, and /087 produced the **opposite** signature: IS up +0.09, OOS crashes −0.83. The trade-selection sub-channel (d) — the only sub-channel a wholesale-expansion (remove-nothing) roster meaningfully exercises — confirms there is no holding-time regime-loading. /087 is not SUSPICIOUS.

### 4.2 NEGATIVE (8.2) — fires, and is canonical

Section 8.2 trigger: `IS Δ < −0.10 OR OOS Δ < −0.20` (and NOT SUSPICIOUS). **OOS Δ = −0.8349** is far past the −0.20 leg — the general NEGATIVE clause fires decisively. The OOS monthly Sharpe of **−0.5027** is a genuine collapse, not noise: all 3 new symbols lost in OOS (GALA −18.98%, MANA −27.16%, SAND −28.07% net pnl), OOS MaxDD blew out to 76.42%, the OOS profit factor fell to 0.8961, and the worst CPCV path hit −3.47 Sharpe. Since SUSPICIOUS does NOT fire and NEGATIVE precedes PROMISING/INERT in the disjunctive precedence, **NEGATIVE is the canonical classification.**

### 4.3 The falsifier-band gap — recorded (Critic flag)

**The brief's F1 falsifier (`IS monthly Sharpe Δ vs /084 < −0.20` → NEGATIVE) did NOT fire** — /087's IS actually *lifted* +0.0883. F1 was the /083-failure-mode falsifier: it was **IS-collapse-specific**, designed for the signature /083 produced (the aggregate IS Sharpe collapsing when a weak symbol drags the pooled book). F2/F3 were designed for the *opposite* divergence (IS flat/down, OOS up). **/087 produced a third signature the F1-F4 band had no dedicated trigger for: `IS up, OOS crashes`** — the textbook IS-overfit signature. The LOCKED taxonomy still classifies /087 correctly — Section 8.2's *general* NEGATIVE clause (`OOS Δ < −0.20`) is the catch-all and it fires cleanly, so there is **no classification ambiguity and no methodology defect**. But the pre-registered *falsifier table* (F1-F4) had no IS-up/OOS-down-specific named gate. This is a brief-design observation, recorded so future universe/per-symbol briefs pre-register a **symmetric** NEGATIVE falsifier — an `OOS Δ < −0.20 regardless of IS sign → NEGATIVE` gate as a *named* F-table falsifier, not only as the Section 8.2 fallback (Critic Rec #2).

### 4.4 The other taxonomy branches (foreclosed, for completeness)

- **PROMISING (8.1)** does NOT fire: requires `OOS Δ ≥ +0.20` — /087's OOS Δ is −0.8349; foreclosed on the OOS leg.
- **INERT (8.4)** does NOT fire as canonical: the IS leg `IS Δ ∈ [−0.10,+0.10]` DOES hold (+0.0883), but INERT additionally requires NOT SUSPICIOUS and is *behind* NEGATIVE in the precedence — NEGATIVE fires (OOS Δ −0.8349 < −0.20), so INERT is foreclosed by precedence.
- **NULL-RESULT (8.5)** does NOT fire: mechanically impossible — 3 symbols were added and `REQUIRED_GAP` changed 66→132, so the /087 roster cannot be bit-identical to /084's (it is a 180-trade superset of /084's 104).

## 5. Section 7 prediction check — NEGATIVE inside the pre-registered set, at the named single most-likely failure path

The brief Section 7 pre-registered the failure-mode distribution: **≈40% PROMISING-or-INERT-mild, ≈30% NEGATIVE (F1), ≈25% SUSPICIOUS (F2/F3/F4), ≈5% NULL-RESULT.** The realized classification is **NEGATIVE** — pre-registered at ≈30% and named in the Section-7 prose as *"the single most-likely failure path."*

The calibration verdict is **clean on the outcome bucket but partially off on the mechanism**:

- **Outcome bucket — correct.** The brief's Section 7 prose named NEGATIVE explicitly: *"≈30% — NEGATIVE (F1). The /083 / /021 failure mode: the production multi-symbol Optuna+gate stack does not transfer the screen's diversification benefit ... This is the single most-likely failure path and is named as such."* The realized outcome IS that bucket — a NEGATIVE-class collapse driven by the production stack failing to transfer the screen's edge. The brief did NOT float PROMISING above the evidence; the Section-7 calibration note explicitly leaned ≈40% modal toward "modest lift OR collapse," and the realized result is the collapse leg.
- **Mechanism — partially off.** The brief tied its ≈30% NEGATIVE estimate specifically to **F1 — *aggregate IS collapse*** (the /083 signature: IS Sharpe regresses when a weak symbol drags the pooled book). The realized NEGATIVE fired via a *different* channel: IS actually *lifted* +0.09 (the breadth diversification did transfer to IS), and the collapse was entirely in **OOS** — the 3 new symbols' per-symbol models overfit IS and inverted OOS. So the brief correctly predicted "the production stack does not transfer the screen's edge," but predicted the non-transfer would show as an *IS* collapse when it actually showed as an *OOS* collapse with IS intact. This is the same gap as Section 4.3's falsifier-band finding: the brief's failure-mode imagination was anchored on the /083 IS-collapse precedent and did not pre-register the IS-up/OOS-down signature as a distinct path.

Recorded for /088+ brief calibration: a universe/per-symbol expansion can fail by IS-overfit of the *added* symbols (IS up, OOS down) just as readily as by IS-aggregate-drag (IS down) — future briefs must pre-register BOTH failure mechanisms, and the falsifier table must carry a symmetric `OOS Δ < −0.20 regardless of IS sign` gate.

## 6. Critic integration — OVERALL=MERGE + 4 Recommendations

**Critic FINAL `24a9dcc`** (`briefs-v3/iteration_v3-087/review.md`): a single-round full review (zero clarifications), OVERALL=**MERGE**. The MERGE verdict CERTIFIES the methodology of a clean EXPLORATION that produced a genuinely NEGATIVE result — it is a methodology certification, NOT an advancement or an edge endorsement. The Critic's result-read is explicitly **NEGATIVE**.

- **All 8 mandatory Checks + 4 optional Checks PASS.** Check 1 (look-ahead) PASS — the universe-selection look-ahead surface (the relevant risk for a breadth axis) is clean: the candidate screen used `open_time < OOS_CUTOFF_MS = 2025-03-24` on every frame with a 60-day new-listing burn-in; GALA/MANA/SAND were selected on IS data only. Check 2 (embargo) PASS — the NO-CHEATING-critical check: `REQUIRED_GAP = (21+1)×6 = 132`, verified by `_verify_label_leakage_gap` recomputing `(timeout_candles+1) × len(V3_MODELS)` dynamically and run.log line 27 confirming `132 PASS`; `PER_CELL_GAP` correctly stays 22; no stale 66 survives anywhere in the validation path; the purge is symmetric. Check 3 (multiple-testing) — per-cell PBO 0.1230 < 0.40 PASS; `frac_positive_paths` 0.5556 ≥ 0.55 PASS; DSR/PSR informational at EXPLORATION mode. Check 4 (IC) PASS — no new feature family (the unchanged 14-feature /059 stack). Check 5 (ADF) PASS. Check 6 (Pareto) PASS-N/A — EXPLORATION single outer seed. Check 7 (reproducibility) PASS — explicit 14-element `feature_columns`, 3-tuple `ENSEMBLE_SEEDS` literal, 3-row OOS trade-PnL spot-check reconciles exactly. Check 8 (hypothesis-implementation alignment) PASS — exactly one axis (`V3_MODELS` 3→6), zero scope creep, the basis features asserted ABSENT. Checks 9-12 all PASS.
- **Critic result-read — NEGATIVE.** The Critic walked the LOCKED disjunctive taxonomy and concluded NEGATIVE is canonical: SUSPICIOUS does not fire (ratio −0.5460 not >3.0; OOS-DOMINANT foreclosed IS Δ +0.0883 ≥ 0; (c)/(d) delegated to this Phase-8 roster-diff); Section 8.2's general `OOS Δ < −0.20` clause fires at OOS Δ −0.8349; NEGATIVE precedes PROMISING/INERT. This Phase 8 ran the delegated roster-diff and confirms: sub-channel (d) does NOT fire (−0.2546); sub-channel (c)'s mechanical fire is an empty-removed-set artifact — SUSPICIOUS does not fire — and the FINAL classification is **NEGATIVE**, consistent with the Critic's read.
- **The EDA-screen fidelity finding (Critic QR-process finding).** The /087 EDA screen mis-signed SAND: SAND screened at +0.1289 standalone Sharpe / +257 net pnl% on the un-gated proxy roster (1485 IS trades), yet the production run with the 7-gate stack + Optuna selected only 41 IS SAND trades that netted **−18.10%**. The screen ran un-gated (no 7-gate risk stack, no Optuna) while production runs the full stack; the gate stack discarded the bulk of SAND's screen-favorable trades and the residual was a net detractor. The screen's `direction-only` disclaimer covers magnitude error but does NOT cover a **sign flip** — and SAND's screen sign (+) and production-IS sign (−) disagreed. This is the /083-lesson pattern recurring (a per-symbol-edge screen that does not survive the gate stack). The methodology is sound — the screen was disclosed, IS-only, and committed — but its predictive fidelity was weaker than the brief's confidence implied. Recorded as Critic Rec #3.
- **Four Critic Recommendations — all integrated:**
  1. **Record /087 as NEGATIVE; do NOT advance the 6-symbol universe to /092; record D2 universe expansion as a 4-failure track record (CLOSED for the rest of cycle 3).** DONE — Section 7 of this diary; BASELINE_V3.md Dead Ideas updated. Direction 2 (universe expansion) now has a **4-failure track record across single, double, and wholesale adds: /021 (HBAR+AVAX), /069 (ADA), /083 (FIL), /087 (GALA+MANA+SAND)**. The breadth `√N` benefit did not transfer through the production Optuna+7-gate stack in any of the four. D2 universe expansion is CLOSED for the remainder of cycle 3.
  2. **Pre-register a symmetric NEGATIVE falsifier in future briefs.** RECORDED (Section 4.3) — /087's F1 (`IS Δ < −0.20`) was IS-collapse-specific and did not fire on the IS-up/OOS-crashes signature; future universe/per-symbol briefs must name an explicit `OOS Δ < −0.20 regardless of IS sign → NEGATIVE` falsifier in the F-table.
  3. **Tighten the universe-screen fidelity protocol.** RECORDED — future Direction-2 screens must either apply the production 7-gate risk stack inside the screen pipeline, OR flag any candidate whose un-gated and gated trade counts diverge by >10× as `screen-sign-provisional` and exclude it from the marginal-lift ranking until a gated re-screen confirms the sign. (Direction 2 is closed for cycle 3, so this binds whenever a universe axis is next reopened.)
  4. **Fix the /087 engineering-report PER_CELL_GAP config-diff doc error.** The engineering report's config-diff table records `/084 PER_CELL_GAP = 11` and `/087 PER_CELL_GAP = 22 (= 132/6)`. Both are wrong: the /084 value was **22** (the /084 fix corrected 43→22), and `PER_CELL_GAP` is `(timeout_candles+1) = 22` for a single-symbol cell — it has no `n_symbols` factor, so the `132/6` derivation is a spurious rationalization. The code (`run_baseline_v3.py:1600`) is correct at 22; only the report prose is wrong. Recorded here so the archaeology record is not poisoned: **`PER_CELL_GAP` is universe-count-invariant at 22 in BOTH /084 and /087.** (The engineering report is a closed artifact; this diary correction is the canonical record.)

## 7. Decision — NO-MERGE; D2 universe expansion CLOSED at a 4-failure record

**NO-MERGE. BASELINE_V3.md is UNCHANGED — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) and tag `v0.v3-059` stay canonical. The /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed) stays the cycle-3 intra-cycle anchor.**

iter-v3/087 classified **NEGATIVE** (brief Section 8.2 — the general `OOS Δ < −0.20` clause; OOS monthly Sharpe Δ −0.8349, OOS monthly Sharpe collapsed to −0.5027; all 3 new symbols OOS-negative). A NEGATIVE axis carries no edge ingredient and does not advance to the CONFIRMATION bundle; an EXPLORATION cannot update the baseline regardless. **No new git tag for a baseline update.** An EXPLORATION closeout marker tag `v0.v3-087` is issued (annotated; explicitly NOT a baseline update — the same pattern as `v0.v3-082` … `v0.v3-086`).

**Direction 2 — symbol-universe expansion — is CLOSED for the remainder of cycle 3 at a 4-failure track record:** /021 (HBAR+AVAX, double add, NEGATIVE), /069 (ADA, single add), /083 (FIL, single add, NEGATIVE — IS collapse), /087 (GALA+MANA+SAND, wholesale add, NEGATIVE — OOS collapse). The four span every expansion topology — single, double, and wholesale — and the breadth `√N` benefit transferred to production in none of them. The /087 wholesale expansion was the strongest pre-backtest case (the EDA's +0.2371 screen aggregate-Sharpe lift, all-positive leave-one-out, the indifference-curve screen on strategy-PnL correlation) and it still failed: the IS lift (+0.09) shows the breadth math is real *in-sample*, but the 3 new symbols' per-symbol models overfit IS and inverted OOS, and the production OOS collapsed −0.83. Recorded in BASELINE_V3.md Dead Ideas. Universe expansion as a v3 axis is exhausted.

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are untouched.

**MANDATORY iter-v3/088-setup action (the standard baseline-restore of a NEGATIVE/NO-MERGE axis).** The /088 setup MUST: (a) revert `V3_MODELS` from the 6-symbol universe back to the 3-symbol /059 universe (BCH/LDO/TRX) — drop GALAUSDT/MANAUSDT/SANDUSDT; (b) recompute `REQUIRED_GAP` 132→66 = (21+1)×3. `PER_CELL_GAP` stays 22 (universe-count-invariant — it was already correct and unchanged at /087). The 14-feature /059 anchor stack stays (the /087 basis-revert is retained — the basis features stay dropped + ABSENT-banned). This restores the canonical /059 starting point for /088.

## 8. Cycle-3 progress + the FRANK CYCLE-3 STRATEGIC ASSESSMENT (Next Iteration Ideas)

### 8.1 Cycle 3 progress — 6/10 EXPLORATION slots done, 0 clean PROMISING

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /082 | NEW crypto-native FEATURE FAMILY (funding-rate 4-channel, Direction 1) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /083 | symbol-universe EXPANSION 3→4 (+FILUSDT, Direction 2) | NEGATIVE |
| #3 | /084 | REFERENCE / METHODOLOGY — PER_CELL_GAP 43→22 fix + clean /059-config 3-symbol anchor re-run | REFERENCE-REANCHOR |
| #4 | /085 | NEW funding-regime-conditioned ENGINEERED feature (Category-2 composed, Direction 1) | SUSPICIOUS (trade-selection sub-channel) |
| #5 | /086 | NEW crypto-native DATA FEED — perp-spot basis 3-feature family (Direction 1) | INERT |
| #6 | /087 | symbol-universe EXPANSION 3→6 WHOLESALE (+GALA+MANA+SAND, Direction 2) | **NEGATIVE** |
| #7-#10 | /088-/091 | TBD per QR research + EDA | — |
| CONFIRMATION | /092 | best cycle-3 bundle (multi-seed validation) | pre-registered MERGE gates |

Cycle 3 has used 6 of its 10 EXPLORATION slots — outcome distribution: 1 SUSPICIOUS-OOS-DOMINANT, 1 NEGATIVE, 1 REFERENCE-REANCHOR, 1 SUSPICIOUS, 1 INERT, 1 NEGATIVE — **0 clean PROMISING.** The pattern matches cycles 1 and 2 (each 0 clean PROMISING). Across 3 cycles (~26 EXPLORATIONs) v3 has found exactly **ONE** edge ingredient — /025's `regime_momentum_signed_5d`, already in the /059 baseline. The clean current-data EXPLORATION-MODE-REFERENCE (/084) is IS +0.8325 / OOS +0.3322 — both below the +1.0 merge floors.

### 8.2 The three structural directions are now ALL exhausted

The cycle-3 plan identified three structural directions. After 6 EXPLORATIONs, all three are closed or near-closed:

- **Direction 1 — NEW crypto-native feature families.** CLOSED by the **7-feed structural verdict** (/086 closeout). Seven independent non-OHLCV feeds — funding rate (5 data points: /019/023/024 direct z-scores, /082 the 4-channel family, /085 the composed sign-switch), microstructure (/015 `tbr_zscore_30`), perp-spot basis (/086) — ALL rank bottom-of-stack by importance. The v3 per-symbol depth-3-5 LightGBM trained on ~2700-5700 IS rows does not allocate ranked split capacity to crypto-native sentiment features regardless of the feed or construction.
- **Direction 2 — universe expansion / breadth.** CLOSED this iteration at a **4-failure track record** (/021/069/083/087) — single, double, and wholesale adds all NEGATIVE. The breadth `√N` benefit does not transfer through the production Optuna+7-gate stack.
- **Direction 3 — multi-symbol-pooled model.** The naive form was EDA-falsified at /085 (only 7/14 features sign-agree on feature→label IC across symbols; pooled+`symbol_id` breaks BCH). A *non-naive* variant remains formally untested — but see the assessment below.

### 8.3 FRANK CYCLE-3 STRATEGIC ASSESSMENT — senior-researcher honest read

**(a) Are there genuinely un-tried structural axes left for /088-091 with a real (not token) chance of an edge?** Honestly — very few, and I will name only the ones I actually believe carry signal-discovery potential, not padding:

1. **A non-naive pooled / cross-sectional model — but ONLY in the cross-sectional-ranking framing, not the absolute-return framing.** The /085 EDA falsified naive pooling on *absolute-return* feature→label IC sign-agreement. It did NOT test the genuinely different operation: **cross-sectional ranking** — at each 8h bar, rank the universe symbols by predicted edge and trade the top/bottom of the cross-section (the v1 Model A precedent is pooled-but-still-absolute; this is different — it is a relative-value model). Cross-sectional crypto factors (size, momentum, low-vol, the Karagiorgis skew-kurtosis plane) have a real 2024-25 literature and are *designed* to be robust where per-symbol absolute models overfit. This is the one Direction-3 variant I believe has a real chance. **Mechanism: the label becomes "did this symbol out/under-perform the cross-section over the next horizon" rather than "did this symbol hit its TP barrier" — a relative label is structurally lower-variance and the /087 result (3 symbols each individually overfit) is exactly the failure mode a cross-sectional model is built to avoid.** It REQUIRES a larger universe (cross-sectional ranking is meaningless at N=3) — and /087 just demonstrated the 6-symbol data is fetched and the feature pipeline is symbol-agnostic. This is the highest-EV remaining axis. It is a genuine model-paradigm change, not a knob.
2. **Meta-labeling, properly executed (the cycle-2 mandate that was never cleanly run).** /017 attempted meta-labeling but as a single-seed over-filter; the cycle-2 plan named it HIGHEST priority and it was never properly executed. An M2 secondary classifier that predicts *whether to act* on the M1 triple-barrier direction is the canonical López de Prado response to a model whose IS edge does not transfer to OOS (AFML Ch. 3) — and /087's per-symbol IS-overfit (positive IS, negative OOS on GALA/MANA/SAND) is precisely the precision-problem meta-labeling targets. I rate this MEDIUM-real (not token): it has a clear mechanism, but /017's over-filter outcome is a genuine warning that the M2 can kill trade count below the floor.

Everything else — more gate knobs, more ATR tweaks, more single-feature additions, on-chain feeds (an 8th crypto-native family, forbidden by the 7-feed verdict) — I do **not** believe carries signal-discovery potential and will not list as a real axis.

**(b) Or is the v3 structural search space, as currently framed, genuinely exhausted?** Largely — yes, for the search space **as currently framed**: *per-symbol* LightGBM + 8h candles + this universe + triple-barrier *absolute*-return labeling. Within that exact frame, three cycles have produced one edge ingredient and the conservative + structural axes are both closed. The binding constraint is now visible and it is **architectural, not feature-level**: a per-symbol depth-3-5 tree on ~3-6k IS rows, predicting an absolute TP/SL barrier hit, overfits IS and does not generalize — and that is true whether you feed it OHLCV features, crypto-native features, or more symbols. The 7-feed verdict and the 4-failure universe record are two faces of the same finding: the *model architecture and the label definition*, not the feature set or the universe size, are the ceiling.

**(c) Recommendation.** Do **not** spend /088-091 on more feature/universe/knob EXPLORATIONs — that is the pattern that produced three 0-PROMISING cycles. Two concrete paths, in priority order:

- **PRIMARY — pivot /088-091 to the model-paradigm and label-definition axes that are still genuinely untried: a cross-sectional-ranking model (relative-value label) over the 6-symbol universe (/088, the highest-EV remaining axis), and properly-executed meta-labeling (/089).** These are the only two axes I believe have real signal-discovery potential. They are structural (a different problem framing — relative-value and act/don't-act — not a knob), they directly target the architectural ceiling /087 exposed, and the cross-sectional model finally makes constructive use of the breadth that Direction-2-as-an-expansion-of-per-symbol-models could not.
- **PARALLEL — escalate for a strategic rethink.** The honest senior read is that v3, framed as per-symbol-LightGBM / 8h / triple-barrier-absolute-labels, has a low ceiling and three cycles of evidence say so. The cross-sectional and meta-labeling pivots above are worth /088-091, but if they also fail, the recommendation is to **escalate to the user for a paradigm decision** rather than open a cycle 4 of the same frame. Candidate paradigm changes for that escalation: (i) abandon per-symbol absolute-return prediction for the cross-sectional relative-value framing wholesale (make it the v3 architecture, not one EXPLORATION); (ii) revisit the candle interval — 8h was chosen for funding-cycle alignment, but the 7-feed verdict means v3 never used the funding signal, so the 8h justification is now weak and a different interval (4h for more samples per symbol, 1d for less microstructure noise) is on the table; (iii) reframe v3 as a pure regime-overlay / risk-allocation layer on v1+v2 rather than a standalone alpha source. This is a user-level decision and should be raised as one, not buried in an EXPLORATION slot.

The /088 setup mandate (revert `V3_MODELS` 6→3, `REQUIRED_GAP` 132→66) restores the /059 starting point; the /088 *axis* should be the cross-sectional-ranking model, QR-EDA-driven per `feedback_v3_axis_selection_quant_discipline.md`.

---

**Commit chain:**
- EDA SHA: `1a117b2` — `analysis/iteration_v3-087/wholesale_breadth_expansion_eda.py` + `robustness_check.py` + the T1-T6 CSVs
- Brief SHA: `287ce0d` (research brief)
- Setup SHA: `0d9a5e4` (V3_MODELS 3→6 + REQUIRED_GAP 66→132 + basis-revert + the 9 affected test files)
- SHA-backfill SHA: `a4b641f` (EDA/brief/setup SHAs backfilled into brief Section 11)
- Phase 5.5 gate SHA: `8d8253f` (PASS — QR-driven wholesale-breadth-expansion axis certified)
- Engineering report SHA: `32becde`
- Critic FINAL SHA: `24a9dcc` (OVERALL=MERGE — methodology-only; result-read NEGATIVE)
- Phase 8 roster-diff analysis SHA: `541e626` — `analysis/iteration_v3-087/roster_diff_oos.py` (the F4 / sub-channel-(c)/(d) adjudication)
- Diary + catalog + cycle3_plan + BASELINE_V3.md Dead-Ideas SHA: `6407312` (this closeout)
**Reports**: `reports-v3/iteration_v3-087/`
**Tag**: `v0.v3-087` (EXPLORATION closeout marker; NOT a baseline update — BASELINE_V3.md UNCHANGED at `v0.v3-059`)
