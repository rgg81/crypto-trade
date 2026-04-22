# Iteration 186 — Implement R3 OOD gate in the backtest

**Date**: 2026-04-22
**Type**: EXPLOITATION (code implementation of iter-185's finding)
**Baseline**: v0.176

## Section 0 — Data Split (non-negotiable)

- OOS cutoff: 2025-03-24 (fixed).
- Walk-forward trains each month on 24 months of past data. OOD mean/cov is
  computed from the training window only. The prediction-time distance is
  computed against that training window's mean/cov.
- Cutoff `ood_cutoff_pct=0.70` was chosen in iter-185 based on IS-only
  quintile analysis; iter 186 reuses that value without re-tuning on OOS.

## Phase 1-4 — Reuse iter 185 research

Iter 185 already did the EDA, labeling, symbol-universe, filtering, and
risk-mitigation design phases. This iteration is purely the engineering
follow-through: take that validated design and put it into production code.

Quick recap of the evidence (from `briefs/iteration_185/research_brief.md`):

| cutoff | IS Sharpe | OOS Sharpe |
|-------:|----------:|-----------:|
| 1.00 (baseline v0.176) | +1.338 | +1.414 |
| 0.70 (IS-picked)       | +1.284 | +2.299 |

The IS Sharpe drops by 0.054 while OOS Sharpe gains 0.885. Both stay above
the 1.0 merge floor.

## Implementation

### `LightGbmStrategy.__init__` — new parameters

```python
ood_enabled: bool = False
ood_features: list[str] | None = None
ood_cutoff_pct: float = 0.70
```

`ood_features` must be a non-empty list when `ood_enabled=True` — validated in
`__init__`.

### `_train_for_month` — training-window stats

After the month's model is trained, compute:

1. `train_ood`: the OOD feature subset from `train_feat_df`, NaN-filtered
   (rows with inf/NaN in any OOD feature are dropped).
2. `self._ood_mean = train_ood.mean(axis=0)`
3. `cov = np.cov(train_ood.T) + ridge * I` where `ridge = 1e-6 * tr(cov) / k`
   stabilizes pinv against near-collinear features (lag-correlated returns).
4. `self._ood_inv_cov = np.linalg.pinv(cov + ridge)`
5. `distances = einsum("ij,jk,ik->i", centered, inv_cov, centered)` for every
   training row.
6. `self._ood_cutoff = np.quantile(distances, ood_cutoff_pct)`
7. Batch-load `OOD_FEATURES` for the test month into
   `self._month_ood_features` (same pattern as `self._month_features`).

If the cov inversion fails (singular), R3 is disabled for that month with a
warning and trading continues.

### `get_signal` — gate

After confidence threshold check, before NATR regime filter:

```python
if self.ood_enabled and self._ood_cutoff is not None:
    ood_row = self._month_ood_features.get(key)
    if ood_row is not None and np.isfinite(ood_row).all():
        diff = ood_row - self._ood_mean
        dist = diff @ self._ood_inv_cov @ diff
        if dist > self._ood_cutoff:
            return NO_SIGNAL
```

## Feature set

Same 16 features as iter 185 (scale-invariant subset of BASELINE_FEATURE_COLUMNS):

```python
OOD_FEATURES = [
    "stat_return_1", "stat_return_2", "stat_return_5", "stat_return_10",
    "mr_rsi_extreme_7", "mr_rsi_extreme_14", "mr_rsi_extreme_21",
    "mr_bb_pctb_10", "mr_bb_pctb_20",
    "mom_stoch_k_5", "mom_stoch_k_9",
    "vol_atr_5", "vol_atr_7",
    "vol_bb_bandwidth_10",
    "vol_volume_pctchg_5", "vol_volume_pctchg_10",
]
```

## Test coverage

`tests/test_lgbm.py::TestR3OodDetector`:
- `test_requires_ood_features` — `ValueError` when `ood_enabled=True` without features
- `test_disabled_by_default` — `ood_enabled=False` leaves state slots None
- `test_ood_state_exposed` — enabled strategy carries the expected state shape
- `test_mahalanobis_math` — near-mean point within cutoff, 5σ point outside

## Decision rules

- **MERGE** iff full-portfolio backtest shows:
  - IS Sharpe ≥ 1.0
  - OOS Sharpe ≥ 1.0
  - OOS Sharpe meaningfully exceeds baseline +1.414 (target ≥ +1.8)
  - OOS MaxDD ≤ v0.176's 27.20% +1% tolerance
- **NO-MERGE** if the actual backtest undershoots the post-hoc simulation
  by a big margin (e.g. OOS Sharpe < 1.5), meaning the simulation missed
  something about how R3 interacts with vol-targeting or R1/R2.

## Commit plan

- `feat(iter-186): R3 OOD Mahalanobis gate in LightGbmStrategy` (code+tests)
- `fix(iter-186): NaN handling and ridge regularization for R3 cov` (robustness)
- `feat(iter-186): v0.186 baseline runner with R3 enabled` (runner)
- `docs(iter-186): research brief` (this doc)
- `docs(iter-186): engineering report` (after backtest)
- `docs(iter-186): diary entry` (final)
