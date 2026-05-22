# Phase 7.5 Critic Review — iter-v3/009 — PRELIMINARY

**Iteration Type**: EXPLORATION (catalog row #2 since last CONFIRMATION)
**Mode**: Round 1 — Preliminary findings, NO OVERALL verdict
**Code SHA**: `43b3ed8` | Brief SHA: `96ec4d5` | Phase 5.5 Gate SHA: `7b72845`

---

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

No new feature code in this iteration. Per the engineering report and brief Section 3.7, iter-v3/009 introduces ZERO new features and ZERO modifications to feature computation. The active 13-feature set inherits from iter-v3/007/008 audit lineage; `vwap_dev_50` was DROPPED (not added), so look-ahead audit reduces to verifying the 13 retained features (all previously cleared in iter-v3/006/007 reviews). The labeling (triple-barrier with past-only ATR), purge gap (88 = (21+1)×4), and walk-forward boundary (`OOS_CUTOFF_MS = 1742774400000`) are byte-for-byte unchanged. No leak vector introduced.

### Check 2 — Embargo Width: PASS

Required gap = (timeout_candles + 1) × n_symbols = (21+1) × 4 = 88. Engineering report quotes the runtime banner: `Label-leakage gap: (timeout_candles=21+1) * n_symbols=4 = 88 [matches REQUIRED_GAP=88] PASS`. Inner CV gap = 22 rows (184h). Source-verified at `run_baseline_v3.py:212` (`required_gap = (timeout_candles + 1) * n_symbols`). PASS.

### Check 3 — Multiple-Testing Correction: METHODOLOGY-PASS / EDGE-INFORMATIONAL

Per TYPE=EXPLORATION: methodology axis (PBO + n_eff) enforced; edge axis (DSR/PSR) is informational only.
- **PBO (per-cell mean) = 0.1145** — well below the 0.40 threshold. iter-v3/007's PBO was 0.1419. PBO improved by ~0.027.
- **n_eff (per-cell median) = 7** — sensible; not pathologically low.
- **n_trials = 40** (10 trials × 4 symbols, single-seed exploration). Matches budget.
- **DSR = 0.0** and **PSR = 1.0** — these are the iter-v3/004-007 well-documented exploration-mode artifact (DSR collapsed at single-seed; PSR saturated). EDGE axis is INFORMATIONAL per cadence rule and Section 8 of brief; not BLOCK-triggering.

Methodology axis: PASS.

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` confirms 13×13 matrix, max off-diagonal `|IC| = 0.6602` (`max_dd_window_50` × `range_realized_vol_50`, negative rho), 0 pairs at or above the 0.70 threshold. Highest cross-family ICs are all below 0.55 (`ema_spread_atr_20` × `vwap_dev_20` = 0.547, `ema_spread_atr_20` × `btc_ret_14d` = 0.508). The IC-redundancy reduction promised by iter-v3/008's setup commit is empirically delivered. No new families added to scrutinize.

### Check 5 — ADF Stationarity: WARN (carry-forward, no regression)

ADF totals: 2278 stationary / 491 non-stationary out of 2769 rows = 17.7% non-stationary. This is the well-documented per-month low-T artifact (60-bar windows + early IS months with sparse coverage); spot-checking 2020-04 BCHUSDT shows `hurst_diff_100_50`, `ret_kurt_50`, and `hurst_100` clearing p < 0.05 in a typical mature month. The non-stationary fraction has not regressed from iter-v3/007 baseline (same 13 features minus `vwap_dev_50`, so structurally must be ≤ iter-v3/007). The walk-forward retraining + ADF-as-monitoring (not gate) was waived in iter-v3/004 and stands; no NEW features introduced means no NEW ADF risk. WARN is carry-forward, not a regression.

### Check 6 — Pareto Dominance: WAIVED (single-seed exploration)

`pareto_front.csv` has exactly 1 row (seed=42). Per Section 8 criterion 9 of the brief and the cadence rule (`--seeds 1` for EXPLORATION), the 10-seed Pareto frontier comparison is structurally vacuous. WAIVED. Note for record: max_concentration = 98.61% (LDOUSDT-driven), informational only per Section 6.3.

### Check 7 — Reproducibility: PASS

- Code SHA stamped: `43b3ed8` in engineering report header.
- `ITERATION_LABEL = "v3-009"` confirmed at `run_baseline_v3.py:99`.
- `feature_columns` explicit via `V3_FEATURE_COLUMNS` (13-tuple, hardcoded literal at `features_v3/__init__.py:118-139`).
- `_verify_feature_columns()` at `run_baseline_v3.py:181-203` raises if `len != 13` OR `'vwap_dev_50' in V3_FEATURE_COLUMNS`. Belt-and-suspenders.
- Library versions stamped (lightgbm 4.6.0, numpy 2.2.6, etc.).

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 1: drop `vwap_dev_50`, expect IS Sharpe ≥ +0.20. Code change in iter-v3/009 is single-line `ITERATION_LABEL` cosmetic update (the feature drop landed in inherited SHA `56b8f8b`). `git show iteration-v3/009 -- run_baseline_v3.py` would show only the label change. Single-axis variation respected. Hypothesis is testable (numeric IS Sharpe band [+0.18, +0.28] pre-registered). Falsifier 1 pre-registered AT IS-axis (correctly did NOT make claims on OOS). The IS = +0.0802 fell BELOW Falsifier 1's +0.10 threshold — the falsifier is mechanically activated per the brief's own pre-registration. The OOS = +1.1223 result is NOT covered by any pre-registered falsifier in Section 4.3 (the brief's predictions assumed IS direction would translate to OOS). Whether to invoke Falsifier 1 mechanically (NEGATIVE) or override on OOS evidence (PROMISING) is a judgment call reserved for the QR (and is the substance of Clarification #1 below). No process-level FAIL; pure interpretation question.

### Check 9 — Symbol Exclusion Enforcement: PASS

`run_baseline_v3.py:151-158` (`_verify_symbols`) raises if `set(symbols) & set(V3_EXCLUDED_SYMBOLS)` is non-empty. Engineering report confirms `set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` verified at runtime.

### Check 10 — Feature Isolation Enforcement: PASS

`_verify_track_isolation()` at `run_baseline_v3.py:223-244` runs grep against `^from crypto_trade\.features ` and `^from crypto_trade\.features_v2` in `src/crypto_trade/features_v3/`. Engineering report confirms `Track isolation (features_v3 does not import v1/v2): PASS`.

### Check 11 — Forming-Candle Audit: PASS (no change)

Same data-staleness guard as iter-v3/007; data extent runs through 2026-04-30+ candle close (gates fire on full universe with 706+ rows in 2026-04 retrain month). No forming-candle issue identified.

### Check 12 — Library Version Pinning: PASS

Engineering report stamps versions: lightgbm 4.6.0, numpy 2.2.6, pandas 3.0.0, pyarrow 23.0.1, pytest 9.0.2, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6. Stack matches iter-v3/007. No new external deps per brief Section 9.

---

## Anomaly Scrutiny — IS/OOS Divergence

The headline IS/OOS divergence (IS Δ -0.144, OOS Δ +1.060, ratio ~14x) is the dominant interpretive question. The methodology axes (Checks 1-12) are all clean — no leakage path explains it. Per-symbol decomposition:

| Symbol | iter-v3/007 OOS PnL | iter-v3/009 OOS PnL | Δ | iter-v3/007 OOS WR | iter-v3/009 OOS WR |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | +8.15% | +3.16% | -4.99% | 47.2% | 43.2% |
| LDOUSDT | +17.72% | +85.51% | **+67.79%** | 44.4% | 75.0% |
| MKRUSDT | -6.49% | -13.09% | -6.60% | 33.3% | 30.8% |
| TRXUSDT | +3.92% | +5.97% | +2.05% | 41.7% | 44.0% |

The +1.060 OOS Sharpe lift is **almost entirely driven by LDOUSDT** (+67.79% of +89.42% portfolio PnL delta). LDO went from 18 trades / 44.4% WR to 12 trades / **75.0% WR** with average 7.13% per trade. iter-v3/007's worst symbol was MKR at -6.5%; iter-v3/009's worst is MKR at -13.1% (got WORSE). This pattern argues *against* a "vwap_dev_50 was overfit-friendly across the board" reading and *for* either (b) single-seed OOS noise OR (c) LDO-specific lottery effect. The 12-trade OOS LDO sample is N=12; statistical confidence on the WR jump 44%→75% is thin without bootstrap.

Falsifier 1 (IS < +0.10 → vwap_dev_50 had real IS signal) was PRE-REGISTERED before the OOS reveal and is mechanically activated by IS = +0.0802. The OOS direction does NOT logically retract the IS-axis falsifier — the brief's own framing was about whether `vwap_dev_50` had independent IS signal, and the answer to THAT question is "yes, on the IS axis." Whether the simultaneous OOS jump means something separate is a SECONDARY interpretation the brief did not pre-register.

PBO comparison: iter-v3/007 = 0.1419, iter-v3/009 = 0.1145 — slight improvement, methodology axis is not getting WORSE.

---

## Clarifications Requested from QR

### Clarification 1 — Falsifier 1 disposition

The brief's Section 4.3 Falsifier 1 mechanically activates: IS Sharpe = +0.0802 < +0.10 threshold → "vwap_dev_50 was actually contributing independent signal; revert top-14 hypothesis. Verdict: EXPLORATION-NEGATIVE on this axis." The OOS reveal contradicts the falsifier's *spirit* but not its *letter*. **How does the QR want the catalog row recorded — EXPLORATION-NEGATIVE (mechanical), EXPLORATION-PROMISING (OOS-overridden), or split (NEGATIVE-IS / PROMISING-OOS)?** The pre-registration discipline (project memory feedback "no cheating": never change measurement to escape bad outcomes) argues mechanical NEGATIVE; the cadence-discipline ledger value of capturing the OOS observation argues for PROMISING with disclosed override. This is a process question only the QR can answer.

### Clarification 2 — LDO concentration interpretation

LDOUSDT alone drives 104.87% of OOS PnL (12 trades, 75.0% WR, +85.51% net). MKRUSDT contributes -16.06%. The iter-v3/007 OOS pattern was BCH-dominated (84% concentration); iter-v3/009 is LDO-dominated (98.61% concentration). The dominant symbol changed but the concentration pattern did not. Two questions for the QR:
(a) Is the OOS metric improvement attributable to a robust 13-feature edge OR to a 12-trade LDO lottery? A bootstrap CI on the 12-trade LDO WR (75%, 95% CI ≈ [42.8%, 94.5%] under exact binomial) would clarify, but no such analysis is in the artifacts.
(b) Does "LDO drove OOS in iter-v3/009 just as BCH drove OOS in iter-v3/007" tell us anything more than "single-seed exploration runs are dominated by 1 symbol's lottery"?

### Clarification 3 — `_verify_feature_columns` source-of-truth drift

`run_baseline_v3.py:182-185` docstring still says `"iter-v3/008 brief Section 3.3"` and `"iter-v3/008 CONFIRMATION"`. iter-v3/009 is an EXPLORATION (per brief Section 0.5), not CONFIRMATION, and references iter-v3/008's brief, not iter-v3/009's. This is cosmetic but it's the second iteration with a stale docstring banner reference (iter-v3/007 had the same "feature-cols=34 PASS" banner drift caught by Critic Clarification 4). Should the next iteration's first commit fix this docstring to track the active brief, or is the lineage attribution to iter-v3/008 (whose setup commit `56b8f8b` actually made the change) the intended audit trail?

### Clarification 4 — Sample-size guardrail for OOS interpretation

Total OOS trades across 4 symbols = 87. LDO contributes 12 of those. The IS sample = 267. Trade-rate floor (project memory) is 130 OOS trades for merge-floor confidence. iter-v3/009 has 87 OOS trades (well below 130). On EXPLORATION this is informational, but as iter-v3/009 is the FIRST EXPLORATION row producing a "headline OOS lift," does the QR want to record a 130-trade-floor caveat in the catalog row to prevent future CONFIRMATION QRs from reading +1.12 OOS Sharpe as a robust signal worth bundling?
