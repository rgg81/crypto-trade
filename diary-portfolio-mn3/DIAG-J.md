# DIAG-J — funding term-dynamics: DEAD (all three kill criteria fired; folds into family I)

**Date:** 2026-07-11. **Role:** QR. **Family:** J (funding term-dynamics — the funding SURFACE
as signal). **Spec:** PLAN §3.4, FROZEN pre-registration, executed verbatim — nothing tuned,
nothing salvaged. **Script:** `analysis/portfolio/mn3_diag_j.py` (helpers unit-tested in
`tests/test_mn3_diag_j.py`, 15 tests). **Run:** IS-only, `mn3_guard_grid` called before any
metric; panel T=4,929 (2020-01-01 → 2024-06-30), C=747; no token, no holdout, no Stage-3 data.

## 0. Pre-registered header (restated from PLAN §3.4 — the frozen spec)

- **Signal:** per-name funding-momentum ΔL[t] = (9c-mean funding at t) − (9c-mean funding at
  t−L), L ∈ {9, 21, 63}; 9c-mean = trailing mean of the raw 8h bucket-sum funding rate, min 5/9
  finite (inherited DIAG-A min-obs convention, disclosed design DOF). Cross-sectional rank.
- **Level signal (the control):** 9c-mean funding at t — family I's signal core.
- **Forward return:** 3-candle residual TOTAL return, fwd3[t] = Σ_{j=1..3}(resid[t+j] −
  fund[t+j]); resid via `mn_beta.rolling_beta` frozen defaults at the [k−1] lag; all 3 candles
  finite required; sum-not-compound (per-candle engine accounting).
- **Cells:** exactly **6 registered** = 3 L × {RAW, LEVEL-CONTROLLED}. Level-controlled =
  per-candle cross-sectional rank-regression (OLS with intercept) of rank(momentum) on
  rank(level); IC of the residual. Bucket/IS-half splits are report AXES of the same cells.
- **Universe:** PIT top-40, trailing 30c mean $-volume, ex-stables, ≥270c history; min 20 valid
  members per scored candle. Buckets at the DECISION candle (frozen mn3_regimes rules). IS
  halves: H1 = decision open < 2022-04-01; H2 = rest of IS.
- **Best lc cell:** decile-extreme L/S book on the lc residual signal at rebal ∈ {3, 21}, full
  phase sweep (3 / 21 phases; phase-agnostic mean = headline), costs 7.5 bps/side on Σ|dw| +
  funding inside the return stream; 2×-cost twin. Direction = measured full-IS lc-IC sign
  (single disclosed DOF; the PLAN mechanism predicted NEGATIVE/fade — and negative it was).
- **BANNED and not touched:** aggregate funding-momentum as a standalone timing overlay.
  Nothing in the script computes an aggregate timing signal — cross-sectional form only.
- **Kill criteria (frozen):** (a) no L with lc |IC| ≥ 0.015 sign-stable across IS halves;
  (b) best cell fails 2×-cost coverage at BOTH rebal 3 and 21; (c) lc IC < 50% of raw IC at
  EVERY L → fold into family I, no J token spent.

**Contamination note (PLAN §1.3 row, reproduced):** *"J funding term-dynamics — W1: funding
AUTOCORRELATION/half-life stats (DIAG-A lags 1–90) measured here; W2: same; W3: funding-LEVEL
book revealed (family I's, not J's). Mildly contaminated. Persistence summary stats are known
over W1–W2; the funding-MOMENTUM cross-sectional IC — J's object — was never measured
anywhere."* This run measured that object for the first time, on the new IS only.

**Multiple-testing ledger (family J):** opened at 6, used 6, cap 12, **no amendment used.
Ledger closes at 6.**

## 1. Data hygiene (mn3_datacheck pattern — run FIRST)

- Panel health: BTC grid OK (T=7,149 contiguous), MN3 IS extent covered; DEGRADED verdict is
  live-feed staleness only (post-fetch freshest candle) — irrelevant to an IS-only probe.
