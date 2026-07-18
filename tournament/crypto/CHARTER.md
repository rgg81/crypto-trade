# crypto-cup-01 — Tournament Charter

Ten independent teams compete to build the best 8h-bar long/short portfolio over the weekly
top-40 Binance USDT crypto perpetuals. Kaggle/Numerai spirit: frozen data, sealed holdout, one
submission per team, best holdout performance wins and deploys to a 6-month paper desk. This
charter is BINDING for every agent in the tournament.

## 1. Objective & spirit

- Objective metric: **net Sharpe** (monthly-summed, √12-annualised, after ALL costs: taker fee,
  liquidity-scaled slippage, and funding P&L). Never raw return, never beating buy-and-hold.
- The goal is the strategy that GENERALIZES best — performs across bull, bear, and chop. The
  sealed holdout and the paper desk reward exactly that.
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

- Universe: **weekly point-in-time top-40** USDT perps by trailing 7-day dollar volume
  (21-candle mean quote-volume, `.shift(1)`, refreshed at Monday 00:00 UTC candles), computed
  on the FULL ~500-symbol pure-crypto pool (stablecoins, tokenized stocks, metals, index
  baskets, pre-market names excluded). Survivorship-safe: delisted coins are in when they
  ranked. The mask ships in the snapshot (`aux['eligibility']`) — organizer data, past-only.
- Bars: Binance-perp **8h** (00/08/16 UTC opens). Decide at close[t], fill at open[t+1] (the
  engine applies the `.shift(1)`; strategies emit same-bar decisions). Rebalance as often as
  every candle; costs punish over-trading naturally.
- **Weekly floor (organizer-enforced):** weights outside the current top-40 list are zeroed at
  decision time — a coin dropping out at a Monday refresh is force-closed at the next candle
  open (≤8h after the refresh) and the close-out turnover is costed.
- Costs: 5 bps/side taker (`COST_SIDE = 0.0005`) **plus** liquidity-scaled slippage per side:
  `clip(1.0 + 20.0/dvol_$M, 1, 10)` bps from the trailing 90-candle dollar volume (past-only).
  The published stress tier (`2x`) doubles BOTH.
- **Funding P&L is charged natively over the whole backtest**: every funding event with
  timestamp in `(open[t], open[t+1]]` is summed and charged to the book held during candle t
  (`−w·funding`; longs pay positive rates). Symbols on 4h/1h funding intervals pay every event.
- Organizer-owned book construction (`portfolio_tournament.engine.normalize_and_cap`):
  eligibility mask → gross-normalise to 1.0 → per-name cap |w_i| ≤ 0.10 → net cap |Σw| ≤ 0.25 →
  portfolio vol-target 1%/candle (84-candle lookback, max leverage 3×). Teams emit RAW signed
  weights ONLY — never fills, positions, PnL, or scores.
- Breadth validity floor: median active names per side ≥ 5 over the IS window (Critic-checked).

## 4. Windows & visibility

| Window | Range | Visibility |
|---|---|---|
| IN-SAMPLE | 2020-01-01 → 2024-06-30 | Teams: full access via the frozen snapshot |
| HOLDOUT | 2024-07-01 → 2026-06-30 | SEALED. Orchestrator-only, run ONCE per finalist |
| Quarantine | 2026-07-01 → paper start | Nobody trades or scores it |

- Teams get ZERO holdout views. There is no feedback channel: no metrics, no pass/fail, no
  hints, before the final report.
- The holdout panel WILL contain coins the IS panel never had (new listings entering the
  top-40 after 2024-06). **Strategies must be column-set agnostic** — derive symbols from the
  panel columns at runtime, never hard-code names or column counts (harness WIDENING check).
- Stage-2 runs twice per finalist: a causality run on the frozen IS columns (its IS rows must
  bit-reproduce the frozen stage-1 net) and the canonical scoring run on the full holdout
  universe. The tournament constants live in `analysis/portfolio_tournament/constants.py` and
  are immutable after the Phase-0 freeze.

