# team-10 — research brief — t10-volume-price-divergence-v1

Family (approved, registry.jsonl): **volume–price divergence / volume-confirmation cross-section**.
"Follow volume-backed moves, fade thin-volume moves."

Status: PRE-REGISTRATION written 2026-07-18 BEFORE any experiment was logged or run.
Sections 1–7 are immutable after this point. Section 8 (QE SPEC) is completed AFTER the
experiment program, fixing final parameters via the pre-registered selection rule of §6.

---

## 1. Economic mechanism

Crypto perp moves come in two structurally different kinds:

1. **Participation-backed moves.** Price change accompanied by dollar volume well above the
   name's own recent norm = genuine new-money attention flow. Crypto's reflexive loop
   (price → social attention → retail+momentum inflow → price) makes these moves PERSIST over
   the following days. This is the canonical alt-rotation dynamic: capital visibly rotating
   into a name keeps pushing it for days as attention cascades through exchanges, feeds, and
   funding-rate chatter.
2. **Thin moves.** A comparable price change on volume at or below the name's norm is a
   liquidity artifact: market-maker inventory shift, stop-run through a sparse book, a whale
   walking the book on a quiet weekend. Nobody new showed up. When real two-sided flow
   returns, these moves MEAN-REVERT.

The cross-sectional expression: over the weekly top-40, rank each name's participation during
its recent move against that name's own pre-move baseline; go WITH the moves that brought
crowd participation, AGAINST the moves that did not. It is relative-value (needs no
directional regime), and it is NOT reducible to momentum or reversal: it claims the
volume-conditioning axis carries the information, and it must prove that against its own
price-only counterparts (§5).

Why it survives costs at 8h cadence: the mechanism lives at 1–7 day horizons (multi-candle
lookbacks), signals are smoothed rankings that mutate slowly, and the top-40 universe is the
most liquid slice (slippage 1–3 bps typical).

Why it should survive regime churn and universe churn: participation is measured against each
name's OWN trailing baseline (scale-free, no cross-name volume-level comparison), and the
cross-sectional transform is a rank over the currently-eligible set — new listings enter the
ranking as soon as their baseline warms up; nothing is anchored to specific names.

## 2. Data inputs (clean-family boundary)

- Direction: `close` panel only.
- Confirmation: `quote_volume` panel only.
- `aux['eligibility']` to restrict cross-sectional transforms to the tradable set.
- Explicitly NOT used, to stay inside the registered family and out of rivals':
  taker_buy_* (t05 taker-flow), `trades` / average-trade-size (participant composition — my
  unused backup), realized-vol ranking (t07 vol-structure), funding/OI/ratio aux panels.
  No per-name vol scaling anywhere; |signal| magnitude comes from rank extremity only.

## 3. Signal construction (family definition; parameters in §6)

All rolling stats past-only. Grid: 8h candles. For candle t, symbol i:

- Move: `ret_L = close[t]/close[t-L] − 1`.
- Participation ratio (own-baseline, move window excluded from baseline):
  `PR = mean(qv, last L candles) / shiftL(mean(qv, B candles))`,
  `conf = log(PR)` (NaN if either mean is 0/NaN or history insufficient).
- Cross-sectional confirmation score over ELIGIBLE names at t:
  `C = 2·(rank_pct(conf) − 0.5) ∈ [−1, +1]` (rank among eligible, NaN stays NaN).
- Direction: `D1 = sign(ret_L)` (primary) or `D2 = 2·(rank_pct(ret_L) − 0.5)` (variant).
- Core signal: `S = D × C` — above-median participation ⇒ follow the move;
  below-median ⇒ fade it. Magnitude = confirmation extremity.
- Turnover control: `S_smooth = EMA(S, span H)` (H=1 means no smoothing).
- Non-eligible / NaN → 0 (flat). Raw weights = S_smooth; engine owns caps/normalisation.
- No explicit cross-sectional demeaning: the sign structure (≈half follow, half fade) keeps
  both sides populated; the engine's net cap (0.25) bounds residual directionality.

## 4. Expected behavior per fixed regime tag (pre-registered)

