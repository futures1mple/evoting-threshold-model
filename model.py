"""Availability / privacy model for (n, t) threshold election authorities.

Authority states per election (independent part):
  unavailable with probability a_i  (crash, lost key material, refusal of an honest authority)
  corrupted   with probability c_i  (secret material reaches the adversary; may also withhold)
Common-cause shocks (beta-factor / Marshall-Olkin style):
  each group g (organisation, platform, vendor) has an outage shock with probability A_g that makes
  all its members unavailable and a compromise shock with probability K_g that corrupts all its members;
  a global shock (one software/hardware supplier for everybody) with probabilities A_0, K_0.

Tally fails      iff fewer than t authorities are available AND uncorrupted (corrupted ones may withhold),
                 or, for a scheme with probabilistic aggregation rounds, iff no round within the deadline
                 yields t valid contributions.
Privacy breach   iff at least t authorities are corrupted.
n-of-n schemes are the special case t = n.
All probabilities are computed exactly (dynamic programming over authorities, enumeration over shocks).
"""
from itertools import product
from math import comb


def _dp_counts(probs):
    """Distribution of the number of successes for independent Bernoulli(p_i)."""
    dist = [1.0]
    for p in probs:
        new = [0.0] * (len(dist) + 1)
        for k, v in enumerate(dist):
            new[k] += v * (1 - p)
            new[k + 1] += v * p
        dist = new
    return dist


def round_success(S, t, kappa=4, p_attempt=1 / 3, rounds=1):
    """P[tally completes] given S participating authorities, each with kappa attempts per round,
    an attempt succeeding with probability p_attempt; a round succeeds iff >= t authorities have a
    non-aborting attempt; up to `rounds` rounds before the deadline. rounds=None -> deterministic."""
    if S < t:
        return 0.0
    if rounds is None:
        return 1.0
    s = 1 - (1 - p_attempt) ** kappa
    pr = sum(comb(S, j) * s ** j * (1 - s) ** (S - j) for j in range(t, S + 1))
    return 1 - (1 - pr) ** rounds


def evaluate(n, t, a, c, groups=None, A=None, K=None, A0=0.0, K0=0.0, rounds=None, kappa=4):
    """Return (P_fail, P_breach).

    a, c: per-authority independent probabilities (float or list of length n).
    groups: list of group index per authority (0..G-1) or None; A, K: per-group shock probabilities.
    A0, K0: global shock probabilities.
    rounds: number of aggregation rounds before the deadline (None = deterministic one-round tally).
    """
    a = [a] * n if isinstance(a, (int, float)) else list(a)
    c = [c] * n if isinstance(c, (int, float)) else list(c)
    if groups is None:
        groups, A, K = [None] * n, [], []
    G = len(A)
    p_fail = p_breach = 0.0
    # enumerate group outage / compromise shocks and the global ones
    for gs_out in product((0, 1), repeat=G):
        w_out = 1.0
        for g in range(G):
            w_out *= A[g] if gs_out[g] else 1 - A[g]
        for gs_comp in product((0, 1), repeat=G):
            w_comp = 1.0
            for g in range(G):
                w_comp *= K[g] if gs_comp[g] else 1 - K[g]
            for o0, k0 in product((0, 1), repeat=2):
                w = w_out * w_comp * (A0 if o0 else 1 - A0) * (K0 if k0 else 1 - K0)
                if w == 0.0:
                    continue
                p_ok, p_corr = [], []
                for i in range(n):
                    g = groups[i]
                    out = o0 or (g is not None and gs_out[g])
                    comp = k0 or (g is not None and gs_comp[g])
                    pc = 1.0 if comp else c[i]
                    pa = 1.0 if out else a[i]
                    p_corr.append(pc)
                    p_ok.append((1 - pa) * (1 - pc))  # available and uncorrupted
                d_ok = _dp_counts(p_ok)
                d_corr = _dp_counts(p_corr)
                succ = sum(v * round_success(S, t, kappa=kappa, rounds=rounds) for S, v in enumerate(d_ok))
                p_fail += w * (1 - succ)
                p_breach += w * sum(d_corr[t:])
    return max(p_fail, 0.0), max(p_breach, 0.0)


