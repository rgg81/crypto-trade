# RISK-006 — Risk-Engineer Calibration Report (five control families)

- **Iteration:** RISK-006 (baseline-BLIND top-20 L/S portfolio track)
- **Branch:** `quant-portfolio-blind` (worktree: `.worktrees/quant-portfolio-blind`)
- **IS-ONLY.** OOS sealed at `OOS_CUTOFF = 2025-03-24`. Not looked at. Every number below is
  computed on candles with `grid_ms < OOS_CUTOFF_MS` (blind_universe.is_mask).
- **NO SHARPE-BASED CALIBRATION.** Every frozen parameter is derived from ex-ante indicator
  statistics (distributions, quantiles, flag coverage, firing rates, regime durations) +
  a-priori reasoning. The /005 reference book is reproduced ONCE — only to obtain input
  statistics (its own return/leg/equity series) and for indicator-overlap analysis (which months
  the gate flags) — NEVER to pick a threshold by Sharpe. The frozen values get ONE evaluation
  later in the engineer's pre-registered variant matrix.
- **Script:** `analysis/portfolio/blind_risk_calib_006.py` (committed; runs end-to-end).
- **Parity anchor:** /005 reproduces to the digit — **Sharpe +0.9134 / maxDD −32.99% /
  turnover 55.4x** (target +0.913 / −33% / 55.4x). Per-candle leg attribution
  `long_px + short_px − net_fund − tcost ≡ rets` reconciles at **1.4e-17**, so every
  decomposition below is exact.

---

## 0. Frozen recommendations (TL;DR for the QR)

| ctrl | parameter | **FROZEN value** | derived from |
|---|---|---|---|
| **C1** | `btc_mom_lookback` / `btc_mom_thr` | **63 candles (21d) / +0.09** (≈IS p70 of BTC 21d return) | ex-ante distribution |
| C1 | `disp_lookback` / `disp_z_win` / `disp_z_thr` | **21 / 365 / +0.5** | dispersion z-stat |
| C1 | `fund_lookback` / `fund_z_win` / `fund_z_thr` | **21 / 365 / +0.5** | funding z-stat |
| C1 | combination | **`btc_up AND (disp_hi OR fund_hi)`** | mania/crash separation |
| C1 | application / floor | **SHORT leg only, floor 0.5×** (`short_scalar_series`) | leg-clip accounting |
| **C2** | `K` / `Q` | **21 candles (7d) / +0.30** (≈IS p90 universe 7d return) | trailing-return dist |
| C2 | excluded budget | **SHRINK** (drop to SKIP, do not re-allocate) | squeeze audit |
| **C3** | `vol_target_ann` | **0.25** (IS p50 of L=45 trailing ann-vol; book vol 29.5%) | realized-vol dist |
| C3 | `vol_lookback` / `max_lev` | **45 candles (15d) / 1.0** (never lever up) | responsiveness/tail |
| **C4** | `dd_brake_threshold` | **0.20** (−20%; ≈3× the p90 DD-episode depth of 7%) | DD-episode dist |
| C4 | `dd_brake_scale` / `dd_brake_recovery` | **0.5 / 0.10** (half, not flatten; hysteresis band) | recovery/whipsaw |
| **C5** | btc_drawdown_scalar (FALSIFY) | **defaults 540/0.20/0.30/0.30**, whole-book | falsification arm |

**Combination order for the variant matrix:** `/005` → `+C1` → `+C1+C2` → `+C1+C2+C3` →
`+C1+C2+C3+C4`; **C5 evaluated alone** as the falsification arm. C1 is the lead (most surgical,
biggest expected effect); C2 catches the intra-week squeezes C1 structurally can't; C3 is the
second-moment governor; C4 is tail insurance only.

