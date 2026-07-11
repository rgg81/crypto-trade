# ORCHESTRATOR BRIEF — Market-Neutral Track v3 (MN3): the TWO-YEAR-HOLDOUT restart

**Authorized by user 2026-07-11.** Supersedes ORCHESTRATOR_BRIEF_MN.md (v2 concluded: SURVEY-001
= 5 families / 1 survivor; CONFIRMATION-A = PARTIAL on a 6-month window the user judged — and the
evidence confirmed — too short to trust). The v2 lesson IS the v3 charter: a 6-month holdout
cannot even contain the regimes needed to judge an all-weather book.

## THE METHODOLOGY (user directive, verbatim intent — the track lifecycle)
1. **Stage 1 — IS development:** diagnostics + explorations, pre-registered, IS-only.
2. **Stage 2 — the TWO-YEAR sealed holdout:** one reveal per family, ever, against a frozen map.
   A model must GENERALIZE ACROSS TWO YEARS before anything else happens.
3. **Stage 3 — six-month forward paper-trade** (recompute architecture; pre-registered gates).
4. **Stage 4 — live real money** (user decision; small size first).
No stage may be skipped or shortened; failing any stage terminates the family (no rescue).

## Splits
- **IS = 2020-01-01 → 2024-06-30** (4.5 yr; covers COVID, 2021 mania, 2022 collapse, 2023 chop,
  2024-H1 mania — all regime buckets present).
- **HOLDOUT = 2024-07-01 → 2026-06-30 (2 years, SEALED)** — one family-token reveal, ever.
- Data after 2026-06-30 accrues for Stage-3 paper trading.
- New split module mn3_split.py (MN3_IS_CUTOFF = 2024-07-01); the v2 mn_split (2026-01-01) and
  old-track cutoffs must be structurally unusable in mn3 code.

## CONTAMINATION MAP (disclose in every brief — no virgin 2-year window exists in this dataset)
- Old track: 2020→2025-03 mined (vol_low family); 2025-03→2026-07 REVEALED for vol_low-family
  books. vol_low family CLOSED permanently.
- MN v2: 2020→2025-12 was IS for the 5-family diagnostics (carry, coint, crowding, taker,
  resid-mom); 2026-01→2026-07 REVEALED for the funding-carry family (A3-1, PARTIAL).
- Therefore: (a) for GENUINELY NEW mechanism families the holdout is sealed in the only sense
  achievable — never evaluated for that mechanism; regime-composition knowledge (2025-11→2026-07
  crash-heavy; 2026-H1 mania-free) leaks and is disclosed, with market-only bucketing and
  pre-registration as the defenses; (b) previously-probed families may re-enter ONLY with
  per-window contamination disclosure and explicit Critic discounting — funding-carry's
  2026-01→07 slice is fully revealed and can never count as evidence for that family;
  (c) killed-at-mechanism families (pairs-persistence, taker-standalone, resid-mom-standalone,
  OI-fade, vol_low) stay closed.

## ALL-WEATHER + CRISIS DOCTRINE (new, user-directed — built into every construction from birth)
1. **Three-state risk regime machine, pre-registered per construction:**
   - **NORMAL** — full book.
   - **STRESS** — gross throttled AND universe contracted toward the blue-chip core.
   - **CRISIS ("the model is lost")** — the book collapses to a BLUE-CHIP-ONLY minimal neutral
     core (BTC, ETH + top-liquidity majors) or flat; no alt exposure survives a black swan.
   State transitions driven by PAST-ONLY crisis indicators; hysteresis pre-registered; the
   machine's leak tests are mandatory (the SCUD/stateful-gate lessons apply).
2. **Crisis indicator suite (crypto-native — no VIX/DVOL feed exists in this repo; slot-in ready
   if the user adds Deribit DVOL / Volmex BVIV later):** cross-sectional realized-vol index z;
   median pairwise correlation spike (correlation-to-one = systemic event); aggregate |funding|
   dislocation; BTC single-candle gap detector; breadth collapse. Calibrated coverage-only
   (no Sharpe scans), falsified against IS crisis episodes (COVID 2020-03, 2021-05, FTX 2022-11).
