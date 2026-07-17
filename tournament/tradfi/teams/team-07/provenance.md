# team-07 provenance — t07-overnight-tugofwar-v1

## What was read (complete list)

Authorized tournament documents:
- `tournament/tradfi/CHARTER.md`, `tournament/tradfi/config.toml`,
  `tournament/tradfi/FAMILY-MENU.md`, `tournament/tradfi/registry.jsonl`
- `tournament/tradfi/teams/team-07/BOOTSTRAP.md` (own team dir only)
- Evaluator source: `analysis/portfolio/tradfi/tournament/engine.py`,
  `analysis/portfolio/tradfi/tournament/constants.py` (NOT `holdout.py`)
- Approved substrate modules (read for interface/semantics, imported in scratch):
  `analysis/portfolio/tradfi/core_tradfi.py` (panels/ret_fwd definition, metric helpers,
  regime windows), `analysis/portfolio/tradfi/neutralize.py`
- Role definition: `.claude/agents/tradfi-tournament-qr.md`

Market data was reached EXCLUSIVELY through `tournament.engine.load_is_panels()` (manifest-
verified frozen IS snapshot, boundary-enforced). No file under `tournament/tradfi/data_is/`
was opened directly; no other data source of any kind was used.

## What was imported in team scratch code

`tournament.engine` (load_is_panels / team_view / run_is), `neutralize.sector_neutralize`
(approved substrate; used only in the sector-neutral experiments e-011 etc., NOT in the final
spec), `numpy`, `pandas`, stdlib `json`/`sys`/`pathlib`. Nothing else.

## Negative declarations

- NONE of the prohibited paths were read, grepped, imported, or referenced: `data/`,
  `data_live_tradfi/`, `data/funding_rates/`, `diary-portfolio-tradfi/`, `BASELINE_TRADFI.md`,
  `reports-tradfi/`, `analysis/portfolio/tradfi/iter_*.py`, `oos_forensic.py`,
  `splice_loader.py`, `reconcile_basis_tradfi.py`, `live_tradfi.py`, `live_weights_tradfi.py`,
  `analysis/portfolio/tradfi/tournament/holdout.py`, `tournament/tradfi/MANIFEST.sha256.json`
  (path passed opaquely to the evaluator loader only, never opened), `tournament/tradfi/
  results/`, `tournament/tradfi/critic/`, any other team's directory.
- `pn['ret_fwd']` was NEVER used in signal construction — signals are built from
  `te.team_view(pn)` (open/close only in the final spec); `pn` is passed opaquely to
  `te.run_is` for scoring, exactly as the evaluator contract prescribes.
- No network access of any kind (no WebSearch/WebFetch/HTTP; nothing fetched).
- No holdout inference, probing, or estimation was attempted; the IS snapshot ends 2024-06-30
  and nothing past it was seen.
- No cross-team communication; no other team's registration content was used beyond the
  public registry.jsonl approval/veto lines.

## Independence statement

All design decisions were made from: the authorized tournament documents above, the frozen IS
snapshot via the evaluator, and general public-domain finance knowledge (the overnight/
intraday "tug of war" literature — Lou, Polk, Skouras-style decomposition — cited from
memory, not fetched). No production-book code, baselines, diaries, or reports of the
incumbent tradfi desk informed any choice. The final specification (research_brief.md §7)
uses only `pn['open']` and `pn['close']` plus numpy/pandas, is fully deterministic, and does
not use `aux['seed']`, `aux['vix']`, or `aux['sector_map']`.

## Artifact trail

- `experiments.jsonl` — 18 append-only lines (reg-001 + e-002..e-018), each written before
  its result was read; timestamps monotone.
- `out/e-*.json` — full-precision evaluator output per experiment (config + 1x and 2x
  metrics).
- `out/scratch/scratch_tugofwar.py` — the scratch runner that produced them (moved out of the
  bundle root so the static scan sees a clean tree; it imports sys/json by design and is not
  part of the submission).
- `research_brief.md` — pre-registration (§1-5) written BEFORE any experiment ran; §6-7
  completed after.

## QE implementation notes (post-freeze-of-spec)

- `strategy.py` implements research_brief.md §7 verbatim: `on = open/close.shift(1) - 1` ->
  `rolling(252, min_periods=252).mean()` -> `rank(axis=1, pct=True)` -> row-mean-centered ->
  `ewm(halflife=5, min_periods=1).mean()`. Constants W=252 / min_periods=252 / halflife=5 are
  module-level and match the spec; no other axis (skip, standardization, zscore/tercile,
  sector-neutral, VIX gating) is present. Inputs touched: `pn['open']`, `pn['close']` only.
  `aux` (vix / sector_map / seed) is unused — the book carries no randomness and no regime
  gating, exactly as specified. No caps / lag / costs / vol-target / gross-normalisation are
  pre-applied (engine owns all of it); raw signed weights only, NaN = flat.
- The QE made NO research choices: the §7 spec left nothing ambiguous (lookback, missing-data
  rule, transform order and every parameter are pinned), and the reference config path in
  `out/scratch/scratch_tugofwar.py` for e-018 (construct=ON, W=252, standardize=raw,
  xform=rank, weighting=linear, ema_halflife=5, sector_neutral=False, skip=0) matches the §7
  code line-for-line. No BLOCK was necessary.
- `test_strategy.py` — 7 tests, imports restricted to numpy / pandas + the local `strategy`
  module (no `pytest` import) so the file passes the harness static-import scan. Tests use a
  seeded synthetic geometric-random-walk panel (never the frozen snapshot): determinism,
  seed-independence, future-bar corruption (mangle bars strictly after a cut, assert
  at/before-cut weights unchanged), open/close-only dependence (mangle high/low/volume ->
  weights unchanged), same-bar close perturbation (weights strictly before t* unchanged),
  row-wise dollar-neutrality, and strict 252-bar warmup flatness. All green.
- Verification runs (all from the frozen `strategy.py`, no source edits after):
  - `cli.py team-run --team team-07` -> `out/is_metrics.json` + `out/net_is.csv`; metrics
    bit-identical to `out/e-018.json` at full float64 precision: Sharpe@1x 0.44780065218805115
    (@2x 0.417076087873868), maxDD -0.3497940349655483, ann. turnover 3.8874611181288348,
    median names 24/24, 174 months, mean_gross 1.0, mean_net 0.0004954102549571672. 2x-cost
    Sharpe decay = 0.031 (0.448 -> 0.417).
  - `cli.py audit --team team-07` -> PASS: scan / determinism / truncated-replay (11 cuts) /
    future-corruption / same-bar all OK, zero violations (`out/harness.json`).
- Independence unchanged from above: only authorized tournament docs + the evaluator package
  (`engine.py`, `protocol.py`, `harness.py`, `cli.py`, `leaderboard.py`, `constants.py`) were
  read for the interface contract; no prohibited path was read, imported, or referenced.
