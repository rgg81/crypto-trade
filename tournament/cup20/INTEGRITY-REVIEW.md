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

## 0a. Pre-start readiness — run this BEFORE dispatching any team

Everything below this section audits a tournament that has already run. This one check runs at the
other end, and it is the only one whose failure is cheap: it establishes that a candidate can be
scored **at all** on the shipped snapshot.

```
uv run python scripts/cup20_readiness.py
```

It runs one reference strategy over the full in-sample window through the real pipeline —
`run_candidate` → `assemble_scored_metrics` → `adjudicate_candidate` — and fails if any stage
raises. Run it before the first team is dispatched, and again after **any** change to the snapshot,
the universe rules, the evaluator or the scoring stack.

**Why it is not covered by the test suite.** Every unit test builds its own fixture, and a fixture
is exactly where a *data* defect cannot live. 862 of them passed while the built snapshot held 21
decision boundaries at which the evaluator raised `missing current mark for eligible symbols` on a
member whose mark history began a week after it entered the universe. That raise fires on the
eligible symbol set before any strategy code runs, so it would have crashed all twelve teams, on
every candidate, at the first backtest. This script is what reaches it.

**Pass:** every stage prints `ok`, followed by the reference strategy's full metric vector, the
hard-floor table, and `READINESS PASSED`. Read the metric vector — a Sharpe of 40, a drawdown of
0.0 or a trade count of 3 means the pipeline is broken even though nothing raised.

**A `NOT QUALIFIED` verdict for the reference book is not a failure.** The reference strategy is a
load, not a benchmark: a weekly cross-sectional reversal book chosen because it trades both sides,
turns over, and exercises the caps and the risk unit. Only a raise — or the mark-coverage check
below — fails this gate.

**Fail:** the failing stage is named, with the exception. The one failure mode with its own message
is `READINESS FAILED: the snapshot holds N (boundary, symbol) pairs the evaluator cannot mark`,
which names the symbols and the first offending boundary. That is a defect in the built universe,
not in a team's code: rebuild with `scripts/cup20_build_snapshot.py --skip-acquire` and do not
dispatch teams until it is clean.

**Cost:** it reads only `data/cup20/is`, so it runs with the holdout still quarantined, and it
reports its own wall-clock time on the last line. The mark-coverage check is the first stage and
finishes in under a second, so a snapshot with this defect is rejected immediately rather than
after the full evaluation.

---

## 0. Before you start

You need two things that are not in the repository:

| Thing | Where it is | Why it is not committed |
|---|---|---|
| the quarantine root | wherever `quarantine-receipt.json` says, outside the repo | it holds the sealed bytes |
| the canary token | `<quarantine-root>/canary-token.txt` | a token in the repo is a token a team can grep for and avoid |

If you cannot reach the quarantine root, check 3a and the token half of check 4 cannot be
completed, and the review is **incomplete**, not passed. (Checks 3 and 7 do not need it: check 3
reads the journal and the committed receipt, and check 7 reads the restored sealed tree and the
access baseline, both of which are in the working tree by the time it runs.)

Checks 1–7 run in one command:

```
uv run python scripts/cup20_integrity_review.py
```

It prints `PASS` / `FAIL` / `SKIP` per check and exits `0` only when every check passed. `SKIP` is
not a pass — it names an artifact that was missing. Run the individual checks below when you need
to see why, or when you are auditing the driver itself rather than trusting it.

**Check 3a is not in the driver and cannot be**: it verifies the holdout *while it is still in
quarantine*, and by the time this review runs the holdout has been restored and the quarantine
root is empty. It is a phase-1 check, run periodically during the research phase, and its results
belong in the tournament record alongside this one. A review that never ran it has no evidence
about the holdout's bytes for the whole research window — only about where they were.

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

**Pass:** exits 0. *That* is the check — `verify_activation` recomputes all eight authorities from
the files on disk and raises on the first that has moved. The printed digest is not evidence on its
own: `verify_activation` returns the frozen record, so the value printed is read out of
`activation-freeze.json`, not recomputed. What it is good for is the one comparison the function
cannot make for you — against the record as **committed**, which is what catches a working file
edited to match a tree that drifted:

```
git show HEAD:tournament/cup20/activation-freeze.json | grep sealed_manifest
```

**Fail:** `ValueError: activation authority changed: <label>`. The label names which of the eight
bound authorities moved. If the label is `sealed snapshot`, the holdout is not the data the
tournament was activated against and **no result computed on it is valid**. Stop. Do not publish.

**While the holdout is still quarantined** this check fails on a missing path rather than on drift,
because the sealed root is not in the working tree. That is expected during phase 1. The stand-in
for that window is

