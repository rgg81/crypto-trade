"""The pre-registered in-sample bar, applied before the sealed window is opened.

CUP-50's charter promised that all twelve lanes were scored with no performance qualification, its
release ranked all twelve on the sealed window, and a top-three in-sample stage was then applied
retrospectively. The incident record admits the correction "cannot recreate pre-OOS finalist
blindness", and it demoted the highest-scoring entry.

So the rule here is fixed in the config the activation record binds, evaluated at field close from
evidence frozen in each nomination, and never touched again. It is a bar rather than a rank because
in-sample position carries almost no information about sealed position -- CUP-50's sealed winner
ranked ninth of twelve in sample -- while a lane that showed no in-sample edge at all should not be
able to win on one sealed draw. Every nominated lane is observed either way.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping

from crypto_trade.cup50v2.config import QualificationPolicy, active_policy


@dataclasses.dataclass(frozen=True, slots=True)
class Eligibility:
    eligible: bool
    reason: str


def evaluate_eligibility(
    nomination: Mapping[str, object], *, policy: QualificationPolicy | None = None
) -> Eligibility:
    """Decide from the nomination's own frozen in-sample evidence."""
    rules = policy if policy is not None else active_policy().qualification
    score = nomination.get("is_score")
    regimes = nomination.get("is_regime_scores")
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        return Eligibility(False, "nomination carries no in-sample score")
    if not isinstance(regimes, Mapping) or not regimes:
        return Eligibility(False, "nomination carries no in-sample regime scores")
    if float(score) < rules.minimum_is_score:
        return Eligibility(
            False,
            f"in-sample score {float(score):.6f} is below the {rules.minimum_is_score:.6f} bar",
        )
    weakest_name, weakest = min(
        ((str(name), float(value)) for name, value in regimes.items()), key=lambda item: item[1]
    )
    if weakest < rules.minimum_is_regime_score:
        return Eligibility(
            False,
            f"in-sample {weakest_name} regime score {weakest:.6f} is below the "
            f"{rules.minimum_is_regime_score:.6f} bar",
        )
    return Eligibility(True, "cleared the pre-registered in-sample bar")
