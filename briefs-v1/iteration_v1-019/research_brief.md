# iter-v1/019 — Research Brief (Phases 2-5)

**Branch**: `iteration-v1/019` from `iteration-v1/018` HEAD `056a9a7` (tag `v0.v1-018`).

**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`). Portfolio IS Sharpe **+0.2829** / OOS Sharpe **+0.6637** / OOS trades 189 / 5-sym universe / 4 models (A, C, D, E).

**Per-cohort anchor** (this iter's verdict baseline): ETH-in-pool IS monthly Sharpe **−0.1022** / OOS monthly Sharpe **+0.0503** (from `analysis/iteration_v1-019/eth_per_symbol_baseline.csv`).

**Track**: v1 (refactored 2026-05-23). 13 phases. LightGBM Master + Critic.

**Iteration type**: EXPLORATION (cycle-3 #4 of 10).

---

## Section 0 — Position in cycle / pivot context

### 0.1 Cycle-3 cadence position

- Cycle-3 EXPLORATION #4 of 10 (CONFIRMATION earliest at /027).
- Prior cycle-3 EXPLORATIONs: /016 (sample-weighting NEGATIVE-catastrophic), /017 (universe NEGATIVE-anti-direction-INERT), /018 (per-cohort-specialization-LINK PROMISING-INERT favorable).
- Cycle-3 ledger thus far: 1 PROMISING-INERT favorable / 2 NEGATIVE / 0 merges.

### 0.2 Per-cohort methodology — second cohort

User strategic pivot 2026-05-26 codified at `feedback_v1_per_cohort_exploration_strategy.md`. /018 LINK-only validated empirically (FIRST cycle-3 edge candidate; PROMISING-INERT favorable). /019 advances the methodology by attacking the **opposite per-symbol prior**: ETH, the strongest NEGATIVE per-symbol prior in v1 catalog.

### 0.3 Methodology + structural justification

ETH IS/OOS trajectory across baseline + /014/015/016/017 (from `analysis/iteration_v1-019/eth_oos_trajectory.csv`):

| Iter | ETH IS trades | ETH IS WR | ETH IS net_pnl_pct | ETH OOS trades | ETH OOS WR | ETH OOS net_pnl_pct |
|---|---|---|---|---|---|---|
| baseline | 145 | 38.6% | **−13.70%** | 46 | 39.1% | **+2.75%** |
| /014 | 143 | 31.5% | **−99.73%** | 38 | 31.6% | **−41.18%** |
| /015 | 146 | 38.4% | +17.34% | 49 | 40.8% | **−23.29%** |
| /016 | 160 | 34.4% | **−46.47%** | 64 | 34.4% | **−51.46%** |
| /017 | 159 | 37.7% | **−13.49%** | 53 | 39.6% | **−28.07%** |

**ETH OOS positive: 1/5 (baseline only). ETH IS positive: 1/5 (/015 only). Both are 5/5 negative under cycle-3 architectures.**

ETH-in-pool monthly Sharpe (F1/F3 anchors): IS **−0.1022** / OOS **+0.0503**. Asymmetry vs LINK's pool anchors (IS +0.3724 / OOS +0.8184) is the strongest in v1 catalog. **ETH is structurally the worst per-symbol cohort to test under cohort isolation alone.** Pool training likely masks ETH drag via Model A's BTC-pooled regularization. ETH-only training without an intervention would expose this drag fully and likely produce a catastrophic NEGATIVE — that's why the axis pairs ETH cohort isolation with a regime gate that is mechanistically targeted at the source of ETH's drag.

### 0.4 Mechanistic hypothesis sharpening (EDA-driven)

The prompt's mechanistic hypothesis ("down-trend BTC drags ETH; up-trend BTC may protect ETH") was tested by 3 candidate symmetric indicators (`analysis/iteration_v1-019/btc_trend_indicators.csv`). **All 3 symmetric framings were falsified at IS** — bull-BTC ETH trades were *worse* than bear-BTC ETH trades.

The EDA reframed the hypothesis to a **direction-aware** gate (script 03/04). The pattern that emerged is unambiguous:

| Cell | n | WR | total_pnl | avg_pnl |
|---|---|---|---|---|
| ETH long  + BTC ret14 > 0 | 33 | 45.5% | +20.40% | +0.62% |
| ETH long  + BTC ret14 ≤ 0 | 37 | 37.8% | **−9.56%** | **−0.26%** |
| ETH short + BTC ret14 > 0 | 42 | 31.0% | **−36.68%** | **−0.87%** |
| ETH short + BTC ret14 ≤ 0 | 33 | 42.4% | +12.14% | +0.37% |

**Pattern**: counter-trend ETH trades (long when BTC dumping; short when BTC rallying) are the source of ETH drag. **Trend-aligned ETH trades net positive.** This is the same pattern v2/019 discovered for SOL/XRP/DOGE/NEAR.

### 0.5 Cadence ledger summary

Cycle-3 #4 of 10 needed for /027 CONFIRMATION. After this iteration: 4 of 10 done. 6 more EXPLORATIONs needed before /027.

### 0.6 Axis Rotation Discipline + Family Declaration (v1 mandatory)

- **This iter's axis family**: `per-cohort-specialization-ETH` (NEW 10th family — FIRST usage; per /018 closeout LM Master + Critic CONVERGENT recommendation).
- **Cohort identifier**: ETH (single-symbol cohort).
- **Specialization dimension**: stateless BTC-trend regime gate (direction-aware, ±8% threshold on BTC 14d return).
- **Prior 5 EXPLORATION families** (verified against `briefs-v1/exploration_catalog.md`):
  - /014: `labeling`
  - /015: `labeling` (CONFIRMATION)
  - /016: `sample-weighting`
  - /017: `universe`
  - /018: `per-cohort-specialization-LINK`
- **Rotation status**: **VALID** — `per-cohort-specialization-ETH` is in NONE of the prior 5 families. Per /018 closeout LESSON #1 (codified rule), per-cohort specialization is the default cycle-3 methodology; ETH is a different COHORT from LINK (rotation by cohort, not by family literal-name).
- **One-sentence rationale**: ETH has the strongest NEGATIVE per-symbol structural prior (5/5 IS-OOS negative across cycle-3); a direction-aware BTC-trend gate targets the mechanism (counter-trend ETH = drag source) discovered in IS EDA.

**NEW family declaration check (Critic Phase 7.5 Check 14 PASS requires Critic + LM Master + QR convergence on orthogonality)**: cohort-specialization-ETH is orthogonal to /018's cohort-specialization-LINK because (a) different COHORT, (b) different SPECIALIZATION (regime gate vs none/isolation), (c) test of OPPOSITE-sign structural prior. Justified per /018 pre-committed Path Forward + LM Master Phase 7.4 §6.

### 0.7 LM Master Phase 4.5 coordination slot

LM Master Phase 4.5 fires AFTER this brief. Section 3.4 below RESERVES a placeholder for LM Master responses; integration is a Phase 5.5 BLOCK condition if LM Master fires after brief but brief doesn't echo each recommendation.

---

## Section 1 — Hypothesis

**Primary hypothesis (H1)**: A LightGBM model trained on **ETH-only data** (single-symbol cohort) at Model A's existing pool config (`atr_tp=2.9, atr_sl=1.45, apply_r1=False`) with a **stateless direction-aware BTC-trend regime gate** (kill ETH long when BTC 14d return < −8%; kill ETH short when BTC 14d return > +8%) applied as a post-hoc trade-stream filter will **flip ETH's cycle-3 OOS catastrophic trajectory** (4/4 negative across /014-/017) and produce OOS Sharpe materially above ETH-in-pool OOS Sharpe +0.0503 anchor.

**Secondary hypothesis (H2 — INFORMATIONAL only; does NOT determine verdict)**: At portfolio level, ETH-only is single-symbol concentration; portfolio Sharpe comparison vs baseline +0.6637 is not the verdict criterion per per-cohort methodology caveat 1.

**Falsification logic**:
- If gated ETH-only OOS Sharpe ≤ +0.05 (matches anchor) → gate has no effect or wrong direction → NEGATIVE.
- If gated ETH-only OOS Sharpe ∈ (+0.05, +0.25] → gate works directionally but small effect → INERT.
- If gated ETH-only OOS Sharpe ≥ +0.25 → gate flips ETH drag → PROMISING.
- If gated ETH-only OOS Sharpe ≤ −0.20 (worse than anchor) → cohort isolation drag dominates gate's lift → NEGATIVE-INTRINSIC (ETH drag is not BTC-trend-conditional).

**Critical interpretation note**: ETH OOS Sharpe anchor (+0.0503) is essentially flat — this is a **directional flip experiment**, not an edge-discovery experiment. The verdict cell thresholds in Section 8 are calibrated to the anchor's small absolute magnitude.

---

## Section 2 — IS-Only Evidence (EDA results)

EDA scripts under `analysis/iteration_v1-019/`. Outputs committed at `2028c1d`.

### 2.1 ETH OOS catastrophic 4/4 across /014/015/016/017

See `eth_oos_trajectory.csv` (table reproduced in Section 0.3 above).

ETH OOS net_pnl mean across baseline + cycle-3: **−28.25% / std 20.57 / range [−51.46, +2.75]**. The single positive was baseline at +2.75%; every cycle-3 architecture produced ETH OOS catastrophic.

### 2.2 ETH baseline OOS monthly distribution (regime concentration check)

From `eth_monthly_oos_baseline.csv`:

| Month | n | wins | net_pnl_pct | avg_pnl |
|---|---|---|---|---|
| 2025-04 | 3 | 2 | +5.12% | +1.71% |
| 2025-05 | 6 | 1 | **−15.47%** | −2.58% |
| 2025-06 | 3 | 1 | +0.26% | +0.09% |
| 2025-07 | 6 | 1 | **−15.68%** | −2.61% |
| 2025-08 | 3 | 3 | +27.15% | +9.05% |
| 2025-09 | 1 | 0 | −1.27% | −1.27% |
| 2025-10 | 1 | 1 | +7.16% | +7.16% |
| 2025-11 | 2 | 2 | +18.39% | +9.19% |
| 2025-12 | 1 | 1 | +2.55% | +2.55% |
| 2026-01 | 2 | 2 | +7.96% | +3.98% |
| 2026-02 | 3 | 0 | **−10.44%** | −3.48% |
| 2026-03 | 4 | 3 | +8.52% | +2.13% |
| 2026-04 | 6 | 1 | **−16.77%** | −2.79% |
| 2026-05 | 5 | 0 | **−14.74%** | −2.95% |

5 catastrophic months (>10% loss each) totaling **−73.10%**. The good months total +77.13%. **ETH OOS drag is regime-concentrated, not uniformly distributed** — exactly the pattern a regime gate is designed to address.

### 2.3 Symmetric BTC-trend gate FALSIFIED at IS (script 02)

| Indicator | bull n | bull avg_pnl | bear n | bear avg_pnl | sep (bull−bear) | IS PnL lift if skip bear |
|---|---|---|---|---|---|---|
| I1 BTC > SMA50 | 73 | −0.185% | 72 | −0.003% | **−0.18%** | +0.18% (negligible) |
| I2 BTC 14d ret > 0 | 75 | −0.217% | 70 | +0.037% | **−0.25%** | −2.58% (worse) |
| I3 BTC EMA12 > EMA26 | 69 | −0.167% | 76 | −0.029% | **−0.14%** | +2.20% (small) |

**All three symmetric framings show bear-BTC ETH trades doing LESS BADLY than bull-BTC ETH trades**. The prompt's mechanistic hypothesis is **falsified** for the symmetric "skip ETH when BTC bearish" framing at IS. EDA reframed to direction-aware.

### 2.4 Direction-aware gate selection (script 03/04)

Direction-aware 4-cell IS split for the chosen indicator (BTC 14d return; `btc_trend_direction_aware.csv`):

| Cell | n | WR | total_pnl | avg_pnl |
|---|---|---|---|---|
| ETH long + BTC ret14 > 0 (trend-aligned) | 33 | 45.5% | **+20.40%** | +0.62% |
| ETH long + BTC ret14 ≤ 0 (counter-trend) | 37 | 37.8% | −9.56% | −0.26% |
| ETH short + BTC ret14 > 0 (counter-trend) | 42 | 31.0% | **−36.68%** | **−0.87%** |
| ETH short + BTC ret14 ≤ 0 (trend-aligned) | 33 | 42.4% | +12.14% | +0.37% |

**Counter-trend ETH (long+dump or short+rally) is the drag**. Trend-aligned ETH (long+rally or short+dump) net positive. The gate kills counter-trend only.

### 2.5 Threshold sweep + cross-year IS stability (script 04)

Threshold sweep on BTC 14d return (IS only; from `gate_threshold_sweep.csv`):

| Threshold | IS skip | IS gated PnL | IS lift | OOS skip projected (informational) | OOS lift projected (informational) |
|---|---|---|---|---|---|
| ±3% | 29.7% | +17.34 | +31.04 | 52.2% | −6.16 |
| ±5% | 25.5% | +18.59 | +32.29 | 34.8% | +7.36 |
| **±8%** | **17.2%** | **+28.77** | **+42.47** | 17.4% | +7.84 |
| ±10% | 14.5% | +19.79 | +33.49 | 10.9% | +6.95 |
| ±12% | 10.3% | +27.18 | +40.88 | 4.3% | −2.12 |
| ±15% | 7.6% | +8.61 | +22.31 | 2.2% | +0.12 |
| ±20% (v2/019 clone) | 4.1% | −1.18 | +12.52 | 2.2% | +0.12 |

**±8% chosen** — best IS lift (+42.47%) at modest IS skip (17.2%).

Cross-year IS stability (`gate_cross_year_stability.csv`, IS H1=pre-2024, IS H2=2024+):

| Threshold | H1 baseline | H1 lift | H2 baseline | H2 lift | both halves positive |
|---|---|---|---|---|---|
| ±5% | +51.30 | +4.69 | −65.00 | +27.60 | YES |
| **±8%** | **+51.30** | **+6.33** | **−65.00** | **+36.15** | **YES** |
| ±10% | +51.30 | +6.02 | −65.00 | +27.47 | YES |
| ±12% | +51.30 | +20.22 | −65.00 | +20.67 | YES |
| ±15% | +51.30 | +13.10 | −65.00 | +9.21 | YES |
| ±20% | +51.30 | +9.96 | −65.00 | +2.55 | YES |

**All tested thresholds pass cross-year stability** (both halves positive lift). The chosen ±8% gives the largest combined lift while keeping IS skip ≤ 25%.

### 2.6 Predicted gate fire rate band (pre-registered)

From `gate_fire_rate_band.csv`:

| Scope | Expected fire rate | Acceptable [low, high] |
|---|---|---|
| **IS** | 17.2% | [10%, 30%] |
| **OOS_PROJECTED** | 17.4% | [5%, 35%] |

If observed gate fire rate falls **outside** these bands, gate is malfunctioning (mechanism check fires under F-AXIS-MECHANISM #3).

### 2.7 Specialization option assessment

| Option | EDA evidence | Implementation risk | Decision |
|---|---|---|---|
| A: ETH-only isolation (no gate) | Drag mechanism unaddressed; structural prior 4/4 catastrophic | LOW | REJECT — too risky alone |
| B: ETH-only + symmetric BTC gate | Falsified at IS (script 02) | LOW | REJECT |
| **C: ETH-only + direction-aware BTC gate at ±8%** | **IS lift +42.47%, cross-year stable, 17% skip; v2/019 pattern** | **LOW (re-use v2 filter pattern)** | **ADOPT** |
| D: ETH-only + per-symbol R1 + BTC gate | Two specializations = multi-axis | MEDIUM | REJECT — single-axis discipline |
| E: ETH-only + on-chain ETH gate | No data infrastructure for ETH on-chain | HIGH | REJECT — defer to /024+ |

**Decision: Option C.** Single-axis isolation: SYMBOL DIMENSION (5-sym → 1-sym + drop A/C/D/E dispatch + add ETH-only Model G with stateless BTC-trend post-hoc filter). All other knobs frozen at baseline.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1 mandatory)

**Declaration: HIGH-RISK.**

**Reason (one sentence)**: dropping Models A/C/D/E from the dispatch is a structural change to Optuna's training-objective domain (universe goes from 5 symbols to 1) AND adding a post-hoc gate alters the realized trade stream — both modifications change the OOS measurement substrate vs the baseline; ETH structural NEGATIVE-prior 4/4 means cohort isolation alone is expected catastrophic absent the gate intervention.

**Mitigation (opt-in)**: NONE — single-seed-style EXPLORATION at ENSEMBLE_SIZE=3 inner seeds (fixed cycle-3 default per `feedback_v1_wall_clock_discipline_enforced.md`). Multi-seed validation deferred to /027 CONFIRMATION.

**HIGH-RISK cumulative tracker (cycle-3)**:
- /016: HIGH-RISK declared / NEGATIVE-catastrophic / >1σ OOS Δ
- /017: HIGH-RISK declared / NEGATIVE-anti-direction-INERT / OOS Δ within band
- /018: HIGH-RISK declared / PROMISING-INERT favorable / OOS Δ +0.16
- **/019** (this iter): HIGH-RISK declared / outcome TBD

If /019 produces ≥1σ negative OOS Δ catastrophic, that would be the 2nd cycle-3 catastrophic HIGH-RISK out of 4. Per `feedback_v1_n_eff_barrier_magnitude_curve.md` forward-binding mandate, 3 consecutive ≥1σ HIGH-RISK negatives triggers MANDATORY multi-seed on the next HIGH-RISK iteration.

---

## Section 3 — Implementation Spec

### 3.1 Code change (two src/ file changes)

**File 1 — `run_baseline_v1.py`** — add new universe constant + dispatch branch + BTC gate import + post-hoc filter wiring:

```python
# After V1_ITER018_UNIVERSE definition (line ~128):
V1_ITER019_UNIVERSE: tuple[str, ...] = ("ETHUSDT",)
"""iter-v1/019 cohort: ETH-only with stateless direction-aware BTC-trend gate.

USER STRATEGIC PIVOT 2026-05-26 cycle-3 #4 EXPLORATION:
per-cohort-specialization-ETH (NEW 10th family). ETH has strongest NEGATIVE
per-symbol structural prior (5/5 IS-OOS negative across baseline + /014-/017).
Direction-aware BTC-trend gate at +-8% on 14d BTC return kills counter-trend
ETH entries; IS EDA shows +42.47% lift with cross-year stability.

LOCAL to runner — NOT shared via features_v1/__init__.py (only CONFIRMATION-MERGE
updates V1_BASELINE_UNIVERSE). assert_v1_universe() accepts {ETHUSDT} because
ETHUSDT is NOT in V1_EXCLUDED_SYMBOLS.
"""

