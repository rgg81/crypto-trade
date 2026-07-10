# EXPLORATION-006 — Mania-Aware Risk-Overlay Stack on the /005 Weekly Mid-Vol Neutral (IS-only, pre-registered)

## Section 0 — Provenance & scope (pre-registration)

- **Frozen:** 2026-07-10, BEFORE any variant backtest runs. This brief is the frozen contract;
  the engineer runs the matrix ONCE and the results are scored against the gates below. **No
  post-hoc tuning is permitted** — any change to construction, controls, gates, month lists, or the
  decision tree after the run invalidates the pre-registration and must be recorded as a new
  EXPLORATION.
- **Track:** baseline-BLIND top-20 L/S portfolio (worktree `quant-portfolio-blind`).
- **BASELINE-BLINDING intact.** Designed against `blind_*` modules + the blind diaries
  (DIAGNOSTIC-003, RISK-006, EXPLORATION-005 engineering/PHASE7/REVIEW) only. **No baseline
  artifact read** (`BASELINE_PORTFOLIO.md`, `analysis/portfolio/iter_*.py`, `diary-portfolio-top20/`,
  sibling worktrees — none touched).
- **OOS QUARANTINE — this is an IS-ONLY phase end to end. There is NO OOS reveal in EXPLORATION-006.**
  `OOS_CUTOFF = 2025-03-24` is sealed; `CONFIRMATION-005.md` (burned OOS numbers) was NOT read.
  Every number produced by the matrix is computed on candles `open_time < 2025-03-24`. **The
  verdict semantics below are IS-level only.** The deliverable is a *regime-robust design validated
  in-sample* + IS evidence, explicitly **NOT** a deployability claim. Deployability is decided by a
  FUTURE, separate forward-validation protocol that this brief does not run and does not preview.
