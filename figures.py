"""Figures for the (n, t) paper. Reads results/*.json, writes fig/*.pdf and fig/*.png.

Single-column figures are drawn at 3.5 in width (panels stacked), so that text prints at 7-8 pt.
"""
import json, math, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

H = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(H, "results", "scenarios.json")))
C = json.load(open(os.path.join(H, "results", "cost.json")))["configs"]
FIG = os.path.join(H, "fig")
os.makedirs(FIG, exist_ok=True)

CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
BLUE = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
        "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("blue", BLUE)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
W = 3.5   # column width in inches

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "legend.frameon": False, "legend.fontsize": 7, "savefig.dpi": 300, "savefig.bbox": "tight"})
A = R["a_grid"]
ALAB = [f"$a={100*a:.2f}\\%$ (lower)" if i == 0 else f"$a={100*a:.2f}\\%$ (calibration)" if i == 1 else f"$a={100*a:.2f}\\%$ (upper)"
        for i, a in enumerate(A)]
TT = {"moderate": "moderate: $P_{\\mathrm{fail}}\\leq10^{-3}$, $P_{\\mathrm{breach}}\\leq10^{-4}$",
      "strict": "strict: $P_{\\mathrm{fail}}\\leq10^{-4}$, $P_{\\mathrm{breach}}\\leq10^{-6}$"}


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".pdf"))
    fig.savefig(os.path.join(FIG, name + ".png"))
    plt.close(fig)


# ---------- Fig. 1: heatmaps of P_fail and P_breach (a = estimate, c = 1 %), full width
def fig_heat():
    NMAX = 15
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw={"wspace": 0.25})
    eps = (1e-3, 1e-4)
    for k, (ax, title) in enumerate(zip(axes, ["failed tally  $P_{\\mathrm{fail}}$", "breach of secrecy  $P_{\\mathrm{breach}}$"])):
        M = [[math.nan] * NMAX for _ in range(NMAX)]
        for key, v in R["heat"].items():
            n, t = map(int, key.split(","))
            M[t - 1][n - 1] = max(math.log10(max(v[k], 1e-12)), -12)
        im = ax.imshow(M, origin="lower", cmap=SEQ.reversed(), vmin=-12, vmax=0, aspect="auto",
                       extent=(0.5, NMAX + 0.5, 0.5, NMAX + 0.5))
        for key, v in R["heat"].items():
            n, t = map(int, key.split(","))
            if v[0] <= eps[0] and v[1] <= eps[1]:
                ax.add_patch(Rectangle((n - 0.5, t - 0.5), 1, 1, fill=False, ec=CAT[1], lw=1.4))
        ax.set_xlim(1.5, NMAX + 0.5); ax.set_ylim(0.5, NMAX + 0.5)
        ax.set_xlabel("number of authorities $n$"); ax.set_ylabel("threshold $t$")
        ax.set_title(title, fontsize=8.5, color=INK, loc="left")
        ax.grid(False)
        ax.set_xticks(range(2, NMAX + 1, 2)); ax.set_yticks(range(1, NMAX + 1, 2))
    cb = fig.colorbar(im, ax=list(axes), fraction=0.03, pad=0.02)
    cb.set_label("$\\log_{10}$ probability per election", color=INK2)
    save(fig, "fig1_heatmaps")


# ---------- Fig. 2: smallest feasible n versus c (stacked panels)
def fig_min_n():
    fig, axes = plt.subplots(2, 1, figsize=(W, 4.0), sharex=True, gridspec_kw={"hspace": 0.35})
    for ax, tn in zip(axes, ["moderate", "strict"]):
        for i, a in enumerate(A):
            xs, ys = [], []
            for c in R["c_grid"]:
                v = R["min_n"][f"{tn}|a={a}|c={c}"]
                if v:
                    xs.append(c * 100); ys.append(v["n"])
            ax.plot(xs, ys, "-o", color=CAT[i], lw=1.8, ms=4.5, mec="white", mew=1, label=ALAB[i])
        ax.set_xscale("log"); ax.set_xticks([0.5, 1, 2, 5]); ax.set_xticklabels(["0.5", "1", "2", "5"])
        ax.set_title(TT[tn], fontsize=7.5, color=INK, loc="left")
        ax.set_ylabel("smallest feasible $n$"); ax.set_ylim(2, 15); ax.set_yticks(range(3, 16, 2))
    axes[1].set_xlabel("corruption probability $c$ per authority (%)")
    axes[0].legend(loc="upper left")
    save(fig, "fig2_min_n")