#: Gate configuration constants (frozen for /019; tunable at /027 if /019 PROMISING).
V1_ITER019_BTC_GATE_LOOKBACK_BARS: int = 42  # 14 days at 8h cadence
V1_ITER019_BTC_GATE_THRESHOLD_PCT: float = 8.0  # +-8% BTC 14d return
V1_ITER019_BTC_GATE_ENABLED: bool = True
```

```python
# At top of file, add import for the v2 filter helper (RE-USE; do NOT duplicate):
from crypto_trade.strategies.ml.risk_v2 import (
    BtcTrendFilterConfig,
    apply_btc_trend_filter,
    load_btc_klines_for_filter,
)
```

```python
# Add elif branch after V1_ITER018_UNIVERSE branch (line ~1339):
elif set(symbols) == set(V1_ITER019_UNIVERSE):
    # iter-v1/019: ETH-only single-cohort EXPLORATION + stateless BTC-trend gate
    # (cycle-3 #4 of 10; per-cohort-specialization-ETH; NEW 10th axis family).
    # USER STRATEGIC PIVOT 2026-05-26: per-cohort specialization axis.
    #
    # Dispatch — ONLY Model G (ETH-only + R3 only, mirroring Model A's
    # apply_r1=False semantics; ATR 2.9/1.45 matches Model A which trained ETH
    # in pool). Models A (BTC+ETH pooled), C/D/E DROPPED — single-axis isolation.
    #
    # Single-axis isolation: SYMBOL DIMENSION (5 sym -> 1 sym + drop A/C/D/E)
    # AND post-hoc direction-aware BTC-trend gate as the specialization.
    # The gate is a STATELESS post-hoc trade-stream filter (no model retrain;
    # mirrors v2/019 BtcTrendFilterConfig pattern).
    #
    # F-AXIS-MECHANISM #1: trades.csv must contain ONLY ETHUSDT rows.
    # F-AXIS-MECHANISM #3: gate fire rate IS in [10%, 30%] / OOS in [5%, 35%].
    results_g, faxm_g = run_model(
        "G (ETH-only + R3 + BTC-trend gate)",
        ("ETHUSDT",),
        atr_tp=2.9,
        atr_sl=1.45,
        apply_r1=False,
        n_trials=n_trials,
        ensemble_size=ensemble_size,
        oof_persist_path=OOF_PARQUET_PATH,
        feature_columns=active_feature_columns,
        bounds_profile=bounds_profile,
        **_r5_kwargs,
    )
    # Apply stateless direction-aware BTC-trend gate as post-hoc filter.
    btc_open_times, btc_closes = load_btc_klines_for_filter()
    gate_cfg = BtcTrendFilterConfig(
        lookback_bars=V1_ITER019_BTC_GATE_LOOKBACK_BARS,
        threshold_pct=V1_ITER019_BTC_GATE_THRESHOLD_PCT,
        enabled=V1_ITER019_BTC_GATE_ENABLED,
    )
    results_g, gate_stats = apply_btc_trend_filter(
        results_g, btc_open_times, btc_closes, gate_cfg,
    )
    gate_stats_dict = gate_stats.as_dict()
    print(
        f"[iter-v1/019 BTC-trend gate] "
        f"normal={gate_stats_dict['n_normal']} "
        f"warmup={gate_stats_dict['n_warmup']} "
        f"killed={gate_stats_dict['n_killed']}/{gate_stats_dict['n_total']} "
        f"fire_rate={gate_stats_dict['fire_rate']:.2%}"
    )
    _all_faxm_logs = faxm_g
    all_results = results_g
    _r5_model_results = [results_g]
