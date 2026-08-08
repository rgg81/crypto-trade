"""Collate the organiser's coaching packets into one table for the certificate."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("tournament/cup20/teams/team-03/research")
ORDER = [
    ("21", "packet_T21_nominee.json", "run-gated-trend (cadence 3)"),
    ("22", "packet_T22_gate_off.json", "gate OFF, other controls kept"),
    ("23", "packet_T23_slow.json", "run-gated-trend-slow (cadence 9)"),
    ("24", "packet_T24_controls_off.json", "all controls off (baseline)"),
    ("25", "packet_T25_gate_only.json", "gate only (on the baseline)"),
    ("26", "packet_T26_formation45.json", "formation 45 bars"),
    ("27", "packet_T27_cadence1.json", "cadence 1 (every bar)"),
    ("29", "packet_T29_weekly.json", "run-gated-trend-weekly (cadence 21)"),
]

FIELDS = [
    ("net_sharpe", "sharpe1x", "{:.3f}"),
    ("annualized_return", "ret1x", "{:.4f}"),
    ("annualized_volatility", "vol", "{:.3f}"),
    ("max_drawdown", "maxDD", "{:.3f}"),
    ("annualized_turnover", "turnover", "{:.2f}"),
    ("gross_edge_bps_per_turnover", "edge/turn", "{:.1f}"),
    ("cost_share_of_positive_gross", "costshare", "{:.4f}"),
    ("long_gross_pnl", "longPnL", "{:+.3f}"),
    ("short_gross_pnl", "shortPnL", "{:+.3f}"),
    ("trade_count", "trades", "{:.0f}"),
    ("positive_quarter_fraction", "posQ", "{:.3f}"),
]


def value(payload: dict, key: str, level: str = "1x") -> float:
    return float(payload["cost_levels"][level][key])


def main() -> None:
    header = (["seq", "what"] + [label for _, label, _ in FIELDS]
              + ["sharpe2x", "folds@2x", "B", "conf@T8", "fails"])
    print(" | ".join(header))
    for sequence, filename, label in ORDER:
        path = ROOT / filename
        if not path.is_file():
            print(f"{sequence} | {label} | (not run)")
            continue
        payload = json.loads(path.read_text())
        row = [sequence, label]
        for key, _, fmt in FIELDS:
            row.append(fmt.format(value(payload, key)))
        row.append("{:.3f}".format(value(payload, "net_sharpe", "2x")))
        folds = payload.get("fold_sharpes") or {}
        values = folds.values() if isinstance(folds, dict) else folds
        row.append(" ".join(f"{float(v):+.2f}" for v in values))
        bootstrap = float(payload.get("bootstrap_positive_fraction", float("nan")))
        row.append(f"{bootstrap:.4f}")
        row.append(f"{max(0.0, 1.0 - 8.0 * (1.0 - bootstrap)):.3f}")
        row.append(",".join(payload.get("measured_failures", ())) or "-")
        print(" | ".join(row))


if __name__ == "__main__":
    main()
