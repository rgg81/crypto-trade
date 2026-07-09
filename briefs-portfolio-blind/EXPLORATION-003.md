# EXPLORATION-003 — Multi-Factor rev_3 Blend (vol_low + rev_3 in the EXPLORATION-002 shell)

## Section 0 — Provenance (pre-registration)

- **Frozen:** 2026-07-09, BEFORE any backtest run of this design. IS-only.
- **OOS sealed:** `OOS_CUTOFF = 2025-03-24`. Not looked at, not planned around.
- **Track:** baseline-blind top-20 L/S portfolio (this worktree).
- **Predecessors:**
  - `briefs-portfolio-blind/EXPLORATION-002.md` — the mid-vol shell this iteration preserves verbatim (`weighting="midvol_short"`, long_frac=0.5, short_frac=0.25, gross=1.0, rebal=6, cost 5+2.5bps, funding ON, PIT top-20-$-volume universe).
  - `diary-portfolio-blind/EXPLORATION-002-engineering.md` — primary book: Sharpe **+0.09**, MaxDD **−48.5%**, turnover **138x**, 2021 **−0.38**, 2022 **+0.89**, 2021 funding **−240 bps** (net income), 2x-cost **−0.29**.
  - `diary-portfolio-blind/REVIEW-002.md` — Critic **CONDITIONAL-PASS**; "+0.09 REAL but cost-depressed ~0.1–0.2 Sharpe by structurally elevated turnover"; Path Forward #1 (HIGHEST) = "Multi-factor blend with `rev_3` — IC +0.045 at corr −0.006 to vol_low. Only axis adding a NEW alpha source."
  - `diary-portfolio-blind/PHASE7-002.md` — formal NO-MERGE: G1/G2/G5/G6 fail (return-alpha + cost-fragility); G3/G4/G7 pass (defensive substrate verified).
  - `diary-portfolio-blind/DIAGNOSTIC-001-signal-ic.md` — `vol_low` rank-IC +0.052; **`rev_3` rank-IC +0.045** (t=+16.1, IR +0.21), positive every IS year (+.048/+.054/+.050/+.047/+.027/+.032 for 2020/21/22/23/24/25Q1); **avg cross-sectional rank-corr(vol_low, rev_3) = −0.006 → orthogonal**. rev_3 = `-close.pct_change(3)` → past-only leak-safe (computed at close[t] from close[t-3..t]).
- **Blinding:** designed against `blind_engine.py`, `blind_universe.py`, `blind_funding.py`, `blind_signal_ic_probe.py`, and the blind EXPLORATION-001/002 diaries only. No baseline artifact read. OOS never inspected.
- **Choice provenance:** direction (rev_3 blend) chosen by the user + Critic's #1 Path-Forward recommendation; not re-weighed against other axes in this brief.

---

## Section 1 — Hypothesis (one sentence)

**Blending the orthogonal short-term-reversal signal `rev_3` (cross-sectional rank-IC +0.045 at corr −0.006 to `vol_low`) into the EXPLORATION-002 mid-vol tail-capped neutral shell — as an equal-weight cross-sectional z-blend `0.5·z(vol_low) + 0.5·z(rev_3)` fed to the unchanged `target_weights_midvol_short` builder — adds a material return-alpha leg (mean-reversion of recent losers) on top of vol_low's defensive leg, lifting primary IS Sharpe from +0.09 to ≥ +0.29 net of realistic cost, while HOLDING the verified defensive properties (MaxDD ≥ −60%, every per-year Sharpe ≥ −1.0, 2021 funding drag ≤ +1500 bps) because the near-dollar-neutral mid-vol shell that delivered those defenses is preserved verbatim.**

---

## Section 2 — Chosen mechanism + crypto-native rationale

### The one change

**Replace the single-factor signal `signal = lowvol_signal(panel)` with an equal-weight cross-sectional z-blend of two signals, `signal = 0.5·z_cs(vol_low) + 0.5·z_cs(rev_3)`, computed per-timestamp over the PIT top-20 universe. Everything downstream — `target_weights_midvol_short`, long_frac=0.5, short_frac=0.25, gross=1.0, rebal=6, cost model, funding panel, universe — is byte-identical to EXPLORATION-002.** The Sharpe / MaxDD / funding / turnover deltas vs EXPLORATION-002's +0.09 are attributable SOLELY to the signal blend.

The engine takes the signal as a raw `(T, C)` array and `target_weights_midvol_short` ranks each row via `rankdata` internally — so a blended signal requires **zero engine change**. The blend happens entirely at signal construction.

