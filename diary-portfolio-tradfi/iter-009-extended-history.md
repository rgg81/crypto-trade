# iter-009 — EXTENDED-HISTORY VALIDATION (2018 → 2010 IS; 2 bears → 5 bears)

**Date:** 2026-07-01 · **Track:** portfolio-tradfi · **Role:** Quant Engineer
**Cadence:** EXPLORATION / data-expansion + validation (IS-only, `< OOS_CUTOFF 2025-03-24`; **OOS HIDDEN** — no `--confirm`, no OOS number computed). **NO new strategy** — only the data window + the regime tags changed (a pre-registered measurement-period extension).
**Motivation:** the momentum book's bear behaviour + the iter-008 VIX brake were validated on only **2 in-sample bears** (COVID + 2022). Extend IS back to 2010 to bring **3 more documented bears** (2011, 2015-16, 2018-Q4) into the test and re-validate.
**Sources of truth (every number):** `analysis/portfolio/tradfi/iter_006_crashbrake.py`, `iter_008_vix_stop.py`, and the new `iter_009_per_bear.py` (all IS-only). Reproduce: `uv run python analysis/portfolio/tradfi/iter_009_per_bear.py`.

---

## 1. What changed (data + tags only — signal/gate/band/cost/overlays UNCHANGED)

1. **Yahoo re-ingest from 2010-01-01** (`ingest_yahoo.py` default start pushed 2018 → 2010; `auto_adjust=True` total-return, native trading-day calendar). 69/69 names ingested, 0 failed. **42 names carry full 2010 history** (4147 bars each through 2026-06-30, ≈3828 of them IS); recent IPOs stay **ragged / point-in-time** (PLTR 2020, COIN 2021, HOOD 2021, RIVN 2021, ARM 2023, ALAB/NBIS 2024, CRCL/SNDK 2025 …) — NaN before listing → 0 weight, leak-safe. **^VIX** extended to 2010 (4148 bars). IS totals: **union trading-day grid = 3828 rows** (2010-01-04 … 2025-03-21); 195,914 name-bars IS.
2. **Regime tags extended** (`core_tradfi._REGIMES`): the **2020+ COVID/2022/chop/bull tags are BYTE-IDENTICAL** (comparability); **3 pre-2020 bears ADDED**, macro-anchored (S&P peak→trough + named catalyst), pre-registered in a comment, **not tuned to P&L**:
   - **2011** debt-ceiling downgrade / EU sovereign : `2011-07-22 → 2011-10-03`
   - **2015-16** China deval / oil crash / growth scare : `2015-08-17 → 2016-02-11`
   - **2018-Q4** Fed tightening / QT selloff : `2018-10-01 → 2018-12-24`
   - intervening calm = bull; documented transitional recoveries (into the 2012 spring low / 2016 US election / 2019 post-trade-war low) = chop.
3. **Guards still green.** Split-unadjustment regression guard (the test that would have caught the Dukascopy bug) + all 44 tradfi tests **PASS** on the longer, split-heavier data (auto_adjust cleanly removes AAPL 7:1 2014, 4:1 2020; AMZN 20:1; NVDA 4:1/10:1; TSLA 5:1/3:1 — no name single-bar-collapses below the −0.65 floor). Change is isolated to the tradfi track (only `test_portfolio_tradfi_foundation` imports `core_tradfi`).

## 2. Full-IS effect (2010-2025 vs the 2018-only anchors)

| build | net (2018-only) | **net (2010-25)** | bull | bear | chop | maxDD |
|---|---|---|---|---|---|---|
| **iter-006** (crash gate) | +0.43 | **+0.28** | +0.30 | **−0.24** | +0.51 | −29.2% |
| **VIX brake ALONE** | +0.41 | **+0.23** | +0.22 | **−0.09** | +0.46 | −29.1% |

Two things move on the longer window: **(a)** headline net drops (+0.43 → +0.28) — the 2018-2025 slice was a uniquely strong mega-cap-tech momentum era; the 2010-2018 extension dilutes it to a more honest, still-**positive** +0.28. **(b)** The **aggregate bear collapses from −1.23 (2-bear) to −0.24 (5-bear)** — the "catastrophic bear" was largely a **COVID+2022 concentration artifact**, not a structural property of the book.

## 3. PER-BEAR TABLE — the key deliverable (iter-006 base → VIX-alone)

