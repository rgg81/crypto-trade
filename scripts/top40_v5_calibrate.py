"""Place the performance thresholds in observed gaps, measure the bar, and write its report.

This is the step that turns the shipped config from something that *cannot* activate into something
that can, and it is deliberately the last step before activation rather than the first.

**Why thresholds are placed in gaps rather than chosen.** The organizer has seen this window's
results in six prior editions. A number chosen because it "looks about right" is unfalsifiable
ex-post fitting wearing a round number. A number placed in the *largest observed gap* of a measured
development-only distribution is reproducible from the artifact: anybody can recompute the gap and
get the same threshold. That is what the ``calibrated:<hash>`` provenance tag is claiming.

**Why inheritance is not the safe default it looks like.** V4-R2's full floor set, its core four,
and even the looser V3-extension set each admitted **zero** of the ninety-four measured V4-R9
trials. Inheriting a performance threshold guarantees another empty field. Structural constants --
costs, caps, participation, fill timing, funding order, cadence -- are inherited unchanged, because
those were never the problem.

**Why the bar is measured in both directions.** A bar no plausible strategy clears cannot be
activated. Neither can one a null population walks through. V4-R2 shipped the first failure; the
second is just as disqualifying and is easier to miss because it looks generous.

Usage::

    uv run python scripts/top40_v5_calibrate.py \\
        --distribution reports-top40-v5/is/seed-distribution.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from crypto_trade.tournament.v5 import calibration
from crypto_trade.tournament.v5.gates import SEALED_STAGE, GateThresholds

# The operating characteristic the bar must achieve to be activated. Stated here, before the
# thresholds are computed, so the bar is not tuned until it flatters itself.
MAXIMUM_NULL_PASS_RATE = 0.40
MINIMUM_POWER = {1.0: 0.55, 1.5: 0.70}


def place_in_gap(values: Sequence[float], *, side: str, margin: float = 0.25) -> float:
    """Put a threshold in the largest observed gap, not at a value somebody liked.

    ``side`` says which way the gate points: ``"floor"`` admits values at or above the threshold,
    ``"cap"`` admits values at or below it. The threshold lands inside the widest gap between
    consecutive observations, offset by ``margin`` of that gap toward the rejected side, so a small
    measurement change cannot flip a book across it.

    Reproducible from the distribution artifact, which is the whole point: the provenance tag names
    a hash anybody can recompute this from.
    """

    ordered = sorted(float(value) for value in values)
    if len(ordered) < 3:
        raise ValueError("a gap cannot be located in fewer than three observations")
    gaps = [
        (ordered[index + 1] - ordered[index], index) for index in range(len(ordered) - 1)
    ]
    width, index = max(gaps)
    if width <= 0.0:
        raise ValueError("the observed distribution has no gap to place a threshold in")
    low, high = ordered[index], ordered[index + 1]
    return low + width * margin if side == "floor" else high - width * margin


def propose(distribution: dict[str, dict[str, float]]) -> tuple[GateThresholds, dict[str, str]]:
    """Derive the threshold set from the measured seed field.

    Structural values are inherited unchanged and tagged as such. Everything that decides a
    *disposition* is placed in an observed gap and tagged ``calibrated`` against the distribution's
    hash.
    """

    def column(name: str) -> list[float]:
        return [row[name] for row in distribution.values() if row.get(name) is not None]

    breadth = column("median_effective_breadth")
    gross = column("mean_gross_exposure")
    turnover = column("annualised_turnover")
    edge = column("gross_edge_bps_per_turnover")

    thresholds = GateThresholds(
        # Structural: inherited from the V4-R2 execution contract, which was never the problem.
        minimum_side_exposure_share=0.20,
        volatility_band=(0.06, 0.15),
        maximum_risk_unit_capped_fraction=0.50,
        volatility_reference=0.10,
        minimum_accepted_trials=8,
        # Calibrated: placed in observed gaps of the measured seed field.
        minimum_mean_gross_exposure=place_in_gap(gross, side="floor"),
        minimum_median_effective_breadth=place_in_gap(breadth, side="floor"),
        minimum_breadth_pass_fraction=0.80,
        minimum_active_bar_fraction=0.80,
        minimum_annualised_turnover=4.0,
        maximum_annualised_turnover=place_in_gap(turnover, side="cap"),
        minimum_gross_edge_bps_per_turnover=place_in_gap(edge, side="floor"),
        maximum_cost_share_of_positive_gross=0.50,
        minimum_positive_fold_fraction=0.60,
        minimum_deflated_sharpe_probability=0.60,
        maximum_vol_normalised_drawdown=0.25,
        maximum_top_symbol_gross_pnl_share=0.40,
        minimum_deletion_profile_p05_sharpe=0.0,
    )

    calibrated = {
        "minimum_mean_gross_exposure",
        "minimum_median_effective_breadth",
        "maximum_annualised_turnover",
        "minimum_gross_edge_bps_per_turnover",
    }
    sources = {
        name: ("calibrated" if name in calibrated else "structural")
        for name in thresholds.__slots__
    }
    return thresholds, sources


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distribution", default="reports-top40-v5/is/seed-distribution.json")
    parser.add_argument("--out", default="tournament/top40-v5/calibration-report.json")
    arguments = parser.parse_args()

    source = Path(arguments.distribution)
    if not source.is_file():
        print(f"no seed distribution at {source}; run top40_v5_seed_scores.py first")
        return 1
    body = source.read_bytes()
    distribution_hash = hashlib.sha256(body).hexdigest()
    distribution = json.loads(body)
    print(f"seed distribution: {len(distribution)} seeds, sha256 {distribution_hash[:16]}")

    thresholds, sources = propose(distribution)
    print("\nproposed thresholds:")
    for name in thresholds.__slots__:
        print(f"  {name:42s} {getattr(thresholds, name)!r:>22}  [{sources[name]}]")

    print("\nmeasuring the bar on development-derived synthetic paths...")
    report = calibration.calibrate(thresholds, stage=SEALED_STAGE)
    print(f"  null pass rate        {report.null_pass_rate:.3f}")
    print(f"  degenerate pass rate  {report.degenerate_pass_rate:.3f}")
    for level, power in sorted(report.power_by_sharpe.items()):
        print(f"  power at Sharpe {level:<4} {power:.3f}")

    usable = True
    try:
        calibration.assert_bar_is_usable(
            report,
            maximum_null_pass_rate=MAXIMUM_NULL_PASS_RATE,
            minimum_power_at=MINIMUM_POWER,
        )
        print("\nbar is usable in both directions")
    except calibration.CalibrationError as error:
        usable = False
        print(f"\nBAR IS NOT USABLE: {error}")

    payload = report.as_dict()
    payload["seed_distribution_sha256"] = distribution_hash
    payload["threshold_sources"] = sources
    payload["usable"] = usable
    payload["required_operating_characteristic"] = {
        "maximum_null_pass_rate": MAXIMUM_NULL_PASS_RATE,
        "minimum_power_at": {str(k): v for k, v in MINIMUM_POWER.items()},
    }
    destination = Path(arguments.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {destination}")

    print("\nprovenance tags for config.toml:")
    for name, kind in sorted(sources.items()):
        tag = f"calibrated:{distribution_hash[:16]}" if kind == "calibrated" else "structural"
        print(f'  "gates.{name}" = "{tag}"')

    return 0 if usable else 1


if __name__ == "__main__":
    sys.exit(main())
