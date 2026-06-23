# portfolio-iteration-v2 EXPLORATION-010 — short-term cross-sectional REVERSAL (NEGATIVE, OOS hidden)

**Type:** EXPLORATION (OOS HIDDEN — discipline: baseline DSR already moderate, don't burn more OOS). ONE
change: a short-horizon (1-2 day) cross-sectional reversal sleeve (SHORT recent winners / LONG losers),
the last literature lead (RESEARCH_notes #6). Code: `iter_v2_010_reversal.py`. **Verdict: NEGATIVE.**

## Results (IS + EARLY/LATE; OOS HIDDEN)
- baseline XS-mom ensemble: LATE +1.46, turn 0.157.
- **reversal standalone is catastrophically NEGATIVE:** K=1 IS −3.15 / LATE −4.19 / turn **1.21**;
  K=3 IS −2.28 / LATE −2.28 / turn 0.72; K=6 similar. 2×-taker far worse (K=1 LATE −6.15).
- corr(ensemble, reversal K=1) = −0.07 (slightly negative, as expected) — but reversal is so negative the
  combine LOSES: ens+revK3 w=0.2 LATE +1.16, w=0.35 LATE +0.49 (both < ensemble +1.46).

## Lesson (reinforces the baseline)
Rank-21-40 mid-caps are MOMENTUM-driven at EVERY horizon — short-horizon winners KEEP winning (no
short-term reversal), so the reversal sign is wrong AND its turnover (1.21 for K=1) is cost-catastrophic.
This is positive evidence FOR the XS-mom thesis: relative-strength persistence dominates the cohort. Both
opposite-class sleeves now fail — funding-fade (/009, carry-faded) and reversal (/010, momentum-dominated).
DEAD PATH: short-term cross-sectional reversal on rank 21-40.

## Standing baseline (unchanged)
XS-mom 5-way ensemble {42,63,84,126,168} rank-21-40 8h + risk layer (tv=0.006/ml=2.0): OOS +1.37 /
2×-taker +1.03 / OOS DD −16% / turn 0.157. The cohort's edge is momentum; reversal and carry both lose.
