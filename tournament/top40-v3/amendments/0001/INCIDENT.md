# Top40 V3 incident 0001: mixed UTC metric bounds

Status: confirmed organizer-infrastructure failure; no metric observation disclosed

## What happened

The first V3 training invocation accepted Team 04's grandfathered incumbent and completed the
expensive target-generation and execution work, but failed during post-simulation metric
projection. The frozen runner sliced a UTC `DatetimeIndex` with two string labels in different
forms: an offset-aware start (`2020-02-03T00:00:00Z`) and a date-only end (`2022-06-30`). Pandas
rejected that mixed-offset slice with `ValueError: Both dates must have the same UTC offset`.

Independent review then found the next deterministic boundary mismatch before any retry: the
runner would publish the train-window start in timestamp form while the frozen coaching schema
requires the date-only identity `2020-02-03`.

Both defects are representation errors after portfolio simulation. They do not change a strategy,
market row, fill, cost, return, threshold, seed, or eligibility rule.

## Immutable evidence

- Parent Phase-0 internal record SHA-256:
  `4de6efcfb10cab132d3f6430edbaeee7c3070998babec59e009e0175bdc4062f`
- Parent Phase-0 file SHA-256:
  `a4e9b4a0593c65bc94b5eb96858a8e809da803131f103e7ee881e2a13a9cde07`
- Accepted request SHA-256:
  `68ec70faf91c82a7f689484f3cd0106e4570569d15bf02823c7cf8aafe59f08f`
- Failed terminal SHA-256 and activation journal head:
  `1737d4431198669b1d5d64962e6d04052620a6e69175eb8f20b029f89b539d64`
- Candidate source archive SHA-256:
  `5f9fe7938315dfc59583cf1265d79c453065b1d8202c12984261fc21e08df60f`
- Candidate source-bundle SHA-256:
  `e58b2f905a70acfd88d6450f9fe394d642aacd7b7b61d1848f969f1c6ffe6cfb`
- Historical-evidence commit: `d1b4f7e233efbdc5cf85d6fff58c2606e40bee8f`

The terminal record has `metric_packet_sha256 = null`, an empty gate vector, and no artifact
hashes. No Team 04 lab output directory was published. The only report-side file is the immutable
source archive accepted before execution.

## Accounting and fairness

The failed request remains Team 04 run sequence 1 and material trial 1. It is never deleted,
renumbered, relabelled, or converted into a success. Amendment 0001 does not activate a special
training replay mode and does not reset any counter. A later invocation is an ordinary, fully
logged material trial 2 with a new evaluator-authority hash.

No other team will run under the defective evaluator. The amendment is frozen before any metric
packet exists, so its scope cannot be selected in response to strategy performance.
