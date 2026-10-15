"""Effect of probabilistic aggregation (kappa attempts per round, R rounds before the deadline) on P_fail."""
import json, os
from model import evaluate
S = json.load(open("results/scenarios.json"))
A, C = S["a_grid"][1], S["c_illustrative"]
out = {}
for (n, t) in [(5, 3), (7, 4), (9, 5)]:
    for kappa in (4, 8, 16):
        for R in (1, 3, 5, 10):
            out[f"n={n},t={t},kappa={kappa},R={R}"] = evaluate(n, t, A, C, rounds=R, kappa=kappa)[0]
    out[f"n={n},t={t},deterministic"] = evaluate(n, t, A, C)[0]
json.dump(out, open(os.path.join("results", "rounds.json"), "w"), indent=1)
for k, v in out.items(): print(f"{k:32s} {v:.2e}")

# Separate tallies per constituency: the same S authorities run G tallies; an authority that is unavailable
# or corrupted is so for the whole election, while aborts are independent per tally and tally attempt.
# The election fails if any of the G tallies fails within its R tally attempts.
from math import comb
from model import round_success


def p_fail_split(n, t, a, c, G, R, kappa):
    p = (1 - a) * (1 - c)
    return sum(comb(n, S) * p ** S * (1 - p) ** (n - S) * (1 - round_success(S, t, kappa=kappa, rounds=R) ** G)
               for S in range(n + 1))


split = {}
for (n, t) in [(7, 4), (9, 5)]:
    for kappa in (4, 8, 16):
        for R in (1, 3):
            for G in (1, 125):
                split[f"n={n},t={t},kappa={kappa},R={R},G={G}"] = p_fail_split(n, t, A, C, G, R, kappa)
assert abs(split["n=7,t=4,kappa=8,R=3,G=1"] - out["n=7,t=4,kappa=8,R=3"]) < 1e-15
out["split_constituencies"] = split
json.dump(out, open(os.path.join("results", "rounds.json"), "w"), indent=1)
for k, v in split.items(): print(f"{k:40s} {v:.2e}")

# only t = 4 of 7 authorities remain (three failed together): failure of a single tally and of 125 tallies
only_t = {}
for kappa in (8, 16):
    f1 = 1 - round_success(4, 4, kappa=kappa, rounds=3)
    only_t[f"kappa={kappa},R=3"] = {"single": f1, "125 tallies": 1 - (1 - f1) ** 125}
out["only_t_remaining_n7_t4"] = only_t
json.dump(out, open(os.path.join("results", "rounds.json"), "w"), indent=1)
print(only_t)
