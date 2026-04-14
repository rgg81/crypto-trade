"""Post-hoc per-symbol drawdown-brake feasibility study (iter-v2/014).

Direct response to iter-v2/013's concentration failure: apply the
drawdown brake INDEPENDENTLY to each symbol's OOS trade stream, so
DOGE's brake sees only DOGE's DD, SOL's sees only SOL's, etc. No
cross-symbol contamination.

Same 4 configs as iter-v2/012:
    A — 5% / 10%
    B — 6% / 12%
    C — 8% / 16%   (iter-v2/012 winner)
    D — 4% / 8%
    None (baseline)

Usage:
    uv run python analyze_per_symbol_brake.py

Outputs:
    reports-v2/iteration_v2-014_per_symbol_brake/
        summary.json              — per-config aggregate + per-symbol
        per_config_trades.csv     — trade-by-trade brake state per config
        concentration_matrix.csv  — per-config × per-symbol share table
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

V2_REPORT = Path("reports-v2/iteration_v2-005")
OUT_DIR = Path("reports-v2/iteration_v2-014_per_symbol_brake")


@dataclass(frozen=True)
class BrakeConfig:
    name: str
    shrink_pct: float
    flatten_pct: float
    shrink_factor: float = 0.5


CONFIGS: tuple[BrakeConfig, ...] = (
    BrakeConfig("none", shrink_pct=float("inf"), flatten_pct=float("inf")),
    BrakeConfig("A_5_10", shrink_pct=5.0, flatten_pct=10.0),
    BrakeConfig("B_6_12", shrink_pct=6.0, flatten_pct=12.0),
    BrakeConfig("C_8_16", shrink_pct=8.0, flatten_pct=16.0),
    BrakeConfig("D_4_8", shrink_pct=4.0, flatten_pct=8.0),
)


def _apply_per_symbol_brake(
    trades: pd.DataFrame, cfg: BrakeConfig
) -> tuple[pd.DataFrame, dict]:
    """Apply an independent brake to each symbol's trade stream.

    Each symbol has its own shadow_equity starting at 1.0. Trades are
    processed in open_time order within each symbol. State is decided
    from the symbol's OWN compound equity DD, so cross-symbol
    contamination is impossible.
    """
    trades = trades.sort_values(["symbol", "open_time"]).reset_index(drop=True).copy()

    effective_factor: list[float] = []
    effective_pnl: list[float] = []
    brake_state: list[str] = []
    per_symbol_dd: list[float] = []

    firing_counts: dict[str, dict[str, int]] = {}

    for sym, group in trades.groupby("symbol", sort=False):
        shadow = 1.0
        peak = 1.0
        n_normal = 0
        n_shrink = 0
        n_flatten = 0

        for _, trade in group.iterrows():
            dd_pct = (shadow - peak) / peak * 100.0  # non-positive

            if -dd_pct >= cfg.flatten_pct:
                eff = 0.0
                state = "flatten"
                n_flatten += 1
            elif -dd_pct >= cfg.shrink_pct:
                eff = cfg.shrink_factor
                state = "shrink"
                n_shrink += 1
            else:
                eff = 1.0
                state = "normal"
                n_normal += 1

            wpnl = float(trade["weighted_pnl"])
            effective_factor.append(eff)
            effective_pnl.append(wpnl * eff)
            brake_state.append(state)
            per_symbol_dd.append(dd_pct)

            # Shadow equity updated from UNBRAKED per-symbol PnL
            shadow *= 1.0 + wpnl / 100.0
            peak = max(peak, shadow)

        firing_counts[sym] = {
            "normal": n_normal,
            "shrink": n_shrink,
            "flatten": n_flatten,
        }

    trades["effective_factor"] = effective_factor
    trades["effective_weighted_pnl"] = effective_pnl
    trades["brake_state"] = brake_state
    trades["per_symbol_dd_before_entry"] = per_symbol_dd

    return trades, firing_counts


def _annualize_daily(daily_pnl: pd.Series, periods: int = 365) -> float:
    if len(daily_pnl) < 2 or daily_pnl.std() == 0:
        return 0.0
    return float(daily_pnl.mean() / daily_pnl.std() * np.sqrt(periods))


def _trade_level_sharpe(pnl: pd.Series) -> float:
    if len(pnl) < 2 or pnl.std() == 0:
        return 0.0
    return float(pnl.mean() / pnl.std() * np.sqrt(len(pnl)))


def _max_drawdown(equity_curve: pd.Series) -> float:
    if len(equity_curve) == 0:
        return 0.0
    rolling_max = equity_curve.cummax()
    dd = (equity_curve - rolling_max) / rolling_max.replace(0, np.nan)
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
    }


def _per_symbol_shares(trades: pd.DataFrame, pnl_col: str) -> pd.DataFrame:
    g = trades.groupby("symbol").agg(
        trades=(pnl_col, "size"),
        wpnl=(pnl_col, "sum"),
    )
    total = g["wpnl"].sum()
    g["share_pct"] = g["wpnl"] / total * 100.0 if total != 0 else 0.0
    return g.sort_values("wpnl", ascending=False)


def main() -> None:
    print("=" * 70)
    print("PER-SYMBOL DRAWDOWN BRAKE FEASIBILITY — iter-v2/014")
    print("=" * 70)

    oos_path = V2_REPORT / "out_of_sample/trades.csv"
    if not oos_path.exists():
        print(f"ERROR: {oos_path} not found")
        return

    trades = pd.read_csv(oos_path)
    print(f"\nLoaded {len(trades)} OOS trades from {oos_path}")
    print(f"Symbols: {sorted(trades['symbol'].unique().tolist())}")
    print(f"Total baseline weighted PnL: {trades['weighted_pnl'].sum():.2f}%")
    print()

    summaries: dict[str, dict] = {}
    per_symbol_tables: dict[str, pd.DataFrame] = {}
    concentration_rows: list[dict] = []
    per_config_firings: dict[str, dict] = {}

    for cfg in CONFIGS:
        braked, firings = _apply_per_symbol_brake(trades, cfg)
        agg = _summarize(braked, "effective_weighted_pnl", cfg.name)
        agg["config"] = {
            "shrink_pct": cfg.shrink_pct if np.isfinite(cfg.shrink_pct) else None,
            "flatten_pct": cfg.flatten_pct if np.isfinite(cfg.flatten_pct) else None,
            "shrink_factor": cfg.shrink_factor,
        }
        summaries[cfg.name] = agg
        per_config_firings[cfg.name] = firings

        # Per-symbol breakdown from braked stream
        psyms = _per_symbol_shares(braked, "effective_weighted_pnl")
        per_symbol_tables[cfg.name] = psyms
        for sym, row in psyms.iterrows():
            concentration_rows.append(
                {
                    "config": cfg.name,
                    "symbol": sym,
                    "trades": int(row["trades"]),
                    "weighted_pnl": round(float(row["wpnl"]), 3),
                    "share_pct": round(float(row["share_pct"]), 2),
                }
            )

    # Headline table
    print("=" * 90)
    print("HEADLINE METRICS (daily-annualized Sharpe, MaxDD, Calmar, concentration)")
    print("=" * 90)
    header = (
        f"{'config':<10} {'shr':>4} {'flt':>4} "
        f"{'sr_tr':>8} {'sr_day':>8} {'MaxDD%':>8} {'Calmar':>7} "
        f"{'PnL%':>7} {'MaxConc%':>9} {'TopSym':>8}"
    )
    print(header)
    print("-" * len(header))
    for name, s in summaries.items():
        cfg = s["config"]
        sh = f"{cfg['shrink_pct']}" if cfg["shrink_pct"] else "—"
        fl = f"{cfg['flatten_pct']}" if cfg["flatten_pct"] else "—"
        psyms = per_symbol_tables[name]
        max_share = float(psyms["share_pct"].max()) if len(psyms) else 0.0
        top_sym = psyms.index[0] if len(psyms) else "—"
        print(
            f"{name:<10} {sh:>4} {fl:>4} "
            f"{s['sharpe_trade']:>+8.4f} "
            f"{s['sharpe_daily_annualized']:>+8.4f} "
            f"{s['max_dd_pct']:>+8.2f} "
            f"{s['calmar']:>+7.2f} "
            f"{s['total_pnl_pct']:>+7.2f} "
            f"{max_share:>+9.2f} {top_sym:>8}"
        )

    print()
    print("=" * 90)
    print("DECISION CRITERIA — pass if: MaxDD<25% AND Sharpe_trade>1.3 AND MaxConc<55%")
    print("=" * 90)
    for name, s in summaries.items():
        if name == "none":
            continue
        mdd_ok = abs(s["max_dd_pct"]) < 25.0
        sr_ok = s["sharpe_trade"] > 1.3
        psyms = per_symbol_tables[name]
        max_share = float(psyms["share_pct"].max()) if len(psyms) else 0.0
        conc_ok = max_share < 55.0
        negative_flip = bool((psyms["wpnl"] < 0).any())
        flip_ok = not negative_flip
        overall = (
            "PASS" if (mdd_ok and sr_ok and conc_ok and flip_ok) else "FAIL"
        )
        print(
            f"  {name}: "
            f"MaxDD={s['max_dd_pct']:+.2f}% ({'ok' if mdd_ok else 'BAD'}) | "
            f"Sharpe={s['sharpe_trade']:+.4f} ({'ok' if sr_ok else 'BAD'}) | "
            f"MaxConc={max_share:.2f}% ({'ok' if conc_ok else 'BAD'}) | "
            f"NegFlip={'no' if flip_ok else 'YES'} "
            f"→ {overall}"
        )

    # Per-symbol concentration for the winner (or best config)
    print()
    print("=" * 90)
    print("PER-SYMBOL BREAKDOWN (each config)")
    print("=" * 90)
    for name in summaries:
        print(f"\n{name}:")
        print(per_symbol_tables[name].to_string())

    print()
    print("=" * 90)
    print("PER-CONFIG BRAKE FIRINGS (by symbol)")
    print("=" * 90)
    for name, firings in per_config_firings.items():
        print(f"\n{name}:")
        for sym, counts in firings.items():
            print(
                f"  {sym}: normal={counts['normal']} "
                f"shrink={counts['shrink']} "
                f"flatten={counts['flatten']}"
            )

    # Persist artifacts
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.json").write_text(json.dumps(summaries, indent=2, default=str))
    pd.DataFrame(concentration_rows).to_csv(
        OUT_DIR / "concentration_matrix.csv", index=False
    )

    # Combined per-config trades
    all_frames = []
    for cfg in CONFIGS:
        braked, _ = _apply_per_symbol_brake(trades, cfg)
        braked = braked.copy()
        braked["brake_config"] = cfg.name
        all_frames.append(braked)
    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv(OUT_DIR / "per_config_trades.csv", index=False)

    print(f"\nArtifacts written to {OUT_DIR}")


if __name__ == "__main__":
    main()
