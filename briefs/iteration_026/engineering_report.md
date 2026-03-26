# Engineering Report: Iteration 026
Added 7 engineered features (3 calendar + 4 interaction) via runtime injection in lgbm.py.
113 total features (106 parquet + 7 injected). OOS: Sharpe +0.28, WR 38.3%, PF 1.04.

## User Feedback (for future iterations)
Features should be added to the parquet generation pipeline (`src/crypto_trade/features/`), not injected at runtime. Regenerating parquet is cleaner and avoids complex injection logic in lgbm.py.
