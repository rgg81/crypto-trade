---
name: quant-iteration
description: "DEPRECATED — legacy v1 iteration skill, superseded by quant-iteration-v1 (refactored 2026-05-23). This stub redirects to the new v1 skill. The legacy v1 workflow that ran for 186 iterations (iteration/001 through iteration/186) is preserved in git history; the v0.186 baseline was found to have a walk-forward look-ahead bias (fixed at walk_forward.py:113 in commit 5566a69). New v1 iterations use quant-iteration-v1 with the corrected baseline in BASELINE_V1.md, plus v3 rigor (CPCV/DSR/PBO/PSR/ADF/IC), four QR↔Critic dynamic improvements (Constructive Critic, BLOCK-PENDING-FIX, QR Axis Rotation Discipline, LightGBM Master agent), and new phases 4.5 / 6.0 / 7.4. Use this stub when the user types `/quant-iteration` (without -v1 suffix) — the user likely wants the new v1 workflow."
---

# Quant Iteration Skill — DEPRECATED, Use quant-iteration-v1

This skill file is a **deprecation stub** as of the 2026-05-23 v1 refactor.

## What changed

The original `quant-iteration` skill governed the v1 track for 186 iterations (`iteration/001` through `iteration/186`). In May 2026, we discovered a serious walk-forward look-ahead bias at the train/test boundary (`walk_forward.py` had `train_end_ms = test_start_ms` with no embargo, allowing training labels to scan forward into the test window through the triple-barrier labeler's 7-day forward horizon). The fix landed at `walk_forward.py:113` in commit `5566a69`.

Re-running the v0.186 baseline under the corrected walk-forward produces materially worse OOS numbers — the historical headline (OOS Sharpe +1.735) was inflated by leaked labels. The corrected baseline (OOS Sharpe +0.827) is preserved in `BASELINE_V1.md`.

The v1 track was **refactored on 2026-05-23** to:
1. Restart with the corrected baseline as the formal anchor
2. Bring v1 up to v3's rigor (CPCV / DSR / PBO / PSR / ADF / IC / meta-labeling / fractional Kelly)
3. Add four QR↔Critic dynamic improvements diagnosed from the v3 cycle-7 forensic:
   - Constructive Critic — every BLOCK verdict includes a Path Forward section
   - BLOCK-PENDING-FIX — one rerun chance for isolated defects
   - QR Axis Rotation Discipline — mandatory family rotation every 5 EXPLORATIONs
   - LightGBM Master agent — read-only ML specialist firing Phase 4.5 (pre-design) and Phase 7.4 (post-mortem)
4. Add three new phases: 4.5 (LM Master pre-design), 6.0 (Critic pre-flight), 7.4 (LM Master post-mortem)

The new skill is at `.claude/commands/quant-iteration-v1.md`. Trigger it with `/quant-iteration-v1` or any of the v1-aware keywords (iter-v1/NNN, BASELINE_V1, briefs-v1, diary-v1, reports-v1, LightGBM Master, etc.).

## Migration

When the user types `/quant-iteration` (without the `-v1` suffix), interpret it as `/quant-iteration-v1` — they almost certainly want the new v1 workflow, not the deprecated legacy.

For new iterations:
- Use `iter-v1/NNN` not `iteration/NNN`
- Reference `BASELINE_V1.md` not `BASELINE.md`
- Write briefs to `briefs-v1/iteration_v1-NNN/`
- Write diaries to `diary-v1/iteration_v1-NNN.md`
- Write reports to `reports-v1/iteration_v1-NNN/`
- Use branches `iteration-v1/NNN` (off `quant-research`)
- Tag merges as `v0.v1-NNN`

The 186 historical iterations are preserved in git history (`iteration/NNN` branches and `v0.NNN` tags) for archaeological reference. The legacy `BASELINE.md` is kept for backward-compatible reads but is no longer the canonical v1 anchor — `BASELINE_V1.md` is. The legacy `ITERATION_PLAN_8H.md` is similarly preserved.

## See Also

- **`.claude/commands/quant-iteration-v1.md`** — the canonical v1 skill (refactored 2026-05-23)
- `.claude/commands/quant-iteration-v2.md` — v2 (diversification track, unchanged)
- `.claude/commands/quant-iteration-v3.md` — v3 (rigor track, unchanged)
- `BASELINE_V1.md` — current v1 baseline (corrected walk-forward stats)
- `BASELINE.md` — legacy v1 baseline (kept for reference; superseded)
- `ITERATION_PLAN_8H_V1.md` — v1 workflow doc (refactored)
- `ITERATION_PLAN_8H.md` — legacy v1 workflow doc (kept for reference; superseded)
- `.claude/agents/lightgbm-master.md` — new LightGBM Master agent (used in v1 Phase 4.5 / 7.4)
- `.claude/agents/quant-critic.md` — Critic agent (updated 2026-05-23 with Path Forward, BLOCK-PENDING-FIX, v1 awareness, Phase 6.0 pre-flight)
- `.claude/agents/quant-researcher.md` — Researcher agent (updated 2026-05-23 with v1 awareness, Axis Rotation Discipline, HIGH-RISK declaration)
- `.claude/agents/quant-engineer.md` — Engineer agent (updated 2026-05-23 with v1 awareness, Phase 6.0 Critic dispatch)

When the user invokes this skill, immediately invoke `quant-iteration-v1` instead.
