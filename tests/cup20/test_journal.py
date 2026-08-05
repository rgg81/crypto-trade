"""Tests for the CUP-20 append-only, hash-chained research journal.

A trial is consumed the moment it is ACCEPTED, before market data are opened -- so the count of
`trial_accepted` records a team has is the single fact the multiplicity penalty is computed from,
and the incentive to quietly drop one is direct: fewer recorded trials means a lighter penalty
means a candidate that would otherwise be disqualified passes. Three properties are the whole
point, and the test groups below are organised around proving (or, for the adversarial group,
honestly disproving) one of them:

1. Tamper-evidence -- altering any byte of any record's payload, digest field, sequence number or
   parent link must break the chain.
2. Deletion detection -- removing a record from the middle (or the first record, or reordering
   records) must break the chain.
3. Byte-stable digests -- the same payload always produces the same digest, independent of dict
   insertion order (`sort_keys=True`, fixed separators), so a digest is reproducible from frozen
   authorities without needing the original writer's process.

No private (underscore-prefixed) helper is imported anywhere in this file, including in the
adversarial re-chaining tests -- everything below goes through the four public functions, or,
where an "attacker" needs to reproduce the digest scheme, an independent reimplementation of the
two-line canonicalisation rule. That mirrors test_scoring.py's precedent of never importing
`_clamp` directly, and matches the actual threat model: the canonicalisation rule is meant to be
publicly reproducible ("a digest is reproducible from frozen authorities"), not secret.

The (b) adversarial group's honest conclusion, stated up front rather than only in the task
report: `verify_chain` DOES catch a naive delete (mismatched sequence numbers left behind in the
file) but does NOT catch a delete-or-alter followed by a correct re-chain of every downstream
record, because SHA-256 over canonical JSON is a public, keyless scheme -- nothing stops a
file-write-access attacker from recomputing it. Closing that gap needs an externally-stored anchor
(a published head digest, WORM storage, or an independent witness), which is out of this module's
scope. See the two tests in that group and the task report for the full discussion.
"""

import hashlib
import json

import pytest

from crypto_trade.cup20.journal import (
    accepted_trial_count,
    append_record,
    read_records,
    verify_chain,
)

# --- brief Step 1, verbatim -------------------------------------------------


