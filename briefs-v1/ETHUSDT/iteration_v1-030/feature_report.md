# iter-v1/030 Feature Report — Multi-speed Trend-State ENSEMBLE direction (ETHUSDT)

**Role:** Feature Engineer (Phase 4). **Symbol:** ETHUSDT. **Track:** v1 single-symbol.
**Mode:** IS-only EDA + WIRING-SPEC (NO backtest, NO src/ edits — iter-029 K=20 confirmation is running).
**Cutoff:** `OOS_CUTOFF_MS = 1742774400000` (2025-03-24). All numbers below are from the committed,
cutoff-asserted, leak-guarded script `analysis/ETHUSDT/iteration_v1-030/breadth_eda.py` (IS rows = 5727,
span 2020-01-01 .. 2025-03-23). **This brief does NOT implement; the orchestrator implements §3 after iter-029.**

---

## 1. Candidate feature — economic hypothesis + lineage

**Candidate:** a *multi-speed trend-state ENSEMBLE* direction override that replaces the single
SMA-200 trend-state sign with a **signed-majority vote** across SMA windows `{50,100,150,200,300}`.

- **Lineage.** The incumbent ETH direction primitive is `lgbm._compute_trend_state`:
  `trend_state(t)=+1 if close[t-1] > SMA_200(close)[t-1] else -1`, past-only (searchsorted
  side="right"−1), trades on ETH's OWN close (`trend_state_symbol = ETHUSDT`). It is the merged
  iter-020→027 deterministic direction and the M1 primary in the iter-028/029 meta-labeling stack.
- **Economic hypothesis (crypto-native).** The single SMA-200 partitions price into ONE slow
  trend/counter-trend regime. In a 24/7 trending-then-liquidating crypto tape, *different
  participants act on different trend speeds* — fast momentum traders (50–100 candle), swing
  (150–200), macro positioning (300). A single speed parks the book in one long regime (max
  IS run = **409 candles** for SMA-200), so a few big captures in that regime carry the OOS net
  (top-1 OOS = 78% @ iter-028). Voting across speeds keeps the SAME parameter-free, can't-overfit
  property but produces **more, shorter direction regimes** → more distinct conviction-gated
  entries → a less-concentrated roster, WITHOUT trading direction-correctness away.
- **Why it can't overfit.** Every member sign is a fixed deterministic SMA comparison (no fitted
  param, no quantile, no OOS exposure). The vote is a fixed aggregation. There is nothing to tune
  on IS noise — exactly the property that made the single SMA-200 generalize where seed-varying
  sizing did not (the recurring "only deterministic parts generalize" lesson).

---

## 2. IS-only evidence (IS rows = 5727; forward horizon FWD_H = 42 candles = 14d; embargo-safe N = 5685)

### 2a. Warmup coverage & directional accuracy (embargo-safe candles)

| rule | cov_frac | n_active(emb) | dir_acc (P[dir==sign(fwd14d)]) | mean dir×fwd (NO costs) |
|---|---|---|---|---|
| single_sma200 (incumbent) | 0.965 | 5485 | **0.531** | 0.02058 |
| ens_sma_majority {50,100,150,200,300} | 0.948 | 5385 | **0.539** | 0.02002 |
| ens_sma_signed_avg(0.20) | 0.948 | 5385 | 0.539 | 0.02002 |
| ens_sma+tsmom_majority (+{21,42,84}) | 0.948 | 5031 | 0.539 | 0.02214 |
| ens_sma+tsmom_signed_avg(0.25) | 0.948 | 5031 | 0.539 | 0.02214 |

Direction-correctness is **preserved and marginally improved** (+0.7–0.8pp accuracy vs SMA-200).
The ensemble loses ~1.7pp warmup coverage (it needs the slowest member, SMA-300, warm — 2 extra
months of history; immaterial across a 24-month training window).

### 2b. Agreement & disagreement quality

- SMA-majority **agrees with SMA-200 on 92.2%** of candles; SMA+TSMOM agrees 89.8%.
- On the disagreement set, neither side is clearly more correct at the *candle* level
  (`rule_acc_dis ≈ sma200_acc_dis ≈ 0.50`). The value is NOT "the ensemble is more right on a
  per-candle vote" — it is **WHERE/WHEN it flips** (breadth + de-concentration), below.

### 2c. TRADE-LEVEL concentration — the load-bearing test

