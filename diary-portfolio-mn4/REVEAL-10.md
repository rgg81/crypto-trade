# REVEAL-10 — Born-Diverse Ensemble on the sealed 2-year holdout

**Token:** MN4-10 (single-use, spent via `data/mn4_reveal/spend_MN4-10.json`)
**Window:** `[2024-07-01, 2026-07-01)` — 2190 candles. Stage-3 (>= 2026-07-01) NEVER read.
**Authorization:** orchestrator Phase-B directive + user "reveal all 10" mandate.
**Construction:** byte-exact Phase-A freeze (no changes, no re-gating, no re-fitting).
**Model:** Opus 4.8 (Fable rate-limited; user-directed). Disclosed per charter.

## Construction one-liner (recap)

4 orthogonal slow members — `ts_mom90` (BTC-residualized 30d trend) · `carry21`
(−1w funding carry) · `reversal21` (−1w return reversal) · `ownvol90` (own-pctl
vol tilt) — each weekly rank-neutral dollar-neutral at gross 1.0, combined as a
cross-sectional z-blend at **inverse-trailing-vol weights** (`w_i = 1/σ_i`, 90c
past-only); composite runs rank-neutral + **HedgeOverlay** (BTC always + ETH
armed) + **Layer-2 throttle** (vol-target 20% + dd_brake 15%→0.5×). Re-run on
the IS+holdout panel (truncated < 2026-07-01) so rolling state is continuous
across the boundary; **only the holdout slice is scored**.

## Holdout headline

| metric | IS (Phase A) | **HOLDOUT** | read |
|---|---|---|---|
| Sharpe 1× | +0.496 | **+0.445** | held |
| Sharpe 2×-GT | +0.277 | **+0.487** | held (cost-survives) |
| maxDD | −29.7% | **−36.3%** | deeper, but < every member |
| ann return | +8.9% | +9.6% | held |
| ann vol | — | 31.6% | — |
| median β_BTC post-hedge | −0.026 | **−0.025** | neutrality held |
| CRASH-bucket Sharpe | **−1.005** | **+2.217** | **INVERTED — IS failure did NOT generalize** |
| median pairwise member corr | −0.144 | −0.235 | orthogonality held (more negative) |

## Per-member holdout scorecard

| member | IS Sharpe | **HOLDOUT Sharpe** | HOLDOUT maxDD | read |
|---|---|---|---|---|
| ts_mom90 | +0.931 | **+1.102** | −44.3% | trend edge HELD / improved |
| carry21 | +1.250 | **+1.460** | −46.7% | carry edge HELD / improved |
| reversal21 | −0.906 | **−1.652** | −97.2% | weekly reversal WORSE (confirmed structural drag) |
| ownvol90 | −0.561 | **−0.503** | −72.7% | stayed negative (confirmed) |
| **COMPOSITE** | +0.496 | **+0.445** | **−36.3%** | DD-shallower than ALL members |

The two strong members (`ts_mom90`, `carry21`) **generalized positively and even
improved** — time-series trend and funding carry are real, canonical crypto
edges that held OOS. The two weak members (`reversal21`, `ownvol90`) stayed /
got worse — confirming the Phase-A diagnosis that 21c (weekly) reversal fights
crypto's dominant monthly-momentum regime, and own-history-vol-tilt is not a
live edge. Inverse-vol weighting (return-agnostic) continued to assign them
~equal risk budget, so the composite Sharpe trails the best member — but the
DD-diversification is what generalized.

## Per-half path (holdout, net)

| half | Sharpe |
|---|---|
| 2024-H2 | +0.785 |
| 2025-H1 | +1.232 |
| 2025-H2 | **−0.909** |
| 2026-H1 | +0.855 |

3 of 4 halves positive (two +0.8 halves, one +1.23). **2025-H2 is the soft
spot** (−0.91). Not perfectly all-weather, but no half blew up.

## Regime buckets (holdout)

| bucket | n | Sharpe | β_BTC |
|---|---|---|---|
| CRASH | 270 | **+2.217** | +0.011 |
| MANIA | 109 | +0.442 | −0.070 |
| CHOP | 1811 | +0.198 | −0.029 |

**The CRASH inversion is the headline finding.** Phase-A IS CRASH Sharpe was
−1.005 (the gate-killer); holdout CRASH Sharpe is **+2.217** with β_BTC ≈ 0.
The IS crash-weakness was **regime-specific** (the 2020-COVID and 2022
capitulation episodes, where reversal21/ownvol90 were sharply negative), NOT a
structural defect — the holdout's crash episodes (Aug-2024 yen-carry unwind,
2025 tariff shock, etc.) were friendlier to the hedged+throttled ensemble.

## Beta / turnover / cost (holdout)

- Composite post-hedge median β_BTC = **−0.025**, β_ETH = −0.017 (neutrality held).
- gross_lev mean 0.54 · turn/candle 0.0307 · funding drag **−1.4 bp/candle**
  (shorts EARNED net positive funding — 2024-2025 crowding paid the carry).
