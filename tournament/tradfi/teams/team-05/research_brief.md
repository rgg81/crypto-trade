# team-05 research brief — t05-lowvol-bab-v1 (low-volatility / betting-against-beta)

Status: PRE-REGISTRATION written 2026-07-17 BEFORE any evaluator run. The FINAL SPEC section
is filled in only after the pre-registered experiment ladder completes; everything above it is
frozen intent.

## 1. Mechanism & economic rationale

Leverage-constrained and lottery-seeking investors overpay for high-volatility / high-beta
names (they buy embedded leverage), flattening the risk-return line: low-risk names earn too
much per unit of risk, high-risk names too little. A Binance single-stock perp universe is
close to a worst-case lottery-demand clientele (retail, levered, drawn to the most volatile
tickers), so the overpricing of the volatile end should be at least as strong as in cash
equities, where this premium has a century of evidence. The book monetizes it by holding the
underpriced boring end against the overpriced lottery end. The organizer-side portfolio
vol-target supplies the leverage that makes the low-risk side competitive — the
betting-against-beta construction. Sort key is systematic risk rank ONLY (no momentum, no
anchoring, no sector-relative spreads, no MAX/lottery tails, no VIX conditioning) — family
purity vs teams 01/02/03/07/09.

Why it fits this tournament's cost model: vol and beta ranks are highly persistent, so
natural turnover is small and the 6 bps/side daily cost drag is nearly negligible — the edge
does not need to clear a large cost hurdle, unlike any short-horizon family.

## 2. Expected regime behavior (pre-registered)

- Bear / high-VIX stress: best regime — the short lottery leg falls faster than the long
  defensive leg; vol ranks widen.
- Grinding bull: modestly positive to flat; premium accrues slowly.
- Speculative melt-up (2020-04 → 2021-02 core): WORST regime — short high-beta runners
  bleeds; caps + vol-target bound but do not remove it. Must be documented honestly.
- Key structural risk (coordinator-flagged, pre-registered kill): a dollar-neutral low-vol
  book is implicitly short beta; if the edge vanishes under proper beta-balancing it is a
  disguised short-market position, not a cross-sectional premium.

## 3. Signal definitions (exact formulas)

Panels: `view = te.team_view(pn)`; `close`, `open`, etc. are dates×tickers with NaN on
ragged/absent bars (never forward-filled).

- Daily returns: `ret = close.pct_change(fill_method=None)` (NaN preserved — no padding).
- Realized vol (primary sort key): `vol_L = ret.rolling(L, min_periods=max(40, L//2)).std()`.
- EWMA vol (estimator variant): `ret.ewm(halflife=L/2, min_periods=max(40, L//2)).std()`.
- Universe proxy return (for beta only): `mkt = ret.mean(axis=1)` (equal-weight across names
  with a return that day).
- Beta (variant sort key + balancing input): rolling 252d, `min_periods=120`:
  `beta_raw = ret.rolling(252, min_periods=120).cov(mkt) / mkt.rolling(252, min_periods=120).var()`,
  shrunk `beta = 0.6*beta_raw + 0.4*1.0` (Frazzini–Pedersen-style shrinkage).
- Eligibility mask at day t: non-NaN sort-key value AND non-NaN `close[t]`. Ineligible = NaN
  raw weight = flat (engine maps NaN→0).

Weight construction (primary, rank-linear symmetric):
- Among eligible names at t: `rank_t = vol.rank(axis=1, method='average')` (1 = lowest vol),
  `N_t` = eligible count, `raw_i = (N_t + 1)/2 - rank_i` → lowest vol most positive (long),
  highest vol most negative (short), symmetric → dollar-neutral pre-caps. Scale is irrelevant
  (engine gross-normalizes each row).
- Quantile variant: long the Q lowest-vol names at +1, short the Q highest-vol at −1, else 0.
- BAB beta-balancing overlay variant: per day, scale the long leg by `1/max(betabar_plus, 0.25)`
  and the short leg by `1/max(betabar_minus, 0.25)`, where `betabar_±` is the |w|-weighted
  mean shrunk beta of that leg. Engine's |net| ≤ 0.25 cap limits how much balancing can
  express — documented, not fought.
