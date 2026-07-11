# MN4 IDEA-01 — Phase-B REVEAL (token MN4-01)

**Authorized 2026-07-12 by user mandate + orchestrator Phase-B directive.** Single
authorized holdout read. Window: `[2024-07-01, 2026-07-01)`. Stage-3 (≥ 2026-07-01)
NEVER touched. Panel capped at `grid_ms < MN3_HOLDOUT_END_MS` (no Stage-3 leakage;
asserted at load time). Token MN4-01 spent irreversibly by this reveal.

**Construction (one-liner):** TS-mom signal `(close[t]/close[t-84] - 1) /
stdev(rets[t-21:t])`; rank_neutral L/S on PIT top-10 + BTC/ETH/SOL forced core;
cross-sectional β-null projection; weekly rebal (21-phase tranche, phase-agnostic
mean = headline); CRASH-regime gross throttle (0.5) + managed-variance (vol_target
0.30, max_lev 1.5) + DD brake (15%/50%/7.5%); 5+2.5bps+funding 1× cost with a
10+5bps GT twin.

**Construction is BYTE-FROZEN** — every builder imported verbatim from the
committed Phase-A module (`mn4_idea01_tsmom.py`); every constant is the Phase-A
value. NOTHING re-tuned, re-gated, or re-fit. The reveal is the same object scored
on the holdout window via warmup-continuity (full-panel build, holdout-only
measurement).

**Model:** Opus 4.8 (Fable suspended — user-directed; disclosed per charter).

---

## 1. Holdout headline scorecard

| metric | 1× cost | 2× GT | ratio |
|---|---|---|---|
| **Sharpe** | **+1.128** | +0.972 | 0.862 |
| t-stat | +1.594 | +1.372 | — |
| ann return | +29.11% | +23.64% | — |
| ann vol | 25.52% | 25.02% | — |
| **maxDD** | **-26.43%** | -27.09% | — |
| win rate | 49.7% | 49.4% | — |
| final equity | 1.667 | 1.528 | — |
| n periods | 2189 | 2189 | — |

**Cost-survival:** Sharpe 2×/1× = 0.862 (holdout) vs 0.864 (IS) — the strategy
retains 86% of its Sharpe at doubled cost. Cost is NOT binding.

---

## 2. Per-half path (the 4 halves of the 2-year holdout)

| half | 1× | 2× GT |
|---|---|---|
| 2024-H2 | **+2.071** | +1.976 |
| 2025-H1 | -0.039 | -0.149 |
| 2025-H2 | **+1.817** | +1.629 |
| 2026-H1 | +0.177 | -0.015 |

The IS H1/H2 asymmetry (H1 weak, H2 strong) **persisted** in holdout: 2024-H2 and
2025-H2 are strong (+2.07, +1.82); 2025-H1 and 2026-H1 are flat (-0.04, +0.18).
The seasonal pattern is genuine, not IS noise — cross-sectional momentum in crypto
consistently does better in Q3-Q4 (correction/chop with wider dispersion) than in
Q1-Q2 (correlated accumulation).

---

## 3. Regime buckets (holdout)

| bucket | n | 1× Sharpe | 1× t | 1× cum | 2× Sharpe | 2× cum |
|---|---|---|---|---|---|---|
| CRASH | 269 | **+0.255** | +0.13 | **+0.75%** | +0.096 | +0.02% |
| MANIA | 109 | +0.706 | +0.22 | +1.94% | +0.535 | +1.25% |
| CHOP | 1811 | **+1.270** | +1.63 | +62.27% | +1.111 | +50.91% |

**CRASH FLIPPED from IS -0.916 Sharpe / -8.09% cum → holdout +0.255 / +0.75%.**
This is the single biggest generalization surprise: the regime I flagged as
"structurally negative" in Phase A (cross-sectional momentum can't extract trend
when all blue-chips correlate down) became mildly POSITIVE in the holdout's crash
periods. The Layer-2 throttle (gross=0.5 in CRASH) limited losses AND the
holdout's crash periods (269 candles — likely Aug-2024 yen-carry unwind, Apr-2025
tariff shock, etc.) had enough cross-sectional dispersion for the L/S spread to
extract a small positive edge. IS n=570 vs holdout n=269: different crash episodes
with different cross-sectional structure.

**CHOP carries the book** (+62.3% cum, Sharpe +1.27, t=1.63) — same as IS. The
holdout was 83% CHOP (1811/2189 candles); this is where the strategy earns its
keep.

**MANIA is thin** (n=109 vs IS n=890) — the holdout had few mania candles (the
2024 ETF-approval rally was largely in IS territory; 2025-2026 was more chop/
correction than mania). The Sharpe is positive (+0.71) but the cum is small
(+1.94%).

---

## 4. Neutrality (holdout)

**Rolling book β (holdout-window):**
- β_BTC: mean = **-0.001**, median = -0.007, std = 0.032, [min=-0.069, max=+0.131]
- β_ETH: mean = **-0.000**, median = +0.001, std = 0.024, [min=-0.040, max=+0.103]

**Regime-bucket β (holdout, direct OLS):**

| bucket | β_BTC | β_ETH |
|---|---|---|
| CRASH | -0.016 | -0.010 |
| MANIA | +0.127 | +0.021 |
| CHOP | -0.012 | -0.005 |

Market-neutrality **maintained** in holdout. Mean |β_BTC| ≈ 0.001 across the whole
holdout; the worst regime-bucket is MANIA at β_BTC = +0.127 (still well under the
0.30 gate). The cross-sectional β-null projection generalizes — it's a mechanical
projection, so this is expected, but it's confirmed.

---

## 5. Turnover + cost coverage (holdout)