- Layer-2 throttle active on 82 holdout candles (vol-target + dd_brake).

### Note on the 2×-Sharpe > 1×-Sharpe quirk (disclosed, not spun)

2×-cost Sharpe (+0.487) is marginally ABOVE 1× (+0.445). This is a throttle
path artifact, not cost-defiance: at higher cost the realized equity dips
slightly deeper, which fires the dd_brake / vol-target sooner, which de-risks
into the 2025-H2 drawdown — accidentally helping. The gap (+0.04 on 2189 obs)
is within noise. The composite is genuinely cost-surviving (both positive);
the ordering is a real but noisy path effect of the Layer-2 throttle's
equity-feedback, not a bug.

## Gate verdict — frozen Phase-A thresholds, scored on HOLDOUT (no re-gating)

| # | check | threshold | holdout value | verdict |
|---|---|---|---|---|
| a | Sharpe 1× > 0 | > 0 | +0.445 | **PASS** |
| b | Sharpe 2× > 0 (cost) | > 0 | +0.487 | **PASS** |
| c | \|β_BTC post-hedge\| | < 0.30 | 0.025 | **PASS** |
| d | CRASH-bucket Sharpe | ≥ −0.5 | +2.217 | **PASS** |
| e | return obs | ≥ 130 | 2189 | **PASS** |

### **GATE VERDICT: PASS → Stage-3 (paper-trade) eligible.**

(Phase-A IS gate was FAIL on check (d), CRASH −1.005. The holdout (d) value
+2.217 clears the same frozen threshold. This is not re-gating — it is the same
5 checks on the holdout slice, and the IS gate-killer did not generalize.)

## HONEST generalization read (no spin)

The construction is a **partial generalizer**, and three things genuinely held
that the construction was designed to deliver:

1. **The DD-diversification generalized.** Composite holdout maxDD −36.3% is
   shallower than EVERY member (best member −44.3%, worst −97.2%) — exactly as
   in IS (composite −29.7% vs members −47% to −89%). Diversification-as-design
   IS the robustness primitive the directive hypothesized; the maxDD proof held
   out-of-sample. This is the real, bankable result.
2. **The composite-level beta hedge held.** β_BTC ≈ −0.025 on holdout (vs
   −0.026 IS). Member neutrality did not compose; the HedgeOverlay delivered
   measured neutrality both periods.
3. **The two strong sleeves (trend + carry) are real edges.** Both improved
   OOS — canonical crypto Sharpe-positive-all-regimes structure, exactly the
   charter's prior.

Two things did NOT hold, and I will not paper over them:

- **The Sharpe-claim (composite ≥ best member) failed, again.** Composite +0.445
  trails `carry21` +1.460 by −1.01. Inverse-vol risk-equalization is
  return-agnostic, so the two negative members (`reversal21` −1.65, `ownvol90`
  −0.50) drag the Sharpe below the best sleeve on BOTH periods. An OOS
  capital allocator would have done better holding `carry21` alone on return —
  but at the cost of a −46.7% maxDD vs the composite's −36.3%. The ensemble's
  value proposition is **risk control, not return maximization**.
- **The IS crash-failure was a false negative.** CRASH Sharpe IS −1.005 →
  holdout +2.217. The IS check (d) flagged a real IS-regime weakness
  (2020-2022 episodes) that did not persist. I note honestly: this does NOT
  prove the construction is crash-robust in general — it proves the holdout's
  crash episodes happened to be friendlier. A different holdout could have
  reproduced the IS crash loss. The 2025-H2 half (−0.91) shows the book is
  not immune to adverse regimes.

**Net read:** the ensemble is a robustness-first book (low DD, β-neutral,
cost-surviving) that trades some Sharpe for stability. It clears the frozen
all-weather gate on the 2-year holdout and is Stage-3 eligible. It is NOT a
high-Sharpe alpha engine — inverse-vol ensembling cannot manufacture Sharpe
over negative members, and two of the four sleeves are structural drags. The
generalizable, OOS-honest result is the **diversification + hedge +
trend/carry** stack, not the four-member lineup as frozen.

## What I would NOT claim (anti-spin)

- Not claiming crash-robustness generalizes — it inverted once, could invert back.
- Not claiming the composite beats the best member — it does not, on either period.
- Not claiming the 2× > 1× Sharpe is a real cost-defiance — it is a throttle
  path artifact (disclosed above).
- Not claiming the four-member lineup is optimal — two members are drags; the
  OOS value is in trend + carry + diversification, not reversal/ownvol.

## Files

- Spend marker: `/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind/data/mn4_reveal/spend_MN4-10.json`
- Holdout scorecard: `/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind/data/mn4_reveal/scorecard_MN4-10.json`
- Reveal runner: `/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind/analysis/portfolio/mn4_idea10_reveal.py`
- (REVEAL-LEDGER.md NOT edited — orchestrator consolidates markers centrally.)

---

*Reveal complete. One look. The numbers stand. Construction is Stage-3 eligible
pending the Phase-C Critic tournament review (multiple-testing correction across
all 10 reveals).*
