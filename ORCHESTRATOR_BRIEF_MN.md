# ORCHESTRATOR BRIEF — Baseline-Blind MARKET-NEUTRAL Portfolio Track (MN, v2 restart)

**Authorized by user 2026-07-10.** Successor to the concluded baseline-blind L/S track
(diary-portfolio-blind/TRACK-CONCLUSION-2026-07-10.md). Fresh research line, fresh namespaces.

**MISSION:** invent and validate MARKET-NEUTRAL crypto perp portfolio strategies that perform in
ANY market condition — bull, bear, chop, crash, mania. Sharpe is the metric. True neutrality is
a hard requirement: **beta-neutral, not merely dollar-neutral** (the old track's books were
dollar-neutral with realized crash/mania beta — that is the failure mode to engineer away).

## Hard constraints (inherited + new)
1. **BASELINE-BLINDING (unchanged):** never read BASELINE_PORTFOLIO.md, analysis/portfolio/
   iter_*.py, diary-portfolio-top20/, sibling quant-portfolio*/metals/tradfi worktrees.
2. **OLD-TRACK SIGNAL BAN:** the vol_low / mid-vol cross-sectional family is CLOSED (concluded
   negative). The old track's diary MAY be read for METHODOLOGY only (leak tests, phase sweeps,
   gate anchoring, review discipline) — never for signal construction.
3. **ALL AGENTS RUN ON FABLE** (model="fable" on every dispatch). User mandate.
4. **DATA HYGIENE FIRST:** verify panel completeness before ANY backtest (the starvation bug
   corrupted 4.5 months of history and an OOS verdict). Live-feed-scoped guards; per-symbol
   tolerant fetches.
5. **Anti-leak discipline (tightened):**
   - New splits: **IS = 2020-01-01 → 2025-12-31. HOLDOUT = 2026-01-01 → present, SEALED** — one
     reveal per candidate FAMILY, ever. Final arbiter = forward paper-trade (recompute
     architecture, reusable from blind_paper_l1.py).
   - Contamination map (disclose in every brief): 2020→2025-03 heavily mined by prior tracks
     (new mechanism families OK); 2025-03→2026-07 was REVEALED for the old vol_low-family books
     (BURNED-REVEAL-2026-07-10.md) — regime knowledge exists (2025-11→2026-07 was crash-heavy);
     new-family evaluation there is discounted, not forbidden.
   - Pre-registration + adversarial Critic pre-flight/review on every exploration; falsification
     arms; frozen decision maps; NO post-hoc re-gating, ever.
6. **Phase sweeps mandatory:** any rebal cadence > 1 candle reports the FULL phase-offset
   distribution; headline = phase-agnostic mean (or tranche ensemble); single-phase numbers are
   never load-bearing. ([[feedback_rebal_phase_first_order_axis]])
7. **Neutrality is measured, not assumed:** every book reports realized rolling beta to BTC and
   ETH, crash-bucket and mania-bucket beta, and the beta-hedge mechanics. Gate on it.
8. **Costs honest from candle one:** taker 5bps + slip 2.5bps + funding on every leg; 2×-cost
   twin always; trade-rate/sample floors sized to the strategy's frequency.

## Data available (worktree, shared trunk)
8h OHLCV+taker_buy_volume for ~747 perps 2020→now (1h/15m fetchable on demand); funding rates
(~790 symbols); **OI history via `fetch-oi` / data.binance.vision archives (UNTAPPED — use it)**.
NOT available: spot, cross-exchange, liquidation prints, order book.

## SEEDED IDEA MENU (orchestrator research, 2026-07-10 — evaluate, don't worship)
Ranked by prior × data-fit × novelty-vs-old-track:
- **A. Funding-carry market-neutral basket:** long low/negative-funding perps vs short
  high-funding perps, BETA-HEDGED; harvests the funding spread (a paid-in-all-regimes flow) +
  positioning mean-reversion. Industry delta-neutral books reported ~19% ann. at <2% maxDD in
  2025. Watch: funding cross-section concentration, regime flips in aggregate funding.
