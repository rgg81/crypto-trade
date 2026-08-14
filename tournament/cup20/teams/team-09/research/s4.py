import time, pandas as pd, numpy as np
from sweep import run
cfgs=[]
for kind in ("imbsml","imbbig","per","bigp","lvl"):
    for w in (42,90,180):
        for hold in (21,42,63,90,126):
            for k in (4,5,6):
                cfgs.append(dict(kinds=(kind,),weights=(1.0,),w=w,purge=("ret","size","liq"),
                                 k=k,hold=hold,cadence=1,phase=0))
print(len(cfgs),'configs'); t=time.time()
df=run(cfgs,workers=16,out='sweep_s4.csv'); print('%.0fs'%(time.time()-t))
pd.set_option('display.width',270)
cols=['kinds','w','hold','k','sharpe1','sharpe2','vol','dd1','dd2','turn','edge_bps','worst_fold','median_fold','pq2','G','short_gross']
print(df.sort_values('G',ascending=False).head(20)[cols].to_string(index=False))
print(); print(df.groupby('kinds')[['sharpe1','sharpe2','G','worst_fold','turn']].mean().sort_values('G',ascending=False).to_string())
print(); print(df.groupby(['kinds','w'])[['sharpe2','G','worst_fold']].mean().to_string())
