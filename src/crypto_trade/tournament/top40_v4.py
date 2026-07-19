"""Fail-closed machine contract for the two-round Top-40 V4 tournament."""

from __future__ import annotations

import dataclasses
import hashlib
import math
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT

TEAM_IDS = TOP40_V4_LAYOUT.team_ids

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
        "selection",
        "historical_oos",
        "ensemble",
        "mandates",
    }
)

_EXPECTED_PATHS = {
    "tournament_root": "tournament/top40-v4-r1",
    "reports_root": "reports-top40-v4-r1",
    "team_root": "tournament/top40-v4-r1/teams",
    "research_journal": "tournament/top40-v4-r1/research-journal.jsonl",
    "nomination_registry": "tournament/top40-v4-r1/nomination-registry.json",
    "selection_freeze": "tournament/top40-v4-r1/selection-freeze.json",
    "activation_freeze": "tournament/top40-v4-r1/activation-freeze.json",
    "source_archive_root": "reports-top40-v4-r1/source-archives/sha256",
    "is_reports_root": "reports-top40-v4-r1/is",
    "private_final_root": "tournament/top40-v4-r1/private/historical-oos",
    "final_release_root": "reports-top40-v4-r1/historical-oos",
}

_EXPECTED_FOLDS = (
    ("2020", "2020-02-03T00:00:00Z", "2021-01-01T00:00:00Z"),
    ("2021", "2021-01-01T00:00:00Z", "2022-01-01T00:00:00Z"),
    ("2022", "2022-01-01T00:00:00Z", "2023-01-01T00:00:00Z"),
    ("2023", "2023-01-01T00:00:00Z", "2024-01-01T00:00:00Z"),
    ("2024H1", "2024-01-01T00:00:00Z", "2024-07-01T00:00:00Z"),
)

