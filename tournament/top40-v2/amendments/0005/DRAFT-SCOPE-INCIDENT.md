# Amendment 0005 draft-scope incident

Date: `2026-07-16`

The infrastructure drafter was instructed not to inspect team namespaces. While looking for an
organizer architecture report, it ran this incorrectly pruned filename search:

```text
find . -path './team-*' -prune -o -path './.git' -prune -o -type f -print | rg -i 'amendment.?5|score.*adapter|architecture|diagnostic' | sort
```

The command printed pathnames only. It did not print or open file contents. The visibly printed
team-associated paths were:

- `tournament/top40-v2/teams/team-01/development_diagnostics_rdf_ref_001.json`
- `tournament/top40-v2/teams/team-01/post_result_diagnostics_rdf_core_h14_k3_g05_r1.json`
- `tournament/top40-v2/teams/team-01/post_result_diagnostics_rdf_core_h21_k3_g10.json`
- `tournament/top40-v2/teams/team-02/post_result_diagnostics_team_02_fir_reference_001.json`
- `tournament/top40-v2/teams/team-03/POST_RESULT_DIAGNOSTICS.md`
- `tournament/top40-v2/teams/team-04/pivot-01/organizer_score_adapter.py`
- `tournament/top40-v2/teams/team-05/SCORE-ADAPTER-CONTRACT.md`
- `reports-top40-v2/team-04/post-result/team-04-utc-reference-001-diagnostics.md`
- `src/crypto_trade/tournament/score_adapters/team01_rdf_v1.py`
- `src/crypto_trade/tournament/score_adapters/__pycache__/team01_rdf_v1.cpython-313.pyc`

No team content was incorporated and no team namespace was edited by the A5 drafter. The A5 design
came from the organizer-supplied architecture summary and shared organizer infrastructure. This was
an organizer-infrastructure task, not a competing team clean room, so the pathname-only exposure
does not contaminate a team submission. It remains a review finding because it violated the
drafter's narrower assigned scope and demonstrates that the draft's path hardening requires
independent scrutiny.
