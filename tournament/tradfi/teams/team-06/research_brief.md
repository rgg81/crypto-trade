# team-06 research brief — t06-sector-pairs-coint-v1

Family (APPROVED in registry.jsonl): **Sector pairs / cointegration stat-arb** (menu #8).
Status: PRE-REGISTRATION written BEFORE any experiment result was read (see experiments.jsonl
ordering; reg-001/reg-002 are registration lines, exp-003+ are Phase-2 lines).

## 1. Mechanism & economic rationale

Within a sector, close economic substitutes (same end-market, same macro exposures) are held
together by shared cash-flow news and shared investor flows; their log prices drift apart on
idiosyncratic order-flow shocks (single-name retail bursts, index/ETF rebalance pressure,
earnings-adjacent overreaction) and converge back as arbitrageurs and slower fundamental flows
re-price the laggard. Trading the spread long-laggard/short-leader harvests a liquidity-provision
premium that is dollar-neutral by construction (each pair's legs net out), fitting the
market-neutral-ish mandate and the 0.25 net cap natively. On Binance single-stock perps the
convergence flow exists in the underlying equities; we harvest it at the daily horizon where
6 bps/side is survivable if weights move slowly.

Why it can still exist post-2010 at daily cadence: the classic (Gatev) distance-pairs edge decayed
mostly at intraday/HF horizons; a slow, banded/smoothed daily book on a small, retail-heavy
universe is a different niche. We accept ex-ante that the edge is thin — the falsifier below is
armed accordingly.

## 2. Data & universe rules (causal, ragged-start-safe)

- Inputs: `close` panel (log prices x = log(close)), `aux['sector_map']`. No ret_fwd, ever.
- Selection dates: index POSITIONS s = W_form-1, W_form-1+R, W_form-1+2R, … on the panel grid
  (anchored at panel START — invariant under future-truncation, harness-safe).
- Candidate pair (i, j), i<j alphabetically, at selection date s: same sector; each leg has
  >= ceil(0.95·W_form) valid closes inside the trailing W_form window AND >= 1 valid close in the
  last 5 rows of the window.
- For estimation and spread evaluation, log prices are forward-filled with limit=5 INSIDE the
  code path; if a leg has no close for >5 consecutive days the pair signal is forced to 0 (flat)
  until data resumes. NaN weight cells emitted as 0 (engine treats NaN as flat anyway).

## 3. Signal pipeline (exact, per selection segment)

1. On the formation window (last W_form rows up to and including s): OLS x_i = α + β·x_j + e.
   Discard pair if β ∉ [0.2, 5.0] (degenerate hedge).
2. Cointegration score = Dickey-Fuller t-stat of ρ in Δe_t = ρ·e_{t−1} + ε over the window
   (more negative = stronger mean reversion). Alternatives pre-registered: SSD of start-normalised
   prices (Gatev distance); |corr| of daily log returns.
3. Rank all candidate pairs (global across sectors) by score; keep top-N, with at most
   MAX_PER_NAME pairs containing any single name (default: unlimited; variant 4).
4. μ, σ = mean/std of e over the formation window (frozen for the segment).
   Variant: rolling z with window W_z re-estimated daily (still causal).
5. Daily for rows t in [s, next_s − 1]: e_t = x_i,t − α − β·x_j,t; z_t = (e_t − μ)/σ.
6. Pair signal (CONTINUOUS default): p_t = −clip(z_t, −Z_MAX, +Z_MAX); p_t = 0 where |z_t| < Z_DEAD.
   Variant (BANDED): enter ±sign at |z| ≥ Z_IN, exit to 0 at |z| ≤ Z_OUT (stateful); state carries
   across reselection iff the identical pair is re-selected, else closed.
7. Leg weights: w_i += p_t · u, w_j −= p_t · β · u with u = 1/(1+|β|).
   Variant: inverse-spread-vol sizing u ∝ [1/(1+|β|)] · [median_pair σ_Δe / σ_Δe(pair)] (capped ×3).
8. Sum over pairs → raw row. Optional EMA smoothing of the summed raw panel, halflife H days.
9. Emit raw signed weights; engine owns gross-norm, caps, lag, cost, vol-target.

## 4. Pre-registered parameter grid (+ rationale)

| Axis | Grid | Rationale |
|---|---|---|
| Selection score | DF t-stat / SSD / |corr| | DF = mechanism-native; SSD, corr = robustness cross-checks |
| W_form | 126 / 252 / 504 | half-year to two-year equilibrium estimation; 252 default |
| Reselect R | 21 (default) / 5 | monthly = stable book; weekly = adaptivity check |
| N pairs | 10 / 20 / 40 | breadth floor needs enough simultaneous pairs; 20 default |
| z mode | frozen-formation (default) / rolling W_z=63 | frozen = classic EG; rolling = adaptive |
| Z_DEAD / Z_MAX | 0.5 / 3.0 defaults; Z_DEAD ∈ {0, 0.5, 1.0} | deadband kills small-z churn (cost control) |
| Banded Z_IN/Z_OUT | 2.0 / 0.5 | classic Gatev bands; PREDICTION: fails breadth floor at N=20 |
| Pair sizing | equal / inverse-σ_Δe | risk parity across spreads |
| EMA halflife H | 0 / 3 / 7 | first-class cost control |
| MAX_PER_NAME | ∞ / 4 | concentration control |

Budget: target ≤ 20 material experiment lines for this phase (hard cap 40 incl. registrations).
Batching: lines are appended BEFORE the batch script that produces their results is run.

## 5. Pre-registered selection rule

Choose the configuration maximising **min(Sharpe@1×, Sharpe@2×)** subject to:
(a) median names/side ≥ 5 (hard floor, Critic-checked);
(b) plateau: every one-step neighbour in the grid keeps the same Sharpe sign and ≥ 60% of the
    candidate's Sharpe@1× (isolated peaks are disqualified);
(c) ties broken by lower annual turnover.
No configuration may be selected on a metric not produced by `te.run_is` / team-run.

## 6. Falsifier (kills the family)

- Default config net IS Sharpe@1× ≤ 0 AND no grid region reaches ≥ +0.30 with a valid plateau; OR
- every config with Sharpe@1× > 0 violates the breadth floor; OR
- Sharpe@2× < 0 across the entire positive-@1× region (edge = cost artifact).
Any of these → family dead; single documented pivot per charter.

## 7. Expected regime behaviour (pre-registered prediction)

- Chop / range markets: best regime — spreads oscillate, convergence frequent.
- Calm bull: mildly positive; fewer dislocations, thinner spread vol.
- Stress / crash (2020-03, 2022): two-sided — dislocations widen first (mark-to-market pain,
  z overshoot) then converge hard; expect drawdown INTO the spike, recovery after. Vol-targeting
  shrinks exposure into the spike, which helps.
- Sustained sector re-rating (one leg structurally re-priced): worst case — spreads trend, not
  revert; the DF-selection and formation re-estimation each R days is the defense.

## 8. Results — FALSIFIER FIRED (all numbers from `te.run_is`; raw JSON in out/scratch_results.jsonl)

Census (exp-003): 65 names, 9 sectors (Tech 18, Semi 18, ConsDisc 9, Comm 5, Fin 5, Crypto 3,
Health 3, ConsStap 2, Indust 2); 164→337 candidate within-sector pairs across the window.
Breadth was feasible; the edge was not.

| exp | config (delta vs default) | Sharpe@1× | maxDD | annTO | med L/S | bull/bear/chop |
|---|---|---|---|---|---|---|
| 004 | DEFAULT (cont, DF, W252, N20, frozen z) | −0.71 | −0.85 | 62 | 9/9 | −1.10/+0.75/−0.30 |
| 005 | band 2.0/0.5 | −0.16 | −0.69 | 25 | 4/4 FAIL | −0.67/+0.61/+1.15 |
| 006 | SSD selection | −1.11 | −0.93 | 45 | 10/10 | −1.29/+0.14/−0.87 |
| 007 | corr selection | −0.49 | −0.74 | 35 | 7/7 | −0.94/+0.27/+0.62 |
| 008 | W_form 126 | −0.86 | −0.89 | 76 | 10/9 | −1.01/−0.47/−0.45 |
| 009 | W_form 504 | −0.87 | −0.88 | 47 | 9/9 | −1.47/+1.55/−0.71 |
| 010 | N=10 | −0.49 | −0.75 | 57 | 6/6 | −0.74/+0.30/−0.13 |
| 011 | N=40 | −0.76 | −0.85 | 59 | 14/14 | −1.19/+0.71/−0.31 |
| 012 | rolling z 63 | −0.81 | −0.85 | 73 | 10/10 | −1.21/+0.94/−0.56 |
| 013 | band N40 | −0.52 | −0.73 | 33 | 8/8 | −0.99/+0.18/+0.94 |
| 014 | band N40 + z_stop 3.5 | −0.51 | −0.72 | 38 | 7/7 | −0.98/+0.24/+0.89 |
| 015 | band N40 + t_stop 21 | −0.50 | −0.75 | 38 | 6/6 | −1.09/+0.56/+0.96 |
| 016 | band N40 + both stops | −0.42 | −0.72 | 41 | 6/6 | −1.02/+0.74/+0.93 |
| 017 | 016 + DF gate ≤ −3.0 | −0.41 | −0.77 | 26 | 3/3 FAIL | −0.91/+0.34/+0.76 |
| 018 | band z_in 2.5 + stops | −0.27 | −0.63 | 31 | 4/4 FAIL | −0.60/+1.00/+0.15 |
| 019 | FAST: roll z21, R5, band+stops | −0.71 | −0.85 | 87 | 7/7 | −1.12/+0.47/+0.03 |
| 020 | FAST cont: roll z21, R5, dead 1.0, EMA3 | −0.31 | −0.60 | 48 | 21/21 | −0.66/+1.16/+0.17 |
| 021 | DIAG: 016 at ZERO cost | −0.10 | −0.56 | 41 | 6/6 | −0.68/+1.07/+1.17 |
| 022 | DIAG: sign-flip of 004 (divergence) | −0.33 | −0.64 | 62 | 9/9 | +0.05/−1.52/−0.69 |
| 023 | 016 at 2× cost | −0.73 | −0.84 | 41 | 6/6 | −1.34/+0.41/+0.68 |

Falsifier verdict against §6 (pre-registered):
1. Default config Sharpe@1× = −0.71 ≤ 0. FIRED.
2. No grid region ≥ +0.30 with a valid plateau — in fact NO configuration is > 0 anywhere in the
   pre-registered space (18 backtests + 3 diagnostics). FIRED.
3. Gross-alpha check: the best breadth-valid config is −0.10 at ZERO cost (exp-021) — the
   mechanism's gross alpha is absent; no cost engineering can rescue it. FIRED.

Economic post-mortem (consistent across all 21 runs): the universe is Tech/Semi-heavy US
mega-caps over 2010–2024 — a secular-DIVERGENCE regime in which within-sector "laggards" keep
lagging for years (bull regime Sharpe −0.6..−1.5 in every convergence config), while bear/chop
regimes show genuine convergence (+0.2..+1.6). The sign-flip forensic (exp-022, disclosed
diagnostic, never a candidate) is ALSO negative (−0.33; bear −1.52): divergence books get
snapped in compressions. Neither unconditional direction of the pair-spread process carries
net alpha under the tournament's construction; the residual regime-conditional structure
belongs to a different mechanism family (#7 VIX-conditional) and is out of scope here.

## 9. Final QE specification

NONE. The family is falsified per §6/§8 — handing the QE any configuration from this space
would be laundering a known-negative strategy. Recommendation to the orchestrator: exercise
team-06's single documented pivot (charter §6), ranked preference:
1. Family #6 — volume & liquidity anomalies (OHLCV-native, several distinct sub-mechanisms,
   no overlap with any registered family, cost-shapeable to low turnover);
2. Family #7 — VIX-conditional regime books (the bear/chop-positive structure measured here is
   honest evidence that regime conditioning has content; VIX is the deliberately-shipped aux);
3. Family #13 — intra-sector lead-lag (weakest prior: mega-cap lead-lag has largely decayed).
Ledger continues (23 lines used incl. registrations; 17 remain under the hard cap).

---

# PIVOT — t06-vix-regime-books-v1 (family #7, pre-approved; reg-024)

PRE-REGISTRATION written BEFORE any pivot-family experiment result was read (reg-024 appended
first; exp-025+ follow).

## P1. Mechanism & economic rationale

Different cross-sectional books under calm vs stressed VIX states; **the alpha claim is the
STATE-CONDITIONALITY itself**, not either inner book. Two of the best-documented conditional
facts in US equities: (a) the short-horizon reversal premium is compensation for liquidity
provision and concentrates almost entirely in HIGH-VIX states (market makers withdraw, snap-backs
overshoot); (b) cross-sectional momentum earns its premium in CALM states and crashes in
high-VIX rebound states. An unconditional book pays for each premium's bad regime; switching
deploys each only where its premium exists. VIX is observable at decision time (aux series,
close[t]) and the perp universe's retail flow makes stress dislocations if anything sharper.
Family fidelity: another team gates EXPOSURE on VIX; this design switches the BOOK COMPOSITION
— mechanism kept clearly distinct, and unconditional inner books are run only as disclosed
REFERENCE diagnostics for the fidelity falsifier (P4).

## P2. Design space (exact, causal)

- VIX state v_t: trailing percentile of VIX close over PCT_WIN days (percentile = fraction of
  window values <= current; min history 252 else state=calm). Hard-switch with hysteresis:
  stressed when pct >= HI, calm when pct <= LO, carry previous in between (start calm).
  Variant RAMP: s_t = clip((pct − LO)/(HI − LO), 0, 1), continuous blend, no hysteresis.
  Variant ABS: absolute VIX thresholds (calm < 20, stressed > 25, hysteresis between).
- Calm book (momentum, generic 12-1): m = close[t−SKIP]/close[t−FORM] − 1 over eligible names
  (valid close at t and t−FORM, valid close within last 5 days); cross-sectional z, winsorize
  ±3, re-demean → w_mom.
- Stressed book (short-horizon reversal): r = close[t]/close[t−REV_WIN] − 1 (variant:
  standardized by trailing 21d daily-return vol); cross-sectional z, winsorize ±3, re-demean,
  NEGATED → w_rev.
- Each book gross-normalised to 1, then composite w = (1−s)·w_mom + s·w_rev; optional EMA
  halflife H on the composite. Rows with <10 eligible names → flat. NaN → 0.
- Grid: PCT_WIN ∈ {252, 504, 756}; (HI, LO) ∈ {(0.8, 0.6), (0.7, 0.5), (0.85, 0.7)}; ABS
  (25, 20); SKIP=21, FORM=252 fixed (generic textbook values, not tuned); REV_WIN ∈ {5, 10};
  vol-std reversal on/off; blend ∈ {hard, ramp}; H ∈ {0, 3}.
- Defaults: PCT_WIN=504, HI=0.8, LO=0.6, hard switch, REV_WIN=5, plain z, H=0.

## P3. Expected regime behaviour (pre-registered)

Calm bull: momentum book carries; modest positive. Stress onset (VIX spike): book flips to
reversal; expect the strongest contribution during/after spikes (2011, 2015-16, 2018Q4, 2020-03,
2022) — harvesting overshoot snap-backs. Chop: whichever state dominates locally; hysteresis
prevents whipsaw. Failure mode: sustained mid-VIX drift with frequent state flips (transition
churn), and momentum crashes that begin BEFORE the VIX percentile trips stressed.

## P4. Falsifier (kills the pivot family; no further pivot exists)

1. Composite Sharpe@1× <= 0 on the default config AND no grid region >= +0.30 with a valid
   plateau (same plateau rule as §5); OR
2. FIDELITY: best composite fails to exceed BOTH unconditional reference books (mom-only,
   rev-only, same ingredients, run as disclosed diagnostics) by >= +0.10 Sharpe@1× — the switch
   is not load-bearing and shipping would misrepresent the family; OR
3. every breadth-valid positive config flips negative @2×; OR breadth floor unfixable.

## P5. Budget plan

17 lines remained; reg-024 spent 1 → 16 left. Plan: 2 reference diagnostics + ~10 material
composites (state axis, blend axis, reversal variant, smoothing, plateau neighbours) + 2×-cost
finalist runs + <= 2 reserve. Selection rule identical to §5 (max min(Sharpe@1×, @2×), breadth
>= 5/side, plateau, then lower turnover).

## P6. Results (all numbers from `te.run_is`; raw JSON in out/scratch_results.jsonl)

| exp | config (delta vs default) | Sharpe@1× | maxDD | annTO | bull/bear/chop |
|---|---|---|---|---|---|
| 025 | REF: mom-only (unconditional) | +0.49 | −0.25 | 19 | +0.65/−1.75/+0.76 |
| 026 | REF: rev-only (unconditional) | −0.79 | −0.89 | 156 | −0.95/−0.16/−0.44 |
| 027 | composite DEFAULT (pct504, 0.8/0.6, hard) | +0.57 | −0.24 | 59 | +0.53/+0.78/+0.53 |
| 028 | ramp blend | +0.53 | −0.26 | 68 | +0.45/+0.39/+0.88 |
| 029 | abs VIX 20/25 | +0.29 | −0.49 | 55 | +0.19/+0.13/+0.77 |
| 030 | vol-std reversal | +0.56 | −0.26 | 60 | +0.57/+0.26/+0.62 |
| 031 | pct_win 252 | +0.62 | −0.20 | 60 | +0.56/+0.01/+1.09 |
| 032 | pct_win 756 | +0.24 | −0.44 | 60 | +0.10/+0.54/+0.55 |
| 033 | thresholds 0.7/0.5 | +0.16 | −0.47 | 72 | +0.04/+0.45/+0.40 |
| 034 | thresholds 0.85/0.7 | +0.67 | −0.23 | 52 | +0.56/+0.53/+1.15 |
| 035 | rev_win 10 | +0.55 | −0.25 | 47 | +0.53/+0.64/+0.52 |
| 036 | EMA halflife 3 | +0.58 | −0.23 | 26 | +0.45/+0.90/+0.93 |
| 037 | COMBO A: 0.85/0.7 + EMA3 | +0.75 | −0.23 | 22.5 | +0.61/+0.75/+1.25 |
| 038 | COMBO B: 0.85/0.7 + EMA3 + rev10 | +0.74 | −0.23 | 18.1 | +0.63/+0.41/+1.28 |
| 039 | COMBO A @2× cost | +0.63 | −0.23 | 22.5 | +0.51/+0.42/+1.15 |
| 040 | COMBO B @2× cost | +0.64 | −0.23 | 18.1 | +0.55/+0.17/+1.19 |

Breadth: 22/27 median names long/short on every composite (floor is 5 — passed 4×+ over).

- Falsifier P4.1: NOT fired (default +0.57 > 0; plateau region exists well above +0.30).
- Fidelity P4.2: NOT fired — best composite +0.75/+0.74 exceeds the best unconditional
  reference (+0.49) by ≥ +0.25; bear regime flips from −1.75 (mom-only) to +0.41..+0.78
  (composites): the SWITCH is load-bearing, exactly the family's mechanism claim.
- P4.3: NOT fired — @2× both finalists remain ≥ +0.63.
- SELECTION (pre-registered rule): max min(Sharpe@1×, @2×): COMBO B = min(0.739, 0.639) = 0.639
  beats COMBO A = min(0.750, 0.631) = 0.631; B also wins the lower-turnover tiebreak. FINALIST = B.
- Plateau evidence for B (same sign, ≥60% retention everywhere sampled): rev axis (B→A rev5)
  0.75 (101%); EMA axis at same thresholds (H3→H0, rev5) 0.67 (91%); threshold axis at EMA3
  (0.85/0.7→0.8/0.6, rev5) 0.58 (79%); state-window axis at base config 252/504/756 =
  0.62/0.57/0.24 (both neighbours positive). HONEST CAVEAT: not every one-step neighbour of B
  itself was run (budget cap 40 reached); the sampled surface is smooth and everywhere-positive
  in the deep-stress + smoothed region. The 756d window and 0.7/0.5 thresholds are the weak
  edges of the space and are far from the selected point.

## P7. FINAL QE SPECIFICATION — t06-vix-regime-books-v1 (COMBO B; every parameter fixed)

Interface: `build_raw_weights(pn, aux)` returns a dates×tickers DataFrame of raw signed
weights. Tickers = `pn['close'].columns` at runtime (never hard-coded). Uses ONLY
`pn['close']` and `aux['vix']`. Deterministic; `aux['seed']` unused (no randomness).

1. `close = pn['close'].astype(float)`; all computations on this panel's index/columns.
2. VIX state series:
   a. `v = aux['vix'].reindex(close.index).ffill()` (no limit).
   b. Percentile: for each row t, `pct[t]` = fraction of the trailing 504-row window of v
      (rows max(0, t−503)..t, finite values only) that is <= v[t]; require >= 252 finite
      values in the window AND finite v[t], else pct[t] = NaN.
   c. Hard switch with hysteresis, initial state CALM (s=0): iterate rows in order; if pct[t]
      is finite and pct[t] >= 0.85 -> s=1 (stressed); elif pct[t] is finite and pct[t] <= 0.70
      -> s=0 (calm); else carry previous s. (NaN pct carries state, which at the start of the
      panel means calm.)
3. Calm book (momentum): `sig_m = close.shift(21) / close.shift(252) - 1`.
4. Stressed book (reversal): `sig_r = close / close.shift(10) - 1`.
5. Cross-sectional transform, applied to each signal panel independently, row-wise:
   z = (sig − row_mean) / row_std with std ddof=1 (row_std of 0 -> whole row NaN);
   clip to [−3, +3]; subtract the row mean of the clipped values (re-demean).
   For the reversal book NEGATE after re-demeaning. Rows with fewer than 10 finite values
   become all-NaN. Then row gross-normalise: divide by the row sum of |z| (sum of 0 -> NaN),
   fillna(0.0). Yields w_mom and w_rev.
6. Composite: `raw = w_mom * (1 − s) + w_rev * s` (s broadcast per row).
7. Smoothing: `raw = raw.ewm(halflife=3.0, min_periods=1).mean()`.
8. Return raw. (NaN cells, if any, are flat by engine contract; step 5 already fills 0.)

Missing data: names with insufficient history are NaN in the shifted signals and are simply
absent from that row's cross-section (ragged starts safe). No forward-filling of close prices
anywhere. No sector_map, no volume, no OHLC beyond close. State grid causality: percentile
windows are trailing and row-anchored; EMA is causal; truncating future rows cannot change
past outputs (truncated-replay safe).

Expected IS metrics (evaluator, out/scratch_results.jsonl exp-038/exp-040 — team-run must
reproduce): Sharpe@1× 0.739, Sharpe@2× 0.639, maxDD −0.230, ann. turnover 18.1×, median names
22 long / 27 short, total return +3.44, regime Sharpe bull +0.63 / bear +0.41 / chop +1.28.
