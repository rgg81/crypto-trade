# CUP-20 Integrity Review

This is the procedure the organiser runs **before advancing anyone** — before the leaderboard is
published, before the paper desk opens, and before any result is treated as evidence about a
strategy. It is written for someone who was not present when the tournament ran.

Run every command from the repository root, with `export PATH="$HOME/.local/bin:$PATH"`.

**What this review can and cannot establish.** Every agent in CUP-20 runs as the same operating
system account. During phase 1 the holdout is physically out of the working tree, so blindness for
that window is a fact and this review can demonstrate it. During phase 3 the sealed data has to be
readable in order to be scored, so for that window these checks are *detection*, not prevention.
A clean review means the mechanical checks found no evidence of a read. It does not mean no read
occurred. Charter §5 and §14.8 state the residual; do not overclaim past them when reporting.

---

## 0. Before you start

You need two things that are not in the repository:

| Thing | Where it is | Why it is not committed |
|---|---|---|
| the quarantine root | wherever `quarantine-receipt.json` says, outside the repo | it holds the sealed bytes |
| the canary token | `<quarantine-root>/canary-token.txt` | a token in the repo is a token a team can grep for and avoid |

If you cannot reach the quarantine root, checks 3, 4 (token half) and 7 cannot be completed, and
the review is **incomplete**, not passed.

The whole review runs in one command:

```
uv run python scripts/cup20_integrity_review.py
```

It prints `PASS` / `FAIL` / `SKIP` per check and exits `0` only when every check passed. `SKIP` is
not a pass — it names an artifact that was missing. Run the individual checks below when you need
to see why, or when you are auditing the driver itself rather than trusting it.

Before checks 4–6 it prints `4-6. there is something to scan`, with the team and nomination counts.
Read that line. Checks 4–6 loop over teams and candidates, and an empty loop emits nothing at all —
a review pointed at the wrong root, or run before anyone nominated, would otherwise look identical
to a clean one.

---

## 1. The sealed manifest is unchanged from activation

```
uv run python -c "
from crypto_trade.cup20.activation import verify_activation
r = verify_activation('tournament/cup20/activation-freeze.json')
print(r['sealed_manifest_sha256'])"
```

**Pass:** prints the digest and exits 0. That digest must equal `sealed_manifest_sha256` in
`tournament/cup20/activation-freeze.json` as committed — read it out of git history, not out of the
working file, if there is any doubt about the file itself:

```
git show HEAD:tournament/cup20/activation-freeze.json | grep sealed_manifest
```

**Fail:** `ValueError: activation authority changed: <label>`. The label names which of the eight
bound authorities moved. If the label is `sealed snapshot`, the holdout is not the data the
tournament was activated against and **no result computed on it is valid**. Stop. Do not publish.

**While the holdout is still quarantined** this check fails on a missing path rather than on drift,
because the sealed root is not in the working tree. That is expected during phase 1; use
`scripts/cup20_quarantine.py verify` instead (check 3), which verifies the same digest at the
quarantine location.

---

## 2. The research journal is a chain

```
uv run python -c "
from crypto_trade.cup20.journal import verify_chain
print(verify_chain('tournament/cup20/research-journal.jsonl'), 'records')"
```

**Pass:** prints a record count. Every sequence number, parent link and record digest is intact.

**Fail:** `journal sequence break at position N`, `journal parent link break at sequence N`, or
`journal record digest mismatch at sequence N`. Read the record at that position and the one before
it. A break means records were deleted, reordered, renumbered or edited.

**What the chain does not prove:** the digest is keyless SHA-256 over public bytes, so anyone with
write access to the file who deletes a record can also re-chain every record after it. The chain
detects careless tampering, not a determined editor. Check 3 is what makes the ordering load-
bearing anyway: an editor who re-chains the whole file still has to explain a quarantine event
that moved.

---

## 3. Quarantine was in place for the whole research phase

This is the strongest check in the review, and the only one that establishes blindness rather than
merely failing to disprove it.

```
uv run python -c "
from crypto_trade.cup20.quarantine import verify_quarantine_covered_research
import json; print(json.dumps(verify_quarantine_covered_research(
    journal_path='tournament/cup20/research-journal.jsonl',
    receipt_path='tournament/cup20/quarantine-receipt.json'), indent=2))"
```

**Pass:** prints five numbers, and

- `quarantine_sequence` is **lower** than `first_trial_sequence`, and
- `restore_sequence` is **higher** than `last_trial_sequence` (or `null`, if the holdout has not
  been restored yet), and
- `trials_covered` is greater than zero.

Read that as: the holdout left the working tree before the first accepted trial and did not come
back until after the last one. Because the journal is hash-chained, moving either event to make
this true breaks check 2.

