# iter-v3/097 — Research Brief — SYMBOL-UNIVERSE RE-SELECTION: re-anchor v3 onto genuine-signal symbols

**Iteration**: iter-v3/097 — cycle-4 EXPLORATION — a symbol-universe RE-SELECTION (a structural axis, category 5 of the `feedback_v3_structural_over_knob_exploration.md` ladder)
**Type**: EXPLORATION — universe RE-SELECTION (drop thin-signal symbols, re-anchor onto screened genuine-signal symbols). NOT a universe EXPANSION (the count stays 3; the denominator does not grow).
**Author role**: Quant Researcher (QR), v3
**Branch**: `iteration-v3/097`
**Date**: 2026-05-18
**Anchor**: BASELINE_V3.md `v0.v3-059` — per-symbol LightGBM, triple-barrier label, IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, tag `v0.v3-059`. UNCHANGED by this iteration.
**EDA SHA**: `f06eef7` — `analysis/iteration_v3-097/symbol_universe_screen_eda.py` + `seed_robustness_check.py` + T1-T6 CSVs.

---

## Section 0 — Data-Split Declaration

```
OOS_CUTOFF_DATE = 2025-03-24      # IMMUTABLE — src/crypto_trade/config.py
OOS_CUTOFF_MS   = 1742774400000   # IMMUTABLE
training_months = 24              # IMMUTABLE
```

