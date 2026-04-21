# Crypto-Trade: LightGBM 8H Candle Iteration Plan — v2 Track

**Branch**: `quant-research` (NOT `main`)
**Baseline file**: `BASELINE_V2.md`
**Iteration artifacts**: `briefs-v2/iteration_NNN/`, `diary-v2/iteration_NNN.md`, `reports-v2/iteration_NNN/`
**Branch prefix**: `iteration-v2/NNN`
**Tag format**: `v0.v2-NNN`

## Mission

v2 is the diversification arm of the crypto-trade strategy. v1's baseline
(OOS Sharpe +2.83) is mature on BTC/ETH/LINK/BNB. v2 explores the rest of
the tradable USDT perpetual universe with:

- A completely new feature set (rebuilt around regime awareness and tail risk)
- A hardened risk-management layer (black-swan and out-of-distribution defenses)
- Tighter validation (Deflated Sharpe + regime-stratified OOS; CPCV/PBO from iter-v2/002+)

v2 and v1 share: the backtest engine, labeling, walk-forward, the immutable
OOS_CUTOFF_DATE (2025-03-24), 8h candles, and LightGBM.

## Workflow

See `.claude/commands/quant-iteration-v2.md` for the full workflow (8 phases,
roles, git discipline, feature catalog, risk layer, validation upgrades).

## Data Split

`OOS_CUTOFF_DATE = 2025-03-24` — fixed, shared with v1, never changes. Defined
in `src/crypto_trade/config.py`. Research phases 1-5 use IS-only data. Walk-forward
runs continuously on all data; reports are split at the cutoff.

## Git & Code Management

- All v2 work happens in the `quant-research` worktree on branches
  `iteration-v2/NNN`. The merge target is `quant-research` (never `main`).
- v2 must never touch `src/crypto_trade/features/` (v1's feature package).
  v2 features live in `src/crypto_trade/features_v2/`.
- v2 never imports v1's feature modules.

## Baseline Rules

See `BASELINE_V2.md` for current metrics and the forbidden-symbol table.
Baseline comparison rules for v2 live in the skill file.

## Feature Column Pinning — MANDATORY

Every v2 runner MUST pass `feature_columns=list(V2_FEATURE_COLUMNS)` to
`LightGbmStrategy`. Never `None`, never sorted, never reordered. Column
order matters to LightGBM (via `colsample_bytree` position-based sampling);
changing the order silently produces a different model and breaks
reproducibility. See `.claude/commands/quant-iteration-v2.md` § "Feature
Column Pinning — REPRODUCIBILITY GUARANTEE" for the full rationale and
v1's post-mortem that prompted this rule.

## Candle Integrity — MANDATORY

Every v2 iteration MUST verify before fetching or backtesting:
1. `fetcher.py` contains the closed-candle filter (`k.close_time < now_ms`)
2. No kline CSV has a tail row with `close_time` in the future

Fix lives on `main` (commit `19a1d3e`, 2026-04-13). If the quant-research
branch lacks this fix, merge `main` before running `crypto-trade fetch`.
Forming candles silently corrupt rolling features for up to ~100 rows and
are a second major source of non-reproducibility, distinct from the
column-order bug. See `.claude/commands/quant-iteration-v2.md` § "Candle
Integrity — CLOSED CANDLES ONLY" for the QE pre-flight check script.

## Relationship to v1

- **Shared**: OOS cutoff, 8h candles, LightGBM, backtest engine, labeling,
  walk-forward harness, NO-CHEATING rules, exploration/exploitation 70/30,
  seed validation discipline.
- **Diverged**: symbol universe (excludes v1's 4), feature set (v1's 9 groups
  forbidden for iter-v2/001), risk layer, validation rigor, git flow.
- **Future**: once both baselines are stable, a combined-portfolio runner on
  `main` will load v1 + v2 side-by-side.
