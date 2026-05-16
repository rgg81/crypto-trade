# Engineering Report — iter-v3/081

## Headers

- Iteration: iter-v3/081
- Branch: iteration-v3/081 (cycle-2 shared branch, iteration-v3/047)
- Commit chain:
  - EDA: `be0ccf5` — `analysis/iteration_v3-081/baseline_integrity_audit.py` + T1-T4 CSVs
  - EDA ruff-clean: `f9ddea5`
  - Brief: `944dddf`
  - Brief SHA-backfill: `d544e65`
  - Setup: `5d42c4a` — Sub-fixes 1-3 (vol-floor revert + assertion + ITERATION_LABEL v3-081)
  - Phase 5.5 gate: `75248b3` — PASS
  - HEAD at report time: `75248b3`
- Hardware: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2, x86_64, 60 GB RAM
- Wall-clock time: 3.07h (within 6.0h CONFIRMATION cap; `--skip-features` per setup)
- Run mode: CONFIRMATION (NO `--exploration` flag) — `ENSEMBLE_SIZE=10`, unified 10-seed architecture
- Run command: `uv run python run_baseline_v3.py --clean-oof --skip-features`
- Optuna budget: 35 trials × 3 symbols × 10 seeds = 1050 trials total

### Ensemble architecture (10 seeds, 2 outer lineages)

| Index | Seed | Lineage |
|---|---:|---|
| 0 | 191664963 | outer=42 |
| 1 | 1662057957 | outer=42 |
| 2 | 1405681631 | outer=42 |
| 3 | 942484272 | outer=42 |
| 4 | 929893137 | outer=42 |
| 5 | 33158374 | outer=123 |
| 6 | 1465339467 | outer=123 |
| 7 | 1273345680 | outer=123 |
| 8 | 115579757 | outer=123 |
| 9 | 1952249162 | outer=123 |

`ensemble_summary.json` confirms: `mode=confirmation`, `ensemble_size=10`. Gate G.10 PASS.

---

## Configuration Diff vs BASELINE_V3.md (/059)

/081 is the cycle-2 CONFIRMATION re-validation of the genuine /059 canonical config. The single change from the current HEAD (pre-/081 setup) was reverting the illegitimate iter-v3/061 TRX `vol_scale_floor` accretion to `{}`.

| Parameter | Current HEAD before /081 | /081 | Change type |
|---|---|---|---|
| `vol_scale_floor_per_symbol` | `{"TRXUSDT": 0.5}` | `{}` | **REVERT** — illegitimate /061 EXPLORATION accretion removed |
| `ITERATION_LABEL` | `"v3-080"` | `"v3-081"` | Label bump |
| Runner pre-flight assertion `expected_floor_dict` | `{"TRXUSDT": 0.5}` | `{}` | Consistency with Sub-fix 1 |
| All other params | unchanged | unchanged | CLEAN (T1 audit confirmed HEAD == /059 on all other behavior-affecting knobs) |

After the revert, /081 is **bit-identical to the /059 canonical config** on every behavior-affecting parameter. Sacred constants confirmed: `OOS_CUTOFF_DATE = 2025-03-24`, `TRAINING_MONTHS = 24`, `REQUIRED_GAP = 66 = (21+1) × 3`.

### The revert context — /081 is the first genuine /059 re-measurement since /059 itself

The brief Section 2 (T1-T2 audit) established that `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` was introduced by iter-v3/061, an EXPLORATION with verdict INERT-AT-EXPLORATION, that was never tagged (`git tag -l v0.v3-*` returns only `{018, 028, 058, 059}`), and was never carried by a CONFIRMATION-MERGE. The /061 EXPLORATION closeout stated verbatim: "BASELINE_V3.md is UNCHANGED — /059 stays canonical." The vol-floor line rode forward silently through all 19 subsequent iterations (/062-/080) because each varied exactly one OTHER axis.

Cycle 1's /070 CONFIRMATION also ran with the /061 floor active. **`/081 is therefore the first CONFIRMATION-class run since /059 itself to measure the genuine /059 canonical config.`**

---

