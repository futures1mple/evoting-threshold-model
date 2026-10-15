import sys, json, time
import os
sys.path.insert(0, os.environ.get("ESTIMATOR_DIR", "lattice-estimator"))  # malb/lattice-estimator, commit 53da598
from sage.all import log, oo
from estimator import LWE, SIS, ND, RC
N=256
def bits(res): return {k:(float(log(v["rop"],2)) if v["rop"]!=oo else None) for k,v in res.items()}
d=int(sys.argv[1]); q=int(sys.argv[2]); beta=float(sys.argv[3]); L=1
t0=time.time()
lwe=LWE.estimate(LWE.Parameters(n=d*N,q=q,Xs=ND.DiscreteGaussian(1.0),Xe=ND.DiscreteGaussian(1.0),m=(d+L)*N),red_cost_model=RC.MATZOV,quiet=True)
sis=SIS.estimate(SIS.Parameters(n=d*N,q=q,length_bound=beta,m=(2*d+L)*N,norm=2),quiet=True)
lb,sb=bits(lwe),bits(sis)
print(json.dumps({"d":d,"q":q,"log2q":float(log(q,2)),"log2beta":float(log(beta,2)),"hiding":min(v for v in lb.values() if v),"binding":min(v for v in sb.values() if v),"lwe":lb,"sis":sb,"sec":round(time.time()-t0)}))