### Why z-blend (not rank-blend)

Both candidates are parameter-free (the 0.5/0.5 weight is the pre-registered midpoint, not scanned). The selection:

| option | what it preserves | robustness | match to Critic's mental model | verdict |
|---|---|---|---|---|
| **(i) z-blend** `0.5·z(vol_low)+0.5·z(rev_3)` then rank | **magnitude within the cross-section** — a coin 2σ from mean on BOTH signals scores higher than one 1σ on both | scale-normalized; outlier-sensitive in z-space (but bounded by the downstream rank) | "two orthogonal alpha sources added" → combined IC ≈ √(IC_vol² + IC_rev²) assumes linear-alpha combination, which is the z-blend | **CHOSEN** |
| (ii) rank-blend `0.5·rank(vol_low)+0.5·rank(rev_3)` | only ordinal info per signal — discards within-rank magnitude | maximally outlier-robust (Carver's forecast-combination default) | throws away the magnitude info that lets strong-on-both names score highest | rejected — loses signal |

The z-blend is the canonical "combine two orthogonal alphas at equal scale" construction. Cross-sectional z-scoring puts both signals on the same scale before averaging — **necessary** because vol_low (a return-std, typical magnitude 0.01–0.10) and rev_3 (a 3-candle return, typical magnitude ±0.30 in 8h crypto) live on incompatible raw scales; raw averaging would be dominated by rev_3.

The downstream `rankdata` in `target_weights_midvol_short` then converts the blended z-score to a within-row rank, so the long/mid-short/skip partition remains the same 10/5/5 split EXPLORATION-002 used — only the **identity** of which 10/5/20 names populate each band changes.

### Crypto-native rationale for why the rev_3 blend should add return-alpha

1. **rev_3 and vol_low capture genuinely different economic forces.** vol_low is the lottery-preference anomaly — retail overpays for high-skew names, so low-vol large-caps drift up (defensive, slow-decaying: realized-vol rankings are persistent → low turnover). rev_3 is short-term mean reversion — recent losers bounce, recent winners pull back (alpha source, fast-decaying: 3-candle signal → higher turnover but higher IC decay). corr −0.006 confirms orthogonality at 8h cross-sectionally. Combining two uncorrelated alpha sources produces a higher combined-IC than either alone: under independence, `IC_combined ≈ √(IC_vol² + IC_rev²) = √(0.052² + 0.045²) = 0.069` — a +33% IC lift over vol_low alone.

2. **The crypto 8h cross-section mean-reverts (DIAGNOSTIC-001).** Cross-sectional momentum (mom_24, mom_84) is negative every IS year; 1-day reversal (rev_3) is positive every IS year. This is structural: retail FOMO chases recent winners into local tops, leverage-driven liquidation cascades (BIS WP 1087, 2025) overshoot both directions, and the 8h cadence is long enough for the cascade to complete but short enough that the mean-reversion hasn't fully priced in. rev_3 monetizes exactly this timescale.

3. **rev_3 is FASTER than vol_low — and that's the point.** vol_low's IC is highly stable (rising to +0.076 in 2025Q1) but its signal decays slowly (vol clustering → low turnover → low cost → low gross alpha). rev_3's IC is also stable (+0.045 every year) but its signal decays in ~3 candles (high turnover → higher cost but higher gross alpha). The blend should produce **more gross alpha than vol_low alone, at somewhat higher cost** — the open empirical question is whether the net-of-cost balance clears +0.20 Sharpe (G-ALPHA).

4. **The mid-vol shell's defensive properties are signal-orthogonal.** EXPLORATION-002 verified that near-dollar-neutrality + tail-capping deliver MaxDD −48.5% and 2021 funding −240bps income. These properties live in `target_weights_midvol_short` (the 10-long/5-mid-short/5-skip partition + sum(w)=0), NOT in the signal. Changing only the signal cannot break them — UNLESS the new signal pulls different names into the mid-short band (the band where 2021 short-side blowup risk lives). That risk is real and gated explicitly (G-DEF-REGIME, G-DEF-DD — see §4).

### Known mechanism risk the Critic should weigh

The "skip extreme tail" property is preserved in **rank terms** (the bottom-5 blended-signal names are still skipped), but the **identity** of those 5 names changes. Specifically:
- **Agreement case (defensive property holds):** a pumped lottery mooner is high-vol (low vol_low) AND recently-pumped (low rev_3, since rev_3 = −past_return). Both signals agree → bottom of blend → SKIP. Safe.
- **Disagreement case (new risk):** a coin that just CRASHED 50% in 3 candles is high-vol (low vol_low) BUT a recent loser (high rev_3). z(vol_low) ≈ −2, z(rev_3) ≈ +2 → blended z ≈ 0 → mid-rank → SHORT band. Under EXPLORATION-002 that coin was in the SKIP band (extreme-vol tail); under the blend it may enter the short band. **If crashed coins keep crashing (bear regime), the short profits; if they bounce (mania reversal), the short loses.** This is exactly where rev_3 contributes alpha in bear markets (2022: +0.93 short-leg price P&L is the analog) and where it adds risk in mania (2021). G-DEF-REGIME (2021 ≥ −1.0) and G-DEF-DD are the gates that catch a regression.

---

## Section 3 — Exact implementation spec (for the quant-engineer)

### 3.1 rev_3 signal loader (NEW — leak-safe reference verified)

The leak-safe reference is `blind_signal_ic_probe.py` line 116: `"rev_3": -close.pct_change(3)`. The probe computed IC +0.045 from this exact formula. The loader below mirrors `lowvol_signal`'s past-only convention.

```python
def rev3_signal(panel: Panel, lookback: int = 3) -> np.ndarray:
    """Short-term reversal signal. High = recent loser = want-long.

    rev_3[t] = -(close[t] / close[t-3] - 1)

    Past-only: at time t, uses only close[t-3], close[t-2], close[t-1], close[t].
    All four values are known at close[t]. Leak-safe by construction (matches
    blind_signal_ic_probe.py line 116 exactly — same formula that produced the
    DIAGNOSTIC-001 IC +0.045).
    """
    close = pd.DataFrame(panel.close)
    return (-close.pct_change(lookback)).to_numpy()
```

`lookback=3` is the only parameter and is FROZEN at the DIAGNOSTIC-001 value (no scan).

### 3.2 Cross-sectional z-scoring (NEW helper — past-only)

```python
def _cs_zscore_2d(arr: np.ndarray, univ: np.ndarray, min_n: int = 2) -> np.ndarray:
    """Cross-sectional z-score per timestamp, over universe members only.

    At each t, computes (arr[t,c] - mean) / std over {c : univ[t,c] & finite(arr[t,c])}.
    Past-only by construction: uses ONLY cross-sectional values at timestamp t.
    No future information is read. NaN where the cross-section has < min_n valid
    members or zero std.

    This is the leak-safe equivalent of the row-IC computation in
    blind_signal_ic_probe.row_ic (same per-timestamp cross-sectional scope).
    """
    out = np.full_like(arr, np.nan, dtype=float)
    for t in range(arr.shape[0]):
        m = univ[t] & np.isfinite(arr[t])
        if m.sum() < min_n:
            continue
        vals = arr[t, m]
        mu = float(vals.mean())
        sd = float(vals.std(ddof=1))
        if sd > 0:
            out[t, m] = (vals - mu) / sd
    return out
```

### 3.3 Blended signal (NEW — the one signal change)

```python
def blended_signal(
    panel: Panel, univ: np.ndarray,
    w_vol: float = 0.5, w_rev: float = 0.5,
    vol_window: int = 12, rev_lookback: int = 3,
) -> np.ndarray:
    """Equal-weight cross-sectional z-blend of vol_low and rev_3.

    signal = w_vol * z_cs(vol_low) + w_rev * z_cs(rev_3)

    Both components are 'high = want-long' and on the same z-scale, so the
    0.5/0.5 average is a parameter-free equal-weight midpoint (no scan).
    Returns a (T, C) array of blended z-scores; feed directly to run_backtest
    as the `signal` argument — target_weights_midvol_short will rank each row
    exactly as it did for the single-factor vol_low signal in EXPLORATION-002.
    """
    s_vol = lowvol_signal(panel, window=vol_window)
    s_rev = rev3_signal(panel, lookback=rev_lookback)
    z_vol = _cs_zscore_2d(s_vol, univ)
    z_rev = _cs_zscore_2d(s_rev, univ)
    return w_vol * z_vol + w_rev * z_rev
```

The default `w_vol = w_rev = 0.5` is FROZEN — no weight scan. (A 2D grid over (w_vol, w_rev) would be tuning on IS and is explicitly out of scope.)

### 3.4 What stays byte-identical to EXPLORATION-002

| component | value | source |
|---|---|---|
| `weighting` | `"midvol_short"` | EXPLORATION-002 §3.3 (unchanged engine code) |
| `long_frac` | `0.5` | EXPLORATION-002 §3.4 |
| `short_frac` | `0.25` | EXPLORATION-002 §3.4 |
| `gross` | `1.0` | EXPLORATION-002 §3.4 |
| `rebal` | `6` | EXPLORATION-002 §3.4 (48h cadence) |
| `cost` | `CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)` | EXPLORATION-002 §3.4 (honest Binance rates) |
| `funding` | `load_funding(panel)` ON (post-S1 SHIB fix) | EXPLORATION-002 §3.4 |
| `univ` | `pit_topn_universe(panel, top_n=20, lookback=30)` | EXPLORATION-002 §3.2 |
| `vol_target_ann` | `None` (primary) | EXPLORATION-002 §3.4 (no VT in primary) |
| IS slice | `slice_is(full)` (`open_time < OOS_CUTOFF_MS`) | EXPLORATION-002 §3.2 |

The QE may relocate `lowvol_signal` into a shared `blind_signals.py` module if it prefers (it currently lives in `blind_sanity_lowvol.py`); if so, the EXPLORATION-002 import path must produce a byte-identical signal array. **Verify parity by re-running EXPLORATION-002's run-1 in the new script and confirming Sharpe +0.09 reproduces.**

### 3.5 Backtest configuration (primary)

| parameter | value |
|---|---|
| `weighting` | `"midvol_short"` |
| `signal` | `blended_signal(panel, univ)` (the one change) |
| `univ` | `pit_topn_universe(panel, top_n=20, lookback=30)` |
| `cost` | `CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)` |
| `gross`, `rebal`, `long_frac`, `short_frac` | `1.0`, `6`, `0.5`, `0.25` |
| `funding` | `load_funding(panel)` |
| `vol_target_ann` | `None` |

### 3.6 Required runs (all IS-only, all reported in one committed table)

The first three are the **alpha-attribution triplet** — they isolate rev_3's marginal contribution by holding the shell fixed and varying only the signal.

1. **Primary (blended):** `signal = blended_signal(panel, univ)`, weighting=`midvol_short`. **The EXPLORATION-003 result.**
2. **vol_low-only (EXPLORATION-002 reproduction):** `signal = lowvol_signal(panel)`, weighting=`midvol_short`. **Must reproduce EXPLORATION-002 run-1 Sharpe +0.09 bit-identically** (parity check — delta must be 0.00 to the reported +0.09; tolerance ±0.005 for any float-ordering noise).
3. **rev_3-only:** `signal = rev3_signal(panel)` cross-sectionally z-scored via `_cs_zscore_2d(rev3_signal(panel), univ)`, weighting=`midvol_short`. Isolates rev_3's standalone contribution through the same shell.
4. **EW-top-20 benchmark:** `signal = lowvol_signal(panel)`, weighting=`ew_long`, rebal=6. (Same as EXPLORATION-002 run-3; the G-EW anchor.)
5. **Long-only benchmark:** `signal = lowvol_signal(panel)`, weighting=`longonly_tophalf`, rebal=6. (Same as EXPLORATION-002 run-4; reference for the funding-drag delta.)
6. **B&H BTC:** existing `buy_hold_btc(panel)`.
7. **Cost-stress (blended at 2x cost):** primary + `CostModel(taker_fee_bps=10.0, slippage_bps=5.0, funding_enable=True)`. (G-COST gate.)
8. **Cost-stress (rev_3-only at 2x cost):** run-3 signal + 2x cost. **Reveals whether rev_3 alone is cost-fragile** — diagnostic for interpreting the blend's cost-resilience.

All eight share the same IS-truncated panel (`slice_is`). Per-year Sharpe must be reported for runs 1, 2, 3, 4, 5. **Funding-by-year attribution (bps of equity) must be reported for runs 1, 2, 3** so the funding-tax dodge can be confirmed to hold under both signals independently and under the blend.

### 3.7 Mandatory test extension (leak-safety + blend discipline)

Extend `tests/test_blind_engine.py`. Target: 18 existing + 5 new = 23 green before any MERGE evaluation. New tests live alongside the EXPLORATION-002 midvol tests; the existing 18 stay byte-identical (regression guard).

1. **`test_rev3_signal_past_only`** — leak positive-control on the new signal loader. Corrupt `panel.close[t:]` (and `panel.open[t:]`, `quote_volume[t:]` for safety) from a cutoff forward → `rev3_signal[:t]` bit-identical to the uncorrupted run. Mirrors `test_future_corruption_leaves_past_identical_midvol`'s structure.
2. **`test_cs_zscore_past_only`** — corrupt `arr[t:]` and `univ[t:]` forward → `_cs_zscore_2d[:t]` bit-identical. Documents that z-scoping uses only the per-timestamp cross-section.
3. **`test_blended_signal_no_future_leak`** — end-to-end positive control: corrupt panel forward from cutoff → run `blended_signal(panel, univ)` and `run_backtest(...)` with `weighting="midvol_short"`; assert past weights / turnover / equity bit-identical to the uncorrupted run. **This is the load-bearing leak assertion for the new path.**
4. **`test_blended_skips_agreement_outlier`** — construct a row where one name has z(vol_low) = −5 (extreme high vol = lottery mooner) and z(rev_3) = −5 (extreme recent pump) → blended z = −5, lowest rank → SKIP (weight 0). Confirms the defensive property holds when both signals agree on "avoid this name." Mirrors `test_midvol_short_skips_extreme_tail`.
5. **`test_blended_crashed_coin_lands_short`** — construct a row where one name has z(vol_low) = −3 (high vol) and z(rev_3) = +3 (recently crashed) → blended z ≈ 0, mid-rank → SHORT band (weight < 0). **Documents the known disagreement-case behavior** (a crashed/high-vol coin that EXPLORATION-002 would have skipped now enters the short band). Not a pass/fail assertion about desirability — a regression-lock so future changes to the blend formula surface as a test failure if this behavior shifts.

### 3.8 Attribution the QE MUST report (so rev_3's marginal alpha is visible)

The headline question is "does rev_3 ADD alpha net-of-cost, holding the shell fixed?" The attribution below isolates the answer:

- **Three-book comparison** (runs 1, 2, 3) in one table: Sharpe, MaxDD, turnover, per-year Sharpe, final equity. The Sharpe delta (run-1 − run-2) IS the rev_3 marginal contribution net of cost.
- **Per-leg, per-year price P&L** for the blended book (long leg vs short leg) — verify both legs contribute (not just one signal dominating the blend).
- **Per-year funding attribution** (primary vs vol_low-only vs rev_3-only) — confirm the near-neutrality dodge (2021 ≤ +1500 bps) holds for all three; if rev_3-only violates it, the blend inherits a partial drag.
- **Realized cross-sectional rank-corr(vol_low, rev_3)** averaged over IS rebal steps in the top-20 universe — confirm ≈ −0.006 (matches DIAGNOSTIC-001; if production realized corr is materially different, the blend's combined-IC math breaks down and the brief's prediction is void).
- **2x-cost stress on all three books** (runs 7, and re-runs of 2 & 3 at 2x cost) — isolate which signal drives cost-fragility.

---

## Section 4 — Pre-registered IS MERGE / NO-MERGE criteria (FROZEN)

Gates apply to the **primary blended book** (run 1). All gates evaluated IS-only. Any single failure → NO-MERGE; the diary records which gate and the observed value. Thresholds pre-registered BEFORE any run.

| # | gate | threshold | what it tests |
|---|---|---|---|
| G-ALPHA | **IS Sharpe (blended primary)** | `≥ +0.29` (= EXPLORATION-002 +0.09 + 0.20) | **the core return-alpha test.** rev_3 must lift Sharpe by a material, noise-marginal amount. REVIEW-002's overlap SE ≈ 0.05–0.08 → +0.20 is ~2.5–4σ; the minimum claimable lift. If the blend can't beat the single-factor book by this, rev_3 is not contributing net-of-cost alpha. |
| G-EW | IS Sharpe (blended) ≥ EW-top-20 + 0.15 | `≥ +0.60` (EW was +0.451) | the noise-marginal edge over naive (inherited from EXPLORATION-002 G2). |
| G-DEF-DD | **MaxDD (blended)** | `≥ −60%` | the defensive MaxDD must not materially regress. EXPLORATION-002 was −48.5%; allow 11.5pp slack because rev_3 is a faster-decaying signal that may raise turnover and short-side vol. A regression past −60% means the crashed-coin-into-short-band risk (§2 disagreement case) is realized, not theoretical. |
| G-DEF-REGIME | **every per-year Sharpe ≥ −1.0** | `{2020..2025Q1}` all `≥ −1.0` | hold EXPLORATION-002's regime-robustness (G4 passed at 2021 −0.38 / 2022 +0.89). The 2021 book is the crux: if rev_3 pulls crashed coins into the short band and those squeeze, 2021 could regress below −1.0 → the disagreement-case risk fired. |
| G-FUND | **2021 funding drag (blended)** | `≤ +1500 bps` | hold the near-neutrality dodge (EXPLORATION-002 G7 passed at −240 bps net income). Inherited threshold. |
| G-COST | **2x-cost IS Sharpe (blended)** | `≥ 0.5` | cost-resilience. EXPLORATION-002 FAILED this gate at −0.29; the blend must do substantially better. If rev_3's alpha is real and cost-robust, 2x-cost Sharpe should be ≥ 0.5; if rev_3 is cost-fragile (run-8 at 2x cost is also negative), the alpha is illusory. |

**G-ALPHA threshold justification.** +0.20 above EXPLORATION-002's +0.09 is the minimum material claimable lift given REVIEW-002's overlap SE (~0.05–0.08). It is also the threshold at which the answer to "is rev_3 a portable alpha source at 8h?" flips. The Critic's path-forward combined-IC math (`√(S_vol²+S_rev²)`) implies that if rev_3 carries real independent alpha, the lift should be substantially positive (combined IC +0.069 vs vol_low's +0.052 → +33% IC lift → ideally +0.03 Sharpe pre-cost, with realization depending on turnover). If the realized lift is < +0.20, either (a) the orthogonality breaks down in the top-20 universe (realized corr ≫ −0.006), (b) rev_3's turnover cost eats the spread, or (c) rev_3's IC doesn't survive the midvol_short partition. All three are informative.