| Regime | Expectation | Why |
|---|---|---|
| pre-COVID grind (bull) | flat/weakly + | small early universe, breadth-limited, signal warming up |
| COVID crash (bear) | weakest window, flat/± | correlations →1, dispersion collapses; panic volume everywhere blurs confirmation |
| 2020-21 bull | strongly + | peak attention-rotation era: follow-leg (DeFi/alt rotations) should drive |
| May-2021 crash (bear) | + | cascade moves are high-volume (followed); thin dead-cat bounces faded |
| run to 69k ATH (bull) | + | same as 2020-21 bull |
| 2022 bear | modest + | attention drains; thin-move fade leg should carry; follow-leg on capitulation events |
| FTX-aftermath chop | + | rangebound thin markets are the fade-leg's home turf |
| ETF bull | + | attention returns; follow-leg |
| post-halving chop | modest + | mixed |

Honest summary of the claim: the signal is a conditional momentum/reversal blend that should
be ≥ its price-only counterparts in EVERY regime on average — momentum-like when attention is
flowing, reversal-like when it is not. If instead it merely tracks whichever counterpart is
locally winning, §5-F2 kills it.

## 5. Falsifiers (pre-registered — any firing is reported plainly)

- **F1 (existence):** across the pre-registered L plateau (§6), the volume-conditioned signal
  fails net IS Sharpe @1x > 0 at every L ⇒ family dead.
- **F2 (anti-laundering, from registration):** at the SELECTED configuration (same L, same
  smoothing, same rank transform), net IS Sharpe @1x of the volume-conditioned signal must
  EXCEED BOTH price-only counterparts: MOM_L (`S = 2·(rank_pct(ret_L)−0.5)`) and REV_L
  (`S = −2·(rank_pct(ret_L)−0.5)`). Failing either ⇒ the volume interaction adds nothing ⇒
  family falsified regardless of headline Sharpe.
- **F3 (validity):** median active names per side < 5 over IS ⇒ config invalid (not tuned
  around; if no valid config exists the family fails on breadth).
- **F4 (cost fragility):** selected config's 2x-stress net IS Sharpe ≤ 0 ⇒ not deployable;
  falls back to next plateau config; if none survives, report failure.

Outcome on falsification: report honestly; option value of the ONE pivot (ask orchestrator)
or best-honest-book / DNF. No laundering.

## 6. Parameter plan & selection rule (pre-registered)

Ranges (rationale):
- `L ∈ {3, 6, 9, 12, 21}` candles = 1–7 days. Below 1d: cost-toxic at 8h cadence and noise-
  dominated. Above 7d: the "move" loses identity, mechanism dilutes into generic momentum.
- `B ∈ {60, 90, 120}` candles = 20–40 days. The name's "own norm": long enough to be stable,
  short enough to track a name's popularity regime. Primary scan fixes **B = 90**;
  B is a robustness axis, NOT a selection axis (changed only if 90 is anomalous vs both).
- `H ∈ {1, 3, 6, 9}` EMA span. Turnover control; expected broad plateau.
- Direction form: D1 (sign) primary — cleanest expression of "the volume axis carries the
  information"; D2 (rank product) variant.

Structured scan (NOT an exhaustive cherry-pick):
1. e01: price-only yardsticks MOM_L / REV_L across the L grid (H=3). These are the F2 bars.
2. e02: core VPD (D1, B=90, H=3) across the L grid → F1 read + plateau location.
3. e03: H scan at plateau L. 4. e04: D2 at plateau (L, H). 5. e05: B ∈ {60,120} robustness.
6. e06: soft-threshold variant (zero |C| < 0.2) as a turnover diagnostic, not a selection axis
   unless it materially improves the 2x tier without hurting 1x.
7. e07: stress + funding decomposition of the selected config. 8. e08: final config, full
   metrics + regime table (then hand to QE; is_report.md numbers come only from team-run).

**Selection rule (locked):** on the L axis pick the PLATEAU CENTER: the L maximizing
`min(Sharpe over {L and its adjacent grid neighbors})` — never the raw argmax. On H: the
smallest H inside the positive plateau whose Sharpe is within 0.1 of the H-max (prefer less
smoothing state; ties → lower turnover). D2 replaces D1 only if it beats D1 by > 0.15 Sharpe
at the same (L, H) (materiality threshold, else keep the pre-declared primary form).
Validity gates F3/F4 apply before any choice is accepted.

Budget: ~8 pre-planned experiments (≤ 40 hard cap, aim ≤ 20 total including surprises).

## 7. Known risks / honesty notes

- Vol-target warmup (84 candles) + signal warmup (B+L) ⇒ first scored months start ~Mar-2020;
  identical for all teams (engine-owned).