- **Backtests run by this QR: exactly ONE — the /005 V0 parity construction** (Critic-permitted under
  REVIEW-006-preflight Condition 1, for the market-only mania-bucket definition + V0 mania-baseline
  recompute). It reproduced /005 to the digit (Sharpe +0.9134, maxDD −32.99%, turnover 55.4x, crash
  bucket +2.586% ≡ DIAGNOSTIC-003's +2.59%), confirming faithfulness. **No variant/search backtest was
  run** — the 9-run matrix remains the engineer's single frozen pass. Separately, a pure market-regime
  classification (BTC monthly return + trailing-540 drawdown) reproduced DIAGNOSTIC-003's 20-month
  CRASH bucket exactly (all 13 shown months matched, plus the 7 not shown; §3.3).
- **Post-preflight revision (REVIEW-006-preflight PASS-WITH-CONDITIONS, 2026-07-10):** the MANIA bucket
  was re-defined by a committed MARKET-ONLY rule (`analysis/portfolio/blind_mania_rule.py`), replacing
  the retired P&L-tracking hand list (Condition 1); §3.3/§6 C1-crash predictions corrected (Condition
  2); decision-tree Rule 2 pinned to crash(L2) (Condition 3); G-turnover metric source stated
  (Condition 4); §7 ledger notes + selection-bias disclosure added (Condition 5). No calibrated C1–C5
  value was unfrozen.

### 0.1 The design thesis (one paragraph)

DIAGNOSTIC-003 overturned the naive "de-risk the crashes" framing. The /005 book (Sharpe +0.913,
maxDD −33%, all six IS years positive) **already wins BTC-crash months** (+2.59%/mo mean, 70% win
across the 20 market-defined crash months), and that crash P&L is carried **entirely by the SHORT
leg** (+1.531 aggregate short-price P&L over the 20 crash months vs −0.892 for the long leg). The
book's *true* fragility is the opposite regime: an **alt-mania short squeeze** in BTC-UP months with
blown-out cross-sectional dispersion (2020-11, 2021-Q1, 2023-12, 2024-Q1, 2024-11), where the
short-high-vol leg is run over (the worst-10 strategy months are −1.467 short-leg loss, 165% of
combined price P&L; 7 of 10 are BTC-UP months). The book is also fat-concentrated (top-10 months =
98.8% of log-growth), so any control that clips the right tail guts the Sharpe. **The operational
reading of the user directive** ("succeed in ALL conditions, ESPECIALLY the worst price-drop months;
a decent Sharpe is fine, need not be 0.91"): the worst *price-drop* months are the crash bucket,
which the book already wins — so **PRESERVE the crash-month strength (it must not degrade)**, **FIX
the mania-month short squeeze** (the actual drawdown driver), **keep all IS years positive**, and
**accept a Sharpe haircut** in exchange for that robustness. This phase tests a **mania-aware
risk-overlay stack** (RISK-006's five ex-ante-calibrated controls) that attacks exactly that
regime, isolated per-control and composed as a nested ladder.

---

## Section 1 — Hypotheses + crypto-native mechanism (one paragraph per control)

All five controls are RISK-006's frozen calibrations (ex-ante indicator statistics; NO Sharpe-based
tuning). Adopted here verbatim (see §2.6 for the single non-value handling note).

**C1 — Mania-regime SHORT-leg gate (LEAD).** *Mechanism:* in a crypto alt-mania, retail leverage
and reflexive momentum drive lottery/high-vol alts 3–10× while BTC rips; the short-high-vol leg of a
vol-ranked neutral book is structurally on the wrong side of that squeeze (short_px −0.282 in
2020-11, −0.391 in 2024-11). A regime gate that fires on **BTC momentum up (63c > +9%) AND
(cross-sectional dispersion blow-out OR funding blow-off)** and cuts the short half-gross to a floor
of 0.5× surgically removes the squeezed short exposure while leaving the mania-winning LONG leg
untouched (in every one of RISK-006's 9 originally-named mania months the long leg is POSITIVE,
+0.06…+0.29 — those 9 are RISK-006's *calibration* months, distinct from this brief's committed
13-month G-mania bucket of §3.4). The **BTC-UP requirement is load-bearing**: it mechanically forbids
the gate from firing in any BTC-DOWN capitulation month, structurally preserving the short leg's crash
alpha there (RISK-006 §1.1, §1.3: all 9 calibration-mania months flag, mean 58%; the named BTC-down
capitulation crash months de-flag, mean 1%). *Evidence:* RISK-006 §1.4
first-order MANIA-bucket P&L delta at floor 0.5 = **+0.492**, positive in every bucket, total
+1.001.

**C2 — Per-name parabolic short-exclusion (intra-week squeeze defense).** *Mechanism:* C1 is a
weekly *regime* gate; it cannot see a single coin that 3–10×'s between weekly rebalances. The
canonical squeeze fuel is a name that has just gone parabolic — a coin up >30% in 7 days is precisely
the one that will keep squeezing a short. Excluding any short-band name with **trailing-21c return >
+30%** from the short leg (moving it to SKIP, not shorting it) removes that name at entry. *Evidence:*
RISK-006 §2.2–2.3: the excluded set (5.6% of short-name-candles at Q=+30%) had **−4.08 aggregate
forward short-price P&L** — deeply net-losing, i.e. exactly the squeeze fuel; the 2024-11 audit shows
C2 excludes DOGE +89% / ADA +49% / PEPE +38% on the 11-13 rebalance (the squeeze peak), the exact
names that ran the short leg to −0.391 that month. **SHRINK budget mode** (do NOT re-spread the freed
budget over survivors): in a *broad* mania many mid-vol names are parabolic at once; re-spreading
would concentrate the short into the few survivors, which are themselves squeeze-prone. Shrinking
naturally de-risks the short leg exactly when mania is broad, tilting the book mildly net-long — the
same acceptable direction as C1.

**C3 — Portfolio vol-targeting (second-moment governor).** *Mechanism:* portfolio realized vol
spikes in the loser months; scaling gross to a **0.25 annualized target** (trailing-45c realized
vol, max_lev 1.0 = never lever up) auto-shrinks the book into high-vol regimes. This is the honest,
mechanically-neutral second-moment lever. *Evidence & honest cost:* RISK-006 §3.2 — at vt=0.25 the
top-10-month mean scale (0.876) EQUALS the all-candle mean scale (0.876): the winners are **not**
disproportionately high-vol, so C3 is a **uniform ~12% de-gross**, not a winner-selective clip. It
is symmetric, so it also shaves the crash months the book WINS (the acceptable, bounded cost that
makes C3 only the #3-priority lever). max_lev=1.0 because a moderate-edge, 10-month-concentrated book
must never lever into calm regimes that precede spikes (crypto fat tails make the Kelly point fragile
to vol mis-estimation).

**C4 — Drawdown circuit brake (tail insurance).** *Mechanism:* a past-only, own-equity hysteresis
brake that halves gross when the book's trailing drawdown breaches −20% and releases at −10%. It is a
regime-agnostic backstop for the tail cases C1/C2 leave on the table (fast intra-week squeezes and
the funding-grind loss). *Evidence:* RISK-006 §4.2 — at −20%/−10% it engages **4 times over 5.25 IS
years** (2020-11, 2023-09, 2024-05, 2024-11), all of which are alt-mania squeeze / funding-grind
losers and **none of which are in the 20-month crash bucket** (verified §3) — so C4 caps mania-tail
*depth* without touching crash alpha. scale=0.5 (not flatten) because deep drawdowns here are often
followed by strong recovery months (e.g. 2024-05 −20% → 2024-06 +12.1%, a top-10 month); flattening
would lock out the rebound and pay full round-trip turnover. C4 adds little Sharpe (the squeeze losses
are fast; the brake engages after the worst candle) — it is a maxDD-tail layer, not an alpha lever.

**C5 — BTC-crash de-risk (FALSIFICATION ARM — pre-registered to HURT).** *Mechanism (the thing the
diagnostic says is WRONG):* a whole-book gross cut on BTC trailing drawdown (`btc_drawdown_scalar`
540/0.20/0.30/0.30). Applied whole-book it cuts BOTH legs in BTC-drawdown regimes — exactly where the
SHORT leg delivers the crash alpha. *Pre-registered prediction:* NEGATIVE net — worse crash bucket,
≈0 mania (BTC is up in mania → no BTC drawdown → scalar ≈ 1.0), nothing where the real problem is.
C5 is NEVER part of any candidate; it exists only to confirm the redesign attacks the RIGHT regime.
If C5 *improves* Sharpe or the crash bucket, the diagnostic thesis is indicted (§5 mandatory verdict).

---

## Section 2 — Construction (frozen, exact)

### 2.1 Base book = EXPLORATION-005, byte-frozen

```python
panel_is = slice_is(load_panel())                       # HARD IS slice at top
sig      = lowvol_signal(panel_is, window=12)
univ     = pit_topn_universe(panel_is, top_n=20, lookback=30)
fund     = load_funding(panel_is, verbose=False)         # funding ON
cost     = CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)
# base run:
run_backtest(panel_is, sig, univ, cost, gross=1.0, rebal=21,     # weekly — KEPT
             funding=fund, weighting="midvol_short",
             long_frac=0.5, short_frac=0.25)
# warmup = max(vol_lookback, 30) = 63 candles (V0). See §2.6 for the C3 caveat.
```

**Weekly rebalance is KEPT** (rebal=21), per the user directive. No change to signal, universe,
cost, gross, fractions, weighting, or funding. The ONLY additions are the opt-in risk controls below,
all of which are byte-identical to the base when off (44/44 tests, positive controls green).

### 2.2 The five controls — FROZEN parameter values (RISK-006, adopted verbatim)

| Ctrl | Parameter | **FROZEN value** | Engine hook |
|---|---|---|---|
| **C1** | btc_mom_lookback / btc_mom_thr | **63c / +0.09** | `short_scalar_series` (T,) |
| C1 | disp_lookback / z_win / z_thr | **21 / 365 / +0.5** | (feeds the gate) |
| C1 | fund_lookback / z_win / z_thr | **21 / 365 / +0.5** | (feeds the gate) |
| C1 | combination | **btc_up AND (disp_hi OR fund_hi)** | |
| C1 | application / floor | **SHORT-leg-only, floor 0.5×** | `short_scalar_series[t] ∈ {0.5, 1.0}` |
| **C2** | K / Q | **21c / +0.30** | `short_exclude` (T,C) bool |
| C2 | budget mode | **SHRINK** | `short_exclude_mode="shrink"` |
| **C3** | vol_target_ann | **0.25** | `vol_target_ann=0.25` |
| C3 | vol_lookback / max_lev | **45 / 1.0** | `vol_lookback=45, max_lev=1.0` |
| **C4** | dd_brake_threshold | **0.20** | `dd_brake_threshold=0.20` |
| C4 | dd_brake_scale / recovery | **0.5 / 0.10** | `dd_brake_scale=0.5, dd_brake_recovery=0.10` |
| **C5** (falsify) | btc_drawdown_scalar | **540 / 0.20 / 0.30 / 0.30, whole-book** | `gross_scalar_series` (T,) |

### 2.3 C1 indicator series — EXACT construction (implement without decisions)

The C1 gate is **already implemented** as `mania_gate()` in `analysis/portfolio/blind_risk_calib_006.py`
(committed). The engineer MUST reuse it verbatim (import or port into a shared module) to guarantee
zero drift. Its logic, restated for the record — all inputs known at `close[t]` (past-only):

```
btc_mom[t]  = close_BTC[t] / close_BTC[t-63] - 1                       # NaN for t < 63
btc_up[t]   = btc_mom[t] > +0.09
rK_i[t]     = close_i[t] / close_i[t-21] - 1        (per name; NaN if close[t-21] <= 0 / t<21)
disp[t]     = std_{i : univ[t,i] & finite(rK_i[t])} ( rK_i[t] ), ddof=1   # only if >= 4 members
fmean[t]    = mean_{i : univ[t,i] & finite(fund_tr_i[t])} ( fund_tr_i[t] ), where
             fund_tr_i[t] = rolling-21 mean of funding_i (min_periods=10)     # only if >= 4 members
z365(x)[t]  = (x[t] - roll_mean_365(x)[t]) / roll_std_365(x, ddof=1)[t],  min_periods = 182
disp_hi[t]  = z365(disp)[t]  > +0.5
fund_hi[t]  = z365(fmean)[t] > +0.5
gate[t]     = btc_up[t] AND (disp_hi[t] OR fund_hi[t])
```

Then: `short_scalar_series[t] = np.where(gate[t], 0.5, 1.0)`.

- **NaN policy at the panel edge (frozen):** any comparison against a NaN component evaluates to
  `False` (numpy semantics), so `gate[t]` is `False` wherever `btc_mom`, `disp`, or the z-scores are
  NaN (early candles before `min_periods`) → `short_scalar_series[t] = 1.0` (inert, full short leg).
  This is the safe default: the gate can only ever *reduce* the short leg, never manufacture one.
- **Consumption lag (frozen):** pass `short_scalar_series` indexed by `t` (aligned to `close[t]`).
  The engine consumes it at `[k-1]` internally (`target_weights_midvol_short(..., short_scalar=
  short_scalar_series[k-1])`, verified `blind_engine.py:509`). **Do NOT pre-shift** — the engine
  applies the one-candle decision lag, exactly as it does for `signal[k-1]`. Pre-shifting = double lag.

### 2.4 C2 indicator series — EXACT construction

```
rK_i[t] = close_i[t] / close_i[t-21] - 1                 # SAME 21c return as C1's rK; reuse it
short_exclude[t, i] = (rK_i[t] > +0.30)                  # NaN -> False (do not exclude on missing)
short_exclude_mode  = "shrink"
```

- The engine consults `short_exclude[k-1]` and demotes only names actually in the SHORT band to SKIP
  (rank partition unchanged; long band + skip tail untouched — `blind_engine.py:191-219`). "shrink"
  fixes per-name short weight at `short_half / n_short_band_original`, so total short gross falls by
  the excluded fraction (book net-longs by that amount).
- **Consumption lag (frozen):** pass `short_exclude` indexed by `t`; engine reads `[k-1]`. Do NOT
  pre-shift.

### 2.5 C5 indicator series (falsification)

`gross_scalar_series` = `btc_drawdown_scalar(panel, lookback=540, threshold=0.20, band=0.30,
floor=0.30)` (the `blind_regime` module default), applied WHOLE-book. Consumed at `[k-1]`
(`blind_engine.py:490`). Already leak-tested in `test_blind_engine.py` (RISK-006 §7).

### 2.6 The ONE handling note — NO parameter changed; a reporting-comparability fix (load-bearing)

**I adopted every RISK-006 value verbatim — zero parameter adjustments.** There is exactly ONE
engine-mechanics interaction that MUST be handled, and it is a *reporting protocol*, not a value
change:

`run_backtest` computes its metric warmup as `warmup = max(vol_lookback, 30)` (`blind_engine.py:582`).
C3 sets `vol_lookback=45`, so any C3-containing run (V3, L2, L3) would internally compute its metrics
over a warmup of **45**, while the non-C3 runs (V0, V1, V2, V4, V5) use **63** (default). That would
(a) make Sharpe/maxDD non-comparable across variants (different denominators) and (b) inject the
universe lookback-ramp edge artifact (candles 45–62, flagged by REVIEW-001 S4) into the C3 runs only.

**Frozen fix:** the report harness computes **ALL** comparative metrics (headline Sharpe, 2×-cost
Sharpe, maxDD, per-year Sharpe, worst month, monthly win rate, top-10 concentration, and BOTH bucket
aggregates) for **every** variant on a **common, frozen post-warmup slice starting at candle index
63** — i.e. re-slice `res.rets[63:]` (and equity/turnover correspondingly) uniformly, and do NOT use
`res.metrics` for cross-variant comparison when `vol_lookback != 63`. C3's `vol_lookback=45` is
UNCHANGED (it still governs the vol-target scale's own trailing window); only the *metric-reporting
warmup* is frozen at 63 for all nine runs. The 20-month CRASH and 13-month MANIA month lists (§3) are
defined on this warmup=63 month set (the mania rule uses `warmup=63` in `blind_mania_rule.mania_months`).
This is a comparability invariant, not a tuning knob.

**Metric-source note (REVIEW-006-preflight F4) — the ONE exception to the `[63:]`-recompute rule.**
Every HARD-gate metric EXCEPT turnover is recomputed on the common `res.rets[63:]` slice with equity
**rebased at index 63** (Sharpe, 2×-cost Sharpe, maxDD, per-year Sharpe, worst month, and both bucket
aggregates). **G-turnover is the exception:** it reads `res.metrics['turnover_ann_one_way']`, which
`_metrics` computes as `res.turnover.mean() * PERIODS_PER_YEAR` over the FULL array
(`blind_engine.py:616-618`) — this is already cross-variant comparable (turnover has no warmup-edge
inflation), so no re-slice is applied to it. State this in the report so the turnover figure's
provenance is unambiguous.

---

## Section 3 — Frozen variant matrix + frozen bucket month lists

### 3.1 The nine runs (frozen run list)

| Run | Stack | Purpose |
|---|---|---|
| **V0** | /005 base, no controls | parity control (must reproduce +0.913) |
| **V1** | C1 only | isolation — mania short-leg gate |
| **V2** | C2 only | isolation — parabolic short-exclusion |
| **V3** | C3 only | isolation — vol-target governor |
| **V4** | C4 only | isolation — DD brake |
| **V5** | C5 only | **FALSIFICATION** — BTC-crash de-risk (pre-registered to HURT) |
| **L1** | C1 + C2 | ladder — marginal of C2 over C1 |
| **L2** | C1 + C2 + C3 | ladder — marginal of C3 |
| **L3** | C1 + C2 + C3 + C4 | ladder — marginal of C4 → full stack |

Singletons (V1–V5) give per-control **isolation** (the user's explicit ask); the ladder (L1–L3)
gives **marginal contributions** in RISK-006's priority order. C5 is a singleton falsification only —
it never enters the ladder.

### 3.2 Standard characterization per run (all 9, on the frozen warmup=63 slice)

For EACH run report: IS Sharpe (honest cost), 2×-cost Sharpe, maxDD, turnover (ann one-way), ann
return, monthly win rate, per-year Sharpe {2020, 2021, 2022, 2023, 2024, 2025Q1}, worst single
calendar month, **top-10-month concentration share** (fraction of total log-growth), and the two
frozen bucket aggregates below, each with **leg-level P&L** (aggregate long_px / short_px / net_fund
over the bucket's candles).

### 3.3 CRASH bucket — 20 market-defined months (FROZEN; copied from DIAGNOSTIC-003 criterion)

Market definition (DIAGNOSTIC-003 §2, `blind_diag_003_monthly.py`): a month is CRASH iff
`btc_ret_m < −15%` **OR** `btc_dd_end(540) > 25%`. Reproduced exactly by this QR (pure BTC
classification, IS-sliced, warmup=63; all 13 DIAGNOSTIC-003-shown months matched):

```
2020-03, 2021-05, 2021-06, 2021-07, 2021-08, 2021-09, 2021-12, 2022-01, 2022-02, 2022-03,
2022-04, 2022-05, 2022-06, 2022-07, 2022-08, 2022-09, 2022-10, 2022-11, 2022-12, 2025-02
```
(20 months.) **V0 reference:** mean strat return **+2.59%/mo**, win rate **70%**, aggregate leg P&L
long_px −0.892 / short_px **+1.531** / net_fund −0.035 (short leg carries the crash alpha).
Note: none of C4's 4 engagement months (2020-11, 2023-09, 2024-05, 2024-11) is in this bucket.

**IMPORTANT correction (REVIEW-006-preflight F2) — the crash bucket splits into two sub-regimes for
C1:**
- **(i) BTC-DOWN capitulation crash** (btc_ret_m < 0; the majority — 2020-03, 2021-05/06/09/12,
  2022-01/04/05/06/08/09/11/12, 2025-02): C1 is **structurally inert** here (`btc_up` requires
  `btc_mom_63 > +9%`, false in a capitulation) → the short leg runs at FULL gross and delivers the
  crash alpha (+1.531 aggregate short_px). This is the property that must NOT be degraded.
- **(ii) BTC-UP bear-rally crash** (btc_ret_m > 0, qualifying via the trailing-DD clause — 2021-07,
  2021-08, 2022-02, 2022-03, 2022-07, 2022-10): here **C1 CAN fire**, and in the squeeze months
  (2021-08 short_px −0.142; 2022-07 short_px −0.146 — bear-market rallies that ran the short leg over)
  **C1 firing HELPS**. So C1 activity inside the crash bucket is not a violation — it is the same
  mania-squeeze mechanism appearing inside a deep-DD flag.

Therefore crash-bucket P&L is degraded ONLY by C3's symmetric de-gross (C1 is inert in capitulation
and net-helpful in bear-rallies; C2 rarely fires — alts seldom +30%/7d in a crash). The **2022-07→08
turn** (bear rally → resumed decline while flagged) is an unexamined stress case (RISK-006's tail
scenario covered only the 2021-04→05 turn) — the engineer must report C1 flag coverage across ALL 20
crash months so G-crash preservation is attributed to the right sub-regime (§8).

### 3.4 MANIA bucket — 13 months from a COMMITTED MARKET-ONLY rule (FROZEN; REVIEW-006-preflight F1 fix)

**The pre-flight Critic (F1) rejected the original hand-authored 9-month list because its boundary
tracked strategy P&L** (2023-01 flagged 62% by the C1 detector yet EXCLUDED — a strategy winner
+3.1%; 2023-11 flagged 43% yet EXCLUDED; 2021-03 flagged only 23% yet INCLUDED — a strategy loser).
That made G-mania near-tautological. The bucket is now defined by a **committed, reproducible,
market-only rule** (`analysis/portfolio/blind_mania_rule.py`, with a `__main__` reproducibility
self-test):

> **MANIA(month) iff the fraction of its post-warmup candles flagged by the committed C1 `mania_gate`
> is ≥ 0.40.**

- The C1 gate is market-only (`btc_up AND (disp_hi OR fund_hi)`) with a **trailing-365-candle z**
  (min_periods 182) — a LOCAL normalization that correctly identifies the 2020-Q4 mania (a full-IS
  monthly z mis-normalizes it, inflated by 2021's extreme dispersion, which is why the monthly-market
  variant was rejected in favor of the gate-coverage rule).
- **Threshold 0.40 chosen a-priori = ~2× C1's 19.3% IS base-rate coverage** ("a mania month = the C1
  regime active at more than double baseline"). NOT tuned to a target list. Sensitivity
  (informational): ≥30% → 16 months; ≥40% → 13; ≥50% → 9. The ≥50% list is the squeeze-heavy,
  C1-FAVORABLE one (V0 mean −1.6%/mo) and was **not** chosen; ≥40% keeps month-level winner months so
  the V0 bucket is net-positive (+2.52%/mo, not a negative base), which RAISES the G-mania bar (the
  stack must reach +4.52%/mo, not merely lift losers out of a hole).

**FROZEN 13-month list** (`blind_mania_rule.MANIA_MONTHS_FROZEN`, regeneration verified):
```
2020-08, 2020-11, 2020-12, 2021-01, 2021-02, 2021-08, 2021-10,
2023-01, 2023-11, 2023-12, 2024-02, 2024-03, 2024-11
```
**Delta vs the retired 9-month hand list:** ADDED 2020-08 (+3.0%), 2021-08 (+8.7%), 2021-10 (−1.9%),
2023-01 (+3.1%), 2023-11 (+2.4%); DROPPED 2021-03 (−13.5%). This matches the Critic's expectation
exactly (2023-01/2023-11 IN, 2021-03 OUT) and moves the boundary from P&L to market-coverage: four of
the five ADDED months are strategy WINNERS — a P&L-selected "worst months" list would never add them.

**V0 baseline on the NEW 13-month list** (recomputed by the single Critic-permitted V0 rerun,
`mania_rule.py`; V0 parity confirmed: Sharpe +0.9134, maxDD −32.99%, turnover 55.4x, and crash bucket
+2.586% ≡ DIAGNOSTIC-003's +2.59%): **mean monthly return +2.52%/mo, win rate 61.5%, worst month
2024-11 −16.35% (also the overall worst calendar month), best month 2020-12 +21.4%.**

**What G-mania actually tests (mechanism-efficacy, not regime alpha).** C1 scales ONLY the short leg,
so it HURTS a month only where that month's SHORT leg won. Per RISK-006 §1.3 short_px, **of the 13
market-defined mania months only 2020-12 (short_px +0.143) is a short-leg-winner where C1's floor-0.5
clip HURTS; the other 12 are short-loser months** (e.g. 2020-08 −0.086, 2021-08 −0.142, 2024-02 −0.041)
**where C1 helps by construction.** G-mania is therefore a **MECHANISM-EFFICACY test — does the
surviving stack net-improve its own market-defined firing footprint by ≥ +2.0 pp after C3's symmetric
de-gross, C2's shrink, and turnover** — a bar V1-alone likely clears but an L2/L3 stack containing C3
may miss. **A G-mania pass must NOT be read as evidence of independent regime alpha.** The engineer
recomputes V0's mania mean on the frozen warmup=63 slice (should reproduce +2.52%/mo); **G-mania is the
RELATIVE delta** (candidate mania mean − V0 mania mean ≥ +2.0pp ⇒ threshold ≈ **+4.52%/mo**).

---

## Section 4 — Pre-registered GATES for the PRIMARY CANDIDATE (frozen thresholds)

Gates apply to the **primary candidate** — the surviving stack chosen by the §5 decision tree
(NOT necessarily L3). All evaluated IS-only on the frozen warmup=63 slice. **HARD = fail kills the
candidate (FAIL verdict). SOFT = report + inform the SUCCESS/PARTIAL tier.**

| # | Gate | Metric | Threshold | HARD/SOFT | Rationale |
|---|---|---|---|---|---|
| **G-years** | per-year Sharpe | every IS year/part-year {2020,2021,2022,2023,2024,2025Q1} **≥ 0** | **HARD** | user mandate #1: all years positive incl. worst regimes |
| **G-crash** | crash-bucket (20mo) mean monthly return | **≥ +1.55%/mo AND > 0** | **HARD** | preserve ≥ 60% of V0's +2.59%; below → C3 over-shaved the crash alpha |
| G-crash-win | crash-bucket monthly win rate | ≥ 55% (V0 = 70%) | SOFT | crash robustness texture |
| G-crash-leg | crash-bucket aggregate short_px | > 0 (short leg still the crash friend) | SOFT | confirms mechanism preserved |
| **G-mania** | mania-bucket (13mo, market-only) mean monthly return | **≥ V0_mania_mean + 2.0 pp** (V0 = +2.52%/mo ⇒ **≥ +4.52%/mo**) | **HARD** | the redesign's raison d'être — mechanism-efficacy: net-improve C1's firing footprint after C3 de-gross / C2 shrink / turnover |
| G-mania-worst | mania-bucket worst single month | strictly better (less negative) than V0's **2024-11 −16.35%** | SOFT | operationalizes "fix the squeeze" |
| **G-sharpe-floor** | headline Sharpe **and** 2×-cost Sharpe | **≥ +0.45 AND ≥ +0.35** | **HARD** | controls did not net-destroy edge |
| G-sharpe-target | headline Sharpe **and** 2×-cost Sharpe | ≥ +0.60 AND ≥ +0.50 | SOFT | /005 G1/G5 convention → SUCCESS tier |
| **G-dd-floor** | maxDD | **≥ −35%** | **HARD** | the net-long mania tilt did not create a NEW tail (V0 = −33%; 2pp slack for the documented V-reversal risk, RISK-006 §6.2) |
| G-dd-target | maxDD | ≥ −30% | SOFT | controls delivered net tail protection → SUCCESS tier |
| **G-turnover** | turnover ann one-way | **≤ 100x/yr** | **HARD** | /005 G6; cost-fragility guard |
| **G-worst-month** | worst single IS calendar month | **≥ −15.0%** | **HARD** | improve on V0's −16.35%; no new worse month via net-long tilt |

**7 HARD gates** (G-years, G-crash, G-mania, G-sharpe-floor, G-dd-floor, G-turnover, G-worst-month)
+ 5 SOFT.

**Threshold justifications (frozen, pre-run):**
- **G-crash +1.55%/mo (60% of V0's +2.59%):** full preservation is impossible because C3 symmetrically
  shaves ALL months ~12% (and more in high-vol crash tails). But C1/C2 are structurally inert in
  crash (C1: BTC-down can't flag; C2: alts rarely +30%/7d in a crash), and C3's trailing-45c lag
  means it de-grosses the *tail-end* of crashes, not the onset where the short-leg crash alpha lands
  — so ≥ 60% preservation is the acceptable-degradation floor. Falling below it means C3 is eating the
  crash alpha itself, which is a design failure (→ drop C3, see §5).
- **G-mania +2.0 pp (⇒ ≥ +4.52%/mo on the market-only 13-month bucket):** RISK-006 §1.4's first-order
  MANIA delta at floor-0.5 is +0.492 aggregate P&L over the flagged mania candles ≈ +3.8 pp/mo spread
  over the 13-month bucket — so requiring only ≥ +2.0 pp/mo is a conservative floor inside the
  predicted effect, yet a genuine (non-token) fix. It is a **mechanism-efficacy** bar (net improvement
  of C1's own firing footprint after C3 de-gross / C2 shrink / turnover), NOT an independent-alpha
  claim: 12 of the 13 mania months are short-loser months where C1 helps by construction, and only
  2020-12 is a short-leg-winner where the clip hurts (§3.4). The margin was frozen at +2.0 pp in the
  ORIGINAL pre-registration and is UNCHANGED by the bucket redefinition.
- **G-sharpe-floor +0.45 / +0.35 (HARD) with the +0.60 / +0.50 SOFT target:** the user explicitly
  deprioritized headline Sharpe ("a decent Sharpe is fine, does NOT need to be 0.91"). Making +0.60 a
  HARD gate would reject a candidate that achieves the full robustness mandate at a mandated haircut —
  contradicting the directive. So +0.60/+0.50 is the SOFT SUCCESS target; +0.45/+0.35 is the HARD
  floor below which the controls have net-destroyed edge (not merely haircut it). A candidate that
  clears all other HARD gates but lands in Sharpe [+0.45, +0.60) is PARTIAL, not FAIL (§5).
- **G-dd-floor −35% (HARD) / −30% (SOFT):** C3+C4 should IMPROVE maxDD; −30% (3pp better than V0) is
  the SOFT target confirming that. But RISK-006 §6.2 flags that C1+C2 tilt the book net-long in mania,
  so a mania→crash V-reversal could DEEPEN maxDD; the HARD floor allows 2pp of slack (−35%) to absorb
  that documented interaction, while still catching an actual blow-up.
- **G-worst-month −15.0%:** V0's worst month is 2024-11 (−16.35%), the primary C1+C2 target (flag 92%;
  C2 excludes DOGE/ADA/PEPE). The month should improve materially; −15.0% is a conservative
  ≥1.35pp-improvement floor that also guarantees the net-long tilt did not manufacture a NEW worse
  month elsewhere.

---

## Section 5 — Frozen selection / decision tree (decided NOW, before any run)

### 5.1 Ladder marginals (computed from the frozen run list)

```
m_C1     = Sharpe(V1) − Sharpe(V0)          Δmania_C1 = mania(V1) − mania(V0)
m_C2     = Sharpe(L1) − Sharpe(V1)          Δmania_C2 = mania(L1) − mania(V1)
m_C3     = Sharpe(L2) − Sharpe(L1)          Δmania_C3 = mania(L2) − mania(L1)
m_C4     = Sharpe(L3) − Sharpe(L2)          Δmania_C4 = mania(L3) − mania(L2)
```
(`mania(·)` = mania-bucket mean monthly return; `Sharpe(·)` = headline honest-cost Sharpe, frozen
warmup=63 slice.)

### 5.2 The primary candidate is a NESTED-LADDER PREFIX of [C1, C2, C3, C4]

Start from the full stack **L3** and apply the drop rules below. The surviving stack is always the
**longest prefix** of `[C1, C2, C3, C4]` in which every included rung is retained (a rung can be IN
the stack only if all rungs below it are IN). So the primary candidate is exactly one of:
`{C1+C2+C3+C4 (=L3), C1+C2+C3 (=L2), C1+C2 (=L1), C1 (=V1)}`. **C1 is never dropped** (the anchor).

**Drop rules (frozen; evaluated top-down, prefer the leaner stack on ties):**
1. **Drop C4** (L3 → L2) iff `m_C4 < −0.05` **AND** C4 does not tighten maxDD by ≥ 1 pp
   (`maxDD(L3) ≥ maxDD(L2) − 0.01`). C4 is tail insurance; it stays only if it lifts Sharpe
   (`m_C4 ≥ −0.05`) OR meaningfully tightens maxDD.
2. **Drop C3** (→ L1; also drops C4 by nesting) iff **[** `m_C3 < −0.05` **AND** `Δmania_C3 ≤ 0` **]**
   **OR** **[** **crash-bucket mean of L2** (the leanest stack containing C3, pinned per F3)
   **< +1.55%/mo** (the G-crash floor) **]**. The crash-preservation clause is a HARD user constraint:
   C3 that over-shaves the crash alpha is dropped even if it is Sharpe-neutral. (C4 is inert on the
   crash bucket — none of its 4 engagements is a crash month — so crash(L3) ≈ crash(L2); the trigger
   is pinned to crash(L2) to remove the ambiguity.)
3. **Drop C2** (→ C1 only) iff `m_C2 < −0.05` **AND** `Δmania_C2 ≤ 0`. C2's whole job is the
   intra-week mania squeeze; if it helps neither Sharpe nor the mania bucket, it is dropped.
4. **C1 is never dropped.** If V1 shows C1 does NOT improve mania (`Δmania_C1 ≤ 0`), that **indicts
   the diagnostic thesis** — write the mandatory §5.4 verdict paragraph — but C1 remains the stack
   anchor (a failed C1 is a phase-level FAIL finding, documented, not silently patched with a swap).

### 5.3 C5 is NEVER in the stack (falsification only)

Regardless of its result, C5 does not change the stack. But its result is a **diagnostic falsifier**:
if `Sharpe(V5) > Sharpe(V0)` OR C5's crash-bucket mean > V0's +2.59%/mo, then BTC-crash de-risking
*helped* — which contradicts DIAGNOSTIC-003's central finding that the short leg IS the crash alpha.
That triggers the mandatory §5.4 verdict paragraph re-examining the whole thesis. The pre-registered
prediction is the opposite (V5 worse than V0, crash bucket degraded).

### 5.4 Mandatory verdict paragraphs (write regardless of pass/fail)

- **C5 falsification verdict:** did C5 hurt as predicted? Report V5 vs V0 headline Sharpe + crash
  bucket. If C5 helped, state explicitly that the diagnostic thesis is called into question and the
  redesign's regime-targeting must be revisited before any forward-validation.
- **C1 anchor verdict:** did C1 (V1) improve the mania bucket vs V0? If `Δmania_C1 ≤ 0`, the lead
  control failed its mechanism and the phase is a FAIL at the design level.

### 5.5 FROZEN IS interpretation map (SUCCESS / PARTIAL / FAIL — IS-level only, NO OOS)

Evaluated on the primary candidate (surviving stack). There is **no OOS reveal**; these are
design-validation verdicts, not deployability verdicts.

| Outcome | Condition | Interpretation |
|---|---|---|
| **SUCCESS** | ALL 7 HARD gates pass **AND** both SOFT Sharpe targets (≥ +0.60 / ≥ +0.50) **AND** SOFT maxDD target (≥ −30%) | The mania-aware redesign is **IS-validated**: mania fixed, crash preserved, all years positive, deployable-grade Sharpe retained. **Register the surviving stack for a FUTURE, separate forward-validation protocol** (NOT run here). |
| **PARTIAL** | ALL 7 HARD gates pass **BUT** one/both SOFT Sharpe targets missed (Sharpe in [+0.45,+0.60) or 2×-cost in [+0.35,+0.50)) **OR** SOFT maxDD in (−35%, −30%) | Robustness achieved at a Sharpe/DD haircut — **exactly the trade the user pre-authorized**. Design directionally validated; a future forward-validation is warranted with the headline softness noted as the known, accepted cost. |
| **FAIL** | ANY HARD gate fails | Redesign did not meet its IS goal. The specific failing gate localizes the cause (G-sharpe-floor → controls destroyed edge; G-crash → C3 over-shaved; G-mania → mania not fixed; G-dd-floor/G-worst-month → net-long tilt created a new tail; G-years → a regime broke). Document honestly; NO post-hoc tuning; NO OOS. Conclude or spawn a new pre-registered EXPLORATION. |

---

## Section 6 — Pre-registered predictions (axis-saturation discipline; from RISK-006, copied in)

Directional per-bucket predictions, frozen pre-run so we score prediction hits, not just outcomes.

| Ctrl | CRASH bucket | MANIA bucket | OTHER / QUIET | Headline Sharpe | maxDD |
|---|---|---|---|---|---|
| **C1** | ≈ 0 net: **inert in BTC-DOWN capitulation** (short-leg crash alpha preserved) + **mildly + in BTC-UP bear-rally** crash months (2021-08/2022-07 squeezes cut) | **improves** (short squeeze cut; +0.492 first-order) | small + (short also losing in flagged OTHER months) | + (removes −1.47 short-leg tail) | tightens (mania depth) |
| **C2** | ≈ 0 (alts rarely +30%/7d in crash) | **improves** (excludes parabolic mooners; excluded set −4.08 fwd short_px) | small + | + (fires 5.6% of short-name-candles, all net-losing) | tightens (worst-month) |
| **C3** | **− (shaved ~12%+)** symmetric | − to ≈0 (also shaved ~12%) | − (~12% de-gross) | ≈ neutral (mean & vol both scale) | tightens (uniform de-gross) |
| **C4** | ≈ 0 (no crash-bucket engagements) | small + (caps 2024-11 depth) | ≈ 0 (fires 4× total) | ≈ neutral-to-slightly − (engages after worst candle) | tightens (caps −20% breaches) |
| **C5** (falsify) | **− (worse)** cuts winning short leg (~62% of +0.781 named-crash short_px) | ≈ 0 (BTC up → no dd → scalar ≈ 1.0) | ≈ 0 | **− (NEGATIVE net)** | ≈ 0 / slightly tighter in 2022 |

**Composite prediction (the surviving stack, likely L3):** mania bucket materially improved
(≥ +2 pp/mo), crash bucket positive but ~15–30% below V0's +2.59% (C3 shave), all years still
positive, maxDD tightened toward −30%, headline Sharpe **at or modestly below** V0's +0.913 (the C1/C2
mania fix roughly offsets the C3 uniform de-gross; a PARTIAL outcome in Sharpe [+0.60, +0.913) is the
central expectation). Book tilts mildly net-long in mania (C1 floor-0.5 + C2 shrink) — the top tail
risk to watch is a mania→crash V-reversal with no BTC-momentum roll-over (RISK-006 §6.2), backstopped
by C1 floor-0.5 (not 0) and C4.

---

## Section 7 — Multiple-testing honesty (n_eff accounting + haircut instruction for the Critic)

- **This is the track's 6th exploration.** The matrix is **9 runs** scored against **7 HARD gates**.
- **The 9 runs are NOT 9 independent strategy searches.** They are isolations (V1–V5) + a single
  **nested ladder** (L1–L3) of ONE pre-committed control stack. Every control parameter was frozen
  ex-ante by RISK-006 from **ex-ante indicator statistics** (distributions, quantiles, firing rates,
  regime durations) — **NO Sharpe-based calibration** was performed at any point (RISK-006 §0). So the
  genuine model-**selection** degrees of freedom introduced by this exploration are (a) the choice of
  **which nested-ladder prefix survives** → 4 nested stacks {C1, C1+C2, C1+C2+C3, L3}, and (b) the
  **mania-bucket rule DOF** (the C1-coverage threshold; the crash rule was inherited from
  DIAGNOSTIC-003, so it is not a fresh DOF). Counting both → `n_eff ≈ 5–6` for this phase. The 5
  singletons are attribution, not selection; C5 is a pre-registered falsification, not a candidate.
- **Cumulative track-level n_eff.** REVIEW-005 established the track's prior selection surface at
  `n_eff ≈ 10–15` (5 explorations × constructions + the cadence scan), warranting a Bailey/López de
  Prado deflated-Sharpe haircut of ~0.15–0.25 Sharpe. EXPLORATION-006 adds ~5–6 → **cumulative n_eff ≈
  15–21**.
- **Haircut instruction for the Critic:** apply a DSR/deflation consistent with cumulative n_eff ≈
  15–21 to ANY headline Sharpe reported here — expect ~0.15–0.25 Sharpe deflation. An IS headline of,
  e.g., +0.65 should be read as a true-expectation ~+0.40–0.50. **BUT** — this phase is **IS-only with
  NO OOS reveal**, so per the track's EXPLORATION-mode DSR convention the deflation is **informational
  only**: it does not gate the IS design-validation verdict; it sizes expectations for the FUTURE
  forward-validation (a separate protocol). The IS verdict is a *design* verdict, explicitly NOT a
  deployability claim.
- **Ledger notes (REVIEW-006-preflight F5/F6 — recorded for candor):**
  1. **C2's calibration evidence was partly P&L-adjacent.** RISK-006 chose K=21/Q=+0.30 partly using
     the forward short_px of the excluded set (−4.08) — a P&L-adjacent statistic. The *parameter
     values themselves* are ex-ante distribution facts (Q=+0.30 ≈ the IS p90 of member trailing-21
     returns), but the disclosure is on the record.
  2. **The mania-list definition is an additional researcher DOF** (the C1-coverage rule + its 0.40
     threshold), now counted in n_eff above. It was picked a-priori (2× base rate) with a documented
     sensitivity, but it is a genuine choice and is disclosed as such.
  2a. **Anti-tuning affirmation (threshold review):** at threshold selection I consulted V0 *strategy
     P&L* of the three candidate coverage lists (≥30% / ≥40% / ≥50% → V0 mean +2.27% / +2.52% / −1.6%
     per month) — a dependent-variable consultation of the F1 class. It was exercised **only in the
     anti-favorable direction**: the gate-FAVORABLE ≥50% list (V0 −1.6%/mo, where C1's improvement is
     nearly guaranteed) was REJECTED and the harder ≥40% list CHOSEN. The 0.40 anchor (2× the 19.3%
     base rate) is independent of that P&L and was the stated a-priori rule.
  2b. **Anti-tuning affirmation (margin):** the +2.0 pp G-mania margin was frozen in the ORIGINAL
     pre-registration (before the bucket redefinition) and is UNCHANGED by the F1 bucket fix — only the
     bucket membership and V0 baseline (+2.52%/mo) moved; the required delta did not.
  2c. **Non-disjointness disclosure:** the CRASH (20) and MANIA (13) buckets are NOT disjoint —
     **crash ∩ mania = {2021-08}** (in crash via the trailing-DD clause, in mania via ≥40% C1
     coverage). Economically coherent — a bear-rally squeeze inside a deep-DD flag is genuinely both —
     but it means the G-crash and G-mania pass/fail signals are mildly correlated through that one
     shared month; scored independently, noted here.
  3. **This is the SECOND IS redesign on the SAME IS window after a burned OOS** (CONFIRMATION-005
     already spent the one-shot OOS look on the /005 base). The cumulative IS selection surface across
     the whole track is therefore materially larger than this phase's `n_eff ≈ 5–6`; a future
     forward-validation MUST size its deflation against that whole-track surface, NOT this phase alone,
     and must use a genuinely unseen window (a fresh OOS or true forward paper period).
- **Forthright selection-bias disclosure (restoring /005's candor, per the Critic's style note).** I
  am NOT claiming these controls will hold OOS. The IS improvements this matrix will show are earned on
  a window whose /005 base already burned its OOS look; the controls were calibrated (RISK-006) and the
  mania bucket defined (this brief) using IS statistics; the surviving-stack selection is one of several
  admissible prefixes. What guards against over-fit here is that (i) NO parameter was Sharpe-tuned, (ii)
  the gates and month lists were frozen before the run, (iii) the mania bucket is market-defined and
  net-positive for V0 so G-mania is not a giveaway, and (iv) C5 is a live falsifier that would expose a
  wrong regime target. None of that substitutes for out-of-sample confirmation, which this phase does
  not perform. The deliverable is an IS-validated *design*, not a deployable book.
- **Explicit pre-registration statements (for the record):**
  1. **All gate thresholds in §4 were chosen BEFORE any variant ran** (this brief is the frozen
     contract).
  2. **The CRASH month list (20) is MARKET-defined** — `btc_ret < −15% OR btc_dd_end(540) > 25%`,
     a pure BTC-price criterion, NOT strategy-performance-defined.
  3. **The MANIA month list (13) is defined by a COMMITTED MARKET-ONLY rule** (C1-flag coverage ≥ 40%;
     `blind_mania_rule.py` with a reproducibility self-test), replacing the retired hand-authored
     9-month literal whose boundary tracked strategy P&L (REVIEW-006-preflight F1). The rule's
     second-order self-reference (bucket = "months where the C1 detector fires ≥40%") is disclosed.
     G-mania is a **mechanism-efficacy** test, not a regime-alpha claim: C1 scales only the short leg,
     so of the 13 mania months only **2020-12** (short_px +0.143) is a short-leg-winner where C1's clip
     HURTS — the other 12 (e.g. 2020-08 −0.086, 2021-08 −0.142, 2024-02 −0.041) are short-loser months
     where C1 helps by construction. The stack must net-improve its own firing footprint by ≥ +2.0pp
     after C3's de-gross / C2's shrink / turnover; a pass is NOT evidence of independent regime alpha.
  4. **The decision tree (§5) and interpretation map (§5.5) are frozen NOW**, so the primary candidate
     is selected by rule, not by post-hoc Sharpe inspection.

---

## Section 8 — Engineer deliverables spec

**Script:** `analysis/portfolio/blind_exploration_006.py` (template: `blind_exploration_005.py` +
`blind_risk_calib_006.py`). **Import verbatim — no reimplementation, no drift:** `mania_gate` (from
`blind_risk_calib_006`), the `rK` construction, `btc_drawdown_scalar` (from `blind_regime`), and the
committed **MANIA bucket** via `from blind_mania_rule import mania_months, MANIA_MONTHS_FROZEN`
(the frozen 13-month list; verify `mania_months(mania_gate(...)[0], panel.grid_ms, warmup=63,
thr=0.40) == MANIA_MONTHS_FROZEN`). IS hard-slice (`slice_is`) at the top; **all indicator series
constructed vectorized and IS-sliced BEFORE any `run_backtest` call.**

**Required deliverables:**
1. **Parity guard (ABORT on fail):** V0 must reproduce **Sharpe +0.913 ± 0.005**, maxDD **−33% ± 1pp**,
   turnover **55.4x ± 2**. If any drifts, STOP — the base construction was perturbed.
2. **The 9-run matrix** (§3.1) with the full per-run characterization (§3.2) on the **frozen
   warmup=63 slice** (§2.6) — including per-year Sharpe, worst month, monthly win rate, top-10
   concentration, and the **CRASH bucket (20 market-defined months, §3.3)** + **MANIA bucket
   (`MANIA_MONTHS_FROZEN`, 13 months, §3.4)** aggregates **with leg-level P&L** (long_px / short_px /
   net_fund per bucket). **Also report (REVIEW-006-preflight F2): C1 flag coverage for EACH of the 20
   crash-bucket months**, split into the BTC-DOWN capitulation subset (C1 must read ≈0 — crash alpha
   preserved) and the BTC-UP bear-rally subset (2021-07/08, 2022-02/03/07/10 — C1 may fire, and where
   it does it should be P&L-positive), so G-crash preservation is attributed to the correct sub-regime.
3. **Ladder-marginal table:** `m_C1..m_C4` and `Δmania_C1..Δmania_C4` (§5.1), and the resolved
   **primary candidate** (surviving stack per §5.2 drop rules).
4. **Gate scorecard** for the primary candidate against all 12 gate lines (§4), each HARD/SOFT with
   pass/fail, and the resolved **SUCCESS / PARTIAL / FAIL** verdict (§5.5).
5. **The two mandatory verdict paragraphs** (§5.4): C5 falsification + C1 anchor.
6. **Tests — all green.** The existing **44 tests stay green** (no engine edits; controls are opt-in
   and byte-identical when off — already covered by `test_short_leg_plumbing_byte_identical_when_off`
   and the gross_scalar/dd_brake positive-controls). The C1 gate series and C2 exclusion matrix are
   built **outside** the engine, so they need their **own leak positive-controls** (spec):
   - `test_mania_gate_series_no_future_leak` — build the C1 `short_scalar_series` on a clean IS panel
     and on a panel whose `close`/`funding` are corrupted from a cutoff forward; assert
     `short_scalar_series[:cutoff]` is **bit-identical** (`np.testing.assert_array_equal`), and a
     non-vacuous guard confirms post-cutoff values DO change. (Catches any accidental forward read in
     the rolling z-score / dispersion / funding construction.)
   - `test_parabolic_exclude_series_no_future_leak` — same pattern for the C2 `short_exclude` (T,C)
     matrix: corrupt `close` post-cutoff, assert `short_exclude[:cutoff]` bit-identical + non-vacuous.
   These mirror the existing `test_future_corruption_leaves_past_identical_midvol_rebal21` discipline
   but target the indicator constructions rather than the engine.
7. **Consumption-lag guard:** confirm series are passed indexed by `t` (engine applies `[k-1]`); a
   quick assertion/comment that no pre-shift is applied.

**Do NOT:** touch OOS (no `slice` past `OOS_CUTOFF`), read any baseline/CONFIRMATION artifact, change
any FROZEN parameter, or re-run/re-tune after seeing the results. Hand the report to the QR for the
Phase-7 IS evaluation. **There is no OOS reveal in this phase.**

---

**FROZEN.** Gate thresholds, the 9-run list, the two bucket month lists, the decision tree, and the
interpretation map are locked as of 2026-07-10, pre-run. Any deviation is a new EXPLORATION.
