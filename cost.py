"""Cost model for threshold commitment-based tallying (T-EVOLVE instantiation) as a function of n, t, N_V.

Sizes: computed by build/param_report of T-EVOLVE at national scale
(https://github.com/futures1mple/t-evolve-national-scale; same encoding as the measured
ballots; identical to v1.0.0 for N_V <= 10^6).
Times: unit costs measured on one vCPU of a Contabo Cloud VPS 8 (AMD EPYC, 2.0 GHz, 8 shared vCPUs,
gcc 13.3 -O3 -march=native), repository t-evolve-national-scale, results/national_scale:
  step 1  ballots at d = 8, q = 2^46 - 1103 (medians of 3 runs x 30 ballots, one core),
  step 3  aggregation per block with the bounds of 6,480,000 leaves (tree of 100,000 leaves, 2 runs),
  step 4  one constituency end to end (N_V = 51,829, d = 7, q = 2^43 - 175, 4 runs + 1 ballot stream).
Totals for the national tree (E = 13,857) are derived: per-block time x number of blocks (partial blocks
counted as full), as in results/national_scale/summary_steps_1_3_4_5.md.
Not included: encryption of seeds, signatures, complaint evidence, network.
"""
import json, os, subprocess
from math import comb

TEV = os.environ.get("TEVOLVE_DIR", "../t-evolve-national-scale")  # source tree of t-evolve-national-scale with build/param_report
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)
P_ATTEMPT = 1 / 3

# ---- unit times measured on the server (seconds unless noted)
NAT = {  # d = 8, q = 2^46 - 1103, bounds of 6,480,000 leaves
    "verify_ms": {4: 17.90, 5: 20.53, 7: 26.32, 9: 31.29, 11: 40.46},   # decode + Verify per ballot (step 1)
    "check_ms": 1.846,                                                   # Check_k per share, n = 7 (step 1)
    "tree_s_per_node": 0.308e-3,                                         # building the tree (step 3)
    "r1": (3.570, 3.783), "r2": (3.736, 3.851), "ver": (2.830, 3.379),   # per full block (open, zero), step 3 medians
}
CON = {  # d = 7, q = 2^43 - 175, N_V = 51,829 (step 4)
    "verify_ms": {7: 23.84}, "check_ms": 1.512, "vote_ms": 89.90,
    "tree_s_per_node": 14.0 / 53618,                                     # median tree time 14 s per authority (traced run)
    "r1": (2.244, 2.418), "r2": (2.575, 2.617), "ver": (2.576, 2.781),
    "tally_h_measured": 2.23, "tally_h_range": (2.02, 2.28), "peak_GB": 5.68,
    "auth_r1_s": 1044, "auth_r2_attempt_s": 281, "auth_ver_s": 300,      # per authority, measured (traced run)
}
MEM_NATIONAL_GB = 784.7      # step 5, one authority, sequential mode, N_V = 6,480,000
STREAM_NAT = {"ballots": 6_478_546, "accepted": 6_478_546, "share_checks": 45_349_822, "failed_checks": 0,
              "bytes": 1_304_154_433_157, "wall_h": 41.03, "core_h": 305.2,
              "vote_ms_loaded": 121.9, "verify_ms_loaded": 32.3, "check_ms_loaded": 2.06}

PARAMS = {10**4: (7, 2**42 - 143), 10**5: (7, 2**43 - 175), 10**6: (7, 2**45 - 591),
          6_480_000: (8, 2**46 - 1103)}  # national case: d=8 needed for hiding >= 2^128 (est_nat.py)