The candle-level book scores 5,485 overlapping 14d windows → HHI ≈ 1/N by construction (NOT how
the strategy trades). Collapsing consecutive same-direction runs into **one trade per
direction-regime** (entry = first candle of run, exit = close at the candle after the run ends)
proxies the REAL trade roster whose OOS concentration we attack:

| rule | n_trades | top1 share | top2 share | HHI | net (NO cost) | win% |
|---|---|---|---|---|---|---|
| **single_sma200** | 151 | 0.221 | 0.293 | 0.0656 | 3.523 | 27.8% |
| **ens_sma_majority** | **178 (+18%)** | **0.215** | **0.263 (-3.0pp)** | **0.0589 (-10%)** | 3.463 | 29.8% |
| ens_sma+tsmom_majority | 145 (-4%) | 0.213 | 0.265 | 0.0617 | 5.260 | 35.2% |

- **SMA-majority** is the clean de-concentrator: **+18% trades, lower top-1/top-2/HHI, higher
  win%, essentially flat net.** It splits the roster across more, shorter regimes.
- **SMA+TSMOM majority** has higher net & win% but **fewer trades (145 < 151)** — the wrong
  direction for breadth — and its net lift is on overlapping windows, not trustworthy as edge.

### 2d. Breadth / temporal spread (full IS, all defined candles)

| rule | n_active | sign_changes | flip_rate | max single-regime run |
|---|---|---|---|---|
| single_sma200 | 5527 | 151 | 0.0273 | **409** |
| ens_sma_majority | 5427 | **178 (+18%)** | 0.0328 | **343 (-16%)** |
| ens_sma+tsmom_majority | 5073 | 145 | 0.0286 | 339 |

SMA-majority cuts the longest single-regime run 409 → 343 and raises sign-changes +18%. This is
the *mechanism* of de-concentration: fewer 400-candle parks where one big capture dominates.

### 2e. ADF / stationarity (informational)

The ensemble direction is a {−1,0,+1} categorical sign, not a continuous series; ADF is not
meaningful for it. Its INPUTS (SMA distances) are the same family already in the merged stack;
no new continuous feature column is introduced into `feature_columns` (the override is a RULE
layer, identical in nature to the existing single-SMA override — it does NOT enter the LightGBM
feature matrix).

### 2f. IS-only VERDICT

**SMA-majority {50,100,150,200,300} de-concentrates the IS trade roster (+18% trades, top-2 −3pp,
HHI −10%, max-run −16%) while preserving direction-correctness (dir_acc +0.8pp) and net.** The
signed-average(0.20) variant is byte-identical to majority on this family (5 odd members, dead-band
never triggers a different sign) — **majority is the canonical, simpler form.** Adding TSMOM
*reduces* trade count (anti-breadth) despite higher net, so it is NOT recommended for the
de-concentration objective; it is logged as a secondary observation, not the iter-030 axis.

> **HONEST caveat.** This is candle/run-level IS evidence with NO costs and NO conviction-gate /
> R2 / R5 interaction. The conviction gate (q=0.40) and R2 brake will reshape which of the +18%
> extra flips actually become trades. The backtest (orchestrator, post iter-029) is the arbiter of
> whether de-concentration survives net of fees+slippage and the gate stack. The IS signal is
> *directionally supportive and mechanism-coherent*, not a guaranteed OOS win.

---

## 3. WIRING SPEC (orchestrator implements after iter-029; DO NOT implement now)

### 3.1 `lgbm.py` — extend the trend-state override to a multi-speed ensemble

**Constructor (`LightGbmStrategy.__init__`, near the existing `trend_state_sma_window` param ~L311):**
add three params with defaults that preserve byte-identity for every existing single-window run:

```python
trend_state_sma_windows: tuple[int, ...] | None = None,  # None => single-window legacy path
trend_state_ensemble_mode: str = "majority",             # "majority" | "signed_avg"
trend_state_ensemble_avg_thresh: float = 0.20,           # only used when mode == "signed_avg"
```

Store:
```python
self._trend_state_sma_windows = (
    tuple(int(w) for w in trend_state_sma_windows) if trend_state_sma_windows else None
)
self._trend_state_ensemble_mode = str(trend_state_ensemble_mode)
self._trend_state_ensemble_avg_thresh = float(trend_state_ensemble_avg_thresh)
```