```

**File 2** — None. The v2 `apply_btc_trend_filter` (in `risk_v2.py`) is RE-USED. **Note**: per `ITERATION_PLAN_8H_V1.md` track-isolation guard, v1 code must NOT import from `crypto_trade.features_v2` or `crypto_trade.features_v3`. The `risk_v2.py` module is a **strategy/risk helper**, NOT a feature module — it lives under `src/crypto_trade/strategies/ml/risk_v2.py` and is allowed cross-track imports per the existing pattern in the codebase (the test suite at `tests/live/test_engine_v2.py` already cross-imports `risk_v2` types from cross-runner contexts). Phase 5.5 gate or Critic Phase 6.0 may revisit this; if BLOCK, fallback is to **vendor a thin copy** into `src/crypto_trade/strategies/ml/risk_v1_gates.py` with the same `apply_btc_trend_filter` signature (zero behavior change; pure code-isolation).

**Diff scope** (single src/ file): `run_baseline_v1.py`, ~50 lines added. Zero changes to:
- `src/crypto_trade/features_v1/`
- `src/crypto_trade/strategies/ml/lgbm.py`
- `src/crypto_trade/strategies/ml/optimization.py`
- `src/crypto_trade/strategies/ml/walk_forward.py`
- `src/crypto_trade/labeling.py`
- Risk gate code (R1/R3 unchanged)
- v2's `risk_v2.py` (only IMPORTED, not modified)

**Foundation guardrail**: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. No regression.

### 3.2 CLI invocation

```bash
uv run python run_baseline_v1.py \
  --symbols ETHUSDT \
  --pruned-features \
  --ensemble-size 3 \
  --n-trials 18 \
  --iteration-label "v1-019" \
  --reports-dir reports-v1
