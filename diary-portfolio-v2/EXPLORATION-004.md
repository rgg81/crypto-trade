# portfolio-iteration-v2 EXPLORATION-004 — residual (BTC-beta) cross-sectional momentum (NEGATIVE)

**Type:** EXPLORATION (OOS hidden). ONE change: BTC-beta-neutralized cross-sectional momentum (the
literature's top OOS-survivor, RESEARCH_notes.md #1/#3) on rank 21–40, via run_book_from_signal.
**Verdict:** **NEGATIVE.** Residualization HURT vs raw XS-mom on this cohort. Falsifies the hypothesis
here. Code: `resmom_v2.py`, `iter_v2_004_resmom.py`.

## Results (IS + EARLY/LATE; OOS hidden; default slip)
- anchor (trend+carry): IS +1.53, EARLY +2.17, LATE +1.16, turn 0.297.
- RAW xs-mom L=84 (sibling): IS +0.43, EARLY +0.19, **LATE +1.36**, turn 0.185.
- resmom sweep (L×betaWin): L=42 NEGATIVE (LATE −0.4/−0.9); L=84 bw90 best → IS +0.29, EARLY −0.12,
  **LATE +0.64**, turn 0.183; L=126 LATE +0.59/+0.12.
- best resmom (L=84, bw90) cost: 2×taker LATE **−0.01**, 2×slip/pessimistic LATE +0.49.

## Gate read
- **G2 (ΔLATE ≥ +0.20): FAIL** — best resmom LATE +0.64 vs anchor +1.16 → **ΔLATE −0.52**.
- **Gbeat (residualization adds): FAIL** — resmom LATE +0.64 << raw XS-mom LATE +1.36. Residualizing
  against BTC made it WORSE, and it also dies at 2× taker.

## Why (lesson)
On a dollar-neutral within-band RANK, common BTC moves already largely cancel cross-sectionally, so the
"strip the market beta" benefit is mostly already present. The explicit rolling-beta subtraction then
just injects beta-estimation noise (mid-cap betas are unstable), degrading the rank. The literature's
residual-momentum edge (documented on spot/long-only equity-style baskets) does NOT transfer to an
already-cross-sectional dollar-neutral mid-cap perp rank. DEAD PATH: BTC-beta-residual XS-mom on rank
21–40.

## Standing finding across iter-001…004 (drives iter-005)
The era-complementarity is the robust signal: **TREND owns EARLY (+2.17), XS-mom owns LATE (+1.36)**,
temporally separated, and raw XS-mom is LOW turnover (0.185 < anchor 0.297) — so the cost worry was
about the fixed BLEND, not the standalone. Next: **iter-v2-005 regime / factor-momentum ROUTING** —
hold trend when trend is winning, rotate to XS-mom when trend fades. The untried vehicle for the one
real edge found.
