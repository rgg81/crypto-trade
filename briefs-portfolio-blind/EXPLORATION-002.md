# EXPLORATION-002 — Mid-Vol-Decile Shorts (tail-capped near-neutral L/S)

## Section 0 — Provenance (pre-registration)

- **Frozen:** 2026-07-09, BEFORE any backtest run of this design. IS-only.
- **OOS sealed:** `OOS_CUTOFF = 2025-03-24`. Not looked at, not planned around.
- **Track:** baseline-blind top-20 L/S portfolio (this worktree).
- **Predecessors:**
  - `DIAGNOSTIC-001-signal-ic.md` — `vol_low` rank-IC +0.052, positive every year incl. mania (+0.068 in 2021), monotone across the cross-section.
  - `DIAGNOSTIC-002-engine-lowvol-sanity.md` — naive L/S −0.18 at rebal=6, 2021 −1.83 (short-side lottery blowup), 2022 +0.94 (shorts profit in bear). Funding pro-cyclical to short pain.
  - `briefs-portfolio-blind/EXPLORATION-001.md` — long-only tilt (FROZEN gates G1–G6).
  - `diary-portfolio-blind/EXPLORATION-001-engineering.md` — long-only result: Sharpe +0.56, MaxDD −87%, 2022 −1.53, funding drag +7216bps/~12%/yr (+37% in 2021).
  - `diary-portfolio-blind/REVIEW-001.md` — Critic CONDITIONAL-PASS; the three path-forward suggestions this brief weighs.
- **Blinding:** designed against `blind_engine.py` / `blind_universe.py` / `blind_funding.py` only. No baseline artifact read. OOS never inspected.
- **Blocking prerequisite:** the SHIB funding symbol-resolution fix (REVIEW-001 finding S1: `SHIBUSDT` klines vs `1000SHIBUSDT` funding — silent zero-funding subsidy) **MUST land in `blind_funding.py` before the QE runs this design.** Without it, any short book that touches 1000x-scaled low-price listings receives a silent funding subsidy, biasing the short-side alpha measurement. The fix is a symbol-resolution map + a post-`load_funding` assertion that every IS-universe member is `present`. The Critic's exact required fix is quoted in REVIEW-001 S1.

---

## Section 1 — Hypothesis (one sentence)