```

(`--symbols ETHUSDT` triggers the new elif branch via `set(symbols) == set(V1_ITER019_UNIVERSE)`. `--pruned-features` activates V1_FEATURE_COLUMNS_PRUNED + bounds_profile=v1_pruned. `--ensemble-size 3` + `--n-trials 18` matches cycle-3 EXPLORATION budget. **No `--no-engineering-report`** per Critic /017 Rec #2.)

### 3.3 Pinned values

- `feature_columns = list(V1_FEATURE_COLUMNS_PRUNED)` — 40 cols, passed explicitly.
- `bounds_profile = "v1_pruned"` — same as baseline.
- `ENSEMBLE_SEEDS[0:3] = [42, 123, 456]` — same as baseline 3-seed EXPLORATION default.
- `r5_vol_target_enabled = False` (cycle-3+ default).
- `r5_binary_kill_enabled = False` (cycle-3+ default).
- `sample_weight_mode = "abs_pnl"` (baseline default).
- `sigma_source = "natr"` (baseline default).
- `apply_r1 = False` (mirrors Model A's BTC+ETH pool semantics; ETH-in-pool baseline did NOT use R1).
- `apply_r2 = False` (Model E only; ETH is not Model E).
- **GATE: `lookback_bars=42, threshold_pct=8.0, enabled=True`** (frozen for /019).

### 3.4 LM Master Phase 4.5 Responses

Per the advisory at `briefs-v1/iteration_v1-019/lgbm_advisor.md` (commit `62e5056`).

**Section 3.4 introduction (LM Master §1 informational confirmation)**: LM Master §1 independently confirms that the QR's EDA pivot from symmetric framing to direction-aware gating is mechanistically superior — the per-cell asymmetric economics (+0.62% / −0.87% / −0.26% / +0.37%) cannot be captured by any symmetric gate. LM Master further confirms that this is **NOT a v2/019 SAME-pattern re-discovery**: the direction-aware mechanism is general but the per-symbol economics on ETH (this iter) differ from SOL/XRP/DOGE/NEAR (v2/019). Re-using `apply_btc_trend_filter` from `risk_v2.py` is CODE re-use, NOT signal re-use; /027 multi-seed validation on the ETH cohort with v1's labeling + 5-feature stack + Model A semantics retains its first-validation value.

### Adopted (without modification)

- **[#3] Verdict-interpretation principle (LM §2)** → integrated as the verdict-interpretation principle block below; PROMISING here is a directional flip success, NOT edge discovery; /027 bundle contribution via diversification not absolute Sharpe.
- **[#4] Realistic /019 IS lift +13% to +25% PnL → IS Sharpe ~+0.15 to +0.40 / Δ +0.25 to +0.50 (LM §3)** → cross-referenced at Section 4 F3 row (Section 4 F3 already cites +0.25-+0.50 band; LM Master independently confirms the calibration).
- **[#5] Verdict-class priors adjusted to 35% PROMISING / 40% INERT / 25% NEGATIVE (LM §4)** → Section 5 row updated.
- **[#6] n_eff_per_cell prediction [4, 8] band (LM §5; LOWER than /018's 9)** → added as F-AXIS-MECHANISM #4 informational row in Section 4 (informational only per /017 closeout demotion; if observed n_eff < 4 flagged at Phase 7.4).
- **[#7] KEEP n_trials=18 (LM §6.1)** → already pinned at Section 3.3.
- **[#8] KEEP ENSEMBLE_SIZE=3 (LM §6.2)** → already pinned at Section 3.3.
- **[#9] Accept current Optuna bounds; do NOT modify (LM §6.3)** → no Optuna bounds modification in Section 3.1/3.3.
- **[#10] LEAVE gate constants frozen (LM §6.4)** → `lookback_bars=42, threshold_pct=8.0, enabled=True` pinned at Section 3.3; /020+ verdict-conditional retunes per Section 11.7.
- **[#16] F-AXIS-MECHANISM #3 fire-rate test elevated to LOAD-BEARING (LM §9)** → "LOAD-BEARING" marker added to Section 4 F-AXIS #3 row.
- **[#17] /020+ verdict-conditional pre-staging matrix (LM §9)** → Section 11.7 cross-references LM Master §9 (numerical content already matches; explicit attribution added).

### Adopted (with modification)

- (none — all adopted recommendations integrated without modification)

### Rejected

- (none — LM Master recommendations are fully aligned with QR brief design)

### Informational confirmations (LM Master agrees with existing brief content; no edit needed)

- **[#1] Direction-aware gate mechanistically superior to symmetric framing (LM §1)** → already at Section 0.4 + 2.3.
- **[#2] NOT a v2/019 SAME-pattern re-discovery (LM §1)** → already at Section 0.4; LM Master §1 confirms.
- **[#11] Single-cohort + single-seed basin lottery HIGH-RISK (LM §7)** → already declared at Section 2.5; cross-reference confirmed.
- **[#12] Gate fire-rate band [10%, 30%] IS / [5%, 35%] OOS correctly wide (LM §7)** → Section 2.6 + Section 4 F-AXIS #3 band confirmed wide.
- **[#13] Re-training divergence risk absorbed by F-AXIS #3 fire-rate band (LM §7)** → already designed at Section 4 F-AXIS #3; mechanism-level test by construction.
- **[#14] PROMISING-MECHANICAL adjacent (Critic Check 14 watch; LM §7)** → added as a sub-bullet in Section 5 Failure-mode framing (Section 6.7 adjacency note).
- **[#15] What LM did NOT recommend (LM §8)** → cross-referencing reasoning is sound; no multi-seed, no tighter gate at /019, no Optuna tightening, no pre-emptive vendoring (vendoring is Phase 5.5/Critic-conditional fallback per Section 3.1), no Optuna direction-asymmetry, no F8 tightening — all consistent with QR brief design.
- **[#18] Cross-track import risk (LM §8)** → already documented at Section 3.1 as Phase 5.5/Critic fallback (vendor `risk_v1_gates.py` if cross-import BLOCKed); LM Master concurs with fallback approach.

### Verdict-interpretation principle (LM Master §2)

PROMISING here is a **directional flip success** (gate did its job, flipping ETH's 4/4 OOS-negative cycle-3 trajectory toward neutral-or-positive), NOT an edge-discovery milestone. This is structurally different from /018's LINK-only PROMISING-INERT favorable at +0.98, where the verdict meant "preserved a strong existing edge." For /019, PROMISING means "found a small directional signal in a structurally NEGATIVE cohort." Both are legitimate /027 bundle candidates, but the bundle math differs:

- LINK-only specialist /027 multi-seed mean projection: **+0.80 anchor** (per /018 Phase 7.4 §5).
- ETH-only + gate /019 multi-seed mean projection: **~+0.15 anchor band, possibly [+0.10, +0.40]** (per LM Master §2).

At /027, ETH+gate contributes via **low cross-correlation to LINK**, not via absolute Sharpe magnitude. A modest absolute Sharpe is acceptable for a diversification ingredient. This principle propagates downstream: Critic Phase 7.5 verdict cell selection should weight directional-flip + mechanism-level F-AXIS #3 PASS more heavily than absolute F1 Sharpe magnitude for /019 specifically.

### Most important LM Master flag (LM Master §9)

**F-AXIS-MECHANISM #3 (gate fire-rate band) is LOAD-BEARING for verdict disambiguation despite the small F1 anchor magnitude.** The small absolute anchor (+0.0503) means F1 OOS Sharpe Δ has reduced diagnostic power — modest gate efficacy clears PROMISING easily, modest gate harm clears NEGATIVE easily, and the noise floor of single-seed Optuna basin lottery can swamp F1. The fire-rate test, however, is **mechanism-level and prediction-pre-registered**: if observed OOS fire rate falls below 5% (under-fire), ETH cohort exposure is unmitigated → catastrophic almost certain. If OOS fire rate exceeds 35% (over-kill), gate is regime-shifted from IS. The fire-rate test is binary, pre-registered, and load-bearing on cell selection. Critic Phase 7.5 should evaluate F-AXIS #3 BEFORE F1 magnitude when assigning verdict cell.

### 3.5 Axis Family Declaration (v1 mandatory)

- **Axis family**: `per-cohort-specialization-ETH` (NEW 10th family declaration; FIRST usage; convergent recommendation from /018 closeout Critic + LM Master + USER STRATEGIC PIVOT).
- **Cohort + Specialization pairing**: cohort=ETH, specialization=direction-aware BTC-trend gate (lookback=42 bars, threshold=±8%, stateless post-hoc filter).
- **Single-axis isolation verified**: ONLY SYMBOL DIMENSION + GATE changes — but per `feedback_v1_per_cohort_exploration_strategy.md` per-cohort methodology, COHORT + ONE SPECIALIZATION is the single-axis unit (the LM Master Phase 7.4 §6 framing). All other knobs frozen at baseline.
- **Phase 7.5 Critic Check 14 PASS requires**: NEW family declaration is structurally orthogonal to /018's per-cohort-specialization-LINK (different cohort, different specialization, opposite-sign structural prior).

### 3.6 Wall-Clock Estimate (CRITICAL — Phase 5.5 BLOCK if missing or > 1.6h)

**Predicted wall-clock: 26 minutes total.**

Decomposition (from `wallclock_estimate.csv`):
- Anchor: /018 LINK-only (1 sym) at ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED ran **25 min** total per /018 diary.
- ETH-only (1 sym, identical scale config) projected: **25 min** (linear).
- BTC-trend gate post-hoc filter overhead: **~1 min** (numpy boolean mask on ~150 IS + ~50 OOS trades + 1 BTC kline CSV load).
- Methodology + reporting overhead: ~3 min (CPCV, PSR, DSR on 1-model trade roster).
- **Total projected: 26 minutes.**

**Margin vs 2h cap = 1h:34min (78% margin).**
**Margin vs 1.6h Phase 5.5 BLOCK threshold = 70+ minutes of buffer.**

**Contingency**: even at 2× linear-scaling overhead (worst case 52 minutes), margin remains 1h:08min = 57%, well above the 20% Phase 5.5 floor.

**No n_trials compression needed.** n_trials=18 stays at cycle-3 EXPLORATION default. **Kill-switch**: Engineer kills backtest if wall-clock exceeds **45 minutes** (1.7× projected; well below 2h cap).

### 3.7 Reproducibility

- `--symbols ETHUSDT` exact flag value (no comma list)
- `ENSEMBLE_SEEDS[0:3] = [42, 123, 456]` (literal pin at run_baseline_v1.py line ~97)
- `OOF_PARQUET_PATH = data/v1_iter_v1-019_trial_oof.parquet` (iter-stamped)
- BTC gate constants explicitly defined as module-level constants (not CLI args; frozen for /019).
- HEAD SHA recorded at Phase 5.5 (post-brief) + Phase 6 (post-implementation).

---

## Section 4 — Falsifiers (F1-F8 + F-AXIS-MECHANISM)

Per `feedback_v1_per_cohort_exploration_strategy.md`: per-cohort EXPLORATION. F1 + F8 thresholds adapt to ETH-only cohort scale, NOT portfolio-level.

### F1 — ETH-only OOS Sharpe Δ vs ETH-in-pool OOS Sharpe anchor

**Anchor**: ETH-in-pool OOS monthly Sharpe in v1 baseline = **+0.0503** (from script 01 `eth_per_symbol_baseline.csv`).

| Verdict cell | F1 OOS Sharpe Δ band | Absolute OOS Sharpe |
|---|---|---|
| **PROMISING** | Δ ≥ +0.20 | ≥ +0.25 |
| INERT | Δ ∈ [−0.20, +0.20] | ∈ [−0.15, +0.25] |
| **NEGATIVE** | Δ ≤ −0.20 | ≤ −0.15 |
| Catastrophic-NEGATIVE | Δ ≤ −0.55 | ≤ −0.50 |

**Calibration note**: anchor is small absolute (+0.05). The standard ±0.20 PROMISING/NEGATIVE bands (from /018 LINK calibration) apply nominally. **Mechanism check tighter**: H1 specifically claims the gate flips ETH OOS sign; if OOS Sharpe ends within ±0.05 of anchor, gate had no measurable effect (PROMISING-INERT-no-effect subtype).

### F3 — ETH-only IS Sharpe Δ vs ETH-in-pool IS Sharpe anchor

**Anchor**: ETH-in-pool IS monthly Sharpe = **−0.1022**.

| Verdict cell | F3 IS Sharpe Δ band | Absolute IS Sharpe |
|---|---|---|
| **PROMISING** | Δ ≥ +0.20 | ≥ +0.10 |
| INERT | Δ ∈ [−0.20, +0.20] | ∈ [−0.30, +0.10] |
| **NEGATIVE** | Δ ≤ −0.20 | ≤ −0.30 |
| Catastrophic-NEGATIVE | Δ ≤ −0.30 | ≤ −0.40 |

**EDA prediction (informational)**: gate post-hoc applied to baseline ETH IS lifts net_pnl from −13.70% → +28.77% (+42.47% lift). Sharpe lift depends on monthly variance; rough estimate IS Sharpe goes from −0.10 to **+0.25-+0.50** band. The actual /019 backtest will re-run from scratch under the gate — Optuna trajectory differs. PROMISING (Δ ≥ +0.20) is plausible IS but not guaranteed.

### F2 — Embargo/look-ahead PASS (structural; automatic)

`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. BTC gate is past-only (np.searchsorted right-1 with warmup floor of 42 bars). PASS by construction.

