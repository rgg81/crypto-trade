"""The research certificate: present, answered, and in the team's own words."""

from __future__ import annotations

from pathlib import Path

import pytest

from crypto_trade.cup50v2.qualification import CERTIFICATE_SECTIONS, verify_certificate

ANSWER = (
    "This section is answered at length in the team's own words, describing what was done, what "
    "was expected, what actually happened, and what that implies for the candidate being frozen."
)


def _certificate(tmp_path: Path, *, omit: str | None = None, thin: str | None = None) -> Path:
    lines = ["# team-01 research certificate", ""]
    for section in CERTIFICATE_SECTIONS:
        if section == omit:
            continue
        lines.append(f"## {section}")
        lines.append("too short" if section == thin else ANSWER)
        lines.append("")
    path = tmp_path / "RESEARCH-CERTIFICATE.md"
    path.write_text("\n".join(lines))
    return path


def test_a_complete_certificate_is_accepted(tmp_path: Path) -> None:
    verify_certificate(_certificate(tmp_path))


@pytest.mark.parametrize("section", ["Falsifiers and ablations", "Known weaknesses"])
def test_a_missing_section_is_refused(tmp_path: Path, section: str) -> None:
    with pytest.raises(ValueError, match="missing sections"):
        verify_certificate(_certificate(tmp_path, omit=section))


def test_an_unanswered_section_is_refused(tmp_path: Path) -> None:
    """Presence is not an answer; a heading with nothing under it is an omission with a title."""
    with pytest.raises(ValueError, match="not answered"):
        verify_certificate(_certificate(tmp_path, thin="Cost"))


def test_the_shipped_template_cannot_be_submitted_unedited() -> None:
    with pytest.raises(ValueError, match="template scaffolding|not answered"):
        verify_certificate(Path("tournament/cup50v2/seeds/team-01/RESEARCH-CERTIFICATE.md"))
