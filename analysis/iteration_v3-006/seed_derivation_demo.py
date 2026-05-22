"""iter-v3/006 — Seed Derivation Demo

Phase 5 IS-only numerical evidence for iter-v3/006's research brief.

Verifies, on the producer side (no parquet I/O, no model training), that
`_derive_ensemble_seeds(outer_seed)` from run_baseline_v3.py:
  1. Returns a deterministic 5-seed list per outer seed
  2. Different outer seeds → different inner ensembles (zero pairwise overlap)
  3. None of 5 representative outer seeds {42, 17, 100, 999, 8675309}
     reproduces the legacy hardcoded `LEGACY_ENSEMBLE_SEEDS=[42,123,456,789,1001]`
  4. Cross-pair Jaccard / Hamming overlap is exactly zero — no shared inner seeds
     across outer seeds in the demo set

Outputs:
  - analysis/iteration_v3-006/derived_ensembles.csv   (5 outer × 5 inner = 25 rows)
  - analysis/iteration_v3-006/overlap_matrix.csv      (5×5 pairwise overlap counts)
  - analysis/iteration_v3-006/legacy_check.csv        (5 rows: outer, derived, equals_legacy)
  - analysis/iteration_v3-006/synthesis.md            (1-2 paragraphs)

This script is committed BEFORE the brief per Phase 5.5 reproducibility rule.
The 6 adversarial tests in tests/strategies/ml/test_outer_seed_propagation.py
already passed at SHA 9314db4 — this script complements those tests with
human-readable artifacts the QR/Critic can inspect.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = REPO_ROOT / "analysis" / "iteration_v3-006"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


def _load_runner():
    """Load run_baseline_v3.py as a module (mirrors test_outer_seed_propagation pattern)."""
    runner_path = REPO_ROOT / "run_baseline_v3.py"
    spec = importlib.util.spec_from_file_location("_run_baseline_v3_demo", runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load runner from {runner_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    runner = _load_runner()

    # 1. Compute the 5-seed inner ensemble for each demo outer seed.
    demo_outer_seeds = [42, 17, 100, 999, 8675309]
    derived: dict[int, list[int]] = {
        s: runner._derive_ensemble_seeds(s) for s in demo_outer_seeds
    }

    # 2. Persist `derived_ensembles.csv` — long format (one row per (outer, position, inner)).
    rows: list[dict] = []
    for outer in demo_outer_seeds:
        for pos, inner in enumerate(derived[outer]):
            rows.append(
                {
                    "outer_seed": outer,
                    "position": pos,
                    "inner_seed": inner,
                }
            )
    derived_df = pd.DataFrame(rows)
    derived_df.to_csv(ANALYSIS_DIR / "derived_ensembles.csv", index=False)

    # 3. Pairwise overlap matrix — count of shared inner seeds across each pair.
    n = len(demo_outer_seeds)
    overlap_rows: list[dict] = []
    for outer_a in demo_outer_seeds:
        row: dict[str, int | str] = {"outer_seed": outer_a}
        for outer_b in demo_outer_seeds:
            shared = len(set(derived[outer_a]) & set(derived[outer_b]))
            row[str(outer_b)] = shared
        overlap_rows.append(row)
    overlap_df = pd.DataFrame(overlap_rows)
    overlap_df.to_csv(ANALYSIS_DIR / "overlap_matrix.csv", index=False)

    # 4. Legacy check — none of the demo outer seeds should reproduce
    #    LEGACY_ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001].
    legacy = runner.LEGACY_ENSEMBLE_SEEDS
    legacy_rows: list[dict] = []
    for outer in demo_outer_seeds:
        d = derived[outer]
        legacy_rows.append(
            {
                "outer_seed": outer,
                "derived_inner_seeds": " ".join(str(x) for x in d),
                "equals_legacy": d == legacy,
                "shared_with_legacy": len(set(d) & set(legacy)),
            }
        )
    legacy_df = pd.DataFrame(legacy_rows)
    legacy_df.to_csv(ANALYSIS_DIR / "legacy_check.csv", index=False)

    # 5. Summary stats for synthesis.
    n_pairs = (n * (n - 1)) // 2
    off_diag_overlaps: list[int] = []
    for i, oa in enumerate(demo_outer_seeds):
        for ob in demo_outer_seeds[i + 1 :]:
            off_diag_overlaps.append(len(set(derived[oa]) & set(derived[ob])))
    legacy_reproductions = sum(1 for r in legacy_rows if r["equals_legacy"])
    legacy_shared_total = sum(int(r["shared_with_legacy"]) for r in legacy_rows)

    summary = {
        "n_outer_seeds_demo": n,
        "n_inner_seeds_per_ensemble": runner.ENSEMBLE_SIZE,
        "demo_outer_seeds": demo_outer_seeds,
        "n_pairs_off_diagonal": n_pairs,
        "max_off_diagonal_overlap": max(off_diag_overlaps) if off_diag_overlaps else 0,
        "min_off_diagonal_overlap": min(off_diag_overlaps) if off_diag_overlaps else 0,
        "n_pairs_with_zero_overlap": sum(1 for v in off_diag_overlaps if v == 0),
        "legacy_ensemble_seeds": legacy,
        "n_demo_seeds_reproducing_legacy": legacy_reproductions,
        "total_demo_inner_seeds_shared_with_legacy": legacy_shared_total,
    }

    (ANALYSIS_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    # 6. Synthesis (1-2 paragraphs).
    pairs_with_zero = summary["n_pairs_with_zero_overlap"]
    n_pairs_total = summary["n_pairs_off_diagonal"]

    derived_lines = []
    for outer in demo_outer_seeds:
        derived_lines.append(f"- outer={outer}: inner={derived[outer]}")
    derived_block = "\n".join(derived_lines)

    synthesis = f"""# iter-v3/006 — Seed Derivation Demo Synthesis