# ---------- Fig. 3: configurations used in practice
def fig_practice():
    fig, ax = plt.subplots(figsize=(W, 2.8))
    am = A[1]
    for k, v in R["practice"].items():
        lab = k.split()[-1].replace("-of-", " of ")
        x = v[f"P_fail|a={am}"]; y = 100 * v["c_tol_breach_1e-4"]
        lo, hi = v[f"P_fail|a={A[0]}"], v[f"P_fail|a={A[2]}"]
        ax.plot([lo, hi], [y, y], color=CAT[0], lw=1.2, alpha=0.6, solid_capstyle="round")
        ax.plot(x, y, "o", color=CAT[0], ms=6, mec="white", mew=1.2, zorder=3)
        off = {"4 of 4": (0, -11), "3 of 3": (0, 6)}.get(lab, (0, 6))
        ax.annotate(lab, (x, y), xytext=off, textcoords="offset points", fontsize=7.5, color=INK, ha="center")
    ax.set_xscale("log")
    ax.set_xlabel("$P_{\\mathrm{fail}}$ per election at $c=0$")
    ax.set_ylabel("tolerable $c$ for $P_{\\mathrm{breach}}\\leq10^{-4}$ (%)")
    ax.axvline(1e-3, color=CAT[1], lw=1, ls="--")
    ax.annotate("$10^{-3}$", (1e-3, 11.5), xytext=(3, 0), textcoords="offset points", fontsize=7, color=CAT[1])
    ax.set_ylim(0, 12.5)
    save(fig, "fig3_practice")


# ---------- Fig. 4: same n, different allocation to organisations (stacked)
def fig_groups():
    fig, axes = plt.subplots(2, 1, figsize=(W, 4.4), sharex=False, gridspec_kw={"hspace": 0.45})
    for ax, (n, designs) in zip(axes, [(6, ["n=6, 3 orgs x 2", "n=6, 6 orgs x 1"]),
                                       (9, ["n=9, 3 orgs x 3", "n=9, 9 orgs x 1"])]):
        for i, dname in enumerate(designs):
            ts = list(range(1, n + 1))
            pb = [max(R["groups"][f"{dname}|t={t}"][1], 1e-13) for t in ts]
            pf = [max(R["groups"][f"{dname}|t={t}"][0], 1e-13) for t in ts]
            lab = "3 organizations" if i == 0 else "one per organization"
            ax.plot(ts, pb, "-o", color=CAT[i], lw=1.8, ms=4, mec="white", mew=1, label=f"breach, {lab}")
            ax.plot(ts, pf, "--s", color=CAT[i], lw=1.4, ms=3.5, mec="white", mew=1, label=f"failure, {lab}")
        ax.set_yscale("log"); ax.set_ylim(1e-12, 1)
        ax.set_xlabel("threshold $t$"); ax.set_title(f"$n={n}$", fontsize=8.5, loc="left", color=INK)
        ax.set_ylabel("probability per election")
        ax.set_xticks(range(1, n + 1))
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.06), fontsize=6.8)
    save(fig, "fig4_groups")


# ---------- Fig. 5: national-scale cost versus n (stacked)
def fig_cost():
    rows = [r for r in C if r["NV"] == 6_480_000]
    ns = [r["n"] for r in rows]
    fig, axes = plt.subplots(2, 1, figsize=(W, 3.6), sharex=True, gridspec_kw={"hspace": 0.2})
    axes[0].bar(ns, [r["board_GB"] / 1000 for r in rows], color=CAT[0], width=0.7, edgecolor="white", linewidth=1)
    axes[0].set_ylabel("bulletin board (TB)")
    axes[1].bar(ns, [r["verify_ballots_core_h"] + r["verify_contrib_core_h"] for r in rows], color=CAT[0],
                width=0.7, edgecolor="white", linewidth=1)
    axes[1].set_ylabel("public verification\n(core-hours)"); axes[1].set_xlabel("number of authorities $n$ ($t=\\lfloor n/2\\rfloor+1$)")
    for ax in axes:
        ax.set_xticks(ns); ax.grid(axis="x", visible=False)
    save(fig, "fig5_cost")


