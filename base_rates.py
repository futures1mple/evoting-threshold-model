"""Empirical anchor for the unavailability probability a (per key-holding party and election).

Two public cases (sources in the paper):
  IACR elections with Helios, 2010-2025: 16 annual elections plus the repeated 2025 election,
      3 human trustees each = 51 trustee-elections, 1 irretrievably lost trustee key (2025).
      (In 2018-2020 the Helios server acted as an additional, automated trustee; it is not counted.)
  Swiss Post e-voting, 18.06.2023-27.09.2026: 12 federal voting dates. BS, SG, TG on the first two;
      GR in addition from 03.03.2024 (8 dates up to 08.03.2026): 3*2 + 4*8 = 38 canton-ballots;
      SG, GR, TG on 14.06.2026 (3) and SG, GR, TG, LU on 27.09.2026 (4): 45 canton-ballots in total,
      1 failure (Basel-Stadt, 08.03.2026: decryption password unusable).
Exact (Clopper-Pearson) 95 % intervals; the pooled estimate treats both as Bernoulli trials of one
key-holding party. Sensitivity: each source alone, Jeffreys interval, and Z additional failure-free
trials from systems without reported failures.
"""
import json, os
from scipy.stats import beta

CASES = {"IACR (Helios), 2010-2025": (1, 51), "Swiss Post, 2023-2026": (1, 45)}


def cp(k, N, level=0.95):
    lo = beta.ppf((1 - level) / 2, k, N - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - (1 - level) / 2, k + 1, N - k) if k < N else 1.0
    return lo, hi


def jeffreys(k, N, level=0.95):
    return beta.ppf((1 - level) / 2, k + 0.5, N - k + 0.5), beta.ppf(1 - (1 - level) / 2, k + 0.5, N - k + 0.5)


if __name__ == "__main__":
    out = {}
    K = N = 0
    for name, (k, n) in CASES.items():
        lo, hi = cp(k, n)
        out[name] = {"failures": k, "trials": n, "estimate": k / n, "ci95": [lo, hi]}
        K += k; N += n
    lo, hi = cp(K, N)
    out["pooled"] = {"failures": K, "trials": N, "estimate": K / N, "ci95": [lo, hi]}
    out["sensitivity"] = {"pooled_jeffreys_ci95": list(jeffreys(K, N))}
    for Z in (0, 45, 96):
        out["sensitivity"][f"pooled_plus_{Z}_failure_free"] = {"estimate": K / (N + Z), "ci95": list(cp(K, N + Z))}
    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/base_rates.json", "w"), indent=1)
    for k, v in out.items():
        if k == "sensitivity":
            print(json.dumps(v, indent=1)); continue
        print(f"{k:28s} {v['failures']}/{v['trials']} = {100*v['estimate']:.2f}%  95% CI [{100*v['ci95'][0]:.2f}%, {100*v['ci95'][1]:.2f}%]")
