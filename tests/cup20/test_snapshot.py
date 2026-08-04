import pandas as pd
import pytest

from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start, write_split_snapshots


def _fixture_frames():
    times = pd.date_range("2024-07-25T00:00:00Z", periods=30, freq="8h")
    bars = pd.DataFrame(
        {
            "open_time": list(times) * 2,
            "symbol": ["AUSDT"] * 30 + ["BUSDT"] * 30,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 10.0,
            "quote_volume": 1000.0,
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": list(times) * 2,
            "symbol": ["AUSDT"] * 30 + ["BUSDT"] * 30,
            "funding_rate": 0.0001,
        }
    )
    marks = pd.DataFrame(
        {
            "mark_time": list(times) * 2,
            "symbol": ["AUSDT"] * 30 + ["BUSDT"] * 30,
            "mark_price": 100.0,
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [
                pd.Timestamp("2024-07-29T00:00:00Z"),
                pd.Timestamp("2024-07-29T00:00:00Z"),
                pd.Timestamp("2024-08-05T00:00:00Z"),
            ],
            "symbol": ["AUSDT", "BUSDT", "AUSDT"],
            "liquidity_rank": [1, 2, 1],
            "trailing_quote_volume": [1000.0, 900.0, 1000.0],
        }
    )
    metadata = pd.DataFrame({"symbol": ["AUSDT", "BUSDT"], "contract_type": ["PERPETUAL"] * 2})
    return bars, funding, marks, membership, metadata


def test_sealed_rows_are_absent_from_the_is_snapshot(tmp_path):
    bars, funding, marks, membership, metadata = _fixture_frames()
    is_paths, sealed_paths = write_split_snapshots(
        bars,
        funding,
        marks,
        membership,
        metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_end=pd.Timestamp("2024-08-01T00:00:00Z"),
        sealed_end=pd.Timestamp("2026-08-01T00:00:00Z"),
    )
    is_snapshot = load_snapshot(is_paths.root)
    assert is_snapshot.bars["open_time"].max() < pd.Timestamp("2024-08-01T00:00:00Z")
    assert is_snapshot.funding["funding_time"].max() < pd.Timestamp("2024-08-01T00:00:00Z")
    assert is_snapshot.membership["reconstitution_time"].max() < pd.Timestamp(
        "2024-08-01T00:00:00Z"
    )
    sealed_snapshot = load_snapshot(sealed_paths.root)
    assert sealed_snapshot.bars["open_time"].min() >= pd.Timestamp("2024-08-01T00:00:00Z")


def test_snapshots_have_distinct_manifest_hashes(tmp_path):
    bars, funding, marks, membership, metadata = _fixture_frames()
    is_paths, sealed_paths = write_split_snapshots(
        bars,
        funding,
        marks,
        membership,
        metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_end=pd.Timestamp("2024-08-01T00:00:00Z"),
        sealed_end=pd.Timestamp("2026-08-01T00:00:00Z"),
    )
    assert (
        load_snapshot(is_paths.root).manifest_sha256
        != load_snapshot(sealed_paths.root).manifest_sha256
    )


def test_snapshot_write_is_deterministic(tmp_path):
    bars, funding, marks, membership, metadata = _fixture_frames()
    digests = []
    for name in ("first", "second"):
        is_paths, _ = write_split_snapshots(
            bars,
            funding,
            marks,
            membership,
            metadata,
            is_root=tmp_path / name / "is",
            sealed_root=tmp_path / name / "sealed",
            is_end=pd.Timestamp("2024-08-01T00:00:00Z"),
            sealed_end=pd.Timestamp("2026-08-01T00:00:00Z"),
        )
        digests.append(load_snapshot(is_paths.root).manifest_sha256)
    assert digests[0] == digests[1]


def test_resolve_is_start_is_first_boundary_reaching_target_size():
    membership = pd.DataFrame(
        {
            "reconstitution_time": (
                [pd.Timestamp("2020-07-06T00:00:00Z")] * 19
                + [pd.Timestamp("2020-07-13T00:00:00Z")] * 20
            ),
            "symbol": [f"S{index}" for index in range(19)] + [f"S{index}" for index in range(20)],
            "liquidity_rank": list(range(1, 20)) + list(range(1, 21)),
            "trailing_quote_volume": [1.0] * 39,
        }
    )
    assert resolve_is_start(membership, target_size=20) == pd.Timestamp("2020-07-13T00:00:00Z")


