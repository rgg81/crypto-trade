"""Tests for CUP-20 result packets, manifests and the single atomic release.

This module's contract is atomicity: every packet and the manifest are built privately, then one
rename makes the whole bundle public -- never a partial one. Two things are load-bearing and
covered explicitly below, not just incidentally: ``json.dumps(..., allow_nan=False)`` in both
write paths (a non-finite metric must raise, never silently emit the non-standard "Infinity"
token into a hash-chained release artifact), and ``atomic_release``'s refusal to ever overwrite
an existing release (publication happens once).

Each test group states what mutation it is designed to catch, per the standing instruction that a
test asserting a file exists proves little next to one that proves a digest tracks real content.
"""

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.metrics import (
    WindowMetrics,
    daily_returns,
    fold_sharpes,
    is_folds,
    window_metrics,
)
from crypto_trade.cup20.report import atomic_release, build_packet, write_manifest
from crypto_trade.cup20.runner import (
    STAGE_EXECUTED,
    STAGE_REQUESTED,
    CandidateRun,
    exposure_cap_trim,
)
from crypto_trade.tournament.engine_v2 import EvaluationResult, EvaluatorConfig
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

IS_START = pd.Timestamp("2020-08-01T00:00:00Z")
IS_END = pd.Timestamp("2024-08-01T00:00:00Z")

# The packet discloses what the section 4 caps did, so these fixtures carry a real trim rather
# than an empty one: ``_REQUESTED`` asks for 0.60/-0.10 against a 0.20 per-symbol cap at its first
# boundary and sits inside every cap at its second, so the summary that reaches ``summary.json``
# has both a trimmed and an untrimmed boundary to count.
_CAP_CONFIG = EvaluatorConfig(
    max_gross_exposure=1.0, max_abs_net_exposure=1.0, max_symbol_exposure=0.20
)
_REQUESTED = pd.DataFrame(
    {
        "AUSDT": [0.60, 0.10],
        "BUSDT": [-0.10, -0.10],
        REBALANCE_INSTRUCTION_COLUMN: [True, True],
    },
    index=pd.date_range("2020-08-01T00:00:00Z", periods=2, freq="8h"),
)
_REQUESTED_TRIM = exposure_cap_trim(_REQUESTED, _CAP_CONFIG, stage=STAGE_REQUESTED)
_EXECUTED_TRIM = exposure_cap_trim(_REQUESTED, _CAP_CONFIG, stage=STAGE_EXECUTED)


def _run():
    index = pd.date_range("2020-08-01T00:00:00Z", periods=4400, freq="8h", name="timestamp")
    rng = np.random.default_rng(1)
    values = rng.normal(0.0002, 0.003, len(index))
    frame = pd.DataFrame(
        {
            "net_return": values,
            "price_pnl": values,
            "long_price_pnl": values,
            "short_price_pnl": np.zeros(len(index)),
            "funding_pnl": np.zeros(len(index)),
            "long_funding_pnl": np.zeros(len(index)),
            "short_funding_pnl": np.zeros(len(index)),
            "fees": np.zeros(len(index)),
            "slippage": np.zeros(len(index)),
            "turnover": np.full(len(index), 0.01),
        },
        index=index,
    )
    events = pd.DataFrame({"event_type": ["trade"] * 600, "notional": [10.0] * 600})
    result = EvaluationResult(frame, pd.DataFrame(), events)
    return CandidateRun(
        requested_targets=_REQUESTED,
        targets=pd.DataFrame(),
        scaled_targets=pd.DataFrame(),
        requested_trim=_REQUESTED_TRIM,
        executed_trim=_EXECUTED_TRIM,
        risk_scalars=pd.Series(dtype=float),
        unscaled=result,
        results={1: result, 2: result, 3: result},
    )


