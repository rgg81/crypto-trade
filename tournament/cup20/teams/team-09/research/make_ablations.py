"""Generate the ablation candidates from the frozen nominee source.

Each ablation is the nominee's ``strategy.py`` with EXACTLY ONE thing changed, and the change is
stated at the top of the generated file. They exist to answer "is my lane's mechanism carrying this
book, or is something generic carrying it", which is the question amendment A6 made affordable:
journaled ``--kind ablation`` they are exempt from the multiplicity charge, and in exchange none of
them can ever be nominated.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAND = HERE.parent / "candidates"
NOMINEE = CAND / "print-size-flow"

BASE = (NOMINEE / "strategy.py").read_text()

# ------------------------------------------------------------------ the single-change edits
SCORE_LINE = "            raw = _ranks(block[:, 0]) + _ranks(block[:, 1])"
RESID_BLOCK = """            residual = _residualise(
                raw, [_ranks(block[:, 2]), _ranks(block[:, 3]), _ranks(block[:, 4])]
            )"""

IMBSML_BLOCK = """        # IMBSML -- imbalance over the below-norm-print bars only, USDT weighted within them.
        small = usable & (shock <= 0.0)
        if not small.any():
            return None
        small_quote = bar_quote[small].sum()
        if small_quote <= 0.0:
            return None
        imbsml = float((bar_imb[small] * bar_quote[small]).sum() / small_quote)"""

IMBALL_BLOCK = """        # ABLATION: the plain USDT-weighted taker imbalance over the whole window -- the
        # transparent baseline, i.e. the obvious reading of this lane, with no print-size
        # conditioning of any kind.
        imbsml = float((bar_imb[usable] * bar_quote[usable]).sum() / denom)"""

IMBEQ_BLOCK = """        # ABLATION: the EQUAL-BAR-WEIGHT mean imbalance over the whole window. This removes the
        # dominance of the highest-volume bars -- the other thing restricting to small-print bars
        # does -- WITHOUT using print size to choose which bars count. The gap between this and the
        # nominee is the part of the result that is genuinely about print size.
        imbsml = float(bar_imb[usable].mean())"""

ABLATIONS: dict[str, dict] = {
    "ablation-imbalance-baseline": {
        "what": "the transparent baseline: plain USDT-weighted taker imbalance, no conditioning",
        "edits": [
            (IMBSML_BLOCK, IMBALL_BLOCK),
            (SCORE_LINE, "            raw = _ranks(block[:, 1])"),
        ],
    },
    "ablation-equal-bar-weight": {
        "what": "IMBSML replaced by an equal-bar-weight imbalance -- de-weights big bars without "
        "using print size",
        "edits": [(IMBSML_BLOCK, IMBEQ_BLOCK)],
    },
    "ablation-covats-only": {
        "what": "the print-size/direction covariance alone; the conditioned imbalance removed",
        "edits": [(SCORE_LINE, "            raw = _ranks(block[:, 0])")],
    },
    "ablation-imbsml-only": {
        "what": "the small-print imbalance alone; the covariance removed",
        "edits": [(SCORE_LINE, "            raw = _ranks(block[:, 1])")],
    },
    "ablation-controls-off": {
        "what": "controls off: no residualisation against the price move, print-size class or "
        "turnover class",
        "edits": [(RESID_BLOCK, "            residual = raw - raw.mean()")],
    },
    "ablation-single-phase": {
        "what": "one cadence-HOLD_BARS sleeve at a single phase instead of HOLD_BARS overlapping "
        "sleeves -- the same signal and the same holding horizon, exposed to phase",
        "edits": [
            (
                "        self._sleeves.append(dict(self._last))",
                """        # ABLATION: hold ONE sleeve, refreshed every HOLD_BARS boundaries at phase 0,
        # instead of averaging HOLD_BARS overlapping sleeves. Same signal, same holding horizon,
        # but now the book depends on which offset it happens to sit on.
        if self._tick % HOLD_BARS == 0:
            self._single = dict(self._last)
        self._tick += 1
        self._sleeves.clear()
        self._sleeves.append(dict(self._single))""",
            ),
            (
                "        self._last: dict[str, float] = {}",
                "        self._last: dict[str, float] = {}\n"
                "        self._single: dict[str, float] = {}\n"
                "        self._tick = 0",
            ),
        ],
    },
}

HEADER = '''"""ABLATION -- {what}.

Generated from the team-09 nominee ``print-size-flow`` by changing exactly one thing. Journaled
``--kind ablation`` under charter amendment A6: it is a control, it is exempt from the multiplicity
charge, and it can never be nominated. Read the nominee's own module docstring for what the
mechanism is; everything below is identical to it except the change named above.
"""

'''


def main() -> None:
    for name, spec in ABLATIONS.items():
        source = BASE
        for old, new in spec["edits"]:
            if old not in source:
                raise SystemExit(f"{name}: anchor not found:\n{old[:120]}")
            source = source.replace(old, new, 1)
        # Replace the nominee's docstring with the ablation banner, keeping the code identical.
        body = source.split('"""', 2)[2]
        out = CAND / name
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy.py").write_text(HEADER.format(what=spec["what"]) + body.lstrip("\n"))
        shutil.copy(NOMINEE / "risk_policy.json", out / "risk_policy.json")
        (out / "README.md").write_text(
            f"# {name}\n\n**ABLATION -- cannot be nominated (charter A6).**\n\n"
            f"{spec['what'].capitalize()}.\n\n"
            "Identical to the team-09 nominee `print-size-flow` in every other respect: same\n"
            "universe, same book shape, same parameters, same risk policy, same seed. It exists so\n"
            "the certificate can say what this lane's mechanism contributes rather than assert it.\n"
        )
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