_EXPECTED_MANDATES = {
    "team-01": "slow-per-coin-time-series-momentum",
    "team-02": "fast-breakout-time-series-momentum",
    "team-03": "volume-confirmed-time-series-momentum",
    "team-04": "market-residual-cross-sectional-momentum",
    "team-05": "short-horizon-liquidity-shock-reversal",
    "team-06": "downside-risk-low-volatility",
    "team-07": "funding-carry-crowding-crash-protection",
    "team-08": "funding-crowding-mean-reversion",
    "team-09": "taker-flow-price-volume-pressure",
    "team-10": "dynamic-cointegration-relative-value",
    "team-11": "utc-weekday-seasonality",
    "team-12": "simple-preregistered-regime-ensemble",
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
    _expect(raw, ("name",), TOP40_V4_LAYOUT.name)
    _expect(raw, ("policy_status",), "active-pending-activation")
    _expect(raw, ("charter_path",), "TOURNAMENT-CHARTER-TOP40-V4-R1.md")
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
        ("data", "manifest_path"): "tournament/top40/data_manifest.json",
        ("data", "manifest_sha256"): (
            "077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3"
        ),
        ("splits", "is", "start"): "2020-02-03T00:00:00Z",
        ("splits", "is", "end_exclusive"): "2024-07-01T00:00:00Z",
        ("splits", "historical_oos", "start"): "2024-07-01T00:00:00Z",
        ("splits", "historical_oos", "end_exclusive"): "2026-07-01T00:00:00Z",
        ("splits", "historical_oos", "globally_pristine"): False,
        ("splits", "historical_oos", "candidate_relative_oos"): True,
        ("splits", "live_forward", "start"): "2026-08-01T00:00:00Z",
        ("splits", "live_forward", "minimum_observation_days"): 365,
        ("universe", "size"): 40,
        ("universe", "reconstitution"): "weekly-monday-00:00-utc",
        ("universe", "liquidity_measure"): "frozen-median-daily-quote-volume",
        ("universe", "trailing_days"): 30,
        ("universe", "minimum_history_days"): 30,
        ("universe", "membership_path"): "data/top40/snapshot-v1/membership.parquet",
        ("universe", "eligibility_mode"): "fail-closed-a6-native-crypto",
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
        ("statistics", "bootstrap_seed"): 20260719,
        ("statistics", "maximum_drawdown_is_positive_magnitude"): True,
        ("research", "strategy_seed"): 20260719,
        ("research", "maximum_accepted_trials_per_team"): 12,
        ("research", "minimum_accepted_trials_before_nomination"): 8,
        ("research", "maximum_mechanism_pivots_per_team"): 1,
        ("research", "accepted_failure_consumes_trial"): True,
        ("research", "journal_before_market_access"): True,
        ("research", "exact_replay_required_for_success"): False,
        ("research", "candidate_metadata_filename"): "candidate.json",
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
        ("research", "minimum_neighborhood_pass_fraction"): 0.70,
        ("research", "minimum_neighborhood_median_double_cost_sharpe"): 0.50,
        ("selection", "floors", "minimum_net_sharpe_inclusive"): 1.0,
        ("selection", "floors", "minimum_annualized_return_inclusive"): 0.05,
        ("selection", "floors", "maximum_drawdown_inclusive"): 0.20,
        ("selection", "floors", "minimum_double_cost_sharpe_inclusive"): 0.75,
        ("selection", "floors", "minimum_triple_cost_sharpe_exclusive"): 0.0,
        ("selection", "floors", "minimum_positive_quarter_fraction_inclusive"): 0.60,
        ("selection", "floors", "minimum_positive_base_folds"): 4,
        ("selection", "floors", "minimum_positive_double_cost_folds"): 4,
        ("selection", "floors", "minimum_worst_fold_sharpe_inclusive"): -0.25,
        ("selection", "floors", "maximum_annualized_turnover_inclusive"): 20.0,
        ("selection", "floors", "minimum_gross_edge_per_turnover_bps_inclusive"): 50.0,
        ("selection", "floors", "maximum_base_cost_share_inclusive"): 0.25,
        ("selection", "floors", "minimum_trial_adjusted_confidence_inclusive"): 0.90,
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
        ): 0.35,
        ("selection", "floors", "maximum_fold_positive_pnl_share_inclusive"): 0.60,
        ("selection", "ranking", "advance_count"): 5,
        ("selection", "ranking", "advance_all_when_fewer"): True,
        ("selection", "ranking", "lower_floors_to_fill_bracket"): False,
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
        ): 0.0,
        (
            "historical_oos",
            "winner_eligibility",
            "minimum_double_cost_annualized_return_exclusive",
        ): 0.0,
        (
            "historical_oos",
            "winner_eligibility",
            "minimum_double_cost_sharpe_exclusive",
        ): 0.0,
        ("historical_oos", "winner_eligibility", "maximum_drawdown_inclusive"): 0.30,
        ("historical_oos", "winner_eligibility", "minimum_positive_quarters"): 4,
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
            "leveraged-token",
            "tokenized-metal",
            "tokenized-commodity",
            "direct-metal",
            "direct-commodity",
            "equity",
            "stock",
            "etf",
            "index",
            "forex",
            "fx",
            "premarket",
            "tradfi",
        ],
    )
    a6_expected = {
        "policy_id": "top40-v2-pure-crypto-usdt-perpetual-v1",
        "policy_sha256": "2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350",
        "audit_module_path": "src/crypto_trade/tournament/pure_crypto_universe_v6.py",
        "audit_module_sha256": "fc93c0f26dcbf6304abe028736693ab2bee7430a56c14a8547defff472008192",
        "audit_dependency_path": "src/crypto_trade/tournament/amendment_integrity_v2.py",
        "audit_dependency_sha256": (
            "e3a4f60aa955ebcf461026527da5b6b28b87e9e7ec057dd2e10a1e884612a8ab"
        ),
        "audit_report_sha256": "b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b",
        "data_manifest_path": "tournament/top40/data_manifest.json",
        "data_manifest_sha256": "077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3",
        "membership_sha256": "f51c9eb207c1da51cc4b9ff6045bb5e914828015b5c9c214f0e2673cd868eb14",
        "contract_metadata_sha256": (
            "0995d50011e73de880358b994031fdf8bb58e75ab8901de2c5601e7abed05243"
        ),
        "exchange_info_sha256": "aab4219452e61cfa5e135518ed182c98fd7e527d13bc240e891bb6b550deeb64",
        "expected_contract_metadata_symbols": 667,
        "expected_distinct_membership_symbols": 321,
        "expected_membership_rows": 12866,
        "expected_violations": 0,
        "expected_audit_status": "passed",
        "required_before_and_after_every_result_command": True,
    }
    if dict(_mapping(_mapping(raw["universe"], "universe")["a6_authority"], "a6")) != a6_expected:
        raise ValueError("V4 A6 pure-crypto authority differs from the frozen contract")

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
    path: str | Path = TOP40_V4_LAYOUT.config_path,
    *,
    root: str | Path = ".",
) -> LoadedV4Config:
    """Load only the canonical regular V4 config and bind its exact bytes."""

    root_path = Path(root).resolve()
    expected = (root_path / TOP40_V4_LAYOUT.config_path).resolve()
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
        raise ValueError(f"invalid Top-40 V4 config: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("Top-40 V4 config root must be a table")
    validate_config(raw)
    return LoadedV4Config(config_path, hashlib.sha256(payload).hexdigest(), raw)


__all__ = ["LoadedV4Config", "TEAM_IDS", "load_config", "validate_config"]