## Key Metrics Block

### Headline vs BASELINE_V3.md /059 (the re-validation target)

| Metric | BASELINE_V3.md /059 | /081 IS | IS Δ | /059 OOS | /081 OOS | OOS Δ | /081 OOS/IS |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +1.0894 | **+1.0894** | **0.0000** | +0.5791 | **+0.5999** | **+0.0208** | **0.5507** |
| daily_sharpe | — | +2.7092 | — | — | +1.4871 | — | 0.5489 |
| max_drawdown | — | 30.97% | — | — | 34.53% | — | 1.1150 |
| profit_factor | — | 1.4949 | — | — | 1.2183 | — | 0.8150 |
| win_rate | — | 33.3% | — | — | 38.3% | — | 1.1489 |
| n_trades | 171 | **171** | **0** | 94 | **94** | **0** | 0.5497 |
| total_pnl | — | 78.1805 | — | — | 23.5506 | — | 0.3012 |
| monthly_calmar | — | 2.5246 | — | — | 0.6821 | — | 0.2702 |
| pbo | 0.1278 | **0.1278** | 0 | — | — | — | — |
| psr | 1.0000 | **1.0000** | 0 | — | — | — | — |
| dsr (legacy) | 0.0 | 0.0 | 0 | — | — | — | — |
| dsr_relative_b4 | — | **1.0000** | — | — | — | — | — |
| frac_positive_paths | 0.6444 | **0.6444** | **0** | — | — | — | — |
| n_trials | 1050 | 1050 | 0 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |

The IS monthly Sharpe is **+1.0894 exactly** — bit-identical to BASELINE_V3.md /059. This is the load-bearing re-validation result (see Section "IS Exact-Reproduction" below).

### Per-symbol section

| Symbol | IS wpnl | IS n_trades | IS win_rate | IS pct_of_total | OOS wpnl | OOS n_trades | OOS win_rate | OOS concentration_pct |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | +109.23 | 83 | 49.4% | 95.76% | +24.7502 | 34 | 41.2% | 105.09% |
| TRXUSDT | +3.95 | 79 | 34.2% | 3.47% | +4.9787 | 48 | 39.6% | 21.14% |
| LDOUSDT | +0.89 | 9 | 33.3% | 0.78% | −6.1783 | 12 | 25.0% | −26.23% |

---

## Classification per Brief Section 8 LOCKED

Section 8.1 defines CONFIRMED: ALL gates G.1-G.11 pass.

| Gate | Threshold | /081 result | Status |
|---|---|---|---|
| **G.1** IS monthly Sharpe within ±0.20 of +1.0894 | [+0.8894, +1.2894] | **+1.0894** | **PASS** |
| **G.2** OOS monthly Sharpe within ±0.20 of +0.5791 | [+0.3791, +0.7791] | **+0.5999** | **PASS** |
| **G.3** OOS/IS ratio ≥ 0.50 | ≥ 0.50 | **0.5507** | **PASS** |
| **G.4** frac_positive_paths ≥ 0.55 | ≥ 0.55 | **0.6444** | **PASS** |
| **G.5** PBO mean < 0.40 | < 0.40 | **0.1278** | **PASS** |
| **G.6** PSR > 0.95 | > 0.95 | **1.0000** | **PASS** |
| **G.7** OOS/IS ratio not SUSPICIOUS | ≤ 3.0 | **0.5507** | **PASS** |
| **G.8** vol-floor revert effective | `vol_scale_floor_per_symbol == {}` + assertion PASS | pre-flight PASS; IS roster bit-identical | **PASS** |
| **G.9** All v3 tests pass | full `uv run pytest` green | green (per setup commit `5d42c4a` run) | **PASS** |
| **G.10** ensemble_summary mode/size | `mode=confirmation`, `ensemble_size=10` | confirmed | **PASS** |
| **G.11** Anchor-byte gate | ITERATION_LABEL="v3-081"; floor={}; ATR=(2.0,1.0); 3 sym; OOS_CUTOFF/training_months immutable | all confirmed | **PASS** |