3. **Blue-chip core, mechanically defined:** top-5 by trailing 90d dollar-volume among
   {BTC, ETH, BNB, SOL, XRP, + rank-eligible majors}, frozen rule not frozen list.
4. Neutrality doctrine unchanged and gated: beta-neutral (rolling + crash/mania-bucket),
   measured never assumed.

## Inherited methodology (all of it — v2's hard-won rules stay binding)
ALL AGENTS ON FABLE. Phase sweeps mandatory (tranche ensembles; phase-agnostic headlines).
Costs honest from candle one (5+2.5bps + funding; ground-truth 2× twins — analytic twins only
for stateless constructions). Market-only regime buckets. No-Sharpe-scan calibration.
Principle/relative-anchored gates (never fitted to revealed draws). Pre-registration + Critic
pre-flight/review + falsification arms + frozen decision maps; no post-hoc re-gating. Data
hygiene first (mn_datacheck pattern). Sample floors sized to frequency. The ENSEMBLE CAPSTONE
carries: ≥2 banked families → cross-family ensemble with a-priori weights; an ensemble holdout
reveal consumes every member's budget.

## SEEDED IDEA MENU v3 (orchestrator research 2026-07-11 — "most advanced hedge fund" mandate)
Industry context: market-neutral crypto funds gained ~14% in 2025 while directional lost; the
leading desks run ML-driven multi-strategy books with regime-adaptive risk. Ranked by prior ×
data-fit × cleanliness:
- **G. ML cross-sectional residual alpha (flagship):** LightGBM (the house's deepest-proven
  stack) predicting beta-RESIDUALIZED forward returns from neutralized features (funding level/
  momentum, OI structure, taker imbalance, vol structure, liquidity) — walk-forward monthly
  retrain, weekly tranche-ensemble rebal, strictly pre-registered feature list + HP region (the
  multiple-testing surface is the danger; the v1/v3-track discipline applies: explicit feature
  columns, seed ensembles, no per-run tuning).
- **H. Born-ensemble multi-sleeve MN composite:** 3-4 weak orthogonal sleeves (carry-like flow,
  OI-structure, vol-structure, liquidity provision proxy) combined at equal-risk from birth —
  the user's ensemble directive as a construction, not a capstone; each sleeve individually
  pre-registered with kill criteria.
- **I. Funding-carry v2 (contamination-disclosed):** the proven durable mechanism (funding leg
  positive 7/7 revealed months at 3× IS rate) re-instantiated under the crisis machine +
  blue-chip fallback; Critic discounts the revealed windows; holdout evidence for this family
  is structurally weaker — flagged.
- **J. Funding term-dynamics:** aggregate + cross-sectional funding momentum/mean-reversion
  (the funding SURFACE as signal, not just its level) — unprobed axis.
- **K. Event-conditioned books:** trade only inside high-dispersion windows (the E2 lesson:
  intraday MN must be born with turnover suppression).
Closed: vol_low, pairs-cointegration, taker-standalone, resid-mom-standalone, OI-fade.

## Namespaces & process
`analysis/portfolio/mn3_*.py`, `diary-portfolio-mn3/`, `briefs-portfolio-mn3/`. Engine: reuse
blind_engine.py (leak-proven, 105-test suite) — extensions only via the sanctioned opt-in
pattern with leak tests. Same team (QR/QE/risk-engineer/Critic — all Fable), same cadence.
**STARTING POINT:** QR writes diary-portfolio-mn3/PLAN.md — the crisis-machine spec, 3-5
construction sketches from the menu, cheapest-to-falsify diagnostics with kill criteria on the
NEW IS (2020→2024-06), diagnostic order, QE infrastructure asks (mn3_split, crisis indicators,
regime machine).
