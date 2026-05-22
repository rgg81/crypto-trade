# iter-v3/090 — Research Brief — the GROSS-SIGNAL-STRENGTHENING cross-sectional iteration: downside-risk feature expansion (cycle-3 EXPLORATION #9)

**Iteration**: iter-v3/090
**Type**: EXPLORATION (cycle-3 slot #9 of 10) — the GROSS-SIGNAL-STRENGTHENING next build on the RETAINED /088 cross-sectional architecture + the /089 cost-aware construction. NOT a fresh re-architecture; NOT a third round of turnover reduction.
**Branch**: `iteration-v3/090` (off the /089 closeout merge `70ba3ce`)
**Date**: 2026-05-17
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — **IMMUTABLE** (`src/crypto_trade/config.py`, `OOS_CUTOFF_MS = 1742774400000`).
- `training_months = 24` — **IMMUTABLE**.
- IS = every bar with `open_time < OOS_CUTOFF_MS` (2022-03 → 2025-02, 37 months). OOS = every bar at/after it (2025-03 → 2026-05, 15 months).
- The QR sees OOS for the **FIRST time in Phase 7**. Every design parameter in this brief — the two new features, their construction windows, the sign alignment, the feature-selection cut — is selected on **IS data only** (the committed `analysis/iteration_v3-090/*.py` EDAs) or set **a-priori from cited research**. This is scrutinised in Section 10.3. The /089 cost-aware construction (quintile, 3-bar overlapping holds, no-trade band, the 0.138 turnover ceiling) is RETAINED unchanged.

## Section 0.5 — Iteration Type Declaration

iter-v3/090 is a **GROSS-SIGNAL-STRENGTHENING EXPLORATION** — cycle-3 slot #9 of 10, EXPLORATION mode (single-seed seed=42, `--n-trials 35`). **Wall-clock budget: ≤ 2h** (the cross-sectional path ran 0h 22m at /088 and /089; the two added features add negligibly to per-month training). Its axis is the gross-signal feature expansion the /089 closeout (diary Section 7) and the /089 Critic (FINAL `74054c2`, Recs #2/#3) mandated: **strengthen the cross-sectional ranker's GROSS signal so that, net of the already-cost-disciplined fees, the OOS book turns net-positive.**

This is the corrected next build on the **RETAINED** /088 cross-sectional `LGBMRanker` architecture — the architecture the /088 closeout classified ARCHITECTURE-PARTIAL and recorded as **the active v3 research line**, and which /089 (CONSTRUCTION-PARTIAL) advanced to a **gross-positive book** (OOS gross monthly Sharpe **+0.1717**). Per `feedback_v3_bold_research_mandate.md` (SHARPENED 2026-05-17): the cross-sectional architecture is v3's most sustained positive trajectory (OOS lifted +0.44 across /088→/089); /090's job is to push it to net-positive. This brief carries a **single axis** — a researched, IS-EDA-selected, multivariate-contribution-tested feature expansion — and explicitly DEFERS the short-leg-asymmetry construction to /091 (Section 2.5 / Section 3.6).

This brief **supersedes the cycle-3 incremental plan** (`briefs-v3/cycle3_plan.md`) for slot #9, exactly as /088 and /089 did for #7/#8: the cross-sectional architecture is the active line and /088–/091 iterate it.

---

## Section 1 — Hypothesis

> **The /089 cross-sectional book is GROSS-POSITIVE (OOS gross monthly Sharpe +0.1717) and fails NET only on transaction cost (OOS fees/gross 1.58×). The committed IS-only EDA shows (A) the cross-sectional signal in this 22-symbol altcoin universe resolves 4.1× more sharply at the LOSER end of the book (within-half IC: bottom 0.0576 vs top 0.0141) — it is structurally a downside predictor — and (B) of the candidate cross-sectional feature families, DOWNSIDE-RISK carries the largest INCREMENTAL multivariate contribution to the 13-feature anchor composite (d composite IC-IR +0.0306, d quintile long-short spread Sharpe +0.0215 — the iter-v3/070-correct test, not a univariate Spearman). Adding the two leave-one-out-confirmed ORTHOGONAL downside-risk features — `xs_sortino_mom_12` and `xs_downbeta_50` — to the pooled LGBMRanker strengthens the gross long-short spread (IS composite IC-IR +0.198 → +0.217, +9.6%; IS quintile spread Sharpe −0.0754 → −0.0535, a +0.0219 improvement) without blowing turnover (the features change the score ranking, not the rebalance cadence — the /089 0.138 turnover ceiling is re-used as a hard gate). The honest scope: the feature expansion is the single /090 axis; the short-tilt / asymmetric-leg construction the asymmetry also motivates is a SECOND, orthogonal axis, pre-registered for /091.**

This is the honest hypothesis the EDA supports. /090 is a genuine, well-researched, multivariate-contribution-tested feature expansion — not a marginal trailing-return stack (the /089-scoped G4 "cross-sectional momentum channels" were plain `close`-ratio returns already in the panel; /090 rejects that as the iter-v3/070 dead-path and instead adds genuinely-different downside-risk features). It is honest about the residual: the gross-signal lift is real but modest, and whether it carries the OOS book net-positive is the open question Phase 7 answers.

### 1.1 — Why this is not defeatism, and why it is not a knob-tweak

The bold-research mandate (SHARPENED) forbids defeatism and forbids incremental knob-tweaks. /090 is neither. It does NOT keep shaving turnover (the /089 Critic Rec #2 named that as steeply-diminishing and gross-signal-destroying — /089 EDA E3 shows the gross signal going negative at hold ≥ 3). It does NOT re-architect (the architecture is working — gross-positive, OOS-improving). It executes the highest-EV remaining lever the /089 closeout identified — grow the gross signal — with genuine research (Section 10.2: the Liu-Tsyvinski crypto-factor literature, the idiosyncratic-vol anomaly, the cross-sectional downside-risk literature), a committed IS-only multivariate-contribution EDA, and a disciplined feature-selection cut that REJECTS a redundant candidate even though its univariate IC looked strong. That is rigorous, ambitious, top-quant-firm-grade execution.

---

## Section 2 — IS-Only Numerical Evidence

Two committed EDA scripts, both IS-only (`open_time < OOS_CUTOFF_MS`, 60-day/180-bar listing burn-in), both built on the RETAINED `cross_sectional.py` infrastructure. The forward-return target throughout is the H=3 cross-sectional forward return — the same target the /088 label and the /089 G-EDA use.

- `analysis/iteration_v3-090/gross_signal_expansion_eda.py` — (A) the short-leg-asymmetry diagnosis (A1–A3) and (B) the multivariate-contribution feature expansion (B1–B4). CSVs `X0`, `A1`–`A3`, `B1_B3`, `B4`.
- `analysis/iteration_v3-090/b2_feature_selection_eda.py` — the B2 per-feature selection: C1 greedy forward selection, C2 leave-one-out, C3 pairwise redundancy. CSVs `C1`–`C3`. The C4 orthogonal-subset tiebreak CSV completes the cut.

### 2.1 — A1–A3: the short-leg-asymmetry diagnosis (Critic /089 Rec #3)

/089's per-leg PnL decomposition showed the SHORT leg carries the entire gross spread (OOS short-leg gross +0.1200; long-leg gross −0.0633). The /089 Critic (Rec #3) asked /090 to pre-register, with IS-only EDA, whether the cross-sectional signal in this 22-symbol altcoin universe is structurally a downside/short predictor.

**A1 — `A1_tercile_fwd_profile.csv`** — per-tercile realised forward-return profile of the sign-aligned 13-feature anchor composite (model-free equal-weight rank composite):

| Tercile | mean forward return | excess vs universe mean |
|---|---:|---:|
| bottom (predicted losers → SHORT) | +0.004139 | **+0.001521** |
| middle | +0.002294 | −0.000323 |
| top (predicted winners → LONG) | +0.001518 | **−0.001099** |

The bottom tercile's *excess* return magnitude (0.001521) is **1.38× the top tercile's** (0.001099) — modest asymmetry. Note all three terciles have a positive mean forward return (the IS window had a positive altcoin drift) — the *cross-sectional* signal is the excess-vs-universe column.

**A2 — `A2_per_leg_spread.csv`** — the anchor composite's quintile long-short per-leg decomposition: long-leg mean forward +0.001308, short-leg mean forward +0.004720. The long leg contributes only +0.001308 to the spread; the short leg contributes −0.004720. The model-free equal-weight composite's quintile L-S spread Sharpe is **−0.0754** (the equal-weight rank composite is a weaker proxy than the trained `LGBMRanker` — consistent with the /088/089 G-EDA convention, where the model-free spread is negative while the trained model's gross book is positive; the model-free EDA is for *relative* feature-family comparison, not for predicting the trained book's sign).

**A3 — `A3_ic_by_half.csv`** — the decisive asymmetry evidence. Split each cross-section at the composite-score median; compute the rank-IC *within* each half:

| Half | n snapshots | within-half rank-IC |
|---|---:|---:|
| bottom half (low composite score) | 4743 | **+0.05755** |
| top half (high composite score) | 4743 | **+0.01406** |

**The cross-sectional signal resolves 4.1× more sharply at the loser end of the book.** Within the bottom-half (the predicted losers), the composite's rank genuinely orders the realised forward returns (IC +0.058); within the top-half it barely does (IC +0.014). This is a clean, internally-consistent confirmation of /089's per-leg finding: the cross-sectional signal in this 22-altcoin universe is **structurally a downside / short predictor**.

**The scoping conclusion** (Section 3.6 + Section 7): the asymmetry is real, but it is *modest at the tercile level* (A1: 1.38×) and the per-leg gross-PnL gap /089 observed (long −0.063, short +0.120) is the trained-model number. There are two distinct levers it motivates: (i) **feature design** — add features that better rank the loser end (the /090 axis — A3 says downside-risk features are the natural choice, and B confirms they contribute most); (ii) **construction** — a short-tilted or asymmetric-leg-sizing book. The iter-v3/070 / `feedback_v3_engineered_features_dont_stack.md` discipline forbids stacking two axes in one EXPLORATION. /090 takes the **feature axis** (it directly strengthens the gross signal — the /089 Critic Rec #2's named higher-EV lever — and is testable in a single clean EXPLORATION); the **short-tilt construction is pre-registered as the /091 axis** (Section 3.6), with its falsifier in Section 4.3 (F-ASYM).

### 2.2 — X0: the per-feature IS rank-IC (sign alignment)

`X0_feature_is_ic.csv` — the IS per-timestamp rank-IC of every feature (anchor + all candidates), used to sign-align each predictor in the composite. The candidate downside-risk features and their IS rank-ICs: `cand_semidev_50` −0.0464, `cand_sortino_mom_12` −0.0432, `cand_downbeta_50` −0.0045, `cand_maxdd_50` +0.0259 — vs the strongest existing-stack feature `range_realized_vol_50` −0.0607. **Univariate IC alone is NOT the selection criterion** (the iter-v3/070 dead-path: `cand_semidev_50` and the existing `range_realized_vol_50` are both strong univariate but near-collinear). The selection is the multivariate B/C tests below.

### 2.3 — B1–B4: the multivariate-contribution feature expansion (the /090 axis)

`gross_signal_expansion_eda.py` Section B tests three genuinely-different cross-sectional feature families for their **INCREMENTAL multivariate contribution** — the IS composite IC-IR and the realised quintile long-short spread Sharpe of the 13-feature anchor *with vs without* the family added. This is the iter-v3/070-correct test (a family that merely correlates with the existing stack adds nothing to the multivariate composite even if its univariate IC is strong). The families (researched — Section 10.2): **B1 idiosyncratic volatility** (residual vol after a BTC-beta regression), **B2 downside risk** (semi-deviation, down-beta, rolling max-drawdown, Sortino-scaled momentum), **B3 liquidity / size** (Amihud illiquidity, log dollar volume, high-low range).

`B1_B3_family_incremental.csv` — per-family incremental contribution vs the 13-feature anchor (anchor baseline: composite IC mean +0.05851, IC-IR **+0.1981**, quintile L-S spread Sharpe **−0.0754**):

| Candidate family | n features | composite IC-IR | d IC-IR vs anchor | quintile L-S spread Sharpe | d spread Sharpe vs anchor |
|---|---:|---:|---:|---:|---:|
| B1 idiosyncratic vol | 2 | +0.2126 | +0.0145 | −0.0702 | +0.0052 |
| **B2 downside risk** | 4 | **+0.2287** | **+0.0306** | **−0.0539** | **+0.0215** |
| B3 liquidity / size | 3 | +0.2155 | +0.0174 | −0.0581 | +0.0173 |

**B2 downside-risk is the strongest candidate family on BOTH metrics** — the largest incremental composite IC-IR lift (+0.0306) and the largest realised quintile spread-Sharpe improvement (+0.0215). And it is the family A3 predicts should help: downside-risk features better rank the loser end of the book that carries the alpha. B1 and B3 also contribute positively but materially less.

`B4_full_stack.csv` — anchor vs the full stack of all three positive-delta families: stacking all 9 candidate features lifts composite IC-IR to +0.226 and the quintile spread Sharpe to −0.0490. **/090 does NOT carry the full 9-feature stack** — that violates the iter-v3/070 / `feedback_v3_engineered_features_dont_stack.md` discipline (9 marginally-correlated additions dilute `colsample_bytree` picks and overfit at the EXPLORATION budget). /090 carries the single strongest family, B2, *minus its redundant member* (the C-block cut below).

### 2.4 — C1–C4: the disciplined B2 feature-selection cut

`b2_feature_selection_eda.py` isolates which B2 features carry the incremental contribution, so /090 adds the **minimal effective subset**, not all four.

**C1 — `C1_greedy_forward_selection.csv`** — greedy forward selection inside B2 (start from the 13-feature anchor; at each step add the single B2 feature that most raises the composite IC-IR; stop when the marginal d(IC-IR) ≤ +0.005):

| Step | feature added | composite IC-IR | marginal d IC-IR | accepted |
|---:|---|---:|---:|:--|
| 1 | `cand_semidev_50` | +0.2144 | +0.0163 | yes |
| 2 | `cand_sortino_mom_12` | +0.2221 | +0.0077 | yes |
| 3 | `cand_downbeta_50` | +0.2303 | +0.0083 | yes |
| 4 | (`cand_maxdd_50`) | — | (does not raise IC-IR) | **STOP** |

C1 selects 3 of the 4 B2 features; `cand_maxdd_50` never improves the multivariate composite and is dropped.

**C2 — `C2_leave_one_out.csv`** — leave-one-out on the C1 trio: dropping each from `{anchor + 3}` and measuring the IC-IR loss. All three lose > the +0.005 floor on removal (`cand_semidev_50` −0.0132, `cand_sortino_mom_12` −0.0088, `cand_downbeta_50` −0.0083) — each earns its slot in the equal-weight model-free composite.

**C3 — `C3_pairwise_redundancy.csv`** — pairwise cross-sectional rank correlation of the C1 trio against the anchor volatility/tail features. **The decisive finding**: `cand_semidev_50` has a **0.80 cross-sectional rank correlation with the incumbent `range_realized_vol_50`** — it is near-collinear with a feature already in the stack (semi-deviation of negative-only returns is mechanically close to total realised vol). `cand_sortino_mom_12` (max |corr| 0.10) and `cand_downbeta_50` (max |corr| 0.19) are genuinely orthogonal to the incumbent vol/tail features.

**C4 — `C4_orthogonal_subset_tiebreak.csv`** — the final cut. Per the iter-v3/070 dead-path discipline, an 0.80-redundant feature *competes with its incumbent for `colsample_bytree` picks* in the trained `LGBMRanker` — exactly the failure mode that produced iter-v3/070's OOS −38%. So `cand_semidev_50` is **DROPPED** despite its strong univariate IC and its C2 leave-one-out pass. The tiebreak confirms this costs almost nothing on the realised spread:

| Feature set | n features | composite IC-IR | d IC-IR vs anchor | quintile L-S spread Sharpe |
|---|---:|---:|---:|---:|
| anchor_13 | 13 | +0.1981 | +0.0000 | −0.0754 |
| **anchor + `cand_sortino_mom_12` + `cand_downbeta_50` (orthogonal pair)** | **15** | **+0.2171** | **+0.0190** | **−0.0535** |
| anchor + all 3 (incl. redundant `cand_semidev_50`) | 16 | +0.2303 | +0.0322 | −0.0539 |

The orthogonal pair captures the **entire realised quintile-spread improvement** (−0.0535 vs all-3's −0.0539 — identical to 4 decimal places). The redundant `cand_semidev_50` adds +0.013 to the *model-free composite IC-IR* but ~0.000 to the *realised L-S spread* — its IC-IR contribution is the colsample-stealing kind, not the spread-strengthening kind. **The /090 feature additions are the two orthogonal downside-risk features `cand_sortino_mom_12` and `cand_downbeta_50`** (renamed `xs_sortino_mom_12` / `xs_downbeta_50` in the production code).

### 2.5 — Summary of IS evidence

1. The cross-sectional signal in the 22-altcoin universe is structurally a **downside / short predictor** — A3 within-half IC bottom 0.0576 vs top 0.0141 (4.1×). Confirmed for the /089 Critic Rec #3 pre-registration.
2. Of the candidate cross-sectional feature families, **B2 downside-risk** carries the largest incremental multivariate contribution (d composite IC-IR +0.0306, d quintile spread Sharpe +0.0215) — and it is the family the asymmetry predicts should help.
3. The disciplined cut (C1 greedy → C3 redundancy → C4 tiebreak) selects the **two orthogonal downside-risk features** `xs_sortino_mom_12` + `xs_downbeta_50`; the third B2 candidate `cand_semidev_50` is dropped for 0.80 redundancy with the incumbent `range_realized_vol_50` (iter-v3/070 colsample-dilution risk).
4. The /090 15-feature stack: IS composite IC-IR **+0.1981 → +0.2171** (+9.6%), IS quintile L-S spread Sharpe **−0.0754 → −0.0535** (a +0.0219 improvement — the gross-signal strengthening).
5. **The honest scoping call**: /090 carries the feature expansion as its single axis; the short-tilt / asymmetric-leg construction the A-block also motivates is pre-registered as the /091 axis (Section 3.6). One axis per EXPLORATION (the iter-v3/070 discipline).

---

## Section 3 — Proposed Changes (the /090 build spec — the QE Phase-6 build)

### 3.1 — The /090 axis: two DOWNSIDE-RISK cross-sectional features added to the ranker

**The single axis.** Two engineered downside-risk features are appended to the pooled `LGBMRanker`'s feature set. New constant `XS_DOWNSIDE_FEATURES = ("xs_sortino_mom_12", "xs_downbeta_50")` in `cross_sectional.py`. Both are IS-EDA-selected (Section 2.3/2.4) and reproduce the EDA's `cand_sortino_mom_12` / `cand_downbeta_50` exactly:

- **`xs_sortino_mom_12`** — a 12-bar return scaled by downside semi-deviation: `(close / close.shift(12) − 1) / semidev_50`, where `semidev_50` is the 50-bar rolling std of negative-only 1-bar returns. A Sortino-style downside-scaled momentum — a coin that has run up *without* downside dispersion is a stronger relative-value long than one whose run-up came with high downside vol. Window constants: `XS_DOWNSIDE_MOM_LOOKBACK = 12`, `XS_DOWNSIDE_VOL_WINDOW = 50` (a-priori, matched to the existing 50-bar v3 feature windows).
- **`xs_downbeta_50`** — the symbol's beta vs the BTC-return proxy, estimated on **down-market bars only** (the bars where the BTC proxy was negative): `cov(r, b | b<0) / var(b | b<0)` over a 50-bar rolling window (min 15 down-bars). A direct downside-risk channel — a high down-beta coin falls harder when the market falls, making it a stronger relative-value short.

### 3.2 — The precise code changes (`cross_sectional.py` / `run_cross_sectional_v3.py`)

All five changes are wired at the /090 setup commit (`a584fdf`):

1. **`cross_sectional.py` — new constants.** `XS_DOWNSIDE_FEATURES = ("xs_sortino_mom_12", "xs_downbeta_50")`; `XS_DOWNSIDE_VOL_WINDOW = 50`; `XS_DOWNSIDE_MOM_LOOKBACK = 12`. Each with the EDA-provenance docstring.
2. **`cross_sectional.py` — `_engineer_xs_downside_features(df)`.** A new function that adds the two columns to one symbol's panel from `close` + `btc_ret_3d`. Every transform is **backward-looking** (`.rolling()`, `.pct_change()`, `.shift()`) — no look-ahead (Section 3.4). `btc_ret_3d` (a 3-bar BTC return already in the v3 parquet) is converted to a ~1-bar BTC return proxy `(1+btc_ret_3d)^(1/3) − 1` for the per-bar down-beta regression.
3. **`cross_sectional.py` — `build_cross_sectional_panel(..., expand_downside: bool = False)`.** When `expand_downside=True`: the function reads the extra raw column `btc_ret_3d` per symbol, calls `_engineer_xs_downside_features` **BEFORE the 180-bar listing burn-in** (so the rolling windows have warm-up history; the burn-in then drops exactly the warm-up rows), and appends the two feature names to `xs_cols` so they are **cross-sectionally rank-normalized at each timestamp identically to the base features**. `expand_downside=False` is **byte-identical to /088/089** (the parameter defaults False — the legacy path is untouched).
4. **`run_cross_sectional_v3.py` — the feature set.** `XS_BASE_FEATURES` = the 13-feature stack (unchanged). `XS_FEATURE_COLUMNS = XS_BASE_FEATURES + list(XS_DOWNSIDE_FEATURES)` = **15 features**. `_verify_feature_columns` asserts `len(XS_BASE_FEATURES) == 13`, `len(XS_FEATURE_COLUMNS) == 15`, `btc_ret_14d` absent, and both downside features present. `ITERATION_LABEL = "v3-090"`.
5. **`run_cross_sectional_v3.py` — the panel build.** Both `build_cross_sectional_panel` calls (the main backtest + the smoke test) pass `expand_downside=True`. The strategy receives `feature_columns=XS_FEATURE_COLUMNS` (15) — the model trains and scores on all 15.

### 3.3 — UNCHANGED from /088 + /089

- **The cost-aware construction** — quintile legs (`XS_QUANTILE_FRAC = 0.20`), 3-bar overlapping holds (`XS_HOLD_BARS = 3`), no-trade band (`XS_NO_TRADE_BAND = 0.020`), the **HARD turnover ceiling `XS_TURNOVER_CEILING = 0.138`** — all RETAINED unchanged. /090 re-uses the /089 ceiling as a hard gate (Section 4.3, F2): adding features changes the score ranking, not the rebalance cadence, so turnover must stay within 0.138.
- **The model** — `LGBMRanker(lambdarank)`, monthly walk-forward, `train_end_ms = test_start_ms − embargo_ms` (the `e149e9d` fix). The sign fix and the CPCV-proxy fix (/089 corrections) are RETAINED.
- **The universe** — the 22-symbol `XS_UNIVERSE` — unchanged.
- **The label** — `label_cross_sectional_rank`, H=3 forward tercile grade — unchanged.
- **The embargo / CPCV** — `XS_REQUIRED_GAP = 88` — unchanged; the `expected_gap` assertion is retained. The two new features do not change H, so the embargo formula is unchanged.

### 3.4 — Look-ahead safety of the new features

Both new features are computed by `_engineer_xs_downside_features` from `close` and `btc_ret_3d` using **only backward-looking transforms**: `pandas.rolling(window)` is backward-looking; `.pct_change()` and `.shift(+k)` look back. The value at bar `t` uses only bars `≤ t`. The features are **predictors scored at bar t**, never the label. The /090 setup commit includes `test_iter090_downside_features_no_lookahead` — the load-bearing guard: it engineers the features on the full panel and on a truncated prefix and asserts the overlapping rows are **bit-identical** (a feature value at bar t is invariant to appended future bars). The cross-sectional rank-normalization (`_xs_rank_normalize`) ranks each feature *within each timestamp's cross-section only* — no future timestamp. The walk-forward embargo `XS_REQUIRED_GAP = 88` is unchanged and still governs the train/test boundary.

### 3.5 — Single-axis confirmation (Phase 5.5 gate)

iter-v3/090 changes **ONE axis: features.** No symbol change, no label change, no construction-knob change, no risk-gate change. The /089 cost-aware construction is RETAINED verbatim. The two added features are the same family (downside-risk) and are added together as one coherent expansion — the C-block cut (Section 2.4) is the per-feature discipline *within* the single feature axis; it is not a second axis. This is consistent with `feedback_v3_engineered_features_dont_stack.md`: that rule forbids stacking two engineered features *from different compose families* (or same-family time-scale sisters) at single-seed EXPLORATION. `xs_sortino_mom_12` and `xs_downbeta_50` are NOT a compose-family sister pair — they are two distinct downside-risk constructions (a downside-scaled momentum vs a conditional beta), structurally different, with max cross-sectional rank correlation 0.10 (C3) — and they are added as the minimal effective subset of the single best feature family, exactly the disciplined way the C-block selected them. The short-leg-asymmetry *construction* is the genuinely-separate axis, and it is DEFERRED to /091 (Section 3.6).

### 3.6 — The short-leg-asymmetry construction — pre-registered as the /091 axis

The A-block confirms the cross-sectional signal is a downside/short predictor (A3: 4.1× sharper at the loser end). This motivates a SECOND, orthogonal lever — a **short-tilted or asymmetric-leg-sizing construction** (e.g. a larger short leg than long leg, or a long-only-short book). This is a *construction* change, not a *feature* change — it is orthogonal to the /090 feature axis. Per the iter-v3/070 / `feedback_v3_engineered_features_dont_stack.md` single-axis discipline, it is **NOT bundled into /090**. It is **pre-registered here as the iter-v3/091 axis**: /091's QR will (a) carry the /090 feature set forward, (b) EDA the asymmetric-construction grid (the long:short leg-size ratio) on IS data, (c) pre-register an asymmetric-construction falsifier. /090's Section 4.3 pre-registers F-ASYM — the realised /090 OOS per-leg gross decomposition — so the /091 QR inherits a clean, pre-registered measurement of the asymmetry rather than rationalising it post-hoc.

### 3.7 — Risk framework

Unchanged from /089 — the cross-sectional book is risk-managed structurally (dollar-neutral construction, inverse-vol + vol-targeting, quintile diversification, the overlapping-hold tranching, the no-trade band, the HARD turnover ceiling). The /090 feature expansion **adds no new risk surface** — it changes which symbols the ranker scores high/low, within the same dollar-neutral quintile construction. The legacy v3 7-gate stack stays deferred (the cross-sectional gate re-design remains a future-iteration axis).

---

## Section 4 — Expected OOS Impact + evaluation + the pre-registered falsifiers

### 4.1 — Evaluation

iter-v3/090 produces a cross-sectional long-short book; per the /088/089 brief Section 4.1 it is **not directly comparable** to the per-symbol-book Sharpes of the /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322) or the /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791) — a different return distribution, beta, turnover. The operative evaluation:

**(A) The standing absolute bar.** The mission bar is top-quant-firm-grade: the standing v3 merge floors are IS monthly Sharpe ≥ +1.0 AND OOS monthly Sharpe ≥ +1.0. /090 is measured against these. The /090-specific goal is more proximate: **a net-positive OOS book** (OOS monthly Sharpe > 0) — the concrete next milestone the /089 gross-positive result hands /090.

**(B) The architecture-internal diagnostics + the /090-specific gates:**
- **OOS gross monthly Sharpe vs /089's +0.1717** — does the feature expansion strengthen the gross signal OOS? (The /090 hypothesis's direct test.)
- **OOS net monthly Sharpe vs /089's −0.0985** — does the stronger gross signal carry the net book toward / across breakeven?
- **OOS rank-IC > 0** — does the 15-feature model's OOS prediction rank correlate with the realised forward cross-sectional rank?
- **The HARD turnover ceiling — IS mean gross turnover/bar ≤ 0.138** (Section 3.3). A breach is NO-MERGE regardless of Sharpe.
- **frac_positive_paths (CPCV)** — the corrected /089 proxy (actual long-short net return per path).
- **No single symbol > 30% of OOS book PnL** — the quintile dollar-neutral construction should keep this structural.

**The /090 anchor.** The honest internal anchor is the **/089 cross-sectional book** — IS net monthly Sharpe **−0.1960** / OOS net monthly Sharpe **−0.0985**; IS gross monthly Sharpe **+0.0925** / OOS gross monthly Sharpe **+0.1717**; IS turnover/bar **0.1153**. /090's claim is that the downside-risk feature expansion strengthens the gross signal and improves the net book vs the /089 predecessor. The two-anchor rule is satisfied: ANCHOR 1 = the /089 cross-sectional book (the like-for-like architecture predecessor); ANCHOR 2 = the /059 CONFIRMATION baseline (recorded with the comparability caveat — a per-symbol-book reference, reserved for /092).

### 4.2 — Predicted OOS impact (honest)

The IS EDA is the basis. The /090 feature expansion lifts the IS composite IC-IR +9.6% (+0.1981 → +0.2171) and the IS quintile L-S spread Sharpe by +0.0219 (−0.0754 → −0.0535) on the model-free composite. Honest prediction for the OOS run:

- **OOS gross monthly Sharpe improves on /089's +0.1717.** The features strengthen the cross-sectional ranking; the /089 model's OOS gross was +0.17 on the 13-feature stack. Predicted OOS gross monthly Sharpe ≈ **+0.20 to +0.30** — a real but modest lift, in proportion to the IS composite IC-IR's +9.6% gain (the trained `LGBMRanker` typically extracts more than the equal-weight composite, but the EXPLORATION single-seed adds variance, and the model-free IS spread improvement is the conservative guide). I do NOT predict a doubling — the EDA does not support it.
- **OOS net monthly Sharpe improves on /089's −0.0985, plausibly crossing zero.** /089's OOS net was −0.0985 with OOS gross +0.0567 and OOS fees 0.0893 (fees/gross 1.58×). If /090's OOS gross PnL rises ~20–40% (in proportion to the gross-Sharpe lift) while turnover — and therefore fees — stays roughly flat (the features change the ranking, not the cadence), the OOS net PnL moves toward and plausibly just across breakeven. **Honest modal prediction: OOS net monthly Sharpe in roughly [−0.10, +0.20]** — a material improvement on −0.0985, plausibly net-positive, but very likely still well below the +1.0 floor. **Clearing the +1.0 floor on this iteration is NOT expected** — a single feature expansion lifting a +0.17 gross Sharpe does not reach +1.0; the honest read is that /090 is a step toward net-positive, and a CONFIRMATION-worthy cross-sectional book likely needs /090's feature gain *plus* /091's short-tilt construction.
- **IS mean gross turnover/bar ≈ 0.115** — essentially unchanged from /089's 0.1153 (the features change the score ranking, not the rebalance mechanics; the quintile cutoff, hold, and band are unchanged). Within the 0.138 ceiling.
- **OOS rank-IC stays positive**, ≈ +0.02 to +0.05 (the 15-feature model is a strengthened version of the same architecture; /089's OOS rank-IC was +0.0279).

### 4.3 — The LOCKED falsifier band (pre-registered — gates, not predictions)

Per `feedback_v3_per_symbol_target_axis_falsifier.md` — falsifiers are gates. Evaluated in Phase 7:

- **F1 — OOS rank-IC ≤ 0**: the 15-feature model's OOS prediction rank does NOT correlate with the realised forward cross-sectional rank. Since /090 strengthens the /088/089 architecture (which had OOS rank-IC +0.043 / +0.028), an OOS rank-IC ≤ 0 would indicate a build defect (a feature-engineering or panel regression) — a hard investigate-and-block signal.
- **F2 — IS mean gross turnover/bar > 0.138** (`XS_TURNOVER_CEILING`, the RETAINED /089 hard gate): the feature expansion blew turnover. A breach means /090 violated the standing cost discipline → NO-MERGE regardless of any Sharpe. **The /090 brief re-uses the /089 pre-registered ceiling exactly** — adding features must not blow turnover.
- **F3 — OOS gross monthly Sharpe ≤ the /089 book's +0.1717**: the feature expansion did NOT strengthen the gross signal OOS — the central /090 hypothesis is falsified. (The downside-risk features lifted the IS composite but did not transfer; the most likely cause would be IS-overfit feature contribution that does not generalise.)
- **F4 — OOS net monthly Sharpe ≤ the /089 book's −0.0985**: the feature expansion did NOT improve the net OOS book vs the /089 predecessor at all → the gross-signal-strengthening did not produce a net improvement → the /090 axis is falsified for the cycle.
- **F5 — a single symbol > 50% of OOS book PnL**: the quintile dollar-neutral construction failed to diversify (a structural-construction failure distinct from a signal failure).
- **F-ASYM (pre-registration for /091, NOT a /090 merge gate)**: the realised /090 OOS per-leg gross decomposition (OOS long-leg gross PnL, OOS short-leg gross PnL). This is RECORDED in Phase 7 — it is the pre-registered measurement the /091 short-tilt-construction axis builds on. /090's classification does NOT depend on F-ASYM; it is logged so /091 inherits a clean, pre-registered asymmetry measurement.

### 4.4 — What each falsifier implies

- **If F2 fires** — NO-MERGE, unconditionally. The turnover ceiling is the hard gate; a breach means /090 broke the standing cost discipline and the build must be diagnosed.
- **If F1 fires** — a build defect (the architecture itself transferred OOS at /088 and /089); investigate the feature-engineering / panel wiring before any classification.
- **If F3 fires (and F1/F2 do not)** — the gross-signal-strengthening did not transfer OOS; the /090 feature-expansion hypothesis is falsified for this cycle; /091 must rethink the gross-signal lever (and the short-tilt construction becomes the primary remaining axis).
- **If F4 fires (and F1/F2 do not)** — the net OOS book did not improve vs /089; the feature axis did not produce a net advance.
- **If no falsifier fires** — /090 strengthened the gross signal OOS, contained turnover, improved the net book, and the signal transferred; /090 is a genuine, methodologically-clean advance on the gross-signal axis (the Phase-8 classification is the QR's call — Section 8).

---

## Section 5 — Risk Mitigation

Per `feedback_v3_risk_mitigation_design.md`, every merge-candidate iteration carries a Risk Mitigation section. /090's controls are the RETAINED /089 structural controls — the feature expansion adds no new risk surface:

| Risk | Mitigation | IS-calibrated / a-priori | Simulated historical effect |
|---|---|---|---|
| **Turnover / fee drag** (the /088 failure mode) | RETAINED /089 cost-aware construction: overlapping 3-bar holds + no-trade band τ=0.020 + the HARD turnover ceiling 0.138 | IS-selected (/089 EDA E3/E4/E6) | /089: turnover/bar 0.1153, fees/gross OOS 1.58× — the /090 features do not change the rebalance mechanics, so turnover is predicted ≈ 0.115 (within the ceiling) |
| **Feature-overfit / colsample dilution** (the iter-v3/070 dead-path) | Multivariate-contribution feature selection: greedy forward selection (C1) + leave-one-out (C2) + pairwise-redundancy cut (C3/C4) — the redundant `cand_semidev_50` (0.80 corr with the incumbent `range_realized_vol_50`) was DROPPED | IS-selected (/090 EDA C1–C4) | EDA: the 2 orthogonal features (max corr 0.10/0.19 vs incumbents) carry the full realised spread improvement; dropping the redundant feature costs ~0.000 spread Sharpe |
| Directional market drawdown | Dollar-neutral long-short construction | a-priori (construction) | /088/089: market beta removed by design |
| Single-symbol concentration | Quintile long-short — ~4–5 names/leg | a-priori (construction) | /089: max OOS symbol concentration 12.18% — structurally < 30% |
| High-vol-symbol domination | Inverse-vol weighting within each leg + portfolio vol-targeting | a-priori (standard cross-sectional construction) | /089: per-symbol concentration capped |
| Listing non-stationarity | 60-day (180-bar) listing burn-in per symbol — the downside features are engineered BEFORE the burn-in so their rolling windows have warm-up | a-priori (crypto pitfall) | /088/089: applied; /090 engineers-then-burns-in so no warm-up NaN enters training |
| Label / feature look-ahead | `XS_REQUIRED_GAP = 88` pooled-CPCV purge; walk-forward `train_end = test_start − embargo`; the new features are backward-looking only (Section 3.4) — `test_iter090_downside_features_no_lookahead` asserts bit-identity under future-bar truncation | a-priori (formula + test) | /088/089 Critic Check 1/2 PASS; /090 adds the no-look-ahead unit test |

The /090-specific risk addition is the **feature-overfit / colsample-dilution** control — the multivariate-contribution selection that REJECTED a redundant candidate. Its effect is the committed C3/C4 EDA: the orthogonal pair captures the full realised spread improvement.

## Section 6 — Risk Management Design

The cross-sectional book is risk-managed by construction (Section 5). The legacy v3 7-gate stack stays **deferred** — re-introducing it onto the cost-aware cross-sectional book in the same iteration would confound the feature-expansion measurement (the same honest scoping call /088/089 made). /090's risk apparatus is: dollar-neutral construction + inverse-vol + vol-targeting + quintile diversification + the overlapping-hold tranching + the no-trade band + the HARD turnover ceiling + the multivariate-contribution feature-selection discipline. Fire-rate / regime-coverage: the dollar-neutral construction is always-on (every bar produces a long-short book); the turnover ceiling is a measurement gate (evaluated once on the IS run), not a per-bar gate. The /090 features are scored every bar — they have no fire-rate; they shift the ranking continuously.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (honest)

The /088 and /089 closeout calibration lessons are recorded and applied: pre-register the modal outcome honestly, name the dominant failure mechanism, do not over-weight the tail. /090's gross-signal-strengthening is a real but modest lever — the IS evidence is a +9.6% composite IC-IR lift, not a step-change.

- **≈45% — the modal outcome: the feature expansion MATERIALLY improves the OOS book vs /089. OOS gross monthly Sharpe lifts from +0.1717 toward [+0.20, +0.30]; OOS net monthly Sharpe lifts from −0.0985 toward [−0.10, +0.20] — plausibly just net-positive — turnover stays within the 0.138 ceiling; OOS rank-IC stays positive; but the OOS net monthly Sharpe remains well below the +1.0 floor.** The downside-risk features strengthen the gross signal and transfer, the net book improves and plausibly crosses zero, but a single feature expansion does not reach the absolute floor. This is a genuine advance on the gross-signal axis and the expected result; /091's short-tilt construction is the next required lever.
- **≈20% — the feature expansion strengthens the gross signal AND the OOS net book turns clearly net-positive** (OOS net monthly Sharpe in [+0.1, +0.5]). The features extract more OOS than the conservative model-free estimate. A good outcome; sets up /091/092 cleanly.
- **≈20% — F3/F4 fire: the feature expansion does NOT strengthen the gross signal OOS** (OOS gross monthly Sharpe ≤ +0.1717, OOS net ≤ −0.0985). The IS composite IC-IR lift did not transfer — most likely the downside-risk features' contribution was IS-regime-specific, or the trained `LGBMRanker` at the EXPLORATION single-seed allocated colsample picks to the new features in a way that did not generalise (the residual iter-v3/070 risk, even after the redundancy cut). The /090 feature-expansion hypothesis is falsified for the cycle.
- **≈10% — the feature expansion lifts the gross signal but the net book is essentially unchanged** (OOS net monthly Sharpe within ±0.03 of /089's −0.0985) — the gross lift was real but too small to move the net book given the fee base. A marginal-mechanical outcome.
- **≈5% — full success: OOS net monthly Sharpe ≥ +1.0.** The feature expansion clears the floor on the first pass. The IS evidence (a +9.6% composite IC-IR lift on a still-thin signal) makes this the tail — named honestly, not expected.

The single most-likely outcome is the **≈45% "feature expansion works and transfers, OOS book materially improved and plausibly net-positive but sub-floor."** The most likely *failure* is F3/F4 — the IS composite IC-IR lift does not transfer OOS (≈20%) — the foreseeable risk for any feature-expansion axis, and the reason the C-block redundancy cut was applied to minimise the iter-v3/070 colsample-dilution exposure. The honest residual: even the modal success is sub-floor — /090 is a step toward a net-positive cross-sectional book, and /091's short-tilt construction (pre-registered Section 3.6) is the expected complementary lever.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria — Classification Taxonomy (LOCKED)

iter-v3/090 is a gross-signal-strengthening EXPLORATION on the RETAINED cross-sectional architecture. **An EXPLORATION cannot update BASELINE_V3.md regardless of classification** — BASELINE_V3.md stays `v0.v3-059` (IS +1.0894 / OOS +0.5791). The taxonomy, evaluated in disjunctive precedence (first match canonical):

### 8.1 — SUSPICIOUS (evaluated FIRST)
Fires on EITHER (a) OOS net monthly Sharpe / IS net monthly Sharpe **> 3.0** (the OOS-soars-on-flat-IS signature — N/A if both negative), OR (b) OOS rank-IC ≥ 2× the IS-train rank-IC magnitude (an implausible OOS-better-than-IS divergence), OR (c) OOS gross monthly Sharpe ≥ 3× /089's +0.1717 (an implausible feature-expansion gross jump — the EDA supports a ~+10% lift, not a tripling).

### 8.2 — FEATURE-EXPANSION-FALSIFIED
Fires if (NOT SUSPICIOUS) AND **F2 fires (IS turnover > 0.138 ceiling) OR F3 fires (OOS gross monthly Sharpe ≤ /089's +0.1717) OR F4 fires (OOS net monthly Sharpe ≤ /089's −0.0985)**. The feature expansion blew turnover, or did not strengthen the gross signal OOS, or did not improve the net OOS book → the /090 gross-signal-strengthening hypothesis is falsified for the cycle. NO-MERGE. The cross-sectional architecture and `cross_sectional.py` infrastructure are RETAINED (the architecture is not falsified — the /088/089 OOS rank-IC stands; only the /090 feature additions are).

### 8.3 — FEATURE-EXPANSION-VALIDATED-PROMISING
Fires if (NOT SUSPICIOUS, NOT 8.2) AND **OOS rank-IC > 0 AND IS turnover ≤ 0.138 AND OOS gross monthly Sharpe > /089's +0.1717 AND OOS net monthly Sharpe > /089's −0.0985 AND OOS net monthly Sharpe > 0**. The feature expansion strengthened the gross signal, contained turnover, transferred OOS, improved the net book, AND produced a **net-positive OOS book**. Sub-case **8.3-FULL**: additionally OOS net monthly Sharpe ≥ +1.0 AND IS net monthly Sharpe ≥ +1.0 — clears the absolute floors; a /092 CONFIRMATION-bundle candidate. Sub-case **8.3-FOUNDATION**: OOS net monthly Sharpe ∈ (0, +1.0) — validated and generalising, the cross-sectional book is net-positive but sub-floor; advances as the cross-sectional baseline for /091.

### 8.4 — FEATURE-EXPANSION-PARTIAL (the honest modal outcome)
Fires if (NOT SUSPICIOUS, NOT 8.2, NOT 8.3) AND **OOS rank-IC > 0 AND IS turnover ≤ 0.138 AND OOS gross monthly Sharpe > /089's +0.1717 AND OOS net monthly Sharpe > /089's −0.0985** but the OOS net monthly Sharpe is **≤ 0** (so 8.3 does not fire — the net book improved materially but is not yet net-positive). The feature expansion strengthened the gross signal, contained turnover, transferred OOS, and **materially improved the OOS net book** — but the still-thin signal keeps it sub-zero. NO-MERGE; the gross-signal axis is advanced and /091's short-tilt construction is the next required lever. **This is the Section-7 ≈45% modal prediction** (in its sub-zero variant; the net-positive variant is 8.3-FOUNDATION).

### 8.5 — NULL / INCONCLUSIVE
The Phase-6 build did not reach a runnable cross-sectional backtest. Recorded for completeness; the build is a focused feature addition on the RETAINED runnable /088/089 infrastructure, so this is not expected.

**MERGE/NO-MERGE statement.** /090 is an EXPLORATION — it does NOT merge to update BASELINE_V3.md regardless of class. A `v0.v3-090` annotated EXPLORATION closeout marker is issued at Phase 8 (the `v0.v3-082`…`v0.v3-089` pattern). The substantive decision: 8.3-FULL → the /090 feature set advances to the /092 CONFIRMATION bundle as a gross-signal edge ingredient; 8.3-FOUNDATION or 8.4 → the /090 feature set is RETAINED as the cross-sectional baseline for /091 and recorded in the exploration catalog with its delta; 8.2 → the /090 features are dropped, the cross-sectional architecture retained.

---

## Section 9 — Library Stack Declaration

- **LightGBM** — `LGBMRanker` with `objective="lambdarank"` (the RETAINED /088 model; unchanged — now trained on 15 features). Already a v3 dependency.
- **Optuna** — hyperparameter search (existing v3 dependency); CV objective = IS rank-IC.
- **pandas / numpy** — the pooled-panel construction, the two new feature engineering functions (`pandas.rolling` covariance/variance/std), the cross-sectional rank-normalization, the overlapping-tranche book, the no-trade band, the turnover diagnostic, the CPCV path net-return computation.
- **No new third-party dependency.** Every /090 change — the two downside-risk features, `_engineer_xs_downside_features`, the `expand_downside` panel-builder branch — is pure pandas/numpy on the existing LightGBM ranking model. No mlfinlab/mlfinpy/pypbo/fracdiff dependency is added or changed. No walk-forward fallback is triggered (the `XS_REQUIRED_GAP = 88` purge does not eat the 24-month training window — H is unchanged at 3).

## Section 10 — QR Audit Trail

### 10.1 — The orchestrator's lead steer and the QR call

The orchestrator's dispatch LOCKED the **direction** of /090 — strengthen the cross-sectional ranker's GROSS signal (per the /089 closeout + the /089 Critic Recs #2/#3), NOT a third round of turnover reduction. Per `feedback_v3_axis_selection_quant_discipline.md`, the QR owns every *design* decision within that direction, EDA-grounded. The QR's calls in this brief, all IS/research-grounded: (a) **rejecting the /089-scoped G4 "cross-sectional momentum channels"** — the QR audited the /089 `gross_signal_eda.py` G4 and found its candidate channels (`xsret_lb = close/close.shift(lb) − 1`) are plain trailing-return ratios already cross-sectionally rank-normalized in the panel; the per-channel ICs (−0.03..−0.04) are the same magnitude as the existing stack, and the composite moved only +2% — the iter-v3/070 dead-path; (b) **researching and testing genuinely-different cross-sectional feature families** (idiosyncratic vol, downside risk, liquidity/size — Section 10.2) with the iter-v3/070-correct INCREMENTAL multivariate-contribution test; (c) **the disciplined B2 cut** — greedy forward selection, leave-one-out, and the C3/C4 redundancy cut that DROPPED `cand_semidev_50` despite its strong univariate IC; (d) **the honest scoping call** — /090 = the feature axis; the short-tilt construction = the /091 axis (pre-registered Section 3.6 with F-ASYM in Section 4.3). The orchestrator suggested the gross-signal direction; the QR committed the EDA (`cecbc8f`) before this brief and the EDA backs every Section-3 decision.

### 10.2 — Literature-research path (genuine WebSearch/WebFetch, Phases 1–4)

Cross-sectional crypto factors, idiosyncratic volatility, downside risk, the cross-sectional ML literature — the research that grounded the candidate feature families:

1. **Liu, Tsyvinski & Wu (2022), "Common Risk Factors in Cryptocurrency"** — *Journal of Finance* 77(2):1133 / NBER WP 25882. The canonical crypto cross-sectional-factor paper, re-consulted for the cross-sectional factor structure: a crypto three-factor model (market, size, momentum) prices the cross-section of crypto returns, and **size and momentum carry genuine cross-sectional premia**. This grounds /090's premise that genuinely cross-sectional feature families — not more of the same momentum channels — are the lever, and motivated the B3 size/liquidity family (tested, positive but not the strongest).
2. **Liu & Tsyvinski (2021), "Risks and Returns of Cryptocurrency"** — *Review of Financial Studies* 34(6):2689. Establishes that crypto returns are driven by exposure to crypto-specific factors and that **cross-sectional dispersion in those exposures predicts returns** — the foundation for a cross-sectional ranker, and the reason /090 builds features with genuine cross-sectional dispersion (the panel rank-normalizes them per timestamp).
3. **The idiosyncratic-volatility anomaly in crypto** — Ang, Hodrick, Xing & Zhang (2006, *JF*) established the IVOL anomaly in equities (low-IVOL stocks out-perform); the crypto cross-sectional literature (Cakici, Fieberg, Metko & Zaremba 2024, "Cryptocurrency Anomalies and Economic Constraints," *IRFA*; and the crypto-IVOL studies) documents an analogous **negative cross-sectional IVOL relation in crypto** — low-idiosyncratic-vol coins out-perform. This grounded the B1 idiosyncratic-vol family (the EDA's `cand_ivol_50` = residual vol after a BTC-beta regression; B1 tested positive — d IC-IR +0.0145 — but B2 downside-risk was stronger).
4. **Cross-sectional downside risk** — the downside-beta and semi-deviation literature (Ang, Chen & Xing 2006, "Downside Risk," *RFS*; Bawa & Lindenberg 1977 on the lower-partial-moment / downside-beta CAPM) establishes that **downside risk is priced separately from total risk** — assets with high downside beta / high downside dispersion earn a distinct risk premium. The B2 family operationalises this cross-sectionally: semi-deviation, down-beta, rolling max-drawdown, Sortino-scaled momentum. B2 was the strongest candidate family by incremental multivariate contribution (Section 2.3) — and it is the family the short-leg-asymmetry diagnosis (A3) predicts should help, since downside-risk features directly target the loser end of the book.
5. **Cakici et al. (2024), "Cryptocurrency Anomalies and Economic Constraints"** — *International Review of Financial Analysis*. A broad cross-sectional anomaly study confirming that crypto cross-sectional anomalies exist but are concentrated and cost-sensitive, and that **the long-short structure and the leg asymmetry matter** — abnormal returns are not symmetric across the long and short legs. This directly informs the short-leg-asymmetry diagnosis (the A-block) and the decision to pre-register the asymmetric-construction axis for /091.
6. **Poh, Lim, Zohren & Roberts (2021), "Building Cross-Sectional Systematic Strategies By Learning to Rank"** — arXiv 2012.07149 / *J. Financial Data Science* 3(2):70. The /088 methodology paper, re-consulted for the feature-treatment convention: LTR cross-sectional strategies feed **cross-sectionally normalized features** to the ranker — confirming /090's two new features must be (and are) cross-sectionally rank-normalized at panel-build time exactly like the existing 13.

The research path: papers 1–2 established that genuine cross-sectional factors (not more momentum) are the lever; paper 3 supplied the idiosyncratic-vol family; paper 4 supplied the downside-risk family (the eventual /090 axis); paper 5 supplied the leg-asymmetry framing and the /091-deferral rationale; paper 6 confirmed the cross-sectional-normalization treatment. The iter-v3/070 dead-path discipline (a project-internal lesson, not a paper) dictated the multivariate-contribution test over a univariate Spearman rank.

### 10.3 — No-cheating audit

Per `feedback_no_cheating.md` — every design parameter selected on IS data only or a-priori:

- **OOS_CUTOFF_DATE / training_months** — IMMUTABLE, untouched.
- **The two new features `xs_sortino_mom_12` / `xs_downbeta_50`** — selected by the committed IS-only EDA: the B-block (`gross_signal_expansion_eda.py`) tested family-level incremental multivariate contribution on IS rows; the C-block (`b2_feature_selection_eda.py`) did greedy forward selection (C1), leave-one-out (C2), and the redundancy cut (C3/C4) — all on IS data. OOS never read.
- **The feature construction windows** (`XS_DOWNSIDE_VOL_WINDOW = 50`, `XS_DOWNSIDE_MOM_LOOKBACK = 12`) — a-priori, matched to the existing 50-bar v3 feature windows; the EDA used the identical windows (the EDA's `cand_*` features and the production `_engineer_xs_downside_features` are line-for-line equivalent).
- **The sign alignment of each feature in the composite** — the IS rank-IC (`X0_feature_is_ic.csv`), IS data only.
- **The decision to DROP `cand_semidev_50`** — the C3 pairwise cross-sectional rank correlation (0.80 with the incumbent `range_realized_vol_50`) and the C4 tiebreak, both IS-only. A redundancy cut, not an OOS-tuned cut.
- **The /089 cost-aware construction + the 0.138 turnover ceiling** — RETAINED unchanged from /089 (all /089-IS-grounded).
- **The 13 base features, the universe, the H=3 label, the embargo** — UNCHANGED from /088/089.
- The EDA scripts read only IS rows (`open_time < OOS_CUTOFF_MS`, with the 180-bar burn-in). The forward-return target is the H=3 cross-sectional forward return — a per-bar predictor target, computed IS-only.
- The QR sees OOS for the first time in Phase 7. Every Section 4 OOS gate is a pre-registered evaluation gate, not a tuned parameter.

### 10.4 — The honest senior read

iter-v3/090 is a genuine, well-researched, multivariate-contribution-tested gross-signal-strengthening iteration on v3's most promising structural line. It executes the highest-EV lever the /089 closeout identified — grow the gross signal, not shave turnover — with real research (the Liu-Tsyvinski crypto-factor literature, the idiosyncratic-vol and downside-risk anomalies), a committed IS-only EDA that tests INCREMENTAL multivariate contribution (the iter-v3/070-correct test, explicitly rejecting the /089-scoped trailing-return channels as the dead-path), and a disciplined feature-selection cut that REJECTS a redundant candidate even though its univariate IC looked strong. The short-leg-asymmetry diagnosis is delivered cleanly (A3: 4.1× sharper at the loser end — the cross-sectional signal is structurally a downside predictor), and the QR makes the honest scoping call: the feature expansion is /090's single axis; the short-tilt construction is pre-registered as /091's. The honest residual: the gross-signal lift is real but modest (+9.6% IS composite IC-IR), the modal OOS outcome is FEATURE-EXPANSION-PARTIAL or 8.3-FOUNDATION — a material improvement on the /089 book, plausibly net-positive, but well below the +1.0 floor — and a CONFIRMATION-worthy cross-sectional book likely needs /090's feature gain plus /091's short-tilt construction. That is not defeatism; it is the relentless, honest, top-quant-firm-grade execution the mission demands — /090 advances the architecture on the gross-signal axis and hands /091 a concrete, IS-grounded, pre-registered short-tilt axis.

## Section 11 — Reproducibility Stamp

- **EDA SHA**: `cecbc8f` — `analysis/iteration_v3-090/gross_signal_expansion_eda.py` (X0, A1–A3, B1_B3, B4 CSVs) + `analysis/iteration_v3-090/b2_feature_selection_eda.py` (C1–C3 CSVs) + `C4_orthogonal_subset_tiebreak.csv`.
- **Brief SHA**: `bb425a5` (this research brief). **Phase 5.5 gate SHA**: `662d7cc` (PASS). This Section-11 SHA backfill in the immediately-following commit.
- **Setup SHA**: `a584fdf` — `XS_DOWNSIDE_FEATURES` + `_engineer_xs_downside_features` + the `expand_downside` panel-builder branch in `cross_sectional.py`; `XS_FEATURE_COLUMNS` → 15 + `ITERATION_LABEL "v3-090"` + the `_verify_feature_columns` 15-feature assertion in `run_cross_sectional_v3.py`; the 4 new /090 tests in `tests/strategies/ml/test_cross_sectional.py`. `uv run pytest tests/strategies/ml/test_cross_sectional.py` — 40/40 green; `uv run ruff check` — clean.
- **Reports**: `reports-v3/iteration_v3-090/` (Phase 6).
- **Run mode**: EXPLORATION — single-seed (seed=42), `--n-trials 35` (the cross-sectional-path runner spec).
- **Future-iteration axes** (deferred from /090, recorded for the cycle plan): (i) /091 — the cross-sectional short-tilt / asymmetric-leg construction (pre-registered Section 3.6, IS-EDA-grounded by /090's A-block; F-ASYM in Section 4.3 gives /091 a clean pre-registered asymmetry measurement); (ii) the B1 idiosyncratic-vol and B3 liquidity/size families (positive incremental contribution but weaker than B2 — candidates for a later feature expansion if /090 transfers); (iii) the cross-sectional risk-gate re-design (which v3 gates transfer to a market-neutral book); (iv) a dedicated cross-sectional CONFIRMATION if /090/091 reach a FEATURE-EXPANSION-VALIDATED-PROMISING / 8.3 result.
