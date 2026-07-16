# Amendment 0005 declared-score adapter contract

This draft contract applies only to a prospective Team04–Team10 candidate that opts in before its
material development registration. It does not retrofit an existing candidate.

`strategy.py` directly imports `score_boundary` and calls it exactly once on each manifest-scheduled
decision:

```python
from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary
scores = score_boundary(scores)
```

The candidate declares that the call follows score transformation and precedes selection,
weighting, caps, and risk controls. Runtime checks hook identity, schedule, one-call behavior,
finite built-in dictionary bytes, eligibility, mutation, replay, and target equivalence. It cannot
distinguish the operative ranking signal from a decoy/transient dictionary. A hash-bound static
source review must separately approve that semantic claim.

The registration contains exactly:

```json
{
  "_top40_v2_score_adapter": {
    "adapter_id": "top40-v2-declared-score-boundary-v1",
    "manifest_sha256": "<lowercase SHA-256>",
    "schema_version": 1
  }
}
```

The derived canonical manifest is
`tournament/top40-v2/teams/<team>/score-adapters/<candidate>.json`. It declares development stage,
hook `strategy.score_boundary`, boundary
`candidate-declared-post-transform-pre-selection-weight-cap-risk`, UTC anchor/interval, fixed
open-to-open label/statistic semantics, holding horizon, minimum pairs, score description, and
`semantic_coupling_review_sha256`.

The derived review is
`tournament/top40-v2/teams/<team>/score-adapters/<candidate>.semantic-coupling-review.json`. Its
canonical fixed attestation binds team/family/candidate, registered strategy SHA-256, hook,
declared boundary, reviewer/time, approval, five static findings (including no decoy/transient path
found), and the explicit limitation `static-review-attestation-not-runtime-semantic-proof`.

Both files are canonical pretty JSON, unique immutable first-adds, and exact bytes in the required
historical trees. The manifest schedule interval and holding horizon are multiples of eight hours
from 8 through 168. Labels use the executable open at `t` and `t + horizon`; endpoints touching or
crossing a fold end are purged. Pearson is globally pooled and repeated in each frozen fold.

All output is non-material, charges no team budget, and is never an automatic qualification gate.
