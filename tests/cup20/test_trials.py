"""The material trial: its identity, its budget, and the refusal that makes journaling real.

Every raise path below is exercised on its own, and every test names the mutation it kills. The
two that matter most are the ones a passing suite would otherwise hide:

* **the budget off-by-one.** ``spent > limit`` instead of ``spent >= limit`` lets a team run
  thirteen trials while every other test still passes -- the chain verifies, the records are
  well-formed, the counter counts. Only an explicit "the thirteenth is refused" catches it.
* **matching a trial that is not this candidate's.** If ``resolve_accepted_trial`` compared
  candidate ids and nothing else, a team could journal once and then evaluate every edit it made
  afterwards for free, which is precisely the discipline the journal exists to enforce.
"""

import json
import math
from pathlib import Path

import pytest

from crypto_trade.cup20.config import TEAM_IDS, load_config
from crypto_trade.cup20.journal import accepted_trial_count, append_record, verify_chain
from crypto_trade.cup20.trials import (
    MATERIAL_FIELDS,
    TRIAL_ACCEPTED_EVENT,
    JournalBusyError,
    MaterialTrial,
    TrialBudgetExhaustedError,
    TrialNotAcceptedError,
    accepted_trials,
    candidate_source_digest,
    cost_model,
    describe_difference,
    journal_lock,
    matching_trials,
    record_trial,
    resolve_accepted_trial,
    risk_policy_digest,
)

CONFIG_PATH = Path("tournament/cup20/config.toml")
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64

MINIMAL_RISK_POLICY = {
    "schema_version": 1,
    "policy_id": "test-policy",
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


def _trial(**overrides) -> MaterialTrial:
    fields = {
        "team_id": "team-01",
        "candidate_id": "baseline",
        "purpose": "does slow momentum survive costs",
        "kind": "point",
        "source_sha256": DIGEST_A,
        "config_sha256": DIGEST_B,
        "risk_policy_sha256": DIGEST_C,
        "snapshot_sha256": DIGEST_D,
        "seed": 42,
        "window_start": "2020-08-17 00:00:00+00:00",
        "window_end": "2024-08-01 00:00:00+00:00",
        "cost_model": {
            "taker_fee_bps_per_side": 5.0,
            "slippage_bps_per_side": 2.5,
            "cost_multipliers": [1, 2, 3],
        },
        "parameters": {"formation_bars": 30},
        "declared_roles": ("long", "short"),
    }
    fields.update(overrides)
    return MaterialTrial(**fields)


def _candidate(root: Path, *, body: str = "def build_strategy():\n    return object()\n") -> Path:
    candidate = root / "candidates" / "baseline"
    candidate.mkdir(parents=True)
    (candidate / "strategy.py").write_text(body)
    (candidate / "risk_policy.json").write_text(json.dumps(MINIMAL_RISK_POLICY))
    return candidate


# --- the material tuple ------------------------------------------------------------------------


def test_the_material_tuple_is_exactly_the_charter_s_list():
    """Kills the mutation: dropping a component from the tuple, e.g. the seed or the cost model.

    A tuple missing a component means two genuinely different evaluations share one identity, and
    the second runs for free off the first's accepted trial.
    """
    material = _trial().material()
    assert set(material) == set(MATERIAL_FIELDS)
    assert set(MATERIAL_FIELDS) == {
        "kind",
        "source_sha256",
        "config_sha256",
        "risk_policy_sha256",
        "snapshot_sha256",
        "seed",
        "window",
        "cost_model",
        "parameters",
        "declared_roles",
    }


def test_the_material_tuple_survives_a_json_round_trip_unchanged():
    """Kills the mutation: leaving a tuple or a numpy scalar in the tuple.

    Comparison happens AFTER the journal has round-tripped the record through JSON, so anything
    that does not survive that round trip compares unequal to itself and no trial ever matches --
    a refusal that looks exactly like a team having edited its code.
    """
    trial = _trial()
    assert json.loads(json.dumps(trial.material())) == trial.material()


def test_purpose_is_not_part_of_the_identity_but_is_recorded():
    """Kills the mutation: folding the free-text purpose into the fingerprint.

    Purpose is prose. If it were material, a typo when re-typing it would refuse an evaluation the
    team had legitimately journaled -- and it would also let a team manufacture new identities by
    rewording, which the budget already prices correctly on its own.
    """
    first = _trial(purpose="one question")
    second = _trial(purpose="a different question")
    assert first.fingerprint() == second.fingerprint()
    assert first.payload()["purpose"] == "one question"


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"team_id": "team-13"}, "unknown team"),
        ({"team_id": "team-01x"}, "unknown team"),
        ({"candidate_id": "   "}, "candidate_id must not be blank"),
        ({"purpose": ""}, "purpose must not be blank"),
        ({"kind": "exploratory"}, "kind must be one of"),
        ({"seed": 1.5}, "seed must be an integer"),
        ({"seed": True}, "seed must be an integer"),
        ({"source_sha256": "short"}, "source_sha256 must be a SHA-256 digest"),
        ({"config_sha256": "z" * 64}, "config_sha256 must be a SHA-256 digest"),
        ({"risk_policy_sha256": ""}, "risk_policy_sha256 must be a SHA-256 digest"),
        ({"snapshot_sha256": "A" * 64}, "snapshot_sha256 must be a SHA-256 digest"),
        ({"declared_roles": ()}, "declared_roles must name at least one"),
        ({"declared_roles": ("long", "long")}, "declared_roles contains duplicates"),
        ({"declared_roles": ("flat",)}, "unrecognised declared role"),
        ({"parameters": {"x": math.nan}}, "Out of range float"),
    ],
)
def test_every_declaration_defect_is_refused_individually(overrides, fragment):
    """Kills the mutation: dropping any one validation.

    Each row is its own raise path. ``team-13`` and ``team-01x`` are the important pair: the budget
    is counted per team id, so an id outside the roster would spend nobody's budget at all, which
    is unlimited trials wearing a typo.
    """
    with pytest.raises(ValueError, match=fragment):
        _trial(**overrides)


