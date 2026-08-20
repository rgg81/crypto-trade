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
