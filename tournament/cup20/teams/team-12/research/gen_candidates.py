"""Materialise each candidate directory from the template by rewriting module-level constants."""
from __future__ import annotations
import re, shutil, sys
from pathlib import Path

ROOT = Path("tournament/cup20/teams/team-12/candidates")
TPL = Path("tournament/cup20/teams/team-12/research/_template")

VARIANTS = {
    "mse-01": {},
    "abl-baseline-ew": {"BASELINE_LONG_ONLY": 1},
    "abl-sleeve-carry": {"USE_TREND": 0, "USE_LOWRISK": 0, "USE_FLOW": 0},
    "abl-sleeve-trend": {"USE_CARRY": 0, "USE_LOWRISK": 0, "USE_FLOW": 0},
    "abl-sleeve-lowrisk": {"USE_CARRY": 0, "USE_TREND": 0, "USE_FLOW": 0},
    "abl-sleeve-flow": {"USE_CARRY": 0, "USE_TREND": 0, "USE_LOWRISK": 0},
    "abl-equal-notional": {"EQUAL_NOTIONAL": 1},
}

def render(overrides: dict[str, int]) -> str:
    text = (TPL / "strategy.py").read_text()
    for name, value in overrides.items():
        pattern = rf"^{name} = -?\d+"
        new, count = re.subn(pattern, f"{name} = {value}", text, flags=re.M)
        if count != 1:
            raise SystemExit(f"constant {name} matched {count} times")
        text = new
    return text

def main(only=None) -> None:
    for name, overrides in VARIANTS.items():
        if only and name != only:
            continue
        target = ROOT / name
        target.mkdir(parents=True, exist_ok=True)
        (target / "strategy.py").write_text(render(overrides))
        shutil.copy(TPL / "risk_policy.json", target / "risk_policy.json")
        print("wrote", target, overrides)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
