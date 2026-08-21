"""The in-sample bar, and the ordering it produces.

CUP-50 released a leaderboard that ranked all twelve lanes on the sealed window, then applied a
top-three in-sample qualification stage retrospectively: the winner changed, nine lanes were
reclassified after their sealed evidence had already been read, and the incident record concedes the
correction "cannot recreate pre-OOS finalist blindness".

Two properties matter here. The verdict is decided from evidence frozen before the sealed window
opens, and it is a bar rather than a rank, because CUP-50's sealed winner ranked ninth of twelve in
sample and a top-three cut would have discarded it.
"""

from __future__ import annotations

import pytest

from crypto_trade.cup50v2.config import active_policy
from crypto_trade.cup50v2.qualification import evaluate_eligibility
from crypto_trade.cup50v2.scoring import RankedEntry, rank_entries

BAR = active_policy().qualification


def _nomination(score: float, regimes: dict[str, float]) -> dict[str, object]:
    return {"team_id": "team-01", "is_score": score, "is_regime_scores": regimes}


def _even(score: float) -> dict[str, float]:
    return {"bull": score, "bear": score, "chop": score}


def test_a_lane_clearing_both_thresholds_is_eligible() -> None:
    verdict = evaluate_eligibility(_nomination(60.0, _even(50.0)))
    assert verdict.eligible
    assert "cleared" in verdict.reason


def test_a_lane_below_the_overall_bar_is_ineligible() -> None:
    verdict = evaluate_eligibility(_nomination(BAR.minimum_is_score - 0.1, _even(90.0)))
    assert not verdict.eligible
    assert "below" in verdict.reason


def test_a_lane_carried_by_one_market_state_is_ineligible() -> None:
    """A book that is superb in bull and helpless in bear has not shown it generalises."""
    verdict = evaluate_eligibility(
        _nomination(80.0, {"bull": 99.0, "bear": BAR.minimum_is_regime_score - 0.1, "chop": 80.0})
    )
    assert not verdict.eligible
    assert "bear" in verdict.reason


def test_a_nomination_without_in_sample_evidence_cannot_qualify() -> None:
    assert not evaluate_eligibility({"team_id": "team-01"}).eligible
    assert not evaluate_eligibility(_nomination(90.0, {})).eligible


def test_the_bar_is_read_from_the_config_not_a_literal(tmp_path) -> None:
    import tomllib

    from crypto_trade.cup50v2.config import DEFAULT_CONFIG_PATH, load_config

    raw = tomllib.loads(DEFAULT_CONFIG_PATH.read_text())
    raw["qualification"]["minimum_is_score"] = 95.0
    lines = [f"{k} = {v!r}".replace("'", '"') for k, v in raw.items() if not isinstance(v, dict)]
    for section, body in raw.items():
        if isinstance(body, dict):
            lines.append(f"\n[{section}]")
            for key, value in body.items():
                import json as _json

                lines.append(f"{key} = {_json.dumps(value)}")
    path = tmp_path / "config.toml"
    path.write_text("\n".join(lines) + "\n")
    strict = load_config(path).policy.qualification

    nomination = _nomination(60.0, _even(50.0))
    assert evaluate_eligibility(nomination).eligible
    assert not evaluate_eligibility(nomination, policy=strict).eligible


def _entry(team: str, score: float, *, eligible: bool, valid: bool = True) -> RankedEntry:
    return RankedEntry(
        team_id=team,
        candidate_id="centre-v1",
        valid=valid,
        official_score=score,
        lower_quartile_score=score,
        minimum_point_score=score,
        centre_score=score,
        centre_worst_fold_3x_score=score,
        centre_3x_drawdown=0.1,
        centre_turnover=10.0,
        bundle_sha256="a" * 64,
        eligible=eligible,
    )


def test_an_ineligible_lane_is_published_and_ranked_but_cannot_outrank_an_eligible_one() -> None:
    """Every nominated lane is observed; the bar decides who can win, not who is measured."""
    strong_ineligible = _entry("team-09", 90.0, eligible=False)
    modest_eligible = _entry("team-02", 30.0, eligible=True)
    dnf = _entry("team-05", 0.0, eligible=False, valid=False)

    ordered = rank_entries([dnf, strong_ineligible, modest_eligible])

    assert [entry.team_id for entry in ordered] == ["team-02", "team-09", "team-05"]
    assert ordered[1].official_score > ordered[0].official_score


def test_eligible_lanes_still_rank_among_themselves_by_score() -> None:
    ordered = rank_entries(
        [
            _entry("team-01", 10.0, eligible=True),
            _entry("team-02", 40.0, eligible=True),
            _entry("team-03", 25.0, eligible=True),
        ]
    )
    assert [entry.team_id for entry in ordered] == ["team-02", "team-03", "team-01"]