def test_resolve_is_start_raises_when_target_never_reached():
    membership = pd.DataFrame(
        {
            "reconstitution_time": [pd.Timestamp("2020-07-06T00:00:00Z")] * 5,
            "symbol": [f"S{index}" for index in range(5)],
            "liquidity_rank": list(range(1, 6)),
            "trailing_quote_volume": [1.0] * 5,
        }
    )
    with pytest.raises(ValueError):
        resolve_is_start(membership, target_size=20)


def test_write_split_snapshots_rejects_duplicate_time_symbol_rows(tmp_path):
    bars, funding, marks, membership, metadata = _fixture_frames()
    # Duplicate the first row's (open_time, symbol) key. The sort key [column, "symbol"] cannot
    # order these two rows deterministically, so the write must refuse rather than silently pick
    # whichever order the input happened to arrive in.
    bars = pd.concat([bars, bars.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError):
        write_split_snapshots(
            bars,
            funding,
            marks,
            membership,
            metadata,
            is_root=tmp_path / "is",
            sealed_root=tmp_path / "sealed",
            is_end=pd.Timestamp("2024-08-01T00:00:00Z"),
            sealed_end=pd.Timestamp("2026-08-01T00:00:00Z"),
        )


def test_write_split_snapshots_rejects_duplicate_contract_metadata_symbol(tmp_path):
    bars, funding, marks, membership, metadata = _fixture_frames()
    # contract_metadata is timeless and sorts by "symbol" alone, so a duplicated symbol is the
    # same non-total-order hazard as a duplicated (time, symbol) key in the time-keyed datasets.
    metadata = pd.concat([metadata, metadata.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError):
        write_split_snapshots(
            bars,
            funding,
            marks,
            membership,
            metadata,
            is_root=tmp_path / "is",
            sealed_root=tmp_path / "sealed",
            is_end=pd.Timestamp("2024-08-01T00:00:00Z"),
            sealed_end=pd.Timestamp("2026-08-01T00:00:00Z"),
        )


def test_split_is_a_true_partition_of_input_rows(tmp_path):
    """IS + sealed must reconstruct every input row exactly once, not just respect direction.

    The other tests assert the leak *direction* (IS strictly before the cutoff, sealed at or
    after it), which is the property that matters most for blindness. That alone would not catch
    a regression that dropped the boundary row from both snapshots. This test proves the split is
    a true partition: for every time-keyed dataset, the IS and sealed (time, symbol) key sets are
    disjoint and their union is exactly the set of input rows earlier than ``sealed_end`` --
    derived from the fixture itself, not a hardcoded count.
    """
    bars, funding, marks, membership, metadata = _fixture_frames()
    is_end = pd.Timestamp("2024-08-01T00:00:00Z")
    sealed_end = pd.Timestamp("2026-08-01T00:00:00Z")
    is_paths, sealed_paths = write_split_snapshots(
        bars,
        funding,
        marks,
        membership,
        metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_end=is_end,
        sealed_end=sealed_end,
    )
    is_snapshot = load_snapshot(is_paths.root)
    sealed_snapshot = load_snapshot(sealed_paths.root)

    raw_by_dataset = {
        "bars": (bars, "open_time"),
        "funding": (funding, "funding_time"),
        "mark_prices": (marks, "mark_time"),
        "membership": (membership, "reconstitution_time"),
    }
    for name, (raw, column) in raw_by_dataset.items():
        raw_times = pd.to_datetime(raw[column], utc=True)
        # write_split_snapshots places no lower bound on the IS side, so the full range this
        # pair of snapshots claims to cover is everything strictly before sealed_end.
        in_window = raw_times < sealed_end
        expected_keys = set(zip(raw_times[in_window], raw.loc[in_window, "symbol"], strict=True))

        is_frame = getattr(is_snapshot, name)
        sealed_frame = getattr(sealed_snapshot, name)
        is_keys = set(zip(is_frame[column], is_frame["symbol"], strict=True))
        sealed_keys = set(zip(sealed_frame[column], sealed_frame["symbol"], strict=True))

        assert len(is_frame) + len(sealed_frame) == len(expected_keys), name
        assert is_keys.isdisjoint(sealed_keys), name
        assert is_keys | sealed_keys == expected_keys, name