**Two engine extensions the QE must add** (C3/C4/C5 plumbing already exists):
1. **C1** — `short_scalar_series` (T,), consumed at `[k-1]`, scales ONLY the negative-weight
   budget in `target_weights_midvol_short` (long budget unchanged → book goes mildly net-long
   when flagged). Spec in §1.5.
2. **C2** — a trailing-return exclusion inside `target_weights_midvol_short`: any short-band name
   with trailing-`K` return > `Q` moves to SKIP; short gross shrinks (per-name weight unchanged).
   Spec in §2.4.

---

## 1. C1 — Mania-regime SHORT-leg gate (LEAD CANDIDATE)

### 1.1 Construction (exact, implementable)

Past-only (T,) flag `gate[t]`, all inputs known at `close[t]`:

```
btc_up[t]  = ( close_BTC[t] / close_BTC[t-63] - 1 )              > +0.09     # BTC ripping 21d
disp[t]    = cross-sec std over universe members of ( close_i[t]/close_i[t-21] - 1 )
disp_hi[t] = z_365( disp )[t]                                    > +0.5      # dispersion blow-out
fmean[t]   = universe-mean of trailing-21 mean funding_i[t]
fund_hi[t] = z_365( fmean )[t]                                   > +0.5      # funding blow-off
gate[t]    = btc_up[t]  AND  ( disp_hi[t] OR fund_hi[t] )
```

`z_365(x)[t] = (x[t] − mean(x[t-364..t])) / std(x[t-364..t])` — a trailing 365-candle
(≈4-month) rolling z, `min_periods = 182`.

**Why BTC-up is MANDATORY (the load-bearing design decision).** DIAGNOSTIC-003's central finding
is that the enemy is alt-mania (BTC-UP), and that in BTC-crash months the short leg is the book's
crash *alpha* (+1.53 aggregate short_px over 20 crash months) which must NOT be cut. Requiring
`btc_mom_63 > +9%` mechanically guarantees the gate can never fire in a crash month (BTC-down), so
the crash-alpha short leg is structurally preserved. Dispersion + funding then confirm the
cross-sectional signature (lottery alts mooning / positive-funding blow-off, per the diagnostic's
2021-Q1 and 2024-Q4 signatures).

### 1.2 Threshold provenance (ex-ante statistics, not Sharpe)

- `btc_mom_thr = +0.09` = the **IS p70** of BTC 63-candle returns (p60=+5.2%, p70=+9.2%, p90=+26%).
  Chosen because the higher "ripping" bar cleanly de-flags crash months (see §1.4: crash max flag
  21%→7% moving p60→p70) while keeping every named mania month flagged.
- `disp_z_thr = fund_z_thr = +0.5` = "at least half a trailing standard deviation above the
  ≈4-month norm." A principled "elevated" bar, not a tuned value.
- **Coverage = 19.3% of IS candles** — inside the target 10–25% right tail. It sits at the middle
  of the range because the mania regimes it catches (2020-Q4, 2021-Q1, 2024-Q4, and the BTC-up
  legs of 2023) are *persistent multi-month periods*, not point events — a persistent-regime gate
  should cover a coherent slab, not scatter.

### 1.3 Monthly flag map (IS, from the committed script)

`flag` = fraction of the month's candles flagged. `short_px < 0` = the short leg lost that month.

