import time, pandas as pd, numpy as np
from sweep import run
PG=("ret","size","liq")
cfgs=[]
combos=[(("bigp","imbsml"),(1.0,1.0)),(("bigp","lvl"),(1.0,1.0)),(("bigp","imbbig"),(1.0,1.0)),
        (("bigp","per"),(1.0,1.0)),(("imbsml","lvl"),(1.0,1.0)),(("bigp","imbsml"),(1.0,1.5)),
        (("bigp","imbsml"),(1.5,1.0)),(("covqv","imbsml"),(1.0,1.0)),(("covnt","imbsml"),(1.0,1.0))]
for kinds,wts in combos:
    for w in (63,90):
        for hold in (63,90):
            for k in (4,5):
                cfgs.append(dict(kinds=kinds,weights=wts,w=w,purge=PG,k=k,hold=hold,cadence=1,phase=0))
df=run(cfgs,workers=18,out='sweep_s8.csv')
pd.set_option('display.width',280)
print(df.groupby(['kinds','weights'])[['sharpe1','sharpe2','G','worst_fold','f1','f2','f3','f4','dd2','turn','edge_bps','short_gross']].mean().round(3).sort_values('G',ascending=False).to_string())
