# iter-005 BRIEF — Multi-horizon within-sector momentum blend

**Date:** 2026-07-01 · **Track:** portfolio-tradfi · **Cadence:** EXPLORATION (IS-only, `< OOS_CUTOFF 2025-03-24`; **OOS HIDDEN**)
**Working best entering iter-005:** iter-003 (`analysis/portfolio/tradfi/iter_003_hysteresis.py`) — net **+0.16** / gross **+0.29**, bull +0.22 / bear −0.08 / chop −0.10 (**1/3** regimes), maxDD −32.8%.
**Probe (single source of truth for every number below):** `analysis/portfolio/tradfi/iter_005_probe.py` (READ-ONLY; banded δ=0.005, identical to iter-003, for apples-to-apples). Reproduce: `uv run python analysis/portfolio/tradfi/iter_005_probe.py`.

---

## 1. Why iter-003 is bull-only AND gross-capped (deep read, IS numbers)

iter-003's signal is a **single momentum speed** — within-sector 12-1m (`close.shift(21)/close.shift(252)-1`), inverse-vol scaled, sector-demeaned. Two structural facts cap it:

**(a) Gross ceiling +0.29 is a single-speed limit.** A single momentum horizon is a single bet on one persistence timescale. The probe shows the universe is momentum-persistent at MULTIPLE, imperfectly-correlated speeds:

| within-sector sleeve (banded δ=0.005) | net | gross | bull | bear | chop |
|---|---|---|---|---|---|
| 12-1m (= iter-003) | +0.16 | +0.29 | +0.22 | −0.08 | −0.10 |
| 3-1m (63/21) | +0.03 | **+0.32** | +0.39 | −1.23 | −0.84 |
| 6-1m (126/21) | −0.09 | +0.08 | −0.13 | −0.80 | +0.90 |
| fast 1m (no skip) | −0.15 | +0.31 | −0.13 | −2.31 | +1.60 |

IS net-return correlations: ρ(3-1,12-1)=**+0.47**, ρ(6-1,12-1)=+0.59, ρ(fast,12-1)=**+0.21**. The 3-1m sleeve has gross +0.32 (as strong as 12-1m) and is only ~0.47-correlated to it — **a second, decorrelated source of the same edge that iter-003 leaves on the table.** A single horizon cannot harvest it.

**(b) Bull-only is a chop-timing problem, not a sign problem.** 12-1m momentum needs trend persistence + cross-sectional dispersion (present in bull, collapses in chop). The 12-1m sleeve is chop −0.10; but the **shorter** sleeves earn precisely in chop (6-1m chop +0.90, fast chop +1.60) — chop favors faster mean-reversion-adjacent momentum. iter-003 has no exposure to that timescale, so it sits out the one regime it loses.

**Conclusion:** the binding constraint is *signal breadth across momentum speeds*, not cost (already harvested by the band) and not neutralization (β≈0, sector tilt≈0 per iter-001 diag §5). The lever is **multi-horizon diversification.**

## 2. The ONE change for iter-005 (exact spec — implement verbatim)

**Replace the single 12-1m momentum signal with an EQUAL-WEIGHT blend of within-sector momentum at three speeds {3-1m, 6-1m, 12-1m}. Everything downstream (the iter-003 hysteresis band δ=0.005, `net_from_raw`, vol-target, OOS-hidden accounting) is UNCHANGED.**

```python
close = pn["close"]
rvol  = close.pct_change().rolling(ct.VOL_WIN).std()          # 63d realized vol (UNCHANGED)
def sleeve(lookback):                                          # skip = 21 (1-month), UNCHANGED
    raw_h = (close.shift(21) / close.shift(lookback) - 1.0) / rvol
    raw_h = nz.sector_neutralize(raw_h, ut.SECTOR_MAP)         # per-sector demean (UNCHANGED primitive)
    g = raw_h.abs().sum(axis=1).replace(0, np.nan)             # unit-gross-normalize each sleeve
    return raw_h.div(g, axis=0).fillna(0.0)                    #   so no sleeve dominates by scale
raw = (sleeve(63) + sleeve(126) + sleeve(252)) / 3.0          # EQUAL-WEIGHT multi-horizon blend
net, w = i3.banded_net(raw, ret_fwd, delta=0.005)             # iter-003 path, UNCHANGED
```

- **δ stays 0.005** (inherited from iter-003). Sweep on IS confirms {0.005, 0.0075} is the stable basin (net +0.20/+0.21); δ=0.02's +0.23 is a non-robust spike across the δ=0.01 collapse valley (net +0.15) → REFUSED, exactly as iter-003 refused δ=0.03. **No OOS tuning; the band is not re-optimized.**
- **Pre-registered IDENTITY check:** a degenerate one-sleeve blend `sleeve(252)` (gross-norm of a single sleeve = the sleeve) through `banded_net(...,0.005)` must reproduce iter-003 net **+0.16** bit-for-bit. The QE must add a future-bar leak test (corrupt inputs after a cutoff → past net + lagged book bit-identical) mirroring `test_iter003_banded_future_bar_no_leak`; it passes trivially because the blend is a row-wise linear combination of leak-safe sleeves.
- **Equal-weight, NOT risk-parity** (pre-registered, see §4): inverse-sleeve-vol parity over-weights the weak 6-1m sleeve and collapses net to −0.07..+0.05.

## 3. Pre-registered IS success criteria + winning probe numbers

**Winning candidate `EW{3-1,6-1,12-1}` vs iter-003 (+0.16), banded δ=0.005, IS-only:**