```
uv run python scripts/cup20_quarantine.py verify
```

which runs this same `verify_activation` over all eight authorities with the sealed root read at
the quarantine location, and then adds the two whole-tree bundle digests the receipt recorded.
See check 3. Note that it is the plain `verify` that does this; `verify --fast` is an absence test
that reads no bytes at all and prints a paragraph saying so.

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

**Pass:** prints six fields, and

- `quarantine_sequence` is **lower** than `first_trial_sequence`, and
- `restore_sequence` is **higher** than `last_trial_sequence` (or `null`, if the holdout has not
  been restored yet), and
- `trials_covered` is greater than zero.

Read that as: the holdout left the working tree before the first accepted trial and did not come
back until after the last one. Because the journal is hash-chained, moving either event to make
this true breaks check 2.

`custody_episodes` lists every `(opened, closed, closed_by)` interval the holdout spent outside the
working tree. **More than one episode is legitimate only in one shape**, and the list is where you
check which shape you have:

| `closed_by` | Meaning |
|---|---|
| `null` (open) | the current episode; expected while the tournament is running |
| `holdout_released_for_rebuild` | a **pre-start** rebuild: the snapshot was found to be wrong before any team began, so the holdout came back, was rebuilt and was re-quarantined. `release_for_rebuild` refuses to run once any trial exists, so such an episode can only precede the research phase |
| `holdout_restored` | the phase-3 restore. There is at most one, and everything after it is scoring |

Every accepted trial must sit **strictly inside** one episode; a trial in the gap between two is a
failure, not a technicality. Read the whole list — a rebuild episode is a statement that the
tournament's data was replaced, and belongs in the record alongside the reason.

**Fail modes and what each means:**

| Message | Meaning |
|---|---|
| `the trial accepted at sequence N sits outside every custody episode` | research ran while the holdout was reachable — either before the first quarantine, or in a gap between episodes, or after a restore |
| `expected at least one holdout_quarantined record, found none` | quarantine was never journalled; custody is unproven even if it happened |
| `has a second holdout_quarantined at sequence N while the episode opened at M was never closed` | the journal claims the holdout left the tree while it had never come back |
| `a <event> at sequence N with no open custody episode before it` | the holdout came back without having left |
| `expected at most one holdout_restored record, found 2` | two restores; the holdout came back twice after the field closed and the second episode is unaccounted for |
| `records no trial_accepted events` | this is not the journal the review needs — you are pointed at the wrong file |
| `different canary tokens` | the committed receipt and the **most recent** journalled quarantine describe two different quarantines |

Any of these is a **finding about the tournament**, not about the tool. Record it and stop.

### 3a. The live form, run repeatedly while the research phase is still running

The ordering check above answers "was the holdout out of the tree". This one answers "and is what
is sitting in quarantine still the holdout". They are different questions, and the research phase
is months long, so run this periodically rather than only at the end: a corruption first noticed at
restore is noticed after every team has finished, when the only remaining option is to void the
tournament.

```
uv run python scripts/cup20_quarantine.py verify
```

**Pass:** four things, printed in this order:

```
quarantine IS in effect: neither tree is reachable from the working tree
  acquisition  <digest>  matches the receipt
  sealed       <digest>  matches the receipt
  sealed manifest <digest>  matches tournament/cup20/activation-freeze.json, read at the
                            quarantine location
  canary token matches the receipt, so the review scans for the right string

quarantine VERIFIED: the quarantined bytes are the bytes that left the tree
```

Each line is a layer that fails on its own:

| Layer | What only it can catch |
|---|---|
| absence | a tree back in the working tree, where a team process can name it |
| the two bundle digests | any byte changed, any file added or removed, in **either** tree — this is the only layer that covers the acquisition snapshot at all, since it has no manifest of its own, and the only one that can see the canary being deleted |
| the activation record, sealed root read from quarantine | the seven authorities that are in neither tree (charter, config, implementation, dependency lock, IS manifest, pure-crypto audit, test output), and the sealed manifest measured against what activation bound rather than against the receipt, which was written later |
| the canary token | a token file that has drifted from the receipt — with which check 4 below would scan every workspace for a string that was never planted and report clean |

**Fail:** any of

| Message | Meaning |
|---|---|
| `quarantine is NOT in effect: ['sealed'] are present in the working tree at [...]` | someone put the holdout back. Find out who, and when, before any team continues |
| `QUARANTINE INTEGRITY FAILURE: the quarantined <tree> ... does not match the digest recorded when it was quarantined` | the holdout was modified while out of the working tree. Stop; no result computed against it is valid, and restoring it would put modified data back in every team's reach |
| `activation authority changed: <label>` | read as check 1 — the named authority drifted while the holdout was away |
| `QUARANTINE INTEGRITY FAILURE: ... two different holdouts` | the receipt and the activation record no longer describe the same sealed snapshot |
| `the token at ... does not match the receipt's canary_token_sha256` | the planted token cannot be used as evidence; check 4's token half is unavailable until this is explained |