def test_an_uppercase_digest_is_refused_rather_than_normalised():
    """Kills the mutation: case-folding digests.

    Two spellings of one digest would fingerprint differently, so a team that journaled with one
    and evaluated with the other would be refused for a reason it could not see.
    """
    with pytest.raises(ValueError):
        _trial(snapshot_sha256="A" * 64)


def test_every_roster_team_can_journal():
    """Kills the mutation: a roster check that is accidentally narrower than the roster."""
    for team_id in TEAM_IDS:
        assert _trial(team_id=team_id).team_id == team_id


# --- source bytes ------------------------------------------------------------------------------


def test_the_source_digest_covers_the_whole_candidate_directory(tmp_path):
    """Kills the mutation: hashing ``strategy.py`` alone.

    ``risk_policy.json`` is as material as the code, and a helper module beside the entrypoint can
    carry the entire mechanism. Either would change behaviour without changing identity.
    """
    candidate = _candidate(tmp_path)
    before = candidate_source_digest(candidate)
    (candidate / "helper.py").write_text("EDGE = 1\n")
    assert candidate_source_digest(candidate) != before


def test_the_source_digest_refuses_a_missing_directory(tmp_path):
    with pytest.raises(FileNotFoundError, match="candidate directory does not exist"):
        candidate_source_digest(tmp_path / "nope")


def test_the_source_digest_refuses_a_directory_with_no_entrypoint(tmp_path):
    """Kills the mutation: hashing an empty tree.

    ``bundle_digest`` of an empty directory is ``sha256("")`` -- a stable, plausible-looking value
    that would journal cleanly and then match every other empty candidate in the tournament.
    """
    empty = tmp_path / "candidates" / "baseline"
    empty.mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="strategy.py is missing"):
        candidate_source_digest(empty)


def test_the_risk_policy_digest_refuses_a_missing_policy(tmp_path):
    """Kills the mutation: defaulting an absent policy to "no policy".

    "No policy" and "a policy that declares nothing" are different claims and must not share an
    identity; and the policy is a named component of section 7.1's tuple.
    """
    candidate = _candidate(tmp_path)
    (candidate / "risk_policy.json").unlink()
    with pytest.raises(FileNotFoundError, match="risk_policy.json is missing"):
        risk_policy_digest(candidate)


