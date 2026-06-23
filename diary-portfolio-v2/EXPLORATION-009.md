# portfolio-iteration-v2 EXPLORATION-009 — cross-sectional FUNDING carry sleeve (NEGATIVE)

**Type:** EXPLORATION (improvement attempt; OOS shown). ONE change: add an orthogonal cross-sectional
funding-fade sleeve (short crowded-high-funding / long low) to the XS-mom ensemble baseline. User
insight: mid-caps carry richer funding. Code: `funding_v2.py`, `iter_v2_009_funding.py`.
**Verdict: NEGATIVE — carry is regime-faded on this cohort; combine is worse than the ensemble alone.**

## Results (rank 21-40, default slip; OOS shown)
- XS-mom ensemble baseline: IS +0.43, LATE +1.46, OOS **+1.37** [25 +1.61, 26 +0.84], turn 0.157.
- **funding standalone (FADE) is NEGATIVE at every M:** M=9 OOS −0.97, M=21 OOS −0.55, M=63 OOS −0.73,
  weekly OOS −1.16. The 2025 sub-window is strongly NEGATIVE (−1.35 to −1.67) — high-funding mid-caps
  KEPT RUNNING (crowding persisted, didn't revert), so the carry-fade is wrong-signed in the recent
  regime. (2026 flips positive M=21/63 +0.89/+1.10, but 2025 dominates.)
- **combine ensemble+funding is WORSE than ensemble-alone at every weight:** w=0.5 OOS +1.14 / LATE −0.07;
  w=0.3 OOS +1.26 / LATE +0.86; w=0.2 OOS +1.15 / LATE +1.08. All < ensemble OOS +1.37 / LATE +1.46.
- **Not even a hedge:** corr(ensemble net, funding net) = +0.07/+0.10/+0.15 (slightly POSITIVE) — a
  positive-corr negative-Sharpe sleeve can only drag the book down.

## Lesson
RESEARCH_notes #2 confirmed empirically: crypto carry Sharpe collapsed/reversed in 2024-26. On rank
21-40, the cross-sectional funding FADE loses because crowding PERSISTS (high-funding = recent winners
that keep winning — which is momentum, already captured by XS-mom, hence the +corr). A carry FADE is the
wrong sign in this regime; a carry-momentum direction would just duplicate XS-mom. DEAD PATH: cross-
sectional funding-fade sleeve on rank 21-40 (this regime). Deferred-permanently unless carry regime turns.

## Standing v2 baseline (unchanged by /009)
**XS-mom 5-way ensemble {42,63,84,126,168}, rank 21-40, 8h, + risk layer (tv=0.006, ml=2.0)** —
OOS +1.37 / 2×-taker +1.03 / OOS DD ~−16% / turn 0.157. /008 ensemble is the last accretive improvement;
/009 funding rejected. Next: close record items (R1 direct leak test, formal DSR) + write BASELINE_V2.