- The walk-forward / CPCV backtest runs on ALL data. The reporting layer splits results at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/` + `comparison.csv`. No date is cherry-picked; the backtest runs from each symbol's earliest kline.
- **The QR sees OOS for the first time in Phase 7.** This brief and the Section-2 EDA are IS-ONLY. The screening EDA restricts every candidate's panel to `open_time < OOS_CUTOFF_MS` AND drops the first 24 months of each symbol's life (the listing burn-in), so every IC is measured ONLY on the runner's actual walk-forward IS test span `[first_kline + 24mo, OOS_CUTOFF_MS)` — bit-identical to the runner's IS evaluation window (the `feedback_v3_eda_walkforward_faithful.md` /091 fix; see Section 2.6).
- Hard floor `OOS_Sharpe / IS_Sharpe ≥ 0.5` (Gate 3) applies. `OOS_CUTOFF_DATE` and `training_months` are NOT touched. No re-anchor of `BASELINE_V3.md` — `v0.v3-059` stays canonical; an EXPLORATION cannot update the baseline (`feedback_v3_baseline_update_policy.md`).
- All feature parquets for the screened universe already exist on disk (`data/features_v3/*_8h_features.parquet`, 22 of 22 present). No `fetch`/`features` Phase-6 setup item is required for the GENUINE-SIGNAL universe — the parquets ADAUSDT/GALAUSDT/LDOUSDT are all present and current (Section 2.1, T1).

---

## Section 1 — Hypothesis

> v3's binding constraint is that two of its three universe symbols carry no genuine feature→label signal. The /096 EDA measured the within-symbol purged-CV rank-IC of the canonical 14-feature `V3_FEATURE_COLUMNS` stack vs the /059 triple-barrier label at **BCH +0.025 / LDO +0.178 / TRX +0.029** — i.e. `/059`'s OOS +0.58 is carried by LDO alone, and BCH/TRX sit on the noise floor. **A thin feature→label IC on a symbol means that symbol is the wrong instrument for the v3 framing — not that the feature space is worked.** The fix is to screen the broad allowed universe on that exact IC metric and **re-anchor the v3 universe onto the symbols where the existing 14-feature stack already carries genuine, IS-stable, seed-stable signal** (LDO-like symbols, IC clearly above the +0.025 thin floor), dropping the thin-signal symbols (BCH, TRX). A 3-symbol universe of genuine-signal symbols produces a higher-IS / higher-OOS book than the BCH/LDO/TRX universe because two of the three per-symbol models are no longer fitting noise.

This is one architectural claim with one mechanism (per-symbol models on genuine-signal symbols generalize; per-symbol models on thin-signal symbols overfit IS noise and invert OOS). It is **distinct from the /021/069/083/087 universe-EXPANSION dead-path** (Section 7.2): those ADDED weak symbols to the existing BCH/LDO/TRX book — denominator growth, the Grinold-Kahn `√breadth` lever — and every one failed. This iteration does the opposite: it REMOVES the thin-signal symbols and REPLACES them. The universe count stays 3. The screening criterion is also new — a feature→label IC screen, the exact tool the /083 closeout said prior expansions lacked (`/083` used an IS-edge screen, `/087` a Sharpe-indifference-curve PnL-correlation screen; neither measured whether the 14-feature stack actually predicts the label on the candidate).

---

## Section 2 — IS-Only Numerical Evidence

The committed EDA is `analysis/iteration_v3-097/symbol_universe_screen_eda.py` (EDA SHA `f06eef7`), producing `T1`-`T5`; the companion `seed_robustness_check.py` produces `T6`. All console output and CSVs are committed.

### 2.1 — T1: the candidate universe (22 symbols, IS-only, post-24mo-burn-in)

The candidate universe is the 22-symbol `XS_UNIVERSE` (the cross-sectional universe — already feature-complete on disk). It is **disjoint with `V3_EXCLUDED_SYMBOLS`** by construction; the EDA asserts this at runtime (`assert not set(CANDIDATE_UNIVERSE) & set(V3_EXCLUDED_SYMBOLS)` — PASS, 0 overlap). Every candidate passes the ≥300-IS-row sufficiency filter. The three symbols of the proposed re-anchored universe:

| Symbol | IS rows (post-burn-in, NaN-dropped) | IS span | long-label frac | mean tb_pnl |
|---|---:|---|---:|---:|
| LDOUSDT | 581 | 2024-09-11 → 2025-03-23 | 0.537 | 5.49 |
| GALAUSDT | 1689 | 2023-09-08 → 2025-03-23 | 0.498 | 5.20 |
| ADAUSDT | 3476 | 2022-01-20 → 2025-03-23 | 0.463 | 3.62 |

(Full 22-row table: `T1_candidate_is_panels.csv`. The IS-row count is post-24-month-burn-in and post-feature-NaN-drop. LDO's 581-row IS panel is the runner's actual IS span for LDO — it matches the /096 EDA's LDO T1 row exactly; v3 has run LDO on this thin panel since /029. GALA's 1689-row and ADA's 3476-row IS panels both clear the EDA's ≥300-row sufficiency filter with margin; the 5-fold purged CV ran on all 5 folds for both, Section 2.2.)

**Honest note on panel depth.** GALA's 1689-row IS panel is deeper than LDO's 581 (the symbol /059 already trades) but shallower than the dropped BCH/TRX (3567/3509). A thinner panel raises per-symbol Optuna-overfitting risk — but the screen *already accounts for this*: the within-symbol CV-IC is measured on exactly that 1689-row panel with a 22-candle-embargo purged 5-fold, and GALA still scores +0.127 seed-stably. The IC is the panel-depth-adjusted signal measure. F2 (IS collapse) and F3 (GALA per-symbol OOS) are the pre-registered gates if the thin panel nonetheless causes overfitting.

### 2.2 — T2: the headline screen — within-symbol purged-CV rank-IC

T2 is the **headline metric** and is the *same* metric the /096 EDA used to diagnose BCH/LDO/TRX: a v3-representative LightGBM (the /096 `LGB_PARAMS`) trained on 4 of 5 purged folds (22-candle embargo, both sides), predicting the held-out fold, scored by Spearman rank-IC of the prediction vs the realized triple-barrier directional label. Ranked, descending:

| Rank | Symbol | within-symbol CV rank-IC | × the +0.025 thin floor | Band |
|---:|---|---:|---:|---|
| 1 | **LDOUSDT** | **+0.17793** | 7.1× | **GENUINE** |
| 2 | **GALAUSDT** | **+0.12703** | 5.1× | **GENUINE** |
| 3 | AAVEUSDT | +0.04786 | 1.9× | BORDERLINE |
| 4 | EOSUSDT | +0.04718 | 1.9× | BORDERLINE |
| 5 | ADAUSDT | +0.04261 | 1.7× | BORDERLINE |
| 6 | THETAUSDT | +0.03245 | 1.3× | THIN |
| 7 | **TRXUSDT** | **+0.02907** | 1.2× | **THIN** (legacy) |
| 8 | **BCHUSDT** | **+0.02542** | 1.0× | **THIN** (legacy) |
| 9–22 | CRV, ICP, FIL, RUNE, MANA, AXS, VET, GRT, ALGO, ATOM, AVAX, FTM, HBAR, SAND | +0.018 → −0.115 | ≤ 0.74× | THIN |

Bands (pre-registered, decided before running, on the headline metric only): **GENUINE** `CV-IC ≥ +0.060`; **THIN** `CV-IC < +0.040` (the BCH/TRX band); **BORDERLINE** the `[+0.040, +0.060)` gap. Full table: `T2_within_symbol_cv_ic.csv`, `T5_ranked_screen.csv`.

**The screen's two structural findings:**
1. **The /096 thin-signal diagnosis of BCH and TRX is RE-CONFIRMED** on the full-IS-span purged-CV metric: BCH +0.025 (rank 8 of 22), TRX +0.029 (rank 7). The legacy universe carries two noise-floor symbols.
2. **Exactly two symbols are unambiguously genuine-signal**: LDO (+0.178, the symbol /059 already carries) and **GALA (+0.127)** — 7.1× and 5.1× the thin floor. The next tier (AAVE/EOS/ADA, ~+0.045) is genuinely intermediate; everything from rank 6 down is at or below the thin floor (the universe-wide CV-IC mean is +0.002 — most symbols carry no signal for this framing, which is itself the point: symbol selection is decisive).

### 2.3 — T6: the genuine/thin split is seed-stable (NOT a single-seed lottery)

A universe RE-SELECTION must not repeat the `feedback_v3_single_seed_frozen_baseline.md` / iter-v3/036/079 single-seed-lottery failure mode. `seed_robustness_check.py` re-runs the headline within-symbol CV-IC for the top tier under 4 LightGBM seeds (42, 7, 99, 2024):

| Symbol | seed 42 | seed 7 | seed 99 | seed 2024 | mean | std | all 4 seeds clear +0.040? |
|---|---:|---:|---:|---:|---:|---:|:--:|
| LDOUSDT | +0.1779 | +0.1994 | +0.1476 | +0.1608 | **+0.1714** | 0.0194 | **YES** |
| GALAUSDT | +0.1270 | +0.1275 | +0.1514 | +0.1063 | **+0.1281** | 0.0160 | **YES** |
| ADAUSDT | +0.0426 | +0.0408 | +0.0630 | +0.0656 | **+0.0530** | 0.0114 | **YES** |
| AAVEUSDT | +0.0479 | +0.0484 | +0.0494 | +0.0532 | +0.0497 | 0.0021 | YES |
| EOSUSDT | +0.0472 | +0.0397 | +0.0392 | +0.0399 | +0.0415 | 0.0033 | NO (3 of 4 below) |
| BCHUSDT | +0.0254 | +0.0256 | +0.0199 | +0.0298 | +0.0252 | 0.0035 | NO (all 4 below) |
| TRXUSDT | +0.0291 | +0.0354 | +0.0191 | +0.0268 | +0.0276 | 0.0058 | NO (all 4 below) |

(Full table: `T6_seed_robustness.csv`.) **The genuine/thin split is a property of the symbols, not of seed 42.** LDO/GALA hold +0.17/+0.13 across all 4 seeds; BCH/TRX stay on the noise floor across all 4. ADA — the borderline symbol selected as the third universe member (Section 3.1) — clears +0.040 on all 4 seeds with seed-mean +0.053; AAVE clears the floor too but with a lower seed-mean (+0.050); EOS fails it on 3 of 4 seeds. ADA is the strongest seed-stable third symbol.

### 2.4 — T3: sub-period IC is regime-CONCENTRATED for every symbol (a STABILITY ANNOTATION, not a band gate)

T3 splits each symbol's IS span into 3 equal sequential thirds and re-measures the model IC in each. The finding is structural and applies to BCH/LDO/TRX too: **every v3 symbol's edge is regime-concentrated** — no symbol scores positive in all 3 thirds with the model. LDO `[+0.28, −0.22, +0.00]`, GALA `[+0.51, −0.07, +0.20]`, BCH `[−0.00, +0.08, −0.24]`, TRX `[+0.01, −0.07, +0.03]`. This is the IS-dominance signature the /096 EDA already named, and it is *why* /059 is IS-dominant (OOS/IS = 0.53). T3 is therefore reported as a `regime_stability` ANNOTATION (`STABLE` vs `CONCENTRATED`), NOT as a hard band input — demoting an unambiguous +0.178-IC symbol to BORDERLINE because one third dips negative would conflate "regime-concentrated genuine signal" with "thin signal" — they are different objects. The headline band (Section 2.2) is on the CV-IC metric alone. The regime-concentration finding does drive a pre-registered OOS regime-robustness falsifier (F4, Section 4.3). Full table: `T3_subperiod_sign_consistency.csv`.

### 2.5 — T4: per-feature texture of the genuine pair

For LDO and GALA, T4 reports each of the 14 features' univariate rank-IC and its sign-consistency across the 3 thirds:
- **LDO**: led by the Hurst family — `hurst_diff_100_50` +0.240, `hurst_100` +0.203 (`hurst_100` is sign-consistent across all 3 thirds — the single most stable feature on LDO), `ret_kurt_200` +0.168. The genuine signal is a regime/memory signal.
- **GALA**: led by `ret_kurt_200` +0.114 (sign-consistent across all 3 thirds — GALA's stable anchor), `ret_kurt_50` +0.073, `max_dd_window_50` +0.071. A tail-shape / drawdown-regime signal.

Both genuine symbols have a sign-consistent anchor feature in the existing 14-feature stack — the per-symbol models have a real, IS-stable hook to learn. Full table: `T4_per_feature_ic_texture.csv`.

### 2.6 — Walk-forward fidelity (the /091 anti-recurrence)

Per `feedback_v3_eda_walkforward_faithful.md`: the EDA's `load_symbol_is` applies the runner's per-symbol 24-month listing burn-in (`burnin_end = first_ms + 24*30*24*3600*1000`) AND the IS cutoff (`open_time < OOS_CUTOFF_MS`), so every IC is measured on `[first_kline + 24mo, OOS_CUTOFF_MS)` — the runner's actual walk-forward IS evaluation span. The triple-barrier label is computed on the FULL panel first (so the 21-candle forward scan can see post-burn-in bars) and only THEN restricted to the IS window — no OOS leak, no truncated-forward-window artifact. The purged 5-fold CV uses a 22-candle embargo on both sides of each test fold. The /091 full-panel-vs-walk-forward mismatch cannot recur here: there is no separate "full panel" measurement in this EDA.

### 2.7 — What the EDA does NOT establish

The screen measures feature→label IC — it does not run a backtest, and IC is not Sharpe. A genuine within-symbol CV-IC is a *necessary* condition for a per-symbol model to work (BCH/TRX fail it; LDO works) but it is not *sufficient*: the production runner adds Optuna, the 5-gate+BTC risk stack, the 10-seed ensemble, and the monthly walk-forward refit, any of which can attenuate the IC into a thin or negative net Sharpe. **The decisive test is the Phase-6 backtest** (Section 4). GALA additionally carries a specific Phase-7 risk flagged in Section 7.1 — its per-symbol IS→OOS reversal at /087 — which the Section-4 F-falsifiers are designed to catch.

---

## Section 3 — Proposed Changes (the full architecture spec)

The architecture is UNCHANGED — per-symbol LightGBM, the 14-feature `V3_FEATURE_COLUMNS` stack, the `(2.0, 1.0)`-ATR triple-barrier label, the unified 10-seed ensemble, the 5-gate+BTC risk stack, the walk-forward refit. The SOLE change is the `V3_MODELS` universe. This is deliberately a clean single-axis iteration: it isolates the universe re-selection so the Phase-7 read is unambiguous.

### 3.1 — `V3_MODELS`: BCH/LDO/TRX → LDO/GALA/ADA

```python
# run_baseline_v3.py — the SOLE iter-v3/097 axis
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("C (LDOUSDT)",  "LDOUSDT"),    # KEPT — re-screens GENUINE, CV-IC +0.178 (rank 1/22)
    ("F (GALAUSDT)", "GALAUSDT"),   # ADDED — re-screens GENUINE, CV-IC +0.127 (rank 2/22)
    ("G (ADAUSDT)",  "ADAUSDT"),    # ADDED — strongest seed-stable BORDERLINE, CV-IC +0.043 (rank 5/22)
)
```

- **LDO is KEPT** — it re-screens GENUINE (CV-IC +0.178, the universe's strongest, seed-stable across all 4 seeds). It is the symbol the screen confirms /059's OOS already rests on.
- **GALA is ADDED** — it re-screens GENUINE (CV-IC +0.127, rank 2/22, 5.1× the thin floor, seed-stable). It is the only OTHER symbol in the entire 22-symbol universe in the GENUINE band.
- **ADA is ADDED as the third symbol** — v3's per-symbol architecture has used a 3-symbol universe through all of cycles 1-4; a 2-symbol universe is below that structural norm for per-model diversification and aggregate trade-rate. ADA is the **strongest seed-stable BORDERLINE** symbol: CV-IC seed-mean +0.053, clears the +0.040 thin-band ceiling on **all 4** seeds (T6) — the only borderline symbol with that property *and* the highest seed-mean of the borderline tier. ADA at +0.043–0.053 is ~1.8× the +0.025 BCH/TRX floor it replaces — every member of the re-anchored universe out-screens both dropped symbols.
- **BCH and TRX are DROPPED** — both re-screen THIN (CV-IC +0.025 / +0.029, ranks 8 / 7 of 22, below the +0.040 thin ceiling on all 4 seeds). The /096 finding is re-confirmed; the legacy universe's two noise-floor symbols are removed.

The two-leader-plus-strongest-seed-stable-borderline construction is the bold-but-disciplined call: LDO+GALA are the genuine signal; ADA restores the 3-symbol structure with the most defensible available third symbol. A pure 2-symbol LDO+GALA universe is named as the explicit fallback if the Phase-7 read shows ADA is the weak leg (Section 4.4).

### 3.2 — `V3_EXCLUDED_SYMBOLS` disjointness check (NO-CHEATING)

`V3_EXCLUDED_SYMBOLS` = `{BTC, ETH, LINK, LTC, DOT, BNB, SOL, XRP, DOGE, NEAR, MKR}` (v1/v2-traded + MKR). The re-anchored universe `{LDO, GALA, ADA}` is **disjoint** with it — none of the three is a v1/v2 symbol or MKR. The EDA asserts the full 22-candidate universe is disjoint at runtime (Section 2.1); the Phase-6 runner's pre-flight `_verify_*` check (Section 9, test #2) re-asserts `set(sym for _,sym in V3_MODELS).isdisjoint(V3_EXCLUDED_SYMBOLS)` as a HARD build-fail. `V3_EXCLUDED_SYMBOLS` itself is UNCHANGED — this iteration does not add to it (BCH/TRX are dropped from `V3_MODELS` but are NOT v1/v2 symbols, so they do not enter the exclusion list; a future iteration may re-screen them if the framing changes).

### 3.3 — Constants the universe change pulls

- **`REQUIRED_GAP`** (CPCV embargo) = `(timeout_candles + 1) × n_symbols` = `(21 + 1) × 3` = **66** — UNCHANGED (the universe stays 3 symbols; the gap is symbol-count-driven, and 3 → 3 leaves it at 66).
- **`PER_CELL_GAP`** = `(timeout_candles + 1)` = **22** — UNCHANGED (universe-count-invariant; the per-symbol walk-forward embargo).
- **`ITERATION_LABEL`** = `"v3-097"`.
- The unified 10-seed `ENSEMBLE_SEEDS` 10-tuple, `ENSEMBLE_SIZE = 10`, `n_trials = 35` — all UNCHANGED.
- `V3_FEATURES_PER_SYMBOL` stays EMPTY — GALA and ADA get the universal 14-feature `V3_FEATURE_COLUMNS_TOP_N` stack via the `features_for_symbol` fallback, exactly as LDO does. No per-symbol feature override (the `feedback_v3_per_symbol_lifts_oos_breaks_is.md` discipline — per-symbol customizations are a *separate* future axis, not bundled here).
- `V3_ATR_MULTIPLIERS_PER_SYMBOL` stays EMPTY — GALA/ADA/LDO all use `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`.

### 3.4 — Phase-6 setup items

1. Edit `V3_MODELS` (Section 3.1) and `ITERATION_LABEL` in `run_baseline_v3.py`.
2. Update the `_verify_feature_columns` / pre-flight assertions in `run_baseline_v3.py` to reference the new universe (`features_for_symbol("GALAUSDT")` and `features_for_symbol("ADAUSDT")` MUST each return the 14-feature `V3_FEATURE_COLUMNS_TOP_N`; `"BCHUSDT"`/`"TRXUSDT"` assertions are removed; the disjointness assertion of Section 3.2 is added).
3. **No `fetch` / `features` regen needed** — `data/features_v3/{LDOUSDT,GALAUSDT,ADAUSDT}_8h_features.parquet` are all present and current (Section 2.1). The QE MUST verify the three parquets' `open_time.max()` covers the current OOS extent before the run (a one-line `parquet` check; if GALA/ADA klines are stale vs LDO, run `crypto-trade fetch --symbols GALAUSDT,ADAUSDT --intervals 8h` + `crypto-trade features --symbols GALAUSDT,ADAUSDT --interval 8h --track v3` first — `feedback_data_staleness_per_worktree.md`).
4. The integration-test suite (Section 9).

---

## Section 4 — Expected OOS Impact + Pre-Registered Numerical Falsifiers

### 4.1 — Behavioral-effect predictor (`feedback_v3_axis_saturation_predictor.md`)

A universe RE-SELECTION is NOT a saturated axis — it changes 2 of 3 per-symbol models wholesale, so the trade roster changes massively by construction. **Predicted behavioral effect**: the IS+OOS trade roster is ~⅔ replaced — BCH's and TRX's trades (legacy: BCH 34 OOS / TRX 48 OOS trades) are removed, GALA's and ADA's trades are added; only LDO's per-symbol roster is approximately preserved (LDO's Optuna study is independent of the other symbols — `feedback_v3_single_seed_frozen_baseline.md` — so LDO's trades should be near-identical to /059's LDO trades). A Phase-7 observation of < 50% roster turnover would itself be a red flag (the universe change did not take effect) and triggers F0 below.

### 4.2 — Expected OOS impact (point estimate + interval)

The mechanism: replacing two CV-IC ≈ +0.025 symbols with one CV-IC +0.127 symbol (GALA) and one CV-IC +0.053 symbol (ADA) raises the universe-mean feature→label IC from ≈ +0.077 (BCH/LDO/TRX mean) to ≈ +0.119 (LDO/GALA/ADA mean) — a +0.042 absolute lift, +55% relative. IC is not Sharpe, and the gate stack + Optuna attenuate it, so the prediction is deliberately wide:

- **IS monthly Sharpe**: expected in `[+0.9, +1.5]`, point estimate **+1.15** (≈ /059's +1.09; the genuine-IC symbols should at least match /059's IS).
- **OOS monthly Sharpe**: expected in `[+0.4, +1.3]`, point estimate **+0.85** (a +0.27 lift over /059's +0.58; the lift is the conversion of GALA's genuine IC into OOS edge, partially offset by the loss of BCH's OOS contribution — see F1).
- **OOS/IS ratio**: expected ≥ 0.55 (Gate 3 floor 0.50).

**The decisive caveat — /059's per-symbol OOS is the inverse of its CV-IC** (`reports-v3/iteration_v3-059/comparison.csv`): BCH OOS `weighted_pnl` **+24.75** (CV-IC +0.025 — thin), TRX **+4.16** (CV-IC +0.029 — thin), **LDO −6.18** (CV-IC +0.178 — genuine). i.e. at /059 the *thin-signal* symbol BCH carried the OOS book and the *genuine-signal* symbol LDO LOST OOS. This is exactly why the IC screen is necessary but not sufficient (Section 2.7) — and it cuts both ways: (a) it is the F1 risk made concrete (removing BCH removes a +24.75 OOS contributor whose edge the screen cannot explain — possibly a one-regime artifact, possibly genuine-but-unmodelled); (b) it is *also* evidence that /059's OOS is not resting on genuine modelled signal at all — a +0.127-CV-IC GALA leg is a better-founded OOS bet than a +0.025-CV-IC BCH leg even though BCH's *historical* OOS PnL is higher. The honest reading: /059's BCH OOS PnL is a regime coincidence the model did not earn; the re-anchored universe trades that for two legs whose models genuinely learn. F1/F3/F4 are the gates that adjudicate which reading the Phase-7 data supports.

The honest expectation: this is an EXPLORATION, single-seed (`--seeds 1`, `--exploration` per `feedback_v3_exploration_n_trials_35.md`). A PROMISING read (Section 8) makes it a cycle-4 CONFIRMATION-bundle candidate; it is NOT a merge.

### 4.3 — Pre-registered numerical falsifiers (LOCKED — decided before Phase 6)

Evaluated at Phase 7. Each is a HARD gate with an exact number — predictions (Section 4.2) are estimates; falsifiers are different numbers and are gates.

- **F0 — roster-turnover sanity.** Fires if the OOS trade roster shares > 50% of its trades (by `(symbol, open_time)`) with the /059 OOS roster. → the universe change did not take effect; the build is mis-wired. (NULL-class, Section 8.6 — a build defect, not a strategy verdict.)
- **F1 — OOS net-harm.** Fires if OOS monthly Sharpe < +0.40 (i.e. the re-anchored universe did not clear, with margin, the lower bound of the predicted band — and notably below /059's +0.58). → the re-selection did not transfer; dropping BCH's OOS contribution cost more than GALA/ADA added.
- **F2 — IS collapse.** Fires if IS monthly Sharpe < +0.80 (below /059's +1.09 by > 0.29, and below the predicted lower bound). → the genuine-IC symbols did not produce a healthy IS book under the gate stack — the screen's IC did not survive Optuna + the 5-gate stack.
- **F3 — GENUINE-SIGNAL falsified per-symbol.** Fires if GALA's standalone OOS `weighted_pnl` (from `comparison.csv`) is negative AND its IS `weighted_pnl` is positive — the exact /087 IS-up/OOS-down per-symbol signature. → GALA's +0.127 within-symbol CV-IC did not convert to an OOS-genuine per-symbol edge; the /087 GALA reversal recurred (Section 7.1). This is the central GALA-specific risk and gets its own named falsifier per the `feedback_v3_per_symbol_target_axis_falsifier.md` mandate.
- **F4 — regime-concentration confirmed harmful.** Fires if the OOS Sharpe lift over /059 is > 80% attributable to a single calendar month (the T3 regime-concentration finding manifesting as a single-regime OOS artifact rather than a durable edge). → SUSPICIOUS-class.
- **F5 — Gate-3 breach.** Fires if OOS monthly Sharpe / IS monthly Sharpe < 0.50. → researcher-overfitting / IS-dominance; the hard-blocking Gate 3.
- **F6 — trade-starvation.** Fires if total OOS trades < 130 OR aggregate OOS trades/month < 10 (the `feedback_v3_trade_rate_floor.md` floor; for v3 EXPLORATION the floor is informational per `feedback_trade_rate_floor_bundle_level.md`, but a count *materially* below /059's 94 OOS trades is a substantive concern and is recorded).

### 4.4 — The 2-symbol fallback

If F3 fires (GALA fails) but LDO+ADA hold, OR if ADA is the weak leg (ADA standalone OOS `weighted_pnl` negative while LDO+GALA are positive), the Phase-8 QR records the **pure LDO+GALA 2-symbol universe** (or LDO+ADA) as the corrected next build — not a re-architecture, a one-symbol scope correction on the same axis. The fallback is pre-registered here so it is not a post-hoc rationalization.

---

## Section 5 — Risk Mitigation (R1-R5, IS-calibrated, simulated effect)

The 5-gate+BTC risk stack is UNCHANGED and applies per-symbol to GALA and ADA exactly as it does to LDO/the legacy symbols:

- **R1 — z-score OOD gate** (`|z| > 2.5` on the 14 features, IS-covariance-calibrated): applies per-symbol; for GALA/ADA the OOD covariance is fit on each symbol's own IS training window (the `risk_v3.py` `_build_lookups` path). Simulated effect: the gate fires on out-of-distribution feature vectors; on the legacy universe it gated ~5-10% of candidate bars. No re-calibration needed — the cutoff is a per-symbol IS-percentile.
- **R2 — ADX trend-strength gate**, **R3 — Hurst regime gate**, **R4 — vol-scaling**, **R5 — low-vol filter**: all per-symbol, all IS-calibrated on each symbol's own training window. No per-symbol override is introduced (Section 3.3) — GALA/ADA inherit the universal gate config.
- **BTC-trend filter** (`±15%`, 42-bar lookback): symbol-independent (it reads BTC, not the traded symbol) — applies identically.
- **Concentration**: with 3 genuine-or-borderline symbols and per-symbol independent models, no single symbol is expected to dominate; the Phase-7 read records per-symbol OOS `concentration_pct` (F3 already gates the GALA leg specifically). The /059 baseline ran BCH at 108.86% OOS concentration (a single-symbol-carries-the-book pathology) — the re-anchored universe is expected to be *less* concentrated because LDO and GALA are both genuine-signal, not one-genuine-two-noise.

The risk stack is IS-calibrated and was not re-tuned for this iteration — re-tuning gates would confound the universe axis. The Section-9 integration tests assert the gates are present and the OOD covariance is fit on the training window only.

---

## Section 6 — Risk-Management Design (the deeper structural defense)

The deeper defense against this iteration's central risk — that GALA/ADA per-symbol models overfit IS and invert OOS, the /087 failure mode — is built into the *selection criterion itself*, not bolted on afterward:

1. **The screen is a feature→label IC screen, not a PnL screen.** /087 selected GALA on a Sharpe-indifference-curve PnL-correlation argument (diversification), which is silent on whether the 14-feature stack predicts GALA's label. This iteration selects on the within-symbol purged-CV rank-IC — the direct measure of "can the model learn this symbol." GALA scoring +0.127 means the model has a genuine, cross-validated hook; that is a materially stronger pre-backtest case than /087 had, and it is the specific gap the /083 closeout said prior expansions lacked.
2. **The screen is seed-stable** (T6, Section 2.3). The /087 GALA selection was single-seed; T6 confirms GALA's +0.127 holds across 4 seeds. A single-seed lottery is ruled out at the screening stage.
3. **The purged-CV embargo (22 candles, both sides)** means the screen's IC is itself bias-free — no label-window leakage inflates it. The IC the brief reports is the IC the runner's walk-forward should see, modulo Optuna/gate attenuation.
4. **F3 is a pre-registered, GALA-specific, named falsifier** (Section 4.3). If GALA's IS-up/OOS-down /087 signature recurs, the iteration is read NEGATIVE (Section 8) and the 2-symbol LDO-only-genuine fallback is the documented next build (Section 4.4). The risk is bounded and pre-named.
5. **The universe count does not grow** — this is a REPLACEMENT (3 → 3), not the `√breadth` EXPANSION that failed 4 times. The denominator-growth failure mode is structurally absent.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

### 7.1 — The GALA /087 reversal — the named, specific risk

GALA was added to the v3 universe once before, at iter-v3/087, as part of the wholesale BCH/LDO/TRX → +GALA+MANA+SAND expansion. **GALA's per-symbol model scored +67.2% IS net PnL → −19.0% OOS** — a genuine IS-up/OOS-down reversal. This brief does NOT hide that. Three reasons this iteration's GALA inclusion is materially different, and one honest residual:
- **Different selection criterion** — /087 used a PnL-correlation Sharpe-indifference screen; this uses a feature→label IC screen (the /083-closeout-mandated tool). GALA's +0.127 CV-IC is direct evidence the model can learn it, which the /087 screen never measured.
- **Different axis** — /087 was an EXPANSION (6-symbol book); GALA was the 4th/5th/6th symbol diluting a thin universe. Here GALA is one of 3, alongside the genuine-signal LDO. The per-symbol model is identical; what differs is that GALA is now selected *because* its model learns, not *despite* it.
- **Seed-stability** — /087's GALA was single-seed; T6 shows +0.127 across 4 seeds.
- **Honest residual**: a +0.127 IS-measured CV-IC is still an IS measurement. It is a *necessary* condition (BCH/TRX fail it) but the /087 reversal proves IS strength alone does not guarantee OOS transfer. **F3 is the pre-registered gate for exactly this** — if GALA's per-symbol OOS `weighted_pnl` is negative on a positive IS, the iteration is NEGATIVE and the fallback fires. The brief carries the risk explicitly rather than asserting it away.

### 7.2 — Why this is NOT the /021/069/083/087 universe-expansion dead-path

`BASELINE_V3.md` records universe EXPANSION as a 4-failure CLOSED axis: /021 (+HBAR+AVAX), /069 (+ADA), /083 (+FIL), /087 (+GALA+MANA+SAND). Every one ADDED symbols to the BCH/LDO/TRX book — the count grew 3→4, 3→4, 3→4, 3→6. This iteration's `V3_MODELS` count is **3 → 3**: it REMOVES BCH/TRX and ADDS GALA/ADA. It is a RE-SELECTION, not an EXPANSION. The expansion dead-path's failure mechanism — diluting a working book with weak symbols, or chasing the `√breadth` lever — is structurally absent: here the *replacement* symbols out-screen the *replaced* symbols on the headline IC metric (GALA +0.127 / ADA +0.053 vs BCH +0.025 / TRX +0.029). The /069 ADA result is acknowledged — but /069 added ADA as a 4th symbol to a then-thin universe on a weaker screen; ADA here is a screened, seed-stable BORDERLINE third symbol replacing the noise-floor TRX, and is explicitly the universe's *weakest* member with a pre-registered weak-leg fallback (Section 4.4).

### 7.3 — Predicted most-likely failure mode

If this iteration fails, the single most likely mode is **F3** — GALA's genuine IS CV-IC failing to transfer to OOS per-symbol `weighted_pnl` (the /087 reversal recurring), with the iteration read NEGATIVE and the LDO+ADA or LDO+GALA 2-symbol fallback recorded. The second most likely is **F1** — the loss of BCH's large OOS contribution (+24.75 weighted_pnl at /059) outweighing GALA/ADA's additions, leaving the aggregate OOS Sharpe below +0.40. The third is **F2** — ADA, the borderline leg, dragging the IS aggregate. All three are pre-registered with exact thresholds.

---

## Section 8 — Classification Taxonomy (LOCKED, disjunctive precedence)

Evaluated at Phase 7 in this order; first match is canonical:

- **8.0 — NULL / build-defect.** Fires if F0 fires (the universe change did not take effect — OOS roster > 50% shared with /059) OR the Phase-6 build did not reach a runnable backtest. → re-scoped, not a strategy verdict (Section 8.6-analogue).
- **8.1 — SUSPICIOUS.** Fires if (NOT 8.0) AND [ F4 fires (the OOS lift is > 80% one-month) OR OOS-monthly-Sharpe / IS-monthly-Sharpe > 3.0 (OOS-soars-on-flat-IS; N/A if IS Sharpe ≤ 0) ]. → NEGATIVE-class; the re-anchored universe loaded a regime factor, not a durable edge.
- **8.2 — NEGATIVE-no-transfer.** Fires if (NOT 8.0-8.1) AND F1 fires (OOS monthly Sharpe < +0.40). → NEGATIVE-class; the re-selection did not transfer to OOS.
- **8.3 — NEGATIVE-IS-broken.** Fires if (NOT 8.0-8.2) AND F2 fires (IS monthly Sharpe < +0.80). → NEGATIVE-class; the genuine-IC symbols did not produce a healthy IS book under the gate stack.
- **8.4 — NEGATIVE-GALA-reversal.** Fires if (NOT 8.0-8.3) AND F3 fires (GALA OOS `weighted_pnl` < 0 on positive IS). → NEGATIVE-class; the /087 GALA reversal recurred. The Phase-8 QR records the LDO+ADA 2-symbol fallback (Section 4.4) as the next build.
- **8.5 — NEGATIVE-Gate-3 / trade-starvation.** Fires if (NOT 8.0-8.4) AND (F5 fires OR F6 fires). → NEGATIVE-class.
- **8.6 — PROMISING.** Fires if NONE of F0-F6 fire — the re-anchored universe transferred: IS ≥ +0.80, OOS ≥ +0.40, OOS/IS ≥ 0.50, GALA's per-symbol OOS edge positive, the OOS lift is not one-month, the roster genuinely changed, trade-rate adequate. → a cycle-4-CONFIRMATION-bundle candidate. NOT a merge — an EXPLORATION never updates `BASELINE_V3.md`.
- **8.7 — PROMISING-STRONG.** Fires if 8.6 fires AND OOS monthly Sharpe > +0.85 (the point estimate) AND OOS/IS ≥ 0.55. → the re-anchored universe is the priority cycle-4 CONFIRMATION axis; the universe re-selection is v3's strongest cycle-4 lever.

A PROMISING (8.6 / 8.7) result is bundled into the cycle-4 CONFIRMATION per `feedback_v3_strict_10_to_1_cadence.md` — never collapsed into an early CONFIRMATION. A CONFIRMATION (multi-seed) is the only run that can re-anchor `BASELINE_V3.md`, and only if it beats /059 on BOTH IS AND OOS (`feedback_v3_strict_both_is_oos_baseline.md`).

---

## Section 9 — Library Stack + Integration-Test Mandate

### 9.1 — Library stack

Pinned, inherited from `v0.v3-059` unchanged: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. **No new third-party dependency** — this iteration is a `V3_MODELS` constant change; it adds no code module, no data feed, no library.

### 9.2 — Integration-test mandate (HARD, pre-registered — the /090→/093 BLOCK process discipline)

Per the /090→/093 process fixes: every falsifier-driving input must be a correctly-unit'd, reproducible runner artifact; the runner must carry genuine CONFIRMATION-grade DSR/PBO/PSR machinery; and every test below is a HARD build-fail test — a Phase-6 build that omits any of them, or whose runner fails any of them, MUST fail the suite *before* the backtest runs (the `&&`-chain stops). The Phase-6 build MUST ship `tests/strategies/ml/test_universe_reselection_v3.py` with AT LEAST these 6 tests:

1. **`test_v3_models_is_the_reanchored_universe`** — asserts `run_baseline_v3.V3_MODELS` symbols == `{"LDOUSDT", "GALAUSDT", "ADAUSDT"}` exactly (the iteration's SOLE axis is wired) AND `"BCHUSDT" not in` and `"TRXUSDT" not in` the universe (the legacy thin symbols are dropped). A source-level assertion — fails the build if the universe edit was not made.
2. **`test_v3_models_disjoint_from_excluded`** — asserts `set(sym for _, sym in V3_MODELS).isdisjoint(set(V3_EXCLUDED_SYMBOLS))` — the NO-CHEATING universe-legality gate (Section 3.2). HARD-fails if any traded symbol is a v1/v2 symbol or MKR.
3. **`test_dsr_json_is_genuinely_computed`** — asserts the runner's `dsr.json` `dsr` and `psr` fields are FINITE COMPUTED values (NOT `0.0`/`NaN` literals) and `pbo` is a genuine fraction in `[0,1]` OR an explicitly-noted structural sentinel; asserts (source-level `grep` + value-level finiteness) that the runner imports and CALLS `validation_v3.psr` and `validation_v3.deflated_sharpe_ratio_v3`. **This is the structural guarantee against the /090→/092 hardcoded-sentinel defect class — it fails the build if the gates are placeholders.** The Phase-6 engineering report MUST cite the exact `validation_v3` call-site and the SR granularity (trade-level vs daily vs annualized) fed to `psr()` per `feedback_v3_methodology_post_hoc_input_traceback.md`.
4. **`test_feature_columns_pinned_for_new_symbols`** — asserts `features_for_symbol("GALAUSDT")` and `features_for_symbol("ADAUSDT")` each return the 14-feature `V3_FEATURE_COLUMNS_TOP_N` exactly (the `feedback_explicit_feature_columns.md` invariant — GALA/ADA inherit the universal stack, no per-symbol override) AND `V3_FEATURES_PER_SYMBOL` is empty.
5. **`test_walk_forward_embargo_intact`** — asserts the `e149e9d` walk-forward embargo (`train_end_ms = test_start_ms - embargo_ms`, `compute_embargo_candles` helper, `cv_gap = embargo_candles * n_symbols`) is present and load-bearing in the runner for the new 3-symbol universe (`cv_gap` resolves to 66).
6. **`test_oos_cutoff_and_training_months_immutable`** — asserts `config.OOS_CUTOFF_MS == 1742774400000` and `training_months == 24` are unchanged — the NO-CHEATING immutability gate.

The Phase 5.5 gate MUST verify the brief specifies tests #1, #2, and #3 as hard build items. The Phase-6 engineering report MUST cite the F0 roster-turnover artifact (`analysis/iteration_v3-097/roster_diff_oos.py`, computing the `(symbol, open_time)` overlap of the /097 OOS roster vs the /059 OOS roster) as a committed, reproducible artifact.

---

## Section 10 — QR Audit Trail

- **Axis origin**: the iter-v3/097 universe-RE-SELECTION axis is QR-authored, grounded in the committed /096 EDA's thin-signal diagnosis (BCH +0.025 / TRX +0.029 within-symbol CV-IC) and the explicit user directive of 2026-05-18 (`feedback_v3_bold_research_mandate.md`, verbatim: "focus on different symbols ... You are free to select whatever symbol you like ... A thin feature→label IC on a given symbol means that SYMBOL is wrong for the framing"). This is NOT an orchestrator ad-hoc pick — it is the direct, EDA-backed, user-directed response to the /096 finding, with the axis decision (which symbols) made by the QR on the committed `f06eef7` screening evidence (`feedback_v3_axis_selection_quant_discipline.md`).
- **The screen is the QR's quantitative basis**: the 22-symbol within-symbol CV-IC screen (T2) + the 4-seed robustness check (T6) are committed BEFORE this brief (EDA SHA `f06eef7`). The universe selection (LDO kept, GALA + ADA added, BCH + TRX dropped) follows mechanically from the pre-registered bands (GENUINE `≥ +0.060`, THIN `< +0.040`) and the seed-stability tie-break for the third symbol — no symbol was picked by narrative.
- **QR sharpening beyond a naive "swap the bottom symbols"**: (1) the headline metric is fixed to the *exact* /096 within-symbol CV-IC so the screen is directly comparable to the diagnosis it answers; (2) T3 sub-period sign-consistency is demoted from a hard gate to a regime-stability annotation, with the explicit reasoning that every v3 symbol's edge is regime-concentrated — a rigid sign-consistency gate would wrongly demote LDO itself; (3) the third symbol is chosen by seed-stability (T6 all-4-seeds-clear-the-floor), not by raw CV-IC rank, ruling out the single-seed lottery; (4) the /087 GALA reversal is surfaced as a named, pre-registered F3 falsifier rather than hidden; (5) a 2-symbol fallback is pre-registered (Section 4.4) so a GALA or ADA failure has a non-post-hoc next build.
- **Cycle-4 follow-on levers (named for iter-v3/098+)**: per the user directive, FEATURE EXPANSION (genuine feature engineering beyond the frozen 14-feature stack — the user-stated "crucial lever") and POOLED-vs-SINGLE models (the /096 LOSO transfer test was NO-GO on the *legacy* thin universe; it is worth re-running the pooled-model question on the re-anchored *genuine-signal* universe, where the symbols share a learnable feature→label map) are the directed cycle-4 follow-on axes. They build ON the re-anchored universe — iter-v3/097 establishes the universe; iter-v3/098+ engineers features and tests pooling on it. This iteration is deliberately a clean single-axis universe change so the Phase-7 universe read is unconfounded.
- **EDA SHA**: `f06eef7`. **Brief SHA**: this commit. **Setup commit SHA**: backfilled by the QE at Phase 5.5 / Phase 6 (the `V3_MODELS` edit + `ITERATION_LABEL "v3-097"` + the `test_universe_reselection_v3.py` suite).
- **Walk-forward fidelity**: the Section-2 EDA is walk-forward-faithful per `feedback_v3_eda_walkforward_faithful.md` (Section 2.6) — every IC is measured on the runner's `[first_kline + 24mo, OOS_CUTOFF_MS)` IS span; the /091 full-panel mismatch cannot recur.