def test_the_cost_model_is_read_from_the_frozen_execution_table():
    """Kills the mutation: hard-coding 5.0/2.5/[1,2,3] instead of reading the contract."""
    raw = load_config(CONFIG_PATH).raw
    assert cost_model(raw["execution"]) == {
        "taker_fee_bps_per_side": 5.0,
        "slippage_bps_per_side": 2.5,
        "cost_multipliers": [1, 2, 3],
    }


# --- the budget --------------------------------------------------------------------------------


def test_the_thirteenth_trial_is_refused_and_names_the_count(tmp_path):
    """Kills the mutation: ``spent > limit`` instead of ``spent >= limit``.

    An off-by-one here gives every team a thirteenth trial while the chain still verifies, the
    records are still well-formed and the counter still counts. Nothing else in the suite notices.
    """
    journal = tmp_path / "journal.jsonl"
    for index in range(12):
        accepted = record_trial(journal, _trial(purpose=f"question {index}"), budget=12)
        assert accepted.sequence == index + 1
        assert accepted.spent == index + 1
        assert accepted.remaining == 11 - index
    with pytest.raises(TrialBudgetExhaustedError) as failure:
        record_trial(journal, _trial(purpose="one more"), budget=12)
    message = str(failure.value)
    assert "team-01" in message
    assert "all 12 material trials" in message
    assert "12 accepted" in message
    assert "trial 13" in message
    assert accepted_trial_count(journal, "team-01") == 12


def test_the_refused_trial_is_not_appended(tmp_path):
    """Kills the mutation: raising after the append rather than before it.

    A refusal that still wrote the record would consume the budget it just refused to grant.
    """
    journal = tmp_path / "journal.jsonl"
    record_trial(journal, _trial(), budget=1)
    with pytest.raises(TrialBudgetExhaustedError):
        record_trial(journal, _trial(purpose="second"), budget=1)
    assert verify_chain(journal) == 1


def test_the_budget_is_per_team(tmp_path):
    """Kills the mutation: counting every team's trials against one global budget."""
    journal = tmp_path / "journal.jsonl"
    for index in range(12):
        record_trial(journal, _trial(purpose=f"q{index}"), budget=12)
    accepted = record_trial(journal, _trial(team_id="team-02", purpose="first"), budget=12)
    assert accepted.spent == 1
    assert accepted.sequence == 13


def test_a_zero_budget_is_a_caller_error_not_a_silent_refusal(tmp_path):
    with pytest.raises(ValueError, match="trial budget must be at least 1"):
        record_trial(tmp_path / "journal.jsonl", _trial(), budget=0)


def test_the_frozen_budget_is_twelve():
    """Kills the mutation: a CLI defaulting the budget rather than reading the contract."""
    raw = load_config(CONFIG_PATH).raw
    assert int(raw["research"]["trial_budget"]) == 12
    assert int(raw["research"]["minimum_trials_for_nomination"]) == 8


def test_appending_keeps_the_hash_chain_verifiable(tmp_path):
    journal = tmp_path / "journal.jsonl"
    for index in range(5):
        record_trial(journal, _trial(purpose=f"q{index}"), budget=12)
    assert verify_chain(journal) == 5


# --- the lock ----------------------------------------------------------------------------------


def test_a_held_lock_refuses_rather_than_corrupting_the_chain(tmp_path):
    """Kills the mutation: removing the lock.

    Phase 1 runs twelve teams in parallel against ONE journal. Two unsynchronised appends read the
    same head, write the same ``previous_sha256``, and produce two records claiming one sequence
    number -- a chain ``verify_chain`` then reports as corrupt, which nobody corrupted.
    """
    journal = tmp_path / "journal.jsonl"
    with journal_lock(journal):
        with pytest.raises(JournalBusyError, match="is held after"):
            record_trial(journal, _trial(), budget=12, lock_timeout_seconds=0.2)
    # And the lock is released on the way out, so the next append succeeds.
    assert record_trial(journal, _trial(), budget=12).sequence == 1


