# EXPLORATION-004 — CFTC COT managed-money contrarian SLEEVE (4th sleeve)

**Track:** metals portfolio. **Date:** 2026-06-25. User directive: bold, non-obvious, search internet.
**Verdict:** ✅ **PASS** (Critic) — kept as iter-004. **Strongest sleeve in the book + the first
genuine CONFIRMATION candidate** (deep history, leak-clean, robust). Promotion still requires a
CONFIRMATION/OOS reveal. **OOS hidden.** All numbers IN-SAMPLE only.

## The bold move — break the cost ceiling with NON-PRICE data
iter-003 proved a structural law: at 8h/6bps, fast PRICE anomalies (session, lead-lag) are real but
cost-killed; only low-turnover cross-sectional shape / net-direction survive. So iter-004 went to a
**slow (weekly), non-price, orthogonal** axis: **CFTC Commitment-of-Traders managed-money
positioning** (free, 2006+, all metals). Weekly cadence → low turnover by construction → survives the
cost ceiling. Internet-grounded (the macro real-rates/DXY route was rejected — decoupled since 2022,
an OOS trap).

**Mechanism (metals-native):** Managed Money in COT = the speculative/trend crowd (CTAs, hedge funds).
Net positioning is a CROWDING gauge. Crowded net-long (z high) → exhausted marginal buyer, one
liquidation-cascade from a flush → fade it. Washed-out net-short (z low) → forced-seller supply spent
→ primed to rally. The precious-metals analogue of crypto positioning/funding crowding. **Contrarian,
not momentum** — following the crowd into metals LOSES (V2 momentum −0.47).

## Signal (per-metal directional, contrarian)
`mm_net_oi[c] = (MM_long − MM_short)/Open_Interest`; leak-safe aligned to the 8h grid; causal trailing
`z = clip((mm_net_oi − mean_78)/std_78, ±2.5)`; `raw[c] = (−z / rvol[c])` (FADE, inverse-vol). Added as
a 4th raw sleeve: `gn(anchor) + 0.5·gn(dispersion) + 0.25·gn(ptpd) + γ·gn(cot)` → ONE net_from_raw.
Center: **γ=0.25, z_win=78** (26 weeks). Data: `ingest_cot.py` (cot_reports → data/cot/cot_metals.parquet).

## Results (IS-only)
| Book | IS Sharpe | maxDD | turnover |
|---|---|---|---|
| iter-003 3-sleeve (reference) | +0.537 | −25.8% | 0.0146 |
| **4-sleeve center (γ=0.25)** | **+0.641** | **−23.6%** | 0.0237 |
| Standalone COT sleeve (full-IS) | +0.499 | −51.9% | 0.0596 |

- ΔSharpe **+0.103**, maxDD **improves** +2.2pp. Standalone sleeve corr to book **−0.242** (orthogonal,
  risk-reducing). Per-asset standalone: gold +0.19, silver +0.24, platinum +0.32, **palladium +1.13**.
- **Robustness 12/12 cells** (γ{.15,.20,.25,.30}×zw{52,78,104}) lift SR without worsening maxDD
  (+0.578..+0.665).
- **Deep-history (not thin-n):** gold/silver-ONLY combined lift still **+0.031** — the durable claim
  rests on 10yr of deep history, palladium (+1.13, thin 2022+) is a bonus not a dependency.

## Why this is the strongest result — falsifier NOT tripped
IS half-split (2015–2020.5 vs 2020.5–cutoff): standalone H1 **+0.229** / H2 **+0.818** (same sign,
strengthening — no era-inversion); combined lift H1 **+0.040** / H2 **+0.179** (positive both). Unlike
iter-003's pt-pd (which tripped its falsifier), the COT edge is present in BOTH eras and on deep
gold/silver history.

## Leak check (MANDATORY — the #1 risk for this iteration) — PASS
COT = Tuesday-close, released Friday 15:30 ET. Applied only at `Report_Date + 6 days` (next Monday,
conservative) + ffill; `net_from_raw` adds the candle lag. Three independent proofs:
1. **Dual corruption test** (orchestrator): corrupt all FUTURE COT reports AND all FUTURE prices from
   2022-01 forward → 5760 pre-cutoff candles bit-identical (max diff 0.00e+00).
2. **Peek-earlier**: applying COT 1 week early COLLAPSES standalone Sharpe +0.499 → −1.043 (a leaking
   signal would INFLATE, not destroy — the causal signature).
3. **Audit**: 0 reports applied before knowable across 37,888 candles.
Now permanent regressions: `test_cot_alignment_value_correctness` (the exact which-value mapping, not
just presence) + `test_cot_alignment_future_report_is_past_only`. Foundation **18/18 green**.

## Critic note (PASS — concurs leak-free + CONFIRMATION candidate)
Line-by-line audit of `align_cot_to_grid` confirmed causal; dual-corruption bit-identity decisive.
Selection honest (contrarian sign mechanism-justified ex-ante; 12/12 ridge). Palladium dominance
flagged but headline honest (deep claim = GS-only +0.031). **CONFIRMATION pre-registration conditions**
(NOT exploration blockers):
- **lag_days → 7** (Tue+7d = Tuesday) to make holiday-delayed-release weeks provably airtight (current
  6 is empirically clean; the edge case is narrow/theoretical).
- **DSR/PBO deflation** of the disclosed ~140-config screen (5 families × 7 z_win × 4 clip), N_eff from
  the screen.
- **Per-asset OOS-N + palladium-reliance check** (report combined-vs-GS-only lift in OOS; durable claim
  = GS-only, palladium thin-n bonus).
- Re-run era-split falsifier + 12/12 robustness on OOS (not re-tuned) as the promotion gate.

## Path forward (iter-005 ideas)
1. **Commercial (producer/merchant) confirmation** — already cached (`Prod_Merc_Positions_*`): fade
   MM-crowding only when commercials are positioned opposite the specs ("smart money agrees"). Zero new
   data dependency.
2. **COT change (Δ-positioning) vs level** — second orthogonal sleeve on the weekly CHANGE in MM
   positioning (flow extremity vs level extremity) to distinguish the true edge source.

## Files
- `analysis/portfolio/metals/ingest_cot.py` (CFTC COT fetch+cache), `iter_004_cot.py` (sleeve + 4-sleeve)
- `tests/test_portfolio_metals_foundation.py` (18; +2 COT alignment regressions)
- `pyproject.toml` + `uv.lock` (cot_reports dep). Data cache `data/cot/cot_metals.parquet` (gitignored).
