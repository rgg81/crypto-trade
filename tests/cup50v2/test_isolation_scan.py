"""What the clean-room scan refuses, and what it must not refuse.

CUP-50's scan blocked path parts starting `cup20` or `top40` and never learned about `cup50`, so a
v2 team could have imported the previous winner's source. Widening it introduced the opposite
hazard: this namespace's own package name contains the string the scan is hunting for.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from crypto_trade.cup50v2.isolation import (
    IS_END_LITERAL,
    PRIOR_NAMESPACE,
    scan_research_root,
)


def _workspace(tmp_path: Path, source: str, name: str = "strategy.py") -> Path:
    root = tmp_path / "team-01"
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(source)
    return root


CLEAN = '''"""A lane source that behaves."""

from crypto_trade.cup50v2.protocol import DecisionContextV2, TargetStrategyV2
from crypto_trade.cup50v2 import toolkit


class Lane:
    lookback_bars = 189

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        panel = toolkit.close_panel(context)
        return {} if panel.empty else {}


def build_strategy() -> TargetStrategyV2:
    return Lane()
'''


def test_a_clean_lane_source_passes(tmp_path: Path) -> None:
    assert scan_research_root(_workspace(tmp_path, CLEAN)) == ()


@pytest.mark.parametrize(
    "text",
    [
        "crypto_trade.cup50v2",
        "from crypto_trade.cup50v2 import toolkit",
        "cup50v2_desk",
        "reports-cup50v2",
    ],
)
def test_this_tournaments_own_namespace_is_never_flagged(text: str) -> None:
    """The digits are matched possessively; otherwise the engine backtracks to `cup5`,
    the lookahead sees `0v2` instead of `v2`, and every lane source is rejected."""
    assert PRIOR_NAMESPACE.search(text) is None, text


@pytest.mark.parametrize(
    "text", ["cup50", "cup20", "top40", "top40-v2", "reports-cup20", "paper-cup50"]
)
def test_every_earlier_edition_is_flagged(text: str) -> None:
    assert PRIOR_NAMESPACE.search(text) is not None, text


def test_a_source_importing_an_earlier_edition_is_refused(tmp_path: Path) -> None:
    source = CLEAN.replace(
        "from crypto_trade.cup50v2 import toolkit",
        "from crypto_trade.cup50.protocol import DecisionContextV2 as Old",
    )
    violations = scan_research_root(_workspace(tmp_path, source))
    assert any(item.startswith("prior-namespace:") for item in violations), violations


def test_a_post_cutoff_date_literal_is_refused(tmp_path: Path) -> None:
    """Evidence the source was written knowing what came next; intent is not the test."""
    source = CLEAN.replace("lookback_bars = 189", "lookback_bars = 189  # tuned to 2025-03-01")
    violations = scan_research_root(_workspace(tmp_path, source))
    assert any("post-cutoff-date" in item and "2025-03-01" in item for item in violations)


def test_the_cutoff_instant_itself_is_not_post_cutoff(tmp_path: Path) -> None:
    """The in-sample end is printed in the charter, the config and every packet handed to a team.

    Flagging it would mean a team had to redact organizer output to keep its workspace clean.
    """
    source = CLEAN.replace(
        "lookback_bars = 189", f"lookback_bars = 189  # window ends {IS_END_LITERAL}"
    )
    assert scan_research_root(_workspace(tmp_path, source)) == ()


def test_an_in_sample_date_literal_is_allowed(tmp_path: Path) -> None:
    source = CLEAN.replace("lookback_bars = 189", "lookback_bars = 189  # since 2021-03-15")
    assert scan_research_root(_workspace(tmp_path, source)) == ()


@pytest.mark.parametrize(
    "part",
    ["private", "sealed", "acquisition", "reports-cup50", "paper-cup50", "diary", "analysis"],
)
def test_organizer_only_surfaces_are_refused_by_path(tmp_path: Path, part: str) -> None:
    root = tmp_path / "team-01"
    (root / part).mkdir(parents=True)
    (root / part / "note.txt").write_text("x")
    assert scan_research_root(root), part


def test_a_cached_frame_or_oversized_file_is_refused(tmp_path: Path) -> None:
    root = _workspace(tmp_path, CLEAN)
    (root / "panel.parquet").write_bytes(b"0")
    (root / "big.py").write_text("# " + "x" * 2_000_001)
    violations = scan_research_root(root)
    assert "panel.parquet" in violations
    assert "big.py" in violations


def test_a_forbidden_import_or_call_is_refused(tmp_path: Path) -> None:
    source = CLEAN.replace(
        "from crypto_trade.cup50v2 import toolkit",
        "import os\nfrom crypto_trade.cup50v2 import toolkit",
    ).replace("panel = toolkit.close_panel(context)", "panel = open('/etc/passwd')")
    violations = scan_research_root(_workspace(tmp_path, source))
    assert any("forbidden-import" in item for item in violations), violations
    assert any("forbidden-call" in item for item in violations), violations


def test_every_shipped_lane_seed_passes_the_scan(tmp_path: Path) -> None:
    """The organizer's own seeds are the first thing the gate is pointed at."""
    import shutil

    for seed in sorted(Path("tournament/cup50v2/seeds").glob("team-*")):
        root = tmp_path / seed.name
        root.mkdir()
        shutil.copyfile(seed / "strategy.py", root / "strategy.py")
        shutil.copyfile(seed / "parameters.json", root / "parameters.json")
        assert scan_research_root(root) == (), seed.name
