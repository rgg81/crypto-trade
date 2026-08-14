import pandas as pd, numpy as np, itertools
from sweep import run
PG=("ret","size","liq"); C=(("bigp","imbsml"),(1.0,1.0))
base=dict(kinds=C[0],weights=C[1],purge=PG,cadence=1,phase=0)
# extend nb upward to see whether 126 is a slope or a plateau
cfgs=[dict(base,w=w,nb=nb,hold=h,k=k) for w in (72,81,90) for nb in (108,126,144,162,180)
      for h in (63,72,84) for k in (3,4,5)]
df=run(cfgs,workers=18,out='sweep_nb.csv')
pd.set_option('display.width',280)
print(df.groupby('nb')[['sharpe2','G','worst_fold','dd2','turn']].agg(['mean','min']).round(3).to_string())
