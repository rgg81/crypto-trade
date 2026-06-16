# Diary — iter-v1/008 (BTCUSDT) — AXIS PIVOT (research-only, no backtest) — ESCALATE → OVERRIDDEN

> **2026-06-16 USER OVERRIDE — escalation REJECTED, stay on BTC.** The user overrode the symbol-pivot
> recommendation below. Verbatim: *"you can emulate other frequencies by expanding the timeout and
> using higher frequencies for the features. we want Sharpe not absolute return. doesn't matter to
> have less return than buy and hold, the key is sharpe. you ran only a few runs and already give up.
> no. we will stay on this symbol. the agents must understand we are handling crypto so their nature
> is different than normal equity."*
>
> **What this corrects in the analysis below:** the regime forensic dismissed every BTC regime as
> "beta, not alpha" because always-LONG out-RETURNED the model — but the objective is **SHARPE, not
> absolute return / not beating buy-and-hold**. always-LONG has brutal crypto drawdowns and poor
> Sharpe; the model taking less return with controlled drawdown can have a HIGHER Sharpe = the win.
> The forensic used the wrong yardstick. The agents also reasoned equity-brained ("BTC too efficient
> for directional edge") — crypto is different (retail flow, funding, trend persistence,
> microstructure). Recorded as durable rules: [[feedback_v1_sharpe_not_buyhold]],
> [[feedback_crypto_native_not_equity]]; QR/FE/RE/Critic agent defs updated with a CRYPTO-NATIVE &
> SHARPE-FIRST framing block.
>
> **New mandated axis (iter-009):** STAY ON BTC. Emulate a different trading frequency *within* the
> 8h sacred constant by (a) **expanding the label timeout** (longer hold horizon) and (b) using
> **higher-frequency (short-window) features**. Re-examine the "positive-econ" regimes (VOL-high,
> TREND-up, ADX≥25) through a **Sharpe** lens — they may be tradeable gates after all. The IS-only
> label/regime analysis below remains valid evidence; only its absolute-return verdict is overruled.


**Axis:** the two untouched non-feature levers, analyzed IS-only by the QR after the
orthogonal-feature axis closed at iter-007: (1) label horizon/mode learnability, (2)
regime-conditional IS edge. No backtest run — this is a Phase 1/2 research iteration whose output
is a strategic recommendation.

**Outcome: ESCALATE — pivot the first v1 symbol off BTCUSDT.** Three independent IS-only axes now
converge on one root cause.

### Evidence (IS-only, purged/embargoed CV, 41-col prune; OOS never read — scripts verified
strict `open_time < OOS_CUTOFF_MS` + leak-guard assert)

**(1) Label-horizon learnability** — no label config lifts BTC off the noise floor:
| label config | OOF dir_acc | OOF econ %/cand |
|---|---|---|
| triple_barrier ATR 2.9/1.45 7d (CURRENT) | 0.4886 | −0.2398 (loses net of fee) |
| best alt: trend_scanning(5,8,13,21) | 0.5116 | +0.0460 (fraction of a fee, noise) |
| fixed_horizon N21 / tb 4.0/2.0 14d | ≈0.50–0.51 | ≈+0.01–0.03 (negligible) |

Oracle (perfect-direction) label ceilings are healthy (+4–7%/candle) but the model captures ≈0 of
them — a feature-SIGNAL problem relabeling cannot fix.

**(2) Regime-conditional edge** — every "positive" regime is BTC long-drift, not learned alpha:
| bucket | model dir_acc | model econ | always-LONG econ | verdict |
|---|---|---|---|---|
| ungated | 0.434 | −0.103 | +0.216 | model anti-directional |
| VOL high | 0.487 | +0.180 | +0.426 | beta, not alpha |
| TREND100 up | 0.465 | +0.154 | +0.457 | beta, not alpha |
| ADX ≥ 25 | 0.442 | +0.066 | +0.404 | beta, not alpha |

always-LONG beats the model 2–3× in EVERY bucket; model OOF dir_acc < 0.5 everywhere. A regime gate
would only reproduce the iter-001/004/005 inverted beta-drift artifact the merge gate is written to
reject.

### Why ESCALATE (not a manufactured pick)
The decisive number: **the prune model's out-of-fold directional accuracy is below 0.5 across the
entire IS window** — negative directional information content on BTC 8h. You cannot relabel or gate
your way out of a predictor anti-correlated with the target. Three axes — feature (iter-006), label
(§1), regime (§2) — independently confirm BTC's 8h directional signal with this architecture is a
predictable null. BTC is the most efficient, most-arbitraged crypto — a weak prior for an 8h
directional specialist. The QR deliberately declined to screen the least-bad label or highest-econ
regime; the IS-only purged-CV evidence already resolves both as predictable nulls.

### Cumulative BTC record (iter-001 → 008)
- /001 baseline: IS −0.28 / OOS +0.64 (inverted bootstrap)
- /002 prune+R2: NEG (R2 = OOS killer) · /003 K=3 prune: +0.17 IS (lottery) · /004 K=20 prune: IS −0.17 / OOS +0.48 (inverted)
- /005 funding spread: NEG · /006 funding level: NEG · /007 OI: NEG → orthogonal axis CLOSED
- /008 label + regime: NEG → **non-feature levers exhausted; ESCALATE**

### Recommendation (QR, pre-registered)
Pivot the FIRST v1 symbol off BTCUSDT to a less-efficient / higher-retail-flow asset. Pre-screen
candidates with the same 3-script IS-only triplet, ranked by ungated OOF dir_acc AND the
model-vs-always-LONG alpha gap; pick the symbol whose model has dir_acc clearly > 0.50 AND beats
always-LONG (genuine alpha — the exact test BTC failed). Candidate pool (pending Engineer eligibility
vs V1_EXCLUDED_SYMBOLS): the original v1 cohort LTC / DOT / LINK + selected alts.

### Escalation to user
BTC was the user's explicitly-chosen FIRST symbol ("start with BTC, the main one"). A symbol pivot
changes the foundational subject of the v1 redesign, so this fork is surfaced to the user rather
than taken autonomously. Options presented: (A) run the IS-only symbol pre-screen and pivot to the
best-alpha symbol; (B) keep BTC but pivot to a more radical architecture (non-directional / vol
target, different bar interval); (C) other direction.

**Files:** `analysis/BTCUSDT/iteration_v1-008/{label_horizon_learnability,regime_conditional_edge,regime_edge_forensic}.py` (+ CSVs), `briefs-v1/BTCUSDT/iteration_v1-008/research_brief.md`. QR commit `6ec3d9e1`.
