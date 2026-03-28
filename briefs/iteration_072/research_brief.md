# Iteration 072 — Research Brief

**Type**: EXPLORATION (calendar features)
**Date**: 2026-03-28
**Previous**: Iteration 068 (MERGE — cooldown=2, OOS Sharpe +1.84)

---

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

---

## Hypothesis

Add 2 calendar features (hour of day, day of week) — minimal dimensionality increase (106→108). Crypto markets have time-of-day patterns:
- 00:00 UTC: Asian session open
- 08:00 UTC: European session open
- 16:00 UTC: US session open

These sessions have different volatility and trend characteristics.

## New Features

| Feature | Values | Rationale |
|---------|--------|-----------|
| `cal_hour_norm` | 0.0/0.33/0.67 (for 0/8/16 UTC) | Session identification |
| `cal_dow_norm` | 0.0-1.0 (Mon-Sun) | Weekend/weekday patterns |

Both normalized to [0,1] for scale-invariance.

## What stays the same
Everything identical to iter 068 except 108 features (106 + 2 calendar).
