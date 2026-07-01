# Live-deploy Phase 2c — the TradFi PAPER-TRADING engine (dual P&L)

Continuous paper desk for the confirmed **iter-016 BEAR-GATED TSMOM** book, mirroring the metals
paper engine (`analysis/portfolio/metals/live_metals.py`) but for **DAILY** US trading-day bars and
with a **dual P&L**: a backtest-parity track and a live-perp-with-funding track.

Files:
- `analysis/portfolio/tradfi/live_tradfi.py` — `TradfiPaperEngine` + `TradfiPaperConfig`.
- `run_tradfi_paper.py` — thin launcher.
- `tests/test_tradfi_paper_engine.py` — 4 pure-unit tests (PAYP drop, funding sign, coverage, lag).

Launch:
```
PYTHONUNBUFFERED=1 uv run python run_tradfi_paper.py > logs/tradfi_paper.log 2>&1 &
```
Paper only — no real orders. Ctrl-C safe; state in `data/tradfi_paper.db`, snapshots in
`data/tradfi_equity.csv`.

## Design

### Two equity tracks
- **PARITY** (backtest book of record): `net, _ = deployed_book(data_dir)` compounded since launch.
  All 69 names, Yahoo total-return. Parity-by-construction — the same `iter_016.deployed_weights`
  machinery the backtest uses, recomputed from full history each rebalance (no stored position state
  to drift).
- **LIVE** (the real paper P&L): the SAME `deployed_w` weight panel (PAYP dropped), scored on Binance
  single-stock TradFi-perp returns MINUS funding MINUS turnover, coverage-aware.
- `basis_gap = equity_live − equity_parity` — the perp-vs-(underlying+funding) residual. Snapshot
  columns: `ts_utc, bar_date, equity_parity, equity_live, day_funding_pnl, funding_cum, basis_gap`.

### Cadence — DAILY, settled bars only
Poll every 60 s; `_new_candle_due` gates on a **new settled Yahoo daily bar** appearing (newest
universe `data/<SYM>/1d.csv` open_time with date < today UTC advancing). The book is recomputed on a
panel **truncated to bars whose UTC date < today** — the daily analog of the metals forming-8h-candle
drop, so today's unsettled bar never enters signal or P&L. Both tracks compound over **realized bars
only** (`index < as_of`): the `as_of` book is what we now hold into the next open, its forward return
has not settled, so it is not booked (and its live-track weight would coverage-mask to 0 → a spurious
full-unwind cost). First run sets `launch = as_of` → the go-forward desk starts flat.

### PAYP exclusion (Phase-2b)
`LIVE_EXCLUDED = {PAYPUSDT}` — the broken PayPal perp (perp ~$14 vs PayPal ~$43, corr 0.19). Dropped
from the LIVE tradeable book **and NOT re-normalized**: every surviving name keeps its exact backtest
weight (parity-preserving). The dropped leg is logged; the tiny gross/neutrality drift is the
documented cost of the exclusion (smoke: held gross 0.690 vs full meta gross 0.691, the −0.0009 PAYP
short removed, all others unchanged). The **PARITY** track keeps all 69 names (book of record) — so
`basis_gap` also carries the tiny PAYP-exclusion drift by design.

### Funding sign + DRY reuse of the reconcile
Per-leg funding P&L = **`−w·f`** (Binance f>0 ⇒ longs pay: long w>0 → negative; short w<0 → positive).
The load-bearing funding math is **imported, not re-implemented**, from `reconcile_basis_tradfi`:
`load_perp_opens` (perp opens reindexed onto the Yahoo trading-day grid), `fwd_ret` (open-to-open
forward return), and `daily_funding` (the ms-resolution holding-window binning — its `_index_ms`
casts the pandas-2.x DatetimeIndex to `datetime64[ms]` so funding rows do not silently read as zero).
These are clean module-level functions, so no refactor of `reconcile_basis_tradfi` was needed and its
**9 tests stay green**. The engine adds only the portfolio netting on top of those helper outputs, and
that netting is **bit-identical to `reconcile_basis_tradfi.book_level`** (verified: max abs diff 0.0).

### Coverage-aware (ragged onboarding, 34→100 %)
A name with no perp bar / no funding on a day is masked to weight 0 (`w.where(avail, 0.0)`) — it
contributes 0 to `live_ret` that day and does not NaN-poison the sum. This is the same ragged coverage
the Phase-2b reconcile handled as perps onboarded from 2026-01-28 (34 %) to 2026-06-25 (100 %).