def _result(net, *, turnover=0.01, events=None):
    """A second, independent EvaluationResult builder (mirrors test_metrics.py's ``_result``)
    used only by this file's own additions -- ``_run()`` above stays byte-identical to the brief.
    """
    index = pd.date_range("2020-08-01T00:00:00Z", periods=len(net), freq="8h", name="timestamp")
    values = np.asarray(net, dtype=float)
    frame = pd.DataFrame(
        {
            "net_return": values,
            "price_pnl": values,
            "long_price_pnl": values,
            "short_price_pnl": np.zeros(len(net)),
            "funding_pnl": np.zeros(len(net)),
            "long_funding_pnl": np.zeros(len(net)),
            "short_funding_pnl": np.zeros(len(net)),
            "fees": np.zeros(len(net)),
            "slippage": np.zeros(len(net)),
            "turnover": np.full(len(net), turnover, dtype=float),
        },
        index=index,
    )
    event_frame = (
        pd.DataFrame(events)
        if events is not None
        else pd.DataFrame({"event_type": [], "notional": []})
    )
    return EvaluationResult(returns=frame, positions=pd.DataFrame(), events=event_frame)


def _candidate_run(results, *, risk_scalars=None):
    any_result = results[next(iter(results))] if results else _result([0.001] * 10)
    return CandidateRun(
        requested_targets=_REQUESTED,
        targets=pd.DataFrame(),
        scaled_targets=pd.DataFrame(),
        requested_trim=_REQUESTED_TRIM,
        executed_trim=_EXECUTED_TRIM,
        risk_scalars=pd.Series(dtype=float) if risk_scalars is None else risk_scalars,
        unscaled=any_result,
        results=results,
    )


def _three_level_run():
    """Three genuinely different EvaluationResults, one per cost multiplier.

    Needed because ``_run()`` above (kept verbatim from the brief) reuses one identical
    EvaluationResult for all three multipliers. Confirmed empirically (see the report) that this
    makes any test built only on ``_run()`` unable to catch a cross-multiplier wiring bug: with
    identical underlying data, ``cost_levels["1"]`` silently computed from ``results[3]``, or an
    artifact digest hashing the wrong file, produces output byte-identical to the correct
    behaviour. Distinct series per level closes that gap.
    """
    result_1 = _result([0.010, -0.003] * 100)
    result_2 = _result([-0.020, 0.004] * 100)
    result_3 = _result([0.001, 0.002, -0.006] * 67)
    run = _candidate_run({1: result_1, 2: result_2, 3: result_3})
    return run, (result_1, result_2, result_3)


# ---------------------------------------------------------------------------------------------
# build_packet -- given tests, transcribed verbatim
# ---------------------------------------------------------------------------------------------


