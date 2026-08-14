import pandas as pd, numpy as np
from sweep import run
PG=("ret","size","liq"); C=(("bigp","imbsml"),(1.0,1.0))
base=dict(kinds=C[0],weights=C[1],purge=PG,cadence=1,phase=0)
cfgs=[]
for w in (54,63,72,81,90,99,108,117,126,144):
    for nb in (54,72,90,108,126):
        for hold in (42,54,63,72,84,90):
            for k in (3,4,5,6):
                cfgs.append(dict(base,w=w,nb=nb,hold=hold,k=k))
print(len(cfgs)); df=run(cfgs,workers=18,out='sweep_surface.csv')
pd.set_option('display.width',280)
for ax in ('w','nb','hold','k'):
    print('--- by',ax); print(df.groupby(ax)[['sharpe2','G','worst_fold','dd2','turn']].agg(['mean','min']).round(3).to_string())
print('--- top'); 
cols=['w','nb','hold','k','sharpe1','sharpe2','dd1','dd2','vol','turn','edge_bps','f1','f2','f3','f4','worst_fold','pq2','G','short_gross']
print(df.sort_values('G',ascending=False).head(12)[cols].to_string(index=False))