| month | ret | long_px | short_px | flag | tag | | month | ret | long_px | short_px | flag | tag |
|--|--:|--:|--:|--:|--|--|--|--:|--:|--:|--:|--|
| 2020-11 | −0.077 | +0.212 | **−0.282** | 57% | **MANIA** | | 2022-11 | +0.097 | −0.053 | +0.158 | 7% | CRASH |
| 2020-12 | +0.196 | +0.059 | **+0.143** | 42% | **MANIA** | | 2023-01 | +0.033 | +0.188 | −0.152 | 62% | |
| 2021-01 | +0.076 | +0.289 | **−0.211** | 70% | **MANIA** | | 2023-11 | +0.028 | +0.058 | −0.020 | 43% | |
| 2021-02 | +0.112 | +0.283 | **−0.172** | 67% | **MANIA** | | 2023-12 | −0.076 | +0.152 | **−0.245** | 67% | **MANIA** |
| 2021-03 | −0.141 | +0.122 | **−0.262** | 23% | **MANIA** | | 2024-02 | +0.140 | +0.181 | **−0.041** | 45% | **MANIA** |
| 2021-05 | +0.104 | +0.000 | +0.109 | 0% | CRASH | | 2024-03 | −0.030 | +0.122 | **−0.153** | 60% | **MANIA** |
| 2021-06 | −0.003 | −0.088 | +0.087 | 0% | CRASH | | 2024-05 | −0.121 | +0.129 | −0.246 | 2% | |
| 2022-05 | +0.089 | −0.193 | +0.290 | 0% | CRASH | | 2024-11 | −0.163 | +0.230 | **−0.391** | 92% | **MANIA** |
| 2022-06 | −0.089 | −0.218 | +0.137 | 0% | CRASH | | 2024-12 | +0.044 | −0.033 | +0.079 | 23% | |

