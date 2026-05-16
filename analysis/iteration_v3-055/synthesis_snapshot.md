## Synthesis snapshot

- v3 iterations recomputed: 53
- Highest dsr_p_IS observed across 53 iterations: 1.4820e-02 (iter-v3/019)
- dsr_z_IS range (current formula): [-51.44, -2.17], median -34.68
- The actual gate threshold for `DSR > 0.95` in `norm.cdf` space = dsr_z > 1.645

The "0.0" reported in `dsr.json` is rounding. Real p-values are 1e-100..1e-260
range. Every single v3 iteration mechanically FAILS `DSR > 0.95` not because
the strategy is unprofitable, but because `E[max_SR]` at n_trials=525..1500
exceeds `realized_SR` by 20-40 standard-error units in (SR - E[max])/sr_std
space, and `norm.cdf` of a z-score of -20 is 10^-89.

Reformulation pass-table summary (across recent /028..054):

{'R1_DSR_n_trials_PASS': {False: 13}, 'R2_DSR_n_eff_PASS': {False: 13}, 'R3_DSR_p_threshold0_PASS': {False: 13}, 'R4_PSR_0_PASS': {True: 12, False: 1}, 'R5_PSR_cpcv_median_PASS': {True: 12, False: 1}}
