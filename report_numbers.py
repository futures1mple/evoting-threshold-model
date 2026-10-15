"""Print every number quoted in the paper from results/*.json (for checking the text)."""
import json
S = json.load(open("results/scenarios.json")); B = json.load(open("results/base_rates.json"))
R = json.load(open("results/rounds.json")); CJ = json.load(open("results/cost.json")); C = CJ["configs"]; Rb = json.load(open("results/robustness.json"))
A = S["a_grid"]; am = A[1]; st = S["a_stress"]
print("base rates", {k: (v["failures"], v["trials"], round(100*v["estimate"], 2), [round(100*x, 2) for x in v["ci95"]]) for k, v in B.items() if k != "sensitivity"})
print("sensitivity", json.dumps(B["sensitivity"]))
print("a grid", A, "stress", st)
for key in ("moderate", "strict"):
    v = S["min_n"][f"{key}|a={am}|c=0.01"]; print("smallest", key, v)
print("min_n", {k: (v["n"], v["t_mid"]) if v else None for k, v in S["min_n"].items()})
print("min_n stress", {k: (v["n"], v["t_mid"]) if v else None for k, v in S["min_n_stress"].items()})
print("feasible points", sum(1 for v in S["min_n"].values() if v))
for tn in ("moderate", "strict"):
    for a in A + [st]:
        row = []
        for n in range(3, 16):
            v = S["tstar"][f"{tn}|a={a}|n={n}"]
            row.append(f"{n}:t*{v['t']} {100*v['c_max']:.1f}/maj{v['majority']} {100*v['c_max_majority']:.1f}" if v["c_max"] >= 1e-3 else f"{n}:-")
        print(tn, a, " | ".join(row))
print("practice")
for k, v in S["practice"].items():
    print(" ", k, [f"{v[f'P_fail|a={a}']:.1e}" for a in A], f"{100*v['c_tol_breach_1e-4']:.1f}%")
print("heat 5,3", S["heat"]["5,3"], "7,4", S["heat"]["7,4"])
print("common cause", {k: [f"{x:.1e}" for x in v] for k, v in S["common_cause"].items() if "n=9" in k})
for name in ("n=6", "n=9"):
    for t in (4, 5):
        k1 = [k for k in S["groups"] if k.startswith(name) and "3 orgs" in k and k.endswith(f"t={t}")]
        k2 = [k for k in S["groups"] if k.startswith(name) and " orgs x 1" in k and k.endswith(f"t={t}")]
        if k1 and k2:
            f1, b1 = S["groups"][k1[0]]; f2, b2 = S["groups"][k2[0]]
            print("groups", name, t, f"{f2:.1e}/{b2:.1e} vs {f1:.1e}/{b1:.1e} ratios {f1/f2:.1f} {b1/b2:.0f}")
for sh in (0.001, 0.01, 0.1):
    for n, a1, a2 in ((6, "n=6, 3 orgs x 2", "n=6, 6 orgs x 1"), (9, "n=9, 3 orgs x 3", "n=9, 9 orgs x 1")):
        f1, b1 = S["groups_sweep"][f"shock={sh}|{a1}"]; f2, b2 = S["groups_sweep"][f"shock={sh}|{a2}"]
        print("sweep", sh, n, f"fail x{f1/f2:.1f} breach x{b1/b2:.0f}")
print("rounds", {k: f"{v:.1e}" for k, v in R.items() if ("R=1," in k + "," or "R=3" in k or "det" in k)})
for var in ("c", "ac"):
    for tn in ("moderate", "strict"):
        for rho in S["rho_grid"]:
            print("corr", var, tn, rho, " ".join(f"{n}:t{S['corr'][f'{var}|{tn}|rho={rho}|n={n}']['t_best']} {100*S['corr'][f'{var}|{tn}|rho={rho}|n={n}']['c_max_best']:.2f}/{100*S['corr'][f'{var}|{tn}|rho={rho}|n={n}']['c_max_majority']:.2f}" for n in (5, 7, 9, 11, 13, 15)))
print("corr fixed c=1%", {k: [f"{x:.1e}" for x in v] for k, v in S["corr_fixed_c1"].items()})
print("robust", Rb)
rows = [r for r in C if r["NV"] == 6_480_000]
for r in rows:
    if r["n"] in (4, 5, 7, 9, 11):
        print("cost", r["n"], r["t"], r["ballot_KB"], round(r["board_GB"]/1000, 2), round(r["verify_ballots_core_h"] + r["verify_contrib_core_h"], 1),
              round(r["authority_round1_core_h"], 1), round(r["authority_round2_core_h"], 1), round(r["authority_round1_core_h_kappa8"], 1), round(r["authority_round2_core_h_kappa8"], 1),
              round(r["authority_veragg_core_h"], 1), round(r["authority_check_core_h"], 2))
print("constituency", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in CJ["constituency"].items()})
print("constituencies_total", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in CJ["constituencies_total"].items()})
print("split_repeats", {k: {kk: f"{vv:.2e}" for kk, vv in v.items()} for k, v in CJ["split_repeats_n7_t4"].items()})
print("split_pfail", {k: f"{v:.2e}" for k, v in R["split_constituencies"].items()})
print("stream", CJ["stream_national_measured"])
print("only_t", R["only_t_remaining_n7_t4"])
