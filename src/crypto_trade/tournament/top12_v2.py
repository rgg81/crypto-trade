"""Fail-closed machine contract for the three-stage Top-12 V2 tournament."""

from __future__ import annotations

import dataclasses
import hashlib
import math
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from crypto_trade.tournament.layout_top12_v2 import TOP12_V2_LAYOUT

TEAM_IDS = TOP12_V2_LAYOUT.team_ids

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "name",
        "policy_status",
        "charter_path",
        "teams",
        "paths",
        "data",
        "splits",
        "universe",
        "execution",
        "regimes",
        "statistics",
        "research",
        "isolation",
        "selection",
        "is_confirmation",
        "historical_oos",
        "ensemble",
        "mandates",
    }
)

_EXPECTED_PATHS = {
    "tournament_root": "tournament/top12-v2",
    "reports_root": "reports-top12-v2",
    "team_root": "tournament/top12-v2/teams",
    "research_journal": "tournament/top12-v2/research-journal.jsonl",
    "nomination_registry": "tournament/top12-v2/nomination-registry.json",
    "selection_freeze": "tournament/top12-v2/selection-freeze.json",
    "activation_freeze": "tournament/top12-v2/activation-freeze.json",
    "confirmation_freeze": "tournament/top12-v2/confirmation-freeze.json",
    "source_archive_root": "reports-top12-v2/source-archives/sha256",
    "is_reports_root": "reports-top12-v2/is",
    "private_confirmation_root": "tournament/top12-v2/private/is-confirmation",
    "confirmation_release_root": "reports-top12-v2/is-confirmation",
    "private_final_root": "tournament/top12-v2/private/historical-oos",
    "final_release_root": "reports-top12-v2/historical-oos",
    "mechanism_registry": "tournament/top12-v2/ORCHESTRATOR-MECHANISM-REGISTRY.json",
}

_EXPECTED_FOLDS = (
    ("2020H2", "2020-08-03T00:00:00Z", "2021-01-01T00:00:00Z"),
    ("2021H1", "2021-01-01T00:00:00Z", "2021-07-01T00:00:00Z"),
    ("2021H2", "2021-07-01T00:00:00Z", "2022-01-01T00:00:00Z"),
    ("2022H1", "2022-01-01T00:00:00Z", "2022-07-01T00:00:00Z"),
    ("2022H2", "2022-07-01T00:00:00Z", "2023-01-01T00:00:00Z"),
    ("2023H1", "2023-01-01T00:00:00Z", "2023-07-01T00:00:00Z"),
)

_EXPECTED_MANDATES = {
    "team-01": "residual-trend-quality-consensus",
    "team-02": "funding-price-dislocation-repair",
    "team-03": "volume-participation-breadth-thrust",
    "team-04": "realized-volatility-term-structure-breakout",
    "team-05": "funding-dispersion-carry-quality",
    "team-06": "liquidity-shock-impact-persistence",
    "team-07": "correlation-dispersion-regime-allocation",
    "team-08": "intrabar-close-location-persistence",
    "team-09": "signed-volume-pressure-persistence",
    "team-10": "calendar-boundary-flow-reversal",
    "team-11": "drawdown-recovery-asymmetry",
    "team-12": "tail-concentration-defensive-rotation",
}


@dataclasses.dataclass(frozen=True, slots=True)
class LoadedV4Config:
    """Canonical V4 config bytes and parsed policy."""

    path: Path
    sha256: str
    raw: Mapping[str, Any]


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"V4 config {label} must be a table")
    return value


def _sequence(value: object, label: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"V4 config {label} must be an array")
    return value


def _expect(raw: Mapping[str, Any], path: tuple[str, ...], expected: object) -> None:
    current: object = raw
    for component in path:
        current = _mapping(current, ".".join(path)).get(component)
    if current != expected:
        raise ValueError(f"V4 config {'.'.join(path)} differs from the frozen contract")


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"V4 config {label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"V4 config {label} must be finite")
    return result