**BYTE-IDENTITY REQUIREMENT (load-bearing).** When `trend_state_sma_windows is None` (the default),
NOTHING changes: `_compute_trend_state` runs the existing single-window code path verbatim, the
index build at ~L813 is unchanged, and every iter-016→029 run is bit-identical. The ensemble path
is reached ONLY when `trend_state_sma_windows` is a non-empty tuple. (Mirror the
`enable_funding_contra_readmit` default-off discipline.)

**Index build (`compute_features`, ~L813, inside `if self._enable_trend_state_dir:`).** The existing
build loads `(close_time, close)` sorted — that is ALL the ensemble needs (every SMA window is a
mean over the same close series). **No new parquet read, no new column.** Keep the single-window
build exactly as-is; `_trend_state_idx = (sorted_close_time, sorted_close)` already supports any
window. (Add one `verbose` line listing the windows when ensemble is active.)

**`_compute_trend_state` (~L2415) — add an ensemble branch, single-window path UNCHANGED:**

```python
def _compute_trend_state(self, candle_open_time: int) -> int | None:
    if self._trend_state_idx is None:
        return None
    ct_arr, cl_arr = self._trend_state_idx
    idx_curr = int(np.searchsorted(ct_arr, candle_open_time, side="right")) - 1   # candle t-1
    if idx_curr < 0:
        return None
    close_prev = cl_arr[idx_curr]
    if not np.isfinite(close_prev) or close_prev <= 0.0:
        return None

    # ----- ENSEMBLE branch (new; default-off) -----
    if self._trend_state_sma_windows is not None:
        signs: list[int] = []
        for w in self._trend_state_sma_windows:
            idx_lo = idx_curr - w + 1
            if idx_lo < 0:                       # this member is in warmup -> whole ensemble warms
                return None                      # CONSERVATIVE: require ALL members warm (mirrors EDA)
            window = cl_arr[idx_lo : idx_curr + 1]
            if not np.isfinite(window).all() or (window <= 0.0).any():
                return None
            sma_prev = float(np.mean(window))
            signs.append(1 if close_prev > sma_prev else -1)
        s = int(sum(signs))
        if self._trend_state_ensemble_mode == "signed_avg":
            m = s / len(signs)
            t = self._trend_state_ensemble_avg_thresh
            if m >= t:
                return 1
            if m <= -t:
                return -1
            return None                          # dead-band abstain -> caller keeps MODEL sign
        # "majority": sign of the vote sum; even-split (s == 0) -> abstain (keep model sign)
        if s > 0:
            return 1
        if s < 0:
            return -1
        return None

    # ----- single-window legacy path (UNCHANGED) -----
    w = self._trend_state_sma_window
    idx_lo = idx_curr - w + 1
    if idx_lo < 0:
        return None
    window = cl_arr[idx_lo : idx_curr + 1]
    if not np.isfinite(window).all() or (window <= 0.0).any():
        return None
    sma_prev = float(np.mean(window))
    return 1 if close_prev > sma_prev else -1
```

Notes:
- Past-only indexing is the EXACT existing `searchsorted(ct_arr, candle_open_time, "right")-1`
  pattern (candle t-1). Every SMA member reuses `idx_curr` and `close_prev` — same `close[t-1]`,
  same window slice convention `cl_arr[idx_lo:idx_curr+1]`. No member reads any candle with
  `close_time >= candle_open_time`.
- **Recommended config returns only ±1 (majority over 5 odd windows can never tie),** so the
  ensemble override behaves exactly like the single override: a deterministic sign replacement,
  with the SAME warmup→`None`→keep-model-sign fallback. The dead-band/abstain (`None`) only arises
  under `signed_avg`, and it is handled by the existing caller branch (logs
  `trend_state_warmup:kept_model_sign`-style; keep the model sign — CONSERVATIVE).

**Decision-log (override call site ~L2893).** No structural change needed; add the active windows
to the existing `trend_state_override` log dict for attribution, e.g.
`"trend_state_sma_windows": list(self._trend_state_sma_windows or [self._trend_state_sma_window])`,
and `"ensemble_mode": self._trend_state_ensemble_mode if self._trend_state_sma_windows else "single"`.

### 3.2 Conviction-gate coupling — KEEP THE GATE ON SMA-200 (single axis)