## 5. Data authorization

Teams may read ONLY:
- `tournament/crypto/data_is/` — the frozen IS snapshot (11-column 8h klines + funding + OI
  per symbol + the eligibility mask), reached exclusively through the evaluator
  (`cli.py team-run`, `portfolio_tournament.engine.load_is_panels`).
- `tournament/crypto/CHARTER.md`, `config.toml`, `FAMILY-MENU.md`, `registry.jsonl`, their own
  `teams/team-NN/` tree, and the evaluator source in `analysis/portfolio_tournament/`
  (EXCEPT `holdout.py`).
- The ONLY importable substrate module from team code: `teamlib` (metric helpers). Plus
  numpy/pandas/scipy/stdlib-math.

The data menu handed to `build_raw_weights(pn, aux)`:
- `pn`: open, high, low, close, volume, quote_volume, trades, taker_buy_volume,
  taker_buy_quote_volume — candle×symbol panels (taker-flow imbalance is derivable from the
  last two for free).
- `aux`: `funding` (per-candle summed funding events — candle t's events are knowable at its
  close, exactly like close[t]); `oi`, `oi_value` (open interest, [T,T+8h) same-bar snapshot);
  `tt_ls_accounts`, `tt_ls_positions`, `ls_accounts`, `taker_ls_vol` (Binance top-trader /
  global long-short positioning ratios, same-bar); `eligibility` (the organizer top-40 mask,
  bool, past-only); `seed` (int — seed ALL randomness from it). OI/ratio panels are NaN where
  history doesn't exist (pre-2020-09, dead names) — NaN-tolerance is mandatory.

PROHIBITED — reading, importing, grepping, or referencing (mechanically enforced by the static
scan, independently re-checked by the Critic):
```
data/                        (the full store — holds holdout bars)
pf_data/                     data/funding_rates/          data/open_interest/
analysis/portfolio/          analysis/portfolio_v2/       analysis/portfolio_tournament/holdout.py
src/crypto_trade/            diary-portfolio*/            briefs-*/         reports-*/
BASELINE_*.md                iter_*.py                    features_*/
tournament/crypto/MANIFEST.sha256.json (edit = tamper)
tournament/crypto/teams/<any other team>/                 tournament/crypto/critic/
tournament/crypto/results/   tournament/crypto/_build/
any URL (http/https, fapi., binance.com, binance.vision)  .env / testnet credentials
```
- NO network access in team code. NO file reads in team code (data arrives as function
  arguments). NO subprocesses. NO new data ingestion of any kind.
- The IS snapshot is SHA-256 manifest-bound; every evaluator load re-hashes it.

## 6. Mechanism-family registration & diversity

- Before building anything, each QR registers ONE mechanism family (short pre-brief:
  mechanism, economic rationale, expected regime behavior, falsifier). The orchestrator
  approves or vetoes: first-come-first-served on overlap; vetoed teams redraw (≤2 rounds).
- `tournament/crypto/FAMILY-MENU.md` seeds ~14 distinct crypto-native families. Off-menu
  proposals welcome.
- **There are NO reserved families.** Teams cannot read the production book's code (clean
  room, §5), but independently converging on a similar mechanism is legitimate. Diversity is
  enforced BETWEEN teams only, via FCFS registration.
- One documented pivot per team is allowed before freeze (register the new family; the old
  one frees up). Pivot approvals are journaled AT choice time.

## 7. Strategy interface & leak-proofing contract

- `teams/team-NN/strategy.py` exposes exactly:
  `build_raw_weights(pn, aux) -> pd.DataFrame` (candle-index × symbol-columns, raw signed
  weights; NaN = flat). Derive the symbol set from panel columns at runtime.
- Strategies must be PURE and DETERMINISTIC functions of their inputs (seed any randomness
  from `aux['seed']`), and PAST-ONLY: every row's value computable from data at or before that
  row (aux rows for candle t are same-bar info, usable for the decision AT t).