def validate_config(raw: Mapping[str, Any]) -> None:
    """Reject any semantic drift in the activated V4 policy."""

    if set(raw) != _TOP_LEVEL_KEYS:
        raise ValueError("V4 config has missing or unexpected top-level tables")
    _expect(raw, ("schema_version",), 1)
    _expect(raw, ("name",), TOP12_V2_LAYOUT.name)
    _expect(raw, ("policy_status",), "active-pending-activation")
    _expect(raw, ("charter_path",), "TOURNAMENT-CHARTER-TOP12-V2.md")
    if tuple(_sequence(raw.get("teams"), "teams")) != TEAM_IDS:
        raise ValueError("V4 config must contain exactly team-01 through team-12")
    paths = _mapping(raw.get("paths"), "paths")
    if dict(paths) != _EXPECTED_PATHS:
        raise ValueError("V4 config paths differ from the isolated V4 namespace")

    critical: dict[tuple[str, ...], object] = {
        ("data", "source"): "binance-public-usdm",
        ("data", "venue"): "binance-usdm",
        ("data", "instrument"): "linear-usdt-perpetual",
        ("data", "transaction_interval"): "8h",
        ("data", "warmup_start"): "2020-01-01T00:00:00Z",
        ("data", "hard_end_exclusive"): "2026-07-01T00:00:00Z",
        ("data", "manifest_path"): "tournament/top12/data_manifest.json",
        ("data", "manifest_sha256"): (
            "0ced737d1ee62f5a45470c7e363510d4e30aa5a9eb98f82cd17df94caac31198"
        ),
        ("splits", "is", "start"): "2020-08-03T00:00:00Z",
        ("splits", "is", "end_exclusive"): "2023-07-01T00:00:00Z",
        ("splits", "is_confirmation", "start"): "2023-07-01T00:00:00Z",
        ("splits", "is_confirmation", "end_exclusive"): "2024-07-01T00:00:00Z",
        ("splits", "is_confirmation", "raw_data_visible_to_teams"): False,
        (
            "splits",
            "is_confirmation",
            "feedback",
        ): "one-atomic-simultaneous-release-after-selection-freeze",
        ("splits", "historical_oos", "start"): "2024-07-01T00:00:00Z",
        ("splits", "historical_oos", "end_exclusive"): "2026-07-01T00:00:00Z",
        ("splits", "historical_oos", "globally_pristine"): False,
        ("splits", "historical_oos", "candidate_relative_oos"): True,
        ("splits", "live_forward", "start"): "2026-08-03T00:00:00Z",
        ("splits", "live_forward", "minimum_observation_days"): 365,
        ("universe", "size"): 12,
        ("universe", "reconstitution"): "weekly-monday-00:00-utc",
        ("universe", "liquidity_measure"): "frozen-median-daily-quote-volume",
        ("universe", "trailing_days"): 180,
        ("universe", "minimum_history_days"): 180,
        ("universe", "history_completeness"): "exactly-180-complete-utc-days",
        (
            "universe",
            "ranking_information_end",
        ): "strictly-before-reconstitution-boundary",
        ("universe", "tie_breaker"): "lexicographically-smaller-symbol",
        ("universe", "membership_path"): "data/top12/snapshot-v1/membership.parquet",
        ("universe", "eligibility_mode"): "fail-closed-native-crypto",
        ("universe", "allowed_economic_exposure"): "native-crypto-only",
        ("universe", "unknown_classification_is_ineligible"): True,
        ("execution", "base_interval"): "8h",
        ("execution", "initial_equity_usdt"): 100000.0,
        ("execution", "taker_fee_bps_per_side"): 5.0,
        ("execution", "slippage_bps_per_side"): 2.5,
        ("execution", "max_gross_exposure"): 1.0,
        ("execution", "max_abs_net_exposure"): 0.25,
        ("execution", "max_symbol_exposure"): 0.10,
        ("execution", "max_bar_participation"): 0.001,
        ("execution", "double_cost_multiplier"): 2.0,
        ("execution", "triple_cost_multiplier"): 3.0,
        ("execution", "annualization_days"): 365,
        ("execution", "fill_timing"): "next-executable-open",
        (
            "execution",
            "funding_at_rebalance_order",
        ): "funding-on-carried-position-then-rebalance",
        ("regimes", "names"): ["bull", "bear", "chop", "stress"],
        ("regimes", "source"): "frozen-lagged-btc-regimes",
        ("regimes", "stress_trailing_days"): 30,
        ("regimes", "stress_annualized_btc_vol"): 0.80,
        ("regimes", "direction_trailing_days"): 60,
        ("regimes", "bull_btc_return"): 0.10,
        ("regimes", "bear_btc_return"): -0.10,
        ("regimes", "lag_days"): 1,
        ("regimes", "positive_sharpe_comparison"): "strictly-greater-than-zero",
        ("statistics", "bootstrap_samples"): 2000,
        ("statistics", "bootstrap_block_days"): 10,
        ("statistics", "bootstrap_seed"): 20260731,
        ("statistics", "maximum_drawdown_is_positive_magnitude"): True,
        ("research", "strategy_seed"): 20260731,
        ("research", "maximum_accepted_trials_per_team"): 16,
        ("research", "minimum_accepted_trials_before_nomination"): 13,
        ("research", "maximum_mechanism_pivots_per_team"): 1,
        ("research", "accepted_failure_consumes_trial"): True,
        ("research", "journal_before_market_access"): True,
        ("research", "exact_replay_required_for_success"): False,
        ("research", "candidate_metadata_filename"): "candidate.json",
        ("research", "core_evidence_deadline_trial"): 8,
        ("research", "neighborhood_first_trial"): 9,
        ("research", "neighborhood_last_required_trial"): 13,
        ("research", "post_neighborhood_tag"): "neighborhood-repair",
        (
            "research",
            "required_certificate_tags",
        ): [
            "baseline",
            "sign-inversion",
            "formation-grid",
            "rebalance-grid",
            "control-ablation",
            "role-check",
            "local-neighborhood",
        ],
        ("research", "minimum_distinct_formation_horizons"): 3,
        ("research", "minimum_distinct_rebalance_horizons"): 2,
        ("research", "minimum_distinct_control_profiles"): 3,
        ("research", "minimum_neighborhood_points"): 5,
        ("research", "minimum_neighborhood_pass_fraction"): 0.80,
        ("research", "minimum_neighborhood_median_double_cost_sharpe"): 0.75,
        ("selection", "floors", "minimum_net_sharpe_inclusive"): 1.0,
        ("selection", "floors", "minimum_annualized_return_inclusive"): 0.06,
        ("selection", "floors", "maximum_drawdown_inclusive"): 0.20,
        ("selection", "floors", "minimum_double_cost_sharpe_inclusive"): 0.80,
        ("selection", "floors", "minimum_triple_cost_sharpe_exclusive"): 0.25,
        ("selection", "floors", "minimum_positive_quarter_fraction_inclusive"): 0.67,
        ("selection", "floors", "minimum_positive_base_folds"): 5,
        ("selection", "floors", "minimum_positive_double_cost_folds"): 5,
        ("selection", "floors", "minimum_worst_fold_sharpe_inclusive"): -0.25,
        ("selection", "floors", "minimum_median_fold_sharpe_inclusive"): 0.75,
        ("selection", "floors", "maximum_annualized_turnover_inclusive"): 18.0,
        ("selection", "floors", "minimum_gross_edge_per_turnover_bps_inclusive"): 60.0,
        ("selection", "floors", "maximum_base_cost_share_inclusive"): 0.25,
        ("selection", "floors", "minimum_trial_adjusted_confidence_inclusive"): 0.75,
        ("selection", "floors", "minimum_bull_sharpe_exclusive"): 0.0,
        ("selection", "floors", "minimum_bear_sharpe_exclusive"): 0.0,
        ("selection", "floors", "minimum_chop_sharpe_exclusive"): 0.0,
        ("selection", "floors", "minimum_stress_sharpe_inclusive"): -0.50,
        ("selection", "floors", "minimum_long_gross_pnl_exclusive"): 0.0,
        ("selection", "floors", "minimum_short_gross_pnl_exclusive"): 0.0,
        (
            "selection",
            "floors",
            "maximum_top_five_day_absolute_return_share_inclusive",
        ): 0.30,
        ("selection", "floors", "maximum_fold_positive_pnl_share_inclusive"): 0.55,
        ("selection", "ranking", "advance_count"): 4,
        ("selection", "ranking", "advance_all_when_fewer"): True,
        ("selection", "ranking", "lower_floors_to_fill_bracket"): False,
        ("is_confirmation", "maximum_observations_per_nominee"): 1,
        ("is_confirmation", "serial_execution"): True,
        ("is_confirmation", "interim_disclosure"): False,
        ("is_confirmation", "failure_consumes_observation"): True,
        ("is_confirmation", "retry_allowed"): False,
        ("is_confirmation", "replacement_allowed"): False,
        ("is_confirmation", "atomic_release"): True,
        ("is_confirmation", "minimum_base_annualized_return_exclusive"): 0.0,
        ("is_confirmation", "minimum_double_cost_annualized_return_exclusive"): 0.0,
        ("is_confirmation", "minimum_base_sharpe_inclusive"): 0.60,
        ("is_confirmation", "minimum_double_cost_sharpe_inclusive"): 0.50,
        ("is_confirmation", "maximum_drawdown_inclusive"): 0.20,
        ("is_confirmation", "minimum_positive_quarters"): 3,
        ("is_confirmation", "maximum_annualized_turnover_inclusive"): 18.0,
        ("is_confirmation", "minimum_gross_edge_per_turnover_bps_inclusive"): 50.0,
        ("is_confirmation", "maximum_base_cost_share_inclusive"): 0.25,
        ("is_confirmation", "no_qualifier_means_no_finalist"): True,
        ("historical_oos", "maximum_observations_per_finalist"): 1,
        ("historical_oos", "serial_execution"): True,
        ("historical_oos", "interim_disclosure"): False,
        ("historical_oos", "failure_consumes_observation"): True,
        ("historical_oos", "retry_allowed"): False,
        ("historical_oos", "replacement_allowed"): False,
        ("historical_oos", "atomic_release"): True,
        (
            "historical_oos",
            "winner_eligibility",
            "minimum_base_annualized_return_exclusive",
        ): 0.03,
        (
            "historical_oos",
            "winner_eligibility",
            "minimum_double_cost_annualized_return_exclusive",
        ): 0.015,
        (
            "historical_oos",
            "winner_eligibility",
            "minimum_double_cost_sharpe_exclusive",
        ): 0.50,
        ("historical_oos", "winner_eligibility", "maximum_drawdown_inclusive"): 0.25,
        ("historical_oos", "winner_eligibility", "minimum_positive_quarters"): 5,
        ("ensemble", "weight_method"): "capped-inverse-is-daily-volatility",
        ("ensemble", "maximum_constituent_weight"): 0.30,
        ("ensemble", "minimum_constituents"): 2,
        ("ensemble", "weights_use_is_only"): True,
        ("ensemble", "failed_constituent_weight"): "cash-no-redistribution",
        ("ensemble", "aggregation"): "weighted-after-cost-sleeve-daily-returns",
        ("ensemble", "oos_reweighting_allowed"): False,
        ("ensemble", "winner_eligible"): False,
    }
    for path, expected in critical.items():
        _expect(raw, path, expected)

    _expect(
        raw,
        ("universe", "forbidden_exposures"),
        [
            "stablecoin",
            "fiat-proxy",
            "leveraged-token",
            "tokenized-metal",
            "tokenized-commodity",
            "direct-metal",
            "direct-commodity",
            "equity",
            "stock",
            "etf",
            "fund",
            "index",
            "forex",
            "fx",
            "premarket",
            "tradfi",
        ],
    )
    a6_expected = {
        "policy_id": "top12-v1-pure-crypto-six-month-liquidity-v1",
        "policy_sha256": "9459e7dd55bdee32fa4b949db9c219473cb82b8889ed185de5cbe57975d67345",
        "audit_module_path": "src/crypto_trade/tournament/top12_universe_v1.py",
        "audit_module_sha256": "c64de55fc314d56fb2d832276405c176170ea0ce4da8db5c2802857db0f05dac",
        "classification_dependency_path": (
            "src/crypto_trade/tournament/pure_crypto_universe_v6.py"
        ),
        "classification_dependency_sha256": (
            "fc93c0f26dcbf6304abe028736693ab2bee7430a56c14a8547defff472008192"
        ),
        "builder_path": "scripts/build_top12_universe.py",
        "builder_sha256": "2ea5708599627822dab2ae13ca22795fe3bcec3de96c95ab90659f1c54a44825",
        "build_record_path": "tournament/top12-v1/universe-build.json",
        "build_record_sha256": (
            "baa28a2ed0a726bb97f44b6793a0bee6b75d5edd183b8909446c0c9e916e8245"
        ),
        "audit_report_sha256": (
            "c5e802373a2dbdc3a6fdee6dce841645a469124f69b3e9226cebe24d51609d2c"
        ),
        "data_manifest_path": "tournament/top12/data_manifest.json",
        "data_manifest_sha256": (
            "0ced737d1ee62f5a45470c7e363510d4e30aa5a9eb98f82cd17df94caac31198"
        ),
        "membership_sha256": (
            "084e4f19b40053fcb2188d35821bedc70ff680ba4af17e7ad032c1253f31fb87"
        ),
        "contract_metadata_sha256": (
            "0995d50011e73de880358b994031fdf8bb58e75ab8901de2c5601e7abed05243"
        ),
        "exchange_info_sha256": "aab4219452e61cfa5e135518ed182c98fd7e527d13bc240e891bb6b550deeb64",
        "expected_contract_metadata_symbols": 667,
        "expected_distinct_membership_symbols": 61,
        "expected_membership_rows": 3708,
        "expected_weekly_reconstitutions": 309,
        "expected_violations": 0,
        "expected_audit_status": "passed",
        "required_before_and_after_every_result_command": True,
    }
    if dict(_mapping(_mapping(raw["universe"], "universe")["a6_authority"], "a6")) != a6_expected:
        raise ValueError("V4 A6 pure-crypto authority differs from the frozen contract")

    isolation_expected = {
        "prior_strategy_blind": True,
        "cross_team_blind": True,
        "rediscovery_of_prior_mechanism_allowed": False,
        "cross_team_mechanism_collision_allowed": False,
        "organizer_registers_pivot_before_market_access": True,
        "previous_oos_tested_mechanisms_ineligible": True,
        "breach_action": "quarantine-team-and-open-incident",
        "team_permitted_common_paths": [
            "TOURNAMENT-CHARTER-TOP12-V2.md",
            "tournament/top12-v2/TEAM-API.md",
            "tournament/top12-v2/TEAM-ISOLATION.md",
        ],
        "forbidden_path_prefixes": [
            "tournament/top40",
            "reports-top40",
            "diary",
            "briefs",
            "tournament/top12-v1",
            "reports-top12-v1",
            "TOURNAMENT-CHARTER-TOP12-V1.md",
            "tournament/top12-v2/ORCHESTRATOR-MECHANISM-REGISTRY.json",
            "reports-top12-v2",
            "tournament/top12-v2/private",
        ],
    }
    if dict(_mapping(raw.get("isolation"), "isolation")) != isolation_expected:
        raise ValueError("Top-12 V2 isolation policy differs from the frozen contract")

    folds = _sequence(_mapping(raw.get("selection"), "selection").get("folds"), "folds")
    normalized_folds = tuple(
        (
            _mapping(fold, "fold").get("name"),
            _mapping(fold, "fold").get("start"),
            _mapping(fold, "fold").get("end_exclusive"),
        )
        for fold in folds
    )
    if normalized_folds != _EXPECTED_FOLDS:
        raise ValueError("V4 chronological folds differ from the frozen contract")
    _expect(
        raw,
        ("selection", "ranking", "sort"),
        [
            "higher-worst-fold-double-cost-sharpe",
            "higher-median-fold-double-cost-sharpe",
            "higher-trial-adjusted-confidence",
            "higher-gross-edge-per-turnover-bps",
            "lower-annualized-turnover",
            "lexicographically-smaller-team-id",
        ],
    )
    _expect(
        raw,
        ("is_confirmation", "ranking", "sort"),
        [
            "higher-min-confirmation-double-cost-sharpe-and-development-median",
            "higher-confirmation-double-cost-sharpe",
            "higher-development-worst-fold-double-cost-sharpe",
            "higher-confirmation-base-annualized-return",
            "lexicographically-smaller-team-id",
        ],
    )
    _expect(
        raw,
        ("historical_oos", "ranking", "sort"),
        [
            "higher-double-cost-sharpe",
            "higher-base-annualized-return",
            "lower-max-drawdown",
            "higher-gross-edge-per-turnover-bps",
            "lower-annualized-turnover",
            "lexicographically-smaller-team-id",
        ],
    )
    _expect(
        raw,
        ("historical_oos", "ranking", "no_eligible_candidate_means_no_winner"),
        True,
    )
    if dict(_mapping(raw.get("mandates"), "mandates")) != _EXPECTED_MANDATES:
        raise ValueError("V4 team mandates differ from the frozen contract")

    for table_name, keys in (
        ("execution", ("initial_equity_usdt", "max_gross_exposure")),
        ("statistics", ("bootstrap_samples", "bootstrap_block_days")),
    ):
        table = _mapping(raw.get(table_name), table_name)
        for key in keys:
            _finite_number(table.get(key), f"{table_name}.{key}")


def load_config(
    path: str | Path = TOP12_V2_LAYOUT.config_path,
    *,
    root: str | Path = ".",
) -> LoadedV4Config:
    """Load only the canonical regular V4 config and bind its exact bytes."""

    root_path = Path(root).resolve()
    expected = (root_path / TOP12_V2_LAYOUT.config_path).resolve()
    requested = Path(path)
    if not requested.is_absolute():
        requested = root_path / requested
    config_path = requested.resolve()
    if config_path != expected or config_path.is_symlink() or not config_path.is_file():
        raise ValueError("V4 config path must be the canonical regular config file")
    payload = config_path.read_bytes()
    try:
        raw = tomllib.loads(payload.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"invalid Top-12 V2 config: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("Top-12 V2 config root must be a table")
    validate_config(raw)
    return LoadedV4Config(config_path, hashlib.sha256(payload).hexdigest(), raw)


__all__ = ["LoadedV4Config", "TEAM_IDS", "load_config", "validate_config"]
