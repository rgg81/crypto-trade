# Research Brief — iter-v1/023 (BTCUSDT) — Phases 1-2 (target/strategy design, IS-ONLY)

**Author:** Quant Researcher (crypto-markets). **Symbol:** BTCUSDT. **Interval:** 8h (sacred).
**Scope:** Phase 1-2 — redesign the model's role from DIRECTIONAL to volatility-MAGNITUDE-driven
selection/sizing, keeping the deterministic 200-SMA trend-state direction. IS-ONLY.
**Objective:** SHARPE via GENERALIZATION (both-positive first, then OOS; never overfit OOS).

## VERDICT: HONEST NULL — magnitude is a stable SIZE signal but does NOT rescue OOS robustness, because the binding constraint is the deterministic DIRECTION and magnitude selection picks the WRONG candles in the recent (OOS-proxy) regime.

The proposed pivot — keep the deterministic trend-state direction, replace the conviction gate +
directional model with a volatility-MAGNITUDE-driven entry selection/sizing — was tested rigorously,
IS-only, across three committed scripts. **Every angle converges on a null.** I recommend NOT
implementing this axis. The campaign's untried lever turns out to be a SIZE signal that cannot
improve the SELECTION of the deterministic direction in the regime that pre-prints OOS.

This null is EARNED (three backtested IS-only experiments), not declared. It is the valid
"magnitude is stable but doesn't rescue OOS robustness because direction is still the binding
constraint" outcome the task pre-registered as acceptable. It prevents a guaranteed K=5→K=20
wasted-compute cycle.

---

## All numbers from committed IS-only scripts (cutoff-asserted, past-only)
- `analysis/BTCUSDT/iteration_v1-023/magnitude_selected_book.py` → `magnitude_selected_book.csv`
- `analysis/BTCUSDT/iteration_v1-023/magnitude_vs_direction_correctness.py` → `magnitude_vs_direction_correctness.csv`
- `analysis/BTCUSDT/iteration_v1-023/seed_stability_magnitude.py` → `seed_stability_magnitude.csv`