def test_twelve_teams_appending_at_once_still_produce_one_verifiable_chain(tmp_path):
    """Kills the mutation: removing the lock, directly and observably.

    Twelve threads, one append each, against one journal. With the lock the chain verifies and the
    count is twelve; without it, two appends read the same head and the chain breaks. This is the
    exact shape of phase 1, where twelve teams research in parallel.
    """
    import concurrent.futures

    journal = tmp_path / "journal.jsonl"

    def append(team_id: str) -> None:
        record_trial(journal, _trial(team_id=team_id), budget=12)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TEAM_IDS)) as pool:
        for future in [pool.submit(append, team_id) for team_id in TEAM_IDS]:
            future.result()

    assert verify_chain(journal) == len(TEAM_IDS)
    for team_id in TEAM_IDS:
        assert accepted_trial_count(journal, team_id) == 1


def test_the_lock_is_released_even_when_the_body_raises(tmp_path):
    journal = tmp_path / "journal.jsonl"
    lock_path = Path(str(journal) + ".lock")
    with pytest.raises(RuntimeError, match="boom"):
        with journal_lock(journal):
            assert lock_path.exists()
            raise RuntimeError("boom")
    assert not lock_path.exists()


def test_record_trial_leaves_no_lock_behind_after_a_refusal(tmp_path):
    journal = tmp_path / "journal.jsonl"
    record_trial(journal, _trial(), budget=1)
    with pytest.raises(TrialBudgetExhaustedError):
        record_trial(journal, _trial(purpose="second"), budget=1)
    assert not Path(str(journal) + ".lock").exists()


# --- lookup ------------------------------------------------------------------------------------


def test_the_lookup_and_the_counter_agree_on_a_journal_with_malformed_records(tmp_path):
    """Kills the mutation: the lookup and the counter disagreeing about what a trial is.

    ``accepted_trial_count`` deliberately fails OPEN on a malformed payload -- one corrupt record
    must not deny every team's count. If ``accepted_trials`` were stricter or looser, a team could
    be told it had spent eleven while the harness found a twelfth to run against, or vice versa.
    """
    journal = tmp_path / "journal.jsonl"
    record_trial(journal, _trial(), budget=12)
    append_record(journal, TRIAL_ACCEPTED_EVENT, {"team_id": "team-02"})
    append_record(journal, "organiser_note", {"team_id": "team-01"})
    record_trial(journal, _trial(purpose="second"), budget=12)
    assert len(accepted_trials(journal, "team-01")) == accepted_trial_count(journal, "team-01")
    assert accepted_trial_count(journal, "team-01") == 2


def test_matching_compares_the_tuple_not_the_stored_fingerprint(tmp_path):
    """Kills the mutation: trusting ``payload["fingerprint"]``.

    The fingerprint is a convenience for a human reading the journal. A value written into the
    record is not evidence about the values it claims to summarise, so the comparison is over the
    fields themselves.
    """
    journal = tmp_path / "journal.jsonl"
    trial = _trial()
    forged = dict(trial.payload())
    forged["fingerprint"] = trial.fingerprint()
    forged["source_sha256"] = "e" * 64  # the record's own tuple says a different candidate
    append_record(journal, TRIAL_ACCEPTED_EVENT, forged)
    assert matching_trials(accepted_trials(journal, "team-01"), trial) == ()


def test_describe_difference_names_every_field_that_moved():
    recorded = {"payload": _trial().payload()}
    changed = _trial(source_sha256="e" * 64, seed=7)
    differences = describe_difference(recorded, changed)
    assert len(differences) == 2
    assert any(line.startswith("source_sha256:") for line in differences)
    assert any(line.startswith("seed:") for line in differences)


def _recomputed(trial: MaterialTrial) -> dict:
    return {
        "kind": trial.kind,
        "source_sha256": trial.source_sha256,
        "config_sha256": trial.config_sha256,
        "risk_policy_sha256": trial.risk_policy_sha256,
        "snapshot_sha256": trial.snapshot_sha256,
        "window_start": trial.window_start,
        "window_end": trial.window_end,
        "cost_model": dict(trial.cost_model),
    }