### Weight-lag alignment (parity ⇔ live)
`deployed_w` is **already one-bar lagged** — `iter_015.banded_book_freq` ends in `held.shift(1)`
(verified: `banded_book_freq` last statement is `return held.shift(1)`). The backtest
`net[t] = Σ deployed_w[t]·ret_fwd[t] − cost` pairs the lagged weight against the open-to-open forward
return on the **same index t**. The LIVE track uses the **identical** alignment —
`live[t] = Σ deployed_w[t]·perp_rf[t] − Σ deployed_w[t]·f_daily[t] − cost`, `perp_rf[t] =
perp_open[t+1]/perp_open[t] − 1`, **no extra shift** — exactly the `book_level` convention.

**Verified** two ways: (1) feeding `perp_rf ← yahoo ret_fwd` with funding=cost=0 makes the live perp
P&L equal the parity `Σ deployed_w·ret_fwd` bar-for-bar (max abs diff **0.0**); (2) unit test
`test_live_lag_matches_parity_shift` asserts `live_ret == Σ deployed_w[t]·perp_rf[t]` on realized
bars — any spurious extra `.shift()` breaks it.

## Smoke run (offline, one `run_once`)

Back-dated launch to **2026-06-01** so the desk boots with ~1 month of realized dual-P&L (a
go-forward first launch would start flat). `run_once(refresh=False)` — no network, on-disk data only:

```
[exclude] dropped PAYPUSDT leg w=-0.0009 (NOT renormalized)
[rebal] as_of=2026-06-30  gross=0.690  n_pos=68  legs=68  eq_parity=$106,348  eq_live=$105,533
        basis_gap=$-815 (-81bps)  day_fund=$-5.10  cum_fund=$-172.32  (meta gross=0.691)
```

- **Both tracks populate**: eq_parity **+6.35 %**, eq_live **+5.53 %**.
- **basis_gap = −81 bps** — squarely on the Phase-2b whole-book figure of **−85 bps** → no lag/coverage
  bug. (Removing the unrealized-frontier `−cost` artifact moved it from −86 → −81 bps.)
- **funding_cum = −$172.32** (negative = long-premium carry, as expected); day_fund = −$5.10.
- **held excludes PAYP** (68 of 69 legs; gross 0.690 vs meta 0.691 = not re-normalized).
- **State persisted** — all 6 keys (`tradfi_held_w`, `tradfi_last_candle`, `tradfi_launch_candle`,
  `tradfi_equity_parity`, `tradfi_equity_live`, `tradfi_funding_cum`) and one `tradfi_equity.csv` row.

### Cross-check vs the Phase-2b reconcile
Launching the same engine at **perp inception (2026-01-28)** reproduces the reconcile's coverage
decomposition: eq_parity **+20.5 %** (= diary book-of-record +20.46 %, all names) vs eq_live
**+8.8 %** (= diary LIVE +8.65 %, tradeable-subset). Over that full window `basis_gap = −1164 bps` —
**dominated by the early thin-coverage artifact** (mean coverage 34 %), NOT a basis error. That is why
the desk's meaningful basis is measured go-forward under ~100 % coverage, where it lands at the
−85 bps whole-book figure. The go-forward first launch (launch = current bar) starts flat and grows.

## Constraints honored
- `OOS_CUTOFF = 2025-03-24` untouched; the perp/live window is entirely post-cutoff (live-forward). No
  IS/OOS strategy Sharpe computed or revealed.
- No modification of `data/<SYM>/1d.csv`, `core_tradfi.py`, `iter_016*.py`, or `live_weights_tradfi.py`.
  `reconcile_basis_tradfi.py` unchanged (helpers were cleanly importable — no refactor needed; its 9
  tests stay green). All engine code is new files.
- No `git stash` / `checkout` / `reset`. `analysis/` + `data_live_tradfi/` + `data/` are gitignored;
  only the new source/test files were `git add -f`'d — nothing under `data/` or `data_live_tradfi/`.
- `uv run ruff check` clean on the new files; `uv run pytest tests/test_tradfi_paper_engine.py
  tests/test_tradfi_basis_reconcile.py -q` → 13 passed.

> **Operator note:** the smoke seeded `data/tradfi_paper.db` with a back-dated launch (2026-06-01) so
> the desk boots with a real recent track record. For a strictly-flat go-forward start, `rm
> data/tradfi_paper.db* data/tradfi_equity.csv` before the first `run_tradfi_paper.py` launch.