- Optional weight smoothing: `w_s = raw.ewm(span=S).mean()` — ONLY evaluated if the 1×→2×
  Sharpe degradation of the chosen config exceeds 0.15 (cost-bleed trigger).

No use of: `ret_fwd` (never), volume, VIX, sector_map (except optionally in diagnostics
reporting, never in the signal), open/high/low (close-to-close vol only).

## 4. Parameter ranges & rationale (pre-registered)

| Axis | Range | Rationale |
|---|---|---|
| Vol lookback L | {60, 120, 180, 252} | 3m–12m spans the literature's standard estimates; plateau across this range is falsifier axis (c) |
| min_obs | max(40, L//2) | enough obs for a stable std; admits post-IPO names in ~2–6 months |
| Sort key | realized vol (primary); shrunk 252d beta (variant); EWMA vol (variant) | vol is the simplest, most persistent risk rank; beta and EWMA test estimator-robustness, not new families |
| Weighting | rank-linear (primary); top/bottom Q=15 EW (variant) | rank-linear maximizes breadth and minimizes turnover; quantile tests concentration payoff |
| Beta balancing | off (primary) vs leg-scaled BAB (variant) | the coordinator-flagged kill test; also the deployability check |
| Smoothing span S | {none, 10} conditional | only if cost bleed materializes |

## 5. Experiment ladder (pre-registered; ≤12 material experiments planned)

E01 vol-rank L=120 (anchor) → E02 L=60 → E03 L=180 → E04 L=252 (plateau evidence).
E05 quantile Q=15 at plateau-center L. E06 beta-sort (252d shrunk). E07 BAB beta-balanced
overlay on plateau-center vol book (kill test). E08 EWMA-vol estimator at plateau-center L.
E09 (conditional) smoothing span=10. E10 final-candidate confirmation @1× and 2× with full
regime scorecard + pre-registered scratch diagnostics. Reserve E11–E12 for one honest
surprise; anything beyond requires a documented reason in the ledger.

Every experiment is scored at BOTH cost tiers (`cost_mult=1.0` and `2.0`) in the same run.

## 6. Selection rule (pre-registered, applied mechanically)

1. Discard any config with median names/side < 5 (breadth floor) — expected non-binding for
   rank-linear books (~N/2 per side).
2. Plateau rule: among L ∈ {60,120,180,252} for the primary sort, identify the widest
   contiguous set with net Sharpe > 0 at BOTH cost tiers; pick the CENTER of that plateau
   (ties → longer L, more stable estimate). Never the argmax.
3. Variant adoption rule: a variant (quantile, beta-sort, EWMA, smoothing) replaces the
   primary ONLY if it improves net Sharpe at BOTH 1× and 2× by ≥ +0.10 each.
4. Beta-balance decision: ship the BAB-balanced overlay instead of the plain book ONLY if it
   retains ≥ 90% of the plain book's 1× Sharpe OR improves the bull-regime Sharpe by ≥ +0.30
   while keeping 1× Sharpe within −0.10 of plain. Otherwise ship plain and DOCUMENT the
   short-beta character with the beta-balanced result.

## 7. Falsifiers (pre-registered kills — any one triggers pivot to backup 1)

(a) net IS Sharpe @1× ≤ 0 for every config in the pre-registered grid;
(b) 2015-01-01 → 2024-06-30 subperiod net Sharpe ≤ 0 for the selected config
    (computed with the approved `ct.msharpe` on the evaluator's own net series);
(c) no plateau: net Sharpe sign flips across L ∈ {60…252} (lookback-mined artifact);
(d) melt-up drawdown so deep that 2×-cost Sharpe and maxDD are worse than a flat book
    (undeployable under charter caps);
(e) breadth floor unattainable at slow-turnover rank weights;
(+) coordinator-flagged: if the beta-balanced book's Sharpe ≤ 0 while the plain book's is
    positive, the premium is a disguised short-market position — REPORTED prominently either
    way; treated as a kill only in combination with (b) or (d), since the charter permits
    |net| ≤ 0.25 books and the vol-target engine prices the residual beta honestly.

## 8. Pre-registered diagnostics (scratch, evaluator-derived, labeled as such)

- Subperiod Sharpes via `ct.msharpe(net, lo, hi)`: 2010–2015, 2015–2024.5, melt-up core
  2020-04-01 → 2021-02-15.
- Regime scorecard from `m.regime_sharpe` (bull/bear/chop).
- Beta character: OLS slope of daily net vs EW-universe return (diagnostic only).

---

# FALSIFICATION VERDICT — t05-lowvol-bab-v1 is DEAD (pre-registered kill (a) fired)

Ten material experiments (exp-001…exp-010, ledger + out/scratch/results_b{1,2,3}_*.json; all
numbers from `te.run_is`, the evaluator). Every configuration in the pre-registered grid is
NEGATIVE at both cost tiers:

| exp | config | Sharpe@1× | Sharpe@2× | maxDD | 2015→2024H1 sub-Sharpe | β(net,mkt) |
|---|---|---|---|---|---|---|
| 001 | vol rank L=120 | −0.654 | −0.692 | −0.87 | −0.745 | −0.30 |
| 002 | vol rank L=60 | −0.744 | −0.818 | −0.89 | −0.830 | −0.29 |
| 003 | vol rank L=180 | −0.692 | −0.719 | −0.89 | −0.803 | −0.30 |
| 004 | vol rank L=252 | −0.735 | −0.756 | −0.90 | −0.875 | −0.29 |
| 005 | + BAB balance, L=120 | −0.246 | −0.296 | −0.72 | −0.398 | −0.21 |
| 006 | + BAB balance, L=252 | −0.269 | −0.296 | −0.78 | −0.514 | −0.19 |
| 007 | canonical FP: beta-sort + balance | −0.031 | −0.070 | −0.64 | −0.377 | −0.20 |
| 008 | sector-neutral vol rank | −0.472 | −0.524 | −0.84 | −0.728 | −0.25 |
| 009 | sector-neutral + BAB balance | −0.132 | −0.194 | −0.71 | −0.431 | −0.15 |
| 010 | idio-vol + BAB balance | −0.440 | −0.500 | −0.80 | −0.560 | −0.16 |

Mechanism autopsy (honest, evaluator-derived):
1. The plain dollar-neutral low-vol book is a disguised short-market position exactly as the
   pre-registered kill anticipated: β(net, EW-mkt) ≈ −0.30, bear Sharpe +1.3/bull −1.0.
2. The engine's |net| ≤ 0.25 cap makes true beta-neutrality STRUCTURALLY unreachable for a
   low-vol book at gross 1 (balancing wants net ≈ +0.45; the cap stops at +0.25), leaving a
   floor of ≈ −0.15…−0.20 residual beta — a permanent drag in a bull-heavy IS window.
3. Even after stripping sector and beta drag as far as the caps allow, the residual
   cross-sectional low-risk alpha on THIS universe is positive pre-2015 (+0.50…+0.56
   sub-Sharpe) and decisively negative 2015→2024 (−0.38…−0.73) in every variant. The
   Binance-selected universe is the lottery basket itself — its high-vol end contains the
   structural compounders — the worst known habitat for the anomaly, and the IS window says so.
4. What did hold: cost thesis (ann turnover 3–13×, 1×→2× degradation ≤ 0.08 Sharpe) and
   breadth (21–24 names/side vs floor 5). The family fails on alpha, not on deployability.

Plateau verdict: the "widest contiguous positive plateau" of the selection rule is EMPTY.
Falsifier (a) — every config ≤ 0 @1× — fires; (b) would fire for any selected config.
Per pre-registration this kills the family. No further in-family variants will be mined.

# PIVOT REQUEST (the one documented pivot) — to backup 1: t05-shorthorizon-reversal-v1

Registration pre-brief for orchestrator approval (no backup-family experiment will run before
the registry approval line exists):

- Family: Short-horizon reversal (plain, OWN-NAME — menu #2). Mechanically distinct from
  team-03's sector-basket-relative reversion: the signal is each name's own trailing 1–5 day
  return, cross-sectionally ranked; NO sector baskets, NO sector residualization anywhere.
- Mechanism (2–3 sentences): 1–5 day losers bounce and winners fade; providers of liquidity
  earn the premium impatient traders pay for immediacy. In a retail perp universe, gap-chasing
  order flow overshoots single names on multi-day horizons; ranking own-name short-horizon
  returns and fading them harvests the correction, with tranching/smoothing to keep daily
  turnover survivable at 6 bps/side.
- Economic rationale: the reversal premium is compensation for absorbing uninformed flow
  imbalances; it is strongest where flow is retail, attention-driven, and concentrated —
  exactly this universe. It is also the natural complement of the falsified family: it needs
  no beta tilt (rank book is beta-flat-ish because the sort key is a return, not risk), so the
  net-cap constraint that structurally killed BAB does not bind it.
- Expected regime behavior: best in high-vol chop and stress (overshoots are larger); positive
  but thinner in calm bulls; main risk is trending tapes where losers keep losing (momentum
  regimes) and the 2020-03-style cascade where reversal buys falling knives — costs compound
  at daily cadence, so the cost axis is the declared kill-axis.
- Falsifier (pre-registered for the new family): (a) net IS Sharpe @1× ≤ 0 across the whole
  pre-registered formation/tranche grid; (b) Sharpe@2× ≤ 0 for every config with Sharpe@1× > 0
  (edge exists but cannot survive doubled costs — undeployable); (c) 2015→2024H1 sub-Sharpe
  ≤ 0 for the selected config; (d) breadth floor unattainable. Budget: ≤ 12 further material
  experiments (10/40 used).

**ORCHESTRATOR RULING: short-horizon reversal VETOED (already another team's approved
family). Pivot NOT spent. Pre-approved redirect accepted → menu #6.**

---

# PART III — PIVOT registration pre-brief: t05-volume-liquidity-anomalies-v1 (menu #6)

Written 2026-07-17 BEFORE any family-#6 experiment (reg-004 in ledger). Same discipline:
evaluator-only data access, ledger-before-result, plateaus over peaks, both cost tiers.

## Mechanism

Volume is the footprint of attention and liquidity demand. Three seeded sub-mechanisms,
all OHLCV-only, none using own-name return ranks or sector baskets as the sort key:
1. **Abnormal-volume attention premium (anchor; Gervais–Kaniel–Mingelgrin class):** names
   whose recent volume is abnormally high vs their own trailing distribution experience a
   visibility shock; the induced demand/coverage shift predicts drift over the following
   1–4 weeks. Signal: cross-sectional rank of formation-window mean log(volume /
   trailing-median volume). SIGN IS A PRE-REGISTERED EMPIRICAL AXIS: classic GKM says long
   high-abnormal-volume; retail-attention overpricing (Barber–Odean) says fade it. Whichever
   sign the anchor shows must hold across the ENTIRE formation/holding/window grid — a sign
   that flips across the grid falsifies the sub-mechanism (no post-hoc sign cherry-picking).
2. **Amihud illiquidity premium:** ILLIQ = trailing mean of |ret|/dollar-volume; illiquid
   names must pay a return premium. Slow-moving, near-zero turnover.
3. **Volume-price divergence:** volume-flow direction (sum of sign(ret)×relative-volume)
   diverging from the price path over the same window signals under/over-participation;
   long flow-stronger-than-price, short flow-weaker-than-price.

## Economic rationale

This universe is Binance's selection of retail-favorite US names — attention flows are the
selection criterion itself. Attention shocks move ownership breadth and option/perp
activity; liquidity premia persist because arbitraging them requires warehousing illiquidity.
All three sub-mechanisms are cost-plausible at daily cadence: abnormal-volume signals are
tranched over multi-day holding windows; ILLIQ is nearly static.

## Expected regime behavior

Attention premium: strongest in high-attention regimes (melt-ups, stress) when volume shocks
are large and informative; weaker in quiet tape. Amihud: slow harvest, hurt in liquidity
crises (2020-03) when illiquid names gap down together. Divergence: chop-friendly,
trend-vulnerable. The book is roughly beta-flat by construction (volume sort keys are not
risk ranks), so the net-cap constraint that structurally killed BAB should NOT bind — mean
net ≈ 0 expected; this will be verified in the evaluator output.

## Parameter plan (pre-registered grid)

| Axis | Range | Rationale |
|---|---|---|
| Trailing volume window W | 60d (120d robustness) | own-name volume baseline; median for robustness to splits/spikes |
| Formation F | {1, 5} days | event-shock vs week-integrated attention |
| Holding/tranche H | {5, 10, 20} days (rolling mean of daily rank-weights) | GKM horizon 1–4 weeks; H controls turnover |
| ILLIQ window K | {126, 252} | slow characteristic |
| Divergence window D | {20, 60} | flow-vs-price integration horizons |
| Weighting | rank-linear symmetric (as Part I §3), direction = long HIGH sort key unless the pre-registered sign axis resolves negative | breadth + turnover |

## Selection rule (pre-registered)

1. Anchor sub-mechanism = abnormal volume. Amihud and divergence get 1–2 probes each; the
   sub-mechanism taken forward is the one with the widest same-sign plateau (net Sharpe > 0
   at BOTH tiers across its grid), not the highest single number. 2. Within it: pick the
   plateau CENTER of (F, H); ties → larger H (lower turnover). 3. A secondary sub-mechanism
   may be BLENDED (50/50 rank-average) only if both are independently positive at both tiers
   and the blend improves Sharpe@2× by ≥ +0.10 over the better leg. 4. Breadth ≥ 5/side
   mandatory. 5. Sign discipline per the mechanism section.

## Falsifiers (pre-registered kills for this family)

(a) every grid config ≤ 0 net Sharpe @1×; (b) any config positive @1× has Sharpe@2× ≤ 0
(cost-fragile — undeployable); (c) selected config's 2015→2024H1 sub-Sharpe ≤ 0; (d) sign
instability across the anchor grid (see mechanism §1); (e) breadth floor unattainable.
Budget: ≤ 12 material experiments (exp-011 onward; 10/40 used pre-pivot).

## PART III results (exp-011…exp-021; all numbers = evaluator `run_is`, archived in out/scratch/)

- Sub-mechanism 1, abnormal volume (exp-011…014): DEAD. Long-high uniformly negative @1×
  (−0.153…−0.327) across the full F/H grid; per-cost-tier degradation 0.2–0.3 Sharpe at
  26–54× turnover implies gross alpha ≈ +0.16 at best — smaller than its own cost bill; the
  fade direction is gross-negative (mirror arithmetic), so no sign flip was run or claimed.
- Sub-mechanism 3, volume-price divergence (exp-017/018): DEAD. −0.373 (D=20), −0.533
  (D=60); trend-vulnerable exactly as pre-registered (bull −0.54/−0.90).
- Sub-mechanism 2, Amihud illiquidity: ALIVE and robust —

| exp | config | Sharpe@1× | Sharpe@2× | maxDD | turn | 2010→15 | 2015→24H1 | β(net,mkt) |
|---|---|---|---|---|---|---|---|---|
| 015 | ILLIQ K=126 rank | +0.272 | +0.258 | −0.447 | 1.7 | +0.248 | +0.283 | +0.18 |
| 016 | **ILLIQ K=252 rank (SELECTED)** | **+0.350** | **+0.342** | **−0.429** | **0.9** | **+0.255** | **+0.397** | **+0.18** |
| 019 | ILLIQ K=504 rank | +0.246 | +0.240 | −0.452 | 0.6 | +0.191 | +0.272 | +0.18 |
| 020 | inverse-$-volume (isolation control) | +0.115 | +0.109 | −0.585 | 0.7 | −0.117 | +0.224 | +0.08 |
| 021 | ILLIQ K=252 quantile 15/15 | +0.281 | +0.272 | −0.406 | 1.0 | +0.202 | +0.319 | +0.15 |

Selection-rule resolution (mechanical): plateau {126,252,504} all-positive at both tiers →
center K=252. Quantile variant fails the ≥+0.10 adoption rule → rank-linear kept. Blend rule
not triggered (only one positive sub-mechanism). Falsifiers (a)–(e): all cleared.
Mechanism isolation: the |ret|/$vol numerator matters — the static size control (exp-020)
delivers a third of the Sharpe and is negative pre-2015. The premium is price-impact
illiquidity, not merely small-vs-big.

---

# FINAL SPEC — t05-volume-liquidity-anomalies-v1 / Amihud illiquidity rank book
# (QE builds from THIS section only; every parameter fixed; no discretion left)

`build_raw_weights(pn, aux)` — pure, deterministic, `aux['seed']` accepted but unused
(no randomness anywhere).

1. Inputs: `close = pn['close']`, `volume = pn['volume']` (dates×tickers, NaN on absent
   bars; ticker set FROM PANEL COLUMNS at runtime — never hard-coded). No other panel, no
   VIX, no sector_map, no ret_fwd (not in the interface anyway).
2. Daily returns: `ret = close.pct_change(fill_method=None)` — NaN preserved, no padding.
3. Dollar volume: `dollar = (close * volume)` masked to NaN where `<= 0` (zero-volume or
   missing bars never enter the mean).
4. Amihud illiquidity: `illiq = (ret.abs() / dollar).rolling(252, min_periods=126).mean()`
   — rolling mean skips NaN terms; a name needs ≥126 valid (ret, dollar) days inside the
   trailing 252-row window to be eligible (ragged starts enter after ~6 months of history).
5. Eligibility mask at row t: `illiq` non-NaN AND `close` non-NaN at t. Ineligible = NaN
   raw weight (engine maps NaN→flat 0).
6. Cross-sectional weights, LONG ILLIQUID / SHORT LIQUID, rank-linear symmetric:
   `rank = illiq.rank(axis=1, method='average')` over eligible names (ascending: 1 = most
   liquid), `N_t` = eligible count, `raw_t,i = rank_t,i − (N_t + 1)/2`. Most illiquid name
   gets the largest positive weight; book is dollar-neutral pre-caps by symmetry. Row scale
   is irrelevant (engine gross-normalises); emit the centered ranks as-is.
7. No tranching, no smoothing, no beta/sector adjustment, no sign conditioning, no regime
   logic. The engine owns gross=1, |w_i|≤0.10, |net|≤0.25, shift(1), costs, vol-target.

Expected IS metrics (evaluator, exp-016 artifact `results_b6`/`results_b5`… archived in
`out/scratch/results_b5_amihud_divergence.json`): Sharpe@1× +0.350, Sharpe@2× +0.342,
maxDD −0.429, ann turnover 0.9, breadth 24/24 (floor 5), mean net 0.000, mean gross 1.000,
regimes bull +0.410 / bear +0.593 / chop −0.178, total IS months 174. The QE's `team-run`
must reproduce these to the digit; any drift = implementation defect.

Honest caveats (for the record, no action required): the book is quasi-static — a
persistent long-illiquid/short-mega tilt with β(net,mkt) ≈ +0.18 and a melt-up-loving
profile (2020–21 core +1.66); chop is its weak regime (−0.18); the +0.35 IS Sharpe is
modest and the holdout has a wide noise floor at 24 monthly points. This is the family's
genuine, cost-immune plateau — not a laundered peak.