def test_resolution_returns_the_accepted_trial_for_this_exact_state(tmp_path):
    journal = tmp_path / "journal.jsonl"
    trial = _trial()
    record_trial(journal, trial, budget=12)
    resolved = resolve_accepted_trial(
        journal, team_id="team-01", candidate_id="baseline", recomputed=_recomputed(trial)
    )
    assert resolved.sequence == 1
    assert resolved.trial.seed == 42
    assert resolved.trial.declared_roles == ("long", "short")


def test_resolution_refuses_when_the_source_bytes_moved_and_says_so(tmp_path):
    """Kills the mutation: matching on candidate id alone.

    This is the whole point of the command. Journal once, then edit ``strategy.py`` and evaluate
    again, and without this check every subsequent edit is free -- "journaled before you look at a
    number" becomes decoration.
    """
    journal = tmp_path / "journal.jsonl"
    trial = _trial()
    record_trial(journal, trial, budget=12)
    edited = _recomputed(trial) | {"source_sha256": "e" * 64}
    with pytest.raises(TrialNotAcceptedError) as failure:
        resolve_accepted_trial(
            journal, team_id="team-01", candidate_id="baseline", recomputed=edited
        )
    message = str(failure.value)
    assert "source_sha256" in message
    assert "NEW material trial" in message
    assert "sequence #1" in message


@pytest.mark.parametrize(
    "field",
    ["config_sha256", "risk_policy_sha256", "snapshot_sha256", "window_start", "kind"],
)
def test_every_recomputed_component_is_compared(tmp_path, field):
    """Kills the mutation: comparing only the source digest.

    A rebuilt snapshot, an amended config, a re-declared risk policy and a moved window are each a
    different material trial by section 7.1's own definition, and each would otherwise be evaluated
    silently against a trial that described something else.
    """
    journal = tmp_path / "journal.jsonl"
    trial = _trial()
    record_trial(journal, trial, budget=12)
    moved = _recomputed(trial)
    moved[field] = "falsification" if field == "kind" else "f" * 64
    with pytest.raises(TrialNotAcceptedError):
        resolve_accepted_trial(
            journal, team_id="team-01", candidate_id="baseline", recomputed=moved
        )


def test_resolution_refuses_when_the_team_has_journaled_nothing(tmp_path):
    journal = tmp_path / "journal.jsonl"
    with pytest.raises(TrialNotAcceptedError) as failure:
        resolve_accepted_trial(
            journal,
            team_id="team-01",
            candidate_id="baseline",
            recomputed=_recomputed(_trial()),
        )
    message = str(failure.value)
    assert "has no accepted trial" in message
    assert "cup20_trial.py" in message  # tells them exactly what to run


def test_a_point_trial_does_not_licence_the_falsification_battery(tmp_path):
    """Kills the mutation: dropping ``kind`` from the tuple.

    Both batteries are one trial each *because they are declared in full before they run*. If an
    ordinary point trial licensed the battery, the battery would be free.
    """
    journal = tmp_path / "journal.jsonl"
    trial = _trial(kind="point")
    record_trial(journal, trial, budget=12)
    with pytest.raises(TrialNotAcceptedError, match="none of kind 'falsification'"):
        resolve_accepted_trial(
            journal,
            team_id="team-01",
            candidate_id="baseline",
            recomputed=_recomputed(trial) | {"kind": "falsification"},
        )


def test_a_pinned_sequence_that_is_not_an_accepted_trial_is_refused(tmp_path):
    journal = tmp_path / "journal.jsonl"
    trial = _trial()
    record_trial(journal, trial, budget=12)
    with pytest.raises(TrialNotAcceptedError, match="sequence #99 is not an accepted trial"):
        resolve_accepted_trial(
            journal,
            team_id="team-01",
            candidate_id="baseline",
            recomputed=_recomputed(trial),
            pinned_sequence=99,
        )


def test_a_hand_edited_record_is_skipped_rather_than_denying_a_good_trial(tmp_path):
    """Kills the mutation: raising on the first malformed record.

    The journal is shared by twelve teams. One corrupt entry must not deny an evaluation that has
    a perfectly good accepted trial two lines further down.
    """
    journal = tmp_path / "journal.jsonl"
    trial = _trial()
    broken = dict(trial.payload())
    broken["declared_roles"] = "long,short"  # a string, not a list
    append_record(journal, TRIAL_ACCEPTED_EVENT, broken)
    record_trial(journal, trial, budget=12)
    resolved = resolve_accepted_trial(
        journal, team_id="team-01", candidate_id="baseline", recomputed=_recomputed(trial)
    )
    assert resolved.sequence == 2


