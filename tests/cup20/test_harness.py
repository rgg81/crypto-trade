"""The team-facing evaluation harness: what it refuses, what it discloses, and in what order.

The harness is the only scorer twelve teams will ever run, so the mutations that matter are not
"does it compute a Sharpe" -- ``tests/cup20/test_metrics.py`` owns that -- but the ones that would
let it quietly stop being the organiser's pipeline:

* **scanning after the import.** Team code is executed here. A blindness scan that ran afterwards
  would be reporting on a tree the imported code had already had a chance to edit.
* **a gate with no explanation.** The coaching packet restates section 7.3's thresholds so a team
  can see how far short it fell. The way a restatement goes wrong is by falling behind a NEW floor,
  so the coverage test compares this module's table against the gate set ``evaluate_floors``
  actually produces rather than against a copy of it.
* **an inversion that is not exact**, or a placebo that is not a placebo. Both are inputs to a
  DISQUALIFYING verdict.
* **reporting QUALIFIED.** Two gates cannot be decided at a single point, and they are supplied to
  the floors at values that pass. If the verdict read those back, the command would tell a team it
  had qualified on the strength of an assumption the harness made for it.
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.config import IS_END, load_config
from crypto_trade.cup20.harness import (
    _FLOOR_DETAIL,
    _SCALAR_GATES,
    CORE_FLOOR_CHECKS,
    UNMEASURED_AT_A_SINGLE_POINT,
    BlindnessViolationError,
    CandidateLoadError,
    PermutedAttribution,
    SignInverted,
    _confidence,
    _json_safe,
    check_candidate,
    evaluate_point,
    gate_details,
    load_candidate_risk_policy,
    load_team_strategy,
    run_falsification_battery,
    scan_workspace_or_refuse,
)
from crypto_trade.cup20.qualification import evaluate_floors
from crypto_trade.cup20.runner import normalise_unit_gross
from crypto_trade.cup20.scored_metrics import ASSEMBLED_METRIC_KEYS
from crypto_trade.cup20.snapshot import Snapshot
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN, DecisionContext

CONFIG_PATH = Path("tournament/cup20/config.toml")
RAW = load_config(CONFIG_PATH).raw

MINIMAL_RISK_POLICY = {
    "schema_version": 1,
    "policy_id": "harness-test",
    "same_boundary_reentry": True,
    "volatility_target": {
        "enabled": False,
        "lookback_days": 30,
        "annualized_target": 0.10,
        "minimum_scale": 0.5,
        "maximum_scale": 1.0,
    },
    "drawdown_brakes": [],
    "position_stop": {"enabled": False, "loss_fraction": 0.5, "cooldown_bars": 0},
    "time_stop": {"enabled": False, "maximum_holding_bars": 10, "cooldown_bars": 0},
    "turnover_limit": {"enabled": False, "maximum_one_way_turnover": 1.0},
    "side_scaling": {"long_scale": 1.0, "short_scale": 1.0},
}

LONG_SHORT_SOURCE = """
FORMATION_BARS = 30
ENTRY_THRESHOLD = 0.5


class Book:
    def target_weights(self, context, *, seed):
        if context.decision_time.weekday() != 0 or context.decision_time.hour != 0:
            return None
        symbols = sorted(context.eligible_symbols)
        if len(symbols) < 2:
            return {}
        half = len(symbols) // 2
        weight = 1.0 / len(symbols)
        return {s: weight for s in symbols[:half]} | {s: -weight for s in symbols[half:]}


def build_strategy():
    return Book()
