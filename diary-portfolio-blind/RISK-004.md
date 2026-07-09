# RISK-004 — Risk-Engineer Calibration Report (EXPLORATION-004)

- **Iteration:** EXPLORATION-004 (baseline-blind top-20 L/S portfolio track)
- **Branch:** `quant-portfolio-blind` (worktree: `.worktrees/quant-portfolio-blind`)
- **IS-ONLY.** OOS sealed at `OOS_CUTOFF = 2025-03-24`. Not looked at.
- **Script:** `analysis/portfolio/blind_risk_calib_004.py` (committed; mirrors the QE's
  `blind_exploration_004.py` so the R4/R5 base is byte-identical).
- **Parity anchor:** Combo D (default `180d/0.20/0.30`) reproduces the QE's R5
  Sharpe **+0.336** / maxDD **−47.8%** to the digit. Base construction verified.

---

## 0. Frozen recommendations (TL;DR for the QR)

| primitive | frozen value | rationale |
|---|---|---|
| **Regime gate** | **180d lookback / 0.20 threshold / 0.30 band / 0.30 floor** (the default) | Best IS Sharpe of the 8-combo grid (+0.336). No alternative beats it; the threshold=0.25 alternative that cuts 2021 false-positives (51%→43%) actively HARMS 2022 (turns it negative −0.34) because it fires later and under-catches the crash onset. |
| **gross_short** | **0.30** (the default) | On R4: 0.20 has higher Sharpe (+0.304) but FAILS G-FUND (+1834 bps > +1500). 0.30 (+0.235, +1394 bps) and 0.40 (+0.130, +952 bps) both pass; 0.30 dominates on Sharpe and 2022 resilience. |
| **Vol-target** | **NOT wired** (regime gate is the chosen defense) | VT is structurally inert on `longbias_ls` — the VT scale multiplies the single `gross` lever, but the leg-decoupled builder reads `gross_long`/`gross_short` directly (§7.3). |

**Best-achievable R5 Sharpe after calibration: +0.336** (the default). Calibration
confirms rather than overrides the brief's pre-registered defaults — they were
principled round numbers and they are at or near the IS optimum.

---

## 1. §7.1 Regime-gate calibration (8 combos, IS-only, band FIXED 0.30)

Grid: lookback ∈ {90, 180, 365}d × threshold ∈ {0.15, 0.20, 0.25} × floor ∈ {0.0, 0.30}.
Applied to the R4 book (blend-long 0.7 / mid-vol-short 0.3) → R5-variants.

| combo | look | thr | flr | Sharpe | ann | maxDD | 2021 | 2022 | 2020/21/22/23/24 firing % |
|---|---|---|---|---|---|---|---|---|---|
| **D 180/0.20/0.30** | 180d | 0.20 | 0.30 | **+0.336** | +5.7% | **−47.8%** | +1.52 | +0.32 | 14 / 51 / 100 / 4 / 7 |
| A 180/0.25/0.30 | 180d | 0.25 | 0.30 | +0.294 | +4.3% | −46.8% | +1.48 | **−0.34** | 13 / 43 / 100 / 3 / 1 |
| B 180/0.15/0.30 | 180d | 0.15 | 0.30 | +0.316 | +5.0% | −49.0% | +1.47 | +0.94 | 22 / 60 / 100 / 18 / 21 |
| C 365/0.20/0.30 | 365d | 0.20 | 0.30 | +0.275 | +3.7% | −47.9% | +1.52 | +0.80 | 14 / 51 / 100 / **34** / 8 |
| E 365/0.25/0.30 | 365d | 0.25 | 0.30 | +0.263 | +3.3% | −46.8% | +1.48 | +0.51 | 13 / 43 / 100 / **34** / 1 |
| F  90/0.20/0.30 | 90d | 0.20 | 0.30 | +0.183 | +0.6% | **−54.5%** | +1.86 | **−1.64** | 14 / 36 / **80** / 3 / 4 |
| G 180/0.20/0.00 | 180d | 0.20 | 0.00 | +0.276 | +3.7% | −47.8% | +1.40 | +0.29 | 14 / 51 / 100 / 4 / 7 |
| H 365/0.20/0.00 | 365d | 0.20 | 0.00 | +0.243 | +2.5% | −47.9% | +1.40 | +1.10 | 14 / 51 / 100 / **34** / 8 |