def evaluate_corr(n, t, a, c, rho, rho_a=None):
    """(P_fail, P_breach) for exchangeable (correlated) authorities, deterministic tally.

    The per-election unavailability rate A and corruption rate C are drawn independently from beta
    distributions with means a, c and intra-class correlation rho (shape parameters
    mean*(1/rho - 1) and (1 - mean)*(1/rho - 1)); given (A, C), authorities fail independently.
    The number of corrupted authorities is then beta-binomial. Computed exactly from the beta moments
    with 60-digit arithmetic. rho = 0 reduces to evaluate(n, t, a, c).
    rho applies to corruption; rho_a to unavailability (default: the same value; 0 = independent).
    """
    rho_a = rho if rho_a is None else rho_a
    if rho == 0 and rho_a == 0:
        return evaluate(n, t, a, c)
    from mpmath import mp, mpf, binomial
    mp.dps = 60
    s_c = 1 / mpf(rho) - 1 if rho > 0 else None
    s_a = 1 / mpf(rho_a) - 1 if rho_a > 0 else None
    aa, ba = (mpf(a) * s_a, (1 - mpf(a)) * s_a) if s_a else (None, None)
    ac, bc = (mpf(c) * s_c, (1 - mpf(c)) * s_c) if s_c else (None, None)

    def mom(alpha, beta_, m, mean=None):   # E[X^m] for X ~ Beta(alpha, beta_); degenerate if alpha is None
        if alpha is None:
            return mpf(mean) ** m
        r = mpf(1)
        for i in range(m):
            r *= (alpha + i) / (alpha + beta_ + i)
        return r

    # P_breach: beta-binomial tail; Pr[C = k] = binom(n,k) E[C^k (1-C)^(n-k)]
    def pk_corr(k):
        return binomial(n, k) * sum(binomial(n - k, j) * (-1) ** j * mom(ac, bc, k + j, c) for j in range(n - k + 1))
    p_breach = sum(pk_corr(k) for k in range(t, n + 1)) if c > 0 else mpf(0)
    # P_fail: F = number of non-contributing authorities; 1 - g = U V with U = 1 - A, V = 1 - C
    def EUV(m):
        eu = mom(ba, aa, m, 1 - a) if a > 0 else mpf(1)
        ev = mom(bc, ac, m, 1 - c) if c > 0 else mpf(1)
        return eu * ev
    def pk_fail(k):
        return binomial(n, k) * sum(binomial(k, j) * (-1) ** j * EUV(n - k + j) for j in range(k + 1))
    p_fail = sum(pk_fail(k) for k in range(n - t + 1, n + 1))
    return float(p_fail), float(p_breach)


def feasible(nmax, a, c, eps_fail, eps_breach, **kw):
    """All (n, t) with P_fail <= eps_fail and P_breach <= eps_breach."""
    out = []
    for n in range(1, nmax + 1):
        for t in range(1, n + 1):
            pf, pb = evaluate(n, t, a, c, **kw)
            if pf <= eps_fail and pb <= eps_breach:
                out.append((n, t, pf, pb))
    return out


def group_condition(m, n, t, k=1):
    """Tolerance of k simultaneous group shocks when every group holds at most m authorities:
    privacy needs k*m <= t-1, availability needs k*m <= n-t."""
    return k * m <= t - 1 and k * m <= n - t


if __name__ == "__main__":
    # sanity checks against closed forms
    n, t, a, c = 5, 3, 0.05, 0.02
    pf, pb = evaluate(n, t, a, c)
    q = (1 - a) * (1 - c)
    pf_cf = sum(comb(n, j) * q ** j * (1 - q) ** (n - j) for j in range(t))
    pb_cf = sum(comb(n, j) * c ** j * (1 - c) ** (n - j) for j in range(t, n + 1))
    assert abs(pf - pf_cf) < 1e-15 and abs(pb - pb_cf) < 1e-15, (pf, pf_cf, pb, pb_cf)
    # global compromise shock is a floor on the breach probability
    pf2, pb2 = evaluate(9, 6, 0.05, 0.02, K0=1e-3)
    assert pb2 >= 1e-3
    print("checks ok", pf, pb, pb2)
