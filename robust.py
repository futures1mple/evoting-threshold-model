"""Robustness of the qualitative conclusions over the calibration grid (results/robustness.json).

R1  the best threshold t* (largest tolerable c) lies within one of (n+1)/2, for every n = 3..15 for which
    some threshold is feasible, every a in the 95 % interval and both pairs of targets; and its direction
    (below (n+1)/2 only at high a, above only with strict targets at low a).
R1s the same at the stress value a = 11.8 %.
R2  n-of-n never meets the availability target (also analytic: P_fail(n, n) >= 1 - (1 - a)^n >= a > eps_f).
R3  drawing majority-threshold authorities from distinct organisations lowers both P_fail and P_breach,
    for organisation shock probabilities 0.1 %, 1 % and 10 %, n = 6 and 9, all (a, c) on the grid.
"""
import json
from model import evaluate
S = json.load(open("results/scenarios.json"))
A, C = S["a_grid"], S["c_grid"]
res = {"R1_tstar_within_one_of_(n+1)/2": [], "R1s_stress": [], "R1_equal_majority": [], "R1_below_majority": [], "R1_above_majority": [],
       "R2_n_of_n_fails_availability": [], "R3_diversity_wins": []}
for key, v in S["tstar"].items():
    tn, a, n = key.split("|")
    a = float(a[2:]); n = int(n[2:])
    if v["c_max"] < 1e-3:                     # treat c_max below 0.1 % as infeasible
        continue
    t = v["t"][0]
    dev = t - (n + 1) / 2
    ok = abs(dev) <= 1
    if a == S["a_stress"]:
        res["R1s_stress"].append(ok)
        continue
    res["R1_tstar_within_one_of_(n+1)/2"].append(ok)
    m = n // 2 + 1
    res["R1_equal_majority" if t == m else "R1_below_majority" if t < m else "R1_above_majority"].append(f"{key}|t*={t}")
for tn, (ef, eb) in S["targets"].items():
    for a in A:
        for c in C:
            for n in range(2, 16):
                res["R2_n_of_n_fails_availability"].append(evaluate(n, n, a, c)[0] > ef)
for sh in (1e-3, 1e-2, 1e-1):
    for a in A:
        for c in C:
            for n, conc in ((6, [0, 0, 1, 1, 2, 2]), (9, [0, 0, 0, 1, 1, 1, 2, 2, 2])):
                t = n // 2 + 1
                f1, b1 = evaluate(n, t, a, c, groups=conc, A=[sh] * 3, K=[sh] * 3)
                f2, b2 = evaluate(n, t, a, c, groups=list(range(n)), A=[sh] * n, K=[sh] * n)
                res["R3_diversity_wins"].append(f2 < f1 and b2 < b1)
summary = {k: (f"{sum(v)}/{len(v)}" if v and isinstance(v[0], bool) else v) for k, v in res.items()}
summary["R1_counts_equal_below_above"] = [len(res["R1_equal_majority"]), len(res["R1_below_majority"]), len(res["R1_above_majority"])]
summary.pop("R1_equal_majority")
json.dump(summary, open("results/robustness.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