**Fail modes and what each means:**

| Message | Meaning |
|---|---|
| `holdout_quarantined is at sequence N, after the first accepted trial` | research ran while the holdout was reachable |
| `holdout_restored is at sequence N, before the last accepted trial` | the holdout came back while research was still running |
| `expected exactly one holdout_quarantined record, found 0` | quarantine was never journalled; custody is unproven even if it happened |
| `expected exactly one holdout_quarantined record, found 2` | two custody episodes; the gap between them is unaccounted for |
| `records no trial_accepted events` | this is not the journal the review needs — you are pointed at the wrong file |
| `different canary tokens` | the committed receipt and the journalled event describe two different quarantines |

Any of these is a **finding about the tournament**, not about the tool. Record it and stop.

Separately, while the research phase is still running, the live form of this check is:

```
uv run python scripts/cup20_quarantine.py verify
```

**Pass:** `quarantine IS in effect: neither tree is reachable from the working tree`.
**Fail:** `quarantine is NOT in effect: ['sealed'] are present in the working tree at [...]` —
someone put the holdout back. Find out who, and when, before any team continues.

---

## 4. Every team's workspace scans clean

The pre-flight scan reads a team's frozen archive. That is the right surface for a gate and the
wrong one for a review: a team that opened the sealed snapshot and left the evidence in
`research/scratch.md`, a notebook cell, a log or a `.pyc` hands in a spotless archive. This check
reads the **whole workspace**.

```
uv run python -c "
from pathlib import Path
from crypto_trade.cup20.archive import scan_workspace_for_blindness_violations
from crypto_trade.cup20.quarantine import read_canary_token
token = read_canary_token(receipt_path='tournament/cup20/quarantine-receipt.json')
for team in sorted(Path('tournament/cup20/teams').glob('team-*')):
    scan = scan_workspace_for_blindness_violations(
        team, team_id=team.name, canary_tokens=(token,))
    print(team.name, scan.files_scanned, 'files',
          len(scan.violations), 'violations', len(scan.unscanned), 'unread')
    for v in scan.violations: print('   ', v)
    for u in scan.unscanned: print('    UNREAD', u)"
```

**What is scanned:** every regular file under the team's directory. No extension allowlist, no
directory exclusions — `__pycache__` and compiled `.pyc` files included, because a team can delete
a `.py` and keep the compiled constant pool. Content is read with `errors="replace"`, so binary
files are searched as text rather than skipped. Two surfaces per file: its own relative path
(reported at line `0`) and its content line by line. Symlinks are reported both as symlinks and by
what they point at.

**What is not scanned:** files larger than 8 MiB have their path scanned but not their content.
Every one of those is listed under `UNREAD`. That is a hole in the verdict, not a pass — open them
by hand, or re-run with a larger `max_content_bytes`.

**Pass:** `0 violations 0 unread` for every team.

**Fail:** any violation line. Read it as `path:line:what-matched`:

| Match | Meaning |
|---|---|
| `data/cup20/sealed` / `data/cup20/acquisition` / `tournament/cup20/private` / `reports-cup20` | a prohibited path was named |
| `sealed-canary-token` | **the token planted inside the sealed tree is in this team's files** |
| `HOLDOUT-CANARY-DO-NOT-READ` | the canary file's name is in this team's files |
| `symlink-not-allowed` | a symlink, which the archive scan can never see |
| `foreign-team-directory` | another team's directory was named |
| a date regex | a post-cutoff date literal |

A `sealed-canary-token` hit is the strongest single piece of evidence this review can produce and
is a disqualification on its own. The others need reading in context — a certificate that quotes
the prohibition itself will match, and that is not cheating. Judge, do not automate the judgement.

**Known limits of this check.** It is a literal string search. A forbidden reference assembled at
runtime by concatenation or formatting does not match, and a team that read the sealed data and
wrote down only a conclusion leaves nothing to find. Quarantine, not scanning, is what covers the
research phase; this check covers everything after it.

---

## 5. Every nomination's frozen archive scans clean

Narrower surface, same patterns — this is the gate the charter states in §5 layer 3, re-run as
evidence rather than as a gate.

```
uv run python -c "
from pathlib import Path
from crypto_trade.cup20.archive import scan_for_blindness_violations
for team in sorted(Path('tournament/cup20/teams').glob('team-*')):
    for c in sorted((team / 'candidates').glob('*')):
        if not (c / 'strategy.py').is_file(): continue
        print(team.name, c.name, scan_for_blindness_violations(c, team_id=team.name) or 'clean')"
```

**Pass:** `clean` for every nominated candidate.
**Fail:** any violation tuple. Same reading as check 4. A violation here is a **pre-flight
disqualification** under charter §5 layer 3, not a discussion.