def test_the_most_recent_matching_trial_wins(tmp_path):
    journal = tmp_path / "journal.jsonl"
    trial = _trial()
    record_trial(journal, trial, budget=12)
    record_trial(journal, _trial(purpose="asked again"), budget=12)
    resolved = resolve_accepted_trial(
        journal, team_id="team-01", candidate_id="baseline", recomputed=_recomputed(trial)
    )
    assert resolved.sequence == 2


# --- amendment A6: the multiplicity charge counts only chances to pick a winner ----------------


def _journal_with(tmp_path, kinds, team_id="team-01"):
    """A journal holding one accepted trial per kind, through the real append path."""
    from crypto_trade.cup20.journal import append_record

    path = tmp_path / "journal.jsonl"
    for index, kind in enumerate(kinds):
        append_record(
            path,
            "trial_accepted",
            {"team_id": team_id, "candidate_id": f"c{index}", "kind": kind},
        )
    return path


def test_falsification_and_ablation_do_not_raise_the_multiplicity_bar(tmp_path):
    """A6's point: attacking your own result, and declaring a control, are not extra guesses.

    Charging them identically to a parameter search is what made four of the first seven teams stop
    at the eight-trial minimum with a third of the budget unspent.
    """
    from crypto_trade.cup20.journal import accepted_trial_count
    from crypto_trade.cup20.trials import multiplicity_charged_count

    path = _journal_with(
        tmp_path, ["point", "point", "neighbourhood", "falsification", "ablation", "ablation"]
    )
    assert accepted_trial_count(path, "team-01") == 6  # the BUDGET still charges every trial
    assert multiplicity_charged_count(path, "team-01") == 3  # 2 point + 1 neighbourhood


def test_a_kindless_record_is_charged_rather_than_waved_through(tmp_path):
    """Fail closed: 'we cannot tell what this was' must not become a free trial."""
    from crypto_trade.cup20.journal import append_record
    from crypto_trade.cup20.trials import multiplicity_charged_count

    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01", "candidate_id": "c"})
    assert multiplicity_charged_count(path, "team-01") == 1


def test_the_charge_is_per_team(tmp_path):
    from crypto_trade.cup20.journal import append_record
    from crypto_trade.cup20.trials import multiplicity_charged_count

    path = _journal_with(tmp_path, ["point", "point"], team_id="team-01")
    append_record(
        path, "trial_accepted", {"team_id": "team-02", "candidate_id": "x", "kind": "point"}
    )
    assert multiplicity_charged_count(path, "team-01") == 2
    assert multiplicity_charged_count(path, "team-02") == 1


def test_ablation_is_a_recognised_kind_and_the_charged_set_excludes_it():
    from crypto_trade.cup20.trials import MULTIPLICITY_CHARGED_KINDS, TRIAL_KINDS

    assert "ablation" in TRIAL_KINDS
    assert MULTIPLICITY_CHARGED_KINDS == {"point", "neighbourhood"}
    assert not MULTIPLICITY_CHARGED_KINDS & {"falsification", "ablation"}


def test_the_ablation_forfeit_follows_the_bytes_not_the_candidate_name(tmp_path):
    """The price of the exemption, in the version a rename cannot defeat.

    Keyed on the candidate id, the forfeit is trivially escaped: declare nine ablations for free,
    find the best, copy its strategy.py to a fresh id, journal that as a point and nominate it --
    a nine-candidate search for one charge. The bytes are what was explored.
    """
    from crypto_trade.cup20.journal import append_record
    from crypto_trade.cup20.trials import ablated_source_digests

    path = tmp_path / "journal.jsonl"
    append_record(
        path,
        "trial_accepted",
        {"team_id": "team-01", "candidate_id": "keep", "kind": "point", "source_sha256": "a" * 64},
    )
    append_record(
        path,
        "trial_accepted",
        {
            "team_id": "team-01",
            "candidate_id": "control",
            "kind": "ablation",
            "source_sha256": "b" * 64,
        },
    )
    assert ablated_source_digests(path, "team-01") == frozenset({"b" * 64})

    # the escape an id-keyed forfeit allowed: identical bytes under a new name
    append_record(
        path,
        "trial_accepted",
        {
            "team_id": "team-01",
            "candidate_id": "renamed-contender",
            "kind": "point",
            "source_sha256": "b" * 64,
        },
    )
    assert "b" * 64 in ablated_source_digests(path, "team-01")
    assert "a" * 64 not in ablated_source_digests(path, "team-01")