`_compute_trend_strength` measures `|close[t-1] − SMA_W[t-1]| / ATR14[t-1]` with
`W = _trend_state_sma_window` (built at ~L884). **The iter-030 axis changes DIRECTION ONLY.** To
keep this a clean single-axis change, the conviction gate MUST keep measuring magnitude vs the
**reference SMA-200** (`_trend_state_sma_window` stays 200, the strength index build is unchanged).
Do NOT make the gate ensemble-aware in iter-030 — that would confound direction-breadth with
gate-magnitude and break attribution. (A future iteration could explore an ensemble-distance gate;
out of scope here.) **Concretely: set `_spec_trend_state_sma_window = 200` AND
`_spec_trend_state_sma_windows = (50,100,150,200,300)` — the scalar still drives the gate, the
tuple drives the direction.**

### 3.3 LOOK-AHEAD unit test plan — `tests/test_trend_state_ensemble_lookahead.py`

Mirror `tests/test_trend_state_lookahead.py` exactly, with a strategy built using
`trend_state_sma_windows=(50,100,150,200,300), trend_state_ensemble_mode="majority"`. Required cases
(reference impl = signed-majority over manually-sliced past-only windows):

1. `test_matches_manual_majority_uptrend/downtrend` — clean monotone series → all 5 members agree
   → vote == manual sign.
2. `test_matches_manual_across_a_cross` — V-shaped series; loop `t_idx in range(max_window, n)`,
   assert `_compute_trend_state(open_time)` == `sign(sum(manual_sign(closes,t,w) for w in windows))`.
3. **`test_appending_future_candles_does_not_change_value`** — THE leak test: compute value at a
   decision candle, append 50 wild future candles (crash then 10000× spike), assert unchanged.
   This must hold for EVERY member window (the slowest, SMA-300, is the binding past-only check).
4. `test_decision_candle_own_close_never_used` — mutate `cl[t_idx]` to 1e9; value unchanged.
5. `test_uses_exactly_close_t_minus_1` — flat series; nudge `cl[t_idx-1]` above/below the flat mean;
   majority flips +1/−1 (all members share `close[t-1]`).
6. `test_warmup_requires_slowest_window` — with `< max(windows)` closes before t, returns `None`
   (the conservative ALL-members-warm rule); with exactly `max(windows)` history, defined.
7. `test_majority_odd_windows_never_ties` — assert the recommended 5-window config returns ∈{−1,+1}
   (never `None` from a tie) once warm.
8. `test_signed_avg_deadband_returns_none` — build with `mode="signed_avg", thresh=0.60`; construct a
   2-up/3-down candle (mean=−0.2, |mean|<0.6) → `None` (abstain). Guards the dead-band branch.
9. `test_single_window_default_path_unchanged` — build with `trend_state_sma_windows=None` (default);
   assert identical output to the existing single-window test fixtures (byte-identity regression).

### 3.4 `run_baseline_v1.py` — iter-030 keyed config block (mirror the v1-028 `_spec_*` style)

Add module constants near `V1_ITER030_*` (use a NON-colliding name; the existing `V1_ITER030_*`
constants are for an unrelated meta-labeling plan):

```python
V1_ITER030_TRENDSTATE_SMA_WINDOWS: tuple[int, ...] = (50, 100, 150, 200, 300)
V1_ITER030_TRENDSTATE_ENSEMBLE_MODE: str = "majority"  # PINNED (single-axis; not tuned)
```

Add `_spec_*` defaults in the spec block (near ~L3891, default-off → byte-identical elsewhere):

```python
_spec_trend_state_sma_windows: tuple[int, ...] | None = None   # None => single-window legacy
_spec_trend_state_ensemble_mode: str = "majority"
_spec_trend_state_ensemble_avg_thresh: float = 0.20
```

Add an `elif iteration_label == "v1-030":` branch (clone the v1-027 M1 stack — the iter-027 stack
is the current ETH baseline that /029 is confirming; do NOT include the M2 meta-labeling layer,
iter-030 is the M1-direction-breadth axis):

