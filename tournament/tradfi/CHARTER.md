# tradfi-cup-01 — Tournament Charter

Ten independent teams compete to build the best daily market-neutral-ish long/short portfolio
over the Binance `TRADIFI_PERPETUAL` single-company stock universe. Kaggle/Numerai spirit:
frozen data, sealed holdout, one submission per team, best holdout performance wins and deploys
to paper trading. This charter is BINDING for every agent in the tournament.

## 1. Objective & spirit

- Objective metric: **net Sharpe** (monthly-summed, √12-annualised, after costs). Never raw
  return, never beating buy-and-hold.
- Find ONE deployable strategy per team. A DNF (did-not-finish) is honorable; submitting a
  strategy you know is overfit is not.
- **Performance failure is not integrity failure.** A weak result loses; only cheating
  disqualifies.

## 2. Roster & roles

- 10 teams: `team-01` … `team-10`. Each team = one Quant Researcher (QR, model Fable) + one
  Quant Engineer (QE, model Opus). No cross-team communication of any kind.
- Orchestrator: coordinates phases, owns the sealed holdout, resolves family collisions,
  freezes submissions, runs Stage 2, confirms integrity findings.
- Tournament Critic (model Fable, read-only): audits every submission before Stage-1 ranking.

## 3. Substrate & execution contract (organizer-owned)

- Universe: the frozen IS snapshot's tradable set (Binance TradFi single-stock perps with
  Yahoo total-return history; ~69 names), point-in-time ragged starts, never forward-filled.
- Bars: US-trading-day DAILY. Decide at close[t], fill at next open[t+1] (engine applies the
  `.shift(1)`; strategies emit same-bar decisions).
- Costs: 6 bps/side taker+slippage on |Δweight| turnover (`COST_SIDE = 0.0006`); 2× cost is a
  published sensitivity.
- Organizer-owned book construction (`tournament.engine.normalize_and_cap`): gross-normalise
  to 1.0 → per-name cap |w_i| ≤ 0.10 → net cap |Σw| ≤ 0.25 → portfolio vol-target 15%/yr
  (63d lookback, max leverage 5×). Teams emit RAW signed weights ONLY — never fills,
  positions, PnL, or scores.
- Breadth validity floor: median active names per side ≥ 5 over the IS window (Critic-checked).

## 4. Windows & visibility

| Window | Range | Visibility |
|---|---|---|
| IN-SAMPLE | 2010-01-01 → 2024-06-30 | Teams: full access via the frozen snapshot |
| HOLDOUT | 2024-07-01 → 2026-06-30 | SEALED. Orchestrator-only, run ONCE per finalist |
| Quarantine | 2026-07-01 → paper start | Nobody trades or scores it |

- The holdout tail rides the Binance perp splice (the traded instrument) and charges perp
  **funding** (−w·f on the held book) where available — perps onboarded 2026.
- Teams get ZERO holdout views. There is no feedback channel: no metrics, no pass/fail, no
  hints, before the final report.
- The tournament does NOT use `core_tradfi.OOS_CUTOFF`; its own constants live in
  `analysis/portfolio/tradfi/tournament/constants.py` and are immutable after Phase-0 freeze.

## 5. Data authorization

Teams may read ONLY:
- `tournament/tradfi/data_is/` — the frozen IS snapshot (OHLCV per name + VIX), reached
  exclusively through the evaluator (`cli.py team-run`, `tournament.engine.load_is_panels`).
- `tournament/tradfi/CHARTER.md`, `config.toml`, `FAMILY-MENU.md`, `registry.jsonl`, their own
  `teams/team-NN/` tree, and the evaluator source in `analysis/portfolio/tradfi/tournament/`.
- Approved substrate modules importable from team code: `core_tradfi` (constants/metric
  helpers), `neutralize`, `universe_tradfi`. Plus numpy/pandas/scipy/stdlib-math.

PROHIBITED — reading, importing, grepping, or referencing (mechanically enforced by the static
scan, independently re-checked by the Critic):
```
data/                       (the full store — holds holdout bars)
data_live_tradfi/           data/funding_rates/
diary-portfolio-tradfi/     BASELINE_TRADFI.md          reports-tradfi/
analysis/portfolio/tradfi/iter_*.py                     oos_forensic.py
splice_loader.py            reconcile_basis_tradfi.py   live_tradfi.py
live_weights_tradfi.py      tournament/tradfi/MANIFEST.sha256.json (edit = tamper)
analysis/portfolio/tradfi/tournament/holdout.py
tournament/tradfi/teams/<any other team>/               tournament/tradfi/critic/
tournament/tradfi/results/
```
- NO network access in team code. NO file reads in team code (data arrives as function
  arguments). NO subprocesses. NO new data ingestion of any kind.
