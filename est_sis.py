import sys, json
import os
sys.path.insert(0, os.environ.get("ESTIMATOR_DIR", "lattice-estimator"))  # malb/lattice-estimator, commit 53da598
from sage.all import log, oo
from estimator import SIS
N=256; d=int(sys.argv[1]); q=int(sys.argv[2]); beta=2**float(sys.argv[3]); L=1
r=SIS.estimate(SIS.Parameters(n=d*N,q=q,length_bound=beta,m=(2*d+L)*N,norm=2),quiet=True)
print(json.dumps({"d":d,"log2q":float(log(q,2)),"log2beta":float(sys.argv[3]),"sis":{k:(float(log(v["rop"],2)) if v["rop"]!=oo else None) for k,v in r.items()}}))
