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
import pandas as pd

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v2 import V2_FEATURE_COLUMNS
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
from crypto_trade.strategies.ml.risk_v2 import (
    BtcTrendFilterConfig,
    HitRateGateConfig,
    RiskV2Config,
    RiskV2Wrapper,
    apply_btc_trend_filter,
    apply_hit_rate_gate,
    load_btc_klines_for_filter,
)

ITERATION = 1
ITERATION_LABEL = "v2-030"

# iter-v2/017: Hit-rate feedback gate (Config D from iter-v2/016 feasibility).
# For each new signal, look at the last 20 trades that closed before this
# signal's open_time. If the SL rate in that window >= 0.65, kill the signal.
# Only active-window (post-OOS_CUTOFF_MS) trades feed the lookback, so the
# gate is fresh at deployment.
HIT_RATE_CONFIG = HitRateGateConfig(
    window=20,
    sl_threshold=0.65,
    enabled=True,
)

# iter-v2/019: BTC trend-alignment filter. Kill trades whose direction fights
# a BTC 14-day trend exceeding 20% in the opposing direction. Addresses the
# 2024-11 post-election rally disaster where the model went 100% short into
# a BTC +48% month. Filter is full-period (no OOS scoping) so it catches IS
# regime shifts like 2024-11 and 2022-05 (LUNA).
BTC_TREND_CONFIG = BtcTrendFilterConfig(
    lookback_bars=42,  # 14 days of 8h bars
    threshold_pct=20.0,
    enabled=True,
)

V2_EXCLUDED_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT")
"""Symbols belonging to v1's baseline. v2 runners MUST exclude these."""

