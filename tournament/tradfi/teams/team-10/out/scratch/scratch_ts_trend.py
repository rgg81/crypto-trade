"""team-10 scratch runner — t10-ts-trend-v1 experiment program.

Usage (from worktree root):
    uv run python tournament/tradfi/teams/team-10/scratch_ts_trend.py exp-003 exp-004 ...

Discipline: every exp id passed here MUST already have its pre-registration line in
experiments.jsonl (appended BEFORE this script is run). Signals are built from
te.team_view(pn) ONLY; pn['ret_fwd'] is never touched in signal construction — the full pn
is passed exclusively to te.run_is for scoring.
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "analysis/portfolio/tradfi")
from tournament import engine as te  # noqa: E402

TEAM_DIR = Path("tournament/tradfi/teams/team-10")
RESULTS = TEAM_DIR / "out" / "exp_results.json"

# ------------------------------------------------------------------ config registry -------------
# Fixed (pre-registered, never tuned): sigma = EWMstd(span=63, min_periods=42) of daily
# simple returns, floored at 0.004/day; inverse-vol sizing; NaN = flat.
CONFIGS = {
    # Stage A — horizon scan, sign transform, no smoothing, no skip
    "exp-003": {"Ks": [21], "transform": "sign", "smooth": 0, "skip": 0},
    "exp-004": {"Ks": [63], "transform": "sign", "smooth": 0, "skip": 0},
    "exp-005": {"Ks": [126], "transform": "sign", "smooth": 0, "skip": 0},
    "exp-006": {"Ks": [252], "transform": "sign", "smooth": 0, "skip": 0},
    # Stage B — transform at best-plateau horizons from Stage A (252 best, 63 second)
    "exp-007": {"Ks": [63], "transform": "clip2", "smooth": 0, "skip": 0},
    "exp-008": {"Ks": [63], "transform": "tanh", "smooth": 0, "skip": 0},
    "exp-009": {"Ks": [252], "transform": "clip2", "smooth": 0, "skip": 0},
    "exp-010": {"Ks": [252], "transform": "tanh", "smooth": 0, "skip": 0},
    # Stage C — multi-horizon blend
    "exp-011": {"Ks": [63, 126, 252], "transform": "tanh", "smooth": 0, "skip": 0},
    "exp-012": {"Ks": [63, 126, 252], "transform": "sign", "smooth": 0, "skip": 0},
    # Stage D — weight smoothing on best-so-far (exp-006: K=252 sign)
    "exp-013": {"Ks": [252], "transform": "sign", "smooth": 5, "skip": 0},
    "exp-014": {"Ks": [252], "transform": "sign", "smooth": 10, "skip": 0},
    "exp-015": {"Ks": [252], "transform": "sign", "smooth": 21, "skip": 0},
    # Stage E — skip sensitivity on best-so-far (K=252 sign m=21)
    "exp-016": {"Ks": [252], "transform": "sign", "smooth": 21, "skip": 5},
    # Stage F — plateau neighbors of the leading cell (K=252, sign, m=21)
    "exp-017": {"Ks": [252], "transform": "sign", "smooth": 42, "skip": 0},
    "exp-018": {"Ks": [252], "transform": "tanh", "smooth": 21, "skip": 0},
    "exp-019": {"Ks": [126], "transform": "sign", "smooth": 21, "skip": 0},
    # Stage F cont. — fine-grained horizon flatness around K=252 at the pick's settings
    "exp-020": {"Ks": [189], "transform": "sign", "smooth": 21, "skip": 5},
    "exp-021": {"Ks": [315], "transform": "sign", "smooth": 21, "skip": 5},
    # Stage F cont. — smoothing neighbor at matched skip
    "exp-022": {"Ks": [252], "transform": "sign", "smooth": 10, "skip": 5},
    # Stage F cont. — long-horizon shelf edge
    "exp-023": {"Ks": [378], "transform": "sign", "smooth": 21, "skip": 5},
}


def build_raw(view, cfg):
    """Raw signed weights from team_view panels ONLY (close), per-name own-history."""
    close = view["close"]
    ret = close.pct_change(fill_method=None)
    logp = np.log(close)
    sigma = ret.ewm(span=63, min_periods=42).std().clip(lower=0.004)
    s = cfg.get("skip", 0)
    zs = []
    for K in cfg["Ks"]:
        mom = logp.shift(s) - logp.shift(K)
        zs.append(mom / (sigma * np.sqrt(K - s)))
    z = sum(zs) / len(zs)  # NaN if any component NaN (plain mean)
    t = cfg["transform"]
    if t == "sign":
        tz = np.sign(z)
    elif t == "clip2":
        tz = z.clip(-2.0, 2.0)
    elif t == "tanh":
        tz = np.tanh(z)
    else:
        raise ValueError(f"unknown transform {t!r}")
    w = tz / sigma
    m = cfg.get("smooth", 0)
    if m:
        w = w.fillna(0.0).ewm(span=m, min_periods=1).mean()
    return w


def main(exp_ids):
    pn, aux = te.load_is_panels()
    view = te.team_view(pn)
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    for eid in exp_ids:
        cfg = CONFIGS[eid]
        raw = build_raw(view, cfg)
        _, _, m1 = te.run_is(raw, pn)
        _, _, m2 = te.run_is(raw, pn, cost_mult=2.0)
        results[eid] = {"config": cfg, "metrics_1x": m1.to_dict(), "metrics_2x": m2.to_dict()}
        print(
            f"{eid}: cfg={cfg}\n"
            f"  1x: sharpe={m1.sharpe:+.3f} maxdd={m1.maxdd:+.3f} turn={m1.ann_turnover:.1f} "
            f"long/short={m1.median_names_long:.0f}/{m1.median_names_short:.0f} "
            f"gross={m1.mean_gross:.2f} net={m1.mean_net:+.3f} months={m1.n_months}\n"
            f"  2x: sharpe={m2.sharpe:+.3f} maxdd={m2.maxdd:+.3f}\n"
            f"  regimes 1x: {m1.regime_sharpe}"
        )
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(results, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1:])
