from __future__ import annotations

import dataclasses
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.evidence_v2 import (
    _BAR_RETURN_COLUMNS,
    _EVENT_COLUMNS,
    build_qualification_evidence,
    trial_adjusted_probability_positive,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.metrics import (
    aggregate_daily_returns,
    compute_regime_sharpes,
    compute_window_metrics,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.tournament.qualification import assess_development, assess_private
from crypto_trade.tournament.top40_v2 import load_config

REPOSITORY = Path(__file__).parents[2]
TEAM_ID = "team-01"
CANDIDATE_ID = "candidate-1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_daily(path: Path, daily: pd.Series) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {"date": daily.index.strftime("%Y-%m-%d"), "net_return": daily.to_numpy()}
    ).to_csv(path, index=False)


def _bar_frame(index: pd.DatetimeIndex, net_returns: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame(index=index)
    frame["price_pnl"] = net_returns
    frame["long_price_pnl"] = net_returns * 0.6
    frame["short_price_pnl"] = net_returns * 0.4
    frame["funding_pnl"] = 0.0
    frame["long_funding_pnl"] = 0.0
    frame["short_funding_pnl"] = 0.0
    frame["forced_exit_boundary_funding_pnl"] = 0.0
    frame["fees"] = 0.0
    frame["slippage"] = 0.0
    frame["net_return"] = net_returns
    frame["turnover"] = 0.0
    frame["gross_exposure"] = 0.1
    frame["net_exposure"] = 0.0
    frame["long_exposure"] = 0.05
    frame["short_exposure"] = 0.05
    frame["requested_notional"] = 0.0
    frame["unfilled_notional"] = 0.0
    frame["forced_exit_requested_notional"] = 0.0
    frame["forced_exit_unfilled_notional"] = 0.0
    frame["forced_exit_turnover"] = 0.0
    frame["conservative_settlement_notional"] = 0.0
    frame["conservative_settlement_loss"] = 0.0
    frame["terminal_unresolved_notional"] = 0.0
    frame["risk_reduction_turnover"] = 0.0
    frame["risk_cap_breach"] = False
    frame["risk_cap_required_scale"] = 1.0
    frame["equity"] = 100_000.0 * np.cumprod(1.0 + net_returns)
    frame.index.name = "timestamp"
    return frame.loc[:, _BAR_RETURN_COLUMNS[1:]]


def _write_bar(path: Path, frame: pd.DataFrame) -> None:
    output = frame.reset_index()
    assert list(output.columns) == list(_BAR_RETURN_COLUMNS)
    output.to_csv(path, index=False)


def _events(first_timestamp: pd.Timestamp) -> pd.DataFrame:
    rows = []
    for symbol, quantity in (("BTCUSDT", 50.0), ("ETHUSDT", -50.0)):
        rows.append(
            {
                "timestamp": first_timestamp,
                "symbol": symbol,
                "event_type": "trade",
                "phase": "rebalance",
                "quantity": quantity,
                "price": 100.0,
                "notional": quantity * 100.0,
                "funding_rate": 0.0,
                "cashflow": 0.0,
                "fee": 0.0,
                "slippage": 0.0,
                "reason": None,
                "policy_id": None,
            }
        )
    return pd.DataFrame(rows, columns=_EVENT_COLUMNS)


def _regime_series(index: pd.DatetimeIndex) -> pd.Series:
    labels = np.asarray(("bull", "bear", "chop", "stress"), dtype=object)
    return pd.Series(labels[np.arange(len(index)) % len(labels)], index=index, name="regime")


def _window(config, stage: str) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    start = pd.Timestamp(config.raw["splits"]["visible_development_start"], tz="UTC")
    if stage == "development":
        score_start = start
        score_end = pd.Timestamp(
            config.raw["splits"]["visible_development_end_inclusive"], tz="UTC"
        )
    else:
        score_start = pd.Timestamp(config.raw["splits"]["private_qualifier_start"], tz="UTC")
        score_end = pd.Timestamp(
            config.raw["splits"]["private_qualifier_end_inclusive"], tz="UTC"
        )
    return start, score_start, score_end


def _artifact_root(stage: str) -> str:
    if stage == "development":
        return f"reports-top40-v2/{TEAM_ID}/development"
    return f"tournament/top40-v2/private/artifacts/{TEAM_ID}"


def _fixture(root: Path, stage: str = "development") -> dict[str, object]:
    config_target = root / TOP40_V2_LAYOUT.config_path
    config_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPOSITORY / TOP40_V2_LAYOUT.config_path, config_target)
    config = load_config(config_target)
    team_root = root / TOP40_V2_LAYOUT.team_root(TEAM_ID)
    team_root.mkdir(parents=True)
    strategy = team_root / "strategy.py"
    strategy.write_text("def decide(context):\n    return {}\n", encoding="utf-8")
    risk = json.loads(
        (REPOSITORY / "tournament/top40-v2/templates/risk-policy.json").read_text(
            encoding="utf-8"
        )
    )
    risk["policy_id"] = "team-01-base"
    _write_json(team_root / "risk_policy.json", risk)

    replay_start, score_start, score_end = _window(config, stage)
    end_exclusive = score_end + pd.Timedelta(days=1)
    bar_index = pd.date_range(replay_start, end_exclusive, freq="8h", inclusive="left")
    ordinal = np.arange(len(bar_index), dtype=float)
    base_values = 0.00025 + 0.00055 * np.sin(ordinal / 7.0)
    double_values = base_values * 0.8 - 0.00001
    base = _bar_frame(bar_index, base_values)
    doubled = _bar_frame(bar_index, double_values)
    base_daily = aggregate_daily_returns(base["net_return"])
    double_daily = aggregate_daily_returns(doubled["net_return"])

    output_relative = _artifact_root(stage)
    output = root / output_relative
    output.mkdir(parents=True)
    targets = pd.DataFrame(
        {
            "timestamp": bar_index,
            REBALANCE_INSTRUCTION_COLUMN: np.ones(len(bar_index), dtype=bool),
            "BTCUSDT": np.full(len(bar_index), 0.05),
            "ETHUSDT": np.full(len(bar_index), -0.05),
        }
    )
    targets.to_parquet(output / "targets.parquet", index=False)
    event_frame = _events(bar_index[0])
    event_frame.to_parquet(output / "events.parquet", index=False)
    positions = pd.DataFrame(
        {
            "timestamp": bar_index,
            "BTCUSDT": np.full(len(bar_index), 0.05),
            "ETHUSDT": np.full(len(bar_index), -0.05),
        }
    )
    positions.to_parquet(output / "positions.parquet", index=False)
    _write_bar(output / "bar_returns.csv", base)
    _write_bar(output / "double_cost_bar_returns.csv", doubled)
    _write_daily(output / "daily_returns.csv", base_daily)
    _write_daily(output / "double_cost_daily_returns.csv", double_daily)
    event_frame.to_csv(output / "trades.csv", index=False)

    full_index = pd.date_range(
        config.raw["splits"]["visible_development_start"],
        config.raw["splits"]["final_oos_end_inclusive"],
        freq="1D",
        tz="UTC",
    )
    common = root / "reports-top40/common"
    common.mkdir(parents=True)
    btc_path = common / "btc_daily_returns.csv"
    regimes_path = common / "btc_regimes.csv"
    pd.DataFrame(
        {
            "date": full_index.strftime("%Y-%m-%d"),
            "btc_return": 0.001 * np.sin(np.arange(len(full_index)) / 13.0),
        }
    ).to_csv(btc_path, index=False)
    regimes = _regime_series(full_index)
    pd.DataFrame(
        {"date": full_index.strftime("%Y-%m-%d"), "regime": regimes.to_numpy()}
    ).to_csv(regimes_path, index=False)
    manifest_path = root / "tournament/top40/data_manifest.json"
    _write_json(
        manifest_path,
        {
            "schema_version": 1,
            "files": [
                {
                    "name": "btc_daily_returns",
                    "path": "reports-top40/common/btc_daily_returns.csv",
                    "sha256": _sha256(btc_path),
                },
                {
                    "name": "btc_regimes",
                    "path": "reports-top40/common/btc_regimes.csv",
                    "sha256": _sha256(regimes_path),
                },
            ],
        },
    )

    artifacts = {
        "targets": f"{output_relative}/targets.parquet",
        "events": f"{output_relative}/events.parquet",
        "positions": f"{output_relative}/positions.parquet",
        "evaluator_returns": f"{output_relative}/bar_returns.csv",
        "double_cost_evaluator_returns": f"{output_relative}/double_cost_bar_returns.csv",
        "daily_returns": f"{output_relative}/daily_returns.csv",
        "double_cost_daily_returns": f"{output_relative}/double_cost_daily_returns.csv",
        "trades": f"{output_relative}/trades.csv",
    }
    scored = base_daily.loc[score_start:score_end]
    scored_double = double_daily.loc[score_start:score_end]
    metrics = compute_window_metrics(scored)
    regime_sharpes = compute_regime_sharpes(scored, regimes.reindex(scored.index))
    record = {
        "stage": stage,
        "team_id": TEAM_ID,
        "entrypoint": f"{TOP40_V2_LAYOUT.team_root(TEAM_ID)}/strategy.py",
        "seeds": [config.raw["research_budget"]["strategy_seed"]],
        "data_manifest_sha256": _sha256(manifest_path),
        "config_sha256": config.sha256,
        "strategy_sha256": _sha256(strategy),
        "scored_window": {
            "start": score_start.date().isoformat(),
            "end": score_end.date().isoformat(),
            "metrics": dataclasses.asdict(metrics),
        },
        "double_cost_sharpe": compute_window_metrics(scored_double).net_sharpe,
        "regime_sharpe": dict(regime_sharpes),
        "confidence_intervals": {
            "net_sharpe_95": [-1.0, 1.0],
            "double_cost_sharpe_95": [-1.0, 1.0],
        },
        "artifacts": artifacts,
    }
    result: dict[str, object] = {
        "config": config,
        "record": record,
        "base_daily": base_daily,
        "output": output,
    }
    if stage == "development":
        neighbor_root = root / f"reports-top40-v2/{TEAM_ID}/parameter-neighborhood"
        neighbor_root.mkdir(parents=True)
        neighbors = []
        for index, multiplier in enumerate((0.8, 0.9, 1.1), start=1):
            path = neighbor_root / f"neighbor-{index}.csv"
            parameter_path = neighbor_root / f"neighbor-{index}.parameters.json"
            _write_daily(path, base_daily * multiplier)
            _write_json(parameter_path, {"lookback": 10 * index})
            relative = path.relative_to(root).as_posix()
            neighbors.append(
                {
                    "neighbor_id": f"neighbor-{index}",
                    "parameter_artifact_path": parameter_path.relative_to(root).as_posix(),
                    "parameter_artifact_sha256": _sha256(parameter_path),
                    "daily_returns_path": relative,
                    "daily_returns_sha256": _sha256(path),
                }
            )
        neighborhood_path = neighbor_root / "manifest.json"
        _write_json(
            neighborhood_path,
            {
                "schema_version": 1,
                "team_id": TEAM_ID,
                "candidate_id": CANDIDATE_ID,
                "neighbors": neighbors,
            },
        )

        scored_indices = np.array_split(np.arange(len(scored)), 6)
        folds = []
        for index, indices in enumerate(scored_indices, start=1):
            fold_id = f"fold-{index}"
            model = team_root / f"{fold_id}.model"
            model.write_bytes(f"model {index}".encode())
            values = scored.iloc[indices]
            folds.append(
                {
                    "fold_id": fold_id,
                    "training_end_inclusive": (
                        values.index[0] - pd.Timedelta(days=1)
                    ).date().isoformat(),
                    "test_start": values.index[0].date().isoformat(),
                    "test_end_inclusive": values.index[-1].date().isoformat(),
                    "model_artifact_path": model.relative_to(root).as_posix(),
                    "model_artifact_sha256": _sha256(model),
                }
            )
        walk_path = root / f"reports-top40-v2/{TEAM_ID}/walk-forward-manifest.json"
        _write_json(
            walk_path,
            {
                "schema_version": 1,
                "team_id": TEAM_ID,
                "candidate_id": CANDIDATE_ID,
                "evidence_class": "declared-retrained-out-of-fold",
                "stitched_daily_returns_sha256": _sha256(output / "daily_returns.csv"),
                "folds": folds,
            },
        )
        result["neighborhood"] = neighborhood_path
        result["walk"] = walk_path
    return result


def _build(root: Path, fixture: dict[str, object], **overrides):
    arguments = {
        "candidate_id": CANDIDATE_ID,
        "trial_count": 5,
    }
    if "neighborhood" in fixture:
        arguments["parameter_neighborhood_manifest_path"] = fixture["neighborhood"]
        arguments["walk_forward_manifest_path"] = fixture["walk"]
    arguments.update(overrides)
    return build_qualification_evidence(root, fixture["record"], **arguments)


def test_development_builder_derives_complete_gate_schema_and_provenance(tmp_path):
    fixture = _fixture(tmp_path)
    built = _build(tmp_path, fixture)
    evidence = built.evidence
    config = fixture["config"]

    assessment = assess_development(
        evidence, config.qualification_thresholds, evidence_sha256="a" * 64
    )
    assert set(evidence) == {
        "schema_version",
        "stage",
        "team_id",
        "candidate_id",
        "strategy_sha256",
        "risk_policy_sha256",
        "config_sha256",
        "trial_count",
        "aggregate",
        "folds",
        "regimes",
        "roles",
        "sleeves",
        "stability",
    }
    assert len(evidence["folds"]) == 6
    assert evidence["sleeves"]["long"]["executed_notional_usdt"] == 5_000.0
    assert evidence["sleeves"]["short"]["executed_notional_usdt"] == 5_000.0
    assert 0.0 <= evidence["aggregate"]["trial_adjusted_probability_positive"] <= 1.0
    assert built.provenance["walk_forward"]["qualification_ready_oof"] is True
    assert "fixed chronological segmentation" in built.provenance["walk_forward"][
        "statement"
    ].lower()
    assert assessment.passed


def test_private_builder_emits_only_private_schema_fields(tmp_path):
    fixture = _fixture(tmp_path, stage="private")
    built = _build(tmp_path, fixture)
    config = fixture["config"]
    assessment = assess_private(
        built.evidence, config.qualification_thresholds, evidence_sha256="b" * 64
    )

    assert set(built.evidence) == {
        "schema_version",
        "stage",
        "team_id",
        "candidate_id",
        "strategy_sha256",
        "risk_policy_sha256",
        "config_sha256",
        "trial_count",
        "aggregate",
    }
    assert assessment.passed
    assert "walk_forward" not in built.provenance


def test_development_requires_walk_forward_declaration_by_default(tmp_path):
    fixture = _fixture(tmp_path)
    with pytest.raises(ValueError, match="declared walk-forward manifest"):
        _build(tmp_path, fixture, walk_forward_manifest_path=None)

    built = _build(
        tmp_path,
        fixture,
        walk_forward_manifest_path=None,
        allow_evaluation_folds=True,
    )
    assert built.provenance["walk_forward"]["evidence_class"] == "evaluation-folds-only"
    assert built.provenance["walk_forward"]["qualification_ready_oof"] is False


def test_tampered_daily_return_is_rejected_by_bar_reconciliation(tmp_path):
    fixture = _fixture(tmp_path)
    path = fixture["output"] / "daily_returns.csv"
    frame = pd.read_csv(path)
    frame.loc[100, "net_return"] += 0.01
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="do not reconcile"):
        _build(tmp_path, fixture)


