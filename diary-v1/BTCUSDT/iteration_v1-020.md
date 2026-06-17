# Diary — iter-v1/020 (BTCUSDT) — CONFIRMATION (K=20) — NO-MERGE (Critic gate) — but the lottery is SOLVED

**Axis:** K=20 confirmation of the iter-019 conviction-gate both-positive (config bit-identical: iter-016
stack + trend-state direction + trend-strength gate q=0.40).

**Result:** IS Sharpe **+0.3656** / OOS **+0.0944** — BOTH POSITIVE, and it HELD at K=20 (iter-019 K=5
was +0.54/+0.06 → consistent, NOT a collapse). IS net +47.7%, OOS net +13.7%, OOS maxDD 4.12%. 73/38
trades. 20/20 seeds.

**Verdict: CONFIRMATION-NO-MERGE (Critic, results-only review).**

### Two REAL wins (record these — the mechanism is not discarded)
- **The seed-lottery is SOLVED.** Unlike iter-016 (K=5 +0.11 → K=20 −1.15 collapse), iter-020's OOS
  HELD K=5→K=20 (+0.06 → +0.09). The conviction GATE + deterministic trend-state direction stabilized
  the seed dispersion that destroyed iter-016/017. Genuine methodological win.
- **IS improved materially + honestly:** −0.28 (baseline) → +0.37. The conviction-gate stack has a real
  IN-SAMPLE edge.

### Why NO-MERGE (Critic, load-bearing)
1. **The OOS +0.09 is concentration noise, not a generalizing edge.** Two single-trade timeout-short
   months (2025-11 +2.67, 2026-02 +3.63) supply ~+6.3 of the +13.7 OOS net; the other 36 trades net
   ~flat-to-negative. PSR 0.18, PF 1.05 — no edge signature. +0.09 Sharpe on 2-of-38 trades ≈ zero.
   (iter-019's diary pre-diagnosed this: "FLAT, knob-sensitive noise.")
2. **It does NOT beat the baseline's OOS** (+0.64 → +0.09 = −85%). Merging would replace a +0.64-OOS
   baseline with a +0.09-OOS one.
3. Costs/look-ahead/IS-OOS-split all verified clean (Critic Checks PASS). Not a methodology failure —
   a genuine no-edge-in-OOS finding.

### THE GATE AMBIGUITY (load-bearing, for the user — flagged by the Critic)
The merge gate I've been optimizing against is AMBIGUOUS:
- **User verbal directive (iter-002, codified in memory):** "both positives still better than the
  baseline; ratio IS/OOS proves generalization" → COHERENCE gate (both-positive beats inversion).
- **`BASELINE_V1_BTCUSDT.md` line 51-52 (bootstrap text I wrote):** "MERGES iff OOS improves net of
  costs, no material IS regression" → OOS-IMPROVES gate (beat +0.64).
These give OPPOSITE verdicts on a both-positive-but-lower-OOS candidate. iter-020 is NO-MERGE under
BOTH (the concentration finding kills it under coherence too), so the verdict is robust — but the gate
text MUST be reconciled before the next CONFIRMATION, because it sets the campaign's target.

### The fundamental finding (thoroughly evidenced, iter-005→020)
BTC's IS-stable directional edge is **LONG** (iter-018 QR: IS long leg +0.98, short leg −0.58). That
LONG edge does NOT generalize to the 2025-26 OOS regime (a correction/chop). Every lever — features,
horizon, direction source, conviction gate, risk/sizing — confirms: strong IS, OOS-flat-to-negative.
The conviction gate got OOS to FLAT (best yet) but not to a robust positive. **NOTE:** the Critic's
"short-only" Path Forward is an OOS-CURVE-FIT (OOS-shorts-won is a correction artifact; the IS short
leg LOSES) — rejected per OOS-vigilance.

**Next (surfaced to user — genuine fork):**
1. **Resolve the gate** (coherence vs OOS-improves) — sets the target. Genuinely the user's call.
2. **Strategic direction:** the directional approach is thoroughly mapped (strong IS, OOS doesn't
   generalize). Real untried path = the FE's **non-directional / volatility-MAGNITUDE target**
   (iter-014: |move| signal is sub-period-STABLE, unlike direction) — a bigger architecture change.
   OR a crypto-native exogenous regime feature (funding/realized-vol) to make the OOS edge robust.
   Both benefit from user sanction (the user pushed back on premature pivots before).
3. Baseline UNCHANGED (iter-001 stays). Conviction-gate mechanism + lottery-solved finding retained.