# iter-v2/005: added Model H (NEARUSDT) as the 4th v2 symbol to dilute XRP's
# concentration (52.6% in iter-v2/004, 2.6pp over the 50% limit). NEAR passed
# the 6-gate screening in iter-v2/001: v1 corr 0.665, $240M daily volume,
# 4,847 IS candles.
V2_MODELS: tuple[tuple[str, str], ...] = (
    ("E (DOGEUSDT)", "DOGEUSDT"),
    ("F (SOLUSDT)", "SOLUSDT"),
    ("G (XRPUSDT)", "XRPUSDT"),
    ("H (NEARUSDT)", "NEARUSDT"),
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
        raise RuntimeError(f"v2 runner cannot trade v1 baseline symbols: {sorted(overlap)}")


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


def _run_single_seed(
    seed: int,
    n_trials: int,
    btc_times: np.ndarray,
    btc_closes: np.ndarray,
) -> tuple[list, list, dict, dict]:
    """Run all 4 models for a single seed, then apply both risk filters.

    Returns ``(unbraked_trades, braked_trades, btc_stats, hr_stats)``:
    - unbraked: raw concatenation of 4 backtests
    - braked: BTC trend filter + hit-rate gate applied in sequence
    - btc_stats / hr_stats: per-gate firing counters
    """
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
        gate_summary = strategy.gate_stats_summary()
        print(f"  gate stats: {gate_summary}")
        all_trades.extend(results)
    all_trades.sort(key=lambda t: t.open_time)

    # iter-v2/019: BTC trend filter runs FIRST, full-period (no activation
    # scoping). Addresses IS regime shifts like 2024-11 post-election rally.
    after_btc, btc_fire_stats = apply_btc_trend_filter(
        all_trades,
        btc_times,
        btc_closes,
        BTC_TREND_CONFIG,
    )
    btc_stats_dict = btc_fire_stats.as_dict()
    print(
        f"[btc trend filter seed {seed}] "
        f"normal={btc_stats_dict['n_normal']} "
        f"warmup={btc_stats_dict['n_warmup']} "
        f"killed={btc_stats_dict['n_killed']}/{btc_stats_dict['n_total']} "
        f"fire_rate={btc_stats_dict['fire_rate']:.2%}"
    )

    # iter-v2/017: hit-rate feedback gate runs SECOND, OOS-scoped. Operates
    # on the post-BTC-filter stream so it doesn't double-count killed
    # trades in its lookback window.
    braked, hr_fire_stats = apply_hit_rate_gate(
        after_btc,
        HIT_RATE_CONFIG,
        activate_at_ms=OOS_CUTOFF_MS,
    )
    braked.sort(key=lambda t: t.close_time)
    hr_stats_dict = hr_fire_stats.as_dict()
    print(
        f"[hit-rate gate seed {seed}] "
        f"normal={hr_stats_dict['n_normal']} "
        f"warmup={hr_stats_dict['n_warmup']} "
        f"killed={hr_stats_dict['n_killed']}/{hr_stats_dict['n_total']} "
        f"fire_rate={hr_stats_dict['fire_rate']:.2%}"
    )
    return all_trades, braked, btc_stats_dict, hr_stats_dict


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
        default=15,
        help="Optuna trials per monthly model (iter-v2/029: 10→15 middle ground)",
    )
    args = parser.parse_args()

    _verify_branch()
    print(f"BASELINE v2 iter-{ITERATION_LABEL}: DOGE+SOL+XRP individual models with RiskV2Wrapper")
    print(f"Seeds: {args.seeds}  Optuna trials/model: {args.n_trials}")
    print()

    # iter-v2/019: load BTC klines once for the BTC trend filter
    btc_times, btc_closes = load_btc_klines_for_filter()
    print(f"Loaded {len(btc_times)} BTC 8h klines for trend filter")
    print()

    seeds = list(FULL_SEEDS[: args.seeds]) if args.seeds > 1 else list(DEFAULT_SEEDS)

    # Per-seed results for robustness validation
    per_seed_summary: list[dict] = []
    per_seed_concentration: list[dict] = []  # iter-v2/030: per-seed per-symbol OOS share
    primary_trades: list | None = None

    for i, seed in enumerate(seeds):
        print(f"\n{'#' * 60}\n# SEED {seed} ({i + 1}/{len(seeds)})\n{'#' * 60}")
        unbraked, braked, btc_stats, hr_stats = _run_single_seed(
            seed, args.n_trials, btc_times, btc_closes
        )
        if not braked:
            per_seed_summary.append(
                {
                    "seed": seed,
                    "trades": 0,
                    "oos_trades": 0,
                    "oos_sharpe": 0.0,
                    "oos_sharpe_unbraked": 0.0,
                }
            )
            continue

        # Metrics use the BRAKED stream (iter-v2/017 productionization)
        oos = [t for t in braked if t.open_time >= OOS_CUTOFF_MS]
        oos_wp = np.array([t.weighted_pnl for t in oos], dtype=float)
        if len(oos_wp) > 1 and oos_wp.std() > 0:
            oos_sr = float(oos_wp.mean() / oos_wp.std() * np.sqrt(len(oos_wp)))
        else:
            oos_sr = 0.0

        # Report unbraked Sharpe alongside for diagnostics
        oos_ub = [t for t in unbraked if t.open_time >= OOS_CUTOFF_MS]
        oos_ub_wp = np.array([t.weighted_pnl for t in oos_ub], dtype=float)
        if len(oos_ub_wp) > 1 and oos_ub_wp.std() > 0:
            oos_sr_ub = float(oos_ub_wp.mean() / oos_ub_wp.std() * np.sqrt(len(oos_ub_wp)))
        else:
            oos_sr_ub = 0.0

        # Compute IS totals too
        is_tr = [t for t in braked if t.open_time < OOS_CUTOFF_MS]
        is_wp = float(sum(t.weighted_pnl for t in is_tr))
        is_tr_ub = [t for t in unbraked if t.open_time < OOS_CUTOFF_MS]
        is_wp_ub = float(sum(t.weighted_pnl for t in is_tr_ub))

        # Monthly Sharpe (user's preferred metric)
        def _monthly_sharpe(ts: list) -> float:
            if not ts:
                return 0.0
            months = pd.to_datetime([t.close_time for t in ts], unit="ms").to_period("M")
            monthly = (
                pd.Series([t.weighted_pnl for t in ts], index=months).groupby(level=0).sum() / 100.0
            )
            if len(monthly) < 2 or monthly.std() == 0:
                return 0.0
            return float(monthly.mean() / monthly.std() * np.sqrt(12))

        is_sharpe_monthly = _monthly_sharpe(is_tr)
        oos_sharpe_monthly = _monthly_sharpe(oos)

        # iter-v2/030: per-seed per-symbol OOS PnL share for concentration audit
        sym_pnl: dict[str, float] = {}
        for t in oos:
            sym_pnl[t.symbol] = sym_pnl.get(t.symbol, 0.0) + float(t.weighted_pnl)
        total_oos = sum(sym_pnl.values())
        if total_oos != 0:
            sym_share = {s: round(p / total_oos * 100.0, 2) for s, p in sym_pnl.items()}
        else:
            sym_share = {s: 0.0 for s in sym_pnl}
        max_share = max(sym_share.values()) if sym_share else 0.0
        max_symbol = max(sym_share, key=sym_share.get) if sym_share else ""
        per_seed_concentration.append(
            {
                "seed": seed,
                "oos_trades_per_symbol": {s: sum(1 for t in oos if t.symbol == s) for s in sym_pnl},
                "oos_pnl_per_symbol": {s: round(p, 2) for s, p in sym_pnl.items()},
                "oos_share_pct": sym_share,
                "max_share_pct": max_share,
                "max_symbol": max_symbol,
                "pass_50pct": max_share <= 50.0,
                "pass_40pct": max_share <= 40.0,
            }
        )

        per_seed_summary.append(
            {
                "seed": seed,
                "trades": len(braked),
                "oos_trades": len(oos),
                "oos_sharpe": round(oos_sr, 4),
                "oos_sharpe_unbraked": round(oos_sr_ub, 4),
                "is_sharpe_monthly": round(is_sharpe_monthly, 4),
                "oos_sharpe_monthly": round(oos_sharpe_monthly, 4),
                "is_total_wpnl": round(is_wp, 2),
                "is_total_wpnl_unbraked": round(is_wp_ub, 2),
                "btc_killed": btc_stats["n_killed"],
                "hr_killed": hr_stats["n_killed"],
            }
        )
        print(
            f"[seed {seed}] {len(braked)} trades, "
            f"IS monthly={is_sharpe_monthly:+.4f}, OOS monthly={oos_sharpe_monthly:+.4f}"
        )

        if i == 0:
            primary_trades = braked

    if not primary_trades:
        print("No trades produced for primary seed.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("SEED ROBUSTNESS SUMMARY")
    print("=" * 60)
    print(f"{'seed':>6}  {'IS monthly':>12}  {'OOS monthly':>12}  {'OOS trade':>12}")
    for r in per_seed_summary:
        print(
            f"{r['seed']:>6}  "
            f"{r.get('is_sharpe_monthly', 0.0):>+12.4f}  "
            f"{r.get('oos_sharpe_monthly', 0.0):>+12.4f}  "
            f"{r['oos_sharpe']:>+12.4f}"
        )
    is_monthly = np.array([r.get("is_sharpe_monthly", 0.0) for r in per_seed_summary])
    oos_monthly = np.array([r.get("oos_sharpe_monthly", 0.0) for r in per_seed_summary])
    oos_sharpes = np.array([r["oos_sharpe"] for r in per_seed_summary])
    profitable = int((oos_sharpes > 0).sum())
    print(f"\nMean IS monthly Sharpe: {is_monthly.mean():+.4f}")
    print(f"Mean OOS monthly Sharpe: {oos_monthly.mean():+.4f}")
    print(f"Mean OOS trade Sharpe: {oos_sharpes.mean():+.4f}")
    print(f"Profitable seeds: {profitable}/{len(seeds)}")
    ratio = oos_monthly.mean() / is_monthly.mean() if is_monthly.mean() > 0 else float("inf")
    print(f"OOS/IS monthly ratio: {ratio:.2f}x  (target: 1.0-2.0 for balance)")

    # iter-v2/030: per-seed concentration audit (new pre-MERGE hard gate)
    if per_seed_concentration:
        print("\n" + "=" * 60)
        print("SEED CONCENTRATION AUDIT")
        print("=" * 60)
        print(f"{'seed':>6}  {'max':>7}  {'symbol':>10}  {'<=50':>6}  {'<=40':>6}")
        max_shares = []
        for c in per_seed_concentration:
            max_shares.append(c["max_share_pct"])
            print(
                f"{c['seed']:>6}  "
                f"{c['max_share_pct']:>6.2f}%  "
                f"{c['max_symbol']:>10}  "
                f"{'PASS' if c['pass_50pct'] else 'FAIL':>6}  "
                f"{'PASS' if c['pass_40pct'] else 'FAIL':>6}"
            )
        mean_max = float(np.mean(max_shares))
        n_pass_50 = sum(1 for c in per_seed_concentration if c["pass_50pct"])
        n_above_40 = sum(1 for c in per_seed_concentration if not c["pass_40pct"])
        print(f"\nMean per-seed max-share: {mean_max:.2f}%  (rule: <=45%)")
        print(f"Seeds passing <=50%:      {n_pass_50}/{len(per_seed_concentration)}  (rule: all)")
        print(f"Seeds above 40%:          {n_above_40}/{len(per_seed_concentration)}  (rule: <=1)")
        overall_pass = (
            n_pass_50 == len(per_seed_concentration)
            and mean_max <= 45.0
            and n_above_40 <= 1
        )
        print(f"Overall seed concentration: {'PASS' if overall_pass else 'FAIL'}")

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
    (Path(report_dir) / "seed_concentration.json").write_text(
        json.dumps(per_seed_concentration, indent=2)
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
