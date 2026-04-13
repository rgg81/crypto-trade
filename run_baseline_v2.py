"""Baseline v2 runner — iter-v2/001 first baseline.

Runs 3 individual LightGBM models (Models E, F, G) on diversification-arm
symbols (DOGE, SOL, XRP), each wrapped in ``RiskV2Wrapper`` with the 4 MVP
risk gates active:

- Vol-adjusted position sizing (atr_pct_rank_200)
- ADX gate (threshold 20)
- Hurst regime check (5/95 pct of training hurst_100)
- Feature z-score OOD alert (|z| > 3)

Uses the v2 feature catalog (35 features in features_v2/) and
``natr_21_raw`` as the ATR labeling column.

Usage:
    # Fast first-seed (single seed, 10 Optuna trials)
    uv run python run_baseline_v2.py

    # Full 10-seed MERGE validation
    uv run python run_baseline_v2.py --seeds 10
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v2 import V2_FEATURE_COLUMNS
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
from crypto_trade.strategies.ml.risk_v2 import RiskV2Config, RiskV2Wrapper

ITERATION = 1
ITERATION_LABEL = "v2-004"

V2_EXCLUDED_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT")
"""Symbols belonging to v1's baseline. v2 runners MUST exclude these."""

V2_MODELS: tuple[tuple[str, str], ...] = (
    ("E (DOGEUSDT)", "DOGEUSDT"),
    ("F (SOLUSDT)", "SOLUSDT"),
    ("G (XRPUSDT)", "XRPUSDT"),
)

DEFAULT_SEEDS = (42,)  # iter-v2/001 first-pass uses a single seed
FULL_SEEDS = (42, 123, 456, 789, 1001, 1234, 2345, 3456, 4567, 5678)  # MERGE validation


def _verify_branch() -> None:
    """Enforce the git workflow guardrail: v2 runs from iteration-v2/* or quant-research."""
    branch = subprocess.check_output(
        ["git", "--no-optional-locks", "branch", "--show-current"],
        text=True,
    ).strip()
    if not (branch.startswith("iteration-v2/") or branch == "quant-research"):
        raise RuntimeError(
            f"v2 runner must run from iteration-v2/* or quant-research branch; got: {branch}"
        )


def _verify_symbols(symbols: tuple[str, ...]) -> None:
    """Enforce the symbol-exclusion guardrail."""
    overlap = set(symbols) & set(V2_EXCLUDED_SYMBOLS)
    if overlap:
        raise RuntimeError(
            f"v2 runner cannot trade v1 baseline symbols: {sorted(overlap)}"
        )


def _build_model(
    symbol: str,
    seed: int,
    n_trials: int,
    ensemble_seeds: list[int],
) -> tuple[BacktestConfig, RiskV2Wrapper]:
    cfg = BacktestConfig(
        symbols=(symbol,),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=2,
        # Vol targeting is handled by RiskV2Wrapper, not the backtest engine
        vol_targeting=False,
    )
    inner = LightGbmStrategy(
        training_months=24,
        n_trials=n_trials,
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features_v2",
        seed=seed,
        verbose=0,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        atr_column="natr_21_raw",
        use_atr_labeling=True,
        ensemble_seeds=list(ensemble_seeds),
        feature_columns=list(V2_FEATURE_COLUMNS),
    )
    risk_cfg = RiskV2Config()
    strategy = RiskV2Wrapper(inner, risk_cfg)
    return cfg, strategy


def _run_single_seed(seed: int, n_trials: int) -> list:
    """Run all 3 models for a single seed and return concatenated trades."""
    all_trades: list = []
    for name, symbol in V2_MODELS:
        print("=" * 60)
        print(f"MODEL {name} — seed {seed}")
        print("=" * 60)
        cfg, strategy = _build_model(
            symbol=symbol,
            seed=seed,
            n_trials=n_trials,
            ensemble_seeds=[seed],
        )
        _verify_symbols(cfg.symbols)
        t0 = time.time()
        results = run_backtest(cfg, strategy, yearly_pnl_check=False)
        elapsed = time.time() - t0
        print(f"{name}: {len(results)} trades in {elapsed:.0f}s (seed={seed})")
        # Stash gate stats for the engineering report
        gate_summary = strategy.gate_stats_summary()
        print(f"  gate stats: {gate_summary}")
        all_trades.extend(results)
    all_trades.sort(key=lambda t: t.close_time)
    return all_trades


