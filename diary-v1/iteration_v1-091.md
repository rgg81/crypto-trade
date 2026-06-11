# iter-v1/091 — Phase 8 Diary (R-CONV ensemble-conviction trade gate)

**Date**: 2026-06-11
**Track**: v1 (refactored)
**Branch**: `iteration-v1/091`
**TYPE**: SPECIALIST — machinery EXPLORATION (2nd machinery axis of cycle-7; risk-primitive / post-aggregator RULE family). R-CONV = `enable_r_conv_gate=True, r_conv_tau=0.06` (skip candle if `_sp_confidence < 0.06`). Tested on ETH/064 seat. fail-fast=2.0 ON.
**Cycle**: 7, machinery axis
**Author**: QR (autopilot)
**Tag**: `v0.v1-091`

---

## Headline

**SPECIALIST-NEGATIVE (NEGATIVE-NO-EFFECT) — BLOCKED-FAIL-FAST. R-CONV at τ=0.06 filtered ETH trades as designed (132 vs 198 baseline, 33% reduction = F2 ENGAGED) but did NOT rescue ETH's first-2yr to positive (IS weighted_pnl −5.84, net −2.14%, Sharpe ≈ −0.70). The conviction gate's IS noise-signature did NOT transfer — consistent with the LM Phase 4.5 modal (the ETH OOS dropped-set was +6.25%, mirror-opposite of the IS −5.43%).**

R-CONV is ~neutral-to-marginally-negative on ETH (−2.14% net), MUCH milder than W-DECAY/090's first-2yr crater (−27.9%). The gate engaged (trade count cut 33%) but the candles it removed weren't the OOS-noise the IS gradient implied. F1 NEGATIVE, F2 engaged → NEGATIVE-NO-EFFECT.

---

## Result (fail_fast_report.csv)

| Metric | Value |
|---|---:|
| verdict | **BLOCKED-FAIL-FAST** |
| first-2.0yr IS weighted_pnl | **−5.8391** (≤0 → block) |
| first-2.0yr IS net | −2.14% |
| first-2.0yr IS Sharpe (approx) | **−0.6998** |
| IS trades (gate-filtered, 2.0yr) | 132 (vs baseline 198 full-IS; ~33% reduction = F2 ENGAGED) |
| baseline ETH/064 IS | +0.2383 |
| wall-clock | 13,544s (~3.76h) |

---

## Decision: SPECIALIST-NEGATIVE (NO-EFFECT) — NO MERGE

- R-CONV-on-ETH-at-τ=0.06 is NEGATIVE (didn't rescue the first-2yr). ETH seat unchanged.
- **BUNDLE-002 (`v0.v1-082`) UNCHANGED.**

---

## KEY METHODOLOGICAL FINDING: fail-fast is mis-calibrated for MACHINERY re-tests of existing seats

This is the load-bearing learning (more valuable than the R-CONV verdict itself):
- **Both machinery axes blocked on ETH** — W-DECAY/090 (−27.9%, inverse-edge) AND R-CONV/091 (−2.14%, no-effect). Partly because **ETH's first 2 years (2022-24, incl. the 2022 bear) are WEAK at baseline.**
- The fail-fast gates on **ABSOLUTE first-2yr-IS-positive**. For FRESH-COIN mining that's the right question ("does this new coin have early structure?"). But for a **MACHINERY RE-TEST of a known seat**, it conflates "does the machinery help" with "is this seat's early window positive" — the wrong question. The correct machinery test is **R-CONV-ETH vs baseline-ETH on the SAME window (relative)**, NOT an absolute ≤0 threshold.
- We CANNOT attribute whether R-CONV helped-or-hurt vs baseline (the /064 baseline run.log wasn't preserved → baseline ETH first-2yr unknown).
- **So the machinery axes are NOT cleanly refuted — they were tested under a confounded gate.** A definitive machinery verdict needs a re-test design.

**Recommendation for future machinery axes:** run **fail-fast OFF** and compare full-IS/OOS vs the baseline seat (relative), OR test machinery on a seat with a confirmed-strong first-2yr (e.g. DOT/063). Do NOT gate machinery re-tests on absolute first-2yr-positive.

Secondary finding (QE): the `ensemble_std`-on-skip split (LM §1) is NOT reconstructable — `decision_log.log()` is a no-op in backtest mode (only configured in live `engine.py`), so the r_conv_skip entries were dropped. Academic for this NEGATIVE; future TENTATIVE/PROMISING machinery runs should wire a backtest-mode decision_log path (`reports-v1/iteration_v1-NNN/decision_log.jsonl`).

---

## Next Iteration Ideas

The machinery-on-ETH lane is exhausted (both axes blocked, under a confounded gate). Options:
1. **Re-test a machinery axis correctly** — fail-fast OFF, full run, vs-baseline comparison (clean attribution); OR on DOT/063 (strong first-2yr, less confounded). This would give a definitive W-DECAY/R-CONV read.
2. **GATE-INV** (the 3rd machinery axis) — cross-regime sign-invariance feature-admission gate (your principle #3). Feature-admission, not a trade gate — different mechanism.
3. **Sharpen XRP** — the regime-conditional kill (suppress XRP's OFF regime), targeting the one confirmed recent-edge coin.
4. Another coin-mine (alternate).

NO multi-seed CONFIRMATION.

---

## Catalog

iter-v1/091 → `risk-primitive`/aggregation axis (R-CONV conviction gate τ=0.06; 2nd machinery axis of cycle-7) | tested on ETH/064 | **SPECIALIST-NEGATIVE (NO-EFFECT), BLOCKED-FAIL-FAST** — first-2.0yr IS weighted_pnl −5.84 / net −2.14% / Sharpe −0.70 (baseline ETH +0.2383); **F2 ENGAGED** (132 vs 198 trades, 33% cut) but F1 NEGATIVE = gate filtered but conviction noise-signature didn't transfer (LM: ETH OOS dropped-set +6.25% mirror-opposite of IS); much milder than W-DECAY's −27.9% | **KEY: fail-fast mis-calibrated for MACHINERY re-tests (gates absolute first-2yr-positive, conflates machinery-helps with seat-early-window-positive; ETH first-2yr weak at baseline) → machinery axes NOT cleanly refuted; re-test fail-fast-OFF vs-baseline or on strong-first-2yr seat** | ensemble_std split not reconstructable (decision_log no-op in backtest mode) | fail-fast 4th firing | lock intact (opt-in default-OFF, PRUNED 48) | BUNDLE-002 (`v0.v1-082`) UNCHANGED. Tag `v0.v1-091`.
