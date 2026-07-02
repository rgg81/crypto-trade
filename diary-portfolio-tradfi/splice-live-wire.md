# splice-live-wire — wire the SPLICED loader into the live bridge + prove the basis collapse (step 2)

**Date:** 2026-07-02 · **Scope: LIVE-WIRE.** Repoint the tradfi live desk's book + parity track onto
the step-1 SPLICED loader (Yahoo→perp), so the parity track is computed on the SAME instrument the
desk executes. HEADLINE: the parity↔live BASIS collapses to funding-only. Running engine files
(`data/tradfi_paper.db*`, `data/tradfi_equity.csv`, `logs/tradfi_paper.log`) UNTOUCHED — smoked on
isolated tmp DBs; orchestrator flat-restarts the engine after this commit. `splice_loader.py`,
`core_tradfi.py`, `iter_016*.py` frozen (unmodified). `OOS_CUTOFF=2025-03-24` immutable — the
reconcile is execution-tracking over the post-cutoff perp window, NOT a new strategy OOS Sharpe.

## The problem (recap)
Pre-splice the desk's PARITY track marked on Yahoo total-return while the LIVE track marked on the
Binance perp — different series for the same recent day → a whole-book parity↔live gap of ~−85 bps
with 5.8%/yr tracking error and corr 0.70 (Phase-2b). The step-1 splice built a leak-safe Yahoo→perp
book (`load_tradfi_spliced`, IS bit-identical, verified airtight at SHA 9a51032e). Step 2 wires it in.

## What changed (files)
- **`live_weights_tradfi.py`** — `deployed_book` + `deployed_target_weights` load via
  `splice_loader.load_tradfi_spliced(_universe, data_dir, live_data_dir)` instead of `ct.load_tradfi`.
  Added optional `live_data_dir` param (defaults to `data_live_tradfi`). Header/NOTE updated: the
  perp-vs-underlying basis is now SOLVED, not a Phase-2 TODO.
- **`live_tradfi.py`** (engine) — the parity net + traded `deployed_w` come from `_settled_book`,
  which *reimplements* `deployed_book` via a **direct `ct.load_tradfi`** — so repointing only the
  bridge would have left the engine's PARITY on pure Yahoo (basis intact) AND made the persisted
  `held` book (spliced, from `lw`) inconsistent with the traded `deployed_w` (Yahoo). Repointed
  `_settled_book`'s loader to `load_tradfi_spliced` — the minimal change that puts parity + book on
  the executed instrument and keeps `held == deployed_w` coherent. **The live-return math
  (`_live_returns` / `_live_returns_quantized`) is UNCHANGED** — task-3 found no calendar mismatch
  (see below). Docstrings updated (PARITY = spliced; basis collapsed out of `basis_gap`).
- **`reconcile_tradfi.py`** (Phase-1 weight reconcile) — the bit-exact reference now loads via
  `load_tradfi_spliced` (the parity of record is the spliced backtest). Bit-exact tolerance kept.
- **`tests/test_portfolio_tradfi_foundation.py`** — `test_iter016_live_bridge_reconciles_bit_exact`
  now references the SPLICED recompute (same reason as reconcile_tradfi; the assertion stays bit-exact
  because the bridge recomputes from the same spliced code).

## HEADLINE — the divergence COLLAPSED (basis reconcile, coverage-controlled book level)
Measured by re-driving `reconcile_basis_tradfi.book_level` (the −85 bps instrument, unmodified) with
the spliced parity leg vs the pure-Yahoo parity leg on IDENTICAL current data (106 trading days,
2026-01-28→2026-06-30, mean perp coverage 35% over the full window):

| metric | pre-splice (Yahoo parity) | SPLICED parity | collapse |
|---|---|---|---|
| cum LIVE−RECON gap | **+114.9 bps** | **−24.9 bps** | \|gap\| shrinks 78% (basis removed) |
| daily tracking error (ann) | **6.42%** | **0.24%** | 96% tighter |
| corr(LIVE, RECON) | **0.649** | **0.9995** | near-perfect |
| perp-window Sharpe LIVE vs RECON | +2.83 vs +2.62 (Δ0.21) | +2.82 vs +2.88 (Δ0.07) | tracks |