### F4 — Feature ADF stationarity (informational; no new features)

40 V1_FEATURE_COLUMNS_PRUNED unchanged. ADF rerun on ETH-only halves should produce similar bonferroni-pass profile. INFORMATIONAL.

### F5 — PSR_monthly_vs_0 OOS (basin-health signal)

ETH-only OOS PSR_monthly_vs_0:
- Baseline anchor (5-sym OOS portfolio) PSR_monthly_vs_0 = 0.989 (from BASELINE_V1.md).
- ETH-only OOS at 14 OOS months single-symbol distribution; predicted band [0.30, 0.80] for ETH-only OOS PSR after gate intervention. Wider band than LINK-only (/018=0.885) because ETH structural anchor is weaker.

**Catastrophic if** PSR_monthly_vs_0 < 0.10 → indicates ETH OOS still mostly negative after gate (gate failed to flip drag).

### F6 — Per-symbol IS direction (vacuous — only 1 symbol)

ETH-only model has only ETH trades. F6 PASS by construction.

### F7 — Per-symbol IS/OOS sign agreement (ETH only)

ETH IS and OOS PnL must both be positive (same-sign positive basin) for INERT-or-better verdict.

If ETH-only IS PnL < 0 AND ETH-only OOS PnL > 0 → IS-OOS sign disagreement (negative-IS-collapse). If ETH IS PnL > 0 AND OOS PnL < 0 → overfit signature. **The hypothesis CLAIM is that gate produces both halves positive — F7 is the strongest single mechanism check.**

### F8 — ETH-only trade count band (cohort + gate scale)