NV_NATIONAL, N_CONST = 6_478_546, 125
NV_CONST = -(-NV_NATIONAL // N_CONST)     # 51,829


def report(NV, n, t, d, q):
    r = subprocess.run([f"{TEV}/build/param_report", str(NV), str(n), str(t), "1", "-1", str(d), str(q), "1", "64"],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def lin(table, n):
    """measured value if available, else least-squares line through the measured points"""
    if n in table:
        return table[n]
    xs, ys = zip(*sorted(table.items()))
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return my + b * (n - mx)


def a_kappa(kappa):
    return (1 - (1 - P_ATTEMPT) ** kappa) / P_ATTEMPT          # expected examined attempts in round 2


def authority_h(r, U, kappa):
    """work of one authority for one tree (hours, one core): round 1, round 2, VerAgg of its contribution"""
    Eo, Ez = r["E_open"], r["E_zero"]
    r1 = r["nodes"] * U["tree_s_per_node"] + kappa * (Eo * U["r1"][0] + Ez * U["r1"][1])
    r2 = a_kappa(kappa) * (Eo * U["r2"][0] + Ez * U["r2"][1])
    v = Eo * U["ver"][0] + Ez * U["ver"][1]
    return r1 / 3600, r2 / 3600, v / 3600


def board_bytes(NV, r, n, t):
    # ballots + contributions of the t successful authorities + first-round messages of the other n - t
    return NV * r["ballot_bytes"] + t * (r["auth_round1_bytes"] + r["auth_round2_bytes"]) + (n - t) * r["auth_round1_bytes"]


def national(n, t):
    d, q = PARAMS[6_480_000]
    r = report(6_480_000, n, t, d, q)
    NV = NV_NATIONAL
    a4, a8 = authority_h(r, NAT, 4), authority_h(r, NAT, 8)
    vb = NV * lin(NAT["verify_ms"], n) / 1000 / 3600
    return {"NV": 6_480_000, "NV_actual": NV, "n": n, "t": t, "d": d, "log2q": round(r["log2q"], 3), "E": r["E"],
            "log2beta": r["log2beta"], "ballot_bytes": r["ballot_bytes"], "ballot_KB": round(r["ballot_bytes"] / 1024, 1),
            "auth_KB_per_ballot": round(r["auth_per_ballot_bytes"] / 1024, 1),
            "board_GB": board_bytes(NV, r, n, t) / 1e9, "ballots_TB": NV * r["ballot_bytes"] / 1e12,
            "verify_measured_n": n in NAT["verify_ms"],
            "verify_ballots_core_h": vb, "verify_contrib_core_h": t * a4[2],
            "authority_round1_core_h": a4[0], "authority_round2_core_h": a4[1],
            "authority_round1_core_h_kappa8": a8[0], "authority_round2_core_h_kappa8": a8[1],
            "authority_veragg_core_h": a4[2],
            "authority_agg_core_h_kappa4": a4[0] + a4[1], "authority_agg_core_h_kappa8": a8[0] + a8[1],
            "authority_check_core_h": NV * NAT["check_ms"] / 1000 / 3600,
            "memory_GB_per_authority": MEM_NATIONAL_GB if (n, t) == (7, 4) else None}


def constituencies(n=7, t=4):
    d, q = PARAMS[10**5]
    r = report(NV_CONST, n, t, d, q)
    a4, a8 = authority_h(r, CON, 4), authority_h(r, CON, 8)
    per = {"NV": NV_CONST, "E": r["E"], "log2beta": r["log2beta"], "ballot_bytes": r["ballot_bytes"],
           "ballot_KB": round(r["ballot_bytes"] / 1024, 1),
           "board_GB": board_bytes(NV_CONST, r, n, t) / 1e9,
           "authority_h_kappa4_derived": sum(a4), "authority_h_kappa8_derived": sum(a8),
           "authority_h_kappa4_measured": (CON["auth_r1_s"] + a_kappa(4) * CON["auth_r2_attempt_s"] + CON["auth_ver_s"]) / 3600,
           "verify_core_h": NV_CONST * CON["verify_ms"][7] / 1000 / 3600 + t * a4[2]}
    # totals over the electorate: per-ballot costs x actual number of voters, per-tree costs x 125
    tot = {"n_constituencies": N_CONST,
           "board_TB": (NV_NATIONAL * r["ballot_bytes"]
                        + N_CONST * (n * r["auth_round1_bytes"] + t * r["auth_round2_bytes"])) / 1e12,
           "ballots_TB": NV_NATIONAL * r["ballot_bytes"] / 1e12,
           "authority_core_h_kappa4": N_CONST * sum(a4), "authority_core_h_kappa8": N_CONST * sum(a8),
           "authority_agg_core_h_kappa4": N_CONST * (a4[0] + a4[1]), "authority_agg_core_h_kappa8": N_CONST * (a8[0] + a8[1]),
           "authority_agg_core_h_kappa16": N_CONST * sum(authority_h(r, CON, 16)[:2]),
           "authority_round1_core_h_kappa8": N_CONST * a8[0], "authority_round2_core_h_kappa8": N_CONST * a8[1],
           "verify_core_h": NV_NATIONAL * CON["verify_ms"][7] / 1000 / 3600 + N_CONST * t * a4[2],
           "tallies_core_h_measured": N_CONST * CON["tally_h_measured"],
           "memory_GB_per_tally": CON["peak_GB"]}
    return per, tot


def tally_attempt_fail(n, t, kappa):
    """probability that a tally attempt with all n authorities contributing fails (fewer than t non-aborting)"""
    s = 1 - (1 - P_ATTEMPT) ** kappa
    return sum(comb(n, j) * s ** j * (1 - s) ** (n - j) for j in range(t))


if __name__ == "__main__":
    rows = []
    for NV, (d, q) in PARAMS.items():
        for n in range(3, 16):
            t = n // 2 + 1
            if NV == 6_480_000:
                rows.append(national(n, t))
            else:
                r = report(NV, n, t, d, q)
                rows.append({"NV": NV, "n": n, "t": t, "d": d, "E": r["E"], "log2beta": r["log2beta"],
                             "ballot_bytes": r["ballot_bytes"], "ballot_KB": round(r["ballot_bytes"] / 1024, 1)})
    per, tot = constituencies()
    split = {f"kappa={k}": {"p_attempt_fail": tally_attempt_fail(7, 4, k),
                            "p_some_constituency_repeats": 1 - (1 - tally_attempt_fail(7, 4, k)) ** N_CONST,
                            "expected_constituencies_repeating": N_CONST * tally_attempt_fail(7, 4, k)} for k in (4, 8)}
    out = {"configs": rows, "constituency": per, "constituencies_total": tot, "split_repeats_n7_t4": split,
           "stream_national_measured": STREAM_NAT}
    json.dump(out, open(os.path.join(OUT, "cost.json"), "w"), indent=1)
    for r in rows:
        if r["NV"] == 6_480_000 and r["n"] in (4, 5, 7, 9, 11):
            print(f"n={r['n']:>2} t={r['t']} ballot={r['ballot_KB']}KB board={r['board_GB']/1000:.2f}TB "
                  f"verify={r['verify_ballots_core_h']:.1f}+{r['verify_contrib_core_h']:.1f}="
                  f"{r['verify_ballots_core_h']+r['verify_contrib_core_h']:.1f} core-h "
                  f"auth k4 {r['authority_round1_core_h']:.1f}/{r['authority_round2_core_h']:.1f} "
                  f"k8 {r['authority_round1_core_h_kappa8']:.1f}/{r['authority_round2_core_h_kappa8']:.1f} "
                  f"VerAgg {r['authority_veragg_core_h']:.1f} check {r['authority_check_core_h']:.2f}")
    print("constituency", json.dumps(per, indent=1))
    print("125 constituencies", json.dumps(tot, indent=1))
    print("split", json.dumps(split, indent=1))