| metric | iter-005 EW{3-1,6-1,12-1} | iter-003 (12-1m) | Δ |
|---|---|---|---|
| **net Sharpe** | **+0.20** | +0.16 | **+0.04** |
| **gross Sharpe** | **+0.40** | +0.29 | **+0.11** |
| cost drag | +0.20 | +0.13 | +0.07 |
| **bull / bear / chop** | **+0.38 / −0.90 / +0.26** | +0.22 / −0.08 / −0.10 | bull+chop up, bear down |
| **regimes positive** | **2/3** (bull+chop) | 1/3 (bull) | **+1** |
| turnover/day | 0.114 | 0.061 | +88% |
| maxDD (IS) | **−31%** | −33% | better |

**Pre-registered bar (QR brief, unchanged across the arc):**
- net ≥ **+0.30** = promotable; +0.50 = healthy.
- all-weather = positive in ≥**2/3** regimes, no catastrophic regime.
- net > **+1.0** = **assume-leak**, not a win. (Blend is +0.20 — far from leak territory; sanity-confirms the change is signal, not artifact.)

**This iteration's pre-registered verdict logic:** EXPLORATION step. It does NOT clear the +0.30 promote bar (net +0.20) — it is **PROMISING-INTERMEDIATE** if it reproduces: it advances BOTH binding problems (gross +0.29→+0.40; all-weather 1/3→2/3) while improving maxDD. It is **not** a baseline-promote.

## 4. Pre-registered FAILURE mode (honest, before the QE runs)

The bear regime **genuinely deepens** — and this is the known cost, decomposed so it can't be rationalized away post-hoc:

| | COVID (2020-02..04, ~2mo) | 2022 bear (~10mo) |
|---|---|---|
| iter-003 12-1m | Sh −0.80, tot −2% | Sh **+0.10**, tot −0% |
| iter-005 EW{3-1,6-1,12-1} | Sh −1.94, tot −4% | Sh **−0.73**, tot **−11%** |

The bear loss is **NOT** purely a 2-month COVID artifact: the 2022 grind-down bear flips +0.10 → −0.73 (−11%) because the fast 3-1m sleeve crashes in sustained reversals (classic momentum crash). **FAILURE = REJECT and keep iter-003** if the QE's clean re-implementation shows ANY of: (i) net ≤ iter-003's +0.16; (ii) all-weather count ≤ 1/3 (chop falls back negative); (iii) gross < +0.35 (the diversification lift evaporates under a clean build); (iv) bear < −1.3 AND net < +0.18 (the crash overwhelms the bull/chop gains). The bet — pre-registered — is that bull(+0.22→+0.38) + chop(−0.10→+0.26) + gross(+0.40) + maxDD(−31%) outweigh the deeper bear, and the all-weather *count* (the stated criterion) improves 1/3→2/3. If iter-005 reproduces, **iter-006's binding regime becomes BEAR**, and the natural next single-change is a momentum-crash brake conditioned on fast-sleeve / trailing-vol state (the deepened bear is the lever, now isolated).

## 5. Why this beats every other candidate (all probed, all IS-only)

| candidate | net | gross | regimes | verdict |
|---|---|---|---|---|
| **EW{3-1,6-1,12-1} (CHOSEN)** | **+0.20** | **+0.40** | **2/3** (bull+chop) | best gross + best all-weather count |
| EW{fast,3-1,6-1,12-1} | +0.23 | +0.39 | 2/3 | higher net BUT no-skip fast sleeve is unconventional (standalone net −0.15) + worst bear −1.21; less defensible — REJECT as overfit-leaning |
| EW{3-1,12-1} | +0.22 | +0.46 | **1/3** (chop −0.30) | highest gross but **loses all-weather** — the weak-standalone 6-1m sleeve is exactly what keeps chop positive |
| Residual (β-stripped) 12-1m | **−0.24** | −0.12 | 1/3 | within-sector demean already strips the common factor; market-residualization (ρ 0.84 to total) only adds noise — **destroys** the edge. REJECT |
| Low-vol complement (standalone) | **−0.76** | −0.71 | 1/3 | NOT positive-EV (helps only in bear +0.89); blending drags 12-1m to −0.62. REJECT — confirms iter-004 lesson (complement must be +EV) |
| Dispersion gate × iter-003 | +0.16 | +0.29 | 1/3 | **inert** — cross-sectional dispersion scaler barely leaves 1.0; adds no gross. WEAK |
| Risk-parity {3-1,6-1,12-1} | −0.07 | +0.11 | 2/3 | inverse-sleeve-vol over-weights the weak 6-1m → collapse. EQUAL-WEIGHT is correct |
| Universe de-concentration | — | — | — | not probed: iter-001 diag §5 already showed β≈0 / sector-tilt≈0, and within-sector demean makes Semi/Tech weight a *per-bucket* matter, not a portfolio tilt — low EV vs the signal-breadth lever |

Multi-horizon EW is the **only** change that simultaneously raises gross above the +0.29 ceiling (+0.40) and the all-weather count (1/3→2/3), with a better maxDD. Residual momentum and the low-vol complement — the two "obvious" textbook moves — both empirically FAIL on this universe; the probe earns those rejections rather than assuming them.

**Concern.** Net +0.20 is still under the +0.30 promote bar, and the bear regime turns genuinely negative (not just COVID). The change buys *robustness/breadth* (gross + all-weather count + maxDD) more than headline net; the promote-clearing net likely needs iter-006's bear-crash brake on top. Turnover nearly doubles (0.061→0.114/day) — drag rises to +0.20 — but the band keeps it in the stable basin and maxDD still improves, so this is acceptable cost-capture, not a churn artifact.
