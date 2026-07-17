# team-02 IS report — Phase 2 (QE implementation complete)

STATUS: original family `t02-52wk-high-anchor-v1` FALSIFIED in its registered
direction (Section 1 — kept at full precision as part of this submission's honesty
record); documented pivot to `t02-anchor-discount-contrarian-v1` APPROVED in
`registry.jsonl` and designed to a frozen spec (Section 4; research_brief.md PART D).
The QE has implemented that frozen spec in `strategy.py`; the CHOSEN-config headline
numbers in Section 4 are now the CANONICAL `cli.py team-run` output
(`out/is_metrics.json`), reproduced bit-exactly against the QR's reference pipeline
(`out/scratch_explore.py :: build_raw`, grid `exp-012[0]`) — Sharpe +0.4921 @1× /
+0.4695 @2×, maxDD −0.3909, ann. turnover 3.07, breadth 22/26. Harness
`cli.py audit --team team-02` = PASS (all five checks). The NEGATIVE-result record
(Sections 1–2) and the plateau/ladder evidence (Sections 3–4 neighbor rows) are
research-provenance numbers from `tournament.engine.run_is` with raw JSON preserved in
`out/scratch_exp-0*.json`; they are retained verbatim as the honesty record and are
NOT the submission's headline metrics.

## 1. Registered family result (NEGATIVE — reported with full precision)

Signal: PH = close / rolling_max(high, L, min_periods=M); long near-high / short
far-from-high (George–Hwang direction). IS window 2010-01-01 → 2024-06-30, 174 months,
65 names (41 with bars in 2010; ragged starts respected, never forward-filled).

| Config | Sharpe @1× | Sharpe @2× | maxDD | ann. turn | med names L/S |
|---|---|---|---|---|---|
| L=252 M=126 rank (baseline) | −0.7616 | −1.0523 | −0.889 | 40.2 | 24 / 24 |
| L=126 rank | −0.7227 | −1.0851 | −0.881 | 49.6 | 24 / 24 |
| L=189 rank | −0.7676 | −1.0793 | −0.890 | 43.7 | 24 / 24 |
| L=315 rank | −0.7232 | −0.9985 | −0.882 | 38.2 | 24 / 24 |
| L=378 rank | −0.7463 | −1.0111 | −0.890 | 36.7 | 24 / 24 |
| L=252 zscore | −0.6725 | −0.8019 | −0.906 | 25.8 | 30 / 18 |
| L=252 tercile | −0.5623 | −0.8260 | −0.824 | 33.5 | 17 / 16 |
| L=252 quintile-tails | −0.7212 | −1.0379 | −0.885 | 55.2 | 10 / 9 |
| L=252 rank h=5 | −0.5176 | −0.5870 | −0.816 | 9.5 | 25 / 23 |
| L=252 rank h=10 | −0.4941 | −0.5417 | −0.808 | 6.6 | 26 / 22 |
| L=252 rank h=21 | −0.4908 | −0.5226 | −0.810 | 4.4 | 26 / 22 |
| L=252 rank h=10 + inv-vol | +0.2320 | +0.1513 | −0.333 | 8.1 | 26 / 22 |

- Best legitimate configuration: −0.49 vs the pre-registered falsifier bar of ≥ +0.30
  → **falsifier tripped across the entire pre-registered space.**
- The single positive row is a beta artifact, not the mechanism: mean_net = +0.2098
  (net-cap-pinned long book), regime Sharpe bull +0.415 / bear −1.371. Rejected.
- Regime scorecard of the baseline (@1×): bull −0.879, bear +0.079, chop −0.616 —
  the family's pre-registered crash mode (buy-the-dip junk rallies) is this
  universe's dominant regime.

## 2. Falsification diagnostic — reversed book (pivot-request evidence)

Long deep-discount-to-anchor / short near-anchor (rank, reversed sign):

| Config | Sharpe @1× | Sharpe @2× | maxDD | ann. turn | med names L/S |
|---|---|---|---|---|---|
| L=252 h=21 | +0.4272 | +0.3952 | −0.390 | 4.4 | 22 / 26 |
| L=252 h=10 | +0.3985 | +0.3504 | −0.400 | 6.6 | 22 / 26 |
| L=315 h=10 | +0.3862 | +0.3406 | −0.410 | 6.2 | 23 / 25 |
| L=189 h=10 | +0.3608 | +0.3100 | −0.368 | 7.2 | 23 / 26 |
| L=252 h=5 | +0.3781 | +0.3080 | −0.404 | 9.5 | 23 / 25 |
| L=252 unsmoothed | +0.1666 | −0.1316 | −0.400 | 40.2 | 24 / 24 |
| L=252 h=10 + inv-vol | −0.3932 | −0.4736 | −0.698 | 8.1 | 22 / 26 |