- The IS snapshot is SHA-256 manifest-bound; every evaluator load re-hashes it.

## 6. Mechanism-family registration & diversity

- Before building anything, each QR registers ONE mechanism family (short pre-brief:
  mechanism, economic rationale, expected regime behavior, falsifier). The orchestrator
  approves or vetoes: first-come-first-served on overlap; vetoed teams redraw (≤2 rounds).
- `tournament/tradfi/FAMILY-MENU.md` seeds ~12 distinct families. Off-menu proposals welcome.
- **RESERVED (not registrable): bear-gated TSMOM overlays on multi-horizon momentum** — that
  is the incumbent production book's family.
- One documented pivot per team is allowed before freeze (register the new family; the old
  one frees up).

## 7. Strategy interface & leak-proofing contract

- `teams/team-NN/strategy.py` exposes exactly:
  `build_raw_weights(pn, aux) -> pd.DataFrame` where `pn` is
  `{'open','high','low','close','volume'}` (dates×tickers) and `aux` is
  `{'vix': Series, 'sector_map': dict, 'seed': int}`. Return raw signed weights; NaN = flat.
- Derive the ticker set from the panel columns at runtime — never hard-code names.
- Strategies must be PURE and DETERMINISTIC functions of their inputs (seed any randomness
  from `aux['seed']`).
- Mandatory mechanical harness (`cli.py audit`): truncated-replay equivalence, future-bar
  corruption, same-bar perturbation, determinism, static import/path scan. ALL must pass to
  freeze; the leaderboard and Critic re-run them independently.

## 8. Research discipline

- `experiments.jsonl` is append-only: one JSON line per material experiment (feature, param
  set, model variant, risk overlay), written BEFORE reading its result. The Critic audits
  coherence (count, timestamps, monotonicity) against the brief.
- Budget: ≤ 40 material experiments per team. Trial counters never reset (a pivot continues
  the same ledger).
- `is_report.md` numbers come ONLY from `team-run` output (`out/is_metrics.json`). A number
  in prose that does not exist in an artifact is a defect.
- Negative results are reported with the same precision as positive ones.

## 9. Stage 1 — freeze, Critic gate, ranking

1. QE freezes via `cli.py freeze` (full audit + SHA-bind every source file into
   `submission.json`). Post-freeze edits = disqualification (`post-freeze-mutation`).
2. Critic audits ALL submissions. Verdicts: **PASS** / **BLOCK-PENDING-FIX** (mechanical
   defects only — interface mismatch, missing artifact, SHA drift, harness failure, breadth
   floor; ONE fix round, then PASS or FAIL) / **FAIL** (integrity code + evidence).
3. Orchestrator reruns every PASS team canonically (`cli.py leaderboard`): byte-identical
   reproduction of `out/net_is.csv` + `out/is_metrics.json` required.
4. Ranking (LOCKED): **net IS Sharpe @1× cost**; ties: 2×-cost Sharpe, then maxDD (less
   negative). **Top 4 advance to Stage 2.**

## 10. Stage 2 — sealed holdout & winner

- Orchestrator-only, doubly gated (`--confirm-holdout` + env flag), every run journaled.
- Each finalist's FROZEN code runs once, canonically, over 2024-07-01 → 2026-06-30 with the
  perp splice and funding ON. The IS rows of that run must reproduce the frozen stage-1 net
  bit-for-bit (causality cross-check; mismatch = integrity finding).
- **WINNER (LOCKED): best net holdout Sharpe, funding on.** Published sensitivities
  (informational, never re-ranking): funding off, 2× cost, ex-PAYPUSDT.
- The final report states the Sharpe noise floor (24 monthly points) alongside the ranking.

## 11. Integrity & disqualification

Enumerated codes (a DQ requires one code + a cited evidence path; Critic alleges,
orchestrator confirms):
`data-boundary-violation` · `prohibited-path-access` · `network-access` ·
`post-freeze-mutation` · `reproduction-failure` · `family-misrepresentation`.
Free-text criticism is never a DQ. Weak performance is never a DQ.

## 12. Winner deployment

The winner deploys to a SECOND paper desk (`run_tradfi_tournament_paper.py`, own DB
`data/tradfi_tournament_paper.db`, own equity CSV/log) alongside — never touching — the
incumbent production paper desk.

## 13. Immutability & amendments

`CHARTER.md`, `config.toml`, `data_is/` + `MANIFEST.sha256.json`, and the evaluator package
are FROZEN at the Phase-0 commit. Any amendment after that is a journaled event
(`journal.jsonl`) with rationale, applied uniformly to all teams, and never retroactively
changes a locked ranking rule.
