# EXPLORATION-001 — Long-Only Low-Volatility Tilt (drop the short book)

## Section 0 — Provenance (pre-registration)

- **Frozen:** 2026-07-09, BEFORE any backtest run of this design. IS-only.
- **OOS sealed:** `OOS_CUTOFF = 2025-03-24`. Not looked at, not planned around.
- **Track:** baseline-blind top-20 L/S portfolio (this worktree).
- **Predecessors:** `DIAGNOSTIC-001-signal-ic.md` (signal screen), `DIAGNOSTIC-002-engine-lowvol-sanity.md` (naive L/S sanity, funding ON/OFF).
- **Blinding:** designed against `blind_engine.py` / `blind_universe.py` / `blind_funding.py` only. No baseline artifact read.

---

## Section 1 — Hypothesis (one sentence)

The low-vol cross-sectional rank-IC (+0.0523, stable across all 6 IS years, rising in 2025) is a real long-side anomaly whose **long leg alone — held long-only as an equal-weighted lowest-realized-vol-half of the PIT top-20 — is tradeable net-of-cost and regime-robust**, because the diagnosed failure (L/S Sharpe −0.18 at rebal=6, 2021 −1.86, maxDD −77%) was caused entirely by **short-side fat right-tail risk** (equal-dollar shorts of the 10–100× mania mooners that rank-IC's median-based measure hides) plus a **pro-cyclical funding drag on the short book** — both of which vanish when the shorts are dropped.

---

## Section 2 — Chosen mechanism + crypto-native rationale

### The one change

**Dollar-neutral rank L/S → long-only, equal-weighted lowest-vol-half.** No other structural change. Signal window (12-candle realized vol), universe (PIT top-20 by trailing 30-candle $-volume), rebalance cadence (rebal=6), cost model (taker 5bps + slip 2.5bps), and funding (ON) are all held identical to DIAGNOSTIC-002's sanity so the Sharpe delta is attributable solely to removing the short book.

### Why this is the right single change (not B/C/D)

The diagnosis in DIAGNOSTIC-002 was surgical: rank-IC is **positive every year including mania** (+.038 in 2020, +.068 in 2021) yet the L/S P&L is deeply negative in mania. The cause is **not** that low-vol fails to predict — it is that the *payoff* of shorting the highest-vol decile is catastrophically left-skewed: you collect modest premia in calm periods and then, exactly once per cycle, a coordinated retail mania sends the shorted lottery names 10–100× and the short book blows up. Funding does not rescue this (it is *pro-cyclical to the pain*: negative in the calm years where the L/S earns its money, so the short leg pays funding in exactly the good years).

Given that diagnosis, the mechanism options decompose as:

- **(A) Long-only tilt** — removes the failure mode at its source. No short book = no fat-tail blowup = no pro-cyclical short-funding drag. The book is allowed to be net-long per the brief. **This is the sharpest test of whether the long-side IC is monetizable at all.** It is also the cheapest turnover construction (no short-leg churn). A null result here is maximally informative: it would mean the long-side anomaly does not survive costs standalone, which is the prerequisite fact for any later short-side work.
- **(B) Asymmetric / mid-vol shorts** — addresses the tail but introduces 2+ new parameters (which vol band to short, per-name cap level) and still carries residual short-side tail risk. It is a *compromise* that muddies the diagnostic: if it works, we cannot attribute the win to "low-vol works" vs "we found the right short construction." Worse, the IC is monotone across the cross-section, so there is no principled vol-band cutoff that is not a tuning knob. **Defer to EXPLORATION-002** (only if this long-only book passes gates, to harvest the remaining cross-sectional alpha from a *risk-capped* short).
- **(C) Regime gate (flatten in mania)** — the wrong tool. The IC is *positive in mania* (+.068 in 2021). Flattening throws away a year where the cross-sectional signal is actually *stronger*. The problem was never the signal in mania; it was the short-side payoff function. A regime gate also introduces a regime detector + threshold = overfitting surface, and it would need to be calibrated on IS that contains only one full mania cycle (2020–21), making it fragile by construction.

**Verdict: (A).** It is the one change that removes the diagnosed failure mechanism directly, adds zero parameters, and produces a result interpretable in either direction.

### Crypto-native rationale for why long-only low-vol should work

1. **Retail lottery preference / preference for skewness.** Crypto retail systematically overpays for high-volatility, high-positive-skew names (memes, recently-pumped low-caps, degen narratives). This is the equity low-vol / betting-preference anomaly (Blitz, Baker-Hauger) **amplified** — crypto has a far heavier retail share, no shorting discipline to arbitrage the overpricing away, and leverage-driven liquidation cascades concentrated *in* the high-vol names (BIS WP 1087, 2025: carry shocks → liquidation jumps in the high-vol cohort). The flip side: "boring" low-vol large-caps are structurally under-owned and drift up on a risk-adjusted basis.
2. **The long-only construction captures the anomaly's primary Sharpe lever: vol reduction in the denominator.** The low-vol anomaly is fundamentally a minimum-variance effect — the expected return improvement is secondary to the Sharpe gain from holding a lower-vol portfolio. Within the top-20, equal-weighting the lowest-vol-half targets ~half the cross-sectional vol of EW-top-20. Even if absolute return is *equal* to EW-top-20, the Sharpe is materially higher because σ_p is lower. This is exactly the brief's objective (Sharpe, not return).
3. **Adverse selection is naturally mitigated on the long side.** DIAGNOSTIC-002 flagged that volume-rank entry is adverse-selected (a coin pumps into the top-20, then dumps). That adverse selection punished the *short* book (shorting the pump at the top). The low-vol-long book is the *opposite*: a coin that just pumped has *high* realized vol and is pushed *out* of the lowest-vol-half by construction. The long-low-vol-half holds names that have been quiet and large — established, liquid, less pump-exposed.
4. **Mania participation without mania blowup.** In 2021 the low-vol names did not moon as hard as DOGE/SHIB, but they participated in the rally (the IC being positive means low-vol outperformed high-vol *cross-sectionally*, and in a bull market that means low-vol was still up in absolute terms). The long-only book captures this upside; the L/S donated it all back (and more) on the short leg.
5. **Funding on a long-only book is pro-cyclical but bounded.** Longs pay positive funding in bull/manic regimes (2021: +0.0112%/8h) and earn negative funding in bear regimes (2022: −0.0027%, 2025Q1: −0.006%). This is a drag in good years and a bonus in bad — a partial natural hedge that slightly reduces Sharpe but also slightly reduces drawdown, and is dwarfed by the price action. It must be modeled (funding ON) but is not the dominant term.

---

## Section 3 — Exact implementation spec (for the quant-engineer)

### 3.1 Signal (UNCHANGED from DIAGNOSTIC-002 sanity)

```python
def lowvol_signal(panel, window=12):
    ret = pd.DataFrame(panel.close).pct_change().to_numpy()
    rv = pd.DataFrame(ret).rolling(window, min_periods=max(4, window // 2)).std().to_numpy()
    return -rv   # high signal = low realized vol = want-long
```

Window = 12 candles (4 days at 8h). Held identical to the sanity so the only variable is the weighting. The signal is past-only (uses `close[t-12:t]` to decide at `close[t]` → fill `open[t+1]`); leak-safe by the engine's existing convention.

### 3.2 Universe (UNCHANGED)

`pit_topn_universe(panel, top_n=20, lookback=30)` — PIT top-20 by trailing 30-candle quote-volume, ex-stables, re-ranked every 8h. IS slice: `is_mask(panel)` (`open_time < OOS_CUTOFF_MS`).

### 3.3 NEW weighting code path (the one code change)

Add a `weighting: str` parameter to `run_backtest(...)`. Three modes dispatch to target-weight builders:

| `weighting` | builder | description |
|---|---|---|
| `"rank_neutral"` (default) | existing `target_weights` | rank-demean dollar-neutral (backward-compatible; reproduces DIAGNOSTIC-002) |
| `"longonly_tophalf"` | NEW `target_weights_longonly(..., long_frac=0.5)` | equal-weight the highest-signal (lowest-vol) half of valid universe members; long-only; sum(w)=gross |
| `"ew_long"` | NEW `target_weights_longonly(..., long_frac=1.0)` | equal-weight ALL valid universe members long-only → **the EW-top-20 benchmark** |

Implementation of the new builder (pseudo-code — QE to harden, but the logic is pinned here):

```python
def target_weights_longonly(signal_row, univ_row, gross, long_frac):
    w = np.zeros_like(signal_row, dtype=float)
    m = univ_row & np.isfinite(signal_row)
    n = int(m.sum())
    if n < 2:
        return w
    r = rankdata(signal_row[m]) - 1.0      # 0 = lowest signal
    k = max(1, int(round(n * long_frac)))  # number of longs (long_frac=0.5 → 10 of 20)
    threshold = n - k
    long_mask = r >= threshold             # highest-signal k names
    cnt = int(long_mask.sum())
    if cnt == 0:
        return w
    w[m] = np.where(long_mask, gross / cnt, 0.0)
    return w
```

Notes for the QE:
- `rankdata` average-rank ties may give cnt = 11 occasionally (two coins tied at the threshold). This is acceptable and even desirable (robustness); do NOT add a tie-breaker.
- When `long_frac=1.0`: `k=n`, `threshold=0`, all valid members selected → equal-weight. This is the EW-top-20 benchmark, computed through the SAME cost/funding/rebal pipeline (apples-to-apples).
- The function must satisfy: `w[~univ] = 0`, `w[invalid_signal] = 0`, `sum(w) = gross` (all-positive → no dollar-neutrality). Verify in the unit test.

### 3.4 Backtest configuration (primary)

| parameter | value | rationale |
|---|---|---|
| `weighting` | `"longonly_tophalf"` | the one change |
| `gross` | `1.0` | held from sanity; 100% long, no leverage base |
| `rebal` | `6` | held from sanity's best case (48h cadence); isolates the one change |
| `vol_target_ann` | `None` (primary) / `0.40` (secondary overlay) | primary = pure isolation of the long-only switch; secondary = standard vol-target overlay (max_lev=2.0, vol_lookback=63). **Report both.** The vol-target is a risk primitive, not a signal change — but to keep "one change" honest, the primary gate applies to the no-VT variant. |
| `cost` | `CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)` | held from sanity; honest Binance Futures rates |
| `funding` | `load_funding(panel)` | ON — bucket-summed per `blind_funding.py` |

### 3.5 Required runs (all IS-only, all reported in one table)

1. **Primary book:** `weighting="longonly_tophalf"`, rebal=6, funding ON, no VT.
2. **Vol-targeted book:** same + `vol_target_ann=0.40`, `max_lev=2.0`.
3. **EW-top-20 benchmark:** `weighting="ew_long"`, rebal=6, funding ON, no VT. ← **the critical comparison.**
4. **B&H BTC:** existing `buy_hold_btc(panel)`. (already +1.07 / +60% per sanity).
5. **Cost-stress (primary book at 2x cost):** `CostModel(taker_fee_bps=10.0, slippage_bps=5.0, funding_enable=True)`.
6. **(Attribution) L/S sanity reproduction:** `weighting="rank_neutral"`, rebal=6, funding ON — to confirm the engine still reproduces DIAGNOSTIC-002's −0.18 (parity check; not a gate).

All six share the same IS-truncated panel (`slice_is`). Per-year Sharpe must be reported for runs 1–3.

### 3.6 Mandatory test extension (leak-safety)

Extend `tests/test_blind_engine.py` with a positive-control leak test for the new path: build the synthetic panel, run `weighting="longonly_tophalf"`, corrupt signal + open prices from a cutoff forward, assert past weights/turnover/equity are bit-identical (mirror the existing `test_future_corruption_leaves_past_identical`). Also assert `sum(w) == gross` and `all(w >= 0)` at every rebal step (long-only + gross discipline), and that `weighting="ew_long"` with a constant signal gives equal weights across all universe members. **5/5 (existing) + 3 new = 8 green before any MERGE evaluation.**

---

## Section 4 — Pre-registered IS MERGE / NO-MERGE criteria (FROZEN)

Gates apply to the **primary book** (run 1, no VT). VT variant is reported for information. All gates evaluated IS-only. Any single failure → NO-MERGE; the diary records which gate and the observed value.

| # | gate | threshold | what it tests |
|---|---|---|---|
| G1 | **IS Sharpe (primary)** | `≥ 1.0` | absolute risk-adjusted floor; in the ballpark of B&H-BTC (+1.07) |
| G2 | **IS Sharpe (primary) > IS Sharpe (EW-top-20)** | strict `>` | **the key test:** does the low-vol tilt add net-of-cost value over naive equal-weight? If the tilt can't beat EW, the anomaly is not tradeable here. |
| G3 | **MaxDD (primary)** | `≥ −55%` | improved from L/S −77%; crypto-realistic for a long-only book through a full bull-bear cycle |
| G4 | **Per-year Sharpe (primary), every year** | `≥ −1.0` in each of {2020,2021,2022,2023,2024,2025Q1} | **regime-robustness — the diagnosed failure mode must be addressed.** The L/S had 2021 = −1.86; no year of the long-only book may be that bad. (A long-only book in the 2022 bear will be negative — that is expected; it must not be catastrophic.) |
| G5 | **Turnover (primary)** | `≤ 100x/yr one-way` | cost control; L/S was 108x at rebal=6 — the long-only-half should be strictly lower (no short-leg churn, coarser membership) |
| G6 | **Cost-stress (2x cost)** | IS Sharpe `≥ 0.7` | robustness to the cost assumption; if doubling cost collapses the Sharpe, the edge is marginal / turnover-dependent |

**What makes me NO-MERGE** (each failure points to a specific next exploration):
- **G2 fails:** the long-side low-vol anomaly does not survive costs as a standalone book. → Pivot to EXPLORATION-002 = **tail-capped / mid-vol shorts** (complete the anomaly with a risk-managed short that harvests cross-sectional alpha without the extreme-vol lottery exposure).
- **G4 fails (some year < −1.0):** regime-fragility not solved by long-only alone (the long leg still has a catastrophic regime — likely a correlated deleveraging crash). → Pivot to EXPLORATION-003 = **regime gate** (scale gross by a cross-sectional-dispersion or BTC-vol-regime scalar) or a **defensive risk primitive** (drawdown brake).
- **G1 fails but G2 passes:** the tilt beats EW but neither clears 1.0 → the top-20-$-volume universe itself is too costly/adverse-selected at 8h. → Pivot to EXPLORATION-004 = **OI-ranked universe** (DIAGNOSTIC-002 data discovery: historical OI is available via `data.binance.vision` daily archives → 8h; less adverse-selected than $-volume).
- **G5 fails:** turnover is the bottleneck even after dropping shorts. → EXPLORATION-005 = **hysteresis bands** on universe membership / rebal=12.
- **G6 fails:** edge is cost-fragile. → same turnover-reduction pivot.

---

## Section 5 — Predicted behavioral effect (pre-registered, so a null is informative)

| metric | prediction (primary book, no VT) | confidence |
|---|---|---|
| **IS Sharpe** | **+1.0 to +1.5** (above B&H-BTC +1.07 and above EW-top-20) | moderate-high. Primary Sharpe lever is **vol reduction in the denominator** (low-vol-half portfolio σ ≪ EW-top-20 σ), not return alpha. |
| **vs EW-top-20 Sharpe** | primary exceeds EW by **+0.15 to +0.40** Sharpe units | high. This is the core low-vol-anomaly prediction. |
| **2021 (mania) Sharpe** | **+0.3 to +1.2** (vs L/S −1.86) | high direction. Low-vol longs participate in the rally; no short blowup. |
| **2022 (bear) Sharpe** | **−0.3 to −0.8** | moderate. Long-only in a bear market is inevitably negative; low-vol large-caps fall less than alts but still fall. |
| **MaxDD** | **−35% to −50%** (vs L/S −77%) | moderate. Lower-vol book → shallower drawdowns. |
| **Turnover** | **45–80x/yr** one-way (vs L/S 108x) | high. No short-leg churn; bottom-half membership is coarser than rank-magnitudes. |
| **Funding net effect** | small **drag** on Sharpe (longs pay in bull years), larger drag in 2021 than elsewhere | high. Must be ON; not expected to dominate. |
| **VT variant (vol_target=0.40)** | Sharpe **+0.1 to +0.3 above no-VT**; MaxDD improved ~5–10pp | moderate. Standard vol-targeting gain when vol is clustered and persistent. |

**What a null looks like:** IS Sharpe +0.5–0.7, at or below EW-top-20. This would mean the long-side low-vol selection does not generate enough cross-sectional alpha (or vol reduction) to clear the ~4–5%/yr cost drag at rebal=6. It is not a death sentence for the low-vol axis — it is the prerequisite fact that motivates adding a *risk-capped* short leg (EXPLORATION-002) to complete the anomaly. **The null is informative, not terminal.**

---

## Section 6 — What this does NOT do (scope discipline — ONE change)

Explicitly deferred to later EXPLORATIONs (listed so the Critic can verify no scope creep):

- **NO short book at all** (not even mid-vol / risk-capped). EXPLORATION-002 candidate.
- **NO regime gate** (no cross-sectional-dispersion scalar, no BTC-vol-regime flatten). EXPLORATION-003 candidate.
- **NO multi-factor combination** with `rev_3` (IC +0.045, orthogonal to vol_low at corr −0.006 — a natural complement). EXPLORATION-004 candidate.
- **NO universe change** (still PIT top-20 by trailing 30-candle $-volume). OI-based ranking (DIAGNOSTIC-002 data discovery: daily OI archives → 8h are available) deferred to a dedicated universe EXPLORATION.
- **NO signal-window change** (12-candle realized vol, same as the IC screen and sanity).
- **NO per-name weight caps, hysteresis bands, or eligibility-exit logic.**
- **NO weighting-shape optimization** (equal-weight bottom-half is the parameter-free choice; inverse-vol / signal-proportional / min-variance weighting is an EXPLORATION-002 lever if this passes).
- **NO OOS peek.** The OOS_CUTOFF=2025-03-24 wall is untouched. OOS is revealed once at CONFIRMATION, never during EXPLORATION.

---

## Section 7 — Risk primitive (for the risk-engineer)

The brief requires an explicit risk-mitigation design. For EXPLORATION-001 the risk primitives are deliberately minimal (one change):

1. **Long-only** is itself the risk primitive — it removes the short-side tail-risk blowup identified in DIAGNOSTIC-002. This is the primary risk mitigation.
2. **Vol-target overlay (secondary variant, vol_target_ann=0.40, max_lev=2.0):** standard Carver-style vol targeting. Scalar computed from trailing 63-candle (21-day) realized portfolio vol, capped at 2.0× leverage. De-risks in turbulent regimes (2022 bear, 2020-03 COVID), up-leverages in calm. Report the effect on Sharpe and MaxDD vs the no-VT primary.
3. **Report (do not gate on, this iteration):** max per-name weight (flag if any name >20% — concentration risk for the cap discussion in EXPLORATION-002), gross-leverage time series (confirm no drift), and per-year funding contribution (confirm funding is not the dominant term).

No new kill-switch is pre-registered for EXPLORATION-001 beyond the G1–G6 gates. The gates ARE the kill-switch.

---

## Section 8 — Deliverable checklist for QE + risk-engineer

- [ ] Implement `target_weights_longonly` + `weighting` dispatch in `blind_engine.py`.
- [ ] 3 new tests in `test_blind_engine.py` (leak positive-control for new path; long-only+gross discipline; ew_long constant-signal equality). 8/8 green.
- [ ] Run script `analysis/portfolio/blind_exploration_001.py` producing a single committed table (runs 1–6 above) with per-year Sharpe for the primary, VT, and EW runs.
- [ ] Report max per-name weight, gross-leverage series, funding-by-year attribution.
- [ ] Hand results to QR for Phase-7 evaluation against G1–G6 (this brief). **Do not reveal OOS.**

---

**FROZEN.** Any change to the gates, signal, weighting, or parameters after the first backtest run invalidates this pre-registration and must be recorded as a new EXPLORATION.