**All 11 gates PASS. CLASSIFICATION: CONFIRMED (Section 8.1).**

**BASELINE_V3.md UNCHANGED. /059 stays canonical at tag `v0.v3-059`. NO-MERGE (cycle 2 produced 0 PROMISING edge ingredients).**

Diary outcome label per Section 8.1: **CONFIRMATION-REVALIDATE** — the genuine /059 canonical config (post the /061-accretion revert) reproduced the /059 numbers within tolerance. By direct analogy to cycle 1's /070 NO-MERGE re-validation.

---

## IS Exact-Reproduction — the Load-Bearing Result

/081 IS monthly Sharpe = **+1.0894**, matching BASELINE_V3.md /059 to 4 decimal places. IS n_trades = 171 (identical to /059's 171 IS trades). Per-symbol IS breakdown is identical: BCH 83, TRX 79, LDO 9.

**IS trade roster is bit-identical between /059 and /081.** Verified by keying on `(symbol, open_time)` across all 171 IS trades:

- Keys added to /081: 0
- Keys removed from /081: 0
- `weight_factor` diffs: 0

This exact match has two implications:

1. **Reverting the /061 vol-floor restored the genuine /059 config.** The /061 floor had raised TRX `weight_factor` on 13 IS TRX trades from their natural vol-scaled values to the `0.5` floor. After the revert, all 79 IS TRX trades have the same `weight_factor` values as they did in /059. The IS roster is byte-identical, confirming the revert wiring is correct and complete (Gate G.8 PASS).

2. **No other code accretion since /059 perturbed the IS strategy path.** The T1 audit in the brief confirmed HEAD == /059 on all other behavior-affecting knobs (ATR multipliers, symbol universe, labeling params, inference threshold, CPCV gap). The bit-identical IS roster is the run-time confirmation of that audit: the IS window is fixed at `[data-start, 2025-03-24)`, so any config drift would have shown up as a Sharpe or trade-count deviation. None exists.

**Corollary**: /081 is the first CONFIRMATION-class run since /059 itself to measure the true /059 canonical config. Cycle 1's /070 CONFIRMATION ran with the /061 floor active (brief T2, row 8: `git show aab9347:run_baseline_v3.py` carries the floor) and therefore did not measure the genuine /059 config. /081 closes that measurement gap.

---

## OOS Delta +0.0208 — Root-Cause: Data-Extent Artifact

/081 OOS monthly Sharpe = +0.5999 vs /059's +0.5791 (Δ +0.0208). The OOS window `[2025-03-24, data-end)` extends monotonically with calendar time. /081 ran on 2026-05-15 klines; /059 ran earlier.

**The OOS Δ +0.0208 is driven by exactly one trade with changed exit.**

OOS trade roster comparison (/059 vs /081):
- Keys added: 0
- Keys removed: 0
- `weight_factor` diffs: 0
- `net_pnl_pct` diffs: **1** (the sole data-extent-affected trade)

| Field | /059 value | /081 value |
|---|---|---|
| symbol | TRXUSDT | TRXUSDT |
| open_time | 1778572799999 (2026-05-12 07:59:59 UTC) | same |
| weight_factor | 0.5000 | 0.5000 (bit-identical) |
| exit_reason | **end_of_data** | **take_profit** |
| close_time | 1778659199999 (2026-05-13 07:59:59 UTC) | 1778774399999 (2026-05-14 15:59:59 UTC) |
| net_pnl_pct | +0.1035% | +1.7330% |
| weighted_pnl | +0.0517 | +0.8665 |

The same TRXUSDT position that closed `end_of_data` in /059 (at /059's data extent boundary) resolved at take_profit in /081 (1.5 additional candles of OOS data). The wpnl lift is +0.8148. This is the identical mechanism the /077-/080 Critics certified benign — a monotonic calendar effect, not a config drift. The OOS trade roster has zero added/removed keys and zero weight_factor diffs; the only change is this one trade's outcome resolving with more data.

The data-extent direction (TRXUSDT OOS) is consistent with the brief Section 4.1 pre-registration: "any OOS drift is expected in the POSITIVE direction" given more OOS data. The observed Δ +0.0208 is well within the ±0.20 reproduction band (G.2 PASS).

This OOS Δ does not trigger the SUSPICIOUS gate (G.7): ratio = 0.5507 << 3.0 threshold, and the OOS-DOMINANT sub-mode requires IS shift < 0 — IS shift is exactly 0.0000.

---

## Full Gate Readout

### Re-validation gates (Section 8.1)

All 11 gates documented in the Classification section above. Summary: all PASS.

### Aspirational MERGE gates — informational only (/081 is NO-MERGE)

/081 is classified NO-MERGE because cycle 2 produced 0 PROMISING edge ingredients — NOT because of gate failures. For the record, assessing /059 as re-validated against aspirational MERGE thresholds:

| Aspirational gate | Threshold | /081 value | Clears? |
|---|---|---|---|
| IS monthly Sharpe ≥ +1.0 | +1.0 | +1.0894 | YES |
| OOS monthly Sharpe ≥ +1.0 | +1.0 | +0.5999 | NO — structural OOS weakness |
| OOS trades ≥ 130 | ≥ 130 | 94 | NO — 3-symbol universe constraint |
| PBO < 0.40 | < 0.40 | 0.1278 | YES |
| PSR > 0.95 | > 0.95 | 1.0000 | YES |
| DSR_relative_B4 > 0.95 | > 0.95 | 1.0000 | YES |
| frac_positive_paths ≥ 0.55 | ≥ 0.55 | 0.6444 | YES |
| top-symbol OOS ≤ 30% | ≤ 30% | BCH 131.5% | NO — BCH OOS concentration |
| Legacy DSR > 0.0 | > 0.0 | 0.0 | NO — known structural artifact at v3 trade volume |

The aspirational shortfalls (OOS Sharpe < +1.0, OOS trade count < 130, BCH OOS concentration, legacy DSR = 0.0) are standing constraints carried into cycle 3. They do not affect the CONFIRMED classification — /059 is re-validated, not a new merge candidate.

### CPCV paths

45 CPCV paths, 29 positive (frac_positive_paths = 0.6444). Sharpe q25 = −0.2430, median = 0.3351, q75 = 0.8378. Same as the /059 / /077 / /080 anchor (architecture-invariant metric on a bit-identical IS roster). Gate G.4 PASS.

---

## IS Trade-Roster Bit-Identity — the vol-floor revert effectiveness check (Gate G.8)

The vol-floor revert (`vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` → `{}`) was expected to un-floor 13 IS TRX `weight_factor` values per the brief Section 4.3 behavioral-effect predictor.

**Observed result: IS roster bit-identical between /059 (the genuine no-floor config) and /081 (post-revert).** This means the revert is fully effective — the IS TRX `weight_factor` values in /081 match /059's values exactly on all 79 IS TRX trades, including the 13 trades previously floored at 0.5 by the /061 accretion.

The brief also stated BCH and LDO `weight_factor` values should be mathematically invariant to the revert (the floor dict was TRX-only). Confirmed: 0 weight_factor diffs on the 83 BCH IS trades and 0 on the 9 LDO IS trades.

The runner pre-flight assertion (`expected_floor_dict = {}`) passed at startup, providing an early-detection guard that the revert wiring is correct.

---

## Per-Symbol Notes

**BCH**: IS wpnl +109.23 / 83 trades / 49.4% WR / 95.76% of IS total pnl. OOS +24.75 / 34 trades / 41.2% WR. BCH is the structural carrier — 95.76% IS pnl concentration and 131.5% OOS concentration (after netting LDO's drag). This is the standing fragility constraint carried into cycle 3.

**LDO**: IS wpnl +0.89 / 9 trades / 33.3% WR (near-negligible IS contribution). OOS −6.18 / 12 trades / 25.0% WR. LDO is the standing drag symbol — a structural weakness across all of cycles 1 and 2. Confirmed as an unresolved cycle-3 constraint. LDO OOS WR at 25.0% is well below the 50% random baseline for a triple-barrier classifier.

**TRX**: IS wpnl +3.95 / 79 trades / 34.2% WR. OOS +4.98 / 48 trades / 39.6% WR. TRX is the volume carrier (48 OOS trades vs BCH's 34) but contributes modestly to pnl. The vol-floor revert moves TRX back to the genuine /059 posture — no observable IS delta (bit-identical IS roster).

LDO remains the primary standing constraint for cycle 3 axis selection.

---

## Label Leakage Audit

- `REQUIRED_GAP = 66 = (21+1) × 3 symbols` — confirmed unchanged.
- Walk-forward embargo = 22 candles (`compute_embargo_candles(10080, 480) = 22`); `train_end_ms = test_start_ms − embargo_ms`; fixed in this worktree at commit `e149e9d` (iter-v3/058 RE-ANCHOR). The lookahead-bias bug per `feedback_v3_walkforward_lookahead_bug.md` is NOT live in this worktree.
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` — universal ATR multipliers (2.0, 1.0) for all 3 symbols.
- No new feature column; no new data dependency introduced at /081. Feature `confidence` column is sourced from past-only `predict_proba` — look-ahead clean by construction.

---

## Gate Efficacy Table

All risk gates unchanged from /059. No gate was modified at /081.

| Primitive | State | Note |
|---|---|---|
| 1 — Feature OOD z > 2.0 | ON | unchanged from /059 |
| 2 — Hurst regime | ON | unchanged from /059 |
| 3 — ADX gate (global 20.0) | ON | unchanged from /059 |
| 4 — Low-vol filter | ON | unchanged from /059 |
| 5 — Vol-adjusted sizing (RiskV2; floor 0.3, ceiling 1.0) | ON | **TRX floor restored to global 0.3 (revert of /061 0.5 floor)** |
| 6 — BTC trend kill (±15%, 14d) | ON | unchanged from /059 |
| 7 — Per-symbol PnL cap | OFF | `enable_per_symbol_cap=False` |
| 9 — Regime kill switch (primitive 9) | OFF | reverted at /075 |
| 11 — Drawdown brake (primitive 11) | OFF | CLOSED at /054 |
| 12 — BTC-trend SIZE de-rate (primitive 12) | OFF | reverted at /076 |
| 13 — Conviction-derate (primitive 13) | OFF | reverted at /080 |

The Sub-fix 1 revert (primitive 5) removes the TRX-specific `0.5` vol-scale floor, restoring TRX to the same global `0.3` floor as BCH and LDO — the calibrated /059 risk posture.

---

## Seed Concentration Audit (CONFIRMATION mode — 10 seeds)

`ensemble_summary.json` confirms mode=confirmation, ensemble_size=10, 5 seeds outer=42 lineage + 5 seeds outer=123 lineage. Total 1050 trials (35 × 3 sym × 10 seeds).

PBO = 0.1278, frac_positive_paths = 0.6444 — identical to the /059 / /077 / /080 anchor. These are architecture-invariant metrics on a bit-identical IS roster; their invariance confirms the roster is genuinely identical across modes.

BCH IS pct_of_total = 95.76% — the standing single-symbol concentration constraint. No change from /059.

---

## Anomaly Notes

1. **10-trade OOS spot-check — 0 pnl math errors.** Verified `pnl_pct` formula (`direction=1`: `(exit-entry)/entry×100`; `direction=-1`: `(entry-exit)/entry×100`), `net_pnl_pct = pnl_pct - fee_pct`, `weighted_pnl = net_pnl_pct × weight_factor` (units: the stored `weighted_pnl` is `net_pnl_pct × wf`, NOT `net_pnl_pct × wf / 100` — pct units preserved throughout). All 10 sampled trades pass. Exit reasons (take_profit, stop_loss, timeout, end_of_data) are self-consistent. No weight_factor = 0 on wf-carrying trades (one BCH trade has wf=0.0000 per the BTC-contagion gate firing correctly — wf=0 is the intended outcome of that gate; net_pnl_pct × 0 = 0 weighted_pnl, consistent).

2. **IS Sharpe = +1.0894 exactly.** Bit-identical to BASELINE_V3.md /059. IS trade-roster bit-identity confirmed against /059 on all 171 IS trades (0 added, 0 removed, 0 weight_factor diffs). The vol-floor revert is confirmed effective.

3. **OOS Δ +0.0208 is a pure data-extent artifact.** Exactly one TRXUSDT OOS trade (open_time=1778572799999, 2026-05-12 07:59:59 UTC) changed from `end_of_data` at close_time=2026-05-13 07:59:59 UTC (in /059) to `take_profit` at close_time=2026-05-14 15:59:59 UTC (in /081) — 1.5 additional OOS candles resolved the position at TP. wpnl delta = +0.8148. All other 93 OOS trades: 0 key diffs, 0 wf diffs. The OOS Δ is benign and identical in mechanism to the /077-/080 data-extent artifacts certified by the Critics.

4. **PBO, frac_positive_paths, PSR, dsr_relative_B4 all invariant.** PBO = 0.1278 (unchanged from /059 / /077 / /080 — per-cell architecture-invariant metric). frac_positive_paths = 0.6444 (29/45 CPCV paths positive — unchanged). PSR = 1.0000, DSR_relative_B4 = 1.0000 (both at n_trials=1050 saturation floor). Legacy DSR = 0.0 — the known structural artifact at v3 trade volume (~94 OOS trades produces insufficient monthly frequency for the legacy DSR formula); consistent with all prior v3 iterations.

5. **No NaN Sharpe, no zero-trade IS months, no zero-trade OOS months.** IS monthly_pnl: 36 rows, all non-zero trade_count. OOS monthly_pnl: 14 rows, all non-zero trade_count. No NaN in comparison.csv.

6. **`ensemble_summary.json` mode=confirmation, ensemble_size=10.** Gate G.10 PASS. The run used the unified 10-seed architecture — NOT the 3-seed EXPLORATION subset.

---

## BASELINE_V3.md Status

Per brief Section 8.5 (applies regardless of outcome):

- **`vol_scale_floor_per_symbol` code config note**: `BASELINE_V3.md` "Code Configuration" must be updated to record that `vol_scale_floor_per_symbol={}` is the genuine /059 value, and that the iter-v3/061 accretion was reverted at /081. This is a permanent measurement-integrity correction.
- **Measurement Discipline section**: must record the /081 re-validation result (CONFIRMED) and the data-extent OOS Δ +0.0208 with its one-trade root-cause.
- **Baseline numbers**: UNCHANGED — /059 canonical at tag `v0.v3-059`.

These BASELINE_V3.md edits are the QR's responsibility at Phase 8 diary.

---

## Status

OVERALL = READY-FOR-CRITIC

**Classification: CONFIRMED (re-validation) — BASELINE_V3.md UNCHANGED, /059 stays canonical. NO-MERGE.**

The /081 cycle-2 CONFIRMATION re-validated the genuine /059 canonical config (after reverting the illegitimate iter-v3/061 vol-floor accretion that had persisted 19 iterations). IS monthly Sharpe reproduced at exactly +1.0894 (0.0000 delta) with a bit-identical 171-trade IS roster. OOS monthly Sharpe measured at +0.5999 (delta +0.0208 — a pure data-extent artifact from one TRXUSDT `end_of_data → take_profit` trade resolution). All 11 pre-registered gates PASS.

Cycle 2 (iter-v3/071-/080) produced 0 clean PROMISING edge ingredients. /081 carries no edge. The NO-MERGE determination is driven by cycle-2 outcome, not gate failure.

Standing constraints carried into cycle 3: (a) LDO directional weakness (OOS WR 25.0%, structural drag across cycles 1-2); (b) BCH ~96% IS-pnl concentration fragility; (c) OOS Sharpe +0.60 below the aspirational +1.0 floor.

---

Phase 6 complete. Engineering report committed at `75248b3`. Phase 7.5 Critic review required before Phase 7. Orchestrator: invoke `quant-critic` with branch=`iteration-v3/081`, report_dir=`reports-v3/iteration_v3-081`, brief_dir=`briefs-v3/iteration_v3-081`.
