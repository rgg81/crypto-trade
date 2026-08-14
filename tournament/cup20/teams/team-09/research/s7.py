import time, pandas as pd, numpy as np
from sweep import run
PG=("ret","size","liq")
cfgs=[]
combos=[(("bigp",),(1.0,)),(("per",),(1.0,)),(("imbsml",),(1.0,)),
        (("bigp","per"),(1.0,1.0)),(("bigp","per"),(1.0,0.5)),(("bigp","per"),(0.5,1.0)),
        (("bigp","imbsml"),(1.0,1.0)),(("bigp","imbsml"),(1.0,0.5)),
        (("bigp","per","imbsml"),(1.0,0.5,0.5)),(("bigp","covqv"),(1.0,0.5))]
for kinds,wts in combos:
    for w in (63,90,126):
        for hold in (42,63,90):
            for k in (4,5,6):
                cfgs.append(dict(kinds=kinds,weights=wts,w=w,purge=PG,k=k,hold=hold,cadence=1,phase=0))
print(len(cfgs)); t=time.time(); df=run(cfgs,workers=18,out='sweep_combo.csv'); print('%.0fs'%(time.time()-t))
pd.set_option('display.width',280)
print(df.groupby(['kinds','weights'])[['sharpe1','sharpe2','G','worst_fold','f1','f2','f3','f4','dd2','turn']].mean().round(3).sort_values('G',ascending=False).to_string())
print()
cols=['kinds','weights','w','hold','k','sharpe1','sharpe2','vol','dd1','dd2','turn','edge_bps','f1','f2','f3','f4','worst_fold','pq2','G','short_gross']
print(df.sort_values('G',ascending=False).head(15)[cols].to_string(index=False))
