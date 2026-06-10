# iter-v1/085 — Phase 8 Diary (UNIUSDT SPECIALIST)

**Date**: 2026-06-10
**Track**: v1 (refactored)
**Branch**: `iteration-v1/085`
**TYPE**: SPECIALIST — single-coin cohort `("UNIUSDT",)`; fresh-alt MINE; FIRST under the REFINED structure-gate (GATE 1 + GATE 2) AND first NEW-feature-engineering set (4-feature mean-reversion stack, intended as the start of a 4→10 grind).
**Cycle**: 7, fresh-alt mining
**Author**: QR (autopilot)
**Tag**: `v0.v1-085`

---

## Headline

**SPECIALIST-NEGATIVE — triple-falsified (F2-PRIMARY INERT + F3 probe-flat + F4 momentum-dominated). IS Sharpe −0.7005 / OOS +0.1739. The GATE-2 reform is now EMPIRICALLY VALIDATED on its second consecutive correct prediction (CRV/084 + UNI/085).**

UNI was picked as honestly GATE-2-WEAK: it cleared GATE 1 with the most-negative trivial baseline in the eligible pool (−0.2485) and carried the pool's strongest autocorrelation kernel (lag-3 = −0.0843), but FAILED the GATE-2 PRIMARY probe (48-col LightGBM IS Sharpe −0.243) and SECONDARY (max feature-label IC 0.0393). The /085 bet — pre-registered as a downside-tilted gamble — was that 4 NEW UNI-specific reversal features would supply the lag-3 + vol-state coordinates the 48-col stack was blind to. **They did not.** The realized 52-col specialist landed Δ−0.46 BELOW the probe — the NEW features WORSENED IS, exactly the inert-features-amplify-noise-at-higher-budget mechanism.

This is the IDEAL adversarial outcome: the pre-registered hypothesis was tested cleanly (no scope creep, no leak, faithful implementation per Critic Check 8, global PRUNED held at 48) and DECISIVELY FALSIFIED. The negative is structurally robust — all 50 inner seeds converged (cross_seed_sharpe_std = 0.000), so this is NOT a basin-lottery artifact.

---

## Results

| Metric | IS | OOS |
|---|---:|---:|
| Sharpe (monthly) | **−0.7005** | +0.1739 |
| Trades | 168 | 84 |
| Win rate | 38.1% | 40.5% |
| Profit factor | 0.81 | 1.05 |
| Max drawdown | 91.36% | 21.42% |
| DSR (N_eff-corrected) | +0.0936 | +0.591 |
| PSR (monthly vs 0) | 0.0003 | 0.5619 |
| OOS/IS Sharpe ratio | — | −0.2482 |

48-col GATE-2 probe (pre-registered floor): IS Sharpe **−0.243**.

---

## Falsifier outcomes — all THREE fired NEGATIVE