Each hard-filters `open_time < OOS_CUTOFF_MS = 1742774400000` (2025-03-24) and asserts
`df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward quantity. Forward log-return computed AFTER
the IS filter (tail NaN-masked — no OOS candle in frame). SMA200/ATR14/vol-state all `.shift(1)`
past-only; per-sub-period selection quantiles trained on PAST rows only (purged by N_LABEL=42). OOS
rows never read. `src/`, runner, OOS UNTOUCHED. IS window 2020-01..2025-03, 5727 8h candles,
11 ~6-month sub-periods. RT cost 0.14% (fee 0.1% + 2bps/side slippage). Deployed label = fixed_horizon
N=42 (14d), the iter-020 baseline label.

---

## The hypothesis (precise, as tasked)
1. KEEP the deterministic 200-SMA trend-state direction (`+1 if close[t-1] > SMA200[t-1] else -1`).
2. Replace the conviction gate + directional LightGBM with a volatility-MAGNITUDE role: predict the
   |move| magnitude (the FE iter-014 stable signal, IC vs |fwd| up to +0.22) and use it to SELECT
   and/or SIZE the trend-state entries.
3. Claim to test: the magnitude-driven book is (a) MORE sub-period-stable than the directional
   iter-020 book, and (b) LESS seed-dependent — the property that would let it survive K=20.

I implemented the magnitude SELECTION as a deterministic past-only composite vol-state quantile gate
(`vol_natr_7`, `vol_garman_klass_20`, `vol_parkinson_20`, `vol_bb_bandwidth_30` — the FE cluster-17
stable family — expanding-rank composite, past-only), head-to-head vs the iter-020 strength gate
(`|close-SMA200|/ATR ≥ q40`). Both ride the same deterministic direction; both are model-free for
selection. I also tested a magnitude-SIZED variant and the A∩B / A∪B combinations.

---

## Why it's a NULL — three decisive IS-only findings

### (1) The magnitude-gated book INVERTS in the most-recent IS sub-periods — the OOS-fragility fingerprint
`magnitude_selected_book.py`. Per-sub-period net annualized Sharpe of the trend-state book under each
deterministic selection rule (last 3 cols = the recent IS sub-periods that pre-print OOS, per
iter-011):

| selection rule | full | frac_pos | disp | **recent3** | trades | WR |
|---|---:|:--:|---:|---:|---:|---:|
| **A = iter-020 strength gate q40 (incumbent)** | +1.00 | **0.70** | 2.18 | **+1.86** | 2755 | 0.547 |
| B = magnitude gate q40 | +0.72 | 0.50 | 2.35 | **−0.73** | 2504 | 0.539 |
| B = magnitude gate q50 | +0.87 | 0.50 | 2.34 | **−0.63** | 1942 | 0.552 |
| B = magnitude gate q60 | +1.41 | 0.50 | 2.66 | **−0.55** | 1430 | 0.589 |
| B magnitude q50 SIZED by mag | +0.99 | 0.50 | 2.32 | **−0.58** | 1942 | 0.552 |
| A∩B (strength & magnitude) | +1.53 | 0.80 | 3.85 | +0.88 | 1129 | 0.613 |
| A∪B (strength \| magnitude) | +0.77 | 0.60 | 1.71 | +0.21 | 3568 | 0.529 |

Per-sub-period detail (the tell — recent 3 sub-periods 23-12 / 24-06 / 24-12):
- A (strength): … +1.20, +1.21, **+3.19** → recent3 **+1.86**.
- B (magnitude q50): … −0.59, −0.80, **−0.49** → recent3 **−0.63**.

**Every magnitude-gate variant is NEGATIVE in recent3** while the incumbent strength gate is strongly
positive. The magnitude signal selects candles that were profitable in 2020-2023 but turn the
trend-state book NEGATIVE in the most-recent IS regime — i.e. it would generalize WORSE, not better.
A∩B's headline +1.53 is the strength gate doing the work (it inherits A's recent3 = +0.88 but at
3.85 dispersion); the magnitude filter only shrinks the count.

### (2) MECHANISM — magnitude is a SIZE signal, NOT a direction-SELECTION signal, and selection-IC inverts recently
`magnitude_vs_direction_correctness.py`. Full-IS and per-sub-period univariate IC:

| series (univariate IC) | full-IS | frac_same_sign | recent2 (24-06, 24-12) |
|---|---:|:--:|---|
| IC(vol_state, **\|fwd move\|**) — SIZE | +0.079 | 0.364 | −0.14, **−0.42** |
| IC(vol_state, **trend-state PnL**) — SELECTION | +0.137 | 0.545 | −0.21, **−0.45** |
| IC(strength, trend-state PnL) — CONTROL | +0.094 | **0.636** | +0.18, **+0.05** |
| IC(strength, \|fwd move\|) | −0.059 | 0.273 | +0.04, −0.16 |

- The vol-state's SELECTION IC (+0.137 full) looks better than the strength control (+0.094) ON
  AVERAGE — but that average is the overfit trap. It INVERTS to **−0.21 / −0.45** in the two most-recent
  IS sub-periods, while the strength control stays POSITIVE (+0.18 / +0.05). This is exactly the
  iter-011 fragility fingerprint, now from the magnitude side.
- The FE's stable +0.22 was at the N=9 (3d) horizon; at the DEPLOYED N=42 (14d) horizon the |move| IC
  drops to +0.079 AND its sign-stability collapses to frac_same_sign 0.364 (recent 5 sub-periods all
  negative). The magnitude signal that is sub-period-stable at 3d is NOT sub-period-stable at the 14d
  let-winners-run horizon the strategy actually trades.
- Full-IS median split looks deceptively viable (vol-state high-half WR Δ +0.083 / PnL Δ +2.22% vs
  strength's +0.085 / +2.90%) — but the recency inversion above is what kills it OOS.

**Mechanistic reason (crypto-native):** high coming-volatility on BTC 8h CLUSTERS in
corrections/liquidation-chop, where the deterministic trend-state direction gets whipsawed. The
strength gate (distance from SMA200 in ATR units) specifically selects STRONG-TREND candles where the
direction has edge; the magnitude gate selects BIG-MOVE candles regardless of whether the trend-state
is right — and in the 2024-25 regime, the big moves went AGAINST the trend-state.

### (3) The seed-stability premise is moot, AND the incremental rows are net-toxic
`seed_stability_magnitude.py`.
- **Seed-stability (the survival premise):** bootstrap-seed Jaccard of the selected-row set —
  magnitude selector 0.817 vs direction selector 0.844 (Δ **−0.028**). Magnitude selection is NOT more
  seed-stable than direction selection. More fundamentally, the DEPLOYABLE magnitude rule is a
  deterministic past-only quantile (Jaccard 1.0), exactly like the iter-020 strength gate. **The K=20
  lottery (iter-016/021/022) never lived in SELECTION — both iter-020 selection rules are already
  deterministic; it lived in the MODEL doing timing/sizing on selected rows.** So "magnitude selection
  survives K=20 because it's less seed-dependent" is vacuous: it sits on the same deterministic footing
  iter-020 already has, and adds no seed-stability the incumbent lacks.
- **Incremental (only-B rows):** the rows the magnitude gate selects that the strength gate does NOT
  have recent3 = **−2.175**, frac_pos 0.40, WR 0.467, full +0.087. Magnitude adds WORSE trades —
  precisely the recent-regime corrections. only-A (strength only) rows: recent3 **+3.44**, frac_pos
  0.60. The magnitude gate cannot add a single tradeable, recent-stable row beyond the strength gate.

---

## Conclusion: the binding constraint is DIRECTION, which magnitude selection cannot improve
The task pre-registered this exact null: "magnitude predicts size but you still need direction, and
the direction re-introduces the lottery." More precisely here: the direction is DETERMINISTIC (no
lottery), but it is the binding edge constraint — its correctness inverts in the recent regime, and
the magnitude state does NOT predict that correctness (it inverts the same way). Sizing/selecting by
magnitude amplifies the wrong-direction high-vol trades exactly when the direction fails. The FE
iter-014 flag — magnitude is the only sub-period-stable signal — is true for |move| SIZE at the short
horizon, but it is INERT (worse: counter-productive) for improving the SELECTION of a 14d
deterministic-direction book in the OOS-proxy regime.

**iter-020 (strength gate, IS +0.37 / OOS +0.09) remains the robust BTC ceiling of the
trend-following approach.** Magnitude does not thicken or robustify it.

---

## Pre-registered FALSIFIER (this NULL is overturned only if)
1. A backtest of the **B (magnitude gate q50) or A∪B** book at K=20 produces a most-recent-IS-sub-period
   Sharpe ≥ the incumbent strength gate's +3.19 (24-12) AND OOS Sharpe > 0 AND ≥ iter-020's +0.09 —
   i.e. the deterministic-book stability ranking is contradicted by the real bagged specialist.
   I predict it will not: the recency inversion is data-deterministic (no model, no seed) and the
   only-B rows are net-negative recent3 = −2.175.
2. OR a magnitude target at the **N=9 (3d) horizon** (where IC_|fwd| is +0.22 and sign-stable) is shown
   to produce a recent-sub-period-positive direction-SELECTION IC — but the campaign already
   established short holds (iter-009/010) overfit, so this re-opens a closed door.

If neither fires, the volatility-magnitude axis is FALSIFIED for the BTC 8h 14d trend-following book.

## Recommended next axes (NOT magnitude; from families not yet exhausted)
1. **Crypto-native EXOGENOUS regime conditioning of the DIRECTION** (not selection/sizing): the binding
   constraint is direction-correctness in the recent regime. A deterministic regime gate that turns the
   trend-state book OFF in high-funding-stress / high-realized-vol-state regimes (where direction
   whipsaws) — a binary kill switch, not a magnitude sizer. This attacks the actual constraint. Must be
   IS-sub-period-stable + deterministic (no model timing).
2. **Accept iter-020 as the robust BTC baseline** (thin OOS is intrinsic to the let-winners-run
   trend-follower; three axes now confirm OOS-thickening hits the lottery/regime wall) and extend the
   deterministic trend-state + strength-gate stack to the other coins (user: "work with others soon").
   The mechanism may generalize better on a coin whose recent regime is less correction-dominated.

## Risk note
No merge candidate proposed (NULL), so no Risk Mitigation section is required this iteration. If the
falsifier-1 backtest is run despite the prediction, it inherits iter-020's risk stack (R2 brake / R3
OOD / R5 vol-target) unchanged — but I do NOT recommend spending the compute.
