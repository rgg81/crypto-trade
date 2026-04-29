"""Post-hoc hit-rate feedback gate feasibility (iter-v2/016).

New risk primitive: for each new signal at time T, look at the last
N trades that have CLOSED before T (strict past only). Count the
stop-loss hits. If the SL rate exceeds a threshold, kill the signal.

Directly targets v2's slow-bleed drawdown signature: when the model
is systematically wrong about direction, recent trades cluster
heavily on SL exits. The gate fires on that cluster, killing new
signals until the SL rate drops back below threshold.

Diagnostic verified: iter-v2/005 OOS has overall SL rate 50.4%, but
July-August 2025 window has 68.8% SL rate. Rolling-20 SL rate peaks
at 0.75 on 2025-07-30 — exactly v2's drawdown window.

Usage:
    uv run python analyze_hit_rate_gate.py

Outputs:
    reports-v2/iteration_v2-016_hit_rate_gate/
        summary.json           — per-config aggregate + per-symbol
        firing_log.csv         — killed trades per config
        per_config_trades.csv  — braked trade stream per config
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

V2_REPORT = Path("reports-v2/iteration_v2-005")
OUT_DIR = Path("reports-v2/iteration_v2-016_hit_rate_gate")


@dataclass(frozen=True)
class HitRateConfig:
    name: str
    window: int  # number of most-recent closed trades to look at
    sl_threshold: float  # SL rate above which the gate fires (0.0-1.0)


CONFIGS: tuple[HitRateConfig, ...] = (
    HitRateConfig("none", window=0, sl_threshold=2.0),
    HitRateConfig("A_10w_070", window=10, sl_threshold=0.70),
    HitRateConfig("B_10w_060", window=10, sl_threshold=0.60),
    HitRateConfig("C_15w_067", window=15, sl_threshold=0.67),
    HitRateConfig("D_20w_065", window=20, sl_threshold=0.65),
    HitRateConfig("E_20w_060", window=20, sl_threshold=0.60),
)


def _apply_hit_rate_gate(
    trades: pd.DataFrame, cfg: HitRateConfig
) -> tuple[pd.DataFrame, list[dict]]:
    """Apply the hit-rate gate to a sorted trade stream.

    For each trade at open_time T:
    1. Find all trades that have close_time < T (strictly past)
    2. Take the last ``window`` of them
    3. Compute SL rate
    4. If SL rate >= threshold, kill this trade
    """
    trades = trades.sort_values("open_time").reset_index(drop=True).copy()

    effective_factor: list[float] = []
    effective_pnl: list[float] = []
    window_sl_rate_log: list[float] = []
    state_log: list[str] = []
    firings: list[dict] = []

    if cfg.window == 0:
        # Baseline — no gate
        trades["effective_factor"] = 1.0
        trades["effective_weighted_pnl"] = trades["weighted_pnl"]
        trades["sl_rate_window"] = np.nan
        trades["gate_state"] = "normal"
        return trades, firings

    # Precompute is_sl vector for efficient lookup
    is_sl = (trades["exit_reason"] == "stop_loss").to_numpy()
    close_times = trades["close_time"].to_numpy(dtype=np.int64)
    open_times = trades["open_time"].to_numpy(dtype=np.int64)

    for i in range(len(trades)):
        t_open = int(open_times[i])
        # Find indices of trades that closed BEFORE t_open
        prior_mask = close_times < t_open
        prior_indices = np.where(prior_mask)[0]
        if len(prior_indices) < cfg.window:
            # Not enough prior history — pass through
            effective_factor.append(1.0)
            effective_pnl.append(float(trades.iloc[i]["weighted_pnl"]))
            window_sl_rate_log.append(float("nan"))
            state_log.append("warmup")
            continue

        # Take last `window` of them (most recent closed)
        window_idx = prior_indices[-cfg.window :]
        window_sl = is_sl[window_idx]
        sl_rate = float(window_sl.mean())
        window_sl_rate_log.append(sl_rate)

        if sl_rate >= cfg.sl_threshold:
            eff = 0.0
            state = "killed"
            wpnl = float(trades.iloc[i]["weighted_pnl"])
            firings.append(
                {
                    "config": cfg.name,
                    "trade_idx": i,
                    "open_time": t_open,
                    "open_date": pd.to_datetime(t_open, unit="ms").date().isoformat(),
                    "symbol": trades.iloc[i]["symbol"],
                    "sl_rate_window": round(sl_rate, 3),
                    "original_weighted_pnl": round(wpnl, 3),
                }
            )
        else:
            eff = 1.0
            state = "normal"

        effective_factor.append(eff)
        effective_pnl.append(float(trades.iloc[i]["weighted_pnl"]) * eff)
        state_log.append(state)

    trades["effective_factor"] = effective_factor
    trades["effective_weighted_pnl"] = effective_pnl
    trades["sl_rate_window"] = window_sl_rate_log
    trades["gate_state"] = state_log
    return trades, firings


def _trade_level_sharpe(pnl: pd.Series) -> float:
    if len(pnl) < 2 or pnl.std() == 0:
        return 0.0
    return float(pnl.mean() / pnl.std() * np.sqrt(len(pnl)))


def _annualize_daily(daily: pd.Series, periods: int = 365) -> float:
    if len(daily) < 2 or daily.std() == 0:
        return 0.0
    return float(daily.mean() / daily.std() * np.sqrt(periods))


def _max_drawdown(equity: pd.Series) -> float:
    if len(equity) == 0:
        return 0.0
    rolling_max = equity.cummax()
    dd = (equity - rolling_max) / rolling_max.replace(0, np.nan)
    return float(dd.min() or 0.0)


def _summarize(trades: pd.DataFrame, pnl_col: str, label: str) -> dict:
    if len(trades) == 0:
        return {"label": label, "n": 0}

    trades = trades.copy()
    trades["date"] = pd.to_datetime(trades["close_time"], unit="ms").dt.date
    daily = trades.groupby("date")[pnl_col].sum()

    sharpe_daily = _annualize_daily(daily / 100.0)
    sharpe_trade = _trade_level_sharpe(trades[pnl_col])
    equity = (1.0 + daily / 100.0).cumprod()
    max_dd = _max_drawdown(equity)
    pnl = trades[pnl_col]
    wins = pnl[pnl > 0].sum()
    losses = abs(pnl[pnl < 0].sum() or 1)
    pf = float(wins / losses)
    total_pnl = float(pnl.sum())
    total_return = float((1.0 + daily / 100.0).prod() - 1.0)
    calmar = float(total_return / abs(max_dd)) if max_dd != 0 else 0.0

    per_sym = trades.groupby("symbol")[pnl_col].sum().sort_values(ascending=False).to_dict()
    total = sum(per_sym.values())
    per_sym_pct = {
        sym: round(float(pnl / total * 100) if total != 0 else 0.0, 2)
        for sym, pnl in per_sym.items()
    }

    return {
        "label": label,
        "n_trades": int(len(trades)),
        "win_rate": round(float((pnl > 0).mean() * 100), 2),
        "pf": round(pf, 4),
        "sharpe_trade": round(float(sharpe_trade), 4),
        "sharpe_daily_annualized": round(float(sharpe_daily), 4),
        "max_dd_pct": round(float(max_dd * 100), 2),
        "total_pnl_pct": round(total_pnl, 2),
        "calmar": round(calmar, 2),
        "per_sym_pnl": {k: round(float(v), 2) for k, v in per_sym.items()},
        "per_sym_share_pct": per_sym_pct,
    }


def main() -> None:
    print("=" * 70)
    print("HIT-RATE FEEDBACK GATE FEASIBILITY — iter-v2/016")
    print("=" * 70)

    oos_path = V2_REPORT / "out_of_sample/trades.csv"
    if not oos_path.exists():
        print(f"ERROR: {oos_path} not found")
        return

    trades = pd.read_csv(oos_path)
    print(f"\nLoaded {len(trades)} v2 OOS trades")

    # Baseline SL rate
    overall_sl = (trades["exit_reason"] == "stop_loss").mean()
    print(f"Overall OOS SL rate: {overall_sl:.1%}")
    print()

    summaries: dict[str, dict] = {}
    per_config_trades: dict[str, pd.DataFrame] = {}
    all_firings: list[dict] = []

    for cfg in CONFIGS:
        braked, firings = _apply_hit_rate_gate(trades, cfg)
        agg = _summarize(braked, "effective_weighted_pnl", cfg.name)
        agg["config"] = {
            "window": cfg.window,
            "sl_threshold": cfg.sl_threshold,
        }
        agg["n_killed"] = len(firings)
        summaries[cfg.name] = agg
        per_config_trades[cfg.name] = braked
        all_firings.extend(firings)

    # Headline
    print("=" * 95)
    print("HEADLINE METRICS")
    print("=" * 95)
    header = (
        f"{'config':<14} {'win':>4} {'thr':>5} {'kills':>6} "
        f"{'Sharpe':>8} {'MaxDD%':>8} {'Calmar':>7} {'PnL%':>7} {'XRPshr%':>8}"
    )
    print(header)
    print("-" * len(header))
    for name, s in summaries.items():
        cfg = s["config"]
        win = f"{cfg['window']}" if cfg["window"] else "—"
        thr = f"{cfg['sl_threshold']:.2f}" if cfg["window"] else "—"
        xrp_share = s["per_sym_share_pct"].get("XRPUSDT", 0.0)
        print(
            f"{name:<14} {win:>4} {thr:>5} {s['n_killed']:>6} "
            f"{s['sharpe_trade']:>+8.4f} "
            f"{s['max_dd_pct']:>+8.2f} "
            f"{s['calmar']:>+7.2f} "
            f"{s['total_pnl_pct']:>+7.2f} "
            f"{xrp_share:>+8.2f}"
        )

    # Decision check
    print()
    print("=" * 95)
    print("DECISION CRITERIA: MaxDD red ≥15% AND Sharpe drag ≤10% AND conc change ≤5pp")
    print("=" * 95)
    baseline = summaries["none"]
    for name, s in summaries.items():
        if name == "none":
            continue
        mdd_reduction = (
            (abs(baseline["max_dd_pct"]) - abs(s["max_dd_pct"])) / abs(baseline["max_dd_pct"]) * 100
        )
        sharpe_drag = (
            (s["sharpe_trade"] - baseline["sharpe_trade"]) / baseline["sharpe_trade"] * 100
        )
        conc_change = s["per_sym_share_pct"].get("XRPUSDT", 0) - baseline["per_sym_share_pct"].get(
            "XRPUSDT", 0
        )
        negative_flip = any(v < 0 for v in s["per_sym_pnl"].values())
        mdd_ok = mdd_reduction >= 15.0
        sharpe_ok = sharpe_drag >= -10.0
        conc_ok = abs(conc_change) <= 5.0
        flip_ok = not negative_flip
        verdict = "PASS" if (mdd_ok and sharpe_ok and conc_ok and flip_ok) else "FAIL"
        print(
            f"  {name}: MaxDD red={mdd_reduction:+.1f}% ({'ok' if mdd_ok else 'BAD'}) | "
            f"Sharpe drag={sharpe_drag:+.1f}% ({'ok' if sharpe_ok else 'BAD'}) | "
            f"ConcΔ={conc_change:+.2f}pp ({'ok' if conc_ok else 'BAD'}) | "
            f"NegFlip={'no' if flip_ok else 'YES'} "
            f"→ {verdict}"
        )

    # Per-symbol shares
    print()
    print("=" * 95)
    print("PER-SYMBOL SHARE")
    print("=" * 95)
    for name, s in summaries.items():
        shares = s["per_sym_share_pct"]
        print(
            f"  {name}: XRP={shares.get('XRPUSDT', 0):6.2f}%  "
            f"SOL={shares.get('SOLUSDT', 0):6.2f}%  "
            f"DOGE={shares.get('DOGEUSDT', 0):6.2f}%  "
            f"NEAR={shares.get('NEARUSDT', 0):6.2f}%  "
            f"(PnL={s['total_pnl_pct']:+.2f}%)"
        )

    # Firing log sample
    if all_firings:
        print()
        print("=" * 95)
        print("FIRST 20 FIRING EVENTS (across all configs)")
        print("=" * 95)
        fdf = pd.DataFrame(all_firings).sort_values(["config", "trade_idx"])
        print(fdf.head(20).to_string(index=False))

    # Persist
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.json").write_text(json.dumps(summaries, indent=2, default=str))
    if all_firings:
        pd.DataFrame(all_firings).to_csv(OUT_DIR / "firing_log.csv", index=False)
    all_frames = []
    for name, df in per_config_trades.items():
        df = df.copy()
        df["brake_config"] = name
        all_frames.append(df)
    pd.concat(all_frames, ignore_index=True).to_csv(OUT_DIR / "per_config_trades.csv", index=False)
    print(f"\nArtifacts written to {OUT_DIR}")


if __name__ == "__main__":
    main()
