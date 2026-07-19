# Team 02 buffered fast-breakout baseline

This candidate scores each eligible coin from its location in a recent high-low channel and a short return-confirmation window. A move receives full strength only when several completed closes remain on the same side of the channel midpoint and momentum agrees; otherwise its score is heavily attenuated. This is a direct false-breakout control, not a sign inversion.

The portfolio uses broad sign-respecting sleeves, modest gross exposure, and two fixed decisions per week. A side with too few confirmed signals remains cash rather than taking an opposing-sign rank position. A tight turnover limit, fast loss stop, and finite holding window constrain the main risks of the faster signal.

The first neighborhood should vary channel length, confirmation length, and refresh frequency while keeping all other controls frozen.