Regime scorecard (L=252 h=21, @1×): bull +0.571, bear −0.459, chop +0.166.
Mean net ≈ 0.003 (dollar-balanced), mean gross 1.0, breadth floor passed everywhere.
Every smoothed config on every lookback is positive at BOTH cost tiers — plateau, not
peak. No further optimization has been run: that belongs to the pivoted family after
approval (pre-registered remaining space in research_brief.md PART C).

## 3. Pivoted family — PART C ladder (exp-007 … exp-012, post-approval)

All configs: centered pct-rank of PH = close/rollmax(high, L, min_periods=M), sign
reversed (long deep-discount / short near-anchor), EWM halflife H, PH lagged SKIP days.

| exp | Axis | Result @1× (Sharpe) |
|---|---|---|
| exp-007 | H ∈ {21, 42, 63} at L=252 | 0.4272 / 0.4701 / 0.4894 — gain flattens (Δ 0.043 → 0.019), bear −0.46→−0.62 at H=63 → midpoint H=42 per pre-committed rule |
| exp-008 | L ∈ {252, 378, 504} at H=42 | 0.4701 / 0.4415 / 0.3856 — gentle decay; L=252 kept (canonical 52-week anchor) |
| exp-009 | rank vs tercile at (252, 42) | 0.4701 / 0.3733 — rank kept |
| exp-010 | SKIP ∈ {0, 21} | 0.4701 / 0.4921 — skip adopted (bear −0.48→−0.36, maxDD −0.400→−0.391, @2× 0.448→0.470) |
| exp-011 | M ∈ {63, 126, 252} | 0.3762 / 0.4921 / 0.3888 — least-flat axis; M=126 was the incumbent default, not swept in; neighbors above falsifier bands |
| exp-012 | final confirmation: chosen + one-step neighbors on every axis | table in Section 4 |

## 4. Final configuration (frozen for the QE) and falsifier check

**L=252, M=126, centered pct-rank, SKIP=21, H=42, sign=−1** (full pipeline:
research_brief.md PART D.2).

| Config | Sharpe @1× | Sharpe @2× | maxDD @1× | ann. turn | med names L/S |
|---|---|---|---|---|---|
| **CHOSEN** | **0.4921** | **0.4695** | **−0.3909** | **3.07** | **22 / 26** |
| L=189 neighbor | 0.4243 | 0.4004 | −0.3869 | 3.39 | 22 / 26 |
| L=315 neighbor | 0.4878 | 0.4662 | −0.4023 | 2.87 | 22 / 26 |
| H=21 neighbor | 0.4507 | 0.4180 | −0.3601 | 4.40 | 22 / 26 |
| H=63 neighbor | 0.4926 | 0.4745 | −0.4177 | 2.49 | 22 / 26 |
| SKIP=0 neighbor | 0.4701 | 0.4482 | −0.4004 | 3.09 | 22 / 26 |
| M=63 neighbor | 0.3762 | 0.3520 | −0.4094 | 3.17 | 22 / 26 |
| M=252 neighbor | 0.3888 | 0.3656 | −0.4322 | 3.09 | 22 / 26 |

- Pivot falsifier (pre-registered PART C): every neighbor must hold @1× ≥ 0.30 AND
  @2× > 0.25 with breadth ≥ 5/side → **NOT TRIPPED** (worst neighbor 0.3762 / 0.3520;
  breadth 22/26 everywhere).
- Chosen-config detail (@1×), from the canonical `cli.py team-run` artifact
  (`out/is_metrics.json`): total_return +1.927 over 174 months, mean_gross 1.0,
  mean_net +0.0069, regime Sharpe bull +0.679 / bear −0.358 / chop +0.037. The
  neighbor rows above are plateau evidence from `out/scratch_exp-012.json` (same
  evaluator, `tournament.engine.run_is`).
- Selection tensions (H=63 edge, M-axis peakiness) documented in PART D.4 — not
  hidden.
- Known regime risk, stated plainly: the book LOSES in bear regimes (−0.36) by
  construction (long beaten-down names in crashes); it pays in bull (+0.68) and is
  ~flat in chop. A holdout dominated by a sustained bear will hurt this book.

## 5. Ledger state

14 lines total in `experiments.jsonl`: 1 registration (reg-001), 12 material
experiments (exp-001 … exp-012, counting the exp-006 falsification diagnostic
conservatively as material), 1 falsification note. Budget used: 12 of 40. PART C used
exactly its pre-registered ≤ 6 (exp-007 … exp-012). No further QR experiments planned.

QE closeout: `strategy.py` implements research_brief.md PART D.2 verbatim; the frozen
headline numbers now come from `cli.py team-run` (`out/is_metrics.json`) and match the
QR reference (`out/scratch_explore.py`, grid `exp-012[0]`) bit-exactly. `cli.py audit`
= PASS (static-scan, determinism, truncated-replay, future-corruption, same-bar). No
research choices were made in implementation; no spec ambiguity was found.