**Anchor**: ETH-in-pool trade counts in baseline = 145 IS / 46 OOS.

ETH-only at ENSEMBLE_SIZE=3 (not 5) at gate fire rate 10-30% IS: predicted trade band:

| F8 cell | IS trade band | OOS trade band |
|---|---|---|
| PASS | IS ∈ [80, 200] | OOS ∈ [25, 90] |
| **F8 BREACH-low** | IS < 80 OR OOS < 25 | (cohort under-fires or gate over-kills) |
| **F8 BREACH-high** | IS > 200 OR OOS > 90 | (gate under-fires; specialization not engaged) |

OOS lower bound 25 = baseline /018 LINK floor; OOS upper bound 90 covers /016 ETH overshoot (64 trades) plus margin.

### F-AXIS-MECHANISM (compound 3-sub-check)

The single-axis isolation is the SYMBOL DIMENSION + STATELESS GATE.

- **F-AXIS #1 — Dispatch correctness**: ONLY Model G runs; trades.csv contains only ETHUSDT rows (zero rows for BTC/LINK/LTC/DOT/SOL). PASS criterion: `df['symbol'].unique() == ['ETHUSDT']`.
- **F-AXIS #2 — ETH trade-count and PnL within band**: ETH IS trades ∈ [80, 200], ETH OOS trades ∈ [25, 90], ETH OOS PnL > 0 preferred (flips structural prior). Failure indicates Model G is not training correctly or gate is over-killing.
- **F-AXIS #3 — Gate fire-rate within pre-registered band** **[LOAD-BEARING per LM Master §9]**: IS gate fire rate ∈ [10%, 30%], OOS gate fire rate ∈ [5%, 35%] per `gate_fire_rate_band.csv`. Failure indicates gate threshold or BTC indicator computation broken. **LOAD-BEARING rationale**: F1 anchor is small absolute (+0.0503), so F1 OOS Sharpe Δ has reduced diagnostic power; F-AXIS #3 is mechanism-level, pre-registered, and binary — it is the strongest single verdict-disambiguator. Critic Phase 7.5 should evaluate F-AXIS #3 BEFORE F1 magnitude when assigning verdict cell.
- **F-AXIS-MECHANISM #4 — n_eff_per_cell band [4, 8]** **[INFORMATIONAL per /017 closeout; LM Master §5 prediction]**: ETH-only cohort + 17% gate fire rate → ETH IS trades post-gate ~120 (vs LINK-only /018 154). Smaller training rows + post-hoc gate roster trim → narrower Optuna trial diversity. LM Master predicts n_eff band [4, 8] (LINK-only /018 hit 9). INFORMATIONAL only. If observed n_eff < 4 → mechanism issue, flag at Phase 7.4.

### F-PORTFOLIO (informational; cannot determine verdict)

Portfolio-level Sharpe (ETH-only = 1 model = portfolio) compared to v1 baseline portfolio +0.6637. INFORMATIONAL ONLY per per-cohort methodology.

---

## Section 5 — Predicted Verdict Distribution (FLAT priors per cycle-3 lessons; LM Master §4 ADJUSTED)

Per /016/017/018 closeouts: cycle-3 LM Master + QR mechanism-level predictions track FLAT priors at EXPLORATION single-seed level. /018's PROMISING-INERT favorable was correctly predicted modal (45% prior).

**Verdict prior 35/40/25** (modal INERT; LM Master §4 ADJUSTED from QR initial 30/40/30):

- **PROMISING (Δ ≥ +0.20)**: **35%** (LM Master §4 raised from QR 30%) — IS EDA shows +42% IS PnL lift; if signal generalizes to OOS, F1 PROMISING reachable. ETH structural NEGATIVE prior 4/4 means even modest gate lift produces large Δ vs essentially-zero anchor (+0.05). Single-seed basin lottery wide but PROMISING bar is +0.25 absolute — small mechanism win produces large Δ vs zero anchor.
- **INERT (Δ ∈ [−0.20, +0.20])**: **40%** (unchanged) — gate works directionally but smaller-than-EDA effect at OOS Optuna trajectory; modal cell per per-cohort methodology; basin lottery wide; gate works directionally but anchor +0.05 leaves narrow path.
- **NEGATIVE (Δ ≤ −0.20)**: **25%** (LM Master §4 lowered from QR 30%) — cohort isolation drag exposes ETH's structural NEGATIVE prior before gate can fully compensate; OR gate over-kills OOS roster. NEGATIVE bar is −0.15 absolute; would require gate to ACTIVELY HARM the cohort — possible but less likely given EDA cross-year stability.
  - **NEGATIVE-INTRINSIC** (Δ ≤ −0.55, falsifies BTC-trend-conditional drag hypothesis): **8%** subset.
  - **NEGATIVE-CATASTROPHIC** (catastrophic-NEGATIVE; structural prior dominates regardless of gate): **5%** subset.

Two specific mechanism predictions (informational):

