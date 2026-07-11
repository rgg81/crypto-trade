# EXPLORATION-G — engineering diary (slow-label reformulation, ENGINE-scored): **TIER = FAIL**

**Track:** MN3 (two-year-holdout market-neutral). **Date:** 2026-07-11. **Role:** QR/QE (retrain +
scored engine run). **Stage:** Stage-1 IS-only design-validation. **IS window:** 2020-01-01 →
2024-06-30 (`MN3_IS_CUTOFF_MS = 2024-07-01`). **Holdout SEALED** — `mn3_guard_grid` ran on the
IS-sliced grid with `reveal_token=None`; `REVEAL-LEDGER.md` untouched (zero `SPENT` lines); **`MN3-G`
UNSPENT.** Nothing committed to git.

**Spec executed:** `briefs-portfolio-mn3/EXPLORATION-G.md` + `EXPLORATION-G-AMENDMENT-001`
(MUST-1/MUST-2 binding; SHOULD-3..7 applied; FLAG-8 recorded), per the Critic pre-flight
`REVIEW-G-preflight.md`. Frozen construction implemented EXACTLY; the mechanical decision map (§6)
computed with zero re-gating.

> **MODEL NOTE (mandated disclosure).** Retrain + scored run authored and executed on **Opus 4.8, NOT
> Fable** — the charter's Fable mandate is user-suspended this phase (Fable-5 rate limit; user
> direction "continue on Opus"). Standard unchanged; adversarial burden unchanged. Same posture as
> DIAG-G / EXPLORATION-S4 / the Critic pre-flight. The brief was frozen BEFORE this run; nothing was
> revealed; the holdout is sealed.

---

## Verdict (mechanical, MECE §6): **FAIL — the registered turnover-suppression mechanism is falsified (§5.1).**