- Regime occupancy on IS: CRASH 13.2% / MANIA 18.8% / CHOP 68.0% — sanity check PASSED.
- Universe: mean 35.5 members/candle, 232 ever-members; first member candle 2020-04-02 (the
  270c history filter — grid starts exactly 2020-01-01, so COVID predates the scored window;
  effective first scored candle **2020-05-16**, median n_used = 40).
- **Funding coverage (silent-zero guard):** 745/747 panel symbols resolve directly; 1 top-40
  ever-member lacks funding data (**LITUSDT**, excluded from the sort — cannot be ranked);
  per-candle member funding coverage **mean 99.8%, min 97.5%** over 4,651 live candles.
  Signal definedness: 37.5 of 37.6 live members carry a defined ΔL at every L. **Coverage is
  NOT materially broken — the reads below are on solid data.**

## 2. The 6 registered cells (per-candle Spearman IC vs fwd3; n = 4,518 scored candles)

Plain t reported; fwd3 windows overlap (3c horizon) so conservative t/√3 in parentheses.

| Cell | IC (full IS) | t (t/√3) | H1 | H2 | CRASH | MANIA | CHOP | \|lc\|/\|raw\| |
|---|---|---|---|---|---|---|---|---|
| L=9 RAW | **−0.0127** | −4.44 (−2.56) | −0.0201 | −0.0066 | −0.0085 | −0.0212 | −0.0113 | — |
| L=9 LC | +0.0004 | +0.15 (+0.09) | +0.0000 | +0.0008 | +0.0004 | −0.0027 | +0.0012 | **0.03** |
| L=21 RAW | **−0.0180** | −6.23 (−3.60) | −0.0417 | +0.0018 | −0.0077 | −0.0305 | −0.0165 | — |
| L=21 LC | −0.0057 | −2.02 (−1.17) | −0.0222 | +0.0081 | −0.0121 | −0.0161 | −0.0018 | **0.31** |
| L=63 RAW | **−0.0107** | −3.74 (−2.16) | −0.0312 | +0.0063 | +0.0006 | −0.0286 | −0.0081 | — |
| L=63 LC | −0.0000 | −0.00 (−0.00) | −0.0105 | +0.0088 | +0.0017 | −0.0126 | +0.0030 | **0.00** |

(H1 n=2,055; H2 n=2,463; CRASH n=548; MANIA n=820; CHOP n=3,150 per cell.)

## 3. Kill scoring (mechanical)

**(a) — FIRED.** L=9: sign-stable but |IC_lc| = 0.0004 ≪ 0.015. L=21: |IC_lc| = 0.0057 < 0.015
AND sign flips (H1 −0.0222 → H2 +0.0081). L=63: |IC_lc| = 0.0000, sign flips. No L passes.
Scored under the natural reading (full-IS |IC| ≥ bar AND same sign in both halves); the strict
reading (both halves ≥ bar in magnitude, same sign) also fails at every L — **the verdict is
reading-invariant**, no boundary ambiguity.

**(b) — FIRED.** Best lc cell = L=21 (|IC| = 0.0057); direction = fade (long low ΔL), the
measured sign = the mechanism-predicted sign. Decile-extreme book (k=4 per leg at n=40):

| Cadence | gross_ann | net_ann | **NET2X_ann** | turnover_ann | phases net2x>0 |
|---|---|---|---|---|---|
| rebal 3 (3 phases) | +17.5% | −33.3% | **−84.0%** | 676.6× | 0/3 |
| rebal 21 (21 phases) | −12.8% | −27.1% | **−41.4%** | 190.6× | 4/21 |

Full 21-phase NET2X distribution (rebal 21): −49% −92% −84% −111% −93% −96% −109% −75% −47%
−20% +6% −0% −26% −32% −28% +19% +10% +49% −50% −35% −6%. Phase-agnostic mean −41.4% is the
headline; the +49% best phase is the same phase-lottery artifact the track's rebal-phase rule
exists to kill. Fails 2×-cost coverage at BOTH cadences.

**(c) — FIRED.** |IC_lc|/|IC_raw| = 0.03 (L=9), 0.31 (L=21), 0.00 (L=63) — all < 50%.
**It's all the level.** Per the frozen consequence: J folds into family I; **no J token is
spent and none becomes available by rebranding** (PLAN §6.1).

