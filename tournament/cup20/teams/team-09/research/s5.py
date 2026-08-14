import time, pandas as pd, numpy as np
from sweep import run
cfgs=[]
for kind in ("covats","covatsn","covqv","covnt","bigp"):
    for w in (21,42,63,90,126,180):
        for hold in (42,63,90):
            for k in (5,6):
                cfgs.append(dict(kinds=(kind,),weights=(1.0,),w=w,purge=("ret","size","liq"),
                                 k=k,hold=hold,cadence=1,phase=0))
print(len(cfgs),'configs'); t=time.time()
df=run(cfgs,workers=16,out='sweep_s5.csv'); print('%.0fs'%(time.time()-t))
pd.set_option('display.width',270)
print(df.groupby(['kinds','w'])[['sharpe1','sharpe2','G','worst_fold','dd2','turn']].mean().round(3).to_string())
print()
cols=['kinds','w','hold','k','sharpe1','sharpe2','vol','dd1','dd2','turn','edge_bps','worst_fold','median_fold','pq2','G','short_gross']
print(df.sort_values('G',ascending=False).head(14)[cols].to_string(index=False))
