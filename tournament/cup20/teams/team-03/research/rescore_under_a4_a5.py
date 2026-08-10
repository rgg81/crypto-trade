"""Re-score every banked packet under amendments A4 and A5.

Reads only this team's own packet JSONs, which the organiser's harness wrote into this team's own
research directory. Calls the organiser's own scoring and qualification modules -- this is not a
private scorer, it is arithmetic over numbers the organiser already handed us, and it recomputes
nothing the harness measured.

Under the old rules a missed floor removed the candidate, so the cadence ladder read as a set of
disqualifications. Under A4 the ladder is a ranking, and under A5 a missed floor is a proportional
multiplicative haircut. The question this script answers is which rung now scores highest, and how
sensitive that answer is to the trial count T at nomination.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, "src")

import tomllib

from crypto_trade.cup20.qualification import compliance_factor, floor_credits
from crypto_trade.cup20.scored_metrics import ranking_metrics
from crypto_trade.cup20.scoring import robustness_score

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = tomllib.loads(pathlib.Path("tournament/cup20/config.toml").read_text())
FLOORS = CONFIG["floors"]
DRAWDOWN_FLOOR = float(FLOORS["max_drawdown"])

PACKETS = [
    ("24", "controls off (baseline)", "packet_T24_controls_off.json"),
    ("22", "gate OFF, controls kept", "packet_T22_gate_off.json"),
    ("25", "gate ONLY on baseline", "packet_T25_gate_only.json"),
    ("26", "formation 45", "packet_T26_formation45.json"),
    ("27", "full stack, cadence 1", "packet_T27_cadence1.json"),
    ("21", "full stack, cadence 3", "packet_T21_nominee.json"),
    ("23", "full stack, cadence 9", "packet_T23_slow.json"),
    ("29", "full stack, cadence 21", "packet_T29_weekly.json"),
]


def confidence(bootstrap_b: float, trials: int) -> float:
    return max(0.0, min(1.0, 1.0 - trials * (1.0 - bootstrap_b)))


def score_for(packet: dict, trials: int, b_override: float | None = None) -> tuple[float, float]:
    scored = dict(packet["scored"])
    b = packet["bootstrap_positive_fraction"] if b_override is None else b_override
    inputs = ranking_metrics(scored, trial_adjusted_confidence=confidence(b, trials))
    raw = robustness_score(inputs, drawdown_floor=DRAWDOWN_FLOOR)
    factor = compliance_factor(scored, floors=FLOORS)
    return raw, raw * factor


def main() -> None:
    trials_grid = (9, 10, 11)
    print(f"drawdown floor {DRAWDOWN_FLOOR}; scores are robustness_score x compliance_factor\n")
    header = (
        f"{'seq':>4} {'run':<26} {'wfS2x':>7} {'medS2x':>7} {'dd2x':>6} {'cal2x':>6} "
        f"{'pq2x':>6} {'B':>7} {'fac':>5} " + " ".join(f"G@T={t:<2}" for t in trials_grid)
    )
    print(header)
    print("-" * len(header))
    for seq, label, name in PACKETS:
        packet = json.loads((HERE / name).read_text())
        scored = packet["scored"]
        factor = compliance_factor(scored, floors=FLOORS)
        cells = " ".join(f"{score_for(packet, t)[1]:7.2f}" for t in trials_grid)
        print(
            f"{seq:>4} {label:<26} {scored['worst_fold_sharpe']:7.3f} "
            f"{scored['median_fold_sharpe']:7.3f} {scored['double_cost_max_drawdown']:6.3f} "
            f"{scored['calmar']:6.3f} {scored['double_cost_positive_quarter_fraction']:6.3f} "
            f"{packet['bootstrap_positive_fraction']:7.4f} {factor:5.3f} {cells}"
        )

    print("\nper-term decomposition and the floors A5 prices, for the three live rungs:")
    for seq, label, name in PACKETS:
        if seq not in {"21", "23", "27"}:
            continue
        packet = json.loads((HERE / name).read_text())
        scored = packet["scored"]
        credits = floor_credits(scored, floors=FLOORS)
        missed = {k: round(v, 4) for k, v in credits.items() if v < 1.0}
        raw10, net10 = score_for(packet, 10)
        print(
            f"  #{seq} {label}: raw G@T=10 {raw10:6.2f}, factor "
            f"{compliance_factor(scored, floors=FLOORS):.4f}, net {net10:6.2f}; "
            f"credits below 1.0 = {missed or 'none'}"
        )

    print("\nsensitivity of the nominee rung to the neighbourhood-median haircut (T=10):")
    packet = json.loads((HERE / "packet_T21_nominee.json").read_text())
    for haircut in (0.0, 0.05, 0.10, 0.15, 0.20):
        scored = dict(packet["scored"])
        for key in ("worst_fold_sharpe", "median_fold_sharpe", "calmar"):
            scored[key] = scored[key] * (1.0 - haircut)
        scored["double_cost_max_drawdown"] *= 1.0 + haircut
        shim = {
            "scored": scored,
            "bootstrap_positive_fraction": packet["bootstrap_positive_fraction"] - haircut * 0.05,
        }
        raw, net = score_for(shim, 10)
        print(
            f"  median {haircut:4.0%} below the point: raw {raw:6.2f}  "
            f"factor {compliance_factor(scored, floors=FLOORS):.4f}  net {net:6.2f}"
        )


if __name__ == "__main__":
    main()