def main() -> None:
    parser = argparse.ArgumentParser(description="v2 baseline runner — iter-v2/001")
    parser.add_argument(
        "--seeds",
        type=int,
        default=1,
        help="Number of seeds to run (1 for first-pass, 10 for full MERGE validation)",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=10,
        help="Optuna trials per monthly model (v1 uses 50; iter-v2/001 default 10)",
    )
    args = parser.parse_args()

    _verify_branch()
    print(f"BASELINE v2 iter-{ITERATION_LABEL}: DOGE+SOL+XRP individual models with RiskV2Wrapper")
    print(f"Seeds: {args.seeds}  Optuna trials/model: {args.n_trials}")
    print()

    seeds = list(FULL_SEEDS[: args.seeds]) if args.seeds > 1 else list(DEFAULT_SEEDS)

    # Per-seed results for robustness validation
    per_seed_summary: list[dict] = []
    primary_trades: list | None = None

    for i, seed in enumerate(seeds):
        print(f"\n{'#' * 60}\n# SEED {seed} ({i + 1}/{len(seeds)})\n{'#' * 60}")
        trades = _run_single_seed(seed, args.n_trials)
        if not trades:
            per_seed_summary.append({"seed": seed, "trades": 0, "oos_trades": 0, "oos_sharpe": 0.0})
            continue

        oos = [t for t in trades if t.open_time >= OOS_CUTOFF_MS]
        oos_wp = np.array([t.weighted_pnl for t in oos], dtype=float)
        if len(oos_wp) > 1 and oos_wp.std() > 0:
            oos_sr = float(oos_wp.mean() / oos_wp.std() * np.sqrt(len(oos_wp)))
        else:
            oos_sr = 0.0
        per_seed_summary.append(
            {
                "seed": seed,
                "trades": len(trades),
                "oos_trades": len(oos),
                "oos_sharpe": round(oos_sr, 4),
            }
        )
        print(
            f"[seed {seed}] {len(trades)} trades, OOS {len(oos)} trades, "
            f"OOS Sharpe={oos_sr:+.4f}"
        )

        if i == 0:
            primary_trades = trades

    if not primary_trades:
        print("No trades produced for primary seed.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("SEED ROBUSTNESS SUMMARY")
    print("=" * 60)
    print(f"{'seed':>6}  {'trades':>6}  {'oos_trades':>10}  {'oos_sharpe':>10}")
    for r in per_seed_summary:
        print(f"{r['seed']:>6}  {r['trades']:>6}  {r['oos_trades']:>10}  {r['oos_sharpe']:>10}")
    oos_sharpes = np.array([r["oos_sharpe"] for r in per_seed_summary])
    profitable = int((oos_sharpes > 0).sum())
    print(f"\nMean OOS Sharpe: {oos_sharpes.mean():+.4f}")
    print(f"Profitable seeds: {profitable}/{len(seeds)}")
    print(
        f"Pass (mean>0 AND ≥7/10 profitable): "
        f"{oos_sharpes.mean() > 0 and profitable >= max(1, int(0.7 * len(seeds)))}"
    )

    # generate_iteration_reports reads BTCUSDT's v1 features (vol_natr_14,
    # trend_adx_14) purely for the per_regime.csv annotation. BTC is not in
    # v2's feature_v2 parquets (excluded by design). Point the regime lookup
    # at v1's feature dir — it annotates the reports, it does not feed v2's
    # model, so it does not violate the no-v1-features rule.
    report_dir = generate_iteration_reports(
        trades=primary_trades,
        iteration=ITERATION_LABEL,
        features_dir="data/features",
        reports_dir="reports-v2",
        interval="8h",
        n_trials=1,  # v2 iteration count
    )
    # Persist per-seed summary next to the comparison.csv
    (Path(report_dir) / "seed_summary.json").write_text(json.dumps(per_seed_summary, indent=2))
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