### What makes me NO-MERGE (each failure points to a specific next exploration)

- **G-ALPHA fails (Sharpe < +0.29):** rev_3 doesn't carry net-of-cost portable alpha in this shell. → informative null (see §5). The next iteration is NOT "tune the blend weight" (that's IS-tuning, explicitly forbidden); it's a scope break — pivot to an OI-ranked universe (DIAGNOSTIC-002 data discovery: historical OI is available via `data.binance.vision` daily archives → 8h; less adverse-selected than $-volume), OR a different mechanism family (funding-rate signals, on-chain).
- **G-DEF-DD fails (MaxDD < −60%) OR G-DEF-REGIME-2021 fails (Sharpe < −1.0):** the disagreement-case risk fired — crashed/high-vol coins entering the short band squeezed in 2021 or correlated-deleveraged in 2022 worse than vol_low alone. → the mid-vol shell is signal-sensitive in a way EXPLORATION-002 didn't test. EXPLORATION-004 = add a defensive gate that re-applies the vol_low SKIP filter on top of the blended ranking (composite partition: SKIP if EITHER signal flags extreme-vol-tail, regardless of blend rank). This is a signal-composition change, not a shell change.
- **G-FUND fails (2021 drag > +1500 bps):** rev_3 changed the long/short balance enough to break near-neutrality (e.g., rev_3 pulled mania-year mooners into the LONG band). → the funding dodge is signal-sensitive. EXPLORATION-004 = explicit dollar-neutral rebalanced weights (current `target_weights_midvol_short` is near-neutral by construction, not enforced — a name exiting due to `valid_price=False` can break the balance).
- **G-COST fails (2x-cost < 0.5):** the blend is still cost-fragile (rev_3 raises turnover beyond what its alpha covers). → EXPLORATION-004 = turnover-reduction primitive (REVIEW-002 S1 / Path Forward #2 — hysteresis or eligibility-exit buffer). This is the highest-value EXPLORATION-004 regardless of /003's outcome, because EXPLORATION-002's 138x turnover is a verified structural drag.
- **G-EW fails:** the blend doesn't beat naive EW even after adding a second factor → the top-20-$-volume universe is itself the bottleneck (adverse-selected). → EXPLORATION-004 = OI-ranked universe.

---

## Section 5 — Predicted behavioral effect (pre-registered, so a null is informative)

| metric | prediction (blended primary) | confidence | EXPLORATION-002 baseline |
|---|---|---|---|
| **IS Sharpe** | **+0.30 to +0.60** | moderate. Combined-IC math (+33%) and orthogonality support a material lift; cost sensitivity is the genuine uncertainty (rev_3 is faster → higher turnover). | +0.09 |
| **vs vol_low-only** | **+0.15 to +0.45 Sharpe delta** | moderate-high. This is the core G-ALPHA test. | (vs itself: 0) |
| **2021 Sharpe** | **−0.30 to +0.20** | moderate-low. Mean-reversion should help (crashed coins bounce, the long book catches them), BUT the disagreement-case risk (crashed coins pulled into the short band and squeezing) is the genuine downside uncertainty. If this comes in < −1.0, G-DEF-REGIME fires. | −0.38 |
| **2022 Sharpe** | **+0.60 to +1.20** | moderate-high. Mean-reversion shines in bear (shorts on bounce, longs on crash); the short leg's +0.93 price P&L should compound with rev_3's long-bounce alpha. | +0.89 |
| **MaxDD** | **−50% to −62%** | moderate. Some regression from −48.5% as the faster signal raises turnover and vol; should clear G-DEF-DD (≥ −60%) unless the disagreement-case risk materializes. | −48.5% |
| **2021 funding drag** | **−400 to +800 bps** | moderate-high. Near-neutrality is preserved by construction (the partition is unchanged); the identity shift in the long/short bands shouldn't break the dodge. | −240 bps (income) |
| **Turnover** | **150–210x/yr** one-way | moderate-high. rev_3's 3-candle signal rotates ranks faster than vol_low's 12-candle; expect 1.1–1.5× EXPLORATION-002's 138x. | 138x |
| **2x-cost Sharpe** | **−0.10 to +0.40** | low-moderate. Borderline on G-COST (≥ 0.5). If the blend's turnover pushes past 200x, the cost-stress will likely fail again. | −0.29 |

### The informative null (what a failure tells us)

**If G-ALPHA fails (blended Sharpe < +0.29):** rev_3's IC +0.045 doesn't survive realistic cost as a portable alpha source on the PIT-top-20-$-volume universe at 8h. Given that vol_low (+0.052) and rev_3 (+0.045) are the TWO STRONGEST orthogonal signals DIAGNOSTIC-001 found in the OHLCV cross-section at 8h, a joint failure is a strong signal that **OHLCV cross-sectional factors at 8h are collectively too weak to clear costs on this universe in this shell.** That is a structural finding, not a tuning problem. It motivates a SCOPE BREAK, not a parameter tweak:

1. **OI-ranked universe** (DIAGNOSTIC-002 data discovery) — $-volume ranking is adverse-selected (pump→enter→dump); OI ranking selects names with real leveraged positioning, less degen-flow. Different universe, same shell — a one-change iteration.
2. **Different mechanism family** — funding-rate carry (BIS WP 1087, 2025 — 10% carry shock → 22% liquidation jump), on-chain Whale Ratio / MVRV-Z (DIAGNOSTIC-001 noted these are unavailable in this worktree's data but are fetchable from Glassnode/CryptoQuant), or taker-flow order-book imbalance at higher resolution.

**If G-ALPHA passes but G-DEF-DD or G-DEF-REGIME fails:** rev_3 adds alpha but at the cost of defensive regression — the disagreement-case risk fired. → EXPLORATION-004 adds a composite SKIP filter (defensive overlay). Not a null; a partial pass with a defined next step.

**If G-COST fails (blended 2x-cost < 0.5) but G-ALPHA passes at base cost:** the alpha is real but cost-fragile. → EXPLORATION-004 = hysteresis / eligibility-exit buffer (REVIEW-002 Path Forward #2). This is the highest-ROI next iteration regardless of /003's other outcomes, because EXPLORATION-002's 138x turnover is a verified structural drag that hysteresis could recover ~0.1–0.2 Sharpe on.

---

## Section 6 — What this does NOT do (scope discipline — ONE change)

Explicitly deferred to later EXPLORATIONs (listed so the Critic can verify no scope creep):

- **NO blend-weight optimization.** `w_vol = w_rev = 0.5` is the parameter-free midpoint; scanning weights is IS-tuning. Deferred indefinitely unless a separate mechanism-mandate justifies a 2D grid with multiple-testing correction.
- **NO change to the mid-vol shell.** `weighting="midvol_short"`, `long_frac=0.5`, `short_frac=0.25`, `gross=1.0`, `rebal=6` are all byte-identical to EXPLORATION-002. The shell is a frozen substrate.
- **NO hysteresis / eligibility-exit / turnover-reduction primitive.** This is the EXPLORATION-004 candidate if G-COST fails. Addressing turnover in /003 would conflate two mechanisms (alpha-blend + cost-reduction) and destroy the attributability of the Sharpe delta to the signal blend.
- **NO net-long bias.** The book stays near-dollar-neutral. A mild long tilt (0.7/0.3) is a separate Critic suggestion (REVIEW-002 Path Forward #3) — deferred.
- **NO composite SKIP filter.** The defensive overlay (SKIP if EITHER signal flags extreme-vol) is the EXPLORATION-004 candidate if G-DEF-DD or G-DEF-REGIME fires.
- **NO signal-window change.** `vol_window=12`, `rev_lookback=3` are frozen at the DIAGNOSTIC-001 values that produced the measured ICs. Scanning windows is IS-tuning.
- **NO universe change.** Still PIT top-20 by trailing 30-candle $-volume. OI-based ranking is the EXPLORATION-004 (or later) candidate if the OHLCV cross-section proves collectively too weak.
- **NO funding model change.** Same `load_funding` post-S1-SHIB-fix panel.
- **NO VT overlay on primary.** (Reported for information only if the QE chooses to include it; not gated.)
- **NO OOS peek.** `OOS_CUTOFF = 2025-03-24` is untouched.

---

## Section 7 — Risk primitive (for the risk-engineer)

The brief requires an explicit risk-mitigation design. For EXPLORATION-003:

1. **The mid-vol shell IS the primary risk primitive** — inherited verbatim from EXPLORATION-002. It removes the extreme-vol tail (lowest-blended-signal 5 names) from the short book by construction and enforces near-dollar-neutrality (sum(w) ≈ 0) so the funding dodge holds. These properties are signal-orthogonal and do not depend on vol_low being the sole signal.
2. **The blended ranking re-applies the tail SKIP at the blended-signal level** — the bottom-5 blended-z names are skipped. In the agreement case (pumped mooner: low vol_low AND low rev_3), this is identical to EXPLORATION-002's tail SKIP. In the disagreement case (crashed coin: low vol_low BUT high rev_3), the coin may escape the SKIP band and enter the SHORT band — this is a known, gated risk (G-DEF-DD, G-DEF-REGIME), not an unanticipated failure.
3. **No new kill-switch is pre-registered beyond the G-ALPHA / G-EW / G-DEF-DD / G-DEF-REGIME / G-FUND / G-COST gates.** The gates ARE the kill-switch.
4. **Report (do not gate on, this iteration):**
   - Realized cross-sectional rank-corr(vol_low, rev_3) averaged over IS rebal steps — confirm ≈ −0.006 (matches DIAGNOSTIC-001; if material divergence, the combined-IC prediction is void).
   - Per-leg per-year price P&L for the blended book — confirm both legs contribute.
   - Per-year funding attribution for primary vs vol_low-only vs rev_3-only.
   - Max per-name weight (long ~5%, short ~10%; flag if any name > 20% — warmup edge effect may recur as in EXPLORATION-001/002).
   - Gross-leverage series (confirm mean ~1.0, no drift; confirm near-dollar-neutrality: mean|sum(w)| ≈ 0).
   - Turnover time-series by year (did rev_3 lift turnover uniformly, or concentrate in specific regimes?).

---

## Section 8 — Deliverable checklist for QE + risk-engineer

- [ ] Add `rev3_signal(panel, lookback=3)` loader (mirrors `lowvol_signal` past-only convention; formula verified against `blind_signal_ic_probe.py` line 116).
- [ ] Add `_cs_zscore_2d(arr, univ)` helper (per-timestamp cross-sectional z-score; past-only).
- [ ] Add `blended_signal(panel, univ)` (0.5·z(vol_low) + 0.5·z(rev_3)).
- [ ] **No engine change** — verify `target_weights_midvol_short` accepts the blended signal unchanged (it does — `rankdata` is signal-agnostic).
- [ ] 5 new tests in `tests/test_blind_engine.py` (rev3 past-only; cs-zscore past-only; blended end-to-end leak; blended-skips-agreement-outlier; blended-crashed-coin-lands-short). 23/23 green.
- [ ] Run script `analysis/portfolio/blind_exploration_003.py` producing a single committed table (runs 1–8 above) with per-year Sharpe for runs 1–5 and funding-by-year attribution for runs 1–3.
- [ ] **Parity check:** run-2 (vol_low-only) MUST reproduce EXPLORATION-002 run-1 Sharpe +0.09 bit-identically (tolerance ±0.005). If drift, the signal-engineering change perturbed vol_low — STOP and fix before evaluating anything else.
- [ ] Report realized cross-sectional rank-corr(vol_low, rev_3) averaged over IS rebal steps.
- [ ] Hand results to QR for Phase-7 evaluation against G-ALPHA / G-EW / G-DEF-DD / G-DEF-REGIME / G-FUND / G-COST (this brief). **Do not reveal OOS.**

---

**FROZEN.** Any change to the gates, blend weights, signal formulas, shell parameters, or run list after the first backtest run invalidates this pre-registration and must be recorded as a new EXPLORATION.