def test_every_trial_kind_is_reachable_from_some_evaluator_mode():
    """Regression: A6 shipped with ``--kind ablation`` journalable but unrunnable.

    Kind is part of the material tuple, so a trial journaled ``ablation`` can only be resolved by an
    evaluator that PRODUCES ``ablation`` -- and no mode did. The trial was spent and permanently
    unevaluable, and the non-nomination guard then blocked re-running the same candidate as a point.
    A team found this by losing a trial to it.

    Surjectivity onto ``TRIAL_KINDS`` is the property: every kind a team can journal must be a kind
    some mode yields, or that kind is a trap.
    """
    from crypto_trade.cup20.trials import TRIAL_KINDS, kind_for_mode

    reachable = {
        kind_for_mode(falsification=f, ablation=a, neighbourhood=n)
        for f in (True, False)
        for a in (True, False)
        for n in (True, False)
    }
    assert reachable == set(TRIAL_KINDS)


def test_every_scored_mode_of_the_evaluator_actually_runs(tmp_path):
    """Regression: the evaluator called ``kind_for_mode`` without importing it.

    Every scored mode -- point, ablation, neighbourhood, falsification -- died with a NameError
    immediately after the snapshot loaded and immediately BEFORE the accepted trial was resolved.
    Only ``--check`` returns early enough to survive, so the harness looked healthy until a team
    spent its first trial. A whole team hit this and had to run the organiser's own script through
    a shim inside its own workspace to proceed.

    Two earlier attempts at this test were worthless and both are worth remembering. The first
    asserted ``"kind_for_mode(" in source`` -- satisfied by the call site itself, so it passed with
    the import absent. The second ran the script against a MISSING candidate, which refuses at the
    source-digest step, before the broken line is ever reached. The candidate must exist and the
    journal must be empty, so the run reaches ``kind_for_mode`` and then refuses at trial
    resolution.
    """
    import subprocess
    import sys

    workspace = tmp_path / "team-01"
    candidate = workspace / "candidates" / "baseline"
    candidate.mkdir(parents=True)
    (candidate / "strategy.py").write_text("def build_strategy():\n    raise NotImplementedError\n")
    (candidate / "risk_policy.json").write_text(json.dumps(MINIMAL_RISK_POLICY))
    empty_journal = tmp_path / "journal.jsonl"
    empty_journal.write_text("")

    for mode in ([], ["--ablation"], ["--neighbourhood"], ["--falsification"]):
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/cup20_evaluate.py",
                "--team", "team-01",
                "--candidate", "baseline",
                "--team-root", str(tmp_path),
                "--journal", str(empty_journal),
                *mode,
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        label = mode or ["point"]
        combined = completed.stdout + completed.stderr
        assert "NameError" not in combined, f"{label}: {combined[-400:]}"
        assert "Traceback" not in combined, f"{label}: {combined[-400:]}"
        assert "REFUSED" in combined, f"{label}: {combined[-400:]}"
        assert completed.returncode == 2, f"{label}: exit {completed.returncode}"

def test_the_mode_precedence_is_stable():
    from crypto_trade.cup20.trials import kind_for_mode

    assert kind_for_mode(falsification=False, ablation=False, neighbourhood=False) == "point"
    assert kind_for_mode(falsification=False, ablation=True, neighbourhood=False) == "ablation"
    assert kind_for_mode(falsification=False, ablation=False, neighbourhood=True) == "neighbourhood"
    assert kind_for_mode(falsification=True, ablation=False, neighbourhood=False) == "falsification"
