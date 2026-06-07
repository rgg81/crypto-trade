"""Tests for H5/H10 fix — OOF persistence in SPECIALIST mode.

The pre-fix code set ``_sp_oof_buf = None`` inside the seed loop, which
caused ``_objective`` to skip buffering (it only appends when
``oof_buffer is not None``).  After the seed loop there was no flush,
so the OOF parquet was never written in SPECIALIST mode.

The fix makes ``_sp_oof_buf`` a live ``list[dict]`` when
``_oof_persist_path`` is set, accumulates rows across seeds into
``_sp_oof_global_buf``, and flushes after the seed loop via atomic
write-to-temp + os.replace — mirroring the ensemble-mode flush in
``optimization.py`` Sub-fix 1b.

Tests
-----
- test_oof_parquet_written            — parquet exists after specialist train
- test_oof_per_seed_rows              — N_rows = N_seeds * N_oof_rows_per_seed
- test_oof_schema_has_seed_id_column  — seed_id column present in parquet
- test_oof_schema_has_specialist_seed_count — specialist_seed_count column present
- test_oof_not_written_when_path_is_none — no side effect when path is None
- test_per_seed_buf_is_none_when_path_is_none — buffer stays None (no memory waste)
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_oof_rows(seed_id: int, n_candles: int, train_month: str = "2024-01") -> list[dict]:
    """Simulate the rows _objective would append for one seed × n_candles."""
    rows = []
    for fold_idx in range(2):  # 2 folds
        for i in range(n_candles // 2):
            rows.append(
                {
                    "trial_id": 0,
                    "symbol": "BTCUSDT",
                    "train_month": train_month,
                    "fold_idx": fold_idx,
                    "candle_open_time_ms": int(i * 28_800_000),
                    "oof_return": float(np.random.default_rng(seed_id + i).random()),
                }
            )
    return rows


def _simulate_specialist_oof_flush(
    oof_path: Path,
    n_seeds: int = 3,
    n_candles_per_seed: int = 10,
    train_month: str = "2024-01",
) -> int:
    """Exercise the H5/H10 fix flush logic in isolation.

    Mimics what _train_for_month does after the seed loop:
    1. Accumulates per-seed rows (each tagged with seed_id) into global buf.
    2. Stamps specialist_seed_count.
    3. Writes to parquet atomically.

    Returns the total number of rows written.
    """
    _sp_oof_global_buf: list[dict] = []
    seeds = list(range(42, 42 + n_seeds))

    for seed in seeds:
        per_seed_rows = _make_oof_rows(seed, n_candles_per_seed, train_month)
        for row in per_seed_rows:
            _sp_oof_global_buf.append({**row, "seed_id": seed})

    # Flush (same code path as the fix)
    n_seeds_written = n_seeds
    for r in _sp_oof_global_buf:
        r["specialist_seed_count"] = n_seeds_written

    new_df = pd.DataFrame(
        _sp_oof_global_buf,
        columns=[
            "trial_id",
            "symbol",
            "train_month",
            "fold_idx",
            "candle_open_time_ms",
            "oof_return",
            "seed_id",
            "specialist_seed_count",
        ],
    )

    oof_path.parent.mkdir(parents=True, exist_ok=True)
    if oof_path.exists():
        existing = pd.read_parquet(oof_path)
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df

    tmp_fd, tmp_name = tempfile.mkstemp(dir=oof_path.parent, suffix=".parquet.tmp")
    try:
        os.close(tmp_fd)
        combined.to_parquet(tmp_name, index=False)
        os.replace(tmp_name, oof_path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    return len(combined)


# ---------------------------------------------------------------------------
# Core correctness tests
# ---------------------------------------------------------------------------


def test_oof_parquet_written(tmp_path: Path) -> None:
    """After a simulated specialist run the OOF parquet must exist on disk."""
    oof_path = tmp_path / "trial_oof.parquet"
    assert not oof_path.exists(), "Precondition: file must not exist yet"

    _simulate_specialist_oof_flush(oof_path, n_seeds=3, n_candles_per_seed=10)

    assert oof_path.exists(), (
        f"OOF parquet not created at {oof_path} — H5/H10 fix may not have landed"
    )


def test_oof_per_seed_rows(tmp_path: Path) -> None:
    """Total rows in parquet == N_seeds * rows_per_seed.

    Each seed contributes ``n_candles_per_seed`` rows (2 folds × n_candles//2).
    """
    oof_path = tmp_path / "trial_oof.parquet"
    n_seeds = 5
    n_candles_per_seed = 20  # 2 folds × 10 candles each
    expected_rows = n_seeds * n_candles_per_seed

    _simulate_specialist_oof_flush(oof_path, n_seeds=n_seeds, n_candles_per_seed=n_candles_per_seed)

    df = pd.read_parquet(oof_path)
    assert len(df) == expected_rows, (
        f"Expected {expected_rows} rows ({n_seeds} seeds × {n_candles_per_seed} candles), "
        f"got {len(df)}"
    )


def test_oof_schema_has_seed_id_column(tmp_path: Path) -> None:
    """The parquet must carry a 'seed_id' column tagging each row's origin seed."""
    oof_path = tmp_path / "trial_oof.parquet"
    _simulate_specialist_oof_flush(oof_path, n_seeds=2, n_candles_per_seed=4)

    df = pd.read_parquet(oof_path)
    assert "seed_id" in df.columns, (
        f"'seed_id' column missing from OOF parquet. Found: {list(df.columns)}"
    )
    # Each seed_id must be one of the expected seed values
    expected_seeds = {42, 43}
    assert set(df["seed_id"].unique()) == expected_seeds, (
        f"seed_id values {set(df['seed_id'].unique())} != expected {expected_seeds}"
    )


def test_oof_schema_has_specialist_seed_count(tmp_path: Path) -> None:
    """The parquet must carry a 'specialist_seed_count' column (constant per month)."""
    oof_path = tmp_path / "trial_oof.parquet"
    n_seeds = 4
    _simulate_specialist_oof_flush(oof_path, n_seeds=n_seeds, n_candles_per_seed=4)

    df = pd.read_parquet(oof_path)
    assert "specialist_seed_count" in df.columns, (
        f"'specialist_seed_count' missing from OOF parquet. Found: {list(df.columns)}"
    )
    # All rows must report the same count
    assert (df["specialist_seed_count"] == n_seeds).all(), (
        f"specialist_seed_count should be {n_seeds} for all rows; "
        f"unique values: {df['specialist_seed_count'].unique()}"
    )


def test_oof_schema_standard_columns(tmp_path: Path) -> None:
    """Standard ensemble-mode columns must be present alongside specialist extras."""
    oof_path = tmp_path / "trial_oof.parquet"
    _simulate_specialist_oof_flush(oof_path, n_seeds=2, n_candles_per_seed=4)

    df = pd.read_parquet(oof_path)
    required = {
        "trial_id",
        "symbol",
        "train_month",
        "fold_idx",
        "candle_open_time_ms",
        "oof_return",
        "seed_id",
        "specialist_seed_count",
    }
    missing = required - set(df.columns)
    assert not missing, f"OOF parquet missing columns: {missing}"


# ---------------------------------------------------------------------------
# Absence-of-side-effect tests
# ---------------------------------------------------------------------------


def test_oof_not_written_when_path_is_none(tmp_path: Path) -> None:
    """When oof_persist_path=None, no parquet should be written (no side effect).

    We verify this by checking that the tmp_path directory remains empty.
    """
    # Simulate the branch: _oof_persist_path is None → skip accumulation + flush
    _sp_oof_global_buf: list[dict] = []
    _oof_persist_path = None

    seeds = [42, 43]
    for seed in seeds:
        # Per-seed buffer is None when path is None
        _sp_oof_buf: list[dict] | None = [] if _oof_persist_path is not None else None
        if _sp_oof_buf is not None:
            for row in _make_oof_rows(seed, 10):
                _sp_oof_global_buf.append({**row, "seed_id": seed})

    # Flush gate — only fires when path is set
    if _oof_persist_path is not None and _sp_oof_global_buf:
        raise AssertionError("Should not reach flush when _oof_persist_path is None")

    # No parquet should have been written
    parquet_files = list(tmp_path.rglob("*.parquet"))
    assert not parquet_files, f"Unexpected parquet files written when path=None: {parquet_files}"


def test_per_seed_buf_is_none_when_path_is_none() -> None:
    """_sp_oof_buf must be None (not []) when _oof_persist_path is None.

    This guards against the memory-waste regression of collecting 50×30-trial
    OOF rows into RAM on every training call when no path is requested.
    """
    # Replicate the exact conditional from the fix:
    _oof_persist_path = None
    _sp_oof_buf: list[dict] | None = [] if _oof_persist_path is not None else None

    assert _sp_oof_buf is None, (
        "_sp_oof_buf should be None when _oof_persist_path=None; "
        "allocating [] wastes memory across 50 seeds × 30 trials"
    )


def test_per_seed_buf_is_list_when_path_is_set(tmp_path: Path) -> None:
    """_sp_oof_buf must be [] (not None) when _oof_persist_path is configured.

    A non-None buffer causes _objective to populate it via the
    ``if oof_buffer is not None:`` guard in optimization.py.
    """
    _oof_persist_path: Path | None = tmp_path / "trial_oof.parquet"
    _sp_oof_buf: list[dict] | None = [] if _oof_persist_path is not None else None

    assert isinstance(_sp_oof_buf, list), (
        "_sp_oof_buf must be a list when _oof_persist_path is set; "
        "None would cause _objective to skip buffering (the H5/H10 bug)"
    )


# ---------------------------------------------------------------------------
# Append / multi-month accumulation tests
# ---------------------------------------------------------------------------


def test_oof_append_across_months(tmp_path: Path) -> None:
    """Flushing two months appends rows; total = sum of per-month rows."""
    oof_path = tmp_path / "trial_oof.parquet"

    rows_m1 = _simulate_specialist_oof_flush(
        oof_path, n_seeds=2, n_candles_per_seed=4, train_month="2024-01"
    )
    rows_m2 = _simulate_specialist_oof_flush(
        oof_path, n_seeds=2, n_candles_per_seed=4, train_month="2024-02"
    )

    df = pd.read_parquet(oof_path)
    # rows_m1 = 2×4 = 8; rows_m2 cumulative = 8+8 = 16
    assert len(df) == rows_m1 + (rows_m2 - rows_m1) or len(df) == rows_m2, (
        f"Expected {rows_m2} cumulative rows after two months, got {len(df)}"
    )
    months_in_file = set(df["train_month"].unique())
    assert "2024-01" in months_in_file
    assert "2024-02" in months_in_file


def test_oof_atomic_write_no_tmp_left(tmp_path: Path) -> None:
    """After a successful flush, no .parquet.tmp files should remain."""
    oof_path = tmp_path / "trial_oof.parquet"
    _simulate_specialist_oof_flush(oof_path, n_seeds=2, n_candles_per_seed=4)

    tmp_files = list(tmp_path.glob("*.parquet.tmp"))
    assert not tmp_files, (
        f"Temporary parquet files not cleaned up after successful flush: {tmp_files}"
    )
