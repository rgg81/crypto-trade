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
import re
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


REQUIRED_CONTROLS = (
    "drawdown_brake",
    "stop_loss",
    "turnover_limit",
    "side_scaling",
    "exposure_conditioning",
    "position_concentration",
)
# The placeholders the shipped templates actually contain, matched case-sensitively and with
# their delimiters. A bare "replace" fires inside the ordinary English word "replaced", which
# rejected a lane for writing "more principled than the ones they replaced".
_PLACEHOLDERS = ("REPLACE-ME", "REPLACE:")


def verify_risk_declaration(
    declaration: Mapping[str, object], *, candidate_id: str | None = None
) -> None:
    """Require a decision about every control, including the decision to have none.

    CUP-20's risk template defaulted to all-disabled, so a team that never considered risk shipped
    the same bytes as one that thought hard and chose nothing, and the artifact could not tell them
    apart. Silence is not a declaration: "none, deliberately" is, and it is one sentence away.

    A declaration also has to say which candidate it is about, and be right. The field was in
    the schema from the start and nothing ever compared it with the nomination it accompanied,
    so a lane could have declared risk for a variant it never nominated and passed (A5).
    """
    if candidate_id is not None:
        declared = str(declaration.get("candidate_id", "")).strip()
        if not declared:
            raise ValueError("risk declaration does not name the candidate it declares for")
        if declared != candidate_id:
            raise ValueError(
                f"risk declaration is for {declared!r}, not the nominated {candidate_id!r}"
            )
    if int(declaration.get("schema_version", 0)) != 1:
        raise ValueError("risk declaration schema_version must be 1")
    controls = declaration.get("controls")
    if not isinstance(controls, Mapping):
        raise ValueError("risk declaration is missing its controls")
    missing = [name for name in REQUIRED_CONTROLS if name not in controls]
    if missing:
        raise ValueError(f"risk declaration does not decide: {sorted(missing)}")
    for name in REQUIRED_CONTROLS:
        stated = str(controls[name]).strip()
        if len(stated) < 8 or any(marker in stated for marker in _PLACEHOLDERS):
            raise ValueError(f"risk declaration for {name} is a placeholder, not a decision")
    rationale = str(declaration.get("rationale", "")).strip()
    if len(rationale) < 40 or any(marker in rationale for marker in _PLACEHOLDERS):
        raise ValueError("risk declaration needs a rationale in the team's own words")


CERTIFICATE_SECTIONS = (
    "Mechanism and lane alignment",
    "Pre-registered regime expectations",
    "Experiment ledger",
    "Falsifiers and ablations",
    "Cost",
    "Risk declaration rationale",
    "Known weaknesses",
)
_TEMPLATE_MARKERS = (
    "REPLACE-ME",
    "REPLACE:",
    "> Template.",
    "must be answered in the team's own words",
)


def verify_certificate(path) -> None:
    """Require every section to exist and to have been written.

    The check is presence and substance, never quality: a thin certificate is a team's own problem,
    an absent one is the tournament's.
    """
    text = __import__("pathlib").Path(path).read_text()
    lowered = text.lower()
    missing = [section for section in CERTIFICATE_SECTIONS if section.lower() not in lowered]
    if missing:
        raise ValueError(f"research certificate is missing sections: {missing}")
    for marker in _TEMPLATE_MARKERS:
        # Case-sensitive, and with the delimiter the template actually uses: prose is allowed to
        # contain the word "replaced".
        if marker in text:
            raise ValueError(
                f"research certificate still contains its template scaffolding: {marker!r}"
            )
    headings = {}
    for section in CERTIFICATE_SECTIONS:
        # Locate the heading, not the first time the word appears. One required section is called
        # "Cost", an ordinary English word that shows up in prose long before its own heading, so
        # a first-substring search measured the wrong span entirely.
        match = re.search(rf"^#+\s*\d*\.?\s*{re.escape(section)}", text, re.MULTILINE | re.I)
        headings[section] = match.start() if match else lowered.index(section.lower())
    for section in CERTIFICATE_SECTIONS:
        start = headings[section]
        following = [
            headings[other] for other in CERTIFICATE_SECTIONS if headings[other] > start
        ]
        end = min(following) if following else len(text)
        body = text[start + len(section) : end].strip().strip("#").strip()
        if len(body) < 120:
            raise ValueError(f"research certificate section is not answered: {section}")
