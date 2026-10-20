"""Hardness of the national parameter set (d = 8, q = 2^46 - 1103) under four cost models.

MATZOV (classical, as in est_nat.py / est_sis.py), MATZOV with the quantum nearest-neighbour cost of
Albrecht, Gheorghiu, Postlethwaite and Schanck (ASIACRYPT 2020, depth x width), and core-SVP,
2^(0.292 beta) classical and 2^(0.265 beta) quantum (Alkim, Ducas, Poppelmann, Schwabe, USENIX
Security 2016). Same instance as est_nat.py and est_sis.py: M-LWE with n = dN, m = (d+1)N, secret and
error D_1; M-SIS with m = (2d+1)N columns, Euclidean norm, bound beta_SIS from param_report.

usage: ESTIMATOR_DIR=/path/to/lattice-estimator sage -python est_models.py MODEL
  MODEL one of MATZOV, MATZOV_q, ADPS16, ADPS16_q
"""
import json, os, sys, time

sys.path.insert(0, os.environ.get("ESTIMATOR_DIR", "lattice-estimator"))  # malb/lattice-estimator, commit 53da598
from sage.all import log, oo
from estimator import LWE, SIS, ND, RC
from estimator.reduction import ADPS16, MATZOV

N, D, Q, BETA = 256, 8, 2**46 - 1103, 66281600000000.0  # beta_SIS = 2^45.914 (param_report 6480000 7 4 1 -1 8 q 1 64)
MODELS = {"MATZOV": RC.MATZOV, "MATZOV_q": MATZOV(nn="quantum"), "ADPS16": RC.ADPS16, "ADPS16_q": ADPS16(mode="quantum")}


def bits(res):
    return {k: (float(log(v["rop"], 2)) if v["rop"] != oo else None) for k, v in res.items()}


model = sys.argv[1]
t0 = time.time()
lwe = LWE.estimate(LWE.Parameters(n=D * N, q=Q, Xs=ND.DiscreteGaussian(1.0), Xe=ND.DiscreteGaussian(1.0), m=(D + 1) * N),
                   red_cost_model=MODELS[model], deny_list=("arora-gb", "bkw"), quiet=True)
sis = SIS.estimate(SIS.Parameters(n=D * N, q=Q, length_bound=BETA, m=(2 * D + 1) * N, norm=2),
                   red_cost_model=MODELS[model], quiet=True)
lb, sb = bits(lwe), bits(sis)
print(json.dumps({"d": D, "q": Q, "model": model, "estimator": "53da598",
                  "hiding": min(v for v in lb.values() if v), "binding": min(v for v in sb.values() if v),
                  "lwe": lb, "sis": sb, "seconds": round(time.time() - t0)}))