"""


def _write_candidate(workspace: Path, *, source: str = LONG_SHORT_SOURCE) -> Path:
    candidate = workspace / "candidates" / "baseline"
    candidate.mkdir(parents=True)
    (candidate / "strategy.py").write_text(source)
    (candidate / "risk_policy.json").write_text(json.dumps(MINIMAL_RISK_POLICY))
    return candidate


def _context(decision_time, symbols):
    return DecisionContext(
        decision_time=decision_time,
        bars={symbol: pd.DataFrame({"open_time": [], "close": []}) for symbol in symbols},
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=list(symbols),
    )


class _Fixed:
    """Emits one fixed book, or an instruction, at every decision."""

    def __init__(self, book):
        self.book = book

    def target_weights(self, context, *, seed):
        return self.book


# --- the gate table stays level with the floors -------------------------------------------------


def test_the_coaching_table_covers_exactly_the_gates_the_floors_produce():
    """Kills the mutation: adding a floor to ``evaluate_floors`` without teaching this module.

    The packet's job is to say WHICH floor failed and BY HOW MUCH. A new floor with no entry here
    would either raise mid-packet or, worse under a laxer implementation, be rendered as an
    unexplained boolean -- the team is told it failed and not told what by.
    """
    scored = dict.fromkeys(ASSEMBLED_METRIC_KEYS, 0.5)
    gates = evaluate_floors(
        scored,
        floors=RAW["floors"],
        statistics_config=RAW["statistics"],
        research_config=RAW["research"],
        declared_roles=("long", "short"),
        sign_inversion_passes_core=False,
        neighbourhood_positive_fraction=1.0,
        trial_adjusted_confidence=1.0,
    )
    assert set(gates.checks) == set(_FLOOR_DETAIL) | set(_SCALAR_GATES)


def test_every_floor_key_the_table_names_exists_in_the_frozen_contract():
    """Kills the mutation: a typo'd ``[floors]`` key, which would raise only for a real candidate
    seven minutes into an evaluation."""
    named = {key for _, _, key in _FLOOR_DETAIL.values() if key is not None}
    assert named <= set(RAW["floors"])


def test_an_unknown_gate_raises_rather_than_being_rendered_as_a_bare_boolean():
    with pytest.raises(ValueError, match="has no detail entry"):
        gate_details(
            {"a_brand_new_floor": False},
            dict.fromkeys(ASSEMBLED_METRIC_KEYS, 0.5),
            floors=RAW["floors"],
            statistics_config=RAW["statistics"],
            research_config=RAW["research"],
            declared_roles=("long",),
            observed_roles=("long",),
            neighbourhood_positive_fraction=1.0,
            confidence=1.0,
            unmeasured=(),
        )


def test_the_detail_reports_the_observed_value_against_its_floor():
    """Kills the mutation: reporting pass/fail only.

    The floors are public in the charter and a team holds its own returns, so the observed value
    discloses nothing it could not compute -- it only removes the incentive to compute it with a
    different scorer. A team must be able to see it missed 0.80 by 0.02 rather than "it failed".
    """
    scored = dict.fromkeys(ASSEMBLED_METRIC_KEYS, 0.5)
    scored["net_sharpe"] = 0.78
    details = {
        detail.name: detail
        for detail in gate_details(
            {"net_sharpe": False},
            scored,
            floors=RAW["floors"],
            statistics_config=RAW["statistics"],
            research_config=RAW["research"],
            declared_roles=("long",),
            observed_roles=("long",),
            neighbourhood_positive_fraction=1.0,
            confidence=1.0,
            unmeasured=(),
        )
    }
    assert details["net_sharpe"].observed == pytest.approx(0.78)
    assert details["net_sharpe"].floor == pytest.approx(0.80)
    assert details["net_sharpe"].comparison == ">="
    assert "0.78" in details["net_sharpe"].render()


def test_the_core_falsification_floors_are_real_floors():
    """Kills the mutation: a core-floor name that no gate produces, which would silently make the
    sign-inversion verdict read a ``KeyError`` -- or, worse, a shorter conjunction than intended."""
    assert set(CORE_FLOOR_CHECKS) <= set(_FLOOR_DETAIL)
    assert "sign_inversion_not_profitable" not in CORE_FLOOR_CHECKS
    assert "trial_adjusted_confidence" not in CORE_FLOOR_CHECKS
    assert not set(CORE_FLOOR_CHECKS) & {"role_long_gross_pnl", "role_short_gross_pnl"}


# --- loading team code --------------------------------------------------------------------------


def test_the_blindness_scan_runs_before_the_candidate_is_imported(tmp_path):
    """Kills the mutation: scanning after the import, or not at all.

    Team code is EXECUTED by the harness. A scan that ran afterwards would be reporting on a tree
    the imported code had already had the opportunity to rewrite. The strategy here writes a marker
    on import; the marker must not exist.
    """
    workspace = tmp_path / "team-01"
    marker = tmp_path / "imported.marker"
    _write_candidate(
        workspace,
        source=(
            f"import pathlib\npathlib.Path({str(marker)!r}).write_text('x')\n"
            "def build_strategy():\n    return object()\n"
        ),
    )
    (workspace / "research").mkdir()
    (workspace / "research" / "notes.md").write_text("look at data/cup20/sealed for the answer\n")

    with pytest.raises(BlindnessViolationError, match="data/cup20/sealed"):
        evaluate_point(
            snapshot=_snapshot(days=10),
            raw=RAW,
            candidate_root=workspace / "candidates" / "baseline",
            workspace_root=workspace,
            team_id="team-01",
            candidate_id="baseline",
            seed=1,
            declared_roles=("long",),
            trial_sequence=1,
            accepted_trials=1,
            source_sha256="a" * 64,
            is_start=pd.Timestamp("2021-01-01T00:00:00Z"),
        )
    assert not marker.exists(), "the candidate was imported before the workspace was scanned"


def test_the_scan_refuses_a_post_cutoff_date_literal(tmp_path):
    workspace = tmp_path / "team-01"
    _write_candidate(workspace)
    (workspace / "research").mkdir()
    (workspace / "research" / "eda.py").write_text("CUTOFF = '2025-03-01'\n")
    with pytest.raises(BlindnessViolationError, match="violation"):
        scan_workspace_or_refuse(workspace, team_id="team-01")


def test_the_scan_refuses_another_team_s_directory(tmp_path):
    workspace = tmp_path / "team-01"
    _write_candidate(workspace)
    (workspace / "notes.md").write_text("see tournament/cup20/teams/team-07/research\n")
    with pytest.raises(BlindnessViolationError, match="foreign-team-directory"):
        scan_workspace_or_refuse(workspace, team_id="team-01")


def test_the_scan_passes_a_clean_workspace_and_counts_what_it_read(tmp_path):
    """Kills the mutation that makes the scan vacuous: scanning nothing and reporting clean."""
    workspace = tmp_path / "team-01"
    _write_candidate(workspace)
    scan = scan_workspace_or_refuse(workspace, team_id="team-01")
    assert scan.violations == ()
    assert scan.files_scanned == 2


def test_an_unreadably_large_file_warns_rather_than_refusing(tmp_path):
    """Kills the mutation: treating ``unscanned`` as a violation.

    A team's workspace legitimately holds large cached frames. Refusing to evaluate over one is a
    tool making an organiser's decision; the packet surfaces it as a warning instead.
    """
    workspace = tmp_path / "team-01"
    _write_candidate(workspace)
    (workspace / "research").mkdir()
    (workspace / "research" / "cache.bin").write_bytes(b"0" * (8_388_608 + 1))
    scan = scan_workspace_or_refuse(workspace, team_id="team-01")
    assert scan.violations == ()
    assert len(scan.unscanned) == 1


@pytest.mark.parametrize(
    ("source", "fragment"),
    [
        ("raise RuntimeError('boom')\n", "raised on import"),
        ("BUILD = 1\n", "defines no callable build_strategy"),
        ("build_strategy = 3\n", "defines no callable build_strategy"),
        ("def build_strategy():\n    return 7\n", "has no target_weights"),
    ],
)
def test_every_entrypoint_defect_is_named_individually(tmp_path, source, fragment):
    """Kills the mutation: one broad `except` that reports every failure as the same thing.

    A team gets one message and has to act on it; "your entrypoint is bad" is not actionable and
    "build_strategy() returned 7, which has no target_weights()" is.
    """
    workspace = tmp_path / "team-01"
    candidate = _write_candidate(workspace, source=source)
    with pytest.raises(CandidateLoadError, match=fragment):
        load_team_strategy(candidate)


def test_a_missing_entrypoint_is_named(tmp_path):
    workspace = tmp_path / "team-01"
    candidate = _write_candidate(workspace)
    (candidate / "strategy.py").unlink()
    with pytest.raises(CandidateLoadError, match="does not exist"):
        load_team_strategy(candidate)


def test_a_missing_risk_policy_is_named(tmp_path):
    workspace = tmp_path / "team-01"
    candidate = _write_candidate(workspace)
    (candidate / "risk_policy.json").unlink()
    with pytest.raises(CandidateLoadError, match="every candidate declares a risk policy"):
        load_candidate_risk_policy(candidate)


_RELOAD_SOURCE = (
    "VALUE = {value}\n"
    "class B:\n"
    "    def target_weights(self, context, *, seed):\n"
    "        return {{'AUSDT': VALUE}}\n"
    "def build_strategy():\n"
    "    return B()\n"
)


def test_reloading_a_candidate_re_executes_its_current_bytes(tmp_path):
    """Kills the mutation this loader actually shipped with: ``SourceFileLoader.exec_module``.

    Bytecode invalidation is keyed on (mtime to the second, source size). The two sources below
    differ by one character and are written in the same second, so a ``__pycache__``-backed loader
    re-runs the FIRST one -- and nothing downstream can catch it, because the source digest would
    correctly report the second one's bytes while the evaluator ran the first one's code.
    """
    workspace = tmp_path / "team-01"
    candidate = _write_candidate(workspace, source=_RELOAD_SOURCE.format(value=1))
    first = load_team_strategy(candidate).target_weights(_context(None, ["AUSDT"]), seed=1)
    (candidate / "strategy.py").write_text(_RELOAD_SOURCE.format(value=2))
    second = load_team_strategy(candidate).target_weights(_context(None, ["AUSDT"]), seed=1)
    assert first == {"AUSDT": 1}
    assert second == {"AUSDT": 2}


# --- the falsification primitives ---------------------------------------------------------------


def test_the_sign_inversion_negates_every_weight_and_nothing_else():
    book = {"AUSDT": 0.4, "BUSDT": -0.6}
    inverted = SignInverted(_Fixed(book)).target_weights(_context(None, ["AUSDT", "BUSDT"]), seed=1)
    assert inverted == {"AUSDT": -0.4, "BUSDT": 0.6}


@pytest.mark.parametrize("instruction", [None, {}])
def test_the_sign_inversion_leaves_hold_and_flat_instructions_alone(instruction):
    """Kills the mutation: inverting the trading SCHEDULE as well as the direction.

    ``None`` means hold and ``{}`` means go flat. Neither carries a direction, so turning either
    into something else would make the result not an exact inversion of anything -- and the verdict
    it feeds is disqualifying.
    """
    result = SignInverted(_Fixed(instruction)).target_weights(_context(None, ["AUSDT"]), seed=1)
    assert result == instruction


def test_the_inversion_commutes_with_unit_gross_normalisation():
    """Kills the mutation: inverting after normalisation with a sign-sensitive divisor.

    ``normalise_unit_gross`` divides by the row's ABSOLUTE sum, which negation leaves unchanged, so
    inverting before and after must give the identical book. If it did not, "exact sign inversion"
    would be approximate, and the charter's disqualifying verdict would rest on an approximation.
    """
    frame = pd.DataFrame({"AUSDT": [0.4], "BUSDT": [-0.6], REBALANCE_INSTRUCTION_COLUMN: [True]})
    inverted_first = normalise_unit_gross(
        frame.assign(AUSDT=-frame["AUSDT"], BUSDT=-frame["BUSDT"])
    )
    normalised_first = normalise_unit_gross(frame)
    for column in ("AUSDT", "BUSDT"):
        assert inverted_first[column].iloc[0] == pytest.approx(-normalised_first[column].iloc[0])


def test_the_placebo_keeps_the_weight_multiset_and_moves_the_attribution():
    """Kills the mutation: returning the book unchanged, which makes the placebo the candidate.

    A placebo that trades the candidate's own selection is not a null. What must survive is the
    weight multiset (so gross exposure and the sizing distribution are untouched); what must not is
    which symbol receives which weight.
    """
    symbols = [f"S{index:02d}USDT" for index in range(20)]
    book = {"S00USDT": 0.5, "S01USDT": -0.3, "S02USDT": 0.2}
    placebo = PermutedAttribution(_Fixed(book), 7).target_weights(
        _context(pd.Timestamp("2021-01-04T00:00:00Z"), symbols), seed=1
    )
    assert sorted(placebo.values()) == sorted(book.values())
    assert sum(abs(weight) for weight in placebo.values()) == pytest.approx(1.0)
    assert set(placebo) <= set(symbols)
    assert set(placebo) != set(book)


def test_the_placebo_is_deterministic_per_seed_and_boundary_and_varies_across_seeds():
    """Kills two mutations at once: an unseeded RNG (irreproducible falsifier) and a seed that
    ignores the boundary (one permutation reused for four years, which is a relabelling of the
    candidate rather than a null)."""
    symbols = [f"S{index:02d}USDT" for index in range(20)]
    book = {"S00USDT": 0.5, "S01USDT": -0.5}
    monday = pd.Timestamp("2021-01-04T00:00:00Z")
    tuesday = pd.Timestamp("2021-01-05T00:00:00Z")
    first = PermutedAttribution(_Fixed(book), 7).target_weights(_context(monday, symbols), seed=1)
    again = PermutedAttribution(_Fixed(book), 7).target_weights(_context(monday, symbols), seed=1)
    other_seed = PermutedAttribution(_Fixed(book), 8).target_weights(
        _context(monday, symbols), seed=1
    )
    other_day = PermutedAttribution(_Fixed(book), 7).target_weights(
        _context(tuesday, symbols), seed=1
    )
    assert first == again
    assert first != other_seed
    assert first != other_day


def test_the_placebo_draws_from_the_eligible_set_not_the_candidate_s_own_names():
    """Kills the mutation: shuffling within the names the candidate picked.

    That would still be the candidate's selection, merely reordered, and the placebo would inherit
    whatever selection edge it was supposed to null out.
    """
    symbols = [f"S{index:02d}USDT" for index in range(20)]
    book = dict.fromkeys(["S00USDT", "S01USDT"], 0.5)
    seen: set[str] = set()
    for permutation_seed in range(12):
        placebo = PermutedAttribution(_Fixed(book), permutation_seed).target_weights(
            _context(pd.Timestamp("2021-01-04T00:00:00Z"), symbols), seed=1
        )
        seen |= set(placebo)
    assert len(seen) > 2


@pytest.mark.parametrize("instruction", [None, {}])
def test_the_placebo_leaves_hold_and_flat_instructions_alone(instruction):
    result = PermutedAttribution(_Fixed(instruction), 3).target_weights(
        _context(pd.Timestamp("2021-01-04T00:00:00Z"), ["AUSDT"]), seed=1
    )
    assert result == instruction


def test_a_negative_placebo_count_is_refused(tmp_path):
    workspace = tmp_path / "team-01"
    _write_candidate(workspace)
    with pytest.raises(ValueError, match="must not be negative"):
        run_falsification_battery(
            snapshot=_snapshot(days=10),
            raw=RAW,
            candidate_root=workspace / "candidates" / "baseline",
            workspace_root=workspace,
            team_id="team-01",
            candidate_id="baseline",
            seed=1,
            trial_sequence=1,
            is_start=pd.Timestamp("2021-01-01T00:00:00Z"),
            placebo_permutations=-1,
        )


# --- non-finite values fail closed ---------------------------------------------------------------


def test_an_unusable_return_series_fails_the_confidence_floor_rather_than_crashing():
    """Kills the fail-OPEN this term is uniquely exposed to.

    ``trial_adjusted_confidence`` computes ``min(1.0, 1 - T*(1 - B))``, and CPython evaluates
    ``min(1.0, nan)`` as ``1.0`` -- the most favourable possible value out of the one term whose
    job is to penalise. A bootstrap that cannot run must therefore produce a FAILING confidence,
    not a crash and not a perfect score.
    """

    class _Run:
        results = {1: None}

    class _Result:
        returns = pd.DataFrame(
            {"net_return": [math.nan, math.nan, math.nan]},
            index=pd.date_range("2021-01-01", periods=3, freq="D", tz="UTC"),
        )

    run = _Run()
    run.results = {1: _Result()}
    positive_fraction, confidence = _confidence(run, RAW, 4)
    assert math.isnan(positive_fraction)
    assert confidence == 0.0
    assert confidence < float(RAW["statistics"]["minimum_trial_adjusted_confidence"])


def test_non_finite_metrics_serialise_as_null_rather_than_the_nan_token():
    """Kills the mutation: ``allow_nan=True``, which writes the non-standard ``NaN`` token into a
    packet a strict JSON parser then rejects."""
    payload = _json_safe(
        {"a": math.nan, "b": [1.0, math.inf], "c": {"d": -math.inf}, "e": "text", "f": 3}
    )
    assert payload == {"a": None, "b": [1.0, None], "c": {"d": None}, "e": "text", "f": 3}
    json.dumps(payload, allow_nan=False)


# --- the whole pipeline, end to end ---------------------------------------------------------------


def _snapshot(days: int, symbols=("AUSDT", "BUSDT"), end=IS_END, drift=0.0004):
    """A synthetic in-sample snapshot ending exactly at the frozen cutoff."""
    periods = days * 3
    times = pd.date_range(end=end - pd.Timedelta(hours=8), periods=periods, freq="8h")
    generator = np.random.default_rng(11)
    rows = []
    prices: dict[str, np.ndarray] = {}
    for index, symbol in enumerate(symbols):
        steps = generator.normal(drift * (1 if index % 2 == 0 else -1), 0.01, periods)
        price = 100.0 * np.cumprod(1.0 + steps)
        prices[symbol] = price
        rows.append(
            pd.DataFrame(
                {
                    "open_time": times,
                    "symbol": symbol,
                    "open": price,
                    "high": price * 1.01,
                    "low": price * 0.99,
                    "close": price,
                    "volume": 1e6,
                    "quote_volume": 1e8,
                }
            )
        )
    bars = pd.concat(rows, ignore_index=True)
    funding = pd.DataFrame(
        {
            "funding_time": np.tile(times, len(symbols)),
            "symbol": np.repeat(list(symbols), len(times)),
            "funding_rate": 0.0001,
            "mark_price": np.concatenate([prices[symbol] for symbol in symbols]),
        }
    )
    marks = bars[["open_time", "symbol", "open"]].rename(
        columns={"open_time": "mark_time", "open": "mark_price"}
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]] * len(symbols),
            "symbol": list(symbols),
            "liquidity_rank": list(range(1, len(symbols) + 1)),
            "trailing_quote_volume": [1e8] * len(symbols),
        }
    )
    metadata = pd.DataFrame({"symbol": list(symbols), "contract_type": "PERPETUAL"})
    return Snapshot(bars, funding, marks, membership, metadata, manifest_sha256="synthetic")


@pytest.fixture(scope="module")
def end_to_end(tmp_path_factory):
    """One REAL evaluation, over the shortest window ``is_folds`` will accept.

    It costs about four minutes, and it is worth them. This is the command twelve teams run
    dozens of times each; a wiring defect in it -- a keyword argument that moved, a metric key
    that was renamed, a gate with no detail entry -- surfaces at the END of a seven-minute run
    that a team has already paid a trial for. ``scripts/cup20_readiness.py`` exercises the same
    stack on the real snapshot, but it is an organiser pre-flight run once and it does not touch
    the team-facing path at all.

    Everything that can be pinned in milliseconds is pinned in milliseconds above; what is left
    here is only what needs a real run: three real cost levels, four real folds, a real bootstrap,
    a real cap trim, and the real gate vector.
    """
    root = tmp_path_factory.mktemp("cup20-harness")
    workspace = root / "team-01"
    candidate = _write_candidate(workspace)
    days = 1097  # is_folds needs strictly more than three years; this is the cheapest window
    snapshot = _snapshot(days)
    is_start = pd.Timestamp(snapshot.bars["open_time"].min())
    packet = evaluate_point(
        snapshot=snapshot,
        raw=RAW,
        candidate_root=candidate,
        workspace_root=workspace,
        team_id="team-01",
        candidate_id="baseline",
        seed=20240101,
        declared_roles=("long", "short"),
        trial_sequence=3,
        accepted_trials=3,
        source_sha256="a" * 64,
        is_start=is_start,
    )
    return packet


def test_the_packet_carries_the_metric_vector_at_all_three_cost_levels(end_to_end):
    """Kills the mutation this pipeline has already shipped once: a signature drift between the
    harness and the scoring stack, which surfaces only after the whole seven-minute run."""
    assert sorted(end_to_end.cost_levels) == ["1x", "2x", "3x"]
    for level in end_to_end.cost_levels.values():
        assert {"net_sharpe", "max_drawdown", "annualized_turnover", "trade_count"} <= set(level)
    # The cost levels must actually differ -- identical vectors would mean the multiplier was
    # never applied and every "2x" number in the packet is a 1x number wearing a label.
    assert end_to_end.cost_levels["1x"]["net_sharpe"] != end_to_end.cost_levels["3x"]["net_sharpe"]


def test_the_packet_carries_four_fold_sharpes_and_both_cap_stages(end_to_end):
    assert list(end_to_end.fold_sharpes) == ["F1", "F2", "F3", "F4"]
    assert sorted(end_to_end.exposure_caps) == ["executed", "requested"]
    for stage in end_to_end.exposure_caps.values():
        assert stage["boundaries"] > 0
        assert 0.0 < stage["minimum_scale"] <= 1.0


def test_the_packet_explains_every_gate_it_reports(end_to_end):
    """Kills the mutation: a gate vector with no observed values, which tells a team that it failed
    and not what by."""
    assert end_to_end.gate_details
    for detail in end_to_end.gate_details:
        assert detail.name
        assert detail.observed is not None or detail.note


def test_the_packet_never_reports_qualified(end_to_end):
    """Kills the mutation: reading the verdict off ``adjudication.qualified``.

    Two gates are supplied to the floors at values that PASS because a single point cannot decide
    them. A verdict that read those back would tell a team it had qualified on the strength of an
    assumption the harness made on its behalf.
    """
    assert "QUALIFIED" not in end_to_end.verdict.upper().replace("NOT QUALIFIED", "")
    assert set(end_to_end.unmeasured_gates) == set(UNMEASURED_AT_A_SINGLE_POINT)
    unmeasured = {detail.name for detail in end_to_end.gate_details if not detail.measured}
    assert unmeasured == set(UNMEASURED_AT_A_SINGLE_POINT)
    assert all(
        detail.name not in end_to_end.measured_failures
        for detail in end_to_end.gate_details
        if not detail.measured
    )


def test_an_unmeasured_gate_never_reports_the_value_it_was_assumed_at(end_to_end):
    """Kills the mutation: rendering the assumed sign-inversion verdict as a finding.

    ``sign_inversion_not_profitable`` is supplied to the floors at ``passed``. If its note read
    that back -- "the exact sign inversion did NOT clear the core floors" -- a team would take an
    assumption for evidence and could reasonably believe its mandatory falsifier was already
    satisfied. The note has to say the opposite: that nothing was measured.
    """
    note = next(
        detail.note
        for detail in end_to_end.gate_details
        if detail.name == "sign_inversion_not_profitable"
    )
    assert "not measured here" in note
    assert "--falsification" in note


def test_the_packet_reports_the_real_bootstrap_and_the_trial_penalty(end_to_end):
    """Kills the mutation: hard-coding the confidence to 1.0.

    ``confidence = 1 - T(1 - B)`` is the mechanism that makes every extra look expensive. A
    constant would remove the only price the tournament puts on multiplicity.
    """
    assert 0.0 <= end_to_end.bootstrap_positive_fraction <= 1.0
    expected = max(0.0, min(1.0, 1.0 - 3 * (1.0 - end_to_end.bootstrap_positive_fraction)))
    assert end_to_end.trial_adjusted_confidence == pytest.approx(expected)


def test_the_packet_renders_and_serialises(end_to_end):
    text = end_to_end.render()
    assert "coaching packet" in text
    assert "exposure caps" in text
    assert "NOMINATED POINT" in text
    json.dumps(end_to_end.as_dict(), allow_nan=False)


def test_the_packet_records_the_window_and_folds_it_actually_scored(end_to_end):
    assert end_to_end.window[1] == IS_END
    assert end_to_end.folds[-1][2] == IS_END
    assert end_to_end.folds[0][1] == end_to_end.window[0]


# --- the no-cost check --------------------------------------------------------------------------


def test_the_check_opens_no_market_data_and_reports_what_it_verified(tmp_path):
    workspace = tmp_path / "team-01"
    candidate = _write_candidate(workspace)
    report = check_candidate(
        candidate_root=candidate,
        workspace_root=workspace,
        team_id="team-01",
        candidate_id="baseline",
        source_sha256="a" * 64,
    )
    assert report.ok
    assert report.risk_policy_id == "harness-test"
    assert report.neighbourhood_points is None
    assert "consumed no trial" in report.render()


def test_the_check_verifies_declared_coordinates_against_the_frozen_source(tmp_path):
    """Kills the mutation: accepting a neighbourhood whose nominee is not what the code does.

    Section 5.1 exists so the nominated point is provably the frozen behaviour. Catching a
    mismatch at check time costs an edit; catching it at nomination costs the submission.
    """
    workspace = tmp_path / "team-01"
    candidate = _write_candidate(workspace)
    (candidate / "neighbourhood.json").write_text(
        json.dumps(
            {
                "coordinates": ["FORMATION_BARS", "ENTRY_THRESHOLD"],
                "nominee": {"FORMATION_BARS": 25, "ENTRY_THRESHOLD": 0.5},
                "points": [
                    {"FORMATION_BARS": 20, "ENTRY_THRESHOLD": 0.5},
                    {"FORMATION_BARS": 30, "ENTRY_THRESHOLD": 0.5},
                    {"FORMATION_BARS": 25, "ENTRY_THRESHOLD": 0.4},
                    {"FORMATION_BARS": 25, "ENTRY_THRESHOLD": 0.6},
                    {"FORMATION_BARS": 20, "ENTRY_THRESHOLD": 0.4},
                    {"FORMATION_BARS": 30, "ENTRY_THRESHOLD": 0.6},
                ],
            }
        )
    )
    report = check_candidate(
        candidate_root=candidate,
        workspace_root=workspace,
        team_id="team-01",
        candidate_id="baseline",
        source_sha256="a" * 64,
    )
    assert not report.ok
    assert report.neighbourhood_points == 7
    assert any("FORMATION_BARS" in entry for entry in report.coordinate_violations)
    assert "VIOLATIONS" in report.render()