- **All 9 named mania months flag** (mean 58%, min 23% = 2021-03). **All 5 named crash months are
  de-flagged** (mean 1%, max 7% = 2022-11's FTX rebound). The full 63-month map is in the script
  output.
- **The gate is well-targeted beyond the named list:** in the "OTHER" flagged months the short leg
  was *also* mostly losing (2023-01 −0.152, 2020-07 −0.145, 2020-08 −0.086, 2021-10 −0.161), so
  cutting it there is P&L-positive on net (§1.4). The gate is not scattering into short-leg-winning
  territory.
- **Known miss — 2024-05 (2%) and 2023-09 (0%).** 2024-05 is an *intra-week* squeeze (short_px
  −0.246) that a weekly regime gate cannot see → **that is C2's job.** 2023-09 is the diagnostic's
  separate *funding-driven grind loss at low BTC vol* (BTC not up) — no BTC-up gate can flag it;
  it is out of C1's mandate by construction. Both are honestly out of scope for C1.

### 1.4 Application decision: SHORT-leg-only, floor 0.5

First-order P&L delta of scaling the short leg on flagged candles (short_px re-weighted; ignores
turnover feedback — a directional statistic, not a Sharpe score):

| floor | MANIA Δ | CRASH Δ | OTHER Δ | TOTAL Δ | interpretation |
|---|--:|--:|--:|--:|--|
| **0.5×** | **+0.492** | +0.017 | +0.492 | **+1.001** | positive in every bucket |
| 0.0× | +0.984 | +0.035 | +0.983 | +2.001 | doubles benefit; book fully net-long |

- **Short-leg-only (not whole-book) is decisive.** In EVERY mania month the LONG leg is positive
  (+0.06 to +0.29) — low-vol longs rally in mania. Whole-book scaling (the `gross_scalar_series`
  route) would clip that winning long leg. Cutting the SHORT leg only is surgical: it removes the
  squeezed short without touching the mania-winning long. This is the exact mechanism the diagnostic
  called for ("cut/cap the SHORT leg when the cross-section enters mania").
- **Floor 0.5, not 0.0.** Full removal doubles the raw benefit but (a) makes the book strongly
  net-long during mania (a big directional bet), and (b) removes ALL short-leg crash insurance for
  the mania→crash-flip tail (§1.6). Floor 0.5 caps the mania-squeeze loss by half while retaining
  half the hedge and half the dollar-neutrality — the stress-robust choice for a control whose
  whole raison d'être is tail-robustness.
- **Winner-clip cost is small and accepted.** 2020-12 (+19.6%, the top-1 month) is the ONE mania
  where the short leg WON (+0.143). The gate flags it 42%, so floor-0.5 clips ≈ **−0.030** of its
  short P&L — dwarfed by the +0.492 MANIA-bucket benefit. A binary gate cannot distinguish
  ex-ante "mania where short wins" from "mania where short is squeezed"; accepting the occasional
  −0.03 clip to insure the −0.28/−0.39 squeezes is the correct risk trade.

### 1.5 Plumbing spec for the QE (short-leg-only)

Add a `short_scalar_series: np.ndarray | None = None` (T,) arg to `run_backtest`, consumed at the
**same `[k-1]` decision lag** as `signal`/`gross_scalar_series`. Semantics for
`weighting="midvol_short"`:

```
ssc = 1.0 if short_scalar_series is None else max(0.0, float(short_scalar_series[k-1]))
# in target_weights_midvol_short: multiply ONLY the negative (short) per-name budget by ssc:
#   long side  : +half / n_long                (UNCHANGED)
#   short side : -half / n_short * ssc          (scaled)
# => sum(w) = +half - half*ssc  (net-long by half*(1-ssc) when flagged) ; sum(|w|)=half*(1+ssc)
```

This intentionally **breaks dollar-neutrality** while flagged (net-long by `0.5*(1−ssc)` of the
long budget). The whole-book `gross_scalar_series` path already exists and is the inferior fallback
if the short-leg extension cannot land in time. `book_scalar_series` forensics should additionally
record the applied `ssc` per rebal.

### 1.6 Stress test — mania flag colliding with a crash start (2021-04 → 05 turn)

Candle-level gate state through the actual 2021 top (script output, weekly sample):

| date | btc_mom_63 | flag | short_px |
|--|--:|:--:|--:|
| 2021-04-15 | +20.3% | **1** | −0.022 (squeezed — cut helps) |
| 2021-04-19 | −3.5% | 0 | −0.013 |
| 2021-05-10 | +0.4% | 0 | +0.042 |
| 2021-05-20 | −26.7% | 0 | −0.051 |
| 2021-05-29 | −40.3% | 0 | **+0.031 (crash alpha, full gross)** |

**The failure mode did NOT materialize.** The 63-candle BTC momentum rolled negative by
**2021-04-19 — four weeks before** the crash's worst (2021-05-20+), so the gate had fully released
and the short leg was at FULL gross earning its crash alpha (+0.030/+0.031 in late May) exactly when
needed. The mid-April flagged window (04-12→04-17) coincided with the short leg actually being
squeezed (BTC's pump to $64k), so cutting it there *helped*.

**Residual tail risk (documented, mitigated by floor 0.5):** a *V-shaped* mania→crash with no
roll-over period — an instantaneous reversal from `btc_mom > +9%` straight into capitulation —
would keep the gate flagged for up to ~63 candles of momentum-unwind, cutting the short leg into
the first 1–3 weeks of a real crash. Floor 0.5 (retain half the short) bounds this loss; it is the
principal reason the floor is not 0.0. C4 (own-equity DD brake) provides a second, regime-agnostic
backstop for this case.

---

## 2. C2 — Per-name parabolic short-exclusion (intra-week squeeze defense)

### 2.1 Construction

At each rebalance, for any name that `target_weights_midvol_short` would place in the SHORT band:

```
rK_i[t] = close_i[t] / close_i[t-21] - 1          # trailing 7-day return, past-only
if rK_i[t] > Q  ->  move name i to SKIP (do NOT short it)
K = 21 (7 days) ;  Q = +0.30
```

`Q = +0.30` ≈ the **IS p90** of universe-member trailing-21 returns (p90 = +29.2%, p95 = +49.8%).
A fixed, pre-registered threshold ("never short a name up >30% in 7 days") — explainable and
state-discontinuous, preferred over an opaque rolling knob.

### 2.2 Firing statistics (IS)

| K / Q | excludes (% of short-name-candles) | fwd short_px P&L of the excluded set |
|---|--:|--:|
| **21 / p90 (+30%)** | **5.6%** | **−4.08** (strongly net-LOSING → good to drop) |
| 21 / p95 (+50%) | 1.6% | −1.95 |
| 42 / p90 (+54%) | 6.2% | −2.93 |

The excluded high-momentum shorts were, in aggregate, deeply net-losing (−4.08 forward short_px) —
they are precisely the squeeze fuel. **K=21/Q=+30% chosen over K=42:** the 2024-11 mooners
accelerated in ~1 week (below), so the 7-day window catches them at entry; the 14-day window lags.
Q=p90 (not p95) is required to catch the *full* mooner cohort (see §2.3).

### 2.3 Squeeze-case audit — would the 2024-11 mooners have been excluded? (K=21, Q=+30%)

Shorted names + trailing-7d return at each 2024-11 rebalance (`[EXCL]` = excluded by C2):

| rebal | shorted names (trailing-7d return) |
|--|--|
| 2024-11-06 | DOGE +16%[keep], NEIRO +2%, WIF −9%, APE −9% (no mooners yet) |
| 2024-11-13 | **DOGE +89%[EXCL], ADA +49%[EXCL], PEPE +38%[EXCL]**, SHIB +30%[keep], WLD +18% |
| 2024-11-20 | **ADA +48%[EXCL]**, FLOKI +27%[keep], WIF +12%, ACT −11% |
| 2024-11-27 | **XRP +30%[EXCL]**, HBAR +10%, DOGE +2%, NEIRO −17% |

C2 excludes DOGE/ADA/PEPE on 11-13 (the peak of the squeeze), ADA on 11-20, XRP on 11-27 — the
exact names that ran the short leg to −0.391 that month. **ORDIUSDT-style 3.6× (+260%) movers are
far above +30% → always excluded.** SHIB at +30% sits on the boundary (keep) — an accepted edge
case; the three biggest movers are all caught.

### 2.4 Budget handling + plumbing spec

**SHRINK, don't re-spread.** The freed short budget is NOT re-allocated to the remaining shorts:
per-name short weight stays `−half / n_short_original`; excluded names get 0; short gross falls to
`half * (n_short − n_excluded) / n_short_original`. Rationale: in a *broad* mania many mid-vol names
are parabolic at once; re-spreading would concentrate the short budget into the few survivors, which
are themselves squeeze-prone. Shrinking naturally de-risks the short leg exactly when mania is
broad, and mirrors the engine's existing `longbias_ls` overlap-drop convention ("short gross
reduced by one name's worth; NOT re-allocated — deterministic"). Consequence: the book tilts mildly
net-long in mania — same acceptable direction as C1.

QE: add the exclusion inside `target_weights_midvol_short` (needs the trailing-`K` return matrix
passed in, or computed from `panel.close` inside the engine at the decision candle `k-1`).

---

## 3. C3 — Portfolio vol-targeting (second-moment governor)

### 3.1 Construction + provenance

`vol_target_ann = 0.25`, `vol_lookback = 45`, `max_lev = 1.0` — feeds the EXISTING
`_vol_target_scale` (active on `midvol_short`; the `g = gross * scale * book_scalar` path).

- **`vol_target_ann = 0.25`** = the IS **p50** of the /005 book's L=45 trailing annualized realized
  vol (book full-sample vol = 29.5%; p40=23% / p50=25% / p60=27%). Setting the target at the median
  makes the book run ≈1.0× on a typical candle, de-gross when vol is elevated, and (with max_lev=1)
  never lever up. The 40–60th-percentile band the brief suggests is [23%, 27%]; 25% is its center.
- **`vol_lookback = 45` (15 days ≈ 2 rebalance cycles)** — responsive enough to react within ~2
  weekly rebals, stable enough not to whipsaw on a single cycle. (21/45/63/90 all give near-identical
  percentiles, so the choice is a responsiveness/stability judgment, not a fitted value.)
- **`max_lev = 1.0` (pure de-gross, never lever up)** — for a weak-edge book (Sharpe ~0.9, but the
  edge is 10-month-concentrated), levering into calm regimes courts the calm→spike transition and
  would amplify the 2024 alpha-drought grind. Crypto's fat tails make the Kelly-optimal itself
  fragile to vol mis-estimation, so cap at 1.0.

### 3.2 Predicted mechanical effect on the fat right tail (the diagnostic's warning, quantified)

| vol_target | top-10-month mean scale | ALL-candle mean scale | verdict |
|---|--:|--:|--|
| 0.25 | 0.876 | 0.876 | **equal → uniform de-gross, NOT winner-selective** |
| 0.27 | 0.902 | 0.902 | equal |
| 0.30 | 0.930 | 0.930 | equal |

**Important nuance that softens the diagnostic's fear.** The diagnostic warns that symmetric
shrinkage "may clip winners" because top-10 months = 98.8% of growth. C3 *does* scale those months
down by ~12% at vt=0.25 — but it scales them at the SAME rate as every other candle (0.876 vs
0.876). The top-10 winner months are **not** disproportionately high-vol, so vol-targeting is a
*uniform* ~12% de-gross, **not** a winner-selective clip. It trades ~12% of gross for
second-moment stability across the board. This is why C3 is a legitimate governor — but also why
it is only #3 in priority: it is symmetric and non-surgical, unlike C1.

### 3.3 Failure mode

Vol-target lag at a regime turn: `_vol_target_scale` estimates vol from the *trailing* 45 candles,
so at a calm→spike turn the book is still near full gross for the first ~1–2 rebals of the spike
(the estimate hasn't caught up), then de-grosses into the (possibly already-passed) high-vol regime
— the classic vol-target lag. This is acceptable for a governor but is why C3 is not a primary
crash/mania defense.

---

## 4. C4 — Drawdown circuit brake (tail insurance)

### 4.1 Construction + provenance

`dd_brake_threshold = 0.20`, `dd_brake_scale = 0.5`, `dd_brake_recovery = 0.10` — feeds the EXISTING
past-only, own-equity, hysteresis brake.

- **`threshold = 0.20` (−20%)** — the /005 book's post-warmup DD-episode depth distribution is
  p50=1% / p75=2% / **p90=7%** / p95=16%, maxDD −33%. A circuit breaker must sit *well beyond*
  routine chop: −20% is ≈3× the p90 depth and beyond p95, so it fires only on genuine tail events,
  not on the 123 routine episodes.
- **`scale = 0.5` (half, not flatten)** — the book's deep drawdowns are frequently followed by
  *strong recovery* months (the short-leg crash alpha: e.g. the −20% 2024-05 engagement is
  immediately followed by 2024-06 **+12.1%**, a top-10 month). Flattening (0.0) would lock out that
  recovery entirely and pay full round-trip re-entry turnover on an already turnover-heavy book
  (55×/yr). Half-scaling caps the tail depth while keeping half the recovery participation and
  halving the whipsaw turnover.
- **`recovery = 0.10` (= threshold/2)** — hysteresis band [enter −20%, release −10%]; a 10pp band
  avoids chattering at the trigger.

### 4.2 Firing statistics (IS, hysteresis simulated on the raw /005 equity)

| threshold / recovery | engagements | which months | candles braked |
|---|--:|--|--:|
| −15% / −7.5% | 8 | 2020-07,11 / 2021-03 / 2022-01,06 / 2023-09 / 2024-05,11 | 33% (too frequent) |
| **−20% / −10%** | **4** | **2020-11, 2023-09, 2024-05, 2024-11** | 16% |
| −25% / −12.5% | 2 | 2023-12, 2024-12 | 7% (too rare) |

**−20% gives 4 engagements over 5.25 IS years (~0.8/yr)** — appropriately rare for a circuit
breaker. The 4 months are exactly the alt-mania squeeze losers (2020-11, 2024-05, 2024-11) plus the
2023-09 funding grind — i.e. the tail C1/C2 leave on the table (2024-05 and 2023-09 are C1's known
misses). C4 is therefore a genuine complement, not a duplicate of C1. Caveat (per the diagnostic):
the squeeze losses are *fast/intra-week*, so the brake engages AFTER the worst candle — it caps the
grind *depth* (good for the "succeed in the worst months" mandate) but adds little Sharpe; keep it
strictly as a maxDD-tail layer, not an alpha lever.

---

## 5. C5 — BTC-crash de-risk (FALSIFICATION ARM — pre-registered to HURT)

### 5.1 Construction

`btc_drawdown_scalar(lookback=540, threshold=0.20, band=0.30, floor=0.30)` — the module defaults,
applied **whole-book** via `gross_scalar_series` (consumed at `[k-1]`).

### 5.2 Firing statistics (IS)

| year | firing (scalar<1) | mean scalar |
|---|--:|--:|
| 2020 | 15% | 0.930 |
| 2021 | 51% | 0.780 |
| **2022** | **100%** | **0.349** |
| 2023 | 4% | 0.987 |
| 2024 | 7% | 0.994 |
| 2025Q1 | 21% | 0.983 |

Overall 35% firing; mean scalar 0.470 when fired. It fires overwhelmingly in the 2021–2022 bear.

### 5.3 Pre-registered directional prediction

**This arm should REDUCE crash-month P&L and LOWER Sharpe.** Applied whole-book it cuts BOTH legs
in BTC-drawdown regimes — which is exactly where the SHORT leg delivers the book's crash alpha
(**crash-month short_px = +0.781 over the 5 named crash months, with mean whole-book scalar 0.385**
there — i.e. this arm would cut ~62% of that gross). Per-bucket expected sign:

| bucket | expected effect | mechanism |
|---|:--:|--|
| CRASH months | **−** (worse) | cuts the winning short leg during BTC drawdowns |
| MANIA months | ≈0 | BTC is UP → no BTC drawdown → scalar ≈ 1.0, no effect |
| QUIET months | ≈0 | scalar ≈ 1.0 |
| **NET** | **NEGATIVE** | removes crash alpha, adds nothing in mania (the real problem) |

This is the diagnostic's ranked-hypothesis #4 ("BTC-crash de-risking — LOWEST / likely NEGATIVE").
Including it as an explicit falsification arm confirms the redesign is attacking the RIGHT regime
(mania, not crash). If the variant matrix shows C5 improving Sharpe, the whole diagnostic thesis is
wrong and must be revisited.

---

## 6. Combination order + interaction risks

### 6.1 Recommended variant-matrix order (compose in priority order)

1. **`/005`** — control (no risk overlay).
2. **`+C1`** — lead; the surgical mania short-leg gate. Expect the largest single-control effect.
3. **`+C1 +C2`** — add the per-name parabolic exclusion for the intra-week squeezes C1 misses
   (2024-05-type). C1 and C2 attack the same enemy at different time-scales (weekly regime vs
   weekly selection).
4. **`+C1 +C2 +C3`** — add the vol-target governor.
5. **`+C1 +C2 +C3 +C4`** — add the DD-brake tail layer → the full candidate.
6. **`C5` alone** — falsification arm (§5), NOT part of the final candidate.

### 6.2 Interaction risks (RE stress view)

- **C1 + C3 double-shrink in mania (primary interaction risk).** Mania months are high-vol, so C3
  de-grosses the WHOLE book (including the mania-winning LONG leg) at the same time C1 cuts the
  short leg. The concern is C3 clipping the winning long leg in mania. **Bounded** because C3 is
  deliberately mild (max_lev=1.0, ~12% mean de-gross) — but the QE should watch the long-leg
  contribution in 2021-Q1 / 2024-Q4 across the `+C3` variants. If the long leg is materially
  clipped there, consider max_lev slightly >1 in calm or exempting C3 from firing when C1 is
  already engaged.
- **C1 + C2 over-de-risk the short leg in mania → directional net-long.** Both cut short exposure
  when mania is broad. Combined, the short leg runs ≈ `0.5 × (1 − 0.056) ≈ 0.47×` in flagged broad
  manias — the book becomes net-long by roughly half the long budget. If a broad mania V-reverses
  to a crash with no roll-over (§1.6), this is the exposure that bites. Mitigations already baked
  in: C1 floor 0.5 (not 0), C2 touches only the extreme 5.6% tail, and C4 provides an own-equity
  backstop. Flagged as the top tail risk to watch in the matrix.
- **C3 is ACTIVE on `midvol_short`** (unlike RISK-004's `longbias_ls`, where VT was structurally
  inert because that builder reads `gross_long`/`gross_short` directly). /005 uses `midvol_short`,
  which goes through `g = gross * scale * book_scalar`, so `vol_target_ann` genuinely bites here.
  QE should confirm this in the `+C3` forensic (`book_scalar_series` / mean gross < 1.0).
- **C4 + C1 compound after a squeeze** (both de-risk once a mania squeeze has drawn the book down).
  This is *desirable* (post-squeeze de-risk) and low-risk; note only that it can delay re-entry
  into the recovery month — the reason C4 scale is 0.5, not 0.0.

---

## 7. Leak-safety summary (all controls)

| control | inputs | past-only argument | consumed |
|---|---|---|---|
| C1 | `close_BTC[t-63..t]`, member returns `close[t-21..t]`, funding `[t-21..t]`, 365-z | all rolling/trailing windows end at `t`; no forward read | `gate[k-1]` at rebal `k` |
| C2 | `close_i[t-21..t]` per name | trailing return known at `close[t]` | selection at `k-1` |
| C3 | trailing realized rets `[k-45..k-1]` | `_vol_target_scale` uses `past_rets` only | scale at `k` from past |
| C4 | own equity `[0..k-1]`, causal running peak | brake reads `equity[k-1]` (last realized) | at rebal `k` |
| C5 | `close_BTC[t-540..t]` rolling max | `btc_drawdown_scalar` positive-control leak test in `test_blind_engine.py` | `scalar[k-1]` |

Every gate value at index `t` uses only data `≤ close[t]`; the engine consumes it at `[k-1]`
(decide at `close[k-1]`, fill at `open[k]`) — the standard one-candle decision lag matching
`signal[k-1]`. No control reads a forward price, a future funding settle, or an OOS candle.

---

## 8. Position-sizing note (portfolio-level, consistent with RISK-004)

/005 IS Sharpe ≈ 0.91, ann vol 29.5% → full-Kelly gross ≈ 1.05× (Sharpe/vol). This is a
moderate-edge book, not a lever-up candidate: crypto fat tails make the Kelly point fragile to
vol mis-estimation, so a ½-Kelly deployment (~0.5× gross, or ~50% of NAV in the book) is the
prudent live sizing. The risk overlay above (C1 short cut, C3 max_lev=1.0, C4 brake) is a partial
substitute for lower baseline gross — it auto-de-risks in the two regimes (mania squeeze, deep DD)
where the fat-tail loss concentrates — but it does not license running above ~1.0× gross.

---

## Files touched (all within blinding)

- `analysis/portfolio/blind_risk_calib_006.py` — NEW. Reproduces /005 (parity + leg recon),
  builds all five controls, prints every table above. Reads only `blind_*` modules. OOS never
  inspected; no strategy-Sharpe scan.
- `diary-portfolio-blind/RISK-006.md` — this file.

No baseline-artifact reads (`BASELINE_PORTFOLIO.md`, `iter_*.py`, `diary-portfolio-top20/`, sibling
worktrees). No `CONFIRMATION-005.md` read. No commits. OOS sealed at 2025-03-24.
