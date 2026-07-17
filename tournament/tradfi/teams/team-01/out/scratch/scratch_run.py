"""team-01 batch runner: `uv run python tournament/tradfi/teams/team-01/scratch_run.py <exp-id>`.
Each exp-id maps to the pre-registered batch in experiments.jsonl (append BEFORE running).
Results print to stdout and persist to out/<exp-id>_results.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, "analysis/portfolio/tradfi")
sys.path.insert(0, "tournament/tradfi/teams/team-01")

import scratch_common as sc

OUT = Path("tournament/tradfi/teams/team-01/out")

BASE = dict(resid="market", beta_win=252, form=252, skip=21, scaling="ir",
            scheme="rank", halflife=10, mp_frac=0.9)

# Chosen after exp-005/006 plateau reads (updated in place; history in experiments.jsonl).
CHOSEN = dict(BASE, form=252, skip=21, beta_win=63, resid="market+sector", scaling="blend")

BATCHES: dict[str, list[tuple[str, dict]]] = {
    "exp-003": [  # reference: RAW (non-residual) momentum — falsifier evidence for the family
        ("raw-mom form252 skip21 sum", dict(BASE, resid="none", scaling="sum")),
        ("raw-mom form252 skip21 ir", dict(BASE, resid="none", scaling="ir")),
    ],
    "exp-004": [  # family core: market-residual momentum, literature-default params
        ("resid-mom core 252/21 b252 ir", dict(BASE)),
    ],
    "exp-005": [  # formation/skip plateau sweep (single axis)
        (f"form{f} skip{s}", dict(BASE, form=f, skip=s))
        for f in (126, 189, 252) for s in (10, 21)
    ],
    "exp-006": [  # beta-estimation window sweep (single axis, at plateau formation 252/21)
        (f"beta_win{b}", dict(BASE, form=252, skip=21, beta_win=b))
        for b in (63, 126, 252)
    ],
    "exp-007": [  # residualization depth: market-only vs market+sector
        ("resid market", dict(CHOSEN)),
        ("resid market+sector", dict(CHOSEN, resid="market+sector")),
    ],
    "exp-008": [  # signal scaling: idiosyncratic IR vs plain residual sum
        ("scaling ir", dict(CHOSEN)),
        ("scaling sum", dict(CHOSEN, scaling="sum")),
    ],
    "exp-009": [  # ir-vs-sum reconciliation: 50/50 rank blend (within-family combination)
        ("scaling blend", dict(CHOSEN, scaling="blend")),
    ],
    "exp-010": [  # smoothing halflife / turnover-cost frontier (check 1x AND 2x)
        (f"halflife {h}", dict(CHOSEN, halflife=h)) for h in (0, 5, 10, 21)
    ],
    "exp-011": [  # weighting scheme / breadth
        ("rank continuous", dict(CHOSEN)),
        ("quantile q=0.3", dict(CHOSEN, scheme="quantile", q=0.3)),
        ("quantile q=0.2", dict(CHOSEN, scheme="quantile", q=0.2)),
    ],
    "exp-012": [  # eligibility min_periods robustness
        (f"mp_frac {m}", dict(CHOSEN, mp_frac=m)) for m in (0.8, 0.9, 1.0)
    ],
    "exp-013": [  # FINAL spec confirmation (numbers for is_report.md)
        ("FINAL spec", dict(CHOSEN)),
    ],
}


def main(exp_id: str) -> None:
    batch = BATCHES[exp_id]
    results = []
    for label, cfg in batch:
        res = sc.score(cfg, label)
        results.append(res)
        print(sc.brief_line(res), flush=True)
    OUT.mkdir(exist_ok=True)
    (OUT / f"{exp_id}_results.json").write_text(json.dumps(results, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1])