---

## 6. Declared neighbourhood coordinates verify against the frozen source

A team's score is the median across its declared neighbourhood, so a fictional coordinate is a
fictional plateau. Every coordinate must be a module-level numeric constant in the frozen
`strategy.py`, named identically, with the nominee's declared value equal to that constant.

```
uv run python -c "
from pathlib import Path
from crypto_trade.cup20.archive import verify_neighbourhood_coordinates
from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.neighbourhood import load_declaration
minimum = int(load_config('tournament/cup20/config.toml').raw['research']['neighbourhood_minimum_points'])
for team in sorted(Path('tournament/cup20/teams').glob('team-*')):
    for c in sorted((team / 'candidates').glob('*')):
        if not (c / 'strategy.py').is_file(): continue
        d = load_declaration(c / 'neighbourhood.json'); d.validate(minimum)
        print(team.name, c.name, verify_neighbourhood_coordinates(c, d) or 'clean')"
```

**Pass:** `clean` for every candidate, and `validate` raised nothing.

**Fail:** each violation is `strategy.py:<coordinate>:<reason>`:

| Reason | Meaning |
|---|---|
| `absent-from-frozen-source` | the coordinate is not a module-level numeric constant — a class attribute or a function default does not count |
| `conflicting-module-level-values-A-vs-B` | the name is assigned two different values at module scope; which one runs cannot be decided without executing team code |
| `nominee-X-differs-from-frozen-Y` | the declared nominee is not what the frozen code does |
| `nominee-missing-declared-coordinate` | the declaration is internally inconsistent |
| `unparseable-source` / `entrypoint-too-large` / `missing-entrypoint` | the frozen file cannot be verified at all |

Any of these voids the sweep. The candidate's score is not a plateau estimate and must not be
ranked as one.

---

## 7. The phase-3 access tripwire

```
uv run python scripts/cup20_quarantine.py access-report
```

**Read `atime_is_recorded` first.** If it is `false`, the filesystem is mounted `noatime`, the
kernel never recorded an access, and an empty `accessed` list means *nothing at all*. Say that in
the report rather than calling it clean.

**Pass (weak):** `atime_is_recorded: true`, and `accessed` contains only files the organiser's own
scoring run touched. Note that scoring the finalists reads the sealed parquet files, so a normal
phase-3 run leaves most of them in `accessed` — the informative case is `accessed` being non-empty
*before* the organiser's scoring run, or the canary file appearing in it at any point.

**Fail:** `appeared` or `vanished` is non-empty. A file added to or removed from the sealed tree
after arming is a more serious finding than a read; it means the tree's membership changed while it
was back in the working tree.

**What this proves and does not prove.** Every sealed file's `atime` was back-dated 48 hours at
restore, which is what makes the next read recordable under `relatime` (the kernel otherwise skips
the update when `atime` is newer than `mtime` and less than 24 hours old). So the *first* read
after arming is reliably recorded. Beyond that: `O_NOATIME` bypasses it and the file's own owner
may use it; anyone who can call `utime` can put `atime` back; a copy of the tree read elsewhere
leaves the original untouched; and it never says *who* read the file. Treat a hit as a reason to
investigate, never as proof on its own, and treat a miss as no evidence either way.

---

### 7a. If you can, replace check 7 with something stronger

Both phase-3 tripwires infer a read from a side effect. Two controls observe it directly, and if
either is available to you it supersedes check 7 rather than supplementing it — arrange it before
restoring the holdout, and record that you did:

```
# a kernel read audit: names the process, the user and the moment of every open
sudo auditctl -w "$PWD/data/cup20/sealed" -p r -k cup20-holdout
sudo ausearch -k cup20-holdout
```

```
# per-agent operating-system accounts: makes phase-3 blindness a kernel guarantee
sudo chown -R organiser:organiser data/cup20/sealed && sudo chmod 700 data/cup20/sealed
# ... with each team agent launched under its own uid
```

Neither is in place in this deployment: `auditctl` needs root, and every agent here runs as one
account. Charter §14.8 records that as the residual. If you can close it, do, and say so.

---

## 8. Recording the outcome

Write the result into the tournament record with the same honesty the charter uses:

- which checks passed, with the numbers they printed;
- which were skipped and why;
- anything that failed, verbatim;
- the sentence that bounds the claim: **custody is demonstrated for the research phase; phase 3
  rests on detection, and the residual in charter §14.8 is not closed by any check above.**

If any check failed, no team advances and the paper desk does not open until the failure is
explained in the tournament record. Charter §1.1 already accepts "no winner" as a legitimate
outcome; a tournament that cannot show its holdout was untouched has produced exactly that.