**`verify --fast`** exists for a scripted poll and is **not** this check. It tests only that the
trees are absent from the working tree and present at the quarantine root, reads no bytes, and
prints a `NOT CHECKED (--fast)` paragraph listing what it did not look at. Do not record a `--fast`
run as evidence that the holdout is intact; it is not evidence about the holdout's bytes at all.

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
from crypto_trade.cup20.quarantine import load_receipt, read_canary_token
receipt = 'tournament/cup20/quarantine-receipt.json'
token = read_canary_token(receipt_path=receipt)
root = Path(load_receipt(receipt)['quarantine_root']).name
for team in sorted(Path('tournament/cup20/teams').glob('team-*')):
    scan = scan_workspace_for_blindness_violations(
        team, team_id=team.name, canary_tokens=(token,), extra_patterns=(root,))
    print(team.name, scan.files_scanned, 'files',
          len(scan.violations), 'violations', len(scan.unscanned), 'unread')
    for v in scan.violations: print('   ', v)
    for u in scan.unscanned: print('    UNREAD', u)"
```

`extra_patterns` carries the quarantine root's directory name, which cannot be frozen into
`FORBIDDEN_PATTERNS` because it is chosen when the tournament starts. The driver passes it; a
manual run that omits it is strictly weaker than the driver and will not flag a team that named
the quarantine path.

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

This is the gate the charter states in §5 layer 3, re-run as evidence rather than as a gate. It is
deliberately the *same function the gate runs*, so what it reports is what the gate would have
reported — which also means it is **weaker than check 4 in three specific ways**, listed below
rather than left to be discovered.

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
**Fail:** any violation tuple, read as `path:line:what-matched`. A violation here is a **pre-flight
disqualification** under charter §5 layer 3, not a discussion.

**What this check does NOT do, though check 4 does:**

- **It never matches the canary token.** `scan_for_blindness_violations` takes no `canary_tokens`
  argument and cannot emit `sealed-canary-token` — the single strongest piece of evidence this
  review can produce is structurally unavailable on this surface. The `HOLDOUT-CANARY-DO-NOT-READ`
  filename pattern still matches, but a team that copied the token's *value* out of the canary
  and left the filename behind is invisible here.
- **It never matches the quarantine root's name**, which is only known at review time.
- **It stops reading a file's content at 256 KiB and does not say which files it skipped.** There
  is no `unscanned` list on this surface, so a large file's content going unread is silent. Check
  4 has the same kind of cap at 8 MiB but reports every file it hit — that report is the only
  place a too-large file is disclosed.

Also unlike check 4, `__pycache__` is excluded here as derived output.

**Why the review as a whole is still sound.** Every nominated candidate lives at
`tournament/cup20/teams/team-NN/candidates/<name>/`, which is *inside* the directory check 4 scans.
So every file this check reads, check 4 also reads — with the token matched by value, with the
quarantine root's name added, with `__pycache__` included, with a 32× larger content cap, and with
anything still too large named under `UNREAD`. Check 4's surface strictly contains this one; that
containment is what closes the three gaps above, and it is asserted by
`tests/cup20/test_workspace_scan.py`, not merely argued here. If check 4 is skipped or reports
`UNREAD`, these gaps are open and this check does not close them.

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

**The driver cannot make that judgement, and does not pretend to.** `PASS 7` from
`cup20_integrity_review.py` means exactly three things: the mount records access times, no file
appeared in the sealed tree, and none vanished. It prints the `accessed` list and passes whatever
is in it, because deciding whether a given read was the organiser's own is not a decision a script
can make. Read the list yourself; a `PASS` here with an unexplained name in `accessed` is a finding
the driver has handed you, not one it has cleared. Note also that check 1 opens every sealed parquet
file, so running this review at all puts them in `accessed`.

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
- **when check 3a was last run before restore, and what it printed.** It is the only evidence that
  the quarantined bytes were still the holdout's bytes during the research phase; the checks above
  run after restore and cannot recover it. If it was never run, say that instead of implying it;
- the sentence that bounds the claim: **custody is demonstrated for the research phase; phase 3
  rests on detection, and the residual in charter §14.8 is not closed by any check above.**

If any check failed, no team advances and the paper desk does not open until the failure is
explained in the tournament record. Charter §1.1 already accepts "no winner" as a legitimate
outcome; a tournament that cannot show its holdout was untouched has produced exactly that.