- **B. Cointegration pairs/basket stat-arb** on top-liquidity perps: Engle-Granger/Johansen with
  DYNAMIC re-estimation + structural-break kill-switches; 1h frequency for sample size;
  beta-neutral by construction. Academic results show persistent short-term inefficiencies;
  the known killer is regime breaks — the kill-switch design IS the research.
- **C. OI/leverage-crowding fade:** crowding score = ΔOI × funding extremity × taker-imbalance;
  fade the crowded side cross-sectionally, beta-neutral. High-OI + extreme-funding states
  precede liquidation-cascade reversals; standalone cascade alpha is cost-marginal, so the edge
  must come from the cross-sectional portfolio form. Needs fetch-oi backfill first.
- **D. Taker-flow cross-section:** taker_buy_ratio momentum/reversal (already in the panel,
  never used by the old track), beta-neutralized.
- **E. Short-horizon cross-sectional reversal at 1h–4h,** neutralized and cost-gated (old track
  found reversal long-side-only at 8h; frequency + neutralization change the object).
- **F. Meta-layer (later):** dispersion-conditional gross scaling (signal-rich regimes get more
  gross) — regime-adaptive without directionality.
Do NOT lead with lead-lag diffusion (dead at 8h in the old track) or low-beta/BAB tilts.

## Process
Same team (QR / QE / risk-engineer / Critic — all Fable), same cadence discipline
(EXPLORATION cheap and falsifiable → CONFIRMATION rare), diagnostics before constructions
(IC/spread probes with market-only bucketing). Namespaces: `analysis/portfolio/mn_*.py`,
`diary-portfolio-mn/`, `briefs-portfolio-mn/`. Engine: REUSE blind_engine.py (leak-proven);
QE extends it for beta-hedged weights (new leak tests required).

**STARTING POINT:** QR writes `diary-portfolio-mn/PLAN.md` — sketch 3–5 constructions from the
menu (+ any genuinely new angle), pick the cheapest-to-falsify diagnostic for each, propose the
diagnostic order. Then run DIAGNOSTIC-001.

---

## ADDENDUM 2026-07-10 — ENSEMBLE CAPSTONE (user-directed, pre-registered NOW)

**User directive:** "combine solutions, build an ensemble — this generalizes even more."

**The capstone construction, registered before any member field exists:** when ≥2 families hold
BANKED candidates (currently: A3-1; C/E2 surveying), register **EXPLORATION-ENSEMBLE** — the
cross-family combination book. Frozen principles, committed in advance:
1. **Weights chosen a-priori, never IS-optimized:** equal-risk (inverse trailing-vol) or plain
   equal-weight — pick ONE at registration from member vol statistics only; an IS-Sharpe-
   optimized weighting is mining and is banned.
2. **Members enter byte-frozen** as banked; no member re-tuning inside the ensemble.
3. **Gates:** the same frozen charter set (all 11 HARD incl. beta/bucket neutrality on the
   COMBINED book — member-level neutrality does not automatically compose if members share
   exposures; measured, not assumed).
4. **The falsifiable claim:** combined Sharpe ≥ best member's AND combined maxDD shallower than
   every member's, via measured member decorrelation. If members are too correlated to add
   anything, that is a FINDING (mechanism overlap), not a failure to tune away.
5. **Holdout governance (pre-registered to prevent budget gaming):** evaluating the ENSEMBLE on
   the sealed holdout consumes the one-forever reveal of EVERY member family simultaneously.
   The efficient use of the reveal budget is therefore likely ONE ensemble reveal instead of
   per-family reveals — but that decision remains the USER's, made after the field survey.
6. **Intra-family ensembling** (21-phase tranche staggering) remains mandatory at member level —
   the cross-family ensemble stacks ON TOP of it.