def test_candidate_strategy_hash_mismatch_fails_closed(tmp_path):
    fixture = _fixture(tmp_path)
    fixture["record"]["strategy_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="candidate identity or input hashes"):
        _build(tmp_path, fixture)


def test_neighbor_manifest_hash_mismatch_fails_closed(tmp_path):
    fixture = _fixture(tmp_path)
    manifest = json.loads(fixture["neighborhood"].read_text(encoding="utf-8"))
    manifest["neighbors"][0]["daily_returns_sha256"] = "0" * 64
    _write_json(fixture["neighborhood"], manifest)

    with pytest.raises(ValueError, match="neighbor hash differs"):
        _build(tmp_path, fixture)


def test_noncanonical_bar_columns_fail_closed(tmp_path):
    fixture = _fixture(tmp_path)
    path = fixture["output"] / "bar_returns.csv"
    frame = pd.read_csv(path).drop(columns="long_exposure")
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="noncanonical return columns"):
        _build(tmp_path, fixture)


def test_symlinked_canonical_artifact_fails_closed(tmp_path):
    fixture = _fixture(tmp_path)
    path = fixture["output"] / "daily_returns.csv"
    target = fixture["output"] / "daily_returns.real.csv"
    path.rename(target)
    path.symlink_to(target.name)

    with pytest.raises(ValueError, match="symlink component"):
        _build(tmp_path, fixture)


def test_trial_adjustment_is_documented_and_penalizes_more_trials():
    index = pd.date_range("2020-01-01", periods=400, freq="1D", tz="UTC")
    values = pd.Series(
        0.0005 + 0.01 * np.sin(np.arange(len(index)) / 5.0), index=index
    )
    one, one_provenance = trial_adjusted_probability_positive(values, 1)
    many, many_provenance = trial_adjusted_probability_positive(values, 80)

    assert 0.0 <= many < one <= 1.0
    assert one_provenance["method"] == "top40-v2-dsr-v1"
    assert "Euler-Mascheroni" in many_provenance["formula"]