- **F2-PRIMARY FALSIFIED → NEGATIVE-INERT-FEATURE.** `rev_extension_z_3` (the load-bearing directional reversion feature; brief predicted rank 1–4) ranked **42/52**. `rev_vol_gate_signed` ranked 39/52. Both DIRECTIONAL features inert. F2-SUSPICION did NOT fire (capstone didn't dominate while primitive went quiet → clean signal-absence, not the /084 anti-signal pattern). The two VOL-STATE features bound (`vol_state_z_natr_30` rank 3, `rev_halflife_50` rank 9) but as REDUNDANCY with the incumbent vol stack (`vol_atr_14` rank 1, `vol_natr_14` rank 12) — not orthogonal directional gain.
- **F3 FALSIFIED → NEGATIVE-PROBE-FLAT.** IS −0.7005 did not exceed the −0.243 probe by ≥+0.25; it landed Δ−0.46 BELOW. 2nd confirmed case after CRV that the locked 48-col architecture cannot manufacture a structure-gate pass on a sub-probe coin.
- **F4 FALSIFIED → NEGATIVE-MOMENTUM-DOMINATED.** IS −0.7005 < 0 AND < trivial min-horizon −0.2485. Worse than not trading in-sample.

---

## Key findings

1. **The lag-3 kernel died via a LABELING-HORIZON MISMATCH (the load-bearing diagnosis, LM 7.4 + Critic concur).** A 3-bar sub-1% reversion completes INSIDE the 1.45×ATR stop distance, so the triple-barrier directional label never sees a distinct outcome. Corroborated: the inherited `interact_ret1_x_ret3` (closest lag-3 proxy) is ALSO near-dead (rank 49). No lag-3 encoding survives THIS label. **This is correlation ≠ causation made concrete: UNI's autocorr lag-3 = −0.0843 was real in raw returns but carried zero tradeable directional edge through the ATR-barrier label.**

2. **The −0.70 IS / 91% MaxDD magnitude is 94% driven by 2022-09** (−43.87% of the −46.63% IS total), where R5's vol-target cold-start ran 7/8 trades at full weight_factor (1.0) into UNI's listing-shock before the 45-day vol history accumulated. IS-ex-2022-09 ≈ −2.8%. The SIGNAL verdict is "structureless coin-flip" (15/15 IS month split); the catastrophic MAGNITUDE is an R5 cold-start amplifier, not over-attributed to the features.

3. **The +0.17 OOS is noise, not edge** (Critic Check 8): DSR_corrected 0.591 (59% prob > 0), PSR 0.56 (≈coin-flip), 7-pos/9-neg OOS months carried by a few large positives. Both merge floors (IS>1.0 AND OOS>1.0) fail massively. Cannot be cited as regime-specialism.

4. **GATE-2 reform empirically VALIDATED.** GATE 2 said reject UNI (probe −0.243); the full 6.6h backtest confirms feature-engineering could NOT rescue it. CRV + UNI = two consecutive correct GATE-2-WEAK → NEGATIVE predictions. Zero v1 wins (DOT +1.32, ETH, BTC, AAVE) ever came from rescuing a probe-reject — all cleared structure on the STOCK label-probe.

---

## Decision: SPECIALIST-NEGATIVE — NO MERGE

**Verdict** (Phase 7.5 Critic review, commit `8d7171be`): `SPECIALIST-NEGATIVE`, triple-falsified (NEGATIVE-INERT-FEATURE + NEGATIVE-PROBE-FLAT + NEGATIVE-MOMENTUM-DOMINATED).

- UNI DROPPED from the bundle candidate roster.
- The 4 features are NOT carried forward (directional pair INERT-and-harmful; vol-state pair redundant).
- **BUNDLE-002 (`v0.v1-082`; DOT+ETH+BTC+AAVE; IS +0.72 / OOS +1.00) UNCHANGED.** No BUNDLE-003.

---

## Methodological reform: GATE-2 probe is now a HARD REJECT

The big lesson (LM 7.4 Rec 5a + Critic Rec 1): the GATE-2 PRIMARY probe (≥ +0.30 IS Sharpe on the REAL label) becomes a **HARD REJECT**, not a soft "feature-engineering can flip it" flag. The "manufacture a pass via features on a probe-reject coin" hypothesis is now FALSIFIED twice (CRV /084, UNI /085) with zero precedent wins. Future fresh-alt mines must clear GATE-2 PRIMARY on the stock label-probe BEFORE a specialist brief is authored — no more 6.6h craters on coins the probe already rejected. Codified to `feedback_v1_negative_trivial_baseline_selector` memory.

---

## Next Iteration Ideas

The bottleneck has shifted from the SYMBOL to the LABEL + ARCHITECTURE. Per the Critic Path Forward + standing user directives (alternate coin-mining with machinery axes; no multi-seed confirmation):

1. **/086 — TRBUSDT bundle-diversification mine** (already screened, GATE 0 lowest bundle-correlation 0.548, GATE 1 trivial −0.179 pass). MUST run GATE-2 probe FIRST as a HARD REJECT before briefing. Do NOT carry the /085 features.
2. **Machinery axes (alternate)** — W-DECAY time-decay sample weighting, R-CONV ensemble-conviction trade gate, GATE-INV cross-regime sign-invariance feature gate. Bundle-wide, low-variance, no basin lottery.
3. **BNB + XRP universe expansion** (user 2026-06-10; override V1_EXCLUDED_SYMBOLS; XRP keeps cross-track v2 overlap — flag double-exposure at deploy/bundle).
4. **Labeling family (Critic Path-Forward #1)** — short-horizon fixed-bar reversion label, validated on an ALREADY-STRUCTURED coin (DOT/ETH) FIRST, to test whether UNI's lag-3 kernel is unreachable vs merely unreached by the ATR-barrier.
5. **R5 cold-start warmup-aware sizing primitive (Critic Path-Forward #2)** — cap weight_factor until ≥N days vol history; de-risks every future fresh-alt mine's early-IS magnitude.

---

## Catalog

iter-v1/085 → `per-cohort-specialization-UNI` | SPECIALIST-NEGATIVE | triple-falsified (INERT-FEATURE + PROBE-FLAT + MOMENTUM-DOMINATED) | IS −0.7005 / OOS +0.1739 | GATE-2 reform validated (2nd correct prediction) | non-roster.