| bear | iter-006 Sh / ret% | VIX-alone Sh / ret% | VIX fired? (mean/min/frac<1) | did VIX help? |
|---|---|---|---|---|
| **2011** debt-ceiling | **+0.85 / +2.7%** | +1.29 / +2.8% | yes (0.63 / 0.50 / 94%) | **help** (DD −7.7→−4.2%, ret flat) — momentum already WON |
| **2015-16** China/oil | **+1.39 / +9.6%** | +1.03 / +7.1% | yes (0.92 / 0.50 / 48%) | **mild drag** (−2.5pp; trimmed a winning bear) — momentum WON big |
| **2018-Q4** Fed | **−2.75 / −6.1%** | −2.51 / −6.1% | yes (0.94 / 0.70 / 52%) | **no help** (−0.0pp, DD flat) — fast selloff, VIX under-fired |
| **COVID** V-crash | **−3.65 / −10.6%** | −7.89 / −7.1% | yes (0.60 / 0.50 / 87%) | **big help** (ret +3.5pp, DD −14.4→−9.1%) — VIX spiked ~82 |
| **2022** grind | **−0.38 / −2.5%** | +0.26 / +0.6% | yes (0.79 / 0.55 / 89%) | **help** (ret +3.1pp, turned +ve, DD −13.0→−9.2%) |

*(COVID Sharpe is on ~1.5 months / ~2 monthly points → unreliable; read its return + maxDD. The VIX brake reduced the COVID dollar loss and drawdown even though the 2-point Sharpe prints worse.)*

**Read:** the VIX brake is **insurance** — it pays in the bears momentum LOSES (COVID, 2022, and it shallows 2011's DD) and costs a little in the bears momentum WINS (2015-16). Exactly the asymmetry a crash brake should have. The one clean **miss is 2018-Q4**: momentum lost −6.1%, VIX de-levered only modestly (mean 0.94, min 0.70 — the selloff was fast and VIX topped ~36, not the 82 of COVID), so the brake neither helped nor hurt.

## 4. Headline answers

- **Does the momentum edge HOLD across 2010-2025?** **YES, but weaker and honest.** Net **+0.28** (positive), chop strong **+0.51**, bull **+0.30**. Crucially the **5-bear aggregate bear is only −0.24** (not the alarming −1.23) and momentum was **outright PROFITABLE in 2 of the 5 bears** (2011 +2.7%, 2015-16 +9.6%). The book's "bear problem" is specifically the **sharp momentum-reversal crashes** (COVID V, 2022 grind, 2018-Q4 Fed), not bear markets in general.
- **Does the VIX bear-control GENERALIZE across 5 bears (or was the 2-bear result a coincidence)?** **QUALIFIED YES — not a coincidence, not a universal fix.** The brake **fired in 5/5** and **helped in 4/5** (materially in COVID +3.5pp and 2022 +3.1pp — the 2 originals — plus shallowed 2011's DD; a mild drag on the winning 2015-16). Its efficacy is **conditional on VIX actually spiking**: it delivered in the high-VIX sustained crises but **whiffed on the fast, moderate-VIX 2018-Q4 Fed selloff**. Aggregate-bear direction holds on the bigger sample (−0.24 → −0.09, Δ+0.15) at a small net cost (+0.28 → +0.23). So the 2-bear bear-fix was **directionally real, but its magnitude was over-stated by the COVID/2022 concentration** — the extended sample re-prices it as modest, VIX-spike-gated insurance rather than a blanket bear cure.

## 5. Leak safety / OOS

- **OOS HIDDEN** — every metric on the IS slice only (`< 2025-03-24`); data on disk extends to 2026-06-30 but is never read past the cutoff. No `--confirm` path exercised.
- Ragged/point-in-time starts are leak-safe (NaN → 0 weight before listing). VIX brake `.shift(1)` + past-only ffill; both iter-006 and iter-008 **future-bar leak self-checks PASS** on the 2010 panel; 44/44 tradfi tests green.

## 6. Concern / handoff

The headline is a **downgrade of confidence, honestly earned**: the 2018-only +0.43 was flattered by one exceptional momentum regime, and the VIX brake's bear-fix was inflated by only having COVID+2022 in sample. The extended read is a **still-positive but pedestrian momentum book (+0.28)** whose bears are survivable on average, plus a **VIX brake that is genuine but VIX-spike-conditional insurance** (fails fast/shallow-vol selloffs like 2018-Q4). **Open risk for QR:** the strategy's real tail is the *sharp momentum-reversal* class, and VIX only covers the subset of those that come with a vol explosion — 2018-Q4 shows a fast Fed-driven reversal can slip under a VIX=20/floor=0.50 brake. No parameter was re-tuned to fix this (that would be curve-fitting to the newly-revealed bear); flagged for QR to decide whether a second, faster de-risk trigger is warranted — a **strategy decision, not an engineering one**.
