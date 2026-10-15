"""Scenario computations for the (n, t) model. Writes results/scenarios.json.

Unavailability a: empirical anchor (results/base_rates.json): pooled point estimate 2.08 %,
  exact 95 % interval [0.25 %, 7.32 %] -> grid A_GRID = (lower bound, estimate, upper bound);
  stress value A_STRESS = 11.8 % (largest upper bound of a single source, Swiss data alone).
Corruption c: no empirical data. The analysis is therefore inverted: for each (n, t) we compute the
  largest per-authority corruption probability c_max that still meets the targets (tolerable c).
  Tables over a c grid are illustrative only, and the robustness checks show that the qualitative
  conclusions hold on the whole grid.
"""
import json, os
from model import evaluate, evaluate_corr, feasible

H = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(H, "results")
os.makedirs(OUT, exist_ok=True)
NMAX = 15
BR = json.load(open(os.path.join(OUT, "base_rates.json")))["pooled"]
A_LO, A_MID, A_HI = round(BR["ci95"][0], 4), round(BR["estimate"], 4), round(BR["ci95"][1], 4)
A_GRID = [A_LO, A_MID, A_HI]
A_STRESS = 0.118
RHO_GRID = [0.0, 0.01, 0.05, 0.1, 0.2]          # intra-class correlation of the exchangeable model
SHOCK_GRID = [1e-3, 1e-2, 1e-1]                 # organisation shock probabilities (alpha_g = gamma_g)
C_GRID = [0.005, 0.01, 0.02, 0.05]
C_ILL = 0.01                                   # illustrative value for the heatmap and group figures
TARGETS = {"moderate": (1e-3, 1e-4), "strict": (1e-4, 1e-6)}


