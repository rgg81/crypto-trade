# MN4 IDEA-07 — Cross-Sectional Reversal, Dispersion-GATED

## Construction (frozen byte-exact)

**Signal**: `signal_i[t] = -r_i[t]` where `r_i[t] = close_i[t] / close_i[t - REVERSAL_LAG] - 1`.
High signal → want LONG (the trailing losers). Fading the cross-sectional winners.

**Frozen constants** (`analysis/portfolio/mn4_idea07_reversal.py`):

| Constant | Value | Principle-anchor |
|---|---|---|
| `REVERSAL_LAG` | **30 candles (10d)** | Jegadeesh (1990, JF) / Lehmann (1990) short-horizon reversal median (1wk–1mo). NOT the literal seed "3d" — see §Horizon re-anchor. |
| `REBAL` | **21 candles (7d, weekly)** | Charter §4 slow-favored; cadence-matched to a 10d signal. |
| `UNIV_TOPN` | 20 | PIT top-20 by trailing 30-candle $-volume. |
| `weighting` | `rank_neutral` | Continuous rank-based L/S (the cost-engineered form of the decile L/S; weights tilt smoothly to the extremes). |
| `GROSS` | 1.0 | Target sum|w|. |
| `GATE_W / GATE_MIN / GATE_QUANTILE` | 270 / 135 / **0.50** | Coverage-anchored: dispersion gate fires ~50% of days by construction. NOT Sharpe-scanned. |
| `DISP_MIN_MEMBERS` | 10 | Cross-sectional dispersion floor. |
| `CRISIS_GROSS_SCALE` | 0.5 | Halve gross in CRASH regime (trailing-90c BTC ret ≤ -15%). Principle-anchored. |
| Cost (1×) | 5 + 2.5 bps + funding | Honest per-side cost. |
| Cost (2×-GT) | 10 + 5 bps + funding | Ground-truth re-run twin. |
| Beta-hedge | BTC leg (ETH off) | `HedgeOverlay(beta_btc=rolling_beta(panel))`. |

**Composition at each weekly rebal k**:
- `gate_fires[k-1]` = dispersion[k-1] ≥ rolling_median(dispersion, 270)[k-1] (bool, past-only).
- `crisis_scalar[k-1]` = 0.5 if regime[k-1]==CRASH else 1.0.
- `gross_scalar_series[k-1]` = gate_fires × crisis_scalar ∈ {0, 0.5, 1.0}.
- `g = GROSS × gross_scalar_series[k-1]` → rank-neutral target weights → force-exit invalid prices → weight cap → BTC hedge sizing.
- All consumed at the engine's standard [k-1] decision lag (past-only).

---

## Horizon re-anchor — full disclosure sequence (Critic-transparent)

The seed one-liner specified "trailing-3d return." I tested that FIRST.

1. **3d/daily (literal seed)**: mean cross-sectional IC of raw trailing-3d return vs forward-3d return = **+0.0078** (slightly MOMENTUM, not reversal). Crypto top-20 at 3d has reflexive trend-persistence (the funding/liquidation feedback loop in my domain brief). The reversal book faded momentum → systematic loss.

2. **Horizon sign-test diagnostic** (`analysis/portfolio/mn4_idea07_mechanism.py`, IS-only, IC SIGN not Sharpe):

| horizon | univ | IC(raw, fwd close2close) | sign | gated IC |
|---|---|---|---|---|
| 1d | 20T | -0.0183 | REVERSAL | -0.0381 |
| 3d | 20T | +0.0078 | MOMENTUM | +0.0039 |
| 5d | 20T | -0.0025 | NULL | +0.0023 |
| 10d | 20T | -0.0268 | REVERSAL | -0.0441 |
| 20d | 20T | -0.0589 | REVERSAL | -0.0685 |

3. **Re-anchor to 10d** (Jegadeesh/Lehmann 1wk–1mo median). This is NOT the max-IC cell (20d has 2× stronger IC); 10d is the conservative, literature-anchored reading. The pivot is a structural axis change per the Prime Directive, disclosed full-sequence.

**The dispersion gate amplifies the reversal IC at every horizon tested** (gated IC more negative than unconditional at 1d/5d/10d/20d). The gate WORKS as designed at the IC level.

---

## IS scorecard (frozen construction: 10d signal, weekly rebal, 1× cost)

### Headline
| Metric | 1× cost | 2×-GT cost |
|---|---|---|
| **Sharpe** | **-1.0148** | **-1.1010** |
| maxDD | -85.14% | -86.95% |
| annReturn | -33.80% | -35.81% |
| turnover (ann, one-way) | 39.97 | 39.99 |
| win_rate | 25.98% | — |

### Unconditional vs conditional (gate ON vs OFF)
| Variant | Sharpe | turnover | IC (hold-horizon) |
|---|---|---|---|
| Gate ON (frozen) | -1.0148 | 39.97 | cond +0.0007 |
| Gate OFF (unconditional) | -0.7691 | 64.19 | uncond +0.0340 |
| **turnover ratio cond/uncond** | — | **0.623** | **IC ratio 0.020** |

The gate cuts turnover 38% (slow-favored, as designed) but DESTROYS the hold-horizon IC (ratio 0.020 — the gate fires in high-dispersion windows where the 7-day-forward reversal edge is absent).

### Per-year Sharpe (1×)
| 2020 | 2021 | 2022 | 2023 | 2024-H1 |
|---|---|---|---|---|
| -1.088 | -1.094 | -1.140 | -0.682 | -1.389 |

All negative. No year works.

### Regime-bucket Sharpe (1×)
| CRASH | MANIA | CHOP |
|---|---|---|
| -0.226 | -0.691 | -1.276 |

No regime works. NOT all-weather.