**Shorting only the mid-volatility band of the PIT top-20 (vol-ranks 11–15, never the extreme-vol tail at vol-ranks 16–20) while longing the lowest-vol half (vol-ranks 1–10), held near-dollar-neutral at gross=1.0, captures both the funding-tax dodge of dollar-neutrality (the short leg receives funding in mania when longs pay) and the drawdown-dampening of a short book in bear regimes (the naive L/S earned +0.94 in 2022 vs long-only's −1.53), without re-introducing the 2021 lottery-mooner blowup that destroyed the naive L/S — because the 10–100× parabolic moves are concentrated in the extreme-vol tail that this design skips by construction.**

---

## Section 2 — Chosen mechanism + crypto-native rationale

### The one change

**Replace the long-only equal-weight-lowest-vol-half builder with an asymmetric rank-based L/S builder that longs the lowest-vol half, shorts the mid-vol quartile, and skips the extreme-vol quartile.** Signal, universe, rebalance cadence, cost model, and funding are all held identical to EXPLORATION-001 so the Sharpe/drawdown/funding deltas are attributable solely to the weighting change.

In vol-rank terms within the PIT top-20 (vol-rank 1 = lowest realized vol):

| vol-rank band | n=20 count | position | weight each |
|---|---|---|---|
| 1–10 (lowest-vol half) | 10 | **LONG** | +0.05 (= gross_long/10 = 0.5/10) |
| 11–15 (mid-vol band) | 5 | **SHORT** | −0.10 (= gross_short/5 = 0.5/5) |
| 16–20 (extreme-vol tail) | 5 | **SKIP** | 0 |

Near-dollar-neutral: `sum(w) = 10×(+0.05) + 5×(−0.10) = 0`; `sum(|w|) = 0.5 + 0.5 = 1.0 = gross`.

### Why this Critic suggestion (not B or C)

The verified finding from EXPLORATION-001 defines the design problem as a **tension between two failures**:

1. **Funding tax.** Long-only pays ~12%/yr funding (+7216bps cumulative, +37% in 2021 alone). This is structural: longs pay positive funding in bull/manic regimes when the book is stressed.
2. **MaxDD / regime crash.** Long-only has no short hedge and eats the full 2022 correlated-deleveraging crash (−87% MaxDD, 2022 Sharpe −1.53). The naive L/S HAD a short book and earned +0.94 in 2022 — but that same short book blew up in 2021 (−1.83) because it shorted the 10–100× lottery mooners.

The Critic offered three axes. The selection rationale:

| suggestion | addresses funding tax? | addresses maxDD/regime? | mechanism count | verdict |
|---|---|---|---|---|
| **#1 mid-vol-decile shorts** | **YES** — near-dollar-neutrality: short leg receives funding in mania, offsetting long leg's payment (the worst year). Partial dodge (mid-vol funding < extreme-vol funding). | **YES** — short book dampens the 2022 crash (shorts profit when prices fall across the alt complex); skips the lottery tail that blew up 2021. | **ONE** — a single asymmetric rank-based partition into long/mid-short/skip. | **CHOSEN** |
| #2 signal-proportional + vol-floor cap | partially (neutrality if symmetric) | partially (continuous tail cap) | **TWO** — proportional weighting shape change + vol-floor cap are conflated; the brief's own scope-discipline deferred "weighting-shape optimization" to a later EXPLORATION. | rejected — two mechanisms, not one |
| #3 regime-aware gross scalar | **NO** — a gross scalar scales position size but does not change the long/short balance; a long-only book still pays funding on whatever gross it runs | yes (de-risks in turbulent regimes) | one — but addresses only the subordinate failure | rejected — leaves the dominant funding failure untouched |

**#1 is the only suggestion whose single mechanism honestly addresses BOTH failures.** The mid-vol partition is a single rank-based builder (one code path, two fractions with a principled cutoff). It adds the funding-tax dodge (via near-neutrality) AND the crash dampening (via a short book that skips the tail) in one change.

**Why not #3 (regime scalar):** the task explicitly asks: "does the chosen mechanism address BOTH the funding tax AND the maxDD/regime? If a single mechanism can't do both honestly, say so." A gross scalar demonstrably cannot address the funding tax — it scales a long-only book's size but the per-dollar funding rate is unchanged. It would leave the +12%/yr structural drag intact while only helping the drawdown. Since the funding tax is a verified, economically-large failure (it consumed ~98% of the long-only book's gross price P&L over IS), leaving it untouched is not acceptable for the dominant failure. #3 is deferred to EXPLORATION-003 as a candidate if #1 fixes the funding but not the drawdown.

### Crypto-native rationale for why mid-vol shorts should work

1. **Lottery preference is tail-concentrated, not uniform.** The retail overpayment for positive skewness (Blitz; Baker-Hauger; amplified in crypto per BIS WP 1087, 2025) is not evenly distributed across the high-vol cohort — it is concentrated in the **extreme right tail**: the 10–100× mania mooners (DOGE 2021, SHIB 2021, PEPE/BONK/FLOKI 2023–24). These are the names where coordinated retail FOMO + leverage-driven liquidation cascades drive parabolic short-squeezes. The mid-vol band (vol-ranks 11–15) consists of established but moderately volatile alts — mid-cap L1 tokens, older DeFi protocols with real usage — that attract far less degen-flow. Shorting them captures the monotone cross-sectional IC edge (high-vol underperforms low-vol, DIAGNOSTIC-001 +0.052, stable every year) **without taking the lottery-tail risk that lives in vol-ranks 16–20**.

2. **Funding rates scale with retail hype — mid-vol is the moderate regime.** Extreme-vol names carry the most positive funding in mania (retual retail pays up to hold leveraged longs in the hottest names — 2021 market average +0.0112%/8h, but the mooners were far higher). Mid-vol names have moderate funding. So the mid-vol short still **receives** funding income in mania (a partial dodge of the long leg's payment), but less than shorting the extreme tail would. This is the deliberate tradeoff: **give up some mania-year funding income to avoid the price blowup.** The Critic's data confirms the direction: in 2021 the rank-neutral L/S EARNED −142.6bps funding (short leg received more than long leg paid) while the long-only PAID +3722bps.

3. **Deleveraging cascades are correlated across the entire alt complex, not just the tail.** In 2022 (Luna/3AC/FTX), the correlated deleveraging hit everything — majors fell 70–90%, mid-caps fell similarly. The mid-vol short profits here because mid-vol names fall alongside the rest of the market. The naive L/S earned +0.94 in 2022 precisely because its short leg captured this broad-based decline. The mid-vol book's short leg should capture the same effect — mid-vol names are not immune to bear-market deleveraging.

4. **The IC's monotonicity is the principled cutoff — no threshold tuning.** DIAGNOSTIC-001 showed the rank-IC is positive and **monotone** across the entire cross-section (+0.052 overall, rising to +0.076 in 2025Q1). The mid-vol band is the "safe" portion of the high-vol cohort — it captures the IC's monotone prediction (high-vol underperforms low-vol) without the fat-tail breakdown that plagues the extreme decile. The cutoff at `short_frac = 0.25` (the middle quartile of the universe, = vol-ranks 11–15 of 20) is parameter-free: it is the natural midpoint of the high-vol half, pre-registerable without reference to any backtest result. No vol-band threshold was scanned to find it.

5. **The null is crypto-structurally informative.** If mid-vol shorts STILL blow up in 2021 (Sharpe < −1.0), it means the lottery-mooner risk is not concentrated in the extreme tail but is a **broader high-vol-cohort phenomenon** — retail FOMO and liquidation cascades (BIS WP 1087) propagate further down the vol distribution than the extreme-decile framing suggests. That would be a genuine structural finding, pointing away from tail-capping and toward a regime-gate (EXPLORATION-003, Critic suggestion #3) as the only viable defense.

---

## Section 3 — Exact implementation spec (for the quant-engineer)

### 3.1 Signal (UNCHANGED from EXPLORATION-001 / DIAGNOSTIC-002)

```python
def lowvol_signal(panel, window=12):
    ret = pd.DataFrame(panel.close).pct_change().to_numpy()
    rv = pd.DataFrame(ret).rolling(window, min_periods=max(4, window // 2)).std().to_numpy()
    return -rv   # high signal = low realized vol = want-long
```

Window = 12 candles (4 days at 8h). Held identical. Signal is past-only (uses `close[t-12:t]` to decide at `close[t]` → fill `open[t+1]`); leak-safe by the engine's existing convention.

### 3.2 Universe (UNCHANGED)

`pit_topn_universe(panel, top_n=20, lookback=30)` — PIT top-20 by trailing 30-candle quote-volume, ex-stables, re-ranked every 8h. IS slice: `is_mask(panel)` (`open_time < OOS_CUTOFF_MS`).

### 3.3 NEW weighting code path (the one code change)

Add a `weighting: "midvol_short"` mode to `run_backtest(...)` and a new builder `target_weights_midvol_short(...)`. The existing `rank_neutral`, `longonly_tophalf`, and `ew_long` modes are untouched (backward-compat; EXPLORATION-001 parity must hold).

**Rank convention** (must match the existing builders exactly — verified against `target_weights_longonly`):
- `signal = -realized_vol` → high signal = low vol.
- `r = rankdata(signal_row[m]) - 1.0` → `r = 0` is the LOWEST signal (= HIGHEST vol = lottery tail), `r = n-1` is the HIGHEST signal (= LOWEST vol).
- So the extreme-vol tail (to SKIP) is at `r` near 0; the lowest-vol longs are at `r` near `n-1`.

```python
def target_weights_midvol_short(
    signal_row: np.ndarray, univ_row: np.ndarray, gross: float,
    long_frac: float = 0.5, short_frac: float = 0.25,
) -> np.ndarray:
    """Asymmetric rank-based L/S: long lowest-vol half, short mid-vol band,
    SKIP the extreme-vol tail (lottery mooners).

    Partition by signal rank (0 = lowest signal = highest vol):
      - LONG:   r >= long_threshold        (highest-signal `long_frac` = lowest-vol)
      - SHORT:  short_threshold <= r < long_threshold  (mid-vol band, `short_frac`)
      - SKIP:   r < short_threshold        (extreme-vol tail — the 10-100x mooners)

    Near-dollar-neutral: long gross = short gross = gross/2.
      sum(w) = 0, sum(|w|) = gross.

    long_frac=0.5, short_frac=0.25 -> for n=20: long 10, short 5, skip 5.
    `rankdata` average-rank ties may expand a band by 1 (intentional, no tie-breaker).
    Returns zeros if n < 4 (cannot form a meaningful 3-way partition).
    """
    w = np.zeros_like(signal_row, dtype=float)
    m = univ_row & np.isfinite(signal_row)
    n = int(m.sum())
    if n < 4:
        return w
    r = rankdata(signal_row[m]) - 1.0          # 0 = lowest signal = highest vol
    k_long = max(1, int(round(n * long_frac)))
    k_short = max(1, int(round(n * short_frac)))
    long_threshold = n - k_long                # r >= this -> LONG
    short_threshold = long_threshold - k_short  # short_threshold <= r < long_threshold -> SHORT
    if short_threshold < 0:
        # short band would consume the long band (tiny universe) -> degrade to long-only top-half
        short_threshold = 0
    long_mask = r >= long_threshold
    short_mask = (r >= short_threshold) & ~long_mask
    n_long = int(long_mask.sum())
    n_short = int(short_mask.sum())
    if n_long == 0 or n_short == 0:
        return w
    half = gross / 2.0
    w[m] = np.where(
        long_mask,
        half / n_long,
        np.where(short_mask, -half / n_short, 0.0),
    )
    return w
```

**Dispatch in `run_backtest`:** add `"midvol_short"` to the allowed `weighting` set and to the `if/elif` chain. When `weighting == "midvol_short"`, call `target_weights_midvol_short(sig[k-1], universe[k-1], g, lf, sf)` where `lf = long_frac or 0.5` and `sf = short_frac or 0.25`. Add a `short_frac: float | None = None` parameter to `run_backtest(...)`.

**Invariants the builder MUST satisfy** (verified by unit tests in §3.6):
- `w[~univ] = 0`, `w[invalid_signal] = 0`.
- `sum(w) = 0` (dollar-neutral) at every rebal step where `n >= 4`.
- `sum(|w|) = gross` at every rebal step where `n >= 4`.
- All long weights > 0; all short weights < 0; all skipped names = 0.
- The extreme-vol tail (lowest-signal names) is NEVER shorted.

### 3.4 Backtest configuration (primary)

| parameter | value | rationale |
|---|---|---|
| `weighting` | `"midvol_short"` | the one change |
| `long_frac` | `0.5` | long the lowest-vol half (10 of 20) — identical long-side selection to EXPLORATION-001 |
| `short_frac` | `0.25` | short the mid-vol quartile (5 of 20) — the Critic's principled midpoint; skips the extreme tail (5 of 20) |
| `gross` | `1.0` | held from EXPLORATION-001; 0.5 long + 0.5 short, near-dollar-neutral |
| `rebal` | `6` | held from EXPLORATION-001's best case (48h cadence); isolates the one change |
| `vol_target_ann` | `None` (primary) / `0.40` (secondary overlay) | primary = pure isolation of the weighting change; secondary = standard vol-target overlay (max_lev=2.0, vol_lookback=63). **Report both.** The vol-target is a risk primitive, not a signal change — but to keep "one change" honest, the primary gate applies to the no-VT variant. Note: EXPLORATION-001's VT variant UNDERPERFORMED no-VT (+0.44 vs +0.56) because VT de-levers calm years and up-levers the 2022 bear — this pattern may differ for an L/S book (the short leg dampens the bear), so the VT variant is reported but not gated. |
| `cost` | `CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)` | held from EXPLORATION-001; honest Binance Futures rates |
| `funding` | `load_funding(panel)` | ON — bucket-summed per `blind_funding.py` (AFTER the S1 SHIB fix lands) |

### 3.5 Required runs (all IS-only, all reported in one table)

1. **Primary book:** `weighting="midvol_short"`, long_frac=0.5, short_frac=0.25, rebal=6, funding ON, no VT.
2. **Vol-targeted book:** same + `vol_target_ann=0.40`, `max_lev=2.0`.
3. **EW-top-20 benchmark:** `weighting="ew_long"`, rebal=6, funding ON, no VT. ← the critical comparison (re-run with the S1 fix so SHIB funding is correct this time).
4. **Long-only primary (EXPLORATION-001 reproduction):** `weighting="longonly_tophalf"`, rebal=6, funding ON, no VT. ← confirms the funding delta is attributable to adding the short leg.
5. **B&H BTC:** existing `buy_hold_btc(panel)`.
6. **Cost-stress (primary book at 2x cost):** `CostModel(taker_fee_bps=10.0, slippage_bps=5.0, funding_enable=True)`.
7. **(Attribution) Naive L/S reproduction:** `weighting="rank_neutral"`, rebal=6, funding ON — confirms the engine still reproduces DIAGNOSTIC-002's −0.18 (parity check; not a gate).
8. **(Attribution) Full-rank-neutral with mid-vol only is NOT a separate run** — the primary book IS the mid-vol test. This run would be redundant.

All eight share the same IS-truncated panel (`slice_is`). Per-year Sharpe must be reported for runs 1–4. **Funding attribution by year (bps of equity) must be reported for runs 1, 3, 4** so the funding-tax dodge can be measured directly: (primary funding) vs (long-only funding) vs (EW funding), per year.

### 3.6 Mandatory test extension (leak-safety + partition discipline)

Extend `tests/test_blind_engine.py`. Target: 9 existing + 4 new = 13 green before any MERGE evaluation.

1. **`test_future_corruption_leaves_past_identical_midvol`** — positive-control leak check on the new path (mirror the existing `test_future_corruption_leaves_past_identical_longonly`): corrupt signal + open prices from `cutoff` forward → past weights/turnover/equity bit-identical.
2. **`test_midvol_dollar_neutrality_and_gross`** — at every rebal step with `n >= 4`: `sum(w) == 0` (dollar-neutral), `sum(|w|) == gross`, all long weights > 0, all short weights < 0.
3. **`test_target_weights_midvol_short_partition`** — direct unit test of the builder on a hand-computed row (mirror `test_target_weights_longonly_discipline`): verify the 3-way partition (long / short / skip) selects exactly the right names, the extreme-vol tail (lowest-signal names) is NEVER shorted, NaN/universe-excluded names get weight 0, and ties (average-rank) expand a band by at most 1.
4. **`test_midvol_short_skips_extreme_tail`** — construct a row where the lowest-signal name (highest vol) has a massive positive forward return (simulating a 100× mooner) and assert its weight is 0 (skipped, not shorted). This is the **load-bearing assertion** for the mechanism: the extreme tail must never be shorted.

---

## Section 4 — Pre-registered IS MERGE / NO-MERGE criteria (FROZEN)

Gates apply to the **primary book** (run 1, no VT). VT variant is reported for information. All gates evaluated IS-only. Any single failure → NO-MERGE; the diary records which gate and the observed value.

| # | gate | threshold | what it tests |
|---|---|---|---|
| G1 | **IS Sharpe (primary)** | `≥ 1.0` | absolute risk-adjusted floor |
| G2 | **IS Sharpe (primary) ≥ EW-top-20 + 0.15** | strict `≥ +0.15` delta | **the noise-marginal edge test.** EXPLORATION-001's +0.054 was inside noise (REVIEW-001 S3: SE≈0.05–0.08 from overlapping 6-candle holds). A +0.15 delta is ~2σ — the minimum claimable edge. If the mid-vol L/S can't beat EW by a noise-marginal amount, the mechanism does not add net-of-cost value. |
| G3 | **MaxDD (primary)** | `≥ −55%` | improved from long-only −87%; the short book must dampen the 2022 correlated-deleveraging crash. This is the **dominant failure** the mechanism targets. |
| G4 | **Per-year Sharpe, every year ≥ −1.0** | `{2020, 2021, 2022, 2023, 2024, 2025Q1}` all `≥ −1.0` | **the two-sided regime test — the sharpest gate.** 2021 must pass (mid-vol shorts don't blow up like the naive L/S's −1.83) AND 2022 must pass (short book dampens the crash vs long-only's −1.53). If EITHER year fails, the mechanism does not resolve the tension. |
| G5 | **Turnover (primary)** | `≤ 100x/yr one-way` | cost control; the short leg adds some turnover vs long-only's 73x but should stay under the L/S's 108x |
| G6 | **Cost-stress (2x cost)** | IS Sharpe `≥ 0.7` | robustness to the cost assumption |
| G7 | **2021 funding drag (primary)** | `≤ +1500 bps` | **NEW — the funding-tax dodge test.** Long-only paid +3722bps in 2021; the mid-vol book's short leg must offset enough of the long leg's mania-year funding payment to bring the 2021 drag under +1500bps (>60% reduction). This directly verifies near-neutrality is delivering the funding benefit. If the dodge fails here, the mechanism is not earning its short-side risk. |

**What makes me NO-MERGE** (each failure points to a specific next exploration):
- **G2 fails (delta < +0.15):** the mid-vol tilt doesn't add net-of-cost value over EW. → EXPLORATION-003 = **signal-proportional weighting** (Critic #2 — `w ∝ |signal|` concentrates risk budget on the strongest-signal names rather than equal-weighting the band).
- **G3 fails (MaxDD < −55%) OR G4-2022 fails:** the short book does not sufficiently dampen the bear crash (mid-vol names don't fall enough to hedge, or the gross is too low). → EXPLORATION-003 = **regime-aware gross scalar** (Critic #3 — de-risk gross in high-BTC-vol / high-cross-sectional-dispersion regimes; the only axis that can attack a correlated-deleveraging drawdown that position-level shorts can't fully hedge).
- **G4-2021 fails (Sharpe < −1.0):** the **null result**. Mid-vol shorts blow up too — the lottery-mooner risk extends beyond the extreme tail into the mid-vol cohort. This is a genuine structural finding. → EXPLORATION-003 = **regime-aware gross scalar** (Critic #3 is the only remaining defense if tail-capping at the mid-point fails; a regime gate scales ALL positions down when retail-mania indicators fire, regardless of which vol band they sit in).
- **G7 fails (2021 funding > +1500bps):** the near-neutrality is not delivering the funding dodge (mid-vol shorts receive too little funding to offset). → the funding-tax dodge mechanism is falsified for this construction; the short book is adding risk without the funding benefit. Reconsider whether any short construction can dodge the funding tax, or pivot to a pure cost-reduction axis (turnover / hysteresis).
- **G1 fails but G2 + G7 pass:** the tilt beats EW and dodges funding but neither clears 1.0 → the top-20-$-volume universe itself is too costly/adverse-selected at 8h. → EXPLORATION-004 = **OI-ranked universe** (DIAGNOSTIC-002 data discovery: historical OI is available via `data.binance.vision` daily archives → 8h; less adverse-selected than $-volume).

---

## Section 5 — Predicted behavioral effect (pre-registered, so a null is informative)

| metric | prediction (primary book, no VT) | confidence |
|---|---|---|
| **IS Sharpe** | **+0.7 to +1.2** | moderate. Funding dodge lifts the denominator effect; short book dampens 2022 (vs long-only −1.53); but short-side risk in 2021 is the genuine uncertainty. |
| **vs EW-top-20** | **+0.15 to +0.40** Sharpe delta | moderate. Near-neutrality + vol selection + crash dampening should beat EW by a noise-marginal amount. This is the core test (G2). |
| **2021 Sharpe** | **+0.3 to +1.0** (vs naive L/S −1.83, long-only +1.54) | moderate — the experiment's crux. Mid-vol shorts participate in the rally less violently than extreme-vol; no 10–100× blowup. But some short-side pain is expected (mid-vol names still rise in a bull market). If this comes in < −1.0, the null fires. |
| **2022 Sharpe** | **−0.3 to +0.6** (vs long-only −1.53, naive L/S +0.94) | moderate-high. The short book profits in the bear; should be materially better than long-only. The question is whether 5 mid-vol shorts at gross=0.5 are enough to offset 10 longs at gross=0.5. |
| **MaxDD** | **−45% to −65%** (vs long-only −87%, naive L/S −77%) | moderate. Short book dampens; mid-vol cap reduces tail. Should clear G3 (≥ −55%) if the 2022 dampening works. |
| **2021 funding drag** | **+200 to +1200 bps** (vs long-only +3722bps) | moderate-high. Short leg receives mania funding, offsetting the long leg. Half-gross long leg pays ~half the long-only funding (~+1860bps); short leg receives some of that back. |
| **Turnover** | **75–100x/yr** one-way (vs long-only 73x, naive L/S 108x) | moderate. Short leg adds some churn (5 names turning over) but less than the full rank-neutral (which churns all 20). |
| **VT variant** | Sharpe within ±0.2 of no-VT | low. EXPLORATION-001's VT underperformed (de-levered calm, up-levered bear). The L/S book's short leg may change this dynamic (bear dampening → VT less punitive). Reported, not gated. |

**What a null looks like (the informative failure):** IS Sharpe +0.3–0.5, **2021 Sharpe < −1.0.** This means the mid-vol shorts blew up alongside the extreme-vol shorts — the lottery-mooner risk is a broad high-vol-cohort phenomenon, not a tail-concentrated one. The retail-FOMO + liquidation-cascade propagation (BIS WP 1087) extends further down the vol distribution than the extreme-decile framing predicts. This null is **not terminal** — it falsifies tail-capping as a defense and makes the regime-gate (Critic #3) the only remaining axis that can address a broad-based mania blowup. It is a genuine structural finding about crypto cross-sectional risk.

**What a partial pass looks like (also informative):** G1/G2/G7 pass (funding dodge works, beats EW) but G3/G4 fail (2022 still too negative). This means the funding-tax problem is solved by near-neutrality, but the drawdown problem requires a separate defense. → EXPLORATION-003 = regime-aware gross scalar (Critic #3), stacking on top of this book's near-neutrality. The brief's "one change" discipline is preserved per-EXPLORATION; stacking across EXPLORATIONs is the normal research cadence.

---

## Section 6 — What this does NOT do (scope discipline — ONE change)

Explicitly deferred to later EXPLORATIONs (listed so the Critic can verify no scope creep):

- **NO regime gate** (no cross-sectional-dispersion scalar, no BTC-vol-regime flatten, no gross scalar). This is the EXPLORATION-003 candidate if G3/G4 fail here.
- **NO signal-proportional / inverse-vol weighting.** Equal-weight within each band is the parameter-free choice. Weighting-shape optimization is deferred (Critic #2, EXPLORATION-003 candidate if G2 fails).
- **NO per-name short weight cap.** The per-name short weight is 0.10 (= 0.5/5), which is above the 5% long weight but below the 20% concentration flag. If the result shows per-name short concentration is a problem (e.g., a single mid-vol name dominates the short P&L), a per-name cap becomes an EXPLORATION-003 lever.
- **NO multi-factor combination** with `rev_3` (IC +0.045, orthogonal to vol_low at corr −0.006). Deferred.
- **NO universe change** (still PIT top-20 by trailing 30-candle $-volume). OI-based ranking deferred.
- **NO signal-window change** (12-candle realized vol).
- **NO long_frac / short_frac optimization.** long_frac=0.5 / short_frac=0.25 is the parameter-free midpoint; scanning these fractions would be tuning on IS.
- **NO hysteresis bands or eligibility-exit logic.**
- **NO OOS peek.** The OOS_CUTOFF=2025-03-24 wall is untouched.

---

## Section 7 — Risk primitive (for the risk-engineer)

The brief requires an explicit risk-mitigation design. For EXPLORATION-002:

1. **The mid-vol partition IS the primary risk primitive** — it removes the extreme-vol tail (the diagnosed 2021 blowup source) from the short book by construction. This is the core risk mitigation: the names most likely to 10–100× are never shorted.
2. **Near-dollar-neutrality is the secondary risk primitive** — it removes the structural funding tax (the verified +12%/yr drag) by balancing long and short funding flows. The 2021 funding drag should drop from +3722bps to ≤ +1500bps (G7).
3. **Vol-target overlay (secondary variant, vol_target_ann=0.40, max_lev=2.0):** standard Carver-style vol targeting. Reported for information; the no-VT primary is gated. Note the EXPLORATION-001 finding that VT underperformed for a long-only book (de-levers calm, up-levers bear) — this may differ for an L/S book.
4. **Report (do not gate on, this iteration):**
   - Max per-name weight (long side ~5%, short side ~10%; flag if any name > 20% — the warmup edge effect from EXPLORATION-001 may recur).
   - Gross-leverage time series (confirm mean ~1.0, no drift; confirm dollar-neutrality holds: `sum(w) ≈ 0` at every rebal).
   - Short-leg per-year P&L attribution (how much of the 2022 improvement comes from the short leg vs the long leg at half-gross).
   - Funding-by-year attribution for primary vs long-only vs EW (the direct measurement of the funding-tax dodge).

No new kill-switch is pre-registered beyond the G1–G7 gates. The gates ARE the kill-switch.

---

## Section 8 — Deliverable checklist for QE + risk-engineer

- [ ] **PREREQUISITE:** Fix SHIB funding symbol-resolution (REVIEW-001 S1) in `blind_funding.py`. Add the symbol map (`SHIBUSDT → 1000SHIBUSDT`, etc.) + post-`load_funding` assertion that every IS-universe member is `present`. Verify SHIB funding is now non-zero.
- [ ] Implement `target_weights_midvol_short` + `"midvol_short"` dispatch + `short_frac` parameter in `blind_engine.py`.
- [ ] 4 new tests in `test_blind_engine.py` (leak positive-control; dollar-neutrality+gross; partition unit test; extreme-tail-skip). 13/13 green.
- [ ] Run script `analysis/portfolio/blind_exploration_002.py` producing a single committed table (runs 1–8 above) with per-year Sharpe for primary, VT, EW, and long-only runs.
- [ ] Report funding-by-year attribution (primary vs long-only vs EW), short-leg per-year P&L, max per-name weight, gross-leverage series.
- [ ] Hand results to QR for Phase-7 evaluation against G1–G7 (this brief). **Do not reveal OOS.**

---

**FROZEN.** Any change to the gates, signal, weighting, fractions, or parameters after the first backtest run invalidates this pre-registration and must be recorded as a new EXPLORATION.
