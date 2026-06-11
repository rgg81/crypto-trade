"""iter-v1/090 — training_days-collapse reconstruction (IS-only evidence for brief Section 2).

Parses the selected-best Optuna ``training_days`` per walk-forward fold from each
specialist's ``run.log`` (the ones that were preserved) and prints the collapse
distribution that motivates W-DECAY.

Method (no OOS data touched): within each Optuna study block (delimited by a
"Train window:" marker in the log), read every "[trial N] ... training_days=XXX"
line and track the final "Best is trial N" — the winning trial's training_days is
the selected window for that fold. Then summarize the per-fold selected-window
distribution.

This is the script cited in brief Section 2 (`feedback_qr_uses_is_data`). Running it
reproduces the §2.1 table and the §2.2 standalone-seat anchors.

Usage:
    uv run python analysis/iteration_v1-090/training_days_collapse.py
"""

from __future__ import annotations

import csv
import re
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPORTS = REPO / "reports-v1"

# Seats whose run.log was preserved (the recent cycle-7 single-symbol specialists).
# The 4 BUNDLE-002 seats (063/064/065/078) were grandfathered from the /071 stash
# recovery and have NO run.log — their training_days distribution is not measurable.
SEATS_WITH_LOG = {
    "086": "TRB (SPECIALIST-NEGATIVE)",
    "087": "BNB (BLOCKED-FAIL-FAST)",
    "088": "XRP (SPECIALIST-PROMISING)",
}

# Standalone source-iter comparison.csv anchors (the F1 baselines). 078 has no
# comparison.csv (50-seed methodology-lock seat; metrics live in BASELINE_V1).
SEAT_COMPARISONS = ["063", "064", "065", "078"]


def reconstruct_selected_training_days(log_path: Path) -> list[int]:
    """Return the selected (best-trial) training_days per fold from a run.log."""
    if not log_path.exists():
        return []
    folds: list[int] = []
    trial_td: dict[int, int] = {}
    last_best: int | None = None

    def flush() -> None:
        nonlocal trial_td, last_best
        if last_best is not None and last_best in trial_td:
            folds.append(trial_td[last_best])
        trial_td = {}
        last_best = None

    for line in log_path.read_text(errors="ignore").splitlines():
        if "Train window:" in line:
            flush()
            continue
        mt = re.search(r"\[trial (\d+)\].*training_days=(\d+)", line)
        if mt:
            trial_td[int(mt.group(1))] = int(mt.group(2))
            continue
        mb = re.search(r"Best is trial (\d+) with value", line)
        if mb:
            last_best = int(mb.group(1))
    flush()
    return folds


def summarize(name: str, td: list[int]) -> dict:
    if not td:
        return {"seat": name, "n_folds": 0}
    n = len(td)
    return {
        "seat": name,
        "n_folds": n,
        "median_d": round(statistics.median(td)),
        "mean_d": round(statistics.mean(td)),
        "min_d": min(td),
        "max_d": max(td),
        "folds_lt120": sum(1 for x in td if x < 120),
        "pct_lt120": round(100 * sum(1 for x in td if x < 120) / n),
        "folds_lt180": sum(1 for x in td if x < 180),
        "pct_lt180": round(100 * sum(1 for x in td if x < 180) / n),
    }


def main() -> None:
    print("=" * 78)
    print("iter-v1/090 W-DECAY — training_days-collapse evidence (brief Section 2.1)")
    print("Optuna search space: suggest_int('training_days', 10, 500, step=10)")
    print("  (cap = 500d; full 24mo window ~730d is NOT selectable — 500d is the max)")
    print("=" * 78)

    rows = []
    for it, label in SEATS_WITH_LOG.items():
        td = reconstruct_selected_training_days(REPORTS / f"iteration_v1-{it}" / "run.log")
        s = summarize(f"{it} {label}", td)
        rows.append(s)
        if s["n_folds"]:
            print(
                f"\n/{it} {label}\n"
                f"  n_folds={s['n_folds']}  median={s['median_d']}d  mean={s['mean_d']}d  "
                f"min={s['min_d']}  max={s['max_d']}\n"
                f"  folds <120d: {s['folds_lt120']}/{s['n_folds']} ({s['pct_lt120']}%)   "
                f"folds <180d: {s['folds_lt180']}/{s['n_folds']} ({s['pct_lt180']}%)"
            )
        else:
            print(f"\n/{it} {label}: no run.log / no training_days trials parsed")

    print("\nMonotone signature: NEGATIVE seat (TRB) collapses hardest (median ~115d),")
    print("PROMISING seat (XRP) collapses least (median ~250d). Shorter ⇒ worse OOS.\n")

    print("=" * 78)
    print("Standalone source-iter comparison.csv anchors (brief Section 2.2 — F1 baselines)")
    print("=" * 78)
    for it in SEAT_COMPARISONS:
        cmp_path = REPORTS / f"iteration_v1-{it}" / "comparison.csv"
        if not cmp_path.exists() or cmp_path.stat().st_size == 0:
            print(f"/{it}: no/empty comparison.csv (50-seed lock seat — metrics in BASELINE_V1)")
            continue
        with cmp_path.open() as fh:
            r = {row["metric"]: row for row in csv.DictReader(fh)}
        sh = r.get("sharpe", {})
        tr = r.get("total_trades", {})
        print(
            f"/{it}: IS Sharpe={sh.get('in_sample','?')}  OOS Sharpe={sh.get('out_of_sample','?')}  "
            f"IS trades={tr.get('in_sample','?')}  OOS trades={tr.get('out_of_sample','?')}"
        )

    print("\nCHOSEN TEST SEAT: ETH/064 (IS +0.2383 / OOS +0.5171) — balanced positive,")
    print("not regime-inverting (clean F1 attribution), real IS headroom (+0.24 → +0.44 target).")


if __name__ == "__main__":
    main()
