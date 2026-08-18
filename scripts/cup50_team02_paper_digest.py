#!/usr/bin/env python3
"""Concise read-only performance and integrity digest for the Team-02 desk."""

from __future__ import annotations

import argparse
from pathlib import Path

from cup50_team02_paper_healthcheck import health_status


def main() -> int:
    parser = argparse.ArgumentParser(description="CUP-50 Team-02 paper digest")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--skip-process", action="store_true")
    args = parser.parse_args()
    alerts, notes, stats = health_status(skip_process=args.skip_process)
    status = "FAILED" if alerts else str(stats.get("status", "HEALTHY"))
    lines = [
        "# CUP-50 Team 02 forward paper desk",
        "",
        f"- Status: {status}",
        f"- Latest boundary: {stats.get('latest_boundary', 'not observed yet')}",
        f"- Dynamic members: {stats.get('membership_count', 'not observed yet')}",
        f"- Equity: {stats.get('equity', 'not observed yet')}",
        f"- Official return: {stats.get('official_return', 0.0):.6%}",
        f"- Maximum drawdown: {stats.get('maximum_drawdown', 0.0):.6%}",
        f"- Annualized 8-hour volatility: {stats.get('annualized_volatility', 0.0):.6%}",
        f"- Mean turnover: {stats.get('mean_turnover', 0.0):.6f}",
        f"- Mean gross exposure: {stats.get('mean_gross_exposure', 0.0):.6f}",
        "- Largest absolute 8-hour return: "
        f"{stats.get('maximum_absolute_interval_return', 0.0):.6%}",
        f"- Official 8-hour observations: {stats.get('official_observations', 0)}",
        f"- Forward days: {stats.get('forward_days', 0)} / 365 minimum",
        "- Exact historical replay: "
        + ("pass" if not any("PARITY" in item for item in alerts) else "fail"),
        "- Append invariance: "
        + ("pass" if not any("INVARIANCE" in item for item in alerts) else "fail"),
        f"- Public data only: {'pass' if not any('PUBLIC' in item for item in alerts) else 'fail'}",
    ]
    if alerts:
        lines.extend(["", "## Alerts", "", *[f"- {item}" for item in alerts]])
    if notes:
        lines.extend(["", "## Checks", "", *[f"- {item}" for item in notes]])
    payload = "\n".join(lines) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")
    return 1 if alerts else 0


if __name__ == "__main__":
    raise SystemExit(main())
