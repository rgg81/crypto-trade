import time, pandas as pd, numpy as np
from sweep import run
PG=("ret","size","liq")
combos=[(("bigp","imbsml"),(1.0,1.0)),(("bigp","imbeq"),(1.0,1.0)),(("coveq","imbeq"),(1.0,1.0)),
        (("coveq","imbsml"),(1.0,1.0)),(("bigp","per"),(1.0,1.0)),(("imbeq",),(1.0,)),
        (("imbsml",),(1.0,)),(("bigp",),(1.0,)),(("coveq",),(1.0,))]
cfgs=[dict(kinds=k,weights=w,w=ww,purge=PG,k=kk,hold=h,cadence=1,phase=0)
      for k,w in combos for ww in (63,90) for h in (63,90) for kk in (4,5)]
df=run(cfgs,workers=18,out='sweep_ctrl.csv')
pd.set_option('display.width',280)
print(df.groupby(['kinds','weights'])[['sharpe1','sharpe2','G','worst_fold','f1','f2','f3','f4','dd2','turn','edge_bps','short_gross']].mean().round(3).sort_values('G',ascending=False).to_string())
