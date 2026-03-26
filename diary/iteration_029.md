# Iteration 029 Diary - 2026-03-26 — EXPLORATION
## Merge Decision: NO-MERGE
OOS Sharpe -0.94 < baseline +1.33. Long-period-only features worse.
## Type: EXPLORATION (feature frequency filtering)
## Results: OOS Sharpe -0.94, WR 35.3%, PF 0.89. IS Sharpe -0.54.
## Lesson: Short-period features (RSI_5, ROC_3) carry useful signal despite being noisy. The model needs BOTH short and long period features — removing either hurts.
## Exploration/Exploitation Tracker: Last 10 [X, X, X, E, E, E, E, X-next, ?, ?] → 4/7 = 57%