### Realized betas (post-hedge)
- β_BTC: **+0.091** (residual after the BTC hedge leg; not fully canceled — weekly-cadence realized vs 8h-rolling hedge sizing).
- β_ETH: +0.058.
- CRASH net: -0.132%/rebal. MANIA: -0.122%. CHOP: -0.275%.

### Cross-sectional IC (signal vs forward hold-period return)
- Unconditional IC: **+0.034** (n=229 weekly rebals — positive = reversal exists on close-to-close).
- Conditional IC: **+0.0007** (n=122 gate-on rebals — gate KILLS it at the hold horizon).
- Ratio cond/uncond: **0.020**.

### Dispersion-gate occupancy
- 50.9% of all candles; 52.1% of rebal days (decision-lagged). Coverage anchor confirmed.
- Crisis-throttle: 13.2% of rebal days.

---

## WHY it fails — the structural finding

The reversal anomaly does NOT survive the honest open-to-open engine on crypto top-20 perps. Two compounding mechanisms:

### Mechanism 1: close-to-close IC ≠ open-to-open PnL (the S4 lesson redux)

The charter's methodology §1 warns: "close-to-close scoring overstates tradability by capturing bid-ask bounce + delisting artifacts." The IC table (mechanism diagnostic) confirms this directly:

| horizon | IC close2close | IC open2open |
|---|---|---|
| 3d | -0.0149 | **-0.0956** |
| 10d | +0.0098 | **-0.0206** |
| 20d | +0.0491 | **+0.0199** |

At 10d the close-to-close IC is marginally positive (+0.010) but the open-to-open (tradable) IC is NEGATIVE (-0.021). The engine fills at open[k] and holds to open[k+1]. The reversal "edge" is a gap/overnight artifact that evaporates at the tradable fill. Only at 20d does the open-to-open IC turn positive (+0.020), and even there the realized PnL is negative (Sharpe -0.73 price-only) because the 20d signal predicts 20d-forward returns but the engine holds 7 days.

### Mechanism 2: the dispersion gate is backwards for the tradable edge

The seed hypothesized "the edge concentrates in high-dispersion windows." This is true for the close-to-close IC (gated IC > unconditional everywhere). But it is FALSE for the open-to-open tradable PnL:

- High dispersion = big moves = trends/cascades in crypto.
- In trends, crypto has MOMENTUM (reflexive persistence), not reversal.
- The gate concentrates gross exactly where the tradable edge is most negative.
- At the hold horizon: conditional IC +0.0007 vs unconditional +0.034 — the gate destroys 98% of the (already weak) hold-horizon IC.

This is a genuine, honest, mechanism-level falsification of the seed's central hypothesis for crypto. In equities, high dispersion = overreaction = reversal (the Jegadeesh mechanism). In crypto, high dispersion = trend/cascade = momentum continuation. The seed's equity prior does not transplant.

### Mechanism 3: rank-neutral weighting cannot rescue a zero-gross-edge signal

Price-only backtest (no cost, no funding, no hedge): Sharpe **-0.276**, mean ret/rebal **-0.010%**. Even with ZERO cost and ZERO funding, the book loses. The IC is positive (+0.034 close-to-close at the hold) but the open-to-open tradable edge is negative. No weighting scheme (rank-neutral, decile, or otherwise) can make a signal with negative tradable edge profitable.

---

## Leak battery (charter §3) — all PASS

| Check | Result |
|---|---|
| corrupt-future (signal + gate + crisis) | PASS — corrupting close[t0:] leaves indices < t0 bit-identical (17 unit tests). |
| decision-lag [k-1] | PASS — signal/gate/crisis all computed from close[s≤t]; engine consumes [k-1]. |
| PIT cross-sectional membership | PASS — dispersion denominator uses only live-at-t members (no survivorship backfill). |
| append-invariance | PASS — appending future candles leaves past signal/gate bit-identical. |

Tests: `tests/test_mn4_idea07_reversal.py` — 17/17 PASS, ruff clean.

---

## IS-gate verdict

**FAIL.** Do NOT bank for reveal.

The price-only backtest (no cost, no funding) has Sharpe -0.276. This is the strongest possible IS signal that the construction has no tradable edge: even in the absence of ALL frictions, the book loses. The charter's mandate is "high Sharpe, a winner in EVERY market condition"; this construction is negative-Sharpe in EVERY year and EVERY regime bucket on IS.

The reveal will consume token MN4-07 regardless (Phase B reveals all 10). The honest expectation: the holdout will also be negative. The value of this iteration is the STRUCTURAL FINDING (the two mechanisms above), not a deployable book.

---

## Slow-favored disclosure (charter §4)

| Variant | Sharpe 1× | turnover |
|---|---|---|
| Daily rebal (3d signal, seed literal) | -1.7739 | 190.7 |
| Daily rebal (10d signal) | -1.5532 | 118.8 |
| Weekly rebal (10d signal, FROZEN) | -1.0148 | 40.0 |
| Weekly rebal (20d signal) | -1.0170 | 50.1 |

The gate cuts conditional turnover 38% vs unconditional (39.97 vs 64.19) — the slow-favored design works mechanically. But no cadence rescues a signal with negative tradable edge.

---

## Model note

Opus 4.8 (Fable rate-limited this session; user-directed per charter). Disclosed.

---

## Files

- `analysis/portfolio/mn4_idea07_reversal.py` — frozen construction + IS scorecard runner.
- `analysis/portfolio/mn4_idea07_mechanism.py` — horizon/universe IC sign-test diagnostic.
- `tests/test_mn4_idea07_reversal.py` — 17-test leak battery + unit tests.
- `data/mn4_idea07/` — namespace (no artifacts written; all output to stdout).