def test_packet_contains_every_cost_level_and_fold(tmp_path):
    folds = is_folds(pd.Timestamp("2020-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))
    packet = build_packet(
        _run(),
        team_id="team-01",
        candidate_id="c1",
        folds=folds,
        identity={"strategy_sha256": "a" * 64},
        output_dir=tmp_path,
    )
    assert set(packet["cost_levels"]) == {"1", "2", "3"}
    assert set(packet["fold_sharpes"]) == {"F1", "F2", "F3", "F4"}
    assert packet["identity"]["strategy_sha256"] == "a" * 64
    assert (tmp_path / "daily_returns.csv").exists()


def test_packet_records_artifact_digests(tmp_path):
    folds = is_folds(pd.Timestamp("2020-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))
    packet = build_packet(
        _run(),
        team_id="team-01",
        candidate_id="c1",
        folds=folds,
        identity={},
        output_dir=tmp_path,
    )
    assert len(packet["artifact_sha256"]["daily_returns"]) == 64


# ---------------------------------------------------------------------------------------------
# build_packet -- additions. Each targets a mutation the two tests above cannot catch: a digest
# that is merely 64 hex characters (any garbage of the right length passes that check), a
# cost-level or fold-sharpe value silently wrong while its *keys* are right, a summary.json that
# drifts from the returned dict, a single-cost-level run, an empty result set, and the
# allow_nan=False backstop.
# ---------------------------------------------------------------------------------------------


def test_artifact_digests_are_specific_to_each_files_own_content(tmp_path):
    """Directly answers the task's specific check: the recorded digest is of the file actually
    written (not a shared, aggregate, or mismatched one), and tampering with one artifact is
    detectable without disturbing the others' already-recorded digests.

    Uses ``_three_level_run()``, not ``_run()``: with ``_run()``'s identical-object fixture, the
    three CSVs are byte-identical, so a mutation that hashes the *wrong* file (e.g. always
    ``daily_returns.csv``) produces a digest that still matches by coincidence. Confirmed
    empirically before writing this version (see the report) -- distinct per-level content is
    required to make "hashed the wrong file" and "wrote the wrong content" both detectable.
    """
    run, (result_1, result_2, result_3) = _three_level_run()
    folds = is_folds(IS_START, IS_END)
    packet = build_packet(
        run, team_id="team-01", candidate_id="c1", folds=folds, identity={}, output_dir=tmp_path
    )

    digests = packet["artifact_sha256"]
    paths = {
        "daily_returns": tmp_path / "daily_returns.csv",
        "daily_returns_2x": tmp_path / "daily_returns_2x.csv",
        "daily_returns_3x": tmp_path / "daily_returns_3x.csv",
    }
    for name, path in paths.items():
        assert digests[name] == hashlib.sha256(path.read_bytes()).hexdigest()
    # The three underlying series differ, so a correctly wired implementation must produce three
    # distinct digests -- this is what actually rules out "hashed the wrong file".
    assert len(set(digests.values())) == 3

    untouched_before = digests["daily_returns_2x"]
    paths["daily_returns"].write_bytes(paths["daily_returns"].read_bytes() + b"\n# tampered")
    assert (
        hashlib.sha256(paths["daily_returns"].read_bytes()).hexdigest() != digests["daily_returns"]
    )
    # Tampering with one artifact must not retroactively change another's recorded digest --
    # they are independent per-file hashes, not derived from one another or from directory state.
    assert hashlib.sha256(paths["daily_returns_2x"].read_bytes()).hexdigest() == untouched_before


def test_daily_returns_csv_content_matches_the_computed_series(tmp_path):
    run = _run()
    folds = is_folds(IS_START, IS_END)
    build_packet(
        run, team_id="team-01", candidate_id="c1", folds=folds, identity={}, output_dir=tmp_path
    )
    written = pd.read_csv(tmp_path / "daily_returns.csv", index_col=0)["daily_return"]
    expected = daily_returns(run.results[1])
    np.testing.assert_allclose(written.to_numpy(), expected.to_numpy())


def test_packet_wires_each_cost_level_to_its_own_result(tmp_path):
    """Same rationale as the artifact-digest test above: needs distinct per-level data, not
    ``_run()``'s shared object, to actually distinguish a cross-multiplier mix-up from correct
    wiring (confirmed by mutation -- see the report)."""
    run, (result_1, result_2, result_3) = _three_level_run()
    folds = is_folds(IS_START, IS_END)
    packet = build_packet(
        run, team_id="team-01", candidate_id="c1", folds=folds, identity={}, output_dir=tmp_path
    )

    assert packet["cost_levels"]["1"] == window_metrics(result_1).as_dict()
    assert packet["cost_levels"]["2"] == window_metrics(result_2).as_dict()
    assert packet["cost_levels"]["3"] == window_metrics(result_3).as_dict()
    # Non-vacuous: the three levels' metrics actually differ, so a cross-level swap could not
    # hide behind coincidentally-equal data the way it would under _run()'s shared object.
    assert len({packet["cost_levels"][k]["net_sharpe"] for k in ("1", "2", "3")}) == 3

    # fold_sharpes is documented to use the 2x (double-cost) book, not whichever level sorts
    # first and not level 1.
    assert packet["fold_sharpes"] == fold_sharpes(result_2, folds)
    assert packet["fold_sharpes"] != fold_sharpes(result_1, folds)
    assert packet["fold_sharpes"] != fold_sharpes(result_3, folds)


def test_packet_fold_sharpes_falls_back_to_the_minimum_level_when_two_is_absent(tmp_path):
    result_1 = _result([0.010, -0.020] * 100)
    result_3 = _result([-0.050, 0.010] * 100)
    run = _candidate_run({1: result_1, 3: result_3})
    folds = is_folds(IS_START, IS_END)
    packet = build_packet(
        run, team_id="team-01", candidate_id="c1", folds=folds, identity={}, output_dir=tmp_path
    )
    # min({1, 3}) == 1: proves the fallback specifically selects the minimum key, not merely "the
    # only other" key or some other selection (a max()-based fallback would pick 3 instead).
    assert packet["fold_sharpes"] == fold_sharpes(result_1, folds)
    assert packet["fold_sharpes"] != fold_sharpes(result_3, folds)


def test_packet_risk_scalar_summary_matches_independent_computation(tmp_path):
    scalars = pd.Series(
        [0.2, 0.5, 1.0, 3.0],
        index=pd.date_range("2020-08-01T00:00:00Z", periods=4, freq="8h"),
    )
    result = _result([0.001] * 200)
    run = _candidate_run({1: result, 2: result, 3: result}, risk_scalars=scalars)
    folds = is_folds(IS_START, IS_END)
    packet = build_packet(
        run, team_id="team-01", candidate_id="c1", folds=folds, identity={}, output_dir=tmp_path
    )
    assert packet["risk_scalar_summary"] == {
        "count": 4,
        "median": 0.75,
        "minimum": 0.2,
        "maximum": 3.0,
    }


def test_packet_discloses_what_the_exposure_caps_did_to_the_book(tmp_path):
    """Charter section 4's caps reduce rather than reject, so a candidate can be executed at
    weights it did not ask for. The packet is where a team finds that out.

    Mutation this catches: dropping the ``exposure_caps`` block, or reporting only one of the two
    applications (the requested book and the executed book are trimmed at different points and can
    differ, so a single number would hide half of it).
    """
    run = _run()
    folds = is_folds(IS_START, IS_END)
    packet = build_packet(
        run, team_id="team-01", candidate_id="c1", folds=folds, identity={}, output_dir=tmp_path
    )
    assert set(packet["exposure_caps"]) == {"requested", "executed"}
    requested = packet["exposure_caps"]["requested"]
    assert requested["stage"] == STAGE_REQUESTED
    assert packet["exposure_caps"]["executed"]["stage"] == STAGE_EXECUTED
    # The fixture asks 0.60 on one name against a 0.20 cap at its first boundary and sits inside
    # every cap at its second, so this is a real count and not a constant.
    assert requested["boundaries"] == 2
    assert requested["trimmed_boundaries"] == 1
    assert requested["trimmed_fraction"] == pytest.approx(0.5)
    assert requested["minimum_scale"] == pytest.approx(0.20 / 0.60)
    assert requested["binding_cap_counts"] == {"gross": 0, "net": 0, "symbol": 1}
    # And it survives the round trip through ``allow_nan=False`` serialisation.
    assert (
        json.loads((tmp_path / "summary.json").read_text())["exposure_caps"]
        == (packet["exposure_caps"])
    )


def test_summary_json_on_disk_matches_the_returned_packet_exactly(tmp_path):
    run = _run()
    folds = is_folds(IS_START, IS_END)
    packet = build_packet(
        run, team_id="team-01", candidate_id="c1", folds=folds, identity={}, output_dir=tmp_path
    )
    on_disk = json.loads((tmp_path / "summary.json").read_text())
    assert on_disk == packet


def test_packet_with_a_single_cost_level_uses_it_as_the_fold_sharpes_source(tmp_path):
    result = _result([0.001] * 200)
    run = _candidate_run({1: result})
    folds = is_folds(IS_START, IS_END)
    packet = build_packet(
        run, team_id="team-01", candidate_id="c1", folds=folds, identity={}, output_dir=tmp_path
    )
    assert set(packet["cost_levels"]) == {"1"}
    assert set(packet["artifact_sha256"]) == {"daily_returns"}
    # 2 is not in run.results, so fold_sharpes must fall back to the only book present (result),
    # not raise and not silently use an unrelated placeholder.
    assert packet["fold_sharpes"] == fold_sharpes(result, folds)


def test_packet_raises_clearly_on_an_empty_result_set_and_writes_nothing(tmp_path):
    run = _candidate_run({})
    output_dir = tmp_path / "team-01"  # does not exist yet -- proves the guard runs before mkdir
    folds = is_folds(IS_START, IS_END)
    with pytest.raises(ValueError, match="empty"):
        build_packet(
            run,
            team_id="team-01",
            candidate_id="c1",
            folds=folds,
            identity={},
            output_dir=output_dir,
        )
    assert not output_dir.exists()


def test_packet_raises_rather_than_serialising_a_non_finite_metric(tmp_path, monkeypatch):
    """The allow_nan=False backstop. Task 6 guarantees window_metrics never returns a non-finite
    value in practice, so this must reach the failure by monkeypatching window_metrics itself --
    testing report.py's own contract in isolation rather than trying to defeat metrics.py's."""
    bad_metrics = WindowMetrics(
        net_sharpe=float("nan"),
        annualized_return=0.0,
        annualized_volatility=0.06,
        max_drawdown=0.1,
        calmar=1.0,
        positive_quarter_fraction=0.5,
        positive_quarter_count=4,
        annualized_turnover=1.0,
        gross_edge_bps_per_turnover=1.0,
        cost_share_of_positive_gross=0.1,
        top5_day_share=0.1,
        long_gross_pnl=1.0,
        short_gross_pnl=1.0,
        trade_count=1,
    )
    monkeypatch.setattr("crypto_trade.cup20.report.window_metrics", lambda result: bad_metrics)

    folds = is_folds(IS_START, IS_END)
    with pytest.raises(ValueError, match="not JSON compliant"):
        build_packet(
            _run(),
            team_id="team-01",
            candidate_id="c1",
            folds=folds,
            identity={},
            output_dir=tmp_path,
        )
    # Honest accounting of the partial state this leaves (see report for the full analysis): the
    # per-level CSVs do not depend on WindowMetrics, so they are already written by the time the
    # final json.dumps raises. summary.json is not -- there is no half-written summary on disk.
    assert (tmp_path / "daily_returns.csv").exists()
    assert not (tmp_path / "summary.json").exists()


# ---------------------------------------------------------------------------------------------
# write_manifest -- given test, transcribed verbatim
# ---------------------------------------------------------------------------------------------


def test_manifest_digest_changes_with_packet_content(tmp_path):
    first = write_manifest([{"team_id": "team-01", "score": 1.0}], path=tmp_path / "a.json")
    second = write_manifest([{"team_id": "team-01", "score": 2.0}], path=tmp_path / "b.json")
    assert first != second


# ---------------------------------------------------------------------------------------------
# write_manifest -- additions. The given test only proves "differs when content differs"; a
# constant-returning or content-ignoring digest could still pass it if the two calls happened to
# differ some other way. The tests below prove the other, load-bearing half -- "identical when
# content is identical" -- and that the digest is genuinely of the bytes on disk.
# ---------------------------------------------------------------------------------------------


def test_manifest_digest_is_identical_for_identical_content_in_different_key_order(tmp_path):
    packet_a = {"team_id": "team-01", "score": 1.0, "candidate_id": "c1"}
    packet_b = {"candidate_id": "c1", "score": 1.0, "team_id": "team-01"}
    first = write_manifest([packet_a], path=tmp_path / "a.json")
    second = write_manifest([packet_b], path=tmp_path / "b.json")
    # Only passes if sort_keys=True is actually doing its job -- a dict-insertion-order-dependent
    # serialisation would diverge here even though the two packets are the same content.
    assert first == second


def test_manifest_digest_equals_sha256_of_the_bytes_it_wrote(tmp_path):
    path = tmp_path / "manifest.json"
    digest = write_manifest([{"team_id": "team-01", "score": 1.0}], path=path)
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()


def test_write_manifest_creates_missing_parent_directories(tmp_path):
    path = tmp_path / "nested" / "deep" / "manifest.json"
    write_manifest([{"team_id": "team-01"}], path=path)
    assert path.exists()


def test_write_manifest_with_an_empty_packet_list(tmp_path):
    path = tmp_path / "manifest.json"
    digest = write_manifest([], path=path)
    assert len(digest) == 64
    assert json.loads(path.read_text()) == []


def test_manifest_raises_rather_than_serialising_a_non_finite_value(tmp_path):
    path = tmp_path / "manifest.json"
    with pytest.raises(ValueError, match="not JSON compliant"):
        write_manifest([{"team_id": "team-01", "score": float("inf")}], path=path)
    assert not path.exists()


# ---------------------------------------------------------------------------------------------
# atomic_release -- given tests, transcribed verbatim
# ---------------------------------------------------------------------------------------------


def test_atomic_release_moves_the_whole_bundle(tmp_path):
    staging = tmp_path / "staging"
    (staging / "team-01").mkdir(parents=True)
    (staging / "team-01" / "summary.json").write_text("{}")
    release = tmp_path / "release"
    atomic_release(staging, release)
    assert (release / "team-01" / "summary.json").exists()
    assert not staging.exists()


def test_atomic_release_refuses_to_overwrite_an_existing_release(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    release = tmp_path / "release"
    release.mkdir()
    with pytest.raises(FileExistsError):
        atomic_release(staging, release)


# ---------------------------------------------------------------------------------------------
# atomic_release -- additions covering the remaining raise paths from the pre-empt list, plus
# one adversarial ordering test and one proving the ENTIRE tree (not just one shallow file)
# moves intact.
# ---------------------------------------------------------------------------------------------


def test_atomic_release_raises_when_staging_is_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        atomic_release(tmp_path / "does-not-exist", tmp_path / "release")


def test_atomic_release_creates_missing_release_parent_directories(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "payload.json").write_text("{}")
    release = tmp_path / "a" / "b" / "c" / "release"  # tmp_path/a does not exist yet
    atomic_release(staging, release)
    assert (release / "payload.json").exists()
    assert not staging.exists()


def test_atomic_release_checks_release_existence_before_staging_existence(tmp_path):
    """Both preconditions are violated at once: staging is missing AND release already exists.
    The no-overwrite rule must win (FileExistsError), not the missing-staging check
    (FileNotFoundError) -- otherwise a caller could be misled into thinking that merely creating
    a staging directory and retrying would be safe, when the real blocker is the existing
    release. Pins the priority order that a naive "check staging first" implementation would get
    backwards."""
    release = tmp_path / "release"
    release.mkdir()
    with pytest.raises(FileExistsError):
        atomic_release(tmp_path / "does-not-exist", release)


def test_atomic_release_moves_nested_structure_and_multiple_teams_intact(tmp_path):
    staging = tmp_path / "staging"
    (staging / "team-01").mkdir(parents=True)
    (staging / "team-02" / "artifacts").mkdir(parents=True)
    (staging / "team-01" / "summary.json").write_text('{"a": 1}')
    (staging / "team-02" / "summary.json").write_text('{"b": 2}')
    (staging / "team-02" / "artifacts" / "daily_returns.csv").write_text("timestamp,daily_return\n")
    (staging / "manifest.json").write_text("[]")
    release = tmp_path / "release"

    atomic_release(staging, release)

    assert (release / "team-01" / "summary.json").read_text() == '{"a": 1}'
    assert (release / "team-02" / "summary.json").read_text() == '{"b": 2}'
    assert (release / "team-02" / "artifacts" / "daily_returns.csv").exists()
    assert (release / "manifest.json").read_text() == "[]"
    assert not staging.exists()