The reformulation is, on its economics, a **genuine, neutral, all-weather, crash-robust,
placebo-clean, correctly-signed market-neutral book that clears the honest 2× cost wall** — 13/14
HARD gates pass, 2×-cost Sharpe **+0.70**, turnover **62×** (vs DIAG-G's 156×), CRASH edge PRESERVED
and STRENGTHENED (fresh CRASH quintile-spread **t +11.03** vs DIAG-G's +3.21). **But the WHY is not
the registered WHY.** The §5.1 un-suppressed control — the pre-registered HARD falsifier that "the
suppression must cut COST, not add SIGNAL" — **fired on both of its legs**: the slow label did NOT
slow the continuous book (turnover 65.1× vs the fast label's 68.4×; ratio 0.951, not `< 0.5×`), and
the slow book's net win is driven by **higher GROSS** (better signal: +20.5% vs +12.1%; ratio 1.695,
not `≤ 1.25×`), i.e. an un-registered better-alpha claim. Per the frozen map, **a §5-control failure ⇒
FAIL.** This was family-G's ONE authorized revision round (ledger 8→10, cap 16); **a FAIL closes G.**

The honest mechanistic finding is the value of this run: **DIAG-G's kill (d) was a WEIGHTING-
CONSTRUCTION artifact (quintile-extreme), not a horizon-mismatch.** The turnover fix (156× → ~68×)
came from the CONTINUOUS IC-proportional weighting (the §1.2 book form: quintile → `rank_neutral`),
which the brief bundled alongside the label change; the horizon-matched slow LABEL contributed almost
nothing to turnover (68.4× → 65.1×, a 5% cut) and instead delivered a **better signal** (IC
0.0369 → 0.0502). The brief attributed the turnover cure to Lever B (the slow label); the data
attributes it to the continuous weighting. §5.1 caught exactly this.

---

## 1. Retrain verification (Lever B; MUST-1 binding) — PASS

Runner: `analysis/portfolio/mn3_g_oof_slow.py` (clone of the frozen `mn3_g_oof.py`). The three
horizon constants were overridden on the imported `mn3_features` MODULE **in-process only**
(`LABEL_FWD_K` 3→21, `LABEL_WINSOR` 0.20→0.53, `MN3_G_PURGE_CANDLES` 3→21); the frozen module,
DIAG-G scoring, and the test suite read the unmodified constants (verified: `test_mn3_features` green).
Output → `data/mn3_g_slow/oof_predictions.parquet` (the frozen `data/mn3_g/` fast parquet untouched).

**MUST-1 (the load-bearing leak fix) — implemented via the Critic-preferred refactor.** The runner no
longer duplicates the inline purge (`mn3_g_oof.py:143` `b_idx - 3 - 1`); it consumes
`oof_month_slices(grid, purge=21).train_mask` as the **single source of truth**, eliminating the
landmine. An **ABORT-ON-FAIL purge assert** (DIAG-G §3 "Purge PASS" re-run at horizon 21) runs BEFORE
any fit and BEFORE persist: for every walk-forward month, `last_train_idx + 21 < b_idx`.

| MUST-1 check | Result |
|---|---|
| Purge assert, all 30 WF months (`last_train + 21 < b_idx`) | **PASS** (zero train-label / OOF overlap at horizon 21) |
| Per-month member-row re-assert (belt-and-suspenders) | PASS (all 30) |
| Negative control (unit test: purge=3 at horizon 21) | violates on 30/30 months — the assert WOULD catch the landmine |

**SHOULD-7 — winsor clip-fraction (the √-horizon anchor's falsifiable claim):**

| label | winsor | realized clip-fraction | interpretation |
|---|---|---|---|
| SLOW 21c | ±0.53 (= 0.20·√7) | **0.69%** | the anchor HOLDS — clip-fraction comparable to fast |
| FAST 3c | ±0.20 | **0.92%** | (reference) |
| SLOW 21c @ ±0.20 (counterfactual) | ±0.20 | **8.59%** | a fixed ±0.20 would clip 12× more — destroying the fat tails where the crash edge lives |

The √-horizon rescale (±0.20→±0.53) preserves the SAME distributional clip-fraction (0.69% ≈ 0.92%);
a naïve unscaled ±0.20 would have clipped 8.59% and damaged crash preservation. Anchor validated.

**Row/finiteness verification:** 109,440 OOF rows (= 2,736 OOF candles × 40; identical to the fast
parquet); **finite predictions 109,440/109,440** (all 40 pred cols finite); finite labels 107,430
(2,010 NaN = the 21c IS tail, more than the fast's 740, consistent with the longer horizon);
**max open_time < IS cutoff = True** (no holdout leak). Wall: 12.2 min (30 mo × 8 configs × 5 seeds =
1,200 fits).

---

## 2. Signal — slow-c1 pooled OOF IC (the reformulation IMPROVED the signal)

Per-candle cross-sectional Spearman(c1 seed-ensemble prediction, winsorized 21c label), pooled over
2,715 finite OOF candles (median 40 members).

| quantity | slow-c1 (21c) | DIAG-G fast-c1 (3c) | brief expectation | read |
|---|---|---|---|---|
| pooled OOF IC | **+0.0502** | +0.0369 | +0.022 [+0.010,+0.037] | **ABOVE** the range — the 21c target is SMOOTHER, not noisier; a stronger signal |
| per-year 2022 / 2023 / 2024-H1 | +0.0947 / +0.0145 / +0.0317 | +0.0372 / +0.0433 / +0.0232 | all >0 | 3/3 right-signed |
| per-seed (c1) | 42:+0.0487 123:+0.0479 456:+0.0500 789:+0.0471 1001:+0.0485 | — | all >0 | 5/5 right-signed |

**G-signal-IC (pooled > 0 AND ≥2/3 years right-signed): PASS** (comfortably).

**7-config HP-insensitivity cross-check (MUST-2 — cross-check ONLY; tier keys off c1 alone, no
selection):** pooled ICs c0…c7 = +0.0481 / **+0.0502** / +0.0479 / +0.0474 / +0.0488 / +0.0491 /
+0.0476 / +0.0460 — a tight +0.046…+0.050 band; c1 is the max, consistent with the a-priori pin
(pinning cut in the safe direction). No design choice keyed off c0/c2…c7.

---

## 3. Full 14-HARD + 4-SOFT scorecard (as-shipped book = **throttled**, throttle NEUTRAL)

Scored object = the as-shipped book per the §2.2 disposition (NEUTRAL ⇒ throttled). Every threshold
principle/charter/S4-verbatim or a zero/sign floor.

| # | Gate | Class | Realized | Threshold | Verdict |
|---|---|---|---|---|---|
| G1a | rolling-270 \|β_BTC\| | NEUT | ≤0.10 on **100.0%**, max **0.0705** | ≥95% & max ≤0.20 | **PASS** |
| G1b | rolling-270 \|β_ETH\| | NEUT | ≤0.15 on **100.0%**, max **0.0839** | ≥95% & max ≤0.25 | **PASS** |
| G2-CRASH | CRASH bucket \|β_BTC\| | NEUT | **0.0393** (n=354) | ≤0.15 | **PASS** |
| G2-MANIA | MANIA bucket \|β_BTC\| | NEUT | **0.0218** (n=293) | ≤0.15 | **PASS** |
| G3 | \|Σw\|/gross at rebals | NEUT | **0.0000** | ≤0.10 | **PASS** |
| G4 | worst-bucket mean-net t | NEUT | **−0.56** (MANIA) | > −1.0 | **PASS** |
| G-signal-IC | pooled OOF IC | SIGNAL | **+0.0502**, 3/3 yrs | >0 & ≥2/3 yr | **PASS** |
| G-crash-preserve | CRASH net>0 AND fresh CRASH quint t>0 | ALL-WEATHER | **+6.56 bps** & **t +11.03** | both right-signed | **PASS** |
| G-2xcost | 2×-cost Sharpe & ratio & ann | ECON | **Sh +0.7035, ann +9.76%** (≥0.5×1.04) | >0 & ratio & ann>0 | **PASS** |
| G-turnover | ann one-way turnover | ECON | **61.8×** | ≤104× | **PASS** |
| G-sharpe-floor | net Sharpe (1×) | ECON | **+1.0376** | ≥+0.35 | **PASS** |
| G-maxdd | as-shipped maxDD | ECON | **−21.56%** | ≥−25% | **PASS** |
| **G-durable** | H1 net>0 AND H2 net>0 | ECON | **H1 −0.35 bps / H2 +1.50 bps** | both >0 | **FAIL** |
| G-sample | span / rebals / names / years | ECON | 2.50yr / 130rb-ph / 40nm / {22,23,24} | 2.0/100/20/all-3 | **PASS** |

**HARD: 13/14 pass** (only G-durable fails). G-durable's H1 = the 2022-01→2022-03 OOF overlap (only 3
months — the OOF span starts 2022-01, so H1 is thin Q1-2022 at −0.35 bps/candle); a structural
OOF-start artifact, but per the frozen gate it is a FAIL. (Even had §5.1 passed, a G-durable ECON-HARD
fail routes to **MARGINAL**, never SUCCESS — the book is not a clean 14/14.)

| SOFT gate | Realized | Threshold | Verdict |
|---|---|---|---|
| G-crash-strong | fresh CRASH quint **t +11.03** | > +1.5 | **PASS** (crash edge preserved AND strong) |
| G-sharpe-target | **+1.0376** | ≥ +0.90 | **PASS** |
| G5 | max bucket P&L share **64.6%** (CRASH) | ≤ 60% | **FAIL** (one-regime concentration) |
| G-3xcost | 3×-cost Sharpe **+0.3696** | > 0 | **PASS** |

**SHOULD-3:** N/A — G-crash-preserve passes AND G-crash-strong passes; the crash edge is preserved
and *strengthened* (t +11.03 > DIAG-G's +3.21), so no "crash-edge-preserved-but-weakened" flag.

---

## 4. Throttle disposition (C2 MECE partition) — **THROTTLE-NEUTRAL** (pre-registered prediction was HURTS)

| quantity | value |
|---|---|
| coverage: scalar<1 / =φ / mean | 18.7% / 7.8% / 0.9378 (no coverage-mismatch) |
| Δmaxdd = depth(un-thr) − depth(thr) | **+0.99%** (throttle made DD ~1pp shallower) |
| s = Sharpe(thr)/Sharpe(un-thr) | **0.967** |
| partition | Δmaxdd (0.99%) ∈ [0,+2pp) AND s (0.967) ≥ 0.90 ⇒ **NEUTRAL** |
| as-shipped book | **throttled** |

The pre-registered prediction was HURTS (a downside throttle firing in G's profitable crashes); it
came back NEUTRAL — a mild DD help with a near-unchanged Sharpe. Ships throttled; the G divergence
(HURTS stays SUCCESS-eligible) was not needed. The throttle is not the alpha: the un-throttled book
independently grosses/Sharpes above the floors (a scalar ∈ [φ,1] cannot manufacture positive alpha —
SHOULD-4).

---

## 5. Controls — the DISCRIMINATING §5.1 fired; §5.2/§5.3 passed

### §5.1 — un-suppressed comparison vs FROZEN fast-c1 (cut COST not SIGNAL) — **FAIL (the killer)**

Same continuous `rank_neutral` book + same projection + same cost + same 21-rebal; only the signal
varies (slow-c1 vs the frozen fast-c1 parquet, no re-fit). Both un-throttled (apples-to-apples).

| book | gross_ann | net1x_ann | turnover | cost_ann | Sharpe(1×) |
|---|---|---|---|---|---|
| **SLOW** un-thr | **+20.53%** | +15.65% | **65.1×** | 4.88% | +1.073 |
| **FAST** un-thr | **+12.11%** | +6.98% | **68.4×** | 5.13% | +0.507 |

**SHOULD-6 decomposition:** Δnet **+8.66%** = Δgross **+8.41%** − Δcost **+0.25%** (check +8.66% ✓).

| §5.1 sub-condition | required | realized | pass? |
|---|---|---|---|
| turnover(slow) < 0.5 × turnover(fast) | ratio < 0.5 | **0.951** | **FALSE** |
| gross(slow) ≤ 1.25 × gross(fast) | ratio ≤ 1.25 | **1.695** | **FALSE** |

**Both legs fail.** 97% of the net improvement (+8.41% of +8.66%) is GROSS (better signal); only 3%
(+0.25%) is cost. The slow label did NOT slow the book (turnover fell 5%, not ≥50%); it produced a
better alpha (IC +36%, gross +70%). The registered mechanism — "the horizon-match suppresses turnover,
cutting cost" — is **falsified**; the true turnover cure was the continuous weighting (a §1.2 book-form
change), and the label's benefit is an un-registered signal improvement. **§5.1 = FAIL.**

### §5.2 — shuffled-signal GROSS placebo (20 seeds; two-sided C4 null; GROSS = price+funding, pre-cost, SHOULD-5) — **PASS**

| quantity | value |
|---|---|
| placebo GROSS Sharpe (20 seeds) | mean **−0.0411**, sd 0.7033, 95% CI **[−0.349, +0.267]** (min −1.43, max +1.29) |
| real GROSS Sharpe | **+1.4082** |
| real − placebo differential | **+1.4493** (> 0 ✓) |
| two-sided GROSS null (CI ∋ 0) | **True** |
| placebo beta-neutral (max\|β_BTC\| 0.0056 ≤ 0.20) | **True** |

The plumbing is not the edge: a rank-shuffled, demeaned, beta-projected book has a GROSS-Sharpe null
centered at ~0, and the real signal carries +1.45 of gross Sharpe over that null. **§5.2 = PASS.**

### §5.3 — reversed-direction (frozen must beat reversed) — **PASS**
Frozen (un-thr) Sharpe **+1.0732** vs reversed **−1.7429** ⇒ frozen ≫ reversed. Direction integrity
holds (the +1 model-forecasts-the-label sign is correct). **§5.3 = PASS.**

---

## 6. Neutrality panel (incl. ETH buckets) — all NEUT-HARD PASS

| metric | value | gate |
|---|---|---|
| full-window OLS β_BTC | **+0.0047** (se 0.0051) | — |
| full-window OLS β_ETH | **+0.0039** (se 0.0040) | — |
| rolling-270 \|β_BTC\| ≤0.10 coverage / max | 100.0% / 0.0705 | G1a PASS |
| rolling-270 \|β_ETH\| ≤0.15 coverage / max | 100.0% / 0.0839 | G1b PASS |
| CRASH β_BTC (n=354) | +0.0393 | G2-CRASH PASS (≤0.15) |
| MANIA β_BTC (n=293) | −0.0218 | G2-MANIA PASS (≤0.15) |
| CHOP β_BTC (n=2088) | −0.0022 | — |
| **CRASH β_ETH** (reported) | **+0.0318** | — |
| **MANIA β_ETH** (reported) | **−0.0343** | — |
| G3 max \|Σw\|/gross at rebals | 0.0000 | G3 PASS |

Bucket net returns: CRASH +6.56 bps/cd (t +2.61, PnL 64.6%), MANIA −1.83 bps/cd (t −0.56, PnL −14.9%),
CHOP +0.86 bps/cd (t +1.03, PnL 50.2%). Worst-bucket t = −0.56 > −1.0 ⇒ G4 PASS. Max bucket P&L share
64.6% ⇒ G5 SOFT FAIL (the crash-concentrated P&L is the flip side of the strong crash edge).

---

## 7. All-weather / crash read (SHOULD-3) — crash edge PRESERVED **and STRENGTHENED**

- **G-crash-preserve PASS:** (i) CRASH-bucket mean net **+6.56 bps/cd, t +2.61** (>0); (ii) fresh CRASH
  quintile-spread of the slow-c1 prediction **+0.04334, t +11.03** (plain), t/√21 **+2.41**
  (overlap-conservative), n=354.
- **G-crash-strong (SOFT) PASS:** t +11.03 ≫ +1.5. The 21c label did NOT dilute the crowding-syndrome
  crash edge — it SHARPENED it (DIAG-G fast CRASH t was +3.21). The all-weather property the mandate
  demands is intact; the slow book does NOT clear cost by abandoning the crash edge.

---

## 8. 21-phase distribution + leak battery

**21-phase (as-shipped) Sharpe:** min +0.040, p25 +0.517, med +0.670, p75 +1.017, max +1.366;
**positive 21/21** — no phase-lottery; the phase-agnostic headline (+1.04) is robust (contrast
DIAG-G's 9/21 quintile phases).

**Leak battery — ALL PASS** (assert-enforced): (a) MUST-1 purge assert re-verified at horizon 21 on
all 30 WF months (`last_train+21 < b_idx`); (b) corrupt-future on the G-LCDD-z throttle (close+pred
future garbage ⇒ `scalar[<t0]`/`z[<t0]` bit-identical, future changed); (c) inert-default byte-identity
(throttle `None` ≡ `ones`); (d) decision-lag [k−1] (perturb `sig[t0]` ⇒ `weights[:t0+1]` identical).
§5.2 placebo is the negative control (nulls correctly). Unit tests: `tests/test_mn3_exploration_g.py`
(10 tests, all green) — throttle corrupt-future + cohort=top-prediction + scalar bounds/warmup;
per-candle IC perfect/inverse/degenerate; crash quintile-spread sign; placebo determinism/marginal;
and the MUST-1 purge-index property (purge=21 no-overlap, purge=3 would-leak).

---

## 9. Mechanical TIER (MECE §6) — **FAIL**

```
NEUT all pass: True   G-signal-IC: True   G-crash-preserve: True
§5.2 placebo: True    §5.3 direction: True
§5.1 un-suppressed:   FALSE  ← a §5-control failure
ECON all pass: False  (G-durable fails; would be MARGINAL if reached)
14/14 HARD: False     disposition: THROTTLE-NEUTRAL
```

FAIL = ¬(NEUT ∧ G-signal-IC ∧ G-crash-preserve ∧ §5-controls). The §5.1 control failed ⇒ **FAIL.**
(Independently, G-durable ECON-HARD also fails, which alone would cap the tier at MARGINAL, never
SUCCESS.) No re-gating; the falsifier fired exactly as pre-registered.

**Reason:** §5.1 — the slow label's net win is signal-driven (gross ratio 1.695 > 1.25), not
cost-driven, and the label did not slow the book (turnover ratio 0.951, not < 0.5). The registered
turnover-suppression mechanism (Lever B, horizon-match) is falsified.

**Consequence:** **G does NOT bank.** `MN3-G` is UNSPENT; the holdout is sealed. This EXPLORATION
invoked family-G's ONE authorized revision round (ledger 8→10, cap 16). **This was the LAST round — a
FAIL closes family G (FLAG-8).**

---

## 10. Honest interpretation (what actually happened — the value of this run)

1. **DIAG-G's kill (d) was a weighting-construction artifact, not a horizon-mismatch.** The turnover
   cure (156× quintile → ~68× continuous) is the **continuous IC-proportional weighting**
   (`rank_neutral`), a §1.2 book-form change the brief bundled with the label. The fast-c1 CONTINUOUS
   book already runs at 68.4× / gross +12.11% / net1x +6.98% — implying a fast-label continuous book
   would already clear the 2× wall (gross +12.1% − 2×5.1% ≈ +1.9%). The quintile-extreme book (0↔full
   flips, ~3.0 Σ|dw|/rebal) was DIAG-G's cost problem; a graded cross-section fixes it regardless of
   label horizon.
2. **The slow label is a real SIGNAL improvement, not a turnover fix.** IC +0.0369 → +0.0502 (+36%),
   gross +12.1% → +20.5% (+70%), Sharpe +0.51 → +1.07 — all from a smoother weekly target. But it
   barely touched turnover (68.4× → 65.1×). §5.1 is precisely the control that refuses to let a
   signal-improvement be sold as the registered turnover-suppression mechanism.
3. **The economics DID clear** (G-2xcost +0.70, G-turnover 62×, G-sharpe-floor +1.04, G-maxdd −21.6%)
   and **the crash edge STRENGTHENED** (t +11.03) — this is a genuinely attractive MN book on its
   numbers. The FAIL is a *mechanism-provenance* failure under the frozen discipline, not an economics
   or neutrality failure. That distinction is the honest record; it is NOT grounds to re-gate.
4. **Throttle came back NEUTRAL, not HURTS** — a mild DD help; the a-priori prediction was directionally
   wrong (the throttle didn't fire destructively in crashes here), but it also didn't matter (ships
   throttled, tier unaffected).

**G closes.** A hypothetical future family (NEW token, NEW brief, NEW Critic pre-flight) could register
the *continuous-weighting-of-the-fast-signal* as its primary mechanism — but that is not a G rescue and
is out of scope; it is flagged here as the honest mechanistic lead, not acted on.

---

## 11. Artifacts (all gitignored analysis tree / new test; NOTHING committed)

- Slow OOF runner: `analysis/portfolio/mn3_g_oof_slow.py` (MUST-1 refactor + abort-assert + SHOULD-7).
- Scored engine harness: `analysis/portfolio/mn3_exploration_g.py` (`main()` prints the mechanical
  TIER). Reproduce: `PYTHONUNBUFFERED=1 uv run python analysis/portfolio/mn3_exploration_g.py`.
- Slow parquet: `data/mn3_g_slow/oof_predictions.parquet` + `oof_manifest.json` (MUST-1 PASS recorded).
- Tests: `tests/test_mn3_exploration_g.py` — 10 tests green. Full mn3 subset (`test_mn3_exploration_g`,
  `_s4`, `_features`, `_diag_g_score`, `_diag_j`, `_infra`) 76 passed. Ruff clean on all touched files.
- Logs: `logs/mn3_g_oof_slow.log`, `logs/mn3_exploration_g.log`.
- `REVEAL-LEDGER.md` untouched (zero spends). Holdout sealed. `MN3-G` unspent. Not committed to git.

**Track state after EXPLORATION-G:** Field — DIAG-J DEAD, DIAG-H DEAD-as-ensemble (S4/Amihud the
standalone survivor), DIAG-G **now DEAD** (economics reformulation falsified its own registered
mechanism at §5.1; last round spent). Family ledgers: **G:10 (closed, dead; cap 16)**, H:4, I:11,
~~J:6~~, K:1. G was the only live family; with G closed, the born-ensemble/capstone path has no second
standalone survivor to pair with S4.

*— QR/QE, MN3 track, 2026-07-11 (Opus 4.8, Fable-suspended phase). Pre-registered, scored mechanically,
FAILED at its own frozen §5.1 falsifier. An honest fail: the slow label is a real signal upgrade and
the continuous book is economically viable + crash-robust — but the turnover cure was the weighting,
not the horizon-match, so the registered mechanism is falsified and G closes. Holdout sealed; MN3-G
unspent; nothing committed.*