# ---------- Fig. 6: tolerable corruption at the best threshold t*, marker = position of t* (stacked)
def fig_cmax():
    fig, axes = plt.subplots(2, 1, figsize=(W, 4.4), sharex=True, gridspec_kw={"hspace": 0.3})
    for ax, tn in zip(axes, ["moderate", "strict"]):
        for i, a in enumerate(A):
            ns, ys, mk = [], [], []
            for n in range(3, 16):
                v = R["tstar"][f"{tn}|a={a}|n={n}"]
                if v["c_max"] < 1e-3:
                    continue
                t = v["t"][0]; m = n // 2 + 1
                ns.append(n); ys.append(100 * v["c_max"]); mk.append("o" if t == m else ("v" if t < m else "^"))
            ax.plot(ns, ys, "-", color=CAT[i], lw=1.6, label=ALAB[i])
            for x, y, m in zip(ns, ys, mk):
                ax.plot(x, y, m, color=CAT[i], ms=5 if m == "o" else 6, mec="white", mew=0.8)
        ax.set_title(TT[tn], fontsize=7.5, loc="left", color=INK)
        ax.set_ylabel("tolerable $c$ at $t^*$ (%)")
    axes[1].set_xlabel("number of authorities $n$")
    axes[1].set_xticks(range(3, 16))
    h, l = axes[0].get_legend_handles_labels()
    h += [Line2D([], [], marker=m, ls="", color=INK2, ms=5) for m in ("o", "v", "^")]
    l += ["$t^*=\\lfloor n/2\\rfloor+1$", "$t^*$ lower", "$t^*$ higher"]
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=6.6, columnspacing=0.9)
    save(fig, "fig6_tolerable_c")


# ---------- Fig. 7: correlated corruption (exchangeable model, a = estimate)
def fig_corr():
    fig, axes = plt.subplots(2, 1, figsize=(W, 4.6), gridspec_kw={"hspace": 0.62})
    rhos = R["rho_grid"]
    for i, rho in enumerate(rhos):
        ns = [5, 7, 9, 11, 13, 15]
        ys = [100 * R["corr"][f"c|moderate|rho={rho}|n={n}"]["c_max_best"] for n in ns]
        axes[0].plot(ns, ys, "-o", color=CAT[i], lw=1.6, ms=4, mec="white", mew=1, label=f"$\\rho={rho:g}$")
        ns2 = [5, 7, 9, 15, 25, 51]
        ys2 = [max(R["corr_fixed_c1"][f"c|rho={rho}|n={n}"][1], 1e-40) for n in ns2]
        axes[1].plot(ns2, ys2, "-o", color=CAT[i], lw=1.6, ms=4, mec="white", mew=1, label=f"$\\rho={rho:g}$")
    axes[0].set_yscale("log"); axes[0].set_ylabel("tolerable $c$ at $t^*$ (%)")
    axes[0].set_xlabel("number of authorities $n$"); axes[0].set_xticks([5, 7, 9, 11, 13, 15])
    axes[0].set_title("tolerable corruption, moderate targets", fontsize=7.5, loc="left", color=INK)
    axes[0].legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.28), fontsize=6.5, handlelength=1.2, columnspacing=0.8)
    axes[1].set_yscale("log"); axes[1].set_ylim(1e-16, 1e-1)
    axes[1].set_xscale("log"); axes[1].set_xticks([5, 7, 9, 15, 25, 51]); axes[1].set_xticklabels(["5", "7", "9", "15", "25", "51"])
    axes[1].minorticks_off()
    axes[1].set_xlabel("number of authorities $n$, $t=\\lfloor n/2\\rfloor+1$")
    axes[1].set_ylabel("$P_{\\mathrm{breach}}$ at $c=1\\%$")
    axes[1].set_title("breach probability", fontsize=7.5, loc="left", color=INK)
    save(fig, "fig7_correlation")


if __name__ == "__main__":
    fig_heat(); fig_min_n(); fig_practice(); fig_groups(); fig_cost(); fig_cmax(); fig_corr()
    print(sorted(os.listdir(FIG)))
