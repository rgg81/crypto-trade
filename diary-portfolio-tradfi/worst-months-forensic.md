# Worst-Months Forensic — deployed iter-015 book (IS-only)

**Decision: DIAGNOSIS ONLY — no strategy change.** Adds `analysis/portfolio/tradfi/worst_months_forensic.py`
+ this write-up. Deployed book reproduced verbatim (IS Sharpe **+0.665**, matches BASELINE "+0.67").
Every read < `OOS_CUTOFF=2025-03-24`; data untouched; suite green (62+23 tradfi tests pass).

Deployed book = `(1−0.25)·[crash-braked multi-horizon XS-mom + 0.5·(3y−1y LTR)] + 0.25·TSMOM`,
band δ=0.010 / freq=1, VIX brake `s=clip(20/VIX[t-1],0.5,1)`, vol-target.

## 1. Worst IS months (deployed net monthly return)

| rank | month | net% | year | note |
|---|---|---|---|---|
| 1 | **2019-01** | **−10.77%** | 2019 | single worst month in all 15 IS years — ≈ the *entire* −11% year |
| 2 | 2024-05 | −10.62% | 2024 | GOOD year (+15%) — worst month ≠ worst year |
| 3 | 2017-11 | −9.84% | 2017 | good year — low-dispersion reversal |
| 4 | 2010-12 | −8.29% | 2010 | warm-up |
| 5 | 2023-01 | −7.90% | 2023 | good year — Jan reversal |
| 6 | **2018-10** | **−6.92%** | 2018 | Q4 QT crash (worst 2018 month) |
| 7 | 2011-08 | −5.87% | 2011 | 2011 crash (VIX 35–48) |
| 8 | **2019-09** | −5.49% | 2019 | 2019's second hit |
| 9 | 2012-01 | −5.18% | 2012 | reversal |
| 10 | 2020-03 | −5.13% | 2020 | COVID |

**Are 2018/2019 the worst?** As *years*, yes (2019 −11.1%, 2018 −7.3%, plus 2010 warm-up −9.1%). But
the single worst *months* are spread across GOOD years too (2024-05, 2017-11, 2023-01). **2019 is worst
because ONE brutal month (Jan-2019, −10.77%) is essentially the whole year**; 2018 is a grind of
moderate losses with a crash tail (Oct). The bad *years* are made by accumulation + one tail month, not
by a uniquely catastrophic monthly tail.

## 2. Per-sleeve attribution — the corrective finding

Attribution is EXACT-additive on the target (pre-band) book and reconciles to the deployed banded net
(mean |gap| 0.46%/mo, max 2.61%/mo at 2018-10 — band immaterial at δ=0.010). **The MONTH story and the
YEAR story differ, and both correct the coarse "net-long TSMOM tilt" narrative.**

**Single worst months (contribution to net monthly %):**

| month | net | XS-mom | LTR | TSMOM | cost | VIX | bled |
|---|---|---|---|---|---|---|---|
| 2018-10 | −4.3%* | **−4.4%** | +4.7% | **−4.2%** | −0.4% | −0.0% | XS-mom & TSMOM tie (LTR hedged) |
| 2019-01 | −10.1% | −3.5% | −2.4% | **−3.8%** | −0.7% | +0.2% | all three bled; TSMOM largest |

(*2018-10 attribution −4.3% vs deployed −6.9% — the one month where the band/vol-target gap is large;
sign & rank of the split are robust.)

**Full-year attribution (this is the corrective part):**

| year | net | XS-mom | LTR | TSMOM | cost | VIX |
|---|---|---|---|---|---|---|
| 2018 | −6.7% | **+5.9%** | **−8.6%** | +1.1% | −4.0% | −1.0% |
| 2019 | −10.5% | −2.0% | **−6.3%** | **+3.6%** | **−6.1%** | +0.3% |

**Over the full years, TSMOM (the directional beta) is NET POSITIVE both years (+1.1% / +3.6%).** The
dominant annual bleeders are (a) the **LTR / value-proxy sleeve** (−8.6% / −6.3%: the 2010-25 value
drought — shorting the 3y growth winners that kept ripping), and (b) **turnover cost** (−4.0% / −6.1%:
choppy reversal years churn the book; note this is the pre-band target-book cost — the deployed banded
cost is somewhat lower, but cost is clearly a first-order bleeder in the reversal years). The directional
beta only bites in the two crash/whipsaw MONTHS, not across the years. **The coarse "2018/2019 = net-long
TSMOM tilt" story is only right at the month level; at the year level it is the value sleeve + cost.**

## 3. Per-name attribution (worst 2018 + worst 2019 month)

**2018-10 (net −6.9%, EW-mkt −7.0%, dispersion 9.0%) — LONG the crashers:**
AMD −6.07% (LONG, own −40%), AMZN −2.63% (LONG, −20%), QCOM −2.17% (LONG, −13%), HD −1.22%,
COHR −0.91%, CRM −0.91% — every top loser is a **LONG in a momentum winner that crashed hardest** in the
QT selloff (the crowded 2018-H1 growth/semis longs). Broad (6 names each ≥ −0.9%), not one-name.