def test_field_close_refuses_a_nomination_with_no_qualification_verdict(tmp_path) -> None:
    from crypto_trade.cup50v2.config import TEAM_IDS
    from crypto_trade.cup50v2.lifecycle import freeze_field

    dispositions = {
        team: {
            "state": "nominated",
            "nomination_sha256": "a" * 64,
            "point_ids": [f"{team}-p0"],
        }
        for team in TEAM_IDS
    }
    with pytest.raises(ValueError, match="qualification verdict"):
        freeze_field(
            tmp_path / "field.json",
            dispositions=dispositions,
            observation_order=list(TEAM_IDS),
            activation_sha256="b" * 64,
            signing_key=b"k" * 32,
        )


def test_the_observation_order_is_derived_not_numeric() -> None:
    """CUP-50 observed team-01 first and team-12 last; order should carry no information."""
    from crypto_trade.cup50v2.config import TEAM_IDS
    from crypto_trade.cup50v2.lifecycle import observation_order

    order = observation_order(b"k" * 32, activation_sha256="a" * 64)
    assert sorted(order) == sorted(TEAM_IDS)
    assert order != TEAM_IDS
    assert order == observation_order(b"k" * 32, activation_sha256="a" * 64)
    assert order != observation_order(b"j" * 32, activation_sha256="a" * 64)
    assert order != observation_order(b"k" * 32, activation_sha256="b" * 64)


DECLARED = {
    "schema_version": 1,
    "candidate_id": "centre-v1",
    "controls": {
        "drawdown_brake": "none, deliberately: the common risk unit already sizes the book",
        "stop_loss": "none, deliberately: a stop on a weekly book is a turnover tax",
        "turnover_limit": "no-trade band of 0.05 gross, which caps churn without capping size",
        "side_scaling": "short leg halved after a market drawdown, to survive the rebound",
        "exposure_conditioning": "gross scales with signal agreement across horizons",
        "position_concentration": "0.15 per name inside the seed, under the organizer's 0.20",
    },
    "rationale": (
        "The lane's risk is a momentum crash, not a single bad name, so the controls address "
        "the rebound and leave per-name risk to the common unit."
    ),
}


def test_a_complete_risk_declaration_is_accepted() -> None:
    from crypto_trade.cup50v2.qualification import verify_risk_declaration

    verify_risk_declaration(DECLARED)


def test_a_deliberate_absence_counts_as_a_decision() -> None:
    """The point is to distinguish a choice from a default, not to require controls."""
    from crypto_trade.cup50v2.qualification import REQUIRED_CONTROLS, verify_risk_declaration

    nothing = {
        **DECLARED,
        "controls": {name: "none, deliberately: see rationale" for name in REQUIRED_CONTROLS},
    }
    verify_risk_declaration(nothing)


@pytest.mark.parametrize("control", ["drawdown_brake", "stop_loss", "position_concentration"])
def test_an_undecided_control_is_refused(control: str) -> None:
    from crypto_trade.cup50v2.qualification import verify_risk_declaration

    incomplete = {**DECLARED, "controls": dict(DECLARED["controls"])}
    del incomplete["controls"][control]
    with pytest.raises(ValueError, match="does not decide"):
        verify_risk_declaration(incomplete)


def test_the_shipped_template_cannot_itself_be_submitted() -> None:
    """A team that ships the template unedited has declared nothing."""
    import json
    from pathlib import Path

    from crypto_trade.cup50v2.qualification import verify_risk_declaration

    template = json.loads(Path("tournament/cup50v2/RISK-DECLARATION-TEMPLATE.json").read_text())
    with pytest.raises(ValueError, match="placeholder|rationale"):
        verify_risk_declaration(template)


def test_a_blank_rationale_is_refused() -> None:
    from crypto_trade.cup50v2.qualification import verify_risk_declaration

    with pytest.raises(ValueError, match="rationale"):
        verify_risk_declaration({**DECLARED, "rationale": "n/a"})