def test_first_record_has_a_null_parent(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01", "candidate_id": "c1"})
    records = read_records(path)
    assert records[0]["previous_sha256"] is None
    assert records[0]["sequence"] == 1


def test_each_record_chains_to_its_predecessor(tmp_path):
    path = tmp_path / "journal.jsonl"
    first = append_record(path, "trial_accepted", {"team_id": "team-01"})
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    records = read_records(path)
    assert records[1]["previous_sha256"] == first
    assert verify_chain(path) == 2


def test_tampering_with_a_payload_breaks_the_chain(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01", "note": "original"})
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    lines = path.read_text().splitlines()
    record = json.loads(lines[0])
    record["payload"]["note"] = "tampered"
    lines[0] = json.dumps(record, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="record digest"):
        verify_chain(path)


def test_deleting_a_record_breaks_the_chain(tmp_path):
    path = tmp_path / "journal.jsonl"
    for _ in range(3):
        append_record(path, "trial_accepted", {"team_id": "team-01"})
    lines = path.read_text().splitlines()
    path.write_text("\n".join([lines[0], lines[2]]) + "\n")
    with pytest.raises(ValueError):
        verify_chain(path)


def test_accepted_trial_count_is_per_team(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    append_record(path, "trial_accepted", {"team_id": "team-02"})
    append_record(path, "nomination", {"team_id": "team-01"})
    assert accepted_trial_count(path, "team-01") == 2
    assert accepted_trial_count(path, "team-02") == 1
    assert accepted_trial_count(path, "team-09") == 0


def test_records_are_byte_stable_for_identical_payloads(tmp_path):
    digests = []
    for name in ("a", "b"):
        path = tmp_path / f"{name}.jsonl"
        digests.append(append_record(path, "trial_accepted", {"z": 1, "a": 2}))
    assert digests[0] == digests[1]


# --- shared helpers for the additional coverage below -----------------------


def _tamper_record(path, line_index, **overrides):
    """Rewrite one record's top-level fields in place, re-encoding it with the same canonical
    separators the module itself uses. Factors out the inline pattern the brief's own
    test_tampering_with_a_payload_breaks_the_chain uses, for reuse across the raise-path tests
    below that tamper a different top-level field (record_sha256, sequence, previous_sha256).
    """
    lines = path.read_text().splitlines()
    record = json.loads(lines[line_index])
    record.update(overrides)
    lines[line_index] = json.dumps(record, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n")


def _rewrite_lines(path, lines):
    """Replace the whole file with an explicit, caller-chosen ordering of raw JSON lines --
    matches the brief's own delete-the-middle-record pattern, factored out for the
    delete-the-first-record and reordering tests below.
    """
    path.write_text("\n".join(lines) + "\n")


def _adversarial_digest(record):
    """Recompute a record's digest the way an attacker would: reading the public
    canonicalisation rule (sort_keys=True, fixed separators, ensure_ascii=True; the
    record_sha256 field excluded by key name) off the module's own documented contract, not by
    importing any private helper. This is the whole threat model for the (b) adversarial tests
    below -- SHA-256 over canonical JSON is public and keyless, so nothing stops a
    file-write-access attacker from reproducing it exactly.
    """
    body = {key: value for key, value in record.items() if key != "record_sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --- (a) untested branches and raise paths: one test per failure mode -------
#
# The brief's own tests already cover "tampered payload" (digest mismatch) and "deleted middle
# record" (sequence mismatch). The battery below covers every other failure mode named in the
# task instructions: tampered digest field, tampered sequence, tampered parent link, deleted
# first record, reordered records, truncated file, empty file, and a file that does not exist
# yet -- plus the read_records blank-line-skipping branch feeding into all of it.


def test_tampering_the_record_digest_field_directly_breaks_the_chain(tmp_path):
    path = tmp_path / "journal.jsonl"
    for _ in range(3):
        append_record(path, "trial_accepted", {"team_id": "team-01"})
    # Only the stored digest changes -- sequence, previous_sha256 and payload are untouched, so
    # the recomputed digest of the (unchanged) body no longer matches the (tampered) stored one.
    _tamper_record(path, 0, record_sha256="0" * 64)
    with pytest.raises(ValueError, match="record digest"):
        verify_chain(path)


def test_tampering_the_sequence_number_breaks_the_chain(tmp_path):
    path = tmp_path / "journal.jsonl"
    for _ in range(3):
        append_record(path, "trial_accepted", {"team_id": "team-01"})
    # Only the sequence field changes, without recomputing the stored digest -- this is a raw,
    # non-re-chaining tamper of the position claim alone.
    _tamper_record(path, 1, sequence=99)
    with pytest.raises(ValueError, match="sequence break"):
        verify_chain(path)


def test_tampering_the_parent_link_breaks_the_chain(tmp_path):
    path = tmp_path / "journal.jsonl"
    for _ in range(3):
        append_record(path, "trial_accepted", {"team_id": "team-01"})
    # Only previous_sha256 changes -- sequence still matches position, so this isolates the
    # parent-link check specifically (reached only once the sequence check has passed).
    _tamper_record(path, 2, previous_sha256="f" * 64)
    with pytest.raises(ValueError, match="parent link"):
        verify_chain(path)


def test_deleting_the_first_record_breaks_the_chain(tmp_path):
    path = tmp_path / "journal.jsonl"
    for _ in range(3):
        append_record(path, "trial_accepted", {"team_id": "team-01"})
    lines = path.read_text().splitlines()
    # Distinct from the brief's "delete the middle" case: the record that becomes position 1 was
    # originally sequence 2, and its previous_sha256 pointed at the now-deleted first record.
    _rewrite_lines(path, [lines[1], lines[2]])
    with pytest.raises(ValueError, match="sequence break"):
        verify_chain(path)


def test_records_reordered_breaks_the_chain(tmp_path):
    path = tmp_path / "journal.jsonl"
    for _ in range(3):
        append_record(path, "trial_accepted", {"team_id": "team-01"})
    lines = path.read_text().splitlines()
    # A pure permutation of otherwise-untouched lines. Any non-identity reorder misaligns
    # sequence numbers against file position, since sequence numbers are assigned by append
    # order, not by any property recoverable from the reordered file itself.
    _rewrite_lines(path, [lines[0], lines[2], lines[1]])
    with pytest.raises(ValueError, match="sequence break"):
        verify_chain(path)


def test_truncated_last_line_raises_a_value_error(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    append_record(path, "trial_accepted", {"team_id": "team-01", "note": "second record"})
    text = path.read_text()
    # Chop well inside the final record's JSON object -- not just the trailing newline (which
    # read_records tolerates fine) -- so the last line is syntactically broken JSON.
    path.write_text(text[:-20])
    # Fix round 1, Finding 2: read_records now wraps the per-line parse and names the actual
    # record position (2 here -- the second and last record) instead of raising the raw
    # json.JSONDecodeError, whose own line/column numbers are always relative to that one line
    # (always "line 1") and would otherwise misreport the position in a multi-record file.
    with pytest.raises(ValueError, match="position 2"):
        verify_chain(path)


def test_malformed_json_names_the_broken_records_position_not_line_one(tmp_path):
    """Fix round 1, Finding 2: each line is parsed independently, so json.JSONDecodeError's own
    line/column numbers are relative to that single line's own content -- always "line 1" no
    matter which record actually broke, confirmed empirically by the reviewer on a five-record
    file with record four truncated. Corrupting the FOURTH of five records (not the first, and
    not via a whole-file tail truncation like the sibling test above) means an implementation
    that still reports "line 1", or that merely re-raises the raw JSONDecodeError untouched,
    cannot pass this by coincidence.
    """
    path = tmp_path / "journal.jsonl"
    for i in range(5):
        append_record(path, "trial_accepted", {"team_id": "team-01", "i": i})
    lines = path.read_text().splitlines()
    lines[3] = lines[3][:-10]  # corrupt record 4 (0-indexed 3) specifically
    path.write_text("\n".join(lines) + "\n")

    with pytest.raises(ValueError, match="position 4"):
        read_records(path)
    with pytest.raises(ValueError, match="position 4"):
        verify_chain(path)


def test_verify_chain_on_a_nonexistent_file_returns_zero(tmp_path):
    path = tmp_path / "never-written.jsonl"
    assert not path.exists()
    assert verify_chain(path) == 0


def test_verify_chain_on_an_empty_file_returns_zero(tmp_path):
    path = tmp_path / "journal.jsonl"
    path.write_text("")
    assert path.exists()
    assert verify_chain(path) == 0


def test_read_records_on_a_nonexistent_file_returns_an_empty_tuple(tmp_path):
    path = tmp_path / "never-written.jsonl"
    assert read_records(path) == ()


def test_read_records_on_an_empty_file_returns_an_empty_tuple(tmp_path):
    path = tmp_path / "journal.jsonl"
    path.write_text("")
    assert read_records(path) == ()


def test_blank_lines_between_records_are_skipped(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    lines = path.read_text().splitlines()
    # Splice a genuinely blank line between the two records -- exercises read_records's
    # `if line.strip()` filter, which nothing above touches.
    path.write_text(lines[0] + "\n\n" + lines[1] + "\n")
    assert len(read_records(path)) == 2
    assert verify_chain(path) == 2


# --- accepted_trial_count exactness: only trial_accepted, only the named team ---
#
# accepted_trial_count feeds the multiplicity penalty directly. It must count only
# trial_accepted events for the named team -- not nominations, not other event types, not other
# teams -- and must not be foolable by a near-miss event_type string or crash on a malformed
# record.


@pytest.mark.parametrize(
    "near_miss_event_type",
    [
        "nomination",
        "TRIAL_ACCEPTED",
        "trial_accepted_retry",
        "pre_trial_accepted",
        "trial_accept",
    ],
)
def test_accepted_trial_count_ignores_near_miss_event_types(tmp_path, near_miss_event_type):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    append_record(path, near_miss_event_type, {"team_id": "team-01"})
    assert accepted_trial_count(path, "team-01") == 1


def test_accepted_trial_count_on_a_nonexistent_file_returns_zero(tmp_path):
    path = tmp_path / "never-written.jsonl"
    assert accepted_trial_count(path, "team-01") == 0


def test_accepted_trial_count_ignores_payload_missing_team_id(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"candidate_id": "c1"})  # no team_id key at all
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    assert accepted_trial_count(path, "team-01") == 1


def test_accepted_trial_count_skips_a_non_mapping_payload_without_crashing(tmp_path):
    """Fix round 1, Finding 1: `record.get("payload", {}).get("team_id")` only substitutes the
    `{}` default when the "payload" KEY is missing, not when its VALUE is present but not a
    mapping (e.g. a corrupted or hand-edited `payload: null`) -- that used to raise
    AttributeError. Because the scan walks every record for every team's query, one such
    record anywhere in the shared journal broke EVERY team's count, not just its own -- an
    availability attack on the exact disqualification computation this journal exists to
    protect. Chosen fix: skip (never raise) a non-mapping payload, since it cannot name any
    team and so is treated exactly like a mapping that is simply missing the team_id key; full
    reasoning for skip over raise is in the fix-round report section. This test proves both
    halves: no crash, AND other teams' counts are completely unaffected by the malformed
    record.

    Fix round 2 note: this test no longer asserts anything about verify_chain on this journal --
    round 2 makes verify_chain correctly REJECT exactly this malformed record (see
    test_verify_chain_rejects_a_non_mapping_payload below). The two functions have different
    jobs and are tested separately: the counter must stay available in the presence of one bad
    record (asserted here, unchanged), the validator must refuse to bless a journal containing
    one (asserted there).
    """
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    append_record(path, "trial_accepted", {"team_id": "team-02"})

    # Splice in a record with a non-mapping payload, correctly re-chained. This must be built
    # by direct file manipulation -- append_record's own `dict(payload)` call rejects
    # payload=None outright -- matching the same write-access threat model as the rest of this
    # module's tamper tests: a hand-edited or corrupted journal, not a legitimate append.
    records = list(read_records(path))
    malformed = {
        "schema_version": records[-1]["schema_version"],
        "sequence": len(records) + 1,
        "event_type": "trial_accepted",
        "payload": None,
        "previous_sha256": records[-1]["record_sha256"],
    }
    malformed["record_sha256"] = _adversarial_digest(malformed)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(malformed, sort_keys=True, separators=(",", ":")) + "\n")

    # No crash, and the malformed record must not affect ANY other team's count.
    assert accepted_trial_count(path, "team-01") == 1
    assert accepted_trial_count(path, "team-02") == 1
    assert accepted_trial_count(path, "team-03") == 0


def test_verify_chain_rejects_a_non_mapping_payload(tmp_path):
    """Fix round 2: verify_chain must fail closed on a record whose payload is not a mapping --
    the ordinary, non-adversarial case the coordinator named: an organiser-side bug writes a
    payload of the wrong shape. Before this fix, verify_chain returned a clean count for exactly
    this journal (it never inspected payload's type at all), while accepted_trial_count silently
    skipped the malformed record (see the test above) -- a team's trial count could quietly drop
    with the journal's own validator reporting no problem, which is precisely the direction of
    failure this journal exists to prevent: fewer recorded trials means a lighter multiplicity
    penalty means a candidate that should be disqualified passes. Built with the malformed
    record specifically in the MIDDLE (matching the coordinator's own repro: "a three-record
    chain whose middle record has payload: null"), with a legitimate record appended after it
    too, so the reported position must be exactly 2, not 1 or 3, and the check must fire even
    though a perfectly valid record follows.
    """
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01"})

    records = list(read_records(path))
    malformed = {
        "schema_version": records[-1]["schema_version"],
        "sequence": len(records) + 1,
        "event_type": "trial_accepted",
        "payload": None,
        "previous_sha256": records[-1]["record_sha256"],
    }
    malformed["record_sha256"] = _adversarial_digest(malformed)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(malformed, sort_keys=True, separators=(",", ":")) + "\n")

    append_record(path, "trial_accepted", {"team_id": "team-01"})  # a valid record after it too

    with pytest.raises(ValueError, match="payload is not a mapping at sequence 2"):
        verify_chain(path)


def test_verify_chain_rejects_a_non_string_event_type(tmp_path):
    """Fix round 2, my own reasoned extension alongside the mandated payload check (see the
    fix-round-2 report section for the full reasoning on why event_type earns this and sequence
    does not): event_type carries the exact same documented `str` contract as payload carries
    `Mapping[str, Any]` -- both are explicit parameter type hints on append_record -- and
    accepted_trial_count's `== "trial_accepted"` comparison fails open on a non-string
    event_type in exactly the same silent, validator-blind way its `.get("team_id")` call used
    to fail open (pre round-1) on a non-mapping payload.
    """
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01"})

    records = list(read_records(path))
    malformed = {
        "schema_version": records[-1]["schema_version"],
        "sequence": len(records) + 1,
        "event_type": None,
        "payload": {"team_id": "team-01"},
        "previous_sha256": records[-1]["record_sha256"],
    }
    malformed["record_sha256"] = _adversarial_digest(malformed)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(malformed, sort_keys=True, separators=(",", ":")) + "\n")

    with pytest.raises(ValueError, match="event_type is not a string at sequence 2"):
        verify_chain(path)


def test_verify_chain_rejects_a_record_that_is_not_a_mapping(tmp_path):
    """Fix round 2: a line can be valid JSON while decoding to something other than a JSON
    object -- a bare `42`, a string, a list -- and read_records (which, even after round 1's
    Finding 2 fix, only guards against JSON SYNTAX errors, not the parsed TYPE) happily returns
    it as though it were a normal record. Without this check, every downstream `.get(...)` call
    in verify_chain's loop would raise AttributeError instead of a clear, positioned ValueError
    -- the same crash-and-take-everyone-down shape as round 1's Finding 1, one level up (the
    record itself, not just its payload field). This is the adjacent gap flagged, unfixed, in
    the original task-11 report.
    """
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    with path.open("a", encoding="utf-8") as handle:
        handle.write("42\n")

    # read_records itself does not crash -- confirming the malformed value genuinely reaches
    # verify_chain's loop rather than being filtered out earlier.
    assert read_records(path)[1] == 42

    with pytest.raises(ValueError, match="position 2 is not a mapping"):
        verify_chain(path)


# --- digest exclusion is by key NAME, at the TOP LEVEL of the record only ---
#
# _record_digest excludes the record_sha256 field so a digest never covers itself. That
# exclusion must operate on the record dict's own top-level keys only -- a payload that happens
# to contain a nested key of the same name must still be fully covered by the digest. Proven
# black-box: tampering ONLY that nested value must still break the chain.


def test_nested_payload_key_named_record_sha256_is_hashed_not_excluded(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01", "record_sha256": "decoy"})
    assert read_records(path)[0]["payload"]["record_sha256"] == "decoy"
    assert verify_chain(path) == 1  # unmodified: the nested key does not confuse anything yet

    _tamper_record(path, 0, payload={"team_id": "team-01", "record_sha256": "tampered-decoy"})
    with pytest.raises(ValueError, match="record digest"):
        verify_chain(path)


# --- (c) byte-stability: positive extension and negative complements -------
#
# A broken implementation that returns a constant digest (or hashes only a fixed subset of
# fields) would pass the brief's own positive byte-stability test. The negative complements
# below prove the digest actually depends on the content.


def test_nested_payload_keys_are_sorted_recursively_for_byte_stability(tmp_path):
    path_a = tmp_path / "a.jsonl"
    path_b = tmp_path / "b.jsonl"
    payload_a = {"outer": {"z": 1, "a": 2}, "b": 5}
    payload_b = {"b": 5, "outer": {"a": 2, "z": 1}}  # same data, different order at both levels
    digest_a = append_record(path_a, "trial_accepted", payload_a)
    digest_b = append_record(path_b, "trial_accepted", payload_b)
    assert digest_a == digest_b


def test_digest_is_sensitive_to_payload_and_event_type(tmp_path):
    base_path = tmp_path / "base.jsonl"
    base_digest = append_record(base_path, "trial_accepted", {"team_id": "team-01", "z": 1})

    payload_variant_path = tmp_path / "payload_variant.jsonl"
    payload_variant_digest = append_record(
        payload_variant_path, "trial_accepted", {"team_id": "team-01", "z": 2}
    )
    assert payload_variant_digest != base_digest

    event_type_variant_path = tmp_path / "event_type_variant.jsonl"
    event_type_variant_digest = append_record(
        event_type_variant_path, "nomination", {"team_id": "team-01", "z": 1}
    )
    assert event_type_variant_digest != base_digest


def test_same_payload_appended_twice_yields_different_digests(tmp_path):
    # Tight complement to the brief's own test_each_record_chains_to_its_predecessor: proves
    # directly (not just inferred from previous_sha256 wiring) that sequence/previous_sha256 --
    # not just payload -- are part of what gets hashed, which is the entire point of a hash
    # CHAIN rather than a bag of independently hashed records.
    path = tmp_path / "journal.jsonl"
    first = append_record(path, "trial_accepted", {"team_id": "team-01"})
    second = append_record(path, "trial_accepted", {"team_id": "team-01"})
    assert first != second


def test_byte_stability_holds_for_unicode_payload_values(tmp_path):
    path_a = tmp_path / "a.jsonl"
    path_b = tmp_path / "b.jsonl"
    payload = {"team_id": "team-01", "note": "éè café 币 \U0001f4b0"}
    digest_a = append_record(path_a, "trial_accepted", dict(payload))
    digest_b = append_record(path_b, "trial_accepted", dict(payload))
    assert digest_a == digest_b
    assert read_records(path_a)[0]["payload"]["note"] == payload["note"]


def test_append_record_return_value_matches_the_persisted_digest(tmp_path):
    path = tmp_path / "journal.jsonl"
    returned = append_record(path, "trial_accepted", {"team_id": "team-01"})
    persisted = read_records(path)[0]["record_sha256"]
    assert returned == persisted
    assert isinstance(returned, str)
    assert len(returned) == 64  # sha256 hex digest length


# --- (b) adversarial: delete-or-alter, then correctly re-chain the suffix ---
#
# The naive attacks above (tamper one field in isolation, delete without renumbering) are all
# caught. These two tests are the sophisticated version named explicitly in the task
# instructions: an attacker who ALSO recomputes every downstream sequence/previous_sha256/
# record_sha256 after the edit. Read the module docstring above and the task report for the
# honest conclusion these tests establish empirically: verify_chain does not catch this.


def test_a_single_recomputed_record_without_cascading_is_still_caught(tmp_path):
    """Isolates the parent-link check's real, independent value, as a contrast with the two
    fully-cascaded attacks below. The digest check alone already catches any *unrecomputed*
    single-field tamper (the raw tamper tests above never reach the parent-link check on a
    different mechanism -- they are all simultaneously true, and Python's raise-on-first-match
    means only one message ever surfaces). This test recomputes ONE tampered record's own
    digest correctly (so its digest check passes -- the record is internally self-consistent)
    but does not cascade the change into its successor's previous_sha256/record_sha256. That
    incomplete attack is still caught, by the parent-link check on the *next* record, whose
    stored previous_sha256 now names a digest that no longer exists anywhere in the file.
    """
    path = tmp_path / "journal.jsonl"
    for i in range(3):
        append_record(path, "trial_accepted", {"team_id": "team-01", "i": i})

    lines = path.read_text().splitlines()
    record = json.loads(lines[1])
    record["payload"]["i"] = "tampered"
    record.pop("record_sha256", None)
    record["record_sha256"] = _adversarial_digest(record)  # self-consistent, but only this one
    lines[1] = json.dumps(record, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n")

    with pytest.raises(ValueError, match="parent link"):
        verify_chain(path)


def test_delete_and_rechain_a_middle_record_is_not_detected(tmp_path):
    path = tmp_path / "journal.jsonl"
    for i in range(5):
        team = "team-02" if i == 2 else "team-01"
        append_record(path, "trial_accepted", {"team_id": team, "i": i})
    assert verify_chain(path) == 5
    assert accepted_trial_count(path, "team-02") == 1

    kept = [
        json.loads(line) for index, line in enumerate(path.read_text().splitlines()) if index != 2
    ]
    previous = None
    forged = []
    for new_index, record in enumerate(kept, start=1):
        record = dict(record)
        record["sequence"] = new_index
        record["previous_sha256"] = previous
        record.pop("record_sha256", None)
        digest = _adversarial_digest(record)
        record["record_sha256"] = digest
        previous = digest
        forged.append(record)
    path.write_text(
        "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in forged) + "\n"
    )

    # The forged 4-record chain is fully self-consistent under every check verify_chain
    # performs. It does not raise, and the deleted team-02 trial has vanished from the count
    # verify_chain's caller would use to compute the multiplicity penalty.
    assert verify_chain(path) == 4
    assert accepted_trial_count(path, "team-02") == 0


def test_alter_a_payload_and_rechain_the_suffix_is_not_detected(tmp_path):
    path = tmp_path / "journal.jsonl"
    for i in range(4):
        append_record(path, "trial_accepted", {"team_id": "team-01", "note": f"original-{i}"})
    assert verify_chain(path) == 4

    records = [json.loads(line) for line in path.read_text().splitlines()]
    records[1]["payload"]["note"] = "quietly-altered"

    previous = None
    forged = []
    for new_index, record in enumerate(records, start=1):
        record = dict(record)
        record["sequence"] = new_index
        record["previous_sha256"] = previous
        record.pop("record_sha256", None)
        digest = _adversarial_digest(record)
        record["record_sha256"] = digest
        previous = digest
        forged.append(record)
    path.write_text(
        "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in forged) + "\n"
    )

    assert verify_chain(path) == 4
    assert read_records(path)[1]["payload"]["note"] == "quietly-altered"


# --- concurrency-adjacent realism -------------------------------------------


def test_append_record_creates_parent_directories_on_a_fresh_path(tmp_path):
    path = tmp_path / "nested" / "does" / "not" / "exist" / "journal.jsonl"
    assert not path.parent.exists()
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    assert path.exists()
    assert verify_chain(path) == 1


def test_appending_after_reading_continues_the_chain_correctly(tmp_path):
    path = tmp_path / "journal.jsonl"
    append_record(path, "trial_accepted", {"team_id": "team-01"})
    # A reader observes the journal mid-way, holding no lock and no cached state...
    mid_read = read_records(path)
    assert len(mid_read) == 1
    # ...then a later append must still chain correctly off what is actually on disk.
    second = append_record(path, "trial_accepted", {"team_id": "team-01"})
    records = read_records(path)
    assert len(records) == 2
    assert records[1]["record_sha256"] == second
    assert records[1]["previous_sha256"] == mid_read[0]["record_sha256"]
    assert verify_chain(path) == 2


# --- misc robustness ---------------------------------------------------------


def test_functions_accept_a_plain_string_path_as_well_as_a_path_object(tmp_path):
    str_path = str(tmp_path / "journal.jsonl")
    append_record(str_path, "trial_accepted", {"team_id": "team-01"})
    append_record(tmp_path / "journal.jsonl", "trial_accepted", {"team_id": "team-01"})
    assert verify_chain(str_path) == 2
    assert accepted_trial_count(str_path, "team-01") == 2


def test_a_longer_chain_of_many_mixed_records_verifies_correctly(tmp_path):
    path = tmp_path / "journal.jsonl"
    teams = ["team-01", "team-02", "team-03"]
    event_types = ["trial_accepted", "nomination", "trial_accepted", "neighbourhood_declared"]
    expected_accepted = dict.fromkeys(teams, 0)
    for i in range(40):
        team = teams[i % len(teams)]
        event_type = event_types[i % len(event_types)]
        append_record(path, event_type, {"team_id": team, "i": i})
        if event_type == "trial_accepted":
            expected_accepted[team] += 1

    assert verify_chain(path) == 40
    for team in teams:
        assert accepted_trial_count(path, team) == expected_accepted[team]