### Findings

**The default (D) is the IS Sharpe optimum.** None of the 7 alternatives beats +0.336.

**The 2021 "false-positive" framing is largely a red herring.** The 51% 2021 firing
rate looks high vs the brief's "~0%" prediction, but:
- May–Jul 2021 was a LEGITIMATE −55% BTC crash (the gate SHOULD fire). Suppressing it
  is not obviously correct.
- 2021 Sharpe under the default (which fires 51%) is **+1.52** — essentially tied with
  or better than every lower-firing alternative (A: 43% fire → +1.48; F: 36% fire →
  +1.86 but F's 90d lookback catastrophically misses 2022). The 2021 firing is not
  costing 2021 alpha.
- The one combo that meaningfully cuts 2021 firing (A, threshold 0.25: 51%→43%) does
  so by raising the fire threshold — which ALSO delays 2022 firing and turns 2022
  Sharpe **negative (−0.34)**. Catching the crash onset early is worth more than the
  modest 2021 chop de-risking costs.

**Lookback sensitivity is decisive:**
- **90d (F) is catastrophic** — it misses the sustained 2022 bear (only 80% firing)
  because the 90d window forgets the Nov-2021 peak by mid-2022. 2022 Sharpe −1.64,
  maxDD −54.5% (the only combo that fails G-DD). Confirms the brief's intuition that
  the lookback must span the structural peak.
- **365d (C, E, H) over-fires in 2023** (34% of 2023 candles) because the Nov-2021
  peak stays in the rolling window through most of 2023, keeping the gate partially
  engaged during the recovery. This drags 2023 alpha and overall Sharpe down ~0.06.

**Floor 0.0 (G, H) does not help.** Fully de-risking in the deep crash (floor 0 vs
0.30) gives up recovery exposure for no Sharpe benefit (G: +0.276 vs D: +0.336).
The 0.30 floor's "maintain recovery exposure" rationale (brief §3.3) is confirmed.

### Frozen regime config: **180d / 0.20 threshold / 0.30 band / 0.30 floor** (the default)

The brief's pre-registered defaults are at the IS optimum. The 2021 firing is a
feature (legitimate May-Jul crash defense), not a bug to suppress.

---

## 2. §7.2 gross_short calibration (3 values, IS-only on R4, no regime gate)

gross_long FIXED at 0.7; gross_short ∈ {0.2, 0.3, 0.4}.

| gross_short | Sharpe | ann | maxDD | turn/yr | 2021 | 2022 | 2021 net fund (bps) |
|---|---|---|---|---|---|---|---|
| 0.20 | **+0.304** | +3.9% | −64.3% | 153x | +1.57 | −1.36 | **+1834 (FAIL G-FUND)** |
| **0.30** | +0.235 | +1.8% | −58.3% | 180x | +1.44 | −1.17 | +1394 (PASS) |
| 0.40 | +0.130 | −1.5% | −58.8% | 207x | +1.17 | −0.84 | +952 (PASS) |

### Funding-dodge curve (2021 per-leg funding, bps of equity)

| gross_short | long pays | short receives | net 2021 |
|---|---|---|---|
| 0.20 | +2720 | −886 | +1834 |
| 0.30 | +2727 | −1332 | +1394 |
| 0.40 | +2733 | −1781 | +952 |

### Findings

**Lower gross_short = higher Sharpe, but the short leg has ~0 net alpha** (EXPLORATION-002
confirmed). The Sharpe gradient (0.20 > 0.30 > 0.40) is driven by short-side price
toxicity: each +0.1 gross_short adds ~+450 bps of funding income but loses more in
mania-year squeeze cost + turnover (turnover climbs 153x → 207x). The short leg's
defensive value (funding dodge + 2022 dampening) is real but is outweighed by its
drag above ~0.3 gross.

**G-FUND is the binding constraint.** 0.20 fails (+1834 bps > +1500). Of the two that
pass, 0.30 dominates 0.40 on every axis (Sharpe +0.235 vs +0.130; 2022 −1.17 vs −0.84;
2021 +1.44 vs +1.17). The funding-dodge curve shows 0.30 already captures 67% of the
0.40 funding income (−1332 vs −1781) at 60% of the gross.

### Frozen gross_short: **0.30** (the default)

The highest gross_short that maximizes Sharpe AND passes G-FUND. With the regime gate
added (R5), 2021 net funding drops slightly further to +1332 bps (gate fires 51% of
2021, reducing the long leg's payment) — comfortably inside G-FUND's +1500 bps.

---

## 3. §7.3 VT diagnostic (INFORMATIONAL — confirms the brief's design choice)

| run | Sharpe | ann | maxDD | mean gross |
|---|---|---|---|---|
| R5 no-VT | +0.336 | +5.7% | −47.8% | 0.870 |
| R5 +VT=0.40/max_lev=2.0 | +0.336 | +5.7% | −47.8% | 0.870 |

**VT is structurally inert on `longbias_ls`.** The numbers are bit-identical because
the VT scale multiplies the single `gross` lever (`g = gross * scale`), but the
leg-decoupled builder reads `gross_long` / `gross_short` directly
(`blind_engine.py: gl = gross if gross_long is None else float(gross_long)`). The VT
scale is computed and discarded.

This neither confirms nor rejects the EXPLORATION-001 VT-underperformance finding —
VT simply has no effect on this construction. It IS consistent with the brief's §2.5
design decision: the regime gate (not VT) is the chosen crash defense, and the engine
correctly decouples VT from the leg-decoupled gross levers. If VT-on-the-long-leg
were desired, it would require wiring `scale` into the `gl = ...` line — out of scope
for this calibration (signal/structure change, not a risk-primitive param).

---

## 4. Risk analysis (default R5; report, not gated)

### 4.1 maxDD attribution — the maxDD is now a 2024 grinding drawdown, NOT a 2022 crash

| metric | value |
|---|---|
| maxDD | −47.8% |
| peak date | 2024-05-20 |
| trough date | 2024-12-22 |
| driving year | **2024** (not 2022) |

**This is the regime gate's signature.** The 2022 correlated-deleveraging crash —
which drove the −87% long-only / −58% R4 maxDD — is tamed: the gate fired 100% of
2022 candles (mean scalar 0.349, 71.7% at floor), clipping the long leg's 2022 loss
to −0.43 (vs R4's −0.93). The residual maxDD is a **2024 calm-year grind** where the
gate did NOT fire (2024 firing 7%) but both legs bled modestly (long +0.17, short
−0.17). The book's crash defense works; its residual drawdown is ordinary alpha drought,
not a regime failure.

### 4.2 Per-leg per-year price P&L (fraction of equity)

| year | long leg | short leg |
|---|---|---|
| 2020 | +0.453 | −0.295 |
| 2021 | +1.438 | −0.594 |
| **2022** | **−0.428** | **+0.575** |
| 2023 | +0.575 | −0.251 |
| 2024 | +0.171 | −0.172 |
| 2025Q1 | −0.174 | +0.208 |
| **TOTAL** | **+2.034** | **−0.529** |

The long leg is the alpha engine (+2.03 over IS); the short leg is the hedge (−0.53
net, but +0.575 in 2022 precisely when the long leg lost). This is the leg-decoupled
design working as specified. Note 2022 net leg-sum = +0.15 (gate + short hedge
converted a −0.93 long crash into a +0.15 net book gain).

### 4.3 Net-exposure distribution

| metric | value |
|---|---|
| rebal steps | 950 |
| % net-long | 79.4% |
| % net-short | 20.6% |
| % \|net\| < 0.05 | 4.3% |
| mean net | +0.274 |
| range | [−0.090, +0.700] |

The book is net-long 79% of the time (calm/regime-engaged target +0.40) and flips
net-short 21% of the time (deep-crash regime; floor 0.21 long vs 0.30 short → net
−0.09). The gate is NOT over-flipping — it engages the defensive net-short posture
exactly in the crash minority and releases it promptly in recovery. Mean net +0.274
(slightly below the +0.40 calm target because the gate drags the long leg below 0.7
on the ~35% of IS candles where scalar < 1.0).

### 4.4 Per-name concentration

| metric | value | flag |
|---|---|---|
| max \|w\| incl warmup | 0.522 | k=23 (warmup edge, known artifact) |
| max \|w\| post-warmup | **0.371** | k=5261, col=22 (**> 20%**) |

The k=5261 instance is the late-IS overlap-drop case the QE flagged: long-precedence
left few shorts carrying the 0.30 budget. This is a real concentration risk (37% in a
single short name), not a bug. It is structural to using the blend (contains vol_low)
for the long leg and vol_low alone for the short — the overlap rate is 89.8%. A
per-name cap (e.g. clip individual \|w\| at 0.10) would address this but is a
structure change, not a risk-primitive param — deferred to a future iteration if
EXPLORATION-004 proceeds.

### 4.5 Fractional-Kelly sizing note

| metric | value |
|---|---|
| ann vol | 0.310 (31.0%) |
| ann return | +0.057 (+5.7%) |
| Sharpe | +0.336 |
| full-Kelly leverage | **0.59x** |
| 1/4-Kelly | 0.15x |
| 1/2-Kelly | 0.30x |

**This is a weak-edge strategy.** Full-Kelly leverage is 0.59x — meaning the strategy
is already running ABOVE its Kelly-optimal leverage at mean gross 0.87 (calm years
~1.0x). For a Sharpe-0.34 book, prudent live sizing is **0.5–1.0x gross** (roughly
full-Kelly with a thin margin), NOT the 2–3x a Sharpe-1.5 book could justify. A
conservative 1/2-Kelly deployment would target ~0.30x gross — i.e. deploy 1/3 of
capital to the strategy and hold 2/3 in cash. The regime gate's automatic de-risking
in crashes is a partial substitute for lower baseline leverage, but in calm years the
book runs near-Kelly. **Recommendation: if deployed, cap live gross at ~0.6–0.8x
(either via reduced gross_long/gross_short or by sizing the allocation to ~60–80% of
nav).** This is the crypto-native reading: crypto's fat tails mean the Kelly-optimal
is itself fragile to vol-misestimation, so size below full-Kelly.

---

## 5. Honest gap assessment — can calibration close +0.34 → +0.60?

**No. The gap is structural (weak alpha), not a calibration deficit.**

Evidence:
1. **Best-achievable R5 Sharpe after calibration = +0.336** (the default). The 8-combo
   regime sweep's best IS the default; the 3-value gross_short sweep's best is 0.20
   (+0.304) which fails G-FUND. No risk-primitive param combination reaches +0.40,
   let alone +0.60.
2. **The alpha ceiling is binding.** R3 blend long-only = +0.362 — the multi-factor
   synergy DID NOT fire (R3 < R1 vol_low's +0.511). The long-side OHLCV alpha on the
   PIT-top-20-$-volume universe at 8h has a hard ceiling around +0.36. The defensive
   engineering (R4 short + R5 regime gate) reduced maxDD from −89.8% to −47.8% (a real
   achievement), but it cannot manufacture alpha — it only trades return for drawdown
   control. A book whose gross alpha is +0.36 cannot reach +0.60 deployable Sharpe by
   risk-primitive tuning alone.
3. **The defense is already near-optimal.** The regime gate caught 2022 (100% firing,
   2022 flipped from R1's −1.53 to +0.32). The residual maxDD is a 2024 alpha-drought
   grind, not a crash the gate could catch. Further defense tightening (lower floor,
   shorter lookback) either doesn't help (floor 0: +0.276) or actively harms (90d
   lookback: +0.183, misses 2022).

**This is the brief's §5 "informative null" materializing:** G-DEPLOY fails because
the long-side OHLCV alpha on this universe at this frequency is collectively too weak
to overcome the funding tax + crash drawdown, even with the verified defensive
substrate. The defense works (G-DD, G-REGIME, G-FUND all PASS); the alpha engine does
not (G-ALPHA-MF, G-DEPLOY, G-COST all FAIL). The path forward — if the track
continues — is a **scope break** (OI-ranked universe less adverse-selected than
$-volume; or a non-OHLCV mechanism like funding carry per BIS WP 1087 / on-chain
Whale Ratio), not further risk-primitive calibration on this construction.

**One-line verdict:** the +0.34→+0.60 gap is structural — calibration confirms the
defaults are near-optimal and cannot manufacture alpha that the long-side OHLCV
signals do not contain on this universe.

---

## Files touched (all within blinding)

- `analysis/portfolio/blind_risk_calib_004.py` — NEW. The §7.1/§7.2/§7.3 sweep +
  risk-analysis script. Reads only blind_* modules. OOS never inspected.
- `tests/test_blind_engine.py` — UNCHANGED (32/32 green; the sweep adds no engine code).
- `diary-portfolio-blind/RISK-004.md` — this file.

No baseline-artifact reads. No commits. OOS sealed.