**2019-01 (net −10.77%, EW-mkt +8.7% UP, dispersion 10.1%) — SHORT the rippers:**
IBM −1.71% (SHORT, own +20.5%), META −1.46% (SHORT, +28.6%), BABA −1.38% (SHORT, +25.3%),
NVDA −1.31% (SHORT, +10.6%), EBAY −1.16% (SHORT, +22.1%), HPE −1.11% (SHORT, +21.2%) — every top loser
is a **SHORT in a 2018-loser that snapped back +10–29%** in the V-rebound. Classic momentum crash (prior
losers lead the rebound; the book is short them). Broad, not concentrated.

## 4. Regime type per worst month

| month | net | EW-mkt | disp | VIXmn/mx | win−los | type |
|---|---|---|---|---|---|---|
| 2019-01 | −10.8% | **+8.7%** | 10.1% | 20/26 | −3.2 | **MOMENTUM-REVERSAL (V-rebound; short the rippers)** |
| 2018-10 | −6.9% | **−7.0%** | 9.0% | 19/25 | −2.4 | **CRASH (directional-beta + long-momentum crash)** |
| 2011-08 | −5.9% | −4.6% | 6.6% | 35/48 | −3.8 | CRASH (VIX brake DID fire here) |
| 2020-03 | −5.1% | −9.3% | 10.8% | 58/83 | −2.7 | CRASH (VIX brake fired, +5.2% saved) |
| 2017-11, 2023-01, 2012-01, 2019-09 | | +0.4…+14% up | 6.6–16% | calm | strongly − | MOMENTUM-REVERSAL |

**VIX brake in 2018-Q4 — why it whiffed:** the Oct selloff started from a calm base — Oct VIX mean 19.4
(max 25.2) → brake scale mean **0.94** (min 0.79): essentially inert. It only bit in December (VIX
25–36 → scale to 0.55), after most damage. The brake is a *level* trigger; the Oct-2018 crash was a
*fast move from low vol*, which a 20-anchored VIX level can't catch in time. (Contrast 2011-08 / 2020-03,
VIX 35–83 — the brake fired and helped, e.g. +5.2% in COVID March.)

## 5. Mechanism diagnosis

**2018** — a **value-drought + cost-drag GRIND** with a **momentum-crash tail month**. Across the year the
LTR/value sleeve bled −8.6% (short the 3y growth winners in a growth-led tape) and churn cost −4.0%; XS-mom
(+5.9%) and TSMOM (+1.1%) were net *positive*. The −7.3% year was sealed by Oct: the QT crash hit the
crowded momentum LONGS (AMD −40%, semis) AND the TSMOM net-long beta simultaneously (−4.4% / −4.2%), and
the level-based VIX brake was too slow (calm base) to protect.

**2019** — a **single catastrophic momentum-crash month (Jan V-rebound)** on top of the same value-drought
+ churn. Jan-2019 alone (−10.77%) is the whole year: coming off the Dec-2018 bottom the book was SHORT
the 2018 losers (IBM/META/BABA/NVDA…) via cross-sectional momentum AND under-long/net-short via TSMOM
whipsaw, so when the market ripped +8.7% and the losers led (+10–29%), all three sleeves bled together.
TSMOM recovered to +3.6% for the full year, but the Jan hole + LTR −6.3% + cost −6.1% never came back.

**Unifying theme:** both bad years are **momentum-crash / trend-reversal events** (2018-Q4 crash of the
momentum LONGS; 2019-Q1 rebound of the momentum SHORTS) sitting on a **structural value/LTR drought** and
**turnover-cost drag** that bleed regardless of direction. Directional beta is a *secondary*, month-scoped
contributor — NOT the annual driver.

## 6. Improvement proposals (IS-probe evidence; NO change committed)

Baseline: IS +0.665, 13/16 yrs, 2018 −7.3%, 2019 −11.1%. `goodΔμ` = mean return-% change across the 13
good years (2010/2018/2019 excluded); a fix with `goodΔμ ≈ 0` that helps the bad years is generalizable.

| probe | IS_Sh | +yrs | Δ2018 | Δ2019 | goodΔμ | verdict |
|---|---|---|---|---|---|---|
| **A) TSMOM λ→0 in EW-252d bear-state** | **+0.73** | 13/16 | +0.4 | **+3.4** | **+0.62** | **WORTH AN ITERATION** |
| A) TSMOM λ→0.5λ in bear-state | +0.69 | 13/16 | −0.0 | +1.1 | +0.27 | gentler variant of A |
| A′) TSMOM λ→0 in EW-126d (faster) | +0.75 | 13/16 | +0.8 | +2.9 | +1.03 | strong but new free window (overfit risk) |
| B) VIX base 16 / 18 (more sensitive) | +0.63/+0.65 | 13/16 | −0.1/−0.2 | +0.8/+0.1 | **−1.50/−0.64** | **OVERFIT TRAP — reject** |
| C) realized-vol brake (21d, cap≤1) | +0.70 | 13/16 | **+1.5** | +0.4 | −0.26 | secondary; catches fast 2018-Q4 crash |
| D) global λ=0.15 / 0.10 | +0.57/+0.50 | 12/16 | −1.8/−1.9 | +0.3/−0.6 | −1.29/−2.20 | **reject — kills the melt-up benefit** |

