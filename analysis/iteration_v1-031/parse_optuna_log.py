"""Parse logs/v1_iter031.log → structured Optuna trial parquet.

The /031 runner did not persist `data/v1_iter_v1-031_optuna_trials.parquet`,
which Critic Phase 7.5 BLOCK-PENDING-FIX requires for V1 (cross-seed Sharpe
std/mean) and V2 (per-cell best-param Spearman) validations.

Log structure (state machine):

  MODEL A (BTC/ETH): ...                       ← sets MODEL=A
  ...
  [lgbm] === Training for 2022-01 ===          ← sets MONTH=2022-01
  ...
    [ensemble 1/5] seed=42                     ← sets SEED=42
  [I YYYY-MM-DD HH:MM:SS,fff] A new study ...  ← new Optuna study (per seed)
  [I YYYY-MM-DD HH:MM:SS,fff] Trial X finished with value: SR and parameters: {...}

Expected total rows: 4 models × ~53 months × 5 seeds × 50 trials ≈ 51,250
(Model E has 46 months due to DOT data start; A/C/D 53 each.)
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = REPO_ROOT / "logs" / "v1_iter031.log"
OUTPUT_PARQUET = REPO_ROOT / "data" / "v1_iter_v1-031_optuna_trials.parquet"

# Regex patterns
MODEL_RE = re.compile(r"^MODEL ([A-Z]) \(")
MONTH_RE = re.compile(r"^\[lgbm\] === Training for (\d{4}-\d{2}) ===")
SEED_RE = re.compile(r"^\s+\[ensemble (\d+)/\d+\] seed=(\d+)")
TRIAL_RE = re.compile(
    r"^\[I [^\]]+\] Trial (\d+) finished with value: ([0-9eE.\-+nan]+) and parameters: (\{[^}]+\})"
)


def parse_log(log_path: Path) -> pd.DataFrame:
    """Stream-parse log; emit one row per Trial X finished line."""
    rows: list[dict] = []
    current_model = None
    current_month = None
    current_seed = None

    with log_path.open("r") as fh:
        for line in fh:
            # MODEL header (column 1, no leading whitespace)
            m = MODEL_RE.match(line)
            if m:
                current_model = m.group(1)
                current_month = None  # reset on model change
                current_seed = None
                continue

            # Training-month header
            m = MONTH_RE.match(line)
            if m:
                current_month = m.group(1)
                current_seed = None  # reset on month change
                continue

            # Ensemble seed marker
            m = SEED_RE.match(line)
            if m:
                current_seed = int(m.group(2))
                continue

            # Trial result
            m = TRIAL_RE.match(line)
            if m:
                trial_num = int(m.group(1))
                sharpe_str = m.group(2)
                params_str = m.group(3)
                try:
                    sharpe = float(sharpe_str)
                except ValueError:
                    sharpe = float("nan")
                try:
                    params = ast.literal_eval(params_str)
                except (ValueError, SyntaxError):
                    params = {}

                rows.append(
                    {
                        "model": current_model,
                        "month": current_month,
                        "inner_seed": current_seed,
                        "trial_number": trial_num,
                        "sharpe": sharpe,
                        "confidence_threshold": params.get("confidence_threshold"),
                        "training_days": params.get("training_days"),
                        "n_estimators": params.get("n_estimators"),
                        "max_depth": params.get("max_depth"),
                        "num_leaves": params.get("num_leaves"),
                        "learning_rate": params.get("learning_rate"),
                        "min_child_samples": params.get("min_child_samples"),
                        "reg_alpha": params.get("reg_alpha"),
                        "reg_lambda": params.get("reg_lambda"),
                    }
                )

    df = pd.DataFrame(rows)
    return df


def main() -> None:
    print(f"[parse_optuna_log] Reading {LOG_PATH}")
    df = parse_log(LOG_PATH)
    print(f"[parse_optuna_log] Parsed {len(df):,} trial rows")

    # Sanity stats
    print("\n[parse_optuna_log] Trials per model:")
    print(df.groupby("model").size().to_string())
    print("\n[parse_optuna_log] Models × months tracked:")
    print(df.groupby(["model"])["month"].nunique().to_string())
    print("\n[parse_optuna_log] Seeds per (model, month) cell (median, min, max):")
    seeds_per_cell = df.groupby(["model", "month"])["inner_seed"].nunique()
    print(f"  median={seeds_per_cell.median():.1f} min={seeds_per_cell.min()} max={seeds_per_cell.max()}")
    print("\n[parse_optuna_log] Trials per (model, month, seed) cell (median, min, max):")
    trials_per_cms = df.groupby(["model", "month", "inner_seed"]).size()
    print(f"  median={trials_per_cms.median():.1f} min={trials_per_cms.min()} max={trials_per_cms.max()}")

    # Coverage check
    expected = (53 + 53 + 53 + 46) * 5 * 50
    print(f"\n[parse_optuna_log] Expected ~{expected:,} (4 models × months × 5 seeds × 50 trials)")
    print(f"[parse_optuna_log] Actual  {len(df):,} (diff {len(df) - expected:+,})")

    # NaN check on hyperparams
    nans = df[["num_leaves", "learning_rate", "min_child_samples"]].isna().any(axis=1).sum()
    print(f"[parse_optuna_log] Rows with missing hyperparams: {nans}")

    OUTPUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PARQUET, index=False)
    print(f"\n[parse_optuna_log] Wrote {OUTPUT_PARQUET}")


if __name__ == "__main__":
    main()