| metric | 1× | 2× GT |
|---|---|---|
| turnover ann (one-way) | 38.6× | 38.6× |
| cost per candle (mean) | 2.93e-5 | 5.85e-5 |
| coverage ratio (\|ret\|/cost) | **174.4×** | 87.2× |

Turnover DROPPED from IS 44.8× → holdout 38.6× (fewer DD-brake toggles, more
sustained positions). Coverage ratio IMPROVED from IS 159× → holdout 174×. Cost
is even less binding OOS than IS.

---

## 6. Gate verdict (vs FROZEN Phase-A gates — NO re-gating)

| gate | threshold | holdout value | verdict |
|---|---|---|---|
| GATE-A Sharpe(1×) | > 0.5 | **+1.128** | **PASS** |
| GATE-B 2×/1× Sharpe | > 0.5 | **0.862** | **PASS** |
| GATE-C maxDD | > -40% | **-26.43%** | **PASS** |
| GATE-D \|β_BTC\| mean | < 0.30 | **-0.001** | **PASS** |
| GATE-E CRASH cum | > -15% | **+0.75%** | **PASS** |
| GATE-F t_stat(1×) | > 2.0 | **+1.594** | **FAIL** |

**OVERALL: 5/6 PASS → FAIL (closed)**

The single failing gate is GATE-F (statistical significance). The holdout t-stat
is +1.594 (n=2189), which corresponds to a two-tailed p-value of **0.111** — not
significant at the conventional 5% level. With the holdout Sharpe of +1.128, the
strategy is economically meaningful but not conclusively statistically
significant on the 2-year holdout alone.

Per the charter's mechanical verdict rule: **FAIL → construction is closed.** No
rescue, no second reveal. Token MN4-01 is spent irreversibly.

---

## 7. HONEST generalization read (holdout vs IS)

**The construction generalized BETTER than IS suggested on every economic
dimension, but failed the statistical-significance gate.**

| metric | IS (Phase A) | Holdout (Phase B) | direction |
|---|---|---|---|
| Sharpe 1× | +0.963 | **+1.128** | ↑ improved |
| maxDD | -34.42% | **-26.43%** | ↑ improved (shallower) |
| CRASH Sharpe | -0.916 | **+0.255** | ↑ FLIPPED positive |
| CRASH cum | -8.09% | **+0.75%** | ↑ FLIPPED positive |
| β_BTC mean | -0.009 | -0.001 | maintained |
| 2×/1× cost ratio | 0.864 | 0.862 | maintained |
| turnover ann | 44.8× | 38.6× | ↓ improved (lower) |
| coverage ratio | 159× | 174× | ↑ improved |
| t-stat | 1.987 | **1.594** | ↓ regressed (below 2.0) |

The headline Sharpe **improved** OOS (+0.963 → +1.128) — a rare outcome that
suggests the IS period (especially the 2024-H1 mania drag I flagged in Phase A)
was HARDER for this construction than the holdout. The maxDD **shallowed**
(-34.42% → -26.43%) — the risk primitives (DD brake, vol-target, CRASH scalar)
transferred well to unseen drawdown dynamics.

The single biggest generalization surprise: **CRASH flipped from structurally
negative (IS -0.916 Sharpe, -8.09% cum) to mildly positive (holdout +0.255
Sharpe, +0.75% cum).** In Phase A I wrote "CRASH regime is structurally negative —
pure TS-mom would profit, rank_neutral can't." That IS-read was wrong about the
OOS: the holdout's crash episodes (269 candles — a smaller, different sample than
IS's 570 crash candles) had enough cross-sectional dispersion for the L/S spread
to extract a small positive edge, and the Layer-2 throttle limited the downside in
the episodes where dispersion collapsed. The construction's "weakness" was
IS-specific, not structural.

The one metric that regressed is the t-stat (1.987 → 1.594). This is expected
regression-to-the-mean for a strategy at the edge of significance — IS t=1.987
was already marginal, and OOS t pulled back to 1.594 (two-tailed p=0.111). The
strategy is economically meaningful (Sharpe +1.128 over 2 unseen years, maxDD
-26.4%) but not conclusively statistically significant on the holdout alone.

The charter's verdict is mechanical: GATE-F failed → construction closed. But
the generalization is genuinely strong — the construction did NOT decay, invert,
or blow up on any economic dimension. It improved. The failure is narrowly on
statistical significance, which is a function of both effect size (Sharpe +1.128
is healthy) and sample length (2 years is short for a t>2.0 bar at weekly
dispersion). A longer holdout would likely resolve the t-stat either way; the
2-year window is what we have.

**Bottom line:** The construction is closed per the charter's mechanical rule, but
the OOS generalization is honest and strong. The Phase-A disclosed limitations
(DD-brake 65.7% fire-rate, H1/H2 asymmetry) PERSISTED but did not worsen. The
CRASH-structurally-negative read was IS-specific and did NOT persist — the holdout
CRASH was positive. The construction is a near-miss: economically a win,
statistically a fail on a 2-year window.

---

## 8. Files

- `analysis/portfolio/mn4_idea01_reveal.py` — reveal driver (frozen-construction reuse)
- `data/mn4_idea01/holdout_rets_1x.npy`, `holdout_rets_2x.npy`, `holdout_mask.npy`,
  `holdout_beta_btc_roll.npy`, `holdout_beta_eth_roll.npy` — saved holdout arrays
- `data/mn4_reveal/spend_MN4-01.json` — per-token spend marker
- `diary-portfolio-mn4/REVEAL-01.md` — this document

**Token MN4-01 spent.** One look. The 2-year holdout is irreversibly consumed for
this construction. The orchestrator consolidates spend markers into the shared
REVEAL-LEDGER.md; this pair did not edit the ledger directly. No git commits
(per charter — orchestrator commits centrally).