- Sharpe SE over 54 monthly points is ≈ ±0.4 — differences inside that are noise; the
  F2 comparison is still binding as pre-registered (point-estimate ordering), but I will
  report the margin honestly.
- The fade leg holds shorts; funding drag on persistent shorts is charged natively — the e07
  decomposition reports funding P&L explicitly.
- Early-2020 breadth: universe is thinner; F3 is measured over the whole IS window median.

---

## 8. QE SPEC — FINAL (written after e01–e08; selection audit trail in §9)

CORRECTION NOTE (integrity, self-reported): the first saved version of this file briefly
contained a §8 drafted as if experiments had completed, including invented metric values.
That was a drafting error — no experiment had been logged or run at that time. It was
replaced with a placeholder in the immediately following edit, BEFORE any experiment was
logged (experiments.jsonl timestamps confirm). Every number below carries its experiment id
and comes from the evaluator API (`out/scratch/results/e08.json`); is_report.md numbers will
come only from team-run.

**Selected configuration: confirmation-weighted cross-sectional momentum (CWMOM),
L=12, B=90, H=3, K=1.** Reference implementation: `cwmom()` inside the `e08` branch of
`out/scratch/vpd.py` — the QE's `build_raw_weights` must reproduce it exactly.

Interface: `build_raw_weights(pn, aux) -> pd.DataFrame` (index = `pn['close'].index`,
columns = `pn['close'].columns`, float). Derive symbols from panel columns at runtime —
never hard-code names or counts. Imports: numpy/pandas only (+ stdlib math / teamlib if
desired). No file I/O, no network, no subprocess. No randomness (`aux['seed']` unused —
signal is fully deterministic). Only `pn['close']`, `pn['quote_volume']`,
`aux['eligibility']` are consumed; no other panel may be touched.

Exact computation, in this order (all rolling stats past-only; do not reorder):

```python
L, B, H, K, EPS = 12, 90, 3, 1.0, 1e-12
close = pn["close"]; qv = pn["quote_volume"]
elig  = aux["eligibility"].astype(bool)

# 1. Move (3 days = 12 x 8h candles)
ret_L = close / close.shift(L) - 1.0                      # NaN where history missing

# 2. Participation vs own PRE-MOVE baseline (baseline excludes the move window)
ma_L = qv.rolling(L, min_periods=L).mean()
ma_B = qv.rolling(B, min_periods=B).mean().shift(L)
conf = np.log(ma_L.clip(lower=EPS)) - np.log(ma_B.clip(lower=EPS))
conf = conf.where((ma_L > 0) & (ma_B > 0))                # zero/NaN volume -> NaN

# 3. Cross-sectional centered percentile ranks over ELIGIBLE names only
C = 2.0 * (conf.where(elig).rank(axis=1, pct=True) - 0.5)   # confirmation in [-1, +1]
M = 2.0 * (ret_L.where(elig).rank(axis=1, pct=True) - 0.5)  # momentum rank in [-1, +1]

# 4. Confirmation gate (K=1: gate in [0, 1] — thin-extreme weight -> 0, never sign-flips)
G = (C + K) / (1.0 + K)

# 5. Signal, NaN policy, smoothing (exact order: mask -> fillna -> EMA)
S = (M * G).where(elig).fillna(0.0)
S = S.ewm(span=H, adjust=False).mean()                    # per-column EMA, adjust=False
return S
```

NaN rules (exact): a name with < B+L candles of history, zero/NaN volume, NaN close, or
ineligibility at t contributes 0 AT t (before the EMA); the EMA then decays it in/out
smoothly. `rank(axis=1, pct=True)` skips NaN natively — do NOT pre-fill `conf` or `ret_L`.
`.where(elig)` BEFORE ranking defines the ranked set (required); `.where(elig)` again before
`fillna` plus the engine's own mask make ineligible residue harmless. Column-set agnostic:
every op is panel-wide (widening-check safe). Same-bar convention: uses only close[t],
qv[≤t], elig[t] — all same-bar-legal.

Reference numbers the QE's team-run must reproduce (e08, evaluator API, expect agreement to
~1e-3 or better): IS Sharpe **+1.4186 @1x**, **+0.9920 @2x-stress**, maxDD **−36.0%**,
ann. turnover **276.5**, breadth L/S **20/18**, mean gross 0.993, mean net +0.21, regimes
bull **+2.884** / bear **+0.931** / chop **−0.408**, no-funding Sharpe +1.3984, 54 months,
59.3% positive months, worst month −17.0% (2024-04). If team-run diverges materially,
STOP and reconcile with the QR before any freeze.