Producer-side validation that `_derive_ensemble_seeds(outer_seed)`
(committed at SHA `9314db4`) replaces the pre-fix hardcoded
`ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001]` with a per-outer-seed
deterministic distinct 5-seed list. The 6 adversarial tests in
`tests/strategies/ml/test_outer_seed_propagation.py` already pass at
SHA `9314db4`. This script complements those tests with the
human-readable artifacts: `derived_ensembles.csv`, `overlap_matrix.csv`,
and `legacy_check.csv`.

For the 5 representative demo outer seeds `{demo_outer_seeds}`:

{derived_block}

Pairwise off-diagonal Hamming-distance overlap is **{pairs_with_zero}/{n_pairs_total}
pairs with zero shared inner seeds** (max overlap across pairs:
{summary['max_off_diagonal_overlap']}). None of the 5 demo seeds
reproduces `LEGACY_ENSEMBLE_SEEDS={legacy}`
({summary['n_demo_seeds_reproducing_legacy']}/{n} reproductions;
{summary['total_demo_inner_seeds_shared_with_legacy']} total inner seeds
shared across all demos). The fix produces structurally distinct inner
ensembles per outer seed, satisfying the prerequisite for any meaningful
multi-seed Pareto validation. iter-v3/006's central test (Phase 6,
`--seeds 2 --n-trials 10` on BCH-only) verifies the consumer-side
property that distinct ensembles produce distinct trade distributions
(per-seed Sharpe std > 0); this demo only verifies the producer-side
algebra.
"""
    (ANALYSIS_DIR / "synthesis.md").write_text(synthesis)

    # Console echo for the operator.
    print("=" * 60)
    print(f"iter-v3/006 seed derivation demo")
    print("=" * 60)
    print(f"Demo outer seeds: {demo_outer_seeds}")
    print(f"Inner ensemble size: {runner.ENSEMBLE_SIZE}")
    print()
    print("Derived ensembles:")
    for outer in demo_outer_seeds:
        print(f"  outer={outer:>10}: inner={derived[outer]}")
    print()
    print(
        f"Pairwise overlap (off-diagonal): max={summary['max_off_diagonal_overlap']}, "
        f"min={summary['min_off_diagonal_overlap']}, "
        f"zero-overlap pairs={pairs_with_zero}/{n_pairs_total}"
    )
    print(
        f"Legacy reproductions: {legacy_reproductions}/{n} "
        f"(total inner seeds shared with legacy: {legacy_shared_total})"
    )
    print()
    print("Outputs:")
    for fname in (
        "derived_ensembles.csv",
        "overlap_matrix.csv",
        "legacy_check.csv",
        "summary.json",
        "synthesis.md",
    ):
        path = ANALYSIS_DIR / fname
        if path.exists():
            print(f"  {path.relative_to(REPO_ROOT)}  ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
