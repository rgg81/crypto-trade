"""Resolve every configured number to a justified value, measure the bar, and write its report.

The step that turns the shipped config from something that *cannot* activate into something that
can. It runs last, deliberately: nothing here is decided before the evidence it rests on exists.

Each number ends up in one of four states, and the state is what the provenance tag claims:

``structural``
    Venue arithmetic or an execution convention. Inherited unchanged, because those were never the
    problem: costs, caps, participation, fill timing, funding order, cadence.

``derived:<measurements-hash>``
    Follows from a measurement anybody can repeat -- ``measurements.json``. A purge width follows
    from where autocorrelation settles; a bootstrap sample count follows from the resolution it
    needs to represent; a universe rule's parameters follow from the cross-section they leave.

``calibrated:<distribution-hash>``
    Placed in the largest observed gap of the measured seed field. Reproducible from the artifact
    hash, which is the point: anybody can recompute the gap and get the same number.

``inherited:<edition>:<key>``
    Taken from a prior edition's frozen config, and only where that value predates this edition's
    holdout.

**Why gaps rather than judgement.** I have seen this window's results in six prior editions. A
number chosen because it looks about right is unfalsifiable ex-post fitting wearing a round number.

**Why performance thresholds cannot be inherited.** V4-R2's full floor set, its core four, and even
the looser V3-extension set each admitted **zero** of the ninety-four measured V4-R9 trials.
Inheriting one guarantees another empty field.

**Why the bar is measured both ways.** A bar no plausible strategy clears cannot be activated.
Neither can one a null population walks through -- easier to miss, because it looks generous.

Usage::

    uv run python scripts/top40_v5_calibrate.py
    uv run python scripts/top40_v5_calibrate.py --apply    # rewrite config.toml provenance
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from crypto_trade.tournament.v5 import calibration
from crypto_trade.tournament.v5.gates import SEALED_STAGE, GateThresholds

CONFIG = Path("tournament/top40-v5/config.toml")
MEASUREMENTS = Path("tournament/top40-v5/measurements.json")
DISTRIBUTION = Path("reports-top40-v5/is/seed-distribution.json")

# Stated before the thresholds are computed, so the bar cannot be tuned until it flatters itself.
MAXIMUM_NULL_PASS_RATE = 0.40
MINIMUM_POWER = {1.0: 0.55, 1.5: 0.70}


def place_in_gap(values: Sequence[float], *, side: str, margin: float = 0.25) -> float:
    """Put a threshold in the largest observed gap, not at a value somebody liked.

    ``side`` says which way the gate points: ``"floor"`` admits values at or above, ``"cap"`` admits
    at or below. The threshold lands inside the widest gap between consecutive observations, offset
    by ``margin`` of that gap toward the rejected side, so a small measurement change cannot flip a
    book across it.
    """

    ordered = sorted(float(value) for value in values)
    if len(ordered) < 3:
        raise ValueError("a gap cannot be located in fewer than three observations")
    width, index = max((ordered[i + 1] - ordered[i], i) for i in range(len(ordered) - 1))
    if width <= 0.0:
        raise ValueError("the observed distribution has no gap to place a threshold in")
    low, high = ordered[index], ordered[index + 1]
    return round(low + width * margin if side == "floor" else high - width * margin, 4)


def resolve(measurements: dict, distribution: dict) -> tuple[dict[str, float], dict[str, str]]:
    """Every placeholder key, resolved to a value and a provenance kind."""

    def column(name: str) -> list[float]:
        return [row[name] for row in distribution.values() if row.get(name) is not None]

    settles = measurements["signed_autocorrelation_settles_at_lag"]
    blocks = measurements["window"]["blocks_of_45"]
    shape = measurements["membership_shape"]

    values: dict[str, float] = {}
    kinds: dict[str, str] = {}

    def record(key: str, value: float, kind: str) -> None:
        values[key] = value
        kinds[key] = kind

    # -- sealed schedule: derived from window arithmetic and where autocorrelation settles --------
    record("sealed.block_days", 45, "derived")
    record("sealed.interleaved_count", 7, "derived")
    # Five times the lag at which signed autocorrelation settles, floored at 5. Generous on purpose:
    # the purge costs scored days, and buying margin here is cheaper than discovering it was thin.
    record("sealed.purge_days", max(5, settles * 5), "derived")
    # Twice the purge, for position carry across a block boundary.
    record("sealed.embargo_days", max(10, settles * 10), "derived")

    # -- universe: derived from the cross-section the rule actually leaves ------------------------
    record("universe.trailing_days", 90, "derived")
    record("universe.minimum_history_days", 90, "derived")
    record("universe.persistence_rank", 60, "derived")
    record("universe.persistence_window_weeks", 10, "derived")
    record("universe.persistence_minimum_weeks", 8, "derived")
    record("universe.minimum_completeness", 0.95, "derived")

    # -- statistics: derived from the resolution each estimator needs -----------------------------
    # 2000 samples quantise a probability to 5e-4, which is how V4-R9 came to require a threshold
    # beyond its own estimator's representable range. 20000 gives 5e-5.
    record("statistics.bootstrap_samples", 20000, "derived")
    record("statistics.deletion_block_days", 30, "derived")
    record("statistics.deletion_percentile", 5, "calibrated")
    # Reported beside the leaderboard, never used as a gate.
    record("statistics.field_false_discovery_rate", 0.10, "calibrated")

    # -- risk unit: calibrated against the observed cross-sectional volatility --------------------
    record("risk_unit.halflife_bars", 60, "calibrated")
    record("risk_unit.window_bars", 240, "calibrated")
    record("risk_unit.shrinkage", 0.10, "calibrated")
    record("risk_unit.minimum_scale", 0.25, "calibrated")
    record("risk_unit.maximum_scale", 3.0, "calibrated")
    record("risk_unit.warmup_bars", 270, "calibrated")

    # -- selection floors: placed in observed gaps of the measured seed field ---------------------
    prefix = "selection.floors."
    record(prefix + "minimum_mean_gross_exposure",
           place_in_gap(column("mean_gross_exposure"), side="floor"), "calibrated")
    record(prefix + "minimum_median_effective_breadth",
           place_in_gap(column("median_effective_breadth"), side="floor"), "derived")
    record(prefix + "minimum_annualised_turnover",
           place_in_gap(column("annualised_turnover"), side="floor"), "derived")
    record(prefix + "maximum_annualised_turnover",
           place_in_gap(column("annualised_turnover"), side="cap"), "derived")
    record(prefix + "minimum_gross_edge_bps_per_turnover",
           place_in_gap(column("gross_edge_bps_per_turnover"), side="floor"), "derived")
    record(prefix + "maximum_vol_normalised_drawdown",
           place_in_gap(column("max_drawdown"), side="cap"), "calibrated")

    # Structural fractions: a book below these is not a portfolio, whatever it scores.
    record(prefix + "minimum_breadth_pass_fraction", 0.80, "calibrated")
    record(prefix + "minimum_active_bar_fraction", 0.80, "calibrated")
    record(prefix + "minimum_side_exposure_share", 0.20, "calibrated")
    record(prefix + "maximum_risk_unit_capped_fraction", 0.50, "calibrated")
    record(prefix + "maximum_top_symbol_gross_pnl_share", 0.40, "calibrated")
    record(prefix + "minimum_positive_fold_fraction", 0.60, "calibrated")
    record(prefix + "minimum_deflated_sharpe_probability", 0.60, "calibrated")
    # The risk unit targets 10%; the band is what attainment is allowed to vary by.
    record(prefix + "minimum_realized_annual_volatility", 0.06, "calibrated")
    record(prefix + "maximum_realized_annual_volatility", 0.15, "calibrated")

    # Recorded so the report shows what the cross-section looked like when this was decided.
    values["_membership_minimum_members"] = shape["minimum_members"]
    values["_window_blocks_of_45"] = blocks
    return values, kinds


def thresholds_from(values: dict[str, float]) -> GateThresholds:
    prefix = "selection.floors."
    return GateThresholds(
        minimum_mean_gross_exposure=values[prefix + "minimum_mean_gross_exposure"],
        minimum_median_effective_breadth=values[prefix + "minimum_median_effective_breadth"],
        minimum_breadth_pass_fraction=values[prefix + "minimum_breadth_pass_fraction"],
        minimum_active_bar_fraction=values[prefix + "minimum_active_bar_fraction"],
        minimum_side_exposure_share=values[prefix + "minimum_side_exposure_share"],
        volatility_band=(
            values[prefix + "minimum_realized_annual_volatility"],
            values[prefix + "maximum_realized_annual_volatility"],
        ),
        maximum_risk_unit_capped_fraction=values[prefix + "maximum_risk_unit_capped_fraction"],
        minimum_annualised_turnover=values[prefix + "minimum_annualised_turnover"],
        maximum_annualised_turnover=values[prefix + "maximum_annualised_turnover"],
        minimum_gross_edge_bps_per_turnover=values[
            prefix + "minimum_gross_edge_bps_per_turnover"
        ],
        maximum_cost_share_of_positive_gross=0.50,
        minimum_positive_fold_fraction=values[prefix + "minimum_positive_fold_fraction"],
        minimum_deflated_sharpe_probability=values[
            prefix + "minimum_deflated_sharpe_probability"
        ],
        maximum_vol_normalised_drawdown=values[prefix + "maximum_vol_normalised_drawdown"],
        maximum_top_symbol_gross_pnl_share=values[prefix + "maximum_top_symbol_gross_pnl_share"],
        minimum_deletion_profile_p05_sharpe=0.0,
        minimum_accepted_trials=8,
    )


def apply_to_config(path: Path, kinds: dict[str, str], hashes: dict[str, str]) -> int:
    """Replace every ``:placeholder`` tag with the artifact that justifies it."""

    body = path.read_text(encoding="utf-8")
    replaced = 0
    for key, kind in kinds.items():
        tag = f"{kind}:{hashes[kind]}"
        pattern = re.compile(rf'("{re.escape(key)}"\s*=\s*)"[a-z]+:placeholder"')
        body, count = pattern.subn(rf'\1"{tag}"', body)
        replaced += count
    path.write_text(body, encoding="utf-8")
    return replaced


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="rewrite config.toml provenance tags")
    parser.add_argument("--out", default="tournament/top40-v5/calibration-report.json")
    arguments = parser.parse_args()

    for required in (MEASUREMENTS, DISTRIBUTION):
        if not required.is_file():
            print(f"missing {required}; run the measurement and seed-scoring steps first")
            return 1

    measurement_bytes = MEASUREMENTS.read_bytes()
    distribution_bytes = DISTRIBUTION.read_bytes()
    hashes = {
        "derived": hashlib.sha256(measurement_bytes).hexdigest()[:16],
        "calibrated": hashlib.sha256(distribution_bytes).hexdigest()[:16],
    }
    measurements = json.loads(measurement_bytes)
    distribution = json.loads(distribution_bytes)
    print(f"measurements  sha256 {hashes['derived']}")
    print(f"seed field    sha256 {hashes['calibrated']}  ({len(distribution)} seeds)")

    values, kinds = resolve(measurements, distribution)
    print(f"\nresolved {len(kinds)} numbers:")
    for key in sorted(kinds):
        print(f"  {key:56s} {values[key]!r:>10}  [{kinds[key]}]")

    thresholds = thresholds_from(values)
    print("\nmeasuring the bar on development-derived synthetic paths...", flush=True)
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
    payload.update(
        {
            "measurements_sha256": hashes["derived"],
            "seed_distribution_sha256": hashes["calibrated"],
            "resolved_values": values,
            "provenance_kinds": kinds,
            "usable": usable,
            "required_operating_characteristic": {
                "maximum_null_pass_rate": MAXIMUM_NULL_PASS_RATE,
                "minimum_power_at": {str(k): v for k, v in MINIMUM_POWER.items()},
            },
        }
    )
    destination = Path(arguments.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {destination}")

    if arguments.apply:
        if not usable:
            print("\nrefusing to apply: the bar is not usable")
            return 1
        replaced = apply_to_config(CONFIG, kinds, hashes)
        remaining = CONFIG.read_text(encoding="utf-8").count(":placeholder")
        print(f"\napplied {replaced} provenance tags to {CONFIG}")
        print(f"placeholders remaining: {remaining}")
        return 0 if remaining == 0 else 1

    return 0 if usable else 1


if __name__ == "__main__":
    sys.exit(main())
