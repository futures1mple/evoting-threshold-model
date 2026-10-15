# evoting-threshold-model

Model, calibration data and scripts for the paper

> J. Alizadeh, "Choosing the Threshold: Availability, Privacy, and Cost Trade-Offs for Election Authorities in Post-Quantum Threshold E-Voting" (submitted).

The scripts compute, for `t`-of-`n` tallying authorities, the probability that the tally cannot be completed (`P_fail`) and the probability that ballot secrecy is breached (`P_breach`). They cover independent failures, common-cause shocks of organizations and suppliers, and correlated (exchangeable) authorities. They also reproduce every figure and table of the paper.

## Contents

| File | Purpose |
|---|---|
| `model.py` | `evaluate` (independent authorities, organization and global shocks, probabilistic aggregation) and `evaluate_corr` (exchangeable model with beta-distributed rates), all exact |
| `base_rates.py` | Unavailability per key holder and election from the public record (IACR/Helios 2010–2025, Swiss Post 2023–2026): Clopper–Pearson intervals and sensitivity → `results/base_rates.json` |
| `scenarios.py` | Smallest feasible `n`, tolerable corruption `c_max` for every `(n, t)`, best threshold `t*`, configurations used in practice, common causes, organizations, correlation → `results/scenarios.json` |
| `robust.py` | Robustness checks over the calibration grid → `results/robustness.json` |
| `rounds.py` | Probabilistic aggregation (`kappa` attempts, `R` tally attempts), also for 125 separate constituency tallies → `results/rounds.json` |
| `cost.py` | Ballot and bulletin-board sizes and running times for T-EVOLVE at 6.48 million voters, for a single national tally and for 125 constituency tallies → `results/cost.json` (needs the T-EVOLVE build, see below) |
| `est_nat.py`, `est_sis.py` | Lattice-estimator runs for the national parameter set → `results/estimator_*.json*` |
| `figures.py` | All figures → `fig/` |
| `report_numbers.py` | Prints every number quoted in the paper from the result files → `results/numbers.txt` |

All result files are included, so the figures can be redrawn without re-running anything.

## Where each figure and table comes from

| Paper item | Data | Script |
|---|---|---|
| Fig. 1 (heat maps of `P_fail`, `P_breach`) | `results/scenarios.json` (`heat`) | `figures.py` → `fig_heat` |
| Fig. 2 (smallest feasible `n`) | `results/scenarios.json` (`min_n`) | `figures.py` → `fig_min_n` |
| Fig. 3 (tolerable corruption at the best threshold) | `results/scenarios.json` (`tstar`) | `figures.py` → `fig_cmax` |
| Fig. 4, Table 3 (configurations used in practice) | `results/scenarios.json` (`practice`) | `figures.py` → `fig_practice`; `report_numbers.py` |
| Fig. 5 (organizations and common causes) | `results/scenarios.json` (`groups`; the sweep over shock probabilities quoted in the text: `groups_sweep`) | `figures.py` → `fig_groups` |
| Fig. 6 (correlated corruption) | `results/scenarios.json` (`corr`, `corr_fixed_c1`) | `figures.py` → `fig_corr`; `model.py` → `evaluate_corr` (the equation of the exchangeable model) |
| Fig. 7, Table 5 (bulletin board, public verification) | `results/cost.json` (`configs`) | `cost.py`; `figures.py` → `fig_cost` |
| Table 2 (unavailability per key holder and election) | `results/base_rates.json` | `base_rates.py` |
| Table 4 (probabilistic aggregation) | `results/rounds.json` | `rounds.py` |
| Table 6 (national tally vs. 125 constituency tallies) | `results/cost.json` (`constituency`, `constituencies_total`), `results/rounds.json` (`split_constituencies`, `only_t_remaining_n7_t4`) | `cost.py`, `rounds.py` |
| Robustness checks (Section on robustness) | `results/robustness.json` | `robust.py` |
| Every number quoted in the text | `results/numbers.txt` | `report_numbers.py` |

Figure and table numbers refer to the submitted manuscript.

## Requirements

Python 3.11 with `numpy`, `scipy`, `matplotlib`, `mpmath` (see `requirements.txt`). The versions used were numpy 2.4.4, scipy 1.17.1, matplotlib 3.10.9 and mpmath 1.3.0.

```
pip install -r requirements.txt
```

## Reproducing the results

```
python3 model.py          # self-checks against closed forms
python3 base_rates.py
python3 scenarios.py      # about 4 minutes
python3 robust.py
python3 rounds.py
python3 figures.py
python3 report_numbers.py > results/numbers.txt
```

### Cost model (optional)

`cost.py` calls `build/param_report` of T-EVOLVE at national scale (https://github.com/futures1mple/t-evolve-national-scale), an extension of the T-EVOLVE implementation (https://github.com/futures1mple/t-evolve-cryptoalg, release v1.0). The extension adds a larger tail exponent for trees with more than about 2,200 blocks (above about one million voters) and a third convolution level to the Gaussian sampler (needed above about 2.6 million voters); for up to 10^6 voters it gives the same parameters as release v1.0.

```
git clone https://github.com/futures1mple/t-evolve-national-scale
cd t-evolve-national-scale && make build/param_report
cd ../evoting-threshold-model
TEVOLVE_DIR=../t-evolve-national-scale python3 cost.py      # about 3 minutes
```

Sizes come from `param_report`. Running times are unit costs measured on one virtual CPU of a cloud server (Contabo Cloud VPS 8, AMD EPYC 2.0 GHz, 8 shared vCPUs, gcc 13.3 `-O3 -march=native`) and are written as constants at the top of `cost.py`. The measurement code, commands, raw timings and logs are in the same repository, directory `results/national_scale` (all 6,478,546 ballots generated and verified; aggregation per block with the national bounds; one constituency tally of 51,829 voters end to end; memory of a single national tally). Totals for the national aggregation tree are derived from the per-block times, not measured.

### Hardness estimates (optional)

`est_nat.py` and `est_sis.py` need SageMath and the lattice estimator (https://github.com/malb/lattice-estimator, commit 53da598):

```
ESTIMATOR_DIR=/path/to/lattice-estimator sage -python est_nat.py 8 70368744176561 <beta>
ESTIMATOR_DIR=/path/to/lattice-estimator sage -python est_sis.py 8 70368744176561 45.913
```

The SIS estimate was run for log2 beta = 45.913 (value of an earlier analysis build); the extended implementation gives 45.914, which does not change the estimate at the reported precision.

## Calibration data

| Source | Trials | Failures |
|---|---|---|
| IACR elections with Helios, 2010–2025, incl. the repeated 2025 election; 3 human trustees each | 51 | 1 (lost trustee key, 2025) |
| Swiss Post e-voting, federal votes 18.06.2023–27.09.2026; one trial per canton and date | 45 | 1 (Basel-Stadt, 08.03.2026) |

The sources are cited in the paper.

## License

MIT (see `LICENSE`).
