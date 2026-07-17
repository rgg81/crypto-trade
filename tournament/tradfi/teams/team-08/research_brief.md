# team-08 — Research Brief (pre-registered)

Family: `t08-short-horizon-reversal-v1` — plain OWN-NAME short-horizon (1-5d) cross-sectional
reversal. APPROVED in `registry.jsonl` (redraw backup-1, pass-2).

Status: PRE-REGISTRATION written 2026-07-17T01:57Z, BEFORE any experiment was run.
The FINAL SPEC section at the bottom is filled in only after the experiment ledger completes;
everything above it is frozen intent.

---

## 1. Economic mechanism

Short-horizon (1-5 trading day) losers bounce and winners fade. The premium is compensation
for providing liquidity against non-fundamental order-flow pressure: index/ETF rebalancing,
option-hedging flow, retail bursts, and forced de-risking push single names away from fair
value over a few days, and the price impact decays as inventories are worked off. In this
specific universe (~65 US single-stock perps skewed toward high-attention, retail-heavy
glamour names) short-horizon flow pressure should be larger than in the broad market, and the
mechanism requires no information — it harvests other people's demand for immediacy.

Family boundary (Critic-checked): the signal is each name's OWN trailing return, compared
cross-sectionally across the whole universe. NO sector-basket residualization of any kind
(that is team-03's family). `aux['sector_map']` is never touched. Cross-sectional
rank-centering across the full universe is the family's defining transform, not a sector
residual.

## 2. Known structural headwinds (declared up front)

1. **Costs are the existential axis.** 6 bps/side on |Δw| at daily cadence: a naive daily
   full-rebalance rank book turns over 30-120%/day one-way → 5-18%/yr drag before vol-target
   releveraging. Turnover engineering (longer lookback, EWMA smoothing, concentration) is
   first-class design, not an afterthought.
2. **Fill timing loses the overnight bounce.** The engine earns open-to-open starting at
   open[t+1] for a book decided at close[t] (`ret_fwd` + shift(1)); the close[t]→open[t+1]
   reversion — a large share of 1-day reversal alpha — is structurally uncapturable. Design
   response: prefer multi-day lookbacks/holds; explicitly test last-day handling variants.
3. **Post-2010 decay.** Plain STR in liquid US large caps weakened after the 2000s. The IS
   window (2010-2024) is exactly the decayed era — this is why the falsifier below has a
   modern-sub-period clause.

## 3. Signal construction (design space, all pre-registered)

Let close/open be the team-view panels. For name i, day t (all quantities use data ≤ close[t];
the engine applies the decision lag):

- `ret1[i,t] = close[i,t]/close[i,t-1] - 1`
- `sigma[i,t]` = std of ret1 over trailing 63 days, `min_periods=40`
- `r_k[i,t] = close[i,t]/close[i,t-k] - 1` (lookback k days)
- `z_k[i,t] = r_k[i,t] / (sigma[i,t] * sqrt(k))`
- Validity: name active at t iff close[t], close[t-k], sigma[t] all present; invalid → NaN → flat.

Axes and grids:

| Axis | Grid | Rationale |
|---|---|---|
| Lookback k | {1, 2, 3, 4, 5} | family-defining horizon; longer k = slower signal, less overnight loss |
| Weighting | centered-rank linear; z-linear; z-linear winsorized at ±3 | rank robust to outliers; z preserves magnitude |
| Cross-sectional transform | subtract cross-sectional mean (rank or z) over VALID names | dollar-centered book; universe-level, NOT sector |
| Sign | weight ∝ −(centered score) | fade: long losers, short winners |
| Last-day handling | FULL (r_k ends close[t]); LAG1 (ends close[t-1]); INTRA (close[t-k]→close[t-1] composed with open[t]→close[t], i.e. drop the t-1→t overnight) | fill-timing interaction |
| EWMA smoothing halflife h | {0 (none), 1, 2, 3, 5, 8} days on the per-name score (NaN→0 first) | THE turnover lever |
| Concentration q (per tail) | {0.5 (full book), 0.35, 0.25, 0.15} | alpha density vs turnover vs breadth |
| Extreme-move gate z_max | {inf, 4, 3, 2.5} — EXCLUDE names with all-of-window \|z_k\| > z_max (weight 0) | biggest moves are informational (earnings) and trend; exclusion, not winsorization, because ranks are invariant to winsorizing |

Raw weights handed to the engine = smoothed centered score panel (engine owns gross=1,
|w_i|≤0.10, |net|≤0.25, vol-target). No use of `aux['seed']` (no randomness), no
`aux['sector_map']`, no `aux['vix']` in the base design.

## 4. Experiment plan (ledger ids pre-assigned; ≤ 12 material lines intended)

- exp-003 lookback grid k∈{1..5}, rank weights, FULL, h=0, q=0.5, z_max=inf; both cost tiers
- exp-004 weighting scheme at plateau k: rank vs z vs z-winsor
- exp-005 EWMA halflife grid on best-so-far
- exp-006 last-day handling FULL/LAG1/INTRA on best-so-far
- exp-007 concentration grid q on best-so-far
- exp-008 extreme-move gate z_max grid on best-so-far
- exp-009 joint mini-refinement around the winner (≤ 9 combos) — plateau confirmation
- exp-010 FINAL spec confirmation run: 1× + 2×, regimes, breadth, sub-periods, determinism
- exp-011..014 reserved for contingencies (only if a result is ambiguous); hard stop at exp-014

Every line is appended to `experiments.jsonl` BEFORE its result is read. All performance
numbers come from `tournament.engine.run_is` (the evaluator) — never hand-computed.

## 5. Selection rule (pre-registered)

1. Feasibility filter: median names/side ≥ 5 (target ≥ 8 for buffer) AND Sharpe@2× > 0.
2. Among feasible configs, maximize net IS Sharpe@1× **subject to plateau membership**: every
   single-notch perturbation of (k, h, q, z_max) within the grids must retain ≥ 75% of the
   candidate's Sharpe@1×. If the argmax fails, walk down to the best config that passes.
   Plateaus over peaks — a fragile peak is treated as noise, not edge.
3. Regime sanity (report always): prefer configs with no regime (bull/bear/chop) Sharpe below
   −1.0; break ties toward flatter regime profiles.
4. Modern-era clause: final config must have Sharpe > 0 on the 2017-01-01→2024-06-30 slice of
   the evaluator net series (edge must exist in the decayed era, not just 2010-2012).

## 6. Falsifier (pre-registered at family registration; restated verbatim in effect)

The family is DEAD and I report a falsification (pivot or DNF, no laundering) if:
- net Sharpe@1× ≤ 0 across the ENTIRE (k, weighting, h, q, z_max, last-day) design space above
  — i.e., gross reversal alpha exists only at turnover levels 6 bps/side erases; OR
- the only positive-net configs violate the breadth floor; OR
- positive net exists but the modern-era clause (§5.4) fails across the whole plateau
  (pre-2015-only alpha = decayed anomaly, not deployable edge).

## 7. Handoff contract

The FINAL SPEC below (written after experiments) is the complete QE specification: exact
formulas, exact parameters, exact NaN rules, no free choices. The QE implements
`build_raw_weights(pn, aux)` from it verbatim; any ambiguity is a brief defect, escalate back
to QR rather than guessing.

---

## FINAL SPEC — NONE. FAMILY FALSIFIED (verdict written 2026-07-17 after exp-010)

The pre-registered falsifier (§6, clause 1) FIRED across the entire design space. There is no
QE specification and no `strategy.py` to build. Verdict detail:

### What the ledger shows (all numbers from `tournament.engine.run_is`; see `is_report.md`)

- Every one of the 31 configurations evaluated across exp-003..exp-010 has **net IS
  Sharpe@1x < 0** (best: −0.124, k=1/INTRA/h=30) and **net Sharpe@2x < 0** (feasibility
  filter §5.1 admits the EMPTY SET).
- A thin gross edge EXISTS: the 1x-vs-2x cost spread implies zero-cost Sharpe ≈ +0.16..+0.63
  everywhere, peaking for fresh intraday-move fades (k=1 INTRA). The regime profile is the
  textbook liquidity-provision signature (bear +0.5..+0.6, bull negative). The mechanism is
  real — and everywhere smaller than the 6 bps/side drag at any turnover that preserves it.
- The two escape routes both closed: (a) smoothing kills the alpha as fast as the cost
  (exp-005: gross ≈ 0 by h=5 at k=5); (b) the tails carry LESS alpha, not more (exp-007:
  gross falls with concentration; exp-008: extreme-move gating does not help).
- Boundary closure (exp-010): the k=1/INTRA column improves monotonically with h but stays
  negative through h=30, where the construction is no longer in-family anyway (EWMA h=30 of
  1-day intraday ranks has ~43d effective lookback → that is a medium-horizon intraday-
  component fade, mechanically adjacent to team-07's approved overnight-vs-intraday family,
  NOT 1-5d reversal). The 2017-24 sub-period positivity at h ≥ 8 (up to +0.38) belongs to
  that out-of-family mechanism and is NOT claimed; whole-window net remains negative there
  regardless.

### Decision

FALSIFIED per §6 clause 1 (and §5.1 feasibility empty). No submission from this family.
Recommendation to the orchestrator: DNF, or — only if participation is preferred — a
documented pivot; note the remaining free menu families (#7 VIX-conditional books, #13
intra-sector lead-lag) carry weak priors on a panel that has already falsified four families
(52wk-high, low-vol/BAB, sector pairs, and this one), and #13 has mechanism-space adjacency
to team-03's approved family (a "laggard vs sector leaders" long is shape-identical to a
sector-relative reversion long). Ledger spend: 8 material experiments (exp-003..010) of 40.
