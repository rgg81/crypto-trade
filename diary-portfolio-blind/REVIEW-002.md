# REVIEW-002 — Critic Integrity Audit of EXPLORATION-002 (mid-vol-decile tail-capped L/S)

**Reviewer:** Quant Critic (read-only). **Date:** 2026-07-09.
**Scope:** Result INTEGRITY only — specifically: **is the +0.09 Sharpe / 138x turnover REAL or
ARTIFACT?** The QR owns the MERGE verdict (G1–G7). (Persisted by orchestrator — Critic cannot write.)

## OVERALL INTEGRITY VERDICT: CONDITIONAL-PASS

Headline numbers (+0.09 Sharpe, −48.5% MaxDD, 138x turnover, −240bps 2021 net funding income,
+0.51/+0.45/−0.14 parity) are **trustworthy in direction and approximate magnitude**. No sign-flip,
no double-counting, no look-ahead leak on the new path. The +0.09 is REAL — the genuine output of a
correctly-wired near-neutral L/S book — but it is **DEPRESSED ~0.1–0.2 Sharpe by structurally
elevated turnover (138x vs long-only's 73x), partly boundary-jitter at the two new partition
thresholds**. The strategic conclusion ("low-vol is defensive-not-alpha; near-neutral book ~0
Sharpe; tension is return-alpha") is qualitatively correct, but +0.09 should be read as
"cost-inefficient near-neutral book," NOT "the pure information ratio of the low-vol factor."

## THE CRITICAL FINDING — Is +0.09 REAL or ARTIFACT?
**Verdict: REAL but cost-depressed; ~30–50% of the gap-to-long-only is plausibly recoverable via
turnover reduction; the rest is genuine spread compression.**

**(1) Sign/mechanics correct (direct code trace).** `target_weights_midvol_short` for n=20:
k_long=10, k_short=5; long_threshold=10 (r≥10→LONG, +0.05 ea), short_threshold=5 (5≤r<10→SHORT,
−0.10 ea), r<5→SKIP. sum(w)=0, sum|w|=1.0. Funding attribution sign: long(w>0)×pos→drag,
short(w<0)×pos→income; 2021 long +1899bps paid, short −2140bps received → net −240bps income.
Sign-correct for dollar-neutral in mania. Not double-counted. Short-leg 2021 price P&L −1.01 (lost
in bull) and 2022 +0.93 (profited in bear) — signs alternate correctly across regimes. ✓

**(2) Turnover is structurally elevated, not purely jitter.** Long-only 73x → midvol 138x (1.89×).
Two structural factors: (a) per-name weight delta 3× larger on band rotations (long→short moves
0.15 vs long→skip 0.05); (b) TWO boundaries churn (long↔short AND short↔skip) vs one — the mid-band
(ranks 5–9) is where realized-vol ranks cluster, so small σ changes flip order. Partly recoverable
via hysteresis; partly genuine cross-sectional rotation at higher per-rotation cost.

**(3) Decomposition: spread is genuinely near-zero net-of-cost.** Long leg at gross=0.5 ≈ half of
long-only (~+0.4–0.5 isolated). Short leg adds 2022 dampening (+0.93) + 2021 funding income
(−2140bps) but also bull-market losses (2021/23/24) + ~50bps/yr extra cost vs long-only. Net ≈ +0.09.
**The low Sharpe is BOTH genuine spread compression (IC +0.052 is real but small) AND cost-inefficient
construction (138x).** Neither alone fully explains it.

**Net strategic read:** synthesis correct in direction. MaxDD −87%→−48.5% and funding dodge
(+3722bps→−240bps in 2021) are real verified defensive properties. Absence of return alpha is real.
Exact +0.09 is pessimistic by ~0.1–0.2 Sharpe from turnover inefficiency; a hysteresis-corrected
variant would still be well below the brief's +0.7–1.2 prediction. **The QR should not interpret
+0.09 as a precise estimate of the factor's IR — it's an upper bound on the construction's cost.**

## Per-Area Findings (ranked)

### [S1 — MEDIUM] Turnover interpretation ambiguity: 138x is structural + jitter
Number correct; interpretation ("pure rotation" vs "boundary jitter") unresolved without rank
instrumentation. **EXPLORATION-003 must isolate the two** via a turnover-reduction axis (hysteresis /
eligibility-exit buffer / signal-proportional). If Sharpe lifts to +0.3–0.4, turnover was the drag;
if it stays ~+0.1, the spread is genuinely near-zero.

### [S2 — MEDIUM/LOW] Short-leg price-P&L docstring sign-convention INVERTED vs code
`_leg_price_pnl_by_year` (`blind_exploration_002.py` ~line 85–115): `leg = (w*nxt)*(w<0)`. For w<0,
price-up → leg NEGATIVE → in CODE, negative = shorts lost money. The report's stated convention is
the OPPOSITE ("+ = shorts lost"). **Table values are correct (match code); docstring text is wrong.**
Risk: a downstream reader inverts the table and designs EXPLORATION-003 on a wrong premise (thinks
shorts profited in 2021). **Fix (option a, safer): flip the docstring to match the code —
"− = shorts lost (prices rose), + = shorts profited (prices fell)."** One-line text fix.

### [S3 — LOW/MEDIUM] LITUSDT short-side funding residual: 3.92bps upper bound, conservative direction
Carried from EXPLORATION-001. For a SHORT in positive-funding mania, the silent zero is a small
POSITIVE bias on reported short P&L (we did NOT credit income the short would've received) →
conservative; real short book performed marginally BETTER than reported. Immaterial. Not blocking.

### [S4 — LOW] Warmup-edge max|w|>20% at k<63 — same lookback-ramp artifact as REVIEW-001 S4; masked out of metrics. Not a bug.
### [S5 — LOW] Dollar-neutrality single-candle max|sum(w)|=0.25 — engine force-exit branch (shared with other modes); synthetic-panel test confirms strict sum(w)=0 when all fills valid. Not a bug.
### [S6 — LOW] 2025Q1 Sharpe +3.18 — small-sample (~18 rebal steps); don't cite as stable.
### [S7 — LOW] 2025 funding-by-leg both-positive — small-sample 12-week tail artifact; not material to G7 (2021-only).

## Leak-Safety Verdict (mandatory positive-control)
The 4 new midvol tests are MEANINGFUL (not tautologies):
1. `test_future_corruption_leaves_past_identical_midvol` — corrupts signal+open forward; asserts past bit-identical. ✓
2. `test_midvol_dollar_neutrality_and_gross` — sum(w)=0, sum|w|=gross, longs>0, shorts<0 at every n≥4 rebal. ✓
3. `test_target_weights_midvol_short_partition` — hand-computed 8-name row; verifies exact 3-way partition + tie slack. ✓
4. **`test_midvol_short_skips_extreme_tail` — LOAD-BEARING, correctly constructed.** Signal
   `[-100,1,2,3,4,5,6,7]`: −100 = simulated 100× mooner (lowest signal = highest vol); asserts w[0]==0.0
   (skipped, not shorted). For n=8: long_threshold=4, short_threshold=2, r=0<2→SKIP. ✓ Tests what the
   brief claims. **No future-data path in the new builder** (reads only sig[k-1]/univ[k-1]).

SHIB fix verified landed (`_FUNDING_SYMBOL_MAP` SHIBUSDT→1000SHIBUSDT + 7 others; coverage asserted
at run-script line 211, strict=False proceeds on frozen universe but logs LITUSDT loudly). ✓

## Cost Realism & Apples-to-Apples
Taker 5bps+slip 2.5bps fair. **2×-cost stress (run 6: −0.29) is the strongest evidence turnover is
partly the culprit** (S1): 138x×15bps≈207bps/yr vs long-only 73x×7.5bps≈55bps/yr → 152bps/yr cost
differential drags Sharpe. EW/long-only/rank_neutral parity OK (delta ≤0.04). ✓

## Pre-Registration / No-Tuning
Brief FROZEN. long_frac=0.5/short_frac=0.25 are parameter-free midpoints chosen without hindsight.
No vol-band scanned. Predictions were largely WRONG (+0.7–1.2 predicted vs +0.09; 75–100x vs 138x)
but PRE-REGISTERED, so the miss is informative, not suspicious. ✓

## Stats
+0.09 is ~1.5σ from zero (effective SE≈0.05–0.08 from overlap) — not strongly distinguishable from
zero, but sign/magnitude trustworthy via the verified leg decomposition. Per-year direction solid
(~160 rebal/yr); 2025Q1 under-powered.

## Survivorship / Selection
PIT top-20 trailing $-volume, re-ranked — past-only, leak-safe. Adverse-selected (pump→enter→dump);
mid-vol short band sits in the adverse-selection zone — real economic headwind, not a leak. SHIB
resolved; LITUSDT residual single-digit bps, conservative.

## Path Forward for EXPLORATION-003 (constructive)
Synthesis correct: low-vol is DEFENSIVE (MaxDD −87%→−48.5%, funding dodge +3962bps in 2021) but NOT
return-alpha (+0.052 IC too small net-of-cost). Attack return-alpha while preserving defensive props:
1. **[HIGHEST] Multi-factor blend with `rev_3`** [feature-family] — IC +0.045 at corr −0.006 to vol_low.
   Only axis adding a NEW alpha source. Combined-book Sharpe ≈ √(S_vol²+S_rev²); could be much higher if
   rev_3 carries real return-alpha (low corr → different economic force: mean-reversion vs defensive).
   Keeps the mid-vol L/S shell → defensive props preserved; only the signal blend changes.
2. **[HIGH, orthogonal] Turnover-reduction / hysteresis** [risk-primitive] — addresses S1 directly;
   ~+0.1–0.2 Sharpe. Band hysteresis (name must move ≥1.5 ranks past threshold to switch) or
   eligibility-exit buffer (stay until ≥2 ranks out). Parameter-free-ish (1-rank discretization).
3. **[MEDIUM] Mild net-long bias (0.7 long / 0.3 short)** — partial dodge + bull upside; honest middle
   ground between EXPLORATION-001 (+0.51/−87%) and EXPLORATION-002 (+0.09/−48.5%).
4. **[LOWER] Signal-proportional weighting** (REVIEW-001 #2) — best combined with #1 or #2.
**Recommended:** #1 (rev_3 blend) as the single higher-impact change; #2 (hysteresis) as EXPLORATION-004
— or combine #1+#2 if one-change discipline permits a stack.
**Prerequisites:** (a) verify rev_3 has a leak-safe loader; (b) fix S2 docstring before next report
read at face value.