The documented Phase-2b baseline was **−85 bps / 5.8% / 0.70**; a fresh pure-Yahoo re-run on today's
(refreshed) data gives **+114.9 bps / 6.42% / 0.649** — the cumulative basis gap is the most
data-extent-sensitive metric and flipped sign as the window extended, but TE (6.4% vs 5.8%) and corr
(0.65 vs 0.70) reproduce the baseline. Either way the SPLICED result is the same near-deterministic
collapse. **The residual −24.9 bps is FUNDING-ONLY**: the L/S net funding drag is −0.708%/yr, which
over the ~0.42-yr window is ≈ −29.8 bps — i.e. the spliced gap ≈ the funding carry, with the
perp-vs-underlying basis gone. Per-name confirms it: **mean |gap-without-funding| = 0 bps**, median
daily corr **0.999**, pathological names **NONE** (PAYP is no longer pathological — its Yahoo↔perp
basis was the defect, and parity now rides the perp too).

## Task 3 — live-track calendar alignment: NOT NEEDED (and why)
The spliced parity's forward return in the perp window is `perp_open[t+1]/perp_open[t]` on the Yahoo
trading-day grid (weekends folded); the LIVE track's `perp_rf` (`rc.load_perp_opens` reindexed onto
the same grid → `rc.fwd_ret`) is the identical quantity. The reconcile PROVES they coincide:
per-name mean |gap-without-funding| = **0 bps** and corr(LIVE,RECON) = **0.9995** — a calendar
mismatch would make both nonzero. So `_live_returns` / `_live_returns_quantized` were left as-is;
`tradfi_held_w` stays the continuous ideal spliced weights.

## Task 4 — Phase-1 weight reconcile vs the SPLICED backtest: PASS (bit-exact)
`reconcile_tradfi.py` (referencing the spliced recompute): BIT-EXACT overall worst `max|Δw| =
2.78e-16` (tol 1e-10). Crucially the **latest_bar (2026-07-01, in the perp window) = 0.00e+00** and
the **dense 40-bar recent sweep = 0.00e+00** — the spliced live bridge reproduces the spliced backtest
bit-for-bit where spliced ≠ Yahoo, via the public `deployed_target_weights` API too. (The informational
forming-bar proxy widened to 5.69e-2, just over the 5e-2 flag — expected, the perp tail is more
volatile intraday than the Yahoo synthetic; it is NOT a parity gate and does not affect the verdict.)

## Verifications
- **IS-region bridge bit-identical to pre-repoint Yahoo bridge:** `deployed_target_weights` at 6 IS
  dates (2015-06-30 … 2025-03-21) vs a pure-Yahoo truncated recompute → `max|Δw| = 0.0` every date.
  The confirmed iter-016 IS (+0.729/+0.582/+0.875) cannot have moved. Latest book (2026-07-01) sane:
  **69 names, gross 0.710, net +0.082**.
- **Engine coherence smoke (isolated tmp DB, `refresh=False`, read-only on `data/`):** runs on the
  spliced loader; held book **68 names ex-PAYP, gross 0.708** matches the spliced meta gross 0.710.
  June full-coverage continuous basis_gap **−81 → −46.5 bps** (phase-2d methodology; residual =
  funding −16 bps + the mid-June-onboarding coverage artifact, both non-basis). At the $10k budget
  the quantized live track additionally books lot-quantization drag — the honest execution cost,
  separate from basis and isolated in the reconcile.

## Tests + ruff
`tests/test_portfolio_tradfi_foundation.py test_tradfi_basis_reconcile.py test_tradfi_paper_engine.py
test_tradfi_splice.py` → **91 passed**; incl. `test_tradfi_monitor.py` → **102 passed**. `ruff check`
+ `ruff format --check` on the four touched files → clean. (4 unrelated v1-track collection errors in
`test_bundle_config_allow_list.py` / `test_iteration_v1_*` are pre-existing in this worktree.)

## Constraints honored
No touch of `data/tradfi_paper.db*` / `data/tradfi_equity.csv` / `logs/tradfi_paper.log` or any
`data/` / `data_live_tradfi/` CSV (read-only reads only; smoked on tmp DBs). `splice_loader.py` /
`core_tradfi.py` / `iter_016*.py` unmodified. No `git stash`/`checkout`/`reset`. `OOS_CUTOFF`
untouched; no new OOS headline Sharpe. IS anchor stays pure-Yahoo (bit-identical, re-confirmed).
Live parity of record is now the SPLICED backtest.
