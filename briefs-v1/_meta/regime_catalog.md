# Regime Catalog — v1 Track

**Status:** BOOTSTRAP /044 — canonical tag definitions locked. Extension stubs NOT enforced.
**Established:** 2026-05-31 per /044 bootstrap artifact authoring mandate.
**Source:** /042 LM Master Phase 7.4 Item 0 (tagger run; q75/q90 from full IS+OOS distribution).
**See also:** `merge_v1_relative_regime_pareto_proposal.md` §B.1, `regime_ensemble_methodology.md`.

---

## 1. Tagger: BTC 90-Day Return + 30-Day Realized Vol Quantile

**Inputs:**
- `btc_ret_90d`: BTC close-to-close return over trailing 90 calendar days.
- `rv30`: 30-day realized vol (annualized), computed as `sqrt(252) × std(daily_log_return, window=30)`.

**Quantile anchors** (computed once from the full IS+OOS distribution, 2022-01 → 2026-05, 53 months):
- `q75(rv30) = 0.584` annualized (i.e., 58.4% annualized vol)
- `q90(rv30) = 0.729` annualized (i.e., 72.9% annualized vol)

These quantiles are LOCKED at /044 bootstrap. They MUST NOT be recomputed per iteration. Future regime catalog revisions require a new version tag.

---

## 2. Canonical Tag Rules (priority order — first match wins)

| Priority | Tag | Condition | Notes |
|---|---|---|---|
| 1 | `vol-spike` | `rv30 ≥ q90` | Overrides all other tags. High-vol extremes dominate regime character. |
| 2 | `bear` | `btc_ret_90d < −10%` | Sustained BTC downtrend. |
| 3 | `recovery` | `btc_ret_90d ∈ [+10%, +20%)` AND preceding ≥1 bear-tagged month | Post-bear retrace. |
| 4 | `bull` | `btc_ret_90d > +20%` AND `rv30 < q75` | Sustained low-vol uptrend. |
| 5 | `chop` | `|btc_ret_90d| ≤ 10%` | Sideways; no directional momentum. |
| 6 | `other` | (catch-all) | Catch-all for months not matching 1–5. Includes moderate-vol moderate-return states. |

**Source commit:** /042 LM Master Phase 7.4 Item 0 confirms these rules and the q75/q90 anchors were applied to produce the regime tables in `reports-v1/iteration_v1-042/` and `reports-v1/iteration_v1-043/`.

---

## 3. Month-Count Summary (53 months, 2022-01 → 2026-05)

From /042 LM Master Phase 7.4 Item 0 regime attribution table:

| Regime | IS months (2022-01 → 2025-03) | OOS months (2025-03 → 2026-05) | Total |
|---|---|---|---|
| bull | 15 | 3 | 18 |
| bear | 9 | 6 | 15 |
| chop | 10 | 4 | 14 |
| vol-spike | 5 | 1 | 6 |
| recovery | 0 | 1 | 1 |
| other | ~0 (catch-all absorbed into above) | ~0 | ~0 |

Note: "other" tag emitted ZERO months from the canonical BTC-only tagger on this window. All 53 months fell into one of bull/bear/chop/vol-spike/recovery. The `other` tag is retained as a structural safety for future data windows where the 5 primary tags do not cover.

---

## 4. Per-Regime Baseline Metrics (single-seed=42, BOOTSTRAP proxy)

From /042 LM Master Phase 7.4 Item 0 — BASELINE_V1 anchor (`v0.v1-baseline-corrected`):

| Regime | IS Sharpe | IS MaxDD | IS trades | OOS Sharpe | OOS MaxDD | OOS trades |
|---|---|---|---|---|---|---|
| bull | +0.09 | ~29% (est) | 229 | −2.02 | 14.4% | 48 |
| bear | −0.23 | ~34% (est) | 142 | +1.62 | 10.8% | 68 |
| chop | −0.27 | ~72% (est) | 175 | +3.55 | 5.0% | 46 |
| vol-spike | +2.77 | ~30% (est) | 75 | 0.0 (1m) | ~14% | 13 |
| recovery | n/a | n/a | n/a | 0.0 (1m) | ~13% | 14 |
| other | — | — | — | — | — | — |

Source: LM Master /042 Item 0 table. MaxDD figures are estimates (not directly in the LM table; per-symbol max_dd from `regime_attribution.csv` schema at /043 shows these regime-level figures).

**sigma_R_proxy (single-seed bootstrap):** Uses the Sharpe-estimation-noise formula `sigma_R_proxy = sqrt((1 + 0.5 × SR²) / n_regime_months)` where SR = baseline IS monthly Sharpe (+0.2829) and n = regime month count. This is a lower-bound noise proxy; the full 10-seed sigma_R will be computed at /046.

| Regime | IS months | sigma_R_proxy (single-seed) | LM Master 10-seed estimate |
|---|---|---|---|
| bull | 15 | 0.263 | ~0.8 |
| bear | 9 | 0.340 | ~0.6 |
| chop | 10 | 0.322 | ~0.7 |
| vol-spike | 5 | 0.456 | ~1.5 |
| recovery | 0 | NaN | UNDEFINED |
| other | 0 | NaN | UNDEFINED |

The single-seed proxy is systematically NARROWER than the LM Master 10-seed estimates (which capture seed-to-seed variance in addition to sampling noise). Pareto-dominance checks using the proxy will be CONSERVATIVE (harder to pass "within sigma" band) relative to the 10-seed version. This is the safe direction at bootstrap.

---

## 5. Extension Stubs (NOT enforced at /044 or until explicitly activated)

These tags are reserved for future tagger revisions. None are active; no iteration uses them until explicitly chartered.

### 5.1 alt-rotation
**Definition stub:** BTC_ret_90d ∈ [−5%, +5%] AND (LINK_ret_90d > +30% OR DOT_ret_90d > +30%).
**Activation trigger:** Two consecutive IS months where BTC is flat and any v1-universe alt is up >30% in 90d.
**Note from /042 LM Master Item 0:** "BTC-only tagger emitted ZERO months in alt-rotation from the canonical rule." Tagger extension requires per-symbol return inputs not currently in `regime_attribution.csv`.

### 5.2 ETF-flow
**Definition stub:** Calendar date window mask: 2024-01-11 (BTC spot ETF launch date) → present. Could be augmented with BTC spot ETF weekly flow data (external data source, not currently integrated).
**Note:** Passive date-window approach (tag all months post-2024-01-11 as ETF-flow-active) is computable from the existing data without external sources. Full version requires CME/Glassnode flow data.

### 5.3 liquidation-cascade
**Definition stub:** `rv30 spike (rv30 > q75)` AND 3-day rolling liquidations > $1B notional AND `btc_ret_3d < −8%`.
**Note from /042 LM Master Item 0:** Placeholder; requires liquidation-notional data feed not currently fetched. `vol-spike` tag (priority 1) already catches the vol component; cascade adds the liquidation-notional gating layer.

---

## 6. Update Policy

1. Quantile anchors (`q75=0.584`, `q90=0.729`) LOCKED at /044 bootstrap. Change requires new version + PR.
2. New tag families (5.1–5.3) require:
   - QR brief Section 10 charter for the new tag.
   - Committed `analysis/iteration_v1-NNN/tag_family_validation.py` showing month-count + IS coverage.
   - LM Master Phase 4.5 sign-off that the new tag does not overlap with existing tags by > 20% of months.
3. `baseline_seed_regime_matrix.csv` and `baseline_metric_anchors.csv` MUST be regenerated after any tag-definition change that reassigns ≥1 IS month.
