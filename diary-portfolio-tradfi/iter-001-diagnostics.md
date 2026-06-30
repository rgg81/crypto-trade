# iter-001 diagnostics — IS-ONLY forensic (BUG vs REAL NEGATIVE)

**Track:** portfolio-tradfi · **Cadence:** EXPLORATION (IS-only, `< OOS_CUTOFF 2025-03-24`; OOS HIDDEN)
**Anchor:** dollar-neutral XS-momentum 12-1m, `analysis/portfolio/tradfi/iter_001_xsmom.py` (UNCHANGED)
**Diag script:** `analysis/portfolio/tradfi/iter_001_diag.py` (read-only; reuses `core_tradfi.net_from_raw`)
**Headline:** `IS_Sharpe=-0.30  maxDD=-53.8%  netTot=-40%` over 39 ingested names (GOOGL/ORCL/GLW failed Dukascopy fetch — 39 of 42).

**Engineering read: REAL NEGATIVE — not a sign/code bug.** (Promotion verdict is the QR's call; per brief §3 this lands in the `≤ +0.10` REJECT-direction-as-specified tier.) One load-bearing DATA caveat flagged below for the QR (calendar-day weekend padding) — it degrades signal quality but does NOT flip the sign, so it is a recommendation, not a BLOCK.

---

## 0. Data grain — calendar-daily, weekend-padded (load-bearing caveat)

| Property | Value |
|---|---|
| Bars/year (IS) | ~365–366 (NOT 252 trading days) |
| Weekend bars | 886 in AAPL, **100% flat OHLC, zero volume** |
| Zero-return-bar fraction (IS, mean/name) | **28.7%** (≈ weekend share 2/7) |

Consequence: `shift(252)` is **~8.3 calendar-months**, not 12; `shift(21)` ≈ 3 weeks; `rolling(63)` rvol spans ~29% flat weekend days (deflates realized vol → distorts inverse-vol cross-name scaling and the `√252` vol-target). The pre-registered "canonical 12-1m / 252-21-63 trading-day spec" is therefore **not actually being tested** — what ran is an off-spec ~8.3m-minus-3wk formation. Not a BLOCK (it does not flip the sign — see §4 — and the whole track shares this grain), but a strong candidate axis for a future iteration to re-spec windows in trading-day units (mask weekends, or `shift(365)/shift(30)`).

## 1. Breadth (non-NaN signal names per month, IS)

| min | median | max | first month ≥20 active | months <20 |
|---|---|---|---|---|
| 0 | **34** | 39 | **2018-09** | 8 (the pre-warmup months Jan–Aug 2018) |

Healthy from late-2018. (Note: calendar-day grain makes the 252-bar warmup land ~2018-09, faster than the brief's trading-day assumption of ~mid-2019.) Cohorts: 30 names from 2018-01; ZM/UBER/PLTR 2020-10; DELL/HPE/COHR/MRVL/NOW 2022-05. **Not degenerately thin.**

## 2. Book sanity (lagged weight book `w`, IS) — DEGENERATE: NO

| gross Σ\|w\| | \|row-sum\| (dollar-neutral) | max name / gross | long ct | short ct |
|---|---|---|---|---|
| **1.000** | mean 1.0e-16 / max 9.0e-16 | mean 11.0% / **max 22.0%** (<25%) | ~16.5 | ~17.2 |

Gross ~1.0, dollar-neutral to machine epsilon, no concentration pathology (max single name 22% < 25% threshold), balanced L/S. The book is **well-formed** — the negative is not an accounting/concentration artifact.

## 3. Regime / year decomposition (IS) — where the loss lives

| Regime | Sharpe | months | | Year | Sharpe |
|---|---|---|---|---|---|
| bull | **-0.41** | 70 | | 2019 | **-2.09** |
| bear | **-0.81** | 12 (COVID + early-2022) | | 2021 | **-1.18** |
| chop | **+0.60** | 8 | | 2022 | **+0.66** |
| | | | | 2020 | +0.56 |
| cost drag | gross **-0.14** → net **-0.30** | | | 2023 | -0.34 |
| worst IS month | **2023-03  -15.4%** (SVB / regional-bank reversal) | | 2024/25 | +0.33 / +0.82 |

The loss is **broad-based**, not a single-regime artifact: the biggest drags are the **bull-tagged years 2019 (-2.09) and 2021 (-1.18)**, plus the bear bucket (COVID-2020 + choppy early-2022). Notably the **2022 calendar year was +0.66** — momentum *worked* in the 2022 bear, contrary to the brief's worry that 2022 would be the risk; the "bear -0.81" bucket is dominated by the COVID-2020 crash/rebound. Worst single month is **2023-03 (-15.4%)**, a textbook momentum-crash reversal (regional-bank panic). Cost is real but secondary: **gross is already -0.14**, so this is signal-driven, not cost-driven.

## 4. Sign / lookback robustness (diagnostic characterization ONLY — anchor stays 252/21/63)

| Config | IS_Sharpe |
|---|---|
| anchor 12-1m (252/21/63) | **-0.30** |
| **NEGATED** −anchor | **-0.03** |
| alt 6-1m (126/21/63) | -0.04 |
| alt 3-1m (63/21/63) | -0.54 |

Decisive on BUG-vs-REAL: **negating the signal gives ≈ 0 (-0.03), not +0.30** → there is **no hidden positive edge from a flipped sign** (this is NOT a reversal-vs-momentum sign error). The negative is a **robust property of the momentum neighborhood** (every lookback ≤ 0), not a single-config knife-edge.

## 5. Sector / beta exposure (tests the QR's concentration hypothesis)

- **Realized net market-beta** (book vs equal-weight universe, IS): **-0.011** — already ~beta-neutral on average despite being only dollar-neutral.
- **Net sector tilts** (fraction of ~1.0 gross): all small — Health **+0.034** (1-name artifact: only LLY of LLY/NVO/HIMS is ingested), ConsDisc -0.033, Semi -0.027, ConsStap +0.027, Fin +0.019, Tech -0.015, Comm -0.005. **Largest = Health +0.034 (≤3.4% of gross).**

This **only weakly supports** the QR's hypothesis that sector/beta concentration drives the loss: the *time-average* net beta is ~0 and net sector tilts are all ≤3.4% of gross, so a **persistent** beta/sector bet is NOT the driver. iter-002 (beta-neutral) / iter-003 (sector-neutral) are therefore unlikely to rescue the *average-case* −0.30 — though they may still help the *tail* (e.g. 2023-03, where instantaneous beta spikes at a crash onset). The likelier structural driver: the 39-name universe is **62% Semi+Tech (24/39)**, so a dollar-neutral momentum book is mostly making **intra-sector bets among highly-correlated names** (Semi-vs-Semi, Tech-vs-Tech), where the cross-sectional momentum spread is thin/noisy — compounded by the off-spec calendar-day formation window (§0).

---

## Interpretation (BUG vs REAL NEGATIVE)

The −0.30 is a **real negative, not a bug**: the book is well-formed (dollar-neutral to 1e-16, gross ~1.0, max single name 22% < 25%, breadth median 34, balanced ~16L/17S); gross Sharpe is already −0.14 so cost is secondary not causal; and negating the signal yields ≈ 0 (−0.03), not +0.30, so there is no sign error masking a positive edge. The loss is **broad-based** — worst in the bull-tagged years 2019 (−2.09) and 2021 (−1.18) and the COVID/early-2022 bear bucket — while 2022 itself was +0.66, so this is *not* a 2022-bear failure and *not* a single-regime artifact. The QR's sector/beta-concentration thesis is only **weakly** supported (realized beta ≈ 0, largest net sector tilt +3.4%), pointing instead at a thin/noisy cross-sectional momentum premium on a **Semi+Tech-dominated (62%) correlated universe**, plus a **calendar-day data grain** that silently mis-specifies the canonical 12-1m window as ~8.3m. **Recommendation for the QR** (one change per iteration): the most leveraged next axes are (a) re-spec the formation/vol windows in trading-day units (mask weekend pads), and/or (b) broaden/de-concentrate the universe (ingest the 3 failed names, reduce Semi+Tech dominance) — both more promising than the beta/sector overlays for the *average-case* loss, which the exposure numbers do not implicate.