```python
elif iteration_label == "v1-030":
    # iter-v1/030 EXPLORATION (ETHUSDT) — MULTI-SPEED TREND-STATE ENSEMBLE direction.
    # SINGLE AXIS vs the iter-027 baseline: replace the single SMA-200 trend-state DIRECTION
    # with a signed-MAJORITY vote across SMA {50,100,150,200,300} (parameter-free, past-only,
    # can't-overfit). Conviction gate STAYS on SMA-200 (direction-only axis). Targets the
    # iter-027/028 OOS-concentration falsifier (IS: +18% trades, HHI -10%, max-run -16%).
    import pyarrow.parquet as pq  # noqa: PLC0415

    _spec_sym_030 = symbols[0]
    _iter030_parquet = Path("data/features") / f"{_spec_sym_030}_8h_features.parquet"
    assert _iter030_parquet.exists(), f"iter-v1/030: parquet not found at {_iter030_parquet}."
    _parquet_cols = set(pq.ParquetFile(_iter030_parquet).schema.names)
    _missing = [c for c in V1_BTC_ITER009_FEATURES if c not in _parquet_cols]
    assert not _missing, f"iter-v1/030: {len(_missing)} M1 feature columns NOT present — {_missing}."
    # M1 stack — IDENTICAL to the iter-027 baseline EXCEPT the direction is now an ENSEMBLE.
    _spec_feature_columns = list(V1_BTC_ITER009_FEATURES)
    _spec_label_mode = "fixed_horizon"
    _spec_use_atr_labeling = False
    _spec_label_timeout_minutes = 20160                     # 14d == /027
    _spec_atr_tp = 100.0                                    # == /027
    _spec_atr_sl = 1.45                                     # == /027
    _spec_execution_timeout_minutes = 20160                # == /027
    _spec_enable_trend_state_dir = True                    # override ON
    _spec_trend_state_sma_window = 200                     # <-- conviction-gate reference (UNCHANGED)
    _spec_trend_state_sma_windows = V1_ITER030_TRENDSTATE_SMA_WINDOWS  # <-- NEW: ensemble direction
    _spec_trend_state_ensemble_mode = V1_ITER030_TRENDSTATE_ENSEMBLE_MODE
    _spec_trend_state_symbol = _spec_sym_030               # ETH's own close
    _spec_enable_trend_strength_gate = True                # conviction gate == /027 (on SMA-200)
    _spec_trend_strength_atr_window = 14
    _spec_trend_strength_quantile = 0.40
    _spec_apply_r2 = True                                  # ETH-calibrated R2 == /027
    _spec_r2_trigger_pct = 4.07
    _spec_r2_scale_anchor_pct = 16.27
    _spec_r2_scale_floor = 0.20
    # NO meta-labeling (M2 OFF) — iter-030 isolates the direction-breadth axis.
    print(
        f"[iter-v1/030] OVERRIDE ACTIVE ({_spec_sym_030}): MULTI-SPEED TREND-STATE ENSEMBLE "
        f"dir=majority{V1_ITER030_TRENDSTATE_SMA_WINDOWS} (gate stays SMA-200 q=0.40) "
        f"| iter-027 M1 stack otherwise (19-col HYBRID, fixed_horizon N=42(14d), R2 4.07/16.27/0.20)."
    )
```

Thread the two new spec vars into BOTH dispatch sites that pass `enable_trend_state_dir`
(the generic `run_model` call ~L5170 AND, if iter-030 ever routes through `run_meta_model`,
~L5108 — but iter-030 keeps M2 OFF so it takes the generic `run_model` path):

```python
enable_trend_state_dir=_spec_enable_trend_state_dir,
trend_state_sma_window=_spec_trend_state_sma_window,
trend_state_sma_windows=_spec_trend_state_sma_windows,          # NEW
trend_state_ensemble_mode=_spec_trend_state_ensemble_mode,      # NEW
trend_state_symbol=_spec_trend_state_symbol,
```

…and add the matching pass-through params to `run_model(...)` and `run_meta_model(...)` signatures
(default `None`/`"majority"`) so they forward into the `LightGbmStrategy(...)` construction at the
two sites (~L836/L1034). **Defaults `None` keep every other iteration byte-identical.**

### 3.5 Routing guard

iter-030 is single-symbol ETH with `_spec_enable_metalabel = False`, so the universal single-symbol
guard dispatches to the generic `run_model` branch (the `else` at ~L5118). No new universe constant
or `set(symbols) == ...` legacy branch is needed.

---

## 4. Recommended Optuna bounds (incl. training_days)

**No change vs the iter-027 baseline.** The ensemble is a *deterministic direction override* applied
AFTER the model emits its signal — exactly like the single-SMA override it replaces. It does not
enter the LightGBM feature matrix and does not change the label. Therefore:

- **Bounds profile:** `v1_specialist` (unchanged). No reason to switch to `v1_pruned`/default.
- `num_leaves`, `min_child_samples`, `colsample_bytree`, `reg_alpha/lambda`, `learning_rate`,
  `n_estimators`: **unchanged** — the model still learns timing/sizing/confidence on the same
  19-col HYBRID feature set; only the executed sign is overridden downstream.
- **`training_days` search range: KEEP the default `suggest_int("training_days", 10, 500, step=10)`.**
  No IS evidence to tighten/widen. The ensemble does not change the information horizon the model
  needs; it changes which entries the gate fires on, post-model.
- **`n_trials`:** EXPLORATION default for v1 SPECIALIST (n_trials=18, 2h cap, 3 seeds) — this is an
  exploration screen of ONE focused axis, exactly the right scope.

---

## 5. Substitution effects + trial-stability prediction

- **Substitution / importance.** Because the override is a downstream RULE layer, it does NOT
  compete with feature columns for split share — feature-importance ranks should be **unchanged vs
  iter-027** (same feature matrix, same labels). The post-Phase-6 importance CSV should show the
  iter-027 ranking essentially preserved (Spearman ρ ≈ 1.0 vs iter-027). If it shifts materially,
  that signals an unintended labeling/training change — a wiring bug to flag. *(I will append the
  realized importance interpretation here post-Phase-6, comparing to this prediction.)*
- **Trade-roster effect (pre-registered behavioral predictor, per the saturation-predictor rule).**
  Expect the IS trade count to RISE relative to iter-027 (candle-level: +18% sign-changes; after the
  conviction gate + R2 the realized lift will be smaller but POSITIVE — predict **+5% to +20% IS
  trades**). Predict OOS top-1 trade share to FALL from ~0.78 (iter-028) toward ~0.55–0.70 and the
  number of OOS trades to rise. **Falsifier:** if the backtest shows ≤ +2% IS trade-count change AND
  unchanged OOS top-1 share, the ensemble collapsed to the single-SMA roster (the gate/R2 absorbed
  every extra flip) → axis is INERT-by-saturation; do NOT escalate to higher trial budget.
- **Trial-stability / basin risk.** The direction is DETERMINISTIC across seeds (the vote is fixed),
  so the override itself adds ZERO cross-seed dispersion — same property that let the single-SMA
  direction survive K=20 where seed-varying sizing collapsed (the recurring lesson). Cross-seed
  Sharpe dispersion should be NO WORSE than iter-027's. The remaining seed variance comes only from
  the model's confidence/sizing on the (slightly larger) entry set. **Prediction: LOW basin risk;**
  if the K=5 EXPLORATION is both-positive AND de-concentrated, it is a strong K=20 candidate — the
  deterministic axis is precisely the kind that has survived 20 seeds before.
- **Concentration honesty.** The de-concentration is IS-measured at the run/trade-proxy level. The
  binding question is whether it survives net of fees+slippage on the OOS book. The IS mechanism is
  coherent (more, shorter regimes) but the OOS verdict is the backtest's to render.

---

## 6. Recommended exact config (handoff to Quant Research)

- **Direction:** signed-MAJORITY vote, `trend_state_sma_windows = (50, 100, 150, 200, 300)`,
  `trend_state_ensemble_mode = "majority"` (5 odd windows → never ties → pure ±1, same warmup
  fallback as the single override).
- **Conviction gate:** UNCHANGED on SMA-200, q=0.40 (single-axis discipline — direction only).
- **Everything else:** the iter-027 ETH baseline stack (19-col HYBRID, fixed_horizon N=42 14d
  let-winners-run, ETH R2 4.07/16.27/0.20, R3/R5), M2 meta-labeling OFF.
- **Cadence:** EXPLORATION K=5 (3 seeds spirit; v1 specialist n_trials=18, 2h cap). If both-positive
  AND OOS top-1 share falls / OOS trade count rises → strong K=20 CONFIRMATION candidate.
- **Do NOT** ship the SMA+TSMOM variant — it *reduces* trade count (anti-breadth) despite higher
  raw net; it fails the de-concentration objective. SMA-majority is the clean axis.

**Bottom line:** the IS evidence SUPPORTS the multi-speed SMA-majority ensemble as a de-concentrator
(+18% trades, top-2 −3pp, HHI −10%, max-regime-run −16%) at preserved-or-improved direction
accuracy, with zero added seed dispersion (deterministic) and zero Optuna-bounds impact. It is a
clean, can't-overfit, single-axis EXPLORATION worth a backtest after iter-029 completes.