- Mandatory mechanical harness (`cli.py audit`), ALL SIX must pass to freeze: static
  import/path scan, determinism, truncated-replay equivalence, future corruption (klines AND
  funding AND OI AND eligibility), same-bar perturbation, and widening (extra synthetic
  columns must not crash the strategy). The leaderboard freeze and the Critic re-run them
  independently.

## 8. Research discipline

- `experiments.jsonl` is append-only and **evaluator-stamped**: append one line per material
  experiment via `cli.py log-experiment --team NN --json '{...}'` (id, hypothesis, config)
  BEFORE reading its result. Hand-written timestamps are a defect. Budget: ≤ 40 material
  experiments per team; counters never reset (a pivot continues the same ledger).
- `is_report.md` numbers come ONLY from `team-run` output (`out/is_metrics.json`). A number
  in prose that does not exist in an artifact is a defect.
- Negative results are reported with the same precision as positive ones.
- Regime honesty: `team-run` reports per-regime Sharpe over the fixed crypto regime tags
  (COVID crash, 2020-21 bull, May-2021 crash, 2021 ATH run, 2022 bear, FTX-aftermath chop,
  ETF bull, post-halving chop). A strategy that only works in one regime should say so.

## 9. Stage 1 — freeze, Critic gate, ranking

1. The orchestrator freezes via `cli.py freeze` (registry-approved family REQUIRED + full
   audit + SHA-bind every source file into `submission.json`). Post-freeze edits =
   disqualification (`post-freeze-mutation`).
2. Critic audits ALL submissions. Verdicts: **PASS** / **BLOCK-PENDING-FIX** (mechanical
   defects only — interface mismatch, missing artifact, SHA drift, harness failure, breadth
   floor; ONE fix round, then PASS or FAIL) / **FAIL** (integrity code + evidence).
3. Orchestrator reruns every PASS team canonically (`cli.py leaderboard`): byte-identical
   reproduction of `out/net_is.csv` + `out/is_metrics.json` required.
4. Ranking (LOCKED): **net IS Sharpe @1× cost**; ties: 2×-stress Sharpe (cost AND slippage
   doubled), then maxDD (less negative). **Top 4 advance to Stage 2.** The board prints the
   Sharpe noise floor (54 monthly IS points) next to the ranking.

## 10. Stage 2 — sealed holdout & winner

- Orchestrator-only, doubly gated (`--confirm-holdout` + `CRYPTO_TOURNAMENT_ALLOW_HOLDOUT=1`),
  every run journaled BEFORE computing.
- Each finalist's FROZEN code runs canonically over 2024-07-01 → 2026-06-30 with funding ON on
  the full holdout universe (Run B), after the IS-replay causality run (Run A) and the
  eligibility mask-replay check both pass bit-exactly.
- **WINNER (LOCKED): best net holdout Sharpe, funding on.** Published sensitivities
  (informational, never re-ranking): funding off, 2× cost, 2× slippage.
- The final report states the Sharpe noise floor (24 monthly points) alongside the ranking.

## 11. Integrity & disqualification

Enumerated codes (a DQ requires one code + a cited evidence path; Critic alleges,
orchestrator confirms):
`data-boundary-violation` · `prohibited-path-access` · `network-access` ·
`post-freeze-mutation` · `reproduction-failure` · `family-misrepresentation`.
Free-text criticism is never a DQ. Weak performance is never a DQ.

## 12. Winner deployment

The winner deploys to a dedicated 6-month PAPER desk (dry-run `PortfolioEngine` via the
`strategy_module` seam; own DB/log/healthcheck; SHA-recheck of the frozen submission on every
recompute) alongside — never touching — the incumbent production desks.

## 13. Immutability & amendments

`CHARTER.md`, `config.toml`, `data_is/` + `MANIFEST.sha256.json`, and the evaluator package
are FROZEN at the Phase-0 commit. Any amendment after that is a journaled event
(`journal.jsonl`) with rationale, applied uniformly to all teams, and never retroactively
changes a locked ranking rule.