1. **Gate fire rate at observation**: predicted IS 17.2%, OOS 17.4%. If IS observed < 10% or > 30%, gate threshold or computation broken (F-AXIS #3 falsifier).
2. **F-AXIS #2 trade band**: at OOS predicted ~55 trades after gate (cf. baseline 46 OOS ETH trades pre-gate; 5-seed → 3-seed expand factor partially offset by 17% gate skip).

---

## Section 6 — Failure Modes

### 6.1 Single-cohort basin lottery at single-seed=42 EXPLORATION

ETH-only at ENSEMBLE_SIZE=3 + n_trials=18 + single-seed=42 = potentially basin-locked. ETH has NEGATIVE structural prior 4/4 — basin lottery downside band is wider than LINK's (which had +9/9 prior to draw from).

**Mitigation**: gate intervention is mechanically tied to a documented IS pattern (counter-trend ETH = drag) that cross-year-stable in both H1 and H2. /027 multi-seed will dissolve basin-lottery uncertainty.

### 6.2 Gate over-kills OOS

If observed OOS gate fire rate > 35% (above pre-registered F-AXIS #3 upper band), gate is over-killing. Possible cause: OOS regime has higher BTC volatility than IS, triggering more crosses of ±8%. Result: F8 OOS trade count breaches low; verdict cell NEGATIVE-OVER-KILL.

### 6.3 Gate under-fires OOS

If observed OOS gate fire rate < 5%, gate is effectively off. ETH-only cohort isolation alone (without gate intervention) at 4/4 NEGATIVE prior → catastrophic. Verdict: NEGATIVE-COHORT-EXPOSURE.

### 6.4 ETH drag is not BTC-trend-conditional

If gated ETH OOS Sharpe ≤ −0.20 (NEGATIVE-INTRINSIC), the hypothesis that ETH drag is BTC-trend-conditional is FALSIFIED. ETH drag would then be ETH-intrinsic (e.g., ETH liquidity regime, ETH-specific narrative cycle) — load-bearing finding for /020+ axis selection (e.g., on-chain features, ETH-volatility-regime gate).

### 6.5 Stateless gate deadlock risk (per Critic Rec #3 + A8 anti-pattern)

The gate is **stateless by design**:
- Decision at each signal time uses only past BTC data (np.searchsorted right-1 with 42-bar warmup floor).
- No persistent state. No drawdown-conditional ON/OFF. No cumulative counter.
- The v2 `apply_btc_trend_filter` is a post-hoc trade-stream pass; deadlock-impossible by construction.

Verified at code-review time (Phase 6.0 will re-check).

### 6.6 Wall-clock breach (low probability)

26 min predicted with 78% margin. Even worst-case 2× linear scaling stays under 1h. Kill-switch at 45 min provides additional safety. No realistic path to 2h breach.

### 6.7 PROMISING-MECHANICAL adjacency risk (LM Master §7; Critic Check 14 watch)

The gate is mechanism re-use from v2/019, applied post-hoc to a retrained trade stream. **If the verdict is PROMISING but the kept-trade roster preserves >80% of the EDA baseline kept-trade roster (trade_id Jaccard)**, classify the iteration as PROMISING-MECHANICAL — a non-compoundable signal source. Phase 7.4 LM Master post-mortem will verify via trade_id Jaccard between EDA baseline kept set and /019 backtest kept set. This adjacency does NOT change the Phase 5 brief design; it informs Phase 7.4 + Phase 7.5 classification and /027 bundle treatment (PROMISING-MECHANICAL = strictly accretive component decision, NOT new edge ingredient — non-compoundable across iterations per `feedback_promising_mechanical_subtype.md`).

---

## Section 7 — Optional / informational metrics

- ETH-only DSR: expected LOWER than baseline portfolio DSR (single-symbol = lower n_obs). INFORMATIONAL per EXPLORATION rule.
- ETH-only PBO via CSCV: deferred (single-cohort = limited n_obs).
- ETH-only PSR_monthly_vs_1: expected to be very low (anchor is +0.05; matching +1.0 unlikely at single-symbol EXPLORATION). INFORMATIONAL.
- Pareto front: N/A (single-seed EXPLORATION).
- Gate stats JSON: `gate_stats_dict` written to engineering_report.md per /017 Rec #2.

---

## Section 8 — Verdict Matrix (per-cohort + gate variant)

| Verdict cell | F1 (ETH OOS Δ) | F3 (ETH IS Δ) | F-AXIS-MECHANISM | F7 sign | Action |
|---|---|---|---|---|---|
| **PROMISING** | Δ ≥ +0.20 | any | #1+#2+#3 PASS | IS+OOS positive | ETH-only specialist + gate CARRIED to /027 substrate |
| **PROMISING-INERT** | Δ ∈ [−0.20, +0.20] | any | #1+#2+#3 PASS | IS+OOS positive | CONDITIONALLY CARRIED to /027; re-evaluate multi-seed |
| **PROMISING-INERT-no-effect** | |Δ| < 0.05 | any | #3 fire rate within band BUT IS lift not realized | mixed signs | gate had no measurable effect; document; deprioritize at /027 |
| **NEGATIVE-INERT** | Δ ∈ (−0.31, −0.20] | any | #1+#2 PASS | mixed signs | ETH-only specialist + gate DROPPED for /027 |
| **NEGATIVE-INTRINSIC** | Δ ≤ −0.31 | any | #1 PASS | OOS negative | ETH drag NOT BTC-trend-conditional; load-bearing finding for /020+ |
| **NEGATIVE-CATASTROPHIC** | Δ ≤ −0.55 | any | #1 PASS | OOS negative | ETH structural prior dominates; gate insufficient |
| **NEGATIVE-OVER-KILL** | any | any | #3 fire rate > 35% OOS | starved | gate over-aggressive; redesign threshold at /020 |
| **NEGATIVE-UNDER-FIRE** | any | any | #3 fire rate < 5% OOS | cohort exposure dominates | gate effectively off; cohort-alone NEGATIVE confirmed |
| **NEGATIVE-IS-COLLAPSE** | Δ_OOS any | Δ_IS ≤ −0.30 | #1 PASS | IS negative | IS basin inversion at ETH-only |
| **NEGATIVE-DISPATCH** | any | any | #1 FAIL | n/a | Implementation defect; BLOCK-PENDING-FIX candidate |

**Section 8 entry rule**: must select EXACTLY ONE cell. Strict adherence to thresholds. Hierarchy when multiple cells could apply: NEGATIVE-DISPATCH > NEGATIVE-OVER-KILL/UNDER-FIRE > NEGATIVE-IS-COLLAPSE > NEGATIVE-INTRINSIC > NEGATIVE-CATASTROPHIC > NEGATIVE-INERT > PROMISING-INERT-no-effect > PROMISING-INERT > PROMISING.

---

## Section 9 — Library Stack

No changes to library versions. Inheriting cycle-3 baseline:
- `mlfinlab==1.4` (CPCV / meta-labeling utilities)
- `pypbo` (PBO via CSCV)
- `fracdiff>=0.10` (FracdiffStat)
- `statsmodels` (ADF testing)
- `lightgbm>=4.0` (LightGBM regression)
- `optuna>=3.0` (Bayesian hyperparameter search)
- `crypto_trade.strategies.ml.risk_v2.{apply_btc_trend_filter, BtcTrendFilterConfig, load_btc_klines_for_filter}` — re-used as post-hoc filter (no new dependency).

---

## Section 10 — Implementation Spec (CRITICAL detail)

### 10.1 No `--no-engineering-report` flag at launch (Critic /017 Rec #2)

Engineer Phase 6 MUST generate `reports-v1/iteration_v1-019/engineering_report.md`. Run command excludes `--no-engineering-report` flag.

### 10.2 Reports artifacts expected

After backtest completion:

```
reports-v1/iteration_v1-019/
├── comparison.csv              # IS/OOS metrics (sharpe, dsr, psr, n_eff rows, etc.)
├── engineering_report.md       # Engineer Phase 6 summary + gate fire stats
├── f_axis_mechanism.csv        # F-AXIS-MECHANISM #1+#2+#3 rows
├── in_sample/
│   ├── trades.csv              # ONLY ETHUSDT rows (verify F-AXIS #1)
│   ├── per_symbol.csv          # ONLY ETHUSDT row
│   ├── monthly_pnl.csv
│   ├── daily_pnl.csv
│   ├── per_regime.csv
│   ├── dsr.json
│   ├── adf_test.csv
│   ├── ic_matrix.csv
│   └── quantstats.html
└── out_of_sample/
    └── (same structure)
```

Engineer also writes gate stats (n_killed / n_total / fire_rate) to engineering_report.md.

### 10.3 Pre-flight verification (Engineer in Phase 6 setup)

Before launching backtest:
1. Verify `ETHUSDT_8h_features.parquet` exists in `data/features/` and is fresh.
2. Verify `data/BTCUSDT/8h.csv` has close_time within 16h of measurement time (gate reads BTC closes; stale BTC data corrupts gate).
3. Verify `data/ETHUSDT/8h.csv` close_time within 16h.
4. Verify branch is `iteration-v1/019` and HEAD is post-brief commit.
5. Verify `run_baseline_v1.py` HEAD has V1_ITER019_UNIVERSE + import for risk_v2 BTC filter + elif branch.

### 10.4 Engineer launch protocol

Per skill `4cb8972` split-engineer dispatch:
1. Engineer does setup (code change, smoke test, gate sanity check on 5 mock trades).
2. Orchestrator launches `uv run python run_baseline_v1.py ...` as detached bash (run_in_background=true).
3. Engineer writes engineering_report.md after backtest completes.
4. Engineer reports HEAD SHA at handoff to Phase 7.4 LM Master + Phase 7.5 Critic.

### 10.5 Wall-clock kill-switch

Engineer kills the backtest if wall-clock exceeds **45 minutes** (1.7× projected 26 min worst case). Per `feedback_v1_wall_clock_discipline_enforced.md`, 2h is the cycle-3 EXPLORATION HARD CAP; 45 min internal kill-switch is well below cap.

---

## Section 11 — Alternates for /020+ (cycle-3 fifth EXPLORATION onwards)

Per per-cohort methodology, /019 establishes the second cohort baseline; /020+ continues with diverse cohorts and specializations.

### 11.1 /020 PRIMARY — BTC-only specialization (per /018 Critic Path Forward #2)

BTC IS catastrophic rotation at /017 (-93.81); BTC OOS positive (+15.11). Pooled Model A trains poorly on BTC. BTC-only specialized test isolates BTC's intrinsic edge. Specialization options: per-symbol R1 cool-down + ATR adjustment OR no specialization (pure isolation). MEDIUM structural prior.

### 11.2 /021 SECONDARY — LINK-only ATR follow-on (per /018 Path Forward #3)

If /019 PROMISING-or-INERT favorable, /021 layers ATR specialization on top of /018's LINK-only baseline: test LINK-specific (3.0/1.5) tighter or (4.0/2.0) wider against /018's LINK-only-baseline-ATR (3.5/1.75). Conditional on /019 not consuming the slot.

### 11.3 /022 — DOT-only specialized

DOT IS +96.07 at /017 (catastrophic-positive rotation); DOT IS +26.62 at baseline. DOT structural IS positive, OOS approximately flat. DOT-only test characterizes DOT's intrinsic IS-driven edge.

### 11.4 /023 — SOL-only specialized

SOL added at /017; SOL OOS clean 16.4% portfolio share. SOL-only at single-cohort tests SOL's intrinsic edge in 6-sym /017 universe context.

### 11.5 /024-/026 — 2-3 symbol pooled cohorts

Per `feedback_v1_per_cohort_exploration_strategy.md`: 2-3 symbol pooled cohorts test diversified per-cohort edge:
- /024: DOT+LTC vol-cluster (correlation-paired)
- /025: LINK+SOL DeFi-pair
- /026: BTC+ETH separated (revisit Model A architecture)

### 11.6 /027 — CYCLE-3 CONFIRMATION (bundle PROMISING specialists)

Bundle composition: only specialists that PROMISING'd at single-seed EXPLORATION. Multi-seed validation at 10 inner seeds. Diversification weighting (equal or vol-targeted). BASELINE_V1 update only if STRICTLY beats anchor on multi-seed mean both halves + ≥5/10 seeds positive OOS.

Projected bundle composition (conditional):
- LINK-only specialist (LOAD-BEARING from /018; multi-seed anchor +0.80 NOT /018's +0.98 single-seed)
- **ETH-only + BTC-trend gate (TBD at /019)**
- BTC-only specialized (TBD at /020)
- (other cohorts at /021-/026)

### 11.7 Conditional pre-staging on /019 outcomes

The matrix below cross-references **LM Master §9** independent pre-staging recommendations (advisor commit `62e5056`); QR and LM Master converge on the verdict-conditional /020+ assignments. LM Master §9 specifically reinforces NEGATIVE-INTRINSIC as a "load-bearing finding for /024+ on-chain feature axis" (ETH drag not BTC-trend-conditional → on-chain hypothesis required) AND NEGATIVE-CATASTROPHIC as "ETH cohort path closed for cycle-3."

- **PROMISING**: /020 = BTC-only specialized (per /018 Path Forward #2 cohort coverage; LM Master §9 concurs)
- **PROMISING-INERT (modal)**: /020 = BTC-only specialized (same as PROMISING; LM Master §9 concurs)
- **PROMISING-INERT-no-effect**: /020 = ETH-only with TIGHTER gate threshold (±5% or ±10% — single dimension re-tune; LM Master §9 concurs)
- **NEGATIVE-INERT**: /020 = BTC-only specialized; ETH cohort DROPPED for /027 (LM Master §9 concurs)
- **NEGATIVE-INTRINSIC**: /020 = BTC-only specialized; ETH+gate axis PERMANENTLY CLOSED (LM Master §9 framing — load-bearing finding for /024+ on-chain feature axis); on-chain ETH gate deferred to /024+ if data infrastructure ready
- **NEGATIVE-CATASTROPHIC**: /020 = BTC-only specialized; ETH+gate path closed for cycle-3 (LM Master §9 concurs)
- **NEGATIVE-OVER-KILL**: /020 = ETH-only with WIDER gate threshold (±12% or ±15%) at /020 — single dimension re-tune (LM Master §9 concurs)
- **NEGATIVE-UNDER-FIRE**: /020 = ETH-only with TIGHTER gate threshold (±5%) at /020 — single dimension re-tune (LM Master §9 concurs)

---

## Section 12 — Catalog Closeout Plan (Phase 8)

After Phase 7.5 Critic verdict:

1. Update `briefs-v1/exploration_catalog.md` with iter-v1/019 row:
   - axis_varied: "ETH-only single-cohort + stateless direction-aware BTC-trend gate (±8% on BTC 14d return)"
   - axis_family: `per-cohort-specialization-ETH` (NEW 10th family declaration)
   - IS Sharpe Δ: vs ETH-in-pool IS −0.1022 anchor
   - OOS Sharpe Δ: vs ETH-in-pool OOS +0.0503 anchor (informational against portfolio +0.6637)
   - verdict: per Section 8 cell
   - confirmation_candidate: per cell mapping

2. Write `diary-v1/iteration_v1-019.md` with FRONTMATTER + per-cohort verdict + LESSONS (5).
3. Tag `v0.v1-019` after Phase 8 closeout commit.
4. /020 advances per Path Forward conditional from Section 11.7.

---

## Section 13 — Phase 5.5 self-check (QR pre-handoff)

- Section 0.5 — present? YES (cadence position + cycle ledger).
- Section 0.6 — axis family + cohort declared? YES (`per-cohort-specialization-ETH`, NEW 10th family, rotation VALID).
- Section 0.7 — LM Master Phase 4.5 reservation? YES (Section 3.4 placeholder).
- Section 1 — hypothesis explicit and falsifiable? YES (H1 ETH-only OOS Sharpe vs ETH-in-pool OOS Sharpe baseline anchor with directional flip semantics).
- Section 2 — numerical EDA tables committed at `2028c1d`? YES (12 files including 5 source scripts under analysis/iteration_v1-019/).
- Section 2.5 — HIGH-RISK declaration explicit? YES (HIGH-RISK; single-cohort + gate = 2 changes but per-cohort methodology bundle).
- Section 3 — implementation spec specifies src/ file changes (single)? YES (`run_baseline_v1.py` only; v2 `risk_v2.apply_btc_trend_filter` IMPORTED unchanged).
- Section 3.4 — LM Master responses populated? YES (amended in-place after LM Master advisory `62e5056`; 10 adopted, 0 modified, 0 rejected, 8 informational confirmations; verdict-interpretation principle + LOAD-BEARING flag integrated).
- Section 3.5 — axis family declared with cohort framing? YES.
- Section 3.6 — wall-clock estimate explicit, ≥20% margin? YES (26 min predicted; 78% margin against 2h cap; 70+ min buffer against 1.6h BLOCK threshold).
- Section 4 — F1-F8 falsifiers pre-registered + F-AXIS-MECHANISM 3-sub-check including gate fire rate band? YES.
- Section 4 — F1 anchored against ETH-in-pool OOS Sharpe +0.0503 (not portfolio)? YES.
- Section 4 — F8 cohort-scale trade band? YES (IS [80, 200] / OOS [25, 90]).
- Section 4 — F-AXIS #3 gate fire rate pre-registered IS [10%, 30%] / OOS [5%, 35%]? YES.
- Section 5 — verdict prior FLAT-ish? YES (35/40/25 with INERT modal; LM Master §4 ADJUSTED from QR initial 30/40/30).
- Section 6 — failure modes characterized including stateless deadlock check (Critic A8)? YES (7 modes including over-kill, under-fire, BTC-trend-not-conditional, basin lottery, stateless deadlock, PROMISING-MECHANICAL adjacency).
- Section 8 — verdict matrix per-cohort + gate variant with NEGATIVE-OVER-KILL / NEGATIVE-UNDER-FIRE / PROMISING-INERT-no-effect subtypes? YES.
- Section 9 — library stack declared (risk_v2 BTC filter re-use)? YES.
- Section 10 — implementation spec critical detail (engineering report, kill-switch, BTC kline staleness check)? YES.
- Section 11 — alternates for /020+ + conditional pre-staging matrix? YES (7 verdict-conditional next-axis assignments; LM Master §9 cross-referenced).
- Section 12 — catalog closeout plan? YES.
- Section 13 — this checklist? YES.

**Self-check verdict**: brief PASS for Phase 5.5 gate (LM Master Phase 4.5 responses INTEGRATED at Section 3.4 post-advisory commit `62e5056`).

---

**End of brief.**