def test_a_declaration_must_name_the_candidate_it_declares_for() -> None:
    """Amendment A5: the field was in the schema and nothing ever read it.

    The prior tests all passed a declaration with no candidate_id at all, so the fixture was
    constant along the dimension the binding lives on and could not have detected its absence.
    This test asserts the dimension is live in both directions: the same declaration is accepted
    under its own id and rejected under another's.
    """
    import pytest

    from crypto_trade.cup50v2.qualification import verify_risk_declaration

    declaration = {**DECLARED, "candidate_id": "team-04-regime-ensemble-001"}

    # Unbound, it passes -- which is exactly how six declarations naming the wrong candidate
    # reached a frozen nomination.
    verify_risk_declaration(declaration)

    verify_risk_declaration(declaration, candidate_id="team-04-regime-ensemble-001")

    with pytest.raises(ValueError, match="not the nominated"):
        verify_risk_declaration(declaration, candidate_id="team-04-regime-ensemble-002")

    nameless = {k: v for k, v in DECLARED.items() if k != "candidate_id"}
    with pytest.raises(ValueError, match="does not name the candidate"):
        verify_risk_declaration(nameless, candidate_id="team-04-regime-ensemble-001")

    # DECLARED has carried a candidate_id since the fixture was written, and every test above
    # passes it without one being expected. That is the defect in miniature.
    assert DECLARED["candidate_id"] == "centre-v1"
    verify_risk_declaration(DECLARED)


def test_field_close_derives_the_order_and_refuses_a_supplied_one(tmp_path) -> None:
    """Amendment A6: the derivation existed, was tested, and the lifecycle never called it.

    test_the_observation_order_is_derived_not_numeric proves the helper works. It does not prove
    anything calls it, and for the whole research phase nothing did -- _field_close took whatever
    order the dispositions payload carried, so the order C17 requires to be key-derived was in
    practice the organizer's to choose. Testing a helper is not testing the path.
    """
    import argparse
    import json

    import pytest

    from crypto_trade.cup50v2.cli import _field_close
    from crypto_trade.cup50v2.lifecycle import TEAM_IDS, observation_order

    activation = "a" * 64
    key_path = tmp_path / "field.key"
    key_path.write_bytes(b"k" * 32)
    derived = observation_order(b"k" * 32, activation_sha256=activation)
    assert list(derived) != list(TEAM_IDS), "fixture must not be numeric order"

    dispositions = {
        team: {
            "state": "nominated",
            "eligible": True,
            "eligibility_reason": "fixture",
            "nomination_sha256": "d" * 64,
            "point_ids": [f"{team}-p0"],
        }
        for team in TEAM_IDS
    }

    def close(payload, name):
        path = tmp_path / name
        source = tmp_path / f"{name}.json"
        source.write_text(json.dumps(payload))
        return _field_close(
            argparse.Namespace(
                dispositions=str(source),
                activation_sha256=activation,
                signing_key=str(key_path),
                output=str(path),
            )
        )

    # An order the organizer picked is refused outright.
    with pytest.raises(ValueError, match="derived from the signing key"):
        close(
            {"dispositions": dispositions, "observation_order": list(TEAM_IDS)},
            "picked",
        )

    # Omitting it entirely is the intended call, and the frozen record carries the derived order.
    record = close({"dispositions": dispositions}, "derived")
    assert list(record["observation_order"]) == list(derived)


def test_point_ids_must_be_unique_across_the_field_not_only_within_a_lane(tmp_path) -> None:
    """The per-lane check cannot see the collision that actually bites.

    Point ids key the journal and name the private evidence file, both flat across the whole
    field. Twelve lanes each numbering their points 0..n satisfy per-lane uniqueness and collide
    on the second lane's first point, where the exclusive create of the evidence file stops a
    ten-hour one-shot run partway through. The dispositions this edition first generated did
    exactly that: 208 points, 21 distinct.
    """
    import pytest

    from crypto_trade.cup50v2.lifecycle import TEAM_IDS, freeze_field, observation_order

    key = b"k" * 32
    activation = "a" * 64

    def lanes(point_ids_for):
        return {
            team: {
                "state": "nominated",
                "eligible": True,
                "eligibility_reason": "fixture",
                "nomination_sha256": "d" * 64,
                "point_ids": point_ids_for(team),
            }
            for team in TEAM_IDS
        }

    # Per-lane unique, field-wide colliding -- the shape that shipped.
    colliding = lanes(lambda team: ["0", "1", "2"])
    for lane in colliding.values():
        assert len(lane["point_ids"]) == len(set(lane["point_ids"])), "fixture is per-lane unique"
    with pytest.raises(ValueError, match="unique across the field"):
        freeze_field(
            tmp_path / "colliding.json",
            dispositions=colliding,
            observation_order=observation_order(key, activation_sha256=activation),
            activation_sha256=activation,
            signing_key=key,
        )

    record = freeze_field(
        tmp_path / "distinct.json",
        dispositions=lanes(lambda team: [f"{team}-p{index:02d}" for index in range(3)]),
        observation_order=observation_order(key, activation_sha256=activation),
        activation_sha256=activation,
        signing_key=key,
    )
    assert record["field_sha256"]