### TOP CANDIDATE — A: gate the directional (TSMOM) sleeve to zero in the EW-universe bear-state
- **Mechanism:** when the EW-69 universe's trailing 252-day return is negative (`g[t]=1`), set λ→0 so the
  book goes fully market-NEUTRAL; keep λ=0.25 when the market's own trend is up. This is TSMOM's own
  "don't be net-long a downtrend" logic applied at the sleeve-WEIGHT level.
- **Effect:** IS **+0.665 → +0.73**, helps 2019 **+3.4%** and 2018 +0.4%, and `goodΔμ=+0.62` (it also helps
  post-bear recovery years — 2011/2012/2016/2020/2023). Melt-up years 2013/2017 are untouched (`g=0` in
  bulls → identity), so the directional benefit the tilt was ADDED for is preserved.
- **THEORY-GROUNDED / generalizable, ZERO new parameters:** `g[t]` is the *exact same* EW-252d bear-state
  already used by iter-006's crash brake (GATE_LOOKBACK=252) — no new window, no new threshold, sign-0
  boundary. It fires in all 5 IS bears + recoveries, not just 2018/2019. This is the cleanest lever.
- **Overfit flag: LOW.** Reuses an existing, theory-pinned gate; improves the aggregate Sharpe and 4 of 5
  bear-adjacent years, not a single event. Recommend as the next real iteration.

### SECONDARY — C: a realized-vol outer brake (catches the fast crash VIX misses)
- **Mechanism:** de-lever the net when trailing-21d realized vol exceeds its IS median (Barroso-Santa-Clara
  form), past-only, cap ≤ 1. Catches the *fast-from-calm* 2018-Q4 move the level-VIX brake missed.
- **Effect:** IS +0.70, 2018 **+1.5%** (its target), 2019 +0.4%, `goodΔμ=−0.26` (small good-year cost).
- **Overfit flag: MEDIUM** — the 21d window + median target are IS-calibrated; it's a genuine mechanism
  (realized-vol clustering) but softer edge than A. Could STACK on A (A fixes the trend-reversal exposure,
  C the fast-crash exposure). Lower priority; test only after A.

## 7. Overfitting traps to AVOID (respect the prior Critic BLOCK on 2-bear fitting)
- **B) A more-sensitive VIX brake (lower base 16–18)** to catch 2018-Q4: bleeds the good years hard
  (`goodΔμ −0.64…−1.50`) for negligible bad-year help — the classic N=1 fit to the 2018-Q4 moderate-VIX
  event. Rejected by evidence.
- **A′) A faster bear gate (126d)** — better headline numbers but introduces a NEW free window; the +2.9%
  on 2019 is *below* the theory-pinned 252d's +3.4%, and faster trend signals are exactly what iter-014
  found whipsaw on the 2018-crash/2019-recovery. Keep the parameter-free 252d.
- **A V-bottom TSMOM re-entry for 2019** (fast re-arm after the Dec-2018 low): would fit the single
  Jan-2019 rebound (N=1). NOT probed on purpose — proposal A achieves the 2019 fix *generically* by going
  NEUTRAL in the downtrend rather than trying to TIME the re-entry.
- **D) Cutting λ globally:** throws away the melt-up benefit (2018 gets WORSE, good years −1.3…−2.2). The
  directional sleeve is net-beneficial; the problem is only its state (net-long into a downtrend), which is
  exactly what the STATE-DEPENDENT gate A fixes and a global cut does not.

## 8. Concern
The value/LTR sleeve (−8.6% / −6.3%) and turnover cost (−4.0% / −6.1%) are the largest ANNUAL bleeders in
both bad years, yet proposal A (the strongest, cleanest lever) addresses the *directional/reversal
exposure*, not those two. A only lifts the bad years to ~−6.9% / −7.6% — it does not make them positive.
The LTR drought is structural (BASELINE already documents value dead 2010-25) and cutting LTR would hurt
the momentum-crash years it fixes (2013/2016/2023); the cost drag is intrinsic to trading momentum through
reversals. So A improves risk-adjusted return and the worst year, but 16/16 stays structurally unreachable
— the bad years shrink, they don't flip. Also note the 2018-10 attribution reconciliation gap (2.61%) is
the one place the additive split materially undershoots the deployed monthly loss; the sleeve RANK is
robust but the 2018-10 magnitude is the least-trustworthy cell in the table.