def best(a, c, eps_f, eps_b, **kw):
    feas = feasible(NMAX, a, c, eps_f, eps_b, **kw)
    if not feas:
        return None
    n = min(x[0] for x in feas)
    ts = [x[1] for x in feas if x[0] == n]
    tm = ts[len(ts) // 2]
    pf, pb = next((x[2], x[3]) for x in feas if x[0] == n and x[1] == tm)
    return {"n": n, "t_min": min(ts), "t_max": max(ts), "t_mid": tm, "P_fail": pf, "P_breach": pb}


def c_max(n, t, a, eps_f, eps_b, **kw):
    """Largest c in [0, 0.5] with P_fail <= eps_f and P_breach <= eps_b (both increase with c);
    returns 0.0 if even c = 0 fails the availability target."""
    if evaluate(n, t, a, 0.0, **kw)[0] > eps_f:
        return 0.0
    lo, hi = 0.0, 0.5
    for _ in range(60):
        mid = (lo + hi) / 2
        pf, pb = evaluate(n, t, a, mid, **kw)
        if pf <= eps_f and pb <= eps_b:
            lo = mid
        else:
            hi = mid
    return lo


def c_max_corr(n, t, a, eps_f, eps_b, rho, rho_a, iters=30):
    """Tolerable c under the exchangeable model (bisection on c)."""
    if evaluate_corr(n, t, a, 0.0, rho, rho_a)[0] > eps_f:
        return 0.0
    lo, hi = 0.0, 0.5
    for _ in range(iters):
        mid = (lo + hi) / 2
        pf, pb = evaluate_corr(n, t, a, mid, rho, rho_a)
        if pf <= eps_f and pb <= eps_b:
            lo = mid
        else:
            hi = mid
    return lo


PRACTICE = {"Helios 3-of-3": (3, 3), "Swiss Post 4-of-4": (4, 4), "Belenios FAQ 2-of-3": (3, 2),
            "ElectionGuard / iVote 3-of-5": (5, 3), "Estonia 5-of-9": (9, 5), "Norway 2013 6-of-9": (9, 6)}


def main():
    data = {"a_grid": A_GRID, "a_stress": A_STRESS, "rho_grid": RHO_GRID, "c_grid": C_GRID, "c_illustrative": C_ILL, "targets": TARGETS}
    # 1. smallest n over the grid (illustrative), deterministic tally and with 3 rounds, kappa = 8
    for label, kw in (("min_n", {}), ("min_n_rounds3_k8", {"rounds": 3, "kappa": 8})):
        data[label] = {f"{tn}|a={a}|c={c}": best(a, c, ef, eb, **kw)
                       for tn, (ef, eb) in TARGETS.items() for a in A_GRID for c in C_GRID}
    data["min_n_stress"] = {f"{tn}|a={A_STRESS}|c={c}": best(A_STRESS, c, ef, eb)
                            for tn, (ef, eb) in TARGETS.items() for c in C_GRID}
    # 2. tolerable c for every threshold; best threshold t* per n
    data["cmax"], data["tstar"] = {}, {}
    for tn, (ef, eb) in TARGETS.items():
        for a in A_GRID + [A_STRESS]:
            for n in range(3, NMAX + 1):
                vals = {t: c_max(n, t, a, ef, eb) for t in range(1, n + 1)}
                for t, v in vals.items():
                    data["cmax"][f"{tn}|a={a}|n={n}|t={t}"] = v
                best_c = max(vals.values())
                ts = [t for t, v in vals.items() if v == best_c and v > 0]
                data["tstar"][f"{tn}|a={a}|n={n}"] = {"t": ts, "c_max": best_c, "majority": n // 2 + 1,
                                                      "c_max_majority": vals[n // 2 + 1]}
    # 3. thresholds used in practice: P_fail at c = 0 and tolerable c for P_breach <= 1e-4 (any a)
    data["practice"] = {}
    for k, (n, t) in PRACTICE.items():
        row = {"n": n, "t": t}
        for a in A_GRID:
            row[f"P_fail|a={a}"] = evaluate(n, t, a, 0.0)[0]
        lo, hi = 0.0, 0.5
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if evaluate(n, t, 0.0, mid)[1] <= 1e-4 else (lo, mid)
        row["c_tol_breach_1e-4"] = lo
        row["with_global_1e-3"] = evaluate(n, t, A_MID, C_ILL, A0=1e-3, K0=1e-3)
        row["indep_illustrative"] = evaluate(n, t, A_MID, C_ILL)
        data["practice"][k] = row
    # 4. heatmap (a = estimate, illustrative c)
    data["heat"] = {f"{n},{t}": evaluate(n, t, A_MID, C_ILL) for n in range(2, NMAX + 1) for t in range(1, n + 1)}
    # 5. global shocks: floors
    data["common_cause"] = {f"K0={K0}|n={n}": evaluate(n, n // 2 + 1, A_MID, C_ILL, K0=K0)
                            for K0 in (0.0, 1e-4, 1e-3) for n in range(3, NMAX + 1)}
    # 5b. exchangeable (correlated) authorities, a = estimate: tolerable c at the best threshold
    #     variant "c": correlated corruption, independent unavailability; "ac": both correlated
    data["corr"] = {}
    for var in ("c", "ac"):
        for tn, (ef, eb) in TARGETS.items():
            for rho in RHO_GRID:
                for n in range(5, NMAX + 1):
                    ra = rho if var == "ac" else 0.0
                    vals = {t: c_max_corr(n, t, A_MID, ef, eb, rho, ra) for t in range(1, n + 1)}
                    bt = max(vals, key=vals.get)
                    data["corr"][f"{var}|{tn}|rho={rho}|n={n}"] = {"t_best": bt, "c_max_best": vals[bt],
                                                                  "c_max_majority": vals[n // 2 + 1]}
    data["corr_fixed_c1"] = {f"{var}|rho={rho}|n={n}": evaluate_corr(n, n // 2 + 1, A_MID, C_ILL, rho, rho if var == "ac" else 0.0)
                             for var in ("c", "ac") for rho in RHO_GRID for n in (5, 7, 9, 15, 25, 51)}
    # 6. allocation to organisations (group shocks 1 %)
    designs = {"n=6, 3 orgs x 2": (6, [0, 0, 1, 1, 2, 2]), "n=6, 6 orgs x 1": (6, list(range(6))),
               "n=9, 3 orgs x 3": (9, [0, 0, 0, 1, 1, 1, 2, 2, 2]), "n=9, 9 orgs x 1": (9, list(range(9)))}
    data["groups"] = {}
    for name, (n, g) in designs.items():
        G = max(g) + 1
        for t in range(1, n + 1):
            data["groups"][f"{name}|t={t}"] = evaluate(n, t, A_MID, C_ILL, groups=g, A=[0.01] * G, K=[0.01] * G)
    # 6b. sweep of the organisation shock probability, majority thresholds
    data["groups_sweep"] = {}
    for sh in SHOCK_GRID:
        for name, (n, g) in designs.items():
            G = max(g) + 1
            data["groups_sweep"][f"shock={sh}|{name}"] = evaluate(n, n // 2 + 1, A_MID, C_ILL, groups=g, A=[sh] * G, K=[sh] * G)
    json.dump(data, open(os.path.join(OUT, "scenarios.json"), "w"), indent=1)
    return data


if __name__ == "__main__":
    d = main()
    print("a grid:", d["a_grid"])
    for k, v in d["min_n"].items():
        print(f"  {k:30s} " + (f"n={v['n']} t={v['t_min']}..{v['t_max']}" if v else "none<=15"))
    for k, v in d["tstar"].items():
        print(f"  t* {k:28s} t*={v['t']} c={100*v['c_max']:.2f}%  majority {v['majority']}: {100*v['c_max_majority']:.2f}%")
    for k, v in d["corr"].items():
        print("  corr", k, v)
    print("practice:")
    for k, v in d["practice"].items():
        print(f"  {k:28s} Pfail(a=mid,c=0)={v[f'P_fail|a={A_MID}']:.2e}  c_tol(1e-4)={100*v['c_tol_breach_1e-4']:.2f}%")
