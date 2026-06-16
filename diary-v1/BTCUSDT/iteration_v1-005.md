# Diary — iter-v1/005 (BTCUSDT) — EXPLORATION

**Axis:** orthogonal NON-OHLCV feature — `btc_funding_spread_30_90` (funding term-structure
slope, z30−z90) added to the 41-col prune (`V1_BTC_PRUNED_ITER002`). R2 OFF. K=5 screen,
n_trials=35, slippage 2 bps/side, honest costs. First probe of the FE's orthogonal batch
attacking BTC's thin price-only edge.

**Result (vs iter-004 prune-only K=20 IS −0.17 / OOS +0.48; iter-001 baseline IS −0.28 / OOS +0.64):**
IS Sharpe **−0.4322** / OOS **+0.8521**, OOS/IS ratio **−1.97 (INVERSION)**, dispersion **40.05**,
194/83 trades, IS net −18.37, OOS net +12.13. Clean run, 0 seed failures, R5/vt fired 0%.

**Verdict: NEGATIVE on the generalization-coherence gate.**
- The funding feature produced an **inverted profile** (negative IS, positive OOS, ratio −1.97) —
  the SAME structural artifact as the iter-001 baseline (IS −0.28 / OOS +0.64) that the user
  directed us NOT to reward. The headline OOS +0.85 is the largest OOS seen on BTC, but it rides
  on a *worse* IS than prune-only (−0.43 vs −0.17 at K=20). Adding the funding feature pushed IS
  further negative, not positive.
- Funding IS-IC was 0.105 (orthogonal, monotone forward-return buckets per FE), but that linear
  signal did NOT translate into IS Sharpe lift inside the LightGBM specialist — the opposite.

**Verifiability note (process, not result):** my first read flagged a "silent column drop" because
the funding feature is absent from `feature_importance_Model_A_BTCUSDT_specialist.csv`. That was a
MISREAD — the per-run importance CSV is keyed on the canonical 193-col `V1_FEATURE_COLUMNS`, which
does not contain `btc_funding_spread_30_90` (the feature lives only in `V1_FEATURE_COLUMNS_PRUNED`
+ the runner override). I confirmed the feature was genuinely trained on:
- override banner: `features=42 (41-col prune + orthogonal ['btc_funding_spread_30_90'])`
- parquet `data/features/BTCUSDT_8h_features.parquet` HAS the column (235 cols)
- coverage: 5575/5727 IS non-null (97%), 1346/1346 OOS (100%), std 0.92, first non-null 2020-01-31
- the `available_feat_cols` filter keeps any column present in the parquet → kept.
→ iter-005 is a VALID funding test. The 41-non-zero importance count was the 41 prune cols that
*are* in the 193-list; the 42nd (funding) is real but unlisted. **Follow-up (task #130):** wire the
importance writer to `active_feature_columns` for orthogonal-override branches so future screens
are auditable on importance rank, not just headline.

**Confound (flagged, not fatal):** iter-005 is K=5; the cleanest prune-only anchor is iter-004
K=20. No K=5 prune-only control exists. The prune-only IS trend is K-monotonic (K=3 +0.17 →
K=20 −0.17), so K=5 prune-only would sit ≈0; funding dragged it to −0.43, a ~0.4 IS degradation
attributable to the feature beyond the K effect. Either reading lands NEGATIVE on coherence.

**Lessons**
- A high univariate IS-IC (0.105) on an orthogonal family does not survive inside the bagged
  specialist — the tree allocates around it and IS coherence degrades. Importance-rank visibility
  (task #130) is needed to distinguish "learned-but-harmful" from "ignored."
- Inverted profiles keep recurring on BTC (baseline, funding). BTC's edge is genuinely thin; single
  orthogonal swaps are not flipping it coherent.

**Next:** iter-v1/006 — hand the FULL orthogonal family space to the Feature Engineer for IS-only
selection (IC + redundancy-vs-prune + cluster importance) and let FE recommend the next screen
(single feature or a small orthogonal cluster), rather than mechanically swapping one feature at a
time. Honors the "invest in feature engineering" mandate. Conserve the K=20 confirmation for the
best candidate after the batch; ping user before any confirmation.