## 4. Leak checks (proportionate battery — all PASS)

- **Corrupt-future (both signal legs + lc residual):** corrupting funding rows ≥ t0 leaves m9,
  every ΔL, and the lc residual signal rows < t0 bit-identical — PASS.
- **Decision-lag:** perturbing candle t0's residual return moves fwd3 at decision rows
  {t0−3, t0−2, t0−1} ONLY; fwd3[t0] untouched (candle t never sees its own forward window) —
  PASS.
- **Injected-leak positive control:** feeding fwd3 itself as the signal drives measured IC to
  +1.000 — the harness CAN detect leakage; the near-zero lc ICs above are not an alignment
  artifact — PASS.

## 5. VERDICT — **DEAD** (criteria a + b + c ALL fired)

**Family J is dead as a separate family; disposal = fold into family I** (kill c's
pre-registered consequence). The cross-sectional funding-momentum IC — measured for the first
time anywhere — is real in RAW form (L=21 raw IC −0.0180, conservative t −3.60, fade
direction exactly as the §3.4 mechanism predicted) **but it is the funding LEVEL in disguise**:
rank-regressing out the 9c-mean level removes 69–100% of it at every L. There is no funding
term-dynamics edge orthogonal to carry on this IS.

**Honest findings banked (no salvage, just the record):**
1. The raw momentum effect is H1-concentrated (L=21: H1 −0.0417 → H2 +0.0018) — even the
   level-in-disguise component decayed across the IS. Anything that re-derives from it should
   expect the H2 number, not the H1 one.
2. MANIA carries the strongest raw IC at every L (−0.021/−0.031/−0.029) — consistent with the
   funding-ramp-marks-late-leverage story, but again: it's the level's mania signature.
3. The lc residual signal churns brutally (677×/191× ann turnover) with near-zero IC — a
   rank-residual of two correlated rankings is mostly noise trading.
4. Implication for family G (recorded, not acted on): G's pre-registered features
   `fund_mom21_xz`/`fund_mom63_xz` should be expected to add ~nothing beyond `fund_lvl_xz`
   univariately; if they matter in DIAG-G it will be through interactions. No change to G's
   frozen feature list — this is an expectation, and G's own kill criteria arbitrate.

**Proposal written down instead of run (budget discipline — NOT a registered cell):** a
falling-FROM-EXTREME conditioner (momentum conditioned on |level| percentile — "unwind of a
crowded print" rather than unconditional ΔL) is the one variant the mechanism text names that
the 6 cells don't isolate. It would need a PLAN-AMENDMENT (+cells within the ≤12 cap) under
family J's closed mechanism — and given (c) fired at every L and the raw effect is
H1-decaying, my own recommendation is AGAINST spending it. Recorded for completeness.

**Track state:** DIAG-J complete (PLAN §4 order-2). Next per the frozen order: DIAG-H (order-3,
gates open). Family ledgers: G:8, H:4, I:11, ~~J:6~~ (closed at 6, dead), K:1.

## 6. Artifacts

- Script: `analysis/portfolio/mn3_diag_j.py` (frozen constants at top; guard-first; verdict
  mechanical). Reproduce: `uv run python analysis/portfolio/mn3_diag_j.py`.
- Tests: `tests/test_mn3_diag_j.py` — 15 synthetic tests (min-obs semantics, past-only
  corrupt-future on both legs + lc signal, residual⊥level orthogonality, collinear degeneracy
  returns NaN-not-fabrication, exact t+1..t+3 window, all-3-finite, funding-in-total, injected
  leak control, thin cross-section, book decision-lag/costs/direction-mirror). Full mn3 subset
  79/79 green; ruff clean on both files.
- Run log: deterministic single pass; verdict banner `FAMILY J: DEAD (kill criterion fired)`.
- Token ledger: `REVEAL-LEDGER.md` untouched (no spends; kill (c) forecloses a J token forever).

*— QR, MN3 track. Pre-registered, run once, scored mechanically, killed by its own frozen bars.
An honest fail: the funding surface's first derivative is the level wearing a costume. The
holdout remains untouched.*
