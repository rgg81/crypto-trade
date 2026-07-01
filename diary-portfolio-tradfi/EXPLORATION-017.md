# EXPLORATION-017 — Short-window realized-vol brake on iter-016 (iter-017)

**Date:** 2026-07-01 · **Status:** **REJECT as a baseline promote** (OPTIONAL vol-overlay for QR).
Theory-pinned Barroso constant-vol de-lever at a FAST window, stacked on iter-016. ONE change, ZERO
change to signals/weights. OOS UNTOUCHED (IS-only). **NOT a clean wash like iter-008 — see below.**

## Goal
iter-016's worst residual is **Oct-2018 −6.9%**: a fast-from-bull crash the 12m bear-gate lags (g=0)
AND the slow 63d portfolio vol-target reacts to too late. Forensic PROBE C proposed a realized-vol
brake here. **Prior evidence to overcome (iter-008):** a SAME-window (63d) vol overlay WASHES because
the book is ALREADY 63d vol-targeted. The ONLY way iter-017 earns its keep is if a SHORTER/FASTER
window (5–21d) catches fast spikes the 63d target is too slow for — tested honestly.

## The change (`iter_017_rvbrake.py`)
Outer de-lever on the iter-016 deployed net: `s[t] = clip(TARGET / rv_short[t−1], floor, 1)`,
`rv_short = net16.rolling(W).std().shift(1)` (book's OWN trailing short-window daily vol), de-lever
ONLY (cap 1). **PRE-REGISTERED cell:** W=**21d** (PROBE C's 1-month window; NOT the max-net window),
**TARGET = ct.TARGET_VOL** (15%/yr/√252 — the book's OWN vol target, a data-independent constant, ZERO
new fitted param), **floor = 0.50**. Swept W∈{5,10,21} × floor∈{0.4,0.5,0.6}; median-vol target
reported for robustness only.

## Short-window vol dispersion (the iter-008 wash test) — the fast window DOES have more spread
| W | median | p10 | p90 | max | (63d target 15.0%) |
|--|--|--|--|--|--|
| 5d | 12.1% | 5.5% | 22.5% | 90.3% | fast tails the 63d target smooths over |
| 10d | 13.1% | 7.4% | 20.7% | 63.5% | |
| 21d | 14.1% | 8.8% | 20.0% | 43.3% | |

So it is NOT just re-doing the 63d target (that was iter-008's failure). The brake fires **41%** of IS
days at W=21 (mean s=0.93, min 0.50).

## Sweep W × floor (TARGET=15%/yr) — net@1× / net@2× / gross / β / Oct18% / +yrs
| W | floor | net@1× | net@2× | gross | β | Oct-18 | +yrs |
|--|--|--|--|--|--|--|--|
| 5 | 0.50 | +0.776 | +0.632 | +0.919 | +0.126 | −6.06 | 13/16 |
| **10** | **0.50** | **+0.714** | +0.570 | +0.858 | +0.126 | −5.25 | 13/16 |
| **21** | **0.50** * | **+0.761** | +0.616 | +0.906 | +0.125 | −6.03 | 13/16 |

*(baseline iter-016 net@1× **+0.728**. `*` = pre-registered decision cell.)* **6/9 cells beat baseline
BUT the response is NON-MONOTONE in W: the middle window W=10 DIPS to +0.714, BELOW baseline.** The
max-net cell is the un-pre-registered W=5 (+0.776) — a max-net-fit temptation I did NOT take.
Median-target variant confirms the effect (W=21 → +0.774), so it isn't an artifact of the 15% target.

## Pre-registered cell W=21/floor=0.50 vs iter-016
| metric | iter-016 | iter-017 | Δ |
|--|--|--|--|
| net@1× (6bps) | +0.728 | **+0.761** | **+0.034** |
| net@2× (12bps) | +0.581 | +0.616 | +0.035 |
| gross (cost-off) | +0.874 | +0.906 | +0.032 |
| net-β (VIX-off) | +0.148 | **+0.125** | **−0.022** |
| +pos years | 13/16 | 13/16 | 0 |

Brake churn |Δs|/day = 0.0111 (an outer exposure scalar; NOT charged by the standard weight-book cost
model — a caveat for QR, though net@2× already shows cost-robustness).

## Oct-2018 + good-year cost (the whole point)
- **Oct-2018 month: −6.92% → −6.03% (+0.89pp).** 2018 year −6.9% → −5.7% (+1.2pp). Also helps 2020
  COVID (+3.3pp), 2023 (+2.6pp), 2017 (+1.2pp) — multiple events, not just Oct-2018.
- **goodΔμ = −0.08pp** (mean good-year return% change, excl 2010/2018/2019) with **0 good-year sign
  flips.** The good-year RETURNS are FLAT-to-slightly-negative: the brake trims the big-return years
  (2013 −2.1pp, 2014 −3.1pp, 2024 −2.9pp) and helps the recovery years, netting ≈0. **The +0.034
  Sharpe gain is therefore pure VOL-REDUCTION (denominator), NOT a new return edge (numerator).**

## Does OVERALL Sharpe improve or WASH (like iter-008)?
**It IMPROVES, it does NOT wash.** Overall net@1× +0.728 → +0.761 (+0.034), consistent across cost
levels (gross +0.032 / net@2× +0.035), and β DROPS −0.022 (reclaims iter-016's flagged near-ceiling
β headroom). This is a *cleaner* result than iter-008's flat 63d wash. **BUT** the lift is entirely
vol-reduction (goodΔμ ≈ 0 — no new edge), and the window response is **non-monotone** (W=10 below
baseline; max-net at the un-pinned W=5) — the two anti-overfit tells.

## KEEP gate (STACK on iter-016) — verdict per gate
net@1× > +0.728 ✓ (+0.761) · net@2× ≥ +0.50 ✓ (+0.616) · β ≤ 0.15 ✓ (+0.125, DROPS) · +yrs ≥ 13 ✓ ·
gross ≥ +0.80 ✓ (+0.906) · **NO good-year regression ✗ (goodΔμ −0.08pp)** · **robust plateau ✗
(6/9 but NON-MONOTONE; max-net at un-pinned W=5)** · identity ✓ · leak ✓.
**5 clean passes; the 2 fails are precisely the anti-overfit gates.**

## Safety
- **IDENTITY:** brake-off (TARGET=+inf → s≡1) → net17 == iter-016 net bit-for-bit. **PASS.**
- **LEAK:** future-bar corruption of close+ret_fwd after a cutoff leaves the pre-cut braked net
  bit-identical (rv_short=`.shift(1)` past-only; TARGET data-independent). **PASS.** In-script +
  2 pytest tests added (`test_iter017_brake_off_reproduces_iter016`,
  `test_iter017_rvbrake_future_bar_no_leak`).
- Suite green (89 tradfi tests). OOS never computed. `data/` untouched. ZERO new signal params.

## Verdict / handoff to QR
**REJECT as a mandatory baseline promote.** The pre-registered cell fails the two gates that exist to
catch exactly this failure mode: the Sharpe gain is vol-reduction with FLAT good-year returns (goodΔμ
−0.08pp, no new edge), and the plateau is non-monotone with the max-net at an un-pre-registered
shorter window. Promoting it would be adopting a vol-cut that happens to raise the ratio, not a real
edge — the overfit posture the brief warns against.

**HONEST nuance (do not overstate the reject):** unlike iter-008's clean wash, iter-017 genuinely
lifts overall net@1× (+0.034), drops β (−0.022, reclaiming iter-016's near-ceiling headroom), and
shrinks Oct-2018 (+0.89pp) plus 2020/2023. So it is a legitimate **OPTIONAL vol-reduction overlay**
QR may adopt IF the Sharpe-first / β-headroom / drawdown-control priorities outweigh the flat
good-year returns. It is NOT a knife-edge and NOT a pure re-do of the 63d target. If QR does adopt
it, freeze W=21/floor=0.50/TARGET=15%/yr (the theory-pin) — do NOT switch to the max-net W=5 — and
charge the |Δs| exposure churn in the live cost model.