## 9. Program addendum — falsification path, surviving claim, honest caveats

Chronology (all in experiments.jsonl, evaluator-stamped; results in out/scratch/results/):

1. **e01** — price-only yardsticks: MOM_L{9,12,21}_H3 = +1.26/+1.12/+1.33 @1x; REV deeply
   negative at every L (−2.3..−2.9). The cross-section is momentum-dominated at 1–7d.
2. **e02** — pre-registered core form S = sign(ret_L)×C: FAILED. Best +0.08 (L21), rest ≤ 0.
   **F1/F2 fired for the registered core expression.**
3. **e03** — registered-sign Amihud/excess-participation form: FAILED HARDER (−1.8..−2.7).
4. **e04** — flipped-sign exploration (logged as exploratory): also net-negative everywhere
   (best −0.25). The "fade thin moves" half of the registered story is dead in BOTH signs.
   (e03/e04 IC columns are contaminated by a contemporaneous-pairing bug, documented and
   fixed in e05; portfolio numbers are engine-truth and unaffected.)
5. **e05** — surviving-claim test: confirmation as pure STRENGTH modulator on the follow
   side, never sign-flipping (S = M×(C+k)/(1+k), k≥1). Beats matched plain MOM in 4/6 cells
   @1x and 6/6 @2x (L9k1 +1.56 vs +1.26; L12k1 +1.42 vs +1.12; L21 ≈ tie).
6. **e06** — controls: pure interaction M×C standalone-positive (peak +1.31 @L9);
   stale-C placebo collapses CWMOM to plain MOM (+1.25 vs +1.26 — timely volume info is the
   active ingredient); B ∈ {60,90,120} all ≥ MOM (+1.74/+1.56/+1.17); paired monthly diff
   vs MOM: +1.36%/mo t=1.70 (L9), +1.52%/mo t=1.84 (L12). Pre-logged verdict rule
   (placebo clean AND paired t>1) PASSED.
7. **e07/e08** — pre-registered plateau/H rules applied mechanically: L*=12 (interior
   neighborhood-min 1.33 beats L9's 0.98; L21 edge tie broken toward interior), H*=3
   (smallest H within 0.1 of H-max at L12). The rule DISCARDS the higher L9 cells
   (+1.56 H3, +1.60 H6) because L9's neighborhood contains weak L6 — accepted as the
   pre-registered anti-overfit discipline; not overridden.

**Falsifier status, stated plainly:** the pre-registered core claim ("thin-volume moves
mean-revert; fade them") is FALSIFIED (e02–e04). The registered family's other half
("volume-backed moves persist; follow them, scaled by confirmation") SURVIVES with controls:
the confirmation gate adds +0.30 Sharpe over matched plain momentum at the selected config
(paired t≈1.8, placebo-validated, B-robust, improves the 2×-stress tier in 6/6 cells).
F2 at the selected config: +1.419 vs MOM +1.122 and REV −2.44 — PASS on point estimates;
margin is inside the ±0.4 monthly-Sharpe noise floor and is reported as such.

**Family-boundary disclosure (for orchestrator confirmation):** algebraically
CWMOM_k1 = 0.5·(M + M×C): the book carries an unconditional XS-momentum core (a family no
team has registered — t03 is BTC-residual momentum, t04 is time-series trend) plus the
volume-price interaction term (this team's registered axis, standalone-positive per e06).
The submitted mechanism is honestly described as "follow volume-backed moves, weight by
volume confirmation, don't trade the thin extreme" — the first clause of the approved
registry summary; the "fade" clause was falsified and is NOT implemented. If the
orchestrator rules this outside the registered family, the documented pivot remains
available; this disclosure is made BEFORE freeze.

**Honest caveats:** (a) chop-regime Sharpe is NEGATIVE (−0.41; plain MOM: −0.95 — the gate
helps but does not rescue chop); the strategy is long-momentum-structure and says so.
(b) The last three IS months (2024-04..06, post-halving chop) are the worst stretch
(−17.0%/−13.9%/−4.3%) and the sealed holdout begins immediately after — no action taken
(any "fix" would be holdout-tuning). (c) Funding is a small net drag (−0.051 cumulative
raw; no-funding Sharpe +1.398 vs +1.419 — the book is slightly long-tilted, mean net +0.21).
(d) 59.3% positive months, worst −17.0%: the equity path is volatile; maxDD −36%.
